"""Explicit, auditable price corrections without rewriting provider receipts.

A correction changes the effective estimate from its recorded availability time.
It does not create calls, change token counts, rewrite feedback, or publish a Q model.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update, func

from .. import model_pricing, store
from . import ledger
from .contracts import canonical, digest, now, Conflict

VERSION = 'cost-restatement-v1'
EVENT = 'COST_RESTATEMENT_APPLIED'
MAX_TASKS = 10000


def overrides(connection, run_id, cutoff=None):
    query = select(ledger.events.c.payload).where(ledger.events.c.run_id == run_id,
                                                 ledger.events.c.event_type == EVENT)
    if cutoff:
        query = query.where(ledger.events.c.created_at <= cutoff)
    result = {}
    for payload in connection.execute(query.order_by(ledger.events.c.created_at, ledger.events.c.event_id)).scalars():
        event = json.loads(payload)
        if event.get('version') != VERSION:
            continue
        for row in event.get('task_adjustments', []):
            value = row['after_microusd']
            if type(value) is not int or value < 0:
                raise ValueError('Invalid recorded price correction')
            result[row['task_id']] = value
    return result


def effective(actual, task_id, corrections):
    return None if actual is None else corrections.get(task_id, actual)


def available_at(connection, run_id, cutoff=None):
    query = select(func.max(ledger.events.c.created_at)).where(ledger.events.c.run_id == run_id,
                                                              ledger.events.c.event_type == EVENT)
    if cutoff:
        query = query.where(ledger.events.c.created_at <= cutoff)
    return connection.execute(query).scalar_one() or ''


def _parse(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def _time(value):
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _stage(node, created_at, steps):
    point = _time(created_at)
    containing = [s for s in steps if s['started_at'] and s['ended_at']
                  and _time(s['started_at']) <= point <= _time(s['ended_at'])]
    exact = {s['stage'] for s in containing if s['node'] == node}
    stages = exact or {s['stage'] for s in containing}
    if len(stages) == 1:
        return next(iter(stages)), 'recorded_stage_interval'
    # Only explicit pipeline node names have a stage contract. A generic
    # verifier in overlapping stages remains unattributed, never guessed.
    prefixes = (('s0_bootstrap', 'S0_BOOTSTRAP'), ('s0_research', 'S0_RESEARCH'),
                ('s1_', 'S1_INTAKE'), ('s2_', 'S2_CONFIRM'), ('s3_', 'S3_ANALYZE'),
                ('s4_', 'S4_DEFINE'), ('s5_', 'S5_SOLVE'), ('s6_', 'S6_CONCEPT'),
                ('s7_', 'S7_CONSTRAINT'), ('s8_refer', 'S8_REFERENCES'),
                ('s8_review', 'S8_EVALUATE'), ('s8_rank', 'S8_EVALUATE'),
                ('s8_persona', 'S8_EVALUATE'), ('s9_', 'S9_REPORT'), ('s10_', 'S10_FEEDBACK'))
    for prefix, stage in prefixes:
        if node.startswith(prefix):
            return stage, 'node_stage_contract'
    return 'UNATTRIBUTED', 'no_unique_recorded_stage'


def _sources(connection, run_id):
    """Only usage/configuration projections cross the MySQL boundary."""
    tasks = ledger.tasks
    fields = [tasks.c.task_id, tasks.c.fence, tasks.c.status, tasks.c.actual,
              tasks.c.reserve, tasks.c.created_at]
    mysql = connection.dialect.name == 'mysql'
    if mysql:
        fields += [func.json_extract(tasks.c.result, path).label(label) for label, path in (
            ('normal_usages', '$.meta.requests[*].usage'), ('failure_usages', '$.usage.meta.requests[*].usage'),
            ('normal_model', '$.model'), ('failure_model', '$.usage.model'))]
        fields += [func.json_length(func.json_extract(tasks.c.result, path)).label(label)
                   for label, path in (('normal_count', '$.meta.requests'), ('failure_count', '$.usage.meta.requests'))]
    else:
        fields.append(tasks.c.result)
    rows = [dict(row) for row in connection.execute(select(*fields).where(tasks.c.run_id == run_id)
                                                   .order_by(tasks.c.task_id).limit(MAX_TASKS+1)).mappings()]
    if len(rows) > MAX_TASKS:
        raise ValueError('Price correction task bound exceeded')
    pins = {}
    for row in connection.execute(select(ledger.attempts.c.task_id, ledger.attempts.c.fence,
            func.json_extract(ledger.attempts.c.details, '$.request.request.model_config').label('config'),
            func.json_extract(ledger.attempts.c.details, '$.request.request.tier').label('tier'),
            func.json_extract(ledger.attempts.c.details, '$.request.node').label('node'))
            .where(ledger.attempts.c.run_id == run_id)).mappings():
        config = _parse(row['config']) or {}
        pins[(row['task_id'], row['fence'])] = {
            'config': {k: config[k] for k in ('model', 'base_url', 'cost_in', 'cost_out', 'cost_cache_in') if k in config},
            'tier': _parse(row['tier']) or 'UNATTRIBUTED', 'node': _parse(row['node']) or ''}
    for row in rows:
        if not mysql:
            result = json.loads(row.pop('result') or '{}')
            receipt = result if result.get('meta', {}).get('requests') else result.get('usage') or {}
            records = receipt.get('meta', {}).get('requests', [])
            row.update(usages=[r.get('usage', {}) for r in records], request_count=len(records), model=receipt.get('model'))
        else:
            prefix = 'normal' if row['normal_count'] else 'failure'
            row.update(usages=_parse(row[prefix+'_usages']) or [], request_count=row[prefix+'_count'] or 0,
                       model=_parse(row[prefix+'_model']))
            for key in ('normal_usages', 'failure_usages', 'normal_count', 'failure_count', 'normal_model', 'failure_model'):
                row.pop(key)
        row.update(pins.get((row['task_id'], row['fence']), {'config':{}, 'tier':'UNATTRIBUTED', 'node':''}))
    return rows


def _plan(connection, run_id, actor):
    head = ledger._head(connection, run_id)
    ledger.authorize(head, actor)
    row = connection.execute(select(store.runs.c.status, store.runs.c.ended_at, store.states.c.state_json)
        .join(store.states, store.states.c.run_id == store.runs.c.run_id)
        .where(store.runs.c.run_id == run_id)).mappings().one()
    state = json.loads(row['state_json'])
    steps = [dict(s) for s in connection.execute(select(store.steps.c.node, store.steps.c.stage,
        store.steps.c.started_at, store.steps.c.ended_at).where(store.steps.c.run_id == run_id)).mappings()]
    sources = _sources(connection, run_id)
    corrections = overrides(connection, run_id)
    by_tier, by_stage, excluded = defaultdict(int), defaultdict(int), Counter()
    changes, fingerprints = [], []
    before = after = 0
    unknown = 0
    for task in sources:
        tid = task['task_id']
        source_hash = digest(task)
        fingerprints.append([tid, source_hash])
        if task['actual'] is None:
            unknown += 1
            continue
        old = effective(task['actual'], tid, corrections)
        corrected = old
        cfg = task['config']
        eligible = {'model','base_url','cost_in','cost_out'}.issubset(cfg) and model_pricing.resolve(cfg).get('basis') == model_pricing.FLASH_BASIS
        if not eligible:
            excluded['other_model_or_unpinned'] += 1
        elif task['model'] != cfg['model']:
            excluded['provider_model_mismatch'] += 1
        elif not task['request_count'] or len(task['usages']) != task['request_count']:
            excluded['incomplete_usage'] += 1
        else:
            try:
                charges = [model_pricing.calculate(u, model_pricing.resolve(cfg)) for u in task['usages']]
            except model_pricing.ProviderUsageError:
                excluded['invalid_usage'] += 1
            else:
                corrected = model_pricing.to_microusd(sum((Decimal(x['cost_usd']) for x in charges), Decimal(0)))
                stage, attribution = _stage(task['node'], task['created_at'], steps)
                changes.append(dict(task_id=tid, original_microusd=task['actual'], before_microusd=old,
                    after_microusd=corrected, receipt_hash=source_hash, tier=task['tier'], stage=stage,
                    stage_attribution=attribution, created_at=task['created_at'], charges=charges))
        stage, _ = _stage(task['node'], task['created_at'], steps)
        by_tier[task['tier']] += corrected
        by_stage[stage] += corrected
        before += old
        after += corrected
    source_fingerprint = digest([head['epoch'], head['revision'], fingerprints])
    event_id = 'cost-restatement-' + digest([run_id, model_pricing.FLASH_BASIS, source_fingerprint])[:48]
    current_cost = state['cost']
    after_cost = dict(current_cost, total_usd=after/1e6, by_tier={k:v/1e6 for k,v in by_tier.items()},
        by_stage={k:v/1e6 for k,v in by_stage.items()}, over_budget=after/1e6 > current_cost['budget_usd'])
    return dict(version=VERSION, event_id=event_id, run_id=run_id, source_epoch=head['epoch'],
        source_revision=head['revision'], source_fingerprint=source_fingerprint,
        basis=model_pricing.FLASH_BASIS, source_url=model_pricing.SOURCE_URL,
        run_status=row['status'], state_status=state['status'], ended_at=row['ended_at'],
        before_microusd=before, after_microusd=after, delta_microusd=after-before,
        task_count=len(sources), unknown_tasks=unknown, excluded=dict(excluded),
        task_adjustments=changes, before_cost=current_cost, after_cost=after_cost,
        report_snapshot_id=state.get('scratch', {}).get('ax_report_snapshot_id'),
        original_receipts_preserved=True, original_step_prices_preserved=True)


def plan(run_id, actor):
    with store.engine.connect() as connection:
        return _plan(connection, run_id, actor)


def apply(expected, actor):
    """Apply only a reviewed plan for a completed, unchanged project."""
    # Resume/replan reads state before taking the AX head row lock. Use its
    # cross-worker run lock too, so it cannot later save a stale cost projection.
    with store.run_lock(expected['run_id']):
        return _apply_locked(expected, actor)


def _apply_locked(expected, actor):
    run_id = expected['run_id']
    with ledger.transaction() as connection:
        head = ledger._head(connection, run_id, lock=True)
        ledger.authorize(head, actor)
        saved = connection.execute(select(ledger.events.c.payload).where(
            ledger.events.c.run_id == run_id, ledger.events.c.event_id == expected['event_id'],
            ledger.events.c.event_type == EVENT)).scalar_one_or_none()
        if saved:
            return json.loads(saved)
        connection.execute(select(store.runs.c.run_id).where(store.runs.c.run_id == run_id).with_for_update()).one()
        raw_state = connection.execute(select(store.states.c.state_json).where(
            store.states.c.run_id == run_id).with_for_update()).scalar_one()
        current = _plan(connection, run_id, actor)
        if current['run_status'] != 'COMPLETED' or current['state_status'] != 'COMPLETED':
            raise Conflict('Cost correction requires a completed project')
        if current['unknown_tasks'] or any(row['status'] in ('RUNNING', 'UNKNOWN') for row in _sources(connection, run_id)):
            raise Conflict('Unsettled calls must be reconciled before price correction')
        if (current['source_fingerprint'] != expected['source_fingerprint'] or
                current['after_microusd'] != expected['after_microusd'] or
                current['before_cost'] != expected['before_cost']):
            raise Conflict('Price correction source changed; review a fresh plan')
        if abs(Decimal(str(current['before_cost']['total_usd']))*1_000_000-current['before_microusd']) > 1:
            raise Conflict('Project total and paid-call ledger do not reconcile')
        current['applied_at'] = now()
        ledger._event(connection, run_id, EVENT, current, event_id=current['event_id'])
        state = json.loads(raw_state)
        state['cost'] = current['after_cost']
        state.setdefault('scratch', {})['cost_restatement'] = {key:current[key] for key in (
            'event_id', 'basis', 'applied_at', 'source_epoch', 'report_snapshot_id',
            'before_microusd', 'after_microusd', 'after_cost', 'original_step_prices_preserved')}
        connection.execute(update(store.states).where(store.states.c.run_id == run_id)
            .values(state_json=canonical(state), updated_at=current['applied_at']))
        # Preserve project completion time, steps, snapshots, reviews and receipts.
        connection.execute(update(store.runs).where(store.runs.c.run_id == run_id)
            .values(cost_usd=current['after_cost']['total_usd']))
        return current


def report_cost(state, snapshot_id, original):
    correction = state.scratch.get('cost_restatement') or {}
    if snapshot_id and correction.get('report_snapshot_id') == snapshot_id and correction.get('event_id'):
        return correction['after_cost']
    return original
