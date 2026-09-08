"""생성된 리포트에 내부 ID 코드가 남았는지, 시각화가 포함됐는지 점검한다."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from triz import store  # noqa: E402

ID_RE = re.compile(r"\b(?:TC|PC|CPT|IDEA|KP|CON|SU|EV|TR|PER|STP|INT)-[0-9a-fA-F]{6,12}(?![0-9a-fA-F])")
ENUM_RE = re.compile(
    r"\b(?:[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+)\b"  # SNAKE_UPPER 형태의 내부 열거값
)


def main() -> int:
    ids = sys.argv[1:] or [r["run_id"] for r in store.list_runs(200)]
    bad = 0
    for rid in ids:
        st = store.load_state(rid)
        if not st or not st.report or not st.report.markdown:
            continue
        md = st.report.markdown
        leaks = sorted(set(ID_RE.findall(md)))
        enums = sorted(set(ENUM_RE.findall(md)))
        n_viz = md.count("```mermaid")
        n_tbl = md.count("\n|---")
        flag = "OK " if not leaks and not enums else "LEAK"
        if leaks or enums:
            bad += 1
        print(f"  [{flag}] {rid}  {len(md):,}자 · 도표 {n_viz}개 · 표 {n_tbl}개"
              f"{' · 남은코드 ' + ', '.join(leaks[:6]) if leaks else ''}"
              f"{' · 영문열거값 ' + ', '.join(enums[:6]) if enums else ''}")
    print("문제 없음" if not bad else f"코드 노출 {bad}건")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
