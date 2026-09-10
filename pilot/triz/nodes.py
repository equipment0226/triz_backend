"""파이프라인 노드 구현 (S0~S10)."""
from __future__ import annotations

import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from . import agent, digest, domain, knowledge as K, llm, personas as PF, prompts_registry as P, rag, verify
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
    st.cost.budget_usd = float(cfg("run.budget_usd", 3.0))
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
        st.solve.raw_ideas.append(RawIdea(
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
        ))
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
    st = ctx.state
    for pc in _pick_pcs(st):
        d = agent.run_agent(
            ctx, node="s5_track_b", label=f"Track B 분리원리({pc.id})", stage=Stage.S5.value,
            agent_id="inventor_b", prompt_id="P_S5_TRACK_B", tier="T2", rubric_id="R5_B",
            checker=verify.check_separation,
            vars={"element": pc.element, "parameter": pc.parameter,
                  "state_a": pc.state_a, "reason_a": pc.reason_a,
                  "state_b": pc.state_b, "reason_b": pc.reason_b, "scale": pc.scale,
                  "target_system": digest.target_system(st),
                  "resources": digest.resources_digest(st),
                  "su_fields": digest.su_fields_digest(st),
                  "separation_block": K.separation_block()},
            default={},
        ) or {}
        if d.get("redefine_hint"):
            st.solve.gaps.append(d["redefine_hint"])
        for application in d.get('applications') or []:
            application['source_pc_id'] = pc.id
        apps = [a for a in (d.get("applications") or []) if a.get("applicable")]
        for a in apps:
            a["ref"] = f"{a.get('kind')} 분리"
        st.solve.separation_apps += (d.get("applications") or [])
        _add_ideas(st, "B_SEPARATION", apps, ref_key="ref", addresses=[pc.id])


def _track_c(ctx: RunContext) -> None:
    st = ctx.state
    for su in st.analysis.su_fields[:2]:
        cands = K.candidate_standards(su.completeness, su.effect)
        if not cands:
            continue
        d = agent.run_agent(
            ctx, node="s5_track_c", label=f"Track C 76표준해({su.id})", stage=Stage.S5.value,
            agent_id="standards_specialist", prompt_id="P_S5_TRACK_C", tier="T2", rubric_id="R5_C",
            checker=lambda data: verify.check_standards(data, [c['code'] for c in cands]),
            vars={"s1": su.s1, "s2": su.s2, "field": su.field,
                  "completeness": su.completeness, "effect": su.effect,
                  "target_system": digest.target_system(st),
                  "resources": digest.resources_digest(st),
                  "standards_block": K.standards_block(cands)},
            default={},
        ) or {}
        apps = d.get("applications") or []
        for a in apps:
            a["ref"] = f"표준해 {a.get('standard_code')}"
            a['source_su_id'] = su.id
        st.solve.standard_apps += apps
        _add_ideas(st, "C_STANDARDS", apps, ref_key="ref")


