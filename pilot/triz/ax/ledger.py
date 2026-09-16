"""Additive MySQL/SQLite journal. No external call holds a row transaction open.

Artifacts, snapshots, events and reviews are immutable. Only heads, leases and
delivery acknowledgements are mutable. Every read is scoped to a run owner.
"""
from contextlib import contextmanager
import json
import time
import uuid
from sqlalchemy import (MetaData, Table, Column, String, Integer, BigInteger,
                        Text, Double, Index, UniqueConstraint, select, update, func, inspect)
from sqlalchemy.dialects.mysql import LONGTEXT
from .. import store
from .contracts import canonical, digest, now, Conflict, AccessDenied, Review, BudgetBusy

metadata = MetaData()
JSON = Text().with_variant(LONGTEXT(), 'mysql')


def table(name, *columns, **kw):
    return Table('ax_' + name, metadata, *columns, mysql_charset='utf8mb4', **kw)


heads = table('runs', Column('run_id', String(64), primary_key=True),
    Column('owner_id', String(64), nullable=False), Column('tenant_id', String(64), nullable=False),
    Column('project_id', String(64), nullable=False), Column('epoch', Integer, nullable=False),
    Column('revision', Integer, nullable=False), Column('snapshot_id', String(80)),
    Column('bundle', JSON, nullable=False), Column('budget', BigInteger, nullable=False))
