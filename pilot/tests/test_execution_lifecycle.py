"""Regression coverage for human resumes, dispatch races, and lost workers."""
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy import update

from triz import pipeline, store
from triz.context import AbortRun, HumanInterrupt
from triz.schema import StepRecord
from triz.settings import settings


def _step(ctx, node, status, *, label="extract", agent_id="interviewer", output=None):
    step = StepRecord(seq=len(ctx.state.steps) + 1, stage="S1", node=node,
        label=label, agent_id=agent_id, prompt_id="P_S1_EXTRACT", status=status,
        output_json=output or {})
    ctx.state.steps.append(step)
    return step


@pytest.mark.parametrize("replacement", ["OK", "WARN", "SKIPPED"])
def test_answer_success_supersedes_old_failed_call(state, monkeypatch, replacement):
    def intake(ctx):
        if ctx.resume_payload() is None:
            _step(ctx, "s1_extract", "FAILED")
            _step(ctx, "s1_clarify", "OK")
            raise HumanInterrupt("CLARIFY", "Answer needed", {"questions": []})
        _step(ctx, "s1_extract", replacement, output={"frame": "answered"})
    monkeypatch.setattr(pipeline, "PIPELINE", [("intake", "intake", intake)])
    monkeypatch.setattr(pipeline, "start", lambda rid: None)
    assert pipeline.execute_stage(state.run_id, 0)["status"] == "WAITING_HUMAN"
    assert pipeline.resume(state.run_id, {"answers": ["answer"]})
    assert pipeline.execute_stage(state.run_id, 0, 1)["status"] == "COMPLETED"
    saved = store.load_state(state.run_id)
    original = saved.steps[0]
    assert original.status == "FAILED"
    assert original.step_id in saved.scratch["resolved_step_failures"]
    assert "resume_after_seq" not in saved.scratch


@pytest.mark.parametrize("mismatch", ["different_node", "different_target", "new_failure", "empty_skip"])
def test_answer_does_not_hide_unresolved_required_failure(state, monkeypatch, mismatch):
    def intake(ctx):
        if ctx.resume_payload() is None:
            _step(ctx, "s1_extract", "FAILED")
            raise HumanInterrupt("CLARIFY", "Answer needed", {})
        _step(ctx, "other" if mismatch == "different_node" else "s1_extract",
              "SKIPPED" if mismatch == "empty_skip" else "OK",
              label="another target" if mismatch == "different_target" else "extract")
        if mismatch == "new_failure":
            _step(ctx, "s1_extract", "FAILED")
    monkeypatch.setattr(pipeline, "PIPELINE", [("intake", "intake", intake)])
    monkeypatch.setattr(pipeline, "start", lambda rid: None)
    pipeline.execute_stage(state.run_id, 0)
    assert pipeline.resume(state.run_id, {"answers": ["answer"]})
    assert pipeline.execute_stage(state.run_id, 0, 1)["status"] == "FAILED"
    saved = store.load_state(state.run_id)
    assert saved.scratch["retry_notification_id"]
    assert "다시 시도" in saved.scratch["interruption_reason"]


def test_local_resume_during_worker_exit_is_not_lost(state, monkeypatch):
    paused, release, completed = threading.Event(), threading.Event(), threading.Event()
    entered = []
    def intake(ctx):
        if ctx.resume_payload() is None:
            raise HumanInterrupt("CLARIFY", "Answer needed", {})
        ctx.state.scratch["answer_processed"] = True
    execute = pipeline.execute_stage
    def paused_return(*args):
        entered.append(threading.current_thread())
        result = execute(*args)
        if result["status"] == "WAITING_HUMAN":
            paused.set()
            assert release.wait(5)
        elif result["status"] == "COMPLETED":
            completed.set()
        return result
    monkeypatch.setattr(pipeline, "PIPELINE", [("intake", "intake", intake)])
    monkeypatch.setattr(pipeline, "execute_stage", paused_return)
    pipeline.start(state.run_id)
    try:
        assert paused.wait(5)
        assert pipeline.resume(state.run_id, {"answers": ["answer"]})
        release.set()
        assert completed.wait(5)
    finally:
        release.set()
        for worker in entered:
            worker.join(5)
    assert store.load_state(state.run_id).scratch["answer_processed"]
    assert state.run_id not in pipeline._RUNNING
    assert state.run_id not in pipeline._WAKEUPS


