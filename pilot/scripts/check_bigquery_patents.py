"""Run from pilot/: python scripts/check_bigquery_patents.py [--execute].

Default: free metadata + dry run only. Never prints credentials or raw exceptions.
--execute: run the same bounded search path used by the analysis pipeline.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from triz.tools import bigquery_patents as patents


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--query', action='append', help='Repeat to test multiple queries in one job')
    args = parser.parse_args()
    queries = args.query or ['gasket spring preload', 'stacked chip thermal cooling',
                             'substrate conveyor vibration isolation']
    try:
        preflight = patents.preflight(queries)
        print(json.dumps(preflight, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'status':'UNAVAILABLE', 'error':patents._error(exc)}, ensure_ascii=False))
        return 1
    if args.execute:
        results = patents.search_batch(queries)
        print(json.dumps([{'query':q, 'diagnostics':d, 'records':[
            {k:r[k] for k in ('identifier','title','url')} for r in records]}
            for q,(records,d) in zip(queries,results)], ensure_ascii=False))
        return int(any(d['status'] == 'UNAVAILABLE' for _,d in results))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
