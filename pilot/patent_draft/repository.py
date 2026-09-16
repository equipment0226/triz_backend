"""Exact new-table allowlist; no legacy init, migration, serializer or writes."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from sqlalchemy import MetaData, Table, Column, String, Integer, BigInteger, Text, LargeBinary, select, insert, update
from sqlalchemy.dialects.mysql import LONGTEXT, LONGBLOB
from .domain import PatentError, canonical, digest, ident, PROFILE, SCOPE

metadata = MetaData()
JSON_TEXT = Text().with_variant(LONGTEXT(), 'mysql')
BLOB = LargeBinary().with_variant(LONGBLOB(), 'mysql')
cases = Table('patent_draft_cases', metadata,
    Column('case_id', String(64), primary_key=True), Column('owner_id', String(255), nullable=False, index=True),
    Column('revision', Integer, nullable=False), Column('epoch', Integer, nullable=False),
    Column('body', JSON_TEXT, nullable=False), Column('updated_ms', BigInteger, nullable=False))
records = Table('patent_draft_records', metadata,
    Column('record_id', String(64), primary_key=True), Column('case_id', String(64), nullable=False, index=True),
    Column('kind', String(64), nullable=False, index=True), Column('body', JSON_TEXT, nullable=False),
    Column('created_ms', BigInteger, nullable=False))
requests = Table('patent_draft_requests', metadata,
    Column('request_key', String(64), primary_key=True), Column('body_hash', String(64), nullable=False),
    Column('response', JSON_TEXT, nullable=False))
tasks = Table('patent_draft_tasks', metadata,
    Column('task_id', String(64), primary_key=True), Column('case_id', String(64), nullable=False, index=True),
    Column('status', String(32), nullable=False, index=True), Column('lease_until_ms', BigInteger, nullable=False),
    Column('fence', Integer, nullable=False), Column('body', JSON_TEXT, nullable=False))
assets = Table('patent_draft_assets', metadata,
    Column('asset_id', String(64), primary_key=True), Column('case_id', String(64), nullable=False, index=True),
    Column('name', String(255), nullable=False), Column('mime', String(128), nullable=False),
    Column('sha256', String(64), nullable=False), Column('content', BLOB, nullable=False))
cache = Table('patent_draft_public_cache', metadata,
    Column('cache_key', String(128), primary_key=True), Column('body', JSON_TEXT, nullable=False),
    Column('fetched_ms', BigInteger, nullable=False))
image_jobs = Table('patent_draft_image_jobs', metadata,
    Column('job_id', String(64), primary_key=True), Column('case_id', String(64), nullable=False, unique=True),
    Column('status', String(32), nullable=False, index=True), Column('body', JSON_TEXT, nullable=False),
    Column('lease_until_ms', BigInteger, nullable=False), Column('fence', Integer, nullable=False))
TABLES = frozenset(metadata.tables)


def now():
    return int(time.time() * 1000)


class Repository:
    def __init__(self, engine):
        from .sql_guard import guarded
        self.engine = guarded(engine, TABLES)

    def migrate(self):
        # Explicit operator command only. No ALTER or schema-wide create_all.
        assert TABLES == {'patent_draft_cases', 'patent_draft_records', 'patent_draft_requests',
                          'patent_draft_tasks', 'patent_draft_assets', 'patent_draft_public_cache', 'patent_draft_image_jobs'}
        metadata.create_all(self.engine, tables=[metadata.tables[n] for n in sorted(TABLES)])

    def get(self, owner, case_id, conn=None, lock=False):
        if conn is None:
            with self.engine.connect() as c:
                return self.get(owner, case_id, c)
        q = select(cases).where(cases.c.case_id == case_id, cases.c.owner_id == owner)
        row = conn.execute(q.with_for_update() if lock else q).mappings().first()
        if row is None:
            raise PatentError('NOT_FOUND', '특허 초안을 찾을 수 없습니다.', 404)
        return json.loads(row['body'])

    def list(self, owner, offset=0, limit=30):
        with self.engine.connect() as c:
            rows = c.execute(select(cases.c.body).where(cases.c.owner_id == owner)
                             .order_by(cases.c.updated_ms.desc(), cases.c.case_id).offset(offset).limit(limit + 1)).scalars().all()
        return {'items': [json.loads(x) for x in rows[:limit]], 'next_offset': offset + limit if len(rows) > limit else None}

    def append(self, conn, case_id, kind, body, record_id=None):
        record_id = record_id or ident('par')
        conn.execute(insert(records).values(record_id=record_id, case_id=case_id, kind=kind,
                                           body=canonical(body), created_ms=now()))
        return record_id

    def records(self, owner, case_id, kind=None, conn=None):
        if conn is None:
            with self.engine.connect() as c:
                return self.records(owner, case_id, kind, c)
        self.get(owner, case_id, conn)
        q = select(records).where(records.c.case_id == case_id)
        if kind:
            q = q.where(records.c.kind == kind)
        return [{'id': r['record_id'], 'kind': r['kind'], **json.loads(r['body'])}
                for r in conn.execute(q.order_by(records.c.created_ms, records.c.record_id)).mappings()]

    def record(self, owner, case_id, record_id, conn=None):
        if conn is None:
            with self.engine.connect() as c:
                return self.record(owner, case_id, record_id, c)
        self.get(owner, case_id, conn)
        row = conn.execute(select(records).where(records.c.record_id == record_id,
                                                 records.c.case_id == case_id)).mappings().first()
        if not row:
            raise PatentError('NOT_FOUND', '자료를 찾을 수 없습니다.', 404)
        return {'id': record_id, 'kind': row['kind'], **json.loads(row['body'])}

    @staticmethod
    def request_key(owner, scope, key):
        if not key or len(key) > 160:
            raise PatentError('IDEMPOTENCY_REQUIRED', 'Idempotency-Key가 필요합니다.', 422)
        return digest([owner, scope, key])

    def replay(self, c, request_key, body):
        row = c.execute(select(requests).where(requests.c.request_key == request_key)).mappings().first()
        if row:
            if row['body_hash'] != digest(body):
                raise PatentError('IDEMPOTENCY_CONFLICT', '같은 요청 키의 내용이 다릅니다.')
            return json.loads(row['response'])

    def remember(self, c, key, body, response):
        c.execute(insert(requests).values(request_key=key, body_hash=digest(body), response=canonical(response)))

    def artifact(self, c, case, kind, payload, parents=(), producer='OWNER', update_head=True):
        body = {'artifact_type': kind, 'payload': payload, 'content_hash': digest(payload),
                'parent_version_ids': list(parents), 'producer': producer, 'epoch': case['epoch'],
                'source_hash': case['source_hash'], 'rulepack_version': case['rulepack_version'],
                'model_profile': PROFILE, 'policy_version': case['policy_version'], 'scope_policy_version': SCOPE}
        version = self.append(c, case['case_id'], 'artifact', body)
        if update_head:
            case['artifacts'][kind] = version
            manifest = dict(sorted(case['artifacts'].items()))
            snapshot = {'members': manifest, 'content_hash': digest(manifest), 'epoch': case['epoch']}
            case['snapshot_id'] = self.append(c, case['case_id'], 'snapshot', snapshot)
            case['document_status'] = 'DRAFT_WITH_OPEN_ISSUES'
        return version

    def save(self, c, case, old_revision):
        case['revision'] = old_revision + 1
        result = c.execute(update(cases).where(cases.c.case_id == case['case_id'], cases.c.revision == old_revision)
                           .values(revision=case['revision'], epoch=case['epoch'], body=canonical(case), updated_ms=now()))
        if result.rowcount != 1:
            raise PatentError('VERSION_CONFLICT', '다른 작업이 갱신했습니다. 다시 불러와 주세요.')

    def mutate(self, owner, case_id, operation, body, key, fn):
        request_key = self.request_key(owner, case_id + ':' + operation, key)
        with self.engine.begin() as c:
            case = self.get(owner, case_id, c, lock=True)
            previous = self.replay(c, request_key, body)
            if previous is not None:
                return previous
            if (body['expected_revision'], body['expected_epoch'], body['input_snapshot_id']) != (
                    case['revision'], case['epoch'], case['snapshot_id']):
                raise PatentError('VERSION_CONFLICT', '사건 버전이 변경됐습니다. 다시 불러와 주세요.')
            revision = case['revision']
            result = fn(c, case, body.get('payload', {}))
            self.save(c, case, revision)
            self.append(c, case_id, 'event', {'type': operation, 'revision': case['revision'], 'epoch': case['epoch']})
            response = {'case': case, 'result': result}
            self.remember(c, request_key, body, response)
            return response
