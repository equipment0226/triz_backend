"""Prepare a separate bounded review queue; remote reads require explicit commands.

request -> remote pool -> select -> remote hydrate -> commit. Existing immutable
manual-review pages and coverage are read for exclusions and never updated here.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triz import effect_balanced_review as queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['request', 'select', 'commit', 'status'])
    parser.add_argument('--queue', type=Path, default=ROOT/'data/patent_effects_balanced_v1')
    parser.add_argument('--prior-pages', type=Path, default=ROOT/'data/patent_effects_manual')
    parser.add_argument('--pool', type=Path)
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--hydration', type=Path)
    parser.add_argument('--output', type=Path, help='Request or selection output; choose a new filename per batch')
    parser.add_argument('--hydrate-request', type=Path)
    parser.add_argument('--pool-limit', type=int, default=queue.MAX_POOL)
    parser.add_argument('--limit', type=int, default=queue.MAX_SELECTED)
    args = parser.parse_args()
    # Never permit queue state or generated requests to overwrite the old pages.
    old = args.prior_pages.resolve()
    outputs = [args.queue, args.output, args.hydrate_request]
    if any(path and (path.resolve() == old or old in path.resolve().parents) for path in outputs):
        parser.error('Balanced queue outputs must be separate from existing manual pages')
    state = queue.load_state(args.queue)
    if args.action == 'request':
        if not args.output:
            parser.error('request requires --output')
        result = queue.pool_request(state, args.pool_limit)
        queue.immutable_json(args.output, result)
    elif args.action in {'select', 'commit'}:
        if not args.pool:
            parser.error('select/commit requires --pool')
        prior = queue.prior_exclusions(args.prior_pages/'review-ledger.json', sorted(args.prior_pages.glob('page-*.json')))
        pool = queue.read_json(args.pool)
        if args.action == 'select':
            if not args.output or not args.hydrate_request:
                parser.error('select requires --output and --hydrate-request')
            selection = queue.select_pool(pool, state, prior, args.limit)
            queue.immutable_json(args.output, selection)
            queue.immutable_json(args.hydrate_request, queue.hydrate_request(selection))
            result = dict(batch_number=selection['batch_number'], selected=len(selection['selected']),
                          available_by_bucket=selection['available_by_bucket'],
                          proposed_deficits=selection['proposed_deficits'],
                          absent_buckets=selection['absent_buckets'], analysis_performed=False)
        else:
            if not args.selection or not args.hydration:
                parser.error('commit requires --selection and --hydration')
            batch = queue.commit_batch(args.queue, pool, queue.read_json(args.selection),
                                       queue.read_json(args.hydration), prior)
            result = {**batch['inventory'], 'batch_number': batch['batch_number']}
    else:
        result = {k: v for k, v in state.items() if k not in {'attempted_identifiers', 'queued_family_ids'}}
        result['caveat'] = queue.CAVEAT
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
