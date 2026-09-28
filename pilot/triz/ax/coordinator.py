"""Small policy chooses a bounded action; deterministic governor owns permission."""
from ..context import AbortRun
from .. import domain
from . import ledger
from .contracts import ActionTicket, ACTIONS

TRACKS=('A_MATRIX','B_SEPARATION','C_STANDARDS','D_ARIZ','E_TRIMMING','F_TRENDS','G_FOS','H_EFFECTS')
HANDLERS = {
    'tracks-v1': {'callable':'nodes._run_tracks','model_role':'REASONING','tools':['legacy_tracks']},
    'repair-v1': {'callable':'coherence_recovery.run','model_role':'REASONING','tools':['candidate_repair']},
    'merge-v1': {'callable':'nodes._merge','model_role':'REASONING','tools':['legacy_tracks']},
    'defer-v1': {'callable':None,'model_role':'CODE','tools':[]},
}


def handler_id(ticket):
    if ticket.action_type=='GENERATE_BASELINE' or (ticket.action_type=='SOLVE_SUBPROBLEM' and ticket.parameters.get('tracks')):
        return 'tracks-v1'
    if ticket.action_type in ('REPAIR_CANDIDATE','SOLVE_SUBPROBLEM'):
        return 'repair-v1'
    return {'MERGE_IDEAS':'merge-v1','DEFER':'defer-v1'}.get(ticket.action_type)


def features(state):
    base = [1.0, min(1,len(state.definition.technical_contradictions)/4),
            min(1,len(state.definition.physical_contradictions)/4),
            min(1,len(state.solve.gaps)/4), min(1,len(state.concepts)/3),
            min(1,len(state.evidence)/10), float(domain.physical_allowed(state)),
            max(0,1-state.cost.total_usd/max(.001,state.cost.budget_usd))]
    if state.scratch['ax_bundle'].get('feature_schema') == 'ax-features-v2':
        from .coherence import assess
        report=assess(state)
        gaps=[g for r in report['candidates'] for g in r['gaps']]
        base += [len(report['coverage_gaps'])/max(1,len(report['obligations'])),
                 min(1,len(gaps)/max(1,len(report['candidates'])*3)),
                 min(1,sum(g['kind']=='ADVERSE_SIDE_OMITTED' for g in gaps)/max(1,len(report['candidates']))),
                 min(1,sum(bool(r.get('ancestor_regression')) for r in state.scratch.get('ax_recovery',[]))/4)]
    return base


