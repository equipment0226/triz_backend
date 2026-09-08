import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from triz import agent, evidence
from triz.context import RunContext
from triz.schema import ConceptSpec
from triz.settings import settings
from triz.tools import bigquery_patents as bq, scholar


class Job:
    total_bytes_processed = 20 * 1024**2
    total_bytes_billed = 20 * 1024**2
    cache_hit = False

    def __init__(self, rows=(), failure=None):
        self.rows, self.failure, self.cancelled = rows, failure, False

    def result(self, **kw):
        assert kw['job_retry'] is None
        if self.failure:
            raise self.failure
        return self.rows

    def cancel(self, **kw):
        self.cancelled = True


class Client:
    def __init__(self, rows=()):
        self.calls, self.dry, self.job = [], Job(), Job(rows)

    def query(self, sql, **kw):
        self.calls.append((sql, kw))
        assert kw['job_retry'] is None
        return self.dry if kw['job_config'].dry_run else self.job

    def close(self):
        pass

    def get_table(self, table, **kw):
        assert table == bq.TABLE
        return SimpleNamespace(modified=None, num_rows=10)


@pytest.fixture(autouse=True)
def config(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'bigquery_project_id', 'test-project')
    monkeypatch.setattr(settings, 'bigquery_ledger_path', tmp_path / 'budget.sqlite3')
    monkeypatch.setattr(settings, 'bigquery_max_bytes', 100 * 1024**2)
    monkeypatch.setattr(settings, 'bigquery_monthly_bytes', 200 * 1024**2)
    monkeypatch.setattr(settings, 'bigquery_cache_seconds', 86400)
    monkeypatch.setattr(settings, 'patent_search_provider', 'bigquery')
    monkeypatch.setattr(bq, 'client', lambda: pytest.fail('No live BigQuery jobs in tests'))


def row(idx=0, number='US-7909155-B2', abstract='Actual abstract about a spring that maintains gasket preload under thermal cycling.'):
    return dict(query_index=idx, publication_number=number, publication_date=20110322,
                title='Resilient seal support', abstract=abstract, matched=2)


def usage():
    with sqlite3.connect(settings.bigquery_ledger_path) as db:
        return db.execute('SELECT COALESCE(SUM(bytes),0) FROM usage').fetchone()[0]


def test_batch_parameterization_provenance_cache_and_cost(monkeypatch):
    connection = Client([row(), row(), row(1, 'EP-1234567-A1')])
    monkeypatch.setattr(bq, 'client', lambda: connection)
    queries = ['gasket spring preload', "thermal cooling '); DROP TABLE patents; --"]
    result = bq.search_batch(queries)
    assert len(connection.calls) == 2  # One free dry run and one billed job for both queries.
    sql, call = connection.calls[1]
    assert 'DROP TABLE' not in sql and sql.count('`'+bq.TABLE+'`') == 1
    config = call['job_config'].to_api_repr()['query']
    assert int(config['maximumBytesBilled']) <= settings.bigquery_max_bytes
    assert config['useLegacySql'] is False and call['job_id'].startswith('triz_patents_')
    params = json.loads(config['queryParameters'][0]['parameterValue']['value'])
    assert params[0]['minimum'] == 2
    assert [len(records) for records, _ in result] == [1, 1]
    hit = result[0][0][0]
    assert hit['identifier'] == 'US7909155B2' and hit['provider'] == 'bigquery_patents'
    assert hit['snippet'] == row()['abstract'] and hit['year'] == '2011'
    assert hit['url'] == 'https://patents.google.com/patent/US7909155B2/en'
    assert usage() == connection.job.total_bytes_billed
    again = bq.search_batch(queries)
    assert len(connection.calls) == 2 and all(d['cache_hit'] for _, d in again)


def test_dry_run_above_limit_does_not_submit_or_cache(monkeypatch):
    connection = Client(); connection.dry.total_bytes_processed = settings.bigquery_max_bytes + 1
    monkeypatch.setattr(bq, 'client', lambda: connection)
    result = bq.search_batch(['gasket spring'])
    assert len(connection.calls) == 1 and usage() == 0
    assert result[0][1]['errors'][0]['reason'] == 'QUERY_BUDGET_EXCEEDED'
    assert result[0][1]['status'] == 'UNAVAILABLE'
    connection.dry.total_bytes_processed = 20 * 1024**2
    assert bq.search_batch(['gasket spring'])[0][1]['status'] == 'EMPTY'
    assert len(connection.calls) == 3


def test_monthly_limit_is_atomic_and_persistent(monkeypatch):
    monkeypatch.setattr(settings, 'bigquery_monthly_bytes', 100)
    def reserve(i):
        try:
            bq._reserve(str(i), 60)
            return True
        except bq.SearchUnavailable as exc:
            assert exc.detail['reason'] == 'MONTHLY_BUDGET_EXCEEDED'
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, range(2))) == [False, True]
    assert usage() == 60
    with pytest.raises(bq.SearchUnavailable):
        bq._reserve('after-restart', 60)


