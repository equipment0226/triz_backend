"""Transactional MySQL repository with SQLite development support and file archives."""
from __future__ import annotations
import json
import re
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from sqlalchemy import Column, Float, Index, Integer, MetaData, String, Table, Text, create_engine, delete, event, func, select, text, update
from sqlalchemy.dialects.mysql import LONGTEXT, insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from .schema import GlobalState
from .settings import settings

metadata = MetaData()
LargeText = Text().with_variant(LONGTEXT(), "mysql")
def table(name, fields, key):
    return Table(name, metadata, *[Column(n, t, primary_key=n == key,
        autoincrement=(n == key and t is Integer)) for n, t in fields.items()], mysql_charset="utf8mb4")
runs = table("runs", dict(run_id=String(64), user_id=String(64), title=Text, mode=String(16),
    industry=Text, target_system=Text, status=String(32), current_stage=String(64),
    cost_usd=Float, started_at=String(40), ended_at=String(40)), "run_id")
states = table("run_states", dict(run_id=String(64), state_json=LargeText, updated_at=String(40)), "run_id")
steps = table("steps", dict(step_id=String(64), run_id=String(64), seq=Integer,
    stage=String(64), node=String(100), label=Text, agent_id=String(100), prompt_id=String(100),
    tier=String(4), model=String(120), status=String(32), verify_attempts=Integer,
    verdict=String(32), verdict_score=Float, human_intervened=Integer, tokens_in=Integer,
    tokens_out=Integer, cost_usd=Float, input_slice=LargeText, output_json=LargeText,
    verdicts=LargeText, error=Text, started_at=String(40), ended_at=String(40)), "step_id")
feedback = table("feedback_logs", dict(id=Integer, run_id=String(64), concept_id=String(64),
    rating=Integer, adopted=Integer, reason_tags=Text, comment=Text, created_at=String(40)), "id")
rag_docs = table("rag_docs", dict(id=String(100), collection=String(100), doc=LargeText,
    meta=LargeText, weight=Float, usage_count=Integer, created_at=String(40)), "id")
event_log = table("run_events", dict(id=Integer, run_id=String(64), payload=LargeText), "id")
llm_calls = table("llm_calls", dict(call_id=String(64), run_id=String(64), payload=LargeText), "call_id")
Index("idx_steps_run", steps.c.run_id, steps.c.seq)
Index("idx_rag_col", rag_docs.c.collection)
Index("idx_events_run", event_log.c.run_id, event_log.c.id)
Index("idx_calls_run", llm_calls.c.run_id)
engine = create_engine(settings.database_url or f"sqlite:///{settings.db_path.as_posix()}",
                       pool_pre_ping=True, pool_recycle=1800)
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _sqlite_setup(connection, _):
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
_init_lock = threading.Lock()
_initialized = False
_locks = {}
def init():
    global _initialized
    if not _initialized:
        with _init_lock:
            if not _initialized:
                metadata.create_all(engine)
                _initialized = True
def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _json(value):
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
def _upsert(c, target, values):
    ins = (mysql_insert if engine.dialect.name == "mysql" else sqlite_insert)(target).values(**values)
    changes = {k: v for k, v in values.items() if k not in [col.name for col in target.primary_key]}
    stmt = ins.on_duplicate_key_update(**changes) if engine.dialect.name == "mysql" else ins.on_conflict_do_update(
        index_elements=[col.name for col in target.primary_key], set_=changes)
    c.execute(stmt)
