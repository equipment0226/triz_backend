"""Action attribution shared by the existing track and recovery executors."""
from contextlib import contextmanager
from contextvars import ContextVar
import copy
import json
import time
from sqlalchemy import select
from . import ledger
from .contracts import digest, now, Conflict
from .mode_contract import contract, validate_tracks, optional_enabled

active_action = ContextVar('triz_action_context', default=None)


def episode(state):
    return state.scratch.get('semantic_episode_id', state.run_id + ':0')


def identity(state, ticket, context):
    data = ticket.model_dump(mode='json')
    data.pop('action_instance_id', None)
    return 'act-' + digest([state.run_id, episode(state), context, data])[:56]


def emit(state, kind, payload):
    event_id = 'actev-' + digest([state.run_id, kind, payload])[:56]
    with ledger.transaction() as c:
        h = ledger._head(c, state.run_id, lock=True)
        if h['epoch'] != state.scratch.get('execution_epoch', 0):
            raise Conflict('Stale action epoch')
        if not c.execute(select(ledger.events.c.event_id).where(ledger.events.c.event_id == event_id)).first():
            ledger._event(c, state.run_id, kind, payload, event_id=event_id)


def usage(state, action_id):
    from .cost_restatements import effective, overrides
    with ledger.store.engine.connect() as c:
        rows = c.execute(select(ledger.tasks.c.task_id,ledger.tasks.c.actual,ledger.attempts.c.details)
            .join(ledger.tasks,ledger.tasks.c.task_id==ledger.attempts.c.task_id)
            .where(ledger.attempts.c.run_id == state.run_id)).all()
        corrections=overrides(c,state.run_id)
    calls={}; attempts=0
    for row in rows:
        detail=json.loads(row.details)
        if isinstance(detail.get('request'),dict) and detail['request'].get('action_context',{}).get('action_instance_id') == action_id:
            calls[row.task_id]=effective(row.actual,row.task_id,corrections)
            attempts+=1
    unknown=any(value is None for value in calls.values())
    return {'actual_microusd': None if unknown else sum(calls.values()),
            'usage_status': 'UNKNOWN' if unknown else 'SETTLED', 'attempts': attempts,
            'task_ids': sorted(calls)}


def optional_commitment(state):
    from .cost_restatements import effective, overrides
    with ledger.store.engine.connect() as c:
        rows=c.execute(select(ledger.tasks.c.task_id,ledger.tasks.c.actual,ledger.attempts.c.details,ledger.tasks.c.reserve)
            .join(ledger.tasks,ledger.tasks.c.task_id==ledger.attempts.c.task_id)
            .where(ledger.attempts.c.run_id==state.run_id)).all()
        corrections=overrides(c,state.run_id)
    total=0; counted=set()
    for row in rows:
        detail=json.loads(row.details)
        if row.task_id not in counted and detail.get('request',{}).get('action_context',{}).get('optional'):
            actual=effective(row.actual,row.task_id,corrections)
            total+=actual if actual is not None else row.reserve
            counted.add(row.task_id)
    return total


def _saved_action_start(connection, state, ticket, context):
    action_id = ticket.action_instance_id or identity(state, ticket, context)
    raw = connection.execute(select(ledger.events.c.payload).where(
        ledger.events.c.run_id == state.run_id,
        ledger.events.c.event_type == 'ACTION_INSTANCE_STARTED',
        ledger.events.c.payload.contains('"action_instance_id":' + json.dumps(action_id), autoescape=True))
        .order_by(ledger.events.c.created_at).limit(1)).scalar()
    return json.loads(raw) if raw else None


