"""Serialize explicit human/conversation decisions. No semantic inference or API.

An immutable review binds each authored decision to the exact source content.
Fetching, a missing abstract, or an older decision never counts as a fresh read.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .effect_mining import atomic_json, digest

DECISIONS = {'LINK', 'DEFER', 'DESIGN_ONLY', 'REJECT_CLAIM'}


def source_fingerprint(document):
    return digest({k: document.get(k) for k in (
        'identifier', 'content_hash', 'title', 'abstract', 'abstract_truncated',
        'url', 'retrieval_scope')})


def read_pages(paths):
    pages = [json.loads(Path(p).read_text(encoding='utf-8')) for p in paths]
    previous = ''; upper = None; identifiers = set()
    for page in pages:
        inventory = page['inventory']; documents = page['documents']
        if inventory['cursor'] != previous:
            raise ValueError('Noncontiguous page cursor')
        if upper is not None and inventory['upper_bound'] != upper:
            raise ValueError('Mixed sweep upper bounds')
        upper = inventory['upper_bound']
        if inventory['exported_records'] != len(documents):
            raise ValueError('Incorrect page record count')
        for document in documents:
            identifier = document['identifier']
            if identifier in identifiers or not previous < identifier <= upper:
                raise ValueError('Duplicate or out-of-order source: '+identifier)
            identifiers.add(identifier); previous = identifier
        if inventory['next_cursor'] != previous:
            raise ValueError('Incorrect next cursor')
    return pages


def record_decisions(decision_path, pages, canonical_keys, output):
    """Bind the supplied editorial TSV to source hashes, without judging its text."""
    documents = {d['identifier']: d for p in pages for d in p['documents']}
    reviews = []; seen = set()
    raw = Path(decision_path).read_text(encoding='utf-8').encode('utf-8')
    for line in raw.decode('utf-8').splitlines():
        if not line.strip() or line.startswith('#'): continue
        identifier, decision, keys, reason = line.split('|')
        keys = list(filter(None, keys.split(',')))
        if identifier in seen: raise ValueError('Duplicate decision: '+identifier)
        seen.add(identifier)
        if decision not in DECISIONS or not reason.strip():
            raise ValueError('Invalid decision: '+identifier)
        if (decision == 'LINK') != bool(keys) or set(keys)-set(canonical_keys):
            raise ValueError('Invalid canonical links: '+identifier)
        document = documents.get(identifier)
        if not document or not document.get('abstract', '').strip():
            raise ValueError('An explicit read needs an available abstract: '+identifier)
        reviews.append(dict(identifier=identifier, source_fingerprint=source_fingerprint(document),
            content_hash=document.get('content_hash'), decision=decision, keys=keys, reason=reason))
    result = dict(method='conversation_reasoning', external_llm_calls=0,
        decisions_sha256=hashlib.sha256(raw).hexdigest(), reviews=reviews)
    output = Path(output)
    if output.exists():
        existing = json.loads(output.read_text(encoding='utf-8'))
        if any(existing.get(k) != v for k, v in result.items()):
            raise ValueError('Immutable review already exists; use a new review file for changed sources or decisions')
        return existing
    result['recorded_at'] = datetime.now(timezone.utc).isoformat()
    atomic_json(output, result)
    return result


def coverage(pages, snapshots):
    reviews = {(r['identifier'], r['source_fingerprint']): r
               for s in snapshots for r in s['reviews']}
    counts = Counter(); records = []; cursor = ''; prefix_complete = True
    completed_pages = 0
    for page in pages:
        page_complete = True
        for document in page['documents']:
            identifier = document['identifier']; fingerprint = source_fingerprint(document)
            review = reviews.get((identifier, fingerprint))
            if not document.get('abstract', '').strip():
                status = 'NO_ABSTRACT'
            elif review:
                status = review['decision']
            else:
                status = 'PENDING_REVIEW'; page_complete = False
            counts[status] += 1
            records.append(dict(identifier=identifier, source_fingerprint=fingerprint,
                content_hash=document.get('content_hash'), status=status,
                keys=review['keys'] if review else [], reason=review['reason'] if review else ''))
        prefix_complete = prefix_complete and page_complete
        if prefix_complete:
            cursor = page['inventory']['next_cursor']; completed_pages += 1
    latest = pages[-1]['inventory'] if pages else {}
    summary = dict(mode='conversation_only', scope='all_stored_patents_all_industries_including_IT',
        fetched_records=len(records), abstracts_directly_reviewed=sum(counts[s] for s in DECISIONS),
        no_abstract=counts['NO_ABSTRACT'], pending_review=counts['PENDING_REVIEW'],
        decisions=dict(counts), completed_pages=completed_pages, cursor=cursor,
        fetched_cursor=latest.get('next_cursor', ''), upper_bound=latest.get('upper_bound', ''),
        corpus_documents_at_latest_fetch=latest.get('corpus_accounting', {}).get('documents'),
        corpus_observed_at=latest.get('created_at'),
        sweep_complete=bool(pages and prefix_complete and latest.get('complete')),
        external_llm_calls=0,
        caveat='Stored abstracts only. Missing abstracts are not analyzed. Newly inserted or changed earlier keys require another sweep; this is not a transaction snapshot.')
    return summary, records


def merge_explicit_links(pages, snapshots, directory):
    """Attach only authored LINK decisions with matching source fingerprints."""
    directory = Path(directory)
    def read(name):
        path = directory/name
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    sources = read('accepted_literature_sources.json'); links = read('literature_links.json')
    documents = {d['identifier']: d for p in pages for d in p['documents']}
    _, records = coverage(pages, snapshots)
    for row in records:
        if row['status'] != 'LINK': continue
        document = documents[row['identifier']]
        source_id = 'MANUAL-'+row['identifier']+'-'+row['source_fingerprint'][:12]
        sources[source_id] = dict(sources=[dict(identifier=document['identifier'],
            title=document['title'], url=document['url'], source_type='PATENT',
            retrieval_scope='stored_patent_abstract', review_method='conversation_reasoning',
            source_fingerprint=row['source_fingerprint'], review_note=row['reason'])])
        for key in row['keys']:
            links[key] = list(dict.fromkeys([*links.get(key, []), source_id]))
    atomic_json(directory/'accepted_literature_sources.json', sources)
    atomic_json(directory/'literature_links.json', links)
