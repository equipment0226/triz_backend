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
DIMENSION_RUBRICS = {
    "FEASIBILITY": "현재 자원·역량으로 실행 가능한가, 미검증 전제는 무엇인가.",
    "COST": "초기투자·운영비 변화와 산정 근거. 수치는 근거와 단위가 있는 추정만 허용한다.",
    "RISK": "실패 손실·부작용·가역성.",
    "TIME": "도입 기간과 운영 중단 시간.",
    "GOAL": "명시된 성공 기준에 직접 기여하는가.",
    "RESOLUTION": "상충하는 양쪽 요구를 보존하며 다른 주체에 손실을 전가하지 않는가.",
    "CAUSAL": "관측과 가설을 구분하며 반증할 수 있는가.",
    "QUALITY": "해당 문제 유형의 결과 품질·신뢰성.",
    "ADOPTION": "현장·사용자의 수용과 지속 가능성.",
    "SAFETY": "안전·규제·환경 위반. veto 권한 담당자의 확인된 위반은 score=1.",
    "SCALABILITY": "다른 대상·규모로 확장할 수 있는가.",
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(x) for x in value)


def _reference_options(transcript, role_id):
    """Short selectors resolve to real exchanges; models never assemble foreign keys."""
    followups, groups = [], {}
    for i, exchange in enumerate(transcript, 1):
        q = exchange["question"]
        peers = {q["from_role_id"], q["to_role_id"]} - {role_id}
        direct = role_id in (q["from_role_id"], q["to_role_id"])
        followups.append({"followup_id": f"F{i}", "question_id": q["id"],
                          "concept_id": q["concept_id"], "direct": direct})
        group = groups.setdefault(q["concept_id"], {
            "summary_id": f"S{len(groups) + 1}", "concept_id": q["concept_id"],
            "question_ids": [], "peer_role_ids": [], "direct": False})
        group["question_ids"].append(q["id"])
        group["peer_role_ids"] = sorted(set(group["peer_role_ids"]) | peers)
        group["direct"] |= direct
    return followups, list(groups.values())


def _output_normalizer(phase, values):
    previous = {}
    followups = {x["followup_id"]: x for x in values.get("followup_options", [])}
    summaries = {x["summary_id"]: x for x in values.get("summary_options", [])}
    evidence_keys = {x["evidence_key"]: x["id"] for x in values.get("answer_evidence_options", [])}
    assigned = set(values.get("dimensions", []))

    def normalize(data):
        nonlocal previous
        if not isinstance(data, dict):
            return data
        # A repair may return only the corrected top-level fields. Keep prior
        # fields for full validation; never fabricate missing scores or answers.
        data = {**deepcopy(previous), **deepcopy(data)}
        if phase == "initial" or phase == "final":
            if assigned and isinstance(data.get("scores"), list):
                # Keep this role's assigned matrix. Surplus known dimensions are
                # not part of its mandate; missing/duplicate/invalid rows still fail.
                data["scores"] = [row for row in data["scores"] if not isinstance(row, dict)
                    or not isinstance(row.get("dimension"), str)
                    or row["dimension"] not in DIMENSION_RUBRICS or row["dimension"] in assigned]
            for row in data.get("scores", []) if isinstance(data.get("scores"), list) else []:
                if isinstance(row, dict):
                    flags = row.get("red_flags")
                    if flags is None:
                        # A missing safety-veto explanation is substantive, not
                        # an optional empty list; let the checker request it.
                        safety_veto = (row.get("dimension") == "SAFETY" and
                                       isinstance(row.get("score"), (int, float)) and row["score"] <= 1.5)
                        if not safety_veto:
                            row["red_flags"] = []
                    elif isinstance(flags, str):
                        row["red_flags"] = [flags] if flags.strip() else []
        if phase.startswith("questions_"):
            data.setdefault("answers", [])
            for q in data.get("questions", []) if isinstance(data.get("questions"), list) else []:
                if not isinstance(q, dict):
                    continue
                ref = q.get("followup_id")
                if isinstance(ref, str) and ref in followups:
                    option = followups[ref]
                    q.setdefault("concept_id", option["concept_id"])
                    q.setdefault("reply_to_question_id", option["question_id"])
        if phase.startswith("answer_"):
            data.setdefault("questions", [])
            for answer in data.get("answers", []) if isinstance(data.get("answers"), list) else []:
                if isinstance(answer, dict):
                    if "evidence_refs" not in answer and isinstance(answer.get("evidence_keys"), list):
                        answer["evidence_refs"] = [evidence_keys.get(key, key) if isinstance(key, str) else key
                                                   for key in answer["evidence_keys"]]
                    for key in ("evidence_refs", "uncertainties"):
                        if answer.get(key) is None:
                            answer[key] = []
        if phase == "final":
            for item in data.get("communication_summary", []) if isinstance(data.get("communication_summary"), list) else []:
                if not isinstance(item, dict):
                    continue
                ref = item.get("summary_id")
                if isinstance(ref, str) and ref in summaries:
                    for key in ("concept_id", "question_ids", "peer_role_ids"):
                        item.setdefault(key, deepcopy(summaries[ref][key]))
                if item.get("unresolved_issues") is None:
                    item["unresolved_issues"] = []
        previous = deepcopy(data)
        return data

    return normalize


