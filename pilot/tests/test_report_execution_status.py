"""Execution evidence remains distinct from applicability, quality and old runs."""
import copy
import re

import pytest

from triz import ariz_report, render
from triz.ax import report
from triz.schema import ARIZRun, ARIZStep, RawIdea, StepRecord


def snapshot(monkeypatch, state):
    """Pin the report inputs without a DB, coordinator or model dependency."""
    artifacts = copy.deepcopy({
        'input': {'raw_query': state.raw_query, 'domain': state.domain.model_dump(mode='json'),
                  'intake': state.intake.model_dump(mode='json')},
        'problem': {}, 'analysis': state.analysis.model_dump(mode='json'),
        'definition': state.definition.model_dump(mode='json'),
        'solve': state.solve.model_dump(mode='json'), 'constraints': {},
        'evaluation': state.evaluation.model_dump(mode='json'), 'selection': {},
        'report_context': report.context(state),
    })
    monkeypatch.setattr(report, 'manifest', lambda _: ('test-snapshot', artifacts))
    return artifacts


@pytest.mark.parametrize('status', [
    'COMPLETED', 'REVIEWED_NO_APPLICATION', 'NOT_APPLICABLE', 'PENDING', 'FAILED',
])
def test_empty_output_preserves_execution_status_and_reason(status):
    record = {'status': status, 'reason': '기록된 실제 판단 근거', 'output_count': 0}
    actual = report.execution_view({}, {}, {'ax_track_execution': {'H_EFFECTS': record}})
    row = actual['H_EFFECTS']
    assert row['status'] == status
    assert row['reason'] == record['reason']
    assert row['stored_count'] == row['output_count'] == 0
    assert '기록된 실제 판단 근거' in row['empty_message']
    assert ('저장되지 않았다' in row['empty_message']) == (status == 'COMPLETED')


def test_legacy_output_and_enabled_track_do_not_imply_current_execution():
    actual = report.execution_view({'effect_apps': [{'idea': '저장된 적용안'}]},
                                   {'enabled_tracks': ['F_TRENDS']}, {})
    assert actual['H_EFFECTS']['stored_count'] == 1
    assert actual['H_EFFECTS']['status'] == actual['F_TRENDS']['status'] == 'UNRECORDED'
    assert '누적 호출 이력만으로' in actual['H_EFFECTS']['reason']
    assert report.execution_view({}, {}, {}) == {}


def test_trimming_counts_only_its_own_ideas():
    actual = report.execution_view({'raw_ideas': [{'track': 'A_MATRIX'}, {'track': 'E_TRIMMING'}]},
                                   {'enabled_tracks': ['E_TRIMMING']}, {})
    assert actual['E_TRIMMING']['stored_count'] == 1


@pytest.mark.parametrize('boundary', [None, -1, True, '3'])
def test_trace_never_guesses_a_missing_or_invalid_rerun_boundary(boundary):
    steps = [{'seq': 1}, {'seq': 3}, {'seq': 4}]
    result = report.trace_view(steps, {'ax_solve_start_seq': boundary})
    assert result['bounded'] is False
    assert result['groups'] == [{'title': '누적 실행 이력', 'steps': steps}]


def test_trace_boundary_is_inclusive_for_earlier_steps():
    steps = [{'seq': 1}, {'seq': 3}, {'seq': 4}]
    result = report.trace_view(steps, {'ax_solve_start_seq': 3})
    assert [group['steps'] for group in result['groups']] == [steps[:2], steps[2:]]
    assert report.trace_view(steps, {'ax_solve_start_seq': 0})['groups'][0]['steps'] == steps


def test_trace_rows_do_not_duplicate_prompt_and_model_payloads():
    source = [{'seq': 1, 'label': '모델 호출', 'input_slice': {'user': '대형 입력'},
               'output_json': {'applications': ['대형 출력']},
               'verdicts': [{'verdict': 'UNVERIFIED', 'reason': '장문의 검사 기록'}]}]
    result = report.trace_view(source, {})['groups'][0]['steps']
    assert result == [{'seq': 1, 'label': '모델 호출', 'verdicts': [{'verdict': 'UNVERIFIED'}]}]
    assert 'input_slice' in source[0] and 'output_json' in source[0]


