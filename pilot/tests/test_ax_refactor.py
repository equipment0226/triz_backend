"""Offline acceptance of new contracts; synthetic results are not field evidence."""
import copy
import json
import socket
import pytest
from sqlalchemy import select
from triz import pipeline, nodes, agent, store, knowledge
from triz.context import RunContext
from triz.schema import (TechnicalContradiction, PhysicalContradiction, SuFieldModel,
                         TrimmingItem, RawIdea, ConceptSpec, ConstraintCheckResult, Constraint)
from triz.settings import settings
from triz.ax import runtime, coordinator, ledger, effect_history, routing_q, effect_ranker, registry
from triz.ax.mode_contract import contract, PROFILES, coverage
from triz.ax.contracts import ActionTicket, Conflict, digest


@pytest.fixture
def newrun(monkeypatch):
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('Unexpected network'))
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v2')
    effects = [{'id':'heat', 'effects':[
        {'id':'E1','name':'First','function_ko':'열 제거','principle':'전도','conditions':'전도 경로 확보','domain':'PHYSICAL','mechanism_key':'conduction'},
        {'id':'E2','name':'Second','function_ko':'열 제거','principle':'대류','conditions':'유체 사용 가능','domain':'PHYSICAL','mechanism_key':'convection'}]}]
    monkeypatch.setattr(knowledge, 'effects', lambda:copy.deepcopy(effects))
    original = knowledge._load
    monkeypatch.setattr(knowledge, '_load', lambda name: {} if name == 'effects_sources.json' else original(name))
    def create(mode='FULL', user='local'):
        s = pipeline.create_run('열 제거와 전력 증가 모순', mode=mode, user_id=user, workflow_version='triz-ax-v3.1')
        s.domain.problem_type = 'PHYSICAL_TECHNICAL'
        s.confirm.user_confirmed = True
        s.definition.technical_contradictions = [TechnicalContradiction(id='TC1',if_action='유량 증가',then_good='열 제거',but_bad='전력 증가')]
        s.definition.physical_contradictions = [PhysicalContradiction(id='PC1',element='유체',parameter='유량',state_a='높음',state_b='낮음')]
        s.analysis.su_fields = [SuFieldModel(s1='plate',s2='fluid',field='heat')]
        s.definition.trimming = [TrimmingItem()]
        for stage in ('s2_confirm','s3_analyze','s4_define'):
            runtime.checkpoint(s, stage)
        return s
    return create


@pytest.mark.parametrize('mode', ['LITE','FULL','DEEP'])
def test_new_modes_pin_and_complete_every_track(newrun,monkeypatch,mode):
    s = newrun(mode)
    called = []
    from triz.schema import ARIZRun
    def run(track):
        def handler(ctx):
            called.append(track)
            ctx.state.solve.raw_ideas.append(RawIdea(id='raw-'+track,track=track,title=track,idea=track))
            if track == 'D_ARIZ':
                ctx.state.solve.ariz = ARIZRun()
        return handler
    for track in PROFILES[mode]['tracks']:
        monkeypatch.setitem(nodes.TRACK_FUNCS, track, run(track))
    monkeypatch.setattr(nodes,'_evidence',lambda ctx:None)
    monkeypatch.setattr(nodes,'_merge',lambda ctx:False)
    monkeypatch.setattr(routing_q,'choose',lambda *a,**k:pytest.fail('Mandatory work must not route through Q'))
    coordinator.route(RunContext(s))
    nodes.s5_solve(RunContext(s))
    assert set(called) == set(PROFILES[mode]['tracks'])
    assert coverage(s)['complete']
    assert len(s.scratch['ax_action_results']) == len(called)
    assert ledger.decision_history(s.run_id,s.user_id) == []
    before = list(called)
    nodes.s5_solve(RunContext(s))
    assert called == before


@pytest.mark.parametrize('mode',['LITE','FULL'])
def test_executor_rejects_ariz_despite_high_policy(newrun,mode):
    s = newrun(mode)
    with pytest.raises(ValueError,match='forbidden'):
        nodes._run_tracks(RunContext(s), ['D_ARIZ'])
    with pytest.raises(ValueError,match='forbidden'):
        nodes._track_d_ariz(RunContext(s))
    ticket = ActionTicket(action_type='SOLVE_SUBPROBLEM',parameters={'tracks':['D_ARIZ']},
        expected_outputs=[],allowed_tools=['legacy_tracks'],reason='test')
    assert coordinator.feasible(s,ticket,handlers={'SOLVE_SUBPROBLEM'}) == 'mode_forbidden_track'


