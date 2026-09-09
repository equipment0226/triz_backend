"""Bounded concept allocation and one independent audit of the whole portfolio."""
from concurrent.futures import ThreadPoolExecutor
from . import agent, digest, rag, verify
from .coerce import build
from .schema import ConceptSpec, Stage
from .settings import settings


def generate_concepts(ctx):
    st = ctx.state
    ctx.set_stage(Stage.S6.value)
    target = max(1, int(settings.cfg("solutions.max_concepts", 12)))
    ideas = digest.select_ideas([i for i in st.solve.raw_ideas if i.resolution_status != "TRADEOFF"], target)
    prior_limit = max(0, int(settings.cfg("feedback_rag.max_influenced_concepts", 3)))
    prior = rag.prior_cases_block(st) if prior_limit else ""
    groups = []
    cursor = 0
    while cursor < len(ideas):
        size = min(5, prior_limit) if not groups and prior else 5
        groups.append(ideas[cursor:cursor + size])
        cursor += size
    facts = digest.facts_packet(st)
    contradictions = digest.contradictions_digest(st)

    def generate(item):
        number, assigned = item
        batch_prior = prior if number == 0 else ""
        result = agent.run_agent(ctx, node="s6_concept", label=f"해결 개념 구체화 ({number+1}/{len(groups)})",
            stage=Stage.S6.value, agent_id="concept_architect", prompt_id="P_S6_CONCEPT", tier="T2",
            max_tokens=8000, vars={"industry": st.domain.industry, "target_system": digest.target_system(st),
                "super_system": st.domain.super_system, "operating_env": st.domain.operating_env,
                "components": digest.components_digest(st), "resources": digest.resources_digest(st),
                "facts": facts, "contradictions": contradictions,
                "ideas": [digest.idea_packet(i) for i in assigned],
                "evidence_digest": digest.relevant_evidence(st, assigned),
                "prior_cases_block": batch_prior, "taboo_block": verify.taboo_block(st),
                "batch_size": len(assigned),
                "batch_note": "배정된 아이디어당 최대 1개. 다른 배치의 아이디어를 만들지 않는다. 성립하지 않으면 excluded에 기록한다."},
            default={}) or {}
        return assigned, result, bool(batch_prior)

    made, excluded, seen = [], [], set()
    valid_contra = {c['id'] for c in contradictions}
    with ThreadPoolExecutor(max_workers=max(1, int(settings.cfg("run.parallel_workers", 4)))) as pool:
        results = list(pool.map(generate, enumerate(groups)))
    for assigned, data, prior_allowed in results:
        allowed = {i.id: i for i in assigned}
        used_sources = set()
        for raw in data.get("concepts", [])[:len(assigned)]:
            c = build(ConceptSpec, raw)
            if not c or not c.title:
                continue
            # Do not silently attach a generated concept to a different mechanism.
            source_ids = set(c.source_idea_ids)
            if not source_ids or not source_ids <= allowed.keys() or source_ids & used_sources:
                excluded.append({"idea": c.title, "reason": "배정 아이디어 출처 누락·불일치·중복"})
                continue
            sources = [allowed[i] for i in sorted(source_ids)]
            key = tuple(sorted(i.mechanism_key or i.id for i in sources))
            if key in seen:
                excluded.append({"idea": c.title, "reason": "동일 메커니즘 중복"})
                continue
            seen.add(key)
            used_sources.update(source_ids)
            c.mechanism_key = " + ".join(key)
            c.quality_status = "UNVERIFIED"  # generator cannot approve itself
            c.assumptions = list(dict.fromkeys(c.assumptions + [condition for i in sources for condition in i.conditions]))
            c.hypothesis_ids = list(dict.fromkeys(c.hypothesis_ids + [h for i in sources for h in i.hypothesis_ids]))
            c.addresses_contradictions = [i for i in c.addresses_contradictions if i in valid_contra]
            c.evidence_ids = [i for i in c.evidence_ids if any(e.id == i for e in st.evidence)]
            # Search metadata supplied during generation does not establish maturity.
            if not c.evidence_ids:
                c.maturity = "CONCEPT"
            if not prior_allowed:
                c.prior_case_ids = []
            elif not c.prior_case_ids:
                c.prior_case_ids = list(st.scratch.get("prior_case_ids", []))
            else:
                c.prior_case_ids = [i for i in c.prior_case_ids if i in st.scratch.get("prior_case_ids", [])]
            made.append(c)
        excluded.extend(data.get("excluded") or [])
    st.concepts = made[:target]
    st.scratch["excluded_concepts"] = excluded
    audit_concepts(ctx)
    ctx.emit("artifact", kind="CONCEPTS", data={"count": len(st.concepts), "titles": [c.title for c in st.concepts]})
    if len(st.concepts) < int(settings.cfg("solutions.min_concepts", 8)):
        ctx.warn("충분한 근거를 가진 개념만 유지했습니다. 후보 개수보다 모순 해소와 검증 가능성을 우선합니다.")
    ctx.persist()


