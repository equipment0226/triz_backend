"""Repair effects must be explicitly re-adopted from saved candidate sources."""
import copy

import pytest

from test_ax_phase1 import dlc, candidate
from test_ax_coherence_recovery import proposal
from triz import agent, quality
from triz.ax import coherence, coherence_recovery, concept_effects, coordinator, ledger, recovery
from triz.context import RunContext
from triz.schema import RawIdea


def prepare(state, monkeypatch, path, *, new_contract=True, baseline=True):
    candidate(state)
    first=state.concepts[0]
    first.quality_status='REVISE'
    first.quality_issues=['Mechanism repair required']
    first.source_idea_ids=['source-left']
    first.active_effect_ids=['effect-left']
    second=first.model_copy(deep=True,update={'id':'DLC-2','source_idea_ids':['source-right'],
        'active_effect_ids':['effect-right'],'quality_status':'PASS'})
    state.solve.raw_ideas=[RawIdea(id='source-'+side,track='H_EFFECTS',
        detail={'source_effect_id':'effect-'+side,'application_idea':'Recorded '+side+' mechanism'})
        for side in ('left','right','exposed')]
    state.scratch['ax_recovery']=[]
    state.scratch['ax_bundle']['limits']['repairs_per_blocker']=1
    state.scratch['ax_bundle']['limits']['recovery_targets']=1
    if new_contract:
        state.scratch['ax_bundle']['concept_effect_contract']=concept_effects.VERSION
    else:
        state.scratch['ax_bundle'].pop('concept_effect_contract',None)
    raw=proposal(state)
    if path!='coherence':
        raw={key:value for key,value in raw.items() if key in recovery.Proposal.model_fields}
        monkeypatch.setattr(coherence,'enabled',lambda state:False)
    if path=='codesign':
        state.concepts.append(second)
    monkeypatch.setattr(coherence_recovery,'targets',lambda state,phase:[{
        'candidate_id':first.id if baseline else 'scope-TC-DLC',
        'baseline':first if baseline else None,'obligation_ids':['TC-DLC'],
        'gaps':[{'kind':'QUALITY_REVIEW','description':'Mechanism repair'}],
        'action':'REPAIR_CANDIDATE' if baseline else 'SOLVE_SUBPROBLEM'}])
    monkeypatch.setattr(ledger,'budget',lambda _: {'remaining_microusd':10000000})
    monkeypatch.setattr(coordinator,'decide',lambda state,tickets,*args:(tickets[0],'effect-contract-repair'))
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:setattr(ctx.state.concepts[0],'quality_status','PASS'))
    calls=[]
    def provider(*args,**kwargs):
        calls.append(copy.deepcopy(kwargs))
        return copy.deepcopy(raw)
    monkeypatch.setattr(agent,'run_agent',provider)
    def execute():
        if path=='codesign':
            recovery.codesign(RunContext(state),
                {'candidate_id':first.id,'blocker_id':'left','proposal':{}},
                {'candidate_id':second.id,'blocker_id':'right','proposal':{}},
                {first.id:first,second.id:second})
        else:
            recovery.run(RunContext(state))
    return raw,calls,execute


@pytest.mark.parametrize('path',['coherence','legacy','codesign'])
@pytest.mark.parametrize('effects',[[],['effect-left']])
def test_repaired_effects_are_explicit_and_baseline_is_preserved(dlc,monkeypatch,path,effects):
    raw,calls,execute=prepare(dlc,monkeypatch,path)
    raw['active_effect_ids']=effects
    originals=[c.model_dump(mode='json') for c in dlc.concepts]
    execute()
    assert [c.model_dump(mode='json') for c in dlc.concepts[:-1]]==originals
    assert dlc.concepts[-1].active_effect_ids==effects
    assert 'active_effect_ids' in calls[0]['vars']['schema']['required']
    assert {row['source_effect_id'] for row in calls[0]['vars']['analysis']['source_effects']}==(
        {'effect-left','effect-right'} if path=='codesign' else {'effect-left'})
    assert dlc.scratch['ax_recovery'][-1]['status']=='PROPOSED_REQUIRES_GATE'


