"""Checkpointed stage executor shared by n8n/MCP and the local development runner."""
from __future__ import annotations
import logging
import threading
import uuid
import time
from datetime import datetime, timezone
import httpx
from . import events, nodes, store
from .domain import deep_dive
from .context import AbortRun, BudgetExhausted, HumanInterrupt, ProviderUnavailable, UsageUncertain, ConceptReviewIncomplete, RunContext
from .schema import GlobalState, RunMode
from .settings import settings

log = logging.getLogger(__name__)
PIPELINE = [
    ("s0_bootstrap", "실행 계획", nodes.s0_bootstrap),
    ("s0_research", "산업·기술 심층 검토", deep_dive),
    ("s1_intake", "문제 추출·역질의", nodes.s1_extract),
    ("s2_confirm", "대상 시스템 확정", nodes.s2_confirm),
    ("s3_analyze", "시스템·기능·자원·인과 분석", nodes.s3_analyze),
    ("s4_define", "이상해결책·모순 정의", nodes.s4_define),
    ("s5_solve", "다중 기법 해결책 탐색", nodes.s5_solve),
    ("s6_concept", "개념 구체화", nodes.s6_concept),
    ("s7_gate", "제약 검토", nodes.s7_gate),
    ("s8_references", "근거 자료·적용 조건 검토", nodes.s8_references),
    ("s8_evaluate", "다직군 평가", nodes.s8_evaluate),
    ("s9_report", "시각화 보고서", nodes.s9_report),
    ("s10_feedback", "피드백", nodes.s10_feedback),
]
_RUNNING = {}
_WAKEUPS = set()
_thread_lock = threading.Lock()
DISPATCH_GRACE_SECONDS = 180
DISPATCH_ATTEMPTS = 3
def stage_list():
    return [{"key": k, "label": label, "index": i} for i, (k, label, _) in enumerate(PIPELINE)]
def envelope(state):
    return dict(run_id=state.run_id, stage_index=state.control.stage_index,
                epoch=state.scratch.get("execution_epoch", 0), status=state.status,
                continue_execution=state.status == "RUNNING" and not state.pending)
def create_run(raw_query, *, mode=None, user_id="local", attachments=None, workflow_version=None,
               run_id=None, creation_fingerprint=None, training_consent=None, explicit_required_tracks=(), charge_ticket=False):
    if not raw_query.strip():
        raise ValueError("문제를 입력해 주세요.")
    state = GlobalState(run_id=run_id or f"run-{uuid.uuid4().hex[:12]}", user_id=user_id, raw_query=raw_query)
    state.scratch.update(pipeline_version=3, execution_epoch=0)
    if creation_fingerprint:
        state.scratch['creation_fingerprint'] = creation_fingerprint
        state.scratch['creation_pending'] = True
    # A new project takes today's server defaults, never another run's pinned context.
    state.cost.budget_usd = float(settings.triz.get('run',{}).get('budget_usd',2.0))
    if mode:
        state.control.mode = RunMode[mode.upper()]
        state.scratch["mode_locked"] = True
    else:
        state.control.mode = RunMode[str(settings.triz.get('run',{}).get('default_mode','FULL')).upper()]
    state.intake.attachments = attachments or []
    default_training = training_consent is None
    training_consent = 'PROJECT_ONLY' if default_training else training_consent
    if training_consent not in ('NO_TRAINING','PROJECT_ONLY'):
        raise ValueError('Invalid training consent')
    from .ax.mode_contract import pin, ADAPTIVE_VERSION
    pin(state.control.mode.value,version=ADAPTIVE_VERSION,required=explicit_required_tracks)
    state.scratch.update(training_consent=training_consent,
        training_consent_version='project-default-v1' if default_training else 'explicit-project-consent-v1',
        explicit_required_tracks=sorted(set(explicit_required_tracks)))
    store.create_run(state, charge_ticket=charge_ticket)
    return finish_creation(state, workflow_version=workflow_version)


