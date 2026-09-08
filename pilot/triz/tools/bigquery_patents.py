"""Read public patent metadata with bounded SQL jobs, never scrape patent pages.

The persistent ledger limits this deployment's usage, not the billing account's
free allowance. Uncertain/unfinished jobs retain their full byte reservation.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import sqlite3
import time
import uuid

from ..settings import settings

TABLE = "patents-public-data.patents.publications"
PROVIDER = "bigquery_patents"
STOPWORDS = {"a", "an", "and", "or", "the", "of", "for", "to", "in", "with",
             "by", "patent", "patents", "triz", "method", "apparatus", "system"}
# One table reference for the entire batch. Filters/LIMIT do not imply scan savings.
# English metadata matches the existing English FOS query planner.
SQL = r"""
WITH queries AS (
  SELECT query_index, JSON_VALUE_ARRAY(item, '$.terms') AS terms,
         CAST(JSON_VALUE(item, '$.minimum') AS INT64) AS minimum
  FROM UNNEST(JSON_QUERY_ARRAY(@queries)) AS item WITH OFFSET AS query_index
), publications AS (
  SELECT publication_number, family_id, publication_date,
    (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1) AS title,
    (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1) AS abstract
  FROM `patents-public-data.patents.publications`
), scored AS (
  SELECT p.*, q.query_index, q.minimum,
    (SELECT COUNTIF(STRPOS(LOWER(CONCAT(p.title, ' ', COALESCE(p.abstract, ''))), term) > 0)
     FROM UNNEST(q.terms) AS term) AS matched,
    (SELECT COUNTIF(STRPOS(LOWER(p.title), term) > 0)
     FROM UNNEST(q.terms) AS term) AS title_matches
  FROM publications AS p CROSS JOIN queries AS q
  WHERE p.title IS NOT NULL AND p.publication_number IS NOT NULL
), families AS (
  SELECT * FROM scored WHERE matched >= minimum
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY query_index, COALESCE(NULLIF(NULLIF(family_id, ''), '0'), publication_number)
    ORDER BY matched DESC, title_matches DESC, IF(abstract IS NULL, 0, 1) DESC,
             publication_date DESC, publication_number) = 1
)
SELECT query_index, publication_number, title, abstract, publication_date, matched
FROM families
QUALIFY ROW_NUMBER() OVER (PARTITION BY query_index
  ORDER BY matched DESC, title_matches DESC, IF(abstract IS NULL, 0, 1) DESC,
           publication_date DESC, publication_number) <= @result_limit
