"""Product-facing views: human names, evidence gaps, diagrams and actionable next steps."""
from . import visuals
from .labels import build_label_map, humanize
from .render import QUADRANT_KO

def view(state):
    from .pipeline import stage_list
    labels = build_label_map(state)
    def human(value):
        return humanize(str(value or ""), labels)
    solutions = []
    for c in state.concepts:
        e = next((e for e in state.evaluation.evaluations if e.concept_id == c.id), None)
        check = state.check_for(c.id)
        solutions.append(dict(key=c.id, title=c.title, summary=c.one_liner,
            description=human(c.description), mechanism=human(c.working_principle),
            changes=c.changes_to_system, effect=c.expected_effect, assumptions=c.assumptions,
            risks=c.open_risks, validation=c.validation_plan, transfer_conditions=c.transfer_conditions,
            score=e.total_score if e else None, rank=e.rank if e else 0,
            dimensions=e.aggregate if e else {},
            verdict={"PASS": "제약 충족", "CONDITIONAL": "조건 확인 필요", "FAIL": "제약 위반"}.get(check.verdict if check else "", "검토 전"),
            quadrant=QUADRANT_KO.get(e.quadrant, "") if e else "",
            evidence=[dict(title=r.title, url=r.url, kind="특허" if r.source_type == "PATENT" else "논문",
                identifier=r.identifier, scope=r.evidence_scope, verified=r.verified) for r in state.evidences(c.evidence_ids)
                if r.url.startswith(("https://", "http://")) and r.identifier and r.source_type in ("PATENT", "PAPER")]))
    steps = stage_list()
    index = state.control.stage_index
    message = (state.pending.title if state.pending else "보고서가 완성되었어요. 해결안을 검토해 주세요." if state.report
               else "분석이 잠시 멈췄어요. 설정을 확인한 뒤 이어서 진행할 수 있어요." if state.status in ("FAILED", "INTERRUPTED")
               else f"{steps[min(index, len(steps)-1)]['label']}을 진행하고 있어요.")
    return dict(run_id=state.run_id, title=state.scratch.get("title") or state.raw_query[:60],
        query=state.raw_query, industry=state.domain.industry, system=state.domain.target_system,
        status=state.status, stage_index=index, stages=steps, guide=message,
        pending=state.pending.model_dump(mode="json") if state.pending else None,
        profile=state.scratch.get("industry_profile", {}),
        problem=human(state.intake.frame.restated_problem), symptom=state.intake.frame.symptom,
        constraints=[c.statement for c in state.constraints.items],
        reviewers=[dict(role=p.role_name, mandate=p.mandate, avatar=i % 6) for i, p in enumerate(state.evaluation.reviewers)],
        solutions=sorted(solutions, key=lambda c: c["rank"] or 999), figures=visuals.figures(state),
        summary=human(state.report.narrative.get("executive_summary", "")) if state.report else "",
        report_ready=bool(state.report), additions=state.scratch.get("patent_additions", []),
        evidence_gaps=state.scratch.get("evidence_gaps", []), search_status=state.scratch.get("search_status", {}),
        warnings=[human(w) for w in state.control.warnings],
        review_status={"checked": sum(s.status == "OK" for s in state.steps), "unverified": sum(s.status == "WARN" for s in state.steps)})
