"""One native TRIZ stage in a fresh process, with a portable memory journal.

This module intentionally imports no application modules until ``run`` has
replaced the analysis database and storage settings. Invoke it in a new process
for every request; the signed continuation is owned by the API transport.
"""
from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import traceback
import uuid

VERSION = "triz-lab-memory-v1"
MAX_BUDGET_USD = 5.0
_USED = False


class LabInputError(ValueError):
    pass


class SerializedMemoryEngine:
    """Share SQLite across native parallel threads without nested rollbacks.

The lock covers the whole connection lease, rather than only individual SQL
statements. Nested reads reuse the current connection and nested transactions
use savepoints. No provider call holds this lock.
    """

    def __init__(self, engine):
        self._engine = engine
        self._lock = threading.RLock()
        self._local = threading.local()

    @property
    def dialect(self):
        return self._engine.dialect

    @property
    def url(self):
        return self._engine.url

    @contextmanager
    def connect(self):
        with self._lock:
            existing = getattr(self._local, "connection", None)
            if existing is not None:
                yield existing
                return
            with self._engine.connect() as connection:
                self._local.connection = connection
                try:
                    yield connection
                finally:
                    self._local.connection = None

    @contextmanager
    def begin(self):
        with self.connect() as connection:
            transaction = (connection.begin_nested() if connection.in_transaction()
                           else connection.begin())
            with transaction:
                yield connection

    def _run_ddl_visitor(self, *args, **kwargs):
        with self._lock:
            return self._engine._run_ddl_visitor(*args, **kwargs)

    def dispose(self):
        with self._lock:
            self._engine.dispose()


def contract_fingerprint():
    """Reject continuations after native code, knowledge, or prompts change."""
    from .lab_manifest import source_fingerprint
    return source_fingerprint()


def _no_training_review(connection, state, candidate, **values):
    """Keep native review provenance without producing a learning event."""
    if values.get("dimension") == "user_utility":
        return None
    row = dict(candidate_id=candidate.id,
               candidate_snapshot=candidate.model_dump(mode="json"),
               training_consent="NO_TRAINING", **values)
    row.pop("scope", None)
    row.pop("value", None)  # Ordinal reward is unnecessary for output validation.
    key = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False,
                                    default=str).encode()).hexdigest()
    row["review_id"] = "lab-review-" + key
    reviews = state.scratch.setdefault("lab_validation_reviews", [])
    if not any(old["review_id"] == row["review_id"] for old in reviews):
        reviews.append(row)
    return row["review_id"]


def _forbidden_training(*args, **kwargs):
    raise RuntimeError("Feedback, training, and indexing are disabled in the lab")


