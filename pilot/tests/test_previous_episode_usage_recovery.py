"""Operator consent waives one old block, never settles or redirects its charge."""
import copy
import json
import pytest
from sqlalchemy import select, update
from test_ax_refactor import newrun
from test_unknown_usage_recovery import lost_call
from triz import store
from triz.schema import HumanRequest
from triz.ax import ledger, usage_recovery
from triz.ax.contracts import AccessDenied, Conflict


def next_episode(state, episode='next-semantic-episode'):
    state.scratch['semantic_episode_id'] = episode
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline semantic change')
    store.save_state(state)


def authorize(state, task, **kwargs):
    options = dict(reason='Owner explicitly approved additional cost for this episode',
                   acknowledge_possible_duplicate_charge=True)
    options.update(kwargs)
    return usage_recovery.authorize_previous_episode(state.run_id, state.user_id, task['task_id'],
        state.scratch['execution_epoch'], **options)


def snapshot(task):
    with store.engine.connect() as c:
        return (dict(c.execute(select(ledger.tasks).where(ledger.tasks.c.task_id == task['task_id'])).mappings().one()),
                [dict(r) for r in c.execute(select(ledger.attempts).where(
                    ledger.attempts.c.task_id == task['task_id'])).mappings().all()])


def test_previous_episode_retains_all_accounting_and_never_redirects_old_request(newrun):
    state = newrun(); task, old_request = lost_call(state)
    old_episode = state.scratch['semantic_episode_id']
    next_episode(state)
    before = snapshot(task); budget = ledger.budget(state.run_id)
    assert usage_recovery.blocking_count(state) == 1
    value = authorize(state, task)
    assert value['source_semantic_episode_id'] == old_episode
    assert value['semantic_episode_id'] == state.scratch['semantic_episode_id']
    assert value['actor'] == state.user_id and value['expected_epoch'] == 1
    assert value['retained_reserve_microusd'] == task['reserve']
    assert snapshot(task) == before and ledger.budget(state.run_id) == budget
    assert usage_recovery.blocking_count(state) == 0
    assert ledger.acquire(state.run_id, 1, old_request, task['reserve'])['blocked'] == 'UNKNOWN'
    with store.engine.connect() as c:
        assert usage_recovery.approval(c, state.run_id, task['task_id']) is None
    current = copy.deepcopy(old_request)
    current['action_context']['semantic_episode_id'] = state.scratch['semantic_episode_id']
    current['action_context']['execution_epoch'] = 1
    fresh = ledger.acquire(state.run_id, 1, current, task['reserve'])
    assert fresh['task_id'] != task['task_id'] and not fresh.get('blocked')
    assert not fresh['task_id'].startswith('task-retry-')
    ledger.settle(fresh, {}, None, status='UNKNOWN')
    assert usage_recovery.blocking_count(state) == 1
    assert ledger.budget(state.run_id)['reserved_microusd'] == 2 * task['reserve']


def test_approval_is_idempotent_transport_resumes_work_but_next_episode_blocks(newrun):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    first = authorize(state, task)
    assert authorize(state, task) == first
    with store.engine.connect() as c:
        assert len(c.execute(select(ledger.events).where(ledger.events.c.run_id == state.run_id,
            ledger.events.c.event_type == 'UNKNOWN_PREVIOUS_EPISODE_AUTHORIZED')).all()) == 1
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'transport resume'); store.save_state(state)
    assert usage_recovery.blocking_count(state) == 0
    assert authorize(state, task) == first
    next_episode(state, 'another-semantic-episode')
    assert usage_recovery.blocking_count(state) == 1
    second = authorize(state, task)
    assert second['semantic_episode_id'] != first['semantic_episode_id']
    assert usage_recovery.blocking_count(state) == 0
    assert ledger.budget(state.run_id)['reserved_microusd'] == task['reserve']


@pytest.mark.parametrize('options', [
    {'acknowledge_possible_duplicate_charge':False},
    {'acknowledge_possible_duplicate_charge':1},
    {'reason':''}, {'reason':'  '}, {'reason':None}, {'reason':'x' * 2001},
])
def test_explicit_ack_and_meaningful_reason_required(newrun, options):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    with pytest.raises(ValueError): authorize(state, task, **options)
    assert usage_recovery.blocking_count(state) == 1


