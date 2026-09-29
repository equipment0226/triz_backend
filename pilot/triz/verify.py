"""검증 계층: 루브릭 LLM 검증 + 결정론적 규칙 + 제약 엔진 보조."""
from __future__ import annotations

import json
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional

from . import knowledge as K
from .schema import Constraint, ConstraintCheckResult, ConstraintSet, GlobalState
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
        lines.append("(명시된 제약조건 없음. 비용·안전·운영 영향은 검토하되 사용자가 정하지 않은 한계를 절대 제약으로 만들지 않는다.)")
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

    taboo = confirmed_taboos(state)
    if taboo:
        lines.append("")
        lines.append("[이 도메인의 금기 — 이것을 제안하면 현장에서 즉시 기각된다]")
        for t in taboo:
            zone = f"@{t.get('zone', '전체')}" if t.get("zone") else ""
            lines.append(f"- {zone} {t.get('item', '')} — {t.get('why', '')}")
        lines.append("※ 단, 금기는 '적용 영역'이 있다. 다른 영역에서는 허용될 수 있으니 영역을 구분해 판단하라.")
    return "\n".join(lines)


def taboo_block(state: GlobalState) -> str:
    taboo = confirmed_taboos(state)
    if not taboo:
        return ""
    body = "\n".join(f"- @{t.get('zone', '전체')} {t.get('item', '')} ({t.get('why', '')})"
                     for t in taboo)
    return ("[절대 금기 — 이를 위반한 개념은 생성 자체를 하지 마라]\n" + body +
            "\n(영역이 다르면 허용될 수 있다. 예: 챔버 내부는 금지, 대기측 구동부는 허용)")


def confirmed_taboos(state):
    constraints = {c.id: c for c in state.constraints.hard_items() if c.source in ("USER", "REGULATION")}
    return [t for t in state.scratch.get("taboo", [])
            if t.get("constraint_id") in constraints and t.get("confirmed") is True]


def constraints_full(state: GlobalState) -> list[dict]:
    return [
        {"constraint_id": c.id, "kind": c.kind, "category": c.category, "zone": c.zone or "시스템 전체",
         "statement": c.statement, "parameter": c.parameter, "operator": c.operator,
         "value": c.value, "unit": c.unit, "hard": c.hard, "rationale": c.rationale,
         "source": c.source, "confidence": c.confidence, "violation_example": c.violation_example}
        for c in state.constraints.items
    ]


