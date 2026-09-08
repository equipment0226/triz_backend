"""검증 계층: 루브릭 LLM 검증 + 결정론적 규칙 + 제약 엔진 보조."""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from . import knowledge as K
from .schema import Constraint, ConstraintSet, GlobalState
from .settings import settings

Checker = Callable[[Any], list[str]]


CATEGORY_KO = {
    "USER_STATED": "사용자명시", "ENVIRONMENT": "운전환경", "MATERIAL_COMPAT": "재료양립성",
    "PHYSICS": "물리법칙", "REGULATION": "안전·규제", "OPERATION": "운영·보전",
    "INTERFACE": "인터페이스", "ECONOMIC": "경제성",
}
KIND_KO = {"MUST_HAVE": "필수", "MUST_NOT_HAVE": "금지", "NUMERIC": "수치", "PREFERENCE": "선호"}


# ────────────────────────────── 제약 블록 (모든 프롬프트에 주입)
def constraints_block(state: GlobalState) -> str:
    items = state.constraints.items
    lines: list[str] = []
    if not items:
        lines.append("(명시된 제약조건 없음. 단, 비용·안전·기존 운영 연속성은 항상 암묵적 제약이다.)")
    for c in items:
        num = f" [{c.parameter} {c.operator} {c.value}{c.unit}]" if c.operator != "none" else ""
        zone = f" @{c.zone}" if c.zone else ""
        tag = KIND_KO.get(c.kind, c.kind)
        cat = CATEGORY_KO.get(c.category, c.category)
        hard = "HARD" if c.hard else "soft"
        line = f"- ({c.id}/{tag}/{cat}/{hard}){zone} {c.statement}{num}"
        if c.rationale:
            line += f"\n    └ 이유: {c.rationale}"
        if c.violation_example:
            line += f"\n    └ 흔한 오답: {c.violation_example}"
        lines.append(line)
    if state.constraints.open_questions:
        lines.append("- (확인 필요) " + " / ".join(state.constraints.open_questions))

    taboo = state.scratch.get("taboo") or []
    if taboo:
        lines.append("")
        lines.append("[이 도메인의 금기 — 이것을 제안하면 현장에서 즉시 기각된다]")
        for t in taboo:
            zone = f"@{t.get('zone', '전체')}" if t.get("zone") else ""
            lines.append(f"- {zone} {t.get('item', '')} — {t.get('why', '')}")
        lines.append("※ 단, 금기는 '적용 영역'이 있다. 다른 영역에서는 허용될 수 있으니 영역을 구분해 판단하라.")
    return "\n".join(lines)


def taboo_block(state: GlobalState) -> str:
    taboo = state.scratch.get("taboo") or []
    if not taboo:
        return ""
    body = "\n".join(f"- @{t.get('zone', '전체')} {t.get('item', '')} ({t.get('why', '')})"
                     for t in taboo)
    return ("[절대 금기 — 이를 위반한 개념은 생성 자체를 하지 마라]\n" + body +
            "\n(영역이 다르면 허용될 수 있다. 예: 찤4버 내부는 금지, 대기측 구동부는 허용)")


def constraints_full(state: GlobalState) -> list[dict]:
    return [
        {"constraint_id": c.id, "kind": c.kind, "category": c.category, "zone": c.zone or "시스템 전체",
         "statement": c.statement, "parameter": c.parameter, "operator": c.operator,
         "value": c.value, "unit": c.unit, "hard": c.hard, "rationale": c.rationale,
         "violation_example": c.violation_example}
        for c in state.constraints.items
    ]


def rubric_criteria_text(rubric: dict) -> str:
    return "\n".join(
        f"- {c['id']} (가중치 {c.get('weight', 0)}): {c['text']}" for c in rubric.get("criteria", [])
    )