def test_owner_epoch_pending_state_and_task_scope_checked_even_after_approval(newrun):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    options = dict(reason='Owner approval', acknowledge_possible_duplicate_charge=True)
    with pytest.raises(AccessDenied):
        usage_recovery.authorize_previous_episode(state.run_id, 'foreign', task['task_id'], 1, **options)
    with pytest.raises(Conflict):
        usage_recovery.authorize_previous_episode(state.run_id, state.user_id, task['task_id'], 0, **options)
    with pytest.raises(Conflict):
        usage_recovery.authorize_previous_episode(state.run_id, state.user_id, 'foreign-task', 1, **options)
    authorize(state, task)
    state.status = 'RUNNING'; store.save_state(state)
    with pytest.raises(Conflict): authorize(state, task)
    state.status = 'INTERRUPTED'; state.pending = HumanRequest(kind='CLARIFY'); store.save_state(state)
    with pytest.raises(Conflict): authorize(state, task)


@pytest.mark.parametrize('current', [None, '', '  ', 'same'])
def test_missing_blank_or_same_episode_fails_closed(newrun, current):
    state = newrun(); task, _ = lost_call(state)
    if current != 'same':
        state.scratch['semantic_episode_id'] = current
        store.save_state(state)
    with pytest.raises(Conflict): authorize(state, task)
    assert usage_recovery.blocking_count(state) == 1


@pytest.mark.parametrize('recorded', [None, ' ', 'conflicting'])
def test_missing_blank_or_conflicting_recorded_source_episode_rejected(newrun, recorded):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    with ledger.transaction() as c:
        row = c.execute(select(ledger.attempts).where(ledger.attempts.c.task_id == task['task_id'])).mappings().one()
        details = json.loads(row['details']); request = details['request']
        if recorded == 'conflicting':
            request['request']['semantic_episode_id'] = 'different-from-action'
        else:
            request['action_context']['semantic_episode_id'] = recorded
        c.execute(update(ledger.attempts).where(ledger.attempts.c.attempt_id == row['attempt_id'])
                  .values(details=json.dumps(details)))
    with pytest.raises(Conflict): authorize(state, task)
    assert usage_recovery.blocking_count(state) == 1


def test_preserved_unknown_and_validation_reserve_still_enforce_budget(newrun):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    original_budget = ledger.budget(state.run_id)['limit_microusd']
    with ledger.transaction() as c:
        c.execute(update(ledger.heads).where(ledger.heads.c.run_id == state.run_id).values(budget=task['reserve']))
    with pytest.raises(Conflict, match='budget'): authorize(state, task)
    with ledger.transaction() as c:
        c.execute(update(ledger.heads).where(ledger.heads.c.run_id == state.run_id).values(budget=original_budget))
    authorize(state, task)
    with pytest.raises(Conflict):
        ledger.acquire(state.run_id, 1, {'node':'new', 'request':{'semantic_episode_id':state.scratch['semantic_episode_id']}},
                       original_budget, minimum_remaining=1)
    assert ledger.budget(state.run_id)['reserved_microusd'] == task['reserve']


def test_reconciled_task_is_not_a_previous_episode_unknown(newrun):
    state = newrun(); task, _ = lost_call(state); next_episode(state)
    ledger.reconcile(task['task_id'], 50, 'verified offline fixture', 'operator')
    with pytest.raises(Conflict): authorize(state, task)


@pytest.mark.parametrize('recorded,corrected,allowed', [(400000, 100, True), (100, 400000, False)])
def test_budget_uses_same_recorded_cost_restatements_as_ledger(newrun, recorded, corrected, allowed):
    from triz.ax import cost_restatements
    state = newrun()
    paid = ledger.acquire(state.run_id, 0, {'node':'completed-fixture'}, 400000)
    ledger.settle(paid, {'data':{}}, recorded)
    task, _ = lost_call(state); next_episode(state)
    with ledger.transaction() as c:
        ledger._event(c, state.run_id, cost_restatements.EVENT,
            dict(version=cost_restatements.VERSION,
                 task_adjustments=[dict(task_id=paid['task_id'], after_microusd=corrected)]))
        hold = json.loads(ledger._head(c, state.run_id)['bundle'])['limits']['validation_reserve_microusd']
        c.execute(update(ledger.heads).where(ledger.heads.c.run_id == state.run_id)
                  .values(budget=2 * task['reserve'] + hold + 1000))
    before = ledger.budget(state.run_id)
    if allowed:
        authorize(state, task)
        assert usage_recovery.blocking_count(state) == 0
    else:
        with pytest.raises(Conflict, match='budget'): authorize(state, task)
        assert usage_recovery.blocking_count(state) == 1
    assert ledger.budget(state.run_id) == before
