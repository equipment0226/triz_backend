"""Read-only remote helper: bounded Qdrant metadata or selected-only SQL hydration.

Run explicitly with deploy/patent_remote.py and a generated request JSON.
No table initialization, index creation, embeddings, model calls or remote writes.
This standalone helper also works before the new local queue module is deployed.
"""
import json
import re
import uuid
from datetime import datetime, timezone

VERSION = 'balanced-patent-review-v1'
MAX_POOL = 2000
MAX_SELECTED = 72
PAYLOAD_FIELDS = ['publication_number', 'family_id', 'country', 'publication_date', 'cpc', 'ipc', 'revision']


def validate_config(config):
    if config.get('version') != VERSION or config.get('operation') not in {'pool', 'hydrate'}:
        raise ValueError('Invalid balanced queue request')


def read_pool(config, client, collection):
    validate_config(config)
    if config['operation'] != 'pool':
        raise ValueError('Expected pool request')
    limit = config.get('pool_limit', MAX_POOL)
    if type(limit) is not int or not 1 <= limit <= MAX_POOL:
        raise ValueError('Pool limit must be 1..2000')
    if config.get('expected_collection') not in {None, collection}:
        raise ValueError('Configured vector collection changed')
    if not re.fullmatch(r'[0-9a-f]{64}', str(config.get('state_sha256') or '')):
        raise ValueError('Missing local queue state hash')
    offset = config.get('offset')
    if offset is not None and (not isinstance(offset, str) or str(uuid.UUID(offset)) != offset):
        raise ValueError('Expected a Qdrant UUID offset')
    initial = offset
    points = []
    requests = 0
    exhausted = False
    while len(points) < limit and requests < 16:
        records, next_offset = client.scroll(
            collection_name=collection, offset=offset, limit=min(256, limit - len(points)),
            with_payload=PAYLOAD_FIELDS, with_vectors=False, timeout=20)
        requests += 1
        if len(records) > min(256, limit - len(points)):
            raise ValueError('Vector response exceeded requested bound')
        for point in records:
            payload = point.payload or {}
            points.append(dict(id=str(point.id), payload={k: payload[k] for k in PAYLOAD_FIELDS if k in payload}))
        next_offset = str(next_offset) if next_offset is not None else None
        if next_offset is None:
            exhausted = True
            offset = None
            break
        if next_offset == offset:
            raise ValueError('Vector cursor did not advance')
        offset = next_offset
    return dict(inventory=dict(version=VERSION, operation='pool',
        created_at=datetime.now(timezone.utc).isoformat(), collection=collection,
        state_sha256=config['state_sha256'], offset=initial, next_offset=offset,
        pool_limit=limit, scanned_points=len(points), scroll_requests=requests,
        scroll_exhausted=exhausted, request_budget_reached=requests == 16 and len(points) < limit and not exhausted,
        sql_queries=0, with_vectors=False, probability_sample=False,
        exhaustive_review_complete=False, external_llm_calls=0), points=points)


def read_hydration(config, fetch, encode, format_identifier):
    validate_config(config)
    if config['operation'] != 'hydrate':
        raise ValueError('Expected hydration request')
    numbers = config.get('publication_numbers')
    if (not isinstance(numbers, list) or len(numbers) > MAX_SELECTED
            or any(not isinstance(n, str) or not re.fullmatch(r'[A-Z]{2}-[A-Z0-9]*\d[A-Z0-9]*-[A-Z][0-9]{0,2}', n) for n in numbers)
            or len(numbers) != len(set(numbers))):
        raise ValueError('Hydration requires at most 72 unique publication numbers')
    if not re.fullmatch(r'[0-9a-f]{64}', str(config.get('selection_sha256') or '')):
        raise ValueError('Missing selection hash')
    # fetch() uses WHERE publication_number IN (...) against the existing primary
    # key. It never iterates the SQL corpus or creates classification indexes.
    stored = fetch(numbers) if numbers else {}
    if set(stored) - set(numbers):
        raise ValueError('SQL hydration returned unrequested documents')
    documents = []
    for number in numbers:
        if number not in stored:
            continue
        doc = stored[number]
        publication_date = doc.get('publication_date', '')
        documents.append(dict(identifier=number, publication_number=number, source_type='PATENT',
            title=doc.get('title', ''), abstract=doc.get('abstract', ''),
            url='https://patents.google.com/patent/' + format_identifier(number) + '/en',
            year=str(publication_date)[:4] if publication_date else doc.get('year', ''),
            publication_date=publication_date, country_code=doc.get('country_code', ''),
            cpc=doc.get('cpc', []), ipc=doc.get('ipc', []), family_id=doc.get('family_id'),
            content_hash=encode(doc)[0].hex(), abstract_truncated=bool(doc.get('abstract_truncated')),
            retrieval_scope='stored_patent_abstract', origins=['bounded_qdrant_balanced_queue']))
    return dict(inventory=dict(version=VERSION, operation='hydrate',
        created_at=datetime.now(timezone.utc).isoformat(), selection_sha256=config['selection_sha256'],
        requested_numbers=numbers, fetched_records=len(documents),
        missing_numbers=[n for n in numbers if n not in stored],
        sql_queries=int(bool(numbers)), sql_scope='selected_publication_primary_keys_only',
        analysis_performed=False, exhaustive_review_complete=False, external_llm_calls=0), documents=documents)


def main(config):
    validate_config(config)
    if config['operation'] == 'pool':
        from triz.tools import vector_patents
        from triz.settings import settings
        return read_pool(config, vector_patents.client(), settings.patent_collection)
    from triz import patent_corpus
    from triz.tools.bigquery_patents import publication_identifier
    return read_hydration(config, patent_corpus.fetch, patent_corpus.encode, publication_identifier)


if __name__ == '__main__':
    try:
        print(json.dumps(main(globals().get('TASK_CONFIG', {})), ensure_ascii=False))
    except Exception:
        # Never expose connection strings or credentials in remote tracebacks.
        print(json.dumps({'error': 'BALANCED_PATENT_READ_FAILED'}))
        raise SystemExit(1)
