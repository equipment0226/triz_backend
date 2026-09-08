"""State 슬라이스/다이제스트: 노드에 넘길 최소 정보만 만든다 (토큰 절감)."""
from __future__ import annotations

from .schema import GlobalState


def domain_brief(s: GlobalState) -> dict:
    d = s.domain
    return {"industry": d.industry, "sub_domain": d.sub_domain, "job_family": d.job_family,
            "target_system": d.target_system, "super_system": d.super_system,
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
    return [n.text for n in s.analysis.ceca.nodes if n.is_contradiction_seed]


def ceca_roots(s: GlobalState) -> list[str]:
    if not s.analysis.ceca:
        return []
    return [n.text for n in s.analysis.ceca.nodes if n.node_type == "ROOT_CAUSE"]


def ceca_keys(s: GlobalState) -> list[str]:
    if not s.analysis.ceca:
        return []
    return [n.text for n in s.analysis.ceca.nodes if n.node_type == "KEY_DISADVANTAGE"]


def contradictions_digest(s: GlobalState) -> list[str]:
    out = []
    for t in s.definition.technical_contradictions:
        out.append(f"{t.id} [기술적] {t.if_action} → 개선 #{t.improving_param_id} / 악화 #{t.worsening_param_id} : {t.label}")
    for p in s.definition.physical_contradictions:
        out.append(f"{p.id} [물리적] {p.element}의 {p.parameter}: '{p.state_a}' vs '{p.state_b}'")
    return out


def ideas_digest(s: GlobalState, limit: int = 40) -> list[str]:
    return [f"{i.id} [{i.track}/{i.source_ref}] {i.title}: {i.idea}" for i in s.solve.raw_ideas[:limit]]


def concepts_blind(s: GlobalState) -> list[dict]:
    """평가자용 — TRIZ 출처를 제거한 개념 정보 (Context Isolation)."""
    return [
        {"concept_id": c.id, "title": c.title, "one_liner": c.one_liner,
         "description": c.description, "working_principle": c.working_principle,
         "changes_to_system": c.changes_to_system, "required_resources": c.required_resources,
         "expected_effect": c.expected_effect, "assumptions": c.assumptions,
         "open_risks": c.open_risks, "has_external_evidence": bool(c.evidence_ids)}
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
