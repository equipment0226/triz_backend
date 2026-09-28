"""Read-only eligibility projection for unverifiable numeric gate overrides.

Historical gate events are immutable. Their old broad numeric matcher could read
an identifier as a measurement. Preserve the observation and expose the reason
for abstaining, rather than training on that negative or inventing a replacement
technical verdict. Independent reviews and explicit user utility remain usable.
"""
from .contracts import LEARNING_INTEGRITY

NUMERIC_CONTRACT = 'parameter-bound-observed-values-v1'


def project_evaluations(rows):
    result = []
    for row in rows:
        detail = row.get('reviewer_model_and_rubric_version') or {}
        review = detail.get('actual_review') or {}
        constraints = review.get('per_constraint') or []
        numeric_override = any(isinstance(item, dict) and
            str(item.get('reason', '')).lstrip().startswith('수치 자동검증:')
            for item in constraints)
        # The rubric is supplied by the S7 code, not by the model response.
        trusted_rubric = detail.get('rubric') == 'P_S7_GATEKEEPER+' + NUMERIC_CONTRACT
        if (row.get('evaluation_stage') == 's7_gate'
                and row.get('dimension') == 'constraint_quality'
                and numeric_override and not trusted_rubric):
            projected = dict(row, observed_value=None, observed_mask=False)
            projected['learning_integrity'] = row.get('learning_integrity') or dict(
                contract=LEARNING_INTEGRITY,
                status='QUARANTINED',
                reason='UNVERIFIABLE_LEGACY_NUMERIC_OVERRIDE',
                original_observed_value=row.get('observed_value'),
                original_observed_mask=row.get('observed_mask'),
                source_event_id=row.get('event_id'))
            result.append(projected)
        else:
            result.append(row)
    return result