def _legacy_context_matches(state, common, rounds):
    """Retain already completed v1 calls during the reference-format rollout."""
    if state.evaluation.meeting.rounds != rounds or state.control.injected_agents:
        return False
    roles = {p.persona_id: p for p in state.evaluation.reviewers}
    if not roles:
        return False
    checked = set()
    for step in state.steps:
        if step.node != "s8_review_initial":
            continue
        values = step.input_slice.get("vars", {})
        role = roles.get(values.get("role_id"))
        if role is None:
            continue
        if any(values.get(key) != value for key, value in common.items()):
            return False
        if values.get("dimensions") != role.dimensions or values.get("role_name") != role.role_name:
            return False
        checked.add(role.persona_id)
    return checked == set(roles)


def _check_questions(data, role_id, role_ids, concept_ids, limit, prior=None):
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        return ["questions는 질문 객체 배열이어야 한다."]
    questions = data["questions"]
    issues = []
    if not 1 <= len(questions) <= limit:
        issues.append(f"타 직군에 질문을 1~{limit}개 보내야 한다.")
    seen = set()
    for index, q in enumerate(questions, 1):
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
            choices = [key for key, value in prior.items() if value["concept_id"] == cid]
            issues.append(f"questions[{index - 1}]: 후속 질문은 같은 개념의 이전 차수에서 답변된 질문 ID를 참조해야 한다. "
                          f"concept_id={cid}, 잘못된 참조={ref}, 해당 개념의 유효 ID={choices}. followup_options에서 하나를 선택하라.")
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
            allowed = [ref for ref, ids in evidence.items() if expected[qid]["concept_id"] in ids]
            issues.append(f"question_id={qid}: 해당 개념에 제공된 근거 ID만 인용할 수 있다. "
                          f"허용 evidence_refs={allowed}; 제공된 answer_evidence_options에서 이 개념의 키만 선택하라. "
                          "확인되지 않은 연결을 사실로 주장하지 말고, 인용 근거가 없으면 []로 쓰고 불확실성을 밝혀라.")
    if seen != set(expected):
        issues.append("아직 답하지 않은 inbox 질문이 있다.")
    return issues