def feasible(state,ticket,*,handlers):
    """Return a reason on rejection. No policy controls these checks."""
    b=state.scratch['ax_bundle']
    from .mode_contract import contract, optional_enabled, validate_tracks
    if contract(state):
        if ticket.action_type=='CO_DESIGN':
            return 'handler_unavailable'
        try:
            validate_tracks(state, ticket.parameters.get('tracks', []))
        except ValueError:
            return 'mode_forbidden_track'
        if ticket.input_snapshot_id and ticket.input_snapshot_id != state.scratch.get('ax_snapshot_id'):
            return 'stale_input_snapshot'
        if ticket.action_type in ('REPAIR_CANDIDATE', 'SOLVE_SUBPROBLEM', 'CO_DESIGN') and not optional_enabled(state):
            return 'optional_disabled'
        if ticket.action_type in ('REPAIR_CANDIDATE','SOLVE_SUBPROBLEM','CO_DESIGN') and state.scratch.get('ax_coordination'):
            from .mode_contract import coverage
            if not coverage(state)['complete']:
                return 'mandatory_coverage_incomplete'
        if ticket.action_type in ('REPAIR_CANDIDATE','SOLVE_SUBPROBLEM','CO_DESIGN'):
            from .action_runtime import optional_commitment
            if optional_commitment(state)+ticket.reserved_microusd>b['limits']['optional_budget_microusd']:
                return 'optional_phase_budget'
        if ticket.action_type!='DEFER' and (ticket.parameters.get('optional') or ticket.action_type in ('REPAIR_CANDIDATE','SOLVE_SUBPROBLEM','CO_DESIGN')) and ticket.reserved_microusd + b['limits']['validation_reserve_microusd'] > ledger.budget(state.run_id)['remaining_microusd']:
            return 'validation_reserve'
    if ticket.action_type=='ASK_HUMAN':
        return 'coordinator_is_autonomous'
    if ticket.action_type not in handlers:
        return 'handler_unavailable'
    if set(ticket.target_version_ids)-set(state.scratch.get('ax_members',{}).values()):
        return 'stale_or_foreign_target'
    if ticket.action_type=='CHALLENGE_MEANS':
        return 'protected_requirements'
    if ticket.parameters.get('change_requirements'):
        return 'protected_requirements'
    if ticket.parameters.get('depth',0)>b['limits']['depth']:
        return 'depth_limit'
    if ticket.parameters.get('attempt',0)>b['limits']['repairs_per_blocker']:
        return 'repair_limit'
    if len(ticket.parameters.get('tracks',[]))>b['limits']['branches']:
        return 'branch_limit'
    if set(ticket.parameters.get('tracks',[]))-set(TRACKS):
        return 'unknown_track'
    if not domain.physical_allowed(state) and 'C_STANDARDS' in ticket.parameters.get('tracks',[]):
        return 'physical_scope_missing'
    if ticket.action_type=='FINALIZE' and not state.scratch.get('ax_selection',{}).get('recommended'):
        return 'required_validation_missing'
    if set(ticket.allowed_tools)-{'legacy_tracks','evidence_search','deterministic_validation',
                                  'candidate_repair','graph_patch'}:
        return 'tool_not_authorized'
    if ticket.reserved_microusd>ledger.budget(state.run_id)['remaining_microusd']:
        return 'budget_limit'
    return None


def decide(state,proposals,preferred,handlers,context):
    from .mode_contract import contract
    if contract(state):
        return _decide_instances(state, proposals, preferred, handlers, context)
    rows=[]
    for ticket in proposals:
        reason=feasible(state,ticket,handlers=handlers)
        rows.append({'ticket':ticket.model_dump(mode='json'),'allowed':reason is None,'blocked_reason':reason})
    permitted=[i for i,r in enumerate(rows) if r['allowed']]
    if not permitted:
        raise AbortRun('승인된 실행 경로가 없습니다. 요구·근거·예산을 확인해 주세요.')
    proposed=preferred
    chosen=preferred if preferred in permitted else permitted[0]
    policy=state.scratch['ax_bundle'].get('policy')
    mode='RULE_BASED'
    if policy:
        from .learning import choose
        chosen=choose(policy,features(state),[p.action_type for p in proposals],permitted,chosen)
        proposed=chosen
        mode='POLICY_DETERMINISTIC'
    payload={'snapshot_id':state.scratch['ax_snapshot_id'],'context':context,
             'bundle_id':state.scratch['ax_bundle']['bundle_id'],
             'policy_version':state.scratch['ax_bundle']['policy_version'],
             'feature_schema':state.scratch['ax_bundle'].get('feature_schema','ax-features-v1'),
             'features':features(state),'actions':rows,'proposed_index':proposed,'executed_index':chosen,
             'behavior_probability':None,'selection_mode':mode,
             'governor_override':proposed!=chosen,'override_reason':rows[proposed]['blocked_reason'] if proposed!=chosen else None}
    did=ledger.record_decision(state,payload)
    shadow_policy=state.scratch['ax_bundle'].get('shadow_policy')
    if shadow_policy:
        from .learning import choose
        from .registry import observe_shadow
        shadow_index=choose(shadow_policy,payload['features'],[p.action_type for p in proposals],permitted,chosen)
        observe_shadow(state.scratch['ax_bundle']['shadow_policy_version'],did,
            {'run_id':state.run_id,'chosen_index':shadow_index,'executed_index':chosen,
             'legal':shadow_index in permitted,'supported':proposals[shadow_index].action_type in shadow_policy['support_actions']})
    state.scratch['ax_last_decision']=did
    return proposals[chosen],did


