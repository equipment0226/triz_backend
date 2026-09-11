"""Resume every stored patent abstract in primary-key order and stage reviewed candidates.

The editorial effects catalog is deliberately not changed by this process.
Exact duplicate abstracts are linked in a SQLite ledger; different abstracts,
even from one patent family, are independently processed. Restart after a crash
with the same work directory. A new sweep rechecks hashes for changed/new rows.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'pilot'))
from triz.effect_mining import atomic_json,normalize


def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


@contextmanager
def exclusive_run(directory):
    """Hold an OS lock; it is released even when the worker is killed."""
    stream=(directory/'worker.lock').open('a+b')
    stream.seek(0,2)
    if stream.tell()==0:stream.write(b'0');stream.flush()
    stream.seek(0)
    try:
        if sys.platform=='win32':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        stream.close()
        raise RuntimeError('Another sweep already owns this work directory') from None
    try:yield
    finally:stream.close()


def open_ledger(directory):
    ledger=sqlite3.connect(directory/'ledger.sqlite3')
    ledger.execute('CREATE TABLE IF NOT EXISTS records (publication TEXT PRIMARY KEY, content_hash TEXT, abstract_hash TEXT, status TEXT, source_page TEXT)')
    ledger.execute('CREATE INDEX IF NOT EXISTS by_abstract ON records (abstract_hash)')
    ledger.execute('CREATE TABLE IF NOT EXISTS pages (sweep INTEGER, page INTEGER, state TEXT NOT NULL, receipt TEXT NOT NULL, PRIMARY KEY (sweep,page))')
    ledger.execute('CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY CHECK (id=1), state TEXT NOT NULL)')
    return ledger


def committed_progress(ledger,directory):
    # A crash between the database commit and JSON checkpoint must not cause
    # a page to be counted twice or its reviewed records to become "unchanged".
    latest=ledger.execute('SELECT state FROM checkpoint WHERE id=1').fetchone()
    if not latest:latest=ledger.execute('SELECT state FROM pages ORDER BY sweep DESC,page DESC LIMIT 1').fetchone()
    return json.loads(latest[0]) if latest else read(directory/'progress.json',{})


def commit_page(ledger,changes,state,receipt):
    with ledger:
        ledger.executemany('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?)',changes)
        ledger.execute('INSERT INTO pages VALUES (?,?,?,?)',
            (state['sweep'],state['pages'],json.dumps(state,ensure_ascii=False),json.dumps(receipt,ensure_ascii=False)))
        ledger.execute('INSERT OR REPLACE INTO checkpoint VALUES (1,?)',(json.dumps(state,ensure_ascii=False),))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,default=ROOT/'pilot/data/patent_effects_sweep')
    parser.add_argument('--page-size',type=int,default=400)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--max-pages',type=int,default=0,help='0 finishes the bounded sweep')
    parser.add_argument('--new-sweep',action='store_true')
    parser.add_argument('--direct',action='store_true',help='Read the configured corpus directly (server worker)')
    args=parser.parse_args()
    if not 1<=args.workers<=12 or not 1<=args.page_size<=1000:parser.error('invalid bounds')
    directory=args.work_dir.resolve(); directory.mkdir(parents=True,exist_ok=True)
    with exclusive_run(directory):
        return run_sweep(args,directory)


def run_sweep(args,directory):
    ledger=open_ledger(directory)
    state=committed_progress(ledger,directory)
    if args.new_sweep or not state:
        state=dict(sweep=int(state.get('sweep',0))+1,cursor='',upper_bound='',pages=0,scanned=0,analyzed=0,
                   duplicate_abstracts=0,unchanged=0,retained_candidates=0,readable_abstracts=0,empty_abstracts=0,status='STARTING')
    elif state.get('status')=='COMPLETE':
        print('Sweep complete. Use --new-sweep to find new or changed records.'); return 0
    # Upgrade the initial pilot checkpoint, which counted empty source reviews
    # together with actual abstract analysis.
    if 'readable_abstracts' not in state:
        state['readable_abstracts']=ledger.execute("SELECT count(*) FROM records WHERE abstract_hash<>'' AND status='ANALYZED'").fetchone()[0]
        state['empty_abstracts']=ledger.execute("SELECT count(*) FROM records WHERE abstract_hash=''").fetchone()[0]
    def progress(status,**values):
        state.update(status=status,updated_at=datetime.now(timezone.utc).isoformat(),**values)
        with ledger:
            ledger.execute('INSERT OR REPLACE INTO checkpoint VALUES (1,?)',(json.dumps(state,ensure_ascii=False),))
        atomic_json(directory/'progress.json',state)
        print(json.dumps(state,ensure_ascii=False),flush=True)
    def run(command,log):
        # Logs contain public research only. Provider output is suppressed by the
        # reviewed remote helper and extraction code.
        with log.open('a',encoding='utf-8') as stream:
            result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=stream)
        return result.returncode==0
    completed=0
    while not args.max_pages or completed<args.max_pages:
        name=f"sweep-{state['sweep']:03d}-page-{state['pages']+1:06d}"
        page=directory/name; page.mkdir(exist_ok=True)
        payload_path=page/'harvest.json'
        config=dict(cursor=state['cursor'],upper_bound=state['upper_bound'],limit=args.page_size)
        atomic_json(page/'request.json',config)
        progress('HARVESTING',active_page=name)
        if not payload_path.exists():
            if args.direct:
                from triz.effect_source_pages import harvest_page
                try:atomic_json(payload_path,harvest_page(**config))
                except Exception:
                    progress('RETRY_REQUIRED',failed_phase='harvest');return 1
            else:
                command=[sys.executable,str(ROOT/'deploy/patent_remote.py'),str(ROOT/'deploy/harvest_patent_page.py'),
                         '--params',str(page/'request.json'),'--output',str(payload_path)]
                for attempt in range(3):
                    if run(command,page/'harvest.log'):break
                    time.sleep(min(30,5*(attempt+1)))
                else:
                    progress('RETRY_REQUIRED',failed_phase='harvest');return 1
        payload=read(payload_path,{})
        inventory=payload['inventory']; records=payload['documents']
        if inventory['cursor']!=state['cursor'] or (state['upper_bound'] and inventory['upper_bound']!=state['upper_bound']):
            raise ValueError('Saved harvest does not match the committed cursor and upper bound')
        if not records:
            progress('COMPLETE',upper_bound=inventory['upper_bound']);return 0
        if not state['upper_bound']: state['upper_bound']=inventory['upper_bound']
        selected=[]; page_hashes={}; changes=[]; counts=dict(duplicate_abstracts=0,unchanged=0)
        for record in records:
            number=record['publication_number']; content_hash=record['content_hash']
            previous=ledger.execute('SELECT content_hash,status FROM records WHERE publication=?',(number,)).fetchone()
            if previous and previous[0]==content_hash:
                counts['unchanged']+=1;continue
            body=normalize(record.get('abstract'))
            body_hash=hashlib.sha256(body.encode()).hexdigest() if body else ''
            duplicate=(page_hashes.get(body_hash) or ledger.execute("SELECT publication FROM records WHERE abstract_hash=? AND status='ANALYZED' AND publication<>? LIMIT 1",(body_hash,number)).fetchone()) if body_hash else None
            if duplicate:
                status='DUPLICATE_ABSTRACT';counts['duplicate_abstracts']+=1
            else:
                status='ANALYZED' if body else 'INSUFFICIENT_TEXT';selected.append(record)
                if body_hash:page_hashes[body_hash]=number
            changes.append((number,content_hash,body_hash,status,name))
        atomic_json(page/'input.json',dict(inventory=inventory,documents=selected))
        retained=0
        if selected:
            progress('ANALYZING',page_records=len(records),page_unique_abstracts=len(selected))
            command=[sys.executable,str(ROOT/'pilot/scripts/refresh_effects.py'),'--input',str(page/'input.json'),
                '--work-dir',str(page/'mining'),'--review-dir',str(page/'review'),'--workers',str(args.workers)]
            for attempt in range(3):
                if run(command,page/'analysis.log'):break
                time.sleep(min(30,5*(attempt+1)))
            else:
                progress('RETRY_REQUIRED',failed_phase='extraction_or_review');return 1
            candidates=read(page/'review/reviewed-catalog.json',[])
            retained=sum(len(group['effects']) for group in candidates)
        # The page receipt lets audits distinguish reviewed candidate counts from
        # published canonical effects. Candidates still require semantic merging.
        readable=sum(bool(normalize(record.get('abstract'))) for record in selected)
        receipt=dict(records=len(records),analyzed=len(selected),readable_abstracts=readable,empty_abstracts=len(selected)-readable,
            **counts,retained_candidates=retained,cursor=inventory['next_cursor'],publication_status='EDITORIAL_REVIEW_REQUIRED')
        state.update(cursor=inventory['next_cursor'],pages=state['pages']+1,scanned=state['scanned']+len(records),
            analyzed=state['analyzed']+len(selected),retained_candidates=state['retained_candidates']+retained,
            readable_abstracts=state['readable_abstracts']+readable,empty_abstracts=state['empty_abstracts']+len(selected)-readable,
            status='COMPLETE' if inventory['complete'] else 'PAGE_COMPLETE',
            updated_at=datetime.now(timezone.utc).isoformat(),
            **{k:state[k]+v for k,v in counts.items()})
        commit_page(ledger,changes,state,receipt)
        atomic_json(page/'receipt.json',receipt)
        completed+=1
        progress('COMPLETE' if inventory['complete'] else 'PAGE_COMPLETE')
        if inventory['complete']: return 0
    progress('PAUSED_AT_PAGE_LIMIT')
    return 0

if __name__=='__main__':raise SystemExit(main())
