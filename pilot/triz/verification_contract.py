"""Always-applied analysis audit contract, including runs with pinned prompts."""
from __future__ import annotations

import copy
import json
import math

VERSION = "analysis-verification-v3-20261008"
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
            "observations.source_contract/source_provenance에 따라 직접 사용자 보고와 생성 요약을 구별한다. "
            "frame와 confirmed_facts는 생성 요약이며 필드 이름만으로 관측 사실이 되지 않는다. "
            "analysis_context의 기존 분석도 검토할 주장이다. "
            "관측 근거를 인용할 때 observations.user_query, observations.attachments, observations.answers, "
            "observations.confirmed_facts 등의 실제 경로와 뒷받침하는 내용을 적는다. "
            "시도·실패 이력은 원문/사용자 답변의 직접 근거가 있어야 한다. '현실에서 안 통한다'는 의견을 '이미 시도해서 실패했다'로 바꾸지 않는다. "
            "자동 생성한 요약·기능 모델·원인 가설을 관측 사실로 승격하지 않는다.\n" +
            json.dumps(support, ensure_ascii=False) +
            analysis_guidance(state, node))


def verifier_supplement(rubric):
    required = [{"id": row["id"], "min_score": row.get("min_score", 1.0), "text": row["text"]}
                for row in rubric.get("criteria", []) if row.get("required")]
    return (f"\n\n[필수 독립 검증 계약 {VERSION}]\n"
            "모든 기준을 정확히 한 번 채점한다. required 기준은 문체의 완벽성이 아닌 요구 충족 여부로 "
            "1(충족)/0(실제 위반)을 판단한다. 단지 더 상세히 쓸 수 있다는 이유로 0.8/0.9를 주지 않는다. "
            "위반에는 정확한 JSON path, 현재 값의 직접 인용, 해당 기준 및 입력 근거와의 충돌 또는 필수 근거의 누락을 제시한다. "
            "필수 기준 미달, 미해결 수정 지시 또는 결함이 있으면 PASS 금지. "
            "제공된 deterministic_inventory의 실제 BASIC 개수·인덱스·rank·등록 이름을 대조한다. "
            "검사 대상에 없는 값이나 기계적 사실과 반대인 주장을 결함 근거로 만들지 않는다. "
            "observations.source_provenance를 확인한다. frame/confirmed_facts는 생성 요약이므로 원문·실제 사용자 답변과 대조한다. "
            "원문에 없는 시도·실패 이력을 frame.prior_attempts만으로 관측이라고 인정하지 않는다. "
            "boundary.chosen_system과 사용자 확정 경계를 보존하고 상위 시스템의 목적을 모듈 주기능으로 강요하지 않는다. "
            "BASIC은 선택한 시스템의 존재 목적을 나타내는 유익 기능이며 수행자는 그 구성요소일 수 있다. "
            "BASIC 개수는 rank로만 센다. 같은 수행자의 보조/교정 작용은 별개 주기능이 아니다. "
            "독립된 공동목적이 여러 개면 근거 있는 대표 BASIC 하나와 다른 필수 USEFUL 간선을 전체 모델에서 함께 평가한다. "
            "다른 핵심 기능의 AUXILIARY 표시는 앱 저장 규약이며 목적 삭제·중요도 격하가 아니다. 모든 목적을 한 BASIC에 합성하라고 강요하지 않는다. "
            "kind·level·rank는 독립이다. BASIC=USEFUL이면서 INSUFFICIENT 또는 EXCESSIVE일 수 있고 NORMAL을 강요하지 않는다. "
            "PRODUCT가 object인 것은 정상이다. subject/object는 등록된 대상, 그 속성은 parameter_affected에 둔다. "
            "대상의 노출 정도·사용 범위·잔존 기간·전달 경로·승인 상태도 기능적 속성이다. 의미가 같은 '노출 정도→노출 여부' 같은 말바꾸기만을 필수 수정으로 요구하지 않는다. "
            "근거 상태는 evidence_status(OBSERVED/HYPOTHESIS/DERIVED), 인용은 evidence_refs, 한정·선정 이유는 notes다. "
            "HARMFUL은 예상 작용의 유해성도 표현하며 그 자체로 관측을 주장하지 않는다. level은 근거 확실성이 아니다. "
            "동일 주체-대상-작용의 interaction_cells.note나 components.notes에 명확한 가설 한정이 있으면 전체 맥락으로 인정하고 간선 notes에도 보존한다. "
            "유익/유해 간선의 공존과 interaction_cells의 '+-' 요약은 모순이 아니며 작용 조건·속성으로 구별한다. "
            "Su-Field에서 하중·응력·열사이클 부하는 물질이 아니다. S1/S2는 실제 운반체이며 S2→F→S1 방향을 모델별로 판단한다. "
            "한 하중의 유익 열전달과 유해 손상이 공존할 수 있고 유익 효과가 다른 작용의 HARMFUL/EXCESSIVE를 배제하지 않는다. "
            "CECA는 원인 노드.parents=[그 원인이 유발하는 결과 ID], TARGET_DISADVANTAGE.parents=[]이다. "
            "손실 N1←의도 N2←원인 N3이면 N2.parents=[N1], N3.parents=[N2]이며 N2.parents에 N3를 넣지 않는다. AND/OR도 이 방향을 바꾸지 않는다. "
            "조직의 규칙·권한·유인 작용은 물리적 힘이라고 주장하지 않는 한 허용되는 기능 표현이다. "
            "수정 예시는 결정검사와 동일한 스키마를 만족해야 하며 관리한다·최적화한다 같은 금지된 모호 동사나 속성 객체화를 권고하지 않는다. "
            "NW는 명시된 사건 전후/비교조건의 기준값과 장기 세대 이력을 구분한다. 확인된 이전 기준값·처리 이력을 과거 시제만으로 거부하지 않는다. "
            "가능성에 대한 응답은 사건 발생 단정이 아니며 확정 경계 정의는 관측 위조가 아니다. 가설 표기의 문장·문단·셀 적용 범위를 읽는다. "
            "수정사항을 element_findings 배열로 구체화할 수 있다: "
            '{"path":"function_edges[0].rank","issue":"결함",'
            '"suggested_correction":"근거에 맞는 수정", "evidence":"산출물 또는 관측 근거", "criterion_id":"C1"}. '
            "필수 미달은 element_findings로 위반 위치·값·근거와 실행 가능한 수정안을 연결한다. "
            "model_opinions의 이전 판정·수정 지시는 모델 의견이며 관측 근거나 통과 권한이 아니다. "
            "현재 전체 출력을 독립 검증하되 앞선 지시를 뒤집으면 어떤 원문/스키마 근거로 그 지시가 잘못됐는지 criterion comment에 설명한다. "
            "이미 수정된 과거 지적을 반복하지 말고 현재 전체 JSON의 실제 결함을 한 번에 찾아라. "
            "선택적 문체/상세화 조언은 comment에만 적고, 결함이 없으면 revision_instructions와 element_findings는 빈 배열이다. "
            "수정 지시 없는 REVISE/REJECT는 금지한다.\n필수 기준: " + json.dumps(required, ensure_ascii=False))


