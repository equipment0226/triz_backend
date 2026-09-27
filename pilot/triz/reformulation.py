"""ARIZ Part 6 model advice, recorded during S5 without changing the problem."""
from . import digest, verify
from .schema import ARIZStep, ProblemReformulationItem, ProblemReformulationReview

STEP_TITLES = {
    "6.1": "복합 문제 분해",
    "6.2": "다른 모순 선택",
    "6.3": "상위 시스템에서 미니문제 재정의",
}


def part6_context(state, run):
    """Use current ARIZ output, before its isolated track has been committed."""
    return {
        "frame": digest.frame_digest(state),
        "target_system": digest.target_system(state),
        "super_system": state.domain.super_system,
        "super_components": [c.name for c in state.analysis.components if c.level == "SUPER"],
        "mini_problem": state.definition.mini_problem,
        "key_problems": [k.model_dump(exclude_defaults=True) for k in state.definition.key_problems],
        "contradictions": digest.contradictions_digest(state),
        "constraints": verify.constraints_full(state),
        "ariz_context": {
            "unresolved_reason": run.unresolved_reason,
            "steps": [s.model_dump(exclude_defaults=True) for s in run.steps],
            "solution_directions": run.solution_directions,
            "final_ideas": run.final_ideas,
        },
    }


def record_ariz(run, payload):
    """Save complete model advice; never synthesize substitute review items."""
    supplied = {item["step_code"]: item for item in payload["items"]}
    items = [ProblemReformulationItem(step_code=code,
             observation=supplied[code]["observation"].strip(),
             suggestion=supplied[code]["suggestion"].strip(), source="MODEL")
             for code in STEP_TITLES]
    run.problem_reformulation_review = ProblemReformulationReview(items=items)
    run.steps.extend(ARIZStep(step_code=item.step_code, step_title=STEP_TITLES[item.step_code],
        output=f"검토 근거: {item.observation}\n문제 재해석 제안: {item.suggestion}", status="DONE",
        table_columns=["검토 근거", "문제 재해석 제안"],
        table_rows=[[item.observation, item.suggestion]]) for item in items)


def for_report(state):
    """Part 6 belongs to the saved ARIZ run, independently of portfolio size."""
    run = state.solve.ariz
    review = run.problem_reformulation_review if run else None
    if review is None or [i.step_code for i in review.items] != list(STEP_TITLES):
        return None
    return review
