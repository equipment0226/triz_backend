"""Source snapshot and prompt-contract checks; no model or physical validation."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from triz import knowledge as K
from triz import prompts_registry as P
from triz import separation_contract as S


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ('https://wiki.matriz.org/docs/triz/problem-solving-tools-5890/'
          'contradictions/physical-contradiction-6056/'
          'algorithm-for-resolving-physical-contradictions/')
VERSION = 'matriz-pc-7-2026-09-29'
# Independent expected mapping transcribed from the task's source contract,
# preserving the order shown in the inspected MATRIZ sections.
EXPECTED = {
    'SPACE': [1, 2, 3, 7, 4, 17],
    'TIME': [9, 10, 11, 15, 34],
    'CONDITION': [3, 17, 19, 31, 32, 40],
    'DIRECTION': [4, 14, 17, 32, 35, 40],
    'SYSTEM_LEVEL': [1, 5, 12, 33],
    'SATISFY': [13, 28, 35, 36, 37, 38, 39],
    'BYPASS': [],
}
SECTIONS = {
    'SPACE': 'Separating in space',
    'TIME': 'Separating in time',
    'CONDITION': 'Separating in relation (conditions)',
    'DIRECTION': 'Separating in direction',
    'SYSTEM_LEVEL': 'Separating at the system level',
    'SATISFY': 'Satisfying the contradictory demands',
    'BYPASS': 'Bypassing the contradictory demands',
}
LEGACY = {
    'TIME': {'name_ko': '시간 분리', 'question': '상반된 두 상태를 서로 다른 시간에 만족시킬 수 있는가?',
             'principles': [9, 10, 11, 15, 34]},
    'SPACE': {'name_ko': '공간 분리', 'question': '상반된 두 상태를 서로 다른 위치·부분에서 만족시킬 수 있는가?',
              'principles': [1, 2, 3, 4, 5, 17]},
    'CONDITION': {'name_ko': '조건 분리', 'question': '특정 조건(온도·하중·속도·상태)에서만 다르게 거동하게 할 수 있는가?',
                  'principles': [3, 17, 19, 31, 32, 40]},
    'SYSTEM_LEVEL': {'name_ko': '시스템 수준 분리', 'question': '부분에서는 A, 전체에서는 B가 성립하게 할 수 있는가? 상위시스템 전이 또는 역시스템은?',
                     'principles': [1, 5, 12, 33]},
}


def test_exact_seven_approaches_and_source_ordered_principles():
    catalog = K.separation()
    assert list(catalog) == list(EXPECTED)
    assert {kind: row['principles'] for kind, row in catalog.items()} == EXPECTED
    assert {kind: row['family'] for kind, row in catalog.items()} == {
        **{kind: 'SEPARATE' for kind in list(EXPECTED)[:5]},
        'SATISFY': 'SATISFY', 'BYPASS': 'BYPASS',
    }
    assert 24 not in catalog['SATISFY']['principles']
    assert 30 not in catalog['SATISFY']['principles']
    assert catalog['BYPASS']['selection_policy'] == 'UNRESTRICTED'
    assert all(row['selection_policy'] == 'RECOMMENDED_FIRST'
               for kind, row in catalog.items() if kind != 'BYPASS')


def test_standard_principle_number_names_were_not_reassigned():
    assert K.principle(7)['name_en'] == 'Nested doll'
    assert K.principle(4)['name_en'] == 'Asymmetry'
    assert K.principle(5)['name_en'] == 'Merging'
    assert set(K.principles()) == {str(i) for i in range(1, 41)}


def test_source_sections_access_date_and_internal_snapshot_are_per_entry():
    for kind, row in K.separation().items():
        assert row['source_url'] == SOURCE
        assert row['source_section'] == SECTIONS[kind]
        assert row['source_accessed_on'] == '2026-09-29'
        assert row['catalog_version'] == VERSION
        for field in ('name_ko', 'name_en', 'question', 'description'):
            assert isinstance(row[field], str) and row[field].strip()
        assert isinstance(row['principles'], list)


def test_relation_meaning_and_system_level_without_invented_control_question():
    catalog = K.separation()
    assert catalog['CONDITION']['name_ko'] == '관계(조건) 분리'
    assert '대상' in catalog['CONDITION']['question']
    assert '공식 제어 질문 없음' in catalog['SYSTEM_LEVEL']['question']
    assert '항상 검토' in catalog['SYSTEM_LEVEL']['question']
    assert '?' not in catalog['SYSTEM_LEVEL']['question']
    assert 'SATISFY' not in catalog['SYSTEM_LEVEL']['family']


def test_frozen_legacy_preserves_old_order_names_questions_and_principles():
    path = ROOT / 'triz/knowledge/separation_legacy_v1.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    assert catalog == LEGACY
    assert list(catalog) == ['TIME', 'SPACE', 'CONDITION', 'SYSTEM_LEVEL']
    assert all('catalog_version' not in row for row in catalog.values())
    assert S.legacy_catalog() == LEGACY
    # In particular, legacy SPACE and broad CONDITION must not be rewritten.
    assert catalog['SPACE']['principles'] != K.separation()['SPACE']['principles']
    assert catalog['CONDITION']['name_ko'] != K.separation()['CONDITION']['name_ko']


def test_new_block_contains_canonical_names_definitions_once_and_source():
    block = K.separation_block()
    for kind, row in K.separation().items():
        assert kind in block and row['name_ko'] in block and row['family'] in block
        assert row['source_section'] in block and row['question'] in block
    assert SOURCE in block and VERSION in block
    assert '내부 스냅샷' in block and '공식 판번호 아님' in block
    assert '고정 권장 묶음 없음' in block and '40원리 전체 탐색' in block
    for principle in K.principles().values():
        assert block.count(principle['definition']) == 1


def test_legacy_block_remains_byte_equivalent_to_old_formatter():
    expected = '\n'.join(
        f"- {kind} ({row['name_ko']}): {row['question']}\n   연계 발명원리: "
        + ', '.join(f'{pid}({K.principle_name(pid)})' for pid in row['principles'])
        for kind, row in LEGACY.items())
    assert K.separation_block(catalog=S.legacy_catalog()) == expected
    assert 'BYPASS' not in expected and VERSION not in expected


def test_parallel_rendering_does_not_mutate_cached_or_supplied_catalogs():
    cached = K.separation()
    before = deepcopy(cached)
    supplied = deepcopy(cached)
    with ThreadPoolExecutor(max_workers=4) as pool:
        blocks = list(pool.map(lambda _: K.separation_block(catalog=supplied), range(8)))
    assert all(block == blocks[0] for block in blocks)
    assert cached == before and supplied == before


def test_bypass_can_use_unrestricted_principle24_without_fabricated_recommendations():
    applications = [dict(kind=kind, applicable=False,
                         not_applicable_reason='현재 자원으로 성립하는 메커니즘이 확인되지 않음',
                         supporting_principles=[]) for kind in EXPECTED]
    applications[-1].update(applicable=True, not_applicable_reason='',
        how='중간 매개로 필요한 전달 기능을 보존하여 원래 접촉 모순의 전제를 바꿈',
        title='중간 매개 전달', idea='기존 대상의 필수 기능과 제약을 유지하며 중간 매개로 전달한다.',
        supporting_principles=[24])
    original = deepcopy(applications)
    bound = S.normalize({'applications': applications, 'redefine_hint': ''})
    assert S.check(bound) == []
    assert bound['applications'][-1]['recommended_principles'] == []
    assert bound['applications'][-1]['supporting_principles'] == [24]
    assert bound['applications'][-1]['principle_selection_status'] == 'UNRESTRICTED'
    assert applications == original


@pytest.mark.parametrize('prompt_id,expected', [
    ('P_S4_CONTRADICTIONS', {'target_count', 'restated_problem', 'characteristics',
        'problem_functions', 'contradiction_seeds', 'negative_interactions',
        'param_dictionary', 'min_tc', 'min_pc'}),
    ('P_S5_TRACK_B', {'element', 'parameter', 'state_a', 'reason_a', 'state_b',
        'reason_b', 'scale', 'target_system', 'resources', 'su_fields', 'separation_block'}),
    ('P_S5_ARIZ_PART5', {'part4', 'pc_macro', 'pc_micro', 'sfr_inventory',
        'standards_block', 'separation_block', 'effects_block'}),
])
def test_prompt_placeholder_contracts_are_unchanged(prompt_id, expected):
    assert set(P.VAR.findall(P.raw(prompt_id))) == expected


def test_track_b_checks_seven_approaches_without_forcing_seven_successes():
    prompt = P.raw('P_S5_TRACK_B')
    for kind in EXPECTED:
        assert kind in prompt
    assert '7개 true를 강제하지 않는다' in prompt
    assert '적용 가능한 접근이 하나뿐' in prompt
    assert '2개 미만' not in prompt
    assert '실질적인 결함' in prompt
    assert 'principle_selection_reason' in prompt
    assert '공식 권장 목록을 사용 목록으로 복사하지 않는다' in prompt
    assert 'applications' in prompt and 'redefine_hint' in prompt
    for field in ('mechanism', 'mechanism_key', 'intervention_variable', 'conditions',
                  'strongest_objection', 'validation_test', 'hypothesis_ids'):
        assert field in prompt


# These are semantic counterexamples for the written review instructions.
# The test deliberately verifies the prompt/rubric guardrails, not physical truth.
@pytest.mark.parametrize('counterexample,kind,prompt_guard,rubric_guard', [
    ({'kind': 'BYPASS', 'idea': '사용자가 요구한 밀착 기능과 필수 제약을 삭제한다.'},
     'BYPASS', '상위 목적·필수 기능·승인된 hard constraint를 삭제하지 마라', '요구나 제약 삭제'),
    ({'kind': 'SATISFY', 'idea': '같은 대상·속성·조건에서 A와 not-A가 그냥 동시에 성립한다.'},
     'SATISFY', 'A와 not-A가 설명 없이 동시에 성립한다고 쓰지 마라', 'A/not-A 동시 성립'),
    ({'kind': 'CONDITION', 'how': '대상 관계의 차이 없이 온도만 60도로 바꾼다.'},
     'CONDITION', '단순 온도·하중 임계값 변화만으로 관계 분리라고 판정하지 않는다', '온도 변화만으로 관계 분리'),
])
def test_prompt_and_rubric_address_semantic_counterexamples(
        counterexample, kind, prompt_guard, rubric_guard):
    assert counterexample['kind'] == kind
    prompt = P.raw('P_S5_TRACK_B')
    rubric = yaml.safe_load((ROOT / 'config/rubrics.yaml').read_text(encoding='utf-8'))['R5_B']
    assert prompt_guard in prompt
    assert rubric_guard in ' '.join(item['text'] for item in rubric['criteria'])


def test_r5b_criterion_ids_and_weights_are_preserved():
    rubric = yaml.safe_load((ROOT / 'config/rubrics.yaml').read_text(encoding='utf-8'))['R5_B']
    assert [(row['id'], row['weight']) for row in rubric['criteria']] == [
        ('C1', 0.40), ('C2', 0.35), ('C3', 0.25)]


def test_s4_hints_are_not_whitelist_and_ariz_retains_its_own_output_contract():
    assert '검토를 제한하는 허용 목록이 아니다' in P.raw('P_S4_CONTRADICTIONS')
    prompt = P.raw('P_S5_ARIZ_PART5')
    assert 'steps/ideas 출력과 Part 5의 스텝 코드를 유지' in prompt
    assert 'applications 7행 형식을 추가하지 않는다' in prompt
    for step in ('5.1', '5.2', '5.3', '5.4'):
        assert step in prompt
