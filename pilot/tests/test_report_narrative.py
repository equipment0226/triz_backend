from copy import deepcopy

from triz.schema import ReportArtifact


def test_report_narrative_preserves_structured_values_and_round_trips():
    original = {
        'executive_summary': '4,000시간 수명 목표를 검증한다.',
        'next_steps': ['재료 조성 확인', '수명 시험 수행'],
        'limitation_note': {'미확인': ['시험 온도', 'PFAS 함량'], '검증 필요': True},
        'optional_note': None,
    }
    before = deepcopy(original)
    report = ReportArtifact(narrative=original)
    assert original == before
    assert report.narrative['executive_summary'] == original['executive_summary']
    assert all(isinstance(value, str) for value in report.narrative.values())
    assert all(item in report.narrative['next_steps'] for item in original['next_steps'])
    assert '시험 온도' in report.narrative['limitation_note'] and 'PFAS 함량' in report.narrative['limitation_note']
    assert report.narrative['optional_note'] == ''
    assert ReportArtifact.model_validate_json(report.model_dump_json()) == report