def _initialize(temp_root, budget):
    if "triz.settings" in sys.modules or "triz.store" in sys.modules:
        raise RuntimeError("The lab runner requires a fresh isolated process")
    # Explicit DATABASE_URL wins even over dotenv/MySQL aliases. Patent SQL is
    # deliberately separate: its read-only transport retains the original env.
    root = Path(__file__).resolve().parents[1]
    original_storage = (root / os.environ.get("TRIZ_LAB_ORIGINAL_STORAGE_DIR",
                           os.environ.get("STORAGE_DIR", "./data/storage"))).resolve()
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["DB_PATH"] = str(temp_root / "unused-analysis.db")
    os.environ["STORAGE_DIR"] = str(temp_root / "storage")
    os.environ["ORCHESTRATOR"] = "local"
    os.environ["TRIZ_AX_ENABLED"] = "true"
    os.environ["TRIZ_PROJECT_BUDGET_USD"] = str(budget)
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from . import pipeline, rag, store
    from .settings import settings
    from .ax import effect_history, feedback_events, ledger, outbox, registry, worker

    store.engine.dispose()  # The initial engine also points only at memory.
    engine = SerializedMemoryEngine(create_engine("sqlite://",
        connect_args={"check_same_thread": False}, poolclass=StaticPool))
    store.engine = engine
    store._initialized = False
    store._locks.clear()
    store.init()
    native_archive = store.archive

    def archive(run_id, name, value):
        if (name == "state.json" or re.fullmatch(r"stage-\d+-\d+\.json", name)
                or (name.startswith(("call-", "step-")) and name.endswith(".json"))):
            if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id) or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
                raise ValueError("Invalid artifact identifier")
            # These exact payloads are already in the memory SQL journal. Large
            # histories must not duplicate them into a container's small tmpfs.
            return settings.storage_dir / "runs" / run_id / name
        return native_archive(run_id, name, value)

    store.archive = archive
    ledger.metadata.create_all(engine)
    # Native init is additive, but repeated DDL on a single SQLite connection
    # could close a nested lease. All native tables are registered above.
    ledger.init = lambda: None
    ledger.transaction = engine.begin
    pipeline.PIPELINE = pipeline.PIPELINE[:12]
    pipeline.start = lambda run_id: None
    settings.triz.setdefault("feedback_rag", {})["enabled"] = False
    rag.lessons_block = lambda state: ""
    rag.prior_cases_block = lambda state: ""
    registry.for_run = lambda state, **kwargs: {
        "policy": None, "shadow_policy": None, "policy_version": "rules-v1",
        "effect_ranker": None, "shadow_effect_ranker": None,
        "rule_catalog": [], "rule_catalog_version": "empty-v1"}
    registry.observe_shadow = lambda *args, **kwargs: None
    registry.train_project = _forbidden_training
    worker.tick = _forbidden_training
    outbox.claim = _forbidden_training
    outbox.deliver = _forbidden_training
    feedback_events._write = _no_training_review
    feedback_events.user_decisions = lambda *args, **kwargs: []
    feedback_events.final_feedback = _forbidden_training
    store.record_feedback = _forbidden_training
    store.rag_upsert = _forbidden_training
    effect_history.observations = lambda *args, **kwargs: []
    from .tools import vector_patents
    vector_patents.ensure_collection = _forbidden_training
    vector_patents.index_pending = _forbidden_training
    from . import patent_corpus
    for name in ("init", "ingest", "acknowledge", "save_checkpoint", "_upsert"):
        setattr(patent_corpus, name, _forbidden_training)
    native_model = vector_patents.model

    def readonly_model():
        # The native embedding function, pinned ONNX weights, pooling, and
        # prefixes remain intact. Only its download resolver is replaced.
        import huggingface_hub
        snapshot_download = huggingface_hub.snapshot_download

        def existing_snapshot(repo_id, *, revision, cache_dir, allow_patterns, **kwargs):
            expected = [vector_patents.MODEL_FILE, "config.json", "tokenizer.json", "tokenizer_config.json",
                        "special_tokens_map.json", "sentencepiece.bpe.model"]
            if (repo_id != settings.patent_embedding_model or revision != vector_patents.MODEL_COMMIT
                    or allow_patterns != expected or Path(cache_dir) != settings.storage_dir / "embedding_models"):
                raise RuntimeError("Unexpected patent embedding snapshot request")
            cache = original_storage / "embedding_models"
            snapshot = cache / ("models--" + repo_id.replace("/", "--")) / "snapshots" / revision
            for name in (vector_patents.MODEL_FILE, "config.json", "tokenizer.json"):
                target = snapshot / name
                if not target.is_file() or not target.resolve().is_relative_to(cache.resolve()):
                    raise RuntimeError("Pinned patent embedding snapshot is unavailable")
            return str(snapshot)

        huggingface_hub.snapshot_download = existing_snapshot
        try:
            return native_model()
        finally:
            huggingface_hub.snapshot_download = snapshot_download

    vector_patents.model = readonly_model
    return pipeline, store, ledger, engine


def _tables(store, ledger):
    return {**store.metadata.tables, **ledger.metadata.tables}


def _dump_journal(store, ledger, engine):
    from sqlalchemy import select
    result = {}
    with engine.connect() as connection:
        for name, table in sorted(_tables(store, ledger).items()):
            query = select(table).order_by(*table.primary_key.columns)
            result[name] = [dict(row) for row in connection.execute(query).mappings()]
    return result


