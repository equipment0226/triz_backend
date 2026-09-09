from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from qdrant_client import QdrantClient

from triz import patent_corpus as corpus, patent_ingest as ingest, evidence, agent
from triz.context import RunContext
from triz.settings import settings
from triz.tools import vector_patents as vector, scholar, bigquery_patents as bq


def document(number='US-7909155-B2', family='1', abstract='spring preload reduces vibration'):
    return dict(publication_number=number, title='Adaptive gasket preload', abstract=abstract,
                family_id=family, publication_date=20110322, cpc=['F16J'], ipc=['F16J'])


@pytest.fixture
def storage(tmp_path, monkeypatch):
    db = create_engine('sqlite:///' + (tmp_path/'patents.db').as_posix())
    monkeypatch.setattr(corpus, 'engine', lambda: db)
    corpus.init()
    q = QdrantClient(':memory:')
    monkeypatch.setattr(vector, 'client', lambda: q)
    monkeypatch.setattr(vector, 'embed', lambda texts, query=False: [[1.0]+[0.0]*383 for _ in texts])
    monkeypatch.setattr(settings, 'patent_search_provider', 'vector')
    monkeypatch.setattr(bq, 'client', lambda: (_ for _ in ()).throw(AssertionError('Unexpected BigQuery access')))
    yield db, q
    q.close()
    db.dispose()


def test_ingest_idempotent_and_only_changed_documents_reindexed(storage):
    assert corpus.ingest([document()]) == 1
    assert vector.index_pending() == 1
    assert not corpus.pending()
    assert corpus.ingest([document()]) == 0
    assert vector.index_pending() == 0
    assert corpus.ingest([document(abstract='new abstract')]) == 1
    assert vector.index_pending() == 1
    assert storage[1].count(settings.patent_collection).count == 1
    assert corpus.fetch(['US-7909155-B2'])['US-7909155-B2']['abstract'] == 'new abstract'


def test_failed_vector_write_stays_pending_and_retry_has_no_duplicate(storage, monkeypatch):
    corpus.ingest([document()])
    original = storage[1].upsert
    monkeypatch.setattr(storage[1], 'upsert', lambda *a, **kw: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        vector.index_pending()
    assert len(corpus.pending()) == 1
    monkeypatch.setattr(storage[1], 'upsert', original)
    assert vector.index_pending() == 1
    assert storage[1].count(settings.patent_collection).count == 1


def test_vector_capacity_keeps_documents_pending(storage, monkeypatch):
    corpus.ingest([document()])
    monkeypatch.setattr(settings, 'patent_vector_max_points', 0)
    with pytest.raises(RuntimeError, match='VECTOR_CAPACITY_LIMIT'):
        vector.index_pending()
    assert len(corpus.pending()) == 1


def test_concurrent_new_revision_is_not_acknowledged(storage):
    corpus.ingest([document()])
    old = corpus.pending()
    corpus.ingest([document(abstract='source revised while indexing')])
    corpus.acknowledge(old)
    assert len(corpus.pending()) == 1


def test_document_and_resume_token_rollback_together(storage, monkeypatch):
    save = corpus.save_checkpoint
    def fail(connection, name, value):
        if name == 'source':
            raise RuntimeError('checkpoint failed')
        save(connection, name, value)
    monkeypatch.setattr(corpus, 'save_checkpoint', fail)
    with pytest.raises(RuntimeError):
        corpus.ingest([document()], {'page_token': 'next'})
    assert not corpus.fetch(['US-7909155-B2'])


def test_capacity_limit_does_not_advance_page(storage, monkeypatch):
    monkeypatch.setattr(settings, 'patent_db_max_bytes', 1)
    with pytest.raises(RuntimeError, match='CAPACITY_LIMIT'):
        corpus.ingest([document()], {'page_token':'next'})
    assert corpus.checkpoint('source') == {}
    assert corpus.status()['documents'] == 0


def test_global_search_hydrates_and_deduplicates_families(storage):
    corpus.ingest([document(), document('US-7909156-B2'), document('US-7909157-B2', '2')])
    vector.index_pending()
    batches = vector.search_batch(['vibration suppression', '진동 억제'], 6)
    assert [len(hits) for hits, _ in batches] == [2, 2]
    assert all(d['provider'] == 'vector_patents' for _, d in batches)
    assert batches[0][0][0]['snippet'] == 'spring preload reduces vibration'
    assert batches[0][0][0]['cpc'] == ['F16J']
    assert batches[0][0][0]['source_type'] == 'PATENT'


def test_source_finished_but_pending_index_is_not_complete(storage):
    corpus.ingest([document()], {'complete':True})
    vector.ensure_collection()
    assert vector.search_batch(['preload'])[0][1]['corpus_complete'] is False
    vector.index_pending()
    assert vector.search_batch(['preload'])[0][1]['corpus_complete'] is True


def test_missing_sql_is_unavailable_not_empty(storage, monkeypatch):
    corpus.ingest([document()]); vector.index_pending()
    monkeypatch.setattr(corpus, 'fetch', lambda numbers: {})
    hits, info = vector.search_batch(['preload'])[0]
    assert not hits and info['status'] == 'UNAVAILABLE'
    assert info['errors'][0]['reason'] == 'MISSING_SQL_DOCUMENT'


def test_uninitialized_index_and_outage_never_fall_back_to_bigquery(storage, monkeypatch):
    assert vector.search_batch(['preload'])[0][1]['status'] == 'UNAVAILABLE'
    corpus.ingest([document()]); vector.index_pending()
    monkeypatch.setattr(storage[1], 'query_batch_points', lambda *a, **kw: (_ for _ in ()).throw(TimeoutError()))
    detail = {}
    assert scholar.search_kind('preload', 'PATENT', diagnostics=detail) == []
    assert detail['status'] == 'UNAVAILABLE'
    assert 'bigquery_patents' not in scholar.enabled_providers()
    assert 'google_patents' not in scholar.enabled_providers()


def test_evidence_discovery_uses_vector_batch(storage, state, monkeypatch):
    corpus.ingest([document()]); vector.index_pending()
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: {'queries': [
        {'kind':'PATENT', 'query':'gasket spring preload', 'concept_ids':[]}]})
    evidence.discover(RunContext(state))
    assert state.scratch['search_diagnostics']['PATENT:gasket spring preload']['provider'] == 'vector_patents'


