"""Regression coverage for false PASS, incomplete repairs and stale audit reuse."""
import copy
from types import SimpleNamespace

import pytest

from triz import agent, verification_contract as contract
from triz.context import AbortRun, RunContext
from triz.schema import CauseEffectChain, CauseNode, PhysicalContradiction, SystemCandidate, TechnicalContradiction
from triz.settings import settings


def rubric():
    return {"pass_threshold": .72, "reject_below": .45, "criteria": [
        {"id": "C1", "weight": .25, "required": True, "min_score": 1., "text": "Correct basic function"},
        {"id": "C2", "weight": .75, "text": "Other criteria"}]}


def review(verdict="PASS", first=1., **extra):
    return {"verdict": verdict, "score": 1., "per_criterion": [
        {"id": "C1", "score": first}, {"id": "C2", "score": 1.}], **extra}


@pytest.mark.parametrize("verdict", ["REVISE", "REJECT"])
def test_weighted_score_cannot_erase_explicit_decision(verdict):
    result = contract.normalize_verdict(review(verdict), rubric())
    assert result["verdict"] == verdict and result["score"] == 1.


def test_required_basic_criterion_blocks_weighted_pass():
    result = contract.normalize_verdict(review(first=0.), rubric())
    assert result["score"] == .75 and result["verdict"] == "REVISE"
    assert "C1" in result["revision_instructions"][0]


@pytest.mark.parametrize("extra", [
    {"revision_instructions": ["Replace the harmful BASIC with the supported useful function"]},
    {"element_findings": [{"path": "function_edges[0].rank", "issue": "Harmful BASIC",
                            "suggested_correction": "Use AUXILIARY", "evidence": "kind=HARMFUL",
                            "criterion_id": "C1"}]},
])
def test_actionable_findings_are_not_a_pass(extra):
    assert contract.normalize_verdict(review(**extra), rubric())["verdict"] == "REVISE"


@pytest.mark.parametrize("extra", [{"revision_instructions": {"issue": "wrong BASIC"}},
                                    {"fatal_flaws": True}, {"element_findings": "broken"}])
def test_malformed_findings_cannot_be_silently_discarded(extra):
    assert contract.normalize_verdict(review(**extra), rubric())["verdict"] == "UNVERIFIED"


@pytest.mark.parametrize("scores", [None, [], [{"id": "C1", "score": 1.}],
    [{"id": "C1", "score": 1.}, {"id": "C1", "score": 1.}],
    [{"id": "C1", "score": 1.}, {"id": "WRONG", "score": 1.}],
    [{"id": "C1", "score": float("nan")}, {"id": "C2", "score": 1.}],
    [{"id": "C1", "score": float("inf")}, {"id": "C2", "score": 1.}],
    [{"id": "C1", "score": True}, {"id": "C2", "score": 1.}],
])
def test_missing_duplicate_or_nonfinite_scores_cannot_pass(scores):
    result = contract.normalize_verdict({"verdict": "PASS", "score": 1., "per_criterion": scores}, rubric())
    assert result["verdict"] == "UNVERIFIED" and result["score"] == 0.


def test_current_mandatory_rules_overlay_pinned_rubric_without_mutation():
    current = rubric()
    old = rubric()
    old["criteria"][0].pop("required")
    old["criteria"][0].pop("min_score")
    snapshot = copy.deepcopy(old)
    fake = SimpleNamespace(rubric=lambda rid: old, rubrics={"R3_FUNC": current})
    result = contract.effective_rubric(fake, "R3_FUNC")
    assert result["criteria"][0]["required"] and old == snapshot
    assert contract.normalize_verdict(review(first=0.), result)["verdict"] == "REVISE"


def test_new_mandatory_rubric_is_available_to_old_bundle():
    fake = SimpleNamespace(rubric=lambda rid: None, rubrics={"R4_KEY": rubric()})
    assert contract.effective_rubric(fake, "R4_KEY")["criteria"] == rubric()["criteria"]


