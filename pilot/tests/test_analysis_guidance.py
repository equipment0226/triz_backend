"""Offline contracts for source-guided, bounded analysis prompts.

These tests validate routing, context fidelity and configuration, not whether a
model has learned TRIZ or whether a proposed physical solution actually works.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from triz.analysis_guidance import (
    ANALYSIS_CONTRACT_VERSION, MAX_GUIDANCE_CHARS, analysis_guidance,
)
from triz import prompts_registry as P
from triz.schema import GlobalState

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads(
    (ROOT / "triz/knowledge/analysis_guidance_v1.json").read_text(encoding="utf-8")
)


def state_for(kind="PHYSICAL_TECHNICAL", boundary="Conveyor", **domain):
    return {
        "run_id": "local-guidance-fixture",
        "domain": {"problem_type": kind, "target_system": "Unselected factory", **domain},
        "confirm": {
            "user_confirmed": True,
            "chosen_candidate_id": "selected",
            "candidates": [
                {"id": "wrong", "name": "Unselected factory", "description": "Wrong scope"},
                {"id": "selected", "name": boundary, "description": "Selected module"},
            ],
            "user_amendments": ["Only the selected module"],
        },
        "raw_query": "PRIVATE_RAW_QUERY_MUST_NOT_BE_COPIED",
    }


def test_same_confirmed_context_for_dict_and_typed_state_without_mutation():
    state = state_for(boundary="Seal interface")
    before = deepcopy(state)
    typed = GlobalState.model_validate(state)
    typed_before = typed.model_dump(mode="json")
    expected = analysis_guidance(state, "s3_function_model")
    assert analysis_guidance(typed, "s3_function_model") == expected
    assert "Seal interface" in expected
    assert "Only the selected module" in expected
    assert "FN_SEAL_SCOPE" in expected
    assert "Unselected factory" not in expected
    assert "PRIVATE_RAW_QUERY" not in expected
    assert state == before and typed.model_dump(mode="json") == typed_before


def test_invalid_choice_does_not_silently_adopt_first_candidate():
    state = state_for(boundary="Seal interface")
    state["confirm"]["chosen_candidate_id"] = "not-present"
    text = analysis_guidance(state, "s3_function_model")
    assert "Seal interface" not in text and "Unselected factory" not in text
    assert "미확정" in text
    assert "FN_SEAL_SCOPE" not in text


def test_unconfirmed_choice_is_not_promoted_to_confirmed_boundary():
    state = state_for(boundary="Seal interface")
    state["confirm"]["user_confirmed"] = False
    text = analysis_guidance(state, "s3_function_model")
    assert "Seal interface" not in text and "미확정" in text
    assert "FN_SEAL_SCOPE" not in text


@pytest.mark.parametrize("kind,example", [
    ("PHYSICAL_TECHNICAL", "FN_TRANSPORT"),
    ("INFORMATION_SOFTWARE", "FN_SOFTWARE"),
    ("ORGANIZATIONAL_BUSINESS", "FN_ORGANIZATION"),
])
def test_examples_follow_problem_type_not_incidental_raw_keywords(kind, example):
    state = state_for(kind=kind, boundary="Selected module")
    state["raw_query"] = "seal sealing seal seal"
    text = analysis_guidance(state, "s3_function_model")
    assert example in text and "FN_SEAL_SCOPE" not in text


def test_mixed_physical_scope_is_explicit_and_does_not_reclassify_whole_project():
    state = state_for(kind="MIXED", boundary="Approvals and cooling", physical_scope="Heat exchanger only")
    physical = analysis_guidance(state, "s3_sufield")
    whole = analysis_guidance(state, "s3_function_model")
    assert "Heat exchanger only" in physical and "SU_HEAT" in physical
    assert "이 범위 안에만" in physical
    assert "FN_TRANSPORT" not in whole

    state["domain"]["physical_scope"] = ""
    missing = analysis_guidance(state, "s3_sufield")
    assert "미확인" in missing and "SU_NONPHYSICAL" in missing
    assert "SU_HEAT" not in missing


def test_long_boundary_data_keeps_current_amendments_and_required_guidance_bounded():
    state = state_for(boundary="boundary " * 10000, physical_scope="scope " * 10000)
    state["confirm"]["candidates"][1]["description"] = "description " * 10000
    state["confirm"]["user_amendments"] = ["obsolete"] * 100 + ["last-one", "latest-two"]
    for node in CATALOG["stages"]:
        text = analysis_guidance(state, node)
        assert len(text) <= MAX_GUIDANCE_CHARS
        assert "latest-two" in text and "obsolete" not in text
        assert CATALOG["stages"][node] in text
        assert ANALYSIS_CONTRACT_VERSION in text


def test_unknown_node_is_empty_without_serializing_input():
    class Trap:
        def __getattribute__(self, name):
            raise AssertionError("Unrelated node should not inspect state")
    assert analysis_guidance(Trap(), "s8_report") == ""


def test_static_catalog_distinguishes_application_conventions_and_primary_sources():
    assert CATALOG["version"] == ANALYSIS_CONTRACT_VERSION
    assert CATALOG["sources"]
    assert all(row["url"].startswith("https://wiki.matriz.org/") for row in CATALOG["sources"])
    assert any("Formal MATRIZ" in text for text in CATALOG["application_conventions"])
    ids = [row["id"] for row in CATALOG["examples"]]
    assert len(ids) == len(set(ids))
    assert all(row["incorrect"] != row["correct"] for row in CATALOG["examples"])
    assert all(set(row["nodes"]) <= CATALOG["stages"].keys() for row in CATALOG["examples"])


def test_every_analysis_rubric_has_specific_mandatory_semantics_not_all_perfect_scores():
    data = yaml.safe_load((ROOT / "config/rubrics.yaml").read_text(encoding="utf-8"))
    expected = {
        "R3_NW", "R3_FUNC", "R3_SUF", "R3_RES", "R3_CECA", "R3_CONSTRAINT",
        "R4_IFR", "R4_CONTRA", "R4_TRIM", "R4_KEY",
    }
    for rubric in expected:
        rows = data[rubric]["criteria"]
        critical = [row for row in rows if row.get("required")]
        assert critical and len(critical) < len(rows), rubric
        assert all(row["min_score"] == 1.0 for row in critical)
        assert sum(row["weight"] for row in rows) == pytest.approx(1.0)
        assert len({row["id"] for row in rows}) == len(rows)
    c1 = next(row for row in data["R3_FUNC"]["criteria"] if row["id"] == "C1")
    assert c1["required"] and "경계" in c1["text"] and "개수만" in c1["text"]


@pytest.mark.parametrize("prompt_id", [
    "P_S3_NINE_WINDOWS", "P_S3_FUNCTION_MODEL", "P_S3_SUFIELD", "P_S3_RESOURCES",
    "P_S3_CECA", "P_S3_CONSTRAINTS", "P_S4_IFR", "P_S4_CONTRADICTIONS",
    "P_S4_TRIMMING", "P_S4_KEY_PROBLEM",
])
def test_prompt_schema_examples_are_json_objects_and_render_without_new_dependencies(prompt_id):
    body = P.raw(prompt_id)
    placeholders = set(P.VAR.findall(body))
    rendered = P.render(prompt_id, **{name: f"fixture_{name}" for name in placeholders})
    assert not P.VAR.search(rendered)
    example = rendered.split("[출력 JSON]", 1)[1].strip()
    parsed, _ = json.JSONDecoder().raw_decode(example)
    assert isinstance(parsed, dict) and parsed


def test_empty_resources_and_inapplicable_pc_have_explicit_explanations():
    assert '"unavailable_reason":""' in P.raw("P_S3_RESOURCES")
    contradiction = P.raw("P_S4_CONTRADICTIONS")
    assert '"physical_not_applicable_reason":""' in contradiction
    assert "같은 사전 번호로 매핑된다고 물리적 모순이 되는 것은 아니다" in contradiction


def test_repair_and_verifier_do_not_reward_sparse_patches_or_boundary_drift():
    repair = P.raw("P_REPAIR")
    verifier = P.raw("P_VERIFIER_GENERIC")
    assert "전체 완성 JSON" in repair
    assert "components, function_edges" in repair
    assert "검증 의견도 검토할 주장" in repair
    assert "required" in verifier and "min_score" in verifier and "PASS 금지" in verifier
    assert "최신 확정 경계" in verifier and "개수와 의미는 별개" in verifier
