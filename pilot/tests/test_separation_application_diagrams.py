"""Saved proposal diagrams preserve text without inventing a physical mapping."""
from copy import deepcopy
import json
import xml.etree.ElementTree as ET

import pytest

from triz import knowledge as K
from triz.separation_application_diagrams import render_application


def example(kind='SPACE'):
    application = dict(kind=kind, applicable=True, title='분할 지지 구조 적용안',
        how='삽입 시에는 기존 외피를 지지하고 운전 중에는 중앙 연결부의 변형을 허용한다.',
        idea='분할 외피를 기존 연결부에 결합한다.', mechanism='외피와 연결부의 하중 전달 경로를 구분한다.',
        conditions=['외피 제거 여부 미확인', '연결부 변형량 시험 필요'],
        validation_test='반복 삽입과 굽힘 시험에서 균열 발생 여부를 비교한다.',
        catalog_version=K.separation()[kind]['catalog_version'])
    contradiction = dict(element='전극 지지 구조', parameter='굽힘 강성',
        state_a='삽입 하중을 지탱할 만큼 단단해야 한다', reason_a='삽입 중 좌굴 방지',
        state_b='장기 운전 중 유연해야 한다', reason_b='생체 조직 변형 추종')
    solution = dict(title='가변 외피 지지 전극', one_liner='외피와 연결부의 역할을 나눈다.',
        working_principle='외피가 삽입 하중을 담당하고 연결부가 변형을 수용하는 제안이다.')
    return application, contradiction, solution


def xml(figure):
    return ET.fromstring(figure['svg'])


def text(figure):
    return ''.join(xml(figure).itertext())


def field_text(root, name):
    return ''.join(''.join(node.itertext()) for node in root.iter() if node.get('data-field')==name)


@pytest.mark.parametrize('kind', list(K.separation()))
def test_all_approaches_preserve_every_saved_field_and_never_mutate(kind):
    application, contradiction, solution = example(kind)
    before = deepcopy((application, contradiction, solution))
    figure = render_application(application, contradiction=contradiction, solution=solution)
    assert set(figure) == {'title','compact','svg','note'} and figure['compact'] is True
    root = xml(figure)
    assert root.get('data-diagram') == 'separation-application'
    assert root.get('data-approach-kind') == kind
    assert solution['title'] in figure['title'] and K.separation()[kind]['name_ko'] in figure['title']
    for source, fields, prefix in [(application, ['title','how','idea','mechanism','validation_test'], 'application'),
                                  (contradiction, list(contradiction), 'contradiction'),
                                  (solution, ['one_liner','working_principle'], 'solution')]:
        for field in fields:
            assert source[field] in field_text(root, prefix+'.'+field)
    assert all(condition in field_text(root, 'application.conditions') for condition in application['conditions'])
    assert (application, contradiction, solution) == before
    assert figure['note'] == '분석에 기록된 적용 내용이며 실증 결과는 별도입니다.'
    for example_label in ('부위 1', '부위 2', '시점 t₁', '시점 t₂', '대상 1', '대상 2', '같은 목적'):
        assert example_label not in text(figure)


def test_kind_geometry_is_distinct_and_arrows_are_saved_references_only():
    layouts = set()
    for kind in K.separation():
        app, contradiction, solution = example(kind)
        root = xml(render_application(app, contradiction=contradiction, solution=solution))
        geometry = [(node.tag, tuple((k,v) for k,v in sorted(node.attrib.items())
                    if k in ('data-node','x','y','width','height','d')))
                    for node in root.iter() if node.tag.rsplit('}',1)[-1] in ('rect','path')]
        layouts.add(json.dumps(geometry, ensure_ascii=False))
        edges = [node for node in root.iter() if node.get('class')=='separation-application-edge']
        assert edges and all(edge.get('data-relationship')=='saved-reference' for edge in edges)
        assert not any(edge.get('data-source')=='requirement-a' and edge.get('data-target')=='requirement-b' for edge in edges)
    assert len(layouts) == 7


@pytest.mark.parametrize('kind', list(K.separation()))
def test_same_approach_with_different_solutions_has_its_own_title_and_contents(kind):
    app, contradiction, first = example(kind)
    second = dict(first, title='독립된 두 번째 해결책', working_principle='두 번째 해결책의 저장된 작동 원리')
    one = render_application(app, contradiction=contradiction, solution=first)
    other = render_application(dict(app, title='두 번째 적용안', how='두 번째 적용 방식 원문'),
                               contradiction=contradiction, solution=second)
    assert one['title'] != other['title'] and one['svg'] != other['svg']
    assert first['title'] in text(one) and first['title'] not in text(other)
    assert second['working_principle'] in text(other)
    assert '두 번째 적용 방식 원문' in text(other)


@pytest.mark.parametrize('applicable', [False, None, 'false', 'true', 1, 0, [], {}])
def test_only_explicit_boolean_applicable_can_be_drawn(applicable):
    app, _, _ = example()
    app['applicable'] = applicable
    with pytest.raises(ValueError, match='applicable=True'):
        render_application(app)


@pytest.mark.parametrize('kind', ['UNKNOWN', None, [], {}, 7, '<script>'])
def test_unknown_kind_is_rejected(kind):
    with pytest.raises(ValueError, match='Unknown'):
        render_application(dict(kind=kind, applicable=True))


@pytest.mark.parametrize('application', [None, [], 'not a dictionary', {}, {'kind':'SPACE'}])
def test_missing_or_unusable_application_is_not_presented_as_an_application(application):
    with pytest.raises(ValueError):
        render_application(application)


