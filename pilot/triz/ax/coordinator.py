"""Small policy chooses a bounded action; deterministic governor owns permission."""
from ..context import AbortRun
from .. import domain
from . import ledger
from .contracts import ActionTicket, ACTIONS

TRACKS=('A_MATRIX','B_SEPARATION','C_STANDARDS','D_ARIZ','E_TRIMMING','F_TRENDS','G_FOS','H_EFFECTS')


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
    from .coherence import enabled as coherence_enabled
    tracks=[]
    if state.definition.technical_contradictions:
        tracks.append('A_MATRIX')
    if state.definition.physical_contradictions:
        tracks.append('B_SEPARATION')
    pending=[]
    if coherence_enabled(state):
        if domain.physical_allowed(state) and state.analysis.su_fields:
            tracks.append('C_STANDARDS')
        if state.definition.trimming:
            pending.append('E_TRIMMING')
        if state.analysis.function_edges:
            pending.append('G_FOS')
        pending.append('D_ARIZ')
    if 'H_EFFECTS' not in tracks:
        tracks.append('H_EFFECTS')
    pending=list(dict.fromkeys(tracks[3:]+pending))
    tracks=tracks[:3]
    targets=[state.scratch['ax_members']['definition']]
    ticket=ActionTicket(action_type='GENERATE_BASELINE',target_version_ids=targets,
        parameters={'tracks':tracks,'preserve_requirements':True},expected_outputs=['CandidateVersion','ApplicabilityCheck'],
        allowed_tools=['legacy_tracks','evidence_search'],reason='확정된 모순과 필요 기능에 연결되는 기준 경로를 최대 3개 실행한다.')
    defer=ActionTicket(action_type='DEFER',target_version_ids=targets,parameters={},
        expected_outputs=['Blocker'],allowed_tools=[],reason='예산 또는 적용조건 부족으로 탐색을 보류한다.')
    chosen,did=decide(state,[ticket,defer],0,{'GENERATE_BASELINE','DEFER'},'s4.route')
    if chosen.action_type=='DEFER':
        raise AbortRun('추가 탐색을 보류했습니다. 조율 기록을 확인해 주세요.')
    state.scratch['ax_coordination']={'decision_id':did,'tracks':chosen.parameters['tracks'],'pending_tracks':pending,
        'reason':chosen.reason,'snapshot_id':state.scratch['ax_snapshot_id']}
    state.control.enabled_tracks=list(chosen.parameters['tracks'])
    ctx.emit('coordination',**state.scratch['ax_coordination'])


def expand(ctx, need_more):
    """One bounded, problem-driven follow-up through existing TRIZ executors."""
    from .coherence import enabled as coherence_enabled, obligations
    state=ctx.state
    if not coherence_enabled(state):
        return False
    limits=state.scratch['ax_bundle']['limits']
    rounds=state.scratch.get('ax_expansion_rounds',0)
    if rounds>=limits.get('expansion_rounds',1):
        return False
    required=obligations(state)
    addressed={cid for i in state.solve.raw_ideas if i.resolution_status!='TRADEOFF' for cid in i.addresses}
    gaps=[o for o in required if not set(o['contradiction_ids'])&addressed]
    count=len({i.mechanism_key or i.id for i in state.solve.raw_ideas if i.resolution_status!='TRADEOFF'})
    pending=[t for t in state.scratch.get('ax_coordination',{}).get('pending_tracks',[]) if t not in state.solve.tracks_run]
    # Deferred applicability/FOS is a meaningful alternative, not an arbitrary extra model call.
    if not pending or not (need_more or gaps or count<limits['detailed_candidates'] or 'H_EFFECTS' in pending):
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
    return decide(state,[ticket],0,{action_type},'stage:'+action_type)
