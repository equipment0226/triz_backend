"""Deterministic acceptance fixtures; no live learning/performance evidence."""
import copy
import json
import pytest
from sqlalchemy import select
from test_unified_feedback_adaptive import adaptive_run, newrun, candidate, events
from triz import nodes, store, llm
from triz.context import RunContext
from triz.ax import adaptive_tracks, coordinator, feedback_events as feedback, learning_outcomes as outcomes
from triz.ax import routing_q as q, ledger, runtime, effect_history, effect_ranker, worker, registry
from triz.ax.action_runtime import executing, emit, episode
from triz.ax.contracts import ActionTicket, Conflict, AccessDenied


@pytest.fixture(autouse=True)
def isolated_learning_database(tmp_path,monkeypatch):
    from sqlalchemy import create_engine
    from triz.settings import settings
    engine=create_engine('sqlite:///'+(tmp_path/'learning.db').as_posix())
    monkeypatch.setattr(store,'engine',engine)
    monkeypatch.setattr(store,'_initialized',False)
    monkeypatch.setattr(settings,'storage_dir',tmp_path/'storage')
    store.init();ledger.init()
    yield
    engine.dispose()


def observed_episode(state,monkeypatch):
    """Real H producer, gateway journal and selection; fixture candidate for review."""
    from test_ax_targeted_expansion import fake_provider
    state.scratch['training_consent']='PROJECT_ONLY'
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    calls=fake_provider(monkeypatch,[state],application=True)
    ctx=RunContext(state);coordinator.route(ctx)
    tickets=adaptive_tracks.proposals(state)
    index=next(i for i,t in enumerate(tickets) if t.parameters.get('tracks')==['H_EFFECTS'])
    chosen,did=coordinator.decide(state,tickets,index,{'RUN_TRACK','STOP_EXPLORATION'},'adaptive:initial')
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False):
        nodes._run_tracks(ctx,['H_EFFECTS'])
    from triz.schema import ConceptSpec,ConstraintCheckResult
    raw=state.solve.raw_ideas[0]
    value=ConceptSpec(id='candidate-h',title='전도 연결부',working_principle=raw.idea,
        mechanism_key='retained-conduction',source_idea_ids=[raw.id],active_effect_ids=['E1'])
    state.concepts=[value]
    state.constraint_checks=[ConstraintCheckResult(concept_id=value.id,verdict='CONDITIONAL')]
    stop=ActionTicket(action_type='STOP_EXPLORATION',parameters={'phase':'initial'},reason='fixture stop',expected_outputs=['SearchPhaseResult'],allowed_tools=[])
    chosen,did=coordinator.decide(state,[stop],0,{'STOP_EXPLORATION'},'adaptive:initial')
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False): pass
    feedback.user_decisions(state,{value.id:'accept'},{'training_consent':'PROJECT_ONLY'},'keep-1')
    emit(state,'ADAPTIVE_EPISODE_CLOSED',dict(semantic_episode_id=episode(state),candidate_ids=[value.id],
         terminal_decision_id=did,report_snapshot_id=state.scratch['ax_snapshot_id']))
    return value,calls


