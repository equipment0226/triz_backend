"""Explicit recovery must preserve the old UNKNOWN reserve and cap retries."""
import pytest
from sqlalchemy import select
from test_ax_refactor import newrun
from triz import store
from triz.ax import ledger
from triz.ax.contracts import Conflict, AccessDenied


def lost_call(state):
    request = dict(node='s5_track_h', request={'user':'same exact frozen request'},
        action_context=dict(semantic_episode_id=state.scratch['semantic_episode_id'], action_instance_id='original-h',
            execution_epoch=state.scratch['execution_epoch'], input_snapshot_id=state.scratch['ax_snapshot_id'],
            ticket={'input_snapshot_id':state.scratch['ax_snapshot_id']}))
    task = ledger.acquire(state.run_id, state.scratch['execution_epoch'], request, 133379)
    ledger.settle(task, {'error':'worker_lost'}, None, status='UNKNOWN')
    state.status = 'INTERRUPTED'; store.save_state(state)
    return task, request


def test_authorized_retry_keeps_unknown_reserve_and_reuses_completed_child(newrun):
    from triz.ax import usage_recovery
    state = newrun(); task, request = lost_call(state)
    assert ledger.acquire(state.run_id, 0, request, 133379)['blocked'] == 'UNKNOWN'
    approval = usage_recovery.authorize(state.run_id, state.user_id, task['task_id'], 0,
        acknowledge_possible_duplicate_charge=True)
    child = ledger.acquire(state.run_id, 0, request, 133379)
    assert child['task_id'] != task['task_id'] and not child['cached']
    assert ledger.budget(state.run_id)['reserved_microusd'] == 266758
    ledger.settle(child, {'data':{'applications':[]}}, 10000)
    cached = ledger.acquire(state.run_id, 0, request, 133379)
    assert cached['cached'] and cached['task_id'] == child['task_id']
    assert ledger.budget(state.run_id)['reserved_microusd'] == 133379
    assert ledger.budget(state.run_id)['spent_microusd'] == 10000
    assert usage_recovery.blocking_count(state) == 0
    with store.engine.connect() as c:
        old = c.execute(select(ledger.tasks).where(ledger.tasks.c.task_id == task['task_id'])).mappings().one()
    assert old['status'] == 'UNKNOWN' and old['actual'] is None
    assert approval['retained_reserve_microusd'] == 133379


def approve(state, task):
    from triz.ax.usage_recovery import authorize
    return authorize(state.run_id, state.user_id, task['task_id'], state.scratch['execution_epoch'],
                     acknowledge_possible_duplicate_charge=True)


def test_no_ack_foreign_owner_stale_epoch_and_task_are_rejected(newrun):
    from triz.ax.usage_recovery import authorize
    state = newrun(); task, request = lost_call(state)
    with pytest.raises(ValueError): authorize(state.run_id, state.user_id, task['task_id'], 0)
    with pytest.raises(AccessDenied): authorize(state.run_id, 'foreign', task['task_id'], 0, acknowledge_possible_duplicate_charge=True)
    with pytest.raises(Conflict): authorize(state.run_id, state.user_id, task['task_id'], 1, acknowledge_possible_duplicate_charge=True)
    with pytest.raises(Conflict): authorize(state.run_id, state.user_id, 'foreign-task', 0, acknowledge_possible_duplicate_charge=True)
    assert ledger.acquire(state.run_id, 0, request, 133379)['blocked'] == 'UNKNOWN'


def test_duplicate_approval_and_retry_epoch_are_idempotent(newrun):
    from triz.ax import usage_recovery
    state = newrun(); task, request = lost_call(state)
    assert approve(state, task) == approve(state, task)
    state.scratch['execution_epoch'] += 1; ledger.advance_epoch(state, 'resume')
    request['action_context']['execution_epoch'] = 1
    request['action_context']['decision_id'] = 'audit-only'
    child = ledger.acquire(state.run_id, 1, request, 133379)
    ledger.settle(child, {'data':{'ok':True}}, 100)
    assert ledger.acquire(state.run_id, 1, request, 133379)['cached']
    assert usage_recovery.blocking_count(state) == 0
    assert ledger.budget(state.run_id)['reserved_microusd'] == 133379


def test_second_unknown_retry_is_blocked_and_both_reserves_remain(newrun):
    from triz.ax import usage_recovery
    state = newrun(); task, request = lost_call(state); approve(state, task)
    child = ledger.acquire(state.run_id, 0, request, 133379)
    ledger.settle(child, {'error':'lost again'}, None, status='UNKNOWN')
    assert ledger.acquire(state.run_id, 0, request, 133379)['blocked'] == 'UNKNOWN'
    assert usage_recovery.blocking_count(state) == 1
    with pytest.raises(Conflict): approve(state, child)
    assert ledger.budget(state.run_id)['reserved_microusd'] == 266758
    status = usage_recovery.describe(state.run_id, state.user_id)
    assert len(status['items']) == 1 and not status['items'][0]['can_authorize']


