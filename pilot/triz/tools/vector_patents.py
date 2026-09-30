"""Global multilingual ANN retrieval followed by a single SQL batch hydration."""
from functools import lru_cache
import threading
import time
import uuid

from ..settings import settings
from .. import patent_corpus as corpus
from .bigquery_patents import publication_identifier

PROVIDER = 'vector_patents'
DIMENSIONS = 384
MODEL_COMMIT = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
MODEL_FILE = 'onnx/model_qint8_avx512_vnni.onnx'
MODEL_REVISION = 'e5-small:' + MODEL_COMMIT + ':int8:384:title-abstract:v1'
_model_lock = threading.Lock()


@lru_cache(maxsize=1)
def model():
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType
    from huggingface_hub import snapshot_download
    name = settings.patent_embedding_model
    # Use the publisher's pinned ONNX weights with mean pooling + L2 normalization.
    # Register explicitly: FastEmbed's built-in registry does not include E5 small.
    if not any(m['model'] == name for m in TextEmbedding.list_supported_models()):
        TextEmbedding.add_custom_model(name, pooling=PoolingType.MEAN, normalization=True,
            sources=ModelSource(hf=name), dim=DIMENSIONS, model_file=MODEL_FILE)
    path = snapshot_download(name, revision=MODEL_COMMIT,
        cache_dir=str(settings.storage_dir / 'embedding_models'),
        allow_patterns=[MODEL_FILE, 'config.json', 'tokenizer.json', 'tokenizer_config.json',
                        'special_tokens_map.json', 'sentencepiece.bpe.model'])
    return TextEmbedding(name, specific_model_path=path, threads=settings.patent_embedding_threads)


def embed(texts, query=False):
    # E5 requires different prefixes for queries and documents.
    with _model_lock:
        encoder = model()
        prefix = 'query: ' if query else 'passage: '
        values = encoder.embed([prefix+t for t in texts], batch_size=16)
        return [v.tolist() for v in values]


@lru_cache(maxsize=1)
def client():
    from qdrant_client import QdrantClient
    if not settings.qdrant_url:
        raise RuntimeError('QDRANT_NOT_CONFIGURED')
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None,
                        timeout=settings.patent_search_timeout, check_compatibility=False)


def ensure_collection():
    from qdrant_client import models as m
    q = client()
    previous = corpus.checkpoint('index')
    if previous and previous != index_config():
        raise RuntimeError('INDEX_CONFIG_CHANGED_REBUILD_REQUIRED')
    if not q.collection_exists(settings.patent_collection):
        if previous:
            raise RuntimeError('VECTOR_COLLECTION_MISSING_REBUILD_REQUIRED')
        q.create_collection(settings.patent_collection,
            vectors_config=m.VectorParams(size=DIMENSIONS, distance=m.Distance.COSINE, on_disk=True),
            hnsw_config=m.HnswConfigDiff(m=16, ef_construct=100, on_disk=True),
            quantization_config=m.ScalarQuantization(scalar=m.ScalarQuantizationConfig(
                type=m.ScalarType.INT8, quantile=0.99, always_ram=False)),
            on_disk_payload=True)
    config = q.get_collection(settings.patent_collection).config.params.vectors
    if not isinstance(config, m.VectorParams) or config.size != DIMENSIONS or config.distance != m.Distance.COSINE:
        raise RuntimeError('VECTOR_SCHEMA_MISMATCH')
    with corpus.engine().begin() as c:
        corpus.save_checkpoint(c, 'index', index_config())


def index_config():
    return dict(collection=settings.patent_collection, model=MODEL_REVISION)


def warmup():
    """Preload outside requests; credential and HTTP exception text is never logged."""
    try:
        embed(['patent mechanism'], query=True)
    except Exception:
        import logging
        logging.getLogger(__name__).warning('Patent embedding warmup unavailable')


def point_id(number):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'triz:patent:' + number))


def index_pending(batch_size=128, max_batches=0, emit=lambda **kw: None):
    from qdrant_client import models as m
    with corpus.writer_lock('index'):
        ensure_collection()
        stored_points = client().count(settings.patent_collection, exact=True).count
        total = batches = 0
        while not max_batches or batches < max_batches:
            rows = corpus.pending(batch_size)
            if not rows:
                break
            # Conservative admission ceiling for the initially provisioned 50 GB volume.
            # It counts updates too; an operator may raise it after verifying disk headroom.
            if stored_points + total + len(rows) > settings.patent_vector_max_points:
                raise RuntimeError('PATENT_VECTOR_CAPACITY_LIMIT')
            vectors = embed([r['data']['title'] + '\n' + r['data'].get('abstract', '') for r in rows])
            points = [m.PointStruct(id=point_id(r['publication_number']), vector=v,
                payload=dict(publication_number=r['publication_number'],
                    family_id=r['data'].get('family_id'), country=r['data'].get('country_code'),
                    publication_date=r['data']['publication_date'], cpc=r['data'].get('cpc', []),
                    ipc=r['data'].get('ipc', []), revision=MODEL_REVISION)) for r, v in zip(rows, vectors)]
            client().upsert(settings.patent_collection, points=points, wait=True)
            corpus.acknowledge(rows)
            total += len(rows)
            batches += 1
            emit(phase='INDEX', indexed_this_run=total, batches=batches)
        return total


