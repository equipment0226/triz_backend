"""근거 검색 어댑터 점검:  python scripts/check_refs.py "query" """
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from triz.tools import scholar  # noqa: E402

query = " ".join(sys.argv[1:]) or "thermophoretic particle deposition optical window vacuum chamber"
print("활성 공급자:", scholar.enabled_providers())
print("질의:", query)
recs = scholar.search(query, k=3)
print(f"결과 {len(recs)}건\n")
for r in recs:
    print(f"[{r['provider']}/{r['source_type']}] {r['title'][:80]}")
    print(f"   식별자: {r['identifier'] or '-'} | 연도: {r['year'] or '-'} | {r['venue'][:40]}")
    print(f"   {r['url']}")
    if r["snippet"]:
        print(f"   {r['snippet'][:120]}")
    print()
if not recs:
    print("검색 결과 없음 → 공식 검색 링크로 폴백:")
    for r in scholar.search_links(query):
        print(f"   {r['title']} → {r['url']}")