def _restore(continuation, fingerprint, store, ledger, engine):
    from .schema import GlobalState
    if not isinstance(continuation, dict) or continuation.get("version") != VERSION:
        raise LabInputError("Invalid lab continuation version")
    if continuation.get("contract_fingerprint") != fingerprint:
        raise LabInputError("Native TRIZ contract changed; begin a new lab run")
    state = GlobalState.model_validate(continuation.get("state"))
    if not state.run_id.startswith("lab-") or state.scratch.get("training_consent") != "NO_TRAINING":
        raise LabInputError("Invalid lab identity or training consent")
    bundle = state.scratch.get("ax_bundle", {})
    if (bundle.get("config", {}).get("feedback_rag", {}).get("enabled") is not False
            or any(bundle.get(k) for k in ("policy", "shadow_policy", "effect_ranker", "shadow_effect_ranker"))):
        raise LabInputError("Lab continuation contains a learning configuration")
    journal = continuation.get("journal")
    tables = _tables(store, ledger)
    if not isinstance(journal, dict) or set(journal) != set(tables):
        raise LabInputError("Invalid lab journal tables")
    with engine.begin() as connection:
        for name, table in tables.items():
            rows = journal[name]
            if not isinstance(rows, list):
                raise LabInputError("Invalid lab journal rows")
            for row in rows:
                if (not isinstance(row, dict) or set(row) != set(table.columns.keys())
                        or ("run_id" in row and row["run_id"] != state.run_id)):
                    raise LabInputError("Invalid lab journal row scope")
            if rows:
                connection.execute(table.insert(), rows)
    stored = store.load_state(state.run_id)
    if stored is None or stored.model_dump(mode="json") != state.model_dump(mode="json"):
        raise LabInputError("Lab state and journal disagree")
    head = ledger.head(state.run_id, state.user_id)
    if (not math.isfinite(state.cost.budget_usd) or not 0 < state.cost.budget_usd <= MAX_BUDGET_USD
            or not isinstance(head["budget"], int) or not 0 < head["budget"] <= round(MAX_BUDGET_USD * 1_000_000)
            or round(state.cost.budget_usd * 1_000_000) != head["budget"]):
        raise LabInputError("Lab continuation budget must remain within $5")
    if (head["epoch"] != state.scratch.get("execution_epoch", 0)
            or head["bundle"]["bundle_id"] != bundle.get("bundle_id")
            or head["snapshot_id"] != state.scratch.get("ax_snapshot_id")):
        raise LabInputError("Lab journal checkpoint disagrees")
    return state


def _solutions(state, ledger, engine):
    from sqlalchemy import select
    from .ax.candidate_disposition import records
    dispositions = records(state)
    candidates = {candidate.id: candidate.model_dump(mode="json") for candidate in state.concepts}
    for row in dispositions:
        if isinstance(row.get("candidate_snapshot"), dict):
            candidates.setdefault(row["candidate_id"], row["candidate_snapshot"])
    for candidate in state.scratch.get("ax_excluded", []):
        if isinstance(candidate, dict) and candidate.get("id"):
            candidates.setdefault(candidate["id"], candidate)
    for row in dispositions:
        candidates.setdefault(row["candidate_id"], {"id": row["candidate_id"]})
    with engine.connect() as connection:
        applications = {row["application_id"]: json.loads(row["payload"])
                        for row in connection.execute(select(
                            ledger.metadata.tables["ax_effect_applications"])).mappings()}
        effect_reviews = [json.loads(row["payload"]) for row in connection.execute(
            select(ledger.metadata.tables["ax_effect_reviews"])).mappings()]
    checks = {row.concept_id: row.model_dump(mode="json") for row in state.constraint_checks}
    evaluations = {row.concept_id: row.model_dump(mode="json") for row in state.evaluation.evaluations}
    selection = state.scratch.get("ax_selection", {})
    selected = set(selection.get("recommended", []))
    final_checks = {row["candidate_id"]: row for row in selection.get("candidates", [])}
    result = []
    for cid, candidate in sorted(candidates.items()):
        exclusions = [row for row in dispositions if row["candidate_id"] == cid]
        app_ids = {aid for aid, app in applications.items() if app.get("candidate_id") == cid}
        result.append(dict(concept_id=cid, candidate=candidate,
            disposition="EXCLUDED" if exclusions else "RETAINED",
            recommended=cid in selected, exclusions=exclusions,
            validation=dict(quality_status=candidate.get("quality_status", "UNVERIFIED"),
                quality_issues=candidate.get("quality_issues", []),
                constraint_check=checks.get(cid), final_selection=final_checks.get(cid),
                reviews=[r for r in state.scratch.get("lab_validation_reviews", []) if r["candidate_id"] == cid],
                effect_reviews=[r for r in effect_reviews if r.get("application_id") in app_ids]),
            evidence=[e.model_dump(mode="json") for e in state.evidence if e.id in candidate.get("evidence_ids", [])],
            evidence_mapping=state.scratch.get("evidence_mappings", {}).get(cid, {}),
            evaluation=evaluations.get(cid)))
    return result