def _unavailable(exc, stage, started):
    """Keep useful diagnostics without storing exception text, URLs or credentials."""
    import httpx
    allowed = {'INVALID_QUERY', 'INDEX_NOT_READY', 'QDRANT_NOT_CONFIGURED',
               'PATENT_DATABASE_NOT_CONFIGURED', 'INVALID_VECTOR_RESPONSE'}
    reason = str(exc) if str(exc) in allowed else 'VECTOR_SEARCH_UNAVAILABLE'
    source = getattr(exc, 'source', None) or exc.__cause__ or exc
    content = getattr(exc, 'content', b'')
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')
    timed_out = isinstance(source, (TimeoutError, httpx.TimeoutException)) or (
        stage == 'VECTOR_QUERY' and any(word in str(content).lower() for word in ('timeout', 'timed out')))
    if timed_out:
        reason = 'VECTOR_SEARCH_TIMEOUT' if stage == 'VECTOR_QUERY' else 'PATENT_SEARCH_TIMEOUT'
    status = getattr(exc, 'status_code', None)
    return [], dict(provider=PROVIDER, status='UNAVAILABLE', records=0,
        duration_ms=round((time.monotonic()-started)*1000),
        errors=[dict(provider=PROVIDER, reason=reason, retry_after=time.time()+60,
            failure_stage=stage, exception_type=type(exc).__name__,
            http_status=status if isinstance(status, int) else None)])


def search_batch(queries, k=6):
    from qdrant_client import models as m
    if not queries:
        return []
    started = time.monotonic()
    stage = 'VALIDATE_QUERY'
    try:
        if not 1 <= k <= 10 or len(queries) > 64 or any(
                not isinstance(q, str) or not q.strip() or len(q) > 1000 for q in queries):
            raise RuntimeError('INVALID_QUERY')
        stage = 'INDEX_CHECKPOINT'
        if corpus.checkpoint('index') != index_config():
            raise RuntimeError('INDEX_NOT_READY')
        stage = 'SOURCE_CHECKPOINT'
        source = corpus.checkpoint('source')
        corpus_complete = bool(source.get('complete')) and not corpus.has_pending()
        stage = 'CPU_EMBEDDING'
        vectors = embed(queries, query=True)
        if len(vectors) != len(queries):
            raise RuntimeError('INVALID_VECTOR_RESPONSE')
    except Exception as exc:
        return [_unavailable(exc, stage, started) for _ in queries]

    # Qdrant applies its timeout to the entire request. Large requests exhausted
    # that shared deadline even when each individual search could finish in time.
    # Keep CPU embedding and SQL hydration batched, but bound each ANN request
    # separately and retain successful queries when another query fails.
    responses, failures = [], {}
    for index, v in enumerate(vectors):
        try:
            batch = client().query_batch_points(settings.patent_collection, requests=[m.QueryRequest(
                query=v, limit=min(200, k * 12), with_payload=True, with_vector=False,
                score_threshold=settings.patent_min_score,
                params=m.SearchParams(hnsw_ef=128, quantization=m.QuantizationSearchParams(
                    rescore=True, oversampling=2.0)))], timeout=settings.patent_search_timeout)
            if len(batch) != 1 or any(not isinstance(p.payload, dict) or not p.payload.get('publication_number')
                                      for p in batch[0].points):
                raise RuntimeError('INVALID_VECTOR_RESPONSE')
            responses.append(batch[0])
        except Exception as exc:
            responses.append(None)
            failures[index] = _unavailable(exc, 'VECTOR_QUERY', started)

    stage = 'SQL_HYDRATION'
    try:
        # All industries participate. Metadata never adds an implicit domain filter.
        numbers = list({p.payload['publication_number'] for res in responses if res is not None for p in res.points})
        documents = corpus.fetch(numbers)
        from .scholar import _clean, _rec
        results = []
        stage = 'RESULT_MAPPING'
        for index, (query, response) in enumerate(zip(queries, responses)):
            if index in failures:
                results.append(failures[index])
                continue
            hits, families = [], set()
            missing = False
            for point in response.points:
                number = point.payload['publication_number']
                document = documents.get(number)
                if not document:
                    missing = True
                    continue
                family = document.get('family_id')
                family = family if family and family != '0' else number
                if family in families:
                    continue
                families.add(family)
                identifier = publication_identifier(number)
                hits.append(_rec(source_type='PATENT', identifier=identifier, publication_number=number,
                    title=_clean(document['title'], 500), snippet=_clean(document.get('abstract', ''), 3000),
                    url='https://patents.google.com/patent/' + identifier + '/en',
                    year=str(document['publication_date'])[:4], venue='Google Patents Public Datasets',
                    provider=PROVIDER, query=query, similarity=point.score,
                    cpc=document.get('cpc', []), ipc=document.get('ipc', []),
                    retrieval_scope='Qdrant 전체 산업 유사도 검색 후 MySQL 제목·초록·분류 조회; 청구항·명세서 원문 미포함'))
                if len(hits) == k:
                    break
            building = not corpus_complete
            errors = [dict(provider=PROVIDER, reason='MISSING_SQL_DOCUMENT')] if missing else []
            if building:
                errors.append(dict(provider=PROVIDER, reason='CORPUS_BUILDING', retry_after=time.time()+300))
            results.append((hits, dict(provider=PROVIDER, status=('PARTIAL' if hits else 'UNAVAILABLE') if missing or building
                else 'OK' if hits else 'EMPTY', records=len(hits),
                errors=errors, corpus_complete=corpus_complete,
                duration_ms=round((time.monotonic()-started)*1000), collection=settings.patent_collection)))
        return results
    except Exception as exc:
        return [failures[index] if index in failures else _unavailable(exc, stage, started)
                for index in range(len(queries))]
