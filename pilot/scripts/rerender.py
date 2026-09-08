"""저장된 실행 상태를 그대로 두고 리포트만 최신 템플릿으로 다시 만든다.

사용:  python scripts/rerender.py            (완료된 실행 전부)
       python scripts/rerender.py RUN_ID
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from triz import render, store  # noqa: E402
from triz.schema import ReportArtifact, RunMode  # noqa: E402
from triz.settings import settings  # noqa: E402


def main() -> int:
    ids = sys.argv[1:] or [r["run_id"] for r in store.list_runs(200)]
    done = 0
    for rid in ids:
        st = store.load_state(rid)
        if not st:
            print(f"  - {rid}: 상태 없음, 건너뜀")
            continue
        if not st.report and not st.concepts:
            print(f"  - {rid}: 해결책이 없어 리포트를 만들 수 없음")
            continue
        narrative = (st.report.narrative if st.report else {}) or st.scratch.get("narrative") or {}
        try:
            md = render.render_report(st, narrative)
        except Exception as exc:
            print(f"  ! {rid}: 렌더 실패 {exc}")
            continue
        if st.report:
            st.report.markdown = md
            st.report.word_count = len(md)
        else:
            st.report = ReportArtifact(
                markdown=md, narrative=narrative, word_count=len(md),
                template_id=("report_lite" if st.control.mode == RunMode.LITE else "report_full"))
        store.save_state(st)
        (settings.storage_dir / f"{rid}.md").write_text(md, encoding="utf-8")
        print(f"  + {rid}: {len(md):,}자")
        done += 1
    print(f"재생성 완료 {done}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