def test_deep_core_preserved_optional_off(newrun,monkeypatch):
    from triz.ax import recovery, coherence_recovery
    s = newrun('DEEP')
    monkeypatch.setattr(agent,'run_agent',lambda *a,**k:pytest.fail('DEEP optional call'))
    assert recovery.run(RunContext(s)) == []
    assert coherence_recovery.run(RunContext(s),'after_constraints') == []
    assert coordinator.expand(RunContext(s),True) is False
    assert contract(s)['trace_and_snapshot_enabled']
    assert s.scratch['ax_snapshot_id']


def test_missing_input_not_applicability_and_partial_summary(newrun):
    s = newrun('DEEP'); s.definition.trimming=[]
    s.domain.problem_type='INFORMATION_SOFTWARE'
    coordinator.route(RunContext(s))
    assert s.scratch['ax_track_execution']['E_TRIMMING']['status']=='BLOCKED_MISSING_INPUT'
    assert s.scratch['ax_track_execution']['C_STANDARDS']['status']=='NOT_APPLICABLE'
    assert not coverage(s)['complete']


def test_expansion_chooses_real_track_and_preserves_original(newrun,monkeypatch):
    s=newrun(); coordinator.route(RunContext(s))
    s.scratch['ax_track_execution']={t:dict(status='COMPLETED',output_count=1) for t in PROFILES['FULL']['tracks']}
    s.solve.raw_ideas=[RawIdea(id='original',idea='original',title='original')]
    called=[]
    def handler(ctx):
        called.append('H_EFFECTS')
        ctx.state.solve.raw_ideas.append(RawIdea(id='extra',track='H_EFFECTS',idea='extra'))
    monkeypatch.setitem(nodes.TRACK_FUNCS,'H_EFFECTS',handler)
    monkeypatch.setattr(nodes,'_merge',lambda ctx:False)
    # Deterministic catalog order prefers A; select H with a stubbed qualified policy.
    monkeypatch.setattr(routing_q,'choose',lambda p,f,t,allowed,preferred:(next(i for i,a in enumerate(t) if a['parameters'].get('tracks')==['H_EFFECTS']),{},None))
    s.scratch['ax_bundle']['policy']={'fixture':True}
    assert coordinator.expand(RunContext(s),True)
    assert called==['H_EFFECTS']
    assert {i.id for i in s.solve.raw_ideas}=={'original','extra'}
    decisions=ledger.decision_history(s.run_id,s.user_id)
    assert len(decisions[-1]['payload']['actions'])>=3
    assert decisions[-1]['payload']['selection_mode']=='POLICY_DETERMINISTIC'
    assert any(r['produced_raw_idea_ids']==['extra'] for r in s.scratch['ax_action_results'].values())


def action(track):
    return dict(action_type='SOLVE_SUBPROBLEM',parameters={'tracks':[track], 'gap_kinds':['GAP']}, model_role='REASONING',reserved_microusd=100000)


def samples():
    actions=[action('A_MATRIX'),action('H_EFFECTS')]
    rows=[]
    for mode in ('LITE','FULL'):
        for chosen in (0,1):
            for i in range(8):
                fs=dict(schema=routing_q.SCHEMA,mode=mode,phase='solve',gaps=['GAP'],remaining=.8,tracks=[])
                reward=1 if chosen==(0 if mode=='LITE' else 1) else -1
                rows.append(dict(features=fs,actions=actions,executed_index=chosen,permitted=[0,1],reward=reward,
                    next_features=fs,next_actions=[],terminal=True,group=mode+str(i),split='train',maturity='CONCEPT_PROXY'))
    return rows


def test_action_dependent_q_changes_choices_by_state_and_masks():
    rows=samples(); model=routing_q.train(rows,epochs=400)
    assert model['training']['parameters_changed']
    assert model['training']['loss_last']<model['training']['loss_first']
    for mode,expected in [('LITE',0),('FULL',1)]:
        fs=next(r['features'] for r in rows if r['features']['mode']==mode)
        assert routing_q.choose(model,fs,rows[0]['actions'],[0,1],0)[0]==expected
        assert routing_q.choose(model,fs,rows[0]['actions'],[1],1)[0]==1
        options=rows[0]['actions']+[dict(action_type='DEFER',parameters={},model_role='CODE')]
        assert routing_q.choose(model,fs,options,[0,1,2],0)[0]==expected
    wrong=dict(model,feature_schema='ax-features-v2')
    assert routing_q.choose(wrong,rows[0]['features'],rows[0]['actions'],[0,1],0)[2]=='incompatible_feature_schema'
    unsupported=copy.deepcopy(model); unsupported['support']={}
    assert routing_q.choose(unsupported,rows[0]['features'],rows[0]['actions'],[0,1],0)[2]=='insufficient_action_support'


