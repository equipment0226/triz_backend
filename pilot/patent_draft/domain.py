"""Versioned, strict patent contracts, independent of the legacy state serializer."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

PROFILE = 'patent_draft.v0.2'
SCOPE = 'BETA_STUDIO_EXCLUDED_V1'
ROLES = ('TECHNICAL_CONTENT', 'PATENT_CONTENT', 'GLOBAL_FINAL')


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def ident(prefix: str) -> str:
    return prefix + '-' + uuid.uuid4().hex


class PatentError(Exception):
    def __init__(self, code: str, detail: str, status: int = 409, retryable: bool = False):
        super().__init__(detail)
        self.code, self.detail, self.status, self.retryable = code, detail, status, retryable


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Bootstrap(Strict):
    source_run_id: str = Field(min_length=1, max_length=160)
    concept_id: str = Field(min_length=1, max_length=160)
    expected_source_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    purpose: str = Field(min_length=1, max_length=2000)
    jurisdiction: Literal['KR'] = 'KR'
    profile: Literal['KR_GENERAL', 'KR_SOFTWARE_AI', 'KR_MATERIAL_PROCESS', 'KR_SPECIAL_TRIAGE'] = 'KR_GENERAL'


class Mutation(Strict):
    expected_revision: int = Field(ge=0)
    expected_epoch: int = Field(ge=1)
    input_snapshot_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Feature(Strict):
    id: str
    name: str = Field(min_length=1)
    description: str
    provenance: Literal['SOURCE', 'USER_CONFIRMED', 'DERIVED_PROPOSAL'] = 'DERIVED_PROPOSAL'
    source_ids: list[str] = Field(default_factory=list)


class Effect(Strict):
    id: str
    description: str
    feature_ids: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_status: Literal['HYPOTHESIS', 'USER_REPORTED', 'MEASURED'] = 'HYPOTHESIS'


class Invention(Strict):
    title: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    features: list[Feature] = Field(min_length=1)
    effects: list[Effect] = Field(default_factory=list)
    relations: list[dict[str, str]] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def references(self):
        ids = [f.id for f in self.features]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate feature IDs')
        if any(set(e.feature_ids) - set(ids) for e in self.effects):
            raise ValueError('effect references missing feature')
        return self


class Claim(Strict):
    number: int = Field(ge=1)
    text: str = Field(min_length=1)
    depends_on: list[int] = Field(default_factory=list)
    multiple_dependency_mode: Literal['ALTERNATIVE', 'CUMULATIVE'] | None = None
    feature_ids: list[str] = Field(min_length=1)
    support_sections: list[str] = Field(default_factory=list)


class ClaimTree(Strict):
    claims: list[Claim] = Field(min_length=1)

    @model_validator(mode='after')
    def citations(self):
        numbers = [c.number for c in self.claims]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError('claims must be consecutively numbered')
        for c in self.claims:
            if any(n >= c.number or n not in numbers for n in c.depends_on):
                raise ValueError('claim dependency must refer to an earlier claim')
        return self


class Section(Strict):
    id: str
    heading: str
    text: str
    feature_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    omission_reason: str | None = None


class DocumentAST(Strict):
    title: str
    sections: list[Section] = Field(min_length=1)
    abstract: str = Field(min_length=1)
    applicant: dict[str, str] = Field(default_factory=dict)
    inventors: list[dict[str, str]] = Field(default_factory=list)


class Drawing(Strict):
    number: int = Field(ge=1)
    caption: str
    nodes: list[dict[str, str]] = Field(min_length=1, max_length=40)
    edges: list[dict[str, str]] = Field(default_factory=list, max_length=100)
    kind: Literal['CONCEPT', 'FILING_CANDIDATE'] = 'CONCEPT'

    @model_validator(mode='after')
    def graph(self):
        ids=[n.get('id') for n in self.nodes]
        if any(not n.get('id') or not n.get('label') or not n.get('feature_id') for n in self.nodes) or len(set(ids))!=len(ids):
            raise ValueError('drawing nodes need unique marks, names and existing feature references')
        if any(e.get('from') not in ids or e.get('to') not in ids for e in self.edges):
            raise ValueError('drawing edge references an absent node')
        return self


class DrawingSpec(Strict):
    drawings: list[Drawing] = Field(default_factory=list, max_length=20)
    not_required_reason: str | None = None
    sample_prompt_en: str | None = Field(default=None, max_length=2500)

    @model_validator(mode='after')
    def numbers(self):
        values=[d.number for d in self.drawings]
        if len(values)!=len(set(values)):raise ValueError('duplicate drawing number')
        return self


class Facts(Strict):
    drawings_required: StrictBool | None = None
    agent: StrictBool | None = None
    priority: StrictBool | None = None
    disclosure_exception: StrictBool | None = None
    sequence: StrictBool | None = None
    deposit: StrictBool | None = None
    assignment: StrictBool | None = None
    software_or_ai: StrictBool | None = None
    materials_or_special_domain: StrictBool | None = None
    business_review_requested: StrictBool | None = None
    applicant_name: str = Field(default='',max_length=500)
    inventor_names: str = Field(default='',max_length=2000)
    contribution_and_rights: str = Field(default='',max_length=8000)


class SourceSpan(Strict):
    artifact_id: str = Field(min_length=1, max_length=160)
    pointer: str = Field(min_length=1, max_length=1000)
    excerpt: str = Field(min_length=8, max_length=3000)


class Finding(Strict):
    rule_id: str
    outcome: Literal['PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE']
    severity: Literal['BLOCKER', 'MAJOR', 'MINOR', 'ADVISORY', 'INFO']
    explanation: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    affected_artifacts: list[str] = Field(default_factory=list)
    source_spans: list[SourceSpan] = Field(default_factory=list, max_length=20)


class TargetCheck(Strict):
    target_id: str
    content_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    outcome: Literal['PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE']
    explanation: str = Field(min_length=1)


class Review(Strict):
    role: Literal['TECHNICAL_CONTENT', 'PATENT_CONTENT', 'GLOBAL_FINAL']
    input_snapshot_id: str
    covered_artifact_ids: list[str]
    findings: list[Finding]
    summary: str
    target_checks: list[TargetCheck]


class ReadRequest(Strict):
    case_id: str
    snapshot_id: str
    requested_artifact_ids: list[str] = Field(min_length=1, max_length=100)
    purpose: str = Field(min_length=1, max_length=2000)


class Question(Strict):
    id: str = Field(min_length=1, max_length=160)
    question: str = Field(min_length=1)
    reason: str
    affected_fields: list[Literal['invention', 'facts', 'search_plan', 'sources', 'claim_chart',
                                'claims', 'specification', 'drawings', 'economics']] = Field(min_length=1)
    blocking: bool = True


class Questions(Strict):
    questions: list[Question] = Field(max_length=20)

    @model_validator(mode='after')
    def unique_questions(self):
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)) or any(i.startswith('APPLICATION_') for i in ids):
            raise ValueError('question IDs must be unique and cannot replace mandatory intake')
        return self


class SearchPlan(Strict):
    queries: list[str] = Field(min_length=1, max_length=4)
    feature_ids: list[str]
    limitations: list[str]


class ChartEntry(Strict):
    feature_id: str
    source_id: str
    source_passage: str
    assessment: Literal['DISCLOSED', 'NOT_FOUND', 'UNKNOWN']
    explanation: str


class ClaimChart(Strict):
    entries: list[ChartEntry]
    coverage_gaps: list[str]


class Economics(Strict):
    protected_product: str
    market_context: str
    copying_risk: str
    detectability: str
    limitations: list[str]


class PatchProposal(Strict):
    target_type: Literal['invention', 'facts', 'claims', 'specification', 'drawings']
    before_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    replacement: dict[str, Any]
    change_kind: Literal['WORDING', 'TECHNICAL', 'CLAIM_SCOPE']
    change_reason: str = Field(min_length=1, max_length=2000)
    issue_ids: list[str] = Field(default_factory=list)


class Reconciliation(Strict):
    proposals: list[PatchProposal] = Field(max_length=5)
    questions: list[Question] = Field(max_length=10)
    unresolved_issue_ids: list[str]


class TaskTicket(Strict):
    task_id: str
    case_id: str
    epoch: int
    input_snapshot_id: str
    input_hash: str
    rule_pack_version: str
    model_profile: Literal['patent_draft.v0.2']
    policy_version: str
    scope_policy_version: Literal['BETA_STUDIO_EXCLUDED_V1']
    read_version_ids: list[str]
    idempotency_key: str
    operation_payload_ref: str
    tool_name: str
    tier: Literal['CODE', 'T1', 'T2', 'T3']
    review_role: str | None = None
    budget_reservation_id: str | None = None
