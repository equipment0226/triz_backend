"""에이전트 실행기: 생성 → 결정론 검사 → 루브릭 검증 → 수리/승급 → 커밋."""
from __future__ import annotations

import json
import hashlib
import time
from typing import Any, Callable, Optional

from . import llm, prompts_registry as P, verify
from .context import RunContext, AbortRun, ProviderUnavailable
from .settings import settings

TIER_ORDER = ["T1", "T3", "T2"]

def routed_tier(node, requested="T2"):
    if node.startswith("s8_review"):
        return "T3"
    if node in ("s0_bootstrap", "s1_extract", "s1_clarify", "s8_persona_factory",
                "s9_narrative", "s10_distill"):
        return "T1"
    return "T2"

def tracked_chat(ctx, **kwargs):
    """Reserve worst-case request cost before parallel calls; stop without downgrading reasoning."""
    node = kwargs.pop("_node", "independent_verifier")
    deadline = ctx.state.scratch.get("execution_deadline")
    if deadline and time.time() >= deadline:
        raise AbortRun("분석 실행 시간 예산에 도달했습니다. 이어서 실행하면 새 시간 예산으로 재개합니다.")
    tc = settings.tiers[kwargs.get("tier", "T2")]
    max_output = kwargs.get("max_tokens") or tc.max_tokens
    # UTF-8 bytes are a conservative token upper bound; include retry payload overhead.
    input_bound = len((kwargs["system"] + kwargs["user"]).encode("utf-8")) + 16000
    reserve = (input_bound * tc.cost_in + max_output * tc.cost_out) / 1_000_000 * settings.max_retries
    with ctx.lock:
        if ctx.budget.get("provider_status"):
            raise ProviderUnavailable(ctx.budget["provider_status"])
        reserved = ctx.budget["reserved"]
        if ctx.state.cost.total_usd + reserved + reserve > ctx.state.cost.budget_usd:
            raise AbortRun("호출 예산에 도달했습니다. 예산을 조정한 뒤 이어서 실행할 수 있습니다.")
        ctx.budget["reserved"] = reserved + reserve
    res = None
    try:
        with ctx.call_slots:
            with ctx.lock:
                if ctx.budget.get("provider_status"):
                    raise ProviderUnavailable(ctx.budget["provider_status"])
            if deadline and time.time() >= deadline:
                raise AbortRun("분석 실행 시간 예산에 도달했습니다.")
            try:
                res = llm.chat_json(**kwargs)
            except llm.LLMError as exc:
                res = getattr(exc, "usage", None)
                if exc.terminal:
                    # Publish before releasing the slot so queued roles/tracks stop too.
                    with ctx.lock:
                        ctx.budget["provider_status"] = exc.status_code
                    raise ProviderUnavailable(exc.status_code, usage=res) from exc
                raise
        return res
    except llm.LLMError as exc:
        res = getattr(exc, "usage", None)
        raise
    finally:
        with ctx.lock:
            ctx.budget["reserved"] -= reserve
            if res:
                ctx.state.cost.request_count += res.meta.get("attempt") or len(res.meta.get("requests", [])) or 1
                ctx.state.cost.total_usd += res.cost_usd
                ctx.state.cost.tokens_in += res.tokens_in
                ctx.state.cost.tokens_out += res.tokens_out
                tier = kwargs.get("tier", "T2")
                stage = ctx.state.control.current_stage
                ctx.state.cost.by_tier[tier] = ctx.state.cost.by_tier.get(tier, 0) + res.cost_usd
                ctx.state.cost.by_stage[stage] = ctx.state.cost.by_stage.get(stage, 0) + res.cost_usd
                ctx.state.cost.over_budget = ctx.state.cost.total_usd > ctx.state.cost.budget_usd
        if res:
            from . import store
            store.save_call(ctx.state.run_id, {"node": node, "request": kwargs,
                "response": res.text, "tokens_in": res.tokens_in, "tokens_out": res.tokens_out,
                "cost_usd": res.cost_usd, "model": res.model, "meta": res.meta, "error": res.raw_error})


def _promote(tier: str) -> str:
    i = TIER_ORDER.index(tier)
    return TIER_ORDER[min(i + 1, len(TIER_ORDER) - 1)]


def _budget_tier(ctx: RunContext, tier: str) -> str:
    """예산 초과 시 핵심 추론 품질을 낮추지 않고 중단한다."""
    if ctx.state.cost.over_budget:
        raise AbortRun("추론 예산에 도달했습니다.")
    return tier


