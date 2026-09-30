"""Restated costs change available budget without replacing provider journals."""
import pytest
from sqlalchemy import select

from triz import store
from triz.ax import action_runtime, ledger
from triz.ax.contracts import BudgetBusy
from test_budget_interruption_reason import budget_run, spend


def restate(state, adjustments):
    payload = {'version': 'cost-restatement-v1', 'task_adjustments': [
        {'task_id': task['task_id'], 'before_microusd': task['actual'], 'after_microusd': amount}
        for task, amount in adjustments]}
    with ledger.transaction() as conn:
        ledger._event(conn, state.run_id, 'COST_RESTATEMENT_APPLIED', payload)


def saved(task):
    with store.engine.connect() as conn:
        row = dict(conn.execute(select(ledger.tasks).where(ledger.tasks.c.task_id == task['task_id'])).mappings().one())
        attempts = [dict(r) for r in conn.execute(select(ledger.attempts).where(
            ledger.attempts.c.task_id == task['task_id']).order_by(ledger.attempts.c.fence)).mappings()]
    return row, attempts


def settled(state, amount, request=None):
    task = spend(state, amount, request)
    return saved(task)[0]


def scoped_request(node):
    return {'node': node, 'request': {'semantic_episode_id': 'test-cost-episode'},
            'action_context': {'optional': True, 'plan_class': 'INITIAL_SELECTION',
                'semantic_episode_id': 'test-cost-episode', 'action_instance_id': 'test-cost-action'}}


def duplicate_attempt(task):
    _, attempts = saved(task)
    duplicate = dict(attempts[-1], attempt_id=task['task_id'] + '-extra-receipt', fence=2)
    with ledger.transaction() as conn:
        conn.execute(ledger.attempts.insert().values(**duplicate))


def test_budget_and_replay_use_correction_but_keep_original_receipt(budget_run):
    request = {'fixture': 'same paid input'}
    task = settled(budget_run, 5_900_000, request)
    before = saved(task)
    assert ledger.budget(budget_run.run_id)['spent_microusd'] == 5_900_000
    restate(budget_run, [(task, 5_000_000)])
    assert ledger.budget(budget_run.run_id)['spent_microusd'] == 5_000_000
    assert ledger.budget(budget_run.run_id)['remaining_microusd'] == 1_000_000
    replay = ledger.acquire(budget_run.run_id, 0, request, 5_900_000)
    assert replay['cached'] and replay['actual'] == 5_900_000
    assert saved(task) == before


def test_project_admission_and_shortfall_use_effective_spend(budget_run):
    task = settled(budget_run, 5_900_000)
    restate(budget_run, [(task, 5_000_000)])
    new = ledger.acquire(budget_run.run_id, 0, {'node': 'new-work'}, 500_000, minimum_remaining=120_000)
    assert new['status'] == 'RUNNING'
    with pytest.raises(BudgetBusy):
        ledger.acquire(budget_run.run_id, 0, {'node': 'waiting-work'}, 500_000, minimum_remaining=120_000)
    ledger.settle(new, {}, None, status='UNKNOWN')
    with pytest.raises(ledger.BudgetRejected) as caught:
        ledger.acquire(budget_run.run_id, 0, {'node': 'waiting-work'}, 500_000, minimum_remaining=120_000)
    assert caught.value.details['spent_microusd'] == 5_000_000
    assert caught.value.details['reserved_microusd'] == 500_000
    assert caught.value.details['shortfall_microusd'] == 120_000


@pytest.mark.parametrize('scope', ['optional', 'initial_generation'])
def test_scoped_admission_counts_restated_physical_task_once(budget_run, scope):
    task = settled(budget_run, 100_000, scoped_request('paid'))
    duplicate_attempt(task)
    restate(budget_run, [(task, 40_000)])
    ledger.acquire(budget_run.run_id, 0, scoped_request('held'), 20_000)
    limits = {'optional_limit' if scope == 'optional' else 'generation_limit': 150_000}
    assert ledger.acquire(budget_run.run_id, 0, scoped_request('next'), 80_000, **limits)['status'] == 'RUNNING'
    with pytest.raises(ledger.BudgetRejected) as caught:
        ledger.acquire(budget_run.run_id, 0, scoped_request('too-much'), 20_000, **limits)
    assert caught.value.details['scope'] == scope
    assert caught.value.details['spent_microusd'] == 40_000
    assert caught.value.details['reserved_microusd'] == 100_000
    assert caught.value.details['shortfall_microusd'] == 10_000


def test_action_usage_and_optional_commitment_deduplicate_task_receipts(budget_run):
    task = settled(budget_run, 100_000, scoped_request('paid'))
    duplicate_attempt(task)
    before = saved(task)
    # Duplicate journal rows never represent another paid physical task.
    assert action_runtime.usage(budget_run, 'test-cost-action')['actual_microusd'] == 100_000
    assert action_runtime.optional_commitment(budget_run) == 100_000
    restate(budget_run, [(task, 40_000)])
    usage = action_runtime.usage(budget_run, 'test-cost-action')
    assert usage == {'actual_microusd': 40_000, 'usage_status': 'SETTLED',
                     'attempts': 2, 'task_ids': [task['task_id']]}
    assert action_runtime.optional_commitment(budget_run) == 40_000
    assert saved(task) == before


def test_correction_never_converts_unknown_usage_into_free_usage(budget_run):
    known = settled(budget_run, 100_000, scoped_request('paid'))
    task = ledger.acquire(budget_run.run_id, 0, scoped_request('uncertain'), 20_000)
    ledger.settle(task, {}, None, status='UNKNOWN')
    unknown = saved(task)[0]
    restate(budget_run, [(known, 40_000), (unknown, 0)])
    budget = ledger.budget(budget_run.run_id)
    assert budget['spent_microusd'] == 40_000
    assert budget['reserved_microusd'] == 20_000 and budget['unknown_attempts'] == 1
    assert action_runtime.usage(budget_run, 'test-cost-action')['actual_microusd'] is None
    assert action_runtime.optional_commitment(budget_run) == 60_000
    assert saved(task)[0]['actual'] is None
