"""Runtime wiring only; migrations remain an explicit operator command."""
import asyncio
from functools import lru_cache
import json
import os
from sqlalchemy import select, update
from .repository import Repository, tasks, cases, now
from .service import Service
from .domain import PatentError


@lru_cache(maxsize=1)
def service():
    from triz import store
    return Service(Repository(store.engine))


def tick():
    if os.getenv('PATENT_DISPATCH_ENABLED', 'false').lower() != 'true':
        return False
    current = service()
    current.recover_expired()
    from .image_jobs import tick as image_tick
    image_tick(current)
    with current.repo.engine.begin() as c:
        # A paused/dependency-blocked case must not starve unrelated cases.
        candidates = c.execute(select(tasks.c.task_id, tasks.c.body, cases.c.owner_id, cases.c.body.label('case_body'))
            .join(cases, tasks.c.case_id == cases.c.case_id).where(tasks.c.status == 'QUEUED', tasks.c.lease_until_ms <= now())
            .order_by(tasks.c.task_id))
        row = next((r for r in candidates if json.loads(r.case_body)['execution_status']
                    not in ('CANCELLED','PAUSED_USER','PAUSED_BUDGET','PAUSED_DEPENDENCY')), None)
        if row and os.getenv('PATENT_ORCHESTRATOR', 'local') == 'n8n':
            claimed = c.execute(update(tasks).where(tasks.c.task_id == row.task_id,
                tasks.c.status == 'QUEUED', tasks.c.lease_until_ms <= now()).values(lease_until_ms=now()+60000))
            if claimed.rowcount != 1:
                return False
    if not row:
        return False
    try:
        if os.getenv('PATENT_ORCHESTRATOR', 'local') == 'n8n':
            from .dispatch import dispatch_task, node_for
            dispatch_task(row.task_id, node_for(current, row.task_id))
        else:
            current.execute(row.owner_id, json.loads(row.body)['ticket'])
    except PatentError:
        pass
    return True


async def supervise():
    while True:
        try:
            await asyncio.to_thread(tick)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Missing migration pauses the worker; never auto-create legacy tables.
            import logging
            logging.getLogger(__name__).warning('Patent worker dependency unavailable')
        await asyncio.sleep(3)