def _n8n(monkeypatch):
    monkeypatch.setattr(settings, "orchestrator", "n8n")
    monkeypatch.setattr(settings, "n8n_webhook_url", "https://n8n.invalid/webhook")
    monkeypatch.setattr(settings, "service_token", "offline-token")


def test_dispatch_timeout_does_not_overwrite_finished_stage(state, monkeypatch):
    _n8n(monkeypatch)
    monkeypatch.setattr(pipeline, "PIPELINE", [("done", "done", lambda ctx: None)])
    def delivered_then_timeout(*args, **kwargs):
        message = kwargs["json"]
        pipeline.execute_stage(state.run_id, message["stage_index"], message["epoch"])
        raise httpx.ReadTimeout("accepted, but response lost")
    monkeypatch.setattr(pipeline.httpx, "post", delivered_then_timeout)
    pipeline.start(state.run_id)
    saved = store.load_state(state.run_id)
    assert saved.status == "COMPLETED"
    assert saved.control.stage_index == 1
    assert "retry_notification_id" not in saved.scratch


def test_dispatch_timeout_does_not_overwrite_newer_epoch(state, monkeypatch):
    _n8n(monkeypatch)
    def newer_dispatch_then_timeout(*args, **kwargs):
        with store.run_lock(state.run_id):
            fresh = store.load_state(state.run_id)
            fresh.scratch["execution_epoch"] += 1
            fresh.scratch["dispatch_request"] = {"id": "newer request"}
            store.save_state(fresh)
        raise httpx.ReadTimeout("old request failed")
    monkeypatch.setattr(pipeline.httpx, "post", newer_dispatch_then_timeout)
    pipeline.start(state.run_id)
    saved = store.load_state(state.run_id)
    assert saved.status == "QUEUED" and saved.scratch["execution_epoch"] == 1
    assert saved.scratch["dispatch_request"] == {"id": "newer request"}