ORDER BY query_index, matched DESC, publication_number
"""


class SearchUnavailable(Exception):
    def __init__(self, reason, **detail):
        super().__init__(reason)
        self.detail = dict(provider=PROVIDER, reason=reason, **detail)


def client():
    from google.cloud import bigquery
    from google.oauth2 import service_account
    if not settings.bigquery_project_id:
        raise SearchUnavailable('NOT_CONFIGURED')
    credentials = None
    if settings.bigquery_credentials_json:
        try:
            data = json.loads(settings.bigquery_credentials_json)
            if data.get('type') != 'service_account' or data.get('token_uri') != 'https://oauth2.googleapis.com/token':
                raise ValueError('Service account required')
            credentials = service_account.Credentials.from_service_account_info(
                data, scopes=['https://www.googleapis.com/auth/bigquery'])
        except (ValueError, TypeError, KeyError):
            raise SearchUnavailable('INVALID_CREDENTIALS') from None
    return bigquery.Client(project=settings.bigquery_project_id, credentials=credentials,
                           location=settings.bigquery_location)


def _db():
    settings.bigquery_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.bigquery_ledger_path, timeout=15)
    db.execute('CREATE TABLE IF NOT EXISTS usage (job_id TEXT PRIMARY KEY, project TEXT, month TEXT, bytes INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, expires REAL, data TEXT)')
    db.commit()
    return db


def _reserve(job_id, ceiling):
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    with closing(_db()) as db, db:
        db.execute('BEGIN IMMEDIATE')
        used = db.execute('SELECT COALESCE(SUM(bytes),0) FROM usage WHERE project=? AND month=?',
                          (settings.bigquery_project_id, month)).fetchone()[0]
        if used + ceiling > settings.bigquery_monthly_bytes:
            raise SearchUnavailable('MONTHLY_BUDGET_EXCEEDED', used_bytes=used,
                                    limit_bytes=settings.bigquery_monthly_bytes)
        db.execute('INSERT INTO usage VALUES (?,?,?,?)', (job_id, settings.bigquery_project_id, month, ceiling))


def _settle(job_id, billed):
    # Only a completed job with explicit statistics releases a reservation.
    if billed is not None:
        with closing(_db()) as db, db:
            db.execute('UPDATE usage SET bytes=? WHERE job_id=?', (max(0, int(billed)), job_id))


def _parameters(queries, k):
    from google.cloud import bigquery
    if not 1 <= len(queries) <= 40 or not 1 <= k <= 10:
        raise SearchUnavailable('INVALID_QUERY')
    plans = []
    for query in queries:
        if not isinstance(query, str) or len(query) > 500:
            raise SearchUnavailable('INVALID_QUERY')
        terms = list(dict.fromkeys(t for t in re.findall(r'[a-z0-9]+', query.lower())
                                   if len(t) >= 2 and t not in STOPWORDS))[:10]
        if len(terms) < 2:
            raise SearchUnavailable('INVALID_QUERY')
        plans.append(dict(terms=terms, minimum=max(2, math.ceil(len(terms) * 2 / 3))))
    return [bigquery.ScalarQueryParameter('queries', 'STRING', json.dumps(plans)),
            bigquery.ScalarQueryParameter('result_limit', 'INT64', k)]


def _prepare(connection, queries, k):
    from google.cloud import bigquery
    if settings.bigquery_max_bytes <= 0 or settings.bigquery_monthly_bytes <= 0 or settings.bigquery_timeout <= 0:
        raise SearchUnavailable('INVALID_BUDGET_CONFIG')
    parameters = _parameters(queries, k)
    job = connection.query(SQL, job_config=bigquery.QueryJobConfig(
        dry_run=True, use_legacy_sql=False, use_query_cache=False, query_parameters=parameters),
        timeout=20, job_retry=None)
    estimated = job.total_bytes_processed
    if estimated is None:
        raise SearchUnavailable('COST_ESTIMATE_UNAVAILABLE')
    estimated = int(estimated)
    # Include billing rounding headroom, but never exceed the operator's ceiling.
    ceiling = min(settings.bigquery_max_bytes, max(10 * 1024**2, math.ceil(estimated * 1.01)))
    if estimated > ceiling:
        raise SearchUnavailable('QUERY_BUDGET_EXCEEDED', estimated_bytes=estimated,
                                limit_bytes=settings.bigquery_max_bytes)
    return parameters, estimated, ceiling


def preflight(queries, k=6):
    """Metadata and free dry run only; never submits a billed query."""
    connection = client()
    try:
        table = connection.get_table(TABLE, timeout=20)
        _, estimate, ceiling = _prepare(connection, queries, k)
        return dict(table=TABLE, table_modified=table.modified.isoformat() if table.modified else None,
                    rows=table.num_rows, estimated_bytes=estimate, maximum_bytes_billed=ceiling,
                    monthly_limit_bytes=settings.bigquery_monthly_bytes, dry_run=True)
    finally:
        connection.close()


def _error(exc):
    from google.auth.exceptions import DefaultCredentialsError, RefreshError
    from google.api_core import exceptions
    if isinstance(exc, SearchUnavailable):
        return exc.detail
    if isinstance(exc, (DefaultCredentialsError, RefreshError, exceptions.Unauthorized)):
        reason = 'AUTHENTICATION_FAILED'
    elif isinstance(exc, exceptions.Forbidden):
        reason = 'ACCESS_DENIED_OR_QUOTA'
    elif isinstance(exc, exceptions.NotFound):
        reason = 'DATASET_NOT_FOUND'
    elif isinstance(exc, (TimeoutError, exceptions.DeadlineExceeded)):
        reason = 'QUERY_TIMEOUT'
    elif isinstance(exc, exceptions.BadRequest):
        reason = 'QUERY_REJECTED'
    else:
        reason = 'PROVIDER_ERROR'
    # Never expose raw exceptions, SQL, credentials or remote response bodies.
    return dict(provider=PROVIDER, reason=reason)


def search_batch(queries, k=6):
    """Returns one (records, diagnostics) pair per query, in input order."""
    if not queries:
        return []
    connection = job = None
    try:
        # Validate even cache hits. Include SQL/version, project and ordering in key.
        _parameters(queries, k)
        cache_key = hashlib.sha256(json.dumps([SQL, settings.bigquery_project_id, queries, k]).encode()).hexdigest()
        with closing(_db()) as db:
            cached = db.execute('SELECT data FROM cache WHERE key=? AND expires>?', (cache_key, time.time())).fetchone()
        if cached:
            return [(records, {**detail, 'cache_hit': True}) for records, detail in json.loads(cached[0])]
        connection = client()
        parameters, estimate, ceiling = _prepare(connection, queries, k)
        from google.cloud import bigquery
        job_id = 'triz_patents_' + uuid.uuid4().hex
        _reserve(job_id, ceiling)
        job = connection.query(SQL, job_id=job_id, job_retry=None, timeout=20,
            job_config=bigquery.QueryJobConfig(use_legacy_sql=False, use_query_cache=True,
                query_parameters=parameters, maximum_bytes_billed=ceiling,
                job_timeout_ms=settings.bigquery_timeout * 1000, labels={'app': 'triz', 'purpose': 'patent-search'}))
        rows = list(job.result(timeout=settings.bigquery_timeout, job_retry=None))
        _settle(job_id, job.total_bytes_billed)
        from .scholar import _clean, _rec
        batches = [[] for _ in queries]
        seen = [set() for _ in queries]
        for row in rows:
            idx = row['query_index']
            identifier = re.sub(r'[-\s]', '', row['publication_number'] or '').upper()
            if not isinstance(idx, int) or not 0 <= idx < len(queries):
                raise SearchUnavailable('INVALID_RESPONSE')
            if not re.fullmatch(r'[A-Z]{2}\d{4,}[A-Z]\d{0,2}', identifier) or not row['title']:
                raise SearchUnavailable('INVALID_RESPONSE')
            if identifier in seen[idx]:
                continue
            seen[idx].add(identifier)
            batches[idx].append(_rec(source_type='PATENT', identifier=identifier,
                title=_clean(row['title'], 500), snippet=_clean(row['abstract'] or '', 3000),
                url='https://patents.google.com/patent/' + identifier + '/en',
                year=str(row['publication_date'] or '')[:4], venue='Google Patents Public Datasets',
                provider=PROVIDER, query=queries[idx],
                retrieval_scope='BigQuery 공개 데이터의 영문 제목·초록·공개번호 확인; 원문 웹페이지 조회 생략'))
        result = [(records[:k], dict(provider=PROVIDER, status='OK' if records else 'EMPTY',
            records=len(records[:k]), errors=[], job_id=job_id, estimated_bytes=estimate,
            billed_bytes=job.total_bytes_billed, maximum_bytes_billed=ceiling,
            cache_hit=bool(job.cache_hit))) for records in batches]
        with closing(_db()) as db, db:
            db.execute('DELETE FROM cache WHERE expires<=?', (time.time(),))
            db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',
                       (cache_key, time.time() + max(0, settings.bigquery_cache_seconds), json.dumps(result)))
        return result
    except Exception as exc:
        if job is not None:
            try:
                job.cancel(timeout=10)
            except Exception:
                pass
        detail = _error(exc)
        return [([], dict(provider=PROVIDER, status='UNAVAILABLE', records=0,
                         errors=[dict(detail, retry_after=time.time() + 300)])) for _ in queries]
    finally:
        if connection is not None:
            connection.close()