def normalize_constraint_result(result: ConstraintCheckResult, constraints: ConstraintSet
                                ) -> tuple[ConstraintCheckResult, dict]:
    """Derive the gate from known per-constraint rows, never from a model's summary.

    Source/confidence are context, not permission to change the saved hard flag.
    A known FAIL excludes the candidate for either hard or soft constraints.
    Invalid or contradictory evidence cannot establish a failure or a pass.
    """
    normalized = result.model_copy(deep=True)
    known = {}
    duplicate_definitions = set()
    for constraint in constraints.items:
        if constraint.id in known:
            duplicate_definitions.add(constraint.id)
        else:
            known[constraint.id] = constraint
    grouped = {key: [] for key in known}
    issues, unknown_ids, duplicate_ids, missing_hard_ids, missing_ids = [], [], [], [], []
    uncertain = bool(duplicate_definitions) or any(not key.strip() for key in known)
    if uncertain:
        issues.append('CONSTRAINT_IDS_AMBIGUOUS: 제약 정의의 ID가 비어 있거나 중복됩니다.')
    for row in result.per_constraint:
        cid = row.get('constraint_id') if isinstance(row, dict) else None
        if not isinstance(cid, str) or cid not in known:
            unknown_ids.append(cid if isinstance(cid, str) else '(invalid)')
            uncertain = True
            continue
        grouped[cid].append(row)
    if unknown_ids:
        issues.append('UNKNOWN_CONSTRAINT_IDS: 등록되지 않은 제약 판정은 탈락 근거로 쓰지 않습니다.')

    rows, hard_failures, soft_failures, hard_unknowns = [], [], [], []
    for cid, constraint in known.items():
        supplied = grouped[cid]
        if not supplied:
            verdict, reason = 'UNKNOWN', '해당 제약의 개별 판정이 누락되어 확인이 필요합니다.'
            missing_ids.append(cid)
            if constraint.hard:
                missing_hard_ids.append(cid)
        else:
            verdicts = {row.get('verdict') for row in supplied if isinstance(row.get('verdict'), str)}
            invalid = len(verdicts) != 1 or any(row.get('verdict') not in ('PASS', 'FAIL', 'UNKNOWN') for row in supplied)
            if len(supplied) > 1:
                duplicate_ids.append(cid)
            if invalid or cid in duplicate_definitions or not cid.strip():
                verdict, reason = 'UNKNOWN', '중복·상충하거나 잘못된 개별 판정이 있어 확인이 필요합니다.'
                uncertain = True
                issues.append(f'INVALID_CONSTRAINT_VERDICT: {cid}')
            else:
                verdict = next(iter(verdicts))
                reason = ' / '.join(dict.fromkeys(row.get('reason', '') for row in supplied
                    if isinstance(row.get('reason'), str) and row['reason']))
        rows.append({'constraint_id': cid, 'verdict': verdict, 'reason': reason})
        if constraint.hard and verdict == 'FAIL':
            hard_failures.append(cid)
        elif constraint.hard and verdict == 'UNKNOWN':
            hard_unknowns.append(cid)
        elif not constraint.hard and verdict == 'FAIL':
            soft_failures.append(cid)

    failures = [row['constraint_id'] for row in rows if row['verdict'] == 'FAIL']
    unresolved = [row['constraint_id'] for row in rows if row['verdict'] == 'UNKNOWN']
    # Summary-only allegations require clarification, not rejection or approval.
    for cid in result.violated_ids:
        if cid not in known:
            uncertain = True
            if cid not in unknown_ids:
                unknown_ids.append(cid)
            issues.append(f'UNKNOWN_SUMMARY_CONSTRAINT: {cid}')
        elif cid not in failures:
            uncertain = True
            issues.append(f'SUMMARY_ROW_CONTRADICTION: {cid}')
    if result.verdict == 'FAIL' and not failures:
        uncertain = True
        issues.append('UNSUPPORTED_FINAL_FAIL: 개별 판정으로 뒷받침되지 않는 최종 FAIL입니다.')
    if unresolved:
        issues.append('CONSTRAINT_CONFIRMATION_REQUIRED: hard·soft 제약의 개별 검증이 완료되지 않았습니다.')
    if soft_failures:
        issues.append('SOFT_FAILURE_ENFORCED: 사용자 선택 정책에 따라 soft 조건의 확정 위반도 후보에서 제외합니다.')
    normalized.per_constraint = rows
    normalized.violated_ids = failures
    normalized.verdict = 'FAIL' if failures else 'CONDITIONAL' if uncertain or unresolved else 'PASS'
    normalized.requires_user_decision = normalized.verdict == 'CONDITIONAL'
    if normalized.verdict == 'CONDITIONAL':
        clarification = '누락·불명확하거나 상충하는 제약 판정을 확인해야 합니다.'
        normalized.mitigation = ' '.join(value for value in (result.mitigation, clarification) if value)
    if normalized.verdict != result.verdict:
        issues.append(f'FINAL_VERDICT_RECOMPUTED: {result.verdict} → {normalized.verdict}')
    diagnostics = {'contract': 'constraint-verdict-v3', 'policy': 'all-known-constraint-failures-exclude',
        'concept_id': result.concept_id,
        'original_verdict': result.verdict, 'normalized_verdict': normalized.verdict,
        'original_violated_ids': list(result.violated_ids), 'issues': list(dict.fromkeys(issues)),
        'hard_failure_ids': hard_failures, 'soft_failure_ids': soft_failures,
        'hard_unknown_ids': hard_unknowns, 'missing_hard_ids': missing_hard_ids,
        'unresolved_constraint_ids': unresolved, 'missing_constraint_ids': missing_ids,
        'unknown_ids': list(dict.fromkeys(unknown_ids)), 'duplicate_ids': duplicate_ids,
        'duplicate_definition_ids': sorted(duplicate_definitions)}
    return normalized, diagnostics


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
    if len(ids) != len(nodes) or None in ids or "" in ids:
        return ["FATAL-CECA: 노드 ID가 비어 있거나 중복된다."]
    for n in nodes:
        for p in n.get("parents", []):
            if p not in ids:
                issues.append(f"FATAL-CECA: 존재하지 않는 상위 노드 참조 '{p}'.")
    if not any(n.get("node_type") == "ROOT_CAUSE" for n in nodes):
        issues.append("DET-06b: 근본 원인(ROOT_CAUSE) 노드가 없다.")
    if not any(n.get("node_type") == "TARGET_DISADVANTAGE" for n in nodes):
        issues.append("DET-06c: 최상단 손실(TARGET_DISADVANTAGE) 노드가 없다.")
    # 깊이 계산
    try:
        depth = _chain_depth(nodes)
    except ValueError:
        return ["FATAL-CECA: 인과사슬에 순환 참조가 있다."]
    roots = {n['id'] for n in nodes if n.get('node_type') == 'TARGET_DISADVANTAGE'}
    reachable = set(roots)
    for _ in nodes:
        reachable.update(n['id'] for n in nodes if set(n.get('parents', [])) & reachable)
    if reachable != ids:
        issues.append("FATAL-CECA: 최상단 손실과 연결되지 않은 원인 노드가 있다.")
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
    done, visiting = {}, set()
    def depth(key):
        if key in visiting:
            raise ValueError("cyclic cause graph")
        if key in done:
            return done[key]
        visiting.add(key)
        value = 1 + max((depth(p) for p in by_id[key].get('parents', []) if p in by_id), default=0)
        visiting.remove(key)
        done[key] = value
        return value
    return max((depth(key) for key in by_id), default=0)


