"""Offline regression coverage for actual cross-role review exchanges and resume."""
from collections import Counter
from copy import deepcopy
import threading

import pytest

from triz import agent, meeting, nodes, personas, pipeline, store
from triz.context import AbortRun, RunContext
from triz.schema import ConceptSpec, GlobalState, Persona, ReviewerScore
from triz.settings import settings


PHASES = (
    "s8_review_initial",
    "s8_review_answer_1",
    "s8_review_questions_2",
    "s8_review_answer_2",
    "s8_review_final",
)


class MeetingResponders:
    """Each role answers only its inbox; later phases require real earlier output."""

    def __init__(self):
        self.calls = []
        self.completed = set()
        self.lock = threading.Lock()
        self.fail_final_once = ""
        self.failed = False

    def __call__(self, ctx, **kwargs):
        node, values = kwargs["node"], kwargs["vars"]
        role = values["role_id"]
        peer = "B" if role == "A" else "A"
        dimension = "GOAL" if role == "A" else "FEASIBILITY"
        with self.lock:
            self.calls.append((node, role, deepcopy(values)))
            previous = PHASES[:PHASES.index(node)]
            assert all((phase, who) in self.completed
                       for phase in previous for who in ("A", "B"))

        scores = [{
            "concept_id": concept["concept_id"], "dimension": dimension,
            "score": 4 if node == PHASES[-1] and concept["concept_id"] == "C1" else 2,
            "confidence": 0.5,
            "rationale": "Peer response identifies a reversible approval condition."
                         if node == PHASES[-1] and concept["concept_id"] == "C1"
                         else "The intervention still requires field validation.",
            "red_flags": [],
            "improvement_suggestion": "Test the approval condition before rollout.",
        } for concept in values["concepts_blind"]]

        if node == PHASES[0]:
            response = {"scores": scores, "questions": [{
                "to_role_id": peer, "concept_id": "C1",
                "question": f"{role} asks {peer}: What reversible approval condition is needed?",
                "reply_to_question_id": "",
            }]}
        elif node in (PHASES[1], PHASES[3]):
            assert values["exchange_action"] == "ANSWER"
            assert not values["allow_followup_questions"]
            answers = []
            for question in values["inbox"]:
                assert question["to_role_id"] == role
                answers.append({
                    "question_id": question.get("question_id") or question["id"],
                    "answer": f"{role}: Require explicit owner approval and a reversible pilot.",
                    "evidence_refs": [],
                    "uncertainties": ["Field validation is still required."],
                })
            assert answers
            response = {"answers": answers, "questions": []}
        elif node == PHASES[2]:
            assert values["exchange_action"] == "ASK_FOLLOWUP"
            assert values["allow_followup_questions"]
            exchanges = values["prior_exchanges"]
            assert len(exchanges) == 2
            assert all(exchange["answer"]["answer"] for exchange in exchanges)
            own = next(exchange for exchange in exchanges
                       if exchange["question"]["from_role_id"] == role)
            assert own["answer"]["from_role_id"] == peer
            response = {"answers": [], "questions": [{
                "to_role_id": peer, "concept_id": own["question"]["concept_id"],
                "question": "Your owner-approval condition is clear; what stops the pilot safely?",
                "reply_to_question_id": own["question"]["id"],
            }]}
        else:
            if role == self.fail_final_once and not self.failed:
                self.failed = True
                return None
            exchanges = values["meeting_transcript"]
            assert len(exchanges) == 4
            assert {exchange["question"]["round_number"] for exchange in exchanges} == {1, 2}
            assert all(exchange["answer"]["answer"] for exchange in exchanges)
            discussed = [exchange["question"]["id"] for exchange in exchanges
                         if exchange["question"]["from_role_id"] == role]
            response = {"scores": scores, "communication_summary": [{
                "concept_id": "C1", "peer_role_ids": [peer], "question_ids": discussed,
                "summary": f"{peer} clarified owner approval and reversible pilot conditions.",
                "assessment_change": "C1 increases from 2 to 4 subject to these conditions; C2 is unchanged.",
                "unresolved_issues": ["Field validation is still required."],
            }]}

        if kwargs.get("checker"):
            issues = kwargs["checker"](response)
            assert not issues, issues
        with self.lock:
            self.completed.add((node, role))
        return response


