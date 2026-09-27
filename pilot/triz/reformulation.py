"""Report-only ARIZ Part 6 suggestions; never dispatch analysis or change a problem."""
from . import digest, verify
from .schema import ProblemReformulationItem, ProblemReformulationReview, Stage


STEP_TITLES = {
    "6.1": "복합 문제 분해",
    "6.2": "다른 모순 선택",
    "6.3": "상위 시스템에서 미니문제 재정의",
}
SOLUTION_LIMIT = 3


def rank_context(state, solution_count):
    """Only small portfolios add problem context to the existing ranking call."""
    if solution_count > SOLUTION_LIMIT:
        return {}
    ariz = state.solve.ariz
    return {
        "solution_count": solution_count,
        "frame": digest.frame_digest(state),
        "target_system": digest.target_system(state),
        "super_system": state.domain.super_system,
        "super_components": [c.name for c in state.analysis.components if c.level == "SUPER"],
        "mini_problem": state.definition.mini_problem,
        "key_problems": [k.model_dump(exclude_defaults=True) for k in state.definition.key_problems],
        "contradictions": digest.contradictions_digest(state),
        "constraints": verify.constraints_full(state),
        "gaps": state.solve.gaps,
        "ariz_context": {"unresolved_reason": ariz.unresolved_reason,
                         "steps": [s.model_dump(exclude_defaults=True) for s in ariz.steps
                                   if s.step_code in ("1.1", "1.3", "1.4")]} if ariz else {},
        "solutions": [{"id": c.id, "title": c.title, "one_liner": c.one_liner,
                       "addresses": c.addresses_contradictions,
                       "quality_issues": c.quality_issues} for c in state.concepts],
    }


def _recorded_items(state):
    """Questions grounded in saved facts, not a claim that a model reviewed them."""
    problem = (state.definition.mini_problem or state.intake.frame.restated_problem
               or state.intake.frame.symptom or state.raw_query).strip()
    problems = [k.title for k in state.definition.key_problems if k.title]
    contradictions = [c.label for c in state.definition.technical_contradictions if c.label]
    supers = list(dict.fromkeys(filter(None, [state.domain.super_system]
        + [c.name for c in state.analysis.components if c.level == "SUPER"])))
    return [
        ProblemReformulationItem(step_code="6.1",
            observation=("기록된 핵심 문제: " + " / ".join(problems) if problems
                         else "현재 문제: " + (problem or "구체적인 문제 기록이 부족하다.")),
            suggestion="현재 문제에 서로 다른 하위 문제가 묶여 있는지 구분하고, 핵심 문제 하나를 먼저 풀 수 있도록 미니문제를 나누어 보는 것은 어떨까요?"),
        ProblemReformulationItem(step_code="6.2",
            observation=("기록된 모순: " + " / ".join(contradictions) if contradictions
                         else "비교할 기술적 모순의 기록이 부족하다."),
            suggestion=("주기능과 필수 요구조건을 유지하면서 기록된 다른 모순을 출발점으로 선택해 보는 것은 어떨까요?"
                        if len(contradictions) > 1 else
                        "같은 주기능에서 반대 동작 조건의 이익과 손실을 비교해, 다른 출발 모순이 성립하는지 확인해 보는 것은 어떨까요?")),
        ProblemReformulationItem(step_code="6.3",
            observation=("기록된 상위 시스템: " + " / ".join(supers) if supers
                         else "상위 시스템의 범위가 구체적으로 기록되지 않았다."),
            suggestion=(("대상 내부에 한정한 문제를 ‘" + " / ".join(supers)
                         + "에서 필수 요구조건을 유지하며 같은 목표를 달성하려면?’으로 바꾸어 보는 것은 어떨까요?") if supers else
                        "대상과 연결된 상위 시스템의 범위를 먼저 확인하고, 그 수준에서 같은 목표를 달성하는 미니문제로 바꾸어 보는 것은 어떨까요?")),
    ]


def record(state, payload=None, solution_ids=None):
    ids = list(dict.fromkeys(solution_ids if solution_ids is not None else [c.id for c in state.concepts]))
    state.evaluation.problem_reformulation_review = None
    if len(ids) > SOLUTION_LIMIT:
        return
    supplied = payload.get("items") if isinstance(payload, dict) else None
    supplied = supplied if isinstance(supplied, list) else []
    items = []
    for fallback in _recorded_items(state):
        matching = [row for row in supplied if isinstance(row, dict) and row.get("step_code") == fallback.step_code]
        row = matching[0] if len(matching) == 1 else {}
        if all(isinstance(row.get(k), str) and row[k].strip() for k in ("observation", "suggestion")):
            items.append(ProblemReformulationItem(step_code=fallback.step_code,
                observation=row["observation"].strip(), suggestion=row["suggestion"].strip(), source="MODEL"))
        else:
            items.append(fallback)
    state.evaluation.problem_reformulation_review = ProblemReformulationReview(solution_ids=ids, items=items)


def for_report(state):
    """Hide obsolete suggestions if the set of displayed solutions has changed."""
    review = state.evaluation.problem_reformulation_review
    ids = {c.id for c in state.concepts}
    if (review is None or len(ids) > SOLUTION_LIMIT or set(review.solution_ids) != ids
            or [i.step_code for i in review.items] != list(STEP_TITLES)):
        return None
    return review


def record_execution(ctx, solution_ids=None):
    """Log the actual Part 6 gate/review after the final portfolio is known.

    The ranking call already produced any model advice. This trace records
    that result and the conditional decision; it never makes another call.
    """
    state = ctx.state
    ids = list(dict.fromkeys(solution_ids if solution_ids is not None else [c.id for c in state.concepts]))
    review = state.evaluation.problem_reformulation_review
    triggered = len(ids) <= SOLUTION_LIMIT
    step = ctx.start_step(node="s8_ariz_p6", label="ARIZ Part6 문제 변경 조건·제안 검토",
        stage=Stage.S8.value, agent_id="deterministic_review", prompt_id="", tier="")
    step.input_slice = {"solution_ids": ids, "solution_count": len(ids), "threshold": SOLUTION_LIMIT}
    step.output_json = {
        "solution_ids": ids, "solution_count": len(ids), "threshold": SOLUTION_LIMIT,
        "triggered": triggered, "decision": "REPORT_SUGGESTIONS_ONLY" if triggered else "THRESHOLD_NOT_MET",
        "items": [item.model_dump() for item in review.items] if review and set(review.solution_ids) == set(ids) else [],
        "problem_changed": False, "restart_from_s1": False,
        "note": ("6.1~6.3 검토 결과를 보고서 추가 코멘트로 기록했다. 문제 변경과 선행 단계 재실행은 수행하지 않는다."
                 if triggered else "최종 Solution 수가 3개를 초과하므로 문제 변경 제안 조건에 해당하지 않는다."),
    }
    ctx.finish_step(step)
