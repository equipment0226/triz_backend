"""Review all sources and preserve their disposition; elaborate at most ten."""
from __future__ import annotations

import copy
import hashlib
import json

from . import agent, digest
from .context import AbortRun
from .schema import RawIdea, Stage
from .settings import settings


CONTRACT_VERSION = "representative-ideas-max10-v2"
MAX_IDEAS = 10
CONSOLIDATION_CONTRACT = """
[전체 원안 검토·대표 아이디어 최대 10개 계약 v2 — 이전의 무제한 유지 지시보다 우선]
모든 입력을 비교 검토한 뒤 후속 상세검토할 대표 ideas를 최대 10개로 통합·선정한다.
10개를 채울 의무는 없다. 앞 순서, 발상 기법별 할당, 다양성 점수만으로 자르지 않는다.
표현이나 목적만 비슷한 것은 중복이 아니다. 작동 원리, 개입 위치·변수, 적용 조건과 보호할 요구가
실질적으로 같을 때 통합한다. 같은 설계의 치수·표현 변형은 조건을 보존하며 묶는다.
고장 모드·성립 조건이 다른 기구를 억지로 하나의 해법에 숨기거나 새 조합을 발명하지 않는다.
복수 원안의 merge_reason에는 공통 기구, 개입 위치, 조건의 양립성과 차이 보존 방법을 기록한다.
통합 후에도 독립안이 10개를 넘으면 핵심 원인·모순 해결 기여, 기술적 성립 경로,
hard·soft 요구 적합성, 검증 가능성, 미확인 가정과 실행 부담을 비교해 대표안을 선정한다.
선정안에는 selection_reason을 기록하고 비선정 원안은 deferred에 원안 하나의 keep_ids와
구체적 reason을 남긴다. 단순 '10개 초과'나 '다양성 부족'은 사유가 아니다.
모든 입력 id는 ideas 또는 deferred의 keep_ids에 정확히 한 번만 나타나야 한다.
deferred는 상세검토 보류이며 기술적 불가능·제약 위반 확정이나 삭제를 의미하지 않는다.
TRADEOFF/UNSUPPORTED 표기만으로 보류하지 않는다. 대표안 전부를 S6에서 상세검토하고,
hard·soft 제약의 최종 검문은 유지한다. 원안과 통합·보류 사유는 보고서에 보존한다.
""".strip()


def _texts(value):
    return [text for text in value if isinstance(text, str) and text] if isinstance(value, list) else []


def _unique(values):
    return list(dict.fromkeys(values))


def _signature(ideas):
    data = [idea.model_dump(mode="json") for idea in ideas]
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def review_packet(idea):
    """Show only the current selection identity; retain source semantics.

    Stored ancestry remains unchanged. Re-merging a legacy inventory must not
    invite the model to select archived leaf IDs instead of the assigned groups.
    """
    hidden = {'source_idea_ids', 'source_idea_id', 'input_idea_ids', 'keep_ids', 'consolidation'}
    def clean(value, root=False):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()
                    if k not in hidden and (root or k != 'id')}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean(idea.model_dump(mode='json'), root=True)


