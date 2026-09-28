"""A numeric hard failure needs an observed quantity, not numbers in prose."""
import pytest

from triz import verify
from triz.schema import ConceptSpec, Constraint, ConstraintCheckResult


def constraint(parameter='결어긋남률 증가분', value='10', unit='%', operator='<='):
    return Constraint(id='CON-bb39bc4c', kind='NUMERIC', parameter=parameter,
        value=value, unit=unit, operator=operator, statement='등록된 수치 한계', hard=True)


@pytest.mark.parametrize('text', [
    # The actual production failure: 39 in a constraint ID became 39%.
    '인가 중 결어긋남률 증가분 목표 ≤10%(CON-bb39bc4c). 현재 정량 기준선 미확인(answers[1]은 정성 표현).',
    '미측정. 결어긋남률 증가분을 비교하여 10% 이내(CON-bb39bc4c) 유지 여부를 판정한다.',
    '결어긋남률 증가분 미측정. 실측 온도 39°C, 농도 20%.',
    '결어긋남률 증가분은 미확인, 실측 농도 39%.',
    '실측 결어긋남률 증가분 관련 ID CPT-S6-39, 반복률 90%, 목표 10%.',
    '실측 결어긋남률 증가분 설명은 CON-bb39bc4c이며 효율은 39%.',
    '결어긋남률 증가분 실측값 39%가 아니라 목표 10%이다.',
    '결어긋남률 증가분 측정 계획: 39%를 검증한다.',
    '결어긋남률 증가분 실측값은 39%로 가정한다.',
    '결어긋남률 증가분 39%라는 측정값은 없다.',
    '결어긋남률 증가분 39%로 측정되지 않았다.',
    '결어긋남률 증가분 실측값 39%일 경우 위반이다.',
    '결어긋남률 증가분 예상 39%.',
    '결어긋남률 증가분은 39%.',  # A proposed value is not measured proof.
    '결어긋남률 증가분 실측값 39%/s.',
    '결어긋남률 증가분 실측값 39%p.',
    '결어긋남률 증가분 실측값 9%. 효율은 39%.',
    '결어긋남률 증가분 실측값 39% 이하.',
    '결어긋남률 증가분 실측값 9~39%.',  # Straddles the limit.
    '결어긋남률 증가분 실측값 39~9%.',
    '결어긋남률 증가분 실측값 39% ± 35%.',
    '결어긋남률 증가분 실측값 39% (오차 ±35%).',
    '결어긋남률 증가분 실측값 39% - 9%.',
    '결어긋남률 증가분 실측값 39%보다 작다.',
    '결어긋남률 증가분 실측값 39% / s.',
    '결어긋남률 증가분 실측값 1×10^-3%.',
])
def test_uncertain_or_unrelated_prose_never_overrides_gate(text):
    assert verify.numeric_violation(text, constraint()) is None


@pytest.mark.parametrize('text, con, value', [
    ('결어긋남률 증가분 실측값은 39%.', constraint(), '39%'),
    ('실측 결과: 결어긋남률 증가분은 12%.', constraint(), '12%'),
    ('결어긋남률 증가분 12%로 측정되었다.', constraint(), '12%'),
    ('결어긋남률 증가분 측정 결과: 12~15%.', constraint(), '12~15%'),
    ('결어긋남률 증가분 실측값 12%~15%.', constraint(), '12~15%'),
    ('온도 실측값 -30°C.', constraint('온도', '-20', '°C', '>='), '-30°C'),
    ('전류 실측값 2e-3A.', constraint('전류', '1e-3', 'A'), '0.002A'),
    ('전류 실측값 1,200mA.', constraint('전류', '1000', 'mA'), '1200mA'),
    ('압력 실측값 2Pa.', constraint('압력', '3', 'Pa', '=='), '2Pa'),
    ('압력 실측값 3Pa.', constraint('압력', '3', 'Pa', '!='), '3Pa'),
    ('pressure was measured 20Pa.', constraint('pressure', '10', 'Pa'), '20Pa'),
])
def test_explicit_measured_violations_are_preserved(text, con, value):
    result = verify.numeric_violation(text, con)
    assert result is not None and value in result