def _track_d_ariz(ctx: RunContext) -> None:
    st = ctx.state
    run = ARIZRun()
    parts_enabled = cfg("ariz.enabled_parts", [1, 2, 3, 4, 5, 7])
    tcs = _pick_tcs(st, 1)
    key_contra = tcs[0].model_dump() if tcs else (
        st.definition.physical_contradictions[0].model_dump()
        if st.definition.physical_contradictions else {})

    def req(part_id: int) -> list[str]:
        return [s["code"] for s in K.ariz_part(part_id).get("steps", []) if s.get("required")]

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
        run.steps += _ariz_steps(p4)
        run.slp_model = p4.get("slp_model", "")
        run.solution_directions = _text_list(p4.get("solution_directions"))
        _add_ideas(st, "D_ARIZ", [{**i, "ref": f"ARIZ {i.get('source_step','4.x')}"}
                                  for i in (p4.get("ideas") or [])], ref_key="ref")

    if 5 in parts_enabled:
        su = st.analysis.su_fields[0] if st.analysis.su_fields else None
        cands = K.candidate_standards(su.completeness, su.effect) if su else K.standards()[:10]
        p5 = agent.run_agent(
            ctx, node="s5_ariz_p5", label="ARIZ Part5 지식베이스 적용", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART5", tier="T2",
            vars={"part4": p4.get("steps", []), "pc_macro": run.physical_contradiction_macro,
                  "pc_micro": run.physical_contradiction_micro,
                  "sfr_inventory": run.sfr_inventory,
                  "standards_block": K.standards_block(cands),
                  "separation_block": K.separation_block(),
                  "effects_block": K.effects_block()},
            default={},
        ) or {}
        run.steps += _ariz_steps(p5)
        run.final_ideas = _text_list(p5.get("final_ideas"))
        _add_ideas(st, "D_ARIZ", [{**i, "ref": f"ARIZ {i.get('source_step','5.x')}"}
                                  for i in (p5.get("ideas") or [])], ref_key="ref")

    if 7 in parts_enabled and (run.solution_directions or run.final_ideas):
        p7 = agent.run_agent(
            ctx, node="s5_ariz_p7", label="ARIZ Part7 해결안 검증", stage=Stage.S5.value,
            agent_id="ariz_specialist", prompt_id="P_S5_ARIZ_PART7", tier="T2",
            max_tokens=int(cfg("ariz.validation_max_tokens", 8000)),
            vars={"ifr1": run.ifr1, "pc_macro": run.physical_contradiction_macro,
                  "pc_micro": run.physical_contradiction_micro,
                  "ideas": (run.final_ideas or []) + run.solution_directions},
            default={},
        ) or {}
        run.steps += _ariz_steps(p7)
        run.verdicts = [v for v in (p7.get('verdicts') or []) if isinstance(v, dict)]
        for v in (p7.get("verdicts") or []):
            for idea in st.solve.raw_ideas:
                if idea.title == v.get("idea_title"):
                    idea.detail["ariz_verdict"] = v
                    if v.get("is_tradeoff") or v.get("constraint_ok") is False:
                        idea.resolution_status = "TRADEOFF"
                        idea.strongest_objection = v.get("note", "ARIZ 검토 미통과")
            if v.get("is_tradeoff"):
                ctx.warn(f"ARIZ 7.2: '{v.get('idea_title')}'는 모순 해소가 아니라 절충으로 판정됨")
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
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s5_track_f", label="Track F 진화 트렌드", stage=Stage.S5.value,
        agent_id="evolution_analyst", prompt_id="P_S5_TRACK_F", tier="T2",
        vars={"target_system": digest.target_system(st),
              "components": digest.components_digest(st),
              "resources": digest.resources_digest(st),
              "trends_block": K.trends_block()},
        default={},
    ) or {}
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"{a.get('trend_id')} {a.get('trend_name')}"
    st.solve.trend_apps += apps
    st.scratch["s_curve"] = {"stage": d.get("s_curve_stage", ""), "note": d.get("s_curve_note", ""),
                             "bottleneck": d.get("bottleneck", "")}
    _add_ideas(st, "F_TRENDS", apps, ref_key="ref")


def _track_g(ctx: RunContext) -> None:
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s5_track_g", label="Track G 기능지향탐색(FOS)", stage=Stage.S5.value,
        agent_id="cross_domain_scout", prompt_id="P_S5_TRACK_G", tier="T2",
        vars={"required_functions": _required_functions(st),
              "target_system": digest.target_system(st),
              "operating_env": st.domain.operating_env,
              "contradictions": digest.contradictions_digest(st)},
        default={},
    ) or {}
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"FOS/{a.get('leading_area','')}"
    st.solve.fos_apps += apps
    n0 = len(st.solve.raw_ideas)
    _add_ideas(st, "G_FOS", apps, ref_key="ref")
    for idea in st.solve.raw_ideas[n0:]:
        idea.novelty_class = "CROSS_DOMAIN"


def _track_h(ctx: RunContext) -> None:
    st = ctx.state
    d = agent.run_agent(
        ctx, node="s5_track_h", label="Track H 효과(Effects) 적용", stage=Stage.S5.value,
        agent_id="effects_specialist", prompt_id="P_S5_TRACK_H", tier="T2",
        vars={"required_functions": _required_functions(st),
              "target_system": digest.target_system(st),
              "operating_env": st.domain.operating_env,
              "effects_block": K.effects_block(limit=6, required_functions=_required_functions(st))},
        default={},
    ) or {}
    apps = d.get("applications") or []
    for a in apps:
        a["ref"] = f"효과/{a.get('effect_name','')}"
    st.solve.effect_apps += apps
    _add_ideas(st, "H_EFFECTS", apps, ref_key="ref")


TRACK_FUNCS = {
    "A_MATRIX": _track_a, "B_SEPARATION": _track_b, "C_STANDARDS": _track_c,
    "D_ARIZ": _track_d_ariz, "E_TRIMMING": _track_e, "F_TRENDS": _track_f,
    "G_FOS": _track_g, "H_EFFECTS": _track_h,
}


