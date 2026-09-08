import pytest
from triz import agent, nodes, pipeline, store
from triz.context import RunContext
from triz.schema import ConceptSpec, Constraint, ConstraintCheckResult, HumanRequest, StepRecord


def prepare(state):
    state.control.stage_index = 8
    state.status = 'RUNNING'
    state.concepts = [ConceptSpec(title='유지 후보'), ConceptSpec(title='제외 후보')]
    state.constraints.items = [Constraint(statement='센서 추가 금지')]
    store.save_state(state)


def test_failed_gate_manual_decisions_resume_next_stage_and_remain_durable(state, monkeypatch):
    prepare(state)
    def failed(ctx, **kwargs):
        step = ctx.start_step(node=kwargs['node'], label='제약 검토',stage='S7',agent_id='gatekeeper',prompt_id='P_S7_GATEKEEPER',tier='T2')
        ctx.finish_step(step, 'FAILED')
        return {}
    monkeypatch.setattr(agent, 'run_agent', failed)
    monkeypatch.setattr(pipeline, 'start', lambda rid: None)
    result = pipeline.execute_stage(state.run_id, 8)
    assert result['status'] == 'WAITING_HUMAN'
    waiting = store.load_state(state.run_id)
    keep, drop = [c.id for c in state.concepts]
    assert pipeline.resume(state.run_id, {'interrupt_id':waiting.pending.interrupt_id, 'decisions':{keep:'accept',drop:'drop'}})
    result = pipeline.execute_stage(state.run_id, 8, 1)
    assert result['stage_index'] == 9 and result['continue_execution']
    saved = store.load_state(state.run_id)
    assert [c.id for c in saved.concepts] == [keep]
    assert saved.check_for(keep).verdict == 'CONDITIONAL'
    assert not saved.check_for(keep).requires_user_decision
    assert saved.steps[-1].status == 'FAILED'  # Original failure is not falsified.
    assert saved.steps[-1].step_id in saved.scratch['resolved_step_failures']
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw: pytest.fail('Manual gate decision must not call the model again'))
    nodes.s7_gate(RunContext(saved))
    calls=[]
    stages=list(pipeline.PIPELINE)
    stages[9]=('s8_evaluate','다직군 평가',lambda ctx: calls.append('evaluation'))
    monkeypatch.setattr(pipeline,'PIPELINE',stages)
    assert pipeline.execute_stage(state.run_id,9,1)['stage_index'] == 10
    assert calls == ['evaluation']


@pytest.mark.parametrize('decisions', [{}, {'unknown':'accept'}, {'a':'invalid'}, []])
def test_incomplete_decisions_preserve_pending_question(state,monkeypatch,decisions):
    prepare(state)
    state.pending=HumanRequest(kind='DECIDE',title='확인',payload={'conditional':[{'concept_id':'a'}]})
    state.status='WAITING_HUMAN'
    store.save_state(state)
    monkeypatch.setattr(pipeline,'start',lambda rid:pytest.fail('Invalid answer must not dispatch'))
    with pytest.raises(ValueError): pipeline.resume(state.run_id,{'decisions':decisions})
    saved=store.load_state(state.run_id)
    assert saved.pending.interrupt_id == state.pending.interrupt_id
    assert saved.status == 'WAITING_HUMAN'


def test_gate_batches_preserve_all_concepts_and_constraints(state,monkeypatch):
    prepare(state)
    state.concepts=[ConceptSpec(title=str(i)) for i in range(12)]
    state.constraints.items=[Constraint(statement=f'제약 {i}') for i in range(20)]
    seen=[]
    def passed(ctx,**kwargs):
        batch=kwargs['vars']['concepts_for_gate']
        assert len(batch)*len(state.constraints.items) <= 24
        assert kwargs['vars']['constraints_full']
        seen.extend(c['concept_id'] for c in batch)
        return {'results':[{'concept_id':c['concept_id'],'verdict':'PASS'} for c in batch]}
    monkeypatch.setattr(agent,'run_agent',passed)
    nodes.s7_gate(RunContext(state))
    assert seen == [c.id for c in state.concepts]
    assert len(state.constraint_checks) == 12


def test_new_failures_after_manual_resolution_still_stop_execution(state,monkeypatch):
    prepare(state)
    old=StepRecord(seq=1,node='s7_gate',status='FAILED')
    state.steps=[old]
    state.scratch['resolved_step_failures']={old.step_id:'manual decision'}
    store.save_state(state)
    def fail(ctx): ctx.state.steps.append(StepRecord(seq=2,node='s8_review',status='FAILED'))
    stages=list(pipeline.PIPELINE);stages[8]=('test','test',fail)
    monkeypatch.setattr(pipeline,'PIPELINE',stages)
    assert pipeline.execute_stage(state.run_id,8)['status'] == 'FAILED'
