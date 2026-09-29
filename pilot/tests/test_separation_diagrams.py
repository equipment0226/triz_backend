"""Shared approach concepts and report references never fabricate saved results."""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from triz import knowledge as K, separation_diagrams as diagrams

NS = {'s': 'http://www.w3.org/2000/svg'}


def roots(svg):
    return [node for node in ET.fromstring(svg).iter()
            if node.get('data-diagram') == 'separation-concept']


def test_seven_concepts_use_distinct_geometry_canonical_names_and_explicit_limits():
    geometry = set()
    for kind, row in K.separation().items():
        svg = diagrams.diagram(kind)
        root = ET.fromstring(svg)
        assert root.get('data-approach-kind') == kind
        assert root.get('data-catalog-version') == row['catalog_version']
        assert row['name_ko'] in ''.join(root.itertext())
        assert '설명용 개념도' in svg
        assert '실제 적용안이나 검증된 결과를 나타내지 않는다' in svg
        mechanism = next(node for node in root.iter() if node.get('data-mechanism'))
        shapes = [(node.tag, sorted((key, value) for key, value in node.attrib.items()
                   if key not in ('fill', 'stroke', 'data-mechanism'))) for node in mechanism.iter()
                  if node.tag.rsplit('}', 1)[-1] not in ('g', 'text')]
        geometry.add(repr(shapes))
        assert not any(node.tag.endswith(('script','image','foreignObject')) for node in root.iter())
        assert all(float(node.get('font-size')) >= 14 for node in root.iter() if node.get('font-size'))
        assert all(float(node.get('y', 0)) < diagrams.HEIGHT for node in root.iter() if node.tag.endswith('text'))
    assert len(geometry) == 7
    assert '대상 1' in diagrams.diagram('CONDITION') and '대상 2' in diagrams.diagram('CONDITION')
    assert '임계값만 바뀌는' in diagrams.diagram('CONDITION')
    assert '방향 x' in diagrams.diagram('DIRECTION') and '방향 y' in diagrams.diagram('DIRECTION')
    assert '부분 A' in diagrams.diagram('SYSTEM_LEVEL') and '전체 수준' in diagrams.diagram('SYSTEM_LEVEL')
    assert '인과 메커니즘' in diagrams.diagram('SATISFY')
    assert '같은 목적' in diagrams.diagram('BYPASS') and '다른 기능 실현 방식' in diagrams.diagram('BYPASS')


def test_static_asset_manifest_and_overview_match_the_shared_renderer():
    assets = diagrams.assets()
    assert set(assets) == {kind.lower()+'.svg' for kind in K.separation()} | {'overview.svg','legacy_condition.svg'}
    overview = [node for node in ET.fromstring(assets['overview.svg']).iter() if node.get('data-approach-kind')]
    assert [root.get('data-approach-kind') for root in overview] == list(K.separation())
    assert '5가지 분리 + 2가지 보완' in assets['overview.svg']
    for kind in K.separation():
        assert assets[kind.lower()+'.svg'] == diagrams.diagram(kind)
    directory = Path(__file__).resolve().parents[2]/'frontend/public/knowledge/separation'
    if directory.exists():
        for name, svg in assets.items():
            assert (directory/name).read_text(encoding='utf-8') == svg


@pytest.mark.parametrize('kind', ['UNKNOWN', None, '<script>', 'PRESSURE'])
def test_unknown_kind_is_not_drawn_as_a_known_approach(kind):
    with pytest.raises(ValueError):
        diagrams.diagram(kind)


def test_legacy_condition_keeps_broad_conditions_and_mixed_groups_do_not_fill_missing_reviews():
    applications = [
        {'kind':'CONDITION', 'applicable':True, 'how':'Original condition', 'idea':'Saved legacy design'},
        {'kind':'CONDITION', 'applicable':False, 'catalog_version':'matriz-pc-7-2026-09-29',
         'not_applicable_reason':'Saved uncertainty'},
        {'kind':'BYPASS', 'applicable':False, 'catalog_version':'matriz-pc-7-2026-09-29'},
        {'kind':'PRIVATE_UNKNOWN_KIND', 'applicable':False},
    ]
    before = deepcopy(applications)
    svg = diagrams.for_applications(applications)
    concepts = roots(svg)
    assert [r.get('data-approach-kind') for r in concepts] == ['CONDITION','CONDITION','BYPASS']
    assert concepts[0].get('data-catalog-version') == 'legacy-separation-4-v1'
    assert '온도·하중 등 저장된 조건 구분' in ''.join(concepts[0].itertext())
    assert concepts[0].get('aria-label') == '조건 분리 개념도'
    assert '관계(조건) 분리' in ''.join(concepts[1].itertext())
    assert 'PRIVATE_UNKNOWN_KIND' not in svg
    assert 'TIME' not in svg and 'SPACE' not in svg
    assert applications == before
    assert roots(diagrams.for_applications([{'kind':'PRIVATE_UNKNOWN_KIND'}])) == []


