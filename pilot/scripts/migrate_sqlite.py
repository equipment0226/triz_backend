"""Copy PoC SQLite rows to an empty configured MySQL database. Defaults to dry run."""
import argparse
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select, func
from triz import store

def migrate(source, apply=False):
    store.init()
    if store.engine.dialect.name != "mysql":
        raise SystemExit("Configure DATABASE_URL or MYSQL* for a MySQL destination.")
    source = Path(source).resolve(strict=True)
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as old:
        old.row_factory = sqlite3.Row
        tables = (store.runs, store.states, store.steps, store.feedback, store.rag_docs)
        counts = {t.name: old.execute(f'SELECT COUNT(*) FROM "{t.name}"').fetchone()[0] for t in tables}
        if not apply:
            return {"dry_run": True, "rows": counts}
        with store.engine.begin() as target:
            if any(target.execute(select(func.count()).select_from(t)).scalar() for t in tables):
                raise SystemExit("Destination must be empty; existing records will not be overwritten.")
            for t in tables:
                cursor = old.execute(f'SELECT * FROM "{t.name}"')
                while rows := cursor.fetchmany(100):
                    target.execute(t.insert(), [{k: r[k] for k in r.keys() if k in t.c} for r in rows])
        return {"dry_run": False, "rows": counts}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(migrate(args.source, args.apply))