def test_all_expected_empty_sections_and_rerun_groups_render_from_pinned_state(state, monkeypatch):
    statuses = {'A_MATRIX': 'REVIEWED_NO_APPLICATION', 'B_SEPARATION': 'NOT_APPLICABLE',
                'C_STANDARDS': 'NOT_APPLICABLE', 'D_ARIZ': 'FAILED', 'E_TRIMMING': 'NOT_APPLICABLE',
                'F_TRENDS': 'REVIEWED_NO_APPLICATION', 'G_FOS': 'PENDING', 'H_EFFECTS': 'FAILED'}
    state.scratch['ax_track_execution'] = {
        key: {'status': value, 'reason': f'실제 판단 근거 {index}번', 'output_count': 0}
        for index, (key, value) in enumerate(statuses.items(), start=1)
    }
    state.scratch['ax_solve_start_seq'] = 1
    state.steps = [StepRecord(seq=1, stage='s5_solve', label='과거 효과 호출', status='OK'),
                   StepRecord(seq=2, stage='s5_solve', label='현재 호출', status='WARN',
                              verdicts=[{'verdict': 'UNVERIFIED', 'source': 'policy'}])]
    artifacts = snapshot(monkeypatch, state)
    before = copy.deepcopy(artifacts)
    markdown = report.markdown(state)
    for number in range(1, 8):
        assert re.search(rf'^### 4\.{number} ', markdown, re.M)
    for index in range(1, 9):
        assert f'실제 판단 근거 {index}번' in markdown
    assert '독립 검증이나 현장 실증을 뜻하지 않는다' in markdown
    assert '### 이전 이력·이어받은 상위 단계' in markdown
    assert '### 현재 해결 탐색 회차' in markdown
    previous, current = markdown.split('### 현재 해결 탐색 회차', 1)
    assert '과거 효과 호출' in previous and '과거 효과 호출' not in current
    assert '현재 호출' in current and '미검증' in current
    assert '완료·검증 주의' in current
    state.scratch['ax_track_execution']['H_EFFECTS']['reason'] = 'LIVE MUTATION'
    state.scratch['ax_solve_start_seq'] = 0
    state.steps.clear()
    assert report.markdown(state) == markdown
    assert artifacts == before


def test_legacy_trace_warns_and_fos_keeps_application_and_conditions(state, monkeypatch):
    state.solve.fos_apps = [dict(leading_area='선도 분야', transferred_feature='전이 특성',
        generalized_function='일반화 기능', why_leading='참조 선정 근거', adaptation_note='이식 조정',
        title='구체적 적용안 제목', idea='저장된 구체적 기구', conditions=['온도 조건', '재료 조건'])]
    state.steps = [StepRecord(seq=1, label='이전 모델 호출', status='OK')]
    snapshot(monkeypatch, state)
    markdown = report.markdown(state)
    for value in ['참조 선정 근거', '구체적 적용안 제목', '저장된 구체적 기구', '온도 조건 / 재료 조건']:
        assert value in markdown
    assert '회차 경계가 없어 현재 탐색의 실행 범위를 확정할 수 없다' in markdown
    assert '현재 실행 상태 기록 없음' in markdown
    assert '### 현재 해결 탐색 회차' not in markdown
    # Legacy FOS conditions were also stored as a string; preserve it intact.
    state.solve.fos_apps[0]['conditions'] = '문자열로 저장된 이식 조건'
    assert '문자열로 저장된 이식 조건' in render.render_report(state, {}, template='report_full.md.j2')


