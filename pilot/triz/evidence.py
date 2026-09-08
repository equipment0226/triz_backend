"""Function-oriented patent discovery with explicit evidence provenance and query budgets."""
from concurrent.futures import ThreadPoolExecutor
from . import agent, digest, verify
from .schema import EvidenceCard
from .tools import scholar
from .settings import settings

def discover(ctx, before_concepts=False):
    st = ctx.state
    if not settings.cfg("evidence.enabled", True):
        return
    from .nodes import _applied_principles
    spent = st.scratch.setdefault("search_cache", {})
    limit = int(settings.cfg("evidence.max_queries_per_run", 16)) - len(spent)
    if limit <= 0:
        return
    count = min(limit, 4 if before_concepts else 12)
    result = agent.run_agent(ctx, node="s5_patent_plan" if before_concepts else "s9_evidence_plan",
        label="기능·모순 기반 검색 설계", stage=st.control.current_stage,
        agent_id="patent_researcher", prompt_id="P_EVIDENCE_PLAN", tier="T2",
        vars={"industry": st.domain.industry, "functions": digest.function_digest(st, only_problem=True),
              "contradictions": digest.contradictions_digest(st), "principles": _applied_principles(st),
              "transfer_domains": st.scratch.get("industry_profile", {}).get("transfer_domains", []),
              "concepts": [{"id": c.id, "title": c.title, "mechanism": c.working_principle} for c in st.concepts],
              "max_queries": count, "phase": "타산업 특허 우선 탐색" if before_concepts else "각 해결안의 논문과 특허를 각각 확보"},
        default={}) or {}
    plans = []
    for q in result.get("queries", []):
        if not isinstance(q, dict) or q.get("kind") not in ("PATENT", "PAPER") or not q.get("query"):
            continue
        key = q["kind"] + ":" + q["query"].strip().lower()
        if key not in spent and key not in [p[0] for p in plans]:
            plans.append((key, q))
        if len(plans) >= count:
            break
    def lookup(plan):
        key, q = plan
        hits = scholar.search_kind(q["query"], q["kind"], 4)
        return key, [{**hit, "scope": q.get("scope", "direct"),
                      "function_mapping": q.get("function_mapping", "")} for hit in hits]
    if plans:
        with ThreadPoolExecutor(max_workers=min(3, len(plans))) as pool:
            for key, hits in pool.map(lookup, plans):
                spent[key] = hits
    candidates = {r["identifier"].lower(): r for hits in spent.values() for r in hits}
    st.scratch["evidence_candidates"] = list(candidates.values())[:48]
    st.scratch["search_status"] = {
        "queries_used": len(spent), "query_limit": settings.cfg("evidence.max_queries_per_run", 16),
        "patent_provider_configured": bool(set(scholar.enabled_providers()) & {"patentsview", "tavily"}),
        "records": len(candidates)}
    ctx.persist()

def attach(ctx):
    st = ctx.state
    discover(ctx)
    records = st.scratch.get("evidence_candidates", [])
    st.scratch["patent_additions"] = []
    if not records or not st.concepts:
        st.scratch["evidence_gaps"] = [{"title": c.title, "missing": ["PATENT", "PAPER"]} for c in st.concepts]
        return
    result = agent.run_agent(ctx, node="s9_evidence_match", label="특허·논문 적용성 검토",
        stage=st.control.current_stage, agent_id="patent_researcher", prompt_id="P_EVIDENCE_MATCH", tier="T2",
        vars={"concepts": [{"id": c.id, "title": c.title, "mechanism": c.working_principle} for c in st.concepts],
              "candidates": [{"index": i, **r} for i, r in enumerate(records)],
              "constraints": verify.constraints_full(st), "max_additions": settings.cfg("evidence.max_patent_additions", 3)},
        default={}) or {}
    # Never convert generic search links or unselected hits into supporting evidence.
    for match in result.get("matches", []):
        if not isinstance(match, dict):
            continue
        i = match.get("index")
        concept = st.concept(match.get("concept_id", ""))
        if type(i) is not int or not 0 <= i < len(records) or not concept:
            continue
        try:
            confidence = float(match.get("confidence", 0))
        except (ValueError, TypeError):
            continue
        if confidence < .7 or not match.get("mechanism_mapping") or not match.get("transfer_conditions"):
            continue
        r = records[i]
        card = next((e for e in st.evidence if e.identifier == r["identifier"]), None)
        if card is None:
            card = EvidenceCard(title=r["title"], identifier=r["identifier"], url=r["url"],
                year=r["year"], source_type=r["source_type"], snippet=r["snippet"], provider=r["provider"],
                claim=match["mechanism_mapping"], relevance=confidence, verified=True,
                evidence_scope="검색 공급자 메타데이터 확인; 청구항·성능 검증 별도", idea_ids=[concept.id])
            st.evidence.append(card)
        if card.id not in concept.evidence_ids:
            concept.evidence_ids.append(card.id)
        concept.transfer_conditions += [str(x) for x in match["transfer_conditions"] if str(x) not in concept.transfer_conditions]
    for addition in result.get("additions", [])[:int(settings.cfg("evidence.max_patent_additions", 3))]:
        if not isinstance(addition, dict):
            continue
        i = addition.get("index")
        if type(i) is not int or not 0 <= i < len(records) or records[i]["source_type"] != "PATENT":
            continue
        if not addition.get("how_it_differs") or not addition.get("transfer_conditions"):
            continue
        st.scratch["patent_additions"].append({**addition, "reference": records[i],
                                              "status": "추가 검증 후보 · 제약·다직군 평가 전"})
    st.scratch["evidence_gaps"] = []
    for c in st.concepts:
        kinds = {e.source_type for e in st.evidences(c.evidence_ids) if e.verified and e.identifier}
        missing = sorted({"PATENT", "PAPER"} - kinds)
        if missing:
            st.scratch["evidence_gaps"].append({"title": c.title, "missing": missing})
    ctx.persist()
