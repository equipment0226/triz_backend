"""로컬 실행 진입점:  python run.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn  # noqa: E402

from triz.settings import settings  # noqa: E402


def main() -> None:
    print("=" * 60)
    print(" TRIZ Studio v2")
    print(f"  · LLM       : {settings.tiers['T1'].model} / {settings.tiers['T2'].model} / {settings.tiers['T3'].model}")
    print(f"  · Endpoint  : {settings.tiers['T1'].base_url}")
    print(f"  · API Key   : {'설정됨' if settings.llm_ready else '❌ 미설정 (.env 확인)'}")
    print(f"  · DB        : {'MySQL' if settings.database_url else 'SQLite (local)'}")
    print(f"  · 실행      : {settings.orchestrator}")
    print(f"  · 검색      : {settings.search_provider}")
    print(f"  · URL       : http://{settings.host}:{settings.port}")
    print("=" * 60)
    uvicorn.run("api.main:app", host=settings.host, port=settings.port,
                log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
