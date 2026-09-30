"""Resume saved S5 decisions without accepting changed generation inputs."""
import copy
import json

import pytest
from sqlalchemy import select, update

from test_ax_refactor import newrun
from triz import nodes, store
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea
from triz.settings import settings
from triz.ax import adaptive_tracks, coordinator, ledger, runtime
from triz.ax.action_runtime import resume_inputs
from triz.ax.contracts import ActionTicket, Conflict, canonical


@pytest.fixture
def initial(newrun, monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    state = newrun('LITE')
    coordinator.route(RunContext(state))
    monkeypatch.setattr(nodes, '_evidence', lambda _: None)
    return state


def resume(state):
    runtime.checkpoint(state, 's5_solve', interrupted=True)
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'synthetic transport resume')
    runtime.before_stage(RunContext(state), 's5_solve')


def interrupted(initial, monkeypatch):
    def stop(*args, **kwargs):
        raise AbortRun('synthetic stage deadline')
    monkeypatch.setattr(nodes, '_run_tracks', stop)
    with pytest.raises(AbortRun, match='stage deadline'):
        adaptive_tracks.run(RunContext(initial), max_steps=1)
    pending = copy.deepcopy(initial.scratch['adaptive_search']['pending'])
    resume(initial)
    return pending, ActionTicket.model_validate(pending['ticket'])


def test_failed_track_resumes_original_decision_with_same_inputs(initial, monkeypatch):
    pending, ticket = interrupted(initial, monkeypatch)
    assert coordinator.feasible(initial, ticket, handlers={'RUN_TRACK'}) == 'stale_input_snapshot'
    decisions_before = ledger.decision_history(initial.run_id, initial.user_id)
    saved = copy.deepcopy(initial.scratch['ax_action_results'][ticket.action_instance_id])
    with store.engine.connect() as c:
        old_events = dict(c.execute(select(ledger.events.c.event_id, ledger.events.c.payload).where(
            ledger.events.c.run_id == initial.run_id)).all())
    calls = []
    def execute(ctx, tracks):
        calls.append(list(tracks))
        ctx.state.solve.raw_ideas.append(RawIdea(id='new-result', track=tracks[0], idea='fixture'))
        ctx.state.solve.tracks_run.extend(tracks)
    monkeypatch.setattr(nodes, '_run_tracks', execute)
    monkeypatch.setattr(nodes, '_merge', lambda _: False)
    adaptive_tracks.run(RunContext(initial), max_steps=1)
    assert calls == [ticket.parameters['tracks']]
    assert ledger.decision_history(initial.run_id, initial.user_id) == decisions_before
    assert 'pending' not in initial.scratch['adaptive_search']
    result = initial.scratch['ax_action_results'][ticket.action_instance_id]
    assert result['status'] == 'COMPLETED'
    assert result['ticket'] == pending['ticket']
    assert result['exact_input_versions'] == saved['exact_input_versions']
    assert result['decision_id'] == pending['decision_id']
    with store.engine.connect() as c:
        after = dict(c.execute(select(ledger.events.c.event_id, ledger.events.c.payload).where(
            ledger.events.c.run_id == initial.run_id)).all())
    assert all(after[key] == value for key, value in old_events.items())


def test_completed_track_is_not_reexecuted_or_rewritten_after_merge_failure(initial, monkeypatch):
    calls = []
    def execute(ctx, tracks):
        calls.append(list(tracks))
        ctx.state.solve.raw_ideas.append(RawIdea(id='completed-result', track=tracks[0], idea='fixture'))
        ctx.state.solve.tracks_run.extend(tracks)
    monkeypatch.setattr(nodes, '_run_tracks', execute)
    monkeypatch.setattr(nodes, '_merge', lambda _: (_ for _ in ()).throw(AbortRun('synthetic merge interruption')))
    with pytest.raises(AbortRun, match='merge interruption'):
        adaptive_tracks.run(RunContext(initial), max_steps=1)
    pending = copy.deepcopy(initial.scratch['adaptive_search']['pending'])
    result = copy.deepcopy(initial.scratch['ax_action_results'][pending['ticket']['action_instance_id']])
    output = copy.deepcopy(initial.solve.raw_ideas)
    decisions_before = ledger.decision_history(initial.run_id, initial.user_id)
    resume(initial)
    merges = []
    monkeypatch.setattr(nodes, '_merge', lambda ctx: merges.append(True) or False)
    adaptive_tracks.run(RunContext(initial), max_steps=1)
    assert len(calls) == len(merges) == 1
    assert initial.solve.raw_ideas == output
    assert initial.scratch['ax_action_results'][pending['ticket']['action_instance_id']] == result
    assert ledger.decision_history(initial.run_id, initial.user_id) == decisions_before
    assert 'pending' not in initial.scratch['adaptive_search']