def s5_solve(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S5.value)
    tracks = domain.select_tracks(st, st.control.enabled_tracks)
    if st.definition.technical_contradictions and "A_MATRIX" not in tracks:
        tracks.append("A_MATRIX")
    if st.definition.physical_contradictions and "B_SEPARATION" not in tracks:
        tracks.append("B_SEPARATION")
    if domain.physical_allowed(st) and st.analysis.su_fields and "C_STANDARDS" not in tracks:
        tracks.append("C_STANDARDS")

    # Evidence planning consumes only pre-S5 facts; bounded track pool shares the call budget.
    st.scratch.setdefault("agent_cache", {})
    track_state = st.model_copy(deep=True)
    track_state.steps, track_state.cost, track_state.control = st.steps, st.cost, st.control
    track_state.scratch["agent_cache"] = st.scratch["agent_cache"]
    track_ctx = RunContext(track_state)
    track_ctx.lock, track_ctx.budget, track_ctx.call_slots = ctx.lock, ctx.budget, ctx.call_slots
    with ThreadPoolExecutor(max_workers=2) as pool:
        retrieval = pool.submit(_evidence, ctx)
        _run_tracks(track_ctx, tracks)
        retrieval.result()
    st.solve = track_state.solve
    if "s_curve" in track_state.scratch:
        st.scratch["s_curve"] = track_state.scratch["s_curve"]
    need_more = _merge(ctx)

    retries = st.control.retry_count.get("s5_solve", 0)
    if need_more and retries < int(cfg("solve.max_escalations", 0)):
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
    seq = [t for t in ["A_MATRIX", "B_SEPARATION", "C_STANDARDS", "D_ARIZ", "E_TRIMMING",
                       "F_TRENDS", "G_FOS", "H_EFFECTS"] if t in tracks]
    ctx.emit("tracks", tracks=seq)
    # Track outputs are isolated, then merged in catalog order. Sharing one mutable
    # idea list would let FOS relabel another track's ideas during parallel execution.
    from .schema import SolveBundle
    st.scratch.setdefault("agent_cache", {})
    with ctx.lock:
        branches = {t: st.model_copy(deep=True) for t in seq}
    def execute(t):
        fn = TRACK_FUNCS.get(t)
        if not fn:
            return None
        branch = branches[t]
        branch.solve = SolveBundle()
        branch.steps, branch.cost, branch.control = st.steps, st.cost, st.control
        branch.scratch["agent_cache"] = st.scratch["agent_cache"]
        child = RunContext(branch)
        child.lock, child.budget = ctx.lock, ctx.budget
        child.call_slots = ctx.call_slots
        try:
            fn(child)
            return t, branch
        except AbortRun:
            raise
        except Exception as exc:  # noqa: BLE001
            ctx.warn(f"트랙 {t} 실행 중 오류: {exc}")
            raise
    if not seq:
        return
    with ThreadPoolExecutor(max_workers=max(1, min(int(cfg("run.parallel_workers", 4)), len(seq)))) as pool:
        results = list(pool.map(execute, seq))
    for item in results:
        if not item:
            continue
        t, branch = item
        for key in ("matrix_lookups", "principle_apps", "separation_apps", "standard_apps", "trend_apps", "fos_apps", "effect_apps", "raw_ideas", "gaps"):
            getattr(st.solve, key).extend(getattr(branch.solve, key))
        if branch.solve.ariz:
            st.solve.ariz = branch.solve.ariz
        if "s_curve" in branch.scratch:
            st.scratch["s_curve"] = branch.scratch["s_curve"]
        if t not in st.solve.tracks_run:
            st.solve.tracks_run.append(t)


def _evidence(ctx: RunContext) -> None:
    from .evidence import discover
    discover(ctx, before_concepts=True)


