"""A resumed merge keeps one explicitly approved retry and its original debt."""
import copy
import json

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from triz import llm, nodes, store
from triz.ax import gateway, ledger, runtime, usage_recovery
from triz.ax.action_runtime import executing
from triz.ax.contracts import ActionTicket
from triz.context import RunContext
from triz.schema import RawIdea
from triz.settings import settings


def journal(state):
    with store.engine.connect() as connection:
        return {
            table.name: {row[key]: dict(row) for row in connection.execute(
                select(table).where(table.c.run_id == state.run_id)).mappings()}
            for table, key in ((ledger.tasks, 'task_id'), (ledger.attempts, 'attempt_id'))
        }


def next_transport_epoch(state):
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline continuation fixture')
    state.status = 'RUNNING'
    ledger.capture(state, {}, runtime.DEPENDENCIES, 'stage_read_set')


@pytest.mark.parametrize('explicit_snapshot', [False, True])
@pytest.mark.parametrize('with_coherence', [False, True])
def test_resumed_merge_uses_approved_child_once_and_preserves_unknown_receipt(
        newrun, monkeypatch, explicit_snapshot, with_coherence):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    state = newrun()
    state.scratch['stage_key'] = 's5_solve'
    state.control.current_stage = 'S5_SOLVE'
    state.solve.raw_ideas = [RawIdea(id='MERGE-SOURCE', title='Recorded source',
                                    idea='Keep the existing mechanism and conditions')]
    if not with_coherence:
        ledger.capture(state, {}, runtime.DEPENDENCIES, 'offline fixture without coherence',
                       invalidated=['coherence'])
    original_members = copy.deepcopy(state.scratch['ax_members'])
    original_snapshot = state.scratch['ax_snapshot_id']
    ticket = ActionTicket(
        action_type='MERGE_IDEAS', model_role='REASONING',
        input_snapshot_id=original_snapshot if explicit_snapshot else '',
        target_version_ids=list(original_members.values()),
        parameters={'inventory_hash': nodes.digest_json(state.solve.raw_ideas),
                    'parent_action_instance_ids': []},
        expected_outputs=['MergedFamilies', 'RawDisposition'],
        allowed_tools=['legacy_tracks'], reason='Continue the same recorded merge')
    original_ticket = ticket.model_dump(mode='json')
    calls = []
    response = {'ideas': [{'keep_ids': ['MERGE-SOURCE'],
                           'selection_reason': 'Preserve the original mechanism'}],
                'deferred': []}

    def provider(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        if len(calls) == 1:
            raise TimeoutError('Offline fixture: provider response was not received')
        return llm.LLMResult(data=copy.deepcopy(response), text=json.dumps(response),
                             model='offline-fixture', tokens_in=10, tokens_out=20,
                             cost_usd=.00001)

    monkeypatch.setattr(llm, 'chat_json', provider)
    request = dict(_node='s5_merge', system='Frozen merge system',
                   user='Frozen merge payload: MERGE-SOURCE', tier='T2',
                   expect='object', max_tokens=128)
    ctx = RunContext(state)
    with pytest.raises(TimeoutError):
        with executing(ctx, ticket, context='solve:merge', optional=False) as action:
            original_action = copy.deepcopy(action)
            gateway.chat(ctx, **request)
    before = journal(state)
    assert len(before[ledger.tasks.name]) == 1
    original_task = next(iter(before[ledger.tasks.name].values()))
    assert original_task['status'] == 'UNKNOWN' and original_task['actual'] is None
    held = original_task['reserve']
    assert held > 0 and ledger.budget(state.run_id)['reserved_microusd'] == held

    # A real interruption publishes partial solve output and invalidates coherence.
    state.status = 'INTERRUPTED'
    runtime.checkpoint(state, 's5_solve', interrupted=True)
    store.save_state(state)
    assert state.scratch['ax_snapshot_id'] != original_snapshot
    if with_coherence:
        assert original_members['coherence'] not in state.scratch['ax_members'].values()
    else:
        # All old targets remain legal, but the added solve member must not
        # alter the original paid-call identity during explicit continuation.
        assert 'coherence' not in original_members
        assert 'solve' not in original_members and 'solve' in state.scratch['ax_members']
        assert set(original_members.values()) <= set(state.scratch['ax_members'].values())
    approval = usage_recovery.authorize(
        state.run_id, state.user_id, original_task['task_id'],
        state.scratch['execution_epoch'], acknowledge_possible_duplicate_charge=True)
    assert usage_recovery.blocking_count(state) == 0
    next_transport_epoch(state)

    with executing(ctx, ticket, context='solve:merge', optional=False, resume=True) as action:
        assert action['action_instance_id'] == original_action['action_instance_id']
        assert action['exact_input_versions'] == original_action['exact_input_versions']
        assert action['ticket'] == original_ticket
        result = gateway.chat(ctx, **request)
    assert result.data == response and len(calls) == 2 and calls[0] == calls[1]
    after = journal(state)
    child_id = approval['retry_task_id']
    assert set(after[ledger.tasks.name]) == {original_task['task_id'], child_id}
    child = after[ledger.tasks.name][child_id]
    assert child['status'] == 'COMPLETED' and child['actual'] == 10
    assert after[ledger.tasks.name][original_task['task_id']] == original_task
    for attempt_id, row in before[ledger.attempts.name].items():
        assert after[ledger.attempts.name][attempt_id] == row
    child_attempt = json.loads(after[ledger.attempts.name][child_id + '-1']['details'])
    assert child_attempt['retry_of_task_id'] == original_task['task_id']
    assert child_attempt['authorization_event_id'] == usage_recovery.event_id(original_task['task_id'])
    assert ledger.budget(state.run_id)['reserved_microusd'] == held
    assert ledger.budget(state.run_id)['spent_microusd'] == 10
    with store.engine.connect() as connection:
        receipts_before = connection.execute(select(store.llm_calls.c.payload).where(
            store.llm_calls.c.run_id == state.run_id)).scalars().all()
    assert len(receipts_before) == 1
    assert json.loads(receipts_before[0])['task_id'] == child_id

    # Repeating the continuation must reuse the approved child, never pay again.
    next_transport_epoch(state)
    monkeypatch.setattr(llm, 'chat_json', lambda **_: pytest.fail('Paid retry repeated'))
    with executing(ctx, ticket, context='solve:merge', optional=False, resume=True) as action:
        assert action['ticket'] == original_ticket
        assert action['exact_input_versions'] == original_action['exact_input_versions']
        replay = gateway.chat(ctx, **request)
    assert replay.data == response and replay.meta['durable_replay']
    assert replay.meta['source_task_id'] == child_id
    assert replay.tokens_in == replay.tokens_out == replay.cost_usd == 0
    assert journal(state) == after
    assert ledger.budget(state.run_id)['reserved_microusd'] == held
    assert ledger.budget(state.run_id)['spent_microusd'] == 10
    with store.engine.connect() as connection:
        receipts_after = connection.execute(select(store.llm_calls.c.payload).where(
            store.llm_calls.c.run_id == state.run_id)).scalars().all()
    assert receipts_after == receipts_before
    assert ticket.model_dump(mode='json') == original_ticket
