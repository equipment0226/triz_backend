"""Role KPI scoring without peer exchanges, including partial resume and reporting."""
from copy import deepcopy
import threading
from types import SimpleNamespace

import pytest

from triz import agent, evidence, meeting, nodes, personas, presentation, render, review_comments, store
from triz.context import AbortRun, RunContext
from triz.schema import ConceptSpec, EvidenceCard, EvaluationMeeting, Persona
from triz.settings import settings

REAL_RUN_AGENT = agent.run_agent

@pytest.fixture
def independent_case(state, monkeypatch):
    state.concepts = [ConceptSpec(id=f"C{i}", title=f"Option {i}", quality_status="PASS") for i in (1, 2)]
    roles = [Persona(persona_id="A", role_name="Finance", mandate="KPI_MARGIN: improve unit margin.",
                     dimensions=["GOAL", "COST"]),
             Persona(persona_id="B", role_name="Operations", mandate="KPI_UPTIME: preserve service availability.",
                     dimensions=["FEASIBILITY", "TIME"])]
    roster_calls, calls = [], []
    def roster(ctx):
        roster_calls.append(1)
        return deepcopy(roles)
    monkeypatch.setattr(personas, "build_personas", roster)

    def respond(ctx, **kwargs):
        values = kwargs["vars"]
        calls.append(deepcopy(kwargs))
        assert kwargs["node"] == "s8_review_independent"
        assert kwargs["prompt_id"] == "P_S8_REVIEW" and kwargs["max_tokens"] == 8000
        assert not {"participant_roster", "meeting_transcript", "initial_review", "inbox", "prior_exchanges"} & values.keys()
        assert len(values["review_concept_ids"]) * len(values["dimensions"]) <= 12
        return {"scores": [{"concept_id": cid, "dimension": dim, "score": 3, "confidence": .7,
                            "rationale": f"{values['role_name']} reviews {dim} against its KPI.",
                            "red_flags": [], "improvement_suggestion": "Validate with a limited pilot."}
                           for cid in values["review_concept_ids"] for dim in values["dimensions"]],
                "concept_comments": {cid: f"{values['role_name']}: KPI improves if the pilot validates the assumptions."
                                     for cid in values["review_concept_ids"]}}
    monkeypatch.setattr(agent, "run_agent", respond)
    return state, respond, calls, roster_calls


def test_default_pipeline_uses_independent_kpis_and_keeps_report_comments_and_card_scores(independent_case, monkeypatch):
    state, respond, calls, _ = independent_case
    assert settings.cfg("evaluation.mode") == "independent"
    state.raw_query = "VISIBLE_OBSERVATION"
    state.domain.problem_type = "ORGANIZATIONAL_BUSINESS"
    state.domain.is_engineering = False
    state.concepts[0].triz_origin = [{"track": "HIDDEN_ORIGIN"}]
    state.scratch["deep_dive"] = {"competing_hypotheses": ["HIDDEN_HYPOTHESIS"]}
    state.concepts[0].evidence_ids = ["E1"]
    state.evidence = [EvidenceCard(id="E1", claim="VISIBLE_EVIDENCE", evidence_scope="Abstract only")]
    local, requests = threading.local(), []
    def run(ctx, **kwargs):
        local.call = kwargs
        return REAL_RUN_AGENT(ctx, **kwargs)
    def chat(ctx, **kwargs):
        data = respond(ctx, **local.call)
        requests.append(kwargs)
        return SimpleNamespace(data=data, model="offline", tokens_in=10, tokens_out=20, cost_usd=0.0)
    monkeypatch.setattr(agent, "run_agent", run)
    monkeypatch.setattr(agent, "tracked_chat", chat)
    monkeypatch.setattr(agent, "verify_artifact", lambda *a, **kw: {"verdict": "PASS", "score": 1.0})
    monkeypatch.setattr(nodes, "_rank", lambda ctx: None)
    nodes.s8_evaluate(RunContext(state))
    assert len(calls) == len(requests) == 2
    for request in requests:
        assert request["tier"] == "T3" and request["max_tokens"] == 8000
        assert "VISIBLE_OBSERVATION" in request["user"] and "VISIBLE_EVIDENCE" in request["user"]
        assert "HIDDEN_ORIGIN" not in request["user"] and "HIDDEN_HYPOTHESIS" not in request["user"]
        assert "{{" not in request["user"]
        assert ("KPI_MARGIN" in request["user"]) != ("KPI_UPTIME" in request["user"])
    restored = store.load_state(state.run_id)
    session = restored.evaluation.meeting
    assert session.status == "COMPLETED" and session.rounds == 0
    assert not session.questions and not session.answers and not session.initial_reviews
    assert len(session.final_reviews) == 2 and all(not r.communication_summary for r in session.final_reviews)
    for evaluation in restored.evaluation.evaluations:
        assert set(evaluation.aggregate) == {"GOAL", "COST", "FEASIBILITY", "TIME"}
        comments = review_comments.by_concept(restored)[evaluation.concept_id]
        assert len(comments) == 2 and all("KPI improves" in c["comment"] for c in comments)
    card = presentation.view(restored)["solutions"][0]
    assert set(card["dimensions"]) == {"GOAL", "COST", "FEASIBILITY", "TIME"}
    for template in ("report_full.md.j2", "report_lite.md.j2"):
        report = render.render_report(restored, {}, template=template)
        assert report.count("| Finance |") == 2 and report.count("| Operations |") == 2
        assert "| 검토자 | 최종 의견 |" in report