def _context_signature(state):
    context = [digest.facts_packet(state), state.definition.model_dump(mode="json"),
               state.constraints.model_dump(mode="json"), digest.causal_packet(state)]
    return hashlib.sha256(json.dumps(context, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def is_current(state):
    record = state.scratch.get("idea_consolidation", {})
    return (record.get("contract") == CONTRACT_VERSION and record.get("coverage_complete") is True
            and len(state.solve.raw_ideas) <= MAX_IDEAS
            and record.get("context_signature") == _context_signature(state)
            and record.get("output_signature") == _signature(state.solve.raw_ideas))


def ensure_consolidated(ctx):
    """S6 retries from legacy projects must pass the same complete merge contract."""
    if not is_current(ctx.state):
        return consolidate(ctx)
    return None


def check_partition(data, input_ids):
    """Every source has one disposition; only up to ten advance to S6."""
    if not isinstance(data, dict) or not isinstance(data.get("ideas"), list):
        return ["FATAL-CONSOLIDATION: ideas 배열로 모든 입력 ID의 그룹을 반환해야 합니다."]
    expected, seen, issues = set(input_ids), set(), []
    if len(data['ideas']) > MAX_IDEAS:
        issues.append('FATAL-CONSOLIDATION: 대표 ideas는 최대 10개입니다. 전건 비교 후 나머지는 사유와 함께 deferred에 보존하세요.')
    deferred = data.get('deferred', [])
    if not isinstance(deferred, list):
        return ['FATAL-CONSOLIDATION: deferred는 배열이어야 합니다.']
    for row in deferred:
        if (not isinstance(row, dict) or not isinstance(row.get('keep_ids'), list)
                or len(row['keep_ids']) != 1 or not isinstance(row.get('reason'), str) or not row['reason'].strip()):
            issues.append('FATAL-CONSOLIDATION: deferred 각 항목에는 원안 ID 1개와 구체적인 reason이 필요합니다.')
    if deferred:
        for row in data['ideas']:
            if isinstance(row, dict) and not (isinstance(row.get('selection_reason'), str) and row['selection_reason'].strip()):
                issues.append('FATAL-CONSOLIDATION: 보류안 대비 대표안 선정 근거 selection_reason이 필요합니다.')
    for index, row in enumerate(data["ideas"] + deferred):
        if not isinstance(row, dict):
            issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}은 객체여야 합니다.")
            continue
        ids = row.get("keep_ids")
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i for i in ids):
            issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}의 keep_ids가 비어 있거나 잘못되었습니다.")
            continue
        if len(ids) != len(set(ids)) or seen.intersection(ids):
            issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}에 중복 배정된 입력 ID가 있습니다.")
        unknown = set(ids) - expected
        if unknown:
            issues.append("FATAL-CONSOLIDATION: 입력에 없는 ID: " + ", ".join(sorted(unknown)))
        if len(ids) > 1 and not (isinstance(row.get("merge_reason"), str) and row["merge_reason"].strip()):
            issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}에 기구·개입·조건의 동등성을 설명하는 merge_reason이 필요합니다.")
        for key in ("title", "idea", "mechanism", "mechanism_key", "intervention_variable",
                    "strongest_objection", "validation_test", "resolution_argument", "selection_reason"):
            if key in row and not isinstance(row[key], str):
                issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}의 {key}는 문자열이어야 합니다.")
        for key in ("addresses", "uses_resources", "conditions", "hypothesis_ids"):
            if key in row and (not isinstance(row[key], list) or any(not isinstance(v, str) for v in row[key])):
                issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}의 {key}는 문자열 배열이어야 합니다.")
        for key, allowed in (("resolution_status", {"RESOLVED", "TRADEOFF", "UNSUPPORTED"}),
                             ("novelty_class", {"SAME_DOMAIN", "CROSS_DOMAIN", "NEW"}),
                             ("feasibility_hint", {"HIGH", "MID", "LOW"})):
            if key in row and (not isinstance(row[key], str) or row[key] not in allowed):
                issues.append(f"FATAL-CONSOLIDATION: 그룹 {index + 1}의 {key} 값이 잘못되었습니다.")
        seen.update(ids)
    if expected - seen:
        issues.append("FATAL-CONSOLIDATION: 검토에서 누락된 입력 ID: " + ", ".join(sorted(expected - seen)))
    return issues


def _sources(ideas):
    sources = []
    for idea in ideas:
        previous = idea.detail.get("source_details")
        if isinstance(previous, list) and previous and all(isinstance(row, dict) for row in previous):
            sources.extend(copy.deepcopy(previous))
        else:
            row = idea.model_dump(mode="json", exclude={"detail"})
            row.update(copy.deepcopy(idea.detail))
            row.update(source_idea_id=idea.id, source_track=idea.track)
            sources.append(row)
    return sources


