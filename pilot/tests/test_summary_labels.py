from triz import render
from triz.labels import build_label_map, executive_summary
from triz.presentation import view
from triz.schema import ConceptSpec, Constraint, ReportArtifact


def test_summary_full_descriptions_and_other_sections(state):
    title = '미세 패턴의 손상 방지를 위한 펄스 주기와 유량의 독립 제어 (정밀 세정)'
    constraint = '기존 생산 설비의 운전 온도와 처리 시간을 모두 유지하면서 추가 손상을 방지한다'
    state.concepts = [ConceptSpec(id='CB-123456', title=title, description='CB-123456을 검토한다.')]
    state.constraints.items = [Constraint(id='CON-123456', statement=constraint)]
    state.report = ReportArtifact(narrative={'executive_summary': '해결안1(CB-123456)을 적용하고 제약1(CON-123456)을 확인한다.'})
    original = state.model_dump_json()
    expected = f'{title}을 적용하고 {constraint}을 확인한다.'
    assert executive_summary(state.report.narrative['executive_summary'], state) == expected
    assert executive_summary('해결안9 (원문 (내부 설명) 전체)를 검토한다.', state) == '원문 (내부 설명) 전체를 검토한다.'
    assert executive_summary(build_label_map(state)['CB-123456'], state) == title
    for template in ('report_full.md.j2', 'report_lite.md.j2', 'report_visual.md.j2'):
        markdown = render.render_report(state, state.report.narrative, template=template)
        assert expected in markdown
        if template == 'report_full.md.j2':
            assert build_label_map(state)['CB-123456'] in markdown
    assert view(state)['summary'] == expected
    assert expected in render.render_html(state)
    assert state.model_dump_json() == original
