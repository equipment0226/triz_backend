"""파이프라인 노드 구현 (S0~S10)."""
from __future__ import annotations

import json
import hashlib
from .execution_config import ThreadPoolExecutor
from typing import Any

from . import agent, digest, domain, knowledge as K, llm, prompts_registry as P, rag, verify
from .coerce import build, build_list
from .context import AbortRun, HumanInterrupt, RunContext
from .schema import (
    ARIZRun, ARIZStep, CauseEffectChain, CauseNode, ClarifyTurn, Component, ConceptEvaluation,
    ConceptSpec, Constraint, ConstraintCheckResult, ConstraintSet, DomainContext, EvidenceCard,
    FunctionEdge, IFR, InteractionCell, InteractionMatrix, KeyProblem, MatrixLookup, NineWindows,
    PhysicalContradiction, ProblemFrame, RawIdea, ReportArtifact, ResourceItem, ReviewerScore,
    RunMode, Stage, SuFieldModel, SystemCandidate, TechnicalContradiction, TrimmingItem, _as_text,
)
from .settings import settings
from .tools import scholar, search as search_tool


def cfg(path: str, default: Any = None) -> Any:
    return settings.cfg(path, default)


def _text_list(value: Any) -> list[str]:
    """모델 출력에 직접 대입할 때 dict/list 원소를 문자열로 눕힌다."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        value = [value]
    return [_as_text(v) for v in value]


# ════════════════════════════════════════════════ S0
def s0_bootstrap(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S0.value)
    data = agent.run_agent(
        ctx, node="s0_bootstrap", label="실행 계획 판단", stage=Stage.S0.value,
        agent_id="orchestrator", prompt_id="P_S0_BOOTSTRAP", tier="T1",
        vars={"raw_query": st.raw_query,
              "attachment_summaries": [f"{a.filename} ({a.kind})" for a in st.intake.attachments]},
        default={},
    ) or {}

    st.control.lang = data.get("lang") or "ko"
    domain.sync_contract(st, data)
    if not st.scratch.get("mode_locked"):
        mode = (data.get("suggested_mode") or cfg("run.default_mode", "FULL")).upper()
        if mode in RunMode.__members__:
            st.control.mode = RunMode[mode]
    from .titles import ensure_title
    st.scratch["title"] = ensure_title(ctx, data.get("title"))
    if data.get("domain_guess"):
        st.domain.industry = data["domain_guess"]

    tracks = cfg(f"tracks.{st.control.mode.value}", ["A_MATRIX", "B_SEPARATION", "E_TRIMMING"])
    st.control.enabled_tracks = domain.select_tracks(st, tracks)
    from .ax import enabled as ax_enabled
    if not ax_enabled(st):
        st.cost.budget_usd = float(cfg("run.budget_usd", 3.0))
    from .ax.mode_contract import contract
    if contract(st):
        st.control.enabled_tracks = list(contract(st)['profile']['tracks'])
    ctx.emit("plan", mode=st.control.mode.value, tracks=st.control.enabled_tracks,
             title=st.scratch["title"])
    ctx.persist()


# ════════════════════════════════════════════════ S1
def s1_extract(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S1.value)

    payload = ctx.resume_payload()
    if payload:
        answers = payload.get("answers") or []
        pending_turns = [t for t in st.intake.clarify_turns if not t.answered]
        for i, turn in enumerate(pending_turns):
            if i < len(answers):
                turn.user_answer = (answers[i] or "").strip()
                turn.answered = True
        if payload.get("skip"):
            st.scratch["clarify_skipped"] = True

    data = agent.run_agent(
        ctx, node="s1_extract", label="문제·도메인·제약 추출", stage=Stage.S1.value,
        agent_id="interviewer", prompt_id="P_S1_EXTRACT", tier="T2", rubric_id="R1_INTAKE",
        facts=st.raw_query,
        vars={"raw_query": st.raw_query,
              "attachment_facts": digest.attachment_facts(st),
              "clarify_history": digest.clarify_history(st)},
        max_tokens=int(cfg("intake.extract_max_tokens", 4800)),
        default=None,
    )
    if not isinstance(data, dict) or not data:
        raise AbortRun("문제 정보를 추출하지 못했습니다. 답변은 저장되어 있으니 이어서 실행해 주세요.")

    d = data.get("domain") or {}
    previous_contract = st.domain
    st.domain = build(DomainContext, d) or DomainContext()
    if st.domain.problem_type == "UNKNOWN":
        st.domain.problem_type = previous_contract.problem_type
    domain.sync_contract(st, d)
    st.control.enabled_tracks = domain.select_tracks(st, st.control.enabled_tracks)
    f = data.get("frame") or {}
    st.intake.frame = build(ProblemFrame, f, raw_query=st.raw_query) or ProblemFrame(
        raw_query=st.raw_query)
    from .titles import refresh_fallback_title
    refresh_fallback_title(st)
    cs = (data.get("constraints") or {})
    items = build_list(Constraint, cs.get("items"))
    st.constraints = ConstraintSet(items=items, open_questions=cs.get("open_questions") or [])
    st.intake.candidate_characteristics = data.get("candidate_characteristics") or []
    st.intake.candidate_conflicts = data.get("candidate_conflicts") or []

    ctx.emit("artifact", kind="INTAKE", data={
        "domain": st.domain.model_dump(), "frame": st.intake.frame.model_dump(),
        "constraints": st.constraints.model_dump()})
    ctx.persist()

    # 충분성 판단 → 부족하면 역질의
    need = _intake_gaps(st)
    max_rounds = int(cfg("intake.max_clarify_rounds", 2))
    if need and st.control.clarify_rounds < max_rounds and not st.scratch.get("clarify_skipped"):
        st.control.clarify_rounds += 1
        q = agent.run_agent(
            ctx, node="s1_clarify", label=f"역질의 생성 ({st.control.clarify_rounds}차)",
            stage=Stage.S1.value, agent_id="interviewer", prompt_id="P_S1_CLARIFY", tier="T1",
            vars={"missing_info": need, "open_questions": st.constraints.open_questions,
                  "frame_digest": digest.frame_digest(st),
                  "max_questions": cfg("intake.max_clarify_questions", 4)},
            default={"questions": []},
        ) or {}
        turns = [ClarifyTurn(question=x.get("question", ""), why_needed=x.get("why_needed", ""),
                             proposed_answers=x.get("proposed_answers") or [])
                 for x in (q.get("questions") or []) if isinstance(x, dict) and x.get("question")]
        if turns:
            st.intake.clarify_turns.extend(turns)
            ctx.persist()
            raise HumanInterrupt("CLARIFY", "추가 정보가 필요합니다",
                                 {"questions": [t.model_dump() for t in turns]}, Stage.S1.value)


def _intake_gaps(st) -> list[str]:
    gaps: list[str] = []
    if not st.domain.industry:
        gaps.append("업종/직군 정보가 없다")
    if not digest.target_system(st):
        gaps.append("문제가 발생하는 대상 시스템(모듈)이 특정되지 않았다")
    if not st.intake.frame.symptom:
        gaps.append("구체적인 문제 현상이 불명확하다")
    if not st.constraints.items:
        gaps.append("제약조건(수치 한계, 금지사항, 필수 요건)이 하나도 없다")
    if st.intake.frame.confidence < float(cfg("intake.min_confidence", 0.7)):
        gaps += st.intake.frame.missing_info[:3]
    return gaps


# ════════════════════════════════════════════════ S2
def s2_confirm(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S2.value)

    payload = ctx.resume_payload()
    if payload:
        st.confirm.chosen_candidate_id = payload.get("candidate_id") or (
            st.confirm.candidates[0].id if st.confirm.candidates else "")
        chosen = st.confirm.chosen()
        if not chosen or chosen.id != st.confirm.chosen_candidate_id:
            raise ValueError("존재하는 시스템 후보를 선택해 주세요.")
        st.domain.target_system = chosen.name
        if chosen.super_system:
            st.domain.super_system = chosen.super_system
        st.confirm.operative_zone = payload.get("operative_zone") or chosen.operative_zone or st.confirm.operative_zone
        st.confirm.operative_time = payload.get("operative_time") or chosen.operative_time or st.confirm.operative_time
        amend = (payload.get("amendment") or "").strip()
        if amend:
            st.confirm.user_amendments.append(amend)
            st.intake.frame.restated_problem += f"\n[사용자 보완] {amend}"
        if payload.get("problem_zone"):
            st.confirm.problem_zone = payload["problem_zone"]
        st.confirm.user_confirmed = True
        from .titles import refresh_fallback_title
        refresh_fallback_title(st)
        ctx.persist()
        return

    data = agent.run_agent(
        ctx, node="s2_candidates", label="대상 시스템 후보 생성", stage=Stage.S2.value,
        agent_id="system_analyst", prompt_id="P_S2_CANDIDATES", tier="T2", rubric_id="R2_CANDIDATE",
        vars={"domain": digest.domain_brief(st),
              "restated_problem": st.intake.frame.restated_problem,
              "attachment_facts": digest.attachment_facts(st),
              "min_candidates": cfg("confirm.min_candidates", 2),
              "max_candidates": cfg("confirm.max_candidates", 4)},
        default={},
    ) or {}

    st.confirm.candidates = [
        c for c in build_list(SystemCandidate, data.get("candidates")) if c.name
    ]
    st.confirm.problem_zone = data.get("problem_zone", "")
    st.confirm.operative_zone = data.get("operative_zone", "")
    st.confirm.operative_time = data.get("operative_time", "")
    st.confirm.confirm_question = data.get("confirm_question", "이 영역의 문제가 맞습니까?")
    ctx.persist()

    if not st.confirm.candidates:
        ctx.warn("시스템 후보를 생성하지 못해 사용자 입력 시스템을 그대로 사용한다.")
        st.confirm.candidates = [SystemCandidate(name=digest.target_system(st) or "대상 시스템",
                                                 description=st.intake.frame.restated_problem)]
    raise HumanInterrupt("CONFIRM", "대상 시스템을 확정해 주세요", {
        "candidates": [c.model_dump() for c in st.confirm.candidates],
        "problem_zone": st.confirm.problem_zone,
        "operative_zone": st.confirm.operative_zone,
        "operative_time": st.confirm.operative_time,
        "question": st.confirm.confirm_question,
    }, Stage.S2.value)


# ════════════════════════════════════════════════ S3
def s3_analyze(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S3.value)
    lite = st.control.mode == RunMode.LITE

    def nine_windows():
        d = agent.run_agent(
            ctx, node="s3_nine_windows", label="9-Windows 전개", stage=Stage.S3.value,
            agent_id="system_analyst", prompt_id="P_S3_NINE_WINDOWS", tier="T2",
            vars={"target_system": digest.target_system(st), "super_system": st.domain.super_system,
                  "restated_problem": st.intake.frame.restated_problem,
                  "operative_time": st.confirm.operative_time},
            default={},
        ) or {}
        cells = d.get("cells")
        if not isinstance(cells, dict):
            cells = {k: v for k, v in d.items()
                     if isinstance(v, str) and k.split("_")[0] in ("SUB", "SYS", "SUPER")}
        st.analysis.nine_windows = NineWindows(cells=cells,
                                               insights=d.get("insights") or [])

    def function_model():
        chosen = st.confirm.chosen()
        d = agent.run_agent(
            ctx, node="s3_function_model", label="기능 분석(컴포넌트/상호작용/기능도)",
            stage=Stage.S3.value, agent_id="system_analyst", prompt_id="P_S3_FUNCTION_MODEL",
            tier="T2", rubric_id="R3_FUNC", checker=verify.check_function_model,
            facts=st.intake.frame.restated_problem,
            vars={"industry": st.domain.industry,
                  "chosen_system": chosen.model_dump() if chosen else {},
                  "problem_zone": st.confirm.problem_zone,
                  "operative_zone": st.confirm.operative_zone,
                  "attachment_facts": digest.attachment_facts(st),
                  "nw_insights": (st.analysis.nine_windows.insights if st.analysis.nine_windows else []),
                  "min_components": cfg("analysis.min_components", 8),
                  "max_components": cfg("analysis.max_components", 20),
                  "min_harmful": cfg("analysis.min_harmful_functions", 1)},
            default={},
        ) or {}
        st.analysis.components = build_list(Component, d.get("components"))
        st.analysis.function_edges = build_list(FunctionEdge, d.get("function_edges"))
        cells = build_list(InteractionCell, d.get("interaction_cells"))
        st.analysis.interaction_matrix = InteractionMatrix(
            components=[c.name for c in st.analysis.components], cells=cells)
        st.analysis.function_mermaid = d.get("mermaid", "")

    def su_field():
        d = agent.run_agent(
            ctx, node="s3_sufield", label="물질-장 분석(Su-Field)", stage=Stage.S3.value,
            agent_id="sufield_specialist", prompt_id="P_S3_SUFIELD", tier="T2", rubric_id="R3_SUF",
            vars={"problem_functions": digest.function_digest(st, only_problem=True),
                  "components": digest.components_digest(st),
                  "operative_zone": st.confirm.operative_zone,
                  "operative_time": st.confirm.operative_time,
                  "max_models": cfg("analysis.max_su_fields", 3)},
            default={},
        ) or {}
        models = []
        for su in build_list(SuFieldModel, d.get("su_fields")):
            su.standard_class_hint = K.standard_hints(su.completeness, su.effect)
            models.append(su)
        st.analysis.su_fields = models

    def resources():
        d = agent.run_agent(
            ctx, node="s3_resources", label="자원 분석", stage=Stage.S3.value,
            agent_id="resource_analyst", prompt_id="P_S3_RESOURCES", tier="T2", rubric_id="R3_RES",
            vars={"components": digest.components_digest(st),
                  "super_system": st.domain.super_system,
                  "operating_env": st.domain.operating_env,
                  "operative_zone": st.confirm.operative_zone,
                  "operative_time": st.confirm.operative_time,
                  "must_not_have": [c.statement for c in st.constraints.items
                                    if c.kind == "MUST_NOT_HAVE"],
                  "min_resources": cfg("analysis.min_resources", 8)},
            default={},
        ) or {}
        st.analysis.resources = build_list(ResourceItem, d.get("resources"))

    def ceca():
        d = agent.run_agent(
            ctx, node="s3_ceca", label="인과사슬 분석(CECA)", stage=Stage.S3.value,
            agent_id="root_cause_analyst", prompt_id="P_S3_CECA", tier="T2", rubric_id="R3_CECA",
            max_tokens=int(cfg("analysis.ceca_max_tokens", 8000)),
            checker=verify.check_ceca, facts=st.intake.frame.symptom,
            vars={"symptom": st.intake.frame.symptom,
                  "problem_functions": digest.function_digest(st, only_problem=True),
                  "components": digest.components_digest(st),
                  "success_criteria": st.intake.frame.success_criteria,
                  "min_depth": cfg("analysis.ceca_min_depth", 3)},
            default={},
        ) or {}
        nodes = build_list(CauseNode, d.get("nodes"))
        st.analysis.ceca = CauseEffectChain(nodes=nodes, mermaid=d.get("mermaid") or "")

    nine_windows()
    function_model()              # 이후 노드가 기능모델에 의존하므로 순차 실행
    tasks = [resources, ceca]
    if not lite and domain.physical_allowed(st):
        tasks.insert(0, su_field)
    else:
        st.analysis.su_fields = []
    workers = int(cfg("run.parallel_workers", 4))
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(tasks)))) as pool:
        list(pool.map(lambda fn: fn(), tasks))

    _discover_constraints(ctx)

    # 제약에 걸리는 자원 태깅
    banned = [c.statement for c in st.constraints.items if c.kind == "MUST_NOT_HAVE"]
    for r in st.analysis.resources:
        if any(b and (b[:6] in r.name or r.name in b) for b in banned):
            r.blocked_by_constraint = True

    ctx.emit("artifact", kind="ANALYSIS", data={
        "components": len(st.analysis.components), "functions": len(st.analysis.function_edges),
        "su_fields": len(st.analysis.su_fields), "resources": len(st.analysis.resources),
        "ceca_nodes": len(st.analysis.ceca.nodes) if st.analysis.ceca else 0,
        "constraints": len(st.constraints.items)})
    ctx.persist()


def _discover_constraints(ctx: RunContext) -> None:
    """사용자가 말하지 않은 '시스템이 당연히 가지는' 제약을 발굴한다."""
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s3_constraints", label="도메인·시스템 내재 제약 발굴", stage=Stage.S3.value,
        agent_id="constraint_analyst", prompt_id="P_S3_CONSTRAINTS", tier="T2",
        vars={"industry": st.domain.industry, "target_system": digest.target_system(st),
              "super_system": st.domain.super_system,
              "operating_env": st.domain.operating_env,
              "components": digest.components_digest(st),
              "resources": digest.resources_digest(st),
              "operative_zone": st.confirm.operative_zone,
              "operative_time": st.confirm.operative_time,
              "user_constraints": [c.statement for c in st.constraints.items]},
        default={},
    ) or {}

    existing = {c.statement.strip() for c in st.constraints.items}
    added = 0
    for c in build_list(Constraint, d.get("constraints"), source="DOMAIN"):
        if not c.statement or c.statement.strip() in existing:
            continue
        existing.add(c.statement.strip())
        # Unconfirmed domain practice is a hypothesis, not an absolute requirement.
        c.hard = False
        c.confidence = min(c.confidence, 0.6)
        st.constraints.items.append(c)
        added += 1

    taboo = [t for t in (d.get("taboo") or []) if isinstance(t, dict) and t.get("item")]
    for item in taboo:
        item.setdefault("confirmed", False)
    st.scratch["taboo"] = taboo
    st.scratch["domain_assumptions"] = [t for t in taboo if not t.get("confirmed")]
    ctx.emit("artifact", kind="CONSTRAINT_DISCOVERY",
             data={"added": added, "taboo": len(taboo),
                   "items": [f"[{c.category}/{c.zone or '전체'}] {c.statement}"
                             for c in st.constraints.items if c.source == "DOMAIN"][:12]})


# ════════════════════════════════════════════════ S4
def s4_define(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S4.value)
    domain.sync_contract(st)
    scheme = "ENG_39" if st.domain.is_engineering else "BIZ_31"
    st.scratch["param_scheme"] = scheme

    def define_ifr():
        ifr_d = agent.run_agent(
            ctx, node="s4_ifr", label="이상해결책(IFR) 정의", stage=Stage.S4.value,
            agent_id="triz_master", prompt_id="P_S4_IFR", tier="T2", rubric_id="R4_IFR",
            vars={"basic_function": digest.basic_function(st),
                  "key_disadvantages": digest.ceca_keys(st),
                  "root_causes": digest.ceca_roots(st),
                  "resource_names": [r.name for r in st.analysis.resources],
                  "operative_zone": st.confirm.operative_zone,
                  "operative_time": st.confirm.operative_time},
            default={},
        ) or {}
        st.definition.ifr = build(IFR, ifr_d) or IFR()


    def define_contradictions():
        con_d = agent.run_agent(
            ctx, node="s4_contradictions", label="모순 도출(기술적/물리적)", stage=Stage.S4.value,
            agent_id="contradiction_definer", prompt_id="P_S4_CONTRADICTIONS", tier="T2",
            rubric_id="R4_CONTRA", checker=lambda d: verify.check_contradictions(d, scheme),
            facts="\n".join(digest.function_digest(st, only_problem=True)),
            vars={"restated_problem": st.intake.frame.restated_problem,
                  "characteristics": st.intake.candidate_characteristics,
                  "problem_functions": digest.function_digest(st, only_problem=True),
                  "contradiction_seeds": digest.ceca_seeds(st),
                  "negative_interactions": digest.negative_interactions(st),
                  "param_dictionary": K.param_dictionary_text(scheme),
                  "target_count": cfg("definition.target_contradictions", 4),
                  "min_tc": cfg("definition.min_technical_contradictions", 1),
                  "min_pc": cfg("definition.min_physical_contradictions", 1)},
            default={},
        ) or {}

        tcs: list[TechnicalContradiction] = []
        label_to_id: dict[str, str] = {}
        for tc in build_list(TechnicalContradiction, con_d.get("technical_contradictions"),
                             param_scheme=scheme):
            tcs.append(tc)
            label_to_id[tc.label] = tc.id
        pcs: list[PhysicalContradiction] = []
        for raw, pc in zip(con_d.get("physical_contradictions") or [],
                           build_list(PhysicalContradiction,
                                      con_d.get("physical_contradictions"))):
            if isinstance(raw, dict):
                pc.derived_from_tc_id = label_to_id.get(raw.get("derived_from_tc_label", ""), "")
            pcs.append(pc)
        st.definition.technical_contradictions = tcs
        st.definition.physical_contradictions = pcs


    def define_trimming():
        trim_d = agent.run_agent(
            ctx, node="s4_trimming", label="트리밍 후보 도출", stage=Stage.S4.value,
            agent_id="trimming_specialist", prompt_id="P_S4_TRIMMING", tier="T2",
            vars={"function_edges": digest.function_digest(st),
                  "components": digest.components_digest(st),
                  "resources": digest.resources_digest(st)},
            default={},
        ) or {}
        st.definition.trimming = build_list(TrimmingItem, trim_d.get("trimming"))


    with ThreadPoolExecutor(max_workers=max(1, min(3, int(cfg("run.parallel_workers", 4))))) as pool:
        list(pool.map(lambda fn: fn(), [define_ifr, define_contradictions, define_trimming]))
    tcs = st.definition.technical_contradictions
    pcs = st.definition.physical_contradictions

    key_d = agent.run_agent(
        ctx, node="s4_key_problem", label="핵심 문제 선정", stage=Stage.S4.value,
        agent_id="triz_master", prompt_id="P_S4_KEY_PROBLEM", tier="T2",
        vars={"technical_contradictions": [t.model_dump() for t in tcs],
              "physical_contradictions": [p.model_dump() for p in pcs],
              "key_disadvantages": digest.ceca_keys(st),
              "success_criteria": st.intake.frame.success_criteria,
              "max_key": cfg("definition.max_key_problems", 3)},
        default={},
    ) or {}
    kps = []
    for kp in build_list(KeyProblem, key_d.get("key_problems")):
        kp.priority_score = round(kp.impact * 0.6 + kp.tractability * 0.4, 2)
        kps.append(kp)
    st.definition.key_problems = sorted(kps, key=lambda x: -x.priority_score)
    st.definition.dropped = key_d.get("dropped") or []

    ctx.emit("artifact", kind="DEFINITION", data={
        "tc": len(tcs), "pc": len(pcs), "trimming": len(st.definition.trimming),
        "key_problems": [k.title for k in st.definition.key_problems]})
    ctx.persist()


# ════════════════════════════════════════════════ S5
def _selected_contradiction_ids(st) -> set[str]:
    ids: set[str] = set()
    for kp in st.definition.key_problems:
        ids |= set(kp.contradiction_ids)
    return ids


def _pick_tcs(st, limit: int = 3) -> list[TechnicalContradiction]:
    from .ax.exploration_context import current, target_tcs
    targeted = current(st)
    if targeted:
        return sorted(target_tcs(st, targeted), key=lambda t: -t.severity)[:limit]
    sel = _selected_contradiction_ids(st)
    tcs = [t for t in st.definition.technical_contradictions if t.id in sel] or \
        st.definition.technical_contradictions
    return sorted(tcs, key=lambda t: -t.severity)[:limit]


def _pick_pcs(st, limit: int = 2) -> list[PhysicalContradiction]:
    sel = _selected_contradiction_ids(st)
    pcs = [p for p in st.definition.physical_contradictions if p.id in sel] or \
        st.definition.physical_contradictions
    return pcs[:limit]


def _required_functions(st) -> list[str]:
    from .ax.exploration_context import current
    targeted = current(st)
    if targeted:
        return list(targeted['required_functions'])
    out = []
    if st.definition.ifr and st.definition.ifr.x_element:
        out.append(st.definition.ifr.x_element)
    for e in st.analysis.function_edges:
        if e.kind == "HARMFUL":
            out.append(f"{e.object}에 대한 '{e.action}'를 없애면서 기존 유익 기능을 유지한다")
        elif e.level == "INSUFFICIENT":
            out.append(f"{e.subject}가 {e.object}에 대해 '{e.action}'를 충분히 수행한다")
    return out[:4] or [st.intake.frame.restated_problem]


def _add_ideas(st, track: str, apps: list[dict], *, ref_key: str, title_key: str = "title",
               idea_key: str = "idea", addresses: list[str] | None = None) -> int:
    n = 0
    for a in apps or []:
        if not isinstance(a, dict):
            continue
        idea_text = a.get(idea_key) or ""
        if not idea_text:
            continue
        idea = RawIdea(
            track=track,
            source_ref=str(a.get(ref_key, "")),
            title=(a.get(title_key) or idea_text[:24]),
            idea=idea_text,
            uses_resources=a.get("uses_resources") or [],
            addresses=list(addresses or []),
            feasibility_hint=a.get("feasibility_hint") or "MID",
            detail=a,
            mechanism=a.get("mechanism") or a.get("principle", ""),
            mechanism_key=a.get("mechanism_key", ""),
            intervention_variable=a.get("intervention_variable", ""),
            conditions=_text_list(a.get("conditions")),
            strongest_objection=a.get("strongest_objection") or a.get("self_rebuttal", ""),
            validation_test=a.get("validation_test", ""),
            hypothesis_ids=a.get("hypothesis_ids") or [],
        )
        from .ax.exploration_context import current
        targeted = current(st)
        if targeted:
            from .ax.contracts import digest as semantic_digest
            idea.id = 'raw-target-' + semantic_digest([track, targeted, a, addresses])[:32]
            if any(previous.id == idea.id for previous in st.solve.raw_ideas):
                continue
        st.solve.raw_ideas.append(idea)
        n += 1
    return n


def _track_a(ctx: RunContext) -> None:
    st = ctx.state
    scheme = st.scratch.get("param_scheme", "ENG_39")
    max_ids = int(cfg("solutions.max_principles_per_contradiction", 6))

    def llm_principles(tc, count: int) -> list[int]:
        fb = agent.run_agent(
            ctx, node="s5_track_a_select", label=f"발명원리 선별({tc.id})", stage=Stage.S5.value,
            agent_id="inventor_a", prompt_id="P_S5_MATRIX_FALLBACK", tier="T2",
            vars={"count": count,
                  "if_action": tc.if_action, "then_good": tc.then_good, "but_bad": tc.but_bad,
                  "improving_id": tc.improving_param_id,
                  "improving_name": K.param_name(tc.improving_param_id, scheme),
                  "improving_def": K.params(scheme).get(str(tc.improving_param_id), {}).get("definition", ""),
                  "worsening_id": tc.worsening_param_id,
                  "worsening_name": K.param_name(tc.worsening_param_id, scheme),
                  "worsening_def": K.params(scheme).get(str(tc.worsening_param_id), {}).get("definition", ""),
                  "target_system": digest.target_system(st),
                  "principles_brief": K.all_principles_brief()},
            default={},
        ) or {}
        return [int(x) for x in (fb.get("principle_ids") or []) if str(x).isdigit()]

    for tc in _pick_tcs(st):
        ids, source = K.lookup_matrix(tc.improving_param_id, tc.worsening_param_id) \
            if scheme == "ENG_39" else ([], "LLM_FALLBACK")
        note = "모순 행렬 조회 결과"
        if ids:
            # 행렬 값을 정답으로 두고, LLM 제안은 '추가 후보'로만 덧붙인다.
            if cfg("solutions.matrix_cross_check", True) and len(ids) < max_ids:
                extra = [i for i in llm_principles(tc, 3) if 1 <= i <= 40 and i not in ids]
                if extra:
                    added = extra[: max_ids - len(ids)]
                    ids = ids + added
                    note = f"모순 행렬 조회 + 교차검토 추가 {len(added)}건"
        else:
            ids = llm_principles(tc, max_ids)
            note = "행렬 데이터 미탑재 → 전문가(LLM) 선별"
        ids = [i for i in ids if 1 <= i <= 40][:max_ids]
        if not ids:
            continue
        st.solve.matrix_lookups.append(MatrixLookup(
            source_tc_id=tc.id,
            improving_param_id=tc.improving_param_id, worsening_param_id=tc.worsening_param_id,
            principle_ids=ids, source=source, note=note))

        d = agent.run_agent(
            ctx, node="s5_track_a", label=f"Track A 발명원리 적용({tc.id})", stage=Stage.S5.value,
            agent_id="inventor_a", prompt_id="P_S5_TRACK_A", tier="T2", rubric_id="R5_A",
            max_tokens=max(4000, int(cfg("solutions.track_a_max_tokens", 8000))),
            checker=lambda x, allowed=ids: verify.check_principles(x, allowed),
            vars={"industry": st.domain.industry, "target_system": digest.target_system(st),
                  "super_system": st.domain.super_system,
                  "if_action": tc.if_action, "then_good": tc.then_good, "but_bad": tc.but_bad,
                  "improving_id": tc.improving_param_id,
                  "improving_name": K.param_name(tc.improving_param_id, scheme),
                  "improving_def": K.params(scheme).get(str(tc.improving_param_id), {}).get("definition", ""),
                  "worsening_id": tc.worsening_param_id,
                  "worsening_name": K.param_name(tc.worsening_param_id, scheme),
                  "worsening_def": K.params(scheme).get(str(tc.worsening_param_id), {}).get("definition", ""),
                  "resources": digest.resources_digest(st),
                  "su_fields": digest.su_fields_digest(st),
                  "matrix_note": note,
                  "principles_block": K.principles_block(ids),
                  "ideas_per_principle": cfg("solutions.ideas_per_principle", 1)},
            default={},
        ) or {}
        apps = d.get("applications") or []
        for a in apps:
            a.setdefault("principle_name", K.principle_name(a.get("principle_id", 0)))
            a['source_tc_id'] = tc.id
            a["ref"] = f"원리{a.get('principle_id')} {a.get('principle_name')}"
        st.solve.principle_apps += apps
        _add_ideas(st, "A_MATRIX", apps, ref_key="ref", addresses=[tc.id])


def _track_b(ctx: RunContext) -> None:
    from . import separation_contract as separation
    st = ctx.state
    catalog = separation.catalog_for(st)
    for pc in _pick_pcs(st):
        d = agent.run_agent(
            ctx, node="s5_track_b", label=f"Track B 분리원리({pc.id})", stage=Stage.S5.value,
            agent_id="inventor_b", prompt_id="P_S5_TRACK_B", tier="T2", rubric_id="R5_B",
            checker=lambda data: verify.check_separation(data, catalog=catalog),
            normalizer=lambda data: separation.normalize(data, catalog=catalog),
            vars={"element": pc.element, "parameter": pc.parameter,
                  "state_a": pc.state_a, "reason_a": pc.reason_a,
                  "state_b": pc.state_b, "reason_b": pc.reason_b, "scale": pc.scale,
                  "target_system": digest.target_system(st),
                  "resources": digest.resources_digest(st),
                  "su_fields": digest.su_fields_digest(st),
                  "separation_block": K.separation_block(catalog=catalog)},
            default={},
        )
        d = separation.normalize(d, catalog=catalog)
        issues = verify.check_separation(d, catalog=catalog)
        if issues and not separation.is_legacy(catalog):
            raise AbortRun('물리적 모순 해결 접근 검토가 완전하지 않습니다. ' + '; '.join(issues))
        d = d if isinstance(d, dict) else {}
        if d.get("redefine_hint"):
            st.solve.gaps.append(d["redefine_hint"])
        for application in d.get('applications') or []:
            if isinstance(application, dict):
                application['source_pc_id'] = pc.id
        apps = [a for a in (d.get("applications") or []) if isinstance(a, dict) and a.get("applicable") is True]
        for a in apps:
            a["ref"] = separation.display_name(a)
        st.solve.separation_apps += (d.get("applications") or [])
        _add_ideas(st, "B_SEPARATION", apps, ref_key="ref", addresses=[pc.id])


def _track_c(ctx: RunContext) -> None:
    from .catalog_binding import bind_standard
    st = ctx.state
    for su in st.analysis.su_fields[:2]:
        cands = K.candidate_standards(su.completeness, su.effect,
            required_functions=[*_required_functions(st),su.s1,su.s2 or '',su.field or '',*digest.resources_digest(st)])
        if not cands:
            continue
        d = agent.run_agent(
            ctx, node="s5_track_c", label=f"Track C 76표준해({su.id})", stage=Stage.S5.value,
            agent_id="standards_specialist", prompt_id="P_S5_TRACK_C", tier="T2", rubric_id="R5_C",
            checker=lambda data: verify.check_standards(data, [c['code'] for c in cands]),
            normalizer=lambda data: bind_standard(data,cands),
            vars={"s1": su.s1, "s2": su.s2, "field": su.field,
                  "completeness": su.completeness, "effect": su.effect,
                  "target_system": digest.target_system(st),
                  "resources": digest.resources_digest(st),
                  "standards_block": K.standards_block(cands)},
            default={},
        ) or {}
        d = bind_standard(d,cands)
        allowed = {item['code'] for item in cands}
        apps = []
        for app in d.get('applications') or []:
            if isinstance(app,dict) and app.get('standard_code') in allowed:
                apps.append(app)
            else:
                st.solve.gaps.append(f'{su.id}: 후보 목록에 없는 표준해 적용안을 제외함')
        for a in apps:
            a["ref"] = f"표준해 {a.get('standard_code')}"
            a['source_su_id'] = su.id
        st.solve.standard_apps += apps
        _add_ideas(st, "C_STANDARDS", apps, ref_key="ref")


def _track_d_ariz(ctx: RunContext) -> None:
    from .ax.mode_contract import validate_tracks
    validate_tracks(ctx.state, ['D_ARIZ'])
    st = ctx.state
    run = ARIZRun()
    parts_enabled = cfg("ariz.enabled_parts", [1, 2, 3, 4, 5, 7])
    tcs = _pick_tcs(st, 1)
    key_contra = tcs[0].model_dump() if tcs else (
        st.definition.physical_contradictions[0].model_dump()
        if st.definition.physical_contradictions else {})

    def req(part_id: int) -> list[str]:
        return [s["code"] for s in K.ariz_part(part_id).get("steps", []) if s.get("required")]

    def require_complete(data: dict, part_id: int) -> None:
        # Transient provider failures can return the default without a checker.
        issues = verify.check_ariz(data, req(part_id))
        if issues:
            raise AbortRun(f"ARIZ Part{part_id} 검토가 완전하지 않아 후속 분석을 중단합니다. " + "; ".join(issues))

    p1 = {}
    if 1 in parts_enabled:
        p1 = agent.run_agent(
            ctx, node="s5_ariz_p1", label="ARIZ Part1 문제 분석", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART1", tier="T2", rubric_id="R5_D",
            checker=lambda d: verify.check_ariz(d, req(1)),
            vars={"restated_problem": st.intake.frame.restated_problem,
                  "target_system": digest.target_system(st), "super_system": st.domain.super_system,
                  "function_digest": digest.function_digest(st, only_problem=True),
                  "key_contradiction": key_contra, "steps": K.ariz_part_steps_text(1)},
            default={},
        ) or {}
        require_complete(p1, 1)
        run.steps += _ariz_steps(p1)
        run.conflict_pair = p1.get("conflict_pair", "")

    p2 = {}
    if 2 in parts_enabled:
        p2 = agent.run_agent(
            ctx, node="s5_ariz_p2", label="ARIZ Part2 자원 분석", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART2", tier="T2",
            checker=lambda d: verify.check_ariz(d, req(2)),
            vars={"part1": p1.get("steps", []), "resources": digest.resources_digest(st),
                  "components": digest.components_digest(st),
                  "operative_zone": st.confirm.operative_zone,
                  "operative_time": st.confirm.operative_time},
            default={},
        ) or {}
        require_complete(p2, 2)
        run.steps += _ariz_steps(p2)
        run.operative_zone = p2.get("operative_zone", st.confirm.operative_zone)
        run.operative_time = p2.get("operative_time", st.confirm.operative_time)
        run.sfr_inventory = _text_list(p2.get("sfr_inventory"))

    p3 = {}
    if 3 in parts_enabled:
        p3 = agent.run_agent(
            ctx, node="s5_ariz_p3", label="ARIZ Part3 IFR·물리모순", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART3", tier="T2", rubric_id="R5_D",
            checker=lambda d: verify.check_ariz(d, req(3)),
            vars={"part1": p1.get("steps", []), "part2": p2.get("steps", [])},
            default={},
        ) or {}
        require_complete(p3, 3)
        run.steps += _ariz_steps(p3)
        run.ifr1 = p3.get("ifr1", "")
        run.ifr2 = p3.get("ifr2", "")
        run.physical_contradiction_macro = p3.get("pc_macro", "")
        run.physical_contradiction_micro = p3.get("pc_micro", "")

    p4 = {}
    if 4 in parts_enabled:
        p4 = agent.run_agent(
            ctx, node="s5_ariz_p4", label="ARIZ Part4 자원 동원(SLP 등)", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART4", tier="T2",
            checker=lambda d: verify.check_ariz(d, req(4)),
            vars={"ifr2": run.ifr2, "pc_micro": run.physical_contradiction_micro,
                  "pc_macro": run.physical_contradiction_macro,
                  "sfr_inventory": run.sfr_inventory or digest.resources_digest(st)},
            default={},
        ) or {}
        require_complete(p4, 4)
        run.steps += _ariz_steps(p4)
        run.slp_model = p4.get("slp_model", "")
        run.solution_directions = _text_list(p4.get("solution_directions"))
        _add_ideas(st, "D_ARIZ", [{**i, "ref": f"ARIZ {i.get('source_step','4.x')}"}
                                  for i in (p4.get("ideas") or [])], ref_key="ref")

    if 5 in parts_enabled:
        from .catalog_binding import bind_effect, bind_standard
        from .separation_contract import catalog_for as separation_catalog_for
        su = st.analysis.su_fields[0] if st.analysis.su_fields else None
        cands = K.candidate_standards(su.completeness if su else '',su.effect if su else '',
            required_functions=[*_required_functions(st),run.physical_contradiction_macro,run.physical_contradiction_micro])
        from .ax.runtime import effect_candidates
        effect_cands = effect_candidates(st, _required_functions(st), limit=10)
        from .effect_catalog import format_effects
        def bind_part5(data):
            if not isinstance(data,dict): return {}
            result=dict(data)
            ideas=bind_standard({'applications':data.get('ideas') or []},cands)
            result['ideas']=[bind_effect({'applications':[idea]},effect_cands)['applications'][0]
                if isinstance(idea,dict) and (idea.get('source_effect_id') or idea.get('effect_name')) else idea
                for idea in ideas['applications']]
            return result
        p5 = agent.run_agent(
            ctx, node="s5_ariz_p5", label="ARIZ Part5 지식베이스 적용", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART5", tier="T2",
            max_tokens=int(cfg("ariz.knowledge_max_tokens", 16000)),
            checker=lambda d: verify.check_ariz_part5(d, req(5)),
            normalizer=bind_part5,
            vars={"part4": p4.get("steps", []), "pc_macro": run.physical_contradiction_macro,
                  "pc_micro": run.physical_contradiction_micro,
                  "sfr_inventory": run.sfr_inventory,
                  "standards_block": K.standards_block(cands),
                  "separation_block": K.separation_block(catalog=separation_catalog_for(st)),
                  "effects_block": format_effects(effect_cands,len(K.effects()),sum(len(g['effects']) for g in K.effects()),len(K.standards()))},
            default={},
        ) or {}
        p5 = bind_part5(p5)
        issues = verify.check_ariz_part5(p5, req(5))
        if issues:
            raise AbortRun("ARIZ Part5 검토가 완전하지 않아 후속 분석을 중단합니다. " + "; ".join(issues))
        run.steps += _ariz_steps(p5)
        run.final_ideas = _text_list(p5.get("final_ideas"))
        run.unresolved_reason = p5.get("unresolved_reason") or ""
        _add_ideas(st, "D_ARIZ", [{**i, "ref": f"ARIZ {i.get('source_step','5.x')}"}
                                  for i in (p5.get("ideas") or [])], ref_key="ref")

    # Every ARIZ run records Part 6, including configurations pinned before it
    # existed. Advice never mutates the problem or dispatches an earlier stage.
    from . import reformulation
    p6 = agent.run_agent(
        ctx, node="s5_ariz_p6", label="ARIZ Part6 문제 재해석 제안", stage=Stage.S5.value,
        agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART6", tier="T2",
        max_tokens=int(cfg("ariz.reformulation_max_tokens", 8000)),
        checker=verify.check_ariz_part6,
        vars={"problem_reformulation_context": reformulation.part6_context(st, run)},
        default={},
    ) or {}
    issues = verify.check_ariz_part6(p6)
    if issues:
        raise AbortRun("ARIZ Part6 검토가 완전하지 않아 후속 분석을 중단합니다. " + "; ".join(issues))
    reformulation.record_ariz(run, p6)

    if 7 in parts_enabled and (run.solution_directions or run.final_ideas):
        p7 = agent.run_agent(
            ctx, node="s5_ariz_p7", label="ARIZ Part7 해결안 검증", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART7", tier="T2",
            max_tokens=int(cfg("ariz.validation_max_tokens", 16000)),
            checker=lambda d: verify.check_ariz(d, req(7)),
            vars={"ifr1": run.ifr1, "pc_macro": run.physical_contradiction_macro,
                  "pc_micro": run.physical_contradiction_micro,
                  "ideas": (run.final_ideas or []) + run.solution_directions},
            default={},
        ) or {}
        require_complete(p7, 7)
        run.steps += _ariz_steps(p7)
        run.verdicts = [v for v in (p7.get('verdicts') or []) if isinstance(v, dict)]
        for v in run.verdicts:
            for idea in st.solve.raw_ideas:
                if idea.title == v.get("idea_title"):
                    idea.detail["ariz_verdict"] = v
                    if v.get("is_tradeoff") or v.get("constraint_ok") is False:
                        idea.resolution_status = "TRADEOFF"
                        idea.strongest_objection = v.get("note", "ARIZ 검토 미통과")
            if v.get("is_tradeoff"):
                ctx.warn(f"ARIZ 7.2: '{v.get('idea_title')}'는 모순 해소가 아니라 절충으로 판정됨")
    elif 7 in parts_enabled:
        reason = "검증할 해결 방향이나 최종 아이디어가 도출되지 않아 해결안 평가를 실행하지 않았다."
        if run.unresolved_reason:
            reason += " 미해결 이유: " + run.unresolved_reason
        skipped = [ARIZStep(step_code=item["code"], step_title=item["title"],
                            status="SKIPPED", output=reason)
                   for item in K.ariz_part(7).get("steps", []) if item.get("required")]
        run.steps += skipped
        trace = ctx.start_step(node="s5_ariz_p7", label="ARIZ Part7 평가 대상 없음",
            stage=Stage.S5.value, agent_id="deterministic_review", prompt_id="", tier="")
        trace.output_json = {"steps": [step.model_dump() for step in skipped],
                             "verdicts": [], "skip_reason": reason}
        ctx.finish_step(trace, "SKIPPED")
    st.solve.ariz = run


def _ariz_steps(d: dict) -> list[ARIZStep]:
    return build_list(ARIZStep, d.get("steps"))


def _track_e(ctx: RunContext) -> None:
    st = ctx.state
    if not st.definition.trimming:
        return
    d = agent.run_agent(
        ctx, node="s5_track_e", label="Track E 트리밍 구체화", stage=Stage.S5.value,
        agent_id="trimming_specialist", prompt_id="P_S5_TRACK_E", tier="T2",
        vars={"trimming_items": [t.model_dump() for t in st.definition.trimming],
              "resources": digest.resources_digest(st),
              "target_system": digest.target_system(st)},
        default={},
    ) or {}
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"트리밍 규칙{a.get('rule','?')}/{a.get('target_component','')}"
    _add_ideas(st, "E_TRIMMING", apps, ref_key="ref")


def _track_f(ctx: RunContext) -> None:
    from .solve_contract import check_applications
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s5_track_f", label="Track F 진화 트렌드", stage=Stage.S5.value,
        agent_id="evolution_analyst", prompt_id="P_S5_TRACK_F", tier="T2",
        checker=check_applications,
        vars={"target_system": digest.target_system(st),
              "components": digest.components_digest(st),
              "resources": digest.resources_digest(st),
              "trends_block": K.trends_block()},
        default={},
    ) or {}
    _check_track_result(ctx, 'F_TRENDS', d)
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"{a.get('trend_id')} {a.get('trend_name')}"
    st.solve.trend_apps += apps
    st.scratch["s_curve"] = {"stage": d.get("s_curve_stage", ""), "note": d.get("s_curve_note", ""),
                             "bottleneck": d.get("bottleneck", "")}
    _add_ideas(st, "F_TRENDS", apps, ref_key="ref")


def _track_g(ctx: RunContext) -> None:
    from .solve_contract import check_applications
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s5_track_g", label="Track G 기능지향탐색(FOS)", stage=Stage.S5.value,
        agent_id="cross_domain_scout", prompt_id="P_S5_TRACK_G", tier="T2",
        checker=check_applications,
        vars={"required_functions": _required_functions(st),
              "target_system": digest.target_system(st),
              "operating_env": st.domain.operating_env,
              "contradictions": digest.contradictions_digest(st)},
        default={},
    ) or {}
    _check_track_result(ctx, 'G_FOS', d)
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"FOS/{a.get('leading_area','')}"
    st.solve.fos_apps += apps
    n0 = len(st.solve.raw_ideas)
    _add_ideas(st, "G_FOS", apps, ref_key="ref")
    for idea in st.solve.raw_ideas[n0:]:
        idea.novelty_class = "CROSS_DOMAIN"


def _track_h(ctx: RunContext) -> None:
    from .solve_contract import check_applications
    from .catalog_binding import bind_effect
    st = ctx.state
    required = _required_functions(st)
    from .ax.runtime import effect_candidates
    catalog = effect_candidates(st, required, limit=6)
    from .effect_catalog import format_effects
    d = agent.run_agent(
        ctx, node="s5_track_h", label="Track H 효과(Effects) 적용", stage=Stage.S5.value,
        agent_id="effects_specialist", prompt_id="P_S5_TRACK_H", tier="T2",
        checker=check_applications,
        normalizer=lambda data: bind_effect(data,catalog),
        vars={"required_functions": required,
              "target_system": digest.target_system(st),
              "operating_env": st.domain.operating_env,
              "effects_block": format_effects(catalog,len(K.effects()),sum(len(g['effects']) for g in K.effects()),len(K.standards()))},
        default={},
    ) or {}
    d = bind_effect(d,catalog)
    _check_track_result(ctx, 'H_EFFECTS', d)
    apps = [a for a in d.get('applications',[]) if isinstance(a,dict)]
    for a in apps:
        a["ref"] = f"효과/{a.get('effect_name','')}"
    st.solve.effect_apps += apps
    _add_ideas(st, "H_EFFECTS", apps, ref_key="ref")


def _check_track_result(ctx, track, data):
    from .solve_contract import check_applications
    issues = check_applications(data)
    if issues:
        raise AbortRun(f'{track} 분석 결과가 불완전합니다: ' + ' / '.join(issues))
    ctx.state.scratch.setdefault('ax_track_review_reasons', {})[track] = data.get('no_application_reason', '')


TRACK_FUNCS = {
    "A_MATRIX": _track_a, "B_SEPARATION": _track_b, "C_STANDARDS": _track_c,
    "D_ARIZ": _track_d_ariz, "E_TRIMMING": _track_e, "F_TRENDS": _track_f,
    "G_FOS": _track_g, "H_EFFECTS": _track_h,
}


def s5_solve(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S5.value)
    from .ax.mode_contract import adaptive
    if adaptive(st):
        from .ax.adaptive_tracks import run
        run(ctx)
        return
    tracks = domain.select_tracks(st, st.control.enabled_tracks)
    from .ax import enabled as ax_enabled
    if ax_enabled(st):
        tracks = list(st.scratch['ax_coordination']['tracks'])
    elif st.control.mode.value == "DEEP" and "D_ARIZ" not in tracks:
        tracks.append("D_ARIZ")
    if not ax_enabled(st) and st.definition.technical_contradictions and "A_MATRIX" not in tracks:
        tracks.append("A_MATRIX")
    if not ax_enabled(st) and st.definition.physical_contradictions and "B_SEPARATION" not in tracks:
        tracks.append("B_SEPARATION")
    if not ax_enabled(st) and domain.physical_allowed(st) and st.analysis.su_fields and "C_STANDARDS" not in tracks:
        tracks.append("C_STANDARDS")

    # Evidence planning consumes only pre-S5 facts; bounded track pool shares the call budget.
    st.scratch.setdefault("agent_cache", {})
    st.scratch.setdefault('ax_solve_start_seq', len(st.steps))
    track_state = st.model_copy(deep=True)
    track_state.steps, track_state.cost, track_state.control = st.steps, st.cost, st.control
    track_state.scratch["agent_cache"] = st.scratch["agent_cache"]
    track_ctx = RunContext(track_state)
    track_ctx.lock, track_ctx.budget, track_ctx.call_slots = ctx.lock, ctx.budget, ctx.call_slots
    def persist_tracks():
        # The evidence worker persists the parent concurrently. Publish merged
        # track results to that same parent before saving, retaining its evidence.
        with ctx.lock:
            st.solve = track_state.solve
            for key in ('ax_track_execution', 'ax_track_review_reasons', 'ax_action_results'):
                if key in track_state.scratch:
                    st.scratch[key] = track_state.scratch[key]
            if 's_curve' in track_state.scratch:
                st.scratch['s_curve'] = track_state.scratch['s_curve']
        ctx.persist()
    track_ctx.persist = persist_tracks
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            retrieval = pool.submit(_evidence, ctx)
            _run_tracks(track_ctx, tracks)
            retrieval.result()
    finally:
        # Preserve completed branches on interruption; continuation uses their
        # results and does not add duplicate applications or repeat paid calls.
        persist_tracks()
    if ax_enabled(st):
        from .ax.coordinator import complete_required
        complete_required(ctx)
    if st.control.mode.value == "DEEP" and ("D_ARIZ" not in st.solve.tracks_run or st.solve.ariz is None):
        raise AbortRun("ARIZ 실행기록이 없어 심층 분석을 완료할 수 없습니다. S5에서 이어서 실행해 주세요.")
    need_more = _merge(ctx)
    if ax_enabled(st):
        from .ax.coordinator import expand
        expand(ctx,need_more)
        from .ax.mode_contract import contract
        if not contract(st):
            st.scratch['ax_idea_inventory']=[i.model_dump(mode='json') for i in st.solve.raw_ideas]
        # Every consolidated idea remains available for detailed review.

    retries = st.control.retry_count.get("s5_solve", 0)
    from .ax.coherence import enabled as coherence_enabled
    if need_more and not ax_enabled(st) and not coherence_enabled(st) and retries < int(cfg("solve.max_escalations", 0)):
        st.control.retry_count["s5_solve"] = retries + 1
        extra = [t for t in cfg("tracks.escalation_tracks", ["D_ARIZ", "G_FOS", "H_EFFECTS"])
                 if t not in tracks]
        extra = domain.select_tracks(st, extra)
        extra = [t for t in extra if t not in tracks]
        if not extra:
            return
        ctx.emit("track_escalation", added=extra, reason=st.solve.gaps)
        ctx.warn(f"아이디어 부족 → 심화 트랙 추가 실행: {', '.join(extra)}")
        st.control.enabled_tracks = list(set(tracks + extra))
        _run_tracks(ctx, extra)
        _merge(ctx)
    ctx.persist()


def _run_tracks(ctx: RunContext, tracks: list[str]) -> None:
    st = ctx.state
    from .ax.mode_contract import contract, validate_tracks
    validate_tracks(st, tracks)
    seq = [t for t in ["A_MATRIX", "B_SEPARATION", "C_STANDARDS", "D_ARIZ", "E_TRIMMING",
                       "F_TRENDS", "G_FOS", "H_EFFECTS"] if t in tracks and t not in st.solve.tracks_run]
    ctx.emit("tracks", tracks=seq)
    # Track outputs are isolated, then merged in catalog order. Sharing one mutable
    # idea list would let FOS relabel another track's ideas during parallel execution.
    from .schema import SolveBundle
    st.scratch.setdefault("agent_cache", {})
    execution = st.scratch.setdefault('ax_track_execution', {})
    first_seq = len(st.steps)
    with ctx.lock:
        branches = {t: st.model_copy(deep=True) for t in seq}
    def execute(t):
        fn = TRACK_FUNCS.get(t)
        if not fn:
            return None
        branch = branches[t]
        branch.solve = SolveBundle()
        branch.scratch.pop('s_curve', None)
        branch.steps, branch.cost, branch.control = st.steps, st.cost, st.control
        branch.scratch["agent_cache"] = st.scratch["agent_cache"]
        child = RunContext(branch)
        child.lock, child.budget = ctx.lock, ctx.budget
        child.call_slots = ctx.call_slots
        child.persist = ctx.persist
        try:
            if contract(st):
                from .ax.action_runtime import executing, active_action
                from .ax.contracts import ActionTicket
                ticket = ActionTicket(action_type='GENERATE_BASELINE', parameters={'tracks':[t]},
                    target_version_ids=[st.scratch['ax_members']['definition']], model_role='REASONING',
                    expected_outputs=['TrackResult'], allowed_tools=['legacy_tracks'], reason='모드별 필수 기법 실행')
                if active_action.get():
                    fn(child)
                else:
                    with executing(child, ticket, context='track:' + t, optional=False):
                        fn(child)
            else:
                fn(child)
            prefix = 's5_ariz_' if t == 'D_ARIZ' else 's5_track_' + t[0].lower()
            failed = [step for step in st.steps if step.seq > first_seq and
                      step.node.startswith(prefix) and step.status == 'FAILED']
            if failed:
                raise AbortRun(f'{t} 호출 실패로 분석이 완료되지 않았습니다. 이어서 실행해 주세요.')
            return t, branch, None
        except Exception as exc:  # noqa: BLE001
            if not isinstance(exc, AbortRun):
                ctx.warn(f"트랙 {t} 실행 중 오류: {exc}")
            return t, branch, exc
    if not seq:
        return
    with ThreadPoolExecutor(max_workers=max(1, min(int(cfg("run.parallel_workers", 4)), len(seq)))) as pool:
        results = list(pool.map(execute, seq))
    failures = []
    for item in results:
        if not item:
            continue
        t, branch, failure = item
        if contract(st):
            st.scratch.setdefault('ax_action_results', {}).update(branch.scratch.get('ax_action_results', {}))
        if failure:
            budget_failure = 'budget' in str(failure).lower() or '예산' in str(failure)
            execution[t] = {'status': 'NOT_RUN_BUDGET' if budget_failure else 'FAILED', 'reason': str(failure), 'output_count': 0}
            failures.append(failure)
            continue
        for key in ("matrix_lookups", "principle_apps", "separation_apps", "standard_apps", "trend_apps", "fos_apps", "effect_apps", "raw_ideas", "gaps"):
            getattr(st.solve, key).extend(getattr(branch.solve, key))
        if branch.solve.ariz:
            st.solve.ariz = branch.solve.ariz
        if t == 'F_TRENDS' and "s_curve" in branch.scratch:
            st.scratch["s_curve"] = branch.scratch["s_curve"]
        if t not in st.solve.tracks_run:
            st.solve.tracks_run.append(t)
        from .solve_contract import application_count
        count = application_count(branch, t)
        reason = branch.scratch.get('ax_track_review_reasons', {}).get(t, '')
        st.scratch.setdefault('ax_track_review_reasons', {})[t] = reason
        execution[t] = {'status': 'COMPLETED' if count else 'REVIEWED_NO_APPLICATION',
                        'reason': reason or ('분석 결과를 저장했습니다.' if count else
                            '트랙 수행 후 저장된 적용안이 없습니다. 실행 이력과 적용 조건을 확인하세요.'),
                        'output_count': count}
    # Persist the parent after merging each finished batch. Child branches must
    # never replace this checkpoint with their isolated SolveBundle.
    ctx.persist()
    if failures:
        raise failures[0]


def _evidence(ctx: RunContext) -> None:
    from .evidence import discover
    discover(ctx, before_concepts=True)


def _merge(ctx: RunContext) -> bool:
    st = ctx.state
    if not st.solve.raw_ideas:
        ctx.warn("도출된 아이디어가 없다.")
        return True
    from .idea_consolidation import consolidate
    from .ax.mode_contract import contract
    if contract(st):
        from .ax.action_runtime import executing, episode
        from .ax.contracts import ActionTicket
        inventory=digest_json(st.solve.raw_ideas)
        pending=st.scratch.get('ax_merge_pending',{})
        if pending.get('inventory_hash')==inventory and pending.get('semantic_episode_id')==episode(st):
            ticket=ActionTicket.model_validate(pending['ticket'])
        else:
            parents = sorted(st.scratch.get('ax_action_results', {}))
            ticket = ActionTicket(action_type='MERGE_IDEAS',model_role='REASONING',
                parameters={'parent_action_instance_ids':parents, 'inventory_hash':inventory},
                target_version_ids=list(st.scratch.get('ax_members',{}).values()),
                expected_outputs=['MergedFamilies','RawDisposition'],allowed_tools=['legacy_tracks'],
                reason='전 원안의 기구·조건·출처를 비교해 대표안과 보류 이유를 보존한다.')
            st.scratch['ax_merge_pending']=dict(inventory_hash=inventory,semantic_episode_id=episode(st),ticket=ticket.model_dump(mode='json'))
            ctx.persist()
        with executing(ctx,ticket,context='solve:merge',optional=False):
            d = consolidate(ctx)
        st.scratch.pop('ax_merge_pending',None)
    else:
        d = consolidate(ctx)
    st.solve.coverage_note = d.get("coverage_note", "")
    st.solve.gaps = list(dict.fromkeys(st.solve.gaps + _text_list(d.get("gaps"))))
    covered = {cid for i in st.solve.raw_ideas if i.resolution_status == "RESOLVED" for cid in i.addresses}
    unmet = [kp.title for kp in st.definition.key_problems if not covered.intersection(kp.contradiction_ids)]
    st.solve.gaps.extend(f"미해결 핵심 문제: {title}" for title in unmet)
    need_more = bool(unmet) or bool(d.get("need_more"))
    ctx.emit("artifact", kind="IDEAS", data={"count": len(st.solve.raw_ideas),
                                             "tracks": st.solve.tracks_run,
                                             "need_more": need_more})
    return need_more


def digest_json(ideas):
    from .ax.contracts import digest as fingerprint
    return fingerprint([i.model_dump(mode='json') for i in ideas])


# ════════════════════════════════════════════════ S6
def s6_concept(ctx: RunContext) -> None:
    from .quality import generate_concepts
    generate_concepts(ctx)


# ════════════════════════════════════════════════ S7
def _gate_fingerprint(st):
    return hashlib.sha256(json.dumps([c.model_dump(mode='json') for c in st.concepts] +
        [st.constraints.model_dump(mode='json'), [c.model_dump(mode='json') for c in st.constraint_checks]],
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def s7_gate(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S7.value)

    payload = ctx.resume_payload() or st.scratch.get('ax_gate_response_pending')
    if payload:
        decisions = payload.get("decisions") or {}
        expected = set(st.scratch.get('adaptive_gate_pending_ids', [c.concept_id for c in st.constraint_checks if c.verdict == 'CONDITIONAL']))
        recorded = st.scratch.get('ax_gate_response_recorded')
        if not recorded and (set(decisions) != expected or any(v not in ('accept', 'drop') for v in decisions.values())):
            raise ValueError("보류된 모든 해결책의 유지·제외 판정이 필요합니다.")
        from .ax.effect_history import user_reviews
        from .ax.mode_contract import contract
        if contract(st):
            st.scratch['ax_gate_response_pending'] = payload
        if recorded:
            changed = st.scratch.get('ax_gate_delta_pending', [])
        else:
            from .ax.mode_contract import unified
            if unified(st):
                from .ax.feedback_events import user_decisions
                user_decisions(st, decisions, payload, st.scratch.get('ax_response_origin', 'gate-' + _gate_fingerprint(st)))
                changed = []
            else:
                changed = user_reviews(st, payload.get('application_reviews', []), decisions,
                                       st.scratch.get('ax_response_origin', 'legacy-' + _gate_fingerprint(st)))
            if contract(st):
                st.scratch['ax_gate_response_recorded'] = True
                st.scratch['ax_gate_delta_pending'] = changed
                ctx.persist()
        for cid, choice in decisions.items():
            chk = st.check_for(cid)
            if not chk:
                continue
            if choice == "accept":
                # User acceptance cannot turn missing evidence into technical compliance.
                chk.verdict = "CONDITIONAL"
                chk.requires_user_decision = False
            elif choice == "drop":
                from .ax.mode_contract import unified
                if unified(st): st.scratch.setdefault('adaptive_dropped_candidates',[]).append(cid)
                concept = st.concept(cid)
                if concept:
                    if unified(st):
                        from .ax.candidate_disposition import record
                        record(st,concept,'USER_DROP','제약 검토에서 사용자가 제외함',st.scratch.get('ax_response_origin'))
                    st.scratch.setdefault('excluded_concepts', []).append({'idea': concept.title, 'reason': '제약 검토에서 사용자가 제외함'})
                st.concepts = [c for c in st.concepts if c.id != cid]
                st.constraint_checks = [c for c in st.constraint_checks if c.concept_id != cid]
        if changed:
            _recheck_effect_conditions(ctx, changed)
        for key in ('ax_gate_response_pending','ax_gate_response_recorded','ax_gate_delta_pending'):
            st.scratch.pop(key,None)
        st.scratch['gate_decisions'] = {'decisions': dict(decisions), 'fingerprint': _gate_fingerprint(st)}
        st.scratch.pop('adaptive_gate_pending_ids',None)
        # Preserve failed model-call records. A complete human decision resolves only
        # gate-call failures, without declaring the retained concepts compliant.
        resolved = st.scratch.setdefault('resolved_step_failures', {})
        for step in st.steps:
            if step.status == 'FAILED' and (step.node == 's7_gate' or step.node.startswith('s7_gate_')):
                resolved[step.step_id] = '사용자 제약 판정 완료: 조건부 유지 또는 제외. 자동 검토 실패 기록은 보존함.'
        ctx.emit('gate_decisions', decisions=decisions)
        ctx.persist()
        return

    if st.scratch.get('gate_decisions', {}).get('fingerprint') == _gate_fingerprint(st):
        return

    from .ax.mode_contract import unified
    if unified(st): st.scratch['adaptive_gate_cohort']=[c.id for c in st.concepts]

    if not st.constraints.items:
        st.constraint_checks = [ConstraintCheckResult(concept_id=c.id, verdict="PASS")
                                for c in st.concepts]
        from .ax.effect_history import gate_reviews
        gate_reviews(st, 's7_gate')
        return

    concepts = digest.concepts_for_gate(st)
    from .ax.mode_contract import unified
    from .ax.contracts import digest as hash_input
    gate_cache=st.scratch.setdefault('adaptive_gate_cache',{}) if unified(st) else {}
    gate_keys={c['concept_id']:hash_input([c,verify.constraints_full(st),st.scratch.get('ax_condition_facts',{}),
        st.scratch.get('ax_bundle',{}).get('models'),st.scratch.get('ax_bundle',{}).get('prompts',{}).get('P_S7_GATEKEEPER')]) for c in concepts}
    reused_ids={cid for cid,key in gate_keys.items() if key in gate_cache}
    cached_results=[ConstraintCheckResult.model_validate(r) for cid in reused_ids for r in gate_cache[gate_keys[cid]]]
    review_sources={}
    concepts=[c for c in concepts if c['concept_id'] not in reused_ids]
    batch_size = max(1, min(int(cfg('constraints.max_concepts_per_call', 2)),
                           int(cfg('constraints.max_pairs_per_call', 24)) // max(1, len(st.constraints.items))))
    def gate_batch(start):
        batch = concepts[start:start+batch_size]
        condition_facts = st.scratch.get('ax_condition_facts', {})
        d = agent.run_agent(
            ctx, node=f"s7_gate_{start // batch_size + 1}", label=f"제약 검토 {start+1}–{start+len(batch)}/{len(concepts)}", stage=Stage.S7.value,
            agent_id="gatekeeper", prompt_id="P_S7_GATEKEEPER", tier="T2",
            system_override="You are a strict compliance gatekeeper. Output JSON only. "
                            "Judge only constraint compliance, nothing else. "
                            + ("The following facts are USER_REPORTED, not measured proof. Preserve unresolved obligations: "
                               + json.dumps(condition_facts, ensure_ascii=False) if condition_facts else ""),
            vars={"constraints_full": verify.constraints_full(st), "concepts_for_gate": batch}, default={}) or {}
        ids = {c['concept_id'] for c in batch}
        step = next((s for s in reversed(st.steps) if s.node==f's7_gate_{start // batch_size + 1}' and s.status in ('OK','SKIPPED')), None)
        if step:
            for row in d.get('results',[]):
                if isinstance(row,dict) and row.get('concept_id') in ids:
                    review_sources[row['concept_id']]=step.step_id
        parsed=[r for r in build_list(ConstraintCheckResult, d.get('results')) if r.concept_id in ids]
        if unified(st):
            for cid in ids:
                rows=[r.model_dump(mode='json') for r in parsed if r.concept_id==cid]
                if rows: gate_cache[gate_keys[cid]]=rows
        return parsed

    with ThreadPoolExecutor(max_workers=max(1, int(cfg("run.parallel_workers", 4)))) as pool:
        raw_results = cached_results + [r for batch in pool.map(gate_batch, range(0, len(concepts), batch_size)) for r in batch]

    results: list[ConstraintCheckResult] = []
    by_id = {c.id: c for c in st.concepts}
    for c in st.concepts:
        supplied = [r for r in raw_results if r.concept_id == c.id]
        if supplied:
            combined = supplied[0].model_copy(deep=True)
            combined.per_constraint = [row for result in supplied for row in result.per_constraint]
            combined.violated_ids = list(dict.fromkeys(cid for result in supplied for cid in result.violated_ids))
            combined.mitigation = ' / '.join(dict.fromkeys(result.mitigation for result in supplied if result.mitigation))
            if any(result.verdict == 'FAIL' for result in supplied):
                combined.verdict = 'FAIL'
            results.append(combined)
        else:  # 판정 누락분은 CONDITIONAL 처리
            results.append(ConstraintCheckResult(concept_id=c.id, verdict="CONDITIONAL",
                                                 mitigation="자동 판정 누락 — 사용자 확인 필요",
                                                 requires_user_decision=True))
    normalized = []
    diagnostics = []
    for result in results:
        result, diagnostic = verify.normalize_constraint_result(result, st.constraints)
        normalized.append(result)
        diagnostics.append(dict(diagnostic, concept_id=result.concept_id))
    results = normalized
    st.scratch['constraint_normalization'] = diagnostics
    # 코드 기반 수치 재검증(보조)
    for r in results:
        c = by_id.get(r.concept_id)
        if not c:
            continue
        # Separate fields: an observation in one must not qualify a target or
        # parameter in another as a measured result.
        blob = "\n".join([c.description, c.expected_effect, *c.changes_to_system])
        for con in st.constraints.hard_items():
            msg = verify.numeric_violation(blob, con)
            if msg:
                r.verdict = "FAIL"
                r.requires_user_decision = False
                if con.id not in r.violated_ids:
                    r.violated_ids.append(con.id)
                diagnostic = next(d for d in diagnostics if d['concept_id'] == r.concept_id)
                diagnostic.setdefault('numeric_overrides', []).append({
                    'constraint_id': con.id, 'reason': msg,
                    'constraint': con.model_dump(mode='json'), 'source_text': blob,
                    'previous_rows': [row for row in r.per_constraint if row.get('constraint_id') == con.id]})
                # Keep one authoritative row, with the original AI decision in
                # diagnostics and its saved step, rather than UNKNOWN + FAIL.
                r.per_constraint = [row for row in r.per_constraint if row.get('constraint_id') != con.id]
                r.per_constraint.append({"constraint_id": con.id, "verdict": "FAIL",
                                         "reason": f"수치 자동검증: {msg}"})
                diagnostic['normalized_verdict'] = 'FAIL'
                if con.id not in diagnostic['hard_failure_ids']:
                    diagnostic['hard_failure_ids'].append(con.id)
                for key in ('hard_unknown_ids', 'unresolved_constraint_ids', 'missing_hard_ids', 'missing_constraint_ids'):
                    diagnostic[key] = [cid for cid in diagnostic[key] if cid != con.id]
    st.constraint_checks = results
    from .ax.feedback_events import model_review
    for row in results:
        if row.concept_id in review_sources:
            diagnostic = next(d for d in diagnostics if d['concept_id'] == row.concept_id)
            review = row.model_dump(mode='json')
            # This code-owned marker is added after parsing the model response.
            # Store enough evidence to replay any override when building labels.
            review['numeric_validation'] = {'contract': verify.NUMERIC_VALIDATION_CONTRACT,
                'overrides': diagnostic.get('numeric_overrides', [])}
            model_review(st,st.concept(row.concept_id),review,stage='s7_gate',
                step_id=review_sources[row.concept_id],rubric='P_S7_GATEKEEPER+'+verify.NUMERIC_VALIDATION_CONTRACT,
                model=st.scratch.get('ax_bundle',{}).get('models',{}).get('T2'))
    from .ax.effect_history import gate_reviews
    gate_reviews(st, 's7_gate')

    failed = [r for r in results if r.verdict == "FAIL"]
    cond = [r for r in results if r.verdict == "CONDITIONAL"]
    passed = [r for r in results if r.verdict == "PASS"]
    ctx.emit("artifact", kind="CONSTRAINT_GATE",
             data={"pass": len(passed), "conditional": len(cond), "fail": len(failed)})

    for r in failed:  # 제약 위반 개념은 폐기
        c = by_id.get(r.concept_id)
        if c:
            if unified(st):
                from .ax.candidate_disposition import record
                record(st,c,'CONSTRAINT_FAIL',r.model_dump(mode='json'),review_sources.get(c.id))
            from .ax import enabled as ax_enabled
            if ax_enabled(st):
                st.scratch.setdefault('ax_excluded', []).append(c.model_dump(mode='json'))
                st.scratch.setdefault('ax_constraint_failures', {})[c.id]=r.model_dump(mode='json')
            st.scratch.setdefault("excluded_concepts", []).append(
                {"idea": c.title, "source_idea_ids": list(c.source_idea_ids),
                 "reason": f"제약 위반: {', '.join(r.violated_ids) or '판정 FAIL'}"})
    st.concepts = [c for c in st.concepts if c.id not in {r.concept_id for r in failed}]
    st.constraint_checks = [r for r in results if r.verdict != "FAIL"]

    min_pass = int(cfg("constraints.min_passing_concepts", 5))
    if unified(st):
        accepted=st.scratch.get('gate_decisions',{}).get('decisions',{})
        cond=[r for r in cond if not (r.concept_id in reused_ids and accepted.get(r.concept_id)=='accept')]
        for r in st.constraint_checks:
            if r.concept_id in reused_ids and accepted.get(r.concept_id)=='accept': r.requires_user_decision=False
    if cond and not st.scratch.get('ax_autonomous_gate') and (len(passed) < min_pass or any(r.requires_user_decision for r in cond)):
        if unified(st): st.scratch['adaptive_gate_pending_ids']=[r.concept_id for r in cond]
        ctx.persist()
        raise HumanInterrupt("DECIDE", "제약 판정이 보류된 해결책을 확인해 주세요", {
            "conditional": [{
                "concept_id": r.concept_id,
                "title": by_id[r.concept_id].title if r.concept_id in by_id else "",
                "one_liner": by_id[r.concept_id].one_liner if r.concept_id in by_id else "",
                "mitigation": r.mitigation,
                "per_constraint": r.per_constraint,
            } for r in cond],
            "constraints": verify.constraints_full(st),
        }, Stage.S7.value)
    ctx.persist()


def _recheck_effect_conditions(ctx, candidate_ids):
    """Only changed candidates revisit the existing S7 handler; no new HITL gate."""
    st = ctx.state
    branch = st.model_copy(deep=True)
    branch.concepts = [c for c in branch.concepts if c.id in candidate_ids]
    branch.constraint_checks = []
    branch.scratch.pop('resume_payload', None)
    branch.scratch.pop('gate_decisions', None)
    for key in ('ax_gate_response_pending','ax_gate_response_recorded','ax_gate_delta_pending'):
        branch.scratch.pop(key,None)
    branch.scratch['ax_autonomous_gate'] = True
    branch.steps, branch.cost, branch.control = st.steps, st.cost, st.control
    child = RunContext(branch)
    child.lock, child.budget, child.call_slots = ctx.lock, ctx.budget, ctx.call_slots
    child.persist = ctx.persist
    s7_gate(child)
    # A user-reported condition is insufficient to promote the whole candidate.
    for check in branch.constraint_checks:
        if check.verdict == 'PASS':
            check.verdict = 'CONDITIONAL'
            check.mitigation = '사용자 보고 조건을 반영했습니다. 다른 의무와 실증은 별도로 확인해야 합니다.'
        check.requires_user_decision = False
    st.concepts = [c for c in st.concepts if c.id not in candidate_ids] + branch.concepts
    st.constraint_checks = [c for c in st.constraint_checks if c.concept_id not in candidate_ids] + branch.constraint_checks
    for key in ('ax_excluded', 'ax_constraint_failures', 'excluded_concepts'):
        if key in branch.scratch:
            st.scratch[key] = branch.scratch[key]


# ════════════════════════════════════════════════ S8
def s8_evaluate(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S8.value)
    st.evaluation.problem_reformulation_review = None
    if not st.concepts:
        ctx.warn("평가할 개념이 없다.")
        ctx.persist()
        return

    from .meeting import evaluate

    all_scores = evaluate(ctx)
    from .ax.feedback_events import meeting_reviews
    meeting_reviews(st,all_scores)

    st.evaluation.evaluations = _aggregate(st, all_scores)
    _rank(ctx)
    ctx.persist()


def _aggregate(st, scores: list[ReviewerScore]) -> list[ConceptEvaluation]:
    weights = dict(cfg("evaluation.dimension_weights", {}))
    weights.update(cfg(f"evaluation.problem_type_weights.{domain.problem_type(st)}", {}))
    low_risk = float(cfg("evaluation.quadrant_thresholds.low_risk_max", 2.5))
    high_ret = float(cfg("evaluation.quadrant_thresholds.high_return_min", 3.5))
    evals: list[ConceptEvaluation] = []
    for c in st.concepts:
        mine = [s for s in scores if s.concept_id == c.id]
        if not mine:
            evals.append(ConceptEvaluation(concept_id=c.id, total_score=0.0))
            continue
        agg: dict[str, float] = {}
        for dim in {s.dimension for s in mine}:
            vals = [(s.score, max(0.1, s.confidence)) for s in mine if s.dimension == dim]
            agg[dim] = round(sum(v * w for v, w in vals) / sum(w for _, w in vals), 2)
        wsum = sum(weights.get(d, 0.0) for d in agg) or 1.0
        total = round(sum(agg[d] * weights.get(d, 0.0) for d in agg) / wsum, 2)
        if c.quality_status != "PASS":
            total = min(total, 3.0)
        risk_score = agg.get("RISK", 3.0)
        ret = round((agg.get("GOAL", agg.get("QUALITY", 3.0)) + agg.get("RESOLUTION", agg.get("FEASIBILITY", 3.0))) / 2, 2)
        risk_inv = 5 - risk_score          # 값이 클수록 위험
        quadrant = ("QUICK_WIN" if risk_inv <= low_risk and ret >= high_ret else
                    "BIG_BET" if risk_inv > low_risk and ret >= high_ret else
                    "FILL_IN" if risk_inv <= low_risk else "AVOID")
        dissent = [f"{s.reviewer_role}({s.dimension} {s.score}): {s.rationale[:120]}"
                   for s in mine if abs(s.score - agg.get(s.dimension, s.score)) >= 1.5]
        red = [f for s in mine for f in s.red_flags]
        gate = st.check_for(c.id)
        gate_bad = bool(gate and gate.verdict in ("FAIL", "CONDITIONAL"))
        if any(s.dimension == "SAFETY" and s.score <= 1.5 and s.red_flags for s in mine):
            total, quadrant = min(total, 2.0), "AVOID"
        if any("제약위반" in f for f in red):
            # 제약의 최종 판정 권한은 S7 게이트에 있다. 평가자 지적은 게이트가 동의할 때만 강등.
            if gate_bad:
                total = min(total, 2.0)
                quadrant = "AVOID"
            else:
                total = round(max(1.0, total - 0.3), 2)
        evals.append(ConceptEvaluation(
            concept_id=c.id, scores=mine, aggregate=agg, total_score=total,
            risk_level="LOW" if risk_inv <= 2 else "HIGH" if risk_inv >= 3.5 else "MID",
            return_level="HIGH" if ret >= high_ret else "LOW" if ret < 2.5 else "MID",
            quadrant=quadrant, dissent=dissent))
    return evals



def _ranking_errors(data, expected_ids):
    rows = data.get("ranking") if isinstance(data, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return ["FATAL-RANK: ranking 배열이 필요합니다."]
    ids = [row.get("concept_id") for row in rows]
    ranks = [row.get("rank") for row in rows]
    if (any(not isinstance(identifier, str) for identifier in ids)
            or len(ids) != len(expected_ids) or set(ids) != expected_ids):
        return ["FATAL-RANK: 모든 입력 후보를 정확히 한 번씩 포함하세요."]
    if any(type(rank) is not int for rank in ranks) or set(ranks) != set(range(1, len(rows)+1)):
        return ["FATAL-RANK: 순위는 1부터 후보 수까지 중복 없이 지정하세요."]
    return []


def _rank(ctx: RunContext) -> None:
    st = ctx.state
    st.evaluation.problem_reformulation_review = None
    table = [{
        "concept_id": e.concept_id,
        "title": (st.concept(e.concept_id).title if st.concept(e.concept_id) else ""),
        "aggregate": e.aggregate, "total": e.total_score, "quadrant": e.quadrant,
        "risk": e.risk_level, "return": e.return_level,
        "red_flags": [f for s in e.scores for f in s.red_flags][:3],
        "improvements": [s.improvement_suggestion for s in e.scores if s.improvement_suggestion],
        "quality_status": st.concept(e.concept_id).quality_status,
    } for e in st.evaluation.evaluations]
    meta = [{"concept_id": c.id, "novelty_class": c.novelty_class,
             "change_scale": c.change_scale, "maturity": c.maturity} for c in st.concepts]

    d = agent.run_agent(
        ctx, node="s8_rank", label="포트폴리오 구성·우선순위", stage=Stage.S8.value,
        agent_id="portfolio_manager", prompt_id="P_S8_RANK", tier="T2",
        vars={"aggregate_table": table, "concept_meta": meta,
              "dissent": [d for e in st.evaluation.evaluations for d in e.dissent][:10],
              "candidate_count": len(table)},
        checker=lambda data: _ranking_errors(data, {c.id for c in st.concepts}),
        max_tokens=int(cfg("evaluation.rank_max_tokens", 32000)),
        default=None,
    )
    if not isinstance(d, dict):
        raise AbortRun("순위 산정 응답이 없어 후보를 유지한 채 중단합니다. 재시도하면 완료된 직군별 평가를 재사용합니다.")

    errors = _ranking_errors(d, {c.id for c in st.concepts})
    if errors:
        raise AbortRun("전체 후보의 순위 판정이 불완전하여 후보를 유지합니다: " + "; ".join(errors))
    order = {r["concept_id"]: r["rank"] for r in d["ranking"]}
    for e in st.evaluation.evaluations:
        e.rank = order.get(e.concept_id, 99)
    st.evaluation.evaluations.sort(key=lambda e: e.rank)
    st.evaluation.ranking_note = d.get("ranking_note", "")
    st.evaluation.portfolio_note = d.get("portfolio_note", "")
    st.evaluation.roadmap = d.get("roadmap") or []

    ctx.emit("artifact", kind="RANKING",
             data=[{"rank": e.rank, "title": st.concept(e.concept_id).title if st.concept(e.concept_id) else "",
                    "score": e.total_score, "quadrant": e.quadrant}
                   for e in st.evaluation.evaluations])


# ════════════════════════════════════════════════ S9
def _applied_principles(st) -> list[dict]:
    """이번 실행에서 실제로 적용된 원리·표준해를 중복 없이 모은다."""
    out: list[dict] = []
    seen: set[str] = set()

    def add(ref: str, summary: str) -> None:
        key = ref.strip()
        if key and key not in seen:
            seen.add(key)
            out.append({"ref": key, "summary": summary})

    for m in st.solve.matrix_lookups:
        for pid in m.principle_ids:
            add(f"발명원리 {pid} {K.principle_name(pid)}", K.principle_hint(pid))
    for a in st.solve.principle_apps:
        pid = a.get("principle_id")
        if pid:
            add(f"발명원리 {pid} {K.principle_name(int(pid))}", a.get("interpretation", ""))
    for a in st.solve.separation_apps:
        if a.get('applicable') is not False:
            from .separation_contract import display_name
            add(display_name(a), a.get("how") or a.get("interpretation", ""))
    for a in st.solve.standard_apps:
        add(f"표준해 {a.get('standard_code') or a.get('standard_id', '')} {a.get('standard_title','')}", a.get("transformation") or a.get("interpretation", ""))
    for a in st.solve.effect_apps:
        add(f"과학효과 {a.get('source_effect_id') or '추가 가설'} {a.get('effect_name','')}",a.get('principle',''))
    return out


def s8_references(ctx: RunContext) -> None:
    from .evidence import attach
    ctx.set_stage("S8_REFERENCES")
    attach(ctx)


def s9_report(ctx: RunContext) -> None:
    from . import render  # 지연 임포트(템플릿 로딩 비용 회피)

    st = ctx.state
    ctx.set_stage(Stage.S9.value)
    from .ax import enabled as ax_enabled
    if ax_enabled(st):
        md=render.render_report(st,{})
        from .ax.report import project
        st.report=ReportArtifact(narrative=project(st).report.narrative,template_id='report_full',markdown=md,word_count=len(md))
        render.save(st,md)
        ctx.emit('report',length=len(md))
        ctx.persist()
        return
    top = [{"title": (st.concept(e.concept_id).title if st.concept(e.concept_id) else ""),
            "one_liner": (st.concept(e.concept_id).one_liner if st.concept(e.concept_id) else ""),
            "expected_effect": (st.concept(e.concept_id).expected_effect if st.concept(e.concept_id) else ""),
            "score": e.total_score, "quadrant": e.quadrant}
           for e in st.evaluation.evaluations[:3]]

    narrative = agent.run_agent(
        ctx, node="s9_narrative", label="리포트 요약문 생성", stage=Stage.S9.value,
        agent_id="report_generator", prompt_id="P_S9_NARRATIVE", tier="T1",
        vars={"frame": digest.frame_digest(st),
              "contradictions": digest.contradictions_digest(st),
              "top_concepts": top,
              "eval_digest": st.evaluation.ranking_note,
              "warnings": st.control.warnings[:6]},
        default={},
    ) or {}

    report = ReportArtifact(narrative=narrative,
                            template_id="report_lite" if st.control.mode == RunMode.LITE else "report_full")
    try:
        md = render.render_report(st, report.narrative)
    except Exception as exc:  # noqa: BLE001
        # 템플릿 하나가 깨졌다고 리포트 전체를 잃지 않는다.
        ctx.warn(f"상세 리포트 렌더링 실패({exc}) → 간이 서식으로 대체합니다.")
        md = render.render_report(st, report.narrative, template="report_lite.md.j2")
        report.template_id = "report_lite"
    report.markdown = md
    report.word_count = len(md)
    st.report = report
    render.save(st, md)
    ctx.emit("report", length=len(md))
    ctx.persist()


# ════════════════════════════════════════════════ S10
def record_feedback(st, payload: dict, distill: dict | None = None) -> int:
    """피드백 페이로드를 상태에 반영하고 RAG에 적재한다. 완주 후 API에서도 재사용."""
    from . import store
    from .schema import FeedbackArtifact, SolutionFeedback

    fb = FeedbackArtifact(
        overall_rating=int(payload.get("overall_rating") or 0),
        missing_perspective=payload.get("missing_perspective", ""),
        would_reuse=payload.get("would_reuse"),
        solution_feedback=build_list(SolutionFeedback, payload.get("solution_feedback")),
        distilled=distill or {},
    )
    if distill is None:
        # Post-run edits reuse supplied mechanisms/comments without another model call.
        fb.distilled = {"generalized_problem": st.intake.frame.restated_problem,
                        "domain_lesson": fb.missing_perspective,
                        "accepted_patterns": [], "rejected_patterns": []}
        for item in fb.solution_feedback:
            concept = st.concept(item.concept_id)
            if item.rating >= 4 and concept and concept.working_principle:
                fb.distilled["accepted_patterns"].append(concept.working_principle)
            elif item.rating <= 2:
                fb.distilled["rejected_patterns"].extend([item.comment] if item.comment else item.reason_tags)
    st.feedback = fb
    from .ax.mode_contract import unified
    if unified(st):
        from .ax.feedback_events import final_feedback
        changed = final_feedback(st, payload)
        if not changed or st.scratch.get('training_consent') != 'PROJECT_ONLY':
            return 0
        return rag.write_feedback(st, fb.distilled)
    for s in fb.solution_feedback:
        store.save_feedback(st.run_id, s.concept_id, s.rating, s.adopted, s.reason_tags, s.comment)
    return rag.write_feedback(st, fb.distilled)


def s10_feedback(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S10.value)
    payload = ctx.resume_payload()
    if payload is None:
        raise HumanInterrupt("FEEDBACK", "해결책에 대한 피드백을 남겨 주세요", {
            "concepts": [{"concept_id": c.id, "title": c.title, "one_liner": c.one_liner}
                         for c in st.concepts],
        }, Stage.S10.value)

    raw = payload.get("solution_feedback") or []
    distill = {}
    if raw:
        distill = agent.run_agent(
            ctx, node="s10_distill", label="피드백 정제", stage=Stage.S10.value,
            agent_id="rag_writer", prompt_id="P_S10_FEEDBACK_DISTILL", tier="T1",
            vars={"problem_digest": digest.frame_digest(st),
                  "contradiction_digest": digest.contradictions_digest(st),
                  "feedback_raw": [{"title": (st.concept(s.get("concept_id", "")).title
                                              if st.concept(s.get("concept_id", "")) else ""),
                                    "mechanism": (st.concept(s.get("concept_id", "")).working_principle if st.concept(s.get("concept_id", "")) else ""),
                                    "conditions": (st.concept(s.get("concept_id", "")).assumptions if st.concept(s.get("concept_id", "")) else []),
                                    "rating": s.get("rating"), "adopted": s.get("adopted"),
                                    "comment": s.get("comment"), "tags": s.get("reason_tags")}
                                   for s in raw if isinstance(s, dict)]},
            default={},
        ) or {}
    n = record_feedback(st, payload, distill)
    ctx.emit("rag_write", records=n)
    ctx.persist()
