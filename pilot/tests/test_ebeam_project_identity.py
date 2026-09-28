"""Preserve the actual inspection beam when EUV only describes the process."""
from copy import deepcopy
import json

import pytest
from sqlalchemy import select, update

from triz import agent, nodes, presentation, store, titles
from triz.context import RunContext
from triz.schema import ConfirmArtifact, ReportArtifact, SystemCandidate

WRONG = 'EUV 웨이퍼 결함 검출의 조사 에너지 상충 해결'
CORRECT = 'EBEAM 웨이퍼 결함 검출의 조사 에너지 상충 해결'
QUERY = ('초미세 공정(EUV 등)의 수 나노미터 불량을 고해상도 광학계나 '
         'E-beam(전자빔)으로 검출한다. 조사 에너지를 높이면 PR 손상과 차징이 증가한다.')
TARGET = 'E-beam 빔 조사 모듈과 PR 패턴 계면'


@pytest.fixture(autouse=True)
def isolated_title_owner(state):
    # Existing library tests use a 20-row first page and second-resolution
    # timestamps. Keep this module's synthetic runs out of their owner scope.
    state.user_id = 'title-identity-' + state.run_id
    with store.engine.begin() as connection:
        connection.execute(update(store.runs).where(store.runs.c.run_id == state.run_id)
            .values(user_id=state.user_id))


def confirmed(state, source='bootstrap'):
    state.raw_query = QUERY
    state.scratch.update(title=WRONG, title_source=source)
    state.domain.target_system = TARGET
    state.domain.super_system = 'EUV 노광·패터닝 라인'
    state.intake.frame.restated_problem = 'EUV급 PR 패턴의 E-beam 검사에서 해상도와 손상이 상충한다.'
    state.confirm = ConfirmArtifact(user_confirmed=True, chosen_candidate_id='SYS-ebeam',
        candidates=[SystemCandidate(id='SYS-ebeam', name=TARGET)])


@pytest.mark.parametrize('alias', ['EBEAM', 'E-beam', 'e beam', '전자빔', '전자 빔'])
def test_explicit_beam_alias_prevents_unsupported_euv_title_without_model_call(state, monkeypatch, alias):
    state.raw_query = f'{alias} 검사 에너지를 높이면 웨이퍼 PR 손상과 차징이 증가한다.'
    original = state.raw_query
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **k: pytest.fail('Unexpected title model call'))
    assert not titles.valid_title(WRONG, state.raw_query)
    assert titles.ensure_title(RunContext(state), WRONG) == CORRECT
    assert state.raw_query == original


@pytest.mark.parametrize('amendment', [
    'EUV가 아니라 EBEAM입니다.',
    'EBEAM 검사이며 EUV가 아닙니다.',
    'Use E-beam, not EUV.',
])
def test_latest_user_correction_overrides_older_confirmed_technology(state, amendment):
    confirmed(state)
    state.confirm.candidates[0].name = 'EUV 빔 조사 모듈'
    state.confirm.user_amendments = ['EUV 검사 대상', amendment]
    before = state.model_dump(mode='json')
    assert titles.display_title(state) == CORRECT
    assert state.model_dump(mode='json') == before


def test_process_and_beam_in_raw_input_remain_ambiguous_until_target_is_identified(state):
    state.raw_query = QUERY
    state.scratch.update(title=WRONG, title_source='bootstrap')
    state.domain.target_system = ''
    assert titles.display_title(state) == WRONG
    state.domain.target_system = TARGET
    assert titles.display_title(state) == CORRECT


def test_confirmed_beam_wins_process_context_without_rewriting_definition(state):
    confirmed(state)
    original = deepcopy(state.model_dump(mode='json'))
    assert titles.display_title(state) == CORRECT
    titles.refresh_fallback_title(state)
    assert state.scratch['title'] == CORRECT
    assert state.scratch['title_history'] == [dict(previous_title=WRONG, title=CORRECT,
        reason='confirmed_problem_identity')]
    titles.refresh_fallback_title(state)
    assert len(state.scratch['title_history']) == 1
    for key in ('raw_query', 'domain', 'intake', 'confirm', 'analysis', 'constraints'):
        assert state.model_dump(mode='json')[key] == original[key]


@pytest.mark.parametrize('source', ['custom', None])
def test_user_or_unknown_source_title_is_preserved(state, source):
    confirmed(state, source=source)
    before = state.model_dump(mode='json')
    assert titles.display_title(state) == WRONG
    titles.refresh_fallback_title(state)
    assert state.model_dump(mode='json') == before


def test_bootstrap_does_not_replace_an_existing_custom_title(state, monkeypatch):
    confirmed(state, source='custom')
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **k: pytest.fail('Unexpected title model call'))
    assert titles.ensure_title(RunContext(state), CORRECT) == WRONG
    assert state.scratch['title_source'] == 'custom'