# ──────────────────────────────── 결정론적 검사 (LLM 없이)
def check_function_model(data: dict) -> list[str]:
    issues: list[str] = []
    names = {c.get("name", "") for c in data.get("components", [])}
    edges = data.get("function_edges", [])
    if not edges:
        return ["기능 간선이 비어 있다."]
    for e in edges:
        if e.get("subject") not in names:
            issues.append(f"DET-05: 기능 주체 '{e.get('subject')}'가 컴포넌트 목록에 없다.")
        if e.get("object") not in names:
            issues.append(f"DET-05: 기능 대상 '{e.get('object')}'가 컴포넌트 목록에 없다.")
    basics = [e for e in edges if e.get("rank") == "BASIC"]
    if len(basics) != 1:
        issues.append(f"DET-05b: 주기능(BASIC)은 정확히 1개여야 하는데 {len(basics)}개다.")
    harmful = [e for e in edges if e.get("kind") == "HARMFUL"]
    if not harmful and not any(e.get("level") == "INSUFFICIENT" for e in edges):
        issues.append("DET-05c: 문제를 나타내는 유해 또는 부족 기능이 없다.")
    vague = ("제공한다", "개선한다", "최적화한다", "수행한다", "관리한다")
    for e in edges:
        if any(v in (e.get("action") or "") for v in vague):
            issues.append(f"DET-05d: 모호한 기능 동사 '{e.get('action')}' — 구체 동사로 바꿔라.")
    if not any(c.get("level") == "PRODUCT" for c in data.get("components", [])):
        issues.append("DET-05e: 가공/처리 대상(PRODUCT) 컴포넌트가 없다.")
    comps = data.get("components", [])
    min_comp = 2
    if len(comps) < min_comp:
        issues.append(f"DET-05f: 컴포넌트가 {min_comp}개 이상 필요한데 {len(comps)}개다. "
                      "작용 주체와 처리 대상을 구분하라.")
    subs = [c for c in comps if c.get("level") == "SUB"]
    # Domain-specific depth is audited by R3_FUNC; a fixed gearbox-oriented count
    # caused fabricated components in software and semiconductor models.
    return issues[:8]


def check_ceca(data: dict) -> list[str]:
    issues: list[str] = []
    nodes = data.get("nodes", [])
    if not nodes:
        return ["인과사슬 노드가 비어 있다."]
    ids = {n.get("id") for n in nodes}
    for n in nodes:
        for p in n.get("parents", []):
            if p not in ids:
                issues.append(f"DET-06: 존재하지 않는 상위 노드 참조 '{p}'.")
    if not any(n.get("node_type") == "ROOT_CAUSE" for n in nodes):
        issues.append("DET-06b: 근본 원인(ROOT_CAUSE) 노드가 없다.")
    if not any(n.get("node_type") == "TARGET_DISADVANTAGE" for n in nodes):
        issues.append("DET-06c: 최상단 손실(TARGET_DISADVANTAGE) 노드가 없다.")
    # 깊이 계산
    depth = _chain_depth(nodes)
    mind = settings.cfg("analysis.ceca_min_depth", 3)
    if depth < mind:
        issues.append(f"DET-06d: 사슬 깊이가 {depth}단으로 최소 {mind}단에 미달한다.")
    banned = ("관리 부족", "노후화", "인력 부족", "예산 부족")
    for n in nodes:
        if any(b in (n.get("text") or "") for b in banned):
            issues.append(f"DET-06e: 총론적 원인 '{n.get('text')}' — 메커니즘으로 서술하라.")
    return issues[:8]


def _chain_depth(nodes: list[dict]) -> int:
    by_id = {n.get("id"): n for n in nodes}
    best = 1
    for n in nodes:
        depth, cur, guard = 1, n, 0
        while cur.get("parents") and guard < 12:
            cur = by_id.get(cur["parents"][0]) or {}
            if not cur:
                break
            depth += 1
            guard += 1
        best = max(best, depth)
    return best


def check_contradictions(data: dict, scheme: str = "ENG_39") -> list[str]:
    issues: list[str] = []
    tcs = data.get("technical_contradictions", [])
    pcs = data.get("physical_contradictions", [])
    min_tc = settings.cfg("definition.min_technical_contradictions", 1)
    min_pc = settings.cfg("definition.min_physical_contradictions", 1)
    if len(tcs) < min_tc:
        issues.append(f"DET-01a: 기술적 모순이 최소 {min_tc}개 필요하다.")
    if len(pcs) < min_pc:
        issues.append(f"DET-03a: 물리적 모순이 최소 {min_pc}개 필요하다.")
    for tc in tcs:
        imp, wor = tc.get("improving_param_id"), tc.get("worsening_param_id")
        if not K.valid_param(imp, scheme) or not K.valid_param(wor, scheme):
            issues.append(f"DET-01: 파라미터 번호 오류 (개선 {imp}, 악화 {wor}).")
        elif imp == wor:
            issues.append(f"DET-01b: 개선/악화 파라미터가 같다(#{imp}). 물리적 모순으로 재정의하라.")
    for pc in pcs:
        if not pc.get("state_a") or not pc.get("state_b"):
            issues.append("DET-03: 물리적 모순의 두 상태가 모두 기술되어야 한다.")
        if pc.get("state_a", "").strip() == pc.get("state_b", "").strip():
            issues.append("DET-03b: 물리적 모순의 두 상태가 동일하다.")
        if not pc.get("parameter"):
            issues.append("DET-03c: 물리적 모순의 대상 파라미터가 비어 있다.")
    return issues[:8]