def _merged_idea(row, sources):
    base = sources[0]
    data = base.model_dump(mode="json")
    for key in ("title", "idea", "mechanism_key", "mechanism", "intervention_variable",
                "strongest_objection", "validation_test", "novelty_class", "feasibility_hint"):
        if row.get(key):
            data[key] = row[key]
    data["source_ref"] = " + ".join(_unique(i.source_ref for i in sources if i.source_ref))
    for key in ("uses_resources", "addresses", "conditions", "hypothesis_ids"):
        # New model annotations cannot erase the source's resources, scope or assumptions.
        data[key] = _unique([v for i in sources for v in getattr(i, key)] + _texts(row.get(key)))
    data["source_idea_ids"] = _unique(k for i in sources for k in (i.source_idea_ids or [i.id]))
    data["mechanism_key"] = data["mechanism_key"] or base.id
    status = row.get("resolution_status", base.resolution_status)
    if any(i.resolution_status == "TRADEOFF" for i in sources):
        status = "TRADEOFF"
    data["resolution_argument"] = row.get("resolution_argument", base.resolution_argument)
    if status == "RESOLVED" and not data["resolution_argument"]:
        status = "UNSUPPORTED"
    data["resolution_status"] = status
    detail = copy.deepcopy(base.detail)
    detail.update(source_details=_sources(sources),
                  source_tracks=_unique(t for i in sources for t in digest.idea_tracks(i) if t),
                  consolidation={"contract": CONTRACT_VERSION,
                                 "input_idea_ids": [i.id for i in sources],
                                 "selection_reason": row.get('selection_reason', ''),
                                 "merge_reason": row.get("merge_reason", "독립 아이디어로 유지")})
    data["detail"] = detail
    return RawIdea.model_validate(data)


