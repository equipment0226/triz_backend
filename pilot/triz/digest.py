"""State 슬라이스/다이제스트: 노드에 넘길 최소 정보만 만든다 (토큰 절감)."""
from __future__ import annotations

from .schema import GlobalState
from collections import defaultdict


def target_system(s):
    chosen = s.confirm.chosen() if s.confirm.user_confirmed else None
    return chosen.name if chosen else s.domain.target_system


def facts_packet(s):
    """Keep legacy paths while distinguishing direct reports from model summaries.

    `observations` and `confirmed_facts` are historical field names, not proof of
    observation. A generated intake frame must never authenticate its own claims.
    """
    return {"source_contract": {
                "version": "source-provenance-v1-20261008",
                "meaning": "observations는 입력 묶음 이름일 뿐 모든 항목이 직접 관측이라는 뜻이 아니다.",
                "priority": "최신 명시 사용자 수정·답변과 원문을 우선한다. 첨부 추출은 원자료 범위를 확인하고, 생성 요약은 독립 근거로 쓰지 않는다.",
                "direct_report_paths": ["user_query", "answers", "deep_dive_answers",
                                        "deep_dive_answer_turns", "amendments"],
                "generated_summary_paths": ["frame", "confirmed_facts"],
                "report_modality": "사용자 응답도 의견·가능성·목표·실제 관측을 구별한다. 질문의 전제나 미응답은 사용자 확인 사실이 아니다.",
                "history_rule": "시도·실패·운영 이력은 원문 또는 사용자 답변의 직접 인용이 있어야 한다. '작동하지 않을 것이다/현실에서 안 통한다'는 의견을 '시도해서 실패했다'는 이력으로 바꾸지 않는다.",
                "summary_rule": "frame.prior_attempts와 confirmed_facts의 필드 이름은 확인 증거가 아니다. 직접 근거가 없거나 원문과 충돌하면 해당 요약 주장은 미확인/가설로 남긴다.",
            },
            "source_provenance": {
                "user_query": "USER_REPORTED",
                "answers": "USER_REPORTED_ANSWERS_WITH_QUESTION_CONTEXT",
                "deep_dive_answers": "USER_REPORTED",
                "deep_dive_answer_turns": "USER_REPORTED_ANSWERS_WITH_QUESTION_CONTEXT",
                "amendments": "USER_REPORTED_CORRECTIONS",
                "attachments": "EXTRACTED_FROM_USER_ATTACHMENT",
                "frame": "MODEL_GENERATED_SUMMARY_NOT_DIRECT_OBSERVATION",
                "confirmed_facts": "MODEL_GENERATED_SYNTHESIS_REQUIRES_PRIMARY_SUPPORT",
                "confirmed_boundary": ("USER_CONFIRMED_DEFINITION_NOT_EVENT_OBSERVATION"
                    if s.confirm.user_confirmed and s.confirm.chosen() else "MODEL_PROPOSED_BOUNDARY"),
            },
            "baseline_facts": [fact.model_dump() for fact in s.constraints.baseline_facts],
            "baseline_policy": "현재 상태·측정·현황의 원문 근거다. 개선 후에도 이 값을 유지해야 하는 의무가 아니다. 실제 설계 하중·계측 오차·운영 조건은 해법 검증의 맥락에 계속 반영한다.",
            "user_query": s.raw_query, "frame": frame_digest(s),
            "attachments": attachment_facts(s), "answers": clarify_history(s),
            "deep_dive_answers": s.scratch.get("deep_dive", {}).get("answers", []),
            "deep_dive_answer_turns": s.scratch.get("deep_dive", {}).get("answer_turns", []),
            "confirmed_facts": s.scratch.get("deep_dive", {}).get("confirmed_facts", []),
            "confirmed_boundary": target_system(s), "amendments": s.confirm.user_amendments}


def causal_packet(s):
    if not s.analysis.ceca:
        return []
    nodes = s.analysis.ceca.nodes
    wanted = {n.id for n in nodes if n.is_contradiction_seed or n.node_type in ("KEY_DISADVANTAGE", "ROOT_CAUSE")}
    by_id = {n.id: n for n in nodes}
    pending = list(wanted)
    while pending:
        for parent in by_id[pending.pop()].parents:
            if parent in by_id and parent not in wanted:
                wanted.add(parent)
                pending.append(parent)
    return [n.model_dump(exclude_defaults=True) for n in nodes if n.id in wanted]


def idea_tracks(idea):
    """Keep every originating track when a curator combines source ideas."""
    tracks = idea.detail.get("source_tracks", [])
    tracks = list(tracks) if isinstance(tracks, list) else []
    tracks.extend(source.get("source_track", "") for source in idea.detail.get("source_details", [])
                  if isinstance(source, dict))
    tracks.append(idea.track)
    return tuple(dict.fromkeys(t for t in tracks if isinstance(t, str) and t)) or ("",)