def _merge(ctx: RunContext) -> bool:
    st = ctx.state
    if not st.solve.raw_ideas:
        ctx.warn("도출된 아이디어가 없다.")
        return True
    d = agent.run_agent(
        ctx, node="s5_merge", label="아이디어 통합·중복제거", stage=Stage.S5.value,
        agent_id="solution_curator", prompt_id="P_S5_MERGE", tier="T2", rubric_id="R5_MERGE",
        max_tokens=8000,
        vars={"all_ideas": digest.ideas_digest(st, limit=40),
              "redefinition_hints": st.solve.gaps,
              "causal_packet": digest.causal_packet(st),
              "evidence": digest.relevant_evidence(st),
              "key_problems": [k.model_dump() for k in st.definition.key_problems],
              "contradictions": digest.contradictions_digest(st),
              "min_ideas": cfg("solutions.min_raw_ideas", 12),
              "max_ideas": max(int(cfg("solutions.min_raw_ideas", 12)) + 8, 20)},
        default={},
    ) or {}

    merged = d.get("ideas") or []
    if "ideas" in d:
        by_id = {i.id: i for i in st.solve.raw_ideas}
        new_ideas: list[RawIdea] = []
        used_keep_ids = set()
        for m in merged:
            if not isinstance(m, dict):
                continue
            keep_ids = m.get("keep_ids") or []
            if not isinstance(keep_ids, list) or any(not isinstance(k, str) for k in keep_ids):
                continue
            keep_ids = list(dict.fromkeys(keep_ids))
            if any(k not in by_id for k in keep_ids) or used_keep_ids.intersection(keep_ids):
                continue
            keep = [by_id[k] for k in keep_ids]
            if not keep:
                continue
            used_keep_ids.update(keep_ids)
            base = keep[0]
            prior_details = []
            for idea in keep:
                prior_details.extend(idea.detail.get("source_details") or [dict(idea.detail, source_idea_id=idea.id)])
            status = m.get("resolution_status", "UNSUPPORTED")
            if status not in ("RESOLVED", "TRADEOFF", "UNSUPPORTED"):
                status = "UNSUPPORTED"
            if any(i.resolution_status == "TRADEOFF" for i in keep):
                status = "TRADEOFF"
            if status == "RESOLVED" and not m.get("resolution_argument"):
                status = "UNSUPPORTED"
            new_ideas.append(RawIdea(
                id=base.id if base else RawIdea().id,
                track=base.track,
                source_ref=" + ".join(dict.fromkeys(i.source_ref for i in keep if i.source_ref)),
                title=m.get("title") or (base.title if base else ""),
                idea=m.get("idea") or (base.idea if base else ""),
                uses_resources=list(dict.fromkeys(_text_list(m.get("uses_resources")) + [v for i in keep for v in i.uses_resources])),
                addresses=m.get("addresses") or list(dict.fromkeys(v for i in keep for v in i.addresses)),
                novelty_class=m.get("novelty_class") or (base.novelty_class if base else "NEW"),
                feasibility_hint=m.get("feasibility_hint") or base.feasibility_hint,
                detail={"source_details": prior_details},
                source_idea_ids=list(dict.fromkeys(k for i in keep for k in (i.source_idea_ids or [i.id]))),
                mechanism_key=m.get("mechanism_key") or base.mechanism_key or base.id,
                mechanism=m.get("mechanism") or base.mechanism,
                intervention_variable=m.get("intervention_variable") or base.intervention_variable,
                conditions=list(dict.fromkeys(_text_list(m.get("conditions")) + [v for i in keep for v in i.conditions])),
                strongest_objection=m.get("strongest_objection") or base.strongest_objection,
                validation_test=m.get("validation_test") or base.validation_test,
                hypothesis_ids=list(dict.fromkeys(_text_list(m.get("hypothesis_ids")) + [v for i in keep for v in i.hypothesis_ids])),
                resolution_status=status,
                resolution_argument=m.get("resolution_argument", ""),
            ))
        st.solve.raw_ideas = new_ideas
    st.solve.coverage_note = d.get("coverage_note", "")
    st.solve.gaps = list(dict.fromkeys(st.solve.gaps + _text_list(d.get("gaps"))))
    valid_ids = {t.id for t in st.definition.technical_contradictions} | {p.id for p in st.definition.physical_contradictions}
    for idea in st.solve.raw_ideas:
        idea.addresses = [i for i in idea.addresses if i in valid_ids]
        if not idea.addresses:
            idea.resolution_status = "UNSUPPORTED"
    covered = {cid for i in st.solve.raw_ideas if i.resolution_status == "RESOLVED" for cid in i.addresses}
    unmet = [kp.title for kp in st.definition.key_problems if not covered.intersection(kp.contradiction_ids)]
    st.solve.gaps.extend(f"미해결 핵심 문제: {title}" for title in unmet)
    need_more = bool(unmet) or bool(d.get("need_more"))
    ctx.emit("artifact", kind="IDEAS", data={"count": len(st.solve.raw_ideas),
                                             "tracks": st.solve.tracks_run,
                                             "need_more": need_more})
    return need_more


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

    payload = ctx.resume_payload()
    if payload:
        decisions = payload.get("decisions") or {}
        expected = {c.concept_id for c in st.constraint_checks if c.verdict == 'CONDITIONAL'}
        if set(decisions) != expected or any(v not in ('accept', 'drop') for v in decisions.values()):
            raise ValueError("보류된 모든 해결책의 유지·제외 판정이 필요합니다.")
        for cid, choice in decisions.items():
            chk = st.check_for(cid)
            if not chk:
                continue
            if choice == "accept":
                # User acceptance cannot turn missing evidence into technical compliance.
                chk.verdict = "CONDITIONAL"
                chk.requires_user_decision = False
            elif choice == "drop":
                concept = st.concept(cid)
                if concept:
                    st.scratch.setdefault('excluded_concepts', []).append({'idea': concept.title, 'reason': '제약 검토에서 사용자가 제외함'})
                st.concepts = [c for c in st.concepts if c.id != cid]
                st.constraint_checks = [c for c in st.constraint_checks if c.concept_id != cid]
        st.scratch['gate_decisions'] = {'decisions': dict(decisions), 'fingerprint': _gate_fingerprint(st)}
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

    if not st.constraints.items:
        st.constraint_checks = [ConstraintCheckResult(concept_id=c.id, verdict="PASS")
                                for c in st.concepts]
        return

    concepts = digest.concepts_for_gate(st)
    batch_size = max(1, min(int(cfg('constraints.max_concepts_per_call', 2)),
                           int(cfg('constraints.max_pairs_per_call', 24)) // max(1, len(st.constraints.items))))
    def gate_batch(start):
        batch = concepts[start:start+batch_size]
        d = agent.run_agent(
            ctx, node=f"s7_gate_{start // batch_size + 1}", label=f"제약 검토 {start+1}–{start+len(batch)}/{len(concepts)}", stage=Stage.S7.value,
            agent_id="gatekeeper", prompt_id="P_S7_GATEKEEPER", tier="T2",
            system_override="You are a strict compliance gatekeeper. Output JSON only. "
                            "Judge only constraint compliance, nothing else.",
            vars={"constraints_full": verify.constraints_full(st), "concepts_for_gate": batch}, default={}) or {}
        ids = {c['concept_id'] for c in batch}
        return [r for r in build_list(ConstraintCheckResult, d.get('results')) if r.concept_id in ids]

    with ThreadPoolExecutor(max_workers=max(1, int(cfg("run.parallel_workers", 4)))) as pool:
        raw_results = [r for batch in pool.map(gate_batch, range(0, len(concepts), batch_size)) for r in batch]

    results: list[ConstraintCheckResult] = []
    by_id = {c.id: c for c in st.concepts}
    for r in raw_results:
        if r.concept_id in by_id:
            results.append(r)
    for c in st.concepts:  # 판정 누락분은 CONDITIONAL 처리
        if not any(r.concept_id == c.id for r in results):
            results.append(ConstraintCheckResult(concept_id=c.id, verdict="CONDITIONAL",
                                                 mitigation="자동 판정 누락 — 사용자 확인 필요",
                                                 requires_user_decision=True))
    # 코드 기반 수치 재검증(보조)
    for r in results:
        c = by_id.get(r.concept_id)
        if not c:
            continue
        blob = " ".join([c.description, c.expected_effect, " ".join(c.changes_to_system)])
        for con in st.constraints.hard_items():
            msg = verify.numeric_violation(blob, con)
            if msg:
                r.verdict = "FAIL"
                if con.id not in r.violated_ids:
                    r.violated_ids.append(con.id)
                r.per_constraint.append({"constraint_id": con.id, "verdict": "FAIL",
                                         "reason": f"수치 자동검증: {msg}"})
    st.constraint_checks = results

    failed = [r for r in results if r.verdict == "FAIL"]
    cond = [r for r in results if r.verdict == "CONDITIONAL"]
    passed = [r for r in results if r.verdict == "PASS"]
    ctx.emit("artifact", kind="CONSTRAINT_GATE",
             data={"pass": len(passed), "conditional": len(cond), "fail": len(failed)})

    for r in failed:  # 제약 위반 개념은 폐기
        c = by_id.get(r.concept_id)
        if c:
            st.scratch.setdefault("excluded_concepts", []).append(
                {"idea": c.title, "reason": f"제약 위반: {', '.join(r.violated_ids) or '판정 FAIL'}"})
    st.concepts = [c for c in st.concepts if c.id not in {r.concept_id for r in failed}]
    st.constraint_checks = [r for r in results if r.verdict != "FAIL"]

    min_pass = int(cfg("constraints.min_passing_concepts", 5))
    if cond and (len(passed) < min_pass or any(r.requires_user_decision for r in cond)):
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


# ════════════════════════════════════════════════ S8
def s8_evaluate(ctx: RunContext) -> None:
    st = ctx.state
    ctx.set_stage(Stage.S8.value)
    if not st.concepts:
        ctx.warn("평가할 개념이 없다.")
        return

    reviewers = PF.build_personas(ctx)
    st.evaluation.reviewers = reviewers
    ctx.emit("personas", reviewers=[r.model_dump() for r in reviewers])

    blind = digest.concepts_blind(st)
    cblock = verify.constraints_block(st)
    concept_ids = {c.id for c in st.concepts}
    all_scores: list[ReviewerScore] = []

    def review(p):
        d = agent.run_agent(
            ctx, node="s8_review", label=f"평가: {p.role_name}", stage=Stage.S8.value,
            agent_id=f"persona::{p.persona_id}", prompt_id="P_S8_REVIEW", tier="T2",
            rubric_id="R8_REVIEW", checker=lambda x: verify.check_review(x, concept_ids),
            system_override="You are an experienced domain reviewer. Output JSON only. "
                            "You do not know how these ideas were generated.",
            vars={"industry": st.domain.industry, "seniority": p.seniority,
                  "role_name": p.role_name, "mandate": p.mandate, "bias_note": p.bias_note,
                  "dimensions": p.dimensions,
                  "restated_problem": st.intake.frame.restated_problem,
                  "target_system": digest.target_system(st),
                  "operating_env": st.domain.operating_env,
                  "constraints_block": cblock, "concepts_blind": blind,
                  "success_criteria": st.intake.frame.success_criteria,
                  "requirements": [{"improve": t.then_good, "preserve": t.but_bad} for t in st.definition.technical_contradictions]},
            default={},
        ) or {}
        out = []
        for rs in build_list(ReviewerScore, d.get("scores"), reviewer_role=p.role_name):
            if rs.concept_id not in concept_ids:
                continue
            if p.veto_power and rs.red_flags:
                rs.score = min(rs.score, 1.5)
            out.append(rs)
        return out

    workers = int(cfg("run.parallel_workers", 4))
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(reviewers)))) as pool:
        for res in pool.map(review, reviewers):
            all_scores += res

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


