"""Autonomous, bounded recovery. Baselines survive; only new candidates are added."""
import copy
from pydantic import Field
from .. import agent
from ..context import RunContext
from ..schema import ConceptSpec
from . import ledger,coordinator,concept_effects
from .contracts import Contract,ActionTicket,digest


class Proposal(Contract):
    title: str=Field(min_length=1,max_length=300)
    working_principle: str=Field(min_length=1,max_length=4000)
    resolution_argument: str=Field(min_length=1,max_length=4000)
    changes_to_system: list[str]=Field(max_length=12)
    required_resources: list[str]=Field(max_length=12)
    assumptions: list[str]=Field(max_length=12)
    open_risks: list[str]=Field(max_length=12)
    validation_plan: list[dict]=Field(min_length=1,max_length=8)
    provided_functions: list[str]=Field(max_length=12)
    required_functions: list[str]=Field(max_length=12)
    subproblem: str=''


class EffectProposal(Proposal):
    active_effect_ids: list[str] = Field(description='Explicit IDs of source effects retained in this proposal; [] when none are retained.')


def effect_analysis(state, source_ids, analysis):
    """Extend only new-contract requests; old request variables stay unchanged."""
    if not concept_effects.enabled(state):
        return analysis
    return dict(analysis, source_effects=concept_effects.sources(state, source_ids),
        effect_contract='active_effect_ids is required. Include only source_effect_id values from source_effects '
        'that the proposed working principle actually retains. Reassess adoption after the repair or joint design; '
        'do not inherit the baseline list or label every exposed effect as used. Return [] if none are retained. '
        'Preserve unverified conditions and hypotheses; listing an effect is not validation of technical performance.')


def effect_errors(state, source_ids, raw):
    if not concept_effects.enabled(state):
        return []
    return concept_effects.validate(raw, concept_effects.allowed(state, source_ids))


def complementary(left,right,external_functions):
    """Both sides must add a needed function, with an external starting resource."""
    lp,rp=set(left.get('provided_functions',[])),set(right.get('provided_functions',[]))
    ln,rn=set(left.get('required_functions',[])),set(right.get('required_functions',[]))
    if not lp or not rp or lp==rp: return False
    if not (lp&rn or rp&ln): return False
    if not (ln|rn)<=lp|rp|set(external_functions): return False
    # A closed dependency cycle cannot bootstrap itself.
    return bool((ln|rn)&set(external_functions)) or not ln or not rn


