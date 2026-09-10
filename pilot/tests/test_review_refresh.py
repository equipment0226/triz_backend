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