@pytest.mark.parametrize('text, con', [
    ('길이 실측값 20mm.', constraint('길이', '1', 'm')),
    ('길이 실측값 20m/s.', constraint('길이', '1', 'm')),
    ('전력 실측값 20mW.', constraint('전력', '1', 'MW')),
    ('압력 실측값 20Pa s.', constraint('압력', '1', 'Pa')),
    ('입자수 실측값 20개수.', constraint('입자수', '1', '개')),
    ('전류 실측값 2e-3A.', constraint('전류', '0.01', 'A')),
    ('압력 실측값 2~4Pa.', constraint('압력', '3', 'Pa', '==')),
    ('압력 실측값 2~4Pa.', constraint('압력', '3', 'Pa', '!=')),
    ('압력 실측값 2Pa.', constraint('압력', 'NaN', 'Pa')),
    ('압력 실측값 2Pa.', constraint('압력', 'Infinity', 'Pa')),
    ('압력 실측값 2Pa.', constraint('압력', '1~3', 'Pa')),
    ('압력 실측값 2Pa.', constraint('압력', '3', '')),
    ('온도상승 실측값 39°C.', constraint('온도', '10', '°C')),
    ('냉각온도 실측값 39°C.', constraint('온도', '10', '°C')),
])
def test_units_boundaries_ranges_and_invalid_limits_abstain(text, con):
    assert verify.numeric_violation(text, con) is None


def test_measured_value_must_match_constraint_location():
    con = constraint('온도', '10', '°C').model_copy(update={'zone': '챔버 내부'})
    assert verify.numeric_violation('챔버 외부 온도 실측값 39°C.', con) is None
    assert verify.numeric_violation('온도 실측값 39°C.', con) is None
    assert verify.numeric_violation('챔버 내부 온도 실측값 39°C.', con)


def test_gate_preserves_conditional_and_records_only_real_failure(state, monkeypatch):
    from triz import agent, nodes
    from triz.ax import effect_history, feedback_events
    from triz.context import RunContext
    from triz.schema import StepRecord

    state.constraints.items = [constraint()]
    uncertain = ConceptSpec(id='unmeasured', title='계면 차단층',
        description='실측 삽입 손실 3%.',
        expected_effect='결어긋남률 증가분 39%(CON-bb39bc4c).')
    measured = ConceptSpec(id='measured', title='측정된 위반',
        description='결어긋남률 증가분 실측값 39%.')
    state.concepts = [uncertain, measured]
    state.scratch['ax_autonomous_gate'] = True
    recorded = []

    def respond(ctx, **kwargs):
        state.steps.append(StepRecord(node=kwargs['node'], status='OK'))
        return {'results': [{'concept_id': item['concept_id'], 'verdict': 'CONDITIONAL',
            'numeric_validation': {'contract': 'model-claimed-fake', 'overrides': ['untrusted']},
            'per_constraint': [{'constraint_id': 'CON-bb39bc4c', 'verdict': 'UNKNOWN',
                                'reason': 'AI 정량 근거 미확인'}]}
            for item in kwargs['vars']['concepts_for_gate']]}

    monkeypatch.setattr(agent, 'run_agent', respond)
    monkeypatch.setattr(feedback_events, 'model_review', lambda st, concept, review, **kw: recorded.append(review))
    monkeypatch.setattr(effect_history, 'gate_reviews', lambda *args: None)
    nodes.s7_gate(RunContext(state))

    assert [c.id for c in state.concepts] == ['unmeasured']
    assert state.constraint_checks[0].verdict == 'CONDITIONAL'
    reviews = {row['concept_id']: row for row in recorded}
    assert reviews['unmeasured']['verdict'] == 'CONDITIONAL'
    failure = reviews['measured']
    assert failure['verdict'] == 'FAIL' and not failure['requires_user_decision']
    assert len(failure['per_constraint']) == 1
    assert failure['per_constraint'][0]['verdict'] == 'FAIL'
    numeric = failure['numeric_validation']
    assert numeric['contract'] == 'parameter-bound-observed-values-v1'
    assert numeric['overrides'][0]['source_text'] == '결어긋남률 증가분 실측값 39%.\n'
    assert numeric['overrides'][0]['constraint']['id'] == 'CON-bb39bc4c'
    again, _ = verify.normalize_constraint_result(ConstraintCheckResult.model_validate(failure), state.constraints)
    assert again.verdict == 'FAIL'  # No UNKNOWN/FAIL duplicate reverses the result later.
    diagnostic = next(d for d in state.scratch['constraint_normalization'] if d['concept_id'] == 'measured')
    assert diagnostic['numeric_overrides'][0]['previous_rows'][0]['verdict'] == 'UNKNOWN'
    assert diagnostic['normalized_verdict'] == 'FAIL' and diagnostic['hard_unknown_ids'] == []
