"""A killed worker must retain completed batches, step history, and reservations."""
import copy
import threading

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from triz import nodes, pipeline, store, llm
from triz.context import RunContext, UsageUncertain
from triz.schema import RawIdea
from triz.ax import gateway, ledger, runtime
from triz.ax.action_runtime import active_action


def test_finished_batch_survives_process_loss_during_next_track(newrun, monkeypatch):
    state = newrun('FULL')
    state.status = 'RUNNING'
    state.control.current_stage = 'S5_SOLVE'
    state.scratch['execution_stage_active'] = {'epoch': state.scratch['execution_epoch'], 'index': 6}
    ctx = RunContext(state)
    for track in ('A_MATRIX', 'B_SEPARATION'):
        def completed(child, track=track):
            child.state.solve.raw_ideas.append(RawIdea(id='raw-' + track, track=track, title=track, idea='Retained result'))
        monkeypatch.setitem(nodes.TRACK_FUNCS, track, completed)
    nodes._run_tracks(ctx, ['A_MATRIX', 'B_SEPARATION'])
    durable = store.load_state(state.run_id)
    assert durable.solve.tracks_run == ['A_MATRIX', 'B_SEPARATION']
    assert len(durable.solve.raw_ideas) == 2

    completed_task = ledger.acquire(state.run_id, state.scratch['execution_epoch'], {'node': 'earlier'}, 15000)
    ledger.settle(completed_task, {'data': {'ok': True}}, 10000)
    def killed(child):
        child.start_step(node='s5_track_h', label='Effects', stage='S5_SOLVE',
                         agent_id='effects_specialist', prompt_id='P_S5_TRACK_H', tier='T2')
        ledger.acquire(state.run_id, state.scratch['execution_epoch'],
                       {'node': 's5_track_h', 'action_context': copy.deepcopy(active_action.get())}, 20000)
        raise SystemExit('Simulate hard process loss before settlement')
    monkeypatch.setitem(nodes.TRACK_FUNCS, 'H_EFFECTS', killed)
    with pytest.raises(SystemExit):
        nodes._run_tracks(ctx, ['H_EFFECTS'])
    assert state.run_id in pipeline.recover_orphans()
    recovered = store.load_state(state.run_id)
    assert recovered.solve.tracks_run == ['A_MATRIX', 'B_SEPARATION']
    assert [i.id for i in recovered.solve.raw_ideas] == ['raw-A_MATRIX', 'raw-B_SEPARATION']
    assert recovered.steps[-1].node == 's5_track_h'
    assert recovered.steps[-1].status == 'FAILED'
    assert recovered.cost.total_usd == .01
    assert recovered.scratch['ax_interrupted_usage']['reserved_microusd'] == 20000
    assert recovered.scratch['ax_interrupted_usage']['unknown_attempts'] == 1
    assert '과금 상태' in recovered.scratch['interruption_reason']
    with store.engine.connect() as c:
        status = c.execute(select(ledger.attempts.c.status).where(ledger.attempts.c.run_id == state.run_id)).scalars().all()
    assert sorted(status) == ['COMPLETED', 'UNKNOWN']
    before = ledger.budget(state.run_id)
    assert state.run_id not in pipeline.recover_orphans()
    assert ledger.budget(state.run_id) == before


def test_step_journal_updates_stale_checkpoint_without_losing_metadata(state):
    ctx = RunContext(state)
    step = ctx.start_step(node='s5_track_a', label='A', stage='S5_SOLVE', agent_id='solver', prompt_id='P_A', tier='T2')
    step.escalated = True
    ctx.persist()
    step.output_json = {'ideas': [{'title': 'Saved after checkpoint'}]}
    ctx.finish_step(step, 'OK')
    later = ctx.start_step(node='s5_track_b', label='B', stage='S5_SOLVE', agent_id='solver', prompt_id='P_B', tier='T2')
    later.output_json = {'ideas': [{'title': 'Second saved response'}]}
    ctx.finish_step(later, 'WARN')
    stale = store.load_state(state.run_id)
    assert len(stale.steps) == 1 and stale.steps[0].status == 'RUNNING'
    pipeline._recover_step_journal(stale)
    assert [s.status for s in stale.steps] == ['OK', 'WARN']
    assert stale.steps[0].escalated is True
    assert stale.steps[1].output_json == later.output_json
    pipeline._recover_step_journal(stale)
    assert len(stale.steps) == 2