def check_contradictions(data: dict, scheme: str = "ENG_39") -> list[str]:
    issues: list[str] = []
    tcs = data.get("technical_contradictions", [])
    pcs = data.get("physical_contradictions", [])
    min_tc = settings.cfg("definition.min_technical_contradictions", 1)
    min_pc = settings.cfg("definition.min_physical_contradictions", 1)
    if len(tcs) < min_tc:
        issues.append(f"DET-01a: 기술적 모순이 최소 {min_tc}개 필요하다.")
    if len(pcs) < min_pc and not data.get("physical_not_applicable_reason"):
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


def check_standards(data: dict, allowed=None) -> list[str]:
    valid = K.standard_codes() if allowed is None else set(allowed) & K.standard_codes()
    issues = []
    for a in data.get("applications", []):
        if not isinstance(a,dict):
            issues.append('DET-08: 표준해 적용안 형식 오류')
            continue
        if a.get("standard_code") not in valid:
            issues.append(f"DET-08: 존재하지 않는 표준해 코드 '{a.get('standard_code')}'.")
        if a.get('resulting_model') is not None:
            from .su_field_model import check_model
            issues.extend('DET-08-model: '+message for message in check_model(a['resulting_model']))
    return issues[:8]


def check_separation(data: dict, *, catalog=None) -> list[str]:
    from .separation_contract import check
    return check(data, catalog=catalog)


def check_ariz(data: dict, required_codes: list[str]) -> list[str]:
    """Incomplete ARIZ execution must repair or stop, never finish with WARN."""
    from .schema import ARIZStep
    if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
        return ["FATAL-ARIZ: 결과는 steps 배열을 포함한 JSON 객체여야 한다."]
    steps = data["steps"]
    issues = []
    for code in required_codes:
        matches = [row for row in steps if isinstance(row, dict) and row.get("step_code") == code]
        if len(matches) != 1:
            issues.append(f"FATAL-ARIZ: 필수 스텝 {code}의 결과가 정확히 한 번 필요하다.")
    for index, row in enumerate(steps, 1):
        if not isinstance(row, dict):
            issues.append(f"FATAL-ARIZ: steps의 {index}번째 결과는 객체여야 한다.")
            continue
        code = row.get("step_code")
        if not isinstance(code, str) or not code.strip():
            issues.append(f"FATAL-ARIZ: steps의 {index}번째 결과에 step_code가 필요하다.")
        try:
            parsed = ARIZStep.model_validate(row)
        except ValueError:
            issues.append(f"FATAL-ARIZ: {code} 결과의 필드·표 구조가 ARIZStep 형식에 맞지 않는다.")
        else:
            if any(len(cells) != len(parsed.table_columns) for cells in parsed.table_rows):
                issues.append(f"FATAL-ARIZ: {code} 표의 각 행은 열 수와 같아야 한다.")
        if (row.get("status") not in ("DONE", "SKIPPED", "BLOCKED")
                or not isinstance(row.get("output"), str) or not row["output"].strip()):
            issues.append(f"FATAL-ARIZ: {code}에 상태와 검토 내용 또는 미적용·차단 이유가 필요하다.")
    return issues


