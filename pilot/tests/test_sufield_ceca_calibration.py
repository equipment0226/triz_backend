"""Offline coverage of corrected physical roles and cause-graph direction."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_checks, verify, verification_contract as contract
from triz.analysis_guidance import analysis_guidance
from triz.context import RunContext
from triz.settings import settings


@pytest.mark.parametrize("effect", ["USEFUL_SUFFICIENT", "HARMFUL", "EXCESSIVE"])
def test_one_real_carrier_can_have_distinct_effect_models_without_role_reversal(effect):
    # Physical carrier stays a clamp, never the load/stress that it transmits.
    model = {"label": "같은 압착 조건의 접촉/손상 작용을 구별",
             "s1": "접촉 시편", "s2": "클램프", "s3": "", "field": "Me",
             "completeness": "COMPLETE", "effect": effect, "diagram_mermaid": ""}
    assert analysis_checks.sufields({"su_fields": [model]}) == []
    assert model["s2"] == "클램프"


def cause_graph():
    return {"nodes": [
        {"id": key, "text": text, "node_type": kind, "parents": parents,
         "logic": "OR" if key in ("N3", "N4") else "NONE",
         "evidence_status": "HYPOTHESIS", "evidence_refs": [],
         "falsification_test": "비교 집단의 이직 의도와 실제 이탈을 측정해 연결 가설을 반증한다"}
        for key, text, kind, parents in [
            ("N1", "핵심 인재 이탈 손실", "TARGET_DISADVANTAGE", []),
            ("N2", "이직 의도가 높아질 가능성", "INTERMEDIATE", ["N1"]),
            ("N3", "보상 격차가 의도에 영향을 줄 가능성", "ROOT_CAUSE", ["N2"]),
            ("N4", "성장 기회 제약이 의도에 영향을 줄 가능성", "ROOT_CAUSE", ["N2"]),
        ]], "mermaid": ""}


def test_alternative_causes_point_to_effect_and_bad_reviewer_reversal_is_rejected():
    valid = cause_graph()
    assert verify.check_ceca(valid) == []
    bad = deepcopy(valid)
    bad["nodes"][1]["parents"] = ["N3", "N4"]
    issues = verify.check_ceca(bad)
    assert any("순환" in issue for issue in issues)
    assert any("연결" in issue for issue in issues)
    # Minimal repair restores the effect reference; it does not remove causes.
    bad["nodes"][1]["parents"] = ["N1"]
    assert verify.check_ceca(bad) == []
    assert bad == valid


@pytest.mark.parametrize("rubric,node,fragment", [
    ("R3_SUF", "s3_sufield", "클램핑 하중·계면 전단응력·열사이클 부하"),
    ("R3_CECA", "s3_ceca", "N2.parents를 [N3,N4]로 바꾸지 않는다"),
])
def test_physical_and_graph_contracts_reach_old_pinned_generation_and_verification(
        state, monkeypatch, rubric, node, fragment):
    from triz.ax import runtime
    captured = []
    monkeypatch.setattr(runtime, "render_prompt", lambda *args, **kwargs: "PINNED_OLD_BODY")
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)

    def chat(ctx, **kwargs):
        captured.append(kwargs["user"])
        rb = contract.effective_rubric(settings, rubric)
        return SimpleNamespace(data={"verdict": "PASS", "per_criterion": [
            {"id": row["id"], "score": 1.} for row in rb["criteria"]]},
            tokens_in=0, tokens_out=0, cost_usd=0.)

    monkeypatch.setattr(agent, "tracked_chat", chat)
    agent.verify_artifact(RunContext(state), rubric, {}, "")
    for request in [contract.generation_supplement(state, node), captured[0]]:
        assert analysis_guidance(state, node) in request
        assert fragment in request
    if node == "s3_ceca":
        repair = contract.repair_supplement({"revision_instructions": ["N2.parents를 고쳐라"]})
        assert "N2.parents=[N1]" in repair and "N1.parents에 N2를 역추가하지 않는다" in repair
