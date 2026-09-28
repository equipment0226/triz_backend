"""Sequential real track choices; S5 stop hands off to mandatory review."""
import json
import math
import re
from sqlalchemy import select
from . import ledger, mode_contract
from .contracts import ActionTicket, digest, now
from .action_runtime import executing, episode, emit


def state_features(state, phase):
    from .routing_q import ADAPTIVE_SCHEMA
    budget = ledger.budget(state.run_id, state.user_id)
    return dict(schema=ADAPTIVE_SCHEMA, mode=state.control.mode.value, phase=phase,
        domain=state.domain.problem_type, remaining=budget['remaining_microusd']/max(1,budget['limit_microusd']),
        actual_microusd=budget['spent_microusd'], unresolved_reserve=budget['reserved_microusd'],
        mandatory_review_reserve=state.scratch['ax_bundle']['limits']['validation_reserve_microusd'],
        problem_terms=sorted(set(re.findall(r'[\w]+', state.raw_query.casefold())))[:96],
        tracks=sorted(state.solve.tracks_run), gaps=sorted(set(state.solve.gaps)),
        uncovered=sorted(set(state.solve.gaps)), review_available=bool(state.scratch.get('ax_candidate_review',{}).get('audit_completed_concept_ids')),
        candidates={c.id:dict(quality=c.quality_status,conditional=bool(state.check_for(c.id) and state.check_for(c.id).verdict=='CONDITIONAL')) for c in state.concepts},
        attempts=len(state.scratch.get('ax_recovery',[]))/6,
        search_status=state.scratch.get('adaptive_search',{}).get('status','PENDING'))


def prepare(state):
    expected, required, skipped, blocked = mode_contract.execution_plan(state)
    execution = state.scratch.setdefault('ax_track_execution', {})
    for t in expected:
        if t in skipped: execution[t] = dict(status='NOT_APPLICABLE',reason=skipped[t],output_count=0)
        elif t in blocked: execution[t] = dict(status='BLOCKED_MISSING_INPUT',reason=blocked[t],output_count=0)
        else: execution.setdefault(t,dict(status='PENDING',reason='정책 선택 대기',output_count=0))
    eligible = [t for t in expected if t not in skipped and t not in blocked]
    state.scratch['ax_coordination'] = dict(tracks=[], pending_tracks=[], required_tracks=required,
        expected_tracks=expected, eligible_tracks=eligible, coverage_contract=mode_contract.ADAPTIVE_PROFILE)
    state.control.enabled_tracks = eligible
    return eligible, required