def check_ariz_part5(data: dict, required_codes: list[str]) -> list[str]:
    """Part 5 must record each required review, including an honest no-idea result."""
    from .schema import ARIZStep
    if not isinstance(data, dict):
        return ["FATAL-ARIZ5: Part5 결과는 JSON 객체여야 한다."]
    steps = data.get("steps")
    steps = steps if isinstance(steps, list) else []
    issues = []
    for code in required_codes:
        matches = [row for row in steps if isinstance(row, dict) and row.get("step_code") == code]
        if len(matches) != 1:
            issues.append(f"FATAL-ARIZ5: 필수 스텝 {code}의 결과가 정확히 한 번 필요하다.")
            continue
        row = matches[0]
        try:
            ARIZStep.model_validate(row)
        except ValueError:
            issues.append(f"FATAL-ARIZ5: {code} 결과의 필드·표 구조가 ARIZStep 형식에 맞지 않는다.")
        if (row.get("status") not in ("DONE", "SKIPPED", "BLOCKED")
                or not isinstance(row.get("output"), str) or not row["output"].strip()):
            issues.append(f"FATAL-ARIZ5: {code}에 상태와 검토 내용 또는 미적용·차단 이유가 필요하다.")
    ideas = data.get("ideas")
    if not isinstance(ideas, list):
        issues.append("FATAL-ARIZ5: ideas는 배열이어야 한다. 도출한 아이디어가 없으면 []로 기록한다.")
    elif ideas:
        for idea in ideas:
            if (not isinstance(idea, dict)
                    or any(not isinstance(idea.get(k), str) or not idea[k].strip()
                           for k in ("title", "idea"))
                    or idea.get("source_step") not in ("5.1", "5.2", "5.3", "5.4")):
                issues.append("FATAL-ARIZ5: 각 idea에 title·idea·유효한 source_step이 필요하다.")
                break
        final = data.get("final_ideas")
        if not isinstance(final, list) or not any(isinstance(x, str) and x.strip() for x in final):
            issues.append("FATAL-ARIZ5: ideas의 검증 대상 요약을 final_ideas 배열에 기록한다.")
    else:
        if data.get("final_ideas") != []:
            issues.append("FATAL-ARIZ5: ideas가 비었으면 final_ideas도 빈 배열로 기록한다.")
        if not isinstance(data.get("unresolved_reason"), str) or not data["unresolved_reason"].strip():
            issues.append("FATAL-ARIZ5: 아이디어가 없으면 unresolved_reason에 지식베이스 적용 후에도 미해결인 이유를 기록한다.")
    return issues


def check_ariz_part6(data: dict) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return ["FATAL-ARIZ6: 6.1~6.3의 검토 근거와 제안을 items 배열로 기록한다."]
    items = data["items"]
    issues = []
    for code in ("6.1", "6.2", "6.3"):
        matches = [item for item in items if isinstance(item, dict) and item.get("step_code") == code]
        if len(matches) != 1:
            issues.append(f"FATAL-ARIZ6: {code} 검토 결과를 정확히 한 번 기록한다.")
        elif any(not isinstance(matches[0].get(k), str) or not matches[0][k].strip()
                 for k in ("observation", "suggestion")):
            issues.append(f"FATAL-ARIZ6: {code}에 구체적인 observation과 suggestion이 필요하다.")
    if len(items) != 3:
        issues.append("FATAL-ARIZ6: items에는 6.1·6.2·6.3의 세 검토만 기록한다.")
    return issues


def _norm_resource(name: str) -> str:
    return re.sub(r"[\s()（）\[\]{}·,/]|기존|신규|추가", "", (name or "")).lower()


def check_concepts(data: dict, resource_names: set[str]) -> list[str]:
    issues = []
    cs = data.get("concepts", [])
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


