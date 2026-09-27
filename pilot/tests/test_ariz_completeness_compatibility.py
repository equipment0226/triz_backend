"""Part5 repairs or stops; old ranking pins cannot generate downstream Part6."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, knowledge, nodes, prompts_registry, verify
from triz.ax import runtime
from triz.context import AbortRun, RunContext
from triz.settings import settings
from test_ariz_reformulation import model_review, prepare


REQUIRED = ["5.1", "5.3", "5.4"]


def part5(*, no_ideas=False):
    return {
        "steps": [{"step_code": code, "step_title": "Knowledge review",
                   "status": "DONE", "output": "Reviewed applicability and operating limits."}
                  for code in REQUIRED],
        "ideas": [] if no_ideas else [{"title": "Separate conditions",
            "idea": "Separate the incompatible operating conditions.", "source_step": "5.3"}],
        "final_ideas": [] if no_ideas else ["Separate conditions"],
        "unresolved_reason": "Available resources do not satisfy the required operating limits." if no_ideas else "",
    }


def only_part5(monkeypatch):
    original = nodes.cfg
    monkeypatch.setattr(nodes, "cfg", lambda key, default=None:
        [5] if key == "ariz.enabled_parts" else original(key, default))


def chat_result(data):
    return SimpleNamespace(data=deepcopy(data), model="offline", tokens_in=1, tokens_out=1, cost_usd=0)


@pytest.mark.parametrize("problem", ["missing_steps", "duplicate_step", "empty_output",
    "invalid_status", "invalid_table", "empty_ideas_without_reason", "malformed_idea", "missing_final_summary"])
def test_part5_incomplete_results_are_fatal_after_repair_exhaustion(problem):
    data = part5()
    if problem == "missing_steps":
        data["steps"] = [data["steps"][0], {"step_code": "5.2", "output": "Analogy", "status": "DONE"}]
    elif problem == "duplicate_step":
        data["steps"].append(deepcopy(data["steps"][0]))
    elif problem == "empty_output":
        data["steps"][1]["output"] = " "
    elif problem == "invalid_status":
        data["steps"][1]["status"] = "PENDING"
    elif problem == "invalid_table":
        data["steps"][1]["table_rows"] = "This would be dropped by ARIZStep construction."
    elif problem == "empty_ideas_without_reason":
        data["ideas"] = []
    elif problem == "malformed_idea":
        data["ideas"][0]["source_step"] = "4.1"
    elif problem == "missing_final_summary":
        data["final_ideas"] = []
    issues = verify.check_ariz_part5(data, REQUIRED)
    assert issues and all(issue.startswith("FATAL-ARIZ5:") for issue in issues)


def test_part5_allows_documented_nonapplicability_without_fabricating_ideas():
    data = part5(no_ideas=True)
    data["steps"][1].update(status="SKIPPED", output="Required separation axis is unavailable.")
    assert verify.check_ariz_part5(data, REQUIRED) == []


def test_observed_partial_part5_is_repaired_before_committing(state, monkeypatch):
    only_part5(monkeypatch)
    responses = [{"steps": [{"step_code": "5.1", "status": "DONE", "output": "Review"},
                             {"step_code": "5.2", "status": "DONE", "output": "Analogy"}],
                  "ideas": [], "final_ideas": []}, part5(), model_review()]
    requests = []

    def chat(ctx, **kwargs):
        requests.append(kwargs)
        return chat_result(responses.pop(0))

    monkeypatch.setattr(agent, "tracked_chat", chat)
    nodes._track_d_ariz(RunContext(state))

    assert len(requests) == 3
    assert "5.3" in requests[1]["user"] and "5.4" in requests[1]["user"]
    assert "unresolved_reason" in requests[0]["user"]
    assert {step.step_code for step in state.solve.ariz.steps} == set(REQUIRED + ["6.1", "6.2", "6.3"])
    assert len(state.solve.raw_ideas) == 1
    trace = next(step for step in state.steps if step.node == "s5_ariz_p5")
    assert trace.status == "OK" and trace.verify_attempts == 2
    assert trace.verdicts[0]["source"] == "deterministic"


def test_unrepaired_part5_stops_without_committing_an_ariz_run(state, monkeypatch):
    only_part5(monkeypatch)
    monkeypatch.setitem(settings.triz["verification"], "max_repair_attempts", 1)
    calls = []

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return chat_result({"steps": [], "ideas": [], "final_ideas": []})

    monkeypatch.setattr(agent, "tracked_chat", chat)
    with pytest.raises(AbortRun, match="치명적 결함"):
        nodes._track_d_ariz(RunContext(state))
    assert len(calls) == 2 and state.steps[-1].status == "FAILED"
    assert state.solve.ariz is None and not state.solve.raw_ideas


def test_part5_call_failure_default_does_not_silently_complete(state, monkeypatch):
    only_part5(monkeypatch)
    monkeypatch.setattr(agent, "run_agent", lambda *args, **kwargs: {})
    with pytest.raises(AbortRun, match="Part5 검토가 완전하지"):
        nodes._track_d_ariz(RunContext(state))
    assert state.solve.ariz is None


def test_part5_retains_reason_for_legitimate_zero_idea_result(state, monkeypatch):
    only_part5(monkeypatch)
    monkeypatch.setattr(agent, "tracked_chat", lambda *args, **kwargs:
        chat_result(model_review() if kwargs.get("_node") == "s5_ariz_p6" else part5(no_ideas=True)))
    nodes._track_d_ariz(RunContext(state))
    assert state.steps[-1].status == "OK"
    assert state.solve.ariz.unresolved_reason == part5(no_ideas=True)["unresolved_reason"]
    assert not state.solve.raw_ideas


def test_old_pinned_rank_does_not_generate_part6_or_replace_pin(state, monkeypatch):
    prepare(state, 3)
    runtime.initialize(state)
    old = "PINNED RANKING POLICY\n{{aggregate_table}}\nOutput ranking, ranking_note, portfolio_note, roadmap."
    state.scratch["ax_bundle"]["prompts"]["P_S8_RANK"] = old
    pinned = deepcopy(state.scratch["ax_bundle"])
    requests = []

    def chat(ctx, **kwargs):
        requests.append(kwargs)
        assert "[전체 후보 순위 계약 v1]" in kwargs["user"]
        assert "problem_reformulation_context" not in kwargs["user"]
        assert "problem_reformulation_review" not in kwargs["user"]
        return chat_result({"ranking": [{"concept_id": c.id, "rank": i}
            for i, c in enumerate(state.concepts, 1)], "problem_reformulation_review": model_review()})

    monkeypatch.setattr(agent, "tracked_chat", chat)
    nodes._rank(RunContext(state))

    assert len(requests) == 1
    assert state.scratch["ax_bundle"] == pinned
    assert state.evaluation.problem_reformulation_review is None
    assert state.solve.ariz is None
    assert all(step.node != "s8_ariz_p6" for step in state.steps)


def test_compatibility_is_idempotent_and_leaves_current_rank_and_other_pins_unchanged(state):
    current = prompts_registry.raw("P_S8_RANK")
    assert prompts_registry.compatible_body("P_S8_RANK", current) == current
    old = "Old ranking rules {{aggregate_table}}"
    patched = prompts_registry.compatible_body("P_S8_RANK", old)
    assert patched == current
    assert prompts_registry.compatible_body("P_S8_RANK", patched) == patched
    assert prompts_registry.compatible_body("P_S4_CONTRADICTIONS", old) == old
    part5_body = prompts_registry.compatible_body("P_S5_ARIZ_PART5", "Pinned Part5 policy")
    assert part5_body.startswith("Pinned Part5 policy")
    assert prompts_registry.compatible_body("P_S5_ARIZ_PART5", part5_body) == part5_body
    assert "unresolved_reason" in part5_body and all(code in part5_body for code in REQUIRED)
    assert REQUIRED == [s["code"] for s in knowledge.ariz_part(5)["steps"] if s.get("required")]


def test_retired_part6_clause_is_removed_from_rank_pin_without_changing_ranking_policy():
    old = ('Pinned ranking rules {{aggregate_table}}\n'
           '[최종 해결책 수에 따른 ARIZ Part 6 추가 코멘트]\n'
           '{{problem_reformulation_context}}\nSolution이 3개 이하이면 검토한다.\n'
           '[출력 JSON]\n{"ranking":[],"roadmap":[],"problem_reformulation_review":null}\n'
           '검토 대상이면 null 대신 {"items":[]}를 출력한다.')
    updated = prompts_registry.compatible_body("P_S8_RANK", old)
    assert "[전체 후보 순위 계약 v1]" in updated
    assert updated == prompts_registry.raw("P_S8_RANK")
    assert "problem_reformulation" not in updated and "3개 이하" not in updated
    assert prompts_registry.compatible_body("P_S8_RANK", updated) == updated
