"""Legacy title corrections are read-only and retain account isolation."""
import json
from sqlalchemy import select, update
from triz import presentation, store, titles
from triz.schema import HumanRequest

BAD = '안녕하세요 · 초전도 · 방식의 개선 과제'
GOOD = '상온-극저온 신호 전달 경로 개선 과제'


def legacy(state, source='structured_fallback'):
    state.raw_query = '안녕하세요, 초전도 방식의 범용 양자 컴퓨터 확장을 연구합니다.'
    state.domain.target_system = '상온-극저온 신호 전달 경로(동축 케이블 및 그 계면)'
    state.scratch.update(title=BAD, title_source=source)
    state.status = 'WAITING_HUMAN'
    state.pending = HumanRequest(kind='CLARIFY', title='조건 확인')
    store.save_state(state)
    store.publish_run(state.run_id, state.user_id)


def test_existing_title_is_corrected_in_lists_detail_notifications_without_writes(state):
    legacy(state)
    before = state.model_dump_json()
    row = lambda items: next(r for r in items if r['run_id'] == state.run_id)
    assert row(store.runs_page(user_id=state.user_id)['items'])['title'] == GOOD
    assert row(store.runs_page(public=True)['items'])['title'] == GOOD
    assert row(store.list_runs(user_id=state.user_id))['title'] == GOOD
    assert row(store.public_runs_list())['title'] == GOOD
    assert row(store.pending_notifications(state.user_id))['project_title'] == GOOD
    assert presentation.view(state)['title'] == GOOD
    assert state.model_dump_json() == before
    assert store.load_state(state.run_id).model_dump_json() == before
    with store.engine.connect() as c:
        assert c.execute(select(store.runs.c.title).where(store.runs.c.run_id == state.run_id)).scalar_one() == BAD
    assert not store.runs_page(user_id='unrelated-title-owner')['items']
    assert not store.pending_notifications('unrelated-title-owner')


def test_known_custom_title_is_never_reinterpreted_as_fallback(state):
    legacy(state, 'custom')
    assert titles.display_title(state) == BAD
    assert store._display_run_title(state.run_id, BAD) == BAD


def test_old_frozen_title_requires_exact_legacy_formatter_match(state):
    legacy(state)
    state.scratch.pop('title_source')
    before = state.model_dump_json()
    assert titles.display_title(state) == GOOD
    assert state.model_dump_json() == before
    state.raw_query = '다른 문제에 대한 기술 설명입니다.'
    assert titles.display_title(state) == BAD


def test_report_copy_corrects_legacy_title_without_rewriting_saved_report(state):
    from triz.report_style import report_state
    from triz.schema import ReportArtifact
    legacy(state)
    state.scratch.pop('title_source')
    state.report = ReportArtifact(markdown='# ' + BAD)
    before = state.model_dump_json()
    assert report_state(state).scratch['title'] == GOOD
    assert state.model_dump_json() == before


def test_library_correction_does_not_hydrate_unrelated_invalid_checkpoint(state, monkeypatch):
    legacy(state)
    payload = state.model_dump(mode='json')
    payload['concepts'] = 'unrelated-invalid-detail'
    with store.engine.begin() as c:
        c.execute(update(store.states).where(store.states.c.run_id == state.run_id)
                  .values(state_json=json.dumps(payload, ensure_ascii=False)))
    monkeypatch.setattr(store, 'load_state', lambda *a: (_ for _ in ()).throw(AssertionError('full checkpoint loaded')))
    row = next(r for r in store.runs_page(user_id=state.user_id)['items'] if r['run_id'] == state.run_id)
    assert row['title'] == GOOD


def test_fallback_title_with_no_greeting_projects_consistently(state):
    legacy(state)
    state.scratch['title'] = '배선 시스템 개선 과제'
    store.save_state(state)
    assert titles.display_title(state) == store._display_run_title(state.run_id, state.scratch['title']) == GOOD


def test_frozen_ax_title_uses_saved_problem_and_preserves_snapshot(state):
    from triz.ax import ledger, report
    from test_ax_full_report import freeze
    from report_design_fixture import example_report
    from triz.report_style import report_state
    frozen = example_report()
    frozen.run_id, frozen.user_id = state.run_id, state.user_id
    frozen.raw_query = '안녕하세요, 초전도 방식의 범용 양자 컴퓨터 확장을 연구합니다.'
    frozen.domain.target_system = '상온-극저온 신호 전달 경로(동축 케이블 및 그 계면)'
    frozen.scratch.update(title=BAD, title_source='structured_fallback')
    freeze(frozen)
    snapshot = ledger.head(frozen.run_id)
    frozen.domain.target_system = '나중에 변경한 다른 시스템'
    frozen.scratch['title'] = '나중에 변경한 정상 제목'
    before = frozen.model_dump_json()
    assert report_state(frozen).scratch['title'] == GOOD
    assert presentation.view(frozen)['title'] == GOOD
    assert report.project(frozen).scratch['title'] == BAD
    assert frozen.model_dump_json() == before
    assert ledger.head(frozen.run_id) == snapshot