@pytest.fixture
def meeting_case(state, monkeypatch):
    state.concepts = [
        ConceptSpec(id="C1", title="Explicit owner approval", description="Run a reversible pilot.",
                    quality_status="PASS"),
        ConceptSpec(id="C2", title="Alternative process", description="Requires separate validation.",
                    quality_status="PASS"),
    ]
    roster_calls = []

    def build_roster(ctx):
        roster_calls.append(ctx.state.concepts[0].description)
        return [
            Persona(persona_id="A", role_name="Outcome reviewer", dimensions=["GOAL"],
                    mandate="Assess the stated success criteria."),
            Persona(persona_id="B", role_name="Operations reviewer", dimensions=["FEASIBILITY"],
                    mandate="Assess operating conditions and reversibility."),
        ]

    original_cfg = settings.cfg
    overrides = {
        "run.parallel_workers": 2,
        "evaluation.meeting_rounds": 2,
        "evaluation.meeting_questions_per_role": 2,
    }
    monkeypatch.setattr(settings, "cfg", lambda key, default=None:
                        overrides.get(key, original_cfg(key, default)))
    responder = MeetingResponders()
    monkeypatch.setattr(personas, "build_personas", build_roster)
    monkeypatch.setattr(agent, "run_agent", responder)
    return state, responder, roster_calls


def test_two_round_meeting_uses_real_peer_answers_before_final_scores(meeting_case):
    state, responder, roster_calls = meeting_case
    scores = meeting.evaluate(RunContext(state))

    assert len(roster_calls) == 1
    assert Counter(node for node, _, _ in responder.calls) == Counter({phase: 2 for phase in PHASES})
    assert len(scores) == 4 and all(isinstance(score, ReviewerScore) for score in scores)
    assert {score.score for score in scores if score.concept_id == "C1"} == {4}
    assert {score.score for score in scores if score.concept_id == "C2"} == {2}
    session = state.evaluation.meeting
    assert session.status == "COMPLETED" and session.rounds == 2
    assert len(session.initial_reviews) == len(session.final_reviews) == 2
    assert len(session.questions) == len(session.answers) == 4
    questions = {question.id: question for question in session.questions}
    answers = {answer.question_id: answer for answer in session.answers}
    assert len(questions) == 4 and set(questions) == set(answers)
    for question in questions.values():
        answer = answers[question.id]
        assert answer.from_role_id == question.to_role_id
        assert answer.to_role_id == question.from_role_id
        assert answer.concept_id == question.concept_id
        if question.round_number == 2:
            first = questions[question.reply_to_question_id]
            assert first.round_number == 1 and first.concept_id == question.concept_id
    for final in session.final_reviews:
        assert final.communication_summary
        for summary in final.communication_summary:
            assert summary.concept_id == "C1" and summary.unresolved_issues
            assert final.reviewer_id not in summary.peer_role_ids
            for question_id in summary.question_ids:
                question = questions[question_id]
                assert question.concept_id == summary.concept_id
                assert set(summary.peer_role_ids) <= {question.from_role_id, question.to_role_id}


def test_interrupted_final_review_resumes_only_missing_role_with_same_question_ids(meeting_case):
    state, responder, roster_calls = meeting_case
    responder.fail_final_once = "B"
    with pytest.raises(AbortRun):
        meeting.evaluate(RunContext(state))

    assert state.evaluation.meeting.status != "COMPLETED"
    question_ids = [question.id for question in state.evaluation.meeting.questions]
    assert len(question_ids) == 4
    assert len(state.evaluation.meeting.completed_calls) == 9

    restored = GlobalState.model_validate_json(state.model_dump_json())
    before = len(responder.calls)
    scores = meeting.evaluate(RunContext(restored))
    assert [(node, role) for node, role, _ in responder.calls[before:]] == [(PHASES[-1], "B")]
    assert len(roster_calls) == 1
    assert [question.id for question in restored.evaluation.meeting.questions] == question_ids
    assert restored.evaluation.meeting.status == "COMPLETED"
    assert len(restored.evaluation.meeting.final_reviews) == 2
    assert len(scores) == 4


def test_changed_concept_invalidates_completed_meeting_and_rebuilds_roster(meeting_case):
    state, responder, roster_calls = meeting_case
    meeting.evaluate(RunContext(state))
    old_hash = state.evaluation.meeting.input_hash
    before = len(responder.calls)
    responder.completed.clear()
    state.concepts[0].description = "A materially changed intervention with a different approval boundary."

    meeting.evaluate(RunContext(state))

    assert len(roster_calls) == 2
    assert state.evaluation.meeting.input_hash != old_hash
    new_calls = responder.calls[before:]
    assert Counter(node for node, _, _ in new_calls) == Counter({phase: 2 for phase in PHASES})
    assert all(values["concepts_blind"][0]["description"] == state.concepts[0].description
               for _, _, values in new_calls)
    assert len(state.evaluation.meeting.completed_calls) == 10
    assert len(state.evaluation.meeting.questions) == len(state.evaluation.meeting.answers) == 4