def check_review(data: dict, concept_ids: set[str], dimensions: Optional[list[str]] = None) -> list[str]:
    """Validate legacy reviews, or the complete assigned score matrix for meetings."""
    if not isinstance(data, dict):
        return ["DET-R0: 평가 결과는 scores 배열을 포함한 객체여야 한다."]
    scores = data.get("scores")
    if not isinstance(scores, list):
        return ["DET-R0: scores는 평가 객체의 배열이어야 한다."]
    if not scores:
        return ["평가 결과가 비어 있다."]

    strict = dimensions is not None
    assigned = set(dimensions or [])
    issues: list[str] = []
    seen_concepts: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    unassigned: set[str] = set()

    def valid_number(value: Any, lower: float, upper: float) -> bool:
        if isinstance(value, bool) or (strict and not isinstance(value, (int, float))):
            return False
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return False
        return math.isfinite(number) and lower <= number <= upper

    for index, score in enumerate(scores, 1):
        if not isinstance(score, dict):
            issues.append(f"DET-R0: 평가 {index}는 객체여야 한다.")
            continue
        concept_id = score.get("concept_id")
        if isinstance(concept_id, str) and concept_id.strip():
            seen_concepts.add(concept_id)
        else:
            issues.append(f"DET-R1: 평가 {index}의 concept_id는 비어 있지 않은 문자열이어야 한다.")

        rationale = score.get("rationale")
        if not valid_number(score.get("score"), 1, 5) or not isinstance(rationale, str) or not rationale.strip():
            issues.append(f"DET-R3: 평가 {index}는 유한한 1~5점과 비어 있지 않은 문자열 근거가 필요하다.")
        if not strict:
            continue

        dimension = score.get("dimension")
        if not isinstance(dimension, str) or dimension not in assigned:
            unassigned.add(dimension if isinstance(dimension, str) else "(유효한 차원 없음)")
        elif isinstance(concept_id, str) and concept_id in concept_ids:
            pair = (concept_id, dimension)
            if pair in pairs:
                duplicates.add(pair)
            pairs.add(pair)
        if not valid_number(score.get("confidence"), 0, 1):
            issues.append(f"DET-R4: 평가 {index}의 confidence는 유한한 0~1 숫자여야 한다.")
        red_flags = score.get("red_flags")
        if not isinstance(red_flags, list) or any(not isinstance(flag, str) for flag in red_flags):
            issues.append(f"DET-R5: 평가 {index}의 red_flags는 문자열 배열이어야 한다.")
        if "improvement_suggestion" in score and not isinstance(score["improvement_suggestion"], str):
            issues.append(f"DET-R6: 평가 {index}의 improvement_suggestion은 문자열이어야 한다.")

    unknown = seen_concepts - concept_ids
    if unknown:
        issues.append(f"DET-R1: 존재하지 않는 개념 id 평가: {sorted(unknown)[:3]}")
    missing = concept_ids - seen_concepts
    if missing:
        issues.append(f"DET-R2: 평가 누락 개념: {sorted(missing)}")
    if strict:
        missing_pairs = {(concept_id, dimension) for concept_id in concept_ids for dimension in assigned} - pairs
        if missing_pairs:
            issues.append(f"DET-R7: 담당 평가 차원 누락: {sorted(missing_pairs)}")
        if duplicates:
            issues.append(f"DET-R8: 중복된 개념·차원 평가: {sorted(duplicates)}")
        if unassigned:
            issues.append(f"DET-R9: 담당하지 않은 평가 차원: {sorted(unassigned)}")
    return issues


# ──────────────────────────────── 제약 사후 검사(코드)
_MEASURED_NUMBER = r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?"
NUMERIC_VALIDATION_CONTRACT = 'parameter-bound-observed-values-v1'
_OBSERVATION = re.compile(
    r"실측|측정\s*(?:값|치|결과|됨|되었|되었다|됐다)|관측\s*(?:값|치|결과|됨|되었|되었다|됐다)"
    r"|\b(?:measured|observed)\b", re.I)
_UNCONFIRMED_NUMBER = re.compile(
    r"목표|예상|추정|가정|미측정|미확인|미검증|불확|오차|예시|가령|설계값|설정값|기준값|기준선|요구값|"
    r"(?:개선|변경|적용)\s*전|"
    r"측정\s*(?:예정|계획|필요|전)|검증\s*(?:예정|계획|필요|전)|"
    r"확인\s*(?:예정|필요)|여부|아직|않|아니|아님|아닌|없|만약|경우|"
    r"\b(?:target|expected|estimated|assumed|unmeasured|unverified|uncertain|"
    r"hypothetical|planned|not|if|before|baseline)\b", re.I)


