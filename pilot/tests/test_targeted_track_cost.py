import copy
import json
import pytest
from sqlalchemy import select,update
from test_targeted_f1_f5 import isolated_learning_database,adaptive_run,newrun
from triz import llm,store
from triz.context import RunContext
from triz.ax import ledger,track_cost,adaptive_tracks,coordinator
from triz.ax.action_runtime import executing,emit
from triz.ax.contracts import ActionTicket,now
from triz.ax.gateway import chat


def execution(state,monkeypatch,track,costs):
    # Local ledger fixture: consent eligibility is tested separately below.
    state.scratch['synthetic']=False
    costs=iter(costs)
    def provider(**kwargs):
        cost=next(costs)
        return llm.LLMResult(data={'fixture':True},text='{}',tokens_in=10,tokens_out=10,cost_usd=cost,
            meta={'requests':[{'usage':{'input_tokens':10,'output_tokens':10}}]})
    monkeypatch.setattr(llm,'chat_json',provider)
    ctx=RunContext(state)
    ticket=ActionTicket(action_type='GENERATE_BASELINE',parameters={'tracks':[track]},model_role='REASONING',
        expected_outputs=['TrackResult'],allowed_tools=['legacy_tracks'],reason='isolated cost fixture')
    parent=ActionTicket(action_type='RUN_TRACK',parameters={'tracks':[track],'plan_class':'INITIAL_SELECTION'},model_role='REASONING',
        expected_outputs=['TrackResult'],allowed_tools=['legacy_tracks'],reason='isolated parent fixture')
    with executing(ctx,parent,context='adaptive:initial',optional=False):
        with executing(ctx,ticket,context='track:'+track,optional=False):
            for i,cost in enumerate(list(costs)):
                # Refill a one-response iterator for each distinct physical request.
                costs=iter([cost])
                chat(ctx,_node='s5_track_'+track[0].lower(),system='fixture',user='call '+str(i),tier='T2')
    ctx.persist()
    return state.scratch['ax_action_results']


def test_F4_01_02_03_06_08_logical_totals_deduplicate_parent_child(adaptive_run,monkeypatch):
    state=adaptive_run('LITE')
    execution(state,monkeypatch,'A_MATRIX',[.1]*5)
    execution(state,monkeypatch,'H_EFFECTS',[.2])
    # Re-deliver recorded result, without creating another physical execution.
    for result in list(state.scratch['ax_action_results'].values()): emit(state,'ACTION_INSTANCE_RESULT',result)
    a=adaptive_tracks.estimate(state,'A_MATRIX');h=adaptive_tracks.estimate(state,'H_EFFECTS')
    assert a['estimate_microusd']==500000 and h['estimate_microusd']==200000
    assert a['support']==h['support']==1
    assert len(a['samples'][0]['task_ids'])==5
    assert sum(r['actual_producer_cost'] for r in a['samples']+h['samples'])==ledger.budget(state.run_id)['spent_microusd']==700000
    tickets=adaptive_tracks.proposals(state)
    costs={t.parameters['tracks'][0]:t.parameters['cost_estimate']['estimate_microusd'] for t in tickets if t.action_type=='RUN_TRACK'}
    assert costs['H_EFFECTS']<costs['A_MATRIX']


@pytest.mark.parametrize('excluded',['unknown','future','synthetic','no_consent','different_model','different_owner','different_size'])
def test_F4_04_05_09_unusable_history_excluded(adaptive_run,monkeypatch,excluded):
    state=adaptive_run('LITE');execution(state,monkeypatch,'H_EFFECTS',[.2]);ctx=RunContext(state)
    target=state
    if excluded in ('unknown','future'):
        with ledger.transaction() as c:
            values={'actual':None,'status':'UNKNOWN'} if excluded=='unknown' else {'settled_at':'2999-01-01T00:00:00+00:00'}
            c.execute(update(ledger.tasks).where(ledger.tasks.c.run_id==state.run_id).values(**values))
    elif excluded=='synthetic': state.scratch['synthetic']=True;ctx.persist()
    elif excluded=='no_consent': state.scratch['training_consent']='NO_TRAINING';ctx.persist()
    elif excluded=='different_model': state.scratch['ax_bundle']['models']['T2']['cost_in']+=1
    elif excluded=='different_size': state.raw_query='much larger query '*1000
    elif excluded=='different_owner': target=adaptive_run('LITE',user='other')
    result=adaptive_tracks.estimate(target,'H_EFFECTS')
    assert result['support']==0 and not result['sample_ids']


