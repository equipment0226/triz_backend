"""Record explicit abstract decisions in an independent balanced-review ledger.

Queueing and metadata scans never count as reading. Old sequential pages and
manual-progress.json stay unchanged. This command performs no network/model calls.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triz.effect_balanced_review import BUCKETS, immutable_json, read_json, atomic_json
from triz.effect_manual_review import record_decisions, source_fingerprint, merge_review_records


def summarize(batches, snapshots):
    decisions = {}
    for snapshot in snapshots:
        for row in snapshot['reviews']:
            identity = (row['identifier'], row['source_fingerprint'])
            if identity in decisions and decisions[identity] != row:
                raise ValueError('Conflicting immutable reviews: ' + row['identifier'])
            decisions[identity] = row
    documents = {}
    records = []
    counts = Counter()
    sections, countries, years, assigned = Counter(), Counter(), Counter(), Counter()
    for batch in batches:
        for doc in batch['documents']:
            identifier = doc['identifier']
            if identifier in documents:
                raise ValueError('Repeated queued publication: ' + identifier)
            fingerprint = source_fingerprint(doc)
            if fingerprint != doc['source_fingerprint']:
                raise ValueError('Changed immutable abstract: ' + identifier)
            documents[identifier] = doc
            decision = decisions.get((identifier, fingerprint))
            status = decision['decision'] if decision else 'PENDING_REVIEW'
            counts[status] += 1
            records.append(dict(identifier=identifier, source_fingerprint=fingerprint,
                content_hash=doc['content_hash'], status=status,
                keys=decision['keys'] if decision else [], reason=decision['reason'] if decision else ''))
            if decision:
                info = doc['balanced_metadata']
                assigned.update([doc['assigned_bucket']])
                sections.update(info['sections'])
                countries.update([info['country']])
                years.update([info['year']])
    reviewed = len(records) - counts['PENDING_REVIEW']
    selected = sum(b['inventory']['selected_for_hydration'] for b in batches)
    missing = sum(b['inventory']['missing_abstracts'] for b in batches)
    result = dict(mode='conversation_only', queue_version='balanced-patent-review-v1',
        batches=len(batches), metadata_points_scanned=sum(len(b['candidate_pool']['points']) for b in batches),
        selected_for_hydration=selected, queued_abstract_fields=len(documents),
        abstract_fields_directly_reviewed=reviewed, pending_review=counts['PENDING_REVIEW'],
        no_abstract=missing, decisions=dict(counts),
        reviewed_assigned_sections={b: assigned[b] for b in BUCKETS},
        reviewed_section_memberships=dict(sections), reviewed_publication_authorities=dict(countries),
        reviewed_years=dict(years), records=records,
        old_sequential_cursor_advanced=False, exhaustive_review_complete=False, external_llm_calls=0,
        caveat='Stored abstract fields only, including any explicitly deferred placeholder. No full-text or experimental validation. Metadata scans and missing abstracts are not reviews. A-H assignments are scheduling buckets, not population weights. Country can mean publication authority. Prior immutable reviews are excluded, not rebalanced retroactively.')
    return result, documents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--review-id', required=True)
    parser.add_argument('--research', type=Path, default=ROOT/'research/effects')
    parser.add_argument('--apply-links', action='store_true')
    args = parser.parse_args()
    if not args.review_id.replace('-', '').replace('_', '').isalnum():
        parser.error('review-id must contain only letters, digits, hyphens or underscores')
    batch = read_json(args.batch)
    if batch['version'] != 'balanced-patent-review-v1':
        parser.error('Unexpected queue version')
    canonical = {line.split('|')[0] for line in (args.research/'catalog.tsv').read_text(encoding='utf-8').splitlines()
                 if line.strip() and not line.startswith(('#', '@'))}
    # Bind every requested decision before attaching any canonical source.
    record_decisions(args.decisions, [batch], canonical,
        args.research/'balanced_reviews'/f'{args.review_id}.json')
    archive = args.research/'balanced_source_batches'/f"batch-{batch['batch_number']:06d}.json"
    immutable_json(archive, batch)
    batches = [read_json(p) for p in sorted(archive.parent.glob('batch-*.json'))]
    snapshots = [read_json(p) for p in sorted((args.research/'balanced_reviews').glob('*.json'))]
    summary, documents = summarize(batches, snapshots)
    if args.apply_links:
        merge_review_records(summary['records'], documents, args.research)
    atomic_json(args.research/'balanced-patent-progress.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'records'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
