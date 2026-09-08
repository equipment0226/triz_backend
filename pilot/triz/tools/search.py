"""외부 검색 도구 (선택). SEARCH_PROVIDER=none 이면 빈 결과를 반환하고,
근거 단계는 '모델 지식' 모드로 폴백한다."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..settings import settings

log = logging.getLogger("triz.search")

TRUSTED = {
    "HIGH": ["patents.google.com", "worldwide.espacenet.com", "kipris.or.kr", "doi.org",
             "ieeexplore.ieee.org", "sciencedirect.com", "arxiv.org", "nature.com",
             "mdpi.com", "iso.org", "astm.org", "semi.org", "springer.com"],
    "LOW": ["blog.", "tistory.com", "medium.com", "namu.wiki", "brunch.co.kr"],
}


def reliability_of(url: str) -> str:
    u = (url or "").lower()
    if any(d in u for d in TRUSTED["HIGH"]):
        return "HIGH"
    if any(d in u for d in TRUSTED["LOW"]):
        return "LOW"
    return "MID"


def enabled() -> bool:
    return settings.search_provider == "tavily" and bool(settings.tavily_key)


def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    if not enabled():
        return []
    try:
        r = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_key, "query": query, "max_results": k,
                  "search_depth": "basic"},
            timeout=25,
        )
        r.raise_for_status()
        out = []
        for item in r.json().get("results", [])[:k]:
            out.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": (item.get("content") or "")[:400],
                "reliability": reliability_of(item.get("url", "")),
            })
        return out
    except Exception as exc:  # noqa: BLE001
        log.warning("검색 실패(%s): %s", query, exc)
        return []


def multi_search(queries: list[str], k: int = 4, cap: int = 12) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for q in queries[:cap]:
        for hit in search(q, k=k):
            if hit["url"] and hit["url"] not in seen:
                seen.add(hit["url"])
                hit["query"] = q
                out.append(hit)
    return out


def verify_url(url: str) -> bool:
    if not url:
        return False
    try:
        r = httpx.head(url, timeout=8, follow_redirects=True)
        return r.status_code < 400
    except Exception:  # noqa: BLE001
        return False
