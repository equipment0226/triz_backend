"""A meeting may only cite real, addressed exchanges and supplied evidence."""
from copy import deepcopy

import pytest

from triz import agent, meeting, personas
from triz.context import AbortRun, RunContext
from triz.meeting import _check_answers, _check_final, _check_questions, _guard_veto
from triz.schema import EvaluationBundle, Persona, ReviewerScore, StepRecord


ROLE_IDS = {"reviewer", "peer", "observer"}
CONCEPT_IDS = {"concept", "alternative"}


@pytest.fixture
def role():
    return Persona(persona_id="reviewer", role_name="Operations", dimensions=["SAFETY"])


@pytest.fixture
def question():
    return {"to_role_id": "peer", "concept_id": "concept",
            "question": "How is the untested failure condition controlled?"}


@pytest.fixture
def inbox():
    return [{"question_id": "q1", "concept_id": "concept"},
            {"question_id": "q2", "concept_id": "alternative"}]


@pytest.fixture
def answers():
    return {"answers": [
        {"question_id": "q1", "answer": "The supplied pilot covers only normal operation.",
         "evidence_refs": ["e1"], "uncertainties": ["Failure recovery has not been tested."]},
        {"question_id": "q2", "answer": "No supporting observation is available.",
         "evidence_refs": [], "uncertainties": ["This is a peer hypothesis."]},
    ], "questions": []}


@pytest.fixture
def transcript():
    return [{"question": {"id": "q1", "from_role_id": "reviewer",
                          "to_role_id": "peer", "concept_id": "concept"},
             "answer": {"question_id": "q1", "answer": "Failure recovery is untested."}},
            {"question": {"id": "q2", "from_role_id": "peer",
                          "to_role_id": "observer", "concept_id": "alternative"},
             "answer": {"question_id": "q2", "answer": "Evidence is not available."}}]


@pytest.fixture
def final_review():
    return {"scores": [
        {"concept_id": cid, "dimension": "SAFETY", "score": 2, "confidence": 0.4,
         "rationale": "Failure recovery must be tested before adoption.", "red_flags": []}
        for cid in sorted(CONCEPT_IDS)
    ], "communication_summary": [{
        "concept_id": "concept", "peer_role_ids": ["peer"], "question_ids": ["q1"],
        "summary": "The other reviewer confirmed that the pilot did not test failure recovery.",
        "assessment_change": "The assessment remains conditional pending a recovery test.",
        "unresolved_issues": ["No recovery test is available."],
    }]}


def test_initial_question_is_addressed_to_an_actual_other_reviewer(question):
    assert _check_questions({"questions": [question]}, "reviewer", ROLE_IDS, CONCEPT_IDS, 2) == []


@pytest.mark.parametrize("field,value", [
    ("to_role_id", "reviewer"), ("to_role_id", "invented-role"),
    ("to_role_id", []), ("concept_id", "invented-concept"),
    ("concept_id", {}), ("question", "  "), ("question", []),
    ("reply_to_question_id", "q1"),
])
def test_invalid_initial_question_is_rejected(question, field, value):
    question[field] = value
    assert _check_questions({"questions": [question]}, "reviewer", ROLE_IDS, CONCEPT_IDS, 2)


@pytest.mark.parametrize("payload", [None, [], {}, {"questions": {}}, {"questions": [None]}])
def test_malformed_question_response_returns_issues(payload):
    assert _check_questions(payload, "reviewer", ROLE_IDS, CONCEPT_IDS, 2)


def test_question_budget_and_duplicates_are_rejected(question):
    assert _check_questions({"questions": []}, "reviewer", ROLE_IDS, CONCEPT_IDS, 2)
    assert _check_questions({"questions": [question, deepcopy(question)]},
                            "reviewer", ROLE_IDS, CONCEPT_IDS, 2)
    questions = [{**question, "question": f"How will condition {i} be checked?"} for i in range(3)]
    assert _check_questions({"questions": questions}, "reviewer", ROLE_IDS, CONCEPT_IDS, 2)