def finish_creation(state, *, workflow_version=None):
    """A retry can finish setup on its durable identity without making a new run."""
    from .ax import WORKFLOW
    from .ax.runtime import initialize, new_runs_enabled
    if workflow_version == WORKFLOW or (workflow_version is None and new_runs_enabled()):
        initialize(state)
    state.scratch.pop('creation_pending', None)
    store.save_state(state)
    return state
def _upgrade(state):
    if state.scratch.get("pipeline_version", 1) < 2:
        if state.control.stage_index >= 1:
            state.control.stage_index += 1
        state.scratch["pipeline_version"] = 2
    if state.scratch.get("pipeline_version", 2) < 3:
        # Old stage 10 awaited references after ranking. Attach first, then refresh
        # evaluation using those records. Completed reports keep their old revision.
        if state.control.stage_index == 10:
            state.control.stage_index = 9
            state.evaluation = type(state.evaluation)()
            state.report = None
        state.scratch["pipeline_version"] = 3
        if state.status != "COMPLETED":
            from .domain import sync_contract
            sync_contract(state)

def _unresolved_failures(state):
    """A successful answer-driven retry supersedes only its own earlier failure."""
    resolved = state.scratch.setdefault("resolved_step_failures", {})
    cutoff = state.scratch.get("resume_after_seq", 0)
    baseline = state.scratch.get("last_stage_seq", 0)
    def identity(step):
        # Tracks and reviewers reuse node names for different logical invocations.
        return step.stage, step.node, step.agent_id, step.prompt_id, step.label
    replacements = {
        identity(step): step for step in state.steps
        if step.seq > cutoff and step.status in ("OK", "WARN", "SKIPPED")
        and (step.status != "SKIPPED" or step.output_json)
    } if cutoff else {}
    failures = []
    for step in state.steps:
        if step.status != "FAILED" or step.seq <= baseline or step.step_id in resolved:
            continue
        replacement = replacements.get(identity(step)) if step.seq <= cutoff else None
        if replacement:
            resolved[step.step_id] = f"답변 반영 후 같은 분석 호출 완료: {replacement.step_id}"
        else:
            failures.append(step)
    return failures

def _mark_interrupted(state, reason, status="INTERRUPTED"):
    state.status = status
    refresh = state.scratch.get("review_refresh", {})
    if refresh and refresh.get("status") != "COMPLETED":
        refresh["status"] = status
    state.scratch.setdefault("retry_notification_id", f"retry-{uuid.uuid4().hex}")
    state.scratch["interruption_reason"] = reason

def _emit_retry(state):
    events.emit(state.run_id, "retry_required", status=state.status,
                notification_id=state.scratch["retry_notification_id"],
                message=state.scratch["interruption_reason"],
                stage=state.scratch.get("stage_key", ""))