def test_D01_D07_Q02_C01_C02_C03_common_events_project_to_both_tasks(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,calls=observed_episode(state,monkeypatch)
    qm=outcomes.q_dataset('local','local',include_synthetic=True)
    em=outcomes.effect_dataset('local','local',include_synthetic=True)
    assert len(qm['samples'])==2, qm
    assert len(em['samples'])==1, em
    assert em['samples'][0]['effect_id']=='E1'
    assert em['samples'][0]['label']==pytest.approx(.03)
    assert em['samples'][0]['sample_weight']==1
    assert em['samples'][0]['review_ids']==[events(state)[0]['event_id']]
    costs=[i for s in qm['samples'] for i in s['dimensions']['task_ids']]
    assert len(costs)==len(set(costs))==len(calls)
    assert sum(s['dimensions']['actual_microusd'] for s in qm['samples'])==ledger.budget(state.run_id)['spent_microusd']
    assert not outcomes.q_dataset('local','local')['samples']
    assert not outcomes.effect_dataset('local','local')['samples']
    assert qm['synthetic'] and em['synthetic']
    with pytest.raises(ValueError): q.support_model(qm['samples'])
    with pytest.raises(ValueError): effect_ranker.train(em['samples'])
    assert all(r['attribution']=='OBSERVED_JOINT_LINEAGE' for r in events(state))


@pytest.mark.parametrize('rating,expected',[(1,-1.),(5,1.)])
def test_U07_U08_U09_D12_Q05_Q06_late_feedback_revises_only_terminal(adaptive_run,monkeypatch,rating,expected):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    cutoff=events(state)[0]['label_available_at']
    initial=outcomes.q_dataset('local','local',include_synthetic=True)
    body={'submission_id':'final','solution_feedback':[{'concept_id':value.id,'rating':rating}], 'training_consent':'PROJECT_ONLY'}
    assert feedback.final_feedback(state,body)
    assert feedback.final_feedback(state,body) is False
    later=outcomes.q_dataset('local','local',include_synthetic=True)
    assert len(later['samples'])==len(initial['samples'])==2
    terminal=next(s for s in later['samples'] if s['terminal'])
    assert terminal['dimensions']['terminal_outcome']['user_utility']==expected
    assert sum(s['terminal'] for s in later['samples'])==1
    assert outcomes.outcome(events(state),state.scratch['ax_bundle']['run_contract']['feedback_settings'])==outcomes.outcome(list(reversed(events(state))),state.scratch['ax_bundle']['run_contract']['feedback_settings'])
    assert len(feedback.current('local','local',cutoff,include_synthetic=True))==1
    assert len(ledger.decision_history(state.run_id,state.user_id))==2


@pytest.mark.parametrize('row',[{}, {'rating':0}, {'adopted':False}, {'rating':False}])
def test_U05_U10_missing_defaults_are_unobserved(adaptive_run,row):
    state=adaptive_run();value=candidate(state)
    feedback.user_decisions(state,{}, {},'empty')
    assert not events(state)
    feedback.final_feedback(state,{'solution_feedback':[dict(row,concept_id=value.id)]})
    assert events(state)[0]['observed_mask'] is False
    assert events(state)[0]['observed_value'] is None


def test_U06_U11_D10_drop_retains_lineage_and_no_consent_is_excluded(adaptive_run):
    state=adaptive_run();value=candidate(state)
    state.scratch['resume_payload']={'decisions':{value.id:'drop'}}
    nodes.s7_gate(RunContext(state))
    assert not state.concepts
    event=events(state)[0]
    assert event['observed_value']==-.1 and event['dimension']=='user_utility'
    assert event['candidate_snapshot']['id']==value.id
    assert event['source_raw_idea_ids']==['raw-C1'] and event['attribution']=='UNKNOWN_ATTRIBUTION'
    assert feedback.current('local','local',include_synthetic=True)==[]


def test_D03_D04_D09_exposure_and_removed_effect_do_not_label_catalog(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    value.active_effect_ids=['OUTSIDE_CATALOG']
    feedback.final_feedback(state,{'solution_feedback':[{'concept_id':value.id,'rating':5}], 'training_consent':'PROJECT_ONLY'})
    assert outcomes.effect_dataset('local','local',include_synthetic=True)['samples']==[]
    state2=adaptive_run();candidate(state2)
    state2.constraints.items=[]
    nodes.s7_gate(RunContext(state2))
    assert not events(state2)


def test_Q16_revision_owner_scope_and_frozen_report(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    old=events(state)[0];snapshot=copy.deepcopy(state.report)
    with pytest.raises(AccessDenied):
        feedback.revise(state.run_id,'someone-else',old['event_id'],consent_scope='NO_TRAINING',reason='withdraw')
    eid=feedback.revise(state.run_id,state.user_id,old['event_id'],consent_scope='NO_TRAINING',reason='withdraw')
    assert feedback.current('local','local',include_synthetic=True)==[]
    assert feedback.revise(state.run_id,state.user_id,old['event_id'],consent_scope='NO_TRAINING',reason='withdraw')==eid
    assert state.report==snapshot


def training_rows(state,preferred):
    fs=adaptive_tracks.state_features(state,'adaptive:initial')
    tickets=[t.model_dump(mode='json') for t in adaptive_tracks.proposals(state)][:2]
    return [dict(features=fs,actions=tickets,permitted=[0,1],executed_index=i,
        reward=.8 if i==preferred else -.8,terminal=True,next_features=fs,next_actions=[],next_permitted=[],
        next_rule_preferred=None,group=f'fixture-family-{family}',split='train',**q.contracts(q.ADAPTIVE_SCHEMA))
        for family in range(8) for i in range(2)]


@pytest.mark.parametrize('preferred',[0,1])
def test_M03_Q01_Q03_trained_weights_change_actual_first_handler(adaptive_run,monkeypatch,preferred):
    state=adaptive_run('LITE');rows=training_rows(state,preferred)
    model=q.train(rows,epochs=120)
    assert model['training']['parameters_changed']
    state.scratch['ax_bundle'].update(policy=model,policy_version='isolated-test-only')
    called=[]
    from triz.ax.mode_contract import TRACKS
    for track in TRACKS:
        monkeypatch.setitem(nodes.TRACK_FUNCS,track,lambda ctx,t=track:called.append(t))
    monkeypatch.setattr(nodes,'_merge',lambda ctx:False)
    monkeypatch.setattr(nodes,'_evidence',lambda ctx:None)
    adaptive_tracks.run(RunContext(state))
    assert called[0]==rows[0]['actions'][preferred]['parameters']['tracks'][0]
    assert ledger.decision_history(state.run_id,state.user_id)[0]['payload']['selection_mode']=='POLICY_DETERMINISTIC'


def test_Q12_Q13_support_is_independent_and_contracts_not_shape(adaptive_run):
    state=adaptive_run('LITE');rows=training_rows(state,0)
    support=q.support_model(rows*5)
    assert set(support['support'].values())=={8}
    with pytest.raises(ValueError): q.support_model([dict(rows[0],split='holdout')])
    with pytest.raises(ValueError): q.support_model([dict(rows[0],synthetic=True)])
    old=dict(support,feature_schema=q.SCHEMA)
    assert q.choose(old,rows[0]['features'],rows[0]['actions'],[0,1],1)[0]==1
    assert q.choose(old,rows[0]['features'],rows[0]['actions'],[0,1],1)[2]


def test_Q02_Q15_worker_tasks_fail_independently(adaptive_run,monkeypatch):
    state=adaptive_run();candidate(state)
    feedback.user_decisions(state,{'C1':'accept'},{'training_consent':'PROJECT_ONLY'},'keep')
    calls=[]
    def q_failure(*args,**kwargs):
        calls.append(('q',kwargs));raise ValueError('fixture failure')
    monkeypatch.setattr(registry,'train_project',q_failure)
    monkeypatch.setattr(effect_ranker,'train_project',lambda *args,**kwargs:calls.append(('effect',kwargs)) or {'status':'COLLECTING'})
    worker.tick(max_events=1000)
    with store.engine.connect() as c:
        rows=list(c.execute(select(worker.task_queue)).mappings())
    assert {r['task_kind'] for r in rows}=={'routing_q','effect_ranker'}
    assert next(r for r in rows if r['task_kind']=='routing_q')['processed_revision']==0
    effect=next(r for r in rows if r['task_kind']=='effect_ranker')
    assert effect['processed_revision']==effect['revision']
    assert len(calls)==2


def test_M10_C06_C11_incremental_generation_preserves_unchanged_review(adaptive_run,monkeypatch):
    from triz import quality,agent,idea_consolidation,rag
    from triz.schema import RawIdea
    state=adaptive_run();ctx=RunContext(state)
    state.solve.raw_ideas=[RawIdea(id=f'raw-{i}',title=f'idea {i}',idea=f'mechanism {i}',addresses=['TC1']) for i in range(2)]
    monkeypatch.setattr(idea_consolidation,'ensure_consolidated',lambda ctx:None)
    monkeypatch.setattr(rag,'prior_cases_block',lambda state:'')
    generated=[];audited=[]
    def respond(ctx,**kw):
        ids=[i['id'] for i in kw['vars']['ideas']];generated.extend(ids)
        return {'concepts':[{'title':i['title'],'source_idea_ids':[i['id']], 'working_principle':i['idea'],
            'addresses_contradictions':['TC1'],'resolution_argument':'test both requirements','validation_plan':[{'experiment':'comparison'}]}
            for i in kw['vars']['ideas']], 'excluded':[]}
    def review(ctx,rubric,data,facts):
        audited.extend(c['concept_id'] for c in data['concepts'])
        return {'verdict':'PASS','per_concept':[{'concept_id':c['concept_id'],'verdict':'PASS'} for c in data['concepts']]}
    monkeypatch.setattr(agent,'run_agent',respond);monkeypatch.setattr(agent,'verify_artifact',review)
    quality.generate_concepts(ctx)
    baseline={tuple(c.source_idea_ids):c.id for c in state.concepts}
    assert generated==['raw-0','raw-1'] and len(audited)==2
    quality.generate_concepts(ctx)
    assert len(generated)==2 and len(audited)==2
    state.solve.raw_ideas[1].idea='changed mechanism'
    quality.generate_concepts(ctx)
    assert generated==['raw-0','raw-1','raw-1'] and len(audited)==3
    assert next(c.id for c in state.concepts if c.source_idea_ids==['raw-0'])==baseline[('raw-0',)]
    assert len(store.load_state(state.run_id).concepts)==2


def test_C02_Q07_unknown_usage_never_becomes_free_training(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');observed_episode(state,monkeypatch)
    task=ledger.acquire(state.run_id,0,{'node':'fixture-unsettled','request':{'semantic_episode_id':episode(state)}},100)
    assert task['actual'] is None if 'actual' in task else True
    assert outcomes.q_dataset('local','local',include_synthetic=True)['samples']==[]
    assert outcomes.effect_dataset('local','local',include_synthetic=True)['samples']==[]


def test_Q08_C02_future_settlement_is_not_available_at_earlier_cutoff(adaptive_run,monkeypatch):
    from triz.ax.contracts import now
    state=adaptive_run('LITE');observed_episode(state,monkeypatch)
    task=ledger.acquire(state.run_id,0,{'node':'late-fixture-usage','request':{'semantic_episode_id':episode(state)}},100)
    cutoff=now()
    ledger.settle(task,{'usage':'fixture recorded later'},10)
    for project in (outcomes.q_dataset,outcomes.effect_dataset):
        earlier=project('local','local',cutoff,include_synthetic=True)
        assert earlier['samples']==[] and earlier['excluded']['unsettled_usage']==1
        assert project('local','local',include_synthetic=True)['samples']


def test_D05_D06_joint_effect_weight_conserved(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    from triz.schema import RawIdea
    for sid,effect in [('second','E2'),('duplicate','E1')]:
        raw=RawIdea(id=sid,track='H_EFFECTS',title='fixture',idea='combined mechanism',detail={'source_effect_id':effect})
        state.solve.raw_ideas.append(raw);value.source_idea_ids.append(sid)
        next(iter(state.scratch['ax_action_results'].values()))['produced_raw_idea_ids'].append(sid)
    value.active_effect_ids=['E1','E2']
    feedback.final_feedback(state,{'solution_feedback':[{'concept_id':value.id,'rating':5}],'training_consent':'PROJECT_ONLY'})
    manifest=outcomes.effect_dataset('local','local',include_synthetic=True)
    assert {s['effect_id'] for s in manifest['samples']}=={'E1','E2'}
    assert len(manifest['samples'])==2
    assert sum(s['sample_weight'] for s in manifest['samples'])==1


def test_D07_D08_existing_test_submission_enters_common_stream(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    value.validation_plan=[{'experiment':'열 저항 비교'}]
    runtime.checkpoint(state,'s6_concept');store.save_state(state)
    body=dict(event_id='actual-test-fixture',expected_epoch=0,snapshot_id=state.scratch['ax_snapshot_id'],
        target_version_id=state.scratch['ax_members']['concepts'],candidate_id=value.id,obligation_id=value.id+':test:0',
        decision_type='RECORD_TEST_RESULT',reason='사용자가 제출한 시험 fixture',result='FAIL',conditions='동일 접촉 압력',
        evidence_refs=['fixture-measurement-record'],measurement={'thermal_resistance':12},consent='PROJECT_ONLY')
    assert not ledger.submit_review(state.run_id,state.user_id,body)['duplicate']
    assert ledger.submit_review(state.run_id,state.user_id,body)['duplicate']
    row=next(r for r in events(state) if r['evaluation_stage']=='recorded_test')
    assert row['source_event_id']==body['event_id'] and row['observed_value']==-1
    assert row['evidence_level']=='USER_REPORTED_TEST_NOT_INDEPENDENTLY_VALIDATED'


def test_U08_M11_conflicting_clones_do_not_amplify_terminal_utility(adaptive_run):
    state=adaptive_run();candidate(state,'C1');candidate(state,'C2')
    feedback.user_decisions(state,{'C2':'drop','C1':'accept'},{'training_consent':'PROJECT_ONLY'},'same-submit')
    rows=events(state);settings=state.scratch['ax_bundle']['run_contract']['feedback_settings']
    assert len(rows)==2
    first=outcomes.outcome(rows,settings,[])
    assert first['user_utility']==0
    assert first==outcomes.outcome(list(reversed(rows)),settings,[])
    clone=dict(next(r for r in rows if r['candidate_id']=='C1'),candidate_id='C3',event_id='fixture-clone')
    assert outcomes.outcome(rows+[clone],settings,[])['total']==first['total']


def test_Q03_cost_changes_learned_preference_with_equal_quality(adaptive_run):
    state=adaptive_run('LITE');rows=training_rows(state,0)
    for row in rows:
        # Controlled synthetic sequence: identical observed proxy, different settled fixture cost.
        cost=(.2,.7)[row['executed_index']]
        row['reward']=.7-cost
        row['dimensions']={'observed_quality':.7,'normalized_cost':cost}
    first=q.train(rows,epochs=120)
    assert q.choose(first,rows[0]['features'],rows[0]['actions'],[0,1],1)[0]==0
    for row in rows: row['reward']=.7-(.7,.2)[row['executed_index']]
    second=q.train(rows,epochs=120)
    assert q.choose(second,rows[0]['features'],rows[0]['actions'],[0,1],0)[0]==1


def test_D11_Q15_effect_prediction_uses_selection_snapshot(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');value,_=observed_episode(state,monkeypatch)
    before=outcomes.effect_dataset('local','local',include_synthetic=True)['samples'][0]
    feedback.final_feedback(state,{'solution_feedback':[{'concept_id':value.id,'rating':1}],'training_consent':'PROJECT_ONLY'})
    after=outcomes.effect_dataset('local','local',include_synthetic=True)['samples'][0]
    assert before['features']==after['features'] and before['label']!=after['label']
    assert not {'rating','candidate_score','adopted'}&after['context'].keys()
    effects=state.scratch['ax_bundle']['effects'][0]['effects'];ctx=after['context']
    model=effect_ranker.train([dict(feature_schema=effect_ranker.UTILITY_SCHEMA,context=ctx,
        effect_id=e['id'],features=effect_ranker.features(ctx,e),label=1 if e['id']=='E2' else -1) for e in effects])
    state.scratch['ax_bundle']['effect_ranker']=model
    result=effect_history.rerank(state,effects,['열 제거'])
    assert result[0]['id']=='E2'


def test_M10_delta_gate_answer_is_consumed_at_reference_resume(adaptive_run,monkeypatch):
    state=adaptive_run();candidate(state)
    runtime.checkpoint(state,'s6_concept');runtime.checkpoint(state,'s7_gate')
    state.scratch['adaptive_gate_pending_ids']=['C1']
    state.scratch['resume_payload']={'decisions':{'C1':'accept'},'training_consent':'PROJECT_ONLY'}
    monkeypatch.setattr(adaptive_tracks,'followup',lambda ctx,phase:[])
    runtime.before_stage(RunContext(state),'s8_references')
    assert state.check_for('C1').verdict=='CONDITIONAL'
    assert not state.check_for('C1').requires_user_decision
    assert 'adaptive_gate_pending_ids' not in state.scratch
    assert len(events(state))==1


@pytest.mark.parametrize('case',[
    'test_q01_nonterminal_regional_support_matches_online',
    'test_q03_independent_support_reasons',
    'test_q06_q07_unsupported_rule_is_not_single_supported_backup',
    'test_q08_supported_rule_and_forced',
    'test_q09_explicit_terminal_needs_no_next_data',
    'test_q12_holdout_cannot_build_support_or_cross_episode',
])
def test_Q08_Q09_Q10_Q11_adaptive_support_backup_contract(monkeypatch,case):
    """Run the preserved support/backup assertions against the new contract too."""
    import test_routing_q_support_contract as regression
    original=regression.fixture_q
    def adaptive_fixture(patch):
        policy,features,tickets,row=original(patch)
        features['schema']=q.ADAPTIVE_SCHEMA
        policy.update(feature_schema=q.ADAPTIVE_SCHEMA,**q.contracts(q.ADAPTIVE_SCHEMA))
        policy['state_support']={q.support_region(features,a):4 for a in tickets[:2]}
        row.update(q.contracts(q.ADAPTIVE_SCHEMA))
        return policy,features,tickets,row
    monkeypatch.setattr(regression,'fixture_q',adaptive_fixture)
    getattr(regression,case)(monkeypatch)


def test_Q10_adaptive_train_evaluate_use_the_same_supported_backup(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');rows=training_rows(state,0)
    row=dict(rows[0],terminal=False,next_features=rows[0]['features'],
             next_actions=rows[0]['actions'],next_permitted=[0,1],next_rule_preferred=0)
    calls=[];original=q.next_state_backup
    def capture(**kwargs):
        result=original(**kwargs)
        if not kwargs['transition']['terminal']: calls.append(result['mask'])
        return result
    monkeypatch.setattr(q,'next_state_backup',capture)
    model=q.train(rows+[row],epochs=2)
    q.evaluate(model,[row])
    assert calls and all(mask==[0,1] for mask in calls)
    assert set(q.choose(model,row['features'],row['actions'],[0,1],0)[1])=={0,1}