def test_cap_and_approved_reservation_limit_are_enforced(newrun):
    from sqlalchemy import update
    state = newrun(); task, request = lost_call(state)
    with ledger.transaction() as c:
        c.execute(update(ledger.heads).where(ledger.heads.c.run_id == state.run_id).values(budget=200000))
    with pytest.raises(Conflict, match='예산'): approve(state, task)
    with ledger.transaction() as c:
        c.execute(update(ledger.heads).where(ledger.heads.c.run_id == state.run_id).values(budget=2000000))
    approve(state, task)
    with pytest.raises(Conflict, match='예약 한도'): ledger.acquire(state.run_id, 0, request, 133380)
    assert ledger.budget(state.run_id)['reserved_microusd'] == 133379


def test_late_original_settlement_does_not_lose_authorized_child(newrun):
    state = newrun(); task, request = lost_call(state); approve(state, task)
    state.scratch['execution_epoch'] += 1; ledger.advance_epoch(state, 'resume')
    child = ledger.acquire(state.run_id, 1, request, 133379)
    ledger.settle(child, {'data':{'recovered':True}}, 100)
    with pytest.raises(Conflict): ledger.settle(task, {'data':{'late':True}}, 50)
    cached = ledger.acquire(state.run_id, 1, request, 133379)
    assert cached['cached'] and cached['result']['data'] == {'recovered':True}
    assert ledger.budget(state.run_id)['spent_microusd'] == 150


def test_reconciled_usage_updates_attempt_and_can_be_explicitly_retried(newrun):
    import json
    state = newrun(); task, request = lost_call(state)
    ledger.reconcile(task['task_id'], 50, 'verified provider record', 'operator')
    with store.engine.connect() as c:
        attempt = c.execute(select(ledger.attempts).where(ledger.attempts.c.task_id == task['task_id'])).mappings().one()
    assert attempt['status'] == 'RECONCILED' and json.loads(attempt['details'])['actual_microusd'] == 50
    assert ledger.acquire(state.run_id, 0, request, 133379)['blocked'] == 'RECONCILED'
    approve(state, task)
    assert ledger.acquire(state.run_id, 0, request, 133379)['task_id'].startswith('task-retry-')


def test_api_requires_explicit_ack_and_retains_owner_scope(newrun):
    from fastapi.testclient import TestClient
    from api.main import app
    state = newrun(); task, _ = lost_call(state)
    client = TestClient(app)
    path = f'/api/runs/{state.run_id}/ax/usage-recovery'
    assert client.get(path).status_code == 200
    assert client.post(path, json={'task_id':task['task_id'], 'expected_epoch':0}).status_code == 422
    approved = client.post(path, json={'task_id':task['task_id'], 'expected_epoch':0,
        'acknowledge_possible_duplicate_charge':True})
    assert approved.status_code == 200
    foreign = newrun(user='another-owner'); lost_call(foreign)
    assert client.get(f'/api/runs/{foreign.run_id}/ax/usage-recovery').status_code == 404


def test_stage_preflight_only_unblocks_after_explicit_approval(newrun, monkeypatch):
    from triz import pipeline
    from triz.ax import usage_recovery
    state = newrun(); task, request = lost_call(state)
    state.control.stage_index = 0
    invoked = []
    def stage(ctx):
        invoked.append(True)
        child = ledger.acquire(state.run_id, ctx.state.scratch['execution_epoch'], request, 133379)
        ledger.settle(child, {'data':{'ok':True}}, 100)
    monkeypatch.setattr(pipeline, 'PIPELINE', [('s5_solve', 'Solve', stage)])
    state.status = 'RUNNING'; store.save_state(state)
    assert pipeline.execute_stage(state.run_id, 0)['status'] == 'INTERRUPTED'
    assert invoked == []
    approve(state, task)
    state = store.load_state(state.run_id); state.status = 'RUNNING'; store.save_state(state)
    assert pipeline.execute_stage(state.run_id, 0)['status'] == 'COMPLETED'
    assert invoked == [True] and ledger.budget(state.run_id)['unknown_attempts'] == 1


def test_missing_semantic_episode_cannot_authorize_legacy_request(newrun):
    from triz.ax import usage_recovery
    state = newrun()
    task = ledger.acquire(state.run_id, 0, {'node':'legacy'}, 133379)
    ledger.settle(task, {}, None, status='UNKNOWN')
    state.scratch.pop('semantic_episode_id', None)
    state.status = 'INTERRUPTED'; store.save_state(state)
    with pytest.raises(Conflict): approve(state, task)
    assert usage_recovery.blocking_count(state) == 1
    assert not usage_recovery.describe(state.run_id, state.user_id)['items'][0]['can_authorize']


