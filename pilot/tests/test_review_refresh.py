import pytest

from scripts import rerun_completed_reviews as refresh_job
from triz import pipeline, store
from triz.schema import ConceptSpec, FeedbackArtifact, ReportArtifact


def completed(state):
    state.status = "COMPLETED"
    state.report = ReportArtifact(narrative={"executive_summary": "Saved original"}, markdown="Original")
    state.feedback = FeedbackArtifact(overall_rating=4)
    state.concepts = [ConceptSpec(id="C1", title="Keep this solution")]
    state.cost.total_usd = 2.9
    state.scratch["active_seconds"] = 2000
    store.save_state(state)


def test_refresh_runs_only_evaluation_and_report_preserving_feedback_and_inputs(state, monkeypatch):
    completed(state)
    calls = []
    def execute(run_id, index, epoch):
        calls.append(pipeline.PIPELINE[index][0])
        current = store.load_state(run_id)
        if calls[-1] == "s8_evaluate":
            current.evaluation.meeting.status = "COMPLETED"
        else:
            current.report = ReportArtifact(markdown="Refreshed")
        current.control.stage_index += 1
        store.save_state(current)
    monkeypatch.setattr(pipeline, "execute_stage", execute)
    assert refresh_job.refresh(state.run_id, "test-refresh")["status"] == "COMPLETED"
    saved = store.load_state(state.run_id)
    assert calls == ["s8_evaluate", "s9_report"]
    assert saved.concepts == state.concepts and saved.feedback == state.feedback
    assert saved.cost.total_usd == 2.9 and saved.cost.budget_usd == pytest.approx(5.9)
    assert saved.scratch["active_seconds"] == 0
    assert saved.control.stage_index == len(pipeline.PIPELINE)
    assert refresh_job.refresh(state.run_id, "test-refresh")["status"] == "ALREADY_COMPLETED"
    assert len(calls) == 2


def test_refresh_retry_keeps_progress_and_does_not_add_budget_again(state):
    completed(state)
    refresh_job.prepare(state.run_id, "test-refresh")
    current = store.load_state(state.run_id)
    current.status = "INTERRUPTED"
    current.evaluation.meeting.completed_calls["initial:A"] = {"scores": []}
    budget = current.cost.budget_usd
    current.cost.budget_usd = 3.0  # A pre-fix UI retry used the original whole-run cap.
    current.cost.total_usd += 0.2
    store.save_state(current)
    refresh_job.prepare(state.run_id, "test-refresh")
    current = store.load_state(state.run_id)
    assert current.cost.budget_usd == budget
    assert "initial:A" in current.evaluation.meeting.completed_calls


def test_refresh_never_takes_over_an_active_or_unfinished_case(state):
    state.status = "RUNNING"
    store.save_state(state)
    with pytest.raises(ValueError, match="busy"):
        refresh_job.prepare(state.run_id, "test-refresh")
    state.status = "FAILED"
    store.save_state(state)
    with pytest.raises(ValueError, match="Only completed"):
        refresh_job.prepare(state.run_id, "test-refresh")


def test_normal_ui_retry_keeps_refresh_allowance_and_stops_after_report(state, monkeypatch):
    completed(state)
    refresh_job.prepare(state.run_id, "test-refresh")
    current = store.load_state(state.run_id)
    current.status = "INTERRUPTED"
    current.scratch["review_refresh"]["status"] = "INTERRUPTED"
    current.evaluation.meeting.status = "COMPLETED"
    current.control.stage_index = 11
    store.save_state(current)
    monkeypatch.setattr(pipeline, "start", lambda _: None)
    assert pipeline.continue_run(state.run_id)
    resumed = store.load_state(state.run_id)
    assert resumed.cost.budget_usd == pytest.approx(5.9)
    def report(ctx):
        ctx.state.report = ReportArtifact(markdown="Updated")
    stages = list(pipeline.PIPELINE)
    stages[11] = ("s9_report", "Report", report)
    monkeypatch.setattr(pipeline, "PIPELINE", stages)
    result = pipeline.execute_stage(state.run_id, 11, resumed.scratch["execution_epoch"])
    assert result["status"] == "COMPLETED" and not result["continue_execution"]
    saved = store.load_state(state.run_id)
    assert saved.feedback == state.feedback and saved.pending is None
    assert saved.scratch["review_refresh"]["status"] == "COMPLETED"


def test_finished_legacy_ui_retry_is_reconciled_without_new_model_calls(state):
    from triz.schema import HumanRequest
    completed(state)
    refresh_job.prepare(state.run_id, "test-refresh")
    current = store.load_state(state.run_id)
    current.status = "WAITING_HUMAN"
    current.report = ReportArtifact(markdown="Updated")
    current.evaluation.meeting.status = "COMPLETED"
    current.pending = HumanRequest(kind="FEEDBACK", title="Feedback")
    store.save_state(current)
    assert refresh_job.prepare(state.run_id, "test-refresh") is None
    saved = store.load_state(state.run_id)
    assert saved.status == "COMPLETED" and saved.pending is None
    assert saved.feedback == state.feedback
