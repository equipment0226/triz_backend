"""Real source titles survive Korean UI vocabulary, HTML, Markdown and snapshots."""
from html import unescape

import pytest

from triz import presentation, render
from triz.ax import ledger
from triz.labels import display_value
from triz.report_style import plain_value, report_state
from triz.schema import ConceptSpec, EvidenceCard, ReportArtifact, RunMode
from test_ax_full_report import freeze


TITLES = [
    'Motion Profile Design to Reduce Residual Vibration of High-Speed Positioning Stages',
    'Positioning Command Design Method to Minimize Residual Vibration and Positioning Time',
    'Analytical time constant design for jerk-limited acceleration profiles to minimize residual vibration after positioning operation in NC machine tools',
    'Conditional Field Control | Time and Space in CPT-abcdef12 Devices',
]


@pytest.fixture
def references_state(state):
    state.evidence = [EvidenceCard(id=f'EV-reference-{i}', title=title,
        identifier=f'10.1000/reference-{i}', source_type='PATENT' if i == 3 else 'PAPER',
        url=f'https://example.org/source/{i}', verified=True, claim='change_scale=PARAMETER 조건을 확인합니다.')
        for i, title in enumerate(TITLES)]
    state.concepts = [ConceptSpec(id='CPT-abcdef12', title='잔류진동 감소 해결안',
        description='change_scale=PARAMETER 조건을 확인합니다.', evidence_ids=[e.id for e in state.evidence])]
    state.report = ReportArtifact(narrative={})
    state.scratch['related_references'] = [{'concept_id':'CPT-abcdef12', 'reason':'추가 검토가 필요합니다.',
        'reference':{'source_type':'PAPER', 'title':'Time Domain Study of High-Speed Motion',
                     'identifier':'10.1000/related', 'url':'https://example.org/related'}}]
    state.scratch['patent_additions'] = [{'title':'한글로 쓴 추가 해결안', 'how_it_differs':'기존 구성을 조정합니다.',
        'transfer_conditions':['조건 확인'], 'validation_test':'시험이 필요합니다.',
        'reference':{'source_type':'PATENT', 'title':'번역된 제목',
            'original_title':'Original High-Speed Operation Device', 'identifier':'US1234567B2',
            'url':'https://patents.google.com/patent/US1234567B2'}}]
    return state


def test_source_metadata_is_excluded_without_disabling_product_text_cleanup(references_state):
    state = references_state
    before = state.model_dump_json()
    shown = report_state(state)
    assert [r.title for r in shown.evidence] == TITLES
    assert '파라미터 조정' in shown.concepts[0].description
    assert shown.scratch['patent_additions'][0]['title'] == '한글로 쓴 추가 해결안'
    assert shown.scratch['patent_additions'][0]['reference']['title'] == 'Original High-Speed Operation Device'
    literal = {'source_type':'PAPER','title':'CPT-abcdef12 Field Control입니다', 'claim':'CPT-abcdef12 검토'}
    labels = {'CPT-abcdef12':'해결안1 (잔류진동 감소 해결안)'}
    value = plain_value(display_value(literal, labels))
    assert value['title'] == literal['title']
    assert value['claim'] == '해결안1 (잔류진동 감소 해결안) 검토'
    assert state.model_dump_json() == before


@pytest.mark.parametrize('mode', list(RunMode))
def test_source_titles_are_exact_in_solution_cards_and_portable_reports(references_state, mode):
    state = references_state
    state.control.mode = mode
    before = state.model_dump_json()
    data = presentation.view(state)
    cards = data['solutions'][0]['reference_cards']
    assert [r['title'] for r in cards[:4]] == TITLES
    assert cards[4]['title'] == 'Time Domain Study of High-Speed Motion'
    assert [r['title'] for r in data['solutions'][0]['evidence']] == TITLES
    assert data['additions'][0]['reference']['title'] == 'Original High-Speed Operation Device'
    assert data['additions'][0]['title'] == '한글로 쓴 추가 해결안'
    markdown = render.render_report(state, {})
    html = unescape(render.render_html(state))
    for title in TITLES:
        assert title in markdown or title.replace('|', r'\|') in markdown
        assert title in html
    assert '높음-Speed' not in markdown and 'Positioning 시간' not in html
    assert 'translate="no"' in html
    assert state.model_dump_json() == before


def test_frozen_reference_titles_come_from_snapshot_not_mutated_live_metadata(references_state):
    state = references_state
    freeze(state)
    frozen = ledger.head(state.run_id)
    state.evidence[0].title = '바뀐 현재 제목'
    before = state.model_dump_json()
    data = presentation.view(state)
    assert data['solutions'][0]['reference_cards'][0]['title'] == TITLES[0]
    assert TITLES[0] in render.render_report(state, {})
    assert TITLES[0] in unescape(render.render_html(state))
    assert ledger.head(state.run_id) == frozen
    assert state.model_dump_json() == before
