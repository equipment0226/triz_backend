"""Price corrections affect future cost labels, never historical observations."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from test_feedback_candidate_versions import reviewed_episode, final
from test_unified_feedback_adaptive import adaptive_run, newrun
from test_unified_feedback_learning import isolated_learning_database
from triz import store
from triz.ax import ledger, learning_outcomes as outcomes, registry, worker
from triz.ax.action_runtime import episode
from triz.ax.contracts import now


def snapshot(*tables):
    with store.engine.connect() as conn:
        return {
            table.name: [dict(row) for row in conn.execute(
                select(table).order_by(*table.primary_key.columns)).mappings()]
            for table in tables
        }


def add_correction(state, tasks, timestamp, monkeypatch, *, amount=None):
    adjustments = [dict(task_id=task['task_id'], before_microusd=task['actual'],
                        after_microusd=amount if amount is not None else task['actual'] // 2)
                   for task in tasks]
    payload = dict(version='cost-restatement-v1', task_adjustments=adjustments)
    with monkeypatch.context() as clock:
        clock.setattr(ledger, 'now', lambda: timestamp)
        with ledger.transaction() as conn:
            event_id = ledger._event(conn, state.run_id, 'COST_RESTATEMENT_APPLIED', payload)
    return dict(event_id=event_id, run_id=state.run_id,
                event_type='COST_RESTATEMENT_APPLIED', payload=payload, created_at=timestamp)


def later(timestamp):
    return (datetime.fromisoformat(timestamp) + timedelta(seconds=1)).isoformat()


def manifests(cutoff):
    return (outcomes.q_dataset('local', 'local', cutoff, include_synthetic=True),
            outcomes.effect_dataset('local', 'local', cutoff, include_synthetic=True))


def test_v5_restatement_changes_only_cost_after_its_recorded_cutoff(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    assert final(state, candidate, 5, 'saved-final-score')
    cutoff = now()
    original_q, original_effect = manifests(cutoff)
    assert original_q['feature_schema'] == 'ax-state-action-v5'
    assert len(original_q['samples']) == 2 and len(original_effect['samples']) == 1
    original_terminal = next(sample for sample in original_q['samples'] if sample['terminal'])
    quality = original_terminal['dimensions']['terminal_outcome']
    assert quality['masks'] == dict(concept_quality=True, user_utility=True)
    assert quality['concept_quality'] == quality['user_utility'] == 1

    # Read the physical task costs once, rather than counting attempt receipts.
    originals = snapshot(ledger.tasks, ledger.attempts, ledger.decisions, ledger.events)
    tasks = originals[ledger.tasks.name]
    assert tasks and all(task['actual'] > 0 for task in tasks)
    correction_at = later(cutoff)
    add_correction(state, tasks, correction_at, monkeypatch)

    # A later price revision cannot leak into an older training cutoff.
    assert manifests(cutoff) == (original_q, original_effect)
    revised_q, revised_effect = manifests(correction_at)
    assert revised_effect['samples'] == original_effect['samples']
    originals_by_id = {sample['decision_id']: sample for sample in original_q['samples']}
    corrected = {task['task_id']: task['actual'] // 2 for task in tasks}
    coefficient = state.scratch['ax_bundle']['run_contract']['feedback_settings']['lambda_cost']
    budget = ledger.head(state.run_id)['budget']
    changed = 0
    for revised in revised_q['samples']:
        original = originals_by_id[revised['decision_id']]
        expected_cost = sum(corrected[task_id] for task_id in original['dimensions']['task_ids'])
        expected_penalty = coefficient * expected_cost / budget
        assert revised['dimensions']['actual_microusd'] == expected_cost
        assert revised['dimensions']['normalized_cost'] == pytest.approx(expected_penalty)
        penalty_delta = original['dimensions']['normalized_cost'] - expected_penalty
        assert revised['reward'] - original['reward'] == pytest.approx(penalty_delta)
        changed += penalty_delta > 0
        assert revised['reward_revision'] != original['reward_revision']
        assert revised['available_at'] == correction_at
        assert revised['dimensions']['terminal_outcome'] == original['dimensions']['terminal_outcome']
        for key in ('features', 'actions', 'permitted', 'executed_index', 'review_ids',
                    'terminal', 'maturity', 'selection_mode', 'next_features', 'next_actions'):
            assert revised[key] == original[key]
    assert changed > 0
    assert sum(sample['dimensions']['actual_microusd'] for sample in revised_q['samples']) == sum(corrected.values())

    # Dataset projection leaves original costs, receipts, choices and reviews intact.
    after = snapshot(ledger.tasks, ledger.attempts, ledger.decisions, ledger.events)
    for table in (ledger.tasks, ledger.attempts, ledger.decisions):
        assert after[table.name] == originals[table.name]
    assert [event for event in after[ledger.events.name]
            if event['event_type'] != 'COST_RESTATEMENT_APPLIED'] == originals[ledger.events.name]


def test_restatement_does_not_make_unsettled_usage_a_free_learning_sample(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    assert final(state, candidate, 5, 'saved-final-score')
    task = ledger.acquire(state.run_id, ledger.head(state.run_id)['epoch'],
        dict(node='uncertain-usage-fixture', request=dict(semantic_episode_id=episode(state))), 10)
    ledger.settle(task, {}, None, status='UNKNOWN')
    cutoff = now()
    original_q, original_effect = manifests(cutoff)
    assert original_q['samples'] == original_effect['samples'] == []
    assert original_q['excluded']['unsettled_usage'] == 1
    with store.engine.connect() as conn:
        unknown = dict(conn.execute(select(ledger.tasks).where(
            ledger.tasks.c.task_id == task['task_id'])).mappings().one())
    correction_at = later(cutoff)
    add_correction(state, [unknown], correction_at, monkeypatch, amount=0)
    revised_q, revised_effect = manifests(correction_at)
    assert revised_q['samples'] == revised_effect['samples'] == []
    assert revised_q['excluded']['unsettled_usage'] == 1
    assert manifests(cutoff) == (original_q, original_effect)
    with store.engine.connect() as conn:
        assert conn.execute(select(ledger.tasks.c.actual).where(
            ledger.tasks.c.task_id == task['task_id'])).scalar_one() is None


def test_price_correction_does_not_queue_training_or_publish_a_model(adaptive_run, monkeypatch):
    state, _ = reviewed_episode(adaptive_run, monkeypatch)
    tables = (worker.queue, worker.task_queue, registry.versions,
              registry.pointers, registry.task_pointers, registry.audit)
    original = snapshot(*tables)
    tasks = snapshot(ledger.tasks)[ledger.tasks.name]
    correction = add_correction(state, tasks, later(now()), monkeypatch)
    with ledger.transaction() as conn:
        worker.consume(conn, correction)
    assert snapshot(*tables) == original
