"""Query-free BigQuery REST export, with source-version and page checkpoints.

The source is not date partitioned and exposes no row-level modification cursor.
Reconciliation reads selected metadata on each source revision. Only changed
documents are written/embedded. Never infer completeness from MAX(publication_date).
"""
from datetime import datetime
import time

from . import patent_corpus as corpus
from .tools import bigquery_patents as bq
from .settings import settings

FIELDS = {'publication_number', 'family_id', 'publication_date', 'filing_date',
          'priority_date', 'country_code', 'kind_code', 'title_localized',
          'abstract_localized', 'assignee_harmonized', 'cpc', 'ipc'}
FORMAT_VERSION = 1


def selected_fields(table):
    fields = [f for f in table.schema if f.name in FIELDS]
    if {f.name for f in fields} != FIELDS:
        raise RuntimeError('SOURCE_SCHEMA_CHANGED')
    return fields


def localized(items, language=None):
    values = [dict(v) for v in items or [] if v.get('text')]
    if not values:
        return '', ''
    priorities = list(dict.fromkeys([language, 'en', 'ko']))
    selected = min(values, key=lambda v: priorities.index(v.get('language'))
                   if v.get('language') in priorities else len(priorities))
    return selected['text'], selected.get('language', '')


def normalize(row):
    date = int(row.get('publication_date') or 0)
    if date < 20000101:
        return None
    datetime.strptime(str(date), '%Y%m%d')
    number = row['publication_number']
    bq.publication_identifier(number)
    title, language = localized(row.get('title_localized'))
    if not title:
        return None
    abstract, abstract_language = localized(row.get('abstract_localized'), language)
    return dict(publication_number=number, publication_date=date,
        family_id=str(row.get('family_id') or ''), country_code=row.get('country_code') or '',
        kind_code=row.get('kind_code') or '', filing_date=row.get('filing_date'),
        priority_date=row.get('priority_date'), title=title[:1500], abstract=abstract[:24000],
        language=language, abstract_language=abstract_language,
        abstract_truncated=len(abstract) > 24000,
        assignees=sorted({a['name'] for a in row.get('assignee_harmonized', []) if a.get('name')})[:20],
        cpc=sorted({a['code'] for a in row.get('cpc', []) if a.get('code')})[:100],
        ipc=sorted({a['code'] for a in row.get('ipc', []) if a.get('code')})[:100])


def version(table):
    if not table.modified:
        raise RuntimeError('SOURCE_VERSION_UNAVAILABLE')
    return dict(table=bq.TABLE, modified=table.modified.isoformat(), rows=table.num_rows,
                format_version=FORMAT_VERSION, since=20000101)


def probe(sample_rows=1000):
    connection = bq.client()
    try:
        table = connection.get_table(bq.TABLE, timeout=30)
        rows = list(connection.list_rows(table, selected_fields=selected_fields(table),
            max_results=sample_rows, timeout=30))
        documents = [d for row in rows if (d := normalize(dict(row))) is not None]
        size = sum(len(corpus.encode(d)[1]) for d in documents)
        return dict(source=version(table), method='tabledata.list', query_submitted=False,
            sample_rows=len(rows), eligible_sample_rows=len(documents),
            sample_compressed_bytes=size,
            # Non-random physical sample; planning estimate only, not a guarantee.
            estimated_document_bytes=int(size/max(1, len(rows))*table.num_rows),
            estimated_vector_float32_bytes=int(len(documents)/max(1,len(rows))*table.num_rows*384*4),
            note='Physical sample is not random; excludes SQL indexes, vector indexes, quantization and WAL.')
    finally:
        connection.close()


def import_pages(page_size=1000, max_pages=0, force=False, emit=lambda **kw: None,
                 after_page=None):
    if not 1 <= page_size <= 10000 or max_pages < 0:
        raise RuntimeError('INVALID_PAGE_LIMIT')
    connection = bq.client()
    try:
        with corpus.writer_lock('import'):
            table = connection.get_table(bq.TABLE, timeout=30)
            source = version(table)
            progress = corpus.checkpoint('source')
            if progress.get('source') != source or force:
                progress = dict(source=source, page_token=None, scanned=0, accepted=0, changed=0,
                                complete=False, started_at=time.time())
            if progress.get('complete'):
                emit(phase='SOURCE_UNCHANGED', scanned=progress['scanned'], query_submitted=False)
                return progress
            iterator = connection.list_rows(table, selected_fields=selected_fields(table),
                page_size=page_size, page_token=progress.get('page_token'), timeout=60)
            pages = 0
            for page in iterator.pages:
                # Approximate DB statistics are a guard, not a volume quota replacement.
                if corpus.capacity() >= settings.patent_db_max_bytes:
                    raise RuntimeError('PATENT_DATABASE_CAPACITY_LIMIT')
                documents = []
                scanned = 0
                for row in page:
                    scanned += 1
                    document = normalize(dict(row))
                    if document:
                        documents.append(document)
                if version(connection.get_table(bq.TABLE, timeout=30)) != source:
                    raise RuntimeError('SOURCE_CHANGED_RESTART_IMPORT')
                progress = dict(progress, page_token=iterator.next_page_token,
                    scanned=progress['scanned']+scanned, accepted=progress['accepted']+len(documents),
                    complete=not iterator.next_page_token, checked_at=time.time())
                changed = corpus.ingest(documents, progress)
                # The persisted count and token already committed with the documents.
                progress['changed'] = progress.get('changed', 0)+changed
                pages += 1
                emit(phase='IMPORT', scanned=progress['scanned'], accepted=progress['accepted'],
                    changed=progress['changed'], complete=progress['complete'], query_submitted=False)
                if after_page:
                    after_page()
                if max_pages and pages >= max_pages:
                    break
            return progress
    finally:
        connection.close()