@pytest.mark.parametrize('frozen', [False, True])
def test_report_uses_only_saved_approaches_and_preserves_saved_application_rows(state, frozen):
    from triz import render
    from triz.presentation import view
    from triz.schema import PhysicalContradiction, ReportArtifact
    from test_ax_full_report import freeze
    pc = PhysicalContradiction(id='PC-existing', element='support', parameter='rigidity',
        state_a='rigid', state_b='flexible')
    state.definition.physical_contradictions = [pc]
    state.solve.separation_apps = [dict(kind='TIME', source_pc_id=pc.id, applicable=True,
        title='Saved option', how='Saved timing sequence', idea='Saved design idea', supporting_principles=[9],
        catalog_version=K.separation()['TIME']['catalog_version'], approach_name='시간 분리'),
        dict(kind='BYPASS', source_pc_id=pc.id, applicable=False, not_applicable_reason='Saved missing evidence',
        supporting_principles=[], catalog_version=K.separation()['BYPASS']['catalog_version'], approach_name='모순 요구 우회'),
        dict(kind='TIME', source_pc_id=pc.id, applicable=True,
        title='Second saved option', how='Second timing sequence', idea='Second design idea', supporting_principles=[10],
        catalog_version=K.separation()['TIME']['catalog_version'], approach_name='시간 분리')]
    state.report = ReportArtifact()
    if frozen:
        freeze(state)
    before = state.model_dump_json()
    report = view(state)
    figures = [f for f in report['figures'] if f['key'].startswith('separation-')]
    assert [f['key'] for f in figures] == ['separation-0-application-0', 'separation-0-application-2']
    for figure in figures:
        svg = ET.fromstring(figure['svg'])
        assert svg.get('data-diagram') == 'separation-application'
        assert svg.get('data-approach-kind') == 'TIME'
        assert not roots(figure['svg'])
        assert 'Saved missing evidence' not in ''.join(svg.itertext())
    figure_text = [''.join(ET.fromstring(f['svg']).itertext()) for f in figures]
    assert 'Saved timing sequence' in figure_text[0] and 'Saved design idea' in figure_text[0]
    assert 'Second timing sequence' in figure_text[1] and 'Second design idea' in figure_text[1]
    assert 'Second timing sequence' not in figure_text[0] and 'Saved timing sequence' not in figure_text[1]
    used = [b['figure']['key'] for section in report['report_sections'] for b in section['blocks'] if b['type']=='figure']
    assert 'separation-0' not in used
    assert all(used.count(figure['key']) == 1 for figure in figures)
    markdown = render.render_report(state, {})
    for text in ('Saved timing sequence','Saved design idea','Saved missing evidence',
                 'Second timing sequence','Second design idea'):
        assert text in markdown
    assert '5가지 분리와 2가지 보완' in markdown
    assert state.model_dump_json() == before


@pytest.mark.parametrize('frozen', [False, True])
def test_standard_report_keeps_only_saved_application_diagrams_without_catalog_references(state, frozen):
    from triz import render
    from triz.presentation import view
    from triz.schema import ReportArtifact
    from test_ax_full_report import freeze
    # Catalog details remain in the introduction. Reports retain actual saved
    # models and application text, without filling gaps with generic diagrams.
    codes = ['5.1.1','5.4.2','3.1.1']
    catalog = {row['code']:row for row in K.standards()}
    model = {'nodes':[{'id':'S1','label':'Saved existing body'}, {'id':'F','label':'Saved existing action'}],
             'edges':[{'source':'F','target':'S1','label':'저장된 작용 방향','kind':'useful'}]}
    state.solve.standard_apps = [dict(standard_code=code, standard_title='Stored previous label',
        idea='Saved actual option '+code, transformation='Saved transformation '+code,
        resulting_model=deepcopy(model) if i==0 else None) for i, code in enumerate(codes)]
    state.report = ReportArtifact()
    if frozen:
        freeze(state)
    before = state.model_dump_json()
    report = view(state)
    by_key = {f['key']:f for f in report['figures']}
    used = [b['figure']['key'] for section in report['report_sections'] for b in section['blocks'] if b['type']=='figure']
    assert '저장된 작용 방향' in ''.join(ET.fromstring(by_key['standard-0']['svg']).itertext())
    assert ET.fromstring(by_key['standard-0']['svg']).get('data-diagram') == 'standard-application'
    assert used.count('standard-0') == 1
    assert 'standard-1' not in by_key and 'standard-2' not in by_key
    assert not any(key.startswith('reference-standard-') for key in by_key)
    assert not any(key.startswith('reference-standard-') for key in used)
    markdown = render.render_report(state, {})
    assert '적용 내용' in markdown and '표준해 참고 설명' not in markdown
    assert all('Saved actual option '+code in markdown for code in codes)
    assert all('Saved transformation '+code in markdown for code in codes)
    assert all(catalog[code]['title_ko'] in markdown for code in codes)
    assert '공식 하위 기법·번호 없는 분기·개발 순서' not in markdown
    assert catalog['5.4.2']['conditions'] in markdown
    assert state.model_dump_json() == before


def test_repeated_standard_keeps_each_actual_application_without_catalog_reference(state):
    from triz.presentation import view
    from triz.render import render_report
    from triz.schema import ReportArtifact
    state.solve.standard_apps = [dict(standard_code='5.1.1', idea='Saved option '+str(i),
        resulting_model={'nodes':[{'id':'S1','label':'Existing body '+str(i)}], 'edges':[]} if i<2 else None)
        for i in range(3)]
    state.report = ReportArtifact()
    before = state.model_dump_json()
    report = view(state)
    keys = [f['key'] for f in report['figures']]
    assert [key for key in keys if key.startswith('standard-')] == ['standard-0','standard-1']
    assert not any(key.startswith('reference-standard-') for key in keys)
    assert all(ET.fromstring(f['svg']).get('data-diagram') == 'standard-application'
               for f in report['figures'] if f['key'].startswith('standard-'))
    markdown = render_report(state, {})
    assert all('Saved option '+str(i) in markdown for i in range(3))
    assert '앞선 같은 표준해의 참고 설명' not in markdown
    assert state.model_dump_json() == before
