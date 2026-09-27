"""Production regressions: null ARIZ checkpoints and isolated list reads."""
import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from triz import agent, idea_consolidation as merge, llm, pipeline, store
from triz.context import RunContext
from triz.schema import ARIZRun, GlobalState, RawIdea


def overwrite_checkpoint(state, **changes):
    payload = state.model_dump(mode='json')
    payload.update(changes)
    with store.engine.begin() as c:
        c.execute(update(store.states).where(store.states.c.run_id == state.run_id)
                  .values(state_json=json.dumps(payload)))


def test_legacy_null_ariz_is_readable_without_fabricating_reason(state):
    payload = state.model_dump(mode='json')
    payload['solve']['ariz'] = {'unresolved_reason': None}
    overwrite_checkpoint(state, solve=payload['solve'])
    loaded = store.load_state(state.run_id)
    assert loaded.solve.ariz.unresolved_reason == ''
    assert ARIZRun(unresolved_reason=None).unresolved_reason == ''
    store.save_state(loaded)
    assert GlobalState.model_validate_json(loaded.model_dump_json()).solve.ariz.unresolved_reason == ''


def test_corrupt_detail_cannot_break_concurrent_owner_public_and_notification_lists(monkeypatch):
    from api.main import app
    from triz.settings import settings
    monkeypatch.setattr(settings, 'app_token', 'test-list')
    monkeypatch.setattr(settings, 'require_user_auth', True)
    account = store.create_session('list-failure-owner', 'owner@example.invalid', 'Owner')
    owner = account['user']['id']
    states = [pipeline.create_run('Concurrent library project', user_id=owner) for _ in range(2)]
    for s in states:
        s.status = 'INTERRUPTED'
        s.scratch['retry_notification_id'] = 'notice:' + s.run_id
        store.save_state(s)
        store.publish_run(s.run_id, owner)
        # A separate, unrecognized corruption must not enter the list path.
        overwrite_checkpoint(s, concepts='invalid unrelated detail', steps=['invalid history'])
    monkeypatch.setattr(store, 'load_state', lambda *a: pytest.fail('List loaded a full checkpoint'))
    headers = {'X-TRIZ-APP-TOKEN': 'test-list', 'X-TRIZ-SESSION': account['token']}
    paths = ['/api/runs?page=1', '/api/public/runs?page=1&search=Concurrent', '/api/notifications']
    # No lifespan: recovery is tested separately and should not run paid work.
    def request(path):
        response = TestClient(app).get(path, headers=headers)
        assert response.status_code == 200, response.text
        return path, response.json()
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(request, paths * 3))
    expected = {s.run_id for s in states}
    for path, data in responses:
        rows = data if path.endswith('notifications') else data['items']
        assert {row['run_id'] for row in rows} == expected
        assert all('state_json' not in row and 'user_id' not in row for row in rows)
    other = store.create_session('list-other', 'other@example.invalid', 'Other')
    headers['X-TRIZ-SESSION'] = other['token']
    assert TestClient(app).get('/api/runs?page=1', headers=headers).json()['total'] == 0


def test_bad_reference_checkpoint_falls_back_without_hiding_row(state):
    state.scratch['title'] = 'CPT-abcdef12 project'
    state.status = 'INTERRUPTED'
    store.save_state(state)
    overwrite_checkpoint(state, concepts='invalid')
    result = store.runs_page(search='CPT-abcdef12', user_id=state.user_id)
    row = next(r for r in result['items'] if r['run_id'] == state.run_id)
    assert 'CPT-abcdef12' not in row['title']


def test_invalid_checkpoint_does_not_block_recovery_of_another_run(monkeypatch):
    invalid = pipeline.create_run('Invalid recovery checkpoint')
    healthy = pipeline.create_run('Healthy orphan checkpoint')
    for s in (invalid, healthy):
        s.status = 'RUNNING'
        s.scratch['execution_stage_active'] = 's5_solve'
        store.save_state(s)
    overwrite_checkpoint(invalid, concepts='unrecoverable fixture')
    recovered = pipeline.recover_orphans()
    assert healthy.run_id in recovered
    assert store.load_state(healthy.run_id).status == 'INTERRUPTED'
    with store.engine.connect() as c:
        assert c.execute(select(store.runs.c.status).where(store.runs.c.run_id == invalid.run_id)).scalar_one() == 'RUNNING'


def test_grouped_deferrals_expand_without_dropping_or_reassigning_ids():
    raw = {'ideas': [{'keep_ids': ['A'], 'selection_reason': 'Directly addresses cause'}],
           'deferred': [{'keep_ids': ['B', 'C'], 'reason': 'Both require unavailable sensing'}]}
    original = copy.deepcopy(raw)
    normalized = merge.normalize_partition(raw)
    assert raw == original
    assert [r['keep_ids'] for r in normalized['deferred']] == [['B'], ['C']]
    assert not merge.check_partition(normalized, ['A', 'B', 'C'])
    normalized['ideas'].append({'keep_ids': ['A'], 'selection_reason': 'another role'})
    errors = merge.check_partition(normalized, ['A', 'B', 'C'])
    assert any('A (이전 그룹 1, 현재 그룹 2)' in e for e in errors)


def test_actual_merge_repairs_over_limit_and_cross_group_duplicates_before_commit(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id=f'I{i}', idea=f'Independent mechanism {i}') for i in range(21)]
    state.scratch['stage_key'] = 's5_solve'
    state.control.injected_agents = {'stage:s5_solve': [{'role_name': 'Old request', 'instruction': 'Many ideas please'}]}
    ids = [i.id for i in state.solve.raw_ideas]
    valid = {'ideas': [{'keep_ids': [i], 'selection_reason': 'Fits observed cause and resources'} for i in ids[-10:]],
             'deferred': [{'keep_ids': ids[:-10], 'reason': 'Needs unavailable actuation resources'}]}
    duplicate = copy.deepcopy(valid)
    duplicate['ideas'][-1]['keep_ids'].append(ids[-2])
    duplicate['ideas'][-1]['merge_reason'] = 'Same intervention conditions'
    outputs = [{'ideas': [{'keep_ids': [i]} for i in ids]}, duplicate, valid]
    requests = []
    def chat(ctx, **kw):
        requests.append(kw)
        assert len(state.solve.raw_ideas) == 21  # No partial commit or hard clipping.
        return llm.LLMResult(data=copy.deepcopy(outputs.pop(0)), model='offline')
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    monkeypatch.setattr(agent, 'verify_artifact', lambda *a, **kw: {'verdict': 'PASS'})
    merge.consolidate(RunContext(state))
    assert len(requests) == 3 and len(state.solve.raw_ideas) == 10
    assert '현재 21개' in requests[1]['user']
    assert 'I19 (이전 그룹 9, 현재 그룹 10)' in requests[2]['user']
    assert requests[0]['user'].rfind(merge.CONSOLIDATION_CONTRACT) > requests[0]['user'].find('Many ideas please')
    record = state.scratch['idea_consolidation']
    assert len(record['source_ideas']) == 21 and len(record['deferred']) == 11
    assert record['coverage_complete']