def effect_candidate(s,track='H_EFFECTS',effect='E1'):
    s.solve.raw_ideas=[RawIdea(id='raw1',track=track,idea='열 경로',source_ref=effect,
        detail={'source_effect_id':effect,'conditions':['전도 경로 확보'],'source_step':'5.1'})]
    s.concepts=[ConceptSpec(id='C1',title='냉각',working_principle='전도 경로',source_idea_ids=['raw1'],quality_status='PASS')]
    s.constraint_checks=[ConstraintCheckResult(concept_id='C1',verdict='CONDITIONAL')]
    return effect_history.collect(s)[0]


def review(app,decision='condition_confirmed',consent='PROJECT_ONLY'):
    return dict(candidate_id='C1',effect_application_id=app['application_id'],condition_id=app['conditions'][0]['condition_id'],
                decision=decision,training_consent=consent,reason_code='resource_available')


@pytest.mark.parametrize('track',['H_EFFECTS','D_ARIZ'])
def test_common_effect_contract_and_idempotent_scoped_history(newrun,track):
    s=newrun(); app=effect_candidate(s,track)
    s.scratch['ax_response_received_at']='2026-01-01T00:00:00+00:00'
    body=review(app)
    effect_history.user_reviews(s,[body],{'C1':'accept'},'answer-1')
    effect_history.user_reviews(s,[body],{'C1':'accept'},'answer-1')
    assert s.constraint_checks[0].verdict=='CONDITIONAL'
    obs=effect_history.observations(s.user_id,s.user_id)
    assert len([r for r in obs if r['application']['run_id']==s.run_id])==1
    assert app['source_track']==track
    assert effect_history.observations('different-user',s.user_id)==[]
    with pytest.raises(Conflict):
        effect_history.user_reviews(s,[dict(body,effect_application_id='foreign')],{'C1':'accept'},'answer-2')


def test_drop_and_unknown_not_negative_and_immutable_reference(newrun):
    s=newrun(); app=effect_candidate(s)
    effect_history.user_reviews(s,[review(app,'unknown')],{'C1':'drop'},'drop')
    s.concepts=[]
    assert not [r for r in effect_history.observations(s.user_id,s.user_id) if r['application']['run_id']==s.run_id]
    with store.engine.connect() as c:
        row=c.execute(select(effect_history.applications.c.payload).where(effect_history.applications.c.application_id==app['application_id'])).scalar_one()
    assert json.loads(row)['candidate_snapshot']['id']=='C1'


def test_history_changes_priority_only_with_matching_conditions(newrun):
    s=newrun(user='history-owner'); app=effect_candidate(s,effect='E2')
    effect_history.user_reviews(s,[review(app)],{'C1':'accept'},'condition')
    nxt=newrun(user='history-owner')
    candidates=nxt.scratch['ax_bundle']['effects'][0]['effects']
    ranked=effect_history.rerank(nxt,candidates,['열 제거'])
    assert ranked[0]['id']=='E2'
    nxt.constraints.items=[Constraint(id='different',statement='외부 전원 사용 금지',hard=True)]
    assert effect_history.rerank(nxt,candidates,['열 제거'])[0]['id']=='E1'
    other=newrun(user='other-owner')
    assert effect_history.rerank(other,candidates,['열 제거'])[0]['id']=='E1'


def test_effect_ranker_trains_separately_and_unknown_context_falls_back():
    context={'domain':'PHYSICAL','constraints':['no power'],'functions':['cool']}
    rows=[]
    for eid,label in [('E1',1),('E2',-1)]:
        app={'effect_id':eid,'mechanism_key':eid}
        rows.extend(dict(features=effect_ranker.features(context,app),context=context,effect_id=eid,label=label,
                         application=app) for _ in range(8))
    model=effect_ranker.train(rows)
    assert model['training']['parameters_changed']
    assert effect_ranker.predict(model,context,rows[0]['application'])>effect_ranker.predict(model,context,rows[-1]['application'])
    assert effect_ranker.predict(model,dict(context,domain='OTHER'),rows[0]['application'])==0
    assert model['feature_schema']!=routing_q.SCHEMA


