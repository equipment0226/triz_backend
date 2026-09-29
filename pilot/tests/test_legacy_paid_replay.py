"""Pre-contract resumes reuse exact paid input, without inventing verification."""
import copy
import json

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from ariz_fixtures import ariz_payload
from test_ariz_completeness_compatibility import part5
from triz import agent, knowledge, llm, nodes, store, verify
from triz.ax import ledger, usage_recovery
from triz.ax.contracts import Conflict
from triz.context import AbortRun, RunContext
from triz.schema import SolveBundle, Stage


def legacy(state):
    state.scratch['ax_bundle'].pop('run_contract', None)
    state.scratch.pop('semantic_episode_id', None)
    return state


def request(state):
    return dict(node='s5_ariz_p1', bundle_id=state.scratch['ax_bundle']['bundle_id'],
        decision_id='old-decision', request=dict(system='Pinned system', user='Exact Part 1 input',
            tier='T2', expect='object', max_tokens=32000, temperature=None, retries=2,
            model_config=copy.deepcopy(state.scratch['ax_bundle']['models']['T2'])))


def advance(state):
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline legacy resume')


def old_task(state, value, monkeypatch, *, status='COMPLETED', output=None):
    # Write the historical epoch-based format into the isolated fixture DB.
    with monkeypatch.context() as old:
        old.setattr(usage_recovery, 'stage_request_identity', lambda request: None)
        task = ledger.acquire(state.run_id, state.scratch['execution_epoch'], value, 1000)
    if status != 'RUNNING':
        ledger.settle(task, output or {'data': {'saved': True}},
                      123 if status in ('COMPLETED', 'FAILED') else None, status=status)
    return task


def journal(state):
    with store.engine.connect() as c:
        return [dict(row) for row in c.execute(select(ledger.tasks)
            .where(ledger.tasks.c.run_id == state.run_id)).mappings()]


def test_legacy_epoch_journal_replays_before_new_budget_check(newrun, monkeypatch):
    state = legacy(newrun()); value = request(state)
    original = old_task(state, value, monkeypatch)
    before = journal(state); spent = ledger.budget(state.run_id)['spent_microusd']
    advance(state); value['decision_id'] = 'resume-decision'
    result = ledger.acquire(state.run_id, 1, value, 10**12)
    assert result['cached'] and result['task_id'] == original['task_id']
    assert journal(state) == before
    assert ledger.budget(state.run_id)['spent_microusd'] == spent
    with pytest.raises(Conflict, match='epoch'):
        ledger.acquire(state.run_id, 0, value, 1000)


def test_multiple_completed_legacy_calls_keep_first_output_and_every_charge(newrun, monkeypatch):
    state = legacy(newrun()); value = request(state)
    first = old_task(state, value, monkeypatch, output={'data': {'version': 'first'}})
    advance(state); value['decision_id'] = 'second-decision'
    old_task(state, value, monkeypatch, output={'data': {'version': 'second'}})
    before = journal(state)
    advance(state)
    for _ in range(2):
        replay = ledger.acquire(state.run_id, 2, value, 1000)
        assert replay['cached'] and replay['task_id'] == first['task_id']
        assert replay['result']['data'] == {'version': 'first'}
    assert journal(state) == before
    assert ledger.budget(state.run_id)['spent_microusd'] == 246


@pytest.mark.parametrize('status', ['UNKNOWN', 'RUNNING', 'FAILED', 'STALE', 'RECONCILED'])
def test_ambiguous_legacy_history_never_hides_unsettled_or_failed_call(newrun, monkeypatch, status):
    state = legacy(newrun()); value = request(state)
    # Include a new stable-key result too: its direct hit cannot hide an older
    # uncertain call with the same provider input.
    stable = ledger.acquire(state.run_id, 0, value, 1000)
    ledger.settle(stable, {'data': {'saved': True}}, 123)
    advance(state)
    old_task(state, value, monkeypatch, status=status)
    advance(state)
    before = journal(state); budget = ledger.budget(state.run_id)
    with pytest.raises(Conflict, match='reconciliation'):
        ledger.acquire(state.run_id, 2, value, 1000)
    assert journal(state) == before
    assert ledger.budget(state.run_id) == budget


