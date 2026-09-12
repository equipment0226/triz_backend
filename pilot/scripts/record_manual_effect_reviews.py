"""Record already-authored decisions and a resumable read-only patent cursor.

No extraction, summarization, automatic semantic deduplication or model calls.
--record creates an immutable decision/source binding; otherwise only reports
coverage using existing bindings. Changed sources require a new explicit review.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triz.effect_manual_review import read_pages, record_decisions, coverage, merge_explicit_links
from triz.effect_mining import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pages', type=Path, default=ROOT/'data/patent_effects_manual')
    parser.add_argument('--record', type=Path, help='Explicitly authored decision TSV')
    parser.add_argument('--review-id', help='New immutable review filename, e.g. 2026-09-12-01')
    parser.add_argument('--link-sources', action='store_true')
    args = parser.parse_args()
    directory = ROOT/'research/effects'
    pages = read_pages(sorted(args.pages.glob('page-*.json')))
    if not pages: parser.error('No source pages')
    if args.record:
        if not args.review_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.review_id):
            parser.error('--record requires a safe --review-id')
        keys = {line.split('|')[0] for line in (directory/'catalog.tsv').read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.startswith(('#', '@'))}
        record_decisions(args.record, pages, keys, directory/'manual_reviews'/f'{args.review_id}.json')
    snapshots = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((directory/'manual_reviews').glob('*.json'))]
    summary, records = coverage(pages, snapshots)
    atomic_json(args.pages/'review-ledger.json', dict(summary=summary, records=records))
    atomic_json(directory/'manual-progress.json', summary)
    atomic_json(args.pages/'next-request.json', dict(cursor=summary['cursor'], upper_bound=summary['upper_bound'], limit=200))
    if args.link_sources:
        merge_explicit_links(pages, snapshots, directory)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__': main()