def test_semantic_rerun_archives_state_without_resetting_budget(newrun,monkeypatch):
    s=newrun(); s.status='COMPLETED'
    s.scratch.update(ax_recovery_phases=['before_constraints'],ax_expansion_rounds=1,ax_constraint_failures={'C1':{}},ax_selection={'old':True})
    store.save_state(s); old_episode=s.scratch['semantic_episode_id']
    monkeypatch.setattr(pipeline,'start',lambda *a:None)
    assert pipeline.rerun_from(s.run_id,'s4_define')
    nxt=store.load_state(s.run_id)
    assert nxt.scratch['semantic_episode_id']!=old_episode
    assert 'ax_recovery_phases' not in nxt.scratch and 'ax_expansion_rounds' not in nxt.scratch
    assert nxt.scratch['ax_semantic_archive'][-1]['projection']['ax_selection']=={'old':True}
    assert nxt.cost.budget_usd==s.cost.budget_usd


def test_80_raw_sources_preserved_in_deep_merge(newrun,monkeypatch):
    s=newrun('DEEP')
    s.solve.raw_ideas=[RawIdea(id=f'raw-{i}',track='H_EFFECTS' if i>=70 else 'A_MATRIX',idea=f'mechanism {i}',
        resolution_status='TRADEOFF',source_idea_ids=[f'raw-{i}'],addresses=['TC1']) for i in range(80)]
    def merge(ctx,**kw):
        assert len(kw['vars']['all_ideas'])==80
        return dict(ideas=[dict(keep_ids=[f'raw-{i}'],title=f'mechanism {i}',idea=f'mechanism {i}',
                               selection_reason='concrete comparison',resolution_status='RESOLVED') for i in range(10)],
                    deferred=[dict(keep_ids=[f'raw-{i}'],reason='requires additional resource evidence') for i in range(10,80)])
    monkeypatch.setattr(agent,'run_agent',merge)
    nodes._merge(RunContext(s))
    assert len(s.solve.raw_ideas)==10
    assert len(s.scratch['ax_idea_inventory'])==80
    assert len(s.scratch['idea_consolidation']['source_ideas'])==80
    assert all(i.resolution_status!='RESOLVED' for i in s.solve.raw_ideas)


def test_user_condition_rechecks_only_changed_candidate(newrun,monkeypatch):
    s=newrun(); app=effect_candidate(s)
    s.constraints.items=[Constraint(id='R1',statement='전도 경로 필요')]
    untouched=ConceptSpec(id='C2',title='다른 해결안',quality_status='PASS')
    s.concepts.append(untouched)
    s.constraint_checks.append(ConstraintCheckResult(concept_id='C2',verdict='CONDITIONAL'))
    s.scratch['resume_payload']=dict(decisions={'C1':'accept','C2':'accept'},application_reviews=[review(app)])
    called=[]
    def gate(ctx,**kw):
        called.extend(c['concept_id'] for c in kw['vars']['concepts_for_gate'])
        return {'results':[dict(concept_id='C1',verdict='PASS',per_constraint=[dict(constraint_id='R1',verdict='PASS')])]}
    monkeypatch.setattr(agent,'run_agent',gate)
    nodes.s7_gate(RunContext(s))
    assert called==['C1']
    assert s.concept('C2')==untouched
    assert s.check_for('C1').verdict=='CONDITIONAL'
    assert not s.check_for('C1').requires_user_decision


def test_review_withdrawal_and_cutoff_disable_future_history(newrun):
    s=newrun(user='withdrawal-owner'); app=effect_candidate(s)
    store.save_state(s)
    effect_history.user_reviews(s,[review(app)],{'C1':'accept'},'answer')
    observed=effect_history.observations(s.user_id,s.user_id)
    eid=observed[0]['review']['event_id']
    assert effect_history.observations(s.user_id,s.user_id,cutoff='2000-01-01T00:00:00+00:00')==[]
    body=dict(event_id='withdraw-'+s.run_id,expected_epoch=s.scratch['execution_epoch'],snapshot_id=s.scratch['ax_snapshot_id'],
              supersedes_event_id=eid,training_consent='NO_TRAINING',reason='withdraw',judgment=None)
    effect_history.revise_review(s.run_id,s.user_id,body)
    effect_history.revise_review(s.run_id,s.user_id,body)
    assert effect_history.observations(s.user_id,s.user_id)==[]
    with ledger.store.engine.connect() as c:
        assert not registry.reviews_current({'review_ids':[eid]},s.user_id,s.user_id,c)