def _inline_report(state, temp_root):
    if state.report is None:
        return None
    files = {}
    storage = temp_root / "storage"
    for path in sorted(storage.rglob("*")):
        if path.is_file() and (path.name in ("report.md", "report.html") or path.suffix == ".svg"):
            files[path.relative_to(storage).as_posix()] = path.read_text(encoding="utf-8")
    return dict(markdown=state.report.markdown, artifact=state.report.model_dump(mode="json"), files=files)


def _execute_stage(pipeline, state):
    return pipeline.execute_stage(state.run_id, state.control.stage_index,
                                  state.scratch.get("execution_epoch", 0))


def _resume_or_retry(state, payload, pipeline, store):
    response = payload.get("human_response")
    if state.pending:
        if response is None:
            return state
        if not isinstance(response, dict):
            raise LabInputError("human_response must be an object")
        response = dict(response, training_consent="NO_TRAINING")
        if response.get("interrupt_id") != state.pending.interrupt_id:
            raise LabInputError("human_response requires the current interrupt_id")
        if "application_reviews" in response:
            if not isinstance(response["application_reviews"], list) or not all(
                    isinstance(row, dict) for row in response["application_reviews"]):
                raise LabInputError("application_reviews must be a list of objects")
            response["application_reviews"] = [dict(row, training_consent="NO_TRAINING")
                                                for row in response["application_reviews"]]
        if not pipeline.resume(state.run_id, response):
            raise LabInputError("Human response did not resume the current pending request")
        return store.load_state(state.run_id)
    if response is not None:
        raise LabInputError("There is no pending human request")
    if state.status in ("FAILED", "INTERRUPTED"):
        if not pipeline.continue_run(state.run_id):
            raise LabInputError("The interrupted stage cannot continue")
        return store.load_state(state.run_id)
    return state


def _response(state, pipeline, store, ledger, engine, fingerprint, temp_root, error=None, traces=()):
    index = state.control.stage_index
    next_key = pipeline.PIPELINE[index][0] if index < len(pipeline.PIPELINE) else None
    steps = [step.model_dump(mode="json") for step in state.steps]
    solutions = _solutions(state, ledger, engine)
    result = dict(status=state.status, run_id=state.run_id,
        next_stage_key=next_key, stage_index=index,
        continue_execution=not error and state.status in ("CREATED", "RUNNING", "QUEUED") and not state.pending and next_key is not None,
        pending=state.pending.model_dump(mode="json") if state.pending else None,
        stage_outputs={name: getattr(state, name).model_dump(mode="json") for name in
                       ("domain", "intake", "confirm", "analysis", "definition", "solve", "evaluation")},
        steps=steps, solutions=solutions,
        cost=state.cost.model_dump(mode="json"), budget=ledger.budget(state.run_id, state.user_id),
        report=_inline_report(state, temp_root),
        diagnostics=dict(reason=state.scratch.get("interruption_reason"), errors=state.control.errors[-5:], traces=list(traces)),
        continuation_payload=dict(version=VERSION, contract_fingerprint=fingerprint,
            state=state.model_dump(mode="json"), journal=_dump_journal(store, ledger, engine), solutions=solutions))
    if error:
        result["error"] = error
        result["continue_execution"] = False
    return result


class _TraceHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.traces = []

    def emit(self, record):
        if record.exc_info:
            self.traces.append(dict(error_type=record.exc_info[0].__name__, frames=[
                dict(file=Path(frame.filename).name, line=frame.lineno, function=frame.name)
                for frame in traceback.extract_tb(record.exc_info[2])]))