def run(ctx,phase='before_constraints'):
    from .mode_contract import optional_enabled
    if not optional_enabled(ctx.state):
        return []
    from .coherence import enabled as coherence_enabled
    if coherence_enabled(ctx.state):
        from .coherence_recovery import run as repair
        return repair(ctx,phase)
    state=ctx.state
    limits=state.scratch['ax_bundle']['limits']
    if state.scratch.get('ax_recovery_complete'): return
    state.scratch.setdefault('ax_baseline_candidates',[c.model_dump(mode='json') for c in state.concepts])
    source={c.id:c for c in state.concepts}
    for raw in state.scratch.get('ax_excluded',[]):
        c=ConceptSpec.model_validate(raw)
        source.setdefault(c.id,c)
    targets=[c for c in source.values() if c.quality_status in ('REVISE','REJECT')][:limits['recovery_targets']]
    journal=state.scratch.setdefault('ax_recovery',[])
    protected=digest(state.constraints.model_dump(mode='json'))
    for baseline in targets:
        if sum(row.get('status') == 'PROPOSED_REQUIRES_GATE' for row in journal) >= limits.get('recovery_additions', 4): break
        blockers=list(baseline.quality_issues) or ['독립 기구 검토 미통과']
        blocker_id='blocker-'+digest([baseline.id,blockers])[:24]
        attempts=[x for x in journal if x['blocker_id']==blocker_id]
        for attempt in range(len(attempts),limits['repairs_per_blocker']):
            if sum(row.get('status') == 'PROPOSED_REQUIRES_GATE' for row in journal) >= limits.get('recovery_additions', 4): break
            remaining=ledger.budget(state.run_id)['remaining_microusd']
            if remaining<limits['validation_reserve_microusd']+50000:
                journal.append({'blocker_id':blocker_id,'candidate_id':baseline.id,'status':'DEFERRED_BUDGET'})
                break
            action='REPAIR_CANDIDATE' if attempt==0 else 'SOLVE_SUBPROBLEM'
            parameters={'attempt':attempt+1,'depth':1,'candidate_id':baseline.id,'blocker_id':blocker_id}
            tickets=[ActionTicket(action_type=action,target_version_ids=[state.scratch['ax_members']['concepts']],
                parameters=parameters,expected_outputs=['CandidateVersion','Blocker'],allowed_tools=['candidate_repair'],
                model_role='FLASH',reserved_microusd=50000,reason='기준안을 보존하고 미해결 기구를 제한적으로 복구한다.'),
                ActionTicket(action_type='DEFER',target_version_ids=[state.scratch['ax_members']['concepts']],
                    expected_outputs=['Blocker'],allowed_tools=[],reason='검증 의무를 남기고 자동으로 다음 단계에 진행한다.')]
            chosen,did=coordinator.decide(state,tickets,0,{action,'DEFER'},'recovery:'+blocker_id)
            if chosen.action_type=='DEFER':
                journal.append({'blocker_id':blocker_id,'candidate_id':baseline.id,'status':'DEFERRED','decision_id':did})
                break
            source_ids=list(baseline.source_idea_ids)
            proposal_model=EffectProposal if concept_effects.enabled(state) else Proposal
            raw=agent.run_agent(ctx,node='ax_recovery_'+baseline.id+'_'+str(attempt),label='기구 복구',
                stage='S6_CONCEPT',agent_id='effects_specialist',prompt_id='P_AX_RECOVERY',tier='T2',
                vars={'action':chosen.action_type,'baseline':baseline.model_dump(mode='json'),
                      'blockers':blockers,'requirements':state.constraints.model_dump(mode='json'),
                      'analysis':effect_analysis(state,source_ids,{'contradictions':state.definition.model_dump(mode='json'),
                                  'resources':[r.model_dump(mode='json') for r in state.analysis.resources]}),
                      'schema':proposal_model.model_json_schema()},default={}) or {}
            entry={'blocker_id':blocker_id,'candidate_id':baseline.id,'decision_id':did,
                'action':chosen.action_type,'attempt':attempt+1,'depth':1,'status':'INVALID_PROPOSAL'}
            errors=effect_errors(state,source_ids,raw)
            if errors:
                journal.append(dict(entry,effect_contract_errors=errors))
                continue
            try:
                proposal=proposal_model.model_validate(raw)
            except ValueError:
                journal.append(entry)
                continue
            data=baseline.model_dump(mode='json')
            data.update({k:v for k,v in proposal.model_dump(mode='json').items() if k in ConceptSpec.model_fields})
            data.update(id='CPT-AX-'+digest([did,raw])[:12],quality_status='UNVERIFIED',quality_issues=[],evidence_ids=[],
                expected_effect='복구 기구의 효과는 미검증이며 시험 결과가 필요하다.')
            repaired=ConceptSpec.model_validate(data)
            # Reuse the independent quality verifier in an isolated candidate branch.
            from ..quality import audit_concepts
            branch=state.model_copy(deep=True)
            branch.concepts=[repaired]
            branch.scratch['s6_quality_batches']=state.scratch.setdefault('s6_quality_batches',{})
            branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
            bctx=RunContext(branch); bctx.lock,bctx.budget,bctx.call_slots=ctx.lock,ctx.budget,ctx.call_slots
            bctx.persist=ctx.persist
            audit_concepts(bctx)
            accepted=branch.concepts and branch.concepts[0].quality_status=='PASS'
            entry.update(status='PROPOSED_REQUIRES_GATE' if accepted else 'UNRESOLVED',
                proposal=proposal.model_dump(mode='json'),derived_candidate_id=repaired.id,
                preserved_baseline_id=baseline.id)
            journal.append(entry)
            if digest(state.constraints.model_dump(mode='json'))!=protected:
                raise ValueError('Recovery changed protected requirements')
            if accepted:
                state.concepts.append(branch.concepts[0])
                break
    pairs=[x for x in journal if x.get('proposal')]
    if sum(row.get('status') == 'PROPOSED_REQUIRES_GATE' for row in journal) < limits.get('recovery_additions', 4) and len(pairs)>=2:
        left,right=pairs[0],pairs[-1]
        external=[r.name for r in state.analysis.resources]
        if left['candidate_id']!=right['candidate_id'] and complementary(left['proposal'],right['proposal'],external):
            codesign(ctx,left,right,source)
    state.scratch['ax_recovery_complete']=True
    from .runtime import DEPENDENCIES,section
    ledger.capture(state,{'concepts':section(state,'concepts')},DEPENDENCIES,'bounded_recovery')