@pytest.mark.parametrize('path',['coherence','legacy','codesign'])
@pytest.mark.parametrize('value',['missing','effect-left',['effect-left','effect-left'],['invented'],['effect-exposed']])
def test_missing_or_unrelated_effect_claims_do_not_reach_independent_audit(dlc,monkeypatch,path,value):
    raw,calls,execute=prepare(dlc,monkeypatch,path)
    if value!='missing':
        raw['active_effect_ids']=value
    before=[c.model_dump(mode='json') for c in dlc.concepts]
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:pytest.fail('Invalid adoption reached audit'))
    execute()
    assert len(calls)==1
    assert [c.model_dump(mode='json') for c in dlc.concepts]==before
    entry=dlc.scratch['ax_recovery'][-1]
    assert entry['status']=='INVALID_PROPOSAL' and entry['effect_contract_errors']


def test_codesign_retains_both_source_lineages_for_explicit_right_effect(dlc,monkeypatch):
    raw,calls,execute=prepare(dlc,monkeypatch,'codesign')
    raw['active_effect_ids']=['effect-right']
    execute()
    assert dlc.concepts[-1].active_effect_ids==['effect-right']
    assert dlc.concepts[-1].source_idea_ids==['source-left','source-right']


@pytest.mark.parametrize('effects',[[],['effect-left']])
def test_subproblem_without_baseline_cannot_claim_exposed_effects(dlc,monkeypatch,effects):
    raw,calls,execute=prepare(dlc,monkeypatch,'coherence',baseline=False)
    raw['active_effect_ids']=effects
    before=len(dlc.concepts)
    execute()
    assert calls[0]['vars']['analysis']['source_effects']==[]
    if effects:
        assert len(dlc.concepts)==before
        assert dlc.scratch['ax_recovery'][-1]['status']=='INVALID_PROPOSAL'
    else:
        assert len(dlc.concepts)==before+1
        assert dlc.concepts[-1].source_idea_ids==[]
        assert dlc.concepts[-1].active_effect_ids==[]


@pytest.mark.parametrize('path',['coherence','legacy','codesign'])
def test_old_pinned_repair_requests_keep_original_variables_and_schema(dlc,monkeypatch,path):
    raw,calls,execute=prepare(dlc,monkeypatch,path,new_contract=False)
    baseline=[c.model_dump(mode='json') for c in dlc.concepts]
    if path=='coherence':
        schema=coherence_recovery.RepairProposal.model_json_schema()
        analysis={'obligations':coherence.obligations(dlc),
            'resources':[r.model_dump(mode='json') for r in dlc.analysis.resources],
            'existing_mechanisms':[c.working_principle for c in dlc.concepts],
            'contract':coherence.contract_instruction(dlc)}
        expected_baseline=baseline[0]
        blockers=[{'kind':'QUALITY_REVIEW','description':'Mechanism repair'}]
    elif path=='legacy':
        schema=recovery.Proposal.model_json_schema()
        analysis={'contradictions':dlc.definition.model_dump(mode='json'),
            'resources':[r.model_dump(mode='json') for r in dlc.analysis.resources]}
        expected_baseline=baseline[0]
        blockers=['Mechanism repair required']
    else:
        schema=recovery.Proposal.model_json_schema()
        analysis={'external_resources':[r.name for r in dlc.analysis.resources]}
        expected_baseline=baseline
        blockers=[{},{}]
    expected={'action':'CO_DESIGN' if path=='codesign' else 'REPAIR_CANDIDATE',
        'baseline':expected_baseline,'blockers':blockers,
        'requirements':dlc.constraints.model_dump(mode='json'),'analysis':analysis,'schema':schema}
    execute()
    assert calls[0]['vars']==expected
    assert 'active_effect_ids' not in schema['properties']
    assert dlc.concepts[-1].active_effect_ids==([] if path=='coherence' else ['effect-left'])
