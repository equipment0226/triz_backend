from test_ax_phase1 import dlc,candidate
from triz.ax import coherence_recovery as recovery
from triz.ax import coherence
from triz import nodes
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea, TechnicalContradiction
import copy
import pytest


def test_incomplete_merge_does_not_silently_discard_source_ideas(dlc,monkeypatch):
    dlc.scratch['ax_bundle']['limits']['portfolio_completion_v1']=True
    dlc.solve.raw_ideas=[RawIdea(id=f'IDEA-{i}',title=f'기구 {i}',idea=f'독립 작동 기구 {i}',
        mechanism_key=str(i),addresses=['TC-DLC'],resolution_status='UNSUPPORTED') for i in range(7)]
    monkeypatch.setattr(nodes.agent,'run_agent',lambda *a,**k:{'ideas':[
        {'keep_ids':['IDEA-0'],'title':'기구 0','idea':'독립 작동 기구 0','resolution_status':'UNSUPPORTED'}]})
    original=copy.deepcopy(dlc.solve.raw_ideas)
    with pytest.raises(AbortRun,match='누락된 입력 ID'):
        nodes._merge(RunContext(dlc))
    assert dlc.solve.raw_ideas==original
    assert 'idea_consolidation' not in dlc.scratch
    assert not any(row.get('stage')=='merge' for row in dlc.scratch.get('ax_portfolio_trace',[]))


@pytest.mark.parametrize('legacy_completion', [False, True])
def test_fewer_candidates_never_create_quota_recovery_even_with_old_pinned_limits(dlc,monkeypatch,legacy_completion):
    from triz import agent
    candidate(dlc)
    limits=dlc.scratch['ax_bundle']['limits']
    limits.update(presentation_target=5,detailed_candidates=8)
    if legacy_completion:
        limits['portfolio_completion_v1']=True
    else:
        limits.pop('portfolio_completion_v1',None)
    assessment=coherence.assess(dlc)
    assert assessment['coverage_gaps']==[]
    assert assessment['shortfall']==0 and assessment['presentation_target']==0
    assert recovery.targets(dlc,'before_constraints')==[]
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:pytest.fail('A candidate count must not trigger paid recovery'))
    original=copy.deepcopy(dlc.concepts)
    assert recovery.run(RunContext(dlc),'before_constraints')==[]
    assert dlc.concepts==original
    assert dlc.scratch['ax_recovery']==[]


def test_real_quality_and_uncovered_problem_gaps_still_create_recovery_work(dlc):
    candidate(dlc)
    dlc.concepts[0].quality_status='REVISE'
    dlc.concepts[0].quality_issues=['실제 열전달 경로의 가정 보완']
    dlc.scratch['ax_bundle']['limits']['portfolio_completion_v1']=True
    dlc.definition.technical_contradictions.append(TechnicalContradiction(
        id='TC-MISSING',label='유량 증가와 펌프 전력 증가',then_good='열전달 개선',but_bad='전력 증가'))
    planned=recovery.targets(dlc,'before_constraints')
    assert planned[0]['candidate_id']=='scope-TC-MISSING'
    assert planned[0]['action']=='SOLVE_SUBPROBLEM'
    assert planned[0]['obligation_ids']==['TC-MISSING']
    repair=next(p for p in planned if p['candidate_id']=='DLC-1')
    assert repair['action']=='REPAIR_CANDIDATE'
    assert repair['gaps']==[{'kind':'QUALITY_REVIEW','description':'실제 열전달 경로의 가정 보완'}]
    assert all(p['candidate_id']!='portfolio' for p in planned)
    assert not any(g['kind']=='CANDIDATE_SHORTFALL' for p in planned for g in p['gaps'])


@pytest.mark.parametrize('protected_side,expected', [('PROTECT',2),('IMPROVE',1)])
def test_quality_repair_still_checks_both_sides_and_keeps_baseline(dlc,monkeypatch,protected_side,expected):
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
    assert all(row['candidate_id']=='DLC-1' and row['action']=='REPAIR_CANDIDATE'
               for row in dlc.scratch['ax_recovery'])
    assert all('CANDIDATE_SHORTFALL' not in row['gap_kinds'] for row in dlc.scratch['ax_recovery'])
    assert len(dlc.scratch['ax_recovery'])<=2
    assert recovery.run(RunContext(dlc),'before_constraints')==[]


def test_actual_uncovered_problem_can_add_a_candidate_without_a_count_target(dlc,monkeypatch):
    from test_ax_coherence_recovery import proposal
    from triz import agent,quality
    candidate(dlc)
    baseline=dlc.concepts[0].model_dump(mode='json')
    dlc.definition.technical_contradictions.append(TechnicalContradiction(
        id='TC-MISSING',label='유량 증가와 펌프 전력 증가',then_good='열전달 개선',but_bad='전력 증가'))
    dlc.scratch['ax_bundle']['limits']['recovery_targets']=1
    raw=proposal(dlc)
    raw['addresses_contradictions']=['TC-MISSING']
    raw['validation_plan'][0]['obligation_refs']=[
        {'contradiction_id':'TC-MISSING','side':side} for side in ('IMPROVE','PROTECT')]
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:raw)
    monkeypatch.setattr(quality,'audit_concepts',lambda ctx:setattr(ctx.state.concepts[0],'quality_status','PASS'))
    added=recovery.run(RunContext(dlc),'before_constraints')
    assert len(added)==1 and len(dlc.concepts)==2
    assert dlc.concepts[0].model_dump(mode='json')==baseline
    row=dlc.scratch['ax_recovery'][0]
    assert row['candidate_id']=='scope-TC-MISSING' and row['action']=='SOLVE_SUBPROBLEM'
    assert row['gap_kinds']==['COVERAGE_GAP']
    assert row['status']=='PROPOSED_REQUIRES_GATE'
    assert coherence.assess(dlc)['coverage_gaps']==[]
