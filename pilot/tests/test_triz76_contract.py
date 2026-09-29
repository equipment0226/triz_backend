"""Offline contracts; the independent source review is documented separately."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from triz import knowledge as K, prompts_registry as P, verify


# Transcribed from the primary-source section index, not generated from JSON.
EXPECTED_CODES = """
1.1.1 1.1.2 1.1.3 1.1.4 1.1.5 1.1.6 1.1.7 1.1.8
1.2.1 1.2.2 1.2.3 1.2.4 1.2.5
2.1.1 2.1.2 2.2.1 2.2.2 2.2.3 2.2.4 2.2.5 2.2.6
2.3.1 2.3.2 2.3.3
2.4.1 2.4.2 2.4.3 2.4.4 2.4.5 2.4.6 2.4.7 2.4.8 2.4.9 2.4.10 2.4.11 2.4.12
3.1.1 3.1.2 3.1.3 3.1.4 3.1.5 3.2.1
4.1.1 4.1.2 4.1.3 4.2.1 4.2.2 4.2.3 4.2.4 4.3.1 4.3.2 4.3.3
4.4.1 4.4.2 4.4.3 4.4.4 4.4.5 4.5.1 4.5.2
5.1.1 5.1.2 5.1.3 5.1.4 5.2.1 5.2.2 5.2.3 5.3.1 5.3.2 5.3.3 5.3.4 5.3.5
5.4.1 5.4.2 5.5.1 5.5.2 5.5.3
""".split()
EXPECTED_EFFECT_HINTS = {
    'USEFUL_SUFFICIENT': [],
    'USEFUL_INSUFFICIENT': '1.1.2 1.1.3 1.1.4 1.1.5 1.1.7 2.1.1 2.1.2 2.2.1 2.2.2 2.2.3 2.2.4 2.2.5 2.2.6 2.3.1 2.3.2 2.3.3'.split(),
    'HARMFUL': '1.2.1 1.2.2 1.2.3 1.2.4 1.2.5'.split(),
    'EXCESSIVE': '1.1.6 1.1.8 2.2.1'.split(),
    'MEASUREMENT': '4.1.1 4.1.2 4.1.3 4.2.1 4.2.2 4.2.3 4.2.4 4.3.1 4.3.2 4.3.3 4.4.1 4.4.2 4.4.3 4.4.4 4.4.5 4.5.1 4.5.2'.split(),
    '': [], 'UNKNOWN': [], 'INCOMPLETE': [],
}


def test_catalog_complete_unique_and_each_source_actually_reviewed():
    catalog = K.standards()
    assert [s['code'] for s in catalog] == EXPECTED_CODES
    assert len(set(EXPECTED_CODES)) == 76
    assert Counter(s['code'][0] for s in catalog) == {'1': 13, '2': 23, '3': 6, '4': 17, '5': 17}
    summaries = []
    for item in catalog:
        for field in ('code', 'title_ko', 'description', 'transformation', 'conditions', 'limitations', 'verification_scope', 'notes'):
            assert isinstance(item[field], str) and item[field].strip(), (item['code'], field)
        assert isinstance(item['applicability'], list) and all(isinstance(t, str) for t in item['applicability'])
        assert item['verified'] is True
        review = item['source_review']
        assert review['section'] == item['code'] and review['checked_at'] == '2026-09-29'
        assert review['result'] in ('confirmed', 'corrected')
        assert review['primary_url'].startswith('https://www.altshuller.ru/')
        assert review['summary'] and review['cross_check'] and review['diagram_review']
        assert any(s['section'] == item['code'] and 'altshuller.ru' in s['url'] for s in item['sources'])
        summaries.append(review['summary'])
    assert len(set(summaries)) == 76
    assert len({s['description'] for s in catalog}) == 76
    assert len({s['transformation'] for s in catalog}) == 76


def test_official_subnumbers_are_details_not_parent_codes():
    catalog = {s['code']: s for s in K.standards()}
    for parent, count in [('1.1.8', 2), ('5.1.1', 9)]:
        children = catalog[parent]['substandards']
        assert [c['code'] for c in children] == [f'{parent}.{i}' for i in range(1, count + 1)]
        assert len({c['transformation'] for c in children}) == count
    for parent in catalog.values():
        for child in parent.get('substandards', []):
            assert child['parent_code'] == parent['code']
            assert child['code'].startswith(parent['code'] + '.')
            assert child['code'] not in K.standard_codes()
            assert all(child[k] for k in ('title_ko', 'transformation', 'conditions', 'sources'))
            assert any(s['section'] == child['code'] for s in child['sources'])
        for branch in parent.get('variants', []):
            assert 'code' not in branch  # unnumbered source branches stay unnumbered
            assert all(branch[k] for k in ('title_ko', 'transformation', 'conditions', 'sources'))


@pytest.mark.parametrize('completeness', ['COMPLETE', 'MISSING_S2', 'MISSING_F', 'INCOMPLETE', '', 'UNKNOWN'])
@pytest.mark.parametrize('effect', list(EXPECTED_EFFECT_HINTS))
def test_all_hint_combinations_are_independent_and_stable(completeness, effect):
    expected = (['1.1.1'] if completeness in ('MISSING_S2', 'MISSING_F', 'INCOMPLETE') else []) + EXPECTED_EFFECT_HINTS[effect]
    actual = K.standard_hints(completeness, effect)
    assert actual == expected == K.standard_hints(completeness, effect)
    assert len(actual) == len(set(actual)) and set(actual) <= set(EXPECTED_CODES)


def test_missing_aliases_do_not_infer_effect_or_constraints():
    assert K.SU_TO_TAGS == {'MISSING_S2': ['MISSING_S2', 'INCOMPLETE'],
                           'MISSING_F': ['MISSING_F', 'INCOMPLETE'], 'INCOMPLETE': ['INCOMPLETE']}
    assert K.standard_hints('MISSING_F', '') == ['1.1.1']
    assert '1.1.7' not in K.standard_hints('COMPLETE', 'EXCESSIVE')
    assert K.standard_hints('COMPLETE', 'USEFUL_SUFFICIENT') == []
    assert len(K.standard_hints('COMPLETE', 'MEASUREMENT')) == 17


@pytest.mark.parametrize('limit', [-1, 0, 1, 3, 12])
@pytest.mark.parametrize('effect', ['MEASUREMENT', 'USEFUL_INSUFFICIENT'])
def test_state_anchors_survive_hostile_global_ranking(monkeypatch, limit, effect):
    from triz import effect_catalog
    seen = []
    def reverse_catalog(groups, queries, limit):
        entries = groups[0]['effects']
        seen.extend(entries)
        return list(reversed(entries))[:limit]
    monkeypatch.setattr(effect_catalog, 'select_effects', reverse_catalog)
    result = K.candidate_standards('MISSING_F', effect, limit=limit, required_functions=['functional query'])
    codes = [s['code'] for s in result]
    assert len(codes) == max(0, limit) and len(set(codes)) == len(codes)
    if limit <= 0:
        assert not seen
        return
    assert {e['id'] for e in seen} == set(EXPECTED_CODES)
    assert codes[0] == ('4.1.1' if effect == 'MEASUREMENT' else '1.1.1')
    if limit >= 3:
        assert '1.1.1' in codes
    if limit == 12:
        assert len([code for code in codes if code.startswith('5.')]) == 9
    assert all('source_review' not in e['principle'] and 'http' not in e['principle'] for e in seen)


def test_verified_is_not_relevance_and_fallback_is_explicit(monkeypatch):
    original = deepcopy(K.standards())
    before = K.candidate_standards('COMPLETE', 'UNKNOWN')
    changed = deepcopy(original)
    for s in changed:
        s['verified'] = False
    monkeypatch.setattr(K, 'standards', lambda: changed)
    after = K.candidate_standards('COMPLETE', 'UNKNOWN')
    assert [s['code'] for s in before] == [s['code'] for s in after]
    assert all(s['candidate_basis'] == ['catalog_exploration'] for s in after)
    assert all(s['candidate_status'] == 'UNCONFIRMED' for s in after)
    assert [s['code'] for s in K.candidate_standards('COMPLETE', 'HARMFUL')] == EXPECTED_EFFECT_HINTS['HARMFUL']


@pytest.mark.parametrize('code', ['2.4.12', '4.5.2', '5.4.2', '5.5.3'])
def test_late_codes_remain_global_searchable(code):
    item = next(s for s in K.standards() if s['code'] == code)
    actual = K.candidate_standards('COMPLETE', 'USEFUL_INSUFFICIENT', required_functions=[item['title_ko'], item['transformation']])
    assert code in [s['code'] for s in actual]


@pytest.mark.parametrize('parent', ['1.1.8', '5.1.1'])
def test_submethod_search_and_full_selected_detail_render(parent):
    item = next(s for s in K.standards() if s['code'] == parent)
    child = item['substandards'][-1]
    results = K.candidate_standards('COMPLETE', 'UNKNOWN', required_functions=[child['title_ko'], child['transformation']])
    assert parent in [s['code'] for s in results]
    block = K.standards_block([item])
    for sub in item['substandards']:
        assert sub['code'] in block and sub['transformation'] in block and sub['conditions'] in block
    assert item['conditions'] in block and item['limitations'] in block
    assert '조건 충족 미확인' in block and '편집상 공학 검토' in block
    assert item['source_review']['summary'] not in block


def test_parallel_selection_cannot_pollute_cached_catalog():
    before = json.dumps(K.standards(), ensure_ascii=False, sort_keys=True)
    def select_and_mutate(_):
        result = K.candidate_standards('INCOMPLETE', 'MEASUREMENT')
        result[0]['conditions'] = 'polluted'
        result[0]['sources'].clear()
        result[0]['source_review']['summary'] = 'polluted'
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(select_and_mutate, range(12)))
    assert json.dumps(K.standards(), ensure_ascii=False, sort_keys=True) == before
    assert all('candidate_basis' not in s for s in K.standards())


@pytest.mark.parametrize('code', ['1.1.8.1', '5.1.1.9', '9.9.9'])
def test_subcodes_and_invalid_codes_rejected_without_parent_coercion(code):
    from triz.catalog_binding import bind_standard
    data = {'applications': [{'standard_code': code, 'idea': 'submethod must be in text'}]}
    bound = bind_standard(data, K.standards())
    assert bound['applications'][0]['standard_code'] == code
    assert verify.check_standards(bound, EXPECTED_CODES)


def test_prompt_variable_output_and_call_contract_remain_compatible():
    text = P.raw('P_S5_TRACK_C')
    assert set(P.VAR.findall(text)) == {'s1', 's2', 'field', 'completeness', 'effect', 'target_system', 'resources', 'standards_block'}
    assert '최대 6개' in text and '빈 applications' in text and 'resulting_model' in text
    assert '5.1.1.8' in text and 'standard_code' in text and '미확인' in text
    assert 'S2-F-S1로 강제' in text


def test_legacy_regeneration_refuses_without_modifying_canonical_file(monkeypatch, tmp_path):
    script = Path(__file__).resolve().parents[1] / 'scripts/complete_standards.py'
    spec = importlib.util.spec_from_file_location('legacy_standards_generator', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    local_script = tmp_path / 'pilot/scripts/complete_standards.py'
    target = tmp_path / 'pilot/triz/knowledge/standards_76.json'
    target.parent.mkdir(parents=True)
    contents = json.dumps({'standards': K.standards()}, ensure_ascii=False)
    target.write_text(contents, encoding='utf-8')
    monkeypatch.setattr(module, '__file__', str(local_script))
    with pytest.raises(SystemExit, match='Refusing to overwrite'):
        module.build()
    assert target.read_text(encoding='utf-8') == contents
