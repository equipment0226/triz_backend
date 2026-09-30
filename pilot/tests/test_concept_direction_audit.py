"""Offline regressions for the text actually shown in concept summaries.

The auditor is stubbed deliberately: these tests establish what reaches review,
how changed text invalidates prior review, and how its verdict is retained. They
do not claim to measure a model's engineering judgment.
"""
import copy
import json
from unittest.mock import Mock

import pytest

from triz import agent, llm, nodes, quality, render, store
from triz.context import RunContext
from triz.schema import ConceptEvaluation, ConceptSpec, RawIdea


def _candidate(state):
    concept = ConceptSpec(
        id="C-DIRECTION",
        title="구간별 회전 속도 조정",
        source_idea_ids=["IDEA-ROTATION"],
        intervention_variable="가속 시간(s), 최고 각속도(rad/s), 정착 시간(s)",
        one_liner="가속 시간·정착 시간은 줄이고 최고 각속도는 높여 takt 50초 이하를 목표로 한다.",
        description="가속 시간을 단축하고 최고 각속도를 높인다. 정착 시간은 진동 한계 안에서 단축한다.",
        working_principle="구간별 속도 프로파일 조정으로 직렬 공정 소요 시간을 줄인다.",
        addresses_contradictions=["TC-ROTATION"],
        resolution_argument="시간 단축과 정렬 정밀도의 양립은 진동·토크 한계 내에서 검증한다.",
        expected_effect="takt 50초 이하 목표. 실측 결과는 아직 없다.",
        assumptions=["모터 토크와 잔류 진동 한계를 준수한다."],
        validation_plan=[{"experiment": "단계별 takt와 잔류 진동을 측정한다.",
                          "failure_criterion": "정렬 정밀도 또는 토크 한계 초과"}],
    )
    state.concepts = [concept]
    return concept


def _pass(data):
    return {"verdict": "PASS", "per_concept": [
        {"concept_id": row["concept_id"], "verdict": "PASS"}
        for row in data["concepts"]]}


def test_user_visible_summary_and_parameter_context_reach_independent_review(state, monkeypatch):
    concept = _candidate(state)
    seen = []

    def audit(ctx, rubric, data, instruction):
        assert rubric == "R6_CONCEPT"
        seen.extend(copy.deepcopy(data["concepts"]))
        return _pass(data)

    monkeypatch.setattr(agent, "verify_artifact", audit)
    quality.audit_concepts(RunContext(state))

    assert len(seen) == 1
    for field in ("one_liner", "description", "intervention_variable", "source_idea_ids",
                  "working_principle", "expected_effect", "assumptions", "validation_plan"):
        assert seen[0][field] == getattr(concept, field)
        assert state.steps[-1].input_slice["concepts"][0][field] == getattr(concept, field)


@pytest.mark.parametrize(("field", "changed"), [
    ("one_liner", "가속 시간·최고 각속도·정착 시간을 모두 늘려 takt 50초 이하를 달성한다."),
    ("description", "다른 조건은 유지하고 가속 시간을 늘린다."),
    ("intervention_variable", "가속도(rad/s²), 최고 각속도(rad/s), 정착 시간(s)"),
    ("source_idea_ids", ["IDEA-OTHER-SOURCE"]),
])
def test_summary_or_parameter_context_change_invalidates_prior_audit(state, monkeypatch, field, changed):
    concept = _candidate(state)
    calls = []

    def audit(ctx, rubric, data, instruction):
        calls.append(copy.deepcopy(data))
        return _pass(data)

    monkeypatch.setattr(agent, "verify_artifact", audit)
    ctx = RunContext(state)
    quality.audit_concepts(ctx)
    first_hash = state.steps[-1].input_slice["input_hash"]
    quality.audit_concepts(ctx)
    assert len(calls) == 1
    assert state.steps[-1].status == "SKIPPED"

    setattr(concept, field, changed)
    quality.audit_concepts(ctx)
    assert len(calls) == 2
    assert calls[-1]["concepts"][0][field] == changed
    assert state.steps[-1].input_slice["input_hash"] != first_hash
    assert state.steps[-1].status != "SKIPPED"


@pytest.mark.parametrize("overall_verdict", ["PASS", "REVISE"])
def test_direction_revision_survives_storage_and_cached_review_without_self_approval(
        state, monkeypatch, overall_verdict):
    concept = _candidate(state)
    concept.one_liner = "가속 시간·최고 각속도·정착 시간을 모두 늘려 takt를 단축한다."
    issue = "요약의 가속 시간·정착 시간 증가가 본문의 단축 방향과 반대다. 변수별로 수정이 필요하다."
    calls = []

    def audit(ctx, rubric, data, instruction):
        calls.append(copy.deepcopy(data))
        assert data["concepts"][0]["one_liner"] == concept.one_liner
        # A passing portfolio score must not override a candidate's located flaw.
        return {"verdict": overall_verdict, "per_concept": [{
            "concept_id": concept.id, "verdict": "REVISE", "issues": [issue]}]}

    monkeypatch.setattr(agent, "verify_artifact", audit)
    quality.audit_concepts(RunContext(state))
    restored = store.load_state(state.run_id)
    assert restored.concepts[0].quality_status == "REVISE"
    assert issue in restored.concepts[0].quality_issues
    assert restored.steps[-1].output_json["per_concept"][0]["verdict"] == "REVISE"
    if overall_verdict == "REVISE":
        assert restored.steps[-1].status == "WARN"

    quality.audit_concepts(RunContext(restored))
    assert len(calls) == 1
    assert restored.steps[-1].status == "SKIPPED"
    assert restored.concepts[0].quality_status == "REVISE"
    assert issue in restored.concepts[0].quality_issues
    assert restored.concepts[0].one_liner == concept.one_liner


