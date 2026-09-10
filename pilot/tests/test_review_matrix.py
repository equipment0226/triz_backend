"""A completed meeting must retain every assigned assessment without extra votes."""
from copy import deepcopy

import pytest

from triz.verify import check_review


@pytest.fixture
def review():
    return {"scores": [
        {"concept_id": concept_id, "dimension": dimension, "score": 3,
         "confidence": 0.5, "rationale": "적용 조건을 실험으로 확인해야 한다.",
         "red_flags": [], "improvement_suggestion": "실패 조건을 먼저 확인한다."}
        for concept_id in ("A", "B") for dimension in ("GOAL", "SAFETY")
    ]}


def test_complete_matrix_accepts_equal_scores_and_optional_improvement(review):
    for row in review["scores"]:
        row.pop("improvement_suggestion")
    assert check_review(review, {"A", "B"}, ["GOAL", "SAFETY"]) == []


def test_each_concept_present_is_insufficient_when_safety_assessment_is_missing(review):
    review["scores"] = [row for row in review["scores"]
                        if not (row["concept_id"] == "B" and row["dimension"] == "SAFETY")]
    assert check_review(review, {"A", "B"}) == []
    issues = check_review(review, {"A", "B"}, ["GOAL", "SAFETY"])
    assert any("DET-R7" in issue and "B" in issue and "SAFETY" in issue for issue in issues)


def test_duplicate_vote_cannot_hide_a_missing_dimension_or_inflate_aggregation(review):
    review["scores"][-1] = deepcopy(review["scores"][-2])
    issues = check_review(review, {"A", "B"}, ["GOAL", "SAFETY"])
    assert any("DET-R7" in issue for issue in issues)
    assert any("DET-R8" in issue for issue in issues)


def test_foreign_concept_and_unassigned_dimension_are_not_extra_votes(review):
    review["scores"].append({**review["scores"][0], "concept_id": "OTHER", "dimension": "COST"})
    issues = check_review(review, {"A", "B"}, ["GOAL", "SAFETY"])
    assert any("DET-R1" in issue for issue in issues)
    assert any("DET-R9" in issue for issue in issues)


@pytest.mark.parametrize("field,value", [
    ("score", None), ("score", True), ("score", "3"), ("score", float("nan")),
    ("score", float("inf")), ("score", 0), ("score", 6),
    ("confidence", None), ("confidence", True), ("confidence", "0.5"),
    ("confidence", float("nan")), ("confidence", float("inf")),
    ("confidence", -0.1), ("confidence", 1.1),
    ("rationale", []), ("rationale", "  "),
    ("red_flags", "위험"), ("red_flags", [None]),
    ("improvement_suggestion", {"text": "확인"}),
])
def test_malformed_values_cannot_become_default_scores_or_validated_evidence(review, field, value):
    review["scores"][0][field] = value
    assert check_review(review, {"A", "B"}, ["GOAL", "SAFETY"])


@pytest.mark.parametrize("field", ["score", "confidence", "rationale", "red_flags"])
def test_missing_required_assessment_fields_are_not_filled_in(review, field):
    review["scores"][0].pop(field)
    assert check_review(review, {"A", "B"}, ["GOAL", "SAFETY"])


@pytest.mark.parametrize("payload", [None, [], {}, {"scores": {}}, {"scores": [None]},
                                     {"scores": [{"concept_id": [], "dimension": {}}]}])
def test_malformed_response_returns_repair_issues_instead_of_crashing(payload):
    assert check_review(payload, {"A"}, ["SAFETY"])
    assert check_review(payload, {"A"})


def test_boundary_scores_and_confidence_are_valid_and_legacy_callers_remain_supported(review):
    for index, row in enumerate(review["scores"]):
        row["score"] = 1 if index % 2 else 5
        row["confidence"] = 0 if index % 2 else 1
    assert check_review(review, {"A", "B"}, ["GOAL", "SAFETY"]) == []
    legacy = {"scores": [{"concept_id": "A", "score": "3", "rationale": "조건부 가능"}]}
    assert check_review(legacy, {"A"}) == []
    assert check_review(legacy, {"A", "B"})
