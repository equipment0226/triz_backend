"""Actual governor/reducer, fake provider only; repairs cannot erase obligations."""
import copy
import pytest
from test_ax_phase1 import dlc, candidate
from triz.ax import coherence_recovery as repair, coherence, recovery, runtime, ledger, learning, coordinator
from triz.context import RunContext
from triz.schema import TechnicalContradiction, ConstraintCheckResult


def proposal(s,side='PROTECT'):
    base=s.concepts[0]
    plan=copy.deepcopy(base.validation_plan)
    plan[0]['obligation_refs']=[{'contradiction_id':'TC-DLC','side':'IMPROVE'},{'contradiction_id':'TC-DLC','side':side}]
    return dict(title='별도 경로 복구',working_principle='추가 열교환 경로로 열저항 감소',resolution_argument='온수 운전과 GPU 온도 한계 동시 보존',
        changes_to_system=['유로 분리'],required_resources=[],assumptions=['유량 확인'],open_risks=['압력 강하'],
        validation_plan=plan,provided_functions=['열 제거'],required_functions=['유량'],addresses_contradictions=['TC-DLC'],
        coherence=copy.deepcopy(s.scratch['ax_mechanisms']['DLC-1']))


@pytest.mark.parametrize('side,count,status',[('PROTECT',2,'PROPOSED_REQUIRES_GATE'),('IMPROVE',1,'UNRESOLVED')])
def test_repair_rechecks_original_protected_side_even_if_auditor_misses_it(dlc,monkeypatch,side,count,status):
    from triz import agent,quality
    candidate(dlc)
    dlc.concepts[0].quality_status='REVISE'
    # This fixture exercises the previously pinned repair-only contract.
    dlc.scratch['ax_bundle']['limits'].pop('portfolio_completion_v1',None)
    dlc.concepts[0].quality_issues=['기구 보완']
    baseline=dlc.concepts[0].model_dump(mode='json')
    raw=proposal(dlc,side)
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:raw)
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:setattr(ctx.state.concepts[0],'quality_status','PASS'))
    added=recovery.run(RunContext(dlc))
    assert len(dlc.concepts)==count
    assert dlc.concepts[0].model_dump(mode='json')==baseline
    assert dlc.scratch['ax_recovery'][-1]['status']==status
    assert len(dlc.scratch['ax_recovery'])<=2
    assert recovery.run(RunContext(dlc))==[]


def test_missing_problem_and_post_constraint_failure_create_distinct_work(dlc):
    candidate(dlc)
    dlc.definition.technical_contradictions.append(TechnicalContradiction(id='TC-MISSING',label='유량·전력'))
    first=repair.targets(dlc,'before_constraints')[0]
    assert first['action']=='SOLVE_SUBPROBLEM' and first['obligation_ids']==['TC-MISSING']
    removed=dlc.concepts.pop()
    dlc.scratch['ax_excluded']=[removed.model_dump(mode='json')]
    dlc.scratch['ax_constraint_failures']={removed.id:{'verdict':'FAIL','violated_ids':['CON-1']}}
    assert any(t['gaps'][0]['kind']=='CONSTRAINT_FAILURE' for t in repair.targets(dlc,'after_constraints'))


def test_repair_budget_defer_never_dispatches(dlc,monkeypatch):
    from triz import agent
    candidate(dlc)
    dlc.concepts[0].quality_status='REVISE'
    monkeypatch.setattr(ledger,'budget',lambda _: {'remaining_microusd':50000})
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:pytest.fail('Budget-deferred repair dispatched'))
    assert recovery.run(RunContext(dlc))==[]
    assert dlc.scratch['ax_recovery'][0]['status']=='DEFERRED_BUDGET'


def test_new_feature_schema_trains_real_weights_without_changing_legacy_contract(dlc):
    from test_ax_learning import synthetic_samples
    candidate(dlc)
    features=coordinator.features(dlc)
    assert len(features)==12
    old=learning.train(synthetic_samples(),epochs=4)
    assert len(old['weights'][0])==8
    samples=synthetic_samples()
    for sample in samples:
        sample['features']+=features[-4:]
        sample['next_features'] += [0]*4
        sample['feature_schema']='ax-features-v2'
    policy=learning.train(samples,epochs=8)
    assert len(policy['weights'][0])==12 and policy['training']['parameters_changed']
    assert learning.evaluate(policy,samples)['field_improvement_established'] is False
    with pytest.raises(ValueError):
        learning.q_values(old,features)
    with pytest.raises(ValueError):
        learning.train(samples+synthetic_samples())


def test_incomplete_positive_observation_not_used_as_rl_success(dlc):
    from test_ax_learning import reviewed_decision
    from triz import store
    reviewed_decision(dlc)
    dlc.concepts[0].validation_plan[0]['obligation_refs']=[{'contradiction_id':'TC-DLC','side':'IMPROVE'}]
    store.save_state(dlc)
    h=ledger.head(dlc.run_id)
    data=learning.dataset(h['tenant_id'],h['project_id'],feature_schema='ax-features-v2')
    assert not [s for s in data['samples'] if s['run_id']==dlc.run_id]
    assert data['excluded']['incomplete_or_stale_positive_technical_label']>=1
