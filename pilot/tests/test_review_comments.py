from copy import deepcopy

from triz import presentation, render, review_comments
from triz.schema import ConceptEvaluation, ConceptSpec, MeetingFinalReview, ReviewerScore


def populate(state):
    state.concepts = [ConceptSpec(id="C1", title="Approval pilot", quality_status="PASS")]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id="C1", scores=[
        ReviewerScore(concept_id="C1", reviewer_role="Operations", dimension=dim,
                      score=3, rationale=f"{dim}: A reversible pilot is feasible. A repeated paragraph.",
                      improvement_suggestion="Validate approval ownership first.")
        for dim in ("TIME", "COST", "FEASIBILITY")])]


def test_existing_independent_reviews_are_one_comment_per_role_in_cards_and_both_reports(state):
    populate(state)
    original = deepcopy(state.model_dump())
    comments = review_comments.by_concept(state)["C1"]
    assert len(comments) == 1 and comments[0]["role"] == "Operations"
    assert "Validate approval ownership" in comments[0]["comment"]
    assert "repeated paragraph" not in comments[0]["comment"]
    card = presentation.view(state)["solutions"][0]
    assert card["reviewer_comments"] == comments
    for template in ("report_full.md.j2", "report_lite.md.j2"):
        report = render.render_report(state, {}, template=template)
        assert report.count("| Operations |") == 1
        assert "| 검토자 | 최종 의견 |" in report
        assert "| 검토자 | 관점 | 점수 | 의견 |" not in report
    # report_state adds scratch display metadata on a copy, never rewrites evaluations.
    assert state.evaluation.model_dump() == original["evaluation"]


def test_authored_role_conclusion_is_shared_and_safety_veto_cannot_be_hidden(state):
    populate(state)
    state.evaluation.meeting.final_reviews = [MeetingFinalReview(
        reviewer_id="A", reviewer_role="Operations", scores=state.evaluation.evaluations[0].scores,
        communication_summary=[], concept_comments={"C1": "Adopt after owner approval, as clarified by the field reviewer."})]
    assert "field reviewer" in review_comments.by_concept(state)["C1"][0]["comment"]
    state.evaluation.evaluations[0].scores.append(ReviewerScore(
        concept_id="C1", reviewer_role="Operations", dimension="SAFETY", score=1,
        rationale="Deployment is blocked.", red_flags=["Required safety approval is missing."]))
    comment = review_comments.by_concept(state)["C1"][0]["comment"]
    assert "blocked" in comment and "safety approval is missing" in comment
    assert "Adopt after" not in comment


def test_missing_optional_comment_field_is_backward_compatible(state):
    populate(state)
    final = MeetingFinalReview.model_validate(dict(reviewer_id="A",reviewer_role="Operations",
        scores=[],communication_summary=[]))
    state.evaluation.meeting.final_reviews = [final]
    assert review_comments.by_concept(state)["C1"]
