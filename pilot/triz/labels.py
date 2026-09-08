"""내부 ID(TC-xxxx, CPT-xxxx …)를 사람이 읽는 표현으로 바꾼다.

내부 추적에는 ID가 필요하지만, 리포트/화면에서는 사용자가 코드를 역추적하는 일이
없어야 한다. 최종 리포트는 ID를 완전히 제거하고, 중간 산출물은 병기한다.
"""
from __future__ import annotations

import re

# 뒤에 한글 조사(KP-abc123은)가 붙어도 잡히도록 끝에 \b 를 두지 않는다.
ID_RE = re.compile(r"\b(TC|PC|CPT|IDEA|KP|CON|SU|EV|TR|PER|STP|INT)-[0-9a-fA-F]{6,12}(?![0-9a-fA-F])")


def _short(text: str, n: int = 28) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def build_label_map(state) -> dict[str, str]:
    """ID → 표시용 라벨."""
    m: dict[str, str] = {}

    for i, c in enumerate(state.constraints.items, 1):
        m[c.id] = f"제약{i} 「{_short(c.statement, 24)}」"

    for i, t in enumerate(state.definition.technical_contradictions, 1):
        label = t.label or f"{_short(t.then_good, 12)} vs {_short(t.but_bad, 12)}"
        m[t.id] = f"기술모순{i} 「{_short(label, 26)}」"

    for i, p in enumerate(state.definition.physical_contradictions, 1):
        label = p.label or f"{p.element}의 {p.parameter}"
        m[p.id] = f"물리모순{i} 「{_short(label, 26)}」"

    for i, k in enumerate(state.definition.key_problems, 1):
        m[k.id] = f"핵심문제{i} 「{_short(k.title, 26)}」"

    for i, tr in enumerate(state.definition.trimming, 1):
        m[tr.id] = f"트리밍{i} 「{_short(tr.target_component, 18)}」"

    for i, su in enumerate(state.analysis.su_fields, 1):
        m[su.id] = f"물질장모델{i} 「{_short(su.label, 20)}」"

    for c in state.concepts:
        m[c.id] = f"「{_short(c.title, 30)}」"

    for idea in state.solve.raw_ideas:
        m[idea.id] = f"「{_short(idea.title or idea.idea, 24)}」"

    for i, e in enumerate(state.evidence, 1):
        m[e.id] = f"근거{i} 「{_short(e.title or e.claim, 24)}」"

    for p in state.evaluation.reviewers:
        m[p.persona_id] = p.role_name

    return m


def humanize(text: str, labels: dict[str, str], keep_code: bool = False) -> str:
    """문자열 안의 ID를 라벨로 치환한다. 매핑이 없으면 코드를 지운다."""
    if not text:
        return text

    def sub(match: re.Match[str]) -> str:
        code = match.group(0)
        label = labels.get(code)
        if not label:
            return ""
        return f"{label}({code})" if keep_code else label

    out = ID_RE.sub(sub, text)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"(^|\n)[ \t]*[·,]\s*", r"\1", out)
    return out.strip()


def label_of(value, labels: dict[str, str], keep_code: bool = False) -> str:
    """단일 ID 또는 ID 목록을 라벨로."""
    if isinstance(value, (list, tuple, set)):
        return " · ".join(label_of(v, labels, keep_code) for v in value if v)
    return humanize(str(value or ""), labels, keep_code) or str(value or "")
