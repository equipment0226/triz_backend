"""Always-applied analysis audit contract, including runs with pinned prompts."""
from __future__ import annotations

import copy
import json
import math

VERSION = "analysis-verification-v1-20261008"
RUBRIC_NODES = {
    "R1_INTAKE": "s1_extract", "R2_CANDIDATE": "s2_candidates",
    "R3_FUNC": "s3_function_model", "R3_SUF": "s3_sufield",
    "R3_RES": "s3_resources", "R3_CECA": "s3_ceca",
    "R4_IFR": "s4_ifr", "R4_CONTRA": "s4_contradictions",
    "R3_NW": "s3_nine_windows", "R3_CONSTRAINT": "s3_constraints",
    "R4_TRIM": "s4_trimming", "R4_KEY": "s4_key_problem",
}


def is_critical(rubric_id=None, node=""):
    # Intake may legitimately be incomplete before clarification and confirmation.
    return str(rubric_id or "").startswith(("R3_", "R4_")) or node.startswith(("s3_", "s4_"))


def effective_rubric(settings, rubric_id):
    """Overlay current mandatory safety criteria without mutating pinned bundles."""
    rubric = copy.deepcopy(settings.rubric(rubric_id))
    current = settings.rubrics.get(rubric_id)
    if not is_critical(rubric_id) or not current:
        return rubric
    if not rubric:
        rubric = copy.deepcopy(current)
        defaults = settings.rubrics.get("defaults", {})
        rubric.setdefault("pass_threshold", defaults.get("pass_threshold", .72))
        rubric.setdefault("reject_below", defaults.get("reject_below", .45))
        rubric["id"] = rubric_id
    required = {row["id"]: row for row in current.get("criteria", []) if row.get("required")}
    rubric["criteria"] = [copy.deepcopy(required.pop(row["id"], row)) for row in rubric.get("criteria", [])]
    rubric["criteria"].extend(copy.deepcopy(list(required.values())))
    return rubric


def _meaningful(value):
    if isinstance(value, str):
        return value.strip().lower() not in ("", "none", "n/a", "없음", "해당 없음", "없다")
    return bool(value)


def _instructions(value):
    if isinstance(value, str):
        value = [value]
    return [str(item) for item in value if _meaningful(item)] if isinstance(value, list) else []


