"""Compact patent repository. SQL and vector acknowledgement are retry-safe.

Only this repository uses PATENT_DATABASE_URL; application accounts stay in their
existing database. Compressed documents omit claims, descriptions and drawings.
"""
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
import zlib

from sqlalchemy import (Column, Integer, LargeBinary, MetaData, String, Table,
                        Text, create_engine, func, select, text, update)
from sqlalchemy.dialects.mysql import MEDIUMBLOB, insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from .settings import settings

metadata = MetaData()
patents = Table('patent_documents', metadata,
    Column('publication_number', String(64), primary_key=True),
    Column('content_hash', LargeBinary(32), nullable=False),
    Column('document', LargeBinary().with_variant(MEDIUMBLOB(), 'mysql'), nullable=False),
    Column('pending', Integer, nullable=False, index=True), mysql_charset='utf8mb4')
checkpoints = Table('patent_checkpoints', metadata,
    Column('name', String(64), primary_key=True), Column('value', Text, nullable=False),
    mysql_charset='utf8mb4')


@lru_cache(maxsize=1)
def engine():
    if not settings.patent_database_url:
        raise RuntimeError('PATENT_DATABASE_NOT_CONFIGURED')
    options = dict(pool_pre_ping=True, pool_recycle=900)
    if settings.patent_database_url.startswith('mysql'):
        options['connect_args'] = dict(connect_timeout=10, read_timeout=30, write_timeout=60)
    return create_engine(settings.patent_database_url, **options)


def init():
    metadata.create_all(engine())


def _upsert(connection, table, rows):
    if not rows:
        return
    insert = (mysql_insert if connection.dialect.name == 'mysql' else sqlite_insert)(table).values(rows)
    values = {c.name: getattr(insert.inserted if connection.dialect.name == 'mysql' else insert.excluded, c.name)
              for c in table.c if not c.primary_key}
    statement = (insert.on_duplicate_key_update(**values) if connection.dialect.name == 'mysql'
                 else insert.on_conflict_do_update(index_elements=[c.name for c in table.primary_key], set_=values))
    connection.execute(statement)


def save_checkpoint(connection, name, value):
    _upsert(connection, checkpoints, [dict(name=name, value=json.dumps(value, separators=(',', ':')))])


def checkpoint(name):
    with engine().connect() as c:
        value = c.execute(select(checkpoints.c.value).where(checkpoints.c.name == name)).scalar()
    return json.loads(value) if value else {}


def encode(document):
    raw = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).digest(), zlib.compress(raw, 6)


def decode(blob):
    return json.loads(zlib.decompress(blob))


def ingest(documents, progress=None):
    """A page's changes and resume token commit together; identical rows stay indexed."""
    unique = {d['publication_number']: d for d in documents}
    with engine().begin() as c:
        existing = {r[0]: (r[1], r[2]) for r in c.execute(select(patents.c.publication_number,
            patents.c.content_hash, func.length(patents.c.document))
            .where(patents.c.publication_number.in_(unique))).all()} if unique else {}
        accounting = c.execute(select(checkpoints.c.value).where(checkpoints.c.name == 'size')).scalar()
        accounting = json.loads(accounting) if accounting else dict(documents=0, compressed_bytes=0)
        rows = []
        for number, document in unique.items():
            digest, blob = encode(document)
            previous = existing.get(number)
            if not previous or previous[0] != digest:
                rows.append(dict(publication_number=number, content_hash=digest, document=blob, pending=1))
                accounting['documents'] += int(previous is None)
                accounting['compressed_bytes'] += len(blob) - (previous[1] if previous else 0)
        # Conservative logical guard in addition to approximate physical MySQL stats.
        projected = accounting['compressed_bytes'] * 1.5 + accounting['documents'] * 512
        if projected > settings.patent_db_max_bytes:
            raise RuntimeError('PATENT_DATABASE_CAPACITY_LIMIT')
        _upsert(c, patents, rows)
        save_checkpoint(c, 'size', accounting)
        if progress is not None:
            save_checkpoint(c, 'source', dict(progress, changed=progress.get('changed', 0)+len(rows)))
    return len(rows)


def fetch(numbers):
    if not numbers:
        return {}
    with engine().connect() as c:
        rows = c.execute(select(patents.c.publication_number, patents.c.document)
            .where(patents.c.publication_number.in_(numbers))).all()
    return {number: decode(blob) for number, blob in rows}


def pending(limit=128):
    with engine().connect() as c:
        rows = c.execute(select(patents).where(patents.c.pending == 1)
            .order_by(patents.c.publication_number).limit(limit)).mappings().all()
    return [dict(row, data=decode(row['document'])) for row in rows]


def has_pending():
    with engine().connect() as c:
        return c.execute(select(patents.c.pending).where(patents.c.pending == 1).limit(1)).first() is not None


def acknowledge(rows):
    # A concurrent source update must remain pending. Qdrant writes are wait=True.
    with engine().begin() as c:
        for row in rows:
            c.execute(update(patents).where(patents.c.publication_number == row['publication_number'],
                patents.c.content_hash == row['content_hash']).values(pending=0))


def capacity():
    with engine().connect() as c:
        if c.dialect.name == 'mysql':
            # Includes every table in the dedicated database; leave volume headroom
            # for redo, undo, binary logs, fragmentation and Railway system files.
            used = c.execute(text('SELECT COALESCE(SUM(data_length+index_length),0) '
                'FROM information_schema.tables WHERE table_schema=DATABASE()')).scalar()
        else:
            used = c.execute(select(func.coalesce(func.sum(func.length(patents.c.document)), 0))).scalar()
    return int(used or 0)


def status():
    with engine().connect() as c:
        total = c.execute(select(func.count()).select_from(patents)).scalar()
        remaining = c.execute(select(func.count()).select_from(patents).where(patents.c.pending == 1)).scalar()
    return dict(documents=total, pending=remaining, indexed=total-remaining,
                database_bytes=capacity(), source=checkpoint('source'), index=checkpoint('index'),
                size=checkpoint('size'))


@contextmanager
def writer_lock(name):
    """MySQL session lock survives transactions, and releases after worker death."""
    with engine().connect() as c:
        mysql = c.dialect.name == 'mysql'
        if mysql and c.execute(text('SELECT GET_LOCK(:name,0)'), {'name': 'triz_patents_' + name}).scalar() != 1:
            raise RuntimeError('PATENT_WORKER_ALREADY_RUNNING')
        try:
            yield
        finally:
            if mysql:
                c.execute(text('SELECT RELEASE_LOCK(:name)'), {'name': 'triz_patents_' + name})