def select_ideas(ideas, limit=40):
    """Balance source tracks, then problems and mechanisms within the existing cap.

    Unique mechanism keys must not turn selection into a prefix of the A-to-H
    execution order. This chooses inputs for review, not recommended solutions.
    """
    pending = [(i, idea, idea_tracks(idea), tuple(sorted(idea.addresses)),
                idea.mechanism_key or idea.id) for i, idea in enumerate(ideas)]
    track_counts, problem_counts, mechanism_counts = defaultdict(int), defaultdict(int), defaultdict(int)
    result = []
    while pending and len(result) < limit:
        chosen = min(pending, key=lambda row: (
            min(track_counts[t] for t in row[2]), problem_counts[row[3]],
            mechanism_counts[row[4]], row[0]))
        pending.remove(chosen)
        _, idea, tracks, problem, mechanism = chosen
        result.append(idea)
        for track in tracks:
            track_counts[track] += 1
        problem_counts[problem] += 1
        mechanism_counts[mechanism] += 1
    return result


def idea_packet(i):
    packet = i.model_dump(exclude={"detail"}, exclude_defaults=True)
    fields = ("self_rebuttal", "conditions", "adaptation_note", "new_risk", "how",
              "principle", "transformation", "removed_harm", "resolution_argument", "ariz_verdict",
              "standard_code", "standard_title", "source_su_id", "catalog_transformation",
              "source_effect_id", "effect_name", "catalog_function", "catalog_conditions",
              "catalog_limitations", "catalog_sources", "catalog_evidence_level", "catalog_mechanism_key")
    packet["support"] = {k: i.detail[k] for k in fields if i.detail.get(k)}
    # Versioned Track B provenance must reach S6, including BYPASS's meaningful
    # empty recommendation list. Leave historical, unversioned packets intact.
    separation_fields = ("kind", "source_pc_id", "supporting_principles", "catalog_version",
                         "approach_name", "approach_family", "recommended_principles",
                         "principle_selection_policy", "principle_selection_status",
                         "principle_selection_reason")
    def separation_support(source):
        if not source.get("catalog_version") or not source.get("approach_family"):
            return {}
        return {key: source[key] for key in separation_fields if key in source}
    packet["support"].update(separation_support(i.detail))
    packet["support"]["source_tracks"] = [track for track in idea_tracks(i) if track]
    if i.detail.get("source_details"):
        packet["support"]["source_details"] = [
            {**{k: source[k] for k in ("source_idea_id", "source_track", *fields) if source.get(k)},
             **separation_support(source)}
            for source in i.detail["source_details"]]
    return packet


def relevant_evidence(s, ideas=(), limit=6):
    import re
    query = " ".join(i.idea + " " + i.mechanism for i in ideas) or s.intake.frame.symptom
    terms = set(re.findall(r"[\w]{2,}", query.lower()))
    records = s.scratch.get("evidence_candidates", [])
    ranked = sorted(records, key=lambda r: -len(terms & set(re.findall(r"[\w]{2,}",
        (r.get("title", "") + " " + r.get("snippet", "") + " " + r.get("function_mapping", "")).lower()))))
    return [{k: r.get(k, "") for k in ("identifier", "title", "snippet", "scope", "function_mapping")}
            for r in ranked[:limit]]


def domain_brief(s: GlobalState) -> dict:
    d = s.domain
    return {"industry": d.industry, "sub_domain": d.sub_domain, "job_family": d.job_family,
            "target_system": target_system(s), "problem_type": d.problem_type, "super_system": d.super_system,
            "operating_env": d.operating_env, "legacy": d.legacy_note}


def components_digest(s: GlobalState) -> list[str]:
    return [f"{c.name}({c.level})" + (f" - {c.role}" if c.role else "") for c in s.analysis.components]


def function_digest(s: GlobalState, only_problem: bool = False) -> list[str]:
    out = []
    for e in s.analysis.function_edges:
        if only_problem and e.kind == "USEFUL" and e.level == "NORMAL":
            continue
        mark = "유해" if e.kind == "HARMFUL" else "유익"
        lvl = {"INSUFFICIENT": "부족", "NORMAL": "적정", "EXCESSIVE": "과잉"}[e.level]
        out.append(f"[{mark}/{lvl}/{e.rank}] {e.subject} → {e.action} → {e.object}"
                   + (f" (영향: {e.parameter_affected})" if e.parameter_affected else "")
                   + _function_evidence(e))
    return out


def _function_evidence(edge) -> str:
    """Keep epistemic status independent of usefulness/rank/performance level."""
    status = getattr(edge, "evidence_status", "HYPOTHESIS")
    refs = getattr(edge, "evidence_refs", [])
    notes = getattr(edge, "notes", "")
    return (f" [근거 상태: {status}]"
            + (f" [출처: {'; '.join(refs)}]" if refs else "")
            + (f" [해석·조건: {notes}]" if notes else ""))