def test_interrupted_large_review_resumes_only_missing_batches(independent_case, monkeypatch):
    state, respond, calls, roster_calls = independent_case
    state.concepts.extend(ConceptSpec(id=f"C{i}", title=f"Option {i}", quality_status="PASS") for i in range(3, 14))
    failed = False
    def fail_once(ctx, **kwargs):
        nonlocal failed
        values = kwargs["vars"]
        assert len(values["concepts_blind"]) == 13
        if values["role_id"] == "B" and values["review_concept_ids"][0] == "C7" and not failed:
            failed = True
            return None
        return respond(ctx, **kwargs)
    monkeypatch.setattr(agent, "run_agent", fail_once)
    reached = []
    monkeypatch.setattr(nodes, "_rank", lambda ctx: reached.append("rank"))
    with pytest.raises(AbortRun):
        nodes.s8_evaluate(RunContext(state))
    assert not reached and not state.evaluation.evaluations
    restored = store.load_state(state.run_id)
    before = len(calls)
    scores = meeting.evaluate(RunContext(restored))
    assert [(k["vars"]["role_id"], k["vars"]["review_concept_ids"]) for k in calls[before:]] == [
        ("B", [f"C{i}" for i in range(7, 13)]), ("B", ["C13"])]
    assert len(scores) == 52 and len(roster_calls) == 1
    assert all(len(r.concept_comments) == 13 for r in restored.evaluation.meeting.final_reviews)


def test_old_discussion_is_not_reused_as_independent_review_and_changed_inputs_invalidate_cache(independent_case):
    state, _, calls, roster_calls = independent_case
    state.evaluation.meeting = EvaluationMeeting(status="COMPLETED", rounds=2,
        completed_calls={"initial:A": {"scores": []}}, context_hash="old-discussion")
    meeting.evaluate(RunContext(state))
    assert len(calls) == 2 and "initial:A" not in state.evaluation.meeting.completed_calls
    meeting.evaluate(RunContext(state))
    assert len(calls) == 2  # Ranking retries do not repeat role reviews.
    state.concepts[0].description = "Changed operating condition"
    meeting.evaluate(RunContext(state))
    assert len(calls) == 4 and len(roster_calls) == 2


@pytest.mark.parametrize("fault", ["missing_comment", "unknown_comment", "long_comment", "duplicate_score", "missing_score"])
def test_incomplete_comments_or_score_matrix_are_not_accepted(independent_case, fault):
    state, respond, _, _ = independent_case
    role = Persona(role_name="Finance", dimensions=["COST"])
    values = {"role_name": role.role_name, "dimensions": role.dimensions, "review_concept_ids": ["C1", "C2"]}
    data = respond(RunContext(state), node="s8_review_independent", prompt_id="P_S8_REVIEW", max_tokens=8000, vars=values)
    if fault == "missing_comment": del data["concept_comments"]["C2"]
    if fault == "unknown_comment": data["concept_comments"]["OTHER"] = "Unknown"
    if fault == "long_comment": data["concept_comments"]["C1"] = "x" * 321
    if fault == "duplicate_score": data["scores"].append(deepcopy(data["scores"][0]))
    if fault == "missing_score": data["scores"].pop()
    assert meeting._check_independent(data, role, {"C1", "C2"})


def test_large_evidence_candidate_set_has_output_headroom_without_discarding_late_sources(state, monkeypatch):
    state.concepts = [ConceptSpec(id="C1", title="Heat transfer control")]
    state.scratch["evidence_candidates"] = [dict(identifier=f"US{i}", title=f"Patent {i}",
        source_type="PATENT", url=f"https://example.com/{i}", year="2020", provider="offline",
        concept_ids=["C1"], snippet="Thermal transfer is controlled by a reversible contact and an independent isolation mechanism.") for i in range(95)]
    def respond(ctx, **kwargs):
        assert kwargs["max_tokens"] == 8000
        assert len(kwargs["vars"]["candidates"]) == 95
        assert kwargs["vars"]["max_matches_per_kind"] == 2
        return {"matches": [{"concept_id": "C1", "index": 94, "confidence": .8,
                             "mechanism_mapping": "Reversible thermal contact matches the control mechanism.",
                             "transfer_conditions": ["Validate isolation under fault conditions."]}], "additions": []}
    monkeypatch.setattr(agent, "run_agent", respond)
    evidence.attach(RunContext(state), discover_sources=False)
    assert state.evidence[0].identifier == "US94"
    assert state.concepts[0].transfer_conditions == ["Validate isolation under fault conditions."]
