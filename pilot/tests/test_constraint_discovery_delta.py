"""Regression: existing hard rows are not new DOMAIN guesses; direct caps stay USER."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_checks as checks, nodes, verification_contract as contract
from triz.constraint_sources import user_constraint_sources
from triz.context import AbortRun, RunContext
from triz.schema import ClarifyTurn, Constraint
from triz.settings import settings


def archive(state):
    state.constraints.items = [
        Constraint(id='CON-USER', statement='내부 형평성 붕괴 금지', source='USER', hard=True),
        Constraint(id='CON-INFERRED', statement='노조와 사전 협의', source='INFERRED', hard=True, confidence=.8),
        Constraint(id='CON-DOMAIN', statement='최대 연봉 인상률은 미확인', source='DOMAIN', hard=False, confidence=.4),
    ]
    state.intake.clarify_turns = [ClarifyTurn(
        question='현재 연봉 대비 최대 인상 가능 비율은?',
        user_answer='현재 연봉의 10% 이내로만 인상 가능', answered=True)]


def candidate():
    return {'constraints': [], 'user_constraints': [{
        'statement': '핵심 인재의 연봉 인상률은 현재 연봉 대비 10% 이내이다.',
        'kind': 'NUMERIC', 'category': 'USER_STATED', 'source': 'USER',
        'parameter': '연봉 인상률', 'operator': '<=', 'value': '10', 'unit': '%',
        'hard': True, 'confidence': 1.,
        'source_path': 'intake.clarify_turns[0].user_answer',
        'source_quote': '현재 연봉의 10% 이내로만 인상 가능',
        'rationale': '연봉에 관한 직접 답변. 다른 보상 수단 전체의 상한은 아님.',
    }], 'taboo': []}


def check(state, value):
    return checks.discovered_constraints(value, ['CON-USER'],
        [c.id for c in state.constraints.items], state.constraints.items, user_constraint_sources(state))


def test_repeated_existing_hard_row_is_removed_from_delta_without_downgrading(state):
    archive(state)
    before = deepcopy(state.constraints.model_dump())
    value = {'constraints': [state.constraints.items[0].model_dump()], 'user_constraints': [], 'taboo': []}
    issues = check(state, value)
    assert any('출력 배열에서만 제외' in item for item in issues)
    value['constraints'] = []
    assert not check(state, value)
    assert not contract.repair_shape_issues({'constraints': [before['items'][0]], 'taboo': []}, value, node='s3_constraints')
    assert state.constraints.model_dump() == before


def test_existing_statement_is_duplicate_even_if_id_and_source_omitted(state):
    archive(state)
    value = {'constraints': [{'statement': '내부  형평성 붕괴 금지', 'rationale': '같은 뜻',
                             'hard': False, 'confidence': .6}], 'taboo': []}
    assert any('이미 저장된 제약' in issue for issue in check(state, value))


def test_direct_salary_cap_has_valid_source_without_becoming_domain_soft(state):
    archive(state)
    assert not check(state, candidate())
    invalid = candidate()
    invalid['constraints'] = invalid.pop('user_constraints')
    assert any('DOMAIN 가설 전용' in issue for issue in check(state, invalid))


@pytest.mark.parametrize('mutation', ['summary', 'quote', 'source', 'confidence', 'hard_type'])
def test_invalid_direct_source_or_type_cannot_pass_structure(state, mutation):
    archive(state)
    value = candidate()
    row = value['user_constraints'][0]
    if mutation == 'summary':
        row['source_path'] = 'intake.frame.restated_problem'
    elif mutation == 'quote':
        row['source_quote'] = '연봉 인상률은 무제한이다'
    elif mutation == 'source':
        row['source'] = 'INFERRED'
    elif mutation == 'confidence':
        row['confidence'] = float('nan')
    else:
        row['hard'] = 'true'
    assert check(state, value)


def test_inferred_hard_is_preserved_but_is_not_a_confirmed_user_taboo(state):
    archive(state)
    value = {'constraints': [], 'user_constraints': [], 'taboo': [
        {'item': '협의 없는 변경', 'why': '기존 INFERRED 제약', 'confirmed': True,
         'constraint_id': 'CON-INFERRED'}]}
    assert any('확인된 hard' in issue for issue in check(state, value))
    value['taboo'][0]['confirmed'] = False
    assert not check(state, value)
    assert state.constraints.items[1].source == 'INFERRED' and state.constraints.items[1].hard


def test_node_commits_both_new_sources_after_gates_without_mutating_archive(state, monkeypatch):
    archive(state)
    before = deepcopy(state.constraints.model_dump()['items'])
    value = candidate()
    value['constraints'] = [{'statement': '가설: 인정 부여 권한은 미확인', 'source': 'DOMAIN',
        'kind': 'PREFERENCE', 'category': 'OPERATION', 'hard': False, 'confidence': .4,
        'rationale': '현행 문안 확인 필요'}]
    def verified(ctx, **kwargs):
        assert kwargs['rubric_id'] == 'R3_CONSTRAINT'
        assert kwargs['vars']['existing_constraints'] == before
        assert kwargs['vars']['confirmed_hard_constraint_ids'] == ['CON-USER']
        assert not kwargs['checker'](value)
        return value
    monkeypatch.setattr(agent, 'run_agent', verified)
    nodes._discover_constraints(RunContext(state))
    assert [x.model_dump() for x in state.constraints.items[:3]] == before
    assert state.constraints.items[3].source == 'DOMAIN' and not state.constraints.items[3].hard
    cap = state.constraints.items[4]
    assert cap.source == 'USER' and cap.hard and cap.value == '10'
    assert cap.source_quote == value['user_constraints'][0]['source_quote']


def test_semantic_rejection_prevents_any_constraint_commit(state, monkeypatch):
    archive(state)
    before = deepcopy(state.constraints.model_dump())
    def rejected(ctx, **kwargs):
        # Exact quotation does not prove an expanded 'all compensation' cap.
        value = candidate()
        value['user_constraints'][0]['statement'] = '모든 금전 보상 인상은 10% 이내'
        assert not kwargs['checker'](value)
        raise AbortRun('Independent semantic reviewer rejects expanded scope')
    monkeypatch.setattr(agent, 'run_agent', rejected)
    with pytest.raises(AbortRun):
        nodes._discover_constraints(RunContext(state))
    assert state.constraints.model_dump() == before


def test_pinned_generation_and_required_review_receive_new_delta_contract(state):
    archive(state)
    generation = contract.generation_supplement(state, 's3_constraints')
    assert 'user_constraints' in generation and 'source_path/source_quote' in generation
    assert 'CON-INFERRED' in generation and 'INFERRED' in generation
    rubric = contract.effective_rubric(settings, 'R3_CONSTRAINT')
    c1 = next(row for row in rubric['criteria'] if row['id'] == 'C1')
    assert c1['required'] and c1['min_score'] == 1
    assert '질문·원문' in c1['text'] and '의무 수준' in c1['text']
    assert '인용 문자열 일치만으로 USER 승격하지 않는다' in contract.verifier_supplement(rubric)


@pytest.mark.parametrize('outcome', ['accepted', 'rejected', 'repaired'])
def test_real_agent_requires_independent_review_before_direct_user_commit(state, monkeypatch, outcome):
    from triz import rag
    from triz.ax import runtime
    archive(state)
    before = deepcopy(state.constraints.model_dump())
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values: prompt_id + str(values))
    monkeypatch.setitem(settings.triz['verification'], 'enabled', True)
    monkeypatch.setitem(settings.triz['verification'], 'analysis_semantic_repairs', 1 if outcome == 'repaired' else 0)
    value = candidate()
    value['user_constraints'][0]['id'] = 'CON-1234abcd'
    corrected = deepcopy(value)
    if outcome != 'accepted':
        value['user_constraints'][0]['statement'] = '모든 금전 보상 인상은 10% 이내'
    review = {'verdict': 'PASS' if outcome == 'accepted' else 'REVISE',
              'per_criterion': [{'id': 'C1', 'score': 1 if outcome == 'accepted' else 0},
                                {'id': 'C2', 'score': 1}, {'id': 'C3', 'score': 1}],
              'revision_instructions': [] if outcome == 'accepted' else ['연봉 상한을 전체 금전 보상으로 확장하지 말라.']}
    responses = [value, review]
    if outcome == 'repaired':
        responses.extend([corrected, {'verdict': 'PASS', 'per_criterion': [
            {'id': 'C1', 'score': 1}, {'id': 'C2', 'score': 1}, {'id': 'C3', 'score': 1}],
            'revision_instructions': []}])
    if outcome != 'rejected':
        from triz.analysis_semantic_gate import RULES
        responses.append({'checks': [{'id': key, 'status': 'PASS', 'reason': 'offline supported cap', 'findings': []}
                                     for key in RULES['R3_CONSTRAINT']]})
    calls = []
    def chat(ctx, **kwargs):
        # No direct USER candidate is committed until the final independent PASS.
        assert state.constraints.model_dump() == before
        calls.append(kwargs)
        return SimpleNamespace(data=responses.pop(0), text='', model='offline',
                               tokens_in=1, tokens_out=1, cost_usd=0, meta={})
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    if outcome != 'rejected':
        nodes._discover_constraints(RunContext(state))
        assert state.constraints.items[-1].source == 'USER' and state.constraints.items[-1].hard
        assert state.constraints.items[-1].id == 'CON-1234abcd'
        assert state.constraints.items[-1].statement == corrected['user_constraints'][0]['statement']
        assert state.steps[-1].status == 'OK'
        if outcome == 'repaired':
            assert [r['verdict'] for r in state.steps[-1].verdicts] == ['REVISE', 'PASS']
    else:
        with pytest.raises(AbortRun):
            nodes._discover_constraints(RunContext(state))
        assert state.constraints.model_dump() == before
        assert state.steps[-1].status == 'FAILED'
    assert len(calls) == {'accepted': 3, 'rejected': 2, 'repaired': 5}[outcome] and calls[1]['tier'] == 'T3'
    assert '현재 연봉의 10% 이내로만 인상 가능' in calls[1]['user']
    assert '인용 문자열 일치만으로 USER 승격하지 않는다' in calls[1]['user']
