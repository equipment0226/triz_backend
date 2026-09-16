"""Strict contracts at the decision, review and rule execution boundaries."""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ACTIONS = ('GENERATE_BASELINE', 'CHALLENGE_MEANS', 'CHECK_APPLICABILITY',
           'SOLVE_SUBPROBLEM', 'REPAIR_CANDIDATE', 'CO_DESIGN', 'FETCH_EVIDENCE',
           'RUN_TEST', 'ASK_HUMAN', 'PROPOSE_RULE', 'FINALIZE', 'DEFER')
GATES = (
    ('G1', '문제 정의', ('s0_bootstrap', 's0_research', 's1_intake', 's2_confirm')),
    ('G2', '문제 분석', ('s3_analyze', 's4_define')),
    ('G3', '해결안 도출', ('s5_solve', 's6_concept', 's7_gate')),
    ('G4', '검증·선택', ('s8_references', 's8_evaluate', 's9_report', 's10_feedback')),
)


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ActionTicket(Contract):
    action_type: str
    target_version_ids: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_outputs: list[str]
    allowed_tools: list[str]
    model_role: Literal['CODE', 'LITE', 'FLASH', 'EXPERT', 'HUMAN'] = 'CODE'
    reserved_microusd: int = Field(default=0, ge=0)
    reason: str = Field(min_length=1, max_length=1500)

    @model_validator(mode='after')
    def known_action(self):
        if self.action_type not in ACTIONS:
            raise ValueError('Unknown action')
        if len(set(self.target_version_ids)) != len(self.target_version_ids):
            raise ValueError('Duplicate target version')
        return self


class Review(Contract):
    event_id: str = Field(min_length=1, max_length=100)
    expected_epoch: int = Field(ge=0)
    snapshot_id: str
    target_version_id: str
    decision_id: str | None = None
    candidate_id: str | None = None
    obligation_id: str | None = None
    decision_type: Literal['APPROVE_EXPLORATION', 'REJECT_EXPLORATION', 'CORRECT_CLAIM',
                           'PREFER_CANDIDATE', 'APPROVE_TEST', 'RECORD_TEST_RESULT', 'RECORD_FIELD_RESULT']
    reason: str = Field(min_length=1)
    corrected_value: Any = None
    evidence_refs: list[str] = Field(default_factory=list)
    result: Literal['PASS', 'FAIL', 'UNKNOWN', 'NOT_RUN', 'ERROR'] = 'UNKNOWN'
    conditions: str = ''
    measurement: dict[str, Any] = Field(default_factory=dict)
    consent: Literal['NO_TRAINING', 'PROJECT_ONLY'] = 'NO_TRAINING'
    supersedes_event_id: str | None = None

    @model_validator(mode='after')
    def supported_result(self):
        observation = self.decision_type in ('RECORD_TEST_RESULT', 'RECORD_FIELD_RESULT')
        if observation and (not self.conditions or not self.evidence_refs or not self.measurement):
            raise ValueError('An observation requires conditions, evidence and measurements')
        if observation and (not self.candidate_id or not self.obligation_id):
            raise ValueError('An observation requires an exact candidate and obligation')
        if not observation and self.result != 'UNKNOWN':
            raise ValueError('Approval or preference cannot claim technical success')
        if self.decision_type == 'CORRECT_CLAIM' and self.corrected_value is None:
            raise ValueError('A correction requires a proposed value')
        return self


class RuleSpec(Contract):
    name: str = Field(min_length=1, max_length=160)
    domain: str
    required_functions: list[str] = Field(min_length=1, max_length=12)
    provided_function: str = Field(min_length=1)
    operation: Literal['ADD_VERIFICATION', 'SUGGEST_EFFECT', 'SUGGEST_REPAIR']
    effect_ids: list[str] = Field(default_factory=list, max_length=6)
    obligation: str = Field(min_length=1, max_length=1500)
    applicability: str = Field(min_length=1)
    source_versions: list[str] = Field(min_length=1, max_length=12)


class Conflict(ValueError):
    """Optimistic concurrency conflict, exposed as HTTP 409."""


class AccessDenied(ValueError):
    pass


class BudgetBusy(Conflict):
    """Other live calls temporarily hold enough of this run's remaining budget."""