def test_paid_call_identity_survives_transport_epoch_and_unknown(newrun):
    s=newrun(); h=ledger.head(s.run_id)
    context=dict(semantic_episode_id=s.scratch['semantic_episode_id'],action_instance_id='stable-action',
                 execution_epoch=0,input_snapshot_id=s.scratch['ax_snapshot_id'],exact_input_versions=s.scratch['ax_members'],
                 ticket={'input_snapshot_id':s.scratch['ax_snapshot_id']})
    request=dict(node='stub',request={'prompt':'same'},action_context=context)
    first=ledger.acquire(s.run_id,0,request,100)
    ledger.settle(first,{'fixture':True},10)
    s.scratch['execution_epoch']=1; ledger.advance_epoch(s,'transport retry')
    request=copy.deepcopy(request); request['action_context']['execution_epoch']=1
    replay=ledger.acquire(s.run_id,1,request,100)
    assert replay['cached'] and replay['task_id']==first['task_id']
    assert ledger.budget(s.run_id)['spent_microusd']==10
    unknown=ledger.acquire(s.run_id,1,dict(request,node='unknown'),100)
    ledger.settle(unknown,{'usage':'unknown'},None,status='UNKNOWN')
    s.scratch['execution_epoch']=2; ledger.advance_epoch(s,'transport retry')
    request['action_context']['execution_epoch']=2
    assert ledger.acquire(s.run_id,2,dict(request,node='unknown'),100)['blocked']=='UNKNOWN'


def test_worker_effect_queue_collecting_and_schema_pointers(newrun):
    from triz.ax import worker
    s=newrun(user='worker-owner'); app=effect_candidate(s)
    store.save_state(s)
    effect_history.user_reviews(s,[review(app)],{'C1':'accept'},'worker-answer')
    result=worker.tick(max_events=1000,max_projects=100)
    project=next(p for p in result['projects'] if p['scope']==registry.scope(s.user_id,s.user_id))
    assert project['effect_ranker']['status']=='COLLECTING'
    assert project['routing_policy']['status']=='COLLECTING'
    assert result['external_llm_calls']==0
    assert registry.task_scope(s.user_id,s.user_id,'routing_q',routing_q.SCHEMA)!=registry.task_scope(s.user_id,s.user_id,'effect_ranker',effect_ranker.SCHEMA)


def test_routing_review_result_transition_dataset_chain(newrun):
    from triz.ax.action_runtime import executing, emit, episode
    from triz.ax import learning
    s=newrun(user='routing-data-owner')
    proposals=[ActionTicket(**action(t),expected_outputs=['RawIdea'],allowed_tools=['legacy_tracks'],reason='fixture') for t in ('A_MATRIX','H_EFFECTS')]
    ticket,did=coordinator.decide(s,proposals,0,{'SOLVE_SUBPROBLEM'},'solve:fixture')
    with executing(RunContext(s),ticket,did):
        s.solve.raw_ideas=[RawIdea(id='raw1',track='A_MATRIX',idea='path',detail={'source_effect_id':'E1','conditions':['전도 경로 확보']})]
    s.concepts=[ConceptSpec(id='C1',working_principle='path',source_idea_ids=['raw1'])]
    app=effect_history.collect(s)[0]
    effect_history.user_reviews(s,[review(app)],{'C1':'accept'},'routing-answer')
    emit(s,'OPTIONAL_TRANSITION',dict(semantic_episode_id=episode(s),decision_id=did,next_decision_id=None,terminal_reason='OPTIONAL_PHASES_COMPLETED'))
    store.save_state(s)
    dataset=learning.dataset(s.user_id,s.user_id,feature_schema=routing_q.SCHEMA)
    assert len(dataset['samples'])==1
    row=dataset['samples'][0]
    assert row['reward']==.5 and row['maturity']=='CONCEPT_PROXY'
    assert row['terminal'] and row['dimensions']['actual_microusd']==0
    model=routing_q.train(dataset['samples'])
    assert model['training']['parameters_changed']
    assert not learning.readiness(dataset)['ready']


