"""Repair explicit gaps with bounded existing agents; retain every baseline."""
import copy
from pydantic import Field
from . import coherence, coordinator, ledger
from .contracts import ActionTicket, digest
from .recovery import Proposal
from ..schema import ConceptSpec
from ..context import RunContext


class RepairProposal(Proposal):
    addresses_contradictions: list[str] = Field(min_length=1)
    coherence: coherence.Mechanism


def targets(state, phase):
    assessment=coherence.assess(state)
    by_id={c.id:c for c in state.concepts}
    output=[]
    addressed={oid for r in assessment['candidates'] for oid in r['obligation_ids']}
    for gap in assessment['coverage_gaps']:
        if gap['id'] not in addressed:
            output.append({'candidate_id':'scope-'+gap['id'],'baseline':None,'obligation_ids':[gap['id']],
                'gaps':[gap],'action':'SOLVE_SUBPROBLEM'})
    for row in assessment['candidates']:
        c=by_id[row['candidate_id']]
        if row['gaps'] or c.quality_status in ('REVISE','REJECT'):
            output.append({'candidate_id':c.id,'baseline':c,'obligation_ids':row['obligation_ids'],
                'gaps':row['gaps'] or [{'kind':'QUALITY_REVIEW','description':'; '.join(c.quality_issues)}],
                'action':'REPAIR_CANDIDATE'})
    if phase=='after_constraints':
        failures=state.scratch.get('ax_constraint_failures',{})
        for raw in state.scratch.get('ax_excluded',[]):
            if raw['id'] not in failures or raw['id'] in by_id:
                continue
            c=ConceptSpec.model_validate(raw)
            output.append({'candidate_id':c.id,'baseline':c,
                'obligation_ids':[o['id'] for o in assessment['obligations'] if set(o['contradiction_ids'])&set(c.addresses_contradictions)],
                'gaps':[{'kind':'CONSTRAINT_FAILURE','description':failures[c.id]}],'action':'REPAIR_CANDIDATE'})
    if not output and assessment['shortfall'] and assessment['obligations']:
        output.append({'candidate_id':'portfolio','baseline':None,
            'obligation_ids':[o['id'] for o in assessment['obligations']],
            'gaps':[{'kind':'CANDIDATE_SHORTFALL','description':'다른 개입 위치·기구의 대안을 탐색한다. 기존 안을 이름만 바꾸지 않는다.'}],
            'action':'SOLVE_SUBPROBLEM'})
    return output