def estimate(state, track):
    """An explicit prior, optionally informed by settled calls; never actual usage."""
    config = state.scratch['ax_bundle']['models']['T2']
    prior = math.ceil(((len(state.raw_query.encode())+16000)*config['cost_in'] + config['max_tokens']*config['cost_out'])
                      * state.scratch['ax_bundle']['config']['ax'].get('max_provider_attempts',2))
    with ledger.store.engine.connect() as c:
        rows = c.execute(select(ledger.tasks.c.actual,ledger.attempts.c.details).join(ledger.attempts,ledger.attempts.c.task_id==ledger.tasks.c.task_id)
            .join(ledger.heads,ledger.heads.c.run_id==ledger.tasks.c.run_id)
            .where(ledger.heads.c.owner_id==state.user_id,ledger.heads.c.project_id==state.scratch.get('ax_project_id',state.user_id),ledger.tasks.c.actual.is_not(None))).all()
    observed=[]
    for row in rows:
        request=json.loads(row.details).get('request',{})
        if not isinstance(request,dict) or not isinstance(request.get('request',{}),dict): continue
        if (request.get('request',{}).get('model_config',{}).get('model')==config['model']
            and track in request.get('action_context',{}).get('ticket',{}).get('parameters',{}).get('tracks',[])):
            observed.append(row.actual)
    return dict(estimated=True, prior_microusd=prior, estimate_microusd=sorted(observed)[len(observed)//2] if observed else prior,
                reservation_microusd=max(prior,max(observed,default=0)), support=len(observed), basis='pinned-price-token-prior-and-settled-usage-v1')


def proposals(state, phase='initial'):
    eligible, required = prepare(state)
    pending = [t for t in eligible if t not in state.solve.tracks_run]
    rows = []
    required_pending = [t for t in required if t in pending]
    for track in required_pending or pending:
        cost = estimate(state,track)
        parameters = dict(tracks=[track], plan_class='INITIAL_SELECTION' if phase=='initial' else 'FOLLOWUP_SELECTION',
                          cost_estimate=cost, depth=1, preserve_requirements=True)
        if phase!='initial':
            from .exploration_context import build
            from .coherence import obligations
            targets = [o['id'] for o in obligations(state)]
            if targets:
                context = build(state, targets, ['REVIEW_GAP'])
                parameters.update(exploration_context=context,semantic_context_hash=digest(context))
        rows.append(ActionTicket(action_type='RUN_TRACK',parameters=parameters,model_role='REASONING',
            reserved_microusd=cost['reservation_microusd'],expected_outputs=['TrackResult'],allowed_tools=['legacy_tracks'],
            target_version_ids=[state.scratch['ax_members']['definition']],reason='현재 문제에서 아직 실행하지 않은 허용 기법을 검토한다.'))
    minimum = min(mode_contract.contract(state)['minimum_initial_tracks'],len(eligible))
    _, _, skipped, blocked = mode_contract.execution_plan(state)
    no_applicable = not eligible and not blocked
    if not required_pending and not (set(blocked)&set(mode_contract.contract(state).get('explicit_required_tracks',[]))) and (len(state.solve.tracks_run)>=minimum and state.solve.tracks_run or no_applicable):
        rows.append(ActionTicket(action_type='STOP_EXPLORATION',parameters={'plan_class':'PHASE_STOP','phase':phase},
            expected_outputs=['SearchPhaseResult'],allowed_tools=[],reason='추가 트랙 탐색을 종료하고 필수 독립·제약·최종 검토로 진행한다.'))
    return rows


def run(ctx, *, phase='initial', max_steps=None):
    from .. import nodes
    from .coordinator import decide, feasible
    state = ctx.state
    search = state.scratch.setdefault('adaptive_search',{})
    if phase=='initial' and search.get('status') in ('READY_FOR_REVIEW','NO_APPLICABLE_TRACKS'):
        return []
    before = set(state.solve.tracks_run)
    if phase=='initial' and not search.get('evidence_planned'):
        nodes._evidence(ctx)
        search['evidence_planned'] = True
    search['status'] = 'SEARCHING'
    cap = max_steps if max_steps is not None else len(mode_contract.contract(state)['profile']['tracks'])+1
    for _ in range(cap):
        tickets = proposals(state,phase)
        legal = [i for i,t in enumerate(tickets) if feasible(state,t,handlers={'RUN_TRACK','STOP_EXPLORATION'}) is None]
        if not legal:
            reasons = [feasible(state,t,handlers={'RUN_TRACK','STOP_EXPLORATION'}) for t in tickets]
            budget_reasons = {'generation_budget','validation_reserve','optional_phase_budget','budget_limit'}
            search['status'] = 'PARTIAL_BUDGET' if any(r in budget_reasons for r in reasons) else 'BLOCKED_MISSING_INPUT'
            for t in tickets:
                for track in t.parameters.get('tracks',[]):
                    state.scratch['ax_track_execution'][track] = dict(status='NOT_RUN_BUDGET' if search['status']=='PARTIAL_BUDGET' else 'BLOCKED_MISSING_INPUT',reason='; '.join(str(r) for r in reasons),output_count=0)
            break
        stop = next((i for i in legal if tickets[i].action_type=='STOP_EXPLORATION'),None)
        run_indices = [i for i in legal if tickets[i].action_type=='RUN_TRACK']
        preferred = stop if stop is not None and (not search.get('need_more') or not run_indices) else min(run_indices or legal,
            key=lambda i:(tickets[i].parameters.get('cost_estimate',{}).get('estimate_microusd',0),i))
        # Persist the selected action before dispatch. A resume never reselects an unfinished decision.
        pending = search.get('pending')
        if pending:
            ticket, did = ActionTicket.model_validate(pending['ticket']), pending['decision_id']
        else:
            ticket, did = decide(state,tickets,preferred,{'RUN_TRACK','STOP_EXPLORATION'},'adaptive:'+phase)
            search['pending'] = dict(ticket=ticket.model_dump(mode='json'),decision_id=did)
            ctx.persist()
        from ..context import AbortRun
        try:
            with executing(ctx,ticket,did,context='adaptive:'+phase,optional=phase!='initial'):
                if ticket.action_type=='RUN_TRACK':
                    nodes._run_tracks(ctx,ticket.parameters['tracks'])
                else:
                    search['status'] = 'READY_FOR_REVIEW' if state.solve.tracks_run else 'NO_APPLICABLE_TRACKS'
                    search['technical_success'] = False
        except AbortRun as exc:
            if not any(reason in str(exc) for reason in ('Initial generation budget','Insufficient budget','Optional AX budget')):
                raise  # UNKNOWN/provider failures retain their explicit recovery path.
            search.update(status='PARTIAL_BUDGET',technical_success=False)
            for track in ticket.parameters.get('tracks',[]):
                state.scratch['ax_track_execution'][track]=dict(status='NOT_RUN_BUDGET',reason=str(exc),output_count=0)
            search.pop('pending',None)
            break
        search.pop('pending',None)
        if ticket.action_type=='STOP_EXPLORATION':
            break
        search['need_more'] = nodes._merge(ctx)
        # Merge is outside the selected producer action, retaining its own accounting identity.
        ctx.persist()
    for t, row in state.scratch['ax_track_execution'].items():
        if row['status']=='PENDING' and search.get('status') in ('READY_FOR_REVIEW','NO_APPLICABLE_TRACKS'):
            row.update(status='NOT_SELECTED_BY_POLICY',reason='정책/명시적 규칙에 따라 이번 탐색에서 선택하지 않음')
    search['finished_at'] = now()
    ctx.persist()
    return sorted(set(state.solve.tracks_run)-before)


def followup(ctx, phase):
    """Bounded delta exploration prompted by saved independent review gaps."""
    from .coherence_recovery import targets, run as repair
    from .runtime import checkpoint
    from ..quality import generate_concepts
    state=ctx.state;search=state.scratch.setdefault('adaptive_search',{})
    if not mode_contract.optional_enabled(state): return []
    if state.scratch.get('resume_payload') or state.scratch.get('ax_gate_response_pending'): return []
    # A human rejection is not permission to recreate the same dropped portfolio.
    if not state.concepts and state.scratch.get('adaptive_dropped_candidates'): return []
    key=digest([phase,[c.model_dump(mode='json') for c in state.concepts],state.constraints.model_dump(mode='json')])
    processed=search.setdefault('reviewed_inputs',[])
    if key in processed: return []
    gaps=targets(state,phase)
    limits=state.scratch['ax_bundle']['limits']
    before={c.id for c in state.concepts}
    if (gaps or not state.concepts) and search.get('followup_rounds',0)<limits['expansion_rounds']:
        search['followup_rounds']=search.get('followup_rounds',0)+1
        search['need_more']=True
        tracks=run(ctx,phase=phase,max_steps=1)
        if tracks:
            generate_concepts(ctx)
            checkpoint(state,'s6_concept')
    if gaps and search.get('status')!='PARTIAL_BUDGET':
        repair(ctx,phase)
    if search.get('status')=='SEARCHING': search['status']='READY_FOR_REVIEW'
    processed.append(key)
    processed.append(digest([phase,[c.model_dump(mode='json') for c in state.concepts],state.constraints.model_dump(mode='json')]))
    ctx.persist()
    return sorted({c.id for c in state.concepts}-before)