def execute_stage(run_id, stage_index, epoch=0):
    """At-least-once deliveries: lock + expected stage/epoch prevent duplicate commits."""
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            raise ValueError("실행 기록이 없습니다.")
        _upgrade(state)
        if epoch != state.scratch.get("execution_epoch", 0):
            return dict(envelope(state), continue_execution=False, stale=True)
        if stage_index != state.control.stage_index:
            return envelope(state)
        if state.pending or state.status in ("FAILED", "COMPLETED", "INTERRUPTED"):
            return envelope(state)
        if stage_index >= len(PIPELINE):
            state.status = "COMPLETED"
            store.save_state(state)
            return envelope(state)
        ctx = RunContext(state)
        key, label, fn = PIPELINE[stage_index]
        state.status = "RUNNING"
        refresh = state.scratch.get("review_refresh", {})
        if key in ("s8_evaluate", "s9_report") and refresh and refresh.get("status") != "COMPLETED":
            refresh["status"] = "RUNNING"
        state.scratch["stage_key"] = key
        started = time.time()
        state.scratch["execution_stage_active"] = {"epoch": epoch, "index": stage_index, "started_at": started}
        state.scratch["execution_progress_at"] = started
        ctx.persist()
        events.emit(run_id, "stage_start", stage=key, label=label, index=stage_index, total=len(PIPELINE))
        from .execution_config import profile
        profile_token=profile.set(state.scratch.get('ax_bundle'))
        remaining = float(settings.cfg("run.max_wallclock_min", 30)) * 60 - state.scratch.get("active_seconds", 0)
        state.scratch["execution_deadline"] = started + max(0, remaining)
        try:
            if remaining <= 0:
                raise AbortRun("분석 실행 시간 예산에 도달했습니다. 이어서 실행해 주세요.")
            from .ax import enabled as ax_enabled
            if ax_enabled(state):
                from .ax.ledger import budget
                usage = budget(state.run_id, state.user_id)
                from .ax.usage_recovery import blocking_count
                if usage['unknown_attempts'] and blocking_count(state):
                    # A retry must not pay for retrieval/other tracks before
                    # eventually reaching the same blocked UNKNOWN call.
                    state.scratch['ax_interrupted_usage'] = usage
                    state.cost.total_usd = usage['spent_microusd'] / 1e6
                    raise UsageUncertain()
            from .ax import runtime as ax_runtime
            ax_runtime.before_stage(ctx, key)
            fn(ctx)
            if _unresolved_failures(state):
                raise RuntimeError("필수 분석 호출이 실패했습니다. 설정을 확인하고 이어서 실행해 주세요.")
            state.control.stage_index += 1
            # An explicitly requested review refresh ends at its report even when
            # resumed through the normal UI after a provider/validation failure.
            if key == "s9_report" and refresh and refresh.get("status") == "RUNNING":
                refresh["status"] = "COMPLETED"
                state.control.stage_index = len(PIPELINE)
            state.scratch["last_stage_seq"] = len(state.steps)
            state.scratch.pop("resume_after_seq", None)
            state.status = "COMPLETED" if state.control.stage_index == len(PIPELINE) else "RUNNING"
            ax_runtime.checkpoint(state, key)
            store.archive(run_id, f"stage-{epoch}-{stage_index}.json", state.model_dump(mode="json"))
            events.emit(run_id, "stage_end", stage=key, index=state.control.stage_index)
        except HumanInterrupt as exc:
            state.pending = exc.request
            state.status = "WAITING_HUMAN"
            events.emit(run_id, "interrupt", kind=exc.request.kind, title=exc.request.title, stage=key)
        except ProviderUnavailable as exc:
            state.scratch["provider_status"] = exc.status_code
            _mark_interrupted(state, str(exc))
            ctx.warn(str(exc))
        except BudgetExhausted as exc:
            state.scratch['ax_interrupted_budget'] = dict(exc.details)
            _mark_interrupted(state, str(exc))
            ctx.warn(str(exc))
        except AbortRun as exc:
            reason = ("분석 실행 예산에 도달했습니다. 실행 설정을 확인하고 이어서 실행해 주세요."
                      if "예산" in str(exc) else "분석이 중단되었습니다. 저장된 단계에서 다시 이어서 실행해 주세요.")
            if isinstance(exc, (UsageUncertain, ConceptReviewIncomplete)) or str(exc).startswith('ARIZ Part'):
                reason = str(exc)
            _mark_interrupted(state, reason)
            ctx.warn(str(exc))
        except Exception as exc:
            log.exception("Stage failed: %s", key)
            _mark_interrupted(state, "이 단계의 분석을 완료하지 못했습니다. 저장된 내용으로 다시 시도해 주세요.", "FAILED")
            state.control.errors.append(str(exc))
            events.emit(run_id, "stage_error", stage=key, message="이 단계의 분석을 완료하지 못했습니다.")
        finally:
            profile.reset(profile_token)
            elapsed = time.time() - started
            state.scratch["active_seconds"] = state.scratch.get("active_seconds", 0) + elapsed
            state.scratch.setdefault("stage_timings", []).append({"stage": key, "seconds": round(elapsed, 3), "status": state.status})
            state.scratch.pop("execution_deadline", None)
            state.scratch.pop("execution_stage_active", None)
            state.scratch["execution_progress_at"] = time.time()
        if state.status in ('WAITING_HUMAN', 'FAILED', 'INTERRUPTED'):
            from .ax import runtime as ax_runtime
            ax_runtime.checkpoint(state, key, interrupted=True)
        ctx.persist()
        if state.status in ("FAILED", "INTERRUPTED"):
            _emit_retry(state)
        if state.status == "COMPLETED":
            events.emit(run_id, "done", cost=state.cost.total_usd)
        return envelope(state)