def test_model_or_collection_change_requires_rebuild(storage, monkeypatch):
    vector.ensure_collection()
    monkeypatch.setattr(settings, 'patent_collection', 'different_collection')
    with pytest.raises(RuntimeError, match='REBUILD_REQUIRED'):
        vector.ensure_collection()


def test_source_normalization_excludes_old_patents_and_preserves_non_english():
    raw = dict(publication_number='KR-102345678-B1', publication_date=20220201,
               title_localized=[{'language':'ko', 'text':'진동 억제'}],
               abstract_localized=[{'language':'ko', 'text':'탄성 구조'}],
               cpc=[{'code':'F16F'}, {'code':'F16F'}])
    normalized = ingest.normalize(raw)
    assert normalized['language'] == 'ko' and normalized['abstract'] == '탄성 구조'
    assert normalized['cpc'] == ['F16F']
    assert ingest.normalize(dict(raw, publication_date=19991231)) is None
    assert ingest.normalize(dict(raw, publication_number='IN-2005DE00420-A'))
    assert bq.publication_identifier('IN-2005DE00420-A') == 'IN2005DE00420A'


class Pages:
    def __init__(self, batches):
        self.batches, self.next_page_token = batches, None

    @property
    def pages(self):
        for token, rows in self.batches:
            self.next_page_token = token
            yield rows


def test_resume_and_late_old_publication_on_source_revision(storage, monkeypatch):
    table = SimpleNamespace(modified=SimpleNamespace(isoformat=lambda: 'v1'), num_rows=2,
        schema=[SimpleNamespace(name=n) for n in ingest.FIELDS])
    raw = dict(publication_number='US-7909155-B2', publication_date=20110322,
               title_localized=[{'language':'en', 'text':'gasket'}])
    calls = []
    def rows(*args, **kwargs):
        calls.append(kwargs.get('page_token'))
        return Pages([(None, [dict(raw, publication_number='US-7909156-B2')])]) if kwargs.get('page_token') else Pages([
            ('second', [raw]), (None, [dict(raw, publication_number='US-7909156-B2')])])
    connection = SimpleNamespace(get_table=lambda *a, **kw: table, list_rows=rows, close=lambda: None)
    monkeypatch.setattr(bq, 'client', lambda: connection)
    ingest.import_pages(max_pages=1)
    assert corpus.checkpoint('source')['page_token'] == 'second'
    ingest.import_pages()
    assert corpus.checkpoint('source')['complete']
    assert calls == [None, 'second']
    ingest.import_pages()
    assert len(calls) == 2  # Unchanged table: zero data reads.
    table.modified = SimpleNamespace(isoformat=lambda: 'v2')
    connection.list_rows = lambda *a, **kw: Pages([(None, [dict(raw, publication_number='US-7909157-B2', publication_date=20000101)])])
    ingest.import_pages()
    assert corpus.fetch(['US-7909157-B2'])  # Late arrival before previous maximum publication date.


def test_source_change_mid_page_does_not_advance_checkpoint(storage, monkeypatch):
    table = SimpleNamespace(modified=SimpleNamespace(isoformat=lambda: 'v1'), num_rows=1,
        schema=[SimpleNamespace(name=n) for n in ingest.FIELDS])
    revised = SimpleNamespace(modified=SimpleNamespace(isoformat=lambda: 'v2'), num_rows=2)
    tables = iter([table, revised])
    connection = SimpleNamespace(get_table=lambda *a, **kw: next(tables), close=lambda: None,
        list_rows=lambda *a, **kw: Pages([(None, [])]))
    monkeypatch.setattr(bq, 'client', lambda: connection)
    with pytest.raises(RuntimeError, match='SOURCE_CHANGED'):
        ingest.import_pages()
    assert corpus.checkpoint('source') == {}