def basic_function(s: GlobalState) -> str:
    from .context import AbortRun
    basics = [edge for edge in s.analysis.function_edges if edge.rank == "BASIC"]
    names = {component.name for component in s.analysis.components}
    if (len(basics) != 1 or basics[0].kind != "USEFUL" or
            any(not getattr(basics[0], key).strip() for key in
                ("subject", "action", "object", "parameter_affected")) or
            basics[0].subject not in names or basics[0].object not in names):
        raise AbortRun("유효한 주기능(BASIC)이 없어 다음 분석을 진행할 수 없습니다. 기능 분석부터 다시 실행해 주세요.")
    edge = basics[0]
    return (f"{edge.subject} → {edge.action} → {edge.object} (유지·변경 속성: {edge.parameter_affected})"
            + _function_evidence(edge))


def resources_digest(s: GlobalState, include_blocked: bool = False) -> list[str]:
    from .render import AVAIL_KO, RESOURCE_KO, WHERE_KO

    out = []
    for r in s.analysis.resources:
        if r.blocked_by_constraint and not include_blocked:
            continue
        tag = (f"{RESOURCE_KO.get(r.category, r.category)}/"
               f"{WHERE_KO.get(r.where, r.where)}/"
               f"{AVAIL_KO.get(r.availability, r.availability)}")
        out.append(f"{r.name} [{tag}]"
                   + (f" → {', '.join(r.usable_for[:2])}" if r.usable_for else ""))
    return out


def su_fields_digest(s: GlobalState) -> list[str]:
    return [f"{m.id} {m.label}: S1={m.s1} / S2={m.s2 or '없음'} / F={m.field or '없음'} "
            f"({m.completeness}, {m.effect})" for m in s.analysis.su_fields]


def negative_interactions(s: GlobalState) -> list[str]:
    im = s.analysis.interaction_matrix
    if not im:
        return []
    return [f"{c.a} ↔ {c.b} [{c.sign}] {c.note}" for c in im.cells if c.sign in ("-", "+-")]


def ceca_seeds(s: GlobalState) -> list[str]:
    if not s.analysis.ceca:
        return []
    return causal_packet(s)


def ceca_roots(s: GlobalState) -> list[str]:
    if not s.analysis.ceca:
        return []
    return [n.text for n in s.analysis.ceca.nodes if n.node_type == "ROOT_CAUSE"]


def ceca_keys(s: GlobalState) -> list[str]:
    if not s.analysis.ceca:
        return []
    return [n.text for n in s.analysis.ceca.nodes if n.node_type == "KEY_DISADVANTAGE"]


def contradictions_digest(s: GlobalState) -> list[dict]:
    from . import knowledge as K
    out = []
    for t in s.definition.technical_contradictions:
        out.append(dict(t.model_dump(), improving_definition=K.params(t.param_scheme).get(str(t.improving_param_id), {}),
                        worsening_definition=K.params(t.param_scheme).get(str(t.worsening_param_id), {})))
    for p in s.definition.physical_contradictions:
        out.append(p.model_dump())
    return out


def ideas_digest(s: GlobalState, limit: int = 40) -> list[dict]:
    return [idea_packet(i) for i in select_ideas(s.solve.raw_ideas, limit)]


def concepts_blind(s: GlobalState) -> list[dict]:
    """평가자용 — TRIZ 출처를 제거한 개념 정보 (Context Isolation)."""
    return [
        {"concept_id": c.id, "title": c.title, "one_liner": c.one_liner,
         "description": c.description, "working_principle": c.working_principle,
         "changes_to_system": c.changes_to_system, "required_resources": c.required_resources,
         "expected_effect": c.expected_effect, "assumptions": c.assumptions,
         "open_risks": c.open_risks, "validation_plan": c.validation_plan,
         "resolution_argument": c.resolution_argument, "transfer_conditions": c.transfer_conditions,
         "quality_status": c.quality_status, "quality_issues": c.quality_issues,
         "has_external_evidence": bool(c.evidence_ids)}
        for c in s.concepts
    ]


def concepts_for_gate(s: GlobalState) -> list[dict]:
    return [
        {"concept_id": c.id, "title": c.title, "description": c.description,
         "changes_to_system": c.changes_to_system, "required_resources": c.required_resources,
         "expected_effect": c.expected_effect, "assumptions": c.assumptions}
        for c in s.concepts
    ]


def concepts_digest(s: GlobalState) -> list[str]:
    return [f"{c.id}: {c.title} — {c.one_liner}" for c in s.concepts]


def evidence_digest(s: GlobalState) -> list[str]:
    return [f"{e.id} [{e.source_type}/{e.reliability}] {e.title or e.claim}" for e in s.evidence]


def frame_digest(s: GlobalState) -> dict:
    f = s.intake.frame
    return {"restated": f.restated_problem, "symptom": f.symptom, "when_where": f.when_where,
            "success_criteria": f.success_criteria, "prior_attempts": f.prior_attempts}


def attachment_facts(s: GlobalState) -> list[str]:
    out: list[str] = []
    for a in s.intake.attachments:
        out.append(f"[{a.filename}/{a.kind}]")
        out += [f"  - {x}" for x in a.extracted_facts[:25]]
    return out


def clarify_history(s: GlobalState) -> list[str]:
    return [f"Q: {t.question}\nA: {t.user_answer or '(무응답)'}" for t in s.intake.clarify_turns]
