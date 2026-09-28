"""Production paths with an isolated ledger and only the provider boundary faked."""
import copy
import json
import pytest
from test_unified_feedback_learning import isolated_learning_database
from test_unified_feedback_adaptive import adaptive_run, newrun, candidate
from triz import llm, quality, nodes
from triz.context import RunContext
from triz.schema import Constraint
from triz.ax import adaptive_tracks, routing_q, effect_ranker


def review_provider(monkeypatch, state, verdict='REVISE', gate='FAIL'):
    calls = []
    def provider(**kw):
        step = next((s for s in reversed(state.steps) if s.input_slice.get('user') == kw['user']), None)
        if step is None and not any(s.node=='s6_quality' and s.status=='RUNNING' for s in state.steps):
            step=next((s for s in reversed(state.steps) if s.status=='RUNNING' and s.node=='s6_concept'),None)
        prompt = step.input_slice.get('prompt_id') if step else 'VERIFIER'
        variables = step.input_slice.get('vars', {}) if step else {}
        calls.append(prompt)
        data = {'verdict': 'PASS', 'score': 1.}
        if prompt=='P_S5_TRACK_H':
            data['applications']=[dict(effect_id='E1',effect_name='First',idea='접촉면 전도 경로',mechanism_key='conduction',
                conditions=[],strongest_objection='열저항 미측정',validation_test='열저항 시험',application='접촉면 변경',principle='전도')]
        if prompt == 'P_S5_MERGE':
            data.update(ideas=[dict(keep_ids=variables['allowed_idea_ids'],title='전도 연결부',idea='접촉면 전도 경로',merge_reason='같은 기구',selection_reason='검증 가능')], deferred=[],need_more=False,gaps=[])
        elif prompt == 'P_S6_CONCEPT':
            data = dict(concepts=[dict(title='전도 연결부',working_principle='접촉면 전도 경로',source_idea_ids=[i['id']],active_effect_ids=['E1'],addresses_contradictions=['TC1'],resolution_argument='두 요구를 시험한다',
                coherence=dict(intervention='접촉면 변경',target='판',changed_variable='열저항',mediating_functions=['열전달'],outcome='냉각',operating_scope='정상 운전',
                    conditions=[dict(source_idea_id=i['id'],condition=c,applicability='열저항 시험으로 성립 조건을 확인한다') for c in i.get('conditions',[])]),
                validation_plan=[dict(experiment='열 저항 측정',metric='온도 및 전력',success_criterion='열 저항 감소와 전력 유지',failure_criterion='열 저항 또는 전력 증가',obligation_refs=[dict(contradiction_id='TC1',side=side) for side in ('IMPROVE','PROTECT')])]) for i in variables['ideas']], excluded=[])
            if verdict=='EMPTY': data={'concepts':[],'excluded':[]}
        elif prompt == 'VERIFIER':
            audit = next((s for s in reversed(state.steps) if s.node == 's6_quality' and s.status == 'RUNNING'),None)
            if audit: data['per_concept'] = [dict(concept_id=c['concept_id'],verdict=verdict,issues=[] if verdict=='PASS' else ['새 검토 지적']) for c in audit.input_slice['concepts']] if verdict!='MISSING' else []
        elif prompt == 'P_S7_GATEKEEPER':
            data = {'results':[dict(concept_id=c['concept_id'],verdict=gate,violated_ids=['limit'] if gate=='FAIL' else [],per_constraint=[dict(constraint_id='limit',verdict=gate,reason='전원 조건 확인 필요')]) for c in variables['concepts_for_gate']]}
        elif prompt=='P_S8_REVIEW':
            ids=variables['review_concept_ids']
            data=dict(scores=[dict(concept_id=cid,dimension=d,score=4.,confidence=.7,rationale='격리 시험용 검토',red_flags=[],improvement_suggestion='실측 필요') for cid in ids for d in variables['dimensions']],concept_comments={cid:'실측 후 적용 가능성을 확인한다.' for cid in ids})
        elif prompt=='P_S8_RANK':
            data={'ranking':[dict(concept_id=c['concept_id'],rank=i+1) for i,c in enumerate(variables['aggregate_table'])]}
        return llm.LLMResult(data=data,text=json.dumps(data,ensure_ascii=False),tokens_in=10,tokens_out=10,cost_usd=.00001,meta={'requests':[{'usage':{'input_tokens':10,'output_tokens':10}}]})
    monkeypatch.setattr(llm,'chat_json',provider)
    return calls


