"""에이전트 실행기: 생성 → 결정론 검사 → 루브릭 검증 → 수리/승급 → 커밋."""
from __future__ import annotations

import json
import hashlib
import time
from typing import Any, Callable, Optional

from . import llm, prompts_registry as P, verify, verification_contract as contract
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
    from .ax import enabled as ax_enabled
    if ax_enabled(ctx.state):
        from .ax.gateway import chat
        return chat(ctx, **kwargs)
    reasoning = kwargs.pop('_analysis_reasoning', False)
    node = kwargs.pop("_node", "independent_verifier")
    deadline = ctx.state.scratch.get("execution_deadline")
    if deadline and time.time() >= deadline:
        raise AbortRun("분석 실행 시간 예산에 도달했습니다. 이어서 실행하면 새 시간 예산으로 재개합니다.")
    tc = settings.tiers[kwargs.get("tier", "T2")]
    config = {key:value for key,value in vars(tc).items() if key != 'api_key'}
    if reasoning is True:
        from .analysis_model_policy import analysis_model_config
        config = analysis_model_config(config, True)
        kwargs['model_config'] = config
    max_output = kwargs.get("max_tokens") or tc.max_tokens
    # UTF-8 bytes are a conservative token upper bound; include retry payload overhead.
    input_bound = len((kwargs["system"] + kwargs["user"]).encode("utf-8")) + 16000
    from .model_pricing import reserve_microusd
    reserve = reserve_microusd(config, input_bound, max_output, settings.max_retries) / 1_000_000
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