def resume_inputs(state, ticket, decision_id=None, *, context):
    """Prove a saved S5 action survived only its own checkpoint advancement.

    This is an explicit continuation, not a waiver for arbitrary stale tickets.
    Execution is checked against the current head while the original paid-call
    identity/read set remains intact, including UNKNOWN retry authorization.
    """
    initial = (context == 'adaptive:initial' and ticket.action_type == 'RUN_TRACK'
               and ticket.parameters.get('plan_class') == 'INITIAL_SELECTION')
    merge = context == 'solve:merge' and ticket.action_type == 'MERGE_IDEAS'
    if not (initial or merge):
        raise Conflict('Action continuation is not supported for this context')
    h = ledger.head(state.run_id, state.user_id)
    if (h['epoch'] != state.scratch.get('execution_epoch', 0)
            or h['snapshot_id'] != state.scratch.get('ax_snapshot_id')
            or h['bundle']['bundle_id'] != state.scratch['ax_bundle']['bundle_id']):
        raise Conflict('Action input version changed')
    action_id = ticket.action_instance_id or identity(state, ticket, context)
    with ledger.store.engine.connect() as c:
        origin = _saved_action_start(c, state, ticket, context)
        if origin and (origin.get('action_instance_id') != action_id
                or origin.get('run_id') != state.run_id
                or origin.get('semantic_episode_id') != episode(state)
                or origin.get('ticket') != ticket.model_dump(mode='json')
                or origin.get('optional') is not False):
            raise Conflict('Saved action identity changed')
        if initial:
            row = c.execute(select(ledger.decisions).where(ledger.decisions.c.run_id == state.run_id,
                ledger.decisions.c.decision_id == decision_id)).mappings().first()
            if not row:
                raise Conflict('Saved action decision is missing')
            decision = json.loads(row['payload'])
            selected = decision.get('executed_index')
            actions = decision.get('actions', [])
            if (decision.get('bundle_id') != h['bundle']['bundle_id']
                    or decision.get('semantic_episode_id') != episode(state)
                    or decision.get('context') != context or type(selected) is not int
                    or not 0 <= selected < len(actions)
                    or actions[selected].get('ticket') != ticket.model_dump(mode='json')
                    or row['snapshot_id'] != ticket.input_snapshot_id):
                raise Conflict('Saved action decision changed')
            source_snapshot = row['snapshot_id']
        else:
            if not origin or ticket.parameters.get('inventory_hash') != digest(
                    [idea.model_dump(mode='json') for idea in state.solve.raw_ideas]):
                raise Conflict('Saved merge input changed')
            source_snapshot = origin['input_snapshot_id']
        snapshot = c.execute(select(ledger.snapshots.c.members).where(
            ledger.snapshots.c.run_id == state.run_id,
            ledger.snapshots.c.snapshot_id == source_snapshot)).scalar()
        if not snapshot:
            raise Conflict('Saved action snapshot is missing or foreign')
        inputs = json.loads(snapshot)
        if origin and origin.get('exact_input_versions') != inputs:
            raise Conflict('Saved action read set changed')
        core = ('input', 'problem', 'analysis', 'definition')
        current = state.scratch.get('ax_members', {})
        current_raw = c.execute(select(ledger.snapshots.c.members).where(
            ledger.snapshots.c.run_id == state.run_id, ledger.snapshots.c.snapshot_id == h['snapshot_id'])).scalar()
        if not current_raw or current != json.loads(current_raw):
            raise Conflict('Current action read set changed')
        if any(not inputs.get(key) or inputs[key] != current.get(key) for key in core):
            raise Conflict('Saved action generation inputs changed')
        from .runtime import descendants
        changed = {key for key in set(inputs) | set(current) if inputs.get(key) != current.get(key)}
        if changed - descendants({'solve'}):
            raise Conflict('Saved action input changed outside S5 outputs')
        # An interrupted S5 checkpoint can replace solve and remove downstream
        # refs. A newly published downstream version is a real input change,
        # including constraints/evidence consumed by merge; never rebind it.
        if any(key in current for key in changed - {'solve'}):
            raise Conflict('Saved action downstream input was replaced')
        if not set(ticket.target_version_ids) <= set(inputs.values()):
            raise Conflict('Saved action target is stale or foreign')
        artifacts = c.execute(select(ledger.artifacts.c.version_id, ledger.artifacts.c.provenance).where(
            ledger.artifacts.c.run_id == state.run_id, ledger.artifacts.c.version_id.in_(inputs.values()))).all()
        if {row.version_id for row in artifacts} != set(inputs.values()) or any(
                json.loads(row.provenance).get('bundle_id') != h['bundle']['bundle_id'] for row in artifacts):
            raise Conflict('Saved action artifact or bundle changed')
    # Derived output refs may have been invalidated by the interrupted S5 save.
    # Revalidate the corresponding current refs, never retarget base inputs.
    targets = [current[key] for key, version in inputs.items()
               if version in ticket.target_version_ids and key in current]
    validation_ticket = ticket.model_copy(update={'input_snapshot_id': h['snapshot_id'],
                                                 'target_version_ids': targets})
    emit(state, 'ACTION_INPUT_CONTINUED', dict(action_instance_id=action_id, decision_id=decision_id,
        context=context, semantic_episode_id=episode(state), source_snapshot_id=source_snapshot,
        execution_snapshot_id=h['snapshot_id'], exact_input_versions=inputs,
        execution_targets=targets, ticket_hash=digest(ticket.model_dump(mode='json'))))
    return validation_ticket, inputs


