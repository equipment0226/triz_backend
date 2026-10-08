"""Offline regression cases for reviewer/schema disagreements seen in reruns.

These verify request delivery and structural compatibility, not live model
judgment accuracy. No model or production service is called.
"""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_checks, verification_contract as contract
from triz.analysis_guidance import analysis_guidance
from triz.context import RunContext
from triz.settings import settings


def settlement_model(level="INSUFFICIENT"):
    # A rule performs a useful but currently insufficient action on a record.
    # A corrective action with the same carrier does not create another BASIC.
    return {
        "components": [
            {"name": "정산 규칙", "level": "SUB", "role": "사용 내역을 청구 금액으로 변환하는 규칙"},
            {"name": "참여자별 정산 내역", "level": "PRODUCT", "role": "산정 결과가 기록되는 처리 대상"},
        ],
        "function_edges": [
            {"subject": "정산 규칙", "action": "사용 내역에 따라 부담액을 산정한다",
             "object": "참여자별 정산 내역", "parameter_affected": "청구 금액",
             "kind": "USEFUL", "rank": "BASIC", "level": level},
            {"subject": "정산 규칙", "action": "중복 청구 항목을 차단한다",
             "object": "참여자별 정산 내역", "parameter_affected": "중복 청구 건수",
             "kind": "USEFUL", "rank": "CORRECTIVE", "level": "INSUFFICIENT"},
        ],
        "interaction_cells": [], "mermaid": "",
    }


@pytest.mark.parametrize("level", ["INSUFFICIENT", "NORMAL", "EXCESSIVE"])
def test_corrected_teaching_model_preserves_product_direction_carrier_and_level(level):
    artifact = settlement_model(level)
    assert analysis_checks.function_model(artifact) == []
    basics = [e for e in artifact["function_edges"] if e["rank"] == "BASIC"]
    assert len(basics) == 1 and basics[0]["object"] == "참여자별 정산 내역"


@pytest.mark.parametrize("field,value,expected", [
    ("object", "참여자의 보상 경쟁력", "FATAL-FUNC"),
    ("action", "관리한다", "DET-05d"),
    ("kind", "HARMFUL", "FATAL-BASIC"),
])
def test_calibration_does_not_allow_invalid_reviewer_suggestions(field, value, expected):
    artifact = settlement_model()
    artifact["function_edges"][0][field] = value
    assert any(expected in issue for issue in analysis_checks.function_model(artifact))


@pytest.mark.parametrize("rubric_id,node,required_fragment", [
    ("R3_NW", "s3_nine_windows", "사용자가 준 개입 전후 기준값"),
    ("R3_FUNC", "s3_function_model", "PRODUCT가 object인 방향은 정상"),
    ("R3_RES", "s3_resources", "문체 완벽성 점수가 아니다"),
])
def test_old_pinned_verifier_receives_current_calibration_and_full_guidance(
        state, monkeypatch, rubric_id, node, required_fragment):
    from triz.ax import runtime
    old = deepcopy(settings.rubric(rubric_id))
    for row in old["criteria"]:
        row["text"] = "OLD_PINNED_CRITERION"
    snapshot = deepcopy(old)
    monkeypatch.setattr(settings, "rubric", lambda key: old)
    # Simulate a frozen old template lacking all newly introduced instructions.
    monkeypatch.setattr(runtime, "render_prompt", lambda *args, **kwargs: "OLD_PINNED_VERIFIER")
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    captured = []

    def chat(ctx, **kwargs):
        captured.append(kwargs["user"])
        if 'focused semantic auditor' in kwargs['system']:
            from triz.analysis_semantic_gate import RULES
            return SimpleNamespace(data={'checks': [{'id': key, 'status': 'PASS',
                'reason': 'offline calibration fixture', 'findings': []} for key in RULES[rubric_id]]},
                tokens_in=0, tokens_out=0, cost_usd=0.)
        rb = contract.effective_rubric(settings, rubric_id)
        return SimpleNamespace(
            data={"verdict": "PASS", "per_criterion": [
                {"id": c["id"], "score": 1., "evidence": "offline supported fixture"}
                for c in rb["criteria"]], "revision_instructions": [], "element_findings": []},
            tokens_in=0, tokens_out=0, cost_usd=0.)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    verdict = agent.verify_artifact(RunContext(state), rubric_id, {}, "")
    assert verdict["verdict"] == "PASS"
    assert captured[0].startswith("OLD_PINNED_VERIFIER")
    assert contract.verifier_supplement(contract.effective_rubric(settings, rubric_id)) in captured[0]
    assert analysis_guidance(state, node) in captured[0]
    assert required_fragment in captured[0]
    assert "1(충족)/0(실제 위반)" in captured[0]
    assert old == snapshot


def test_better_calibration_never_automatically_promotes_a_fractional_required_score():
    rb = contract.effective_rubric(settings, "R3_RES")
    verdict = {"verdict": "PASS", "per_criterion": [
        {"id": c["id"], "score": .9 if c.get("required") else 1.,
         "evidence": "Reviewer must decide against actual source evidence"}
        for c in rb["criteria"]], "revision_instructions": [], "element_findings": []}
    actual = contract.normalize_verdict(verdict, rb)
    assert actual["verdict"] != "PASS"
    assert any("C1" in issue for issue in actual["revision_instructions"])