@pytest.mark.parametrize('changed', ['input', 'problem', 'analysis', 'definition'])
def test_changed_generation_version_is_rejected(initial, monkeypatch, changed):
    pending, ticket = interrupted(initial, monkeypatch)
    ledger.capture(initial, {changed: {'changed': True}}, runtime.DEPENDENCIES, 'synthetic real input change')
    with pytest.raises(Conflict, match='generation inputs changed'):
        resume_inputs(initial, ticket, pending['decision_id'], context='adaptive:initial')


@pytest.mark.parametrize('context', ['adaptive:initial', 'solve:merge'])
@pytest.mark.parametrize('changed', ['constraints', 'evidence', 'coherence'])
def test_new_downstream_input_version_is_rejected(initial, monkeypatch, context, changed):
    # These prior refs may be removed by an S5 checkpoint, but a newly
    # published replacement must not inherit the original paid-call identity.
    ledger.capture(initial, {changed: {'review': 'original'}}, runtime.DEPENDENCIES,
                   'synthetic prior review')
    original_version = initial.scratch['ax_members'][changed]
    if context == 'adaptive:initial':
        pending, ticket = interrupted(initial, monkeypatch)
        decision = pending['decision_id']
    else:
        from triz import idea_consolidation
        initial.solve.raw_ideas = [RawIdea(id='unchanged-source', track='H_EFFECTS', idea='fixture')]
        monkeypatch.setattr(idea_consolidation, 'consolidate',
            lambda _: (_ for _ in ()).throw(AbortRun('synthetic merge interruption')))
        with pytest.raises(AbortRun, match='merge interruption'):
            nodes._merge(RunContext(initial))
        ticket = ActionTicket.model_validate(initial.scratch['ax_merge_pending']['ticket'])
        decision = None
        resume(initial)
    assert changed not in initial.scratch['ax_members']
    ledger.capture(initial, {changed: {'review': 'new'}}, runtime.DEPENDENCIES,
                   'synthetic new downstream review')
    assert initial.scratch['ax_members'][changed] != original_version
    before = initial.model_dump(mode='json')
    with pytest.raises(Conflict, match='downstream input was replaced'):
        resume_inputs(initial, ticket, decision, context=context)
    assert initial.model_dump(mode='json') == before


def test_missing_core_version_is_rejected_even_if_both_manifests_omit_it(initial, monkeypatch):
    # A malformed historical snapshot cannot prove equality through None == None.
    proposed = adaptive_tracks.proposals(initial)
    legal = [p for p in proposed if coordinator.feasible(initial, p, handlers={'RUN_TRACK'}) is None]
    ticket, decision = coordinator.decide(initial, [legal[0]], 0, {'RUN_TRACK'}, 'adaptive:initial')
    pending = {'decision_id': decision}
    resume(initial)
    with ledger.transaction() as c:
        for snapshot_id in (ticket.input_snapshot_id, initial.scratch['ax_snapshot_id']):
            raw = c.execute(select(ledger.snapshots.c.members).where(ledger.snapshots.c.snapshot_id == snapshot_id)).scalar_one()
            members = json.loads(raw); members.pop('analysis', None)
            c.execute(update(ledger.snapshots).where(ledger.snapshots.c.snapshot_id == snapshot_id).values(members=canonical(members)))
    initial.scratch['ax_members'].pop('analysis', None)
    with pytest.raises(Conflict, match='generation inputs changed'):
        resume_inputs(initial, ticket, pending['decision_id'], context='adaptive:initial')


@pytest.mark.parametrize('changed', ['episode', 'ticket', 'bundle', 'target', 'foreign_snapshot'])
def test_saved_identity_cannot_be_rebound_to_another_action(initial, newrun, monkeypatch, changed):
    pending, ticket = interrupted(initial, monkeypatch)
    if changed == 'episode':
        initial.scratch['semantic_episode_id'] += ':changed'
    elif changed == 'ticket':
        ticket = ticket.model_copy(update={'parameters': dict(ticket.parameters, tracks=['H_EFFECTS'])})
    elif changed == 'bundle':
        initial.scratch['ax_bundle']['bundle_id'] = 'foreign-bundle'
    elif changed == 'target':
        ticket = ticket.model_copy(update={'target_version_ids': ['foreign-version']})
    else:
        other = newrun('LITE')
        ticket = ticket.model_copy(update={'input_snapshot_id': other.scratch['ax_snapshot_id']})
    with pytest.raises(Conflict):
        resume_inputs(initial, ticket, pending['decision_id'], context='adaptive:initial')


