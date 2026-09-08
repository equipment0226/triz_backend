"""공신력 있는 공개 학술·특허 검색 어댑터.

API 키 없이 동작하는 소스를 기본으로 쓴다.
- Crossref  (DOI, 논문)         : 키 불필요
- OpenAlex  (DOI, 논문/저널)     : 키 불필요
- arXiv     (프리프린트)         : 키 불필요
- PatentsView (미국 특허번호)     : PATENTSVIEW_API_KEY 있을 때만
- Tavily    (웹, 화이트리스트 한정): TAVILY_API_KEY 있을 때만

결과는 항상 '실제 응답에서 가져온 값'만 담는다. 번호·URL을 추정해 만들지 않는다.
"""
from __future__ import annotations

import logging
import json
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus, urlparse
from concurrent.futures import ThreadPoolExecutor

import httpx

from ..settings import settings

log = logging.getLogger("triz.scholar")
UA = "TRIZ-Pilot/0.1 (local research assistant)"
TIMEOUT = 20

PATENT_ID_RE = re.compile(r"^(US|EP|JP|KR|CN|WO|DE|FR|GB)[-\s]?\d{4,}[A-Z]?\d*$", re.I)


def _clean(text: str, n: int = 320) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = " ".join(text.split())
    return text[:n]


def _rec(**kw: Any) -> dict:
    base = {"source_type": "PAPER", "title": "", "identifier": "", "url": "", "year": "",
            "venue": "", "snippet": "", "reliability": "HIGH", "provider": ""}
    base.update(kw)
    return base


# ───────────────────────────────────────── Crossref
def crossref(query: str, k: int = 4) -> list[dict]:
    try:
        r = httpx.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": query, "rows": k, "select":
                    "DOI,title,container-title,issued,abstract,type,URL"},
            headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
        out = []
        for it in r.json().get("message", {}).get("items", []):
            title = (it.get("title") or [""])[0]
            doi = it.get("DOI", "")
            if not title or not doi:
                continue
            year = ""
            parts = (it.get("issued") or {}).get("date-parts") or [[]]
            if parts and parts[0]:
                year = str(parts[0][0])
            out.append(_rec(source_type="PAPER", title=_clean(title, 200), identifier=doi,
                            url=f"https://doi.org/{doi}", year=year,
                            venue=_clean((it.get("container-title") or [""])[0], 80),
                            snippet=_clean(it.get("abstract", "")), provider="crossref"))
        return out
    except Exception as exc:  # noqa: BLE001
        log.warning("crossref 실패: %s", exc)
        return []


# ───────────────────────────────────────── OpenAlex
def openalex(query: str, k: int = 4) -> list[dict]:
    try:
        r = httpx.get(
            "https://api.openalex.org/works",
            params={"search": query, "per_page": k, "mailto": "triz-pilot@localhost"},
            headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
        out = []
        for it in r.json().get("results", []):
            title = it.get("display_name") or ""
            doi = (it.get("doi") or "").replace("https://doi.org/", "")
            url = it.get("doi") or (it.get("primary_location") or {}).get("landing_page_url") or ""
            if not title or not url:
                continue
            venue = ((it.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            out.append(_rec(source_type="PAPER", title=_clean(title, 200), identifier=doi,
                            url=url, year=str(it.get("publication_year") or ""),
                            venue=_clean(venue, 80),
                            snippet=_clean(_invert_abstract(it.get("abstract_inverted_index"))),
                            provider="openalex"))
        return out
    except Exception as exc:  # noqa: BLE001
        log.warning("openalex 실패: %s", exc)
        return []


def _invert_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions[:80])


# ───────────────────────────────────────── arXiv
def arxiv(query: str, k: int = 3) -> list[dict]:
    try:
        r = httpx.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": k},
            headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(r.text)
        out = []
        for e in root.findall("a:entry", ns):
            title = (e.findtext("a:title", "", ns) or "").strip()
            url = (e.findtext("a:id", "", ns) or "").strip()
            if not title or not url:
                continue
            out.append(_rec(source_type="PAPER", title=_clean(title, 200),
                            identifier=url.rsplit("/", 1)[-1], url=url,
                            year=(e.findtext("a:published", "", ns) or "")[:4], venue="arXiv",
                            snippet=_clean(e.findtext("a:summary", "", ns)), provider="arxiv"))
        return out
    except Exception as exc:  # noqa: BLE001
        log.warning("arxiv 실패: %s", exc)
        return []


# ───────────────────────────────────────── PatentsView (선택)
def patentsview(query: str, k: int = 4) -> list[dict]:
    key = settings.patentsview_key
    if not key:
        return []
    try:
        r = httpx.get(
            "https://search.patentsview.org/api/v1/patent/",
            params={
                "q": json.dumps({"_or": [{"_text_any": {"patent_title": query}},
                                         {"_text_any": {"patent_abstract": query}}]}),
                "f": '["patent_id","patent_title","patent_date","patent_abstract"]',
                "o": f'{{"size":{k}}}',
            },
            headers={"X-Api-Key": key, "User-Agent": UA}, timeout=TIMEOUT,
        )
        r.raise_for_status()
        out = []
        for p in r.json().get("patents", []) or []:
            pid = p.get("patent_id", "")
            if not pid:
                continue
            out.append(_rec(source_type="PATENT", title=_clean(p.get("patent_title", ""), 200),
                            identifier=f"US{pid}", url=f"https://patents.google.com/patent/US{pid}",
                            year=(p.get("patent_date") or "")[:4], venue="USPTO",
                            snippet=_clean(p.get("patent_abstract", "")), provider="patentsview"))
        return out
    except Exception as exc:  # noqa: BLE001
        log.warning("patentsview 실패: %s", exc)
        return []


# ───────────────────────────────────────── Tavily (선택, 화이트리스트)
TRUSTED_DOMAINS = [
    "patents.google.com", "worldwide.espacenet.com", "kipris.or.kr", "doi.org",
    "ieeexplore.ieee.org", "sciencedirect.com", "arxiv.org", "nature.com", "mdpi.com",
    "springer.com", "aip.org", "iop.org", "osapublishing.org", "optica.org",
    "iso.org", "astm.org", "semi.org", "nist.gov", "nasa.gov",
]


def tavily(query: str, k: int = 4) -> list[dict]:
    if not settings.tavily_key:
        return []
    try:
        r = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_key, "query": query, "max_results": k * 2,
                  "search_depth": "basic", "include_domains": TRUSTED_DOMAINS},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        out = []
        for it in r.json().get("results", [])[: k * 2]:
            url = it.get("url", "")
            host = (urlparse(url).hostname or "").lower()
            if not any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS):
                continue
            ident = ""
            m = re.search(r"/patent/([A-Z]{2}\d+[A-Z]?\d*)", url)
            if m:
                ident = m.group(1)
            out.append(_rec(source_type="PATENT" if "patent" in url else "ARTICLE",
                            title=_clean(it.get("title", ""), 200), identifier=ident, url=url,
                            snippet=_clean(it.get("content", "")), provider="tavily"))
        return out[:k]
    except Exception as exc:  # noqa: BLE001
        log.warning("tavily 실패: %s", exc)
        return []