def verify_artifact(ctx: RunContext, rubric_id: str, data: Any, facts: str, *, previous_verdicts=None) -> dict:
    rubric = contract.effective_rubric(settings, rubric_id)
    if not rubric or not settings.cfg("verification.enabled", True):
        return {"verdict": "UNVERIFIED", "score": 0.0, "skipped": True}
    if not contract.is_critical(rubric_id) and rubric_id not in settings.cfg("verification.critical_rubrics", [rubric_id]):
        return {"verdict": "UNVERIFIED", "score": 0.0, "skipped": True, "source": "policy"}
    from . import digest, domain
    support = {"observations": digest.facts_packet(ctx.state), "provided_context": facts,
               "problem_type": domain.problem_type(ctx.state)}
    analysis_node = contract.RUBRIC_NODES.get(rubric_id, "")
    if contract.is_critical(rubric_id):
        support["analysis_context"] = contract.analysis_context(ctx.state, analysis_node)
        from .analysis_checks import artifact_structure_facts
        support["deterministic_inventory"] = artifact_structure_facts(rubric_id, data)
        if previous_verdicts:
            support['prior_reviews_model_opinions'] = [
                {key:row.get(key) for key in ('verdict','source','per_criterion','revision_instructions','element_findings')}
                for row in previous_verdicts[-5:]]
    if rubric_id in ("R4_CONTRA", "R6_CONCEPT"):
        support["derived_causal_hypotheses"] = digest.causal_packet(ctx.state)
        support["contradictions"] = digest.contradictions_digest(ctx.state)
    if rubric_id == "R4_CONTRA":
        from . import knowledge as K
        scheme = ctx.state.scratch.get("param_scheme", "ENG_39")
        ids = {t.get(k) for t in data.get("technical_contradictions", [])
               for k in ("improving_param_id", "worsening_param_id")}
        support["parameter_definitions"] = {str(i): K.params(scheme).get(str(i), {}) for i in ids}
    from .ax.runtime import render_prompt
    user = render_prompt(ctx.state,
        "P_VERIFIER_GENERIC",
        artifact_json=data,
        facts_block=support,
        constraints_block=verify.constraints_block(ctx.state),
        rubric_name=rubric.get("description", rubric_id),
        rubric_criteria=verify.rubric_criteria_text(rubric),
        pass_threshold=rubric["pass_threshold"],
        reject_below=rubric["reject_below"],
    )
    user += contract.verifier_supplement(rubric)
    if analysis_node:
        from .analysis_guidance import analysis_guidance
        user += analysis_guidance(ctx.state, analysis_node)
    verifier_tokens = int(settings.cfg('verification.max_tokens',
        min(4500,1200+240*len(data.get('concepts',[]))) if isinstance(data,dict) else 1200))
    critical = contract.is_critical(rubric_id)
    if critical:
        verifier_tokens = max(verifier_tokens, 16000)
    try:
        res = tracked_chat(ctx, system="You are a strict independent auditor. Output JSON only.",
                            user=user, tier="T3", temperature=0.0, expect="object",
                            max_tokens=verifier_tokens,
                            **({'_analysis_reasoning':True} if critical else {}))
    except llm.LLMError as exc:
        out = {"verdict": "UNVERIFIED", "score": 0.0, "error": str(exc), "skipped": True}
        usage = getattr(exc, "usage", None)
        if usage:
            out["_tokens"] = (usage.tokens_in, usage.tokens_out, usage.cost_usd)
        return out
    out = contract.normalize_verdict(res.data, rubric)
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
    """Generate, repair and audit; critical analysis never commits invalid output."""
    state = ctx.state
    critical = contract.is_critical(rubric_id, node)
    tier = _budget_tier(ctx, routed_tier(node, tier))
    if max_tokens is None and node.startswith("s5_"):
        # Resolve before cost reservation and cache hashing. Tier-wide defaults can
        # be too small for structured multi-solution outputs, even with bounded retrieval.
        max_tokens = max(state.scratch.get('ax_bundle',{}).get('models',{}).get(tier,{}).get('max_tokens',settings.tiers[tier].max_tokens),
                         int(settings.cfg("solutions.track_max_tokens", 8000)))
    step = ctx.start_step(node=node, label=label, stage=stage, agent_id=agent_id,
                          prompt_id=prompt_id, tier=tier)
    if critical and rubric_id and (not contract.effective_rubric(settings, rubric_id) or
                                   not settings.cfg("verification.enabled", True)):
        step.error = "필수 분석 검증이 비활성화되었거나 검증 기준이 없습니다."
        ctx.finish_step(step, "FAILED")
        raise AbortRun(f"{label}: {step.error}")

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
    from .ax.runtime import render_prompt
    base_user = render_prompt(state, prompt_id, **prompt_vars) + domain_context(state, node) + inject_block
    base_user += contract.generation_supplement(state, node)
    from .ax import concept_effects
    explicit_effects = prompt_id == 'P_S6_CONCEPT' and concept_effects.enabled(state)
    if explicit_effects:
        base_user += concept_effects.instruction(state, [row['id'] for row in prompt_vars.get('ideas', [])])
    if prompt_id == "P_S5_MERGE":
        from .idea_consolidation import CONSOLIDATION_CONTRACT
        # Earlier requests for many ideas apply to generation, while the later
        # product contract advances at most ten representatives to elaboration.
        base_user += "\n\n" + CONSOLIDATION_CONTRACT
    if prompt_id in ('P_S5_TRACK_F', 'P_S5_TRACK_G', 'P_S5_TRACK_H'):
        from .solve_contract import APPLICATION_CONTRACT
        base_user += APPLICATION_CONTRACT
        # Old pinned bodies may not contain these placeholders. Supply the
        # problem contract in the actual request, without replacing their text.
        from . import digest
        base_user += '\n\n[S5 문제 입력 계약 v1]\n' + json.dumps({
            'problem': digest.frame_digest(state),
            'boundary': {
                'user_confirmed': state.confirm.user_confirmed,
                'target_system': digest.target_system(state),
                'operative_zone': state.confirm.operative_zone,
                'operative_time': state.confirm.operative_time,
                'physical_scope': state.domain.physical_scope,
                'user_amendments': state.confirm.user_amendments,
            },
            'contradictions': digest.contradictions_digest(state),
        }, ensure_ascii=False, separators=(',', ':'))
    if node.startswith(("s1_", "s3_")):
        from . import rag
        base_user += rag.lessons_block(state)
    system = system_override or render_prompt(state,
        "P_COMMON_PREAMBLE",
        lang=state.control.lang,
        problem_type=problem_type(state), physical_scope=state.domain.physical_scope,
        constraints_block=verify.constraints_block(state),
    )
    from .ax.exploration_context import current, render, PROMPTS, SCHEMA as expansion_schema
    from .ax.mode_contract import unified
    expansion_prompts = PROMPTS | ({'P_S5_TRACK_B','P_S5_TRACK_C','P_S5_TRACK_E','P_S5_TRACK_F'} if unified(state) else set())
    targeted = current(state) if prompt_id in expansion_prompts else None
    if targeted:
        base_user += render(targeted)
    step.input_slice = {"prompt_id": prompt_id, "vars": vars or {}, "system": system,
                        "user": base_user, "prompt_hash": hashlib.sha256(base_user.encode()).hexdigest()}
    if targeted:
        from .ax.contracts import digest as context_digest
        step.input_slice.update(exploration_context=targeted, semantic_context_hash=context_digest(targeted),
                                exploration_contract=expansion_schema, provider_payload_hash=context_digest([system, base_user]))
    # Cache successful, identical calls within this run only. Changes to prompts, inputs,
    # models or review policy invalidate the cache; no cross-user data sharing.
    import inspect
    try:
        checker_source = inspect.getsource(checker) if checker else ""
    except (OSError, TypeError):
        checker_source = str(checker)
    # Lambdas/wrappers delegate to shared checks and typed schemas.
    from . import analysis_checks, schema
    def cross_reference_issues(value):
        if not node.startswith(('s3_', 's4_')):
            return []
        declared = []
        if node == 's3_constraints' and isinstance(value, dict) and isinstance(value.get('constraints'), list):
            declared = [row.get('id') for row in value['constraints'] if isinstance(row, dict)]
        return analysis_checks.unknown_constraint_references(
            value, [row.id for row in state.constraints.items], declared_constraint_ids=declared)

    validation_source = hashlib.sha256("".join(inspect.getsource(module) for module in
        (verify, analysis_checks, schema, contract)).encode()).hexdigest()
    tc = settings.tiers[tier]
    from . import digest
    audit_context = {"facts": digest.facts_packet(state), "causal": digest.causal_packet(state),
                     "contradictions": digest.contradictions_digest(state),
                     "analysis_context": contract.analysis_context(state, node)} if rubric_id else None
    effective_rubric = contract.effective_rubric(settings, rubric_id) if rubric_id else None
    reasoning_profile = []
    if critical:
        from .analysis_model_policy import analysis_model_config
        pinned_models = state.scratch.get('ax_bundle', {}).get('models', {})
        for model_tier in (tier, 'T3'):
            selected_model = pinned_models.get(model_tier) or settings.tiers[model_tier].__dict__
            reasoning_profile.append(analysis_model_config(
                {key:value for key,value in selected_model.items() if key != 'api_key'}, True))
    cache_key = hashlib.sha256(json.dumps([node, prompt_id, expect, rubric_id, checker_source,
        contract.VERSION, validation_source, effective_rubric, system, base_user, tier, facts, audit_context,
        settings.tiers[tier].model, settings.tiers[tier].base_url, max_tokens, temperature,
        tc.temperature, tc.max_tokens, tc.json_mode, tc.supports_temperature, tc.token_parameter,
        settings.cfg("verification", {}), *([repair_attempts] if repair_attempts is not None else []),
        *([reasoning_profile] if critical else [])],
        sort_keys=True, default=str).encode()).hexdigest()
    cache = state.scratch.setdefault("agent_cache", {})
    if explicit_effects:
        # Keep the legacy checker source/cache identity unchanged. The pinned
        # new prompt already versions this stricter output contract.
        coverage_checker = checker
        checker = lambda value: ((coverage_checker(value) if coverage_checker else []) +
                                 concept_effects.check_batch(state, value))
    if cache_key in cache:
        from . import store
        previous = store.get_step(state.run_id, cache[cache_key])
        if previous and previous["status"] == "OK":
            cached = previous["output_json"]
            cached_data = cached.get("items", []) if expect == "array" else cached
            try:
                if normalizer:
                    cached_data = normalizer(cached_data)
                reusable = (not checker or not checker(cached_data)) and not cross_reference_issues(cached_data)
                if critical:
                    reusable = reusable and isinstance(cached_data, dict if expect == "object" else list)
                    if rubric_id:
                        prior_verdicts = previous.get("verdicts") or []
                        reusable = reusable and bool(prior_verdicts) and bool(effective_rubric)
                        if reusable:
                            reusable = contract.normalize_verdict(prior_verdicts[-1], effective_rubric)["verdict"] == "PASS"
            except Exception:  # A changed checker must not trap retries on stale output.
                reusable = False
            if reusable:
                step.output_json = _as_dict(cached_data)
                step.verdicts = previous["verdicts"]
                ctx.finish_step(step, "SKIPPED")
                return cached_data

    max_repair = (int(settings.cfg("verification.max_repair_attempts", 2)) if repair_attempts is None
                  else max(0, min(3, int(repair_attempts))))
    # Format/reference repair must not consume the only opportunity to correct
    # a semantic finding discovered by the first independent review afterwards.
    # Explicit per-call limits still apply to callers with a narrower contract.
    staged_repair = critical and repair_attempts is None
    repair_limits = {
        "structure": max(0, min(3, int(settings.cfg("verification.analysis_structure_repairs", 2)))),
        "semantic": max(0, min(4, int(settings.cfg("verification.analysis_semantic_repairs", 3)))),
    }
    repair_counts = {"structure": 0, "semantic": 0}
    attempt = 0
    user = base_user
    data: Any = None
    repair_reference = None
    cur_tier = tier

    while True:
        attempt += 1
        step.verify_attempts = attempt
        try:
            res = tracked_chat(ctx, _node=node, system=system, user=user, tier=cur_tier, expect=expect,
                                temperature=temperature, max_tokens=max_tokens,
                                **({'_analysis_reasoning':True} if critical else {}))
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
            if critical:
                raise AbortRun(f"{label}: 모델 호출이 실패해 검증되지 않은 분석을 중단합니다.") from exc
            ctx.warn(f"{label}: LLM 호출 실패 → 기본값으로 진행 ({exc})")
            return default
        if res.meta.get('durable_replay'):
            step.input_slice['replay_source'] = {
                'task_id': res.meta.get('source_task_id'),
                'usage': res.meta.get('replay_source_usage'),
                'new_provider_calls': 0,
            }
        data = res.data
        if expect == "object" and isinstance(data, list):
            # Durable results may contain an array extracted by an older parser.
            # Recover the full object from the original response without a call.
            if getattr(res, "text", ""):
                try:
                    recovered = llm.extract_json(res.text)
                    if isinstance(recovered, dict):
                        data = recovered
                except ValueError:
                    pass
        if expect == "object" and isinstance(data, list):
            merged: dict = {}
            for item in data:
                if not isinstance(item, dict) or merged.keys() & item.keys():
                    # Rows with repeated keys must never overwrite earlier rows.
                    data = {"items": data}
                    break
                merged.update(item)
            else:
                data = merged or {"items": data}
        step.tokens_in += res.tokens_in
        step.tokens_out += res.tokens_out
        step.cost_usd += res.cost_usd
        step.model = res.model
        step.tier = cur_tier

        issues = cross_reference_issues(data)
        if normalizer:
            try:
                data = normalizer(data)
            except Exception as exc:  # Malformed output is a repairable validation failure.
                issues.append(f"DET-SCHEMA: 정규화 실패: {exc}")
        if critical and not isinstance(data, dict if expect == "object" else list):
            issues.append(f"DET-SCHEMA: {expect} 형식의 전체 JSON이 필요하다.")
        if critical and repair_reference is not None:
            issues.extend(contract.repair_shape_issues(repair_reference, data, node=node))
        if checker:
            try:
                issues.extend(checker(data) or [])
            except Exception as exc:  # noqa: BLE001
                issues.append(f"검사기 오류: {exc}")

        if issues:
            verdict = {"verdict": "REVISE", "score": 0.0, "source": "deterministic",
                       "revision_instructions": issues, "fatal_flaws": []}
        elif rubric_id and (critical or node not in settings.cfg("verification.skip_nodes", [])):
            try:
                verdict = verify_artifact(ctx, rubric_id, data, facts,
                    **({'previous_verdicts':step.verdicts} if critical and step.verdicts else {}))
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

        if verdict.get("verdict") == "PASS" or (not critical and verdict.get("verdict") == "UNVERIFIED"):
            step.output_json = _as_dict(data)
            status = "OK" if verdict.get("verdict") == "PASS" else "WARN"
            ctx.finish_step(step, status)
            if status == "OK":
                with ctx.lock:
                    cache[cache_key] = step.step_id
            return data

        if repair_reference is None and isinstance(data, dict):
            repair_reference = data
        repair_phase = "structure" if issues else "semantic"
        exhausted = (repair_counts[repair_phase] >= repair_limits[repair_phase]
                     if staged_repair else attempt > max_repair)
        if exhausted:
            if verdict.get("fatal_flaws") or any(str(i).startswith("FATAL-") for i in issues):
                step.output_json = _as_dict(data)
                step.error = "치명적 분석 결함이 수리되지 않았습니다."
                ctx.finish_step(step, "FAILED")
                if node == 's6_concept' and any(str(i).startswith('FATAL-S6-COVERAGE:') for i in issues):
                    from .context import ConceptReviewIncomplete
                    raise ConceptReviewIncomplete()
                raise AbortRun(f"{label}: 치명적 결함이 남아 후속 분석을 중단합니다.")
            if settings.cfg("verification.escalate_tier_on_fail", True) and cur_tier != "T2" and not step.escalated and not ctx.state.cost.over_budget:
                cur_tier = _promote(cur_tier)
                step.escalated = True
                user = base_user + "\n\n" + render_prompt(state, "P_REPAIR",
                    previous_output=json.dumps(data, ensure_ascii=False),
                    verdict=verdict.get("verdict"), score=verdict.get("score"),
                    fatal_flaws=verdict.get("fatal_flaws", []),
                    revision_instructions=verdict.get("revision_instructions", [])) + contract.repair_supplement(verdict)
                ctx.emit("escalate", node=node, tier=cur_tier)
                continue
            if critical:
                step.output_json = _as_dict(data)
                step.error = "필수 분석 검증을 통과하지 못했습니다. 수정 후 다시 실행해야 합니다."
                ctx.finish_step(step, "FAILED")
                raise AbortRun(f"{label}: 검증 결함이 남아 후속 분석을 중단합니다.")
            step.output_json = _as_dict(data)
            ctx.finish_step(step, "WARN")
            ctx.warn(f"⚠️ 미검증 통과: {label} (판정 {verdict.get('verdict')}, "
                     f"사유: {'; '.join((verdict.get('revision_instructions') or ['-'])[:2])})")
            return data

        repair_counts[repair_phase] += 1
        step.input_slice["repair_counts"] = dict(repair_counts)
        user = base_user + "\n\n" + render_prompt(state,
            "P_REPAIR",
            previous_output=json.dumps(data, ensure_ascii=False),
            verdict=verdict.get("verdict"),
            score=verdict.get("score"),
            fatal_flaws=verdict.get("fatal_flaws", []),
            revision_instructions=verdict.get("revision_instructions", []),
        ) + contract.repair_supplement(verdict)
        if critical:
            # Keep the corrected artifact plus all prior findings in view so a
            # new local fix cannot silently undo an earlier necessary repair.
            history = [{"source": item.get("source", "independent"),
                        "verdict": item.get("verdict"),
                        "revision_instructions": item.get("revision_instructions", []),
                        "element_findings": item.get("element_findings", [])}
                       for item in step.verdicts]
            user += ("\n\n[누적 검증 및 수정 이력]\n" + json.dumps(history, ensure_ascii=False)
                     + "\n이미 바로잡은 결함을 되돌리지 말라. 새 지적은 현재 출력과 원본 근거에 대조하라. "
                       "지적이 실제 출력과 어긋나면 올바른 내용을 유지하고 전체 결과 안에서 근거를 명확히 하라. "
                       "요소·식별자·주체·객체를 변경하면 관련 목록, 참조, 연결 및 도표도 함께 갱신하라. "
                       "근거 없는 요소를 만들어 검사만 통과시키지 말라.")


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
