"""Initialize ticket tables/grants without resetting balances; safe to rerun."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from triz import store

if __name__ == '__main__':
    print(json.dumps(store.migrate_tickets()))
