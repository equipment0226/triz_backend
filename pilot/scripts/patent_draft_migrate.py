"""Explicit additive migration: python scripts/patent_draft_migrate.py --apply."""
import argparse
import json
from sqlalchemy import inspect
from triz import store
from patent_draft.repository import Repository, TABLES
from patent_draft.legacy import LegacyReader


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    before = set(inspect(store.engine).get_table_names())
    schema_before=LegacyReader().schema_fingerprint()
    if args.apply:
        Repository(store.engine).migrate()
        after = set(inspect(store.engine).get_table_names())
        assert before <= after and after-before <= TABLES
        assert LegacyReader().schema_fingerprint()==schema_before, 'Original schema changed'
    print(json.dumps({'mode':'APPLIED' if args.apply else 'PLAN', 'new_tables':sorted(TABLES-before),
                      'legacy_alterations':False,'legacy_schema_hash':schema_before}))


if __name__ == '__main__':
    main()
