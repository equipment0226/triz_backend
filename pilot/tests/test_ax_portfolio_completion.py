from test_ax_phase1 import dlc,candidate
from triz.ax import coherence_recovery as recovery
from triz import nodes
from triz.context import RunContext
from triz.schema import RawIdea
import pytest


def test_incomplete_merge_does_not_silently_discard_source_ideas(dlc,monkeypatch):
    dlc.scratch['ax_bundle']['limits']['portfolio_completion_v1']=True
    dlc.solve.raw_ideas=[RawIdea(id=f'IDEA-{i}',title=f'기구 {i}',idea=f'독립 작동 기구 {i}',
        mechanism_key=str(i),addresses=['TC-DLC'],resolution_status='UNSUPPORTED') for i in range(7)]
    monkeypatch.setattr(nodes.agent,'run_agent',lambda *a,**k:{'ideas':[
        {'keep_ids':['IDEA-0'],'title':'기구 0','idea':'독립 작동 기구 0','resolution_status':'UNSUPPORTED'}]})
    nodes._merge(RunContext(dlc))
    assert len(dlc.solve.raw_ideas)==7
    assert all(i.resolution_status=='UNSUPPORTED' for i in dlc.solve.raw_ideas)
    assert dlc.scratch['ax_portfolio_trace'][-1]['unaccounted_preserved']==6


def test_shortfall_exploration_is_not_starved_by_repairs(dlc):
    candidate(dlc)
    dlc.concepts[0].quality_status='REVISE'
    dlc.scratch['ax_bundle']['limits']['portfolio_completion_v1']=True
    planned=recovery.targets(dlc,'before_constraints')
    assert planned[0]['candidate_id']=='portfolio'
    assert any(p['action']=='REPAIR_CANDIDATE' for p in planned)
    dlc.scratch['ax_bundle']['limits'].pop('portfolio_completion_v1')
    assert all(p['candidate_id']!='portfolio' for p in recovery.targets(dlc,'before_constraints'))


@pytest.mark.parametrize('protected_side,expected', [('PROTECT',2),('IMPROVE',1)])
def test_shortfall_alternative_still_checks_both_sides_and_keeps_baseline(dlc,monkeypatch,protected_side,expected):
    from test_ax_coherence_recovery import proposal
    from triz import agent,quality
    candidate(dlc)
    dlc.concepts[0].quality_status='REVISE'
    baseline=dlc.concepts[0].model_dump(mode='json')
    dlc.scratch['ax_bundle']['limits']['portfolio_completion_v1']=True
    dlc.scratch['ax_bundle']['limits']['recovery_targets']=1
    raw=proposal(dlc,protected_side)
    monkeypatch.setattr(agent,'run_agent',lambda *a,**k:raw)
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:setattr(ctx.state.concepts[0],'quality_status','PASS'))
    recovery.run(RunContext(dlc),'before_constraints')
    assert len(dlc.concepts)==expected
    assert dlc.concepts[0].model_dump(mode='json')==baseline
    assert all(row['candidate_id']=='portfolio' for row in dlc.scratch['ax_recovery'])
    assert len(dlc.scratch['ax_recovery'])<=2
    assert recovery.run(RunContext(dlc),'before_constraints')==[]
