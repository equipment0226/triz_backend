"""파이프라인 전 구간에서 사용하는 도메인 스키마 (MASTER_SPEC §4의 PoC 구현판)."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel as _PydanticBase, Field, field_validator, model_validator


def _as_text(v: Any) -> str:
    """LLM이 문자열 대신 객체/배열을 준 경우에도 읽을 수 있는 한 줄로 만든다."""
    if isinstance(v, dict):
        return " · ".join(f"{k}: {_as_text(x)}" for k, x in v.items() if x not in (None, "", [], {}))
    if isinstance(v, (list, tuple)):
        return ", ".join(_as_text(x) for x in v)
    return "" if v is None else str(v)


class BaseModel(_PydanticBase):
    """모든 스키마의 공통 기반.

    LLM이 str/list[str] 자리에 객체를 넣어도 상태를 저장·복원할 수 있어야 한다.
    한 번 어긋난 값이 들어가면 이후 load_state가 영구히 실패하므로 여기서 눕힌다.
    """

    @model_validator(mode="before")
    @classmethod
    def _flatten_text_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            if name not in data:
                continue
            value = data[name]
            ann = str(field.annotation)
            if ann in ("<class 'str'>", "str") and isinstance(value, (dict, list, tuple)):
                data[name] = _as_text(value)
            elif ann in ("list[str]", "typing.List[str]") and isinstance(value, (list, tuple)):
                if any(isinstance(x, (dict, list, tuple)) for x in value):
                    data[name] = [_as_text(x) for x in value]
        return data


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ────────────────────────────────────────────── 열거형
class Stage(str, Enum):
    S0 = "S0_BOOTSTRAP"
    S1 = "S1_INTAKE"
    S2 = "S2_CONFIRM"
    S3 = "S3_ANALYZE"
    S4 = "S4_DEFINE"
    S5 = "S5_SOLVE"
    S6 = "S6_CONCEPT"
    S7 = "S7_CONSTRAINT"
    S8 = "S8_EVALUATE"
    S9 = "S9_REPORT"
    S10 = "S10_FEEDBACK"


class RunMode(str, Enum):
    LITE = "LITE"
    FULL = "FULL"
    DEEP = "DEEP"


class Track(str, Enum):
    A_MATRIX = "A_MATRIX"
    B_SEPARATION = "B_SEPARATION"
    C_STANDARDS = "C_STANDARDS"
    D_ARIZ = "D_ARIZ"
    E_TRIMMING = "E_TRIMMING"
    F_TRENDS = "F_TRENDS"
    G_FOS = "G_FOS"
    H_EFFECTS = "H_EFFECTS"


# ────────────────────────────────────────────── 공통
class Provenance(BaseModel):
    stage: str = ""
    node: str = ""
    agent_id: str = ""
    prompt_id: str = ""
    tier: str = ""
    model: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    revision: int = 0


# ────────────────────────────────────────────── S1
class DomainContext(BaseModel):
    problem_type: Literal["PHYSICAL_TECHNICAL", "INFORMATION_SOFTWARE", "ORGANIZATIONAL_BUSINESS", "MIXED", "UNKNOWN"] = "UNKNOWN"
    difficulty: Literal["routine", "advanced", "frontier"] = "advanced"
    physical_scope: str = ""
    industry: str = ""
    sub_domain: str = ""
    job_family: str = ""
    legacy_note: str = ""
    target_system: str = ""
    super_system: str = ""
    sub_systems: list[str] = []
    operating_env: str = ""
    domain_tags: list[str] = []
    is_engineering: bool = True


class Constraint(BaseModel):
    id: str = Field(default_factory=lambda: new_id("CON"))
    kind: Literal["MUST_HAVE", "MUST_NOT_HAVE", "NUMERIC", "PREFERENCE"] = "MUST_HAVE"
    category: Literal[
        "USER_STATED", "ENVIRONMENT", "MATERIAL_COMPAT", "PHYSICS", "REGULATION",
        "OPERATION", "INTERFACE", "ECONOMIC",
    ] = "USER_STATED"
    statement: str = ""
    parameter: str = ""
    operator: Literal["<=", ">=", "==", "!=", "in", "not_in", "none"] = "none"
    value: str = ""
    unit: str = ""
    zone: str = ""                 # 적용 영역(예: "찤4버 내부"). 비어 있으면 시스템 전체
    source: Literal["USER", "INFERRED", "REGULATION", "AGENT", "DOMAIN"] = "USER"
    confidence: float = 1.0
    hard: bool = True
    rationale: str = ""
    violation_example: str = ""    # 이 제약을 위반하는 전형적 오답


class ConstraintSet(BaseModel):
    items: list[Constraint] = []
    open_questions: list[str] = []

    def hard_items(self) -> list[Constraint]:
        return [c for c in self.items if c.hard]


class Attachment(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ATT"))
    filename: str = ""
    mime: str = ""
    kind: str = "OTHER"
    extracted_text: str = ""
    extracted_facts: list[str] = []
    storage_path: str = ""
    sha256: str = ""


class ProblemFrame(BaseModel):
    raw_query: str = ""
    restated_problem: str = ""
    symptom: str = ""
    when_where: str = ""
    current_workaround: str = ""
    prior_attempts: list[str] = []
    success_criteria: list[str] = []
    missing_info: list[str] = []
    confidence: float = 0.0


class ClarifyTurn(BaseModel):
    question: str = ""
    why_needed: str = ""
    proposed_answers: list[str] = []
    user_answer: str = ""
    answered: bool = False


class IntakeArtifact(BaseModel):
    frame: ProblemFrame = ProblemFrame()
    attachments: list[Attachment] = []
    clarify_turns: list[ClarifyTurn] = []
    candidate_characteristics: list[str] = []
    candidate_conflicts: list[str] = []


# ────────────────────────────────────────────── S2
class SystemCandidate(BaseModel):
    id: str = Field(default_factory=lambda: new_id("SYS"))
    name: str = ""
    scope: Literal["SUPER", "TARGET", "SUB"] = "TARGET"
    description: str = ""
    diagram_mermaid: str = ""
    similarity_reason: str = ""
    super_system: str = ""
    operative_zone: str = ""
    operative_time: str = ""


class ConfirmArtifact(BaseModel):
    candidates: list[SystemCandidate] = []
    chosen_candidate_id: str = ""
    problem_zone: str = ""
    operative_zone: str = ""
    operative_time: str = ""
    confirm_question: str = ""
    user_confirmed: bool = False
    user_amendments: list[str] = []

    def chosen(self) -> Optional[SystemCandidate]:
        for c in self.candidates:
            if c.id == self.chosen_candidate_id:
                return c
        return self.candidates[0] if self.candidates else None


# ────────────────────────────────────────────── S3
class NineWindows(BaseModel):
    cells: dict[str, str] = {}
    insights: list[str] = []


class Component(BaseModel):
    name: str = ""
    level: Literal["SUPER", "TARGET", "SUB", "ENVIRONMENT", "PRODUCT"] = "TARGET"
    role: str = ""
    notes: str = ""


class FunctionEdge(BaseModel):
    subject: str = ""
    action: str = ""
    object: str = ""
    kind: Literal["USEFUL", "HARMFUL"] = "USEFUL"
    level: Literal["INSUFFICIENT", "NORMAL", "EXCESSIVE"] = "NORMAL"
    parameter_affected: str = ""
    rank: Literal["BASIC", "AUXILIARY", "CORRECTIVE"] = "AUXILIARY"
    cost_hint: Literal["LOW", "MID", "HIGH", "UNKNOWN"] = "UNKNOWN"


class InteractionCell(BaseModel):
    a: str = ""
    b: str = ""
    sign: Literal["+", "-", "0", "+-"] = "0"
    note: str = ""


class InteractionMatrix(BaseModel):
    components: list[str] = []
    cells: list[InteractionCell] = []


class SuFieldModel(BaseModel):
    id: str = Field(default_factory=lambda: new_id("SU"))
    label: str = ""
    s1: str = ""
    s2: str = ""
    s3: str = ""
    field: str = ""
    completeness: Literal["COMPLETE", "INCOMPLETE", "MISSING_S2", "MISSING_F"] = "COMPLETE"
    effect: Literal[
        "USEFUL_SUFFICIENT", "USEFUL_INSUFFICIENT", "HARMFUL", "EXCESSIVE", "MEASUREMENT"
    ] = "USEFUL_INSUFFICIENT"
    diagram_mermaid: str = ""
    standard_class_hint: list[str] = []


class ResourceItem(BaseModel):
    category: Literal[
        "SUBSTANCE", "FIELD", "SPACE", "TIME", "INFORMATION", "FUNCTIONAL", "SYSTEM_LEVEL"
    ] = "SUBSTANCE"
    name: str = ""
    where: Literal["IN_SYSTEM", "IN_SUPERSYSTEM", "IN_ENVIRONMENT", "WASTE", "DERIVED"] = "IN_SYSTEM"
    availability: Literal["FREE", "LOW_COST", "COSTLY"] = "FREE"
    quantity_note: str = ""
    usable_for: list[str] = []
    blocked_by_constraint: bool = False


class CauseNode(BaseModel):
    hypothesis_ids: list[str] = []
    evidence_status: Literal["OBSERVED", "HYPOTHESIS", "DERIVED"] = "HYPOTHESIS"
    evidence_refs: list[str] = []
    falsification_test: str = ""
    id: str = ""
    text: str = ""
    node_type: Literal["TARGET_DISADVANTAGE", "INTERMEDIATE", "ROOT_CAUSE", "KEY_DISADVANTAGE"] = "INTERMEDIATE"
    parents: list[str] = []
    logic: Literal["AND", "OR", "NONE"] = "NONE"
    is_contradiction_seed: bool = False
    comment: str = ""


class CauseEffectChain(BaseModel):
    nodes: list[CauseNode] = []
    mermaid: str = ""


class AnalysisBundle(BaseModel):
    nine_windows: Optional[NineWindows] = None
    components: list[Component] = []
    function_edges: list[FunctionEdge] = []
    function_mermaid: str = ""
    interaction_matrix: Optional[InteractionMatrix] = None
    su_fields: list[SuFieldModel] = []
    resources: list[ResourceItem] = []
    ceca: Optional[CauseEffectChain] = None
    consistency_issues: list[str] = []


# ────────────────────────────────────────────── S4
class IFR(BaseModel):
    statement: str = ""
    x_element: str = ""
    without: list[str] = []
    ideality_note: str = ""
    intensified: str = ""
    constraint_conflicts: list[str] = []


class TechnicalContradiction(BaseModel):
    cause_node_ids: list[str] = []
    hypothesis_ids: list[str] = []
    coupling_mechanism: str = ""
    id: str = Field(default_factory=lambda: new_id("TC"))
    label: str = ""
    if_action: str = ""
    then_good: str = ""
    but_bad: str = ""
    improving_param_id: int = 0
    worsening_param_id: int = 0
    param_scheme: Literal["ENG_39", "BIZ_31"] = "ENG_39"
    severity: int = 3
    rationale: str = ""


class PhysicalContradiction(BaseModel):
    id: str = Field(default_factory=lambda: new_id("PC"))
    label: str = ""
    element: str = ""
    parameter: str = ""
    state_a: str = ""
    reason_a: str = ""
    state_b: str = ""
    reason_b: str = ""
    scale: Literal["MACRO", "MICRO"] = "MACRO"
    derived_from_tc_id: str = ""
    separation_candidates: list[str] = []


class TrimmingItem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("TR"))
    target_component: str = ""
    rule: Literal["A", "B", "C", "D"] = "C"
    replaced_function: str = ""
    replacement_carrier: str = ""
    feasibility: Literal["HIGH", "MID", "LOW"] = "MID"
    risk_note: str = ""


class KeyProblem(BaseModel):
    id: str = Field(default_factory=lambda: new_id("KP"))
    title: str = ""
    contradiction_ids: list[str] = []
    why_key: str = ""
    impact: int = 3
    tractability: int = 3
    priority_score: float = 0.0


class DefinitionBundle(BaseModel):
    ifr: Optional[IFR] = None
    mini_problem: str = ""
    technical_contradictions: list[TechnicalContradiction] = []
    physical_contradictions: list[PhysicalContradiction] = []
    trimming: list[TrimmingItem] = []
    key_problems: list[KeyProblem] = []
    dropped: list[dict] = []


# ────────────────────────────────────────────── S5
class MatrixLookup(BaseModel):
    source_tc_id: str = ""
    improving_param_id: int = 0
    worsening_param_id: int = 0
    principle_ids: list[int] = []
    source: Literal["MATRIX", "LLM_FALLBACK"] = "MATRIX"
    note: str = ""


class RawIdea(BaseModel):
    source_idea_ids: list[str] = []
    mechanism_key: str = ""
    mechanism: str = ""
    intervention_variable: str = ""
    conditions: list[str] = []
    strongest_objection: str = ""
    validation_test: str = ""
    hypothesis_ids: list[str] = []
    resolution_status: Literal["RESOLVED", "TRADEOFF", "UNSUPPORTED"] = "UNSUPPORTED"
    resolution_argument: str = ""
    id: str = Field(default_factory=lambda: new_id("IDEA"))
    track: str = ""
    source_ref: str = ""
    title: str = ""
    idea: str = ""
    uses_resources: list[str] = []
    addresses: list[str] = []
    novelty_class: Literal["SAME_DOMAIN", "CROSS_DOMAIN", "NEW"] = "NEW"
    feasibility_hint: Literal["HIGH", "MID", "LOW"] = "MID"
    detail: dict[str, Any] = {}


class ARIZStep(BaseModel):
    step_code: str = ""
    step_title: str = ""
    output: str = ""
    status: Literal["DONE", "SKIPPED", "BLOCKED"] = "DONE"
    table_columns: list[str] = []
    table_rows: list[list[str]] = []


class ARIZRun(BaseModel):
    verdicts: list[dict[str, Any]] = []
    steps: list[ARIZStep] = []
    conflict_pair: str = ""
    operative_zone: str = ""
    operative_time: str = ""
    sfr_inventory: list[str] = []
    ifr1: str = ""
    ifr2: str = ""
    physical_contradiction_macro: str = ""
    physical_contradiction_micro: str = ""
    slp_model: str = ""
    solution_directions: list[str] = []
    final_ideas: list[str] = []
    unresolved_reason: str = ""


class SolveBundle(BaseModel):
    matrix_lookups: list[MatrixLookup] = []
    principle_apps: list[dict] = []
    separation_apps: list[dict] = []
    standard_apps: list[dict] = []
    trend_apps: list[dict] = []
    fos_apps: list[dict] = []
    effect_apps: list[dict] = []
    ariz: Optional[ARIZRun] = None
    raw_ideas: list[RawIdea] = []
    coverage_note: str = ""
    gaps: list[str] = []
    tracks_run: list[str] = []


class EvidenceCard(BaseModel):
    id: str = Field(default_factory=lambda: new_id("EV"))
    claim: str = ""
    source_type: Literal[
        "PATENT", "PAPER", "STANDARD", "VENDOR", "ARTICLE", "MODEL_KNOWLEDGE", "INTERNAL_FEEDBACK"
    ] = "MODEL_KNOWLEDGE"
    title: str = ""
    identifier: str = ""
    url: str = ""
    year: str = ""
    snippet: str = ""
    relevance: float = 0.0
    reliability: Literal["HIGH", "MID", "LOW"] = "MID"
    verified: bool = False
    provider: str = ""
    evidence_scope: str = "metadata"
    idea_ids: list[str] = []


# ────────────────────────────────────────────── S6~S8
class ConceptSpec(BaseModel):
    source_idea_ids: list[str] = []
    mechanism_key: str = ""
    intervention_variable: str = ""
    resolution_argument: str = ""
    hypothesis_ids: list[str] = []
    prior_case_ids: list[str] = []
    quality_status: Literal["UNVERIFIED", "PASS", "REVISE", "REJECT"] = "UNVERIFIED"
    quality_issues: list[str] = []
    id: str = Field(default_factory=lambda: new_id("CPT"))
    title: str = ""
    one_liner: str = ""
    description: str = ""
    working_principle: str = ""
    changes_to_system: list[str] = []
    required_resources: list[str] = []
    triz_origin: list[dict] = []
    addresses_contradictions: list[str] = []
    novelty_class: Literal["SAME_DOMAIN", "CROSS_DOMAIN", "NEW"] = "NEW"
    evidence_ids: list[str] = []
    expected_effect: str = ""
    assumptions: list[str] = []
    open_risks: list[str] = []
    diagram_mermaid: str = ""
    maturity: Literal["CONCEPT", "PROTOTYPE_KNOWN", "PROVEN_ELSEWHERE"] = "CONCEPT"
    change_scale: Literal["PARAMETER", "PARTIAL", "REDESIGN"] = "PARTIAL"
    validation_plan: list[dict[str, Any]] = []
    transfer_conditions: list[str] = []


class ConstraintCheckResult(BaseModel):
    concept_id: str = ""
    per_constraint: list[dict] = []
    verdict: Literal["PASS", "FAIL", "CONDITIONAL"] = "PASS"
    violated_ids: list[str] = []
    mitigation: str = ""
    requires_user_decision: bool = False


class Persona(BaseModel):
    persona_id: str = Field(default_factory=lambda: new_id("PER"))
    role_name: str = ""
    seniority: str = "15년 경력"
    mandate: str = ""
    dimensions: list[str] = []
    bias_note: str = ""
    veto_power: bool = False


class ReviewerScore(BaseModel):
    concept_id: str = ""
    reviewer_role: str = ""
    dimension: str = ""
    score: float = 3.0
    confidence: float = 0.7
    rationale: str = ""
    red_flags: list[str] = []
    improvement_suggestion: str = ""


class ConceptEvaluation(BaseModel):
    concept_id: str = ""
    scores: list[ReviewerScore] = []
    aggregate: dict[str, float] = {}
    total_score: float = 0.0
    risk_level: Literal["LOW", "MID", "HIGH"] = "MID"
    return_level: Literal["LOW", "MID", "HIGH"] = "MID"
    quadrant: Literal["QUICK_WIN", "BIG_BET", "FILL_IN", "AVOID"] = "FILL_IN"
    rank: int = 0
    dissent: list[str] = []
    feedback_weight_applied: float = 1.0


class MeetingQuestion(BaseModel):
    id: str
    round_number: int
    from_role_id: str
    to_role_id: str
    concept_id: str
    question: str
    reply_to_question_id: str = ""


class MeetingAnswer(BaseModel):
    question_id: str
    round_number: int
    from_role_id: str
    to_role_id: str
    concept_id: str
    answer: str
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class MeetingSummary(BaseModel):
    concept_id: str
    peer_role_ids: list[str]
    question_ids: list[str]
    summary: str
    assessment_change: str
    unresolved_issues: list[str] = Field(default_factory=list)


class MeetingFinalReview(BaseModel):
    reviewer_id: str
    reviewer_role: str
    scores: list[ReviewerScore]
    communication_summary: list[MeetingSummary]
    retained_concerns: list[str] = Field(default_factory=list)
    concept_comments: dict[str, str] = Field(default_factory=dict)


class EvaluationMeeting(BaseModel):
    input_hash: str = ""
    context_hash: str = ""
    status: Literal["NOT_STARTED", "RUNNING", "COMPLETED"] = "NOT_STARTED"
    rounds: int = 2
    initial_reviews: dict[str, list[ReviewerScore]] = Field(default_factory=dict)
    questions: list[MeetingQuestion] = Field(default_factory=list)
    answers: list[MeetingAnswer] = Field(default_factory=list)
    final_reviews: list[MeetingFinalReview] = Field(default_factory=list)
    completed_calls: dict[str, dict[str, Any]] = Field(default_factory=dict)
    completed_call_inputs: dict[str, str] = Field(default_factory=dict)


class EvaluationBundle(BaseModel):
    reviewers: list[Persona] = []
    evaluations: list[ConceptEvaluation] = []
    meeting: EvaluationMeeting = Field(default_factory=EvaluationMeeting)
    ranking_note: str = ""
    portfolio_note: str = ""
    roadmap: list[dict] = []


class ReportArtifact(BaseModel):
    @field_validator('narrative', mode='before')
    @classmethod
    def _normalize_narrative_values(cls, value):
        # Models sometimes add a list (e.g. next_steps) or return a structured
        # paragraph. Preserve its contents without breaking report persistence.
        if isinstance(value, dict):
            return {key: _as_text(content) for key, content in value.items()}
        return value

    markdown: str = ""
    template_id: str = "report_full"
    narrative: dict[str, str] = {}
    word_count: int = 0


class SolutionFeedback(BaseModel):
    concept_id: str = ""
    rating: int = 3
    adopted: Optional[bool] = None
    comment: str = ""
    reason_tags: list[str] = []


class FeedbackArtifact(BaseModel):
    distilled: dict[str, Any] = {}
    overall_rating: int = 0
    solution_feedback: list[SolutionFeedback] = []
    missing_perspective: str = ""
    would_reuse: Optional[bool] = None


# ────────────────────────────────────────────── 실행 제어
class StepRecord(BaseModel):
    step_id: str = Field(default_factory=lambda: new_id("STP"))
    seq: int = 0
    stage: str = ""
    node: str = ""
    label: str = ""
    agent_id: str = ""
    prompt_id: str = ""
    tier: str = ""
    model: str = ""
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    verify_attempts: int = 0
    verdicts: list[dict] = []
    escalated: bool = False
    human_intervened: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    status: Literal["RUNNING", "OK", "WARN", "FAILED", "SKIPPED", "WAITING_HUMAN"] = "RUNNING"
    error: str = ""
    output_json: dict[str, Any] = {}
    input_slice: dict[str, Any] = {}


class CostLedger(BaseModel):
    request_count: int = 0
    total_usd: float = 0.0
    by_tier: dict[str, float] = {}
    by_stage: dict[str, float] = {}
    tokens_in: int = 0
    tokens_out: int = 0
    budget_usd: float = 3.0
    over_budget: bool = False


class ControlBlock(BaseModel):
    mode: RunMode = RunMode.FULL
    lang: str = "ko"
    current_stage: str = Stage.S0.value
    stage_index: int = 0
    retry_count: dict[str, int] = {}
    enabled_tracks: list[str] = []
    clarify_rounds: int = 0
    warnings: list[str] = []
    errors: list[str] = []
    injected_agents: dict[str, list[dict]] = {}


class HumanRequest(BaseModel):
    interrupt_id: str = Field(default_factory=lambda: new_id("INT"))
    kind: Literal["CLARIFY", "CONFIRM", "DECIDE", "FEEDBACK"] = "CLARIFY"
    stage: str = ""
    title: str = ""
    payload: dict[str, Any] = {}


class GlobalState(BaseModel):
    run_id: str
    user_id: str = "local"
    created_at: datetime = Field(default_factory=datetime.now)
    raw_query: str = ""
    status: Literal["CREATED", "QUEUED", "RUNNING", "WAITING_HUMAN", "COMPLETED", "FAILED", "INTERRUPTED"] = "CREATED"

    control: ControlBlock = ControlBlock()
    domain: DomainContext = DomainContext()
    constraints: ConstraintSet = ConstraintSet()
    intake: IntakeArtifact = IntakeArtifact()
    confirm: ConfirmArtifact = ConfirmArtifact()
    analysis: AnalysisBundle = AnalysisBundle()
    definition: DefinitionBundle = DefinitionBundle()
    solve: SolveBundle = SolveBundle()
    evidence: list[EvidenceCard] = []
    concepts: list[ConceptSpec] = []
    constraint_checks: list[ConstraintCheckResult] = []
    evaluation: EvaluationBundle = EvaluationBundle()
    report: Optional[ReportArtifact] = None
    feedback: Optional[FeedbackArtifact] = None

    steps: list[StepRecord] = []
    cost: CostLedger = CostLedger()
    pending: Optional[HumanRequest] = None
    scratch: dict[str, Any] = {}

    # ---- 편의 접근자
    def concept(self, cid: str) -> Optional[ConceptSpec]:
        return next((c for c in self.concepts if c.id == cid), None)

    def evidences(self, ids: list[str]) -> list[EvidenceCard]:
        return [e for e in self.evidence if e.id in ids]

    def check_for(self, cid: str) -> Optional[ConstraintCheckResult]:
        return next((c for c in self.constraint_checks if c.concept_id == cid), None)
