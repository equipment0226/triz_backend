import pytest
from sqlalchemy import select,update
from test_targeted_f1_f5 import isolated_learning_database,adaptive_run,newrun,candidate,utility_model
from test_unified_feedback_adaptive import events
from triz import nodes
from triz.context import RunContext
from triz.ax import registry,ledger,effect_ranker as e
from triz.ax.contracts import Conflict


def test_F5_08_all_public_promotion_and_loading_paths_reject_old_utility(adaptive_run):
    state=adaptive_run('LITE');state.scratch['synthetic']=False;c=candidate(state)
    state.scratch['resume_payload']={'decisions':{c.id:'accept'}}
    nodes.s7_gate(RunContext(state))
    model,_,_=utility_model();model['target_contract']='candidate-utility-cost-v2'
    payload=dict(model=model,offline_eligible=True,evaluation={'mse':.0001},readiness={'ready':True},review_ids=[r['event_id'] for r in events(state)])
    with ledger.store.engine.connect() as connection:
        assert registry.reviews_current(payload,'local','local',connection)
    vid=registry.put('effect_ranker','local','local',payload)
    with pytest.raises(Conflict): registry.set_task_shadow('local','local','effect_ranker',e.UTILITY_SCHEMA,vid)
    with pytest.raises(Conflict): registry.promote_task('local','local','effect_ranker',e.UTILITY_SCHEMA,vid,'tester','isolated fixture')
    with pytest.raises(Conflict): registry.promote_policy('local','local',vid,'tester','isolated fixture')
    with ledger.transaction() as connection:
        pointer=registry._task_pointer(connection,'local','local','effect_ranker',e.UTILITY_SCHEMA)
        connection.execute(update(registry.task_pointers).where(registry.task_pointers.c.scope==pointer['scope']).values(policy_id=vid,shadow_policy_id=vid,canary_percent=100))
    loaded=registry.for_run(state,feature_schema='ax-state-action-v5')
    assert not loaded.get('effect_ranker') and not loaded.get('shadow_effect_ranker')
    # Previously pinned model remains readable; no mutation of frozen bundles.
    state.scratch['ax_bundle'].update(effect_ranker=model,effect_ranker_version=vid)
    assert registry.pinned_permissions_current(state)