def _run_loop(run_id):
    try:
        state = store.load_state(run_id)
        msg = envelope(state)
        while True:
            msg = execute_stage(msg["run_id"], msg["stage_index"], msg["epoch"])
            if not msg["continue_execution"]:
                return
    finally:
        with _thread_lock:
            if _RUNNING.get(run_id) is threading.current_thread():
                _RUNNING.pop(run_id, None)
                if run_id in _WAKEUPS:
                    _WAKEUPS.discard(run_id)
                    _spawn_local(run_id)

def _spawn_local(run_id):
    """Caller holds _thread_lock, including the old worker's final handoff."""
    worker = threading.Thread(target=_run_loop, args=(run_id,), daemon=True)
    _RUNNING[run_id] = worker
    try:
        worker.start()
    except Exception:
        _RUNNING.pop(run_id, None)
        raise

def _dispatch_failed(run_id, dispatch):
    """Never overwrite a stage that started despite a webhook timeout."""
    try:
        with store.run_lock(run_id):
            state = store.load_state(run_id)
            if (not state or state.status != "QUEUED" or state.pending
                    or state.scratch.get("dispatch_request") != dispatch
                    or state.scratch.get("execution_epoch", 0) != dispatch["epoch"]
                    or state.control.stage_index != dispatch["index"]):
                return False
            _mark_interrupted(state, "분석 실행 요청을 전달하지 못했습니다. 다시 시도해 주세요.")
            store.save_state(state)
            _emit_retry(state)
            return True
    except RuntimeError as exc:
        if str(exc) != "Run is busy":
            raise
        return False  # An executing worker owns the state; recovery handles a later loss.
def _dispatch_still_pending(run_id, dispatch):
    """Do not resend a request already claimed, superseded, or deleted."""
    try:
        with store.run_lock(run_id):
            state = store.load_state(run_id)
            return bool(state and state.status == "QUEUED" and not state.pending
                and state.scratch.get("dispatch_request") == dispatch
                and state.scratch.get("execution_epoch", 0) == dispatch["epoch"]
                and state.control.stage_index == dispatch["index"])
    except RuntimeError as exc:
        if str(exc) != "Run is busy":
            raise
        return False


def _send_dispatch(run_id, dispatch, message):
    if not settings.n8n_webhook_url or not settings.service_token:
        raise RuntimeError("n8n webhook과 서비스 인증 설정이 필요합니다.")
    for attempt in range(1, DISPATCH_ATTEMPTS + 1):
        try:
            response = httpx.post(settings.n8n_webhook_url, json=message,
                headers={"Authorization": f"Bearer {settings.service_token}"}, timeout=15)
            response.raise_for_status()
            return
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = status_code is None or status_code in (408, 429) or status_code >= 500
            # The first POST may have arrived even when its response was lost.
            # Check the durable dispatch identity under the stage execution lock.
            if not _dispatch_still_pending(run_id, dispatch):
                return
            events.emit(run_id, "dispatch_attempt_failed", attempt=attempt,
                error_type=type(exc).__name__, status_code=status_code,
                will_retry=retryable and attempt < DISPATCH_ATTEMPTS)
            if not retryable or attempt == DISPATCH_ATTEMPTS:
                raise
            time.sleep(attempt)
            if not _dispatch_still_pending(run_id, dispatch):
                return


def start(run_id):
    if settings.orchestrator == "n8n":
        with store.run_lock(run_id):
            state = store.load_state(run_id)
            if not state:
                raise ValueError("실행 기록이 없습니다.")
            if state.pending or state.status in ("FAILED", "COMPLETED", "INTERRUPTED"):
                return
            if state.scratch.get("execution_stage_active"):
                return
            dispatch = {"id": uuid.uuid4().hex, "epoch": state.scratch.get("execution_epoch", 0),
                        "index": state.control.stage_index, "started_at": time.time()}
            state.status = "QUEUED"
            state.scratch["dispatch_request"] = dispatch
            state.scratch["execution_progress_at"] = dispatch["started_at"]
            store.save_state(state)
            message = envelope(state)
        try:
            _send_dispatch(run_id, dispatch, message)
        except Exception:
            if _dispatch_failed(run_id, dispatch):
                raise
        return
    with _thread_lock:
        if run_id in _RUNNING:
            _WAKEUPS.add(run_id)
            return
        _spawn_local(run_id)
