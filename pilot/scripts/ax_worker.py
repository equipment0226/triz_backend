"""Run separately from the API: python scripts/ax_worker.py [--once]. No paid APIs."""
import argparse
import os
import json
import signal
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triz.ax.worker import tick

def main():
    if hasattr(os,'nice'):
        os.nice(10)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--once',action='store_true')
    args=p.parse_args()
    stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    while not stopping:
        print(json.dumps(tick(),ensure_ascii=False),flush=True)
        if args.once: break
        for _ in range(30):
            if stopping: break
            time.sleep(1)

if __name__=='__main__': main()
