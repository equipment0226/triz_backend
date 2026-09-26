"""Part 6 adds report advice without another model call or changing the problem."""
from copy import deepcopy

import pytest

from triz import agent, nodes, pipeline, reformulation, render, store
from triz.ax import report as ax_report, runtime
from triz.context import RunContext
from triz.schema import (
    ConceptEvaluation, ConceptSpec, Constraint, ConstraintCheckResult,
    KeyProblem, ReportArtifact, TechnicalContradiction,
)
from triz.settings import settings


TITLE = "추가 코멘트 · ARIZ Part 6 문제 변경 제안"
CODES = {"6.1", "6.2", "6.3"}


def prepare(state, count):
    state.domain.target_system = "Cleaning chamber"
    state.domain.super_system = "Wafer production line"
    state.definition.mini_problem = "Remove particles while preserving fine patterns."
    state.definition.technical_contradictions = [
        TechnicalContradiction(id="TC-clean", label="Cleaning versus damage",
            if_action="Raise cleaning intensity", then_good="Remove particles",
            but_bad="Damage patterns"),
        TechnicalContradiction(id="TC-time", label="Cleaning versus throughput",
            if_action="Extend cleaning time", then_good="Remove particles",
            but_bad="Reduce throughput"),
    ]
    state.definition.key_problems = [
        KeyProblem(id="KP-clean", title="Pattern damage", contradiction_ids=["TC-clean"]),
        KeyProblem(id="KP-time", title="Throughput loss", contradiction_ids=["TC-time"]),
    ]
    state.constraints.items = [Constraint(id="CON-safe", statement="Preserve patterns", hard=True)]
    state.concepts = [ConceptSpec(id=f"C{i}", title=f"Candidate {i}",
        quality_status="REVISE", working_principle="Separate cleaning conditions",
        addresses_contradictions=["TC-clean"], resolution_argument="Requires testing")
        for i in range(1, count + 1)]
    state.constraint_checks = [ConstraintCheckResult(concept_id=c.id, verdict="CONDITIONAL")
                               for c in state.concepts]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id=c.id, total_score=3)
                                   for c in state.concepts]
    return state


def model_review():
    return {"items": [
        {"step_code": "6.1", "observation": "Two coupled requirements are recorded.",
         "suggestion": "Could particle removal and damage prevention be framed separately?"},
        {"step_code": "6.2", "observation": "Two technical contradictions are recorded.",
         "suggestion": "Could cleaning versus throughput become the starting contradiction?"},
        {"step_code": "6.3", "observation": "The production line is the recorded supersystem.",
         "suggestion": "Could the particle problem be reformulated across the production line?"},
    ]}


def stub_rank(monkeypatch, state, review):
    calls = []

    def respond(ctx, **kwargs):
        calls.append(deepcopy(kwargs))
        assert kwargs["node"] == "s8_rank", "Part 6 must not introduce another model node"
        return {"ranking": [{"concept_id": c.id, "rank": i}
                            for i, c in enumerate(state.concepts, 1)],
                "ranking_note": "Existing ranking retained.", "portfolio_note": "Test first.",
                "roadmap": [], "problem_reformulation_review": deepcopy(review)}

    monkeypatch.setattr(agent, "run_agent", respond)
    return calls


def freeze_before_evaluation(state):
    runtime.initialize(state)
    for stage in ("s1_intake", "s2_confirm", "s3_analyze", "s4_define", "s5_solve",
                  "s6_concept", "s7_gate", "s8_references"):
        runtime.checkpoint(state, stage)


@pytest.mark.parametrize("count", [1, 3, 4])
def test_rank_reviews_at_most_three_displayed_solutions_without_extra_calls(state, monkeypatch, count):
    prepare(state, count)
    unchanged = {key: deepcopy(getattr(state, key).model_dump())
                 for key in ("intake", "analysis", "definition", "constraints", "solve")}
    concepts_before = [c.model_dump() for c in state.concepts]
    calls = stub_rank(monkeypatch, state, model_review())

    nodes._rank(RunContext(state))

    assert len(calls) == 1
    assert bool(calls[0]["vars"]["problem_reformulation_context"]) == (count <= 3)
    review = state.evaluation.problem_reformulation_review
    if count <= 3:
        assert set(review.solution_ids) == {c.id for c in state.concepts}
        assert {item.step_code for item in review.items} == CODES
        assert {item.source for item in review.items} == {"MODEL"}
        assert reformulation.for_report(state) == review
    else:
        assert review is None
        assert reformulation.for_report(state) is None
    assert [c.model_dump() for c in state.concepts] == concepts_before
    assert unchanged == {key: getattr(state, key).model_dump() for key in unchanged}


def test_zero_solutions_saves_recorded_analysis_advice_without_calling_a_model(state, monkeypatch):
    prepare(state, 0)
    calls = []
    monkeypatch.setattr(agent, "run_agent", lambda *args, **kwargs: calls.append(kwargs))

    nodes.s8_evaluate(RunContext(state))

    review = state.evaluation.problem_reformulation_review
    assert calls == []
    assert review.solution_ids == []
    assert {item.step_code for item in review.items} == CODES
    assert {item.source for item in review.items} == {"RECORDED_ANALYSIS"}
    assert all(item.observation and item.suggestion for item in review.items)
    saved = store.load_state(state.run_id)
    assert saved.evaluation.problem_reformulation_review == review
    assert not state.concepts


@pytest.mark.parametrize("payload", [None, {"items": "invalid"},
    {"items": [{"step_code": "6.4", "observation": "Unsupported step", "suggestion": "Reduce requirements"}]}])
