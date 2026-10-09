"""Authenticated, process-isolated TRIZ tests with client-carried continuation.

Only the child uses a journal, entirely in memory. This module never loads or
saves a production run and never retries a paid stage after a transport error.
"""
from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import hmac
import io
import json
import os
import sys
import tempfile
from pathlib import Path

from .settings import settings

PROTOCOL = 'triz-manual-lab-v1'
MAX_TOKEN_BYTES = 32 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024
MAX_BUDGET_USD = 5.0
_slots = asyncio.Semaphore(2)


class LabInputError(ValueError):
    pass


def current_fingerprint():
    from .lab_manifest import source_fingerprint
    return source_fingerprint()


def _key():
    if not settings.service_token:
        raise LabInputError('테스트 서비스 인증이 설정되지 않았습니다.')
    return hmac.digest(settings.service_token.encode(), PROTOCOL.encode(), 'sha256')


def encode_continuation(payload):
    raw = json.dumps({'protocol': PROTOCOL, 'fingerprint': current_fingerprint(),
        'payload': payload}, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise LabInputError('테스트 상태의 전달 크기 한도를 초과했습니다.')
    data = base64.urlsafe_b64encode(gzip.compress(raw, compresslevel=3, mtime=0)).decode().rstrip('=')
    body = 'lab1.' + data
    token = body + '.' + hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
    if len(token) > MAX_TOKEN_BYTES:
        raise LabInputError('테스트 상태의 전달 크기 한도를 초과했습니다.')
    return token


def decode_continuation(token):
    if not isinstance(token, str) or not token or len(token) > MAX_TOKEN_BYTES:
        raise LabInputError('이전 출력의 continuation 값을 입력해 주세요.')
    parts = token.split('.')
    if len(parts) != 3 or parts[0] != 'lab1':
        raise LabInputError('올바른 테스트 재개 값이 아닙니다.')
    body = '.'.join(parts[:2])
    signature = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
    if not parts[2].isascii() or not hmac.compare_digest(signature, parts[2]):
        raise LabInputError('테스트 재개 값의 무결성 확인에 실패했습니다.')
    try:
        packed = base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4))
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
            raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise ValueError('size')
        envelope = json.loads(raw)
    except (ValueError, OSError, EOFError) as exc:
        raise LabInputError('올바른 테스트 재개 값이 아닙니다.') from exc
    if not isinstance(envelope, dict):
        raise LabInputError('올바른 테스트 재개 값이 아닙니다.')
    if envelope.get('protocol') != PROTOCOL or envelope.get('fingerprint') != current_fingerprint():
        raise LabInputError('실행 코드나 지식·프롬프트 버전이 변경됐습니다. 새 테스트를 시작해 주세요.')
    if not isinstance(envelope.get('payload'), dict):
        raise LabInputError('올바른 테스트 재개 값이 아닙니다.')
    return envelope['payload']