def archive(run_id, name, value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError("Invalid artifact identifier")
    folder = settings.storage_dir / "runs" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / name
    tmp = folder / f".{name}.{uuid.uuid4().hex}.tmp"
    tmp.write_text(value if isinstance(value, str) else _json(value), encoding="utf-8")
    tmp.replace(dest)
    return dest
@contextmanager
def run_lock(run_id):
    """Cross-worker exclusion in MySQL; in-process exclusion for local SQLite."""
    init()
    with _init_lock:
        mutex = _locks.setdefault(run_id, threading.RLock())
    if not mutex.acquire(blocking=False):
        raise RuntimeError("Run is busy")
    try:
        if engine.dialect.name == "mysql":
            import hashlib
            key = "triz:" + hashlib.sha256(run_id.encode()).hexdigest()[:50]
            with engine.connect() as c:
                if c.execute(text("SELECT GET_LOCK(:key, 0)"), {"key": key}).scalar() != 1:
                    raise RuntimeError("Run is busy")
                try:
                    yield
                finally:
                    c.execute(text("SELECT RELEASE_LOCK(:key)"), {"key": key})
        else:
            yield
    finally:
        mutex.release()
def create_run(state, title=""):
    init()
    with engine.begin() as c:
        c.execute(runs.insert().values(run_id=state.run_id, user_id=state.user_id,
            title=title or state.raw_query[:60], mode=state.control.mode.value,
            industry=state.domain.industry, target_system=state.domain.target_system,
            status=state.status, current_stage=state.control.current_stage, cost_usd=0, started_at=_now()))
def save_state(state):
    init()
    payload = state.model_dump_json()
    with engine.begin() as c:
        _upsert(c, states, dict(run_id=state.run_id, state_json=payload, updated_at=_now()))
        values = dict(status=state.status, current_stage=state.control.current_stage,
            cost_usd=state.cost.total_usd, industry=state.domain.industry,
            target_system=state.domain.target_system, mode=state.control.mode.value,
            title=state.scratch.get("title") or state.raw_query[:60])
        if state.status in ("COMPLETED", "FAILED"):
            values["ended_at"] = _now()
        c.execute(update(runs).where(runs.c.run_id == state.run_id).values(**values))
    archive(state.run_id, "state.json", payload)
def load_state(run_id):
    init()
    with engine.connect() as c:
        payload = c.execute(select(states.c.state_json).where(states.c.run_id == run_id)).scalar()
    return GlobalState.model_validate_json(payload) if payload else None
def list_runs(limit=50):
    init()
    with engine.connect() as c:
        return [dict(r) for r in c.execute(select(runs).order_by(runs.c.started_at.desc())
            .limit(max(1, min(limit, 1000)))).mappings()]
def delete_run(run_id):
    init()
    with run_lock(run_id), engine.begin() as c:
        for t in (llm_calls, event_log, feedback, steps, states, runs):
            c.execute(delete(t).where(t.c.run_id == run_id))
def save_step(run_id, step):
    init()
    data = step.model_dump(mode="json")
    verdict = step.verdicts[-1] if step.verdicts else {}
    values = {k: data.get(k) for k in steps.c.keys() if k in data}
    values.update(run_id=run_id, verdict=verdict.get("verdict", ""), verdict_score=verdict.get("score", 0))
    for k in ("input_slice", "output_json", "verdicts"):
        values[k] = _json(values[k])
    with engine.begin() as c:
        _upsert(c, steps, values)
    archive(run_id, f"step-{step.step_id}.json", data)
def list_steps(run_id):
    init()
    with engine.connect() as c:
        rows = c.execute(select(steps).where(steps.c.run_id == run_id).order_by(steps.c.seq)).mappings()
        return [{k: v for k, v in r.items() if k not in ("input_slice", "output_json", "verdicts")} for r in rows]
def get_step(run_id, step_id):
    init()
    with engine.connect() as c:
        row = c.execute(select(steps).where(steps.c.run_id == run_id, steps.c.step_id == step_id)).mappings().first()
    if not row:
        return None
    result = dict(row)
    for k in ("input_slice", "output_json", "verdicts"):
        result[k] = json.loads(result[k] or "null")
    return result
def save_feedback(run_id, concept_id, rating, adopted, tags, comment):
    init()
    with engine.begin() as c:
        c.execute(feedback.insert().values(run_id=run_id, concept_id=concept_id, rating=rating,
            adopted=adopted, reason_tags=_json(tags), comment=comment, created_at=_now()))
def rag_upsert(doc_id, collection, doc, meta, weight=1.0):
    init()
    with engine.begin() as c:
        count = c.execute(select(rag_docs.c.usage_count).where(rag_docs.c.id == doc_id)).scalar() or 0
        _upsert(c, rag_docs, dict(id=doc_id, collection=collection, doc=doc, meta=_json(meta),
            weight=weight, usage_count=count, created_at=_now()))
def rag_all(collection):
    init()
    with engine.connect() as c:
        rows = c.execute(select(rag_docs).where(rag_docs.c.collection == collection)).mappings()
        return [dict(r, meta=json.loads(r["meta"] or "{}")) for r in rows]
def rag_touch(doc_id):
    init()
    with engine.begin() as c:
        c.execute(update(rag_docs).where(rag_docs.c.id == doc_id).values(usage_count=rag_docs.c.usage_count + 1))
def append_event(run_id, payload):
    init()
    with engine.begin() as c:
        return c.execute(event_log.insert().values(run_id=run_id, payload=_json(payload))).inserted_primary_key[0]
def save_call(run_id, payload):
    init()
    call_id = uuid.uuid4().hex
    with engine.begin() as c:
        c.execute(llm_calls.insert().values(call_id=call_id, run_id=run_id, payload=_json(payload)))
    archive(run_id, f"call-{call_id}.json", payload)
def read_events(run_id, after=0):
    init()
    with engine.connect() as c:
        rows = c.execute(select(event_log).where(event_log.c.run_id == run_id,
            event_log.c.id > after).order_by(event_log.c.id).limit(500)).mappings()
        return [dict(json.loads(r["payload"]), event_id=r["id"]) for r in rows]
def stats():
    init()
    with engine.connect() as c:
        counts = {n: c.execute(select(func.count()).select_from(t)).scalar()
                  for n, t in (("runs", runs), ("steps", steps), ("feedback", feedback), ("rag_docs", rag_docs))}
    return dict(counts, backend=engine.dialect.name)