def test_ariz_verdict_fallback_excludes_the_previous_solve(state):
    state.solve.ariz = ARIZRun(steps=[ARIZStep(step_code='7.1', output='현재 해결안 검토')])
    state.steps = [StepRecord(seq=1, node='s5_ariz_p7', status='OK',
                              output_json={'verdicts': [{'idea_title': '과거 해결안'}]})]
    state.scratch['ax_solve_start_seq'] = 1
    assert ariz_report.build(state)['verdicts'] == []
    state.steps.append(StepRecord(seq=2, node='s5_ariz_p7', status='OK',
                       output_json={'verdicts': [{'idea_title': '현재 해결안'}]}))
    assert ariz_report.build(state)['verdicts'] == [{'idea_title': '현재 해결안'}]
    state.solve.ariz.verdicts = [{'idea_title': '명시적으로 저장된 해결안'}]
    assert ariz_report.build(state)['verdicts'] == state.solve.ariz.verdicts


def test_part6_is_inside_ariz_between_parts5_and7_without_a_second_late_section(state, monkeypatch):
    state.solve.ariz = ARIZRun(steps=[
        ARIZStep(step_code='5.4', step_title='지식베이스 활용', output='선행 기구 검토'),
        ARIZStep(step_code='6.1', step_title='문제 재해석', output='하위 공정 경계를 다시 볼 수 있다는 의견'),
        ARIZStep(step_code='6.2', step_title='모델 재검토', output='자원 범위를 넓혀 볼 수 있다는 의견'),
        ARIZStep(step_code='6.3', step_title='전제 재검토', output='작업 순서의 전제를 검토하자는 의견'),
        ARIZStep(step_code='7.1', step_title='해결안 검증', output='도출 기구 검토'),
    ])
    snapshot(monkeypatch, state)
    markdown = report.markdown(state)
    assert markdown.index('Part 5') < markdown.index('Part 6') < markdown.index('Part 7')
    assert markdown.count('Part 6 · 문제 재해석 제안') == 1
    assert markdown.index('하위 공정 경계를 다시 볼 수 있다는 의견') < markdown.index('## 5. 제약조건 검토')
    assert '3개 이하' not in markdown


def test_full_candidate_review_reports_completion_without_count_selection(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id=f'IDEA-{i}', title=f'Distinct mechanism {i}') for i in range(15)]
    state.scratch['ax_candidate_review'] = {
        'available_ideas': 15, 'assigned_ideas': 15, 'review_limit': None,
        'completed_ideas': 10, 'unreviewed_idea_ids': [f'IDEA-{i}' for i in range(10, 15)],
        'contract': 'idea-retention-v2',
    }
    snapshot(monkeypatch, state)
    markdown = report.markdown(state)
    section = markdown.split('### 4.8 원리에서 해결 아이디어로', 1)[1].split('## 5.', 1)[0]
    assert '중복 통합 후 아이디어 **15개** · 상세 검토 완료 **10개** · 미완료 **5개**' in section
    assert '모든 아이디어를 검토 대상으로' in section
    assert '필수·선호 제약을 확인한다' in section
    assert all(idea.title in section for idea in state.solve.raw_ideas)


def test_candidate_review_counts_and_unassigned_sources_are_pinned_without_rejection(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id=f'IDEA-{index}', track='A_MATRIX',
                                    title=f'보존할 원천 아이디어 {index}', idea=f'구체적 기구 {index}')
                             for index in range(1, 4)]
    state.scratch['ax_candidate_review'] = {
        'available_ideas': 3, 'assigned_ideas': 1, 'review_limit': 1,
        'unassigned_idea_ids': ['IDEA-2', 'IDEA-3'], 'contract': 'idea-retention-v1',
    }
    snapshot(monkeypatch, state)
    markdown = report.markdown(state)
    section = markdown.split('### 4.8 원리에서 해결 아이디어로', 1)[1].split('## 5.', 1)[0]
    assert '도출 아이디어 **3개** · 상세 검토 **1개** · 미검토 **2개**' in section
    assert '미검토는 부적합 판정이 아니며' in section
    assert '채택 전 상세 검토와 제약 확인이 필요하다' in section
    for idea in state.solve.raw_ideas:
        assert idea.title in section
    state.scratch['ax_candidate_review']['assigned_ideas'] = 3
    state.scratch['ax_candidate_review']['unassigned_idea_ids'].clear()
    state.solve.raw_ideas.clear()
    assert report.markdown(state) == markdown
