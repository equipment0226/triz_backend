"""Gate verdicts follow saved constraint scope, not an inconsistent model summary."""
import pytest

from triz import verify
from triz.schema import ConceptSpec, Constraint, ConstraintCheckResult, ConstraintSet, GlobalState


def constraint(key, *, hard=True, source='USER', confidence=1.0, **kwargs):
    return Constraint(id=key, statement=key, hard=hard, source=source, confidence=confidence, **kwargs)


def check(items, rows, *, verdict='PASS', violated_ids=()):
    original = ConstraintCheckResult(concept_id='candidate', verdict=verdict,
        violated_ids=list(violated_ids), per_constraint=rows)
    constraints = ConstraintSet(items=items)
    before = (original.model_dump_json(), constraints.model_dump_json())
    result, diagnostic = verify.normalize_constraint_result(original, constraints)
    assert (original.model_dump_json(), constraints.model_dump_json()) == before
    return result, diagnostic


def row(key, verdict, reason='본문의 적용 조건을 확인했다.'):
    return {'constraint_id': key, 'verdict': verdict, 'reason': reason}


@pytest.mark.parametrize('summary_verdict', ['PASS', 'FAIL'])
def test_confirmed_soft_failure_excludes_under_selected_user_policy(summary_verdict):
    items = [constraint('load'), constraint('serial', hard=False, source='DOMAIN', confidence=.6)]
    result, diagnostic = check(items, [row('load', 'PASS'), row('serial', 'FAIL', '직렬 공정을 중첩한다.')],
        verdict=summary_verdict, violated_ids=['serial'])
    assert result.verdict == 'FAIL' and result.violated_ids == ['serial']
    assert result.per_constraint[1] == row('serial', 'FAIL', '직렬 공정을 중첩한다.')
    assert not result.requires_user_decision
    assert diagnostic['original_verdict'] == summary_verdict
    assert diagnostic['normalized_verdict'] == 'FAIL'
    assert diagnostic['soft_failure_ids'] == ['serial']
    assert any('SOFT_FAILURE_ENFORCED' in issue for issue in diagnostic['issues'])


def test_real_hard_violation_overrides_model_pass_and_soft_preferences():
    result, diagnostic = check([constraint('oil'), constraint('cost', hard=False)],
        [row('oil', 'FAIL', '챔버 내부에 그리스를 사용한다.'), row('cost', 'FAIL')])
    assert result.verdict == 'FAIL' and result.violated_ids == ['oil', 'cost']
    assert diagnostic['hard_failure_ids'] == ['oil']
    assert diagnostic['soft_failure_ids'] == ['cost']


@pytest.mark.parametrize('rows', [[], [row('load', 'UNKNOWN')], [row('load', 'UNPROVEN')],
    [row('load', 'PASS'), row('load', 'FAIL')]])
def test_hard_missing_unknown_invalid_or_conflicting_rows_require_confirmation(rows):
    result, diagnostic = check([constraint('load')], rows)
    assert result.verdict == 'CONDITIONAL'
    assert result.violated_ids == [] and result.requires_user_decision
    assert result.per_constraint[0]['verdict'] == 'UNKNOWN'
    assert diagnostic['hard_unknown_ids'] == ['load']


@pytest.mark.parametrize('bad_id', ['invented', ' load', None, ['load']])
def test_unknown_ids_do_not_become_violations_or_a_false_pass(bad_id):
    result, diagnostic = check([constraint('load')], [row('load', 'PASS'), row(bad_id, 'FAIL')], verdict='FAIL')
    assert result.verdict == 'CONDITIONAL' and not result.violated_ids
    assert [item['constraint_id'] for item in result.per_constraint] == ['load']
    assert diagnostic['unknown_ids']


def test_identical_duplicate_rows_are_collapsed_and_logged():
    result, diagnostic = check([constraint('load')], [row('load', 'PASS'), row('load', 'PASS')])
    assert result.verdict == 'PASS' and len(result.per_constraint) == 1
    assert diagnostic['duplicate_ids'] == ['load']


def test_conflicting_duplicate_hard_fail_cannot_be_used_to_reject():
    result, diagnostic = check([constraint('load')], [row('load', 'FAIL'), row('load', 'PASS')],
        verdict='FAIL', violated_ids=['load'])
    assert result.verdict == 'CONDITIONAL' and not result.violated_ids
    assert diagnostic['duplicate_ids'] == ['load']


def test_summary_only_hard_allegation_requires_confirmation():
    result, diagnostic = check([constraint('load')], [row('load', 'PASS')],
        verdict='FAIL', violated_ids=['load'])
    assert result.verdict == 'CONDITIONAL' and not result.violated_ids
    assert any('SUMMARY_ROW_CONTRADICTION' in issue for issue in diagnostic['issues'])


def test_unknown_summary_id_requires_confirmation_even_if_rows_pass():
    result, diagnostic = check([constraint('load')], [row('load', 'PASS')], violated_ids=['invented'])
    assert result.verdict == 'CONDITIONAL'
    assert diagnostic['unknown_ids'] == ['invented']


def test_other_valid_hard_failure_still_rejects_when_another_row_is_uncertain():
    result, _ = check([constraint('load'), constraint('oil')], [row('oil', 'FAIL')])
    assert result.verdict == 'FAIL' and result.violated_ids == ['oil']


