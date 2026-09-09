"""동적 페르소나 팩토리: 도메인 시드 + LLM 생성 병합."""
from __future__ import annotations

from . import agent, digest, domain
from .context import RunContext
from .schema import Persona, Stage
from .settings import settings


def _seed_group(industry: str, job_family: str, is_engineering: bool) -> str:
    if not is_engineering:
        return "business"
    text = f"{industry} {job_family}".lower()
    for rule in settings.personas.get("industry_map", []):
        if any(k.lower() in text for k in rule.get("keywords", [])):
            return rule["group"]
    return "equipment_process" if is_engineering else "business"


def seed_personas(state) -> list[dict]:
    kind = domain.problem_type(state)
    group = {"ORGANIZATIONAL_BUSINESS": "business", "INFORMATION_SOFTWARE": "software_service"}.get(kind)
    group = group or _seed_group(state.domain.industry, state.domain.job_family, state.domain.is_engineering)
    seeds = settings.personas.get("seeds", {})
    base = list(seeds.get(group, [])) or list(seeds.get("default", []))
    domain_roles = [{"role_name": role, "mandate": "도메인 이론과 적용 조건 및 반증 실험을 검토한다",
                     "dimensions": ["FEASIBILITY", "QUALITY"]}
                    for role in state.scratch.get("industry_profile", {}).get("roles", [])]
    return domain_roles + base


def _needs_safety(state) -> bool:
    kws = settings.personas.get("rules", {}).get("safety_keywords", [])
    blob = " ".join([state.raw_query, state.domain.operating_env, state.domain.industry] +
                    [c.statement for c in state.constraints.items]).lower()
    return any(k.lower() in blob for k in kws)


def build_personas(ctx: RunContext) -> list[Persona]:
    state = ctx.state
    seeds = seed_personas(state)
    lo = int(settings.cfg("evaluation.min_reviewers", 4))
    hi = int(settings.cfg("evaluation.max_reviewers", 6))

    data = agent.run_agent(
        ctx,
        node="s8_persona_factory",
        label="검토 페르소나 생성",
        stage=Stage.S8.value,
        agent_id="role_router",
        prompt_id="P_PERSONA_FACTORY",
        tier="T1",
        vars={
            "industry": state.domain.industry,
            "job_family": state.domain.job_family,
            "target_system": state.domain.target_system,
            "constraints_digest": [c.statement for c in state.constraints.items],
            "concepts_digest": digest.concepts_digest(state),
            "seed_roles": seeds,
            "min_reviewers": lo,
            "max_reviewers": hi,
        },
        default={"personas": []},
    ) or {}

    drafts = data.get("personas") or []
    if not drafts:
        drafts = seeds

    personas: list[Persona] = []
    seen: set[str] = set()
    for d in drafts:
        role = (d.get("role_name") or "").strip()
        if not role or role in seen:
            continue
        seen.add(role)
        personas.append(Persona(
            role_name=role,
            seniority=d.get("seniority") or "15년 경력",
            mandate=d.get("mandate") or "",
            dimensions=[x for x in (d.get("dimensions") or ["FEASIBILITY"])][:2],
            bias_note=d.get("bias_note") or "",
            veto_power=bool(d.get("veto_power")),
        ))
        if len(personas) >= hi:
            break

    required = set(settings.personas.get("rules", {}).get("always_dimensions", []))
    required.update(("GOAL", "RESOLUTION", "CAUSAL"))
    if domain.problem_type(state) == "ORGANIZATIONAL_BUSINESS":
        required.add("ADOPTION")
    if _needs_safety(state) or any(p.veto_power for p in personas):
        required.add("SAFETY")
        if not any("SAFETY" in p.dimensions for p in personas):
            personas.append(Persona(role_name="안전·규제 검토역", dimensions=["SAFETY"], veto_power=True))
    # Reserve mandatory perspectives before applying the reviewer cap.
    hi = max(1, hi)
    selected, remaining = [], set(required)
    pool = list(personas)
    while pool and len(selected) < hi:
        best = max(pool, key=lambda p: (len(remaining.intersection(p.dimensions)), p.veto_power))
        pool.remove(best)
        selected.append(best)
        remaining.difference_update(best.dimensions)
    while len(selected) < min(lo, hi):
        selected.append(Persona(role_name=f"문제 해결 검토역 {len(selected)+1}", dimensions=[]))
    for dim in sorted(remaining):
        reviewer = min(selected, key=lambda p: len(p.dimensions))
        reviewer.dimensions.append(dim)
        reviewer.mandate += f" {dim}의 근거와 실패 조건을 검토한다."
        if dim == "SAFETY":
            reviewer.veto_power = True
    return selected