def route(ctx):
    state=ctx.state
    if not state.confirm.user_confirmed:
        raise AbortRun('문제 범위를 먼저 확정해 주세요.')
    if not (state.definition.technical_contradictions or state.definition.physical_contradictions):
        raise AbortRun('해결안 탐색 전에 분석의 모순과 근거를 확인해 주세요.')
    if state.solve.tracks_run and not state.scratch.get('ax_track_execution'):
        # Only an explicit S5 continuation reaches this boundary. Historical
        # completed reports remain untouched. Old tracks_run admitted failed or
        # partial calls, so it cannot establish the new completion contract.
        from ..schema import SolveBundle
        state.scratch['ax_solve_compatibility'] = {
            'contract': 'mode-tracks-v1', 'previous_tracks': list(state.solve.tracks_run),
            'reason': '구형 S5 완료 기록을 현재 출력 계약으로 재검증합니다. 동일한 검증 완료 호출은 캐시를 재사용합니다.'}
        state.solve = SolveBundle()
        for key in ('s_curve', 'ax_track_review_reasons', 'ax_track_execution', 'ax_idea_inventory',
                    'ax_expansion_rounds', 'ax_expansion_deferred', 'ax_solve_start_seq'):
            state.scratch.pop(key, None)
    from ..solve_contract import plan
    expected, required, skipped = plan(state)
    from .mode_contract import contract
    branches=max(1,int(state.scratch['ax_bundle']['limits']['branches']))
    tracks=required[:branches]
    pending=required[branches:]
    state.scratch.setdefault('ax_solve_start_seq',len(state.steps))
    execution=state.scratch.setdefault('ax_track_execution',{})
    for track in expected:
        if track in skipped:
            execution[track]={'status':'NOT_APPLICABLE','reason':skipped[track],'output_count':0}
        elif track in state.scratch.get('ax_blocked_tracks', {}):
            execution[track]={'status':'BLOCKED_MISSING_INPUT','reason':state.scratch['ax_blocked_tracks'][track],'output_count':0}
        else:
            execution.setdefault(track,{'status':'PENDING','reason':'필수 분석 실행 대기','output_count':0})
    targets=[state.scratch['ax_members']['definition']]
    ticket=ActionTicket(action_type='GENERATE_BASELINE',target_version_ids=targets,
        parameters={'tracks':tracks,'preserve_requirements':True},expected_outputs=['CandidateVersion','ApplicabilityCheck'],
        allowed_tools=['legacy_tracks','evidence_search'],reason='분석 모드의 필수 경로를 배치 크기 제한 안에서 순차 실행한다.')
    defer=ActionTicket(action_type='DEFER',target_version_ids=targets,parameters={},
        expected_outputs=['Blocker'],allowed_tools=[],reason='예산 또는 적용조건 부족으로 탐색을 보류한다.')
    if contract(state):
        # Mandatory coverage is a deterministic plan, never a routing-Q choice.
        chosen, did = ticket, None
    else:
        chosen,did=decide(state,[ticket,defer],0,{'GENERATE_BASELINE','DEFER'},'s4.route')
    if chosen.action_type=='DEFER':
        raise AbortRun('추가 탐색을 보류했습니다. 조율 기록을 확인해 주세요.')
    state.scratch['ax_coordination']={'decision_id':did,'tracks':chosen.parameters['tracks'],'pending_tracks':pending,
        'required_tracks':required,'expected_tracks':expected,'coverage_contract':'mode-tracks-v1',
        'reason':chosen.reason,'snapshot_id':state.scratch['ax_snapshot_id']}
    state.control.enabled_tracks=required
    ctx.emit('coordination',**state.scratch['ax_coordination'])


