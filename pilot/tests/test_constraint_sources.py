"""Source anchors cannot turn model summaries or quote fragments into USER facts."""
import copy

import pytest

from triz.constraint_sources import user_constraint_sources, validate_user_constraint_source
from triz.schema import Constraint, GlobalState, ClarifyTurn


def fixture_state():
    state = GlobalState(run_id='source-fixture', raw_query='기존 주설비는 유지해야 하며 새 공장 건설은 불가능합니다.')
    state.intake.clarify_turns = [
        ClarifyTurn(question='현재 핵심 인재에게 지급 가능한 최대 연봉 수준은?',
                    user_answer='현재 연봉의 10% 이내로만 인상 가능', answered=True),
        ClarifyTurn(question='최대 예산은 몇 원인가요?', user_answer='100', answered=False),
    ]
    state.confirm.user_amendments = ['구축할 시스템의 종류는 특정하지 않습니다.']
    state.scratch['deep_dive'] = {
        'answer_turns':[{'question':'허용 최고 온도는 몇 K인가요?', 'answer':'4 K 이하'}],
        'answers':['4 K 이하'],
        'confirmed_facts':['새로 추론한 조건도 사용자 사실이다.'],
    }
    state.intake.frame.success_criteria = ['모든 목표는 100% 달성해야 한다.']
    return state


def test_whitelisted_sources_keep_full_question_context_and_no_generated_provenance():
    state = fixture_state(); before = copy.deepcopy(state.model_dump())
    sources = user_constraint_sources(state)
    assert set(sources) == {'raw_query', 'user_query', 'intake.clarify_turns[0].user_answer',
                           'confirm.user_amendments[0]', 'scratch.deep_dive.answer_turns[0].answer'}
    assert sources['intake.clarify_turns[0].user_answer'] == {
        'text':'현재 연봉의 10% 이내로만 인상 가능', 'question':'현재 핵심 인재에게 지급 가능한 최대 연봉 수준은?'}
    assert state.model_dump() == before


def test_direct_salary_answer_anchors_quote_without_proving_expanded_claim():
    sources = user_constraint_sources(fixture_state())
    row = dict(source='USER', hard=True, source_path='intake.clarify_turns[0].user_answer',
               source_quote='현재 연봉의 10% 이내로만 인상 가능')
    assert validate_user_constraint_source(row, sources) == []
    # This helper authenticates the quote only; independent semantic review must
    # reject applying the salary cap to all compensation or reversing <= to >=.
    row['statement'] = '모든 금전 보상은 10% 이상이어야 한다.'
    assert validate_user_constraint_source(row, sources) == []


@pytest.mark.parametrize('path', [
    'intake.frame.success_criteria[0]', 'scratch.deep_dive.confirmed_facts[0]',
    'confirmed_facts[0]', 'constraints.items[0].statement',
    'intake.attachments[0].extracted_facts[0]', 'intake.attachments[0].extracted_text',
    'confirm.candidates[0].description', 'intake.clarify_turns[1].user_answer',
    'intake.clarify_turns[-1].user_answer', 'observations.answers[0]',
])
def test_non_user_unanswered_and_dynamic_paths_are_rejected(path):
    assert validate_user_constraint_source({'source_path':path, 'source_quote':'직접 확인된 사용자 조건입니다.'},
                                           user_constraint_sources(fixture_state()))


@pytest.mark.parametrize('quote', ['', ' ', '10', '10%', '10% 이상', '현재 연봉의 10퍼센트 이내로만 인상 가능', None, 10])
def test_empty_numeric_fragments_and_inexact_quotes_cannot_anchor_claim(quote):
    assert validate_user_constraint_source({'source_path':'intake.clarify_turns[0].user_answer', 'source_quote':quote},
                                           user_constraint_sources(fixture_state()))


def test_short_complete_answer_is_allowed_with_question_but_not_query_fragment():
    state = fixture_state()
    state.intake.clarify_turns[0].user_answer = '10%'
    sources = user_constraint_sources(state)
    assert validate_user_constraint_source({'source_path':'intake.clarify_turns[0].user_answer', 'source_quote':'10%'}, sources) == []
    state.raw_query = '10%'
    assert validate_user_constraint_source({'source_path':'raw_query', 'source_quote':'10%'}, user_constraint_sources(state))


def test_short_complete_user_prohibition_is_not_mistaken_for_a_numeric_fragment():
    state = fixture_state(); state.raw_query = '폭발금지'
    assert validate_user_constraint_source({'source_path':'raw_query', 'source_quote':'폭발금지'},
                                           user_constraint_sources(state)) == []
    state.raw_query = '안전 요구는 폭발금지이고 충격 내구성도 유지해야 한다.'
    assert validate_user_constraint_source({'source_path':'raw_query', 'source_quote':'폭발금지'},
                                           user_constraint_sources(state))


def test_question_premise_is_not_a_quote_from_the_user_answer():
    state = fixture_state(); state.intake.clarify_turns[0].user_answer = '잘 모르겠다'
    sources = user_constraint_sources(state)
    assert validate_user_constraint_source({'source_path':'intake.clarify_turns[0].user_answer',
                                           'source_quote':'현재 핵심 인재에게 지급 가능한 최대 연봉 수준'}, sources)


def test_legacy_bare_deepdive_answers_and_skipped_turns_are_not_promoted():
    state = fixture_state()
    state.scratch['deep_dive'].pop('answer_turns')
    assert not any(path.startswith('scratch.') for path in user_constraint_sources(state))
    state.scratch['deep_dive']['answer_turns'] = [{'question':'최대 온도?', 'answer':'4 K'}]
    state.scratch['deep_dive']['skipped'] = True
    assert not any(path.startswith('scratch.') for path in user_constraint_sources(state))


def test_malformed_or_missing_question_context_is_excluded():
    state = fixture_state()
    state.scratch['deep_dive']['answer_turns'] = [None, {'answer':'4 K'}, {'question':'온도?', 'answer':{'value':4}}]
    state.intake.clarify_turns[0].question = ''
    sources = user_constraint_sources(state)
    assert not any(path.startswith(('scratch.', 'intake.')) for path in sources)
    assert validate_user_constraint_source({}, sources)
    assert validate_user_constraint_source(None, sources)


def test_source_fields_roundtrip_and_legacy_constraints_remain_loadable():
    old = Constraint(statement='legacy inferred constraint', source='INFERRED', hard=True, confidence=.8)
    assert old.source_path == old.source_quote == ''
    data = dict(statement='현재 연봉 인상률은 10% 이내', source='USER', hard=True,
                source_path='intake.clarify_turns[0].user_answer', source_quote='현재 연봉의 10% 이내로만 인상 가능')
    assert Constraint.model_validate_json(Constraint(**data).model_dump_json()).source_quote == data['source_quote']
    assert old.source == 'INFERRED' and old.confidence == .8
