"""Part6 runs within ARIZ before validation and never changes the problem."""
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
from ariz_fixtures import ariz_payload


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


def configure_ariz(monkeypatch, parts):
    original = nodes.cfg
    monkeypatch.setattr(nodes, "cfg", lambda key, default=None:
        parts if key == "ariz.enabled_parts" else original(key, default))


def part5_payload(no_ideas=False):
    return {"steps": [{"step_code": c, "status": "DONE", "output": "Applicability reviewed."}
                      for c in ("5.1", "5.3", "5.4")],
            "ideas": [] if no_ideas else [{"title": "Original solution", "idea": "Preserve the original boundary.", "source_step": "5.3"}],
            "final_ideas": [] if no_ideas else ["Original solution"],
            "unresolved_reason": "No applicable idea under the recorded limits." if no_ideas else ""}


@pytest.mark.parametrize("count", [0, 3, 4, 12])
def test_part6_always_runs_between_part5_and_part7_without_changing_problem(state, monkeypatch, count):
    prepare(state, count)
    configure_ariz(monkeypatch, [5, 7])  # Old configuration deliberately has no 6.
    unchanged = {key: deepcopy(getattr(state, key).model_dump())
                 for key in ("intake", "analysis", "definition", "constraints")}
    concepts = deepcopy(state.concepts)
    calls = []

    def respond(ctx, **kwargs):
        calls.append(deepcopy(kwargs))
        if kwargs["node"] == "s5_ariz_p5":
            data = part5_payload(no_ideas=count == 0)
        elif kwargs["node"] == "s5_ariz_p6":
            context = kwargs["vars"]["problem_reformulation_context"]
            assert context["ariz_context"]["steps"][-1]["step_code"] == "5.4"
            assert "solution_count" not in context
            assert context["constraints"]
            data = model_review()
        else:
            assert kwargs["node"] == "s5_ariz_p7"
            assert kwargs["vars"]["ideas"] == ["Original solution"]
            data = ariz_payload(7)
        if kwargs.get("checker"):
            assert not kwargs["checker"](data)
        return data

    monkeypatch.setattr(agent, "run_agent", respond)
    nodes._track_d_ariz(RunContext(state))

    assert [call["node"] for call in calls] == ["s5_ariz_p5", "s5_ariz_p6"] + (["s5_ariz_p7"] if count else [])
    codes = [step.step_code for step in state.solve.ariz.steps]
    assert codes[3:6] == ["6.1", "6.2", "6.3"]
    assert codes[6:] == ["7.1", "7.2", "7.3", "7.4"]
    if count == 0:
        assert all(step.status == "SKIPPED" and "미해결 이유" in step.output
                   for step in state.solve.ariz.steps[6:])
        assert state.solve.ariz.verdicts == []
        assert state.steps[-1].node == "s5_ariz_p7" and state.steps[-1].status == "SKIPPED"
        assert state.steps[-1].agent_id == "deterministic_review"
    review = reformulation.for_report(state)
    assert [item.step_code for item in review.items] == ["6.1", "6.2", "6.3"]
    assert {item.source for item in review.items} == {"MODEL"}
    assert review.solution_ids == []  # Advice does not depend on a later portfolio.
    assert len(state.solve.raw_ideas) == bool(count)
    assert state.concepts == concepts
    assert unchanged == {key: getattr(state, key).model_dump() for key in unchanged}


@pytest.mark.parametrize("count", [0, 3, 4, 12])
def test_evaluation_never_invents_part6_without_ariz(state, monkeypatch, count):
    prepare(state, count)
    calls = []

    def respond(ctx, **kwargs):
        calls.append(kwargs)
        assert kwargs["node"] == "s8_rank"
        assert "problem_reformulation_context" not in kwargs["vars"]
        return {"ranking": [{"concept_id": c.id, "rank": i} for i, c in enumerate(state.concepts, 1)],
                "problem_reformulation_review": model_review()}

    monkeypatch.setattr(agent, "run_agent", respond)
    if count:
        nodes._rank(RunContext(state))
    else:
        nodes.s8_evaluate(RunContext(state))
    assert len(calls) == bool(count)
    assert reformulation.for_report(state) is None
    assert state.evaluation.problem_reformulation_review is None
    assert all(step.node != "s8_ariz_p6" for step in state.steps)


@pytest.mark.parametrize("payload", [None, {}, {"items": []},
    {"items": [{"step_code": "6.1", "observation": "Only one", "suggestion": "Incomplete"}]},
    {"items": [{"step_code": code, "observation": "", "suggestion": "Missing evidence"}
               for code in ("6.1", "6.2", "6.3")]}])
