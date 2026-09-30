"""Rejected uploads cannot consume the volume or remove linked source data."""
import asyncio
import io
import threading
import uuid

import pytest
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks, UploadFile
from starlette.requests import Request

from api import main
from triz import pipeline, store
from triz.settings import settings


@pytest.fixture
def upload_client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'app_token', '')
    monkeypatch.setattr(settings, 'require_user_auth', False)
    monkeypatch.setattr(settings, 'storage_dir', tmp_path)
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    # Exercise real upload persistence and rejection, without document payloads.
    monkeypatch.setattr(main.docparse, 'extract', lambda path, name: ('measurements', []))
    existing = tmp_path / 'uploads' / 'existing-source.txt'
    existing.parent.mkdir()
    existing.write_bytes(b'existing project data')
    return TestClient(main.app), existing


def upload(client, files, key=None):
    return client.post('/api/runs', data={'query': '코팅 측정 데이터 검토'},
        headers={'Idempotency-Key': key} if key else {},
        files=[('files', (name, data, 'application/octet-stream')) for name, data in files])


@pytest.mark.parametrize('failure', ['first_parser', 'second_parser', 'second_extension', 'second_size'])
def test_rejected_batch_removes_only_this_request_files(upload_client, monkeypatch, failure):
    client, existing = upload_client
    if failure.endswith('parser'):
        def parse(path, name):
            if name == 'bad.pdf':
                raise ValueError('invalid file')
            return 'measurements', []
        monkeypatch.setattr(main.docparse, 'extract', parse)
    files = [('bad.pdf', b'invalid')] if failure == 'first_parser' else [('good.txt', b'valid')]
    if failure == 'second_parser':
        files.append(('bad.pdf', b'invalid'))
    elif failure == 'second_extension':
        files.append(('bad.exe', b'invalid'))
    elif failure == 'second_size':
        monkeypatch.setattr(settings, 'max_upload_bytes', 8)
        files.append(('large.txt', b'oversized file'))
    expected = {'second_extension': 415, 'second_size': 413}.get(failure, 422)
    for _ in range(3):
        assert upload(client, files).status_code == expected
        assert set(existing.parent.iterdir()) == {existing}
        assert existing.read_bytes() == b'existing project data'


def test_failed_creation_without_idempotency_leaves_no_unlinked_upload(upload_client, monkeypatch):
    client, existing = upload_client
    def fail(*args, **kwargs):
        raise RuntimeError('creation rejected before persistence')
    monkeypatch.setattr(main, '_create_submission', fail)
    with pytest.raises(RuntimeError, match='creation rejected'):
        upload(client, [('good.txt', b'valid')])
    assert set(existing.parent.iterdir()) == {existing}


@pytest.mark.parametrize('with_key', [False, True])
def test_partially_initialized_project_keeps_its_original_source(upload_client, monkeypatch, with_key):
    client, existing = upload_client
    before = {r['run_id'] for r in store.list_runs(limit=10000)}
    def fail(state, **kwargs):
        raise RuntimeError('initialization stopped after persistence')
    monkeypatch.setattr(pipeline, 'finish_creation', fail)
    with pytest.raises(RuntimeError, match='initialization stopped'):
        upload(client, [('good.txt', b'valid')], uuid.uuid4().hex if with_key else None)
    added = [r for r in store.list_runs(limit=10000) if r['run_id'] not in before]
    assert len(added) == 1
    state = store.load_state(added[0]['run_id'])
    attachment = state.intake.attachments[0]
    linked = existing.parent / attachment.storage_path
    assert linked.read_bytes() == b'valid'
    assert set(existing.parent.iterdir()) == {existing, linked}


def test_unknown_ownership_never_deletes_a_possible_project_source(upload_client, monkeypatch):
    _, existing = upload_client
    path = existing.parent / 'new-request.txt'
    path.write_bytes(b'may have been committed')
    def unavailable(_):
        raise RuntimeError('database unavailable')
    monkeypatch.setattr(store, 'load_state', unavailable)
    main._cleanup_submission_uploads([path], 'run-pending')
    assert path.read_bytes() == b'may have been committed'
    assert existing.read_bytes() == b'existing project data'


def test_cancelled_request_keeps_source_when_creation_thread_finishes(upload_client, monkeypatch):
    _, existing = upload_client
    before = {r['run_id'] for r in store.list_runs(limit=10000)}
    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    create = main._create_submission
    def pending(*args, **kwargs):
        started.set()
        try:
            assert release.wait(10)
            return create(*args, **kwargs)
        finally:
            finished.set()
    monkeypatch.setattr(main, '_create_submission', pending)
    async def disconnect():
        request = Request({'type': 'http', 'state': {'user_id': 'local'}})
        task = asyncio.create_task(main.create_run(request, BackgroundTasks(),
            query='Attachment cancellation test', mode=None, public_consent=False,
            training_consent=None, explicit_required_tracks=[],
            files=[UploadFile(io.BytesIO(b'preserve after disconnect'), filename='source.txt')],
            idempotency_key=''))
        try:
            assert await asyncio.to_thread(started.wait, 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            release.set()
        assert await asyncio.to_thread(finished.wait, 10)
    asyncio.run(disconnect())
    added = [r for r in store.list_runs(limit=10000) if r['run_id'] not in before]
    assert len(added) == 1
    state = store.load_state(added[0]['run_id'])
    linked = existing.parent / state.intake.attachments[0].storage_path
    assert linked.read_bytes() == b'preserve after disconnect'
    assert set(existing.parent.iterdir()) == {existing, linked}
