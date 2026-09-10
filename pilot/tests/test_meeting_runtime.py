"""Exercise meeting prompts, role routing and checkpoints through the real runner."""
from collections import Counter
import json
import threading
import time
from types import SimpleNamespace

import pytest

from test_evaluation_meeting import PHASES, meeting_case
from triz import agent, meeting, nodes, store
from triz.context import AbortRun, RunContext
from triz.schema import EvidenceCard


REAL_RUN_AGENT = agent.run_agent


def install_runtime(monkeypatch, responder):
    """Keep real prompt/checker/cache/StepRecord handling; replace only model output."""
    local = threading.local()
    requests = []
    revision = {"answer": ""}
    lock = threading.Lock()

    def run(ctx, **kwargs):
        local.call = kwargs
        return REAL_RUN_AGENT(ctx, **kwargs)

    def chat(ctx, **kwargs):
        metadata = local.call
        data = responder(ctx, **metadata)
        revised = revision["answer"]
        if revised and metadata["node"] == PHASES[1] and metadata["vars"]["role_id"] == "B":
            data["answers"][0]["answer"] = revised
        if revised and metadata["node"] == PHASES[-1]:
            assert revised in json.dumps(metadata["vars"]["meeting_transcript"])
            data["communication_summary"][0]["summary"] = revised
        with lock:
            requests.append({**kwargs, "role_id": metadata["vars"]["role_id"]})
        return SimpleNamespace(data=data, model="offline-meeting-reviewer", tokens_in=10,
                               tokens_out=20, cost_usd=0.0)

    monkeypatch.setattr(agent, "run_agent", run)
    monkeypatch.setattr(agent, "tracked_chat", chat)
    monkeypatch.setattr(agent, "verify_artifact", lambda *args, **kwargs:
                        {"verdict": "PASS", "score": 1.0})
    return requests, revision


def test_real_meeting_runner_renders_blind_business_context_and_persists_final_responses(meeting_case, monkeypatch):
    state, responder, _ = meeting_case
    state.raw_query = "USER_OBSERVATION_371 조직의 권한과 보상 기준을 개선한다."
    state.domain.problem_type = "ORGANIZATIONAL_BUSINESS"
    state.domain.is_engineering = False
    state.scratch["industry_profile"] = {"label": "조직 운영", "difficulty": "advanced"}
    state.scratch["deep_dive"] = {"confirmed_facts": ["CONFIRMED_OBSERVATION_728"],
                                  "competing_hypotheses": ["HIDDEN_COMPETING_HYPOTHESIS_904"]}
    state.concepts[0].triz_origin = [{"track": "HIDDEN_TRIZ_ORIGIN_813"}]
    state.concepts[0].evidence_ids = ["EV_EXTERNAL_265"]
    state.evidence = [EvidenceCard(id="EV_EXTERNAL_265", source_type="PAPER",
                                  claim="FIELD_EVIDENCE_692", evidence_scope="abstract")]
    requests, _ = install_runtime(monkeypatch, responder)

    scores = meeting.evaluate(RunContext(state))

    assert len(scores) == 4 and len(requests) == 10
    assert Counter(request["_node"] for request in requests) == Counter({phase: 2 for phase in PHASES})
    for request in requests:
        assert request["tier"] == "T3"
        assert "{{" not in request["user"]
        for supplied in ("USER_OBSERVATION_371", "CONFIRMED_OBSERVATION_728", "EV_EXTERNAL_265",
                         "FIELD_EVIDENCE_692", "ORGANIZATIONAL_BUSINESS", "행위자·정보·권한·유인"):
            assert supplied in request["user"]
        assert "HIDDEN_TRIZ_ORIGIN_813" not in request["user"]
        assert "HIDDEN_COMPETING_HYPOTHESIS_904" not in request["user"]

    saved = store.load_state(state.run_id)
    assert len(saved.steps) == 10
    assert len({step.step_id for step in saved.steps}) == 10
    for phase in PHASES:
        assert {step.agent_id for step in saved.steps if step.node == phase} == {"persona::A", "persona::B"}
    assert all(step.status == "OK" and step.tier == "T3" for step in saved.steps)
    assert saved.evaluation.meeting.status == "COMPLETED"
    assert len(saved.evaluation.meeting.final_reviews) == 2
    for final in saved.evaluation.meeting.final_reviews:
        step = next(step for step in saved.steps
                    if step.node == PHASES[-1] and step.agent_id == f"persona::{final.reviewer_id}")
        assert store.get_step(state.run_id, step.step_id)["output_json"]["communication_summary"]
        assert final.communication_summary[0].question_ids


