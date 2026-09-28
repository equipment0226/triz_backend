import copy
import math
import pytest
from test_targeted_f1_f5 import isolated_learning_database,adaptive_run,newrun,utility_model
from triz.schema import Constraint,ResourceItem,FunctionEdge
from triz.ax import routing_q as q,adaptive_tracks,effect_ranker as e
from triz.ax.confirmed_context import build,normalized


@pytest.mark.parametrize('change',['function','protected','resource','hard','environment','domain'])
def test_F3_02_semantic_fields_reach_action_interactions(adaptive_run,change):
    state=adaptive_run('LITE');state.constraints.items=[Constraint(id='x',statement='전원')]
    before=adaptive_tracks.state_features(state,'initial')
    if change=='function': state.analysis.function_edges=[FunctionEdge(action='냉각',object='광학계')]
    if change=='protected': state.definition.technical_contradictions[0].but_bad='진동 증가'
    if change=='resource': state.analysis.resources=[ResourceItem(name='폐열',blocked_by_constraint=True)]
    if change=='hard': state.constraints.items[0].hard=False
    if change=='environment': state.domain.operating_env='초고진공'
    if change=='domain': state.domain.problem_type='INFORMATION_SOFTWARE'
    after=adaptive_tracks.state_features(state,'initial')
    ticket={'action_type':'RUN_TRACK','parameters':{'tracks':['H_EFFECTS']}}
    assert q.phi(before,ticket)!=q.phi(after,ticket)


def test_F3_03_04_canonical_context_and_provenance(adaptive_run):
    state=adaptive_run('LITE')
    state.constraints.items=[Constraint(id='a',kind='NUMERIC',parameter='length',value='1000',unit='mm'),Constraint(id='b',statement='  no   power ')]
    a=build(state)
    state.constraints.items.reverse();state.constraints.items[0].id='c';state.constraints.items[0].statement='no power'
    state.constraints.items[1].value='1';state.constraints.items[1].unit='m'
    state.scratch['ax_snapshot_id']='other-snapshot'
    b=build(state)
    assert a['tokens']==b['tokens'] and a['provenance']!=b['provenance']
    assert normalized({'value':'roughly 1000','unit':'mm'})['unit']=='mm'
    assert normalized({'value':'1','unit':'unknown unit'})['value']=='1'


def test_F3_05_07_real_training_context_preferences_and_legacy(adaptive_run):
    state=adaptive_run('LITE')
    a=adaptive_tracks.state_features(state,'adaptive:initial')
    state.constraints.items=[Constraint(statement='전원 및 유체 사용 금지',kind='MUST_NOT_HAVE')]
    b=adaptive_tracks.state_features(state,'adaptive:initial')
    actions=[dict(action_type='RUN_TRACK',model_role='REASONING',parameters={'tracks':[t]}) for t in ('A_MATRIX','H_EFFECTS')]
    rows=[dict(features=fs,actions=actions,executed_index=i,permitted=[0,1],terminal=True,reward=1. if i==preferred else -1.,group=str(g),split='train',**q.contracts(fs['schema'])) for fs,preferred in ((a,0),(b,1)) for g in range(4) for i in (0,1)]
    model=q.train(rows,epochs=400,alpha=0)
    assert q.choose(model,a,actions,[0,1],1)[0]==0
    assert q.choose(model,b,actions,[0,1],0)[0]==1
    legacy=dict(model,feature_schema=q.ADAPTIVE_SCHEMA,**q.contracts(q.ADAPTIVE_SCHEMA))
    assert q.choose(legacy,b,actions,[0,1],0)[0]==0
    state.scratch['ax_bundle']['feature_schema']=q.ADAPTIVE_SCHEMA
    old=adaptive_tracks.state_features(state,'initial')
    assert 'confirmed_context' not in old


def utility_rows(labels=(.03,-.03),weights=(1.,1.)):
    model,context,effect=utility_model()
    model.update(evaluation_contract=e.EVALUATION_CONTRACT,target_contract='candidate-utility-cost-v2')
    rows=[dict(context=context,application=effect,effect_id='E1',features=e.features(context,effect),feature_schema=e.UTILITY_SCHEMA,label=y,sample_weight=w,group=str(i),split='train') for i,(y,w) in enumerate(zip(labels,weights))]
    return model,rows


def test_F5_02_03_weighted_train_and_evaluation():
    model,rows=utility_rows((.3,-.1),(1.,3.))
    trained=e.train(rows,epochs=1)
    assert trained['train_weighted_mean']==pytest.approx(0.)
    assert trained['training']['loss_first']==pytest.approx((.09+.03)/4)
    before=copy.deepcopy(trained)
    result=e.evaluate(trained,[dict(r,label=.9) for r in rows])
    assert result['train_weighted_mean']==pytest.approx(0.) and trained==before
    assert result['weighted_mass']==4.


def test_F5_04_supported_zero_and_unsupported_zero():
    model,rows=utility_rows()
    model['weights']=[0.]*e.DIMENSIONS
    rows[1]['context']={'domain':'OTHER'}
    result=e.evaluate(model,[dict(r,group='holdout-'+r['group'],split='holdout') for r in rows])
    assert result['supported_sample_count']==1 and result['supported_weight_fraction']==.5
    assert result['predictions'][0]=={'prediction':0.,'supported':True,'fallback_reason':None}
    assert result['predictions'][1]['fallback_reason']=='unsupported_context'


@pytest.mark.parametrize('field,value',[('sample_weight',-1),('sample_weight',float('nan')),('sample_weight',float('inf')),('label',float('nan')),('label',float('inf'))])
def test_F5_05_invalid_numeric_observations_rejected(field,value):
    model,rows=utility_rows();rows[0][field]=value
    with pytest.raises(ValueError): e.evaluate(model,rows)
    with pytest.raises(ValueError): e.train(rows,epochs=1)


def test_F5_05_06_09_empty_missing_zero_and_tie():
    model,rows=utility_rows((0.,0.))
    model['weights']=[0.]*e.DIMENSIONS
    for values in ([],[dict(r,sample_weight=0.) for r in rows],[dict(r,label=None) for r in rows],rows):
        result=e.evaluate(model,values)
        assert not e.eligibility(model,result,{'ready':True})['eligible']
    assert e.evaluate(model,rows)['observed_sample_count']==2


def test_F5_07_08_actual_regression_can_pass_and_old_artifact_cannot():
    from triz.ax.registry import eligible_payload
    rows=[]
    for i in range(8):
        for effect_id,label in [('E1',.3),('E2',-.3)]:
            context={'domain':'PHYSICAL'};app={'id':effect_id}
            rows.append(dict(feature_schema=e.UTILITY_SCHEMA,context=context,application=app,effect_id=effect_id,features=e.features(context,app),label=label,sample_weight=.5,group=str(i),split='train'))
    model=e.train(rows,epochs=300)
    result=e.evaluate(model,[dict(r,group='held-out-'+r['group'],split='holdout') for r in rows])
    gate=e.eligibility(model,result,{'ready':True})
    assert gate['eligible']
    payload=dict(model=model,evaluation=result,eligibility=gate,readiness={'ready':True},offline_eligible=True)
    assert eligible_payload(payload)
    old=copy.deepcopy(payload);old['evaluation']={'mse':.001};old['model'].pop('evaluation_contract')
    assert not eligible_payload(old)
