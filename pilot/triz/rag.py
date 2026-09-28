"""피드백 전용 로컬 RAG.

외부 임베딩 API 없이 동작하도록 문자 n-gram + 단어 기반 TF-IDF 코사인 유사도를 쓴다.
저장 대상은 '우리가 만들고 사용자가 검증한 데이터'뿐이다(특허/논문 코퍼스 아님).
"""
from __future__ import annotations

import math
import re
import json
from collections import Counter
from contextlib import nullcontext
from sqlalchemy import select

from . import store
from .settings import settings

COLLECTION = "feedback_solutions"
FAILURES = "failure_patterns"
TOKEN = re.compile(r"[A-Za-z0-9가-힣]+")
FEEDBACK_CASE_CONTRACT = "latest-final-feedback-case-v2"


def _evaluation_index(user_id, project_id, connection=None):
    """Read every revision, including withdrawals and unobserved/neutral edits.

    Filtering consent first would make an older positive observation reappear.
    The journal and raw submission remain immutable; this is only a projection.
    """
    from .ax import ledger, feedback_events
    from .ax.contracts import now
    cutoff = now()
    with (nullcontext(connection) if connection is not None else store.engine.connect()) as c:
        rows = c.execute(select(ledger.events.c.event_id, ledger.events.c.run_id, ledger.events.c.event_type,
            ledger.events.c.payload, ledger.events.c.created_at).join(ledger.heads,
            ledger.heads.c.run_id == ledger.events.c.run_id).where(
            ledger.heads.c.tenant_id == user_id, ledger.heads.c.project_id == project_id,
            ledger.events.c.event_type.in_((feedback_events.KIND, 'FEEDBACK_SUBMITTED')))).mappings().all()
    submissions = {r['event_id']: json.loads(r['payload']) for r in rows if r['event_type'] == 'FEEDBACK_SUBMITTED'}
    events = {r['event_id']: json.loads(r['payload']) for r in rows if r['event_type'] == feedback_events.KIND}
    superseded = {e.get('supersedes_event_id') for e in events.values()}
    latest, scopes = {}, {}
    for event in sorted(events.values(), key=lambda e:(e['label_available_at'], e['event_id'])):
        if (event['event_id'] in superseded or event.get('evaluation_stage') != 's10_feedback'
                or event['label_available_at'] > cutoff):
            continue
        key = (event['run_id'], event['candidate_id'])
        latest[key] = event
    # Empty feedback submissions may still explicitly withdraw training consent.
    for row in sorted(rows, key=lambda r:(r['created_at'], r['event_id'])):
        if row['created_at'] > cutoff:
            continue
        payload = json.loads(row['payload'])
        scopes[row['run_id']] = payload.get('scope', payload.get('training_consent_scope'))
    return dict(events=events, latest=latest, superseded=superseded, submissions=submissions, scopes=scopes, cutoff=cutoff)


def _source_row(event, index):
    rows = index['submissions'].get(event.get('source_event_id'), {}).get('rows', [])
    return next((r for r in rows if r.get('concept_id') == event.get('candidate_id')), {})


def _stored_run_permission(run_id, user_id, project_id):
    """An explicit persisted opt-out wins over any old eligible document."""
    with store.engine.connect() as c:
        raw = c.execute(select(store.states.c.state_json).join(store.runs,
            store.runs.c.run_id == store.states.c.run_id).where(store.runs.c.run_id == run_id,
            store.runs.c.user_id == user_id)).scalar()
    if raw is None:
        return False
    state = json.loads(raw)
    scratch = state.get('scratch', {})
    return (scratch.get('ax_project_id', user_id) == project_id
            and scratch.get('training_consent') != 'NO_TRAINING')


def _feedback_class(rating):
    if type(rating) not in (int, float):
        return None
    if 1 <= rating <= 2:
        return FAILURES
    if max(4, int(settings.cfg('feedback_rag.min_rating_to_store', 4))) <= rating <= 5:
        return COLLECTION
    return None


