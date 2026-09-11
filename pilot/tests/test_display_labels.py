import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile

import pytest
from fastapi.testclient import TestClient
from triz import render, store, visuals
from triz.labels import build_label_map, humanize, label_of
from triz.presentation import view
from triz.schema import ConceptSpec, ConceptEvaluation, HumanRequest, ReportArtifact, SystemCandidate, RunMode


@pytest.fixture
def referenced_state(state):
    state.concepts = [
        ConceptSpec(id='cb-123456', title='펄스 세정', one_liner='짧은 펄스로 손상을 줄인다',
            description='해결안1(cb-123456)은 CPT-abcdef12와 함께 적용한다.',
            changes_to_system=['cb-123456의 제어 주기를 조정한다'],
            assumptions=['CPT-abcdef12의 조건을 유지한다'],
            validation_plan=[{'test': 'cb-123456 검증'}]),
        ConceptSpec(id='CPT-abcdef12', title='유량 분리', one_liner='유량을 독립 제어한다'),
    ]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id='cb-123456', rank=2),
                                    ConceptEvaluation(concept_id='CPT-abcdef12', rank=1)]
    state.confirm.candidates = [SystemCandidate(id='SYS-123abcde', name='세정 장비', description='cb-123456 적용')]
    state.report = ReportArtifact(narrative={'executive_summary': '해결안1(CB-123456)과 CPT-abcdef12를 비교한다.'})
    state.scratch['title'] = 'cb-123456 개선 검토'
    state.raw_query = 'cb-123456의 손상을 낮춘다'
    state.intake.frame.symptom = 'cb-123456의 손상'
    state.control.warnings = ['cb-123456 조건 확인']
    state.scratch['patent_additions'] = [{'title': 'cb-123456 보완', 'working_principle': 'CPT-abcdef12의 조건',
        'reference': {'title': 'cb-123456 적용 근거', 'url': 'https://example.org/patent'}}]
    state.scratch['evidence_gaps'] = [{'title': 'cb-123456', 'missing': ['PATENT']}]
    state.pending = HumanRequest(title='해결안1(cb-123456)을 확인해 주세요', payload={
        'questions': [{'question': 'CB-123456은 어떤가요?', 'why_needed': 'CPT-abcdef12 비교',
                       'proposed_answers': ['cb-123456 유지', 'CPT-abcdef12 적용']}],
    })
    return state


@pytest.mark.parametrize('source', ['cb-123456', 'CB-123456', '해결안1(cb-123456)',
    '해결안 9 (`CB-123456`)', '해결안1[cb-123456]', '「CB-123456」'])
def test_references_have_one_canonical_number_and_summary(referenced_state, source):
    labels = build_label_map(referenced_state)
    assert humanize(source, labels) == '해결안1 (펄스 세정)'
    assert humanize(source, labels, keep_code=True) == '해결안1 (펄스 세정)'
    assert humanize(humanize(source, labels), labels) == '해결안1 (펄스 세정)'
    assert humanize('검토:cb-123456은', labels) == '검토:해결안1 (펄스 세정)은'


def test_unknown_ids_never_fall_back_to_code_and_external_identifiers_survive():
    assert label_of('cpt-99999999', {}) == '해결안 (내용 확인 필요)'
    assert humanize('SYS-99999999 / ATT-abcdef12', {}) == '대상 시스템 (내용 확인 필요) / 첨부자료 (내용 확인 필요)'
    source = 'US-12345678-B2 DOI 10.1234/paper https://example.org/CB-123456'
    assert humanize(source, {}) == source


def test_arbitrary_stored_ids_are_resolved_without_hex_assumptions(state):
    state.concepts = [ConceptSpec(id='legacy-solution-A', title='압력 분리')]
    assert humanize('legacy-solution-A를 검토', build_label_map(state)) == '해결안1 (압력 분리)를 검토'


def _assert_display_clean(value, key=''):
    if key in ('id', 'key', 'url', 'identifier') or key.endswith(('_id', '_ids')):
        return
    if isinstance(value, str):
        assert not re.search(r'(?:cb|cpt|sys)-[a-z0-9]{6,32}', value, re.I), (key, value[:250])
    elif isinstance(value, dict):
        for k, v in value.items():
            _assert_display_clean(v, k)
    elif isinstance(value, list):
        for v in value:
            _assert_display_clean(v, key)


def test_every_view_surface_is_clean_and_selection_keys_survive(referenced_state):
    state = referenced_state
    original = state.model_dump_json()
    data = view(state)
    _assert_display_clean(data)
    assert data['guide'] == '해결안1 (펄스 세정)을 확인해 주세요'
    assert data['solutions'][0]['number'] == 2  # rank changes display order, not identity
    assert data['solutions'][0]['key'] == 'CPT-abcdef12'
    assert data['solutions'][0]['display_label'] == '해결안2 (유량 분리)'
    assert data['pending']['interrupt_id'] == state.pending.interrupt_id
    for kind, payload in [('CONFIRM', {'candidates': [state.confirm.candidates[0].model_dump()]}),
                          ('DECIDE', {'conditional': [{'concept_id': 'cb-123456', 'title': 'cb-123456', 'mitigation': 'CPT-abcdef12 비교'}]}),
                          ('FEEDBACK', {'concepts': [{'concept_id': 'cb-123456', 'title': 'cb-123456'}]})]:
        alternate = state.model_copy(update={'pending': HumanRequest(kind=kind, payload=payload)})
        result = view(alternate)
        _assert_display_clean(result)
        item = next(iter(result['pending']['payload'].values()))[0]
        assert item.get('concept_id', item.get('id')) == ('SYS-123abcde' if kind == 'CONFIRM' else 'cb-123456')
    assert state.model_dump_json() == original


@pytest.mark.parametrize('mode', ['FULL', 'LITE', 'DEEP'])
def test_portable_reports_and_svg_are_clean_before_text_wrapping(referenced_state, mode):
    state = referenced_state
    state.control.mode = RunMode(mode)
    original = state.model_dump_json()
    markdown = render.render_report(state, state.report.narrative)
    html = render.render_html(state)
    _assert_display_clean(markdown)
    _assert_display_clean(html)
    assert '해결안1 (펄스 세정)' in markdown
    for figure in visuals.figures(state):
        root = ET.fromstring(figure['svg'])
        _assert_display_clean(''.join(root.itertext()))
    assert state.model_dump_json() == original


def test_downloads_context_library_and_notifications_use_current_display(referenced_state, monkeypatch):
    from api.main import app
    from triz.settings import settings
    monkeypatch.setattr(settings, 'app_token', '')
    monkeypatch.setattr(settings, 'require_user_auth', False)
    state = referenced_state
    state.status = 'WAITING_HUMAN'
    store.save_state(state)
    store.publish_run(state.run_id, state.user_id)
    original = store.load_state(state.run_id).model_dump_json()
    client = TestClient(app)
    for path in [f'/api/runs/{state.run_id}/view', f'/api/public/runs/{state.run_id}/view',
                 f'/api/runs/{state.run_id}/report/context']:
        response = client.get(path)
        assert response.status_code == 200
        _assert_display_clean(response.json())
    bundle = client.get(f'/api/runs/{state.run_id}/report?format=bundle')
    assert bundle.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        for name in archive.namelist():
            _assert_display_clean(archive.read(name).decode())
    _assert_display_clean(store.runs_page(user_id=state.user_id))
    _assert_display_clean(store.pending_notifications(state.user_id))
    assert store.load_state(state.run_id).model_dump_json() == original