def _mutate(run_id, apply):
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            return False
        _upgrade(state)
        if not apply(state):
            return False
        state.scratch["execution_epoch"] = state.scratch.get("execution_epoch", 0) + 1
        from .ax import enabled as ax_enabled
        if ax_enabled(state):
            from .ax.ledger import advance_epoch
            advance_epoch(state, 'user_resume_or_replan')
        state.status = "RUNNING"
        for key in ("retry_notification_id", "interruption_reason", "provider_status", "execution_stage_active", "dispatch_request", "ax_interrupted_budget"):
            state.scratch.pop(key, None)
        state.scratch["execution_progress_at"] = time.time()
        store.save_state(state)
    start(run_id)
    return True
def resume(run_id, payload):
    def apply(state):
        if not state.pending:
            return False
        if payload.get("interrupt_id") and payload["interrupt_id"] != state.pending.interrupt_id:
            return False
        if state.pending.kind == "DECIDE":
            expected = {c['concept_id'] for c in state.pending.payload.get('conditional', [])}
            decisions = payload.get('decisions')
            if not isinstance(decisions, dict) or set(decisions) != expected or any(v not in ('accept', 'drop') for v in decisions.values()):
                raise ValueError("보류된 모든 해결책의 유지·제외 판정을 선택해 주세요.")
            from .ax.effect_history import validate_reviews
            if payload.get('application_reviews'):
                validate_reviews(state, payload['application_reviews'])
            state.scratch['ax_response_origin'] = state.pending.interrupt_id
            from .ax.contracts import now
            state.scratch['ax_response_received_at'] = now()
        state.scratch["resume_payload"] = payload
        state.scratch["resume_after_seq"] = len(state.steps)
        state.pending = None
        return True
    return _mutate(run_id, apply)
def continue_run(run_id):
    def apply(state):
        if state.pending or state.status not in ("INTERRUPTED", "FAILED", "CREATED", "QUEUED"):
            return False
        if state.scratch.get('creation_pending'):
            finish_creation(state)
        state.scratch["last_stage_seq"] = len(state.steps)
        # Resume preserves this project's own cap and accumulated spend. Global
        # defaults apply only when creating a project, never reset its allowance.
        from .ax import enabled as ax_enabled
        if ax_enabled(state):
            from .ax.ledger import budget
            state.cost.budget_usd=budget(state.run_id)['limit_microusd']/1e6
        refresh = state.scratch.get("review_refresh", {})
        if refresh and refresh.get("status") != "COMPLETED":
            state.cost.budget_usd = float(refresh.get("budget_usd",
                state.cost.budget_usd + float(refresh.get("baseline_cost", 0))))
        state.cost.over_budget = state.cost.total_usd > state.cost.budget_usd
        state.scratch["active_seconds"] = 0
        return state.control.stage_index < len(PIPELINE)
    return _mutate(run_id, apply)