def _final_batches(values):
    """Bound score rows per output while every call retains the full meeting context."""
    ids = [c["concept_id"] for c in values["concepts_blind"]]
    rows = max(6, min(12, int(settings.cfg("evaluation.meeting_final_batch_rows", 12))))
    size = max(1, rows // max(1, len(values["dimensions"])))
    return [{**deepcopy(values), "review_concept_ids": ids[i:i + size],
             "include_communication_summary": i == 0}
            for i in range(0, len(ids), size)]


def _check_final(data, role, concept_ids, transcript, *, summary_concept_ids=None, require_summary=True):
    issues = verify.check_review(data, concept_ids, role.dimensions)
    if not isinstance(data, dict) or not isinstance(data.get("communication_summary"), list):
        return issues + ["communication_summary 배열이 필요하다."]
    exchanges = {x["question"]["id"]: x["question"] for x in transcript}
    own_exchange = False
    for index, item in enumerate(data["communication_summary"]):
        if not isinstance(item, dict):
            issues.append("소통 반영 요약은 객체여야 한다.")
            continue
        cid = item.get("concept_id")
        if not _text(cid) or cid not in (summary_concept_ids or concept_ids):
            issues.append("소통 요약에 실제 concept_id가 필요하다.")
        refs, peers = item.get("question_ids"), item.get("peer_role_ids")
        if not _strings(refs) or not refs or not _strings(peers) or not peers:
            issues.append("소통 요약은 실제 질문 ID와 타 참가자 ID를 인용해야 한다.")
            continue
        allowed_peers = set()
        for ref in refs:
            q = exchanges.get(ref)
            if not q or q["concept_id"] != cid:
                issues.append(f"communication_summary[{index}]: 소통 요약은 같은 개념에 대해 실제 답변된 질문만 참조할 수 있다. "
                              f"concept_id={cid}, 잘못된 참조={ref}. summary_options의 summary_id로 다시 선택하라.")
                continue
            participants = {q["from_role_id"], q["to_role_id"]}
            own_exchange |= role.persona_id in participants
            allowed_peers.update(participants - {role.persona_id})
        if set(peers) - allowed_peers:
            issues.append(f"communication_summary[{index}]: peer_role_ids는 인용한 교환에 참여한 타 참가자만 포함해야 한다. "
                          f"허용 ID={sorted(allowed_peers)}. summary_options의 summary_id를 사용하라.")
        if not _text(item.get("summary")) or not _text(item.get("assessment_change")):
            issues.append("실제 응답 내용과 최초 판단의 변경 또는 유지 이유를 요약해야 한다.")
        if not _strings(item.get("unresolved_issues")):
            issues.append("unresolved_issues는 문자열 배열이어야 한다.")
    if require_summary and not own_exchange:
        issues.append("자신이 실제 타 직군과 주고받은 교환을 최소 한 건 요약해야 한다.")
    comments = data.get("concept_comments", {})
    if (not isinstance(comments, dict) or any(cid not in concept_ids or not _text(comment)
                                               for cid, comment in comments.items())):
        issues.append("concept_comments는 이번 평가 대상 concept_id와 짧은 최종 의견의 객체여야 한다.")
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
    context_identity = {k: identity[k] for k in ("inputs", "rounds", "domain_metadata", "domain",
                                               "personas", "role_seeds", "injected", "lang")}
    context_identity["reviewer_counts"] = [settings.cfg("evaluation.min_reviewers", 4),
                                           settings.cfg("evaluation.max_reviewers", 6)]
    context_hash = hashlib.sha256(json.dumps(context_identity, sort_keys=True, ensure_ascii=False,
                                            default=str).encode()).hexdigest()
    meeting = state.evaluation.meeting
    compatible = (meeting.input_hash == input_hash or meeting.context_hash == context_hash or
                  (not meeting.context_hash and _legacy_context_matches(state, common, rounds)))
    if not compatible or not state.evaluation.reviewers:
        meeting = EvaluationMeeting(input_hash=input_hash, context_hash=context_hash,
                                    rounds=rounds, status="RUNNING")
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
    meeting.input_hash, meeting.context_hash = input_hash, context_hash
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
                "dimensions": list(p.dimensions), "participant_roster": deepcopy(roster),
                "dimension_rubric": "\n".join(f"- {dim}: {DIMENSION_RUBRICS.get(dim, p.mandate)}"
                                               for dim in p.dimensions)}

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
            semantic_inputs = {k: v for k, v in inputs[p.persona_id].items()
                               if k not in ("followup_options", "summary_options", "dimension_rubric", "answer_evidence_options")}
            call_hash = hashlib.sha256(json.dumps(semantic_inputs, sort_keys=True,
                                                  ensure_ascii=False, default=str).encode()).hexdigest()
            saved = meeting.completed_calls.get(key)
            if (saved is not None and meeting.completed_call_inputs.get(key) == call_hash
                    and not check(saved)):
                return deepcopy(saved), call_hash
            def request(values, validate):
                normalize = _output_normalizer(name, values)
                data = agent.run_agent(
                    ctx, node=f"s8_review_{name}", label=f"{label}: {p.role_name}",
                    stage=Stage.S8.value, agent_id=f"persona::{p.persona_id}",
                    prompt_id=prompt_id, tier="T3", system_override=SYSTEM,
                    vars=values, checker=validate, rubric_id=rubric,
                    normalizer=normalize, repair_attempts=settings.cfg("evaluation.meeting_repair_attempts", 2),
                    facts=json.dumps({"review_context": values,
                                      "peer_statements_are_verified_facts": False},
                                     ensure_ascii=False) if rubric else "",
                    max_tokens=token_limit(p), temperature=0.2, default=None)
                data = normalize(data)
                issues = validate(data)
                if issues:
                    raise AbortRun(f"{label}: {p.role_name} 응답이 불완전합니다. {issues[0]}")
                return data

            if name == "final":
                batches = _final_batches(inputs[p.persona_id])
                data = {"scores": [], "communication_summary": [], "concept_comments": {}}
                for index, values in enumerate(batches):
                    batch_ids = set(values["review_concept_ids"])
                    validate = lambda d: [f"FATAL-MEETING: {issue}" for issue in _check_final(
                        d, p, batch_ids, values["meeting_transcript"],
                        summary_concept_ids=concept_ids,
                        require_summary=values["include_communication_summary"])]
                    batch_key = f"{key}:part:{index + 1}"
                    batch_inputs = {k: v for k, v in values.items() if k != "dimension_rubric"}
                    batch_hash = hashlib.sha256(json.dumps(batch_inputs, sort_keys=True,
                        ensure_ascii=False, default=str).encode()).hexdigest()
                    saved_batch = meeting.completed_calls.get(batch_key)
                    if (saved_batch is not None and meeting.completed_call_inputs.get(batch_key) == batch_hash
                            and not validate(saved_batch)):
                        part = deepcopy(saved_batch)
                    else:
                        part = request(values, validate)
                        if len(batches) > 1:
                            with ctx.lock:
                                meeting.completed_calls[batch_key] = deepcopy(part)
                                meeting.completed_call_inputs[batch_key] = batch_hash
                            ctx.persist()
                    data["scores"].extend(part["scores"])
                    data["communication_summary"].extend(part["communication_summary"])
                    data["concept_comments"].update(part.get("concept_comments", {}))
            else:
                data = request(inputs[p.persona_id], check)
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

    score_tokens = lambda p: max(4800, min(8000, int(settings.cfg("evaluation.meeting_review_max_tokens", 8000))))
    exchange_tokens = max(2400, min(8000, int(settings.cfg("evaluation.meeting_exchange_max_tokens", 4000))))
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
                                   "answer_evidence_options": [dict(evidence_key=f"E{i}", id=e["id"],
                                       concept_ids=e["concept_ids"], identifier=e["identifier"],
                                       question_ids=[q["question_id"] for q in inboxes[p.persona_id]
                                                     if q["concept_id"] in e["concept_ids"]])
                                       for i, e in enumerate(evidence_packet, 1)
                                       if any(q["concept_id"] in e["concept_ids"] for q in inboxes[p.persona_id])],
                                   "initial_review": initial[p.persona_id]},
                        lambda d, p: _check_answers(d, inboxes[p.persona_id], evidence),
                        lambda p: min(8000, max(exchange_tokens, 1000 + 650 * len(inboxes[p.persona_id]))),
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
                                        "followup_options": _reference_options(prior, p.persona_id)[0],
                                        "initial_review": initial[p.persona_id]},
                             check_followup, lambda p: exchange_tokens)
            add_questions(followup, number + 1)

    transcript = _transcript(meeting)
    final = phase("final", "회의: 소통 반영 최종 평가", PROMPTS[2],
                  lambda p: {**role_vars(p), "initial_review": initial[p.persona_id],
                             "summary_options": _reference_options(transcript, p.persona_id)[1],
                             "meeting_transcript": deepcopy(transcript), "meeting_gaps": []},
                  lambda d, p: _check_final(d, p, concept_ids, transcript),
                  score_tokens, rubric="R8_REVIEW")
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
            communication_summary=summaries, retained_concerns=retained,
            concept_comments=data.get("concept_comments", {})))
        all_scores.extend(scores)
    meeting.status = "COMPLETED"
    ctx.persist()
    ctx.emit("meeting_phase", phase="completed", label="다직군 회의 완료", rounds=rounds)
    return all_scores
