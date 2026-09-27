"""Detailed ARIZ source records stay intact but are closed in report exports."""
import re

import pytest

from triz import presentation, render
from triz.schema import ARIZRun, ARIZStep, ReportArtifact
from test_ax_full_report import freeze


@pytest.mark.parametrize('ax', [False, True])
def test_structured_analysis_details_are_separate_closed_blocks_in_every_report(state, ax):
    state.solve.ariz = ARIZRun(steps=[ARIZStep(step_code=f'1.{i}', step_title=f'분석 단계 {i}',
        output=f'## 내부 상세 제목 {i}\n\n숨겨둘 전체 분석 근거 {i}\n\n<script>unsafe()</script>',
        table_columns=['항목', '내용'], table_rows=[['근거', f'표에 남는 요약 {i}']]) for i in [1, 2]])
    state.report = ReportArtifact()
    if ax:
        freeze(state)
    before = state.model_dump(mode='json')
    sections = presentation.view(state)['report_sections']
    blocks = [block for section in sections for block in section['blocks']]
    details = [block for block in blocks if block['type'] == 'details']
    assert len(details) == 2
    visible = ''.join(block.get('html', '') for block in blocks if block['type'] == 'html')
    for index, detail in enumerate(details, start=1):
        assert detail['title'] == '상세 분석 기록'
        assert f'숨겨둘 전체 분석 근거 {index}' in detail['html']
        assert f'숨겨둘 전체 분석 근거 {index}' not in visible
        assert f'표에 남는 요약 {index}' in visible
        assert '<script>' not in detail['html']
    assert not any(section['title'].startswith('내부 상세 제목') for section in sections)
    html = render.render_html(state)
    assert len(re.findall(r'<details class="report-details">', html)) == 2
    assert not re.search(r'<details[^>]*\bopen\b', html)
    markdown = render.render_report(state, {}, template='report_full.md.j2')
    assert markdown.count('<details><summary>상세 분석 기록 · 펼치기/접기</summary>') == 2
    for index in [1, 2]:
        assert f'숨겨둘 전체 분석 근거 {index}' in html
        assert f'숨겨둘 전체 분석 근거 {index}' in markdown
    assert state.model_dump(mode='json') == before