@pytest.mark.parametrize('items, rows', [([], []),
    ([constraint('preferred', hard=False)], [row('preferred', 'PASS')])])
def test_no_hard_constraint_can_pass_without_inventing_an_obligation(items, rows):
    result, _ = check(items, rows)
    assert result.verdict == 'PASS'


@pytest.mark.parametrize('rows', [[], [row('preferred', 'UNKNOWN')]])
def test_soft_missing_or_unknown_still_needs_confirmation(rows):
    result, diagnostic = check([constraint('preferred', hard=False)], rows)
    assert result.verdict == 'CONDITIONAL' and result.requires_user_decision
    assert diagnostic['unresolved_constraint_ids'] == ['preferred']


def test_source_confidence_never_overrides_hard_boolean():
    result, _ = check([constraint('hard_inferred', source='INFERRED', confidence=.1),
        constraint('soft_user', hard=False)], [row('hard_inferred', 'FAIL'), row('soft_user', 'FAIL')])
    assert result.violated_ids == ['hard_inferred', 'soft_user']


def test_duplicate_constraint_definitions_are_ambiguous():
    result, diagnostic = check([constraint('same'), constraint('same', hard=False)], [row('same', 'FAIL')])
    assert result.verdict == 'CONDITIONAL' and result.violated_ids == []
    assert diagnostic['duplicate_definition_ids'] == ['same']


@pytest.mark.parametrize('blank_id', ['', ' '])
def test_blank_constraint_definition_cannot_establish_a_hard_failure(blank_id):
    result, _ = check([constraint(blank_id)], [row(blank_id, 'FAIL')], verdict='FAIL')
    assert result.verdict == 'CONDITIONAL' and result.violated_ids == []


def test_constraints_full_preserves_provenance_and_soft_must_have_flag():
    state = GlobalState(run_id='offline-constraints')
    state.constraints.items = [constraint('serial', hard=False, source='DOMAIN', confidence=.6)]
    packet = verify.constraints_full(state)[0]
    assert packet['source'] == 'DOMAIN' and packet['confidence'] == .6
    assert packet['kind'] == 'MUST_HAVE' and packet['hard'] is False


def test_one_well_formed_concept_is_not_rejected_for_missing_count_quota():
    concept = {'title': '서보 설정 변경', 'expected_effect': '정착 시간 감소',
        'assumptions': ['제어기 지원 확인', '부하율 한계 확인'], 'required_resources': ['서보']}
    assert verify.check_concepts({'concepts': [concept]}, {'서보'}) == []
    malformed = dict(concept, expected_effect='', required_resources=['임의 장치'])
    issues = verify.check_concepts({'concepts': [malformed]}, {'서보'})
    assert any('DET-10b' in issue for issue in issues)
    assert any('DET-10:' in issue for issue in issues)


@pytest.mark.parametrize('soft_rows, expected', [([row('soft', 'PASS')], 'READY'),
    ([row('soft', 'FAIL')], 'REJECTED'), ([row('soft', 'UNKNOWN')], 'CONDITIONAL'), ([], 'CONDITIONAL')])
def test_saved_pass_rechecks_all_soft_findings_without_mutating_record(monkeypatch, soft_rows, expected):
    from triz.ax import ledger, validation
    state = GlobalState(run_id='saved-gate-selection', user_id='local')
    state.constraints.items = [constraint('hard'), constraint('soft', hard=False)]
    state.concepts = [ConceptSpec(id='candidate', title='후보', quality_status='PASS',
        resolution_argument='모순 양측을 보존한다.', addresses_contradictions=['TC-1'],
        working_principle='서보 제동으로 진동을 감쇠한다.', validation_plan=[{'metric': '정착 시간'}])]
    state.constraint_checks = [ConstraintCheckResult(concept_id='candidate', verdict='PASS',
        per_constraint=[row('hard', 'PASS'), *soft_rows])]
    state.scratch['ax_members'] = {'concepts': 'version-1'}
    monkeypatch.setattr(ledger, 'active_reviews', lambda *args: [{'payload': {
        'target_version_id': 'version-1', 'decision_type': 'RECORD_TEST_RESULT',
        'obligation_id': 'candidate:test:0', 'candidate_id': 'candidate',
        'result': 'PASS', 'event_id': 'recorded-test'}}])
    before = state.model_dump_json()
    result = validation.selection(state)
    assert state.model_dump_json() == before
    assert result['candidates'][0]['status'] == expected
    assert result['recommended'] == (['candidate'] if expected == 'READY' else [])
    assert result['candidates'][0]['constraint_verdict'] == {
        'READY': 'PASS', 'REJECTED': 'FAIL', 'CONDITIONAL': 'CONDITIONAL'}[expected]


def test_saved_rejection_is_not_reversed_by_missing_individual_details(monkeypatch):
    from triz.ax import ledger, validation
    state = GlobalState(run_id='saved-rejected-candidate', user_id='local')
    state.constraints.items = [constraint('soft', hard=False)]
    state.concepts = [ConceptSpec(id='candidate', title='기존 제외 후보')]
    state.constraint_checks = [ConstraintCheckResult(concept_id='candidate', verdict='FAIL')]
    monkeypatch.setattr(ledger, 'active_reviews', lambda *args: [])
    before = state.model_dump_json()
    result = validation.selection(state)
    assert result['candidates'][0]['status'] == 'REJECTED'
    assert state.model_dump_json() == before
