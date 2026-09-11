"""Resolve internal references to readable, consistently numbered descriptions."""
from __future__ import annotations

import re
from functools import lru_cache
from pydantic import BaseModel

# ASCII boundaries also match IDs adjacent to Korean particles or punctuation.
_KINDS = {
    'TC': '기술모순', 'PC': '물리모순', 'CPT': '해결안', 'CB': '해결안',
    'IDEA': '아이디어', 'KP': '핵심문제', 'CON': '제약', 'SU': '물질장모델',
    'EV': '근거', 'TR': '트리밍', 'PER': '검토자', 'STP': '분석 단계',
    'INT': '확인 요청', 'SYS': '대상 시스템', 'ATT': '첨부자료', 'RUN': '분석',
}
ID_RE = re.compile(r'(?<![A-Za-z0-9_])(?:' + '|'.join(_KINDS) +
                   r')-[A-Za-z0-9]{6,32}(?![A-Za-z0-9_])', re.I)
_STRUCTURAL = {'id', 'key', 'identifier', 'url', 'href', 'parents', 'addresses',
               'source_ref', 'blocked_by', 'violated_ids', 'markdown', 'html', 'svg',
               'diagram_mermaid', 'mermaid', 'function_mermaid', 'completed_calls',
               'completed_call_inputs', 'input_hash', 'context_hash'}


def _short(text: str, n: int = 28) -> str:
    text = ' '.join(str(text or '').split())
    return text if len(text) <= n else text[:n - 1].rstrip() + '…'


def _description(*values, fallback='내용 확인 필요'):
    for value in values:
        text = ID_RE.sub('', str(value or ''))
        text = re.sub(r'해결(?:안|책)\s*\d+\s*', '', text)
        text = re.sub(r'\(\s*\)|\[\s*\]|「\s*」', '', text).strip(' ·:,-')
        if text:
            return _short(text)
    return fallback


def build_label_map(state) -> dict[str, str]:
    """Number concepts by stored order, independently of evaluation rank."""
    labels = {}
    def add(code, kind, number, *values):
        if code:
            labels[code] = f'{kind}{number} ({_description(*values)})'
    for i, c in enumerate(state.constraints.items, 1):
        add(c.id, '제약', i, c.statement)
    for i, c in enumerate(state.confirm.candidates, 1):
        add(c.id, '대상 시스템', i, c.name, c.description)
    for i, c in enumerate(state.definition.technical_contradictions, 1):
        add(c.id, '기술모순', i, c.label, f'{c.then_good} / {c.but_bad}')
    for i, c in enumerate(state.definition.physical_contradictions, 1):
        add(c.id, '물리모순', i, c.label, f'{c.element}의 {c.parameter}')
    for i, c in enumerate(state.definition.key_problems, 1):
        add(c.id, '핵심문제', i, c.title)
    for i, c in enumerate(state.definition.trimming, 1):
        add(c.id, '트리밍', i, c.target_component)
    for i, c in enumerate(state.analysis.su_fields, 1):
        add(c.id, '물질장모델', i, c.label, c.s1, c.s2)
    if state.analysis.ceca:
        for i, c in enumerate(state.analysis.ceca.nodes, 1):
            add(c.id, '원인', i, c.text)
    for i, c in enumerate(state.concepts, 1):
        add(c.id, '해결안', i, c.title, c.one_liner, c.working_principle, c.description)
    for i, c in enumerate(state.solve.raw_ideas, 1):
        add(c.id, '아이디어', i, c.title, c.idea)
    for i, c in enumerate(state.evidence, 1):
        add(c.id, '근거', i, c.title, c.claim)
    for c in state.evaluation.reviewers:
        labels[c.persona_id] = _description(c.role_name, fallback='검토자')
    # Avoid recursively expanding references in labels themselves.
    return {k: humanize(v, {}) for k, v in labels.items()}


@lru_cache(maxsize=64)
def _reference_pattern(keys):
    known = '|'.join(re.escape(k) for k in sorted(keys, key=len, reverse=True) if k)
    token = '(?:' + (known + '|' if known else '') + ID_RE.pattern + ')'
    # Consume legacy wrappers: 해결안1(CB-...) becomes one canonical label.
    wrapped = r'(?:해결(?:안|책)\s*\d+\s*)?[\(\[「]\s*`?(?P<wrapped>' + token + r')`?\s*[\)\]」]'
    bare = r'(?<![A-Za-z0-9_])(?P<bare>' + token + r')(?![A-Za-z0-9_])'
    return re.compile(wrapped + '|' + bare, re.I)


def humanize(text: str, labels: dict[str, str], keep_code: bool = False) -> str:
    """No display mode reintroduces IDs, even for unknown/legacy references."""
    if not text:
        return text
    return _humanizer(labels)(text)


def _humanizer(labels):
    lookup = {key.casefold(): value for key, value in labels.items()}
    def replace(match):
        code = match['wrapped'] or match['bare']
        return lookup.get(code.casefold()) or (_KINDS.get(code.split('-')[0].upper(), '참조 항목') + ' (내용 확인 필요)')
    pattern = _reference_pattern(tuple(labels))
    # Most prose contains no reference at all. A small literal-prefix check
    # avoids running the full legacy-reference expression over long transcripts.
    prefixes = tuple(dict.fromkeys([k.casefold().split('-')[0] for k in labels] +
                                   [k.casefold() + '-' for k in _KINDS]))
    def resolve(text):
        folded = text.casefold()
        if not any(prefix in folded for prefix in prefixes):
            return text
        # Preserve real patent identifiers and link destinations.
        parts = re.split(r'(https?://[^\s<>\[\]"\x27]+)', str(text))
        return ''.join(part if i % 2 else pattern.sub(replace, part) for i, part in enumerate(parts))
    return resolve


def label_of(value, labels: dict[str, str], keep_code: bool = False) -> str:
    if isinstance(value, (list, tuple, set)):
        return ' · '.join(label_of(v, labels) for v in value if v)
    return humanize(str(value or ''), labels)


def display_value(value, labels):
    """Copy nested display text while retaining machine keys and relationships."""
    human = _humanizer(labels)
    def visit(item):
        if isinstance(item, str):
            return human(item)
        if isinstance(item, BaseModel):
            return item.model_copy(update={k: visit(getattr(item, k))
                for k in type(item).model_fields if not _structural(k)})
        if isinstance(item, dict):
            return {k: v if _structural(k) else visit(v) for k, v in item.items()}
        if isinstance(item, list):
            return [visit(v) for v in item]
        if isinstance(item, tuple):
            return tuple(visit(v) for v in item)
        return item
    return visit(value)


def _structural(key):
    return isinstance(key, str) and (key in _STRUCTURAL or key.endswith(('_id', '_ids', '_url')))