def test_F1_01_latest_same_design_replaces_old_pass(adaptive_run, monkeypatch):
    state=adaptive_run('LITE'); candidate(state)
    calls=review_provider(monkeypatch,state,'PASS')
    ctx=RunContext(state); quality.generate_concepts(ctx)
    cid=state.concepts[0].id
    assert state.concepts[0].quality_status=='PASS'
    state.constraints.items=[Constraint(id='limit',statement='추가 전원 금지')]
    calls=review_provider(monkeypatch,state,'REVISE')
    quality.generate_concepts(ctx)
    assert state.concepts[0].id==cid
    assert state.concepts[0].quality_status=='REVISE'
    assert '새 검토 지적' in state.concepts[0].quality_issues
    from test_unified_feedback_adaptive import events
    from triz.ax.learning_outcomes import outcome
    assert outcome(events(state),state.scratch['ax_bundle']['run_contract']['feedback_settings'])['concept_quality']==0.
    key=state.scratch['review_inputs'][state.concepts[0].source_idea_ids[0]]['input_hash']
    assert state.scratch['adaptive_concept_cache'][key]['concepts'][0]['quality_status']=='REVISE'
    before=len(calls); quality.generate_concepts(ctx)
    assert len(calls)==before  # F1-05 exact-input retry


def test_F2_01_automatic_fail_is_not_user_drop(adaptive_run,monkeypatch):
    state=adaptive_run('LITE'); candidate(state)
    state.constraints.items=[Constraint(id='limit',statement='추가 전원 금지')]
    review_provider(monkeypatch,state)
    nodes.s7_gate(RunContext(state))
    assert not state.concepts
    assert not state.scratch.get('adaptive_dropped_candidates')
    rows=state.scratch['candidate_dispositions']
    assert rows[-1]['reason_kind']=='CONSTRAINT_FAIL'


def test_F3_01_confirmed_context_reaches_phi(adaptive_run):
    state=adaptive_run('LITE')
    ticket={'action_type':'RUN_TRACK','parameters':{'tracks':['H_EFFECTS']}}
    state.constraints.items=[Constraint(id='limit',statement='추가 전원 금지')]
    a=adaptive_tracks.state_features(state,'initial')
    state.constraints.items=[Constraint(id='limit',statement='추가 전원 허용')]
    b=adaptive_tracks.state_features(state,'initial')
    assert routing_q.phi(a,ticket)!=routing_q.phi(b,ticket)


def test_F4_07_prior_is_versioned_and_explicit(adaptive_run):
    state=adaptive_run('LITE')
    row=adaptive_tracks.estimate(state,'A_MATRIX')
    assert row.get('cost_contract')=='track-execution-cost-v2'
    assert row['support']==0 and row['sample_ids']==[]
    assert row['input_size_kind']=='utf8_bytes_proxy'


def utility_model(value=.2):
    context={'domain':'PHYSICAL'}; effect={'id':'E1'}
    x=effect_ranker.features(context,effect)
    weights=[0.]*effect_ranker.DIMENSIONS
    for i,v in x.items(): weights[i]=value*v
    return dict(feature_schema=effect_ranker.UTILITY_SCHEMA,weights=weights,supported_effects=['E1'],supported_contexts=[effect_ranker.compatibility_key(context)],train_weighted_mean=0.), context,effect


def test_F5_01_small_utility_baseline_counterexample():
    model,context,effect=utility_model()
    model.update(evaluation_contract=effect_ranker.EVALUATION_CONTRACT,target_contract='candidate-utility-cost-v2')
    rows=[dict(context=context,application=effect,label=y,sample_weight=1.,group=str(i)) for i,y in enumerate([.03,-.03])]
    result=effect_ranker.evaluate(model,rows)
    assert result['wmse_full_fallback_policy']==pytest.approx(.0409)
    assert result['wmse_full_zero']==pytest.approx(.0009)
    gate=effect_ranker.eligibility(model,result,{'ready':True})
    assert not gate['eligible'] and 'no_supported_baseline_improvement' in gate['reasons']
