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
from .context import AbortRun, HumanInterrupt, RunContext
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
def stage_list():
    return [{"key": k, "label": label, "index": i} for i, (k, label, _) in enumerate(PIPELINE)]
def envelope(state):
    return dict(run_id=state.run_id, stage_index=state.control.stage_index,
                epoch=state.scratch.get("execution_epoch", 0), status=state.status,
                continue_execution=state.status == "RUNNING" and not state.pending)
def create_run(raw_query, *, mode=None, user_id="local", attachments=None):
    if not raw_query.strip():
        raise ValueError("문제를 입력해 주세요.")
    state = GlobalState(run_id=f"run-{uuid.uuid4().hex[:12]}", user_id=user_id, raw_query=raw_query)
    state.scratch.update(pipeline_version=3, execution_epoch=0)
    state.cost.budget_usd = float(settings.cfg("run.budget_usd", 3.0))
    if mode:
        state.control.mode = RunMode[mode.upper()]
        state.scratch["mode_locked"] = True
    state.intake.attachments = attachments or []
    store.create_run(state)
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
        remaining = float(settings.cfg("run.max_wallclock_min", 30)) * 60 - state.scratch.get("active_seconds", 0)
        state.scratch["execution_deadline"] = started + max(0, remaining)
        try:
            if remaining <= 0:
                raise AbortRun("분석 실행 시간 예산에 도달했습니다. 이어서 실행해 주세요.")
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
            store.archive(run_id, f"stage-{epoch}-{stage_index}.json", state.model_dump(mode="json"))
            events.emit(run_id, "stage_end", stage=key, index=state.control.stage_index)
        except HumanInterrupt as exc:
            state.pending = exc.request
            state.status = "WAITING_HUMAN"
            events.emit(run_id, "interrupt", kind=exc.request.kind, title=exc.request.title, stage=key)
        except AbortRun as exc:
            reason = ("분석 실행 예산에 도달했습니다. 실행 설정을 확인하고 이어서 실행해 주세요."
                      if "예산" in str(exc) else "분석이 중단되었습니다. 저장된 단계에서 다시 이어서 실행해 주세요.")
            _mark_interrupted(state, reason)
            ctx.warn(str(exc))
        except Exception as exc:
            log.exception("Stage failed: %s", key)
            _mark_interrupted(state, "이 단계의 분석을 완료하지 못했습니다. 저장된 내용으로 다시 시도해 주세요.", "FAILED")
            state.control.errors.append(str(exc))
            events.emit(run_id, "stage_error", stage=key, message="이 단계의 분석을 완료하지 못했습니다.")
        finally:
            elapsed = time.time() - started
            state.scratch["active_seconds"] = state.scratch.get("active_seconds", 0) + elapsed
            state.scratch.setdefault("stage_timings", []).append({"stage": key, "seconds": round(elapsed, 3), "status": state.status})
            state.scratch.pop("execution_deadline", None)
            state.scratch.pop("execution_stage_active", None)
            state.scratch["execution_progress_at"] = time.time()
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
            if not settings.n8n_webhook_url or not settings.service_token:
                raise RuntimeError("n8n webhook과 서비스 인증 설정이 필요합니다.")
            response = httpx.post(settings.n8n_webhook_url, json=message,
                headers={"Authorization": f"Bearer {settings.service_token}"}, timeout=15)
            response.raise_for_status()
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
        state.status = "RUNNING"
        for key in ("retry_notification_id", "interruption_reason", "execution_stage_active", "dispatch_request"):
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
        state.scratch["resume_payload"] = payload
        state.scratch["resume_after_seq"] = len(state.steps)
        state.pending = None
        return True
    return _mutate(run_id, apply)
def continue_run(run_id):
    def apply(state):
        if state.pending or state.status not in ("INTERRUPTED", "FAILED", "CREATED", "QUEUED"):
            return False
        state.scratch["last_stage_seq"] = len(state.steps)
        state.cost.budget_usd = float(settings.cfg("run.budget_usd", state.cost.budget_usd))
        refresh = state.scratch.get("review_refresh", {})
        if refresh and refresh.get("status") != "COMPLETED":
            state.cost.budget_usd += float(refresh.get("baseline_cost", 0))
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
        if idx <= 9:
            state.evidence = []
            for c in state.concepts:
                c.evidence_ids = []
            for key in ("patent_additions", "evidence_gaps"):
                state.scratch.pop(key, None)
        state.scratch.pop("resume_payload", None)
        if idx <= 8:
            state.scratch.pop("gate_decisions", None)
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
def recover_orphans():
    """Detect lost workers under the same lock that protects stage execution.

    A stage marker with a free lock proves its worker exited. Dispatch and stage
    handoffs get a grace period; a healthy, long-running stage keeps its lock.
    """
    from sqlalchemy import select
    store.init()
    with store.engine.connect() as connection:
        rows = connection.execute(select(store.runs.c.run_id, store.states.c.updated_at)
            .join(store.states, store.runs.c.run_id == store.states.c.run_id)
            .where(store.runs.c.status.in_(("RUNNING", "QUEUED")))).mappings().all()
    recovered = []
    for row in rows:
        try:
            with store.run_lock(row["run_id"]):
                with _thread_lock:
                    if row["run_id"] in _RUNNING:
                        continue
                state = store.load_state(row["run_id"])
                if not state or state.pending or state.status not in ("RUNNING", "QUEUED"):
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
                state.scratch.pop("execution_stage_active", None)
                state.scratch.pop("execution_deadline", None)
                _mark_interrupted(state, "분석 실행이 중단되었습니다. 저장된 단계에서 이어서 실행해 주세요.")
                store.save_state(state)
                _emit_retry(state)
                recovered.append(state.run_id)
        except RuntimeError as exc:
            if str(exc) != "Run is busy":
                raise
    return recovered