def test_repair_requires_full_envelope_but_allows_invalid_row_replacement():
    original = {"components": [{"id": "invented"}], "function_edges": [{"id": "duplicate"}]}
    assert contract.repair_shape_issues(original, {"function_edges": []})
    assert not contract.repair_shape_issues(original, {"components": [{"id": "real"}], "function_edges": []})


def result(data, replay=False):
    return SimpleNamespace(data=data, text="", model="offline", tokens_in=2, tokens_out=3, cost_usd=.01,
                           meta={"durable_replay": replay, "source_task_id": "paid-task"})


@pytest.fixture
def runner(state, monkeypatch):
    monkeypatch.setitem(settings.rubrics, "R3_TEST", rubric())
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    monkeypatch.setitem(settings.triz["verification"], "critical_rubrics", [])
    from triz import rag
    monkeypatch.setattr(rag, "lessons_block", lambda state: "")
    from triz.ax import runtime
    monkeypatch.setattr(runtime, "render_prompt", lambda state, prompt_id, **values:
                        "PINNED " + prompt_id + " " + str(values))
    calls = []
    responses = []
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value
    monkeypatch.setattr(agent, "tracked_chat", chat)
    def run(**kwargs):
        return agent.run_agent(RunContext(state), node="s3_test", label="analysis", stage="S3",
            agent_id="system_analyst", prompt_id="P_S3_FUNCTION_MODEL", rubric_id="R3_TEST",
            checker=lambda data: [] if isinstance(data, dict) and "rows" in data else ["rows required"],
            **kwargs)
    return run, responses, calls


def test_findings_repair_whole_output_and_reaudit_before_commit(state, runner):
    run, responses, calls = runner
    bad = {"rows": [{"id": "kept", "action": "bad"}], "mermaid": "unchanged"}
    fixed = {"rows": [{"id": "kept", "action": "fixed"}], "mermaid": "unchanged"}
    finding = {"path": "rows[0].action", "issue": "wrong action", "suggested_correction": "fixed",
               "evidence": "confirmed boundary", "criterion_id": "C1"}
    responses.extend([result(bad, replay=True), result(review(element_findings=[finding])),
                      result(fixed), result(review())])
    assert run() == fixed
    step = state.steps[-1]
    assert step.status == "OK" and len(step.verdicts) == 2
    assert step.verdicts[0]["verdict"] == "REVISE" and step.verdicts[-1]["verdict"] == "PASS"
    assert "rows[0].action" in calls[2]["user"] and "전체 JSON" in calls[2]["user"]
    assert step.input_slice["replay_source"]["task_id"] == "paid-task"
    assert step.tokens_in == 8 and step.tokens_out == 12


def test_partial_repair_cannot_drop_other_envelope_fields(state, runner):
    run, responses, calls = runner
    responses.extend([result({"rows": [], "other": [1]}), result(review("REVISE")), result({"rows": []})])
    with pytest.raises(AbortRun):
        run(repair_attempts=1)
    assert state.steps[-1].status == "FAILED"
    assert state.steps[-1].verdicts[-1]["source"] == "deterministic"
    assert "other" in state.steps[-1].verdicts[-1]["revision_instructions"][0]
    assert len(calls) == 3 and not state.scratch["agent_cache"]


@pytest.mark.parametrize("verdict", ["REVISE", "REJECT", "UNVERIFIED"])
def test_critical_audit_failure_stops_downstream(state, runner, verdict):
    run, responses, calls = runner
    responses.extend([result({"rows": []}), result(review(verdict))])
    with pytest.raises(AbortRun):
        run(repair_attempts=0)
    assert state.steps[-1].status == "FAILED" and not state.scratch["agent_cache"]


def test_transient_generation_failure_does_not_return_default(state, runner):
    from triz import llm
    run, responses, calls = runner
    responses.append(llm.LLMError("offline failure"))
    with pytest.raises(AbortRun):
        run(default={"rows": ["unsafe default"]})
    assert state.steps[-1].status == "FAILED"


