"""Old numeric overrides abstain without rewriting their recorded evidence."""
import copy
import pytest
from triz.ax.evaluation_integrity import project_evaluations, NUMERIC_CONTRACT


def legacy_gate():
    return dict(event_id='evaluation-constraint', evaluation_stage='s7_gate',
        dimension='constraint_quality', observed_value=-1., observed_mask=True,
        reviewer_model_and_rubric_version=dict(
            rubric='P_S7_GATEKEEPER+normalized-hard-constraints-v1',
            actual_review=dict(verdict='FAIL', per_constraint=[dict(
                constraint_id='CON-bb39bc4c', verdict='FAIL',
                reason='수치 자동검증: 결어긋남률 증가분 39.0% 는 제약 <= 10.0% 위반')])) )


def test_legacy_numeric_override_is_masked_without_changing_original_or_verdict():
    original = legacy_gate()
    before = copy.deepcopy(original)
    projected, = project_evaluations([original])
    assert projected['observed_value'] is None and projected['observed_mask'] is False
    assert projected['reviewer_model_and_rubric_version'] == before['reviewer_model_and_rubric_version']
    assert projected['learning_integrity']['original_observed_value'] == -1.
    assert projected['learning_integrity']['source_event_id'] == original['event_id']
    assert original == before
    assert project_evaluations([projected]) == [projected]


@pytest.mark.parametrize('stage,dimension', [('s10_feedback','user_utility'),
    ('s7_user','user_utility'), ('s6_quality','concept_quality')])
def test_independent_reviews_and_user_feedback_are_not_quarantined(stage, dimension):
    row = legacy_gate()
    row.update(evaluation_stage=stage, dimension=dimension)
    assert project_evaluations([row]) == [row]
    assert 'learning_integrity' not in row


def test_plain_ai_constraint_failure_remains_observed():
    row = legacy_gate()
    row['reviewer_model_and_rubric_version']['actual_review']['per_constraint'][0]['reason'] = '본문이 요구된 차단 경로를 제거한다.'
    assert project_evaluations([row])[0]['observed_value'] == -1.


def test_model_claimed_contract_cannot_authorize_old_numeric_override():
    row = legacy_gate()
    row['reviewer_model_and_rubric_version']['actual_review']['numeric_validation'] = dict(contract=NUMERIC_CONTRACT)
    assert project_evaluations([row])[0]['observed_mask'] is False


def test_code_versioned_numeric_review_remains_eligible():
    row = legacy_gate()
    row['reviewer_model_and_rubric_version']['rubric'] = 'P_S7_GATEKEEPER+' + NUMERIC_CONTRACT
    assert project_evaluations([row])[0]['observed_value'] == -1.