def verify_artifact(ctx: RunContext, rubric_id: str, data: Any, facts: str) -> dict:
    rubric = settings.rubric(rubric_id)
    if not rubric or not settings.cfg("verification.enabled", True):
        return {"verdict": "UNVERIFIED", "score": 0.0, "skipped": True}
    if rubric_id not in settings.cfg("verification.critical_rubrics", [rubric_id]):
        return {"verdict": "UNVERIFIED", "score": 0.0, "skipped": True, "source": "policy"}
    from . import digest, domain
    support = {"observations": digest.facts_packet(ctx.state), "provided_context": facts,
               "problem_type": domain.problem_type(ctx.state)}
    if rubric_id in ("R4_CONTRA", "R6_CONCEPT"):
        support["derived_causal_hypotheses"] = digest.causal_packet(ctx.state)
        support["contradictions"] = digest.contradictions_digest(ctx.state)
    if rubric_id == "R4_CONTRA":
        from . import knowledge as K
        scheme = ctx.state.scratch.get("param_scheme", "ENG_39")
        ids = {t.get(k) for t in data.get("technical_contradictions", [])
               for k in ("improving_param_id", "worsening_param_id")}
        support["parameter_definitions"] = {str(i): K.params(scheme).get(str(i), {}) for i in ids}
    user = P.render(
        "P_VERIFIER_GENERIC",
        artifact_json=data,
        facts_block=support,
        constraints_block=verify.constraints_block(ctx.state),
        rubric_name=rubric.get("description", rubric_id),
        rubric_criteria=verify.rubric_criteria_text(rubric),
        pass_threshold=rubric["pass_threshold"],
        reject_below=rubric["reject_below"],
    )
    try:
        res = tracked_chat(ctx, system="You are a strict independent auditor. Output JSON only.",
                            user=user, tier="T3", temperature=0.0, expect="object",
                            max_tokens=min(4500, 1200 + 240 * len(data.get("concepts", []))) if isinstance(data, dict) else 1200)
    except llm.LLMError as exc:
        return {"verdict": "UNVERIFIED", "score": 0.0, "error": str(exc), "skipped": True}
    out = res.data if isinstance(res.data, dict) else {}
    if out.get("verdict") not in ("PASS", "REVISE", "REJECT"):
        out["verdict"] = "UNVERIFIED"
    criteria = out.get("per_criterion")
    if criteria:
        try:
            scores = {c['id']: float(c['score']) for c in criteria}
            required = rubric.get('criteria', [])
            if any(c['id'] not in scores or not 0 <= scores[c['id']] <= 1 for c in required):
                raise ValueError('incomplete criterion scores')
            total_weight = sum(c.get('weight', 0) for c in required)
            out['score'] = sum(scores[c['id']] * c.get('weight', 0) for c in required) / total_weight
            out['verdict'] = ('PASS' if out['score'] >= rubric['pass_threshold'] else
                              'REJECT' if out['score'] < rubric['reject_below'] else 'REVISE')
        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            out['verdict'] = 'UNVERIFIED'
    if out.get("fatal_flaws"):
        out["verdict"] = "REJECT"
    out.setdefault("score", 0.0)
    out["rubric"] = rubric_id
    out["_tokens"] = (res.tokens_in, res.tokens_out, res.cost_usd)
    return out