def test_valid_opposite_directions_by_condition_are_not_rewritten(state, monkeypatch):
    concept = _candidate(state)
    concept.one_liner = "공진 구간에서는 가속 시간을 늘리고, 비공진 구간에서는 줄여 총 소요 시간 단축을 검증한다."
    concept.description = (
        "공진 구간의 가속 시간은 2초에서 3초로 늘리는 시험 조건이다. "
        "비공진 구간의 가속 시간은 5초에서 2초로 줄이는 시험 조건이다. "
        "총 takt 50초 이하는 목표이며 아직 측정하지 않았다."
    )
    before = concept.model_dump(mode="json")
    packets = []

    def audit(ctx, rubric, data, instruction):
        packets.extend(copy.deepcopy(data["concepts"]))
        return _pass(data)

    monkeypatch.setattr(agent, "verify_artifact", audit)
    quality.audit_concepts(RunContext(state))

    assert packets[0]["one_liner"] == before["one_liner"]
    assert packets[0]["description"] == before["description"]
    assert concept.quality_status == "PASS"
    after = concept.model_dump(mode="json")
    assert {key: value for key, value in after.items() if key not in ("quality_status", "quality_issues")} == {
        key: value for key, value in before.items() if key not in ("quality_status", "quality_issues")}


def test_source_proposal_change_invalidates_review_without_changing_concept_text(state, monkeypatch):
    concept = _candidate(state)
    source = RawIdea(
        id=concept.source_idea_ids[0],
        idea="정착 시간을 줄이고 최고 각속도를 높이는 프로파일을 검증한다.",
        mechanism="회전 구간의 속도 프로파일 조정",
        intervention_variable="최고 각속도(rad/s), 정착 시간(s)",
        conditions=["정렬 정밀도와 토크 한계를 준수한다."],
        strongest_objection="원안의 가속 시간 증가 표현이 다른 원안의 단축 방향과 충돌하므로 운전 조건 확인이 필요하다.",
        validation_test="구간별 시간과 잔류 진동을 측정한다.",
    )
    unrelated = RawIdea(id="IDEA-UNRELATED", idea="별도 냉각 회로를 변경한다.")
    state.solve.raw_ideas = [source, unrelated]
    calls = []

    def audit(ctx, rubric, data, instruction):
        calls.append(copy.deepcopy(data))
        return _pass(data)

    monkeypatch.setattr(agent, "verify_artifact", audit)
    ctx = RunContext(state)
    quality.audit_concepts(ctx)
    first_hash = state.steps[-1].input_slice["input_hash"]
    expected = {field: getattr(source, field) for field in (
        "id", "idea", "mechanism", "intervention_variable", "conditions", "strongest_objection", "validation_test")}
    assert calls[0]["concepts"][0]["source_proposals"] == [expected]
    original_concept = concept.model_dump(mode="json")

    unrelated.idea = "별도 냉각 회로의 유량을 조정한다."
    quality.audit_concepts(ctx)
    assert len(calls) == 1
    assert state.steps[-1].status == "SKIPPED"

    source.idea = "공진 구간에서는 가속 시간을 늘려 잔류 진동 감소 가능성을 검증한다."
    quality.audit_concepts(ctx)
    assert len(calls) == 2
    assert calls[-1]["concepts"][0]["source_proposals"][0]["idea"] == source.idea
    assert state.steps[-1].input_slice["input_hash"] != first_hash
    assert state.steps[-1].status != "SKIPPED"
    assert concept.model_dump(mode="json") == original_concept


def test_legacy_report_prompt_receives_body_and_review_issues_with_summary(state, monkeypatch):
    concept = _candidate(state)
    concept.one_liner = "가속 시간·최고 각속도·정착 시간을 모두 늘려 takt를 단축한다."
    concept.changes_to_system = ["가속 시간과 정착 시간을 구간별로 줄인다."]
    concept.quality_status = "REVISE"
    concept.quality_issues = ["서브타이틀의 시간 증가 표현이 본문의 단축 방향과 반대다."]
    state.evaluation.evaluations = [ConceptEvaluation(
        concept_id=concept.id, total_score=3.5, rank=1)]
    narrative = {"executive_summary": "변수별 증감 방향의 수정이 필요한 후보다."}
    chat = Mock(return_value=llm.LLMResult(
        data=narrative, text=json.dumps(narrative, ensure_ascii=False),
        model="offline-test", tokens_in=0, tokens_out=0, cost_usd=0))
    monkeypatch.setattr(llm, "chat_json", chat)
    monkeypatch.setattr(render, "render_report", lambda *args, **kwargs: "offline report")
    monkeypatch.setattr(render, "save", lambda *args, **kwargs: None)

    nodes.s9_report(RunContext(state))

    chat.assert_called_once()
    step = next(step for step in state.steps if step.node == "s9_narrative")
    assert step.prompt_id == "P_S9_NARRATIVE"
    packet = step.input_slice["vars"]["top_concepts"][0]
    for field in ("one_liner", "description", "working_principle", "changes_to_system",
                  "quality_issues", "expected_effect"):
        value = getattr(concept, field)
        assert packet[field] == value
        for text in value if isinstance(value, list) else [value]:
            assert text in chat.call_args.kwargs["user"]
    assert concept.quality_status == "REVISE"
    assert state.report.narrative == narrative
