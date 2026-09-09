"""python scripts/patent_corpus.py {probe,init,import,index,sync,status,benchmark}."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from triz import patent_corpus as corpus, patent_ingest as ingest
from triz.tools import vector_patents as vector


def emit(**data):
    print(json.dumps(data, ensure_ascii=False, default=str), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['probe', 'init', 'import', 'index', 'sync', 'status', 'benchmark'])
    parser.add_argument('--page-size', type=int, default=1000)
    parser.add_argument('--max-pages', type=int, default=0, help='0 = until source is exhausted; checkpoint retained')
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--max-batches', type=int, default=0)
    parser.add_argument('--force', action='store_true', help='Reconcile unchanged source again, retaining existing records')
    parser.add_argument('--query', action='append')
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 256 or args.max_batches < 0:
        parser.error('batch-size must be 1..256 and max-batches >= 0')
    try:
        if args.command == 'probe':
            emit(**ingest.probe(args.page_size))
            return 0
        corpus.init()
        if args.command == 'init':
            vector.ensure_collection()
            emit(phase='INITIALIZED')
        elif args.command in ('import', 'sync'):
            # Small alternating batches bound the backlog and make new records searchable
            # during long initial imports. Import/index may also run as separate processes.
            callback = (lambda: vector.index_pending(args.batch_size, args.max_batches, emit)) if args.command == 'sync' else None
            ingest.import_pages(args.page_size, args.max_pages, args.force, emit, callback)
            if args.command == 'sync':
                vector.index_pending(args.batch_size, args.max_batches, emit)
        elif args.command == 'index':
            vector.index_pending(args.batch_size, args.max_batches, emit)
        elif args.command == 'status':
            emit(**corpus.status())
        elif args.command == 'benchmark':
            queries = args.query or ['gasket spring preload', 'stacked chip thermal cooling',
                                     'substrate conveyor vibration isolation', '진동을 억제하면서 열을 배출하는 구조']
            elapsed = []
            for iteration in range(6):
                started = time.monotonic()
                results = vector.search_batch(queries)
                if any(d['status'] not in ('OK', 'EMPTY') and
                       {e['reason'] for e in d.get('errors', [])} != {'CORPUS_BUILDING'} for _, d in results):
                    emit(phase='BENCHMARK_FAILED', diagnostics=[d for _, d in results])
                    return 1
                ms = round((time.monotonic()-started)*1000)
                elapsed.append(ms)
                emit(iteration=iteration, batch_ms=ms, records=[len(h) for h, _ in results])
            emit(cold_batch_ms=elapsed[0], warm_batch_max_ms=max(elapsed[1:]),
                 warm_batch_mean_ms=sum(elapsed[1:])/5, queries_per_batch=len(queries),
                 note='Sample benchmark; full-corpus latency and recall require validation after indexing.')
        return 0
    except Exception as exc:
        # Driver errors may contain DSNs or SQL parameters. Expose only controlled codes.
        reason = str(exc)
        if not reason.isupper() or not reason.replace('_', '').isalnum() or len(reason) > 80:
            reason = type(exc).__name__
        emit(phase='FAILED', reason=reason)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