def normalize_verdict(raw, rubric):
    """Scores may downgrade a judgment, never erase an explicit correction."""
    out = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    declared = out.get("verdict")
    instructions = _instructions(out.get("revision_instructions"))
    errors = []
    for field in ("revision_instructions", "fatal_flaws"):
        value = out.get(field)
        if value is not None and not isinstance(value, (str, list)):
            errors.append(f"{field} must be a string or an array")
    criteria = rubric.get("criteria", [])
    rows = out.get("per_criterion")
    try:
        if not criteria or not isinstance(rows, list) or len(rows) != len(criteria):
            raise ValueError("every rubric criterion must have exactly one score")
        ids = [row["id"] for row in rows]
        expected = {criterion["id"] for criterion in criteria}
        if len(set(ids)) != len(ids) or set(ids) != expected:
            raise ValueError("missing, duplicate or unknown criterion scores")
        scores = {}
        for row in rows:
            if isinstance(row["score"], bool):
                raise ValueError("boolean is not a criterion score")
            score = float(row["score"])
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("criterion scores must be finite numbers from 0 to 1")
            scores[row["id"]] = score
        weights = [float(criterion.get("weight", 0)) for criterion in criteria]
        if any(not math.isfinite(weight) or weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError("invalid rubric weights")
        out["score"] = sum(scores[c["id"]] * w for c, w in zip(criteria, weights)) / sum(weights)
        score_verdict = ("PASS" if out["score"] >= rubric["pass_threshold"] else
                         "REJECT" if out["score"] < rubric["reject_below"] else "REVISE")
        for criterion in criteria:
            if criterion.get("required"):
                minimum = float(criterion.get("min_score", 1.0))
                if not math.isfinite(minimum) or not 0 <= minimum <= 1:
                    raise ValueError("invalid required criterion threshold")
                if scores[criterion["id"]] < minimum:
                    instructions.append(f"필수 기준 {criterion['id']} 미충족: {criterion['text']} "
                                        f"(최소 {minimum:g}, 현재 {scores[criterion['id']]:g})")
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        errors.append(str(exc))
        out["score"] = 0.0
        score_verdict = "UNVERIFIED"

    findings = out.get("element_findings", [])
    if not isinstance(findings, list):
        errors.append("element_findings must be an array")
        findings = []
    valid_findings = []
    for finding in findings:
        if (not isinstance(finding, dict) or
                any(not isinstance(finding.get(k), str) for k in
                    ("path", "issue", "suggested_correction", "evidence", "criterion_id")) or
                not finding.get("path", "").strip() or not finding.get("issue", "").strip() or
                finding.get("criterion_id") not in {c["id"] for c in criteria}):
            errors.append("invalid element finding; include path, issue, suggested_correction, evidence, criterion_id")
        else:
            valid_findings.append(finding)
    out["element_findings"] = valid_findings
    out["fatal_flaws"] = _instructions(out.get("fatal_flaws"))
    if declared not in ("PASS", "REVISE", "REJECT"):
        errors.append("missing or invalid explicit verifier verdict")
    if errors:
        out["verdict"] = "UNVERIFIED"
        instructions.extend("검증 응답 불완전: " + message for message in errors)
    else:
        severity = {"PASS": 0, "REVISE": 1, "REJECT": 2}
        out["verdict"] = max((declared, score_verdict), key=severity.__getitem__)
        if instructions or valid_findings:
            out["verdict"] = max((out["verdict"], "REVISE"), key=severity.__getitem__)
    if out["fatal_flaws"]:
        out["verdict"] = "REJECT"
    out["revision_instructions"] = list(dict.fromkeys(instructions))
    out["verification_contract"] = VERSION
    return out


def analysis_context(state, node=""):
    from . import digest
    chosen = state.confirm.chosen() if state.confirm.user_confirmed else None
    context = {
        "boundary": {
            "user_confirmed": state.confirm.user_confirmed,
            "chosen_system": chosen.model_dump() if chosen else None,
            "target_system": digest.target_system(state),
            "super_system": state.domain.super_system,
            "problem_zone": state.confirm.problem_zone,
            "operative_zone": state.confirm.operative_zone,
            "operative_time": state.confirm.operative_time,
            "physical_scope": state.domain.physical_scope,
            "user_amendments": list(state.confirm.user_amendments),
        },
        "success_criteria": list(state.intake.frame.success_criteria),
    }
    if node.startswith(("s3_", "s4_")) and node != "s3_function_model":
        context["function_model"] = {
            "components": [row.model_dump() for row in state.analysis.components],
            "function_edges": [row.model_dump() for row in state.analysis.function_edges],
        }
    if node == "s3_function_model" and state.analysis.nine_windows:
        context["nine_windows"] = state.analysis.nine_windows.model_dump()
    if node == "s3_constraints" or node.startswith("s4_"):
        context["causal_hypotheses"] = ([row.model_dump() for row in state.analysis.ceca.nodes]
                                       if state.analysis.ceca else [])
        context["resources"] = [row.model_dump() for row in state.analysis.resources]
        context["resources_unavailable_reason"] = state.analysis.resources_unavailable_reason
    if node == "s3_constraints":
        context["su_fields"] = [row.model_dump() for row in state.analysis.su_fields]
        context["existing_constraints"] = [row.model_dump() for row in state.constraints.items]
    if node == "s4_key_problem":
        context["technical_contradictions"] = [row.model_dump() for row in state.definition.technical_contradictions]
        context["physical_contradictions"] = [row.model_dump() for row in state.definition.physical_contradictions]
        context["physical_not_applicable_reason"] = state.definition.physical_not_applicable_reason
        context["ifr"] = state.definition.ifr.model_dump() if state.definition.ifr else None
    return context


def generation_supplement(state, node):
    if not is_critical(node=node):
        return ""
    from .analysis_guidance import analysis_guidance
    support = {"analysis_context": analysis_context(state, node)}
    if node.startswith(("s3_", "s4_")):
        from . import digest
        support["observations"] = digest.facts_packet(state)
    return (f"\n\n[분석 검증 계약 {VERSION}]\n"
            "확정 경계를 기준으로 분석한다. 상위 시스템의 목적과 선택한 모듈의 주기능을 혼동하지 않는다. "
            "observations는 사용자 입력 근거이고 analysis_context의 기존 분석은 검토할 주장이다. "
            "관측 근거를 인용할 때 observations.user_query, observations.attachments, observations.answers, "
            "observations.confirmed_facts 등의 실제 경로와 뒷받침하는 내용을 적는다. "
            "자동 생성한 요약·기능 모델·원인 가설을 관측 사실로 승격하지 않는다.\n" +
            json.dumps(support, ensure_ascii=False) +
            analysis_guidance(state, node))


def verifier_supplement(rubric):
    required = [{"id": row["id"], "min_score": row.get("min_score", 1.0), "text": row["text"]}
                for row in rubric.get("criteria", []) if row.get("required")]
    return (f"\n\n[필수 독립 검증 계약 {VERSION}]\n"
            "모든 기준을 정확히 한 번 채점한다. 필수 기준 미달, 미해결 수정 지시 또는 결함이 있으면 PASS 금지. "
            "boundary.chosen_system과 사용자 확정 경계를 보존하고 상위 시스템의 목적을 모듈 주기능으로 강요하지 않는다. "
            "BASIC은 선택한 시스템의 존재 목적을 나타내는 유익 기능이어야 한다. "
            "수정사항을 element_findings 배열로 구체화할 수 있다: "
            '{"path":"function_edges[0].rank","issue":"결함",'
            '"suggested_correction":"근거에 맞는 수정", "evidence":"산출물 또는 관측 근거", "criterion_id":"C1"}. '
            "결함이 없으면 revision_instructions와 element_findings는 빈 배열이다. "
            "수정 지시 없는 REVISE/REJECT는 금지한다.\n필수 기준: " + json.dumps(required, ensure_ascii=False))


def repair_supplement(verdict):
    return (f"\n\n[전체 산출물 선택 수정 계약 {VERSION}]\n"
            "아래 지적의 경로와 의존 요소만 수정한 뒤 원래 스키마의 전체 JSON을 반환한다. "
            "부분 객체, 변경 목록, JSON patch만 반환하지 않는다. 모든 필수 최상위 필드를 보존한다. "
            "통과한 요소와 식별자는 유지하되, 지적된 중복·허구·잘못된 요소는 근거에 따라 제거·교체한다. "
            "수정 후 전체 산출물이 다시 결정론 검사와 독립 검증을 받는다.\n" +
            json.dumps({"element_findings": verdict.get("element_findings", []),
                        "revision_instructions": verdict.get("revision_instructions", []),
                        "fatal_flaws": verdict.get("fatal_flaws", [])}, ensure_ascii=False))


ARTIFACT_FIELDS = {
    's3_nine_windows': {'cells', 'insights'},
    's3_function_model': {'components', 'function_edges', 'interaction_cells', 'mermaid'},
    's3_sufield': {'su_fields'},
    's3_resources': {'resources', 'unavailable_reason'},
    's3_ceca': {'nodes', 'mermaid'},
    's3_constraints': {'constraints', 'taboo'},
    's4_ifr': {'statement', 'x_element', 'without', 'ideality_note', 'intensified', 'constraint_conflicts'},
    's4_contradictions': {'technical_contradictions', 'physical_contradictions',
                          'mapping_notes', 'physical_not_applicable_reason'},
    's4_trimming': {'trimming'},
    's4_key_problem': {'key_problems', 'dropped'},
}


def repair_shape_issues(previous, current, verdict=None, *, node=''):
    """Reject accidental partial-object repairs without freezing invalid rows/IDs."""
    if not isinstance(previous, dict):
        return []
    if not isinstance(current, dict):
        return ["DET-REPAIR-SHAPE: 전체 JSON 객체를 반환해야 한다."]
    # A malformed initial answer can be a single component instead of the
    # requested envelope. Do not force its invalid root keys into every repair.
    retained = set(previous) & ARTIFACT_FIELDS.get(node, set(previous))
    missing = sorted(retained - set(current))
    return ["DET-REPAIR-SHAPE: 부분 수정본에서 최상위 필드가 누락됐다: " + ", ".join(missing)] if missing else []
