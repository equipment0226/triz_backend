"""Preserve primary reports and qualifiers without authenticating AI summaries."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, digest, verification_contract as contract
from triz.context import RunContext
from triz.schema import ClarifyTurn, Component, FunctionEdge, SystemCandidate
from triz.settings import settings


def opinion_with_unsupported_history(state):
    state.raw_query = "성과를 공개해서 모두 납득하게 한다는 접근은 현실에서 작동하지 않습니다."
    state.intake.frame.prior_attempts = ["성과 투명 공개를 시도했으나 실패했다"]
    state.scratch["deep_dive"] = {
        "confirmed_facts": ["성과 공개 시도는 이미 실패했다"],
        "answers": ["금전적·비금전적 요인이 복합적"],
        "answer_turns": [{"question": "이직 동기는 무엇인가요?", "answer": "금전적·비금전적 요인이 복합적"}],
    }
    state.intake.clarify_turns = [ClarifyTurn(
        question="최대 인상 가능 범위는?", user_answer="현재 연봉의 10% 이내", answered=True)]


def test_generated_prior_attempts_and_confirmed_facts_are_not_primary_observations(state):
    opinion_with_unsupported_history(state)
    before = deepcopy(state.model_dump())
    packet = digest.facts_packet(state)
    # Existing API paths/values remain reviewable, not silently erased/reclassified.
    assert packet["frame"]["prior_attempts"] == state.intake.frame.prior_attempts
    assert packet["confirmed_facts"] == state.scratch["deep_dive"]["confirmed_facts"]
    assert packet["user_query"] == state.raw_query
    assert packet["answers"] == digest.clarify_history(state)
    assert packet["deep_dive_answers"] == state.scratch["deep_dive"]["answers"]
    assert packet["deep_dive_answer_turns"] == state.scratch["deep_dive"]["answer_turns"]
    assert packet["source_contract"]["generated_summary_paths"] == ["frame", "confirmed_facts"]
    assert not {"frame", "confirmed_facts"} & set(packet["source_contract"]["direct_report_paths"])
    assert packet["source_provenance"]["frame"] == "MODEL_GENERATED_SUMMARY_NOT_DIRECT_OBSERVATION"
    assert packet["source_provenance"]["confirmed_facts"] == "MODEL_GENERATED_SYNTHESIS_REQUIRES_PRIMARY_SUPPORT"
    assert state.model_dump() == before


def test_actual_user_reported_trial_is_preserved_even_when_summary_conflicts(state):
    opinion_with_unsupported_history(state)
    state.raw_query = "지난달 성과 공개를 실제로 시도했지만 노조 반발로 중단했습니다."
    state.intake.clarify_turns.append(ClarifyTurn(
        question="실제 시도 여부는?", user_answer="지난달 실제 시행했습니다", answered=True))
    state.intake.frame.prior_attempts = ["시도 이력 미확인"]
    packet = digest.facts_packet(state)
    assert "실제로 시도" in packet["user_query"]
    assert "지난달 실제 시행" in packet["answers"][-1]
    assert packet["source_provenance"]["user_query"] == "USER_REPORTED"
    assert packet["frame"]["prior_attempts"] == ["시도 이력 미확인"]


def test_boundary_definition_provenance_requires_actual_user_confirmation(state):
    candidate = SystemCandidate(name="보상 규칙", description="기준과 절차를 정의한다")
    state.confirm.candidates = [candidate]
    state.confirm.chosen_candidate_id = candidate.id
    state.confirm.user_confirmed = False
    assert digest.facts_packet(state)["source_provenance"]["confirmed_boundary"] == "MODEL_PROPOSED_BOUNDARY"
    state.confirm.user_confirmed = True
    assert digest.facts_packet(state)["source_provenance"]["confirmed_boundary"] == "USER_CONFIRMED_DEFINITION_NOT_EVENT_OBSERVATION"


def test_source_priority_reaches_both_generation_and_pinned_verifier(state, monkeypatch):
    from triz.ax import runtime
    opinion_with_unsupported_history(state)
    generation = contract.generation_supplement(state, "s3_nine_windows")
    captured = []
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    monkeypatch.setattr(runtime, "render_prompt", lambda state, prompt, **values:
                        "LEGACY_PROMPT " + str(values))

    def chat(ctx, **kwargs):
        captured.append(kwargs["user"])
        rb = contract.effective_rubric(settings, "R3_NW")
        return SimpleNamespace(data={"verdict": "PASS", "per_criterion": [
            {"id": c["id"], "score": 1.} for c in rb["criteria"]]},
            tokens_in=0, tokens_out=0, cost_usd=0.)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    agent.verify_artifact(RunContext(state), "R3_NW", {"cells": {}, "insights": []}, "")
    for request in [generation, captured[0]]:
        assert "MODEL_GENERATED_SUMMARY_NOT_DIRECT_OBSERVATION" in request
        assert "MODEL_GENERATED_SYNTHESIS_REQUIRES_PRIMARY_SUPPORT" in request
        assert state.raw_query in request
        assert "현재 연봉의 10% 이내" in request
        assert "시도·실패" in request


@pytest.mark.parametrize("status", ["HYPOTHESIS", "DERIVED", "OBSERVED"])
def test_function_and_basic_digests_keep_notes_and_evidence_independent_of_level(state, status):
    state.analysis.components = [
        Component(name="정산 규칙", level="TARGET", role="금액 산정"),
        Component(name="정산 기록", level="PRODUCT", role="산정 결과"),
    ]
    edge = FunctionEdge(subject="정산 규칙", action="금액을 산정한다", object="정산 기록",
        kind="USEFUL", level="INSUFFICIENT", rank="BASIC", parameter_affected="청구 금액",
        notes="가설 상태와 수행 부족은 별개이며 예외 처리 조건을 추가 확인한다.",
        evidence_status=status, evidence_refs=["observations.answers[0]: 금액 오산정 사례 보고"])
    state.analysis.function_edges = [edge]
    for text in [digest.function_digest(state)[0], digest.basic_function(state)]:
        assert status in text and edge.notes in text and edge.evidence_refs[0] in text
    assert state.analysis.function_edges[0].level == "INSUFFICIENT"


def test_hypothetical_harm_survives_function_digest_without_becoming_observed(state):
    state.analysis.function_edges = [FunctionEdge(
        subject="고객 IT 팀", action="복제할 수 있다", object="모델",
        kind="HARMFUL", level="NORMAL", rank="AUXILIARY", parameter_affected="기밀성",
        evidence_status="HYPOTHESIS", notes="이번 건의 실제 복제는 미확인",
        evidence_refs=["observations.answers[0]: 자체 개발 가능성이 높다"])]
    text = digest.function_digest(state, only_problem=True)[0]
    assert "HYPOTHESIS" in text and "실제 복제는 미확인" in text
    assert "OBSERVED" not in text