def _legacy_feedback_index(user_id):
    """Exact raw-feedback identities for cases predating the common journal."""
    with store.engine.connect() as c:
        rows = c.execute(select(store.feedback).join(store.runs,
            store.runs.c.run_id == store.feedback.c.run_id).where(store.runs.c.user_id == user_id)
            .order_by(store.feedback.c.id)).mappings().all()
    latest = {}
    for row in rows:
        latest[(row['run_id'], row['concept_id'])] = dict(row)
    return {prefix + run + '-' + candidate: row for (run, candidate), row in latest.items()
            for prefix in ('fb-', 'fx-')}


def _legacy_case_current(doc, index, user_id, project_id, permissions):
    meta = doc.get('meta', {})
    if meta.get('common_evaluation_ids') is not None:
        return True
    source = index.get(doc['id'])
    if source is None:
        # Generic legacy adapters have no feedback identity. A feedback case
        # whose source was removed must not become such an unscoped adapter.
        return not (meta.get('run_id') or meta.get('case_contract') or doc['id'].startswith(('fb-', 'fx-')))
    key = (source['run_id'], user_id, project_id)
    if key not in permissions:
        permissions[key] = _stored_run_permission(*key)
    return (permissions[key] and meta.get('rating') == source['rating']
            and _feedback_class(source['rating']) == doc.get('collection')
            and ('adopted' not in meta or bool(meta.get('adopted')) == bool(source.get('adopted')))
            and meta.get('source_feedback_log_id', source['id']) == source['id'])


def _case_identity(meta, index):
    if meta.get('run_id') and meta.get('concept_id'):
        return meta['run_id'], meta['concept_id']
    # Old negative documents omitted their candidate/run fields, but contain
    # actual common-event references. Never infer an identity from the title.
    identities = {(index['events'][ref]['run_id'], index['events'][ref]['candidate_id'])
                  for ref in meta.get('common_evaluation_ids', []) if ref in index['events']}
    return next(iter(identities)) if len(identities) == 1 else None


def _case_current(doc, index):
    meta = doc.get('meta', {})
    if meta.get('retrieval_active') is False:
        return False
    if meta.get('common_evaluation_ids') is None:
        return True  # Legacy adapters without a common-evaluation contract.
    key = _case_identity(meta, index)
    latest = index['latest'].get(key)
    if not latest or latest['event_id'] not in meta['common_evaluation_ids']:
        return False
    if latest.get('synthetic') or not latest.get('observed_mask') or latest.get('training_consent_scope') != 'PROJECT_ONLY':
        return False
    row = _source_row(latest, index)
    rating = latest.get('reviewer_model_and_rubric_version', {}).get('rating')
    # A corrected normalized value cannot silently retain the old source rating.
    if type(rating) not in (int, float) or latest.get('observed_value') != (rating - 3) / 2:
        return False
    return (meta.get('rating') == rating and _feedback_class(rating) == doc.get('collection')
            and ('adopted' not in meta or bool(meta.get('adopted')) == bool(row.get('adopted'))))


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
    from .ax.mode_contract import unified
    if not settings.cfg("feedback_rag.enabled", True) or not state.feedback:
        return 0
    if unified(state):
        from .ax import ledger
        # Serialize with immutable feedback submissions. A late writer cannot
        # replace a newer case using an earlier in-memory feedback payload.
        with ledger.transaction() as connection:
            head = ledger._head(connection, state.run_id, lock=True)
            ledger.authorize(head, state.user_id)
            index = _evaluation_index(state.user_id, head['project_id'], connection)
            return _write_feedback(state, distill, index=index, connection=connection)
    return _write_feedback(state, distill)


