"""Ticket grants and debits are durable, authenticated, and atomic with creation."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, event, func, select

from api import main
from triz import pipeline, store
from triz.schema import GlobalState
from triz.settings import settings


def account(email=None, subject=None):
    return store.create_session(subject or uuid.uuid4().hex, email or uuid.uuid4().hex + '@example.test', 'Tester')


def charges(user_id):
    with store.engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(store.ticket_charges)
            .where(store.ticket_charges.c.user_id == user_id)).scalar_one()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, 'app_token', 'ticket-test-gateway')
    monkeypatch.setattr(settings, 'require_user_auth', True)
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    return TestClient(main.app)


def headers(user):
    return {'X-Triz-App-Token': 'ticket-test-gateway', 'X-Triz-Session': user['token']}


def submit(client, user, key=None, **data):
    return client.post('/api/runs', headers={**headers(user), 'Idempotency-Key': key or uuid.uuid4().hex},
        data={'query': '코팅 균일도를 개선하면서 재료 손실을 줄이는 문제', 'public_consent': 'true', **data})


def test_login_and_restart_never_replenish_initial_grant():
    subject = uuid.uuid4().hex
    first = account(subject=subject)
    assert first['user']['ticket_balance'] == 1
    state = GlobalState(run_id='run-' + uuid.uuid4().hex, user_id=first['user']['id'], raw_query='Question')
    store.create_run(state, charge_ticket=True)
    assert account(subject=subject)['user']['ticket_balance'] == 0
    for _ in range(2):
        store._initialized = False
        store.init()
        store.migrate_tickets()
        assert store.session_user(first['token'])['ticket_balance'] == 0
    assert charges(first['user']['id']) == 1


def test_existing_accounts_receive_initial_grant_without_new_login():
    # Represent accounts and an active session written before the new tables.
    ordinary, owner = account(), account(email=store.TICKET_OWNER_EMAIL)
    with store.engine.begin() as conn:
        conn.execute(delete(store.ticket_accounts).where(store.ticket_accounts.c.user_id.in_(
            [ordinary['user']['id'], owner['user']['id']])))
    store._initialized = False
    assert store.session_user(ordinary['token'])['ticket_balance'] == 1
    assert store.session_user(owner['token'])['ticket_balance'] == 100
    store.migrate_tickets()
    assert store.ticket_balance(owner['user']['id']) == 100


def test_owner_initial_grant_is_100_and_does_not_reset_spent_tickets(client):
    subject = uuid.uuid4().hex
    owner = account(email='Equipment0226@GMAIL.COM', subject=subject)
    assert owner['user']['ticket_balance'] == 100
    first = submit(client, owner)
    assert first.status_code == 202 and first.json()['ticket_balance'] == 99
    assert account(email=store.TICKET_OWNER_EMAIL, subject=subject)['user']['ticket_balance'] == 99
    store.migrate_tickets()
    assert store.ticket_balance(owner['user']['id']) == 99
    # A similar address does not qualify for the owner's allocation.
    assert account(email='equipment0226+other@gmail.com')['user']['ticket_balance'] == 1


def test_owner_recognition_only_adds_missing_initial_entitlement():
    subject = uuid.uuid4().hex
    user = account(subject=subject)
    store.create_run(GlobalState(run_id='run-' + uuid.uuid4().hex, user_id=user['user']['id'], raw_query='Question'),
        charge_ticket=True)
    assert account(email=store.TICKET_OWNER_EMAIL, subject=subject)['user']['ticket_balance'] == 99
    assert account(email=store.TICKET_OWNER_EMAIL, subject=subject)['user']['ticket_balance'] == 99


def test_concurrent_first_logins_grant_only_once():
    subject = uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=6) as pool:
        sessions = list(pool.map(lambda _: account(subject=subject), range(6)))
    assert len({session['user']['id'] for session in sessions}) == 1
    assert all(store.session_user(session['token'])['ticket_balance'] == 1 for session in sessions)


@pytest.mark.parametrize('ax_enabled', [False, True])
def test_new_question_consumes_one_and_retry_at_zero_is_free(client, monkeypatch, ax_enabled):
    monkeypatch.setenv('TRIZ_AX_ENABLED', str(ax_enabled).lower())
    user, key = account(), uuid.uuid4().hex
    first = submit(client, user, key)
    assert first.status_code == 202 and first.json()['ticket_balance'] == 0
    run_id = first.json()['run_id']
    retry = submit(client, user, key)
    assert retry.status_code == 202
    assert retry.json() == {'run_id': run_id, 'reused': True, 'ticket_balance': 0}
    assert submit(client, user, key, query='Different question').status_code == 409
    rejected = submit(client, user)
    assert rejected.status_code == 402
    assert rejected.json()['detail']['code'] == 'insufficient_tickets'
    assert rejected.json()['detail']['ticket_balance'] == 0
    assert len(store.list_runs(user_id=user['user']['id'])) == 1
    assert charges(user['user']['id']) == 1
    session = client.get('/internal/auth/session', headers=headers(user))
    assert session.json()['user']['ticket_balance'] == 0


def test_parallel_different_questions_cannot_overspend(client):
    user = account()
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: submit(client, user), range(8)))
    assert sorted(r.status_code for r in responses) == [202] + [402] * 7
    assert store.ticket_balance(user['user']['id']) == 0
    assert charges(user['user']['id']) == 1
    assert len(store.list_runs(user_id=user['user']['id'])) == 1


def test_parallel_same_submission_charges_once(client):
    user, key = account(), uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(lambda _: submit(client, user, key), range(6)))
    assert all(r.status_code in (202, 409) for r in responses)
    run_ids = {r.json()['run_id'] for r in responses if r.status_code == 202}
    assert len(run_ids) == 1
    assert submit(client, user, key).json()['run_id'] in run_ids
    assert store.ticket_balance(user['user']['id']) == 0 and charges(user['user']['id']) == 1


def test_busy_submission_has_retryable_error_code(client, monkeypatch):
    user = account()
    def busy(_):
        raise RuntimeError('Run is busy')
    monkeypatch.setattr(store, 'run_lock', busy)
    response = submit(client, user)
    assert response.status_code == 409 and response.json()['detail']['code'] == 'submission_in_progress'
    assert store.ticket_balance(user['user']['id']) == 1 and charges(user['user']['id']) == 0


def test_debit_is_atomic_across_independent_processes():
    user = account()
    # Separate interpreters share only the database, not a Python mutex.
    program = '''
import sys, uuid
from triz import store
from triz.schema import GlobalState
try:
    store.create_run(GlobalState(run_id='run-' + uuid.uuid4().hex, user_id=sys.argv[1], raw_query='Question'), charge_ticket=True)
except store.InsufficientTickets:
    sys.exit(2)
'''
    def create(_):
        return subprocess.run([sys.executable, '-c', program, user['user']['id']], capture_output=True, text=True, timeout=30)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(create, range(4)))
    assert sorted(outcome.returncode for outcome in outcomes) == [0, 2, 2, 2], [o.stderr for o in outcomes]
    assert store.ticket_balance(user['user']['id']) == 0 and charges(user['user']['id']) == 1


@pytest.mark.parametrize('data,status', [({'query': '  '}, 422), ({'mode': 'INVALID'}, 422),
    ({'public_consent': 'false'}, 422), ({'training_consent': 'INVALID'}, 422)])
def test_invalid_requests_do_not_consume_tickets(client, data, status):
    user = account()
    assert submit(client, user, **data).status_code == status
    assert store.ticket_balance(user['user']['id']) == 1 and charges(user['user']['id']) == 0


def test_rejected_attachment_does_not_consume_ticket(client):
    user = account()
    response = client.post('/api/runs', headers=headers(user),
        data={'query': 'Question', 'public_consent': 'true'}, files={'files': ('unsafe.exe', b'file')})
    assert response.status_code == 415
    assert store.ticket_balance(user['user']['id']) == 1 and charges(user['user']['id']) == 0


def test_failed_initial_state_write_rolls_back_debit_and_run(client):
    user = account()
    def fail_state_insert(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('INSERT INTO run_states'):
            raise RuntimeError('injected persistence failure')
    event.listen(store.engine, 'before_cursor_execute', fail_state_insert)
    try:
        with pytest.raises(RuntimeError, match='injected persistence failure'):
            submit(client, user)
    finally:
        event.remove(store.engine, 'before_cursor_execute', fail_state_insert)
    assert store.ticket_balance(user['user']['id']) == 1 and charges(user['user']['id']) == 0
    assert store.list_runs(user_id=user['user']['id']) == []
    assert submit(client, user).status_code == 202


def test_durable_pending_setup_is_recovered_without_another_ticket(client, monkeypatch):
    user, key = account(), uuid.uuid4().hex
    original = pipeline.finish_creation
    def fail(*args, **kwargs):
        raise RuntimeError('setup unavailable')
    monkeypatch.setattr(pipeline, 'finish_creation', fail)
    with pytest.raises(RuntimeError, match='setup unavailable'):
        submit(client, user, key)
    assert store.ticket_balance(user['user']['id']) == 0 and charges(user['user']['id']) == 1
    monkeypatch.setattr(pipeline, 'finish_creation', original)
    assert submit(client, user, key).status_code == 202
    assert charges(user['user']['id']) == 1


def test_balance_display_outage_does_not_prevent_accepted_dispatch(client, monkeypatch):
    user, started = account(), []
    def unavailable(_):
        raise RuntimeError('balance unavailable')
    monkeypatch.setattr(store, 'ticket_balance', unavailable)
    monkeypatch.setattr(pipeline, 'start', started.append)
    response = submit(client, user)
    assert response.status_code == 202
    assert started == [response.json()['run_id']]
    assert charges(user['user']['id']) == 1


def test_deleted_run_does_not_refund_or_allow_free_recreation(client):
    user, key = account(email=store.TICKET_OWNER_EMAIL), uuid.uuid4().hex
    first = submit(client, user, key)
    assert client.delete('/api/runs/' + first.json()['run_id'], headers=headers(user)).status_code == 200
    assert store.ticket_balance(user['user']['id']) == 99
    retry = submit(client, user, key)
    assert retry.status_code == 409 and retry.json()['detail']['code'] == 'submission_already_used'
    assert store.ticket_balance(user['user']['id']) == 99 and charges(user['user']['id']) == 1


def test_continuation_and_clarification_do_not_charge(client, monkeypatch):
    user = account()
    run_id = submit(client, user).json()['run_id']
    calls = []
    monkeypatch.setattr(pipeline, 'resume', lambda run, payload: calls.append(('resume', run)) or True)
    monkeypatch.setattr(pipeline, 'continue_run', lambda run: calls.append(('continue', run)) or True)
    monkeypatch.setattr(pipeline, 'rerun_from', lambda run, stage, instruction: calls.append(('rerun', run)) or True)
    for route, body in [('resume', {'payload': {'answer': 'clarification'}}), ('continue', {}),
                        ('rerun', {'stage': 's1_intake'})]:
        assert client.post(f'/api/runs/{run_id}/{route}', headers=headers(user), json=body).status_code == 200
    assert len(calls) == 3
    assert store.ticket_balance(user['user']['id']) == 0 and charges(user['user']['id']) == 1


def test_untrusted_request_cannot_create_account_or_override_ticket_balance(client):
    user = account()
    identity = {'subject': uuid.uuid4().hex, 'email': store.TICKET_OWNER_EMAIL, 'name': 'Spoofed'}
    assert client.post('/internal/auth/sessions', json=identity).status_code == 401
    assert client.post('/api/runs', headers={'X-Triz-App-Token': 'ticket-test-gateway'},
        data={'query': 'Question', 'public_consent': 'true'}).status_code == 401
    assert client.post('/api/runs', headers={**headers(user), 'X-Triz-Session': 'forged'},
        data={'query': 'Question', 'public_consent': 'true'}).status_code == 401
    assert store.ticket_balance(user['user']['id']) == 1
    assert submit(client, user, ticket_balance=100, email=store.TICKET_OWNER_EMAIL).status_code == 202
    assert submit(client, user, ticket_balance=100, email=store.TICKET_OWNER_EMAIL).status_code == 402
    assert store.ticket_balance(user['user']['id']) == 0