def test_monthly_limit_blocks_execution_after_dry_run(monkeypatch):
    monkeypatch.setattr(settings, 'bigquery_monthly_bytes', 1)
    connection = Client(); monkeypatch.setattr(bq, 'client', lambda: connection)
    result = bq.search_batch(['thermal cooling'])
    assert result[0][1]['errors'][0]['reason'] == 'MONTHLY_BUDGET_EXCEEDED'
    assert len(connection.calls) == 1 and usage() == 0


def test_timeout_cancels_and_keeps_reservation(monkeypatch):
    connection = Client(); connection.job.failure = TimeoutError('sensitive response body')
    monkeypatch.setattr(bq, 'client', lambda: connection)
    result = bq.search_batch(['thermal cooling'])
    assert connection.job.cancelled and usage() > 0
    assert result[0][1]['errors'][0]['reason'] == 'QUERY_TIMEOUT'
    assert 'sensitive' not in json.dumps(result)


def test_missing_auth_is_unavailable_and_not_cached(monkeypatch):
    from google.auth.exceptions import DefaultCredentialsError
    def missing():
        raise DefaultCredentialsError('private credential details')
    monkeypatch.setattr(bq, 'client', missing)
    result = bq.search_batch(['spring preload'])
    assert result[0][1]['errors'][0]['reason'] == 'AUTHENTICATION_FAILED'
    assert 'private' not in json.dumps(result)
    connection = Client([row()]); monkeypatch.setattr(bq, 'client', lambda: connection)
    assert bq.search_batch(['spring preload'])[0][1]['status'] == 'OK'


def test_bad_row_and_missing_abstract_do_not_invent_content(monkeypatch):
    connection = Client([row(abstract=None)]); monkeypatch.setattr(bq, 'client', lambda: connection)
    assert bq.search_batch(['spring preload'])[0][0][0]['snippet'] == ''
    connection.job.rows = [row(number='invented<script>')]
    result = bq.search_batch(['gasket spring'])
    assert result[0][0] == [] and result[0][1]['errors'][0]['reason'] == 'INVALID_RESPONSE'


def test_preflight_never_submits_billed_job(monkeypatch):
    connection = Client(); monkeypatch.setattr(bq, 'client', lambda: connection)
    result = bq.preflight(['spring preload'])
    assert result['dry_run'] is True and len(connection.calls) == 1
    assert not settings.bigquery_ledger_path.exists()


def test_discover_batches_patents_preserves_concept_links_and_papers(state, monkeypatch):
    concept = ConceptSpec(title='Seal'); state.concepts = [concept]
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: {'queries': [
        {'kind':'PATENT', 'query':'spring preload', 'concept_ids':[concept.id], 'scope':'cross_domain'},
        {'kind':'PATENT', 'query':'thermal cooling', 'concept_ids':[concept.id]},
        {'kind':'PAPER', 'query':'seal fatigue', 'concept_ids':[concept.id]}]})
    connection = Client([row(), row(1, 'EP-1234567-A1')])
    monkeypatch.setattr(bq, 'client', lambda: connection)
    def paper(query, kind, k, diagnostics):
        assert kind == 'PAPER'
        diagnostics.update(status='EMPTY', provider='crossref', errors=[])
        return []
    monkeypatch.setattr(scholar, 'search_kind', paper)
    evidence.discover(RunContext(state))
    assert len(connection.calls) == 2
    hits = state.scratch['evidence_candidates']
    assert len(hits) == 2 and all(h['concept_ids'] == [concept.id] for h in hits)
    assert hits[0]['scope'] == 'cross_domain'
    assert state.steps[-1].status == 'OK'
    summary = evidence.search_summary(state)
    assert summary['patent_records'] == 2 and 'BigQuery' in summary['patent_search']


def test_provider_change_retries_old_empty_at_query_limit(state, monkeypatch):
    key = 'PATENT:spring preload'
    state.scratch.update(search_cache={key:[]}, search_diagnostics={key:{'status':'EMPTY','provider':'google_patents'}})
    monkeypatch.setattr(settings, 'triz', {'evidence':{'max_queries_per_run':1}})
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: pytest.fail('Reuse existing query'))
    connection = Client([row()]); monkeypatch.setattr(bq, 'client', lambda: connection)
    evidence.discover(RunContext(state))
    assert state.scratch['search_diagnostics'][key]['provider'] == 'bigquery_patents'
    assert evidence.search_summary(state)['patent_status'] == 'OK'


def test_selected_bigquery_does_not_scrape_google(monkeypatch):
    monkeypatch.setattr(scholar.httpx, 'get', lambda *a, **kw: pytest.fail('No Google scraping'))
    connection = Client([row()]); monkeypatch.setattr(bq, 'client', lambda: connection)
    diagnostics = {}
    assert scholar.search_kind('spring preload', 'PATENT', diagnostics=diagnostics)
    assert diagnostics['provider'] == 'bigquery_patents'
    assert 'google_patents' not in scholar.enabled_providers()