def check_principles(data: dict, allowed: list[int]) -> list[str]:
    issues: list[str] = []
    allowed_set = set(allowed)
    for a in data.get("applications", []):
        pid = a.get("principle_id")
        if pid not in allowed_set:
            issues.append(f"DET-07: 원리 #{pid}는 이번 조회 결과({sorted(allowed_set)})에 없다.")
        if len((a.get("idea") or "")) < 40:
            issues.append(f"DET-07b: 원리 #{pid} 아이디어가 지나치게 짧다. 구체화하라.")
    return issues[:8]


def check_standards(data: dict) -> list[str]:
    valid = K.standard_codes()
    issues = []
    for a in data.get("applications", []):
        if a.get("standard_code") not in valid:
            issues.append(f"DET-08: 존재하지 않는 표준해 코드 '{a.get('standard_code')}'.")
    return issues[:8]


def check_separation(data: dict) -> list[str]:
    kinds = {a.get("kind") for a in data.get("applications", [])}
    missing = {"TIME", "SPACE", "CONDITION", "SYSTEM_LEVEL"} - kinds
    if missing:
        return [f"DET-B1: 다음 분리 원리가 검토되지 않았다: {', '.join(sorted(missing))}"]
    return []


def check_ariz(data: dict, required_codes: list[str]) -> list[str]:
    got = {s.get("step_code") for s in data.get("steps", [])}
    missing = [c for c in required_codes if c not in got]
    if missing:
        return [f"DET-09: ARIZ 필수 스텝 누락: {', '.join(missing)}"]
    return []


def _norm_resource(name: str) -> str:
    return re.sub(r"[\s()（）\[\]{}·,/]|기존|신규|추가", "", (name or "")).lower()


def check_concepts(data: dict, resource_names: set[str]) -> list[str]:
    issues = []
    cs = data.get("concepts", [])
    mn = settings.cfg("solutions.min_concepts", 8)
    if len(cs) < mn:
        issues.append(f"DET-10a: 개념이 {len(cs)}개로 최소 {mn}개에 미달한다.")
    known = {_norm_resource(r) for r in resource_names if r}
    for c in cs:
        if not c.get("expected_effect"):
            issues.append(f"DET-10b: '{c.get('title')}'에 기대효과가 없다.")
        if len(c.get("assumptions") or []) < 2:
            issues.append(f"DET-10c: '{c.get('title')}'의 전제 가정이 부족하다(2개 이상).")
        for r in c.get("required_resources", []):
            if not r or r.startswith("신규:") or not known:
                continue
            key = _norm_resource(r)
            if key and not any(key in k or k in key for k in known):
                issues.append(f"DET-10: '{c.get('title')}'이 자원 목록에 없는 '{r}'을 사용한다. "
                              "기존 자원명을 쓰거나 '신규:' 접두사를 붙여라.")
    scales = {c.get("change_scale") for c in cs}
    if len(cs) >= 3 and len(scales) < 2:
        issues.append("DET-10d: 개조 규모(PARAMETER/PARTIAL/REDESIGN)가 다양하지 않다.")
    return issues[:8]


def check_review(data: dict, concept_ids: set[str]) -> list[str]:
    scores = data.get("scores", [])
    if not scores:
        return ["평가 결과가 비어 있다."]
    issues = []
    unknown = {s.get("concept_id") for s in scores} - concept_ids
    if unknown:
        issues.append(f"DET-R1: 존재하지 않는 개념 id 평가: {sorted(unknown)[:3]}")
    vals = [float(s.get("score", 3)) for s in scores]
    if vals and (max(vals) - min(vals)) < 1.0:
        issues.append("DET-R2: 점수 변별력이 없다(최고-최저 < 1점). 냉정하게 차등하라.")
    return issues


# ──────────────────────────────── 제약 사후 검사(코드)
NUM = re.compile(r"(-?\d+(?:\.\d+)?)")


def numeric_violation(text: str, c: Constraint) -> Optional[str]:
    """개념 본문에서 제약 파라미터와 같은 문맥의 수치를 찾아 단순 비교한다(보조 수단)."""
    if c.operator == "none" or not c.value or not c.parameter:
        return None
    try:
        limit = float(c.value)
    except ValueError:
        return None
    for line in text.split("\n"):
        if c.parameter and c.parameter in line:
            for m in NUM.finditer(line):
                val = float(m.group(1))
                if c.unit and c.unit not in line:
                    continue
                bad = (
                    (c.operator == ">=" and val < limit)
                    or (c.operator == "<=" and val > limit)
                    or (c.operator == "==" and val != limit)
                    or (c.operator == "!=" and val == limit)
                )
                if bad:
                    return f"{c.parameter} {val}{c.unit} 는 제약 {c.operator} {limit}{c.unit} 위반"
    return None


def resource_names(state: GlobalState) -> set[str]:
    return {r.name for r in state.analysis.resources}
