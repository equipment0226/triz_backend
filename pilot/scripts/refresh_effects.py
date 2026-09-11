"""Resume literature extraction and review, keeping publication an editorial step."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Public documents + investigation inventory JSON')
    p.add_argument('--work-dir',type=Path,default=ROOT/'data/effects_mining')
    p.add_argument('--review-dir',type=Path,default=ROOT/'data/effects_review')
    p.add_argument('--workers',type=int,default=6)
    args=p.parse_args()
    if not 1<=args.workers<=12:p.error('workers must be 1-12')
    candidates=args.work_dir/'candidates.json'
    commands=[
        ['mine_effects.py','--input',str(args.input),'--work-dir',str(args.work_dir),'--output',str(candidates),'--workers',str(args.workers)],
        ['review_effects.py','--catalog',str(candidates),'--sources',str(args.work_dir/'sources.json'),'--work-dir',str(args.review_dir),'--workers',str(args.workers)],
    ]
    for script,*options in commands:
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*options])
        if result.returncode:return result.returncode
    print('Review complete. Edit research/effects/catalog.tsv to accept or consolidate mechanisms; then run publish_effects.py.')
    return 0
if __name__=='__main__':raise SystemExit(main())