def complete_required(ctx):
    """A branch limit bounds concurrency, never the number of required methods."""
    state=ctx.state
    plan=state.scratch['ax_coordination']
    from ..nodes import _run_tracks
    branches=max(1,int(state.scratch['ax_bundle']['limits']['branches']))
    pending=[t for t in plan['required_tracks'] if t not in state.solve.tracks_run]
    while pending:
        selected=pending[:branches]
        ticket=ActionTicket(action_type='GENERATE_BASELINE',
            target_version_ids=[state.scratch['ax_members']['definition']],
            parameters={'tracks':selected,'preserve_requirements':True},
            expected_outputs=['CandidateVersion','ApplicabilityCheck'],
            allowed_tools=['legacy_tracks'],reason='아직 수행하지 않은 분석 모드의 필수 경로를 실행한다.')
        from .mode_contract import contract
        if contract(state):
            chosen, did = ticket, None
        else:
            chosen,did=decide(state,[ticket],0,{'GENERATE_BASELINE'},'solve:required_batch')
        _run_tracks(ctx,chosen.parameters['tracks'])
        remaining=[t for t in plan['required_tracks'] if t not in state.solve.tracks_run]
        if remaining==pending:
            raise AbortRun('필수 분석 실행이 완료되지 않았습니다. S5에서 이어서 실행해 주세요.')
        pending=remaining
        plan['pending_tracks']=pending
        plan.setdefault('batches',[]).append({'decision_id':did,'tracks':selected})
    plan['pending_tracks']=[]


def expand(ctx, need_more):
    """One bounded, problem-driven follow-up through existing TRIZ executors."""
    from .coherence import enabled as coherence_enabled, obligations
    state=ctx.state
    from .mode_contract import contract, optional_enabled
    if not optional_enabled(state):
        return False
    if contract(state):
        return _expand_instances(ctx, need_more)
    if not coherence_enabled(state):
        return False
    limits=state.scratch['ax_bundle']['limits']
    rounds=state.scratch.get('ax_expansion_rounds',0)
    if rounds>=limits.get('expansion_rounds',1):
        return False
    required=obligations(state)
    addressed={cid for i in state.solve.raw_ideas if i.resolution_status!='TRADEOFF' for cid in i.addresses}
    gaps=[o for o in required if not set(o['contradiction_ids'])&addressed]
    pending=[t for t in state.scratch.get('ax_coordination',{}).get('pending_tracks',[]) if t not in state.solve.tracks_run]
    # Deferred applicability/FOS is a meaningful alternative, not an arbitrary extra model call.
    if not pending or not (need_more or gaps or 'H_EFFECTS' in pending):
        return False
    if ledger.budget(state.run_id)['remaining_microusd']<limits['validation_reserve_microusd']+100000:
        state.scratch['ax_expansion_deferred']='검증 예산 보존으로 추가 탐색 보류'
        return False
    selected=pending[:limits['branches']]
    ticket=ActionTicket(action_type='SOLVE_SUBPROBLEM',target_version_ids=[state.scratch['ax_members']['definition']],
        parameters={'tracks':selected,'depth':1,'attempt':rounds+1,'obligation_ids':[o['id'] for o in gaps]},
        expected_outputs=['CandidateVersion'],allowed_tools=['legacy_tracks'],reserved_microusd=100000,
        reason='미대응 문제와 보류된 적용 경로를 추가 탐색한다.')
    chosen,did=decide(state,[ticket],0,{'SOLVE_SUBPROBLEM'},'solve:coverage_expansion')
    from ..nodes import _run_tracks,_merge
    _run_tracks(ctx,chosen.parameters['tracks'])
    state.scratch['ax_expansion_rounds']=rounds+1
    state.scratch['ax_coordination'].setdefault('expansions',[]).append(
        {'decision_id':did,'tracks':selected,'obligation_ids':[o['id'] for o in gaps]})
    _merge(ctx)
    return True


