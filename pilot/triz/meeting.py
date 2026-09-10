"""S8: independent reviewers exchange real, addressed questions before scoring again."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

from . import agent, digest, domain, personas, prompts_registry as P, verify
from .context import AbortRun, RunContext
from .schema import (EvaluationMeeting, MeetingAnswer, MeetingFinalReview, MeetingQuestion,
                     MeetingSummary, ReviewerScore, Stage)
from .settings import settings


PROMPTS = ("P_S8_MEETING_INITIAL", "P_S8_MEETING_EXCHANGE", "P_S8_MEETING_FINAL")
SYSTEM = ("You are an experienced domain reviewer participating in a real multi-role review. "
          "Speak only for your assigned role. Treat peer statements as claims, not verified facts. "
          "Output JSON only. You do not know how these ideas were generated.")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(x) for x in value)


def _check_questions(data, role_id, role_ids, concept_ids, limit, prior=None):
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        return ["questions는 질문 객체 배열이어야 한다."]
    questions = data["questions"]
    issues = []
    if not 1 <= len(questions) <= limit:
        issues.append(f"타 직군에 질문을 1~{limit}개 보내야 한다.")
    seen = set()
    for q in questions:
        if not isinstance(q, dict):
            issues.append("각 질문은 객체여야 한다.")
            continue
        target, cid = q.get("to_role_id"), q.get("concept_id")
        if not _text(target) or target not in role_ids or target == role_id:
            issues.append("질문 수신자는 자신을 제외한 실제 참가자여야 한다.")
        if not _text(cid) or cid not in concept_ids or not _text(q.get("question")):
            issues.append("질문에 실제 concept_id와 구체적인 question이 필요하다.")
        ref = q.get("reply_to_question_id", "")
        if prior is None:
            if ref != "":
                issues.append("최초 질문의 reply_to_question_id는 비워야 한다.")
        elif not _text(ref) or ref not in prior or prior[ref]["concept_id"] != cid:
            issues.append("후속 질문은 같은 개념의 이전 차수에서 답변된 질문 ID를 참조해야 한다.")
        if _text(target) and _text(cid) and _text(q.get("question")):
            key = (target, cid, q["question"].strip())
            if key in seen:
                issues.append("동일한 질문을 중복해서 보내지 않는다.")
            seen.add(key)
    return issues


def _check_answers(data, inbox, evidence):
    if not isinstance(data, dict) or not isinstance(data.get("answers"), list):
        return ["answers는 답변 객체 배열이어야 한다."]
    issues = []
    if data.get("questions") != []:
        issues.append("ANSWER 호출의 questions는 []여야 한다.")
    expected = {q["question_id"]: q for q in inbox}
    seen = set()
    for a in data["answers"]:
        if not isinstance(a, dict):
            issues.append("각 답변은 객체여야 한다.")
            continue
        qid = a.get("question_id")
        if not _text(qid) or qid not in expected or qid in seen:
            issues.append("전달받은 각 질문 ID에 정확히 한 번만 답해야 한다.")
            continue
        seen.add(qid)
        if not _text(a.get("answer")) or not _strings(a.get("uncertainties")):
            issues.append("answer와 uncertainties 문자열 배열이 필요하다.")
        refs = a.get("evidence_refs")
        if not _strings(refs):
            issues.append("evidence_refs는 제공된 근거 ID의 문자열 배열이어야 한다.")
        elif any(ref not in evidence or expected[qid]["concept_id"] not in evidence[ref]
                 for ref in refs):
            issues.append("해당 개념에 제공된 근거 ID만 인용할 수 있다.")
    if seen != set(expected):
        issues.append("아직 답하지 않은 inbox 질문이 있다.")
    return issues


def _check_final(data, role, concept_ids, transcript):
    issues = verify.check_review(data, concept_ids, role.dimensions)
    if not isinstance(data, dict) or not isinstance(data.get("communication_summary"), list):
        return issues + ["communication_summary 배열이 필요하다."]
    exchanges = {x["question"]["id"]: x["question"] for x in transcript}
    own_exchange = False
    for item in data["communication_summary"]:
        if not isinstance(item, dict):
            issues.append("소통 반영 요약은 객체여야 한다.")
            continue
        cid = item.get("concept_id")
        if not _text(cid) or cid not in concept_ids:
            issues.append("소통 요약에 실제 concept_id가 필요하다.")
        refs, peers = item.get("question_ids"), item.get("peer_role_ids")
        if not _strings(refs) or not refs or not _strings(peers) or not peers:
            issues.append("소통 요약은 실제 질문 ID와 타 참가자 ID를 인용해야 한다.")
            continue
        allowed_peers = set()
        for ref in refs:
            q = exchanges.get(ref)
            if not q or q["concept_id"] != cid:
                issues.append("소통 요약은 같은 개념에 대해 실제 답변된 질문만 참조할 수 있다.")
                continue
            participants = {q["from_role_id"], q["to_role_id"]}
            own_exchange |= role.persona_id in participants
            allowed_peers.update(participants - {role.persona_id})
        if set(peers) - allowed_peers:
            issues.append("peer_role_ids는 인용한 교환에 참여한 타 참가자만 포함해야 한다.")
        if not _text(item.get("summary")) or not _text(item.get("assessment_change")):
            issues.append("실제 응답 내용과 최초 판단의 변경 또는 유지 이유를 요약해야 한다.")
        if not _strings(item.get("unresolved_issues")):
            issues.append("unresolved_issues는 문자열 배열이어야 한다.")
    if not own_exchange:
        issues.append("자신이 실제 타 직군과 주고받은 교환을 최소 한 건 요약해야 한다.")
    return issues


def _evidence_packet(state):
    """Expose supporting material and its scope, but never generation tracks/lineage."""
    associated = {}
    for concept in state.concepts:
        for eid in concept.evidence_ids:
            associated.setdefault(eid, []).append(concept.id)
    return [{"id": e.id, "concept_ids": associated[e.id], "claim": e.claim,
             "title": e.title, "source_type": e.source_type, "identifier": e.identifier,
             "url": e.url, "snippet": e.snippet, "verified": e.verified,
             "reliability": e.reliability, "evidence_scope": e.evidence_scope}
            for e in state.evidence if e.id in associated]


def _scores(data, role):
    fields = set(ReviewerScore.model_fields) - {"reviewer_role"}
    return [ReviewerScore(**{k: v for k, v in row.items() if k in fields},
                          reviewer_role=role.role_name) for row in data["scores"]]


def _transcript(meeting):
    answers = {a.question_id: a.model_dump() for a in meeting.answers}
    return [{"question": q.model_dump(), "answer": answers[q.id]}
            for q in meeting.questions if q.id in answers]


def _guard_veto(role, initial, final):
    """A peer assertion alone cannot erase a veto raised on unchanged evidence."""
    retained = []
    initial_by_key = {(s.concept_id, s.dimension): s for s in initial}
    for score in final:
        if not role.veto_power:
            continue
        old = initial_by_key[(score.concept_id, score.dimension)]
        if old.dimension == "SAFETY" and old.score <= 1.5 and old.red_flags:
            removed = [flag for flag in old.red_flags if flag not in score.red_flags]
            score.red_flags = list(dict.fromkeys(old.red_flags + score.red_flags))
            if removed or score.score > 1.5:
                note = f"{score.concept_id}/{score.dimension}: 최초 veto 우려는 추가 검증 전까지 유지: {'; '.join(old.red_flags)}"
                retained.append(note)
                score.rationale += " " + note
                score.confidence = min(score.confidence, old.confidence)
        if score.red_flags:
            score.score = min(score.score, 1.5)
    return retained


def evaluate(ctx: RunContext) -> list[ReviewerScore]:
    """Five barriers for two rounds; persist each valid role call for safe retries."""
    state = ctx.state
    rounds = max(1, min(2, int(settings.cfg("evaluation.meeting_rounds", 2))))
    limit = max(1, min(2, int(settings.cfg("evaluation.meeting_questions_per_role", 2))))
    evidence_packet = _evidence_packet(state)
    common = {"industry": state.domain.industry,
              "problem_type": domain.problem_type(state), "physical_scope": state.domain.physical_scope,
              "restated_problem": state.intake.frame.restated_problem,
              "target_system": digest.target_system(state),
              "operating_env": state.domain.operating_env,
              "constraints_block": verify.constraints_block(state),
              "concepts_blind": digest.concepts_blind(state),
              "facts_packet": digest.facts_packet(state), "evidence_packet": evidence_packet,
              "success_criteria": state.intake.frame.success_criteria,
              "requirements": [{"improve": t.then_good, "preserve": t.but_bad}
                               for t in state.definition.technical_contradictions],
              "max_questions": limit}
    # Checkpoint identity deliberately excludes steps, cost and the meeting itself.
    identity = {"version": 1, "inputs": common, "rounds": rounds, "domain_metadata": state.domain.model_dump(),
                "domain": domain.context(state, "s8_review"), "system": SYSTEM,
                "personas": settings.personas, "evaluation": settings.cfg("evaluation", {}),
                "role_seeds": personas.seed_personas(state),
                "prompts": {p: P.raw(p) for p in (*PROMPTS, "P_PERSONA_FACTORY", "P_VERIFIER_GENERIC")},
                "rubric": settings.rubrics.get("R8_REVIEW", {}),
                "verification": settings.cfg("verification", {}),
                "injected": state.control.injected_agents, "lang": state.control.lang,
                "models": {tier: {k: getattr(t, k, None) for k in
                                  ("model", "base_url", "temperature", "max_tokens", "json_mode",
                                   "supports_temperature", "token_parameter")}
                           for tier, t in settings.tiers.items()}}
    input_hash = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False,
                                          default=str).encode()).hexdigest()
    meeting = state.evaluation.meeting
    if meeting.input_hash != input_hash or not state.evaluation.reviewers:
        meeting = EvaluationMeeting(input_hash=input_hash, rounds=rounds, status="RUNNING")
        state.evaluation.meeting = meeting
        state.evaluation.reviewers = []
        state.evaluation.evaluations = []
        state.evaluation.ranking_note = state.evaluation.portfolio_note = ""
        state.evaluation.roadmap = []
        start = len(state.steps)
        reviewers = personas.build_personas(ctx)
        if any(step.status == "FAILED" for step in state.steps[start:]):
            ctx.persist()
            raise AbortRun("회의 참가자 구성 호출이 실패했습니다. 참가자 구성부터 다시 시도해 주세요.")
        state.evaluation.reviewers = reviewers
    reviewers = state.evaluation.reviewers
    role_ids = {p.persona_id for p in reviewers}
    if len(role_ids) < 2 or len(role_ids) != len(reviewers) or any(not p.dimensions for p in reviewers):
        raise AbortRun("다직군 회의에는 서로 다른 참가자 두 명 이상과 각자의 담당 평가 차원이 필요합니다.")
    meeting.status = "RUNNING"
    ctx.persist()
    ctx.emit("personas", reviewers=[r.model_dump() for r in reviewers])
    roster = [{"role_id": p.persona_id, "role_name": p.role_name, "mandate": p.mandate,
               "dimensions": p.dimensions, "veto_power": p.veto_power} for p in reviewers]
    concept_ids = {c.id for c in state.concepts}
    evidence = {e["id"]: e["concept_ids"] for e in evidence_packet}

    def role_vars(p):
        return {**deepcopy(common), "role_id": p.persona_id, "role_name": p.role_name,
                "seniority": p.seniority, "mandate": p.mandate, "bias_note": p.bias_note,
                "dimensions": list(p.dimensions), "participant_roster": deepcopy(roster)}

    def phase(name, label, prompt_id, variables, checker, token_limit, participants=None, rubric=None):
        # Freeze every role's input before launching workers. Completion order cannot
        # change what a peer sees, and subsequent phases only start after all succeed.
        participants = reviewers if participants is None else participants
        inputs = {p.persona_id: variables(p) for p in participants}
        ctx.emit("meeting_phase", phase=name, label=label, rounds=rounds)
        results, errors = {}, []

        def call(p):
            key = f"{name}:{p.persona_id}"
            check = lambda data: [f"FATAL-MEETING: {issue}" for issue in checker(data, p)]
            call_hash = hashlib.sha256(json.dumps(inputs[p.persona_id], sort_keys=True,
                                                  ensure_ascii=False, default=str).encode()).hexdigest()
            saved = meeting.completed_calls.get(key)
            if (saved is not None and meeting.completed_call_inputs.get(key) == call_hash
                    and not check(saved)):
                return deepcopy(saved), call_hash
            data = agent.run_agent(
                ctx, node=f"s8_review_{name}", label=f"{label}: {p.role_name}",
                stage=Stage.S8.value, agent_id=f"persona::{p.persona_id}",
                prompt_id=prompt_id, tier="T3", system_override=SYSTEM,
                vars=inputs[p.persona_id], checker=check, rubric_id=rubric,
                facts=json.dumps({"review_context": inputs[p.persona_id],
                                  "peer_statements_are_verified_facts": False},
                                 ensure_ascii=False) if rubric else "",
                max_tokens=token_limit(p), default=None)
            issues = check(data)
            if issues:
                raise AbortRun(f"{label}: {p.role_name} 응답이 불완전합니다. {issues[0]}")
            return data, call_hash

        workers = max(1, min(int(settings.cfg("run.parallel_workers", 4)), len(participants)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending = {pool.submit(call, p): p for p in participants}
            for future in as_completed(pending):
                p = pending[future]
                try:
                    data, call_hash = future.result()
                except Exception as exc:
                    errors.append(exc)
                    continue
                results[p.persona_id] = data
                with ctx.lock:
                    meeting.completed_calls[f"{name}:{p.persona_id}"] = deepcopy(data)
                    meeting.completed_call_inputs[f"{name}:{p.persona_id}"] = call_hash
                ctx.persist()
        if errors:
            ctx.persist()
            raise errors[0]
        return results

    score_tokens = lambda p: min(8000, 1500 + 200 * len(concept_ids) * len(p.dimensions))
    initial = phase("initial", "회의: 독립 검토·1차 질문", PROMPTS[0], role_vars,
                    lambda d, p: verify.check_review(d, concept_ids, p.dimensions) +
                    _check_questions(d, p.persona_id, role_ids, concept_ids, limit), score_tokens)
    meeting.initial_reviews = {p.persona_id: _scores(initial[p.persona_id], p) for p in reviewers}
    # Rebuild derived transcript deterministically from validated checkpoints on retry.
    meeting.questions, meeting.answers, meeting.final_reviews = [], [], []

    def add_questions(outputs, number):
        for p in reviewers:
            for i, q in enumerate(outputs[p.persona_id]["questions"], 1):
                meeting.questions.append(MeetingQuestion(
                    id=f"MQ{number}_{p.persona_id}_{i}", round_number=number,
                    from_role_id=p.persona_id, to_role_id=q["to_role_id"],
                    concept_id=q["concept_id"], question=q["question"],
                    reply_to_question_id=q.get("reply_to_question_id", "")))
        ctx.persist()

    add_questions(initial, 1)
    for number in range(1, rounds + 1):
        prior = _transcript(meeting)
        inboxes = {p.persona_id: [{**q.model_dump(), "question_id": q.id}
                                 for q in meeting.questions
                                 if q.round_number == number and q.to_role_id == p.persona_id]
                   for p in reviewers}
        outputs = phase(f"answer_{number}", f"회의: {number}차 답변", PROMPTS[1],
                        lambda p: {**role_vars(p), "round_number": number,
                                   "exchange_action": "ANSWER", "allow_followup_questions": False,
                                   "inbox": inboxes[p.persona_id], "prior_exchanges": deepcopy(prior),
                                   "initial_review": initial[p.persona_id]},
                        lambda d, p: _check_answers(d, inboxes[p.persona_id], evidence),
                        lambda p: min(8000, 1000 + 550 * len(inboxes[p.persona_id])),
                        participants=[p for p in reviewers if inboxes[p.persona_id]])
        for p in reviewers:
            answers = {a["question_id"]: a for a in outputs.get(p.persona_id, {}).get("answers", [])}
            for q in inboxes[p.persona_id]:
                a = answers[q["question_id"]]
                meeting.answers.append(MeetingAnswer(
                    question_id=q["question_id"], round_number=number, from_role_id=p.persona_id,
                    to_role_id=q["from_role_id"], concept_id=q["concept_id"], answer=a["answer"],
                    evidence_refs=a["evidence_refs"], uncertainties=a["uncertainties"]))
        ctx.persist()
        if number < rounds:
            prior = _transcript(meeting)
            answered = {x["question"]["id"]: x["question"] for x in prior}

            def check_followup(d, p):
                issues = _check_questions(d, p.persona_id, role_ids, concept_ids, limit, answered)
                if not isinstance(d, dict) or d.get("answers") != []:
                    issues.append("ASK_FOLLOWUP 호출의 answers는 []여야 한다.")
                return issues

            followup = phase(f"questions_{number + 1}", f"회의: {number + 1}차 후속 질문", PROMPTS[1],
                             lambda p: {**role_vars(p), "round_number": number + 1,
                                        "exchange_action": "ASK_FOLLOWUP", "allow_followup_questions": True,
                                        "inbox": [], "prior_exchanges": deepcopy(prior),
                                        "initial_review": initial[p.persona_id]},
                             check_followup, lambda p: 2000)
            add_questions(followup, number + 1)

    transcript = _transcript(meeting)
    final = phase("final", "회의: 소통 반영 최종 평가", PROMPTS[2],
                  lambda p: {**role_vars(p), "initial_review": initial[p.persona_id],
                             "meeting_transcript": deepcopy(transcript), "meeting_gaps": []},
                  lambda d, p: _check_final(d, p, concept_ids, transcript),
                  lambda p: min(8000, score_tokens(p) + 1500), rubric="R8_REVIEW")
    all_scores = []
    for p in reviewers:
        data = final[p.persona_id]
        scores = _scores(data, p)
        retained = _guard_veto(p, meeting.initial_reviews[p.persona_id], scores)
        summaries = [MeetingSummary.model_validate(item) for item in data["communication_summary"]]
        for summary in summaries:
            concerns = [note for note in retained if note.startswith(f"{summary.concept_id}/")]
            if concerns:
                summary.unresolved_issues = list(dict.fromkeys(summary.unresolved_issues + concerns))
                summary.assessment_change += " 서버 검증: 최초 veto 우려와 점수 상한 유지."
        meeting.final_reviews.append(MeetingFinalReview(
            reviewer_id=p.persona_id, reviewer_role=p.role_name, scores=scores,
            communication_summary=summaries, retained_concerns=retained))
        all_scores.extend(scores)
    meeting.status = "COMPLETED"
    ctx.persist()
    ctx.emit("meeting_phase", phase="completed", label="다직군 회의 완료", rounds=rounds)
    return all_scores
