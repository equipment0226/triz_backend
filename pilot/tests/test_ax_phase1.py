"""DLC engineering contract and failure-injection tests. No physical test is claimed."""
from concurrent.futures import ThreadPoolExecutor
import copy
import time
import pytest
from triz import pipeline,store,llm
from triz.context import RunContext
from triz.schema import TechnicalContradiction,PhysicalContradiction,ConceptSpec,ConstraintCheckResult
from triz.ax import WORKFLOW,ledger,runtime,coordinator,validation,gateway,report
from triz.ax.contracts import ActionTicket,Review,Conflict,AccessDenied


@pytest.fixture
def dlc():
    s=pipeline.create_run('DLC 데이터센터 냉각수 온도와 GPU 온도 상충 해결',workflow_version=WORKFLOW)
    s.domain.problem_type='PHYSICAL_TECHNICAL'
    s.domain.target_system='DLC GPU 냉각수 회로'
    s.confirm.user_confirmed=True
    s.intake.frame.missing_info=['GPU 열부하','냉각수 유량','GPU 온도 한계','입수 온도']
    s.definition.technical_contradictions=[TechnicalContradiction(id='TC-DLC',
        if_action='냉각수 온도를 높인다',then_good='냉동기 에너지 감소 가능',but_bad='GPU 접합 온도 상승',
        coupling_mechanism='GPU와 냉각수 사이 열전달 온도차 감소')]
    s.definition.physical_contradictions=[PhysicalContradiction(id='PC-DLC',element='냉각수',parameter='온도',
        state_a='높아야 함',state_b='낮아야 함',reason_a='냉각 에너지 절감',reason_b='GPU 온도 제한')]
    for stage in ('s2_confirm','s3_analyze','s4_define'):
        runtime.checkpoint(s,stage)
    return s


def candidate(s):
    s.concepts=[ConceptSpec(id='DLC-1',title='국소 열저항 감소와 온수 루프',quality_status='PASS',
        working_principle='콜드플레이트의 국소 열전달을 개선한다',
        addresses_contradictions=['TC-DLC'],resolution_argument='동일 열부하에서 국소 열저항 감소로 보상 가능한지 검증',
        expected_effect='냉각수 온도 상승 시 GPU 온도 제한 충족 여부는 미확인',
        assumptions=['열부하와 유량 미제공'],validation_plan=[{'test':'동일 GPU 열부하에서 온도와 펌프 전력 동시 측정'}])]
    s.constraint_checks=[ConstraintCheckResult(concept_id='DLC-1',verdict='PASS')]
    runtime.checkpoint(s,'s6_concept')
    runtime.checkpoint(s,'s7_gate')


def review_body(s,**overrides):
    return dict(event_id='review-'+s.run_id,expected_epoch=s.scratch['execution_epoch'],
        snapshot_id=s.scratch['ax_snapshot_id'],target_version_id=s.scratch['ax_members'].get('concepts',s.scratch['ax_members']['definition']),
        decision_type='APPROVE_EXPLORATION',reason='기구의 추가 탐색 승인',**overrides)


def test_dlc_phase1_route_lineage_validation_and_report(dlc):
    coordinator.route(RunContext(dlc))
    assert dlc.control.enabled_tracks==['A_MATRIX','B_SEPARATION','H_EFFECTS']
    history=ledger.decision_history(dlc.run_id,'local')
    assert history[0]['payload']['selection_mode']=='RULE_BASED'
    candidate(dlc)
    runtime.checkpoint(dlc,'s8_evaluate')
    assert not dlc.scratch['ax_selection']['recommended']
    assert dlc.scratch['ax_selection']['conditional']==['DLC-1']
    runtime.before_stage(RunContext(dlc),'s9_report')
    rendered=report.markdown(dlc)
    assert '조건부 검토' in rendered and '미실행' in rendered
    old=rendered
    dlc.concepts[0].title='UNCOMMITTED FALSE CLAIM'
    assert report.markdown(dlc)==old
    snap=ledger.snapshot(dlc.run_id,dlc.scratch['ax_snapshot_id'],'local')
    assert snap['artifacts']['selection']['parents']
    assert pipeline.stage_list()[6]['key']=='s5_solve'


@pytest.mark.parametrize('kind',['INFORMATION_SOFTWARE','ORGANIZATIONAL_BUSINESS'])
def test_nonphysical_effect_search_uses_canonical_domain(dlc,kind):
    dlc.domain.problem_type=kind
    results=runtime.effect_candidates(dlc,['정보'],limit=6)
    assert results
    assert {e['domain'] for e in results}=={'INFORMATIONAL'}