def stage_action(state,action_type,target):
    """Observed code action, still governed and logged; no human wait action."""
    ticket=ActionTicket(action_type=action_type,
        target_version_ids=[state.scratch['ax_members'][target]],
        expected_outputs=['VersionedResult'],allowed_tools=['deterministic_validation'],
        reason={'CHECK_APPLICABILITY':'과학효과의 필요 조건과 검증 의무를 점검한다.',
                'FETCH_EVIDENCE':'후보별 적용 근거를 수집한다.',
                'FINALIZE':'필수 검증을 충족한 후보를 선택한다.',
                'DEFER':'미실행·미확인 검증을 조건부로 보고하고 추가 승인을 기다리지 않는다.'}[action_type])
    from .mode_contract import contract
    if contract(state):
        return ticket, None
    return decide(state,[ticket],0,{action_type},'stage:'+action_type)


def _decide_instances(state, proposals, preferred, handlers, context):
    from . import routing_q
    from .action_runtime import identity, episode, emit
    from .mode_contract import optional_enabled
    if not optional_enabled(state):
        raise AbortRun('이 모드에서는 선택적 AX 작업을 실행하지 않습니다.')
    proposals = [p.model_copy(update={'action_instance_id': identity(state, p, context),
                    'input_snapshot_id': state.scratch['ax_snapshot_id']}) for p in proposals]
    rows = []
    for ticket in proposals:
        reason = feasible(state, ticket, handlers=handlers)
        rows.append(dict(ticket=ticket.model_dump(mode='json'), allowed=reason is None, blocked_reason=reason))
    permitted = [i for i, row in enumerate(rows) if row['allowed']]
    if not permitted:
        raise AbortRun('허용된 선택적 작업이 없습니다.')
    chosen = preferred if preferred in permitted else permitted[0]
    rule_preferred = chosen
    b = state.scratch['ax_bundle']
    fs = routing_q.state_features(state, context)
    tickets = [r['ticket'] for r in rows]
    mode = 'FORCED' if len(permitted) == 1 else 'RULE_BASED'
    scores, fallback = {}, None
    if b.get('policy') and len(permitted) > 1:
        chosen, scores, fallback = routing_q.choose(b['policy'], fs, tickets, permitted, chosen)
        if fallback is None:
            mode = 'POLICY_DETERMINISTIC'
    payload = dict(snapshot_id=state.scratch['ax_snapshot_id'], context=context, bundle_id=b['bundle_id'],
        policy_version=b['policy_version'], feature_schema=routing_q.SCHEMA, features=fs,
        actions=rows, proposed_index=chosen, executed_index=chosen, rule_preferred=rule_preferred,
        model_scores=scores, permitted_actions=permitted, selection_mode=mode, fallback_reason=fallback,
        policy_kind='routing_q', behavior_probability=None, governor_override=False, override_reason=None,
        semantic_episode_id=episode(state), decision_sequence=state.scratch.get('ax_optional_sequence', 0),
        executed_action_instance=proposals[chosen].action_instance_id)
    did = ledger.record_decision(state, payload)
    previous = state.scratch.get('ax_optional_previous')
    if previous and previous != did:
        emit(state, 'OPTIONAL_TRANSITION', {'semantic_episode_id': episode(state), 'decision_id':previous,
             'next_decision_id':did, 'terminal_reason':None})
    state.scratch['ax_optional_previous'] = did
    state.scratch['ax_optional_sequence'] = payload['decision_sequence'] + 1
    state.scratch['ax_last_decision'] = did
    state.scratch['ax_policy_usage'] = {'selection_mode':mode, 'fallback_reason':fallback,
        'policy_version':b['policy_version'], 'executed_action_instance':proposals[chosen].action_instance_id,
        'reason':proposals[chosen].reason}
    if proposals[chosen].action_type == 'DEFER':
        emit(state, 'OPTIONAL_TRANSITION', {'semantic_episode_id':episode(state), 'decision_id':did,
             'next_decision_id':None, 'terminal_reason':'DEFER_OPTIONAL'})
        state.scratch.pop('ax_optional_previous', None)
    if b.get('shadow_policy') and len(permitted) > 1:
        from .registry import observe_shadow
        index, shadow_scores, why = routing_q.choose(b['shadow_policy'], fs, tickets, permitted, rule_preferred)
        observe_shadow(b['shadow_policy_version'], did, dict(run_id=state.run_id, chosen_index=index,
            executed_index=chosen, legal=index in permitted, supported=why is None, scores=shadow_scores,
            counterfactual_result=None))
    return proposals[chosen], did