def test_single_legacy_unknown_retains_reservation_without_authorizing_retry(newrun, monkeypatch):
    state = legacy(newrun()); value = request(state)
    original = old_task(state, value, monkeypatch, status='UNKNOWN')
    advance(state)
    blocked = ledger.acquire(state.run_id, 1, value, 1000)
    assert blocked == {'task_id': original['task_id'], 'blocked': 'UNKNOWN'}
    assert ledger.budget(state.run_id)['reserved_microusd'] == 1000
    assert len(journal(state)) == 1
    assert usage_recovery.request_episode(value) is None


@pytest.mark.parametrize('change', ['system', 'user', 'model', 'max_tokens', 'temperature',
                                     'expect', 'tier', 'retries', 'bundle_id', 'node', 'run_id'])
def test_changed_actual_request_does_not_reuse_old_paid_output(newrun, monkeypatch, change):
    state = legacy(newrun()); value = request(state)
    original = old_task(state, value, monkeypatch)
    advance(state)
    if change == 'run_id':
        state = legacy(newrun())
    elif change in ('bundle_id', 'node'):
        value[change] += '-changed'
    elif change == 'model':
        value['request']['model_config']['model'] += '-changed'
    else:
        value['request'][change] = {'max_tokens': 16000, 'temperature': .7,
                                   'retries': 1}.get(change, 'changed')
    result = ledger.acquire(state.run_id, state.scratch['execution_epoch'], value, 1000)
    assert not result['cached'] and result['task_id'] != original['task_id']


def test_incomplete_or_invalid_episode_request_is_not_legacy_identity(newrun):
    state = legacy(newrun()); value = request(state)
    assert usage_recovery.stage_request_identity(value)
    for key in ('system', 'user', 'tier', 'expect', 'model_config'):
        partial = copy.deepcopy(value); partial['request'].pop(key)
        assert usage_recovery.stage_request_identity(partial) is None
    value['request']['semantic_episode_id'] = None
    assert usage_recovery.stage_request_identity(value) is None


@pytest.mark.parametrize('text', ['not JSON', '{"z":2,"a":1}', '{"z":true,"a":1}'])
def test_key_order_restore_cannot_change_saved_values(text):
    saved = {'data': {'a': 1, 'z': 1}, 'text': text}
    assert usage_recovery.legacy_replay_result(saved) is saved


@pytest.mark.parametrize('wrapper', ['{}', '```json\n{}\n```', 'Saved response follows:\n{}'])
def test_key_order_restore_uses_equivalent_original_text_without_mutation(wrapper):
    saved = {'data': {'a': 1, 'z': {'a': 2, 'z': 3}}, 'text': '{"z":{"z":3,"a":2},"a":1}'}
    saved['text'] = wrapper.format(saved['text'])
    restored = usage_recovery.legacy_replay_result(saved)
    assert restored == saved
    assert list(restored['data']) == ['z', 'a']
    assert list(restored['data']['z']) == ['z', 'a']
    assert list(saved['data']) == ['a', 'z']