def completed_pending(state, ticket, decision_id=None, *, context):
    """Continue after an already-recorded producer without rewriting its result."""
    action_id = ticket.action_instance_id or identity(state, ticket, context)
    result = state.scratch.get('ax_action_results', {}).get(action_id)
    if not result or result.get('status') != 'COMPLETED':
        return False
    resume_inputs(state, ticket, decision_id, context=context)
    event_id = 'actev-' + digest([state.run_id, 'ACTION_INSTANCE_RESULT', result])[:56]
    with ledger.store.engine.connect() as c:
        exists = c.execute(select(ledger.events.c.event_id).where(ledger.events.c.run_id == state.run_id,
            ledger.events.c.event_id == event_id, ledger.events.c.event_type == 'ACTION_INSTANCE_RESULT')).first()
    if (not exists or result.get('ticket') != ticket.model_dump(mode='json')
            or result.get('semantic_episode_id') != episode(state)
            or result.get('decision_id') != decision_id
            or not set(ticket.parameters.get('tracks', [])) <= set(state.solve.tracks_run)):
        raise Conflict('Saved completed action result changed')
    known = {idea.id for idea in state.solve.raw_ideas}
    known.update(row.get('source_idea_id') for row in state.scratch.get('ax_idea_inventory', []))
    if not set(result.get('produced_raw_idea_ids', [])) <= known:
        raise Conflict('Saved completed action output is missing')
    return True


