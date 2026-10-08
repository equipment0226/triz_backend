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
    if not isinstance(request, dict) or request.get('action_context'):
        return None
    if not request_episode(request):
        # Pre-contract AX runs have no semantic episode. Only a complete saved
        # provider request establishes identity; never broaden a partial journal
        # record or an invalid episode into a reusable legacy call.
        provider = request.get('request')
        if (not isinstance(provider, dict) or 'semantic_episode_id' in provider
                or not isinstance(request.get('node'), str) or not request['node']
                or not isinstance(request.get('bundle_id'), str) or not request['bundle_id']
                or not all(isinstance(provider.get(key), str) for key in ('system', 'user', 'tier', 'expect'))
                or not isinstance(provider.get('model_config'), dict) or not provider['model_config']):
            return None
    # Keep every provider option and the pinned bundle. Epoch and decision are
    # transport/audit identities, not permission to pay for the same call again.
    return digest({k:v for k,v in request.items() if k != 'decision_id'})


def legacy_replay_result(result):
    """Restore response key order only from an equivalent saved provider text.

    The journal canonicalizes JSON keys, while downstream prompt rendering
    preserves insertion order. Reusing the original text's order keeps already
    paid dependent requests byte-identical. Never replace data with a different
    response or change the immutable stored result.
    """
    if not isinstance(result, dict) or not isinstance(result.get('text'), str) or 'data' not in result:
        return result
    try:
        from ..llm import extract_json
        original = extract_json(result['text'])
        equivalent = digest(original) == digest(result['data'])
    except (TypeError, ValueError):
        return result
    return dict(result, data=original) if equivalent else result


def _eligible(task, request, episode):
    # A retry of the retry requires investigation; never form an unbounded chain.
    return (bool(episode) and not task['task_id'].startswith('task-retry-') and task['status'] in ('UNKNOWN', 'RECONCILED')
            and request_episode(request) == episode)


def _previous_episode_event_id(task_id, episode):
    return 'usage-previous-' + digest(dict(task_id=task_id, semantic_episode_id=episode))[:48]


def _previous_episode_approval(c, run_id, task_id, episode):
    if not isinstance(episode, str) or not episode.strip():
        return None
    raw = c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id == run_id,
        ledger.events.c.event_id == _previous_episode_event_id(task_id, episode),
        ledger.events.c.event_type == 'UNKNOWN_PREVIOUS_EPISODE_AUTHORIZED')).scalar()
    return json.loads(raw) if raw else None


def _different_episodes(source, current):
    return (isinstance(source, str) and bool(source.strip())
            and isinstance(current, str) and bool(current.strip()) and source != current)


def _previous_episode_unblocked(c, run_id, task_id, episode):
    value = _previous_episode_approval(c, run_id, task_id, episode)
    if not value or value.get('task_id') != task_id or value.get('semantic_episode_id') != episode:
        return False
    source = request_episode(_request(c, {'task_id': task_id}))
    return (_different_episodes(source, episode) and value.get('source_semantic_episode_id') == source
            and value.get('acknowledged_possible_duplicate_charge') is True)


def blocking_count(state):
    episode = state.scratch.get('semantic_episode_id')
    with store.engine.connect() as c:
        rows = c.execute(select(ledger.tasks.c.task_id).where(ledger.tasks.c.run_id == state.run_id,
            ledger.tasks.c.status == 'UNKNOWN')).scalars().all()
        return sum(not ((episode and value and value.get('semantic_episode_id') == episode)
                       or _previous_episode_unblocked(c, state.run_id, task_id, episode))
                   for task_id in rows for value in [approval(c, state.run_id, task_id)])


def authorize_previous_episode(run_id, actor, task_id, expected_epoch, *, reason,
                               acknowledge_possible_duplicate_charge=False):
    """Operator-only consent to continue one new episode despite an old UNKNOWN.

    There is intentionally no public API route. The caller must supply the owner
    and explicit consent. This neither settles the old charge nor authorizes its
    replay: only this task's preflight block in this semantic episode is waived.
    Ordinary ledger acquisition still enforces all new request costs and limits.
    """
    if acknowledge_possible_duplicate_charge is not True:
        raise ValueError('Explicit acknowledgement of possible duplicate charge is required')
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        raise ValueError('A nonempty operator reason of at most 2000 characters is required')
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            raise ValueError('Run not found')
        with ledger.transaction() as c:
            head = ledger._head(c, run_id, lock=True)
            ledger.authorize(head, actor)
            if head['epoch'] != expected_epoch or state.scratch.get('execution_epoch') != expected_epoch:
                raise Conflict('Execution epoch changed; refresh before authorizing')
            if state.status not in ('INTERRUPTED', 'FAILED') or state.pending:
                raise Conflict('Only an interrupted run without pending input can be authorized')
            task = c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == run_id,
                ledger.tasks.c.task_id == task_id)).mappings().first()
            episode = state.scratch.get('semantic_episode_id')
            source = request_episode(_request(c, task)) if task else None
            if not task or task['status'] != 'UNKNOWN' or not _different_episodes(source, episode):
                raise Conflict('An UNKNOWN task from a different recorded semantic episode is required')
            previous = _previous_episode_approval(c, run_id, task_id, episode)
            if previous:
                if (previous.get('source_semantic_episode_id') != source
                        or previous.get('task_id') != task_id
                        or previous.get('acknowledged_possible_duplicate_charge') is not True):
                    raise Conflict('Existing approval does not match the recorded task')
                return previous
            from .cost_restatements import effective, overrides
            corrections = overrides(c, run_id)
            rows = c.execute(select(ledger.tasks.c.task_id, ledger.tasks.c.status, ledger.tasks.c.actual, ledger.tasks.c.reserve)
                .where(ledger.tasks.c.run_id == run_id)).all()
            used = sum((effective(r.actual, r.task_id, corrections) or 0)
                       + (r.reserve if r.status in ('RUNNING', 'UNKNOWN') else 0) for r in rows)
            hold = json.loads(head['bundle'])['limits']['validation_reserve_microusd']
            if used + task['reserve'] + hold > head['budget']:
                raise Conflict('Insufficient budget with the old reservation and validation reserve retained')
            value = dict(version='unknown-previous-episode-v1', task_id=task_id, actor=actor,
                expected_epoch=expected_epoch, semantic_episode_id=episode,
                source_semantic_episode_id=source, reason=reason.strip(),
                acknowledged_possible_duplicate_charge=True, retained_reserve_microusd=task['reserve'])
            ledger._event(c, run_id, 'UNKNOWN_PREVIOUS_EPISODE_AUTHORIZED', value,
                event_id=_previous_episode_event_id(task_id, episode))
            return value


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
