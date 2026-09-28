import copy
from test_targeted_f1_f5 import isolated_learning_database,adaptive_run,newrun,review_provider
from triz import nodes,quality
from triz.context import RunContext,HumanInterrupt
from triz.schema import Constraint
from triz.ax import coordinator,adaptive_tracks,runtime,learning_outcomes,worker,registry,ledger,report
from triz.ax.action_runtime import executing
from triz.ax.contracts import ActionTicket


def test_R05_R06_F3_06_08_real_pipeline_to_worker_and_next_run(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');ctx=RunContext(state)
    state.constraints.items=[Constraint(id='limit',statement='전력 증가 제한')]
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    calls=review_provider(monkeypatch,state,'PASS',gate='CONDITIONAL')
    coordinator.route(ctx)
    tickets=adaptive_tracks.proposals(state)
    i=next(i for i,t in enumerate(tickets) if t.parameters.get('tracks')==['H_EFFECTS'])
    chosen,did=coordinator.decide(state,tickets,i,{'RUN_TRACK'},'adaptive:initial')
    saved=copy.deepcopy(ledger.decision_history(state.run_id,state.user_id)[-1]['payload']['features'])
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False): nodes._run_tracks(ctx,['H_EFFECTS'])
    nodes._merge(ctx);runtime.checkpoint(state,'s5_solve')
    stop=ActionTicket(action_type='STOP_EXPLORATION',expected_outputs=['SearchPhaseResult'],allowed_tools=[],reason='end exploration')
    chosen,did=coordinator.decide(state,[stop],0,{'STOP_EXPLORATION'},'adaptive:initial')
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False): pass
    quality.generate_concepts(ctx);runtime.checkpoint(state,'s6_concept')
    try: nodes.s7_gate(ctx)
    except HumanInterrupt:
        state.scratch['resume_payload']={'decisions':{c.id:'accept' for c in state.concepts}}
        nodes.s7_gate(ctx)
    assert state.concepts and all(r.verdict=='CONDITIONAL' for r in state.constraint_checks)
    runtime.checkpoint(state,'s7_gate');nodes.s8_evaluate(ctx);runtime.checkpoint(state,'s8_evaluate')
    runtime.before_stage(ctx,'s9_report');nodes.s9_report(ctx);runtime.checkpoint(state,'s9_report')
    nodes.record_feedback(state,{'solution_feedback':[dict(concept_id=c.id,rating=4) for c in state.concepts]})
    assert ledger.decision_history(state.run_id,state.user_id)[0]['payload']['features']==saved
    assert saved['schema']=='ax-state-action-v5' and 'confirmed_context' in saved
    assert 'P_S8_REVIEW' in calls and state.evaluation.meeting.status=='COMPLETED'
    assert state.report and report.project(state).concepts
    q=learning_outcomes.q_dataset('local','local',include_synthetic=True)
    e=learning_outcomes.effect_dataset('local','local',include_synthetic=True)
    assert q['samples'] and e['samples']
    assert all(r['synthetic'] for r in q['samples']+e['samples'])
    assert not learning_outcomes.q_dataset('local','local')['samples']
    assert not learning_outcomes.effect_dataset('local','local')['samples']
    result=worker.tick(max_events=1000,max_projects=2)
    assert result['external_llm_calls']==0
    assert {r['task_kind'] for r in result['projects']}=={'routing_q','effect_ranker'}
    assert all(r['result']['status']=='COLLECTING' for r in result['projects'])
    next_state=adaptive_run('LITE')
    assert next_state.scratch['ax_bundle']['feature_schema']=='ax-state-action-v5'
    assert not next_state.scratch['ax_bundle'].get('policy')
    assert not next_state.scratch['ax_bundle'].get('effect_ranker')
    assert runtime.diagnostics(next_state)


def test_R03_project_default_and_explicit_no_training_remain_distinct(adaptive_run):
    from triz import pipeline
    state=adaptive_run('LITE')
    assert state.scratch['training_consent']=='PROJECT_ONLY'
    assert state.scratch['training_consent_version']=='project-default-v1'
    declined=pipeline.create_run('isolated explicit opt-out',mode='LITE',workflow_version='triz-ax-v3.1',training_consent='NO_TRAINING')
    assert declined.scratch['training_consent']=='NO_TRAINING'
    assert declined.scratch['training_consent_version']=='explicit-project-consent-v1'
