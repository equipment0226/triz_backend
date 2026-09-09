"""실행 컨텍스트: 상태 + 이벤트 + 단계 기록."""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Optional

from . import events, store
from .schema import GlobalState, HumanRequest, StepRecord


class HumanInterrupt(Exception):
    """노드가 사용자 입력을 요구할 때 발생시킨다."""

    def __init__(self, kind: str, title: str, payload: dict[str, Any], stage: str = ""):
        super().__init__(title)
        self.request = HumanRequest(kind=kind, title=title, payload=payload, stage=stage)


class AbortRun(Exception):
    pass


class RunContext:
    def __init__(self, state: GlobalState):
        self.state = state
        self.lock = threading.Lock()
        self.budget = {"reserved": 0.0}
        self.cancelled = False
        from .settings import settings
        self.call_slots = threading.BoundedSemaphore(max(1, int(settings.cfg("run.parallel_workers", 4))))

    # ---------------- 이벤트
    def emit(self, type_: str, **data: Any) -> None:
        events.emit(self.state.run_id, type_, **data)

    # ---------------- 단계 기록
    def start_step(self, *, node: str, label: str, stage: str, agent_id: str,
                   prompt_id: str, tier: str) -> StepRecord:
        with self.lock:
            seq = len(self.state.steps) + 1
            step = StepRecord(seq=seq, stage=stage, node=node, label=label, agent_id=agent_id,
                              prompt_id=prompt_id, tier=tier, status="RUNNING")
            self.state.steps.append(step)
        self.emit("node_start", step_id=step.step_id, seq=seq, stage=stage, node=node,
                  label=label, agent=agent_id, tier=tier)
        return step

    def finish_step(self, step: StepRecord, status: str = "OK") -> None:
        step.status = status
        step.ended_at = datetime.now()
        with self.lock:
            self.state.cost.over_budget = self.state.cost.total_usd > self.state.cost.budget_usd
        store.save_step(self.state.run_id, step)
        v = step.verdicts[-1] if step.verdicts else {}
        self.emit("node_end", step_id=step.step_id, node=step.node, label=step.label,
                  status=status, verdict=v.get("verdict"), score=v.get("score"),
                  attempts=step.verify_attempts, cost=round(step.cost_usd, 5),
                  total_cost=round(self.state.cost.total_usd, 5))

    def warn(self, msg: str) -> None:
        self.state.control.warnings.append(msg)
        self.emit("warning", message=msg)

    # ---------------- 저장
    def persist(self) -> None:
        with self.lock:
            store.save_state(self.state)

    def set_stage(self, stage: str) -> None:
        self.state.control.current_stage = stage
        self.emit("stage", stage=stage)
        self.persist()

    def resume_payload(self) -> Optional[dict]:
        return self.state.scratch.pop("resume_payload", None)
