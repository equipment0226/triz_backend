"""Repair feedback identifies the actual schema defect and preserves provenance."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from triz import analysis_checks, verify
from triz import agent
from triz.context import RunContext, AbortRun
from triz.schema import Constraint
from triz.analysis_guidance import analysis_guidance


def test_nine_windows_object_insights_report_the_actual_repairable_type_error():
    data={'cells':{f'{level}_{time}':'Known or scoped hypothesis' for level in ('SUB','SYS','SUPER')
                   for time in ('PAST','PRESENT','FUTURE')},
          'insights':[{'insight':'Possibility','evidence':'Reported input','condition_to_check':'Measure'}]}
    before=deepcopy(data)
    issues=analysis_checks.nine_windows(data)
    assert len(issues)==1 and 'insights[0]' in issues[0] and '문자열' in issues[0]
    assert '근거를 보존' in issues[0]
    assert data==before
    data['insights']=['Possibility; evidence: Reported input; condition: Measure']
    assert not analysis_checks.nine_windows(data)


def test_inferred_hard_constraint_is_neither_user_confirmed_nor_silently_relaxed(state):
    inferred=Constraint(statement='Consult in advance',category='USER_STATED',source='INFERRED',hard=True,confidence=.8)
    explicit=Constraint(statement='Salary increase at most ten percent',source='USER',hard=True,confidence=1)
    state.constraints.items=[inferred,explicit]
    before=state.constraints.model_dump()
    block=verify.constraints_block(state)
    assert 'source=INFERRED; confidence=0.8' in block
    assert 'source=USER; confidence=1' in block
    assert '입력 기반 추론/HARD' in block
    assert '기존 HARD는 현재 제약으로 유지' in block
    assert state.constraints.model_dump()==before


def test_corrective_side_effect_is_not_mislabeled_as_the_useful_correction():
    data={'components':[{'name':'interlayer','level':'TARGET','role':'supports'},
                        {'name':'part','level':'PRODUCT','role':'supported'}],
          'function_edges':[{'subject':'interlayer','action':'supports','object':'part',
              'parameter_affected':'position','kind':'USEFUL','rank':'BASIC','level':'NORMAL'},
             {'subject':'interlayer','action':'heats','object':'part','parameter_affected':'temperature',
              'kind':'HARMFUL','rank':'CORRECTIVE','level':'NORMAL'}],'interaction_cells':[]}
    issues=analysis_checks.function_model(data)
    assert any('function_edges[1]' in issue and 'HARMFUL/AUXILIARY' in issue for issue in issues)
    data['function_edges'][1]['rank']='AUXILIARY'
    assert not analysis_checks.function_model(data)


def test_physical_property_example_reaches_pinned_generation_and_review_guidance():
    state={'domain':{'problem_type':'PHYSICAL_TECHNICAL'},'confirm':{'user_confirmed':True,
        'chosen_candidate_id':'selected','candidates':[{'id':'selected','name':'열 전달 계면'}]}}
    guide=analysis_guidance(state,'s3_function_model')
    assert 'FN_PROPERTY_CARRIER' in guide
    assert '열저항·열전도율·압력·응력은 부품이 아니다' in guide
    assert '요구/목표는 실제 수행 결과의 관측이 아니' in guide


def test_unavailable_focused_verifier_preserves_artifact_without_paid_regeneration(state, monkeypatch):
    calls=[]
    def generate(ctx,**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data={'ok':True},meta={},model='test-model',tokens_in=10,tokens_out=20,cost_usd=.001)
    monkeypatch.setattr(agent,'tracked_chat',generate)
    monkeypatch.setattr(agent,'verify_artifact',lambda *a,**kw:{'verdict':'UNVERIFIED','score':0,
        'verification_unavailable':True,'revision_instructions':['Fix the audit response format'],
        '_tokens':(11,22,.002)})
    with pytest.raises(AbortRun,match='독립 의미 검증'):
        agent.run_agent(RunContext(state),node='s3_function_model',label='function',stage='S3_ANALYZE',
            agent_id='test',prompt_id='P_S0_BOOTSTRAP',rubric_id='R3_FUNC',
            checker=lambda value:[],vars={'raw_query':'test'})
    step=state.steps[-1]
    assert len(calls)==1 and step.status=='FAILED' and step.output_json=={'ok':True}
    assert step.cost_usd==pytest.approx(.003)
    assert not state.scratch['agent_cache']