def _rank(ctx: RunContext) -> None:
    st = ctx.state
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
              "min_solutions": cfg("solutions.min_solutions", 5),
              "max_solutions": cfg("solutions.max_solutions", 10)},
        default={},
    ) or {}

    order = {r.get("concept_id"): int(r.get("rank", 99)) for r in (d.get("ranking") or [])}
    if not order:
        ranked = sorted(st.evaluation.evaluations, key=lambda e: -e.total_score)
        order = {e.concept_id: i + 1 for i, e in enumerate(ranked)}
    for e in st.evaluation.evaluations:
        e.rank = order.get(e.concept_id, 99)
    st.evaluation.evaluations.sort(key=lambda e: e.rank)
    st.evaluation.ranking_note = d.get("ranking_note", "")
    st.evaluation.portfolio_note = d.get("portfolio_note", "")
    st.evaluation.roadmap = d.get("roadmap") or []

    keep = int(cfg("solutions.max_solutions", 10))
    st.evaluation.evaluations = st.evaluation.evaluations[:keep]
    keep_ids = {e.concept_id for e in st.evaluation.evaluations}
    st.concepts = [c for c in st.concepts if c.id in keep_ids]
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
        add(f"분리원리 {a.get('separation_type', '')}", a.get("interpretation", ""))
    for a in st.solve.standard_apps:
        add(f"표준해 {a.get('standard_id', '')}", a.get("interpretation", ""))
    return out


def s8_references(ctx: RunContext) -> None:
    from .evidence import attach
    ctx.set_stage("S8_REFERENCES")
    attach(ctx)


def s9_report(ctx: RunContext) -> None:
    from . import render  # 지연 임포트(템플릿 로딩 비용 회피)

    st = ctx.state
    ctx.set_stage(Stage.S9.value)
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