def consolidate(ctx):
    """Commit only complete consolidation; leave all source ideas intact on failure.

    All source packets share a single context, including cross-track comparisons.
    An explicitly configured input limit stops rather than silently clipping.
    By default the provider's context limit and the existing budget gate apply.
    """
    state = ctx.state
    sources = list(state.solve.raw_ideas)
    previous = state.scratch.get('idea_consolidation', {})
    # Reconsider retained alternatives when the problem or inventory changes;
    # a prior portfolio decision must never silently erase them on a new merge.
    current_ids = {idea.id for idea in sources}
    prior_ids = {g['idea_id'] for g in previous.get('groups', [])}
    if previous.get('contract') == CONTRACT_VERSION and prior_ids <= current_ids:
        for raw in previous.get('deferred_ideas', []):
            if raw['id'] not in current_ids:
                sources.append(RawIdea.model_validate(raw))
                current_ids.add(raw['id'])
    input_ids = [idea.id for idea in sources]
    if len(input_ids) != len(set(input_ids)):
        raise AbortRun("아이디어 원안 ID가 중복되어 전건 통합을 중단합니다. 원안을 보존했습니다.")
    if not sources:
        return {"ideas": [], "coverage_note": "", "gaps": [], "need_more": False}
    variables = {
        "all_ideas": [review_packet(idea) for idea in sources],
        "allowed_idea_ids": input_ids,
        "facts": digest.facts_packet(state),
        "redefinition_hints": state.solve.gaps,
        "causal_packet": digest.causal_packet(state),
        "evidence": digest.relevant_evidence(state),
        "key_problems": [k.model_dump(mode="json") for k in state.definition.key_problems],
        "contradictions": digest.contradictions_digest(state),
        "constraints": state.constraints.model_dump(mode='json'),
        "consolidation_contract": CONSOLIDATION_CONTRACT,
    }
    input_bytes = len(json.dumps(variables, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    input_limit = max(0, int(settings.cfg("solutions.consolidation_max_input_bytes", 0)))
    if input_limit and input_bytes > input_limit:
        raise AbortRun(f"아이디어 전건 통합 입력이 길이 한도를 초과했습니다 ({input_bytes:,}/{input_limit:,} bytes). "
                       "원안은 모두 보존했으며 일부만 검토하지 않았습니다. 컨텍스트 한도를 조정한 뒤 재개할 수 있습니다.")
    result = agent.run_agent(
        ctx, node="s5_merge", label="전체 아이디어 통합 검토·대표안 선정", stage=Stage.S5.value,
        agent_id="solution_curator", prompt_id="P_S5_MERGE", tier="T2", rubric_id="R5_MERGE",
        checker=lambda data: check_partition(data, input_ids),
        max_tokens=int(settings.cfg("solutions.merge_max_tokens", 16000)),
        facts=json.dumps(variables["all_ideas"], ensure_ascii=False) + "\n" + CONSOLIDATION_CONTRACT,
        vars=variables, default=None,
    )
    issues = check_partition(result, input_ids)
    if issues:
        # Also protect callers that stub/cache the agent without running its checker.
        raise AbortRun("아이디어 전건 통합이 완료되지 않아 원안을 보존하고 중단합니다. " + "; ".join(issues))
    by_id = {idea.id: idea for idea in sources}
    merged = [_merged_idea(row, [by_id[i] for i in row["keep_ids"]]) for row in result["ideas"]]
    valid_ids = {item.id for item in state.definition.technical_contradictions}
    valid_ids.update(item.id for item in state.definition.physical_contradictions)
    for idea in merged:
        unknown = [cid for cid in idea.addresses if cid not in valid_ids]
        idea.addresses = [cid for cid in idea.addresses if cid in valid_ids]
        if unknown:
            idea.detail["consolidation"]["unrecognized_contradiction_ids"] = unknown
        if not idea.addresses:
            idea.resolution_status = "UNSUPPORTED"
            idea.detail["consolidation"]["scope_review_note"] = "유효한 모순 연결이 없어 후속 상세 검토에서 확인합니다."
    groups = [{"idea_id": idea.id, "input_idea_ids": list(row["keep_ids"]),
               "source_idea_ids": list(idea.source_idea_ids),
               "source_tracks": list(digest.idea_tracks(idea)),
               "selection_reason": row.get('selection_reason', ''),
               "merge_reason": row.get("merge_reason", "독립 아이디어로 유지")}
              for idea, row in zip(merged, result["ideas"])]
    record = {"contract": CONTRACT_VERSION, "input_count": len(sources), "group_count": len(merged),
              "max_ideas": MAX_IDEAS,
              "deferred": [dict(row, source_idea_ids=list(by_id[row['keep_ids'][0]].source_idea_ids or row['keep_ids']))
                           for row in result.get('deferred', [])],
              "deferred_ideas": [by_id[row['keep_ids'][0]].model_dump(mode='json')
                                 for row in result.get('deferred', [])],
              "input_idea_ids": input_ids, "groups": groups, "input_bytes": input_bytes,
              "input_signature": _signature(sources), "output_signature": _signature(merged),
              "context_signature": _context_signature(state),
              "coverage_complete": True, "unaccounted_idea_ids": []}
    # Retain complete leaf sources, including deferred ones, for the frozen report.
    record['source_ideas'] = list({row['source_idea_id']: row for row in _sources(sources)}.values())
    state.solve.raw_ideas = merged
    state.scratch["idea_consolidation"] = record
    state.scratch.setdefault("idea_consolidation_history", []).append(copy.deepcopy(record))
    state.scratch.setdefault("ax_portfolio_trace", []).append({
        "stage": "merge", "contract": CONTRACT_VERSION, "input_count": len(sources),
        "merged_count": len(merged), "unaccounted_preserved": 0, "coverage_complete": True})
    return result
