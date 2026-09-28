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
    with ledger.store.engine.connect() as c:
        rows = c.execute(select(ledger.attempts.c.details).where(ledger.attempts.c.run_id == state.run_id)).scalars()
        calls = [json.loads(row) for row in rows]
    calls = [row for row in calls if row.get('request', {}).get('action_context', {}).get('action_instance_id') == action_id]
    unknown = any(row.get('actual_microusd') is None for row in calls)
    return {'actual_microusd': None if unknown else sum(row['actual_microusd'] for row in calls),
            'usage_status': 'UNKNOWN' if unknown else 'SETTLED', 'attempts': len(calls)}


def optional_commitment(state):
    with ledger.store.engine.connect() as c:
        rows=c.execute(select(ledger.attempts.c.details,ledger.tasks.c.reserve)
            .join(ledger.tasks,ledger.tasks.c.task_id==ledger.attempts.c.task_id)
            .where(ledger.attempts.c.run_id==state.run_id)).all()
    total=0
    for details,reserve in rows:
        row=json.loads(details)
        if row.get('request',{}).get('action_context',{}).get('optional'):
            total+=row['actual_microusd'] if row.get('actual_microusd') is not None else reserve
    return total


@contextmanager
def executing(ctx, ticket, decision_id=None, *, context='optional', optional=True):
    """Revalidate immediately before dispatch; retain stale costs in the gateway."""
    state = ctx.state
    if not contract(state):
        yield {}
        return
    from .coordinator import feasible, handler_id
    reason = feasible(state, ticket, handlers={ticket.action_type})
    if reason:
        raise Conflict('Action rejected at execution: ' + reason)
    if optional and not optional_enabled(state):
        raise Conflict('Optional execution is disabled in this mode')
    validate_tracks(state, ticket.parameters.get('tracks', []))
    h = ledger.head(state.run_id, state.user_id)
    if h['epoch'] != state.scratch.get('execution_epoch', 0) or h['snapshot_id'] != state.scratch.get('ax_snapshot_id'):
        raise Conflict('Action input version changed')
    action_id = ticket.action_instance_id or identity(state, ticket, context)
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
                 ticket=ticket.model_dump(mode='json'), optional=optional)
    emit(state, 'ACTION_INSTANCE_STARTED', value)
    token = active_action.set(value)
    before = {i.id for i in state.solve.raw_ideas}
    before_candidates = {c.id for c in state.concepts}
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
        result.update(produced_raw_idea_ids=sorted({i.id for i in state.solve.raw_ideas} - before),
                      candidate_ids=sorted({c.id for c in state.concepts} - before_candidates),
                      wallclock_seconds=round(time.monotonic() - started, 6), completed_at=now(),
                      **usage(state, action_id))
        # A stale result remains immutable accounting evidence, never a live projection.
        current = ledger.head(state.run_id, state.user_id)
        if current['epoch'] == h['epoch']:
            emit(state, 'ACTION_INSTANCE_RESULT', result)
            state.scratch.setdefault('ax_action_results', {})[action_id] = result


def tier(state, ticket):
    return contract(state).get('model_roles', {}).get(ticket.model_role, 'T2')


def candidate_actions(state, candidate):
    leaves=set(candidate.source_idea_ids)
    for idea in state.solve.raw_ideas:
        if idea.id in leaves:
            leaves.update(idea.source_idea_ids)
            leaves.update(r.get('source_idea_id') for r in idea.detail.get('source_details', []))
    return sorted(aid for aid,result in state.scratch.get('ax_action_results',{}).items()
        if candidate.id in result.get('candidate_ids',[]) or leaves.intersection(result.get('produced_raw_idea_ids',[])))
