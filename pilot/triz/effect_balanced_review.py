"""Offline, bounded patent-review queue; no network, model calls or old-ledger writes.

Hash-ordered Qdrant metadata is a candidate source, not a probability sample.
Selection balances A-H plus unclassified; Y is a cross-cutting tag. Every CPC
and IPC is retained, including IPC-only records. Queueing never counts as review.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

VERSION = 'balanced-patent-review-v1'
BUCKETS = tuple('ABCDEFGH') + ('UNCLASSIFIED',)
MAX_POOL = 2000
MAX_SELECTED = 72
REVIEWED = {'LINK', 'DEFER', 'DESIGN_ONLY', 'REJECT_CLAIM'}
EXCLUDED = REVIEWED | {'NO_ABSTRACT'}
CAVEAT = ('Bounded metadata candidate pool, not a statistically random sample or '
          'an exhaustive corpus review. UUID order is deterministic publication-hash '
          'order. Unselected candidates remain unreviewed. Qdrant is not a SQL '
          'snapshot and can lag ingestion. A finished scroll is not completed analysis.')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def immutable_json(path, value):
    path = Path(path)
    if path.exists():
        if read_json(path) != value:
            raise ValueError('Immutable output differs: ' + path.name)
    else:
        atomic_json(path, value)


def family_key(value):
    text = str(value or '').strip()
    return text if text not in {'0', 'None', 'null'} else ''


def codes(value):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    return sorted({re.sub(r'\s+', '', str(item.get('code', '') if isinstance(item, dict) else item)).upper()
                   for item in value if item})


def metadata(document):
    cpc, ipc = codes(document.get('cpc')), codes(document.get('ipc'))
    technical = {code[0] for code in cpc + ipc if re.match(r'^[A-H]\d{2}', code)}
    y_tags = sorted({code for code in cpc + ipc if re.match(r'^Y\d{2}', code)})
    country = str(document.get('country_code') or document.get('country') or '').strip().upper()
    number = str(document.get('publication_number') or document.get('identifier') or '')
    # Country metadata is preferable; the publication authority is an explicit fallback.
    country_source = 'metadata' if country else 'publication_authority'
    if not country and re.match(r'^[A-Z]{2}', number):
        country = number[:2]
    date = str(document.get('publication_date') or '')
    year = date[:4] if re.match(r'^(18|19|20|21)\d{2}', date) else str(document.get('year') or '')
    if not re.fullmatch(r'(18|19|20|21)\d{2}', year):
        year = 'UNKNOWN'
    return dict(cpc=cpc, ipc=ipc, sections=sorted(technical) or ['UNCLASSIFIED'],
                classification_basis='CPC+IPC' if cpc and ipc else 'CPC' if cpc else 'IPC' if ipc else 'NONE',
                y_tags=y_tags, country=country or 'UNKNOWN', country_source=country_source,
                year=year, publication_date=date, family_id=family_key(document.get('family_id')))


def prior_exclusions(ledger_path, page_paths):
    """Read old immutable pages only to recover classification and family metadata."""
    ledger = read_json(ledger_path)
    records = {r['identifier']: r for r in ledger.get('records', []) if r.get('status') in EXCLUDED}
    families = set()
    sections = Counter()
    countries = Counter()
    years = Counter()
    found = set()
    for path in page_paths:
        for doc in read_json(path).get('documents', []):
            number = doc.get('identifier') or doc.get('publication_number')
            if number not in records or number in found:
                continue
            found.add(number)
            info = metadata(doc)
            if info['family_id']:
                families.add(info['family_id'])
            if records[number]['status'] in REVIEWED:
                sections.update(info['sections'])
                countries.update([info['country']])
                years.update([info['year']])
    return dict(identifiers=sorted(records), family_ids=sorted(families),
                section_counts=dict(sections), country_counts=dict(countries), year_counts=dict(years),
                ledger_sha256=digest(ledger), excluded_records=len(records),
                directly_reviewed=sum(r['status'] in REVIEWED for r in records.values()),
                no_abstract=sum(r['status'] == 'NO_ABSTRACT' for r in records.values()),
                metadata_records_found=len(found), missing_metadata_records=len(records) - len(found))


def empty_state():
    return dict(version=VERSION, batch_number=0, collection=None, next_qdrant_offset=None,
                scroll_exhausted=False, assigned_counts={b: 0 for b in BUCKETS},
                section_counts={}, country_counts={}, year_counts={}, attempted_identifiers=[],
                queued_family_ids=[], round_robin=0, scanned_points=0, queued_records=0,
                unselected_records=0, analysis_performed=False, exhaustive_review_complete=False)


def pool_request(state, pool_limit=MAX_POOL):
    if state.get('version') != VERSION:
        raise ValueError('Unsupported queue version')
    if type(pool_limit) is not int or not 1 <= pool_limit <= MAX_POOL:
        raise ValueError('Pool limit must be 1..2000')
    if state['scroll_exhausted']:
        raise ValueError('This scroll ended; use a new queue version/directory for another pass')
    return dict(version=VERSION, operation='pool', offset=state['next_qdrant_offset'],
                expected_collection=state['collection'], pool_limit=pool_limit,
                state_sha256=digest(state))


def validate_pool(pool, state):
    inventory = pool['inventory']
    if inventory.get('version') != VERSION or inventory.get('operation') != 'pool':
        raise ValueError('Unexpected pool format')
    if inventory.get('state_sha256') != digest(state) or inventory.get('offset') != state['next_qdrant_offset']:
        raise ValueError('Pool does not belong to the current queue cursor')
    if state['collection'] and inventory['collection'] != state['collection']:
        raise ValueError('Collection changed')
    points = pool.get('points', [])
    if not isinstance(points, list) or len(points) > MAX_POOL or inventory.get('scanned_points') != len(points):
        raise ValueError('Invalid bounded pool size')
    if state['scroll_exhausted']:
        raise ValueError('Cannot append after scroll exhaustion')
    exhausted = inventory.get('scroll_exhausted')
    if not isinstance(exhausted, bool) or exhausted != (inventory.get('next_offset') is None):
        raise ValueError('Invalid scroll exhaustion marker')
    if not exhausted and inventory.get('next_offset') == inventory.get('offset'):
        raise ValueError('Qdrant cursor did not advance')


def select_pool(pool, state, prior, limit=MAX_SELECTED):
    """Deficit first, then round robin; sparse buckets and prior review gaps break ties.

    A multi-class patent is assigned once but retains every section. A-H and
    unclassified each receive turns when present. Country/year break candidate
    ties, not field quotas. This does not impose worldwide population weights.
    """
    if type(limit) is not int or not 1 <= limit <= MAX_SELECTED:
        raise ValueError('Selection limit must be 1..72')
    validate_pool(pool, state)
    excluded_ids = set(prior['identifiers']) | set(state['attempted_identifiers'])
    excluded_families = set(prior['family_ids']) | set(state['queued_family_ids'])
    candidates = []
    dispositions = []
    seen = set()
    for index, point in enumerate(pool['points']):
        payload = point.get('payload') or {}
        number = str(payload.get('publication_number') or '')
        point_id = str(point.get('id') or '')
        expected = str(uuid.uuid5(uuid.NAMESPACE_URL, 'triz:patent:' + number))
        reason = ''
        info = metadata(payload)
        if not re.fullmatch(r'[A-Z]{2}-[A-Z0-9]*\d[A-Z0-9]*-[A-Z][0-9]{0,2}', number) or point_id != expected:
            reason = 'INVALID_PUBLICATION_OR_HASH_ID'
        elif number in seen:
            reason = 'DUPLICATE_PUBLICATION'
        elif number in excluded_ids:
            reason = 'PREVIOUS_REVIEW_NO_ABSTRACT_OR_QUEUE'
        elif info['family_id'] and info['family_id'] in excluded_families:
            reason = 'PREVIOUS_FAMILY'
        seen.add(number)
        if reason:
            dispositions.append(dict(publication_number=number, point_id=point_id, status=reason))
        else:
            candidates.append(dict(publication_number=number, point_id=point_id, pool_index=index, **info))
    available = Counter(b for c in candidates for b in c['sections'])
    counts = Counter(state['assigned_counts'])
    countries = Counter(state['country_counts'])
    years = Counter(state['year_counts'])
    pointer = state['round_robin']
    selected = []
    while candidates and len(selected) < limit:
        buckets = {b for c in candidates for b in c['sections']}
        bucket = min(buckets, key=lambda b: (
            counts[b], prior.get('section_counts', {}).get(b, 0), available[b],
            (BUCKETS.index(b) - pointer) % len(BUCKETS)))
        options = [c for c in candidates if bucket in c['sections']]
        candidate = min(options, key=lambda c: (
            len(c['sections']), countries[c['country']], years[c['year']], c['pool_index']))
        candidate = {**candidate, 'assigned_bucket': bucket}
        selected.append(candidate)
        counts[bucket] += 1
        countries[candidate['country']] += 1
        years[candidate['year']] += 1
        pointer = (BUCKETS.index(bucket) + 1) % len(BUCKETS)
        remaining = []
        for item in candidates:
            if item['publication_number'] == candidate['publication_number']:
                continue
            if candidate['family_id'] and item['family_id'] == candidate['family_id']:
                dispositions.append(dict(publication_number=item['publication_number'],
                                         point_id=item['point_id'], status='DUPLICATE_SELECTED_FAMILY'))
            else:
                remaining.append(item)
        candidates = remaining
    dispositions.extend(dict(publication_number=c['publication_number'], point_id=c['point_id'],
                             status='ELIGIBLE_NOT_SELECTED_UNREVIEWED') for c in candidates)
    # Counterfactual equalized allocation exposes shortages even when a bucket is absent.
    target = Counter(state['assigned_counts'])
    target_pointer = state['round_robin']
    for _ in range(limit):
        bucket = min(BUCKETS, key=lambda b: (target[b], (BUCKETS.index(b) - target_pointer) % len(BUCKETS)))
        target[bucket] += 1
        target_pointer = (BUCKETS.index(bucket) + 1) % len(BUCKETS)
    result = dict(version=VERSION, batch_number=state['batch_number'] + 1,
                  state_sha256=digest(state), pool_sha256=digest(pool), prior_sha256=digest(prior),
                  limit=limit, selected=selected, dispositions=dispositions,
                  available_by_bucket={b: available[b] for b in BUCKETS},
                  target_cumulative_counts=dict(target), proposed_cumulative_counts=dict(counts),
                  proposed_deficits={b: max(0, target[b] - counts[b]) for b in BUCKETS},
                  absent_buckets=[b for b in BUCKETS if not available[b]], next_round_robin=pointer,
                  prior_summary={k: v for k, v in prior.items() if k not in {'identifiers', 'family_ids'}},
                  analysis_performed=False, external_llm_calls=0, caveat=CAVEAT)
    return result


def hydrate_request(selection):
    return dict(version=VERSION, operation='hydrate', selection_sha256=digest(selection),
                publication_numbers=[c['publication_number'] for c in selection['selected']])


def finish_batch(pool, selection, hydration, state, prior):
    """Validate selected-only SQL response, then queue readable abstracts locally."""
    validate_pool(pool, state)
    if selection != select_pool(pool, state, prior, selection['limit']):
        raise ValueError('Selection changed or exclusion ledger changed; regenerate selection')
    inventory = hydration['inventory']
    requested = [c['publication_number'] for c in selection['selected']]
    if (inventory.get('version') != VERSION or inventory.get('operation') != 'hydrate'
            or inventory.get('selection_sha256') != digest(selection)
            or inventory.get('requested_numbers') != requested):
        raise ValueError('Hydration does not match this selection')
    documents = hydration.get('documents', [])
    numbers = [d.get('publication_number') for d in documents]
    if len(numbers) != len(set(numbers)) or set(numbers) - set(requested) or len(documents) > MAX_SELECTED:
        raise ValueError('Hydration returned duplicate or unrequested documents')
    by_number = {d['publication_number']: d for d in documents}
    queued = []
    dispositions = list(selection['dispositions'])
    families = set(prior['family_ids']) | set(state['queued_family_ids'])
    counts = Counter(state['assigned_counts'])
    sections = Counter(state['section_counts'])
    countries = Counter(state['country_counts'])
    years = Counter(state['year_counts'])
    for candidate in selection['selected']:
        number = candidate['publication_number']
        doc = by_number.get(number)
        reason = ''
        if doc is None:
            reason = 'MISSING_SQL_DOCUMENT'
        elif doc.get('identifier') != number or not re.fullmatch(r'[0-9a-f]{64}', str(doc.get('content_hash') or '')):
            raise ValueError('Invalid hydrated source identity or content hash')
        elif not str(doc.get('abstract') or '').strip():
            reason = 'NO_ABSTRACT'
        else:
            info = metadata(doc)
            if candidate['assigned_bucket'] not in info['sections']:
                reason = 'CLASSIFICATION_CHANGED_SINCE_VECTOR_INDEX'
            elif info['family_id'] and info['family_id'] in families:
                reason = 'DUPLICATE_HYDRATED_FAMILY'
            else:
                if info['family_id']:
                    families.add(info['family_id'])
                fingerprint = digest({k: doc.get(k) for k in (
                    'identifier', 'content_hash', 'title', 'abstract', 'abstract_truncated', 'url', 'retrieval_scope')})
                queued.append({**doc, 'balanced_metadata': info, 'assigned_bucket': candidate['assigned_bucket'],
                               'point_id': candidate['point_id'], 'status': 'PENDING_REVIEW',
                               'source_fingerprint': fingerprint})
                counts[candidate['assigned_bucket']] += 1
                sections.update(info['sections'])
                countries.update([info['country']])
                years.update([info['year']])
                reason = 'PENDING_REVIEW'
        dispositions.append(dict(publication_number=number, point_id=candidate['point_id'], status=reason))
    next_state = {**state, 'batch_number': selection['batch_number'],
                  'collection': pool['inventory']['collection'],
                  'next_qdrant_offset': pool['inventory']['next_offset'],
                  'scroll_exhausted': pool['inventory']['scroll_exhausted'],
                  'assigned_counts': dict(counts), 'section_counts': dict(sections),
                  'country_counts': dict(countries), 'year_counts': dict(years),
                  'attempted_identifiers': sorted(set(state['attempted_identifiers']) | set(requested)),
                  'queued_family_ids': sorted(set(state['queued_family_ids']) |
                                              {d['balanced_metadata']['family_id'] for d in queued
                                               if d['balanced_metadata']['family_id']}),
                  'round_robin': selection['next_round_robin'],
                  'scanned_points': state['scanned_points'] + len(pool['points']),
                  'queued_records': state['queued_records'] + len(queued),
                  'unselected_records': state['unselected_records'] +
                      sum(d['status'] == 'ELIGIBLE_NOT_SELECTED_UNREVIEWED' for d in dispositions)}
    actual = Counter(d['assigned_bucket'] for d in queued)
    return dict(version=VERSION, batch_number=selection['batch_number'],
                input_sha256=digest(dict(pool=pool, selection=selection, hydration=hydration)),
                state_before_sha256=digest(state), state_after=next_state, documents=queued,
                inventory=dict(operation='balanced_review_queue', selected_for_hydration=len(requested),
                    queued_records=len(queued), disposition_counts=dict(Counter(d['status'] for d in dispositions)),
                    actual_assigned_counts={b: actual[b] for b in BUCKETS},
                    actual_section_counts=dict(Counter(b for d in queued for b in d['balanced_metadata']['sections'])),
                    actual_country_counts=dict(Counter(d['balanced_metadata']['country'] for d in queued)),
                    actual_year_counts=dict(Counter(d['balanced_metadata']['year'] for d in queued)),
                    deficits={b: max(0, selection['target_cumulative_counts'][b] - counts[b]) for b in BUCKETS},
                    missing_abstracts=sum(d['status'] == 'NO_ABSTRACT' for d in dispositions),
                    analysis_performed=False, exhaustive_review_complete=False, external_llm_calls=0,
                    caveat=CAVEAT), dispositions=dispositions,
                candidate_pool=pool, selection=selection)


def load_state(directory):
    path = Path(directory) / 'state.json'
    state = read_json(path) if path.exists() else empty_state()
    if state.get('version') != VERSION:
        raise ValueError('Unsupported queue version')
    return state


def commit_batch(directory, pool, selection, hydration, prior):
    """Immutable batch first, atomic cursor second; retry recovers between writes.

    A local exclusive lock prevents competing commits. No old manual page,
    review ledger, canonical research file, SQL row or vector is changed.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / '.commit.lock'
    with lock.open('x', encoding='utf-8') as handle:
        handle.write('local balanced queue commit\n')
    try:
        state = load_state(directory)
        path = directory / f"batch-{selection['batch_number']:06d}.json"
        expected_input = digest(dict(pool=pool, selection=selection, hydration=hydration))
        if path.exists():
            batch = read_json(path)
            if batch['input_sha256'] != expected_input or batch['selection']['prior_sha256'] != digest(prior):
                raise ValueError('Immutable batch inputs differ')
            if state == batch['state_after']:
                return batch
            if digest(state) != batch['state_before_sha256']:
                raise ValueError('Batch does not follow the current queue state')
        else:
            batch = finish_batch(pool, selection, hydration, state, prior)
            batch['created_at'] = datetime.now(timezone.utc).isoformat()
            immutable_json(path, batch)
        atomic_json(directory / 'state.json', batch['state_after'])
        return batch
    finally:
        lock.unlink()