@contextmanager
def executing(ctx, ticket, decision_id=None, *, context='optional', optional=True, resume=False):
    """Revalidate immediately before dispatch; retain stale costs in the gateway."""
    state = ctx.state
    if not contract(state):
        yield {}
        return
    from .coordinator import feasible, handler_id
    stale = ((ticket.input_snapshot_id and ticket.input_snapshot_id != state.scratch.get('ax_snapshot_id'))
             or not set(ticket.target_version_ids) <= set(state.scratch.get('ax_members', {}).values()))
    if resume and not stale:
        with ledger.store.engine.connect() as c:
            origin = _saved_action_start(c, state, ticket, context)
        # A checkpoint can add solve without removing any original target.
        # Retain the original read set so UNKNOWN/cached calls keep one identity.
        stale = bool(origin and origin.get('exact_input_versions') != state.scratch.get('ax_members', {}))
    continuation = resume_inputs(state, ticket, decision_id, context=context) if resume and stale else None
    reason = feasible(state, continuation[0] if continuation else ticket, handlers={ticket.action_type})
    if reason:
        raise Conflict('Action rejected at execution: ' + reason)
    if optional and not optional_enabled(state):
        raise Conflict('Optional execution is disabled in this mode')
    validate_tracks(state, ticket.parameters.get('tracks', []))
    h = ledger.head(state.run_id, state.user_id)
    if h['epoch'] != state.scratch.get('execution_epoch', 0) or h['snapshot_id'] != state.scratch.get('ax_snapshot_id'):
        raise Conflict('Action input version changed')
    action_id = ticket.action_instance_id or identity(state, ticket, context)
    from .exploration_context import enabled as targeted_enabled, validate as validate_targeted
    targeted = ticket.parameters.get('exploration_context') if targeted_enabled(state) else None
    if targeted:
        validate_targeted(targeted, ticket.parameters.get('semantic_context_hash'), state)
    elif targeted_enabled(state) and optional and context == 'solve:coverage_expansion':
        raise Conflict('Targeted expansion context is required')
    parent = active_action.get() or {}
    value = dict(run_id=state.run_id, tenant_id=h['tenant_id'], project_id=h['project_id'],
                 semantic_episode_id=episode(state), execution_epoch=h['epoch'],
                 action_instance_id=action_id, decision_id=decision_id,
                 handler_id=handler_id(ticket),
                 parent_action_instance_id=parent.get('action_instance_id'),
                 parent_action_instance_ids=ticket.parameters.get('parent_action_instance_ids', []),
                 input_snapshot_id=h['snapshot_id'], exact_input_versions=dict(state.scratch.get('ax_members', {})),
                 mode_profile_version=contract(state)['mode_profile_version'],
                 policy_version=state.scratch['ax_bundle']['policy_version'],
                 ticket=ticket.model_dump(mode='json'), optional=optional,
                 plan_class=ticket.parameters.get('plan_class', 'OPTIONAL' if optional else 'FORCED_BASELINE'))
    if continuation:
        value['exact_input_versions'] = dict(continuation[1])
    from .track_cost import comparison
    value['cost_comparison']=comparison(state)
    if targeted:
        value.update(semantic_context_hash=ticket.parameters['semantic_context_hash'],
                     exploration_contract=targeted['schema'])
    previous = state.scratch.get('ax_action_results', {}).get(action_id)
    if context.startswith('track:') and ticket.action_type == 'GENERATE_BASELINE' and previous:
        # A partial S5 checkpoint adds solve output and invalidates derived
        # coherence. Neither changes the inputs of the unfinished base track.
        # Keep its original read set so transport resume reuses paid calls.
        prior_inputs = previous.get('exact_input_versions', {})
        inputs = ('input', 'problem', 'analysis', 'definition')
        if (previous.get('semantic_episode_id') == episode(state)
                and prior_inputs and all(prior_inputs.get(k) == state.scratch['ax_members'].get(k) for k in inputs)):
            value['exact_input_versions'] = dict(prior_inputs)
    emit(state, 'ACTION_INSTANCE_STARTED', value)
    token = active_action.set(value)
    before = {i.id for i in state.solve.raw_ideas}
    before_candidates = {c.id for c in state.concepts}
    before_steps={s.step_id for s in state.steps}
    previous_result=state.scratch.get('ax_action_results',{}).get(action_id,{})
    reused_result=previous_result if previous_result.get('status')=='COMPLETED' else {}
    before_solve=state.solve.model_copy(deep=True)
    before_concepts=copy.deepcopy(state.concepts)
    before_mechanisms=copy.deepcopy(state.scratch.get('ax_mechanisms',{}))
    started = time.monotonic()
    result = dict(value, status='COMPLETED')
    try:
        yield value
        current = ledger.head(state.run_id, state.user_id)
        if current['epoch'] != h['epoch'] or current['snapshot_id'] != h['snapshot_id']:
            raise Conflict('Action output is stale')
    except BaseException as exc:
        result.update(status='FAILED', error_class=type(exc).__name__)
        current=ledger.head(state.run_id,state.user_id)
        if current['epoch']!=h['epoch'] or current['snapshot_id']!=h['snapshot_id']:
            result['quarantined_raw_idea_ids']=sorted({i.id for i in state.solve.raw_ideas}-before)
            state.solve=before_solve
            state.concepts=before_concepts
            state.scratch['ax_mechanisms']=before_mechanisms
        from ..context import AbortRun
        if optional and isinstance(exc,AbortRun) and ('Optional AX budget' in str(exc) or 'Insufficient budget' in str(exc)):
            result['status']='DEFER_OPTIONAL_BUDGET'
            state.scratch['ax_optional_deferred_budget']=str(exc)
        else:
            raise
    finally:
        active_action.reset(token)
        result.update(produced_raw_idea_ids=sorted(({i.id for i in state.solve.raw_ideas} - before)|set(reused_result.get('produced_raw_idea_ids',[]))),
                      candidate_ids=sorted(({c.id for c in state.concepts} - before_candidates)|set(reused_result.get('candidate_ids',[]))),
                      wallclock_seconds=round(time.monotonic() - started, 6), completed_at=now(),
                      **usage(state, action_id))
        prefixes=['s5_ariz_' if t=='D_ARIZ' else 's5_track_'+t[0].lower() for t in ticket.parameters.get('tracks',[])]
        result['producer_step_statuses']=[dict(step_id=s.step_id,node=s.node,status=s.status) for s in state.steps
            if s.step_id not in before_steps and any(s.node.startswith(prefix) for prefix in prefixes)]
        if targeted and result['status'] == 'COMPLETED' and not result['produced_raw_idea_ids']:
            result['contribution_status'] = 'NO_NEW_INFORMATION'
            result['no_application_reasons'] = dict(state.scratch.get('ax_track_review_reasons', {}))
        # A stale result remains immutable accounting evidence, never a live projection.
        current = ledger.head(state.run_id, state.user_id)
        if current['epoch'] == h['epoch']:
            emit(state, 'ACTION_INSTANCE_RESULT', result)
            state.scratch.setdefault('ax_action_results', {})[action_id] = result


def tier(state, ticket):
    return contract(state).get('model_roles', {}).get(ticket.model_role, 'T2')


def candidate_actions(state, candidate):
    from .source_lineage import trace
    sources = trace(state, candidate.source_idea_ids)
    leaves = set(sources['leaves']) if sources['complete'] else set()
    return sorted(aid for aid,result in state.scratch.get('ax_action_results',{}).items()
        if candidate.id in result.get('candidate_ids',[]) or leaves.intersection(result.get('produced_raw_idea_ids',[])))
