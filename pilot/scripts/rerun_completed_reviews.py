"""Explicitly selected completed cases: refresh S8 and S9, retaining prior artifacts.

Run with --run-ids and a stable --job-id. Repeating the job skips finished cases
and resumes valid per-call checkpoints. It never executes S0-S7 or feedback.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from triz import events, pipeline, store
from triz.schema import EvaluationBundle
from triz.settings import settings


def prepare(run_id, job_id):
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            raise ValueError("Case does not exist")
        marker = state.scratch.get("review_refresh", {})
        if marker.get("job_id") == job_id and marker.get("status") == "COMPLETED":
            return None
        if state.status in ("RUNNING", "QUEUED", "WAITING_HUMAN"):
            raise ValueError("Case is busy or waiting for its owner")
        continuing = marker.get("job_id") == job_id
        if not continuing and (state.status != "COMPLETED" or not state.report):
            raise ValueError("Only completed cases with reports can start this job")
        if not continuing:
            store.archive(run_id, f"before-review-refresh-{job_id}.json", state.model_dump(mode="json"))
            marker = {"job_id": job_id, "status": "RUNNING", "baseline_cost": state.cost.total_usd,
                      "original_budget": state.cost.budget_usd, "concept_ids": [c.id for c in state.concepts]}
            pipeline._upgrade(state)
            state.evaluation = EvaluationBundle()
            state.report = None
            state.control.stage_index = next(i for i, p in enumerate(pipeline.PIPELINE) if p[0] == "s8_evaluate")
            # A newly requested execution gets the configured allowance; retain the
            # cumulative ledger and never add another allowance on a job retry.
            state.cost.budget_usd = state.cost.total_usd + float(settings.cfg("run.budget_usd", 3.0))
        if state.cost.total_usd >= state.cost.budget_usd:
            raise ValueError("Refresh allowance exhausted")
        marker["status"] = "RUNNING"
        state.scratch["review_refresh"] = marker
        state.scratch["execution_epoch"] = state.scratch.get("execution_epoch", 0) + 1
        state.scratch["active_seconds"] = 0
        state.scratch["last_stage_seq"] = len(state.steps)
        state.cost.over_budget = False
        for key in ("execution_deadline", "execution_stage_active", "dispatch_request", "resume_payload",
                    "resume_after_seq", "retry_notification_id", "interruption_reason"):
            state.scratch.pop(key, None)
        state.pending = None
        state.status = "RUNNING"
        store.save_state(state)
        return state.scratch["execution_epoch"]


def refresh(run_id, job_id):
    epoch = prepare(run_id, job_id)
    if epoch is None:
        return {"run_id": run_id, "status": "ALREADY_COMPLETED"}
    allowed = {"s8_evaluate", "s9_report"}
    while True:
        state = store.load_state(run_id)
        index = state.control.stage_index
        if state.status != "RUNNING" or index >= len(pipeline.PIPELINE) or pipeline.PIPELINE[index][0] not in allowed:
            break
        pipeline.execute_stage(run_id, index, epoch)
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        marker = state.scratch["review_refresh"]
        if state.scratch.get("execution_epoch") != epoch or marker["job_id"] != job_id:
            raise RuntimeError("Case changed during refresh")
        if state.status == "RUNNING" and state.report and state.evaluation.meeting.status == "COMPLETED":
            if set(marker["concept_ids"]) != {c.id for c in state.concepts}:
                raise RuntimeError("Refresh unexpectedly changed the solution set")
            state.status = marker["status"] = "COMPLETED"
            state.control.stage_index = len(pipeline.PIPELINE)
            events.emit(run_id, "done", cost=state.cost.total_usd)
        else:
            marker["status"] = state.status
        store.save_state(state)
        return {"run_id": run_id, "status": state.status,
                "meeting": state.evaluation.meeting.status,
                "additional_cost": round(state.cost.total_usd - marker["baseline_cost"], 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-ids", nargs="+", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--workers", type=int, default=2, choices=(1, 2))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.job_id):
        parser.error("Invalid job identifier")
    ids = list(dict.fromkeys(args.run_ids))
    def execute(run_id):
        try:
            result = refresh(run_id, args.job_id)
        except Exception as exc:
            result = {"run_id": run_id, "status": "ERROR", "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return result
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(execute, ids))
    print(json.dumps({"job_id": args.job_id, "results": results}), flush=True)
    return 0 if all(r["status"] in ("COMPLETED", "ALREADY_COMPLETED") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
