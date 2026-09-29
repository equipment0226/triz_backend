"""A report must show each saved proposal, never a shared illustrative example."""
from copy import deepcopy
import xml.etree.ElementTree as ET

import pytest

from triz import knowledge as K
from triz.schema import ConceptSpec, PhysicalContradiction, RawIdea, ReportArtifact


def configure_report(state):
    """Synthetic review proposals for display checks; no physical validation."""
    pc1 = PhysicalContradiction(id='PC-heating', label='접합과 열 손상', element='접합 헤드', parameter='온도',
        state_a='접합 시 가열', reason_a='접합부를 형성해야 한다',
        state_b='대기 시 냉각', reason_b='주변 부품의 열 손상을 줄여야 한다')
    pc2 = PhysicalContradiction(id='PC-gripper', label='고정과 이송', element='이송 지그', parameter='구속력',
        state_a='가공 중 고정', reason_a='가공 위치를 유지해야 한다',
        state_b='이송 중 해제', reason_b='다음 공정으로 이동해야 한다')
    state.definition.physical_contradictions = [pc1, pc2]
    first = dict(kind='TIME', applicable=True, source_pc_id=pc1.id,
        catalog_version=K.separation()['TIME']['catalog_version'], title='접합 헤드 펄스 가열',
        how='접합 구간에만 헤드를 가열하고 대기 구간에는 냉각한다.',
        idea='기존 히터 제어기에 가열과 대기의 운전 구간을 나누어 설정한다.',
        mechanism='가열 시간을 제한하여 주변 부품에 축적되는 열을 줄이는 제안이다.',
        conditions=['허용 온도와 냉각 시간은 미확인'], validation_test='접합 강도와 주변 온도를 함께 측정한다.',
        supporting_principles=[9])
    second = dict(kind='TIME', applicable=True, source_pc_id=pc2.id,
        catalog_version=K.separation()['TIME']['catalog_version'], title='지그 구속력 시퀀스',
        how='가공 구간에는 지그를 고정하고 이송 구간에는 지그를 해제한다.',
        idea='장비의 가공 완료 신호와 지그의 해제 명령을 연결한다.',
        mechanism='공정 신호에 따라 고정과 이동 기능의 실행 구간을 나누는 제안이다.',
        conditions=['이송 전 잔류 구속력 확인 필요'], validation_test='위치 오차와 해제 시간을 측정한다.',
        supporting_principles=[15])
    rejected = dict(kind='SPACE', applicable=False, source_pc_id=pc1.id,
        not_applicable_reason='설치 공간을 나눌 수 있는 근거가 없다.', supporting_principles=[])
    state.solve.separation_apps = [first, rejected, second]
    state.solve.raw_ideas = [RawIdea(id=identifier, track='B_SEPARATION', title=app['title'],
        idea=app['idea'], addresses=[app['source_pc_id']], detail=deepcopy(app))
        for identifier, app in [('IDEA-heating', first), ('IDEA-gripper', second)]]
    state.concepts = [ConceptSpec(id='CPT-heating', title='펄스 가열 접합 헤드', source_idea_ids=['IDEA-heating'],
        one_liner='접합에 필요한 구간의 가열을 제어한다.', working_principle='접합 완료 신호 이후 냉각 운전으로 전환한다.',
        changes_to_system=['접합 헤드의 운전 시퀀스 변경']),
        ConceptSpec(id='CPT-gripper', title='이송 연동 지그', source_idea_ids=['IDEA-gripper'],
        one_liner='가공과 이송에 맞춰 지그를 제어한다.', working_principle='가공 완료를 확인한 뒤 지그의 고정을 해제한다.',
        changes_to_system=['이송 인터록과 지그 제어 연결']),
        ConceptSpec(id='CPT-unlinked', title='계보 없는 별도 해결안',
        triz_origin=[{'track':'B_SEPARATION', 'ref':'시간 분리'}],
        working_principle='연결 근거가 없는 설명은 앞선 두 원안과 결합하지 않는다.')]
    state.report = ReportArtifact()
    return first, second, rejected


def svg_text(figure):
    return ''.join(ET.fromstring(figure['svg']).itertext())


@pytest.mark.parametrize('frozen', [False, True])
def test_saved_separation_diagrams_appear_only_in_the_track_section(state, frozen):
    from triz.presentation import view
    from test_ax_full_report import freeze
    first, second, rejected = configure_report(state)
    state.solve.coverage_note = '표시하지 않을 해결범위 종합서술'
    state.solve.gaps = ['표시하지 않을 탐색보완 종합서술']
    if frozen:
        freeze(state)
    before = state.model_dump_json()
    data = view(state)
    by_key = {figure['key']:figure for figure in data['figures']}
    for index, app in enumerate((first, second)):
        proposal_key = f'separation-{index}-application-0'
        proposal = by_key[proposal_key]
        assert ET.fromstring(proposal['svg']).get('data-diagram') == 'separation-application'
        assert app['how'] in svg_text(proposal)
        assert app['idea'] in svg_text(proposal)
        assert (second if index == 0 else first)['how'] not in svg_text(proposal)
        assert '부위 1 · 요구 A' not in svg_text(proposal)
        assert '시점 t₁ · 요구 A' not in svg_text(proposal)
        assert state.concepts[index].working_principle not in svg_text(proposal)
    assert not any(key.startswith('concept-separation-') for key in by_key)
    assert not any('separation-concept-group' in figure['svg'] for figure in by_key.values())
    blocks = [(section['title'], block) for section in data['report_sections'] for block in section['blocks']]
    placements = [(title, block['figure']['key']) for title, block in blocks if block['type'] == 'figure']
    for key in by_key:
        assert sum(used_key == key for _, used_key in placements) == 1
    assert next(title for title,key in placements if key=='separation-0-application-0').startswith('4.')
    concept_section = next(title for title,key in placements if key=='concept-0')
    assert not any(key.startswith('separation-') for title,key in placements if title == concept_section)
    assert not any('표시하지 않을' in block.get('html','') for _,block in blocks)
    assert any(rejected['not_applicable_reason'] in block.get('html','') for _,block in blocks)
    assert state.model_dump_json() == before


def test_unlinked_proposal_uses_its_own_record_without_an_unrelated_pc_or_solution(state):
    from triz.presentation import view
    configure_report(state)
    app = dict(kind='SPACE', applicable=True, title='미연결 구역 배치',
        how='기존 기록에는 구역을 분리한다는 제안만 남아 있다.', idea='설치 구역의 상세 치수는 확인하지 못했다.')
    state.solve.separation_apps = [app]
    state.solve.raw_ideas = []
    before = state.model_dump_json()
    data = view(state)
    figure = next(f for f in data['figures'] if f['key']=='separation-unlinked-application-0')
    text = svg_text(figure)
    assert app['how'] in text and app['idea'] in text
    assert '접합 헤드' not in text and '이송 지그' not in text
    assert not any(f['key'].startswith('concept-separation-') for f in data['figures'])
    assert state.model_dump_json() == before
