"""Regressions for production S8 reference, repair and output-limit failures."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from test_evaluation_meeting import PHASES, meeting_case
from test_meeting_runtime import install_runtime
from triz import agent, meeting, prompts_registry
from triz.context import AbortRun, RunContext
from triz.schema import Persona


def exchanges():
    return [{"question": {"id": qid, "concept_id": cid, "from_role_id": sender,
                           "to_role_id": target}, "answer": {"answer": "A measured condition."}}
            for qid, cid, sender, target in [("Q1", "C1", "A", "B"),
                                            ("Q2", "C2", "A", "B"),
                                            ("Q3", "C1", "B", "A")]]


def score():
    return {"concept_id": "C1", "dimension": "GOAL", "score": 3,
            "confidence": 0.6, "rationale": "Conditional on measured adoption.", "red_flags": []}


def test_short_reference_selectors_resolve_to_exact_recorded_foreign_keys():
    followups, summaries = meeting._reference_options(exchanges(), "A")
    normalize = meeting._output_normalizer("questions_2", {"followup_options": followups})
    data = normalize({"questions": [{"followup_id": "F2", "to_role_id": "B", "question": "Which limit applies?"}]})
    assert data["questions"][0]["reply_to_question_id"] == "Q2"
    assert data["questions"][0]["concept_id"] == "C2"
    assert data["answers"] == []
    normalize = meeting._output_normalizer("final", {"summary_options": summaries})
    data = normalize({"scores": [score()], "communication_summary": [{
        "summary_id": "S1", "summary": "B clarified the adoption condition.",
        "assessment_change": "Retain a conditional score."}]})
    summary = data["communication_summary"][0]
    assert summary["concept_id"] == "C1"
    assert summary["question_ids"] == ["Q1", "Q3"] and summary["peer_role_ids"] == ["B"]
    assert not meeting._check_final(data, Persona(persona_id="A", dimensions=["GOAL"]), {"C1"}, exchanges())


@pytest.mark.parametrize("reference", ["F999", None, ["F1"]])
def test_normalizer_never_invents_or_guesses_missing_references(reference):
    followups, _ = meeting._reference_options(exchanges(), "A")
    data = meeting._output_normalizer("questions_2", {"followup_options": followups})({
        "questions": [{"followup_id": reference, "to_role_id": "B", "question": "Condition?"}]})
    prior = {x["question"]["id"]: x["question"] for x in exchanges()}
    assert meeting._check_questions(data, "A", {"A", "B"}, {"C1", "C2"}, 2, prior)


def test_explicit_wrong_concept_is_not_silently_reassigned_by_selector():
    followups, _ = meeting._reference_options(exchanges(), "A")
    data = meeting._output_normalizer("questions_2", {"followup_options": followups})({
        "questions": [{"followup_id": "F1", "concept_id": "C2", "to_role_id": "B", "question": "Condition?"}]})
    prior = {x["question"]["id"]: x["question"] for x in exchanges()}
    issues = meeting._check_questions(data, "A", {"A", "B"}, {"C1", "C2"}, 2, prior)
    assert issues and "questions[0]" in issues[0] and "Q2" in issues[0]


def test_partial_repairs_preserve_scores_and_flags_without_masking_failed_calls(state, monkeypatch):
    rows = [score()]
    rows[0]["red_flags"] = "Adoption remains unverified."
    normalized = meeting._output_normalizer("initial", {})
    responses = [{"scores": rows}, {"questions": [{"to_role_id": "B", "concept_id": "C1", "question": "Acceptance?"}]}]
    requests = []

    def chat(ctx, **kwargs):
        requests.append(kwargs)
        return SimpleNamespace(data=deepcopy(responses.pop(0)), model="offline", tokens_in=1, tokens_out=1, cost_usd=0)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    result = agent.run_agent(RunContext(state), node="s8_review_initial", label="Initial", stage="S8",
        agent_id="A", prompt_id="P_S8_MEETING_INITIAL", system_override="JSON", vars={},
        normalizer=normalized, repair_attempts=2,
        checker=lambda d: ["FATAL-questions missing"] if not d.get("questions") else [], max_tokens=8000)
    assert len(requests) == 2 and result["scores"][0]["score"] == 3
    assert result["scores"][0]["red_flags"] == ["Adoption remains unverified."]
    assert normalized(None) is None


def test_missing_numeric_scores_remain_invalid_after_metadata_normalization():
    row = score()
    del row["score"]
    del row["red_flags"]
    data = meeting._output_normalizer("initial", {})({"scores": [row]})
    from triz import verify
    assert verify.check_review(data, {"C1"}, ["GOAL"])


def test_missing_safety_veto_explanation_is_not_normalized_to_no_risk():
    from triz import verify
    row = {**score(), "dimension": "SAFETY", "score": 1}
    del row["red_flags"]
    data = meeting._output_normalizer("initial", {})({"scores": [row]})
    assert "red_flags" not in data["scores"][0]
    assert verify.check_review(data, {"C1"}, ["SAFETY"])


def test_meeting_output_limits_have_headroom_without_reducing_rounds(meeting_case):
    state, responder, _ = meeting_case
    original = agent.run_agent
    limits = []

    def respond(ctx, **kwargs):
        limits.append((kwargs["node"], kwargs["max_tokens"], kwargs["repair_attempts"]))
        return original(ctx, **kwargs)

    # The fixture replaces model calls; capture actual orchestration arguments.
    from unittest.mock import patch
    with patch.object(agent, "run_agent", respond):
        meeting.evaluate(RunContext(state))
    assert len(responder.calls) == 10 and state.evaluation.meeting.rounds == 2
    assert all(limit == 8000 for node, limit, _ in limits if node in (PHASES[0], PHASES[-1]))
    assert all(4000 <= limit <= 8000 for node, limit, _ in limits if node not in (PHASES[0], PHASES[-1]))
    assert all(repairs == 2 for _, _, repairs in limits)


def test_legacy_checkpoint_survives_prompt_rollout_and_retries_only_missing_final(meeting_case, monkeypatch):
    state, responder, roster_calls = meeting_case
    requests, _ = install_runtime(monkeypatch, responder)
    real = agent.run_agent

    def stop_final(ctx, **kwargs):
        if kwargs["node"] == PHASES[-1] and kwargs["vars"]["role_id"] == "B":
            raise AbortRun("Provider unavailable")
        return real(ctx, **kwargs)

    monkeypatch.setattr(agent, "run_agent", stop_final)
    with pytest.raises(AbortRun):
        meeting.evaluate(RunContext(state))
    old_ids = [q.id for q in state.evaluation.meeting.questions]
    state.evaluation.meeting.context_hash = ""  # Field absent in pre-fix production states.
    state.evaluation.meeting.input_hash = "old-format-prompt-hash"
    before = len(requests)
    monkeypatch.setattr(agent, "run_agent", real)
    meeting.evaluate(RunContext(state))
    assert len(roster_calls) == 1
    assert [(r["_node"], r["role_id"]) for r in requests[before:]] == [(PHASES[-1], "B")]
    assert [q.id for q in state.evaluation.meeting.questions] == old_ids
    assert state.evaluation.meeting.context_hash


def test_valid_completed_calls_survive_format_only_prompt_changes(meeting_case, monkeypatch):
    state, responder, roster_calls = meeting_case
    meeting.evaluate(RunContext(state))
    original = prompts_registry.raw
    monkeypatch.setattr(prompts_registry, "raw", lambda prompt: original(prompt) + "\nOutput compact JSON.")
    meeting.evaluate(RunContext(state))
    assert len(responder.calls) == 10 and len(roster_calls) == 1


def test_large_final_review_resumes_only_failed_part_with_full_conversation(meeting_case, monkeypatch):
    from triz.schema import ConceptSpec, GlobalState
    state, responder, _ = meeting_case
    state.concepts.extend(ConceptSpec(id=f"C{i}", title=f"Alternative {i}", quality_status="PASS")
                          for i in range(3, 14))
    requests, failed = [], False

    def respond(ctx, **kwargs):
        nonlocal failed
        values = kwargs["vars"]
        if kwargs["node"] != PHASES[-1]:
            return responder(ctx, **kwargs)
        targets = values["review_concept_ids"]
        requests.append((values["role_id"], list(targets)))
        assert len(values["concepts_blind"]) == 13  # No loss of comparative context.
        assert len(values["meeting_transcript"]) == 4
        assert len(targets) <= 12
        if values["role_id"] == "B" and targets == ["C13"] and not failed:
            failed = True
            return None
        narrowed = {**values, "concepts_blind": [c for c in values["concepts_blind"] if c["concept_id"] in targets]}
        data = responder(ctx, **{**kwargs, "vars": narrowed, "checker": None})
        if not values["include_communication_summary"]:
            data["communication_summary"] = []
        data["concept_comments"] = {cid: "Adopt only after the agreed approval check." for cid in targets}
        return data

    monkeypatch.setattr(agent, "run_agent", respond)
    with pytest.raises(AbortRun):
        meeting.evaluate(RunContext(state))
    restored = GlobalState.model_validate_json(state.model_dump_json())
    before = len(requests)
    result = meeting.evaluate(RunContext(restored))
    assert requests[before:] == [("B", ["C13"])]
    assert len(result) == 26 and len({(s.reviewer_role, s.concept_id) for s in result}) == 26
    assert all(len(r.concept_comments) == 13 for r in restored.evaluation.meeting.final_reviews)
    assert restored.evaluation.meeting.status == "COMPLETED"


def test_final_partition_bounds_output_rows_and_requires_all_target_scores():
    values = {"concepts_blind": [{"concept_id": f"C{i}"} for i in range(10)],
              "dimensions": ["GOAL", "RESOLUTION", "CAUSAL"], "meeting_transcript": exchanges()}
    batches = meeting._final_batches(values)
    assert [len(b["review_concept_ids"]) for b in batches] == [4, 4, 2]
    assert sum(b["include_communication_summary"] for b in batches) == 1
    role = Persona(persona_id="A", dimensions=["GOAL"])
    assert meeting._check_final({"scores": [score()], "communication_summary": []}, role,
                               {"C1", "C2"}, exchanges(), require_summary=False)