def defer_ticket(state):
    return ActionTicket(action_type='DEFER', parameters={'optional':True}, expected_outputs=['OptionalCompletion'],
        allowed_tools=[], reason='미확인 의무를 남기고 선택적 탐색을 종료한다. 필수 검토는 계속한다.')


def _expand_instances(ctx, need_more):
    from .coherence import obligations
    from .mode_contract import contract
    from .action_runtime import executing
    state = ctx.state; limits = state.scratch['ax_bundle']['limits']
    rounds = state.scratch.get('ax_expansion_rounds', 0)
    if rounds >= limits['expansion_rounds'] or not need_more or state.scratch.get('ax_optional_sequence',0)>=limits['max_optional_rounds'] or state.scratch.get('ax_optional_deferred_budget'):
        return False
    addressed = {cid for i in state.solve.raw_ideas if i.resolution_status == 'RESOLVED' for cid in i.addresses}
    gaps = [o for o in obligations(state) if not set(o['contradiction_ids']) & addressed]
    if not gaps:
        return False
    if state.scratch.get('ax_blocked_tracks'):
        return False  # Never spend optional budget before required input is resolved.
    proposals = [ActionTicket(action_type='SOLVE_SUBPROBLEM', model_role='REASONING',
        target_version_ids=[state.scratch['ax_members']['definition']],
        parameters={'tracks':[t], 'optional':True, 'attempt':rounds + 1, 'depth':1,
                    'obligation_ids':[o['id'] for o in gaps], 'gap_kinds':['UNCOVERED_OBLIGATION']},
        expected_outputs=['RawIdea'], allowed_tools=['legacy_tracks'], reserved_microusd=100000,
        reason='미대응 모순에 대해 허용된 기법으로 다른 적용 경로를 탐색한다.')
        for t in contract(state)['profile']['tracks'] if t in ('H_EFFECTS', 'G_FOS', 'A_MATRIX')]
    proposals.append(defer_ticket(state))
    chosen, did = decide(state, proposals, 0, {'SOLVE_SUBPROBLEM','DEFER'}, 'solve:coverage_expansion')
    if chosen.action_type == 'DEFER':
        state.scratch['ax_expansion_rounds'] = limits['expansion_rounds']
        return False
    from ..nodes import _run_tracks, _merge
    from ..context import RunContext
    from ..schema import SolveBundle
    branch = state.model_copy(deep=True)
    branch.solve = SolveBundle()
    branch.solve.gaps = ['미대응 모순: ' + ', '.join(chosen.parameters['obligation_ids'])]
    branch.steps, branch.cost, branch.control = state.steps, state.cost, state.control
    child = RunContext(branch)
    child.lock, child.budget, child.call_slots = ctx.lock, ctx.budget, ctx.call_slots
    with executing(child, chosen, did, context='solve:coverage_expansion'):
        _run_tracks(child, chosen.parameters['tracks'])
    if branch.scratch.get('ax_optional_deferred_budget'):
        state.scratch['ax_optional_deferred_budget']=branch.scratch['ax_optional_deferred_budget']
        state.scratch.setdefault('ax_action_results',{}).update(branch.scratch.get('ax_action_results',{}))
        return False
    # Existing ideas remain inputs to the same complete merge/quality path.
    for key in ('matrix_lookups','principle_apps','separation_apps','standard_apps','trend_apps','fos_apps','effect_apps','raw_ideas'):
        getattr(state.solve, key).extend(getattr(branch.solve, key))
    state.scratch.setdefault('ax_action_results', {}).update(branch.scratch.get('ax_action_results', {}))
    state.scratch['ax_expansion_rounds'] = rounds + 1
    state.scratch['ax_coordination'].setdefault('expansions', []).append({'decision_id':did,'tracks':chosen.parameters['tracks']})
    _merge(ctx)
    return True
