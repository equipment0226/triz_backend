import importlib.util
from pathlib import Path
import sys
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def drawing(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / 'services/patent-drawing/app.py'
    spec = importlib.util.spec_from_file_location('patent_drawing_test_app', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, 'DATA', tmp_path)
    monkeypatch.setattr(mod, 'TOKEN', 'test-drawing-secret')
    # Model execution is explicitly separate from API contract tests.
    monkeypatch.setattr(mod, 'worker', lambda: None)
    with TestClient(mod.app) as client:
        yield mod, client


def test_private_idempotent_queue(drawing):
    mod, c = drawing
    body = dict(case_id='case-a', artifact_version_id='version-a', prompt='black line heat exchanger')
    headers = {'Authorization': 'Bearer test-drawing-secret', 'Idempotency-Key': 'first'}
    assert c.post('/v1/drawings', json=body).status_code == 401
    first = c.post('/v1/drawings', json=body, headers=headers)
    assert first.status_code == 202
    assert c.post('/v1/drawings', json=body, headers=headers).json() == first.json()
    assert c.post('/v1/drawings', json={**body, 'prompt': 'changed'}, headers=headers).status_code == 409
    job = first.json()['job_id']
    assert c.get('/v1/drawings/' + job).status_code == 401
    assert c.get('/v1/drawings/' + job + '/image', headers=headers).status_code == 409
    with mod.db() as db:
        db.execute("UPDATE jobs SET status='RUNNING' WHERE id=?", (job,))
    mod.init()
    result = c.get('/v1/drawings/' + job, headers=headers).json()
    assert result['status'] == 'INTERRUPTED'
    assert result['result']['compute_charge'] == 'UNKNOWN'


@pytest.mark.parametrize('change', [{'steps': 31}, {'width': 1024}, {'width': 257}, {'seed': -1}, {'model': 'arbitrary'}, {'prompt': ''}])
def test_resource_bounds(drawing, change):
    _, c = drawing
    response = c.post('/v1/drawings', headers={'Authorization': 'Bearer test-drawing-secret', 'Idempotency-Key': 'test'},
                      json={'case_id': 'a', 'artifact_version_id': 'b', 'prompt': 'drawing', **change})
    assert response.status_code == 422


def test_queue_bound(drawing):
    _, c = drawing
    for n in range(5):
        r = c.post('/v1/drawings', headers={'Authorization': 'Bearer test-drawing-secret', 'Idempotency-Key': str(n)},
                   json={'case_id': 'case-'+str(n), 'artifact_version_id': 'b', 'prompt': 'drawing'})
        assert r.status_code == (202 if n < 4 else 429)


def test_one_sample_per_case_even_with_new_idempotency_key(drawing):
    mod, c = drawing
    headers = {'Authorization': 'Bearer test-drawing-secret', 'Idempotency-Key': 'first'}
    body = {'case_id': 'a', 'artifact_version_id': 'b', 'prompt': 'drawing'}
    first = c.post('/v1/drawings', headers=headers, json=body).json()
    headers['Idempotency-Key'] = 'second'
    assert c.post('/v1/drawings', headers=headers, json=body).json() == first
    rejected = c.post('/v1/drawings', headers=headers, json={**body, 'prompt': 'different'})
    assert rejected.status_code == 409
    mod.init()
    assert c.post('/v1/drawings', headers=headers, json={**body, 'artifact_version_id': 'new'}).status_code == 409
