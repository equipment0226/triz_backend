"""Keep the resumable patent effect sweep running on a persistent server volume."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

PILOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PILOT))
from triz.effect_mining import atomic_json
from sweep_patent_effects import exclusive_run


def bootstrap(directory,archive):
    # Mounts survive deployments. A seed is only used for a completely new
    # volume; it must never overwrite a more advanced server checkpoint.
    if (directory/'ledger.sqlite3').exists():return
    if not archive.exists():return
    with zipfile.ZipFile(archive) as seed:
        # Install the ledger last: its presence certifies all accompanying
        # evidence/checkpoint files were copied, even after bootstrap interruption.
        for item in sorted(seed.infolist(),key=lambda item:item.filename=='ledger.sqlite3'):
            target=(directory/item.filename).resolve()
            if not target.is_relative_to(directory.resolve()):raise ValueError('Unsafe seed path')
            if item.is_dir():continue
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_suffix(target.suffix+'.seed-tmp')
            with seed.open(item) as source,temporary.open('wb') as output:shutil.copyfileobj(source,output)
            temporary.replace(target)
    print('Restored previously reviewed patent pages onto the persistent volume.',flush=True)


def main():
    directory=Path(os.environ.get('EFFECT_SWEEP_DIR','/data/patent_effects_sweep'))
    directory.mkdir(parents=True,exist_ok=True)
    bootstrap(directory,PILOT.parent/'seed.zip')
    # A second deployment on the same mounted volume cannot launch a second
    # paid extraction process. The child separately owns the actual sweep lock.
    supervisor=directory/'supervisor';supervisor.mkdir(exist_ok=True)
    with exclusive_run(supervisor):
        while True:
            command=[sys.executable,str(PILOT/'scripts/sweep_patent_effects.py'),'--direct',
                '--work-dir',str(directory),'--page-size',os.environ.get('EFFECT_SWEEP_PAGE_SIZE','400'),
                '--workers',os.environ.get('EFFECT_SWEEP_WORKERS','4')]
            result=subprocess.run(command,cwd=PILOT.parent)
            state=json.loads((directory/'progress.json').read_text()) if (directory/'progress.json').exists() else {}
            status='COMPLETE' if result.returncode==0 and state.get('status')=='COMPLETE' else 'RETRYING'
            atomic_json(directory/'worker-status.json',dict(status=status,at=datetime.now(timezone.utc).isoformat(),
                exit_code=result.returncode,scanned=state.get('scanned',0),cursor=state.get('cursor','')))
            if status=='COMPLETE':
                print('Bounded sweep complete; reviewed candidates await editorial publication.',flush=True)
                return 0
            print('Sweep interrupted; retrying from durable checkpoint in 60 seconds.',flush=True)
            time.sleep(60)


if __name__=='__main__':raise SystemExit(main())
