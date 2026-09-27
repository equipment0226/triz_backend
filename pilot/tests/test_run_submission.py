import asyncio
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from api.main import app
from triz import pipeline, store
from triz.settings import settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, 'app_token', '')
    monkeypatch.setattr(settings, 'require_user_auth', False)
    return TestClient(app)


def submit(client, key, **kwargs):
    return client.post('/api/runs', headers={'Idempotency-Key': key},
        data={'query': '유리 기판의 코팅 균일도를 개선합니다.', 'mode': 'DEEP', 'public_consent': 'true', **kwargs})


def test_dispatch_failure_still_returns_project_and_retry_reuses_it(client, monkeypatch):
    monkeypatch.setattr(pipeline.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(settings, 'orchestrator', 'n8n')
    monkeypatch.setattr(settings, 'n8n_webhook_url', 'https://dispatcher.invalid/webhook')
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise httpx.ConnectError('dispatcher unavailable')
    monkeypatch.setattr(pipeline.httpx, 'post', fail)
    key = uuid.uuid4().hex
    first = submit(client, key)
    assert first.status_code == 202
    run_id = first.json()['run_id']
    assert store.load_state(run_id).status == 'INTERRUPTED'
    retry = submit(client, key)
    assert retry.status_code == 202 and retry.json() == {'run_id': run_id, 'reused': True}
    assert calls == [1] * pipeline.DISPATCH_ATTEMPTS
    assert client.get(f'/api/runs/{run_id}/view').json()['status'] == 'INTERRUPTED'
    assert store.is_published(run_id)


def test_same_key_cannot_change_problem(client, monkeypatch):
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    key = uuid.uuid4().hex
    first = submit(client, key)
    assert submit(client, key, query='다른 문제입니다.').status_code == 409
    assert store.load_state(first.json()['run_id']).raw_query.startswith('유리 기판')


def test_owner_scoping_and_parallel_retries(client, monkeypatch):
    monkeypatch.setattr(settings, 'require_user_auth', True)
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    accounts = [store.create_session(uuid.uuid4().hex, f'{uuid.uuid4().hex}@example.com', 'Test') for _ in range(2)]
    key = uuid.uuid4().hex
    def send(account):
        return client.post('/api/runs', headers={'Idempotency-Key': key, 'X-Triz-Session': account['token']},
            data={'query': '동일한 문제', 'public_consent': 'true'})
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: send(accounts[0]), range(4)))
    assert all(r.status_code in (202, 409) for r in responses)
    ids = {r.json()['run_id'] for r in responses if r.status_code == 202}
    assert len(ids) == 1
    assert send(accounts[0]).json()['run_id'] in ids
    assert send(accounts[1]).json()['run_id'] not in ids
    assert len(store.list_runs(user_id=accounts[0]['user']['id'])) == 1


def test_response_precedes_dispatch_completion(client, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    def slow_start(_):
        started.set()
        assert release.wait(10)
    monkeypatch.setattr(pipeline, 'start', slow_start)
    # Observe ASGI sends directly: TestClient waits for background work itself.
    async def check():
        from starlette.requests import Request
        from starlette.background import BackgroundTasks
        from fastapi.responses import JSONResponse
        from api.main import create_run
        background = BackgroundTasks()
        result = await create_run(Request({'type': 'http'}), background,
            query='응답 지연 검증', mode='FULL', public_consent=False, files=[], idempotency_key=uuid.uuid4().hex)
        response = JSONResponse(result, status_code=202, background=background)
        sent = []
        async def send(message):
            sent.append(message)
            if message['type'] == 'http.response.body':
                assert not started.is_set()
                release.set()
        await response({'type': 'http'}, None, send)
        assert sent[0]['status'] == 202 and started.is_set()
    asyncio.run(check())


def test_created_run_recovers_if_process_stops_before_dispatch(client):
    state = pipeline.create_run('서버 재시작 사이에 접수된 문제')
    state.scratch['execution_progress_at'] = time.time() - pipeline.DISPATCH_GRACE_SECONDS - 10
    store.save_state(state)
    assert state.run_id in pipeline.recover_orphans()
    assert store.load_state(state.run_id).status == 'INTERRUPTED'


def test_retry_recovers_partially_initialized_project(client, monkeypatch):
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    original = pipeline.finish_creation
    def fail(*args, **kwargs):
        raise RuntimeError('setup unavailable')
    monkeypatch.setattr(pipeline, 'finish_creation', fail)
    key = uuid.uuid4().hex
    with pytest.raises(RuntimeError, match='setup unavailable'):
        submit(client, key)
    before = {r['run_id'] for r in store.list_runs(limit=1000)}
    monkeypatch.setattr(pipeline, 'finish_creation', original)
    recovered = submit(client, key)
    assert recovered.status_code == 202
    assert recovered.json()['run_id'] in before
    assert not store.load_state(recovered.json()['run_id']).scratch.get('creation_pending')


def test_attachment_retry_keeps_original_and_removes_temporary_copies(client, monkeypatch):
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    key = uuid.uuid4().hex
    def upload(content=b'coating measurements'):
        return client.post('/api/runs', headers={'Idempotency-Key':key}, data={'query':'첨부된 코팅 측정 데이터'},
            files={'files':('measurements.txt',content,'text/plain')})
    first = upload()
    assert first.status_code == 202
    run_id = first.json()['run_id']
    stored = store.load_state(run_id).intake.attachments[0]
    original = settings.storage_dir/'uploads'/stored.storage_path
    before = set(original.parent.iterdir())
    assert upload().json()['run_id'] == run_id
    assert upload(b'different measurements').status_code == 409
    assert original.read_bytes() == b'coating measurements'
    assert set(original.parent.iterdir()) == before
