"""실행 이벤트 버스 (SSE 브로드캐스트용)."""
from __future__ import annotations

import queue
import threading
from datetime import datetime
from typing import Any

_LOCK = threading.Lock()
_SUBS: dict[str, list[queue.Queue]] = {}
_LOG: dict[str, list[dict]] = {}
MAX_LOG = 500


def subscribe(run_id: str) -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=1000)
    with _LOCK:
        _SUBS.setdefault(run_id, []).append(q)
    return q


def unsubscribe(run_id: str, q: queue.Queue) -> None:
    with _LOCK:
        if run_id in _SUBS and q in _SUBS[run_id]:
            _SUBS[run_id].remove(q)


def history(run_id: str) -> list[dict]:
    with _LOCK:
        return list(_LOG.get(run_id, []))


def emit(run_id: str, type_: str, **data: Any) -> dict:
    ev = {"type": type_, "ts": datetime.now().isoformat(timespec="seconds"), **data}
    from . import store
    ev["event_id"] = store.append_event(run_id, ev)
    with _LOCK:
        log = _LOG.setdefault(run_id, [])
        log.append(ev)
        if len(log) > MAX_LOG:
            del log[: len(log) - MAX_LOG]
        for q in list(_SUBS.get(run_id, [])):
            try:
                q.put_nowait(ev)
            except queue.Full:
                pass
    return ev


def clear(run_id: str) -> None:
    with _LOCK:
        _LOG.pop(run_id, None)