def test_new_project_gets_its_own_dollar_despite_old_pinned_context(dlc,monkeypatch):
    from triz.settings import settings
    from triz.execution_config import profile
    monkeypatch.setitem(settings.triz['ax'],'hard_budget_usd',1.0)
    old=copy.deepcopy(dlc.scratch['ax_bundle'])
    old['config']['ax']['hard_budget_usd']=.6
    token=profile.set(old)
    try:
        first=pipeline.create_run('First budget project',workflow_version=WORKFLOW)
        task=ledger.acquire(first.run_id,0,{'probe':'spent'},750000)
        ledger.settle(task,{},750000)
        second=pipeline.create_run('Second independent budget project',workflow_version=WORKFLOW)
    finally:
        profile.reset(token)
    assert first.cost.budget_usd==second.cost.budget_usd==1.0
    assert ledger.budget(first.run_id)['remaining_microusd']==250000
    assert ledger.budget(second.run_id)['remaining_microusd']==1000000
    assert second.cost.total_usd==0
    # Changing future defaults or pressing resume does not grant this run a new dollar.
    first.status='INTERRUPTED'
    first.cost.total_usd=.75
    store.save_state(first)
    monkeypatch.setitem(settings.triz['run'],'budget_usd',10.0)
    monkeypatch.setattr(pipeline,'start',lambda run_id:None)
    assert pipeline.continue_run(first.run_id)
    resumed=store.load_state(first.run_id)
    assert resumed.cost.budget_usd==1.0 and resumed.cost.total_usd==.75
    assert ledger.budget(first.run_id)['remaining_microusd']==250000


def test_reviews_idempotent_stale_epoch_and_owner(dlc):
    body=review_body(dlc)
    assert not ledger.submit_review(dlc.run_id,'local',body)['duplicate']
    assert ledger.submit_review(dlc.run_id,'local',body)['duplicate']
    with pytest.raises(AccessDenied):
        ledger.submit_review(dlc.run_id,'someone-else',body)
    changed=dict(body,reason='changed')
    with pytest.raises(Conflict):
        ledger.submit_review(dlc.run_id,'local',changed)
    dlc.scratch['execution_epoch']+=1
    ledger.advance_epoch(dlc,'test')
    with pytest.raises(Conflict):
        ledger.submit_review(dlc.run_id,'local',dict(body,event_id='new'))


def test_missing_or_failed_test_never_becomes_success(dlc):
    candidate(dlc)
    with pytest.raises(ValueError):
        Review.model_validate(dict(review_body(dlc),result='PASS'))
    body=dict(review_body(dlc),decision_type='RECORD_TEST_RESULT',candidate_id='DLC-1',obligation_id='DLC-1:test:0',
        result='PASS',conditions='SYNTHETIC fixture conditions',measurement={'fixture_only':True},evidence_refs=['fixture:measurement'])
    ledger.submit_review(dlc.run_id,'local',body)
    assert validation.selection(dlc)['recommended']==['DLC-1']
    ledger.submit_review(dlc.run_id,'local',dict(body,event_id=body['event_id']+'-fail',result='FAIL',supersedes_event_id=body['event_id']))
    assert validation.selection(dlc)['candidates'][0]['status']=='REJECTED'


def test_budget_reservation_is_atomic_under_parallel_calls(dlc):
    amount=ledger.budget(dlc.run_id)['limit_microusd']*3//4
    def reserve(i):
        try:
            return ledger.acquire(dlc.run_id,0,{'branch':i},amount)
        except Conflict:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(reserve,range(2)))
    assert sum(r is not None for r in results)==1
    assert ledger.budget(dlc.run_id)['reserved_microusd']==amount


def test_crash_reservation_reconcile_fences_old_result(dlc):
    t=ledger.acquire(dlc.run_id,0,{'request':'lost'},100,lease_seconds=-1)
    assert ledger.acquire(dlc.run_id,0,{'request':'lost'},100)['blocked']=='UNKNOWN'
    assert ledger.budget(dlc.run_id)['unknown_attempts']==1
    ledger.reconcile(t['task_id'],50,'provider usage export','test-operator')
    with pytest.raises(Conflict):
        ledger.settle(t,{'late':True},50)
    assert ledger.budget(dlc.run_id)['spent_microusd']==50


def test_stale_response_keeps_cost_but_cannot_commit(dlc):
    t=ledger.acquire(dlc.run_id,0,{'request':'old'},100)
    runtime.checkpoint(dlc,'s5_solve')
    with pytest.raises(Conflict):
        ledger.settle(t,{'old':True},60)
    assert ledger.budget(dlc.run_id)['spent_microusd']==60
    assert ledger.budget(dlc.run_id)['reserved_microusd']==0


