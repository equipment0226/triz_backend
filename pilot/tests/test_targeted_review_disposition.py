import copy
import pytest
from test_targeted_f1_f5 import isolated_learning_database,adaptive_run,newrun,review_provider,candidate
from test_unified_feedback_adaptive import events
from triz import quality,nodes,store
from triz.context import RunContext,AbortRun
from triz.schema import Constraint,ConceptSpec
from triz.ax import incremental_review,learning_outcomes,adaptive_tracks,coherence_recovery
from triz.ax.candidate_disposition import record,records,blocked,all_user_dropped


def test_F1_02_06_08_revision_outcome_and_frozen_report(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');candidate(state);ctx=RunContext(state)
    review_provider(monkeypatch,state,'REVISE');quality.generate_concepts(ctx)
    cid=state.concepts[0].id
    old_events=copy.deepcopy(events(state))
    from triz.ax import runtime,report
    runtime.checkpoint(state,'s6_concept')
    state.scratch['ax_report_snapshot_id']=state.scratch['ax_snapshot_id']
    old_report=report.markdown(state)
    cutoff=max(e['label_available_at'] for e in old_events)
    state.constraints.items=[Constraint(id='limit',statement='추가 전원 금지')]
    review_provider(monkeypatch,state,'PASS');quality.generate_concepts(ctx)
    assert state.concepts[0].id==cid and state.concepts[0].quality_status=='PASS'
    assert not state.concepts[0].quality_issues
    cfg=state.scratch['ax_bundle']['run_contract']['feedback_settings']
    assert learning_outcomes.outcome(old_events,cfg)['concept_quality']==0.
    assert learning_outcomes.outcome(events(state),cfg)['concept_quality']==1.
    assert report.markdown(state)==old_report
    from triz.ax.feedback_events import current
    assert learning_outcomes.outcome(current('local','local',cutoff,include_synthetic=True),cfg)['concept_quality']==0.
    runtime.checkpoint(state,'s6_concept')
    state.scratch['ax_report_snapshot_id']=state.scratch['ax_snapshot_id']
    assert report.project(state).concepts[0].quality_status=='PASS'
    assert len(events(state))>len(old_events)
    assert state.scratch['candidate_review_revisions'][cid]['revision']==2


@pytest.mark.parametrize('verdict',['REJECT','MISSING','EMPTY'])
def test_F1_03_04_07_no_stale_pass_on_bad_review(adaptive_run,monkeypatch,verdict):
    state=adaptive_run('LITE');candidate(state);ctx=RunContext(state)
    review_provider(monkeypatch,state,'PASS');quality.generate_concepts(ctx)
    cid=state.concepts[0].id
    state.constraints.items=[Constraint(id='limit',statement='변경된 제약')]
    review_provider(monkeypatch,state,verdict)
    if verdict=='EMPTY':
        with pytest.raises(AbortRun): quality.generate_concepts(ctx)
    else: quality.generate_concepts(ctx)
    assert all(c.quality_status!='PASS' for c in state.concepts)
    if verdict=='REJECT':
        assert not state.concepts
        row=state.scratch['candidate_dispositions'][-1]
        assert row['reason_kind']=='QUALITY_REJECT' and row['candidate_id']==cid
        assert row['original_leaf_ids']
        assert coherence_recovery.targets(state,'after_quality')
    if verdict=='MISSING':
        assert state.concepts[0].quality_status=='UNVERIFIED'
        assert state.scratch['ax_candidate_review']['completed_ideas']==0
    if verdict=='EMPTY':
        persisted=store.load_state(state.run_id)
        assert persisted.concepts and persisted.concepts[0].quality_status=='UNVERIFIED'


def test_F1_07_explicit_disposition_completeness():
    assert not incremental_review.complete_entry([],[],[])
    assert not incremental_review.complete_entry([{'id':'C1'}],[],[])
    assert incremental_review.complete_entry([], [{'reason':'not applicable'}], [])
    assert incremental_review.complete_entry([{'id':'C1'}],[],['C1'])


def test_F2_03_04_05_06_design_exclusion_and_legacy(adaptive_run):
    state=adaptive_run('LITE');c=candidate(state)
    record(state,c,'USER_DROP','explicit','event1')
    record(state,c,'USER_DROP','explicit','event1')
    assert len(records(state))==1
    renamed=c.model_copy(deep=True);renamed.id='new-id';renamed.title='new title';renamed.source_idea_ids=['different-raw']
    assert blocked(state,renamed)
    state.concepts=[]
    assert all_user_dropped(state)
    assert adaptive_tracks.followup(RunContext(state),'after_constraints')==[]
    assert state.scratch['adaptive_search']['stop_reason']=='ALL_EXPLICIT_USER_DROP'
    changed=renamed.model_copy(update={'working_principle':'완전히 다른 수동 열전달 설계'})
    assert not blocked(state,changed)
    record(state,changed,'CONSTRAINT_FAIL','actual failure','step2')
    assert not all_user_dropped(state)
    assert blocked(state,changed)
    state.scratch['adaptive_dropped_candidates']=['unknown-old-id']
    assert records(state)[-1]['reason_kind']=='LEGACY_UNKNOWN_ORIGIN'


def test_F2_01_02_07_automatic_failure_reaches_real_budget_evaluation(adaptive_run,monkeypatch):
    from sqlalchemy import update
    from triz.ax import ledger
    state=adaptive_run('LITE');c=candidate(state)
    record(state,c,'QUALITY_REJECT','independent rejection','step1');state.concepts=[]
    # All generation is unaffordable; real proposals/governor must still be evaluated.
    with ledger.transaction() as connection:
        connection.execute(update(ledger.heads).where(ledger.heads.c.run_id==state.run_id).values(budget=0))
    adaptive_tracks.followup(RunContext(state),'after_quality')
    assert state.scratch['adaptive_search']['followup_rounds']==1
    assert state.scratch['adaptive_search']['status']=='PARTIAL_BUDGET'
    assert coherence_recovery.targets(state,'after_quality')


def test_F1_06_keep_survives_as_utility_but_never_overrides_reject(adaptive_run,monkeypatch):
    from triz.schema import ConstraintCheckResult
    state=adaptive_run('LITE');candidate(state);ctx=RunContext(state)
    review_provider(monkeypatch,state,'PASS');quality.generate_concepts(ctx)
    cid=state.concepts[0].id
    state.constraint_checks=[ConstraintCheckResult(concept_id=cid,verdict='CONDITIONAL')]
    state.scratch['resume_payload']={'decisions':{cid:'accept'}};nodes.s7_gate(ctx)
    state.constraints.items=[Constraint(statement='새 제약')]
    review_provider(monkeypatch,state,'REJECT');quality.generate_concepts(ctx)
    value=learning_outcomes.outcome(events(state),state.scratch['ax_bundle']['run_contract']['feedback_settings'])
    assert not state.concepts and value['concept_quality']==-1. and value['user_utility']==.1
    assert value['total']==pytest.approx(-.67)


def test_F2_01_04_05_real_alternative_after_automatic_failure(adaptive_run,monkeypatch):
    state=adaptive_run('LITE');old=candidate(state);ctx=RunContext(state)
    state.constraints.items=[Constraint(id='limit',statement='전원 증가 제한')]
    review_provider(monkeypatch,state,gate='FAIL');nodes.s7_gate(ctx)
    assert not state.concepts
    state.solve.tracks_run=['A_MATRIX','B_SEPARATION','E_TRIMMING']
    state.scratch['ax_bundle']['effects'][0]['function_ko']='열 제거'
    review_provider(monkeypatch,state,'PASS',gate='PASS')
    adaptive_tracks.followup(ctx,'after_constraints')
    assert 'H_EFFECTS' in state.solve.tracks_run
    assert state.concepts and all(c.id!=old.id for c in state.concepts)
    nodes.s7_gate(ctx)
    assert all(c.quality_status=='PASS' for c in state.concepts),[(c.quality_status,c.quality_issues) for c in state.concepts]
    assert all(r.verdict=='PASS' for r in state.constraint_checks)


def test_F2_03_04_cohort_separates_historical_failures(adaptive_run):
    state=adaptive_run('LITE');a=candidate(state,'A');b=candidate(state,'B')
    record(state,a,'CONSTRAINT_FAIL','observed fail')
    record(state,b,'USER_DROP','explicit drop')
    state.concepts=[];state.scratch['adaptive_gate_cohort']=['A','B']
    assert not all_user_dropped(state)
    # Subsequent completed gate reviewed only the new portfolio B.
    state.scratch['adaptive_gate_cohort']=['B']
    assert all_user_dropped(state)


def test_F2_07_no_candidate_stop_has_technical_reason(adaptive_run,monkeypatch):
    state=adaptive_run('LITE')
    state.solve.tracks_run=['A_MATRIX','B_SEPARATION','E_TRIMMING','H_EFFECTS']
    state.scratch['ax_track_execution']={t:dict(status='REVIEWED_NO_APPLICATION',output_count=0) for t in state.solve.tracks_run}
    # Stored synthetic no-application history; no generated candidate is invented.
    review_provider(monkeypatch,state)
    adaptive_tracks.followup(RunContext(state),'after_quality')
    assert not state.concepts
    assert state.scratch['adaptive_search']['stop_reason']=='NO_CURRENT_TECHNICAL_CANDIDATES'