def _numeric_decimal(value: str) -> Optional[Decimal]:
    if not re.fullmatch(_MEASURED_NUMBER, value):
        return None
    try:
        result = Decimal(value.replace(',', ''))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def numeric_violation(text: str, c: Constraint) -> Optional[str]:
    """Only explicit measured values can override an uncertain model verdict.

    Free prose is not a measurement table: an ID, target, another parameter or
    nearby unit cannot establish failure. Deliberately abstain for conversions,
    open bounds, uncertainty and unsupported phrasing; the AI/HITL review still
    handles those. A None result does not establish compliance.
    """
    if c.operator not in ('<=', '>=', '==', '!=') or not c.parameter.strip() or not c.unit.strip():
        return None
    limit = _numeric_decimal(c.value.strip())
    if limit is None:
        return None

    # An exact unit must belong to this quantity, not somewhere in the sentence.
    # Preserve unit case (mW and MW are different). Do not accept m as mm or m/s.
    unit = re.escape(c.unit.strip())
    unit_end = r"(?![A-Za-z0-9_%/·^²³⁻])"
    glue = (r"(?:은|는|이|가|의)?\s*"
            r"(?:(?:실측|측정|관측)\s*(?:값|치|결과)?(?:은|는|이|가)?\s*)?"
            r"(?:(?:was|is|measured|observed)\s+)*(?:[:=]\s*)?")
    # A scoped constraint also needs its saved location bound to the parameter.
    # A measured external temperature cannot reject an internal-temperature rule.
    zone = (re.escape(c.zone.strip()) + r'(?:의)?\s*[:：]?\s*') if c.zone.strip() else ''
    start = r"(?<![\w-])" + zone + re.escape(c.parameter.strip()) + glue
    measured = re.compile(start + rf"(?P<low>{_MEASURED_NUMBER})\s*"
        rf"(?:(?:{unit})?\s*(?:~|～|–|—|\bto\b)\s*(?P<high>{_MEASURED_NUMBER})\s*)?"
        + unit + unit_end, re.I if not re.search('[A-Za-z]', c.unit) else 0)
    # Decimal points and thousands separators must stay inside their quantity.
    clauses = re.split(r"[\n;!?。]|(?<!\d)\.(?!\d)|(?<=\d)\.(?!\d)|,(?!\d)", text)
    for clause in clauses:
        if not _OBSERVATION.search(clause) or _UNCONFIRMED_NUMBER.search(clause):
            continue
        for match in measured.finditer(clause):
            suffix = clause[match.end():].lstrip()
            # Neither endpoints of an open bound nor an error bar are a point
            # measurement. Also reject malformed/unsupported compound units.
            if re.match(r"(?:이상|이하|초과|미만|내외|정도|까지|부터|에서|보다|±|\+/-|~|～|–|—|-|/|\^|\bto\b)", suffix):
                continue
            if re.match(r'[A-Za-z]', suffix) and not re.match(r'(?:was|is|measured|observed)\b', suffix, re.I):
                continue
            # Korean units can also be prefixes of a different word (개/개수).
            if re.search('[가-힣]$', c.unit) and re.match('[가-힣]', suffix) and not re.match(r'(?:은|는|이|가|로|으로|였|임|이다)', suffix):
                continue
            low = _numeric_decimal(match['low'])
            high = _numeric_decimal(match['high']) if match['high'] else low
            if low is None or high is None or low > high:
                continue
            # A range proves failure only if its entire interval violates.
            bad = ((c.operator == '>=' and high < limit)
                or (c.operator == '<=' and low > limit)
                or (c.operator == '==' and not low <= limit <= high)
                or (c.operator == '!=' and low == high == limit))
            if bad:
                value = str(low) if low == high else f'{low}~{high}'
                return f"{c.parameter} 실측값 {value}{c.unit} 는 제약 {c.operator} {limit}{c.unit} 위반"
    return None


def resource_names(state: GlobalState) -> set[str]:
    return {r.name for r in state.analysis.resources}