def test_isolated_review_queue_train_shadow_next_run_end_to_end(newrun):
    """An isolated SQLite corpus exercises plumbing, never a production pointer."""
    from triz.ax.action_runtime import executing, emit, episode
    from triz.ax import worker
    owner='offline-shadow-corpus'
    first=None
    for family in range(8):
        for sample in range(4):
            s=newrun(user=owner)
            first=first or s
            s.scratch['ax_problem_group']='synthetic-family-'+str(family)
            proposals=[ActionTicket(**action(t),expected_outputs=['RawIdea'],allowed_tools=['legacy_tracks'],reason='offline stub') for t in ('A_MATRIX','H_EFFECTS')]
            chosen=sample%2
            ticket,did=coordinator.decide(s,proposals,chosen,{'SOLVE_SUBPROBLEM'},'solve:fixture')
            eid='E1' if chosen==0 else 'E2'
            with executing(RunContext(s),ticket,did):
                s.solve.raw_ideas=[RawIdea(id='raw1',track=ticket.parameters['tracks'][0],idea='synthetic mechanism',
                    detail={'source_effect_id':eid,'conditions':['explicit fixture condition']})]
            s.concepts=[ConceptSpec(id='C1',working_principle='synthetic mechanism',source_idea_ids=['raw1'])]
            app=effect_history.collect(s)[0]
            effect_history.user_reviews(s,[review(app,'condition_confirmed' if chosen==0 else 'condition_rejected')],{'C1':'accept'},'answer-'+s.run_id)
            emit(s,'OPTIONAL_TRANSITION',dict(semantic_episode_id=episode(s),decision_id=did,next_decision_id=None,terminal_reason='OPTIONAL_PHASES_COMPLETED'))
            store.save_state(s)
    result=worker.tick(max_events=1000,max_projects=100)
    item=next(p for p in result['projects'] if p['scope']==registry.scope(owner,owner))
    assert item['routing_policy']['status']=='SHADOW'
    assert item['effect_ranker']['status']=='SHADOW'
    assert first.scratch['ax_bundle'].get('shadow_policy') is None
    nxt=newrun(user=owner)
    assert nxt.scratch['ax_bundle']['shadow_policy']['feature_schema']==routing_q.SCHEMA
    assert nxt.scratch['ax_bundle']['shadow_effect_ranker']['feature_schema']==effect_ranker.SCHEMA
    assert nxt.scratch['ax_bundle']['policy'] is None
    with pytest.raises(Conflict,match='shadow'):
        registry.promote_task(owner,owner,'routing_q',routing_q.SCHEMA,item['routing_policy']['policy_id'],'test','synthetic plumbing only')
    # Production ingestion explicitly excludes fixtures carrying their provenance.
    first.scratch['synthetic']=True
    store.save_state(first)
    from triz.ax import learning
    assert learning.dataset(owner,owner,feature_schema=routing_q.SCHEMA)['excluded']['test_or_missing_run']==1


def test_offline_deep_tracks_merge_gate_frozen_report(newrun,monkeypatch):
    from triz import quality, render, presentation
    from triz.schema import ARIZRun
    s=newrun('DEEP'); ctx=RunContext(s)
    for track in PROFILES['DEEP']['tracks']:
        def handler(child,track=track):
            child.state.solve.raw_ideas.append(RawIdea(id='raw-'+track,title=track,idea='가설 '+track,track=track,
                addresses=['TC1'],resolution_status='UNSUPPORTED'))
            if track=='D_ARIZ':
                child.state.solve.ariz=ARIZRun()
        monkeypatch.setitem(nodes.TRACK_FUNCS,track,handler)
    monkeypatch.setattr(nodes,'_evidence',lambda ctx:None)
    def provider(child,**kw):
        assert kw['node']=='s5_merge'
        return {'ideas':[dict(keep_ids=[i['id']],title=i['title'],idea=i['idea']) for i in kw['vars']['all_ideas']]}
    monkeypatch.setattr(agent,'run_agent',provider)
    runtime.before_stage(ctx,'s5_solve'); nodes.s5_solve(ctx); runtime.checkpoint(s,'s5_solve')
    def concepts(child):
        child.state.concepts=[ConceptSpec(id='C-'+i.id,title=i.title,working_principle=i.idea,
            source_idea_ids=[i.id],addresses_contradictions=['TC1'],quality_status='PASS') for i in child.state.solve.raw_ideas]
    monkeypatch.setattr(quality,'generate_concepts',concepts)
    runtime.before_stage(ctx,'s6_concept'); nodes.s6_concept(ctx); runtime.checkpoint(s,'s6_concept')
    runtime.before_stage(ctx,'s7_gate'); nodes.s7_gate(ctx); runtime.checkpoint(s,'s7_gate')
    runtime.before_stage(ctx,'s8_references'); runtime.checkpoint(s,'s8_references')
    runtime.checkpoint(s,'s8_evaluate'); runtime.before_stage(ctx,'s9_report'); nodes.s9_report(ctx)
    assert coverage(s)['complete']
    assert len(s.scratch['ax_idea_inventory'])==8
    assert ledger.decision_history(s.run_id,s.user_id)==[]
    markdown=s.report.markdown; snapshot=s.scratch['ax_report_snapshot_id']
    before_view=presentation.view(s)
    assert '모드의 적용 가능 필수 기법 실행 완료' in markdown
    s.concepts[0].title='uncommitted change'
    assert render.render_report(s,{})==markdown
    assert presentation.view(s)['solutions']==before_view['solutions']
    assert s.scratch['ax_report_snapshot_id']==snapshot


