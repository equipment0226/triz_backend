"""현재 실행 상태 조회:  python scripts/status.py [run_id]"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(ROOT))
from triz import store

run_id = sys.argv[1] if len(sys.argv) > 1 else None
if not run_id:
    row = next(iter(store.list_runs(1)), None)
else:
    row = next((r for r in store.list_runs(1000) if r["run_id"] == run_id), None)
if not row:
    print("실행 없음")
    raise SystemExit(0)

run_id = row["run_id"]
print(f"RUN {run_id} | {row['status']} | {row['current_stage']} | "
      f"${row['cost_usd']:.4f} | {row['started_at']} → {row['ended_at'] or '진행중'}")
print(f"   {row['industry']} / {row['target_system']}")
print("-" * 100)

steps = store.list_steps(run_id)
for s in steps:
    score = s["verdict_score"] or 0.0
    print(f"{s['seq']:>3} {s['status']:<7} {s['verdict'] or '-':<7} {score:>4.2f} "
          f"try{s['verify_attempts']} ${s['cost_usd']:.4f} {s['tier']:<3} {s['label']}")
print("-" * 100)
print(f"총 {len(steps)}단계 / 누적 ${sum(s['cost_usd'] for s in steps):.4f}")