def test_expired_lease_updates_task_and_attempt_together(newrun):
    state = newrun()
    task = ledger.acquire(state.run_id, 0, {'node':'expired'}, 133379, lease_seconds=-1)
    assert ledger.acquire(state.run_id, 0, {'node':'expired'}, 133379)['blocked'] == 'UNKNOWN'
    with store.engine.connect() as c:
        assert c.execute(select(ledger.attempts.c.status).where(ledger.attempts.c.task_id == task['task_id'])).scalar_one() == 'UNKNOWN'


@pytest.mark.parametrize('retry_status', ['COMPLETED', 'UNKNOWN'])
def test_v3_stage_call_recovers_old_epoch_key_without_losing_reserve(newrun, monkeypatch, retry_status):
    from triz.ax import usage_recovery
    state = newrun()
    request = dict(node='s3_constraints', decision_id=None,
        request={'user':'exact frozen stage request','semantic_episode_id':state.scratch['semantic_episode_id']})
    # Record the actual pre-fix epoch-based journal format in the isolated DB.
    with monkeypatch.context() as prior:
        prior.setattr(usage_recovery, 'stage_request_identity', lambda request: None)
        task = ledger.acquire(state.run_id, 0, request, 99044)
    ledger.settle(task, {}, None, status='UNKNOWN')
    state.status='INTERRUPTED';store.save_state(state)
    assert usage_recovery.describe(state.run_id,state.user_id)['items'][0]['can_authorize']
    state.scratch['execution_epoch']=1;ledger.advance_epoch(state,'fixture resume');store.save_state(state)
    assert ledger.acquire(state.run_id,1,request,99044)['blocked']=='UNKNOWN'
    approved=approve(state,task)
    child=ledger.acquire(state.run_id,1,request,99044)
    assert child['task_id']==approved['retry_task_id']
    assert ledger.budget(state.run_id)['reserved_microusd']==198088
    ledger.settle(child,{'fixture':True},10 if retry_status=='COMPLETED' else None,status=retry_status)
    state.scratch['execution_epoch']=2;ledger.advance_epoch(state,'fixture transport retry');store.save_state(state)
    replay=ledger.acquire(state.run_id,2,request,99044)
    assert replay['task_id']==child['task_id']
    if retry_status=='COMPLETED':
        assert replay['cached'] and ledger.budget(state.run_id)['reserved_microusd']==99044
    else:
        assert replay['blocked']=='UNKNOWN'
        assert not usage_recovery.describe(state.run_id,state.user_id)['items'][0]['can_authorize']
        assert ledger.budget(state.run_id)['reserved_microusd']==198088


def test_conflicting_recorded_episode_cannot_authorize_recovery():
    from triz.ax.usage_recovery import request_episode, stage_request_identity
    request={'action_context':{'semantic_episode_id':'old'},'request':{'semantic_episode_id':'new'}}
    assert request_episode(request) is None
    assert stage_request_identity(request) is None
    assert request_episode({'request':'legacy text'}) is None


def test_concurrent_acquire_allocates_only_one_retry(newrun):
    from concurrent.futures import ThreadPoolExecutor
    state = newrun(); task, request = lost_call(state); approve(state, task)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:ledger.acquire(state.run_id, 0, request, 133379), range(2)))
    assert len({r['task_id'] for r in results}) == 1
    assert sum(r.get('blocked') == 'RUNNING' for r in results) == 1
    assert ledger.budget(state.run_id)['reserved_microusd'] == 266758


def test_gateway_retries_only_after_consent_then_replays_without_provider(newrun, monkeypatch):
    from triz import llm
    from triz.context import RunContext, UsageUncertain
    from triz.ax import gateway
    from triz.ax.action_runtime import active_action
    state = newrun(); calls = []
    def provider(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise TimeoutError('response lost')
        return llm.LLMResult(data={'applications':[{'effect':'fixture'}]}, cost_usd=.00001)
    monkeypatch.setattr(llm, 'chat_json', provider)
    token = active_action.set(dict(semantic_episode_id=state.scratch['semantic_episode_id'],
        action_instance_id='h-fixture', ticket={'model_role':'TRACK_SOLVE'}))
    try:
        invoke = lambda: gateway.chat(RunContext(state), system='frozen', user='request', _node='s5_track_h')
        with pytest.raises(TimeoutError): invoke()
        with pytest.raises(UsageUncertain): invoke()
        assert len(calls) == 1
        held = ledger.budget(state.run_id)['reserved_microusd']
        with store.engine.connect() as c:
            task = dict(c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == state.run_id)).mappings().one())
        state.status = 'INTERRUPTED'; store.save_state(state); approve(state, task)
        assert invoke().data['applications']
        assert invoke().meta['durable_replay']
        assert len(calls) == 2 and calls[0] == calls[1]
        assert ledger.budget(state.run_id)['reserved_microusd'] == held
        assert ledger.budget(state.run_id)['spent_microusd'] == 10
    finally:
        active_action.reset(token)