def run(payload):
    """Execute begin or exactly one current native stage; never dispatch a run."""
    global _USED
    if _USED:
        raise RuntimeError("Use a fresh process for every lab invocation")
    _USED = True
    if not isinstance(payload, dict) or payload.get("action") not in ("begin", "stage"):
        return dict(status="INVALID_REQUEST", error="action must be begin or stage", continue_execution=False,
                    continuation_payload=None, next_stage_key=None, pending=None, stage_outputs={}, steps=[], solutions=[])
    budget = payload.get("budget_usd", MAX_BUDGET_USD)
    if (isinstance(budget, bool) or not isinstance(budget, (int, float))
            or not math.isfinite(budget) or not 0 < budget <= MAX_BUDGET_USD):
        return dict(status="INVALID_REQUEST", error="budget_usd must be finite, greater than $0 and at most $5",
                    continue_execution=False, continuation_payload=None, next_stage_key=None,
                    pending=None, stage_outputs={}, steps=[], solutions=[])
    budget = float(budget)
    ram = Path("/dev/shm")
    directory = str(ram) if ram.is_dir() and os.access(ram, os.W_OK) else None
    fingerprint = contract_fingerprint()
    engine = None
    handler = _TraceHandler()
    logger = logging.getLogger("triz.pipeline")
    logger.addHandler(handler)
    try:
        with tempfile.TemporaryDirectory(prefix="triz-lab-", dir=directory) as folder:
            temp_root = Path(folder)
            # Native diagnostics must not corrupt the stdout JSON protocol.
            with redirect_stdout(sys.stderr):
                pipeline, store, ledger, engine = _initialize(temp_root, budget)
                state = None
                try:
                    if payload["action"] == "begin":
                        if payload.get("continuation_payload") is not None:
                            state = _restore(payload["continuation_payload"], fingerprint, store, ledger, engine)
                            state = _resume_or_retry(state, payload, pipeline, store)
                        else:
                            if payload.get("human_response") is not None:
                                raise LabInputError("A human response requires a continuation")
                            from .ax import WORKFLOW
                            mode = payload.get("mode") or "STANDARD"
                            mode = {"QUICK":"LITE", "STANDARD":"FULL"}.get(mode, mode)
                            state = pipeline.create_run(payload.get("raw_query", ""), mode=mode,
                                user_id="lab-user", run_id="lab-" + uuid.uuid4().hex,
                                workflow_version=WORKFLOW, training_consent="NO_TRAINING")
                    else:
                        state = _restore(payload.get("continuation_payload"), fingerprint, store, ledger, engine)
                        index = state.control.stage_index
                        expected = pipeline.PIPELINE[index][0] if index < len(pipeline.PIPELINE) else None
                        if expected is None or payload.get("stage_key") != expected:
                            raise LabInputError("stage_key must match the exact next_stage_key")
                        state = _resume_or_retry(state, payload, pipeline, store)
                        if state.pending:
                            return _response(state, pipeline, store, ledger, engine, fingerprint, temp_root)
                        _execute_stage(pipeline, state)
                        state = store.load_state(state.run_id)
                    return _response(state, pipeline, store, ledger, engine, fingerprint, temp_root, traces=handler.traces)
                except (LabInputError, ValueError, KeyError) as exc:
                    if state is not None:
                        return _response(state, pipeline, store, ledger, engine, fingerprint, temp_root,
                                         error=str(exc), traces=handler.traces)
                    return dict(status="INVALID_REQUEST", error=str(exc), continue_execution=False,
                        continuation_payload=None, next_stage_key=None, pending=None, stage_outputs={}, steps=[], solutions=[])
    finally:
        if engine is not None:
            engine.dispose()
        logger.removeHandler(handler)


def main():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        payload = json.load(sys.stdin)
        result = run(payload)
    except Exception as exc:
        # Exception messages/provider internals belong on stderr, not wire state.
        traceback.print_exc(file=sys.stderr)
        result = dict(status="INVALID_REQUEST" if isinstance(exc, LabInputError) else "FAILED",
            error=str(exc) if isinstance(exc, LabInputError) else type(exc).__name__, continue_execution=False,
            continuation_payload=None, next_stage_key=None, pending=None, stage_outputs={}, steps=[], solutions=[])
    json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