def test_completed_result_with_missing_output_is_rejected(initial, monkeypatch):
    from triz.ax.action_runtime import completed_pending
    pending, ticket = interrupted(initial, monkeypatch)
    # Changing the saved projection does not create an immutable completion event.
    initial.scratch['ax_action_results'][ticket.action_instance_id]['status'] = 'COMPLETED'
    initial.solve.tracks_run.extend(ticket.parameters['tracks'])
    with pytest.raises(Conflict, match='completed action result changed'):
        completed_pending(initial, ticket, pending['decision_id'], context='adaptive:initial')


@pytest.mark.parametrize('completed', [False, True])
def test_same_snapshot_stop_pending_keeps_strict_path_without_merge(initial, monkeypatch, completed):
    from triz.ax.action_runtime import executing
    initial.solve.tracks_run = ['A_MATRIX']
    ticket = ActionTicket(action_type='STOP_EXPLORATION', parameters={'plan_class': 'PHASE_STOP', 'phase': 'initial'},
        expected_outputs=['SearchPhaseResult'], allowed_tools=[], reason='fixture')
    ticket, decision = coordinator.decide(initial, [ticket], 0, {'STOP_EXPLORATION'}, 'adaptive:initial')
    if completed:
        with executing(RunContext(initial), ticket, decision, context='adaptive:initial', optional=False):
            pass
    initial.scratch['adaptive_search'] = {'status': 'SEARCHING', 'evidence_planned': True,
        'pending': {'ticket': ticket.model_dump(mode='json'), 'decision_id': decision}}
    monkeypatch.setattr(nodes, '_merge', lambda _: pytest.fail('STOP must not merge'))
    adaptive_tracks.run(RunContext(initial), max_steps=1)
    assert initial.scratch['adaptive_search']['status'] == 'READY_FOR_REVIEW'
    assert 'pending' not in initial.scratch['adaptive_search']


def test_same_snapshot_followup_pending_keeps_strict_path(initial, monkeypatch):
    ticket = ActionTicket(action_type='RUN_TRACK', model_role='REASONING',
        parameters={'tracks': ['H_EFFECTS'], 'plan_class': 'FOLLOWUP_SELECTION'},
        target_version_ids=[initial.scratch['ax_members']['definition']],
        expected_outputs=['TrackResult'], allowed_tools=['legacy_tracks'], reason='fixture')
    ticket, decision = coordinator.decide(initial, [ticket], 0, {'RUN_TRACK'}, 'adaptive:s8')
    initial.scratch['adaptive_search'] = {'status': 'SEARCHING',
        'pending': {'ticket': ticket.model_dump(mode='json'), 'decision_id': decision}}
    called = []
    def run(ctx, tracks):
        called.append(tracks)
        ctx.state.solve.tracks_run.extend(tracks)
    monkeypatch.setattr(nodes, '_run_tracks', run)
    monkeypatch.setattr(nodes, '_merge', lambda _: False)
    adaptive_tracks.run(RunContext(initial), phase='s8', max_steps=1)
    assert called == [['H_EFFECTS']]
    assert 'pending' not in initial.scratch['adaptive_search']


def test_merge_saved_before_dispatch_can_continue_without_origin_event(initial, monkeypatch):
    from triz import idea_consolidation
    initial.solve.raw_ideas = [RawIdea(id='fixture', track='H_EFFECTS', idea='fixture')]
    first = RunContext(initial)
    monkeypatch.setattr(first, 'persist', lambda: (_ for _ in ()).throw(AbortRun('saved before dispatch')))
    with pytest.raises(AbortRun, match='saved before dispatch'):
        nodes._merge(first)
    assert initial.scratch['ax_merge_pending']
    called = []
    monkeypatch.setattr(idea_consolidation, 'consolidate', lambda ctx: called.append(True) or {'need_more': False})
    assert nodes._merge(RunContext(initial)) is False
    assert called == [True]
    assert 'ax_merge_pending' not in initial.scratch