def test_missing_optional_records_do_not_create_empty_cards_or_fabricated_states_or_goals():
    for kind in ('TIME','SATISFY','BYPASS'):
        figure = render_application(dict(kind=kind, applicable=True, title='원안 제목',
                                         how='저장된 적용 내용', idea='원안의 구체적 아이디어'))
        words = text(figure)
        assert '대상 모순 연결 정보 없음' in words
        assert '저장된 적용 내용' in words and '원안의 구체적 아이디어' in words
        nodes={node.get('data-node') for node in xml(figure).iter() if node.get('data-node')}
        assert nodes == {'application-how','proposal'}
        assert '기록 없음' not in words and '해결안의 작동 방식' not in words
        for invented in ('검증 통과','목적 달성','요구 A 충족','요구 B 충족','시점 t','상태 전환 완료'):
            assert invented not in words


def test_time_wording_is_not_split_or_reclassified_into_an_event_sequence():
    app, contradiction, solution = example('TIME')
    app['how'] = '먼저/나중이라는 표현은 가설이다. 위치·시간 전환의 순서와 구간은 아직 확정되지 않았다.'
    root = xml(render_application(app, contradiction=contradiction, solution=solution))
    assert app['how'] in field_text(root, 'application.how')
    assert {node.get('data-node') for node in root.iter() if node.get('data-node')} == {
        'contradiction','application-how','requirement-a','requirement-b','proposal','solution','conditions'}
    assert not any(node.get('data-phase') or node.get('data-time') or node.get('data-order') for node in root.iter())


def test_legacy_condition_and_explicit_relation_remain_distinct():
    app, contradiction, solution = example('CONDITION')
    current = render_application(app, contradiction=contradiction, solution=solution)
    del app['catalog_version']
    old = render_application(app, contradiction=contradiction, solution=solution)
    assert current['title'].endswith('관계(조건) 분리')
    assert old['title'].endswith('조건 분리') and '관계(조건) 분리' not in text(old)
    app.update(kind='RELATION', catalog_version=K.separation()['CONDITION']['catalog_version'])
    assert xml(render_application(app)).get('data-approach-kind') == 'CONDITION'


def test_original_application_and_final_solution_keep_their_own_content_and_provenance():
    app, contradiction, solution = example('TIME')
    solution.update(provenance_label='도출 원안의 분리 적용 기록',
                    working_principle='최종 해결안에서 수정된 구동 방식',
                    changes_to_system=['변경된 연결부 치수','최종 해결안의 추가 제어기'])
    root=xml(render_application(app,contradiction=contradiction,solution=solution))
    assert any(node.get('data-provenance-label') == solution['provenance_label'] for node in root.iter())
    assert '원안의 분리 방식' in ''.join(root.itertext())
    assert app['how'] in field_text(root,'application.how')
    assert app['mechanism'] in field_text(root,'application.mechanism')
    assert solution['working_principle'] in field_text(root,'solution.working_principle')
    assert all(change in field_text(root,'solution.changes_to_system') for change in solution['changes_to_system'])


def test_repeated_original_wording_is_shown_once_and_absent_solution_is_omitted():
    wording='중앙 연결부의 변형을 허용한다.'
    app=dict(kind='SPACE',applicable=True,title='중앙 연결부',how=wording,idea=wording,mechanism=wording)
    root=xml(render_application(app))
    assert not any(node.get('data-node')=='solution' for node in root.iter())
    assert sum(''.join(node.itertext()).count(wording) for node in root.iter() if node.tag.endswith('text')) == 1
    assert not any(node.get('data-node')=='proposal' for node in root.iter())


def test_wide_latin_identifiers_are_wrapped_conservatively_without_losing_characters():
    from triz.separation_application_diagrams import wrap
    raw='WMWMwm@%'*100
    lines=wrap(raw,184,16)
    assert ''.join(lines)==raw
    assert all(len(line)*16*1.08<=184 for line in lines)


@pytest.mark.parametrize('kind', list(K.separation()))
def test_long_korean_english_and_tags_are_escaped_wrapped_and_not_truncated(kind):
    app, contradiction, solution = example(kind)
    korean = '확인되지 않은 실제 작동 조건과 저장된 실험 계획을 끝까지 보존한다. '*24
    english = 'UnbrokenLongEngineeringIdentifierWithoutSpaces0123456789'*12
    hostile = '<script>alert("x")</script><img src=x onerror="alert(1)"> & <foreignObject>unsafe</foreignObject>'
    app.update(title=hostile, how=korean+english, idea=english, mechanism=hostile,
               conditions=[korean,hostile], validation_test=korean)
    contradiction.update(state_a=korean, reason_a=english, state_b=hostile, reason_b=korean)
    solution.update(title=hostile+english, one_liner=english, working_principle=korean)
    root = xml(render_application(app, contradiction=contradiction, solution=solution))
    assert english in field_text(root,'application.how')
    assert korean.strip() in field_text(root,'application.how')
    assert hostile in field_text(root,'application.mechanism')
    assert not any(node.tag.rsplit('}',1)[-1] in ('script','img','image','foreignObject') for node in root.iter())
    assert not any(key.lower().startswith('on') for node in root.iter() for key in node.attrib)
    width,height = map(float,root.get('viewBox').split()[2:])
    assert height > 3000
    for node in root.iter():
        if node.get('class') != 'separation-application-node':
            continue
        x,y,w,h = [float(node.get('data-'+key)) for key in ('x','y','width','height')]
        assert x >= 0 and y >= 0 and x+w <= width and y+h <= height
        for item in node.iter():
            if item.tag.endswith('text'):
                assert y < float(item.get('y')) < y+h
                assert all(line for line in item.itertext())