def rerun_from(run_id, stage_key, instruction=""):
    idx = next((i for i, (key, _, _) in enumerate(PIPELINE) if key == stage_key), None)
    if idx is None:
        return False
    def apply(state):
        if state.status in ("RUNNING", "QUEUED"):
            return False
        from .ax.mode_contract import contract
        if contract(state):
            import copy
            keys = [k for k in state.scratch if k.startswith('ax_') and k not in
                    ('ax_bundle', 'ax_members', 'ax_snapshot_id', 'ax_project_id', 'ax_semantic_archive')]
            state.scratch.setdefault('ax_semantic_archive', []).append({
                'episode_id': state.scratch['semantic_episode_id'], 'stage': stage_key,
                'snapshot_id': state.scratch.get('ax_snapshot_id'),
                'projection': {k: copy.deepcopy(state.scratch[k]) for k in keys}})
            from .ax.mode_contract import unified
            if not unified(state) or idx<=8:
                state.scratch['semantic_generation'] = state.scratch.get('semantic_generation', 0) + 1
                state.scratch['semantic_episode_id'] = state.run_id + ':' + str(state.scratch['semantic_generation'])
            for key in ('ax_optional_previous', 'ax_optional_sequence', 'ax_optional_deferred_budget', 'ax_selection', 'ax_coherence', 'ax_report_snapshot_id'):
                state.scratch.pop(key, None)
            if idx <= 8:
                for key in ('ax_recovery_fingerprints', 'ax_constraint_failures', 'ax_action_results',
                            'ax_effect_applications', 'ax_effect_reviews', 'ax_effect_selections', 'ax_condition_facts',
                            'ax_gate_response_pending','ax_gate_response_recorded','ax_gate_delta_pending',
                            'adaptive_gate_pending_ids','adaptive_dropped_candidates'):
                    state.scratch.pop(key, None)
            if idx <= 6:
                for key in ('prior_case_ids', 'ax_blocked_tracks','adaptive_search'):
                    state.scratch.pop(key, None)
        state.scratch.pop("review_refresh", None)
        state.control.stage_index = idx
        state.pending = None
        state.report = None
        # Keep archived revisions, but invalidate every dependent product artifact.
        for boundary, field in ((4, "analysis"), (5, "definition"), (6, "solve"),
                                (7, "concepts"), (8, "constraint_checks"), (10, "evaluation")):
            if idx <= boundary:
                previous = getattr(state, field)
                setattr(state, field, [] if isinstance(previous, list) else type(previous)())
        if idx <= 6:
            # A new solve revision gets its own bounded expansion. Continuing
            # an interrupted revision still retains its completed round count.
            for key in ('ax_coordination', 'ax_expansion_rounds', 'ax_expansion_deferred',
                        'ax_idea_inventory', 'ax_effect_applicability', 's_curve',
                        'ax_track_execution', 'ax_track_review_reasons', 'ax_solve_start_seq',
                        'ax_portfolio_trace', 'ax_solve_compatibility', 'idea_consolidation'):
                state.scratch.pop(key, None)
        if idx <= 9:
            state.evidence = []
            for c in state.concepts:
                c.evidence_ids = []
            for key in ("patent_additions", "evidence_gaps", "evidence_mappings", "related_references"):
                state.scratch.pop(key, None)
        state.scratch.pop("resume_payload", None)
        if idx <= 8:
            state.scratch.pop("gate_decisions", None)
            state.scratch.pop("constraint_normalization", None)
            for key in ('ax_recovery_complete','ax_recovery','ax_recovery_phases','ax_baseline_candidates','ax_applied_rules','ax_rule_patches'):
                state.scratch.pop(key,None)
        if idx <= 7:
            state.scratch.pop('ax_candidate_review',None)
            state.scratch.pop('ax_excluded',None)
            state.scratch.pop('ax_mechanisms',None)
            state.scratch.pop('excluded_concepts',None)
        state.scratch["last_stage_seq"] = len(state.steps)
        if instruction:
            state.control.injected_agents.setdefault(f"stage:{stage_key}", []).append(
                {"role_name": "사용자 의견", "instruction": instruction})
        return True
    return _mutate(run_id, apply)
def inject_agent(run_id, node, role_name, instruction):
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state or state.status in ("RUNNING", "QUEUED"):
            return False
        state.control.injected_agents.setdefault(node, []).append(
            {"role_name": role_name, "instruction": instruction})
        store.save_state(state)
    return True