artifacts = table('artifact_versions', Column('version_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('artifact_key', String(180), nullable=False),
    Column('epoch', Integer, nullable=False), Column('content_hash', String(64), nullable=False),
    Column('payload', JSON, nullable=False), Column('parents', JSON, nullable=False),
    Column('supersedes', String(80)), Column('created_at', String(40), nullable=False),
    Column('available_at', String(40), nullable=False), Column('provenance', JSON, nullable=False))
edges = table('artifact_edges', Column('parent_id', String(80), primary_key=True),
    Column('child_id', String(80), primary_key=True), Column('relation', String(32), primary_key=True),
    Column('run_id', String(64), nullable=False))
snapshots = table('snapshots', Column('snapshot_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('epoch', Integer, nullable=False),
    Column('members', JSON, nullable=False), Column('manifest_hash', String(64), nullable=False),
    Column('created_at', String(40), nullable=False), Column('reason', String(180), nullable=False))
tasks = table('tasks', Column('task_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('epoch', Integer, nullable=False),
    Column('input_snapshot', String(80)), Column('input_hash', String(64), nullable=False),
    Column('status', String(32), nullable=False), Column('fence', Integer, nullable=False),
    Column('lease_until', Double, nullable=False), Column('result', JSON),
    Column('reserve', BigInteger, nullable=False), Column('actual', BigInteger),
    Column('created_at', String(40), nullable=False), Column('settled_at', String(40)))
attempts = table('task_attempts', Column('attempt_id', String(100), primary_key=True),
    Column('task_id', String(80), nullable=False), Column('run_id', String(64), nullable=False),
    Column('fence', Integer, nullable=False), Column('status', String(32), nullable=False),
    Column('details', JSON, nullable=False), UniqueConstraint('task_id', 'fence'))
decisions = table('decisions', Column('decision_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('snapshot_id', String(80), nullable=False),
    Column('epoch', Integer, nullable=False), Column('payload', JSON, nullable=False),
    Column('created_at', String(40), nullable=False))
reviews = table('reviews', Column('event_id', String(100), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('actor_id', String(64), nullable=False),
    Column('payload', JSON, nullable=False), Column('content_hash', String(64), nullable=False),
    Column('created_at', String(40), nullable=False))
events = table('events', Column('event_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('event_type', String(80), nullable=False),
    Column('payload', JSON, nullable=False), Column('created_at', String(40), nullable=False))
outbox = table('outbox', Column('event_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('status', String(24), nullable=False),
    Column('claim_token', String(80)), Column('lease_until', Double, nullable=False),
    Column('delivered_at', String(40)))
for name, t, columns in [('artifact_run', artifacts, ('run_id','artifact_key')),
                        ('snapshot_run', snapshots, ('run_id','created_at')),
                        ('task_run', tasks, ('run_id','status')),
                        ('decision_run', decisions, ('run_id','created_at')),
                        ('review_run', reviews, ('run_id','created_at')),
                        ('outbox_pending', outbox, ('status','lease_until'))]:
    Index('ix_ax_' + name, *[t.c[c] for c in columns])


def init():
    from . import outbox  # Register additive consumer tables before schema creation.
    from . import registry
    from . import worker
    metadata.create_all(store.engine)
    if store.engine.dialect.name == 'mysql':
        # MySQL FLOAT cannot round-trip Unix epoch seconds accurately enough for
        # a 60-second lease. Upgrade only these two AX fields; retain all rows.
        schema=inspect(store.engine)
        for name in ('ax_tasks','ax_outbox'):
            column=next(c for c in schema.get_columns(name) if c['name']=='lease_until')
            if str(column['type']).upper().startswith('FLOAT'):
                with store.engine.begin() as c:
                    c.exec_driver_sql(f'ALTER TABLE {name} MODIFY COLUMN lease_until DOUBLE NOT NULL')


@contextmanager
def transaction():
    with store.engine.connect() as c:
        if c.dialect.name == 'sqlite':
            c.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            c.begin()
        try:
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise


def _head(c, run_id, *, lock=False):
    q = select(heads).where(heads.c.run_id == run_id)
    row = c.execute(q.with_for_update() if lock else q).mappings().first()
    if not row:
        raise ValueError('AX run not found')
    return dict(row)


def authorize(head, actor):
    if actor != head['owner_id']:
        raise AccessDenied('Run not found')


def head(run_id, actor=None):
    with store.engine.connect() as c:
        result = _head(c, run_id)
    if actor is not None:
        authorize(result, actor)
    result['bundle'] = json.loads(result['bundle'])
    return result


def _event(c, run_id, kind, payload, event_id=None):
    event_id = event_id or 'event-' + uuid.uuid4().hex
    c.execute(events.insert().values(event_id=event_id, run_id=run_id, event_type=kind,
                                     payload=canonical(payload), created_at=now()))
    c.execute(outbox.insert().values(event_id=event_id, run_id=run_id, status='PENDING', lease_until=0))
    return event_id


def bootstrap(state, bundle):
    init()
    with transaction() as c:
        if c.execute(select(heads.c.run_id).where(heads.c.run_id == state.run_id)).first():
            return head(state.run_id)
        c.execute(heads.insert().values(run_id=state.run_id, owner_id=state.user_id,
            tenant_id=state.user_id, project_id=state.scratch.get('ax_project_id',state.user_id), epoch=state.scratch.get('execution_epoch',0),
            revision=0, bundle=canonical(bundle), budget=round(state.cost.budget_usd * 1_000_000)))
        _event(c, state.run_id, 'RUN_CREATED', {'bundle_id': bundle['bundle_id']})


def _members(c, h):
    if not h['snapshot_id']:
        return {}
    return json.loads(c.execute(select(snapshots.c.members).where(
        snapshots.c.snapshot_id == h['snapshot_id'])).scalar_one())


def capture(state, sections, dependencies, reason, *, invalidated=(), projection=True):
    """Commit typed section deltas, exact snapshot and compatible state together."""
    with transaction() as c:
        h = _head(c, state.run_id, lock=True)
        epoch = state.scratch.get('execution_epoch', 0)
        if h['epoch'] != epoch:
            raise Conflict('Stale execution epoch')
        members = _members(c, h)
        prior_members = dict(members)
        for key in invalidated:
            members.pop(key, None)
        changed = []
        for key, payload in sections.items():
            parents = [members[p] for p in dependencies.get(key, ()) if p in members]
            old = c.execute(select(artifacts).where(artifacts.c.version_id == members.get(key))).mappings().first()
            content_hash = digest(payload)
            if old and old['content_hash'] == content_hash and json.loads(old['parents']) == parents:
                continue
            version = 'av-' + uuid.uuid4().hex
            c.execute(artifacts.insert().values(version_id=version, run_id=state.run_id, artifact_key=key,
                epoch=epoch, content_hash=content_hash, payload=canonical(payload), parents=canonical(parents),
                supersedes=prior_members.get(key), created_at=now(), available_at=now(),
                provenance=canonical({'workflow':state.scratch['workflow_version'],
                    'bundle_id':json.loads(h['bundle'])['bundle_id'], 'reason':reason,
                    'decision_id':state.scratch.get('ax_last_decision'),
                    'evidence_status':'ASSERTED', 'approval_status':'UNREVIEWED'})))
            for parent in parents:
                c.execute(edges.insert().values(parent_id=parent, child_id=version, relation='depends_on',run_id=state.run_id))
            members[key] = version
            changed.append(version)
        manifest_hash = digest(members)
        old_epoch=c.execute(select(snapshots.c.epoch).where(snapshots.c.snapshot_id==h['snapshot_id'])).scalar() if h['snapshot_id'] else None
        if members == prior_members and not invalidated and h['snapshot_id'] and old_epoch==epoch:
            sid = h['snapshot_id']
        else:
            sid = 'snap-' + uuid.uuid4().hex
            c.execute(snapshots.insert().values(snapshot_id=sid,run_id=state.run_id,epoch=epoch,
                members=canonical(members),manifest_hash=manifest_hash,created_at=now(),reason=reason))
            _event(c,state.run_id,'SNAPSHOT_COMMITTED',{'snapshot_id':sid,'versions':changed,'invalidated':list(invalidated)})
        c.execute(update(heads).where(heads.c.run_id==state.run_id).values(snapshot_id=sid,revision=h['revision']+1))
        state.scratch['ax_snapshot_id'] = sid
        state.scratch['ax_members'] = members
        if projection:
            store._save_state_db(c,state)
    return sid


def advance_epoch(state, reason):
    with transaction() as c:
        h = _head(c,state.run_id,lock=True)
        epoch = state.scratch['execution_epoch']
        if epoch != h['epoch'] + 1:
            raise Conflict('Epoch must advance exactly once')
        c.execute(update(heads).where(heads.c.run_id==state.run_id).values(epoch=epoch,revision=h['revision']+1))
        c.execute(update(tasks).where(tasks.c.run_id==state.run_id,tasks.c.status=='RUNNING').values(status='UNKNOWN'))
        _event(c,state.run_id,'EPOCH_CHANGED',{'previous':h['epoch'],'epoch':epoch,'reason':reason})
        store._save_state_db(c,state)


def snapshot(run_id, snapshot_id, actor):
    h = head(run_id,actor)
    with store.engine.connect() as c:
        row = c.execute(select(snapshots).where(snapshots.c.snapshot_id==snapshot_id,
                                               snapshots.c.run_id==run_id)).mappings().first()
        if not row:
            raise ValueError('Snapshot not found')
        result = dict(row)
        result['members'] = json.loads(result['members'])
        result['artifacts'] = {key: _artifact(c,run_id,vid) for key,vid in result['members'].items()}
        result['is_current'] = snapshot_id == h['snapshot_id'] and row['epoch']==h['epoch']
        return result


def _artifact(c,run_id,version_id):
    row=c.execute(select(artifacts).where(artifacts.c.run_id==run_id,
                                         artifacts.c.version_id==version_id)).mappings().first()
    if not row:
        raise ValueError('Artifact not found')
    result=dict(row)
    for key in ('payload','parents','provenance'):
        result[key]=json.loads(result[key])
    if digest(result['payload'])!=result['content_hash']:
        raise ValueError('Artifact hash mismatch')
    return result


def artifact(run_id,version_id,actor):
    head(run_id,actor)
    with store.engine.connect() as c:
        result=_artifact(c,run_id,version_id)
        result['children']=list(c.execute(select(edges.c.child_id).where(edges.c.run_id==run_id,
                                                        edges.c.parent_id==version_id)).scalars())
        return result


def budget(run_id,actor=None):
    h=head(run_id,actor)
    with store.engine.connect() as c:
        rows=c.execute(select(tasks.c.status,tasks.c.reserve,tasks.c.actual).where(tasks.c.run_id==run_id)).all()
    actual=sum(r.actual or 0 for r in rows)
    reserved=sum(r.reserve for r in rows if r.status in ('RUNNING','UNKNOWN'))
    return {'limit_microusd':h['budget'],'spent_microusd':actual,'reserved_microusd':reserved,
            'remaining_microusd':max(0,h['budget']-actual-reserved),
            'unknown_attempts':sum(r.status=='UNKNOWN' for r in rows)}


def acquire(run_id,epoch,request,reserve,lease_seconds=1800,*,minimum_remaining=0):
    task_id='task-'+digest([run_id,epoch,request])[:60]
    with transaction() as c:
        h=_head(c,run_id,lock=True)
        if epoch!=h['epoch']:
            raise Conflict('Stale action epoch')
        old=c.execute(select(tasks).where(tasks.c.task_id==task_id)).mappings().first()
        if old:
            if old['status']=='COMPLETED':
                return dict(old,cached=True,result=json.loads(old['result']))
            if old['status']=='RUNNING' and old['lease_until']<time.time():
                # No automatic second paid attempt after an ambiguous process loss.
                c.execute(update(tasks).where(tasks.c.task_id==task_id).values(status='UNKNOWN'))
                _event(c,run_id,'USAGE_UNKNOWN',{'task_id':task_id})
                return {'task_id':task_id,'blocked':'UNKNOWN'}
            return {'task_id':task_id,'blocked':old['status']}
        rows=c.execute(select(tasks.c.status,tasks.c.reserve,tasks.c.actual).where(tasks.c.run_id==run_id)).all()
        used=sum((r.actual or 0)+(r.reserve if r.status in ('RUNNING','UNKNOWN') else 0) for r in rows)
        if reserve<0 or used+reserve+minimum_remaining>h['budget']:
            committed=sum((r.actual or 0)+(r.reserve if r.status=='UNKNOWN' else 0) for r in rows)
            if reserve>=0 and committed+reserve+minimum_remaining<=h['budget'] and any(r.status=='RUNNING' for r in rows):
                raise BudgetBusy('Waiting for in-flight cost reservations to settle')
            raise Conflict('Insufficient budget; required validation reserve retained')
        record=dict(task_id=task_id,run_id=run_id,epoch=epoch,input_snapshot=h['snapshot_id'],
            input_hash=digest(request),status='RUNNING',fence=1,lease_until=time.time()+lease_seconds,
            reserve=reserve,created_at=now())
        c.execute(tasks.insert().values(**record))
        c.execute(attempts.insert().values(attempt_id=task_id+'-1',task_id=task_id,run_id=run_id,
            fence=1,status='RUNNING',details=canonical({'request':request,'snapshot_id':h['snapshot_id']})))
        _event(c,run_id,'ACTION_RESERVED',{'task_id':task_id,'reserve':reserve})
        return dict(record,cached=False)


def settle(task, result, actual=None, *, status='COMPLETED'):
    with transaction() as c:
        h=_head(c,task['run_id'],lock=True)
        old=c.execute(select(tasks).where(tasks.c.task_id==task['task_id'])).mappings().one()
        if old['status']=='COMPLETED':
            return json.loads(old['result'])
        if old['fence']!=task['fence'] or (old['status']!='RUNNING' and not (old['status']=='UNKNOWN' and actual is not None)):
            raise Conflict('Stale task lease')
        stale=(h['epoch']!=task['epoch'] or h['snapshot_id']!=task['input_snapshot'])
        final_status='STALE' if stale and actual is not None else status
        c.execute(update(tasks).where(tasks.c.task_id==task['task_id']).values(
            status=final_status,result=canonical(result),actual=actual,settled_at=now()))
        previous=c.execute(select(attempts.c.details).where(attempts.c.task_id==task['task_id'],attempts.c.fence==task['fence'])).scalar_one()
        c.execute(update(attempts).where(attempts.c.task_id==task['task_id'],attempts.c.fence==task['fence']).values(
            status=final_status,details=canonical({**json.loads(previous),'result':result,'actual_microusd':actual})))
        _event(c,task['run_id'],'ACTION_'+final_status,{'task_id':task['task_id'],'actual_microusd':actual})
    if stale:
        raise Conflict('Result retained for accounting but input snapshot has changed')
    return result


def record_decision(state,payload):
    with transaction() as c:
        h=_head(c,state.run_id,lock=True)
        if h['epoch']!=state.scratch.get('execution_epoch',0) or h['snapshot_id']!=payload['snapshot_id']:
            raise Conflict('Decision read set is stale')
        did='dec-'+digest([state.run_id,h['epoch'],payload])[:60]
        prior=c.execute(select(decisions.c.decision_id).where(decisions.c.decision_id==did)).first()
        if not prior:
            c.execute(decisions.insert().values(decision_id=did,run_id=state.run_id,snapshot_id=h['snapshot_id'],
                epoch=h['epoch'],payload=canonical(payload),created_at=now()))
            _event(c,state.run_id,'DECISION_RECORDED',{'decision_id':did})
        return did


def submit_review(run_id,actor,body):
    body=Review.model_validate(body)
    payload=body.model_dump(mode='json')
    fingerprint=digest(payload)
    with transaction() as c:
        h=_head(c,run_id,lock=True)
        authorize(h,actor)
        old=c.execute(select(reviews).where(reviews.c.event_id==body.event_id)).mappings().first()
        if old:
            if old['run_id']!=run_id or old['actor_id']!=actor or old['content_hash']!=fingerprint:
                raise Conflict('Review event id already has different content')
            return {'event_id':body.event_id,'duplicate':True}
        if h['epoch']!=body.expected_epoch or h['snapshot_id']!=body.snapshot_id:
            raise Conflict('Review snapshot changed; reload the current snapshot and compare versions')
        members=_members(c,h)
        if body.target_version_id not in members.values():
            raise Conflict('Review target is not in the visible snapshot')
        target=_artifact(c,run_id,body.target_version_id)
        if body.candidate_id:
            candidates=target['payload'].get('candidates',[])
            candidate=next((x for x in candidates if x.get('id')==body.candidate_id),None)
            if not candidate:
                raise Conflict('Candidate is not in the reviewed version')
            if body.obligation_id and body.obligation_id not in [
                body.candidate_id+':test:'+str(i) for i in range(len(candidate.get('validation_plan',[])))]:
                raise Conflict('Unknown validation obligation')
        if body.decision_id:
            decision=c.execute(select(decisions).where(decisions.c.run_id==run_id,
                decisions.c.decision_id==body.decision_id)).mappings().first()
            if not decision:
                raise Conflict('Unknown decision')
            todo=[body.target_version_id]; seen=set(); causal=False
            while todo:
                version=todo.pop()
                if version in seen: continue
                seen.add(version)
                item=_artifact(c,run_id,version)
                causal |= item['provenance'].get('decision_id')==body.decision_id
                todo.extend(item['parents'])
            if not causal:
                raise Conflict('Review target was not produced by this decision or its descendants')
        if body.supersedes_event_id:
            prior=c.execute(select(reviews).where(reviews.c.event_id==body.supersedes_event_id,
                reviews.c.run_id==run_id,reviews.c.actor_id==actor)).mappings().first()
            if not prior or json.loads(prior['payload'])['target_version_id']!=body.target_version_id:
                raise Conflict('Review supersedes an unrelated event')
            following=c.execute(select(reviews.c.payload).where(reviews.c.run_id==run_id)).scalars()
            if any(json.loads(p).get('supersedes_event_id')==body.supersedes_event_id for p in following):
                raise Conflict('Review revision was already superseded')
        c.execute(reviews.insert().values(event_id=body.event_id,run_id=run_id,actor_id=actor,
            payload=canonical(payload),content_hash=fingerprint,created_at=now()))
        _event(c,run_id,'REVIEW_CONFIRMED',{'review_id':body.event_id})
        return {'event_id':body.event_id,'duplicate':False,'applied_to_artifact':False}


def decision_history(run_id,actor):
    head(run_id,actor)
    with store.engine.connect() as c:
        return [dict(r,payload=json.loads(r['payload'])) for r in c.execute(select(decisions)
            .where(decisions.c.run_id==run_id).order_by(decisions.c.created_at)).mappings()]


def active_reviews(run_id, actor):
    head(run_id,actor)
    with store.engine.connect() as c:
        rows=[dict(r,payload=json.loads(r['payload'])) for r in c.execute(select(reviews)
              .where(reviews.c.run_id==run_id).order_by(reviews.c.created_at)).mappings()]
    superseded={r['payload'].get('supersedes_event_id') for r in rows}
    return [r for r in rows if r['event_id'] not in superseded]


def reconcile(task_id, actual_microusd, evidence, actor):
    """Operator reconciliation never replays a possibly accepted provider call."""
    if actual_microusd<0 or not evidence.strip() or not actor:
        raise ValueError('Verified usage, evidence and operator are required')
    with transaction() as c:
        row=c.execute(select(tasks).where(tasks.c.task_id==task_id)).mappings().one()
        _head(c,row['run_id'],lock=True)
        if row['status'] not in ('UNKNOWN','RUNNING') or (row['status']=='RUNNING' and row['lease_until']>time.time()):
            raise Conflict('Only an unknown or expired task can be reconciled')
        c.execute(update(tasks).where(tasks.c.task_id==task_id).values(status='RECONCILED',
            actual=actual_microusd,settled_at=now(),fence=row['fence']+1))
        _event(c,row['run_id'],'USAGE_RECONCILED',{'task_id':task_id,'actual_microusd':actual_microusd,
            'evidence':evidence,'actor':actor})