def test_incomplete_part6_cannot_be_replaced_with_static_suggestions(state, monkeypatch, payload):
    from triz.context import AbortRun
    configure_ariz(monkeypatch, [])
    monkeypatch.setattr(agent, "run_agent", lambda *args, **kwargs: deepcopy(payload))
    with pytest.raises(AbortRun, match="Part6 검토가 완전하지"):
        nodes._track_d_ariz(RunContext(state))
    assert state.solve.ariz is None
    assert reformulation.for_report(state) is None


def test_part6_repair_exhaustion_is_failed_and_never_runs_part7(state, monkeypatch):
    from types import SimpleNamespace
    from triz.context import AbortRun
    configure_ariz(monkeypatch, [])
    monkeypatch.setitem(settings.triz["verification"], "max_repair_attempts", 1)
    calls = []
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        assert kwargs["_node"] == "s5_ariz_p6"
        return SimpleNamespace(meta={}, data={"items": []}, model="offline", tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, "tracked_chat", chat)
    with pytest.raises(AbortRun, match="치명적 결함"):
        nodes._track_d_ariz(RunContext(state))
    assert len(calls) == 2 and state.steps[-1].status == "FAILED"
    assert state.solve.ariz is None


def test_old_pin_missing_part6_gets_only_the_explicit_new_prompt(state, monkeypatch):
    from types import SimpleNamespace
    prepare(state, 4)
    runtime.initialize(state)
    pinned = state.scratch["ax_bundle"]
    pinned["prompts"].pop("P_S5_ARIZ_PART6")
    pinned_before = deepcopy(pinned)
    configure_ariz(monkeypatch, [])
    requests = []

    def chat(ctx, **kwargs):
        requests.append(kwargs)
        assert kwargs["_node"] == "s5_ariz_p6"
        assert "in-track-review-v1" in kwargs["user"]
        assert "Wafer production line" in kwargs["user"]
        assert "Remove particles while preserving fine patterns." in kwargs["user"]
        return SimpleNamespace(meta={}, data=model_review(), model="offline", tokens_in=1, tokens_out=1, cost_usd=0)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    nodes._track_d_ariz(RunContext(state))
    assert len(requests) == 1 and state.steps[-1].node == "s5_ariz_p6"
    assert state.steps[-1].status == "OK"
    assert state.scratch["ax_bundle"] == pinned_before
    with pytest.raises(KeyError):
        runtime.render_prompt(state, "UNPINNED_UNRELATED_PROMPT")


def save_review(state):
    from triz.schema import ARIZRun
    state.solve.ariz = ARIZRun()
    reformulation.record_ariz(state.solve.ariz, model_review())
    return state.solve.ariz.problem_reformulation_review


@pytest.mark.parametrize("count", [0, 4, 12])
def test_report_review_belongs_to_ariz_regardless_of_later_solution_count(state, count):
    prepare(state, count)
    review = save_review(state)
    state.report = ReportArtifact(narrative={})
    before = state.model_dump(mode="json")
    outputs = [render.render_report(state, {}, template=template)
               for template in ("report_full.md.j2", "report_lite.md.j2")]
    outputs.append(render.render_html(state))
    for output in outputs:
        for item in review.items:
            assert item.step_code in output and item.suggestion in output
        assert "3개 이하" not in output
        assert "최종 보고서에 포함된 해결책이" not in output
    assert state.model_dump(mode="json") == before


def test_evaluation_rerun_retains_ariz_advice_and_solve_rerun_clears_it(state, monkeypatch):
    prepare(state, 4)
    save_review(state)
    state.status = "COMPLETED"
    store.save_state(state)
    monkeypatch.setattr(pipeline, "start", lambda run_id: None)
    assert pipeline.rerun_from(state.run_id, "s8_evaluate")
    saved = store.load_state(state.run_id)
    assert reformulation.for_report(saved) is not None
    saved.status = "COMPLETED"
    store.save_state(saved)
    assert pipeline.rerun_from(state.run_id, "s5_solve")
    assert reformulation.for_report(store.load_state(state.run_id)) is None


def test_ax_report_uses_part6_from_frozen_solve_even_after_live_state_changes(state):
    prepare(state, 4)
    save_review(state)
    state.report = ReportArtifact(narrative={})
    runtime.initialize(state)
    for stage in ("s1_intake", "s2_confirm", "s3_analyze", "s4_define", "s5_solve",
                  "s6_concept", "s7_gate", "s8_references", "s8_evaluate"):
        runtime.checkpoint(state, stage)
    runtime.before_stage(RunContext(state), "s9_report")
    markdown = render.render_report(state, {})
    state.solve.ariz = None
    state.concepts = []
    assert render.render_report(state, {}) == markdown
    assert reformulation.for_report(ax_report.project(state)) is not None
