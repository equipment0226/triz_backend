"""테스트로 잘못 적재된 RAG 레코드를 정리한다.

사용:  python scripts/clean_rag.py --dry            (미리보기)
       python scripts/clean_rag.py --run RUN_ID     (해당 실행의 실패패턴 삭제)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from triz import rag, store  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default=rag.FAILURES)
    ap.add_argument("--run", default="")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    rows = store.rag_all(args.collection)
    targets = [r for r in rows
               if not args.run or (r.get("meta") or {}).get("run_id") == args.run]
    print(f"[{args.collection}] 전체 {len(rows)}건 / 대상 {len(targets)}건")
    for r in targets:
        print("  -", r["id"], json.dumps(r["doc"], ensure_ascii=False)[:110])
    if args.dry or not targets:
        return 0

    from sqlalchemy import delete
    with store.engine.begin() as cx:
        cx.execute(delete(store.rag_docs).where(store.rag_docs.c.id.in_([r["id"] for r in targets])))
    print(f"삭제 완료: {len(targets)}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
