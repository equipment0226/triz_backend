"""프론트엔드 라이브러리를 web/vendor/ 로 내려받는다 (오프라인 실행 대비)."""
from __future__ import annotations

import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEST = Path(__file__).resolve().parents[1] / "web" / "vendor"
FILES = {
    "react.min.js": "https://unpkg.com/react@18.3.1/umd/react.production.min.js",
    "react-dom.min.js": "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
    "htm.js": "https://unpkg.com/htm@3.1.1/dist/htm.js",
    "marked.min.js": "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js",
    "mermaid.min.js": "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js",
}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    failed = 0
    with httpx.Client(follow_redirects=True, timeout=90) as cli:
        for name, url in FILES.items():
            path = DEST / name
            if path.exists() and path.stat().st_size > 1000:
                print(f"  = {name} (이미 있음, {path.stat().st_size:,} bytes)")
                continue
            try:
                r = cli.get(url)
                r.raise_for_status()
                path.write_bytes(r.content)
                print(f"  + {name} ({len(r.content):,} bytes)")
            except Exception as exc:
                failed += 1
                print(f"  ! {name} 실패: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