# ───────────────────────────────────────── 검증된 검색 링크 (최후 수단)
def search_links(query: str) -> list[dict]:
    """번호를 지어내는 대신, 사용자가 바로 확인할 수 있는 공식 검색 링크를 제공한다."""
    q = quote_plus(query)
    return [
        _rec(source_type="PATENT", title=f"Google Patents 검색: {query}", identifier="",
             url=f"https://patents.google.com/?q={q}", venue="Google Patents",
             snippet="해당 키워드의 특허 검색 결과 페이지(직접 확인 필요)",
             reliability="MID", provider="search_link"),
        _rec(source_type="PATENT", title=f"Espacenet 검색: {query}", identifier="",
             url=f"https://worldwide.espacenet.com/patent/search?q={q}", venue="EPO Espacenet",
             snippet="유럽특허청 검색 결과 페이지(직접 확인 필요)",
             reliability="MID", provider="search_link"),
    ]


# ───────────────────────────────────────── 통합
PROVIDERS = {
    "crossref": crossref, "openalex": openalex, "arxiv": arxiv,
    "patentsview": patentsview, "tavily": tavily,
}


def enabled_providers() -> list[str]:
    names = [p.strip().lower() for p in settings.evidence_providers if p.strip()]
    out = []
    for n in names:
        if n == "patentsview" and not settings.patentsview_key:
            continue
        if n == "tavily" and not settings.tavily_key:
            continue
        if n in PROVIDERS:
            out.append(n)
    return out


def search(query: str, k: int = 4, providers: list[str] | None = None) -> list[dict]:
    """여러 공신력 소스를 조회해 URL 기준으로 중복 제거한 결과를 반환한다."""
    seen: set[str] = set()
    out: list[dict] = []
    names = enabled_providers() if providers is None else providers
    if not names:
        return []
    with ThreadPoolExecutor(max_workers=min(3, len(names))) as pool:
        batches = list(pool.map(lambda name: PROVIDERS[name](query, k), names))
    for name, batch in zip(names, batches):
        try:
            for rec in batch:
                url = rec.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                rec["query"] = query
                out.append(rec)
        except Exception as exc:  # noqa: BLE001
            log.warning("%s 조회 실패: %s", name, exc)
    return out

def search_kind(query: str, kind: str = "PATENT", k: int = 4) -> list[dict]:
    if kind not in ("PATENT", "PAPER"):
        raise ValueError("kind must be PATENT or PAPER")
    allowed = {"patentsview", "tavily"} if kind == "PATENT" else {"crossref", "openalex", "arxiv"}
    providers = [p for p in enabled_providers() if p in allowed]
    records = search(query, k, providers)
    return [r for r in records if r["source_type"] == kind and r.get("identifier")
            and r.get("provider") != "search_link"][:k]


def verify_url(url: str) -> bool:
    if not url:
        return False
    try:
        r = httpx.head(url, timeout=8, follow_redirects=True, headers={"User-Agent": UA})
        if r.status_code == 405:  # HEAD 미지원 사이트
            r = httpx.get(url, timeout=10, follow_redirects=True, headers={"User-Agent": UA})
        return r.status_code < 400
    except Exception:  # noqa: BLE001
        return False


def available() -> bool:
    return bool(enabled_providers())
