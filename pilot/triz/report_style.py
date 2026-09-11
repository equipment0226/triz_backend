"""Presentation-only Korean register and reference formatting; source artifacts stay intact."""
import re
from html import escape
from pydantic import BaseModel
from .labels import build_label_map, humanize, display_value

_ADJECTIVES = set("가능 불가능 필요 불필요 중요 유효 무효 적합 부적합 충분 불충분 부족 안전 위험 유리 불리 용이 곤란 명확 불명확 확실 불확실 정확 부정확 단순 복잡 동일 유사 상이 민감 강력 강인 우수 취약 과도 과다 적절 부적절 합리 비합리 타당 부당 필수 필연 현저 미미 상당 심각 빈번 희박 적당 특수 일반 양호 불량 모호 엄격 어렵 간단 다양 풍부 저렴 비싸 편리 불편 긍정 부정 확고 긴급 필요충분 지속가능".split())
_END = r"(?=$|[\s.!?。…,;:|<>\]\)}*\"'])"

def plain_text(value):
    """Normalize common formal/report endings without changing numbers, URLs or saved facts."""
    def text(chunk):
        chunk = re.sub(r"([가-힣]*)합니다" + _END,
            lambda m: m[1] + ("하다" if m[1] in _ADJECTIVES else "한다"), chunk)
        for old, new in (("입니다", "이다"), ("아닙니다", "아니다"), ("드립니다", "한다"),
                         ("있어요", "있다"), ("없어요", "없다"), ("이에요", "이다"), ("예요", "이다"),
                         ("하세요", "하라"), ("해요", "한다"), ("주세요", "달라"), ("습니다", "다")):
            chunk = re.sub(re.escape(old) + _END, new, chunk)
        # ㅂ니다: 됩니다 → 된다, 생깁니다 → 생긴다, 다릅니다 → 다르다.
        def ending(m):
            prefix, syllable = m[1], m[2]
            offset = ord(syllable) - 0xAC00
            if offset % 28 != 17:
                return m[0]
            stem = chr(ord(syllable) - 17)
            adjective = prefix + stem in ("다르", "빠르", "느리", "크", "기", "멀")
            return prefix + (stem if adjective else chr(ord(stem) + 4)) + "다"
        chunk = re.sub(r"([가-힣]*)([가-힣])니다" + _END, ending, chunk)
        chunk = re.sub(r"(인가|한가|있는가|없는가|할까|될까|있나|없나)요" + _END, r"\1", chunk)
        return chunk
    # Do not rewrite link destinations or inline code identifiers.
    parts = re.split(r"(https?://[^\s<>]+|(?<!`)`[^`\n]+`(?!`))", str(value))
    return "".join(p if i % 2 else text(p) for i, p in enumerate(parts))

def plain_value(value):
    if isinstance(value, str):
        return plain_text(value)
    if isinstance(value, BaseModel):
        return value.model_copy(update={k: plain_value(getattr(value, k)) for k in type(value).model_fields})
    if isinstance(value, dict):
        return {k: v if k in ('url', 'identifier', 'id', 'run_id', 'user_id', 'markdown') else plain_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain_value(v) for v in value]
    return value

def report_state(state):
    # A view passes the same detached copy to templates, diagrams and reference
    # cards. Prepare its text once; this transient flag is never serialized.
    if getattr(state, '_report_prepared', False):
        return state
    labels = build_label_map(state)
    fields = ('raw_query', 'domain', 'intake', 'confirm', 'constraints', 'analysis', 'definition', 'solve', 'concepts',
              'evidence', 'constraint_checks', 'evaluation', 'report')
    result = state.model_copy(update={k: plain_value(display_value(getattr(state, k), labels)) for k in fields})
    result.scratch = dict(state.scratch)
    from .evidence import search_summary
    result.scratch['search_status'] = search_summary(state)
    for key in ('title', 'excluded_concepts', 's_curve', 'taboo', 'principle_patents', 'patent_additions', 'related_references', 'evidence_mappings'):
        if key in result.scratch:
            result.scratch[key] = plain_value(display_value(result.scratch[key], labels))
    result.control = state.control.model_copy(update={'warnings': plain_value(display_value(state.control.warnings, labels))})
    object.__setattr__(result, '_report_prepared', True)
    return result

def reference_cards(state, concept):
    labels = build_label_map(state)
    def human(s): return plain_text(humanize(str(s or ''), labels))
    cards = []
    for r in state.evidences(concept.evidence_ids):
        if not r.url.startswith(('https://', 'http://')):
            continue
        mapping = state.scratch.get('evidence_mappings', {}).get(concept.id, {}).get(r.identifier, {})
        cards.append(dict(title=r.title or r.claim, url=r.url, kind={'PATENT':'특허','PAPER':'논문'}.get(r.source_type,'참고자료'),
            description=human(mapping.get('mechanism') or r.claim), scope=human(r.evidence_scope),
            identifier=r.identifier, status='연결 근거' if r.verified else '미검증 참고자료'))
    for related in state.scratch.get('related_references', []):
        if related.get('concept_id') != concept.id:
            continue
        r = related['reference']
        if not r.get('url', '').startswith(('https://', 'http://')):
            continue
        cards.append(dict(title=r['title'], url=r['url'], kind='특허' if r.get('source_type')=='PATENT' else '논문',
            description=human(related.get('reason')), scope='', identifier=r.get('identifier',''),
            status='유사 사례 · 적용성 추가 검토 필요'))
    return cards

def references_html(state, concept):
    out = ['<div class="reference-list">']
    for r in reference_cards(state, concept):
        out.append('<article class="reference-card"><p class="reference-status">'+escape(r['status'])+'</p>'
            '<a class="reference-title" target="_blank" rel="noopener noreferrer" href="'+escape(r['url'],quote=True)+'">'
            '<span class="reference-kind">'+escape(r['kind'])+'</span> '+escape(r['title'])+' ↗</a>'
            '<p class="reference-description">'+escape(r['description'])+'</p>'
            '<p class="reference-meta">'+escape(r['identifier']+' · '+r['scope'])+'</p></article>')
    for gap in state.scratch.get('evidence_gaps', []):
        if gap.get('title') == concept.title:
            out.append('<p class="reference-description">'+escape('·'.join('특허' if k=='PATENT' else '논문' for k in gap['missing']))+' 근거의 추가 확보가 필요하다.</p>')
    return ''.join(out)+'</div>'