def audit_concepts(ctx):
    st = ctx.state
    if not st.concepts:
        return
    step = ctx.start_step(node="s6_quality", label="전체 개념의 독립 품질 검토", stage=Stage.S6.value,
                          agent_id="independent_auditor", prompt_id="P_VERIFIER_GENERIC", tier="T3")
    packets = [{"concept_id": c.id, "title": c.title, "working_principle": c.working_principle,
        "changes_to_system": c.changes_to_system, "required_resources": c.required_resources,
        "addresses_contradictions": c.addresses_contradictions, "resolution_argument": c.resolution_argument,
        "expected_effect": c.expected_effect, "assumptions": c.assumptions, "open_risks": c.open_risks,
        "validation_plan": c.validation_plan, "transfer_conditions": c.transfer_conditions} for c in st.concepts]
    step.input_slice = {"concepts": packets, "facts": digest.facts_packet(st)}
    verdict = agent.verify_artifact(ctx, "R6_CONCEPT", {"concepts": packets}, "후보별 판단을 per_concept에 반드시 기록한다.")
    usage = verdict.pop("_tokens", None)
    if usage:
        step.tokens_in, step.tokens_out, step.cost_usd = usage
    rows = verdict.get("per_concept") or []
    by_id = {r.get("concept_id"): r for r in rows if isinstance(r, dict)}
    localized_fatal = any(r.get("fatal_flaws") or r.get("verdict") == "REJECT" for r in by_id.values())
    retained = []
    for c in st.concepts:
        row = by_id.get(c.id, {})
        status = row.get("verdict", "UNVERIFIED")
        if status not in ("PASS", "REVISE", "REJECT"):
            status = "UNVERIFIED"
        if verdict.get("verdict") == "UNVERIFIED":
            status = "UNVERIFIED"
        issues = row.get("issues") or []
        if not isinstance(issues, list):
            issues = [issues]
        if row.get("fatal_flaws"):
            status = "REJECT"
            flaws = row["fatal_flaws"]
            issues += flaws if isinstance(flaws, list) else [flaws]
        # Global fatal judgement without item locations cannot become a silent pass.
        if verdict.get("fatal_flaws") and not localized_fatal:
            flaws = verdict["fatal_flaws"]
            status, issues = "REJECT", flaws if isinstance(flaws, list) else [flaws]
        c.quality_status, c.quality_issues = status, [str(i) for i in issues]
        if not c.resolution_argument or not c.validation_plan or not c.addresses_contradictions:
            if status != "REJECT":
                c.quality_status = "REVISE"
            c.quality_issues.append("모순 해소 근거·대상 모순·검증 계획을 모두 명시해야 한다.")
        known = {verify._norm_resource(r.name) for r in st.analysis.resources if r.name}
        for name in c.required_resources:
            normalized = verify._norm_resource(name)
            if name and not name.startswith("신규:") and normalized not in known:
                if c.quality_status != "REJECT":
                    c.quality_status = "REVISE"
                c.quality_issues.append(f"기존 자원 확인 또는 신규 도입 표시 필요: {name}")
        if c.quality_status == "REJECT":
            st.scratch.setdefault("excluded_concepts", []).append({"idea": c.title, "reason": "; ".join(c.quality_issues) or "독립 품질 검토 REJECT"})
        else:
            retained.append(c)
    st.concepts = retained
    step.output_json = verdict
    step.verdicts = [verdict]
    ctx.finish_step(step, "OK" if verdict.get("verdict") == "PASS" else "WARN")