def test_condition_recheck_transport_failure_retains_response(newrun,monkeypatch):
    from triz.context import AbortRun
    s=newrun(); app=effect_candidate(s)
    s.constraints.items=[Constraint(id='R1',statement='전도 경로 필요')]
    s.scratch['resume_payload']=dict(decisions={'C1':'accept'},application_reviews=[review(app)])
    calls=[]
    def gate(ctx,**kw):
        calls.append(kw['node'])
        if len(calls)==1:
            raise AbortRun('offline transport interruption')
        return {'results':[dict(concept_id='C1',verdict='CONDITIONAL')]}
    monkeypatch.setattr(agent,'run_agent',gate)
    with pytest.raises(AbortRun):
        nodes.s7_gate(RunContext(s))
    assert s.scratch['ax_gate_response_pending']['decisions']=={'C1':'accept'}
    nodes.s7_gate(RunContext(s))
    assert 'ax_gate_response_pending' not in s.scratch
    rows=[r for r in effect_history.observations(s.user_id,s.user_id) if r['application']['run_id']==s.run_id]
    assert len(rows)==1 and s.check_for('C1').verdict=='CONDITIONAL'


def test_full_q_selects_other_candidate_actual_repair_and_independent_audit(newrun,monkeypatch):
    from test_ax_phase1 import candidate
    from test_ax_coherence_recovery import proposal
    from triz.ax import coherence_recovery
    from triz import quality
    s=newrun()
    s.definition.technical_contradictions[0].id='TC-DLC'
    s.definition.physical_contradictions=[]
    runtime.checkpoint(s,'s4_define'); candidate(s)
    s.concepts[0].quality_status='REVISE'
    s.concepts.append(s.concepts[0].model_copy(deep=True,update={'id':'C2','title':'second repair target'}))
    s.scratch['ax_mechanisms']['C2']=copy.deepcopy(s.scratch['ax_mechanisms']['DLC-1'])
    baseline=copy.deepcopy(s.concepts)
    raw=proposal(s)
    raw['active_effect_ids']=[]  # This new-run fixture has no saved scientific-effect source.
    calls=[]; audits=[]
    def provider(ctx,**kw):
        calls.append((kw['vars']['baseline']['id'],kw['tier']))
        return raw
    def audit(ctx):
        audits.extend(c.id for c in ctx.state.concepts)
        ctx.state.concepts[0].quality_status='PASS'
    monkeypatch.setattr(agent,'run_agent',provider)
    monkeypatch.setattr(quality,'audit_concepts',audit)
    monkeypatch.setattr(routing_q,'choose',lambda p,f,t,allowed,preferred:
        (next(i for i,a in enumerate(t) if a['parameters'].get('candidate_id')=='C2'),{},None))
    s.scratch['ax_bundle']['policy']={'fixture':True}
    s.scratch['ax_bundle']['limits']['max_optional_rounds']=1
    added=coherence_recovery.run(RunContext(s),'before_constraints')
    assert len(added)==1 and calls==[('C2','T2')]
    assert audits==added
    assert s.concepts[:2]==baseline
    decision=ledger.decision_history(s.run_id,s.user_id)[-1]['payload']
    assert decision['selection_mode']=='POLICY_DETERMINISTIC' and len(decision['actions'])==3
    result=next(r for r in s.scratch['ax_action_results'].values() if r.get('candidate_ids'))
    assert result['candidate_ids']==added and result['ticket']['parameters']['candidate_id']=='C2'


