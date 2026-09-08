"""피드백 전용 로컬 RAG.

외부 임베딩 API 없이 동작하도록 문자 n-gram + 단어 기반 TF-IDF 코사인 유사도를 쓴다.
저장 대상은 '우리가 만들고 사용자가 검증한 데이터'뿐이다(특허/논문 코퍼스 아님).
"""
from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from typing import Any

from . import store
from .settings import settings

COLLECTION = "feedback_solutions"
FAILURES = "failure_patterns"
TOKEN = re.compile(r"[A-Za-z0-9가-힣]+")


def _tokens(text: str) -> list[str]:
    words = [w.lower() for w in TOKEN.findall(text or "")]
    grams: list[str] = []
    for w in words:
        grams.append(w)
        if len(w) > 2:
            grams += [w[i:i + 2] for i in range(len(w) - 1)]
    return grams


def _vec(text: str) -> Counter:
    return Counter(_tokens(text))


def _cosine(a: Counter, b: Counter, idf: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    num = sum(a[k] * b[k] * (idf.get(k, 1.0) ** 2) for k in keys)
    na = math.sqrt(sum((v * idf.get(k, 1.0)) ** 2 for k, v in a.items()))
    nb = math.sqrt(sum((v * idf.get(k, 1.0)) ** 2 for k, v in b.items()))
    return num / (na * nb) if na and nb else 0.0


def _idf(docs: list[str]) -> dict[str, float]:
    n = len(docs) or 1
    df: Counter = Counter()
    for d in docs:
        df.update(set(_tokens(d)))
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


# ─────────────────────────────── 쓰기
def write_feedback(state, distill: dict) -> int:
    if not settings.cfg("feedback_rag.enabled", True) or not state.feedback:
        return 0
    min_rating = int(settings.cfg("feedback_rag.min_rating_to_store", 4))
    wmax = float(settings.cfg("feedback_rag.weight_max", 1.3))
    written = 0
    gen = distill.get("generalized_problem") or state.intake.frame.restated_problem
    contra = "; ".join(c.label for c in state.definition.technical_contradictions[:2]) or ""

    for fb in state.feedback.solution_feedback:
        concept = state.concept(fb.concept_id)
        if not concept:
            continue
        if fb.rating >= min_rating:
            weight = min(wmax, 1.0 + 0.05 * (fb.rating - 3) + (0.05 if fb.adopted else 0.0))
            store.rag_upsert(
                doc_id=f"fb-{uuid.uuid4().hex[:10]}",
                collection=COLLECTION,
                doc=f"{gen} :: {contra} :: {concept.title} — {concept.one_liner}",
                meta={
                    "run_id": state.run_id, "concept_id": concept.id, "title": concept.title,
                    "one_liner": concept.one_liner, "industry": state.domain.industry,
                    "is_engineering": state.domain.is_engineering,
                    "novelty_class": concept.novelty_class,
                    "triz_origin": concept.triz_origin,
                    "improving": [t.improving_param_id for t in state.definition.technical_contradictions][:3],
                    "worsening": [t.worsening_param_id for t in state.definition.technical_contradictions][:3],
                    "rating": fb.rating, "adopted": bool(fb.adopted),
                    "mechanism": concept.working_principle[:300],
                },
                weight=weight,
            )
            written += 1
        elif fb.rating <= 2:
            store.rag_upsert(
                doc_id=f"fx-{uuid.uuid4().hex[:10]}",
                collection=FAILURES,
                doc=f"{gen} :: {concept.title} :: {fb.comment or ''} :: {', '.join(fb.reason_tags)}",
                meta={"industry": state.domain.industry, "reason_tags": fb.reason_tags,
                      "title": concept.title, "rating": fb.rating},
                weight=1.0,
            )
            written += 1
    return written


# ─────────────────────────────── 읽기
def retrieve(query: str, collection: str = COLLECTION, k: int | None = None,
             industry: str = "") -> list[dict]:
    if not settings.cfg("feedback_rag.enabled", True):
        return []
    docs = store.rag_all(collection)
    if not docs:
        return []
    k = k or int(settings.cfg("feedback_rag.top_k", 3))
    idf = _idf([d["doc"] for d in docs])
    qv = _vec(query)
    scored: list[tuple[float, dict]] = []
    for d in docs:
        sim = _cosine(qv, _vec(d["doc"]), idf) * float(d.get("weight") or 1.0)
        if industry and d.get("meta", {}).get("industry") == industry:
            sim *= 1.1
        if sim > 0.05:
            scored.append((sim, d))
    scored.sort(key=lambda x: -x[0])
    out = []
    for sim, d in scored[:k]:
        store.rag_touch(d["id"])
        out.append({"score": round(sim, 3), "doc": d["doc"], "meta": d.get("meta", {})})
    return out


def prior_cases_block(state) -> str:
    """S6 개념 구체화 프롬프트에 주입할 과거 사례 블록(과적합 방지 규칙 포함)."""
    if not settings.cfg("feedback_rag.enabled", True):
        return ""
    query = f"{state.intake.frame.restated_problem} {' '.join(c.label for c in state.definition.technical_contradictions[:2])}"
    hits = retrieve(query, industry=state.domain.industry)
    fails = retrieve(query, collection=FAILURES, k=2, industry=state.domain.industry)
    if not hits and not fails:
        return ""
    limit = int(settings.cfg("feedback_rag.max_influenced_concepts", 3))
    lines = []
    if hits:
        lines.append("[참고: 과거 유사 문제에서 사용자가 높게 평가한 접근]")
        for h in hits:
            m = h["meta"]
            lines.append(f"- ({h['score']}) {m.get('title','')}: {m.get('one_liner','')} / 메커니즘: {m.get('mechanism','')[:120]}")
        lines.append("[사용 규칙]")
        lines.append("- 위 사례는 '참고'다. 그대로 복사하지 마라.")
        lines.append(f"- 도출할 개념 중 최대 {limit}개까지만 이 방향을 반영하고, 나머지는 반드시 독립적으로 새로 도출하라.")
        lines.append("- 현재 시스템의 제약과 충돌하면 무시하라.")
    if fails:
        lines.append("[참고: 과거에 거절된 패턴 — 같은 실수를 반복하지 마라]")
        for f in fails:
            lines.append(f"- {f['meta'].get('title','')}: {', '.join(f['meta'].get('reason_tags', []))}")
    return "\n".join(lines)


def stats() -> dict:
    return {"feedback_solutions": len(store.rag_all(COLLECTION)),
            "failure_patterns": len(store.rag_all(FAILURES))}