async def _run_child(payload):
    root = settings.root
    ram = Path('/dev/shm')
    with tempfile.TemporaryDirectory(prefix='triz-manual-lab-', dir=ram if ram.is_dir() else None) as directory:
        env = os.environ.copy()
        env.update(DATABASE_URL='sqlite://', MYSQL_URL='', DB_PATH=str(Path(directory) / 'unused.db'),
            STORAGE_DIR=directory, ORCHESTRATOR='local', TRIZ_AX_WORKER_ENABLED='false',
            PATENT_WORKER_ENABLED='false', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
            TOKENIZERS_PARALLELISM='false', TRIZ_LAB_CHILD='1',
            TRIZ_LAB_ORIGINAL_STORAGE_DIR=str(settings.storage_dir))
        # Patent SQL is a separate read-only source. Never redirect it into the
        # temporary analysis journal when a deployment shares the same server.
        if settings.patent_database_url:
            env['PATENT_DATABASE_URL'] = str(settings.patent_database_url)
        process = await asyncio.create_subprocess_exec(sys.executable, '-m', 'triz.lab_runtime',
            cwd=str(root), env=env, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(json.dumps(payload,
                ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()), timeout=3600)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            if process.returncode is None:
                process.kill()
            await process.communicate()
            raise
        if process.returncode != 0:
            raise RuntimeError('테스트 실행이 완료되지 않았습니다. 자동 재호출하지 않았습니다.')
        if len(stdout) > MAX_SNAPSHOT_BYTES * 2:
            raise RuntimeError('테스트 출력이 전달 크기 한도를 초과했습니다.')
        try:
            result = json.loads(stdout.strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise RuntimeError('테스트 실행 응답을 확인하지 못했습니다. 자동 재호출하지 않았습니다.') from exc
        if not isinstance(result, dict) or not isinstance(result.get('continuation_payload'), dict):
            raise RuntimeError('테스트 실행 응답을 확인하지 못했습니다. 자동 재호출하지 않았습니다.')
        return result


def validate_payload(payload):
    if not isinstance(payload, dict) or set(payload) - {
        'action', 'raw_query', 'mode', 'budget_usd', 'continuation', 'human_response', 'stage_key'}:
        raise LabInputError('지원하지 않는 테스트 입력입니다.')
    action = payload.get('action')
    if action not in ('begin', 'stage'):
        raise LabInputError('지원하지 않는 테스트 동작입니다.')
    request = dict(payload)
    token = request.pop('continuation', '')
    if token:
        request['continuation_payload'] = decode_continuation(token)
    elif action == 'stage':
        raise LabInputError('이전 출력의 continuation 값을 입력해 주세요.')
    else:
        query = request.get('raw_query')
        if not isinstance(query, str) or not query.strip() or len(query) > 100000:
            raise LabInputError('질의를 입력해 주세요(최대 100,000자).')
        if request.get('mode', 'STANDARD') not in ('QUICK', 'STANDARD', 'DEEP'):
            raise LabInputError('지원하지 않는 실행 모드입니다.')
        budget = request.get('budget_usd', MAX_BUDGET_USD)
        if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not 0 < budget <= MAX_BUDGET_USD:
            raise LabInputError('테스트 예산은 $0 초과 $5 이하로 입력해 주세요.')
        request['budget_usd'] = float(budget)
    if request.get('human_response') is not None and not isinstance(request['human_response'], dict):
        raise LabInputError('human_response는 JSON 객체로 입력해 주세요.')
    if action == 'stage':
        from .lab_manifest import build_manifest
        if request.get('stage_key') not in {row['key'] for row in build_manifest()['stages']}:
            raise LabInputError('지원하지 않는 테스트 단계입니다.')
    return request


async def execute(payload):
    request = validate_payload(payload)
    async with _slots:
        result = await _run_child(request)
    snapshot = result.pop('continuation_payload')
    result['continuation'] = encode_continuation(snapshot)
    result['protocol'] = PROTOCOL
    result['fingerprint'] = current_fingerprint()
    result['storage'] = {'analysis': 'memory-only; carried in continuation',
        'feedback': 'disabled', 'reinforcement_learning': 'disabled', 'automatic_paid_retry': False}
    return result


def inspect_solutions(token, candidate_id=''):
    snapshot = decode_continuation(token)
    state = snapshot.get('state', {})
    if not isinstance(state, dict):
        raise LabInputError('테스트 상태를 확인할 수 없습니다.')
    if isinstance(snapshot.get('solutions'), list):
        rows = [row for row in snapshot['solutions'] if not candidate_id
            or row.get('concept_id') == candidate_id]
        if candidate_id and not rows:
            raise LabInputError('이 테스트에 해당 해결안이 없습니다.')
        return {'status': state.get('status'), 'solutions': rows, 'cost': state.get('cost', {}),
            'pending': state.get('pending'), 'new_model_calls': 0, 'analysis_db_writes': 0}
    rows = []
    concepts = list(state.get('concepts', []))
    excluded = state.get('scratch', {}).get('ax_excluded', [])
    known = {row.get('id') for row in concepts}
    concepts.extend(row for row in excluded if isinstance(row, dict) and row.get('id') not in known)
    for concept in concepts:
        cid = concept.get('id')
        if candidate_id and cid != candidate_id:
            continue
        checks = [row for row in state.get('constraint_checks', []) if row.get('concept_id') == cid]
        evaluations = [row for row in state.get('evaluation', {}).get('evaluations', []) if row.get('concept_id') == cid]
        evidence_ids = set(concept.get('evidence_ids', []))
        rows.append({'candidate_id': cid, 'solution': concept, 'constraint_checks': checks,
            'independent_evaluations': evaluations,
            'evidence': [row for row in state.get('evidence', []) if row.get('id') in evidence_ids],
            'included_in_current_portfolio': cid in known,
            'validation_trace': [row for row in state.get('steps', [])
                if cid and _contains_identifier(row.get('output_json', {}), cid)]})
    if candidate_id and not rows:
        raise LabInputError('이 테스트에 해당 해결안이 없습니다.')
    return {'status': state.get('status'), 'solutions': rows, 'cost': state.get('cost', {}),
        'pending': state.get('pending'), 'new_model_calls': 0, 'analysis_db_writes': 0}


def _contains_identifier(value, identifier):
    if isinstance(value, dict):
        return any(_contains_identifier(item, identifier) for item in value.values())
    if isinstance(value, list):
        return any(_contains_identifier(item, identifier) for item in value)
    return value == identifier
