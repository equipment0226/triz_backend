"""Read-only pre-upload guard. Run in the current backend; never stop live work."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from triz import store


def readiness():
    with store.engine.connect() as connection:
        active = connection.execute(select(store.runs.c.run_id, store.runs.c.status,
            store.runs.c.current_stage).where(store.runs.c.status.in_(('CREATED', 'QUEUED', 'RUNNING')))).mappings().all()
    return {'ready': not active, 'active_count': len(active), 'active_runs': [dict(row) for row in active]}


if __name__ == '__main__':
    result = readiness()
    print(json.dumps(result))
    raise SystemExit(0 if result['ready'] else 2)
