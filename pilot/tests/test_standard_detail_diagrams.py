"""Source-contract regressions for the public/report SIS concept diagrams."""
from collections import Counter
from copy import deepcopy
import xml.etree.ElementTree as ET

import pytest

from triz import knowledge as K
from triz.standard_diagram_specs import specifications
from triz.standard_detail_specs import detail_specifications
from triz.standard_diagrams import (
    render_standard, render_standard_detail, supplemental_details,
    validate_detail_specs,
)


def _standard(code):
    return next(item for item in K.standards() if item['code'] == code)


def _text(svg):
    return ''.join(ET.fromstring(svg).itertext())


def test_complete_catalog_has_76_parents_11_official_methods_76_branches_13_sequences():
    catalog = K.standards()
    assert len(catalog) == 76
    assert len(validate_detail_specs(catalog)) == 87
    counts = Counter(detail['kind'] for item in catalog for detail in supplemental_details(item))
    assert counts == {'substandard': 11, 'variant': 76, 'sequence': 13}
    for item in catalog:
        before = deepcopy(item)
        parent = ET.fromstring(render_standard(item))
        assert parent.get('data-standard-code') == item['code']
        assert '실제 적용·검증 결과가 아닙니다' in ''.join(parent.itertext())
        assert item['conditions'].replace(' ', '') in ''.join(parent.itertext()).replace(' ', '')
        for detail in supplemental_details(item):
            svg = render_standard_detail(item, detail['key'])
            xml = ET.fromstring(svg)
            assert xml.get('data-standard-detail') == detail['key']
            assert detail['parent_code'] == item['code']
            assert detail['conditions'].replace(' ', '') in ''.join(xml.itertext()).replace(' ', '')
            assert '실제 적용·검증 결과가 아닙니다' in ''.join(xml.itertext())
            assert any(node.get('class') == 'sis-node' for node in xml.iter())
            if detail['kind'] != 'sequence':
                assert any(edge.get('class') == 'sis-edge' for edge in xml.iter())
        assert item == before


def test_only_official_substandards_have_codes_and_sources_are_not_mutated():
    for item in K.standards():
        for detail in supplemental_details(item):
            assert ('code' in detail) == (detail['kind'] == 'substandard')
            assert bool(detail.get('steps')) == (detail['kind'] == 'sequence')
            assert detail['sources']
            assert all(source.get('section') for source in detail['sources'])
    standard = deepcopy(_standard('5.1.1'))
    snapshot = deepcopy(standard)
    detail = supplemental_details(standard)[0]
    detail['sources'][0]['section'] = 'modified only in caller'
    assert standard == snapshot


def test_unknown_detail_or_new_unreviewed_branch_has_no_invented_fallback():
    with pytest.raises(KeyError):
        render_standard_detail(_standard('1.1.1'), 'variant-99')
    extended = deepcopy(_standard('1.1.1'))
    extended['variants'].append(dict(title_ko='미검토 분기', transformation='미확인', conditions='미확인', sources=[]))
    with pytest.raises(KeyError):
        render_standard_detail(extended, 'variant-4')
    with pytest.raises(AssertionError):
        validate_detail_specs([extended])


def test_maximum_shielding_and_minimum_local_amplification_are_distinct_alternatives():
    graphs = detail_specifications()
    maximum = graphs['1.1.8--sub-1.1.8.1']
    minimum = graphs['1.1.8--sub-1.1.8.2']
    max_nodes = {node['id']: node for node in maximum['nodes']}
    min_nodes = {node['id']: node for node in minimum['nodes']}
    assert max_nodes['F']['label'] == '전체 최대 장'
    assert max_nodes['S3']['kind'] == 'shield'
    assert ('S3', 'M') in {(edge['source'], edge['target']) for edge in maximum['edges']}
    assert min_nodes['F']['label'] == '전체 최소 장'
    assert min_nodes['S3']['kind'] == 'substance'
    assert ('S3', 'H') in {(edge['source'], edge['target']) for edge in minimum['edges']}
    assert '추가 장 생성' in min_nodes['S3']['label']


