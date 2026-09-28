"""One owner-approved retry; the original unknown charge remains reserved."""
import json
from sqlalchemy import select, update
from .. import store
from . import ledger
from .contracts import Conflict, digest

VERSION = 'unknown-usage-retry-v1'


def event_id(task_id):
    return 'usage-retry-' + digest(task_id)[:48]


def approval(c, run_id, task_id):
    raw = c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id == run_id,
        ledger.events.c.event_id == event_id(task_id), ledger.events.c.event_type == 'UNKNOWN_RETRY_AUTHORIZED')).scalar()
    return json.loads(raw) if raw else None


def _request(c, task):
    raw = c.execute(select(ledger.attempts.c.details).where(ledger.attempts.c.task_id == task['task_id'])
        .order_by(ledger.attempts.c.fence.desc())).scalar()
    return json.loads(raw).get('request', {}) if raw else {}


def request_episode(request):
    """Read the recorded episode in both action and v3 stage-call journals."""
    if not isinstance(request, dict): return None
    action = request.get('action_context') or {}
    provider = request.get('request') or {}
    if not isinstance(action, dict) or not isinstance(provider, dict): return None
    values = [v for v in (action.get('semantic_episode_id'), provider.get('semantic_episode_id')) if v is not None]
    if not values or any(not isinstance(v, str) or not v for v in values) or len(set(values)) != 1:
        return None
    return values[0]


def stage_request_identity(request):
    if not isinstance(request, dict) or request.get('action_context') or not request_episode(request):
        return None
    return digest({k:v for k,v in request.items() if k != 'decision_id'})


def _eligible(task, request, episode):
    # A retry of the retry requires investigation; never form an unbounded chain.
    return (bool(episode) and not task['task_id'].startswith('task-retry-') and task['status'] in ('UNKNOWN', 'RECONCILED')
            and request_episode(request) == episode)


def blocking_count(state):
    episode = state.scratch.get('semantic_episode_id')
    with store.engine.connect() as c:
        rows = c.execute(select(ledger.tasks.c.task_id).where(ledger.tasks.c.run_id == state.run_id,
            ledger.tasks.c.status == 'UNKNOWN')).scalars().all()
        return sum(not (episode and value and value.get('semantic_episode_id') == episode)
                   for task_id in rows for value in [approval(c, state.run_id, task_id)])


def describe(run_id, actor):
    head = ledger.head(run_id, actor)
    state = store.load_state(run_id)
    episode = state.scratch.get('semantic_episode_id')
    budget = ledger.budget(run_id, actor)
    hold = head['bundle']['limits']['validation_reserve_microusd']
    items = []
    with store.engine.connect() as c:
        rows = c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == run_id,
            ledger.tasks.c.status.in_(('UNKNOWN', 'RECONCILED')))).mappings().all()
        for task in rows:
            request = _request(c, task)
            allowed = approval(c, run_id, task['task_id'])
            if episode and allowed and allowed['semantic_episode_id'] == episode:
                continue
            eligible = _eligible(task, request, episode)
            fits = budget['remaining_microusd'] >= task['reserve'] + hold
            items.append(dict(task_id=task['task_id'], node=request.get('node'),
                retained_reserve_microusd=task['reserve'] if task['status'] == 'UNKNOWN' else 0,
                retry_reserve_limit_microusd=task['reserve'],
                can_authorize=eligible and fits and state.status in ('INTERRUPTED', 'FAILED') and not state.pending,
                reason=None if eligible and fits else '복구 재시도 실패·입력 변경·예산 부족은 관리자 확인이 필요합니다.'))
    return dict(version=VERSION, expected_epoch=head['epoch'], items=items, budget=budget)


def authorize(run_id, actor, task_id, expected_epoch, *, acknowledge_possible_duplicate_charge=False):
    if acknowledge_possible_duplicate_charge is not True:
        raise ValueError('기존 호출 비용 예약을 유지하며 추가 비용이 발생할 수 있음에 동의해 주세요.')
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            raise ValueError('Run not found')
        with ledger.transaction() as c:
            head = ledger._head(c, run_id, lock=True)
            ledger.authorize(head, actor)
            if head['epoch'] != expected_epoch or state.scratch.get('execution_epoch') != expected_epoch:
                raise Conflict('분석 버전이 변경되었습니다. 새로고침 후 확인해 주세요.')
            if state.status not in ('INTERRUPTED', 'FAILED') or state.pending:
                raise Conflict('중단된 분석에서만 복구를 승인할 수 있습니다.')
            task = c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == run_id,
                ledger.tasks.c.task_id == task_id)).mappings().first()
            episode = state.scratch.get('semantic_episode_id')
            if not task or not _eligible(task, _request(c, task), episode):
                raise Conflict('이 작업은 1회 복구 대상이 아닙니다. 관리자 확인이 필요합니다.')
            previous = approval(c, run_id, task_id)
            if previous:
                if previous['semantic_episode_id'] != episode:
                    raise Conflict('다른 분석 버전의 복구 승인입니다.')
                return previous
            rows = c.execute(select(ledger.tasks.c.status, ledger.tasks.c.actual, ledger.tasks.c.reserve)
                .where(ledger.tasks.c.run_id == run_id)).all()
            used = sum((r.actual or 0) + (r.reserve if r.status in ('RUNNING', 'UNKNOWN') else 0) for r in rows)
            hold = json.loads(head['bundle'])['limits']['validation_reserve_microusd']
            if used + task['reserve'] + hold > head['budget']:
                raise Conflict('기존 미확인 비용과 검토 예산을 보존하면 재시도 예산이 부족합니다.')
            value = dict(version=VERSION, task_id=task_id, actor=actor, expected_epoch=expected_epoch,
                semantic_episode_id=episode, acknowledged_possible_duplicate_charge=True,
                retained_reserve_microusd=task['reserve'] if task['status'] == 'UNKNOWN' else 0,
                max_reserve_microusd=task['reserve'], retry_task_id='task-retry-' + digest(task_id)[:48])
            # Older expired-lease handling changed only the task projection.
            if task['status'] == 'UNKNOWN':
                c.execute(update(ledger.attempts).where(ledger.attempts.c.task_id == task_id,
                    ledger.attempts.c.status == 'RUNNING').values(status='UNKNOWN'))
            ledger._event(c, run_id, 'UNKNOWN_RETRY_AUTHORIZED', value, event_id=event_id(task_id))
            return value


def redirect(c, run_id, task, request, reserve):
    """Called under the AX head lock. Does not allocate or settle either task."""
    value = approval(c, run_id, task['task_id'])
    episode = request_episode(request)
    if not episode or not value or value.get('semantic_episode_id') != episode:
        return None
    if reserve > value['max_reserve_microusd']:
        raise Conflict('복구 요청 비용이 승인한 예약 한도를 초과했습니다.')
    return value