def test_failed_ranking_preserves_meeting_and_candidates_and_retries_only_ranking(meeting_case, monkeypatch):
    state, responder, roster_calls = meeting_case
    original_cfg = settings.cfg
    monkeypatch.setattr(settings, "cfg", lambda key, default=None:
                        1 if key in ("solutions.min_solutions", "solutions.max_solutions")
                        else original_cfg(key, default))
    monkeypatch.setattr(pipeline, "PIPELINE", [("s8_evaluate", "Multi-role review", nodes.s8_evaluate)])
    monkeypatch.setattr(pipeline, "start", lambda run_id: None)
    rank_calls = []

    def respond(ctx, **kwargs):
        if kwargs["node"] != "s8_rank":
            return responder(ctx, **kwargs)
        rank_calls.append(deepcopy(kwargs["vars"]))
        step = ctx.start_step(**{key: kwargs[key] for key in
                                ("node", "label", "stage", "agent_id", "prompt_id", "tier")})
        if len(rank_calls) == 1:
            ctx.finish_step(step, "FAILED")
            return None
        ctx.finish_step(step, "OK")
        return {"ranking": [{"concept_id": "C1", "rank": 1}, {"concept_id": "C2", "rank": 2}],
                "ranking_note": "C1 has clearer reversible operating conditions.",
                "portfolio_note": "Validate the pilot first.", "roadmap": []}

    monkeypatch.setattr(agent, "run_agent", respond)
    store.save_state(state)
    interrupted = pipeline.execute_stage(state.run_id, 0)
    assert interrupted["status"] == "INTERRUPTED" and interrupted["stage_index"] == 0
    saved = store.load_state(state.run_id)
    assert [concept.id for concept in saved.concepts] == ["C1", "C2"]
    assert saved.evaluation.meeting.status == "COMPLETED"
    assert len(saved.evaluation.meeting.completed_calls) == 10
    assert len(responder.calls) == 10 and len(rank_calls) == 1
    assert all(evaluation.rank == 0 for evaluation in saved.evaluation.evaluations)
    initial_hash = saved.evaluation.meeting.input_hash
    question_ids = [question.id for question in saved.evaluation.meeting.questions]

    assert pipeline.continue_run(state.run_id)
    retry = store.load_state(state.run_id)
    completed = pipeline.execute_stage(state.run_id, 0, retry.scratch["execution_epoch"])
    assert completed["status"] == "COMPLETED"
    saved = store.load_state(state.run_id)
    assert len(rank_calls) == 2 and len(responder.calls) == 10 and len(roster_calls) == 1
    assert saved.evaluation.meeting.input_hash == initial_hash
    assert [question.id for question in saved.evaluation.meeting.questions] == question_ids
    assert [concept.id for concept in saved.concepts] == ["C1"]
    assert saved.evaluation.evaluations[0].rank == 1


@pytest.mark.parametrize("failure", ["initial", "missing_answer"])
def test_incomplete_meeting_never_reaches_aggregation_or_ranking(meeting_case, monkeypatch, failure):
    state, responder, _ = meeting_case
    reached = []

    def respond(ctx, **kwargs):
        node, role = kwargs["node"], kwargs["vars"]["role_id"]
        if role == "B" and failure == "initial" and node == PHASES[0]:
            return None
        if role == "B" and failure == "missing_answer" and node == PHASES[1]:
            return {"answers": [], "questions": []}
        return responder(ctx, **kwargs)

    monkeypatch.setattr(agent, "run_agent", respond)
    monkeypatch.setattr(nodes, "_aggregate", lambda *args: reached.append("aggregate"))
    monkeypatch.setattr(nodes, "_rank", lambda *args: reached.append("rank"))
    with pytest.raises(AbortRun):
        nodes.s8_evaluate(RunContext(state))

    assert not reached
    assert state.evaluation.meeting.status != "COMPLETED"
    assert state.evaluation.evaluations == []
    assert [concept.id for concept in state.concepts] == ["C1", "C2"]
    assert not any(node == PHASES[-1] for node, _, _ in responder.calls)