def test_missing_or_invalid_optional_review_uses_recorded_analysis_without_retry(state, monkeypatch, payload):
    prepare(state, 2)
    calls = stub_rank(monkeypatch, state, payload)

    nodes._rank(RunContext(state))

    assert len(calls) == 1
    review = state.evaluation.problem_reformulation_review
    assert {item.step_code for item in review.items} == CODES
    assert {item.source for item in review.items} == {"RECORDED_ANALYSIS"}
    assert all(item.observation and item.suggestion for item in review.items)
    assert "Reduce requirements" not in str(review.model_dump())


def test_partial_review_preserves_valid_advice_and_labels_each_fallback_honestly(state, monkeypatch):
    prepare(state, 2)
    supplied = model_review()["items"]
    payload = {"items": [supplied[0], supplied[1], deepcopy(supplied[1]),
                         {"step_code": "6.3", "observation": "Missing suggestion", "source": "MODEL"}]}
    calls = stub_rank(monkeypatch, state, payload)

    nodes._rank(RunContext(state))

    assert len(calls) == 1
    items = {item.step_code: item for item in state.evaluation.problem_reformulation_review.items}
    assert items["6.1"].source == "MODEL"
    assert items["6.1"].suggestion == supplied[0]["suggestion"]
    assert items["6.2"].source == items["6.3"].source == "RECORDED_ANALYSIS"
    assert items["6.2"].suggestion and items["6.3"].suggestion


def test_zero_report_distinguishes_missing_analysis_from_completed_model_review(state):
    reformulation.record(state)

    markdown = render.render_report(state, {})

    assert TITLE in markdown
    assert "해결책이 0개" in markdown
    assert "기존 분석 기록" in markdown
    assert "기록이 부족" in markdown
    assert "개별 검토 응답이 없어" in markdown
    assert "선행 단계 재실행이나 변경된 문제의 해결책 도출은 수행하지 않았다" in markdown
    assert "검토 의견" not in markdown
    assert all(item.source == "RECORDED_ANALYSIS"
               for item in state.evaluation.problem_reformulation_review.items)


def test_review_is_hidden_after_candidate_replacement_and_removed_when_count_grows(state):
    prepare(state, 3)
    reformulation.record(state, model_review())
    assert reformulation.for_report(state) is not None
    state.concepts[-1] = ConceptSpec(id="REPLACEMENT", title="Changed candidate")
    assert reformulation.for_report(state) is None
    state.concepts.append(ConceptSpec(id="C4", title="Fourth candidate"))
    reformulation.record(state, model_review())
    assert state.evaluation.problem_reformulation_review is None
    assert reformulation.rank_context(state, 4) == {}


def test_manual_evaluation_rerun_invalidates_prior_review(state, monkeypatch):
    prepare(state, 3)
    reformulation.record(state, model_review())
    state.status = "COMPLETED"
    state.report = ReportArtifact(markdown="Old report")
    store.save_state(state)
    monkeypatch.setattr(pipeline, "start", lambda run_id: None)

    assert pipeline.rerun_from(state.run_id, "s8_evaluate")

    saved = store.load_state(state.run_id)
    assert saved.evaluation.problem_reformulation_review is None
    assert saved.report is None
    assert len(saved.concepts) == 3


def test_review_appears_in_full_lite_and_html_reports_without_modifying_state(state):
    prepare(state, 3)
    reformulation.record(state, model_review())
    state.report = ReportArtifact(narrative={})
    before = state.model_dump(mode="json")

    outputs = [render.render_report(state, {}, template=template)
               for template in ("report_full.md.j2", "report_lite.md.j2")]
    outputs.append(render.render_html(state))

    for output in outputs:
        assert TITLE in output
        for item in state.evaluation.problem_reformulation_review.items:
            assert item.step_code in output
            assert item.suggestion in output
    assert state.model_dump(mode="json") == before


def test_ax_report_keeps_review_from_frozen_analysis_after_live_state_changes(state):
    prepare(state, 3)
    reformulation.record(state, model_review())
    state.report = ReportArtifact(narrative={})
    freeze_before_evaluation(state)
    runtime.checkpoint(state, "s8_evaluate")
    runtime.before_stage(RunContext(state), "s9_report")
    markdown, html = render.render_report(state, {}), render.render_html(state)
    assert TITLE in markdown and TITLE in html

    state.concepts = [ConceptSpec(id="NEW", title="Later candidate")]
    state.evaluation.problem_reformulation_review = None
    state.definition.mini_problem = "Later problem definition"

    assert render.render_report(state, {}) == markdown
    assert render.render_html(state) == html
    assert len(ax_report.project(state).evaluation.problem_reformulation_review.solution_ids) == 3


@pytest.mark.parametrize("ax", [False, True])
def test_trigger_matches_the_report_when_rank_caps_the_live_candidates(state, monkeypatch, ax):
    prepare(state, 4)
    monkeypatch.setitem(settings.triz["solutions"], "max_solutions", 3)
    if ax:
        freeze_before_evaluation(state)
    calls = stub_rank(monkeypatch, state, model_review())

    nodes._rank(RunContext(state))

    assert len(state.concepts) == 3
    assert len(calls) == 1
    assert bool(calls[0]["vars"]["problem_reformulation_context"]) == (not ax)
    if ax:
        runtime.checkpoint(state, "s8_evaluate")
        runtime.before_stage(RunContext(state), "s9_report")
        projected = ax_report.project(state)
        assert len(projected.concepts) == 4
        assert projected.evaluation.problem_reformulation_review is None
        assert TITLE not in render.render_report(state, {})
    else:
        assert len(state.evaluation.problem_reformulation_review.solution_ids) == 3
        assert TITLE in render.render_report(state, {})