@pytest.mark.parametrize("limit", ["budget", "deadline"])
def test_real_budget_and_deadline_stop_meeting_before_aggregation_or_model_call(meeting_case, monkeypatch, limit):
    state, responder, _ = meeting_case
    monkeypatch.setattr(agent, "run_agent", REAL_RUN_AGENT)
    if limit == "budget":
        state.cost.budget_usd = 0
        state.cost.total_usd = 1
        state.cost.over_budget = False  # Exercise tracked_chat reservation, not the earlier cached flag.
    else:
        state.scratch["execution_deadline"] = time.time() - 1
    reached = []
    monkeypatch.setattr(nodes, "_aggregate", lambda *args: reached.append("aggregate"))
    monkeypatch.setattr(nodes, "_rank", lambda *args: reached.append("rank"))

    with pytest.raises(AbortRun):
        nodes.s8_evaluate(RunContext(state))

    assert reached == [] and responder.calls == []
    assert not state.evaluation.meeting.completed_calls
    assert state.evaluation.meeting.status != "COMPLETED"
    assert state.evaluation.evaluations == [] and state.cost.request_count == 0


def test_regenerated_answer_invalidates_dependent_meeting_checkpoints(meeting_case, monkeypatch):
    state, responder, _ = meeting_case
    requests, revision = install_runtime(monkeypatch, responder)
    meeting.evaluate(RunContext(state))
    question_ids = [question.id for question in state.evaluation.meeting.questions]
    state.evaluation.meeting.completed_calls["answer_1:B"]["answers"][0]["answer"] = None
    # Simulate loss of the lower-level call cache while keeping durable meeting checkpoints.
    state.scratch["agent_cache"] = {}
    revision["answer"] = "Require two named approvers and a recorded rollback trigger."
    before = len(requests)

    meeting.evaluate(RunContext(state))

    retried = Counter((request["_node"], request["role_id"]) for request in requests[before:])
    expected = Counter({(PHASES[1], "B"): 1})
    expected.update({(phase, role): 1 for phase in PHASES[2:] for role in ("A", "B")})
    assert retried == expected
    assert [question.id for question in state.evaluation.meeting.questions] == question_ids
    assert all(final.communication_summary[0].summary == revision["answer"]
               for final in state.evaluation.meeting.final_reviews)


def test_real_agent_rechecks_cached_output_against_changed_checker_closure(state, monkeypatch):
    required = {"value": "initial policy"}
    generated = []

    def checker(data):
        return [] if data.get("value") == required["value"] else ["현재 검증 조건에 맞는 응답이 필요하다."]

    def chat(ctx, **kwargs):
        generated.append(required["value"])
        return SimpleNamespace(data={"value": required["value"]}, model="offline-cache-policy",
                               tokens_in=10, tokens_out=20, cost_usd=0.0)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    ctx = RunContext(state)
    arguments = dict(node="s8_review_cache_policy", label="검증 정책 확인", stage="S8",
                     agent_id="persona::policy", prompt_id="P_S8_REVIEW", vars={},
                     checker=checker, system_override="Return the requested JSON object.")
    assert REAL_RUN_AGENT(ctx, **arguments) == {"value": "initial policy"}
    original_keys = set(state.scratch["agent_cache"])

    # Source text, prompts and inputs stay identical; the closure's contract tightens.
    required["value"] = "current policy"
    assert REAL_RUN_AGENT(ctx, **arguments) == {"value": "current policy"}
    assert generated == ["initial policy", "current policy"]
    assert set(state.scratch["agent_cache"]) == original_keys
    assert state.steps[-1].status == "OK"

    # An output that satisfies the current checker remains safely reusable.
    assert REAL_RUN_AGENT(ctx, **arguments) == {"value": "current policy"}
    assert len(generated) == 2 and state.steps[-1].status == "SKIPPED"