def test_title_naming_both_process_and_inspection_beam_is_already_clear(state):
    confirmed(state)
    state.scratch['title'] = 'EUV 웨이퍼의 E-beam 검사 손상 최소화'
    assert titles.display_title(state) == state.scratch['title']


def test_process_only_amendment_does_not_replace_confirmed_inspection_beam(state):
    confirmed(state)
    state.confirm.user_amendments = ['EUV 공정의 패턴 치수는 기존 조건을 유지합니다.']
    assert titles.display_title(state) == CORRECT


def test_euv_optics_problem_is_not_reinterpreted_as_ebeam(state):
    state.raw_query = 'EUV 광학계의 나노 열변형을 줄이며 광학 성능을 유지한다.'
    state.scratch.update(title='EUV 광학계 나노 열변형 억제 방열 메커니즘', title_source='bootstrap')
    state.domain.target_system = 'EUV 광학계'
    assert titles.display_title(state) == state.scratch['title']


def test_s1_refreshes_only_automatic_title_after_extracting_actual_system(state, monkeypatch):
    state.raw_query = QUERY
    state.scratch.update(title=WRONG, title_source='bootstrap')
    result = dict(domain=dict(industry='반도체', target_system=TARGET),
        frame=dict(restated_problem='EUV급 PR 패턴의 E-beam 검사 손상', symptom='PR 손상', confidence=.9),
        constraints=dict(items=[dict(statement='PR 패턴 손상을 방지한다.')]))
    calls = []
    def extract(ctx, **kwargs):
        calls.append(kwargs['node'])
        assert kwargs['vars']['raw_query'] == QUERY
        return deepcopy(result)
    monkeypatch.setattr(agent, 'run_agent', extract)
    nodes.s1_extract(RunContext(state))
    saved = store.load_state(state.run_id)
    assert calls == ['s1_extract']
    assert saved.scratch['title'] == CORRECT
    assert saved.intake.frame.restated_problem == result['frame']['restated_problem']
    assert saved.domain.target_system == TARGET
    assert saved.raw_query == QUERY


@pytest.mark.parametrize(('source', 'expected'), [('bootstrap', CORRECT), ('title_extraction', CORRECT), ('custom', WRONG)])
def test_s2_confirmation_persists_title_grounding_but_keeps_custom_titles(state, monkeypatch, source, expected):
    confirmed(state, source)
    state.confirm.user_confirmed = False
    state.confirm.chosen_candidate_id = ''
    state.domain.target_system = 'EUV급 공정 검사 스테이션'
    state.scratch['resume_payload'] = dict(candidate_id='SYS-ebeam')
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **k: pytest.fail('Confirmation must not call a model'))
    nodes.s2_confirm(RunContext(state))
    saved = store.load_state(state.run_id)
    assert saved.confirm.user_confirmed
    assert saved.domain.target_system == TARGET
    assert saved.scratch['title'] == expected
    assert saved.raw_query == QUERY


def test_list_and_detail_projection_agree_without_full_state_hydration_or_writes(state, monkeypatch):
    confirmed(state)
    store.save_state(state)
    assert presentation.view(state)['title'] == CORRECT
    payload = state.model_dump(mode='json')
    payload['concepts'] = 'unrelated-invalid-detail'
    saved_json = json.dumps(payload, ensure_ascii=False)
    with store.engine.begin() as connection:
        connection.execute(update(store.states).where(store.states.c.run_id == state.run_id).values(state_json=saved_json))
    monkeypatch.setattr(store, 'load_state', lambda *a, **k: pytest.fail('Full checkpoint hydration'))
    row = next(r for r in store.runs_page(user_id=state.user_id)['items'] if r['run_id'] == state.run_id)
    assert row['title'] == CORRECT
    with store.engine.connect() as connection:
        assert connection.execute(select(store.states.c.state_json).where(store.states.c.run_id == state.run_id)).scalar_one() == saved_json
        assert connection.execute(select(store.runs.c.title).where(store.runs.c.run_id == state.run_id)).scalar_one() == WRONG


def test_completed_report_projects_saved_identity_without_changing_snapshot(state):
    from triz.report_style import report_state
    confirmed(state)
    state.report = ReportArtifact(markdown='# ' + WRONG)
    before = state.model_dump(mode='json')
    titles.refresh_fallback_title(state)
    assert report_state(state).scratch['title'] == CORRECT
    assert state.model_dump(mode='json') == before


def test_fallback_cannot_reintroduce_unsupported_euv_term(state):
    state.raw_query = 'EBEAM 조사에 의한 웨이퍼 PR 패턴 손상을 줄인다.'
    state.domain.target_system = 'EUV 웨이퍼 검사'
    state.scratch.update(title='EUV 웨이퍼 검사 개선 과제', title_source='structured_fallback')
    assert titles.fallback_title(state) == 'EBEAM 웨이퍼 검사 개선 과제'
    assert titles.display_title(state) == 'EBEAM 웨이퍼 검사 개선 과제'