def test_disabled_critical_verification_stops_before_spending_on_generation(state, runner, monkeypatch):
    run, responses, calls = runner
    monkeypatch.setitem(settings.triz["verification"], "enabled", False)
    with pytest.raises(AbortRun):
        run()
    assert not calls and state.steps[-1].status == "FAILED"


def test_cache_checks_contract_and_reaudits_changed_rubric(state, runner, monkeypatch):
    run, responses, calls = runner
    responses.extend([result({"rows": ["valid"]}), result(review())])
    run()
    run()
    assert len(calls) == 2 and state.steps[-1].status == "SKIPPED"
    changed = rubric()
    changed["criteria"][0]["text"] = "A stricter criterion"
    monkeypatch.setitem(settings.rubrics, "R3_TEST", changed)
    responses.extend([result({"rows": ["valid"]}), result(review())])
    run()
    assert len(calls) == 4 and state.steps[-1].status == "OK"


def test_verifier_receives_user_confirmed_module_boundary(state, monkeypatch):
    selected = SystemCandidate(name="Mirror suspension", description="Support the mirror", super_system="Detector")
    state.confirm.candidates = [selected]
    state.confirm.chosen_candidate_id = selected.id
    state.confirm.user_confirmed = True
    state.domain.target_system = "Detector"
    captured = []
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    monkeypatch.setitem(settings.triz["verification"], "critical_rubrics", [])
    def chat(ctx, **kwargs):
        captured.append(kwargs["user"])
        rb = contract.effective_rubric(settings, "R3_FUNC")
        return result({"verdict": "PASS", "per_criterion": [{"id": c["id"], "score": 1.} for c in rb["criteria"]]})
    monkeypatch.setattr(agent, "tracked_chat", chat)
    verdict = agent.verify_artifact(RunContext(state), "R3_FUNC", {"function_edges": []}, "")
    assert verdict["verdict"] == "PASS"
    assert "Mirror suspension" in captured[0] and "Support the mirror" in captured[0]
    assert "user_confirmed" in captured[0] and "필수 독립 검증 계약" in captured[0]


def test_key_problem_verifier_receives_all_candidate_contradictions_and_cause_nodes(state, monkeypatch):
    state.definition.technical_contradictions = [TechnicalContradiction(id="TC-saved", label="TC1")]
    state.definition.physical_contradictions = [PhysicalContradiction(id="PC-saved", derived_from_tc_id="TC-saved")]
    state.analysis.ceca = CauseEffectChain(nodes=[
        CauseNode(id="N-unselected", text="Unselected intermediate explanation", node_type="INTERMEDIATE")])
    captured = []
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    def chat(ctx, **kwargs):
        captured.append(kwargs["user"])
        rb = contract.effective_rubric(settings, "R4_KEY")
        return result({"verdict": "PASS", "per_criterion": [{"id": c["id"], "score": 1.} for c in rb["criteria"]]})
    monkeypatch.setattr(agent, "tracked_chat", chat)
    verdict = agent.verify_artifact(RunContext(state), "R4_KEY", {"key_problems": []}, "")
    assert verdict["verdict"] == "PASS"
    assert all(value in captured[0] for value in ("TC-saved", "PC-saved", "N-unselected",
                                                "Unselected intermediate explanation"))


def test_ceca_generation_receives_citable_observations_and_confirmed_boundary(state):
    selected = SystemCandidate(id="module", name="Selected module", description="Confirmed operating scope")
    state.confirm.candidates = [selected]
    state.confirm.chosen_candidate_id = selected.id
    state.confirm.user_confirmed = True
    state.scratch["deep_dive"] = {"confirmed_facts": ["MEASURED source fact"]}
    text = contract.generation_supplement(state, "s3_ceca")
    assert all(value in text for value in (state.raw_query, "MEASURED source fact", "Selected module",
                                           "Confirmed operating scope", "observations.confirmed_facts"))