def test_initial_batch_checkpoint_preserves_concurrent_evidence(newrun, monkeypatch):
    state = newrun('FULL')
    ctx = RunContext(state)
    runtime.before_stage(ctx, 's5_solve')
    published = threading.Event()
    def evidence(parent):
        parent.state.scratch['retrieval_marker'] = 'preserved'
        parent.persist()
        published.set()
    monkeypatch.setattr(nodes, '_evidence', evidence)
    for track in ('A_MATRIX', 'B_SEPARATION', 'C_STANDARDS'):
        def track_fn(child, track=track):
            assert published.wait(5)
            child.state.solve.raw_ideas.append(RawIdea(id=track, track=track, title=track, idea='Saved'))
        monkeypatch.setitem(nodes.TRACK_FUNCS, track, track_fn)
    def stop_before_next_batch(ctx):
        saved = store.load_state(state.run_id)
        assert saved.scratch['retrieval_marker'] == 'preserved'
        assert saved.solve.tracks_run == ['A_MATRIX', 'B_SEPARATION', 'C_STANDARDS']
        raise SystemExit('Stop before next batch')
    from triz.ax import coordinator
    monkeypatch.setattr(coordinator, 'complete_required', stop_before_next_batch)
    with pytest.raises(SystemExit):
        nodes.s5_solve(ctx)


def test_unknown_response_remains_blocked_after_resume(newrun, monkeypatch):
    state = newrun()
    ctx = RunContext(state)
    monkeypatch.setattr(ledger, 'acquire', lambda *a, **k: {'task_id': 'unknown', 'blocked': 'UNKNOWN'})
    def no_call(**kwargs):
        raise AssertionError('Unknown usage must not trigger another paid request')
    monkeypatch.setattr(llm, 'chat_json', no_call)
    with pytest.raises(UsageUncertain, match='과금 상태'):
        gateway.chat(ctx, _node='s5_track_h', system='JSON', user='Effects', tier='T2')


def test_usage_warning_survives_pipeline_interruption(state, monkeypatch):
    def stop(ctx):
        raise UsageUncertain()
    monkeypatch.setattr(pipeline, 'PIPELINE', [('s5_solve', 'Solve', stop)])
    assert pipeline.execute_stage(state.run_id, 0)['status'] == 'INTERRUPTED'
    assert '과금 상태' in store.load_state(state.run_id).scratch['interruption_reason']


def test_deployment_guard_rejects_active_work_and_allows_human_wait(state):
    from scripts.deployment_readiness import readiness
    state.status = 'RUNNING'
    store.save_state(state)
    assert state.run_id in [r['run_id'] for r in readiness()['active_runs']]
    assert readiness()['ready'] is False
    state.status = 'WAITING_HUMAN'
    store.save_state(state)
    assert state.run_id not in [r['run_id'] for r in readiness()['active_runs']]


def test_unknown_h_blocks_stage_before_retrieval_or_other_paid_work(newrun, monkeypatch):
    state = newrun()
    state.status = 'RUNNING'
    state.control.stage_index = 0
    state.solve.tracks_run = ['A_MATRIX', 'B_SEPARATION', 'C_STANDARDS', 'E_TRIMMING', 'F_TRENDS', 'G_FOS']
    task = ledger.acquire(state.run_id, state.scratch['execution_epoch'], {'node': 's5_track_h'}, 133379)
    ledger.settle(task, {'error': 'worker_lost'}, None, status='UNKNOWN')
    store.save_state(state)
    invoked = []
    monkeypatch.setattr(pipeline, 'PIPELINE', [('s5_solve', 'Solve', lambda ctx: invoked.append('retrieval_and_tracks'))])
    result = pipeline.execute_stage(state.run_id, 0, state.scratch['execution_epoch'])
    assert invoked == []
    assert result['status'] == 'INTERRUPTED'
    recovered = store.load_state(state.run_id)
    assert '과금 상태' in recovered.scratch['interruption_reason']
    assert recovered.solve.tracks_run == state.solve.tracks_run
    assert ledger.budget(state.run_id)['reserved_microusd'] == 133379
