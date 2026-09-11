"""Resume the independent source review, publishing only a complete pass."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triz.effect_review import review_catalog,apply_reviews
from triz.effect_mining import atomic_json

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--catalog',type=Path,required=True)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--work-dir',type=Path,required=True)
    p.add_argument('--workers',type=int,default=8)
    a=p.parse_args()
    if not 1<=a.workers<=12:p.error('workers must be 1-12')
    snapshot=a.work_dir/'input-catalog.json'
    atomic_json(snapshot,json.loads(a.catalog.read_text(encoding='utf-8')))
    catalog=json.loads(snapshot.read_text(encoding='utf-8'))
    documents=json.loads(a.sources.read_text(encoding='utf-8'))['documents']
    results=review_catalog(catalog,documents,a.work_dir/'batches',workers=a.workers,emit=lambda s:print(s,flush=True))
    if any(r['status']!='COMPLETE' for r in results):return 1
    reviewed,rejected=apply_reviews(catalog,results)
    atomic_json(a.work_dir/'reviewed-catalog.json',reviewed)
    atomic_json(a.work_dir/'rejected.json',rejected)
    print(json.dumps({'status':'COMPLETE','retained':sum(len(g['effects']) for g in reviewed),'rejected':len(rejected)}))
    return 0

if __name__=='__main__':raise SystemExit(main())
