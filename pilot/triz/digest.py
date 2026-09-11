"""State 슬라이스/다이제스트: 노드에 넘길 최소 정보만 만든다 (토큰 절감)."""
from __future__ import annotations

from .schema import GlobalState
from collections import defaultdict


def target_system(s):
    chosen = s.confirm.chosen() if s.confirm.user_confirmed else None
    return chosen.name if chosen else s.domain.target_system


def facts_packet(s):
    return {"user_query": s.raw_query, "frame": frame_digest(s),
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


def select_ideas(ideas, limit=40):
    """Round-robin by addressed problem and mechanism/track, never by completion order."""
    groups = defaultdict(list)
    for idea in ideas:
        groups[(tuple(sorted(idea.addresses)), idea.mechanism_key or idea.track)].append(idea)
    result = []
    while groups and len(result) < limit:
        for key in list(groups):
            result.append(groups[key].pop(0))
            if not groups[key]:
                del groups[key]
            if len(result) >= limit:
                break
    return result


def idea_packet(i):
    packet = i.model_dump(exclude={"detail"}, exclude_defaults=True)
    fields = ("self_rebuttal", "conditions", "adaptation_note", "new_risk", "how",
              "principle", "transformation", "removed_harm", "resolution_argument", "ariz_verdict",
              "standard_code", "standard_title", "source_su_id", "catalog_transformation",
              "source_effect_id", "effect_name", "catalog_function", "catalog_conditions",
              "catalog_limitations", "catalog_sources", "catalog_evidence_level", "catalog_mechanism_key")
    packet["support"] = {k: i.detail[k] for k in fields if i.detail.get(k)}
    if i.detail.get("source_details"):
        packet["support"]["source_details"] = [
            {k: source[k] for k in ("source_idea_id", *fields) if source.get(k)}
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
                   + (f" (영향: {e.parameter_affected})" if e.parameter_affected else ""))
    return out


def basic_function(s: GlobalState) -> str:
    for e in s.analysis.function_edges:
        if e.rank == "BASIC":
            return f"{e.subject} → {e.action} → {e.object}"
    return s.domain.target_system


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