def test_ariz_replays_first_paid_chain_and_keeps_policy_warn(newrun, monkeypatch):
    state = legacy(newrun('DEEP'))
    for group in state.scratch['ax_bundle']['effects']:
        group['function_ko'] = '열 제거'
    original_cfg = nodes.cfg
    monkeypatch.setattr(nodes, 'cfg', lambda key, default=None:
        [1, 2, 3, 4, 5] if key == 'ariz.enabled_parts' else original_cfg(key, default))
    acquire = ledger.acquire

    def stop_before_unpaid_part6(run_id, epoch, value, *args, **kwargs):
        if value.get('node') == 's5_ariz_p6':
            raise Conflict('Offline stop before the unpaid Part 6')
        return acquire(run_id, epoch, value, *args, **kwargs)

    monkeypatch.setattr(ledger, 'acquire', stop_before_unpaid_part6)
    outputs = [ariz_payload(part) for part in (1, 2, 3, 4)] + [part5()]
    provider_calls = []

    def provider(**kwargs):
        provider_calls.append(copy.deepcopy(kwargs))
        payload = copy.deepcopy(outputs[len(provider_calls) - 1])
        return llm.LLMResult(data=payload, text=json.dumps(payload), model='offline-fixture',
                             cost_usd=.000123, tokens_in=10, tokens_out=20)

    monkeypatch.setattr(llm, 'chat_json', provider)
    with monkeypatch.context() as old:
        old.setattr(usage_recovery, 'stage_request_identity', lambda request: None)
        with pytest.raises(AbortRun, match='unpaid Part 6'):
            nodes._track_d_ariz(RunContext(state))
    first_steps = {step.node: copy.deepcopy(step) for step in state.steps if step.status != 'FAILED'}
    assert len(provider_calls) == 5 and state.solve.ariz is None
    assert first_steps['s5_ariz_p1'].status == first_steps['s5_ariz_p3'].status == 'WARN'
    assert first_steps['s5_ariz_p1'].verdicts[-1] == {
        'verdict': 'UNVERIFIED', 'score': 0.0, 'skipped': True, 'source': 'policy'}

    # Reproduce the historical second Part 1, with no paid downstream result.
    advance(state)
    changed = copy.deepcopy(outputs[0]); changed['steps'][0]['output'] += ' Different generated wording.'
    outputs.append(changed)
    with monkeypatch.context() as old:
        old.setattr(usage_recovery, 'stage_request_identity', lambda request: None)
        agent.run_agent(RunContext(state), node='s5_ariz_p1', label='ARIZ Part1', stage=Stage.S5.value,
            agent_id='ariz_specialist', prompt_id='P_S5_ARIZ_PART1', tier='T2', rubric_id='R5_D',
            checker=lambda value: verify.check_ariz(value, [row['code'] for row in
                knowledge.ariz_part(1)['steps'] if row.get('required')]),
            vars=first_steps['s5_ariz_p1'].input_slice['vars'], default={})
    assert state.steps[-1].input_slice == first_steps['s5_ariz_p1'].input_slice
    assert state.steps[-1].output_json != first_steps['s5_ariz_p1'].output_json
    before = journal(state); spent = ledger.budget(state.run_id)['spent_microusd']
    count = state.cost.request_count
    advance(state)
    state.solve = SolveBundle()
    state.scratch['agent_cache'] = {}  # Exercise durable replay for every Part.
    monkeypatch.setattr(llm, 'chat_json', lambda **kwargs: pytest.fail('Repeated paid ARIZ call'))
    start = len(state.steps)
    with pytest.raises(AbortRun, match='unpaid Part 6'):
        nodes._track_d_ariz(RunContext(state))
    replayed = [step for step in state.steps[start:] if step.status != 'FAILED']
    assert [step.node for step in replayed] == [f's5_ariz_p{part}' for part in range(1, 6)]
    for step in replayed:
        saved = first_steps[step.node]
        replay_source = step.input_slice['replay_source']
        assert {key: value for key, value in step.input_slice.items()
                if key != 'replay_source'} == saved.input_slice
        source = next(row for row in before if row['task_id'] == replay_source['task_id'])
        assert replay_source['new_provider_calls'] == 0
        assert replay_source['usage'] == {'tokens_in': 10, 'tokens_out': 20,
            'cost_usd': .000123, 'settled_microusd': source['actual']}
        assert step.tokens_in == step.tokens_out == 0
        assert step.cost_usd == 0
        assert step.output_json == saved.output_json
        assert step.status == saved.status
        assert step.verdicts == saved.verdicts
    assert journal(state) == before
    assert ledger.budget(state.run_id)['spent_microusd'] == spent
    assert state.cost.request_count == count
