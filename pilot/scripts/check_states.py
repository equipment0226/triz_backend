"""실행 상태 로딩과 단계 재실행 경로를 LLM 호출 없이 점검한다."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from triz import pipeline, store  # noqa: E402


def main() -> int:
    bad = 0
    for r in store.list_runs(200):
        rid = r["run_id"]
        try:
            st = store.load_state(rid)
            pend = st.pending.kind if st.pending else "-"
            print(f"  OK   {rid}  {st.status:<14} stage={st.control.stage_index:>2} pending={pend}")
        except Exception as exc:
            bad += 1
            print(f"  FAIL {rid}  {str(exc)[:140]}")

    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        state = store.load_state(target)
        available = state is not None and state.status not in ("RUNNING", "QUEUED")
        print(f"\n  재검토 가능: {available} (상태 변경 없이 조회)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