def test_dispatch_timeout_preserves_worker_holding_run_lock(state, monkeypatch):
    _n8n(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    workers = []
    def running(ctx):
        entered.set()
        assert release.wait(5)
    monkeypatch.setattr(pipeline, "PIPELINE", [("work", "work", running)])
    def delivered_then_timeout(*args, **kwargs):
        message = kwargs["json"]
        worker = threading.Thread(target=pipeline.execute_stage,
            args=(state.run_id, message["stage_index"], message["epoch"]))
        workers.append(worker)
        worker.start()
        assert entered.wait(5)
        raise httpx.ReadTimeout("accepted; worker is still running")
    monkeypatch.setattr(pipeline.httpx, "post", delivered_then_timeout)
    try:
        pipeline.start(state.run_id)
        assert store.load_state(state.run_id).status == "RUNNING"
    finally:
        release.set()
        for worker in workers:
            worker.join(5)
    assert store.load_state(state.run_id).status == "COMPLETED"


def test_dispatch_failure_preserves_answer_and_exposes_retry(state, monkeypatch):
    _n8n(monkeypatch)
    state.status = "RUNNING"
    state.scratch["resume_payload"] = {"answers": ["saved answer"]}
    store.save_state(state)
    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("private endpoint details")
    monkeypatch.setattr(pipeline.httpx, "post", unavailable)
    with pytest.raises(httpx.ConnectError):
        pipeline.start(state.run_id)
    saved = store.load_state(state.run_id)
    assert saved.status == "INTERRUPTED"
    assert saved.scratch["resume_payload"] == {"answers": ["saved answer"]}
    assert "private" not in saved.scratch["interruption_reason"]
    retries = [event for event in store.read_events(state.run_id) if event["type"] == "retry_required"]
    assert len(retries) == 1
    assert retries[0]["notification_id"] == saved.scratch["retry_notification_id"]
    monkeypatch.setattr(pipeline, "start", lambda rid: None)
    assert pipeline.continue_run(state.run_id)
    assert "retry_notification_id" not in store.load_state(state.run_id).scratch


@pytest.mark.parametrize("error,expected", [(RuntimeError("internal details"), "FAILED"), (AbortRun("budget"), "INTERRUPTED")])
def test_stage_stop_emits_durable_user_safe_retry(state, monkeypatch, error, expected):
    def stop(ctx):
        raise error
    monkeypatch.setattr(pipeline, "PIPELINE", [("stop", "stop", stop)])
    assert pipeline.execute_stage(state.run_id, 0)["status"] == expected
    saved = store.load_state(state.run_id)
    notification_id = saved.scratch["retry_notification_id"]
    assert "internal details" not in saved.scratch["interruption_reason"]
    assert "execution_stage_active" not in saved.scratch
    assert pipeline.execute_stage(state.run_id, 0)["status"] == expected
    assert store.load_state(state.run_id).scratch["retry_notification_id"] == notification_id
    assert len([event for event in store.read_events(state.run_id) if event["type"] == "retry_required"]) == 1


def test_recovery_preserves_live_worker_even_with_stale_progress(state, monkeypatch):
    _n8n(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    def running():
        with store.run_lock(state.run_id):
            state.status = "RUNNING"
            state.scratch["execution_stage_active"] = {"epoch": 0, "index": 0}
            state.scratch["execution_progress_at"] = time.time() - 3600
            store.save_state(state)
            entered.set()
            assert release.wait(5)
    worker = threading.Thread(target=running)
    worker.start()
    try:
        assert entered.wait(5)
        assert state.run_id not in pipeline.recover_orphans()
        assert store.load_state(state.run_id).status == "RUNNING"
    finally:
        release.set()
        worker.join(5)
    assert state.run_id in pipeline.recover_orphans()
    saved = store.load_state(state.run_id)
    assert saved.status == "INTERRUPTED" and saved.scratch["retry_notification_id"]
    assert state.run_id not in pipeline.recover_orphans()


@pytest.mark.parametrize("status", ["QUEUED", "RUNNING"])
def test_recovery_allows_handoff_grace_then_notifies(state, monkeypatch, status):
    _n8n(monkeypatch)
    state.status = status
    state.scratch["execution_progress_at"] = time.time()
    store.save_state(state)
    assert state.run_id not in pipeline.recover_orphans()
    state.scratch["execution_progress_at"] -= pipeline.DISPATCH_GRACE_SECONDS + 5
    store.save_state(state)
    assert state.run_id in pipeline.recover_orphans()
    assert store.load_state(state.run_id).status == "INTERRUPTED"


def test_recovery_uses_legacy_state_timestamp(state, monkeypatch):
    _n8n(monkeypatch)
    state.status = "RUNNING"
    store.save_state(state)
    assert state.run_id not in pipeline.recover_orphans()
    old = datetime.fromtimestamp(time.time() - 3600, tz=timezone.utc).isoformat()
    with store.engine.begin() as connection:
        connection.execute(update(store.states).where(store.states.c.run_id == state.run_id).values(updated_at=old))
    assert state.run_id in pipeline.recover_orphans()


def test_recovery_reloads_legacy_timestamp_after_acquiring_lock(state, monkeypatch):
    _n8n(monkeypatch)
    state.status = "RUNNING"
    store.save_state(state)
    old = datetime.fromtimestamp(time.time() - 3600, tz=timezone.utc).isoformat()
    with store.engine.begin() as connection:
        connection.execute(update(store.states).where(store.states.c.run_id == state.run_id).values(updated_at=old))
    run_lock = store.run_lock
    @contextmanager
    def worker_just_finished(run_id):
        with run_lock(run_id):
            if run_id == state.run_id:
                store.save_state(store.load_state(run_id))
            yield
    monkeypatch.setattr(store, "run_lock", worker_just_finished)
    assert state.run_id not in pipeline.recover_orphans()
    assert store.load_state(state.run_id).status == "RUNNING"
