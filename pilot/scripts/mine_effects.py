"""Curate saved literature into the effects schema, with restartable batch records.

Example:
 python pilot/scripts/mine_effects.py --input .tmp/effect-sources.json \
   --work-dir pilot/data/effects_mining --output pilot/data/effects_mining/candidates.json
Failed batches can be retried with the identical command. A catalog is only
published when all source batches have completed; progress is never called full
patent-corpus coverage merely because an ANN search has finished.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triz.effect_mining import mine, export_catalog, atomic_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--batch-size',type=int,default=50)
    args = parser.parse_args()
    if args.output.resolve() == (Path(__file__).resolve().parents[1]/'triz/knowledge/effects.json').resolve():
        parser.error('자동 추출 결과는 정본 effects.json에 쓰지 않습니다. data/effects_mining/candidates.json을 사용하세요.')
    if not 1 <= args.workers <= 12 or not 1 <= args.batch_size <= 50:
        parser.error('workers: 1–12; batch-size: 1–50')
    payload = json.loads(args.input.read_text(encoding='utf-8'))
    original = json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else []
    args.work_dir.mkdir(parents=True,exist_ok=True)
    backup = args.work_dir / 'base-catalog.json'
    if not backup.exists(): atomic_json(backup,original)
    result = mine(payload['documents'],args.work_dir,workers=args.workers,batch_size=args.batch_size,
                  emit=lambda value: print(value,flush=True))
    if result['failed_batches']:
        print(json.dumps({'status':'INCOMPLETE','failed_batches':result['failed_batches'],'action':'rerun to resume; catalog not published'}))
        return 1
    catalog = export_catalog(result,original)
    atomic_json(args.output,catalog)
    reviews = Counter(r['status'] for batch in result['batches'] for r in batch.get('reviews',[]))
    report = {'completed_at':datetime.now(timezone.utc).isoformat(),'inventory':payload.get('inventory',{}),
              'source_reviews':dict(reviews),'function_groups':len(catalog),
              'total_effects':sum(len(g['effects']) for g in catalog),
              'literature_effects':sum(e.get('extraction_method') is not None for g in catalog for e in g['effects']),
              'failed_batches':0,'review_note':'Extracted from available abstracts/excerpts, not full-text review or independent technical validation.'}
    atomic_json(args.work_dir / 'report.json',report)
    print(json.dumps(report,ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
