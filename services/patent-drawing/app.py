"""Private durable single-worker API, usable unchanged behind a GPU host later."""
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

DATA = Path(os.getenv('DRAWING_DATA_DIR', '/data'))
STOP = threading.Event()
TOKEN = os.getenv('PATENT_DRAWING_TOKEN', '')


class DrawingRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: str = Field(min_length=1, max_length=64)
    artifact_version_id: str = Field(min_length=1, max_length=64)
    prompt: str = Field(min_length=1, max_length=4000)
    negative_prompt: str = Field(default='photograph, color, shading, text, watermark, blurry', max_length=1000)
    seed: int = Field(default=42, ge=0, le=2147483647)
    steps: int = Field(default=20, ge=1, le=30)
    width: int = Field(default=512, ge=256, le=512)
    height: int = Field(default=512, ge=256, le=512)

    @model_validator(mode='after')
    def dimensions(self):
        if self.width % 64 or self.height % 64:
            raise ValueError('dimensions must be multiples of 64')
        return self


def db():
    c = sqlite3.connect(DATA / 'jobs.sqlite3', timeout=15)
    c.row_factory = sqlite3.Row
    return c


def init():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'images').mkdir(exist_ok=True)
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, body_hash TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created REAL NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS case_images (case_id TEXT PRIMARY KEY, job_id TEXT NOT NULL UNIQUE)')
        for row in c.execute('SELECT id,body FROM jobs ORDER BY created').fetchall():
            c.execute('INSERT OR IGNORE INTO case_images VALUES (?,?)', (json.loads(row['body'])['case_id'], row['id']))
        # An interrupted inference has unknown compute, never silently rerun it.
        c.execute("UPDATE jobs SET status='INTERRUPTED',result=? WHERE status='RUNNING'",
                  (json.dumps({'code': 'WORKER_RESTARTED', 'compute_charge': 'UNKNOWN'}),))


def worker():
    while not STOP.wait(1):
        with db() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute("SELECT * FROM jobs WHERE status='QUEUED' ORDER BY created LIMIT 1").fetchone()
            if row is None:
                continue
            c.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (row['id'],))
        request_path = DATA / 'images' / (row['id'] + '.request.json')
        image_path = DATA / 'images' / (row['id'] + '.png')
        request_path.write_text(row['body'], encoding='utf-8')
        status, result = 'FAILED', {'code': 'INFERENCE_FAILED', 'compute_charge': 'UNKNOWN'}
        proc = None
        try:
            proc = subprocess.Popen([sys.executable, str(Path(__file__).with_name('inference.py')),
                str(request_path), str(image_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + min(1800, int(os.getenv('DRAWING_TIMEOUT_SEC', '1200')))
            while proc.poll() is None and not STOP.wait(.5) and time.monotonic() < deadline:
                pass
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=15)
                result = {'code': 'INTERRUPTED' if STOP.is_set() else 'TIME_LIMIT', 'compute_charge': 'UNKNOWN'}
            elif proc.returncode == 0:
                result = json.loads(image_path.with_suffix('.json').read_text(encoding='utf-8'))
                status = 'COMPLETED'
            elif image_path.with_suffix('.error.json').exists():
                result.update(json.loads(image_path.with_suffix('.error.json').read_text(encoding='utf-8')))
        except Exception:
            if proc is not None and proc.poll() is None:
                proc.kill()
                proc.wait(timeout=15)
        finally:
            request_path.unlink(missing_ok=True)
        with db() as c:
            c.execute('UPDATE jobs SET status=?,result=? WHERE id=?', (status, json.dumps(result), row['id']))


@asynccontextmanager
async def lifespan(app):
    if not TOKEN:
        raise RuntimeError('PATENT_DRAWING_TOKEN is required')
    init()
    STOP.clear()
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    yield
    STOP.set()
    thread.join(timeout=20)


app = FastAPI(title='Private patent drawing worker', lifespan=lifespan, docs_url=None, redoc_url=None)


def authorize(authorization: str = Header(default='')):
    if not TOKEN or not secrets.compare_digest(authorization, 'Bearer ' + TOKEN):
        raise HTTPException(401, 'Unauthorized')


@app.get('/healthz')
def health():
    return {'ok': True, 'service': 'patent-drawing', 'device': os.getenv('DRAWING_DEVICE', 'cpu')}


@app.post('/v1/drawings', dependencies=[Depends(authorize)], status_code=202)
def create(body: DrawingRequest, idempotency_key: str = Header(min_length=1, max_length=160)):
    raw = json.dumps(body.model_dump(), sort_keys=True, ensure_ascii=False)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    key = hashlib.sha256((body.case_id + ':' + idempotency_key).encode()).hexdigest()
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        prior = c.execute('SELECT * FROM jobs WHERE request_key=?', (key,)).fetchone()
        if prior:
            if prior['body_hash'] != hashed:
                raise HTTPException(409, 'Idempotency conflict')
            return {'job_id': prior['id'], 'status': prior['status']}
        existing = c.execute('SELECT j.* FROM case_images q JOIN jobs j ON q.job_id=j.id WHERE q.case_id=?', (body.case_id,)).fetchone()
        if existing:
            if existing['body_hash'] == hashed:
                return {'job_id': existing['id'], 'status': existing['status']}
            raise HTTPException(409, 'CASE_IMAGE_LIMIT: one generated sample image per patent case')
        if c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('RUNNING','QUEUED')").fetchone()[0] >= 4:
            raise HTTPException(429, 'Drawing queue is full')
        job_id = uuid.uuid4().hex
        c.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',
            (job_id, key, hashed, raw, 'QUEUED', None, time.time()))
        c.execute('INSERT INTO case_images VALUES (?,?)', (body.case_id, job_id))
    return {'job_id': job_id, 'status': 'QUEUED'}


def get_job(job_id):
    with db() as c:
        row = c.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Not found')
    return row


@app.get('/v1/drawings/{job_id}', dependencies=[Depends(authorize)])
def get(job_id: str):
    row = get_job(job_id)
    return {'job_id': row['id'], 'status': row['status'], 'result': json.loads(row['result']) if row['result'] else None}


@app.get('/v1/drawings/{job_id}/image', dependencies=[Depends(authorize)])
def image(job_id: str):
    row = get_job(job_id)
    if row['status'] != 'COMPLETED':
        raise HTTPException(409, 'Image is not ready')
    return FileResponse(DATA / 'images' / (row['id'] + '.png'), media_type='image/png',
                        headers={'Cache-Control': 'private, no-store'})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='::', port=int(os.getenv('PORT', '8000')), workers=1)
