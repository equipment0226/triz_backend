"""Explicit operator budget increases; never reset usage or change pinned content."""
import json
from decimal import Decimal
from sqlalchemy import select, update
from . import store


def increase(run_id, minimum_usd, *, reason):
    amount = Decimal(str(minimum_usd))
    if not amount.is_finite() or amount <= 0 or not reason.strip():
        raise ValueError('A positive finite limit and authorization reason are required')
    with store.run_lock(run_id):
        with store.engine.begin() as connection:
            row = connection.execute(select(store.states.c.state_json)
                .where(store.states.c.run_id == run_id).with_for_update()).first()
            if not row:
                raise ValueError('Project not found')
            raw = json.loads(row.state_json)
            previous = Decimal(str(raw['cost']['budget_usd']))
            target = max(amount, previous)
            head = None
            if raw.get('scratch', {}).get('workflow_version', '').startswith('triz-ax-'):
                from .ax import ledger
                head = connection.execute(select(ledger.heads)
                    .where(ledger.heads.c.run_id == run_id).with_for_update()).mappings().one()
                target = max(target, Decimal(head['budget']) / 1000000)
            changed = target > previous or (head is not None and int(target * 1000000) > head['budget'])
            result = {'run_id': run_id, 'previous_limit_usd': float(previous),
                'limit_usd': float(target), 'spent_usd': raw['cost']['total_usd'], 'changed': changed}
            if not changed:
                return result
            raw['cost']['budget_usd'] = float(target)
            raw['cost']['over_budget'] = Decimal(str(raw['cost']['total_usd'])) >= target
            # Preserve all unknown legacy JSON fields, timestamps, stage and status.
            connection.execute(update(store.states).where(store.states.c.run_id == run_id)
                .values(state_json=json.dumps(raw, ensure_ascii=False, separators=(',', ':'))))
            audit = dict(result, type='budget_limit_increased', reason=reason)
            if head is not None:
                connection.execute(update(ledger.heads).where(ledger.heads.c.run_id == run_id)
                    .values(budget=int(target * 1000000)))
                ledger._event(connection, run_id, 'BUDGET_LIMIT_INCREASED', audit)
            connection.execute(store.event_log.insert().values(run_id=run_id, payload=store._json(audit)))
        store.archive(run_id, 'state.json', raw)
        return result


def inventory():
    """Read numeric limits only; do not expose project content or upgrade state."""
    with store.engine.connect() as connection:
        rows = connection.execute(select(store.states.c.run_id, store.states.c.state_json)).all()
    return [dict(run_id=row.run_id, status=raw['status'], budget_usd=raw['cost']['budget_usd'],
        spent_usd=raw['cost']['total_usd']) for row in rows for raw in [json.loads(row.state_json)]]
