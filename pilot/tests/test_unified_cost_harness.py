"""B0/B1/B2 fake-provider cost accounting; never an operational savings claim."""
import json
import pytest
from sqlalchemy import select
from test_unified_feedback_learning import isolated_learning_database
from test_unified_feedback_adaptive import adaptive_run,newrun
from triz import nodes,llm,quality,render,store
from triz.context import RunContext
from triz.ax import coordinator,runtime,ledger,registry,routing_q as q,adaptive_tracks,effect_ranker,effect_history
from triz.ax import feedback_events,learning_outcomes
from triz.settings import settings
from triz.schema import Constraint,ReviewerScore,Persona
from triz.context import HumanInterrupt


def test_C01_C04_C05_C10_C14_equal_model_price_review_cost_harness(adaptive_run,monkeypatch,tmp_path):
    states=[];calls=[]
    mechanism='전도 경로의 접촉면에 유연한 연결부를 설치하여 같은 열전달 목표와 소비 전력 제한을 유지하며 국소 접촉 저항을 확인한다.'
    def provider(**kw):
        step=next((s for state in states for s in reversed(state.steps) if s.input_slice.get('user')==kw['user']),None)
        prompt=step.input_slice.get('prompt_id') if step else 'VERIFIER'
        variables=step.input_slice.get('vars',{}) if step else {}
        calls.append(prompt)
        app=dict(idea=mechanism,principle_id=1,effect_id='E1',effect_name='First',mechanism_key='contact',
            conditions=['접촉 저항 시험'],strongest_objection='미검증',validation_test='열 저항 시험',application='접촉면 변경',principle='전도')
        data=dict(verdict='PASS',score=1.,applications=[app],principle_ids=[1])
        if prompt=='P_S5_TRACK_B': data['applications']=[dict(app,kind=k,applicable=k=='TIME') for k in ('TIME','SPACE','CONDITION','SYSTEM_LEVEL')]
        if prompt=='P_S5_MERGE':
            ids=variables['allowed_idea_ids']
            data.update(ideas=[dict(keep_ids=ids,title='전도 연결부',idea=mechanism,merge_reason='same fixture mechanism and conditions',selection_reason='testable')],
                deferred=[],need_more=False,gaps=[],coverage_note='fixture')
        if prompt=='P_S6_CONCEPT':
            data=dict(concepts=[dict(title='전도 연결부',working_principle=mechanism,source_idea_ids=[i['id']],
                addresses_contradictions=['TC1'],resolution_argument='원래 두 요구 모두 시험',validation_plan=[{'experiment':'열 저항 측정'}],active_effect_ids=['E1']) for i in variables['ideas']],excluded=[])
        if prompt=='VERIFIER':
            audit=next((s for state in states for s in reversed(state.steps) if s.node=='s6_quality' and s.status=='RUNNING'),None)
            if audit: data['per_concept']=[dict(concept_id=c['concept_id'],verdict='PASS') for c in audit.input_slice['concepts']]
        if prompt=='P_S7_GATEKEEPER':
            data={'results':[dict(concept_id=c['concept_id'],verdict='CONDITIONAL',mitigation='측정 전',requires_user_decision=True,
                per_constraint=[dict(constraint_id='limit',verdict='CONDITIONAL',reason='미측정')]) for c in variables['concepts_for_gate']]}
        if prompt=='P_S8_RANK': data={'ranking':[dict(concept_id=c['concept_id'],rank=i+1) for i,c in enumerate(variables['aggregate_table'])]}
        return llm.LLMResult(data=data,text=json.dumps(data,ensure_ascii=False),tokens_in=10,tokens_out=10,cost_usd=.00001,
            meta={'requests':[{'usage':{'input_tokens':10,'output_tokens':10}}]})
    monkeypatch.setattr(llm,'chat_json',provider)
    monkeypatch.setattr(nodes,'_evidence',lambda ctx:None)  # Identical empty search fixture for all arms.
    from triz import meeting
    def fixture_meeting(ctx):
        from triz.ax.gateway import chat
        chat(ctx,_node='s8_review_fixture',system='same fixture rubric',user='same fixture score',tier='T3')
        step=ctx.start_step(node='s8_review_fixture',label='fixture reviewer',stage='S8_EVALUATE',agent_id='persona::p1',prompt_id='P_S8_REVIEW',tier='T3')
        scores=[ReviewerScore(concept_id=c.id,reviewer_role='시험 검토',dimension='GOAL',score=4,rationale='fixture observed proxy') for c in ctx.state.concepts]
        step.output_json={'scores':[s.model_dump() for s in scores]};ctx.finish_step(step,'OK')
        return scores
    monkeypatch.setattr(meeting,'evaluate',fixture_meeting)
    # Isolated CPU-trained fixture models are explicitly barred from registry approval.
    original_permission=registry.pinned_permissions_current
    monkeypatch.setattr(registry,'pinned_permissions_current',lambda state:True if state.scratch.get('synthetic') else original_permission(state))
    results={}
    for arm,version in [('B0','ax-run-v2'),('B1','ax-run-v3'),('B2','ax-run-v3')]:
        monkeypatch.setitem(settings.triz['ax'],'run_contract_version',version)
        state=adaptive_run('LITE',user=arm);states.append(state)
        state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
        state.scratch['training_consent']='PROJECT_ONLY'
        state.constraints.items=[Constraint(id='limit',statement='원래 전력 한도 유지')]
        state.evaluation.reviewers=[Persona(persona_id='p1',role_name='시험 검토')]
        for stage in ('s2_confirm','s3_analyze','s4_define'): runtime.checkpoint(state,stage)
        ctx=RunContext(state);start=len(calls)
        if arm=='B2':
            fs=adaptive_tracks.state_features(state,'adaptive:initial')
            tickets=[t.model_dump(mode='json') for t in adaptive_tracks.proposals(state)]
            rows=[dict(features=fs,actions=tickets,permitted=list(range(len(tickets))),executed_index=i,
                terminal=True,next_features=fs,next_actions=[],next_permitted=[],reward=.9 if t['parameters']['tracks']==['H_EFFECTS'] else -.9,
                group=f'isolated-family-{g}',split='train',**q.contracts(q.ADAPTIVE_SCHEMA)) for g in range(8) for i,t in enumerate(tickets)]
            from triz.ax.contracts import ActionTicket
            after=dict(fs,tracks=['H_EFFECTS'],search_status='SEARCHING')
            next_tickets=[t for t in tickets if t['parameters']['tracks']!=['H_EFFECTS']]+[
                ActionTicket(action_type='STOP_EXPLORATION',parameters={'plan_class':'PHASE_STOP','phase':'initial'},
                    expected_outputs=['SearchPhaseResult'],allowed_tools=[],reason='fixture phase stop').model_dump(mode='json')]
            rows.extend(dict(features=after,actions=next_tickets,permitted=list(range(len(next_tickets))),executed_index=i,
                terminal=True,next_features=after,next_actions=[],next_permitted=[],reward=.9 if t['action_type']=='STOP_EXPLORATION' else -.9,
                group=f'isolated-family-{g}',split='train',**q.contracts(q.ADAPTIVE_SCHEMA)) for g in range(8) for i,t in enumerate(next_tickets))
            state.scratch['ax_bundle']['policy']=q.train(rows,epochs=100)
            context=effect_history.structured_context(state);effects=state.scratch['ax_bundle']['effects'][0]['effects']
            state.scratch['ax_bundle']['effect_ranker']=effect_ranker.train([dict(feature_schema=effect_ranker.UTILITY_SCHEMA,
                context=context,features=effect_ranker.features(context,e),effect_id=e['id'],label=.5 if e['id']=='E1' else -.5) for e in effects])
        coordinator.route(ctx);nodes.s5_solve(ctx);runtime.checkpoint(state,'s5_solve')
        quality.generate_concepts(ctx);runtime.checkpoint(state,'s6_concept')
        try: nodes.s7_gate(ctx)
        except HumanInterrupt:
            state.scratch['resume_payload']={'decisions':{c.id:'accept' for c in state.concepts},'training_consent':'PROJECT_ONLY'}
            nodes.s7_gate(ctx)
        runtime.checkpoint(state,'s7_gate')
        nodes.s8_evaluate(ctx);runtime.checkpoint(state,'s8_evaluate')
        runtime.before_stage(ctx,'s9_report');nodes.s9_report(ctx);runtime.checkpoint(state,'s9_report')
        nodes.record_feedback(state,{'solution_feedback':[{'concept_id':c.id,'rating':4} for c in state.concepts],'training_consent':'PROJECT_ONLY'})
        budget=ledger.budget(state.run_id)
        with store.engine.connect() as c:
            tasks=list(c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==state.run_id)).mappings())
        assert sum(t['actual'] for t in tasks)==budget['spent_microusd']==(len(calls)-start)*10
        assert len(state.concepts)==1 and state.report
        assert not state.scratch['idea_consolidation']['unaccounted_idea_ids']
        results[arm]=dict(calls=len(calls)-start,actual_microusd=budget['spent_microusd'],reserve=budget['reserved_microusd'],
            tracks=state.solve.tracks_run,reviewed=len(state.concepts),quality=[c.quality_status for c in state.concepts],
            constraint=[r.verdict for r in state.constraint_checks],synthetic=True,live_status='not_evaluated_live')
    assert len(results['B0']['tracks'])==4
    assert len(results['B1']['tracks'])==len(results['B2']['tracks'])==1
    assert results['B1']['calls']<results['B0']['calls']
    assert results['B2']['tracks']==['H_EFFECTS']
    assert results['B0']['constraint']==results['B1']['constraint']==results['B2']['constraint']
    artifact=tmp_path/'cost-comparison.json';artifact.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))