def test_budget_forces_optional_exit_and_stale_ticket_is_rejected(newrun,monkeypatch):
    s=newrun()
    task=ledger.acquire(s.run_id,0,{'fixture':'mandatory-cost'},1900000)
    ledger.settle(task,{'fixture':True},1900000)
    ticket=ActionTicket(**action('H_EFFECTS'),expected_outputs=['RawIdea'],allowed_tools=['legacy_tracks'],reason='test')
    monkeypatch.setattr(routing_q,'choose',lambda *a,**k:pytest.fail('Forced exit must not invoke Q'))
    s.scratch['ax_bundle']['policy']={'fixture':True}
    chosen,did=coordinator.decide(s,[ticket,coordinator.defer_ticket(s)],0,{'SOLVE_SUBPROBLEM','DEFER'},'solve:budget')
    assert chosen.action_type=='DEFER'
    assert ledger.decision_history(s.run_id,s.user_id)[-1]['payload']['selection_mode']=='FORCED'
    stale=ticket.model_copy(update={'input_snapshot_id':'foreign'})
    assert coordinator.feasible(s,stale,handlers={'SOLVE_SUBPROBLEM'})=='stale_input_snapshot'


def test_optional_limit_keeps_unknown_reservations_and_replays_free(newrun):
    s=newrun()
    context=dict(semantic_episode_id=s.scratch['semantic_episode_id'],action_instance_id='optional',optional=True,
                 ticket={},execution_epoch=0)
    request=dict(node='optional',action_context=context)
    task=ledger.acquire(s.run_id,0,request,100000,optional_limit=100000)
    ledger.settle(task,{'fixture':True},50000)
    assert ledger.acquire(s.run_id,0,request,100000,optional_limit=100000)['cached']
    with pytest.raises(Conflict,match='Optional AX budget'):
        ledger.acquire(s.run_id,0,dict(request,node='another'),100000,optional_limit=100000)


def test_action_scope_enforces_primary_and_review_roles(newrun,monkeypatch):
    from triz.ax import gateway
    from triz.ax.action_runtime import executing
    from triz.context import AbortRun
    from triz import llm
    s=newrun(); ctx=RunContext(s)
    ticket=ActionTicket(action_type='REPAIR_CANDIDATE',model_role='REASONING',
        parameters={'candidate_id':'C1'},expected_outputs=['CandidateVersion'],allowed_tools=['candidate_repair'],reason='fixture')
    for model in s.scratch['ax_bundle']['models'].values():
        model.update(cost_in=0,cost_out=0)
    calls=[]
    monkeypatch.setattr(llm,'chat_json',lambda **kw:(calls.append(kw['tier']) or llm.LLMResult(data={'ok':True},cost_usd=.00001)))
    with executing(ctx,ticket,context='coherence:roles'):
        with pytest.raises(AbortRun,match='모델 역할'):
            gateway.chat(ctx,_node='repair',system='s',user='u',tier='T1')
        gateway.chat(ctx,_node='repair',system='s',user='u',tier='T2')
        gateway.chat(ctx,_node='independent_verifier',system='s',user='review',tier='T3')
    assert calls==['T2','T3']
    result=next(iter(s.scratch['ax_action_results'].values()))
    assert result['actual_microusd']==20 and result['attempts']==2
    with store.engine.connect() as c:
        rows=c.execute(select(ledger.attempts.c.details).where(ledger.attempts.c.run_id==s.run_id)).scalars()
        roles={json.loads(r)['request']['action_context']['call_model_role'] for r in rows}
    assert roles=={'REASONING','INDEPENDENT_REVIEW'}


def test_stale_action_output_never_enters_current_portfolio(newrun):
    from triz.ax.action_runtime import executing
    s=newrun(); ctx=RunContext(s)
    ticket=ActionTicket(**action('A_MATRIX'),expected_outputs=['RawIdea'],allowed_tools=['legacy_tracks'],reason='fixture')
    with pytest.raises(Conflict,match='stale'):
        with executing(ctx,ticket):
            s.solve.raw_ideas.append(RawIdea(id='stale',idea='must be quarantined'))
            s.scratch['execution_epoch']=1
            ledger.advance_epoch(s,'simulated changed owner')
    assert s.solve.raw_ideas==[]
