"""Client-carried state cannot be forged or silently replayed at the API bridge."""
import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.lab import router
from triz import lab_transport as lab
from triz.settings import settings


@pytest.fixture
def signed(monkeypatch):
    monkeypatch.setattr(settings, 'service_token', 'fixture-service-secret')
    monkeypatch.setattr(lab, 'current_fingerprint', lambda: 'native-contract-fixture')
    return lab.encode_continuation


def test_continuation_retains_pending_journal_without_state_service(signed):
    state = {'state': {'status': 'WAITING_HUMAN', 'pending': {'kind': 'DECIDE'},
        'cost': {'budget_usd': 5, 'total_usd': 0.3}},
        'journal': {'ax_tasks': [{'status': 'UNKNOWN', 'reserve': 99044, 'actual': None}]}}
    token = signed(state)
    assert lab.decode_continuation(token) == state
    assert 'fixture-service-secret' not in token


def test_altered_budget_and_other_service_cannot_resume(signed, monkeypatch):
    token = signed({'state': {'cost': {'budget_usd': 5}}})
    changed = token[:8] + ('A' if token[8] != 'A' else 'B') + token[9:]
    with pytest.raises(lab.LabInputError, match='무결성'):
        lab.decode_continuation(changed)
    monkeypatch.setattr(settings, 'service_token', 'another-service')
    with pytest.raises(lab.LabInputError, match='무결성'):
        lab.decode_continuation(token)


def test_changed_native_contract_and_decompressed_size_are_rejected(signed, monkeypatch):
    token = signed({'state': {'raw_query': 'a' * 4000}})
    monkeypatch.setattr(lab, 'MAX_SNAPSHOT_BYTES', 64)
    with pytest.raises(lab.LabInputError):
        lab.decode_continuation(token)
    monkeypatch.setattr(lab, 'MAX_SNAPSHOT_BYTES', 256 * 1024 * 1024)
    monkeypatch.setattr(lab, 'current_fingerprint', lambda: 'changed-prompt-or-knowledge')
    with pytest.raises(lab.LabInputError, match='버전'):
        lab.decode_continuation(token)


def test_no_paid_transport_retry_after_uncertain_completion(signed, monkeypatch):
    calls = []
    async def fail(payload):
        calls.append(payload)
        raise RuntimeError('provider or response uncertain')
    monkeypatch.setattr(lab, '_run_child', fail)
    with pytest.raises(RuntimeError, match='uncertain'):
        asyncio.run(lab.execute({'action': 'begin', 'raw_query': 'fixture problem', 'budget_usd': 5}))
    assert len(calls) == 1


@pytest.mark.parametrize('budget', [0, -1, 5.01, True, float('nan'), float('inf')])
def test_budget_bound_rejects_before_any_child(signed, monkeypatch, budget):
    calls = []
    async def child(payload):
        calls.append(payload)
        return {}
    monkeypatch.setattr(lab, '_run_child', child)
    with pytest.raises(lab.LabInputError):
        asyncio.run(lab.execute({'action': 'begin', 'raw_query': 'fixture problem', 'budget_usd': budget}))
    assert calls == []


def test_individual_inspection_keeps_candidate_ids_and_exclusions(signed):
    token = signed({'state': {'status': 'COMPLETED', 'concepts': [{'id': 'C1', 'evidence_ids': ['E1']}],
        'scratch': {'ax_excluded': [{'id': 'C10', 'evidence_ids': []}]},
        'constraint_checks': [{'concept_id': 'C1', 'status': 'PASS'}],
        'evaluation': {'evaluations': [{'concept_id': 'C1', 'score': 0.8}]},
        'evidence': [{'id': 'E1'}, {'id': 'E2'}],
        'steps': [{'output_json': {'concept_id': 'C1'}}, {'output_json': {'concept_id': 'C10'}}]}})
    rows = lab.inspect_solutions(token)['solutions']
    assert [row['candidate_id'] for row in rows] == ['C1', 'C10']
    assert rows[0]['evidence'] == [{'id': 'E1'}]
    assert rows[0]['validation_trace'] == [{'output_json': {'concept_id': 'C1'}}]
    assert rows[1]['included_in_current_portfolio'] is False
    assert lab.inspect_solutions(token, 'C1')['new_model_calls'] == 0
    with pytest.raises(lab.LabInputError, match='해당 해결안'):
        lab.inspect_solutions(token, 'missing')


def test_inspection_preserves_native_dropped_candidate_reviews(signed):
    rows = [
        {'concept_id': 'C1', 'disposition': 'RETAINED', 'validation': {'constraint_check': {'status': 'PASS'}}},
        {'concept_id': 'C10', 'disposition': 'EXCLUDED', 'exclusions': [{'reason': 'unsupported evidence'}],
         'validation': {'effect_reviews': [{'verdict': 'REJECT'}]}, 'evidence': []},
    ]
    token = signed({'state': {'status': 'COMPLETED', 'concepts': [{'id': 'C1'}]}, 'solutions': rows})
    assert lab.inspect_solutions(token)['solutions'] == rows
    assert lab.inspect_solutions(token, 'C10')['solutions'] == [rows[1]]
    assert lab.inspect_solutions(token, 'C1')['solutions'] == [rows[0]]


def test_api_requires_service_auth_and_rejects_forged_state_before_mcp(signed, monkeypatch):
    from triz import mcp_client
    calls = []
    async def call(payload):
        calls.append(payload)
        return {'status': 'CREATED'}
    monkeypatch.setattr(mcp_client, 'execute_lab', call)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.post('/internal/lab/begin', json={'raw_query': 'fixture'}).status_code == 401
        headers = {'Authorization': 'Bearer fixture-service-secret'}
        assert client.post('/internal/lab/begin', headers=headers, json={'continuation': 'forged'}).status_code == 422
        assert calls == []
        result = client.post('/internal/lab/begin', headers=headers, json={'raw_query': 'fixture'})
        assert result.status_code == 200
        assert calls[0]['action'] == 'begin'
