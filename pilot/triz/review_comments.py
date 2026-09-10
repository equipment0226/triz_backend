"""One role comment per solution, including reviews saved before meeting summaries."""
import re


def _sentence(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip(" -•\t")
    text = re.sub(r"^(?:FEASIBILITY|COST|TIME|RISK|GOAL|RESOLUTION|CAUSAL|QUALITY|ADOPTION|SAFETY|SCALABILITY|시간|비용|코스트)\s*[:：]\s*", "", text)
    return re.split(r"(?<=[.!?。])\s+", text, maxsplit=1)[0]


def by_concept(state):
    """Read-only presentation; numeric scores and actual exchanges remain intact."""
    result = {}
    finals = {r.reviewer_role: r for r in state.evaluation.meeting.final_reviews}
    for evaluation in state.evaluation.evaluations:
        groups = {}
        for score in evaluation.scores:
            groups.setdefault(score.reviewer_role, []).append(score)
        comments = []
        for role, scores in groups.items():
            final = finals.get(role)
            summaries = [s for s in final.communication_summary if s.concept_id == evaluation.concept_id] if final else []
            critical = sorted(scores, key=lambda s: (not (s.dimension == "SAFETY" and s.score <= 1.5),
                                                       not bool(s.red_flags), s.score, s.confidence))[0]
            authored = getattr(final, "concept_comments", {}).get(evaluation.concept_id, "") if final else ""
            # A saved optimistic comment must never override a retained safety veto.
            veto = critical.dimension == "SAFETY" and critical.score <= 1.5 and critical.red_flags
            if authored and not veto:
                comment = re.sub(r"\s+", " ", authored).strip()
            else:
                main = _sentence(critical.rationale)
                condition = next((flag for s in [critical, *scores] for flag in s.red_flags if flag.strip()), "")
                if not condition:
                    condition = next((issue for s in summaries for issue in s.unresolved_issues if issue.strip()), "")
                if not condition and summaries:
                    condition = summaries[0].assessment_change
                if not condition:
                    condition = critical.improvement_suggestion
                detail = _sentence(condition)
                comment = main
                if detail and detail.rstrip(".!?。") not in main:
                    comment = f"{main.rstrip('.。')} — {detail}" if main else detail
            if comment:
                comments.append({"role": role, "comment": comment})
        result[evaluation.concept_id] = comments
    return result