def run_agent(
    ctx: RunContext,
    *,
    node: str,
    label: str,
    stage: str,
    agent_id: str,
    prompt_id: str,
    tier: str = "T2",
    vars: Optional[dict] = None,
    expect: str = "object",
    rubric_id: Optional[str] = None,
    checker: Optional[Callable[[Any], list[str]]] = None,
    normalizer: Optional[Callable[[Any], Any]] = None,
    repair_attempts: Optional[int] = None,
    facts: str = "",
    system_override: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    default: Any = None,
) -> Any:
    """단일 LLM 노드 실행. 계정 오류는 중단하고 일시적 호출 실패는 default를 반환한다."""
    state = ctx.state
    tier = _budget_tier(ctx, routed_tier(node, tier))
    if max_tokens is None and node.startswith("s5_"):
        # Resolve before cost reservation and cache hashing. Tier-wide defaults can
        # be too small for structured multi-solution outputs, even with bounded retrieval.
        max_tokens = max(settings.tiers[tier].max_tokens,
                         int(settings.cfg("solutions.track_max_tokens", 8000)))
    step = ctx.start_step(node=node, label=label, stage=stage, agent_id=agent_id,
                          prompt_id=prompt_id, tier=tier)

    # 동적으로 투입된 에이전트의 추가 지시 (노드별 + 현재 단계 전체)
    stage_key = state.scratch.get("stage_key", "")
    injected = list(state.control.injected_agents.get(node) or [])
    injected += list(state.control.injected_agents.get(f"stage:{stage_key}") or [])
    inject_block = ""
    if injected:
        inject_block = "\n\n[추가 투입된 전문가의 관점 — 반드시 반영하라]\n" + "\n".join(
            f"- {a.get('role_name','전문가')}: {a.get('instruction','')}" for a in injected)

    from .domain import context as domain_context
    from .domain import problem_type, physical_allowed
    prompt_vars = {"problem_type": problem_type(state), "physical_scope": state.domain.physical_scope,
                   "physical_allowed": physical_allowed(state), **(vars or {})}
    if node.startswith("s5_"):
        from . import digest
        prompt_vars.setdefault("contradictions", digest.contradictions_digest(state))
    base_user = P.render(prompt_id, **prompt_vars) + domain_context(state, node) + inject_block
    if node.startswith(("s1_", "s3_")):
        from . import rag
        base_user += rag.lessons_block(state)
    system = system_override or P.render(
        "P_COMMON_PREAMBLE",
        lang=state.control.lang,
        problem_type=problem_type(state), physical_scope=state.domain.physical_scope,
        constraints_block=verify.constraints_block(state),
    )
    step.input_slice = {"prompt_id": prompt_id, "vars": vars or {}, "system": system,
                        "user": base_user, "prompt_hash": hashlib.sha256(base_user.encode()).hexdigest()}
    # Cache successful, identical calls within this run only. Changes to prompts, inputs,
    # models or review policy invalidate the cache; no cross-user data sharing.
    import inspect
    try:
        checker_source = inspect.getsource(checker) if checker else ""
    except (OSError, TypeError):
        checker_source = str(checker)
    tc = settings.tiers[tier]
    from . import digest
    audit_context = {"facts": digest.facts_packet(state), "causal": digest.causal_packet(state),
                     "contradictions": digest.contradictions_digest(state)} if rubric_id else None
    cache_key = hashlib.sha256(json.dumps([node, prompt_id, expect, rubric_id, checker_source,
        settings.rubrics.get(rubric_id, {}), system, base_user, tier, facts, audit_context,
        settings.tiers[tier].model, settings.tiers[tier].base_url, max_tokens, temperature,
        tc.temperature, tc.max_tokens, tc.json_mode, tc.supports_temperature, tc.token_parameter,
        settings.triz.get("verification", {}), *([repair_attempts] if repair_attempts is not None else [])],
        sort_keys=True, default=str).encode()).hexdigest()
    cache = state.scratch.setdefault("agent_cache", {})
    if cache_key in cache:
        from . import store
        previous = store.get_step(state.run_id, cache[cache_key])
        if previous and previous["status"] == "OK":
            cached = previous["output_json"]
            cached_data = cached.get("items", []) if expect == "array" else cached
            try:
                if normalizer:
                    cached_data = normalizer(cached_data)
                reusable = not checker or not checker(cached_data)
            except Exception:  # A changed checker must not trap retries on stale output.
                reusable = False
            if reusable:
                step.output_json = _as_dict(cached_data)
                step.verdicts = previous["verdicts"]
                ctx.finish_step(step, "SKIPPED")
                return cached_data

    max_repair = (int(settings.cfg("verification.max_repair_attempts", 2)) if repair_attempts is None
                  else max(0, min(3, int(repair_attempts))))
    attempt = 0
    user = base_user
    data: Any = None
    cur_tier = tier

    while True:
        attempt += 1
        step.verify_attempts = attempt
        try:
            res = tracked_chat(ctx, _node=node, system=system, user=user, tier=cur_tier, expect=expect,
                                temperature=temperature, max_tokens=max_tokens)
        except AbortRun as exc:
            _finish_aborted_step(ctx, step, exc)
            raise
        except llm.LLMError as exc:
            usage = getattr(exc, "usage", None)
            if usage:
                step.tokens_in += usage.tokens_in
                step.tokens_out += usage.tokens_out
                step.cost_usd += usage.cost_usd
            step.error = str(exc)
            ctx.emit("node_error", node=node, error=str(exc))
            ctx.finish_step(step, "FAILED")
            ctx.warn(f"{label}: LLM 호출 실패 → 기본값으로 진행 ({exc})")
            return default
        data = res.data
        if expect == "object" and isinstance(data, list):
            merged: dict = {}
            for item in data:
                if isinstance(item, dict):
                    merged.update(item)
            data = merged or {"items": data}
        if normalizer:
            data = normalizer(data)
        step.tokens_in += res.tokens_in
        step.tokens_out += res.tokens_out
        step.cost_usd += res.cost_usd
        step.model = res.model
        step.tier = cur_tier

        issues = []
        if checker:
            try:
                issues = checker(data) or []
            except Exception as exc:  # noqa: BLE001
                issues = [f"검사기 오류: {exc}"]

        if issues:
            verdict = {"verdict": "REVISE", "score": 0.0, "source": "deterministic",
                       "revision_instructions": issues, "fatal_flaws": []}
        elif rubric_id and node not in settings.cfg("verification.skip_nodes", []):
            try:
                verdict = verify_artifact(ctx, rubric_id, data, facts)
            except AbortRun as exc:
                step.output_json = _as_dict(data)
                _finish_aborted_step(ctx, step, exc)
                raise
            tk = verdict.pop("_tokens", None)
            if tk:
                step.tokens_in += tk[0]
                step.tokens_out += tk[1]
                step.cost_usd += tk[2]
        else:
            verdict = {"verdict": "PASS", "score": 1.0, "source": "none"}

        step.verdicts.append(verdict)
        ctx.emit("verify", node=node, step_id=step.step_id, verdict=verdict.get("verdict"),
                 score=verdict.get("score"), attempt=attempt,
                 instructions=verdict.get("revision_instructions", [])[:3])

        if verdict.get("verdict") in ("PASS", "UNVERIFIED"):
            step.output_json = _as_dict(data)
            status = "OK" if verdict.get("verdict") == "PASS" else "WARN"
            ctx.finish_step(step, status)
            if status == "OK":
                with ctx.lock:
                    cache[cache_key] = step.step_id
            return data

        if attempt > max_repair:
            if verdict.get("fatal_flaws") or any(str(i).startswith("FATAL-") for i in issues):
                step.output_json = _as_dict(data)
                step.error = "치명적 분석 결함이 수리되지 않았습니다."
                ctx.finish_step(step, "FAILED")
                raise AbortRun(f"{label}: 치명적 결함이 남아 후속 분석을 중단합니다.")
            if settings.cfg("verification.escalate_tier_on_fail", True) and cur_tier != "T2" and not step.escalated and not ctx.state.cost.over_budget:
                cur_tier = _promote(cur_tier)
                step.escalated = True
                user = base_user
                ctx.emit("escalate", node=node, tier=cur_tier)
                continue
            step.output_json = _as_dict(data)
            ctx.finish_step(step, "WARN")
            ctx.warn(f"⚠️ 미검증 통과: {label} (판정 {verdict.get('verdict')}, "
                     f"사유: {'; '.join((verdict.get('revision_instructions') or ['-'])[:2])})")
            return data

        user = base_user + "\n\n" + P.render(
            "P_REPAIR",
            previous_output=json.dumps(data, ensure_ascii=False),
            verdict=verdict.get("verdict"),
            score=verdict.get("score"),
            fatal_flaws=verdict.get("fatal_flaws", []),
            revision_instructions=verdict.get("revision_instructions", []),
        )


def _finish_aborted_step(ctx, step, exc):
    usage = getattr(exc, "usage", None)
    if usage:
        step.tokens_in += usage.tokens_in
        step.tokens_out += usage.tokens_out
        step.cost_usd += usage.cost_usd
    step.error = str(exc)
    ctx.emit("node_error", node=step.node, error=str(exc))
    ctx.finish_step(step, "FAILED")


def _as_dict(data: Any) -> dict:
    if isinstance(data, dict):
        return data
    return {"items": data}


def _trim(obj: Any, limit: int = 4000) -> Any:
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        return str(obj)[:limit]
    return json.loads(s) if len(s) <= limit else {"_truncated": s[:limit]}