def _write_feedback(state, distill, *, index=None, connection=None):
    from .domain import problem_type
    wmax = float(settings.cfg("feedback_rag.weight_max", 1.3))
    written = 0
    legacy = _legacy_feedback_index(state.user_id) if index is None else {}
    gen = distill.get("generalized_problem") or state.intake.frame.restated_problem
    contra = "; ".join(c.label for c in state.definition.technical_contradictions[:2]) or ""

    for fb in state.feedback.solution_feedback:
        concept = state.concept(fb.concept_id)
        if not concept:
            continue
        latest = index['latest'].get((state.run_id, concept.id)) if index is not None else None
        raw_legacy = legacy.get(f'fb-{state.run_id}-{concept.id}')
        if raw_legacy and (raw_legacy['rating'] != fb.rating or bool(raw_legacy['adopted']) != bool(fb.adopted)
                           or raw_legacy['comment'] != fb.comment or json.loads(raw_legacy['reason_tags']) != fb.reason_tags):
            continue
        if index is not None:
            if (not latest or latest.get('synthetic') or latest['training_consent_scope'] != 'PROJECT_ONLY'
                    or index['scopes'].get(state.run_id) != 'PROJECT_ONLY'
                    or state.scratch.get('training_consent') != 'PROJECT_ONLY'):
                continue
            raw = _source_row(latest, index)
            if any(raw.get(field, default) != getattr(fb, field) for field, default in (
                    ('rating', 3), ('adopted', None), ('adopted_explicit', False), ('comment', ''), ('reason_tags', []))):
                continue  # An out-of-order projection must not resurrect stale text.
        refs = [latest['event_id']] if latest else []
        context = {"problem_type": problem_type(state), "conditions": concept.assumptions,
                   "contradiction_structure": [t.coupling_mechanism or t.label for t in state.definition.technical_contradictions],
                   "domain_lesson": distill.get("domain_lesson", ""),
                   "accepted_patterns": distill.get("accepted_patterns", []),
                   "rejected_patterns": distill.get("rejected_patterns", []),
                   "feedback_status": "USER_PREFERENCE_NOT_VALIDATION",
                   "retrieval_active": True, "case_contract": FEEDBACK_CASE_CONTRACT,
                   "run_id": state.run_id, "concept_id": concept.id, "adopted": bool(fb.adopted)}
        if index is not None:
            context.update(common_evaluation_ids=refs, project_id=state.scratch.get('ax_project_id', state.user_id),
                           source_evaluation_id=latest['event_id'], source_submission_id=latest.get('source_event_id'),
                           source_available_at=latest['label_available_at'])
        elif raw_legacy:
            context['source_feedback_log_id'] = raw_legacy['id']
        positive_id, negative_id = f"fb-{state.run_id}-{concept.id}", f"fx-{state.run_id}-{concept.id}"
        rating = latest.get('reviewer_model_and_rubric_version', {}).get('rating') if latest else fb.rating
        classification = _feedback_class(rating)
        if latest and (type(rating) not in (int, float) or not latest.get('observed_mask')
                       or latest.get('observed_value') != (rating - 3) / 2):
            classification = None
        if classification == COLLECTION:
            weight = min(wmax, 1.0 + 0.05 * (fb.rating - 3) + (0.05 if fb.adopted else 0.0))
            store.rag_upsert(
                doc_id=positive_id,
                collection=COLLECTION,
                doc=f"{gen} :: {contra} :: {concept.title} — {concept.one_liner} :: {context['domain_lesson']} :: {context['accepted_patterns']}",
                meta={
                    **context,
                    "user_id": state.user_id,
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
                deactivate_ids=(negative_id,), connection=connection,
            )
            written += 1
        elif classification == FAILURES:
            store.rag_upsert(
                doc_id=negative_id,
                collection=FAILURES,
                doc=f"{gen} :: {concept.title} :: {fb.comment or ''} :: {', '.join(fb.reason_tags)}",
                meta={**context, "user_id": state.user_id, "industry": state.domain.industry, "reason_tags": fb.reason_tags,
                      "title": concept.title, "rating": fb.rating},
                weight=1.0,
                deactivate_ids=(positive_id,), connection=connection,
            )
            written += 1
        else:
            store.rag_deactivate((positive_id, negative_id), connection=connection,
                                 superseded_by=latest['event_id'] if latest else None)
    return written


# ─────────────────────────────── 읽기
def retrieve(query: str, collection: str = COLLECTION, k: int | None = None,
             industry: str = "", user_id: str = "", problem_type: str = "", conditions=(), require_common=False,
             project_id: str | None = None) -> list[dict]:
    if not settings.cfg("feedback_rag.enabled", True):
        return []
    docs = [dict(doc, collection=collection) for doc in store.rag_all(collection)]
    if require_common: docs=[d for d in docs if d.get('meta',{}).get('common_evaluation_ids')]
    if settings.require_user_auth or user_id:
        docs = [d for d in docs if d.get("meta", {}).get("user_id") == user_id and user_id]
    project_id = project_id or user_id
    docs = [d for d in docs if d.get('meta', {}).get('project_id', user_id) == project_id]
    common = any(d.get('meta', {}).get('common_evaluation_ids') is not None for d in docs)
    index = _evaluation_index(user_id, project_id) if common else None
    legacy = _legacy_feedback_index(user_id) if any(d.get('meta', {}).get('common_evaluation_ids') is None for d in docs) else {}
    permissions = {}
    docs = [d for d in docs if _case_allowed(d.get('meta', {}), user_id, index=index, permissions=permissions)
            and _case_current(d, index) and _legacy_case_current(d, legacy, user_id, project_id, permissions)]
    for doc in docs:
        if doc.get('meta', {}).get('common_evaluation_ids') is not None:
            latest = index['latest'][_case_identity(doc['meta'], index)]
            # Older valid documents listed every historical feedback event.
            # Return the actual current source alone without rewriting storage.
            doc['meta'] = dict(doc['meta'], common_evaluation_ids=[latest['event_id']],
                               source_evaluation_id=latest['event_id'])
    if not docs:
        return []
    k = k or int(settings.cfg("feedback_rag.top_k", 3))
    idf = _idf([d["doc"] for d in docs])
    qv = _vec(query)
    scored: list[tuple[float, dict]] = []
    for d in docs:
        meta = d.get("meta", {})
        kind = meta.get("problem_type")
        if not kind and "is_engineering" in meta:
            kind = "PHYSICAL_TECHNICAL" if meta["is_engineering"] else "ORGANIZATIONAL_BUSINESS"
        if problem_type and kind != problem_type:
            continue
        sim = _cosine(qv, _vec(d["doc"]), idf) * float(d.get("weight") or 1.0)
        if conditions and meta.get("conditions"):
            sim *= 1 + .15 * _cosine(_vec(" ".join(conditions)), _vec(" ".join(meta['conditions'])), idf)
        if industry and d.get("meta", {}).get("industry") == industry:
            sim *= 1.1
        if sim > 0.05:
            scored.append((sim, d))
    scored.sort(key=lambda x: -x[0])
    out = []
    for sim, d in scored[:k]:
        store.rag_touch(d["id"])
        out.append({"id": d['id'], "score": round(sim, 3), "doc": d["doc"], "meta": d.get("meta", {}),
                    "cross_industry": bool(industry and d.get("meta", {}).get("industry") != industry)})
    return out


def _case_allowed(meta, user_id, *, index=None, permissions=None):
    refs=meta.get('common_evaluation_ids')
    if refs is None: return True  # Preserve legacy service records and adapters.
    if not user_id or not refs:
        return False
    project_id = meta.get('project_id', user_id)
    index = index if index is not None else _evaluation_index(user_id, project_id)
    permissions = permissions if permissions is not None else {}
    revisions = {e.get('supersedes_event_id'): e for e in index['events'].values() if e.get('supersedes_event_id')}
    for ref in refs:
        event = index['events'].get(ref)
        if event is None:
            return False
        seen = set()
        while event['event_id'] in revisions and event['event_id'] not in seen:
            seen.add(event['event_id'])
            event = revisions[event['event_id']]
        run_id = event['run_id']
        if (event.get('training_consent_scope') != 'PROJECT_ONLY' or event.get('synthetic')
                or event['label_available_at'] > index['cutoff'] or index['scopes'].get(run_id) != 'PROJECT_ONLY'):
            return False
        key = (run_id, user_id, project_id)
        if key not in permissions:
            permissions[key] = _stored_run_permission(*key)
        if not permissions[key]:
            return False
    return True


def case_permissions_current(state):
    ids=set(state.scratch.get('prior_case_ids',[]))
    if not ids: return True
    docs={d['id']:d for collection in (COLLECTION,FAILURES) for d in store.rag_all(collection)}
    sources = state.scratch.get('prior_case_sources', {})
    indexes, permissions, legacy = {}, {}, None
    for ident in ids:
        if ident not in docs:
            return False
        meta = sources.get(ident, {}).get('meta', docs[ident].get('meta', {}))
        if meta.get('user_id', state.user_id) != state.user_id:
            return False
        project = meta.get('project_id', state.user_id)
        if project != state.scratch.get('ax_project_id', state.user_id):
            return False
        if meta.get('common_evaluation_ids') is None:
            if legacy is None:
                legacy = _legacy_feedback_index(state.user_id)
            source = legacy.get(ident)
            if source is None and ident.startswith(('fb-', 'fx-')):
                return False
            if source is not None:
                key = (source['run_id'], state.user_id, project)
                if key not in permissions:
                    permissions[key] = _stored_run_permission(*key)
                if not permissions[key]:
                    return False
        if meta.get('common_evaluation_ids') is not None and project not in indexes:
            indexes[project] = _evaluation_index(state.user_id, project)
        if not _case_allowed(meta, state.user_id, index=indexes.get(project), permissions=permissions):
            return False
    return True


def case_sources_current(state, *, request_text=None):
    """Rating/source freshness is distinct from historical consent permission.

    Call this only before a NEW paid request; already-paid replay may still use
    the recorded historical input when its consent remains valid.
    """
    ids = set(state.scratch.get('prior_case_ids', []))
    if request_text is not None:
        headers = ('[참고: 과거 유사 문제에서 사용자가 높게 평가한 접근]',
                   '[참고: 과거에 거절된 패턴 — 같은 실수를 반복하지 마라]',
                   '[과거 사용자 피드백의 가설성 교훈 — 사실·절대 금지로 승격하지 않는다]')
        if not any(header in request_text for header in headers):
            return True
        # A candidate's historical prior_case_ids inside review JSON are audit
        # provenance, not a newly injected reference block for this request.
        ids = {ident for ident in ids if re.search(r'(?m)^- \[' + re.escape(ident) + r'\](?:\s|$)', request_text)}
    if not ids:
        return True
    docs = {d['id']: d for collection in (COLLECTION, FAILURES) for d in store.rag_all(collection)}
    sources = state.scratch.get('prior_case_sources', {})
    indexes, permissions = {}, {}
    legacy = _legacy_feedback_index(state.user_id) if any(
        sources.get(ident, docs.get(ident, {})).get('meta', {}).get('common_evaluation_ids') is None for ident in ids) else {}
    for ident in ids:
        if ident not in docs:
            return False
        doc = sources.get(ident, docs[ident])
        meta = doc.get('meta', {})
        project = meta.get('project_id', state.user_id)
        if meta.get('common_evaluation_ids') is not None and project not in indexes:
            indexes[project] = _evaluation_index(state.user_id, project)
        if (not _case_current(doc, indexes.get(project))
                or not _legacy_case_current(doc, legacy, state.user_id, project, permissions)):
            return False
    return True


def _remember_sources(state, hits, *, replace=False):
    sources = {} if replace else dict(state.scratch.get('prior_case_sources', {}))
    for hit in hits:
        meta = hit.get('meta', {})
        sources[hit['id']] = dict(id=hit['id'], collection=_feedback_class(meta.get('rating')), meta={
            key: meta[key] for key in ('user_id', 'project_id', 'run_id', 'concept_id', 'rating', 'adopted',
                'common_evaluation_ids', 'source_evaluation_id', 'source_feedback_log_id') if key in meta})
    state.scratch['prior_case_sources'] = sources


def prior_cases_block(state) -> str:
    from .domain import problem_type
    """S6 개념 구체화 프롬프트에 주입할 과거 사례 블록(과적합 방지 규칙 포함)."""
    if not settings.cfg("feedback_rag.enabled", True):
        return ""
    query = f"{state.intake.frame.restated_problem} {' '.join(c.label for c in state.definition.technical_contradictions[:2])}"
    options = dict(industry=state.domain.industry, user_id=state.user_id, problem_type=problem_type(state),
                   project_id=state.scratch.get('ax_project_id', state.user_id),
                   conditions=[c.statement for c in state.constraints.items])
    from .ax.mode_contract import unified
    options['require_common']=unified(state)
    hits = retrieve(query, **options)
    fails = retrieve(query, collection=FAILURES, k=2, **options)
    state.scratch["prior_case_ids"] = [h['id'] for h in hits + fails]
    _remember_sources(state, hits + fails, replace=True)
    if not hits and not fails:
        return ""
    limit = int(settings.cfg("feedback_rag.max_influenced_concepts", 3))
    lines = []
    if hits:
        lines.append("[참고: 과거 유사 문제에서 사용자가 높게 평가한 접근]")
        for h in hits:
            m = h["meta"]
            lines.append(f"- [{h['id']}] ({h['score']}, 타산업={h['cross_industry']}) {m.get('title','')}: {m.get('mechanism','')[:300]} / 조건: {m.get('conditions',[])} / 패턴: {m.get('accepted_patterns',[])}")
        lines.append("[사용 규칙]")
        lines.append("- 위 사례는 사용자 선호이며 실증 근거가 아니다. 적용 조건의 호환성을 확인하고 그대로 복사하지 마라.")
        lines.append(f"- 도출할 개념 중 최대 {limit}개까지만 이 방향을 반영하고, 나머지는 반드시 독립적으로 새로 도출하라.")
        lines.append("- 현재 시스템의 제약과 충돌하면 무시하라.")
    if fails:
        lines.append("[참고: 과거에 거절된 패턴 — 같은 실수를 반복하지 마라]")
        for f in fails:
            lines.append(f"- [{f['id']}] {f['meta'].get('title','')}: {f['meta'].get('rejected_patterns', [])} / 교훈: {f['meta'].get('domain_lesson','')} / {', '.join(f['meta'].get('reason_tags', []))}")
    return "\n".join(lines)


def lessons_block(state):
    from .domain import problem_type
    from .ax.mode_contract import unified
    hits = retrieve(state.raw_query, collection=FAILURES, k=2, industry=state.domain.industry,
                    user_id=state.user_id, project_id=state.scratch.get('ax_project_id', state.user_id),
                    problem_type=problem_type(state),require_common=unified(state))
    state.scratch['prior_case_ids']=sorted(set(state.scratch.get('prior_case_ids',[]))|{h['id'] for h in hits})
    _remember_sources(state, hits)
    identify = state.scratch.get('ax_bundle', {}).get('rag_case_contract') == FEEDBACK_CASE_CONTRACT
    return "\n[과거 사용자 피드백의 가설성 교훈 — 사실·절대 금지로 승격하지 않는다]\n" + "\n".join(
        f"- {('[' + h['id'] + '] ') if identify else ''}{h['meta'].get('domain_lesson','')} / 실패 패턴: {h['meta'].get('rejected_patterns',[])} / 적용 조건: {h['meta'].get('conditions',[])}"
        for h in hits) if hits else ""


def stats() -> dict:
    return {"feedback_solutions": len(store.rag_all(COLLECTION)),
            "failure_patterns": len(store.rag_all(FAILURES))}
