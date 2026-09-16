import re
import pytest
from triz.display_terms import display_text,TERMS
from triz import render
from triz.schema import ConceptSpec,ConceptEvaluation,ReportArtifact


@pytest.mark.parametrize('term',sorted(TERMS))
def test_registered_terms_in_report_prose(term):
    assert display_text('분류: '+term)== '분류: '+TERMS[term]


def test_assignments_links_and_real_code_are_distinguished():
    value='change_scale=PARAMETER; `change_scale=PARTIAL`; QUICK_WIN / BIG_BET'
    assert display_text(value)=='변경 범위: 파라미터 조정; 변경 범위: 국부적 변경; QUICK WIN / BIG BET'
    protected='https://example.com/QUICK_WIN?q=change_scale=PARAMETER `GPU_TEMP` ```python\nchange_scale=PARAMETER\n```'
    assert display_text(protected)==protected
    assert display_text(display_text(value))==display_text(value)


def test_reports_keep_raw_enum_and_render_readable_fields(state):
    state.concepts=[ConceptSpec(id='CPT-test',title='DLC',change_scale='PARAMETER',
        description='change_scale=PARAMETER이며 QUICK_WIN 접근과 BIG_BET 접근을 비교한다.')]
    state.evaluation.evaluations=[ConceptEvaluation(concept_id='CPT-test',quadrant='QUICK_WIN')]
    state.report=ReportArtifact(narrative={'executive_summary':'PROTOTYPE_KNOWN 및 change_scale=PARTIAL'})
    original=state.model_dump_json()
    markdown=render.render_report(state,state.report.narrative)
    html=render.render_html(state)
    for text in (markdown,html):
        assert 'QUICK WIN' in text and 'BIG BET' in text
        assert '변경 범위' in text and '파라미터 조정' in text and '국부적 변경' in text
        assert not re.search(r'QUICK_WIN|BIG_BET|change_scale\s*=',text)
    assert state.model_dump_json()==original