def test_gateway_durable_replay_and_timeout(dlc,monkeypatch):
    calls=[]
    def chat(**kw):
        calls.append(kw)
        return llm.LLMResult(data={'ok':True},cost_usd=.00001)
    monkeypatch.setattr(llm,'chat_json',chat)
    first=gateway.chat(RunContext(dlc),system='system',user='user',tier='T1')
    second=gateway.chat(RunContext(dlc),system='system',user='user',tier='T1')
    assert len(calls)==1 and second.meta['durable_replay']
    assert ledger.budget(dlc.run_id)['spent_microusd']==10
    assert calls[0]['model_config']['model']==dlc.scratch['ax_bundle']['models']['T1']['model']


def test_unknown_usage_keeps_reserved_even_with_previous_success(dlc,monkeypatch):
    def broken(**kw):
        e=llm.LLMError('response lost')
        e.usage=llm.LLMResult(data=None,cost_usd=.01,meta={'requests':[{'usage':{'tokens':1}}, {'usage':{},'status_code':None}]})
        raise e
    monkeypatch.setattr(llm,'chat_json',broken)
    with pytest.raises(llm.LLMError):
        gateway.chat(RunContext(dlc),system='s',user='u')
    assert ledger.budget(dlc.run_id)['unknown_attempts']==1


@pytest.mark.parametrize('params,reason', [({'tracks':['A_MATRIX']*4},'branch_limit'),
    ({'change_requirements':True},'protected_requirements'),({'depth':3},'depth_limit'),({'attempt':3},'repair_limit')])
def test_governor_rejects_illegal_action(dlc,params,reason):
    action=ActionTicket(action_type='GENERATE_BASELINE',parameters=params,expected_outputs=[],allowed_tools=[],reason='test')
    assert coordinator.feasible(dlc,action,handlers={'GENERATE_BASELINE'})==reason


def test_snapshot_invalidation_and_bundle_isolation(dlc):
    candidate(dlc)
    old=dlc.scratch['ax_snapshot_id']
    dlc.definition.technical_contradictions[0].rationale='new rationale'
    runtime.checkpoint(dlc,'s4_define')
    assert 'concepts' not in dlc.scratch['ax_members']
    assert 'concepts' in ledger.snapshot(dlc.run_id,old,'local')['members']
    with pytest.raises(AccessDenied):
        ledger.snapshot(dlc.run_id,old,'other')


def test_legacy_run_keeps_existing_workflow(state):
    assert 'workflow_version' not in state.scratch


def test_coordinator_never_dispatches_hitl(dlc):
    ticket=ActionTicket(action_type='ASK_HUMAN',expected_outputs=[],allowed_tools=['human_review'],reason='missing information')
    assert coordinator.feasible(dlc,ticket,handlers={'ASK_HUMAN'})=='coordinator_is_autonomous'


def test_outbox_duplicate_and_expired_delivery(dlc):
    from triz.ax import outbox
    ledger.init()
    event=outbox.claim(lease_seconds=-1)
    with pytest.raises(Conflict):
        outbox.deliver(event,'test',lambda c,e:None)
    replacement=outbox.claim()
    calls=[]
    assert outbox.deliver(replacement,'test',lambda c,e:calls.append(e['event_id']))
    assert not outbox.deliver(replacement,'test',lambda c,e:calls.append(e['event_id']))
    assert len(calls)==1


def test_api_stale_review_returns_version_diff(dlc):
    from fastapi.testclient import TestClient
    from api.main import app
    body=review_body(dlc)
    candidate(dlc)
    client=TestClient(app)
    response=client.post('/api/runs/'+dlc.run_id+'/ax/reviews',json=body)
    assert response.status_code==409
    assert response.json()['detail']['changed']


def test_gateway_waits_for_temporary_reservations_instead_of_aborting(dlc,monkeypatch):
    from triz.ax.contracts import BudgetBusy
    acquire=ledger.acquire; attempts=[]
    def first_busy(*args,**kw):
        attempts.append(1)
        if len(attempts)==1: raise BudgetBusy('in flight')
        return acquire(*args,**kw)
    monkeypatch.setattr(ledger,'acquire',first_busy)
    monkeypatch.setattr(llm,'chat_json',lambda **kw:llm.LLMResult(data={'ok':True},cost_usd=.000001))
    assert gateway.chat(RunContext(dlc),system='s',user='u').data['ok']
    assert len(attempts)==2