def run(ctx, phase):
    state=ctx.state
    limits=state.scratch['ax_bundle']['limits']
    complete=state.scratch.setdefault('ax_recovery_phases',[])
    if phase in complete:
        return []
    state.scratch.setdefault('ax_baseline_candidates',[c.model_dump(mode='json') for c in state.concepts])
    journal=state.scratch.setdefault('ax_recovery',[])
    protected=digest(state.constraints.model_dump(mode='json'))
    added=[]
    for target in targets(state,phase)[:limits['recovery_targets']]:
        blocker='gap-'+digest([target['candidate_id'],target['gaps'],target['obligation_ids']])[:24]
        prior=[x for x in journal if x.get('blocker_id')==blocker and x.get('attempt')]
        for attempt in range(len(prior),limits['repairs_per_blocker']):
            if sum(x.get('status')=='PROPOSED_REQUIRES_GATE' for x in journal)>=limits.get('recovery_additions',4):
                break
            entry={'blocker_id':blocker,'candidate_id':target['candidate_id'],'phase':phase,
                   'obligation_ids':target['obligation_ids'],'gap_kinds':[g['kind'] for g in target['gaps']]}
            if ledger.budget(state.run_id)['remaining_microusd']<limits['validation_reserve_microusd']+100000:
                journal.append(dict(entry,status='DEFERRED_BUDGET'))
                break
            members=state.scratch['ax_members']
            refs=[members[k] for k in ('definition','concepts','constraints') if k in members]
            ticket=ActionTicket(action_type=target['action'],target_version_ids=refs,
                parameters={'attempt':attempt+1,'depth':1,'candidate_id':target['candidate_id'],
                    'obligation_ids':target['obligation_ids'],'gap_kinds':entry['gap_kinds'],
                    'ancestor_regression_checks':['original_improvement','original_protected_side','hard_constraints']},
                expected_outputs=['CandidateVersion','CoherenceReview'],allowed_tools=['candidate_repair'],
                reserved_microusd=100000,model_role='FLASH',reason='원래 문제의 누락된 연결과 보호 조건을 보완한다.')
            chosen,did=coordinator.decide(state,[ticket],0,{target['action']},'coherence:'+blocker)
            from .. import agent
            raw=agent.run_agent(ctx,node='ax_repair_'+blocker+'_'+str(attempt),label='미해결 부분 보완',
                stage='S6_CONCEPT',agent_id='effects_specialist',prompt_id='P_AX_RECOVERY',tier='T2',
                vars={'action':chosen.action_type,'baseline':target['baseline'].model_dump(mode='json') if target['baseline'] else {},
                      'blockers':target['gaps'],'requirements':state.constraints.model_dump(mode='json'),
                      'analysis':{'obligations':coherence.obligations(state),
                          'resources':[r.model_dump(mode='json') for r in state.analysis.resources],
                          'existing_mechanisms':[c.working_principle for c in state.concepts],
                          'contract':coherence.contract_instruction(state)},
                      'schema':RepairProposal.model_json_schema()},default={}) or {}
            entry.update(decision_id=did,action=target['action'],attempt=attempt+1,status='INVALID_PROPOSAL')
            try:
                proposal=RepairProposal.model_validate(raw)
            except ValueError:
                journal.append(entry)
                continue
            valid={cid for o in coherence.obligations(state) for cid in o['contradiction_ids']}
            required={cid for o in coherence.obligations(state) if o['id'] in target['obligation_ids'] for cid in o['contradiction_ids']}
            if not set(proposal.addresses_contradictions)<=valid or not set(proposal.addresses_contradictions)&required:
                journal.append(dict(entry,status='OBLIGATION_MISMATCH'))
                continue
            if any(' '.join(c.working_principle.split()).casefold()==' '.join(proposal.working_principle.split()).casefold()
                   for c in state.concepts):
                journal.append(dict(entry,status='DUPLICATE_MECHANISM'))
                continue
            data={k:v for k,v in proposal.model_dump(mode='json').items() if k in ConceptSpec.model_fields}
            data.update(id='CPT-AX-'+digest([did,raw])[:12],quality_status='UNVERIFIED',
                one_liner=proposal.title,description=proposal.working_principle,
                expected_effect='제안한 효과는 미검증이며 원래 모순 양측의 시험이 필요하다.',
                source_idea_ids=list(target['baseline'].source_idea_ids) if target['baseline'] else [],
                mechanism_key=digest([proposal.coherence.intervention,proposal.coherence.target,proposal.coherence.changed_variable]))
            repaired=ConceptSpec.model_validate(data)
            branch=state.model_copy(deep=True)
            branch.concepts=[repaired]
            branch.scratch.setdefault('ax_mechanisms',{})[repaired.id]=proposal.coherence.model_dump(mode='json')
            branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
            child=RunContext(branch)
            child.lock,child.budget,child.call_slots=ctx.lock,ctx.budget,ctx.call_slots
            from ..quality import audit_concepts
            audit_concepts(child)
            checked=coherence.candidate_check(branch,repaired)
            # Code obligations remain authoritative even if an independent model misses one.
            accepted=bool(branch.concepts) and repaired.quality_status=='PASS' and not checked['gaps']
            if digest(state.constraints.model_dump(mode='json'))!=protected:
                raise ValueError('Recovery changed protected requirements')
            entry.update(status='PROPOSED_REQUIRES_GATE' if accepted else 'UNRESOLVED',
                proposal=proposal.model_dump(mode='json'),derived_candidate_id=repaired.id,
                ancestor_regression=checked['gaps'],preserved_baseline_id=target['candidate_id'])
            journal.append(entry)
            if accepted:
                state.concepts.append(repaired)
                state.scratch.setdefault('ax_mechanisms',{})[repaired.id]=proposal.coherence.model_dump(mode='json')
                added.append(repaired.id)
                break
    complete.append(phase)
    from .runtime import DEPENDENCIES, section
    ledger.capture(state,{'concepts':section(state,'concepts'),'coherence':coherence.assess(state)},
                   DEPENDENCIES,'coherence_recovery:'+phase)
    return added
