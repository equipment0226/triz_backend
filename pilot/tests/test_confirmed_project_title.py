"""Confirmed system boundaries govern automatic titles, including frozen reports."""
import json

import pytest
from sqlalchemy import select, update

from triz import presentation, store, titles
from triz.schema import ConfirmArtifact, SystemCandidate


BAD = '안녕하세요 · 초전도 · 방식의 개선 과제'
GOOD = '상온-극저온 신호 전달 경로 개선 과제'
CHOSEN = '상온-극저온 신호 전달 경로(동축 케이블 및 그 계면)'
LONG_DOMAIN = '상온 제어·측정 장비와 15 mK 큐빗 칩 사이의 신호 전달 및 열 차단 시스템'


def confirmed_boundary(state):
    state.raw_query = '안녕하세요, 초전도 방식의 범용 양자 컴퓨터 확장을 연구합니다.'
    state.domain.target_system = LONG_DOMAIN
    state.scratch.update(title=BAD, title_source='structured_fallback')
    state.confirm = ConfirmArtifact(
        user_confirmed=True,
        chosen_candidate_id='SYS-selected',
        candidates=[SystemCandidate(id='SYS-unselected', name='선택하지 않은 전체 장비'),
                    SystemCandidate(id='SYS-selected', name=CHOSEN)],
    )


def test_explicitly_confirmed_selected_system_wins_long_initial_domain(state):
    confirmed_boundary(state)
    before = state.model_dump(mode='json')
    assert titles.fallback_title(state) == GOOD
    assert titles.display_title(state) == GOOD
    assert state.model_dump(mode='json') == before


@pytest.mark.parametrize(('confirmed', 'selected_id'), [
    (False, 'SYS-selected'),
    (True, ''),
    (True, 'SYS-missing'),
])
def test_candidate_needs_explicit_confirmation_and_exact_selected_id(state, confirmed, selected_id):
    confirmed_boundary(state)
    state.domain.target_system = '초기 배선 시스템'
    state.confirm.user_confirmed = confirmed
    state.confirm.chosen_candidate_id = selected_id
    assert titles.fallback_title(state) == '초기 배선 시스템 개선 과제'


def test_empty_confirmed_selected_name_falls_back_to_structured_domain(state):
    confirmed_boundary(state)
    state.domain.target_system = '초기 배선 시스템'
    state.confirm.candidates[1].name = ''
    assert titles.fallback_title(state) == '초기 배선 시스템 개선 과제'


def test_frozen_report_uses_frozen_confirmation_without_live_overrides(state):
    from triz.ax import ledger, report
    from triz.report_style import report_state
    from test_ax_full_report import freeze
    from report_design_fixture import example_report

    frozen = example_report()
    frozen.run_id, frozen.user_id = state.run_id, state.user_id
    confirmed_boundary(frozen)
    freeze(frozen)
    head = ledger.head(frozen.run_id)
    frozen.domain.target_system = '나중에 변경한 다른 장비'
    frozen.confirm.candidates[1].name = '나중에 변경한 다른 확정 범위'
    frozen.scratch['title'] = '나중에 변경한 정상 제목'
    before = frozen.model_dump(mode='json')

    assert report.project(frozen).domain.target_system == LONG_DOMAIN
    assert report_state(frozen).scratch['title'] == GOOD
    assert presentation.view(frozen)['title'] == GOOD
    assert frozen.model_dump(mode='json') == before
    assert ledger.head(frozen.run_id) == head


def test_compact_list_projection_uses_confirmation_without_loading_full_checkpoint(state, monkeypatch):
    confirmed_boundary(state)
    store.save_state(state)
    payload = state.model_dump(mode='json')
    payload['concepts'] = 'unrelated-invalid-detail'
    saved_json = json.dumps(payload, ensure_ascii=False)
    with store.engine.begin() as c:
        c.execute(update(store.states).where(store.states.c.run_id == state.run_id)
                  .values(state_json=saved_json))

    def no_hydration(*args, **kwargs):
        raise AssertionError('Title projection loaded the full checkpoint')

    monkeypatch.setattr(store, 'load_state', no_hydration)
    row = next(item for item in store.runs_page(user_id=state.user_id)['items']
               if item['run_id'] == state.run_id)
    assert row['title'] == GOOD
    assert store._display_run_title(state.run_id, BAD) == GOOD
    with store.engine.connect() as c:
        assert c.execute(select(store.states.c.state_json)
                         .where(store.states.c.run_id == state.run_id)).scalar_one() == saved_json
        assert c.execute(select(store.runs.c.title)
                         .where(store.runs.c.run_id == state.run_id)).scalar_one() == BAD
