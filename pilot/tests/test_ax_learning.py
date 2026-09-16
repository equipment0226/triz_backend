"""Synthetic fixtures verify mechanisms only; never evidence of field improvement."""
import copy
import pytest
from sqlalchemy import select,update
from test_ax_phase1 import dlc,candidate,review_body
from triz import store
from triz.ax import learning,registry,ledger,runtime,coordinator,rules,recovery,engineering,worker
from triz.ax.contracts import ACTIONS,ActionTicket,RuleSpec,Conflict,digest
from triz.context import RunContext


def synthetic_samples():
    return [dict(features=[1,0,0,1,0,0,1,.8],action='REPAIR_CANDIDATE' if i%2 else 'DEFER',
        reward=1.0 if i%2 else -1.0,allowed=['REPAIR_CANDIDATE','DEFER'],
        next_features=[0]*8,next_allowed=[],terminal=True,group='synthetic-'+str(i//4),
        split='holdout' if i>=24 else 'train',maturity='TECHNICAL') for i in range(32)]


def test_real_weight_updates_reproducible_and_masked():
    samples=synthetic_samples()
    p=learning.train(samples)
    assert p==learning.train(samples)
    assert p['training']['parameters_changed']
    assert p['training']['loss_last']<p['training']['loss_first']
    actions=['REPAIR_CANDIDATE','DEFER','ASK_HUMAN']
    assert learning.choose(p,samples[0]['features'],actions,[0,1])==0
    assert learning.choose(p,samples[0]['features'],actions,[1])==1
    assert learning.evaluate(p,samples)['field_improvement_established'] is False


def test_readiness_rejects_synthetic_preference_only_and_leakage():
    s=synthetic_samples()
    assert not learning.readiness({'samples':s,'synthetic':True})['ready']
    assert learning.readiness({'samples':s,'synthetic':False})['ready']
    for row in s: row['maturity']='PREFERENCE'
    assert 'insufficient_technical_observations' in learning.readiness({'samples':s})['reasons']
    s[-1]['group']=s[0]['group']
    assert 'split_leakage' in learning.readiness({'samples':s})['reasons']


def reviewed_decision(s,*,consent='PROJECT_ONLY',result='PASS'):
    coordinator.route(RunContext(s))
    did=s.scratch['ax_last_decision']
    runtime.checkpoint(s,'s5_solve')
    candidate(s)
    body=dict(review_body(s),decision_id=did,decision_type='RECORD_TEST_RESULT',candidate_id='DLC-1',
        obligation_id='DLC-1:test:0',conditions='SYNTHETIC test fixture; no physical experiment',
        measurement={'fixture_only':True},evidence_refs=['fixture:temperature'],result=result,consent=consent)
    ledger.submit_review(s.run_id,'local',body)
    s.status='COMPLETED'; store.save_state(s)
    return body


def test_dataset_consent_exact_decision_revision_and_missing_reward(dlc):
    body=reviewed_decision(dlc,consent='NO_TRAINING')
    h=ledger.head(dlc.run_id)
    def samples():
        return [s for s in learning.dataset(h['tenant_id'],h['project_id'],feature_schema=dlc.scratch['ax_bundle']['feature_schema'])['samples'] if s['run_id']==dlc.run_id]
    assert samples()==[]
    revised=dict(body,event_id=body['event_id']+'-consent',supersedes_event_id=body['event_id'],consent='PROJECT_ONLY')
    ledger.submit_review(dlc.run_id,'local',revised)
    assert len(samples())==1 and samples()[0]['reward']==1
    failure=dict(revised,event_id=body['event_id']+'-failure',supersedes_event_id=revised['event_id'],result='FAIL')
    ledger.submit_review(dlc.run_id,'local',failure)
    assert len(samples())==1 and samples()[0]['reward']==-1
    assert samples()[0]['review_ids']==[failure['event_id']]
    assert not registry.train_project(h['tenant_id'],h['project_id']).get('ready',False)


def test_next_run_registry_pin_withdrawal_and_rollback(dlc):
    body=reviewed_decision(dlc)
    h=ledger.head(dlc.run_id); t,p=h['tenant_id'],h['project_id']
    policy=learning.train(synthetic_samples())
    vid=registry.put('policy',t,p,{'model':policy,'review_ids':[body['event_id']],'offline_eligible':True})
    with pytest.raises(Conflict):
        registry.promote_policy(t,p,vid,'test','synthetic fixture')
    # Shadow pointer does not change the already-pinned run.
    with ledger.transaction() as c:
        pointer=registry._pointer(c,t,p)
        c.execute(update(registry.pointers).where(registry.pointers.c.scope==pointer['scope']).values(shadow_policy_id=vid))
    pinned=copy.deepcopy(dlc.scratch['ax_bundle'])
    assert registry.for_run(dlc)['shadow_policy_version']==vid
    assert dlc.scratch['ax_bundle']==pinned
    withdrawal=dict(body,event_id=body['event_id']+'-withdraw',supersedes_event_id=body['event_id'],consent='NO_TRAINING')
    ledger.submit_review(dlc.run_id,'local',withdrawal)
    assert 'shadow_policy' not in registry.for_run(dlc)
    registry.rollback(t,p,'test','fixture cleanup')
    with pytest.raises(ValueError): registry.get(vid,'other',p)


def spec(s):
    return dict(name='열전달 조건 검증',domain='PHYSICAL_TECHNICAL',required_functions=['열 제거'],
        provided_function='열 제거',operation='ADD_VERIFICATION',effect_ids=['1.1'],
        obligation='온도·열부하·열저항을 측정한다',applicability='측정 경계가 일치해야 함',
        source_versions=[s.scratch['ax_members']['definition']])


def test_rule_dsl_additive_scope_and_no_executable_patch(dlc):
    rule=spec(dlc)
    candidate(dlc)
    before=digest(dlc.constraints.model_dump(mode='json'))
    dlc.solve.effect_apps=[{'catalog_function':'열 제거'}]
    dlc.scratch['ax_bundle']['rule_catalog']=[dict(rule,version_id='test-rule')]
    assert rules.apply(dlc)
    assert len(dlc.concepts[0].validation_plan)==2
    assert rules.apply(dlc)==[]
    assert digest(dlc.constraints.model_dump(mode='json'))==before
    assert not rules.patch(rule,'INFORMATION_SOFTWARE',['열 제거'])['matched']
    with pytest.raises(ValueError): RuleSpec.model_validate(dict(rule,python='delete files'))
    with pytest.raises(ValueError): rules.validate(dict(rule,effect_ids=['FAKE']),dlc)


def test_closed_dependency_cycle_is_not_codesign():
    a={'provided_functions':['A'],'required_functions':['B']}
    b={'provided_functions':['B'],'required_functions':['A']}
    assert not recovery.complementary(a,b,[])
    assert recovery.complementary(a,b,['A'])
    assert not recovery.complementary(a,a,['A','B'])


def test_dlc_registered_calculation_and_missing_inputs():
    assert engineering.run('dlc_steady_state_v1',{})['status']=='NOT_RUN'
    data={'inlet_c':40,'heat_w':1000,'total_resistance_k_per_w':.04,'gpu_limit_c':85}
    result=engineering.run('dlc_steady_state_v1',data)
    assert result['estimated_gpu_c']==80 and result['status']=='PASS'
    assert not result['physical_test_performed']
    assert engineering.run('dlc_steady_state_v1',dict(data,inlet_c=50))['status']=='FAIL'
    assert engineering.run('dlc_steady_state_v1',dict(data,heat_w=float('nan')))['status']=='ERROR'
    with pytest.raises(ValueError): engineering.run('execute_python',{})


def test_recovery_preserves_baseline_and_rejects_unknown_patch(dlc,monkeypatch):
    from triz import agent,quality
    candidate(dlc)
    dlc.scratch['ax_bundle'].pop('coherence_contract')  # The pinned legacy repair contract remains supported.
    dlc.concepts[0].quality_status='REVISE'
    dlc.concepts[0].quality_issues=['기구 설명 보완']
    baseline=dlc.concepts[0].model_dump(mode='json')
    proposal=dict(title='복구 가설',working_principle='열저항 감소',resolution_argument='열저항 경로 수정',
        changes_to_system=['표면 변경'],required_resources=[],assumptions=['열부하 미제공'],open_risks=['미시험'],
        validation_plan=[{'test':'동일 부하 시험'}],provided_functions=['열 제거'],required_functions=['유량'])
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:proposal)
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:setattr(ctx.state.concepts[0],'quality_status','PASS'))
    recovery.run(RunContext(dlc))
    assert len(dlc.concepts)==2
    assert dlc.concepts[0].model_dump(mode='json')==baseline
    assert dlc.scratch['ax_recovery'][0]['status']=='PROPOSED_REQUIRES_GATE'
    recovery.run(RunContext(dlc))
    assert len(dlc.concepts)==2
    with pytest.raises(ValueError): recovery.Proposal.model_validate(dict(proposal,requirements={'gpu_limit':999}))


def test_worker_requires_no_provider_and_repeated_delivery_safe(dlc):
    reviewed_decision(dlc)
    result=worker.tick(max_events=1000,max_projects=20)
    assert result['external_llm_calls']==0
    result2=worker.tick(max_events=1000,max_projects=20)
    assert result2['external_llm_calls']==0