def test_F4_07_prior_uses_node_caps_and_price_units(adaptive_run):
    state=adaptive_run('LITE')
    row=adaptive_tracks.estimate(state,'A_MATRIX')
    assert row['prior_microusd']>0 and len(row['planned_calls'])==3
    assert row['planned_calls'][0]['max_tokens']>=4000
    assert row['basis']=='pinned-node-price-cap-prior'


def test_F4_10_pending_stop_skips_history_reselection(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');state.solve.tracks_run=['H_EFFECTS'];adaptive_tracks.prepare(state)
    stop=ActionTicket(action_type='STOP_EXPLORATION',parameters={'phase':'initial'},expected_outputs=['SearchPhaseResult'],allowed_tools=[],reason='recorded stop')
    chosen,did=coordinator.decide(state,[stop],0,{'STOP_EXPLORATION'},'adaptive:initial')
    state.scratch['adaptive_search']={'evidence_planned':True,'pending':{'ticket':chosen.model_dump(mode='json'),'decision_id':did}}
    # Database boundary: any new history query would require a new connection.
    before=len(ledger.decision_history(state.run_id,state.user_id))
    adaptive_tracks.run(RunContext(state),max_steps=1)
    assert len(ledger.decision_history(state.run_id,state.user_id))==before
    assert state.scratch['adaptive_search']['status']=='READY_FOR_REVIEW'


def test_F4_02_03_repeated_attempt_log_does_not_duplicate_task(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');execution(state,monkeypatch,'A_MATRIX',[.1,.1])
    with ledger.transaction() as c:
        attempt=dict(c.execute(select(ledger.attempts).where(ledger.attempts.c.run_id==state.run_id)).mappings().first())
        attempt.update(attempt_id=attempt['attempt_id']+'-replayed',fence=99)
        c.execute(ledger.attempts.insert().values(**attempt))
    value=adaptive_tracks.estimate(state,'A_MATRIX')
    assert value['support']==1 and value['estimate_microusd']==200000
    assert len(value['samples'][0]['task_ids'])==2


def test_F4_04_missing_task_attribution_fails_closed(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');execution(state,monkeypatch,'A_MATRIX',[.1,.1])
    with ledger.transaction() as c:
        row=c.execute(select(ledger.attempts).where(ledger.attempts.c.run_id==state.run_id)).mappings().first()
        details=json.loads(row['details']);details['request'].pop('action_context')
        c.execute(update(ledger.attempts).where(ledger.attempts.c.attempt_id==row['attempt_id']).values(details=json.dumps(details)))
    result=adaptive_tracks.estimate(state,'A_MATRIX')
    assert result['support']==0 and result['excluded']['unknown_task_lineage']>=1


def test_F4_06_cache_only_execution_does_not_lower_generation_average(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');execution(state,monkeypatch,'H_EFFECTS',[.2])
    ticket=ActionTicket(action_type='GENERATE_BASELINE',parameters={'tracks':['H_EFFECTS']},model_role='REASONING',
        allowed_tools=['legacy_tracks'],expected_outputs=['TrackResult'],reason='isolated cached branch')
    with executing(RunContext(state),ticket,context='track:cached-only',optional=False): pass
    result=adaptive_tracks.estimate(state,'H_EFFECTS')
    assert result['support']==1 and result['estimate_microusd']==200000
    assert result['excluded']['cache_only_or_no_paid_usage']==1


def test_F4_real_adaptive_producer_shape_is_observed(adaptive_run,monkeypatch):
    from test_targeted_f1_f5 import review_provider
    from triz import nodes
    state=adaptive_run('LITE');state.scratch['synthetic']=False
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    review_provider(monkeypatch,state,'PASS');ctx=RunContext(state)
    coordinator.route(ctx)
    tickets=adaptive_tracks.proposals(state)
    i=next(i for i,t in enumerate(tickets) if t.parameters.get('tracks')==['H_EFFECTS'])
    chosen,did=coordinator.decide(state,tickets,i,{'RUN_TRACK'},'adaptive:initial')
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False): nodes._run_tracks(ctx,['H_EFFECTS'])
    ctx.persist()
    value=adaptive_tracks.estimate(state,'H_EFFECTS')
    assert value['support']==1 and value['estimate_microusd']==ledger.budget(state.run_id)['spent_microusd']


def test_F4_10_new_cost_metadata_reuses_legacy_paid_identity(adaptive_run):
    state=adaptive_run('LITE')
    request=dict(node='s5_track_h',request={'system':'same','user':'same'},
        action_context=dict(semantic_episode_id=state.scratch['semantic_episode_id'],action_instance_id='saved-action',ticket={}))
    task=ledger.acquire(state.run_id,0,request,1)
    ledger.settle(task,{'observed':'old response'},1)
    current=copy.deepcopy(request);current['action_context']['cost_comparison']={'contract':track_cost.CONTRACT}
    reused=ledger.acquire(state.run_id,0,current,1)
    assert reused['cached'] and reused['task_id']==task['task_id']
    assert ledger.budget(state.run_id)['spent_microusd']==1


def test_F4_10_resume_completed_producer_preserves_ticket_and_lineage(adaptive_run,monkeypatch):
    from test_targeted_f1_f5 import review_provider
    from triz import nodes
    state=adaptive_run('LITE');ctx=RunContext(state)
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    calls=review_provider(monkeypatch,state,'PASS');coordinator.route(ctx)
    tickets=adaptive_tracks.proposals(state)
    i=next(i for i,t in enumerate(tickets) if t.parameters.get('tracks')==['H_EFFECTS'])
    chosen,did=coordinator.decide(state,tickets,i,{'RUN_TRACK'},'adaptive:initial')
    state.scratch['adaptive_search']={'evidence_planned':True,'pending':dict(ticket=chosen.model_dump(mode='json'),decision_id=did)}
    with executing(ctx,chosen,did,context='adaptive:initial',optional=False) as action:
        nodes._run_tracks(ctx,['H_EFFECTS'])
    original=copy.deepcopy(state.scratch['ax_action_results'][action['action_instance_id']]);ctx.persist()
    adaptive_tracks.run(ctx,max_steps=1)
    current=state.scratch['ax_action_results'][action['action_instance_id']]
    assert current['produced_raw_idea_ids']==original['produced_raw_idea_ids']
    assert current['ticket']==original['ticket'] and current['decision_id']==did
    assert calls.count('P_S5_TRACK_H')==1
    assert len(ledger.decision_history(state.run_id,state.user_id))==1


def test_F4_10_interrupted_merge_retains_selected_ticket(adaptive_run,monkeypatch):
    from test_targeted_f1_f5 import review_provider
    from triz import nodes
    state=adaptive_run('LITE');ctx=RunContext(state)
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    review_provider(monkeypatch,state,'PASS');provider=llm.chat_json
    def interrupted(**kwargs):
        step=next((s for s in reversed(state.steps) if s.input_slice.get('user')==kwargs['user']),None)
        if step and step.input_slice.get('prompt_id')=='P_S5_MERGE': raise RuntimeError('isolated provider interruption')
        return provider(**kwargs)
    monkeypatch.setattr(llm,'chat_json',interrupted);coordinator.route(ctx)
    tickets=adaptive_tracks.proposals(state);i=next(i for i,t in enumerate(tickets) if t.parameters.get('tracks')==['H_EFFECTS'])
    chosen,did=coordinator.decide(state,tickets,i,{'RUN_TRACK'},'adaptive:initial')
    state.scratch['adaptive_search']={'evidence_planned':True,'pending':dict(ticket=chosen.model_dump(mode='json'),decision_id=did)}
    with pytest.raises(RuntimeError,match='isolated provider'): adaptive_tracks.run(ctx,max_steps=1)
    assert state.scratch['adaptive_search']['pending']['decision_id']==did
    assert store.load_state(state.run_id).scratch['adaptive_search']['pending']['decision_id']==did
    from triz.context import UsageUncertain
    before=ledger.budget(state.run_id)
    monkeypatch.setattr(llm,'chat_json',provider)
    with pytest.raises(UsageUncertain): adaptive_tracks.run(ctx,max_steps=1)
    after=ledger.budget(state.run_id)
    assert before['spent_microusd']==after['spent_microusd']
    assert before['reserved_microusd']==after['reserved_microusd']