def test_followup_requires_an_answered_reference_for_the_same_concept(question):
    answered = {"q1": {"concept_id": "concept"}}
    question["reply_to_question_id"] = "q1"
    assert _check_questions({"questions": [question]}, "reviewer", ROLE_IDS,
                            CONCEPT_IDS, 2, answered) == []
    for ref, cid in [("", "concept"), ("unanswered-q", "concept"), ("q1", "alternative")]:
        question.update(reply_to_question_id=ref, concept_id=cid)
        assert _check_questions({"questions": [question]}, "reviewer", ROLE_IDS,
                                CONCEPT_IDS, 2, answered)


def test_all_inbox_questions_are_answered_with_scoped_evidence(inbox, answers):
    assert _check_answers(answers, inbox, {"e1": ["concept"]}) == []


@pytest.mark.parametrize("payload", [None, [], {}, {"answers": {}},
                                     {"answers": [None], "questions": []}])
def test_malformed_answer_response_returns_issues(payload, inbox):
    assert _check_answers(payload, inbox, {"e1": ["concept"]})


def test_missing_duplicate_and_foreign_answers_are_rejected(inbox, answers):
    missing = deepcopy(answers)
    missing["answers"].pop()
    assert _check_answers(missing, inbox, {"e1": ["concept"]})
    duplicate = deepcopy(answers)
    duplicate["answers"].append(deepcopy(duplicate["answers"][0]))
    assert _check_answers(duplicate, inbox, {"e1": ["concept"]})
    foreign = deepcopy(answers)
    foreign["answers"][0]["question_id"] = "someone-elses-question"
    assert _check_answers(foreign, inbox, {"e1": ["concept"]})


@pytest.mark.parametrize("evidence", [{}, {"e1": ["alternative"]}])
def test_answer_cannot_cite_missing_or_other_concept_evidence(inbox, answers, evidence):
    assert _check_answers(answers, inbox, evidence)


@pytest.mark.parametrize("field,value", [
    ("question_id", []), ("answer", ""), ("answer", {}),
    ("evidence_refs", "e1"), ("evidence_refs", [None]),
    ("uncertainties", None), ("uncertainties", [" "]),
])
def test_malformed_answer_fields_do_not_crash(inbox, answers, field, value):
    answers["answers"][0][field] = value
    assert _check_answers(answers, inbox, {"e1": ["concept"]})


def test_answer_phase_cannot_emit_followup_before_the_barrier(inbox, answers, question):
    answers["questions"] = [question]
    assert _check_answers(answers, inbox, {"e1": ["concept"]})


def test_final_review_can_keep_its_score_while_summarizing_a_real_peer_answer(role, transcript, final_review):
    assert _check_final(final_review, role, CONCEPT_IDS, transcript) == []


@pytest.mark.parametrize("field,value", [
    ("concept_id", "invented-concept"), ("concept_id", []),
    ("concept_id", "alternative"), ("question_ids", ["invented-question"]),
    ("question_ids", []), ("question_ids", [None]),
    ("peer_role_ids", ["invented-role"]), ("peer_role_ids", ["reviewer"]),
    ("peer_role_ids", ["observer"]), ("peer_role_ids", []),
    ("summary", "  "), ("assessment_change", {}), ("unresolved_issues", None),
])
def test_final_summary_rejects_foreign_references_and_malformed_fields(
        role, transcript, final_review, field, value):
    final_review["communication_summary"][0][field] = value
    assert _check_final(final_review, role, CONCEPT_IDS, transcript)


def test_final_review_must_summarize_at_least_one_exchange_it_participated_in(
        role, transcript, final_review):
    final_review["communication_summary"][0].update(
        concept_id="alternative", question_ids=["q2"], peer_role_ids=["peer", "observer"])
    assert _check_final(final_review, role, CONCEPT_IDS, transcript)


@pytest.mark.parametrize("payload", [None, [], {}, {"communication_summary": {}},
                                     {"communication_summary": [None]}])
def test_malformed_final_response_returns_issues(role, transcript, payload):
    assert _check_final(payload, role, CONCEPT_IDS, transcript)