def codesign(ctx,left,right,baselines):
    state=ctx.state
    limits=state.scratch['ax_bundle']['limits']
    if ledger.budget(state.run_id)['remaining_microusd']<limits['validation_reserve_microusd']+50000: return
    if any(x.get('action')=='CO_DESIGN' for x in state.scratch['ax_recovery']): return
    ticket=ActionTicket(action_type='CO_DESIGN',target_version_ids=[state.scratch['ax_members']['concepts']],
        parameters={'depth':2,'attempt':1,'partners':[left['candidate_id'],right['candidate_id']]},
        expected_outputs=['CandidateVersion','InteractionCheck'],allowed_tools=['candidate_repair'],
        reserved_microusd=50000,model_role='FLASH',reason='서로 보완하는 기능과 외부 시작 자원이 확인된 두 기구를 공동 설계한다.')
    chosen,did=coordinator.decide(state,[ticket],0,{'CO_DESIGN'},'recovery:codesign')
    source_ids=list(dict.fromkeys(sid for row in (left,right)
        for sid in baselines[row['candidate_id']].source_idea_ids))
    proposal_model=EffectProposal if concept_effects.enabled(state) else Proposal
    raw=agent.run_agent(ctx,node='ax_codesign',label='상호작용 공동 설계',stage='S6_CONCEPT',agent_id='effects_specialist',
        prompt_id='P_AX_RECOVERY',tier='T2',vars={'action':chosen.action_type,
            'baseline':[baselines[x['candidate_id']].model_dump(mode='json') for x in (left,right)],
            'blockers':[left['proposal'],right['proposal']],'requirements':state.constraints.model_dump(mode='json'),
            'analysis':effect_analysis(state,source_ids,{'external_resources':[r.name for r in state.analysis.resources]}),
            'schema':proposal_model.model_json_schema()},default={}) or {}
    entry={'action':'CO_DESIGN','blocker_id':'joint-'+digest([left['blocker_id'],right['blocker_id']])[:24],
        'candidate_id':left['candidate_id'],'partners':[left['candidate_id'],right['candidate_id']],
        'decision_id':did,'status':'INVALID_PROPOSAL','depth':2}
    errors=effect_errors(state,source_ids,raw)
    if errors:
        state.scratch['ax_recovery'].append(dict(entry,effect_contract_errors=errors))
        return
    try:
        proposal=proposal_model.model_validate(raw)
    except ValueError:
        state.scratch['ax_recovery'].append(entry)
        return
    base=baselines[left['candidate_id']].model_dump(mode='json')
    base.update({k:v for k,v in proposal.model_dump(mode='json').items() if k in ConceptSpec.model_fields})
    if concept_effects.enabled(state):
        base['source_idea_ids']=source_ids
    base.update(id='CPT-AX-'+digest([did,raw])[:12],quality_status='UNVERIFIED',quality_issues=[],evidence_ids=[],
        expected_effect='공동 설계의 상호작용과 성능은 독립 검증 및 시험 필요')
    from ..quality import audit_concepts
    branch=state.model_copy(deep=True); branch.concepts=[ConceptSpec.model_validate(base)]
    branch.scratch['s6_quality_batches']=state.scratch.setdefault('s6_quality_batches',{})
    branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
    bctx=RunContext(branch); bctx.lock,bctx.budget,bctx.call_slots=ctx.lock,ctx.budget,ctx.call_slots
    bctx.persist=ctx.persist
    audit_concepts(bctx)
    accepted=branch.concepts and branch.concepts[0].quality_status=='PASS'
    entry.update(status='PROPOSED_REQUIRES_GATE' if accepted else 'UNRESOLVED',proposal=proposal.model_dump(mode='json'))
    state.scratch['ax_recovery'].append(entry)
    if accepted: state.concepts.append(branch.concepts[0])