def test_all_nine_material_bypass_methods_have_their_own_mechanisms():
    item = _standard('5.1.1')
    details = supplemental_details(item)
    assert [d['code'] for d in details] == [f'5.1.1.{i}' for i in range(1, 10)]
    graphs = [detail_specifications()['5.1.1--' + d['key']] for d in details]
    assert len({repr(graph) for graph in graphs}) == 9
    assert any(n['kind'] == 'hollow' for n in graphs[0]['nodes'])
    assert any(n['kind'] == 'field' for n in graphs[1]['nodes'])
    assert any(n['kind'] == 'layer' for n in graphs[2]['nodes'])
    assert any('고활성' in n['label'] for n in graphs[3]['nodes'])
    assert any(n['kind'] == 'pattern' for n in graphs[4]['nodes'])
    assert any(n['kind'] == 'pulse' for n in graphs[5]['nodes'])
    assert any(n['kind'] == 'copy' for n in graphs[6]['nodes'])
    assert any('화합물' in n['label'] for n in graphs[7]['nodes'])
    assert any('기존 대상·환경' in n['label'] for n in graphs[8]['nodes'])


def test_ferromagnetic_particle_and_host_material_sequences_remain_independent():
    xml = ET.fromstring(render_standard_detail(_standard('2.4.2'), 'sequence'))
    paths = [node for node in xml.iter() if node.get('data-sequence-path')]
    assert len(paths) == 2
    assert [len([node for node in path.iter() if node.get('data-sequence-stage')]) for path in paths] == [3, 4]
    assert '강자성 입자의 발전' in ''.join(paths[0].itertext())
    assert '입자를 포함하는 물질의 별도 발전' in ''.join(paths[1].itertext())
    assert [len([node for node in path.iter() if node.get('class') == 'sequence-edge']) for path in paths] == [2, 3]
    for path in paths:
        stages = [node.get('data-sequence-stage') for node in path.iter() if node.get('data-sequence-stage')]
        for edge in path.iter():
            if edge.get('class') == 'sequence-edge':
                assert edge.get('data-source-stage') in stages and edge.get('data-target-stage') in stages


@pytest.mark.parametrize('code', ['2.2.3', '2.2.4', '2.4.11', '3.1.3', '3.1.4', '4.5.2', '5.2.1', '5.2.2', '5.2.3', '5.3.5', '5.4.2', '5.5.2'])
def test_every_development_step_is_present_in_order(code):
    item = _standard(code)
    xml = ET.fromstring(render_standard_detail(item, 'sequence'))
    stages = [node for node in xml.iter() if node.get('data-sequence-stage')]
    assert len(stages) == len(item['development_sequence'])
    for stage, text in zip(stages, item['development_sequence']):
        assert text.replace(' ', '') in ''.join(stage.itertext()).replace(' ', '')
    if code.startswith('5.2.'):
        assert '이 경로로 불가능하면' in ''.join(xml.itertext())


def test_phase_coexistence_is_not_confused_with_interaction_or_periodic_transition():
    specs = specifications()
    assert specs['5.3.4']['after']['edges'] == []
    interaction = specs['5.3.5']['after']['edges'][0]
    assert interaction['style'] == 'both'
    assert '물리적 또는 화학적 상호작용' == interaction['label']
    assert '5.3.4' in specs['5.3.5']['before']['title']
    physical = _text(render_standard_detail(_standard('5.3.5'), 'variant-1'))
    chemical = _text(render_standard_detail(_standard('5.3.5'), 'variant-2'))
    assert '물리적 상호작용' in physical and '화학적 상호작용' in chemical
    assert specs['5.4.1']['after']['edges'][0]['style'] == 'both'
    assert '정방향·복귀 조건' in specs['5.4.1']['after']['edges'][0]['label']


def test_critical_output_preserves_energy_source_and_trigger_and_contact_compensation_preserves_both_substances():
    specs = specifications()
    graph = specs['5.4.2']['after']
    assert {node['id'] for node in graph['nodes']} == {'E', 'C', 'I', 'R'}
    assert {(edge['source'], edge['target']) for edge in graph['edges']} == {('E', 'C'), ('I', 'C'), ('C', 'R')}
    contact = specs['1.2.4']['after']
    assert {node['id'] for node in contact['nodes']} == {'F1', 'S1', 'S2', 'F2'}
    assert any(e['source'] == 'S2' and e['target'] == 'S1' and '직접 접촉' in e['label'] for e in contact['edges'])


def test_incorrect_extra_starting_prerequisites_are_removed():
    specs = specifications()
    assert '기존 시스템' in specs['2.4.2']['before']['title']
    assert '4.1.1' in specs['4.1.2']['before']['title']
    assert '장 통과' in specs['4.3.2']['before']['title']
    assert '도구 교체·첨가' in specs['5.1.2']['before']['title']
    assert '도구가 없고' not in specs['5.1.2']['before']['title']
