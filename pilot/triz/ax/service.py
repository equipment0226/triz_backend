"""Supervise one separate CPU trainer process inside the existing backend service."""
import asyncio
import logging
import os
from pathlib import Path
import subprocess
import sys


async def supervise():
    worker=Path(__file__).resolve().parents[2]/'scripts'/'ax_worker.py'
    child=None
    try:
        while True:
            if child is None or child.poll() is not None:
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                child=subprocess.Popen([sys.executable,str(worker)],creationflags=flags)
                logging.getLogger(__name__).info('AX CPU worker started')
            await asyncio.sleep(30)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                await asyncio.to_thread(child.wait,timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                await asyncio.to_thread(child.wait)