def test_veto_guard_retains_prior_flags_without_treating_peer_confidence_as_evidence(role):
    role.veto_power = True
    initial = [ReviewerScore(concept_id="concept", dimension="SAFETY", score=1,
                             confidence=0.4, rationale="Recovery is untested.",
                             red_flags=["Recovery is untested."])]
    final = [ReviewerScore(concept_id="concept", dimension="SAFETY", score=4,
                           confidence=0.9, rationale="A peer expects recovery to work.",
                           red_flags=["The pilot is small."])]
    concerns = _guard_veto(role, initial, final)
    assert concerns
    assert final[0].red_flags == ["Recovery is untested.", "The pilot is small."]
    assert final[0].score == 1.5
    assert final[0].confidence == 0.4
    assert concerns[0] in final[0].rationale
    assert initial[0].score == 1


def test_veto_guard_preserves_already_conservative_score_and_caps_new_flags(role):
    role.veto_power = True
    initial = [ReviewerScore(concept_id="concept", dimension="SAFETY", score=1,
                             confidence=0.4, red_flags=["Untested recovery."]),
               ReviewerScore(concept_id="alternative", dimension="SAFETY", score=3)]
    final = [initial[0].model_copy(deep=True),
             ReviewerScore(concept_id="alternative", dimension="SAFETY", score=4,
                           red_flags=["A new failure mode was identified."])]
    _guard_veto(role, initial, final)
    assert final[0].score == 1
    assert final[0].red_flags == ["Untested recovery."]
    assert final[1].score == 1.5


def test_normal_reviewer_can_revise_a_nonveto_assessment(role):
    initial = [ReviewerScore(concept_id="concept", dimension="SAFETY", score=1,
                             red_flags=["Prior concern."])]
    final = [ReviewerScore(concept_id="concept", dimension="SAFETY", score=4,
                           confidence=0.8, rationale="The peer clarified the operating boundary.")]
    unchanged = final[0].model_dump()
    assert _guard_veto(role, initial, final) == []
    assert final[0].model_dump() == unchanged


@pytest.mark.parametrize("dimension,score", [("COST", 3), ("SAFETY", 4)])
def test_veto_reviewer_can_revise_a_caveat_that_was_not_an_actual_safety_veto(role, dimension, score):
    role.veto_power = True
    initial = [ReviewerScore(concept_id="concept", dimension=dimension, score=score,
                             red_flags=["A boundary condition needs clarification."])]
    final = [ReviewerScore(concept_id="concept", dimension=dimension, score=4,
                           confidence=0.8, rationale="The peer clarified the operating boundary.")]
    unchanged = final[0].model_dump()
    assert _guard_veto(role, initial, final) == []
    assert final[0].model_dump() == unchanged


def test_failed_persona_factory_cannot_start_a_meeting_with_fallback_reviewers(state, monkeypatch):
    def failed_factory(ctx):
        ctx.state.steps.append(StepRecord(node="persona_factory", status="FAILED"))
        return [Persona(persona_id="reviewer", dimensions=["SAFETY"]),
                Persona(persona_id="peer", dimensions=["GOAL"])]

    model_calls = []
    monkeypatch.setattr(personas, "build_personas", failed_factory)
    monkeypatch.setattr(agent, "run_agent", lambda *args, **kwargs: model_calls.append(kwargs))
    with pytest.raises(AbortRun):
        meeting.evaluate(RunContext(state))
    assert model_calls == []
    assert state.evaluation.reviewers == []
    assert state.evaluation.meeting.status != "COMPLETED"
    assert state.evaluation.meeting.completed_calls == {}


def test_saved_pre_meeting_evaluation_loads_and_default_checkpoints_are_independent():
    old_payload = {"reviewers": [{"persona_id": "old", "role_name": "Operations"}],
                   "evaluations": [{"concept_id": "old-concept", "total_score": 3}],
                   "ranking_note": "Existing ranking", "portfolio_note": "Existing portfolio",
                   "roadmap": [{"milestone": "Existing pilot"}]}
    restored = EvaluationBundle.model_validate(old_payload)
    assert restored.meeting.status == "NOT_STARTED"
    assert restored.meeting.rounds == 2
    assert restored.meeting.completed_calls == {}
    assert restored.evaluations[0].total_score == 3
    assert restored.ranking_note == "Existing ranking"
    restored.meeting.completed_calls["old-call"] = {"scores": []}
    assert EvaluationBundle().meeting.completed_calls == {}