def _recover_step_journal(state):
    """Restore durable step results omitted from the last parent checkpoint."""
    import json
    from sqlalchemy import select
    from .schema import StepRecord
    by_id = {step.step_id: step for step in state.steps}
    with store.engine.connect() as connection:
        rows = connection.execute(select(store.steps).where(store.steps.c.run_id == state.run_id)).mappings().all()
    for row in rows:
        prior = by_id.get(row['step_id'])
        fields = prior.model_dump() if prior else {}
        fields.update({key: value for key, value in row.items() if key in StepRecord.model_fields
                       and (value is not None or key == 'ended_at')})
        for key in ('input_slice', 'output_json', 'verdicts'):
            fallback = [] if key == 'verdicts' else {}
            value = fields.get(key)
            fields[key] = (json.loads(value) if isinstance(value, str) else value) or fallback
        saved = StepRecord.model_validate(fields)
        if not prior or saved.status != 'RUNNING' or prior.status == 'RUNNING':
            by_id[saved.step_id] = saved
    state.steps = sorted(by_id.values(), key=lambda step: (step.seq, step.step_id))
    for step in state.steps:
        if step.status == 'RUNNING':
            step.status = 'FAILED'
            step.error = '실행 워커가 종료되어 이 호출의 완료를 확인하지 못했습니다.'
            step.ended_at = datetime.now()
            store.save_step(state.run_id, step)


def recover_orphans():
    """Detect lost workers under the same lock that protects stage execution.

    A stage marker with a free lock proves its worker exited. Dispatch and stage
    handoffs get a grace period; a healthy, long-running stage keeps its lock.
    """
    from sqlalchemy import select
    from pydantic import ValidationError
    store.init()
    with store.engine.connect() as connection:
        rows = connection.execute(select(store.runs.c.run_id, store.states.c.updated_at)
            .join(store.states, store.runs.c.run_id == store.states.c.run_id)
            .where(store.runs.c.status.in_(("CREATED", "RUNNING", "QUEUED")))).mappings().all()
    recovered = []
    for row in rows:
        try:
            with store.run_lock(row["run_id"]):
                with _thread_lock:
                    if row["run_id"] in _RUNNING:
                        continue
                state = store.load_state(row["run_id"])
                if not state or state.pending or state.status not in ("CREATED", "RUNNING", "QUEUED"):
                    continue
                active = state.scratch.get("execution_stage_active") or state.scratch.get("execution_deadline")
                last_progress = state.scratch.get("execution_progress_at")
                if not last_progress:
                    # Legacy runs do not have progress markers yet. Read again
                    # under the lock so a just-completed handoff is never stale.
                    with store.engine.connect() as connection:
                        updated = connection.execute(select(store.states.c.updated_at)
                            .where(store.states.c.run_id == state.run_id)).scalar()
                    modified = datetime.fromisoformat(updated)
                    if modified.tzinfo is None:
                        modified = modified.replace(tzinfo=timezone.utc)
                    last_progress = modified.timestamp()
                if not active and time.time() - last_progress < DISPATCH_GRACE_SECONDS:
                    continue
                _upgrade(state)
                _recover_step_journal(state)
                state.scratch.pop("execution_stage_active", None)
                state.scratch.pop("execution_deadline", None)
                reason = '실행 워커가 종료되어 분석이 중단되었습니다. 완료된 분석은 보존되어 있습니다.'
                from .ax import enabled as ax_enabled
                if ax_enabled(state):
                    from .ax import ledger
                    try:
                        usage = ledger.recover_interrupted(state)
                    except ValueError as exc:
                        if str(exc)!='AX run not found': raise
                        # A damaged/deleted journal for one legacy checkpoint must
                        # not stop recovery of every other owner's run. Never
                        # rebuild its usage as zero or launch a replacement call.
                        _mark_interrupted(state,'실행 원장이 없어 비용·실행 상태를 확인할 수 없습니다. 원장 복구가 필요합니다.')
                        store.save_state(state)
                        _emit_retry(state)
                        recovered.append(state.run_id)
                        continue
                    if usage['unknown_attempts']:
                        reason += ' ' + str(UsageUncertain())
                    else:
                        reason += ' 저장된 단계에서 이어서 실행해 주세요.'
                else:
                    reason += ' 저장된 단계에서 이어서 실행해 주세요.'
                _mark_interrupted(state, reason)
                store.save_state(state)
                _emit_retry(state)
                recovered.append(state.run_id)
        except ValidationError:
            # One unreadable legacy checkpoint must not disable recovery for
            # every other run or prevent API startup. Retain it for repair.
            log.exception("Cannot recover invalid checkpoint for %s", row["run_id"])
        except RuntimeError as exc:
            if str(exc) != "Run is busy":
                raise
    return recovered