def repair_supplement(verdict):
    return (f"\n\n[전체 산출물 선택 수정 계약 {VERSION}]\n"
            "아래 지적의 경로와 의존 요소만 수정한 뒤 원래 스키마의 전체 JSON을 반환한다. "
            "부분 객체, 변경 목록, JSON patch만 반환하지 않는다. 모든 필수 최상위 필드를 보존한다. "
            "통과한 요소와 식별자는 유지하되, 지적된 중복·허구·잘못된 요소는 근거에 따라 제거·교체한다. "
            "검증 의견도 원문·현재 출력·스키마와 대조한다. PRODUCT를 object에서 빼거나 속성을 object로 만드는 잘못된 지시는 따르지 않는다. "
            "subject/object 변경 시 실제 컴포넌트의 이름·역할, 모든 연결 간선·상호작용·도식을 함께 갱신한다. "
            "가짜 성능 속성 노드를 만들어 참조만 맞추지 않는다. action에는 관리한다·최적화한다 대신 실제 변화/유지를 일으키는 구체 작용을 쓴다. "
            "이미 표시된 가설·가능성, 관측된 사건 전후 기준값, BASIC의 부족/과잉 수준을 점수 때문에 사실과 다르게 바꾸지 않는다. "
            "notes·evidence_status·evidence_refs를 전체 JSON에 보존한다. 불확실한 유해 작용은 HARMFUL+HYPOTHESIS가 가능하며 level로 불확실성을 대신하지 않는다. "
            "공동목적의 대표 BASIC 하나를 선택한 이유를 notes에 적고 다른 필수 유익 작용도 보존한다. 동의어 치환·불필요한 합성/분리 대신 실제 결함을 고친다. "
            "CECA는 원인 노드.parents=[결과 ID], TARGET_DISADVANTAGE.parents=[]이다. N2가 N1의 원인이면 N2.parents=[N1]만 두고 N1.parents에 N2를 역추가하지 않는다. "
            "대안 원인들은 같은 결과를 parents로 가리키며 AND/OR을 위해 방향을 뒤집지 않는다. 수리 후 전체 손실 연결과 순환 여부를 다시 확인한다. "
            "이전 지적과 이번 지적을 함께 검토하되 모순되는 지시에는 최신 원문 근거와 스키마를 우선하고 허용된 notes 등에 판단 근거를 남긴다. "
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
