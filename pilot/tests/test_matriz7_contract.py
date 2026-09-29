from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json

import pytest

from triz import knowledge as K, separation_contract as SC, verify
from triz.ax import runtime, WORKFLOW
from triz.ax.contracts import digest
from matriz7_fixtures import KINDS, payload, legacy_bundle, legacy_payload


def test_valid_reviews_and_one_applicable_need_no_automatic_redefinition():
    for active in [(), ('TIME',), KINDS]:
        data = payload(active)
        normalized = SC.normalize(data)
        assert verify.check_separation(normalized) == []
        assert normalized['redefine_hint'] == ''
        assert sum(a['applicable'] is True for a in normalized['applications']) == len(active)


@pytest.mark.parametrize('data', [None, [], 'text', True, 0, {}, {'applications':None},
                                {'applications':{}}, {'applications':'text'}, {'applications':[None]}])
def test_malformed_structure_is_not_deleted_or_fabricated(data):
    before = deepcopy(data)
    normalized = SC.normalize(data)
    assert data == before
    assert normalized == data
    assert all(i.startswith('FATAL-') for i in verify.check_separation(normalized))
    assert verify.check_separation(normalized)


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'unknown', 'alias_duplicate', 'object_kind', 'list_kind', 'number_kind'])
def test_exact_canonical_coverage(defect):
    data = payload()
    if defect == 'missing': data['applications'].pop()
    if defect == 'duplicate': data['applications'].append(deepcopy(data['applications'][0]))
    if defect == 'unknown': data['applications'][0]['kind'] = 'NEW_TRACK'
    if defect == 'alias_duplicate': data['applications'].append(dict(data['applications'][2],kind='RELATION_CONDITIONS'))
    if defect == 'object_kind': data['applications'][0]['kind'] = {}
    if defect == 'list_kind': data['applications'][0]['kind'] = []
    if defect == 'number_kind': data['applications'][0]['kind'] = 7
    assert verify.check_separation(SC.normalize(data))


@pytest.mark.parametrize('alias', ['RELATION', 'RELATION_CONDITIONS', ' relation '])
def test_explicit_relation_alias_preserves_seven_kinds(alias):
    data = payload()
    data['applications'][2]['kind'] = alias
    normalized = SC.normalize(data)
    assert normalized['applications'][2]['kind'] == 'CONDITION'
    assert verify.check_separation(normalized) == []
    assert data['applications'][2]['kind'] == alias


@pytest.mark.parametrize('value', ['false', 'true', None, 0, 1, [], {}])
def test_applicable_requires_a_real_boolean(value):
    data = payload()
    data['applications'][0]['applicable'] = value
    assert any('bool' in e for e in verify.check_separation(SC.normalize(data)))


@pytest.mark.parametrize('field', ['how', 'title', 'idea'])
@pytest.mark.parametrize('value', ['', ' ', None, [], 1])
def test_applicable_proposal_requires_real_text(field, value):
    data = payload()
    data['applications'][1][field] = value
    assert verify.check_separation(data)


@pytest.mark.parametrize('value', ['', ' ', None, [], 1])
def test_not_applicable_requires_reason(value):
    data = payload()
    data['applications'][0]['not_applicable_reason'] = value
    assert verify.check_separation(data)


@pytest.mark.parametrize('actual', [None, '9', 9, {}, [True], [False], [0], [41], [-1], ['9'], [9.0], [{}], [[]], [9, 9]])
def test_principle_ids_are_real_unique_catalog_integers(actual):
    data = payload()
    data['applications'][1]['supporting_principles'] = actual
    assert verify.check_separation(SC.normalize(data))


def test_recommended_extended_unrestricted_and_unspecified_are_distinct():
    data = payload(('SPACE','TIME','SATISFY','BYPASS'))
    apps = {a['kind']:a for a in data['applications']}
    apps['SPACE']['supporting_principles'] = [24]
    apps['SPACE']['principle_selection_reason'] = 'An intermediary provides the required spatial boundary.'
    apps['SATISFY']['supporting_principles'] = []
    apps['SATISFY']['principle_selection_reason'] = 'Principle identity remains unconfirmed; no ID invented.'
    normalized = SC.normalize(data)
    assert not verify.check_separation(normalized)
    normalized = {a['kind']:a for a in normalized['applications']}
    assert normalized['SPACE']['principle_selection_status'] == 'EXTENDED'
    assert 24 not in normalized['SPACE']['recommended_principles']
    assert normalized['TIME']['principle_selection_status'] == 'RECOMMENDED'
    assert normalized['SATISFY']['principle_selection_status'] == 'UNSPECIFIED'
    assert normalized['BYPASS']['principle_selection_status'] == 'UNRESTRICTED'
    assert normalized['BYPASS']['recommended_principles'] == []
    assert normalized['BYPASS']['supporting_principles'] == [24]
    apps['SPACE'].pop('principle_selection_reason')
    assert verify.check_separation(SC.normalize(data))
    apps['SPACE']['supporting_principles'] = [1]
    apps['SATISFY'].pop('principle_selection_reason')
    assert verify.check_separation(SC.normalize(data))


def test_model_provenance_does_not_replace_server_catalog_or_fake_pc_identity():
    data = payload()
    data['applications'][0].update(catalog_version='forged', catalog_sources=[{'url':'forged'}],
        recommended_principles=[40], approach_name='wrong', approach_family='BYPASS',
        principle_selection_policy='UNRESTRICTED', source_pc_id='invented-pc')
    normalized = SC.normalize(data)
    app = normalized['applications'][0]
    assert 'source_pc_id' not in app
    assert app['catalog_version'] == K.separation()['SPACE']['catalog_version']
    assert app['recommended_principles'] == [1,2,3,7,4,17]
    assert app['supporting_principles'] == []
    assert app['catalog_sources'][0]['url'] == K.separation()['SPACE']['source_url']
    assert not verify.check_separation(normalized)
    assert verify.check_separation(data)  # unbound forged provenance is rejected


def test_parallel_normalization_cannot_mutate_input_or_catalog():
    catalog = K.separation()
    data = payload()
    before = json.dumps([data, catalog], sort_keys=True)
    def normalize_and_mutate(_):
        result = SC.normalize(data, catalog=catalog)
        result['applications'][0]['catalog_sources'].clear()
        result['applications'][0]['recommended_principles'].append(40)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(normalize_and_mutate,range(12)))
    assert json.dumps([data,catalog],sort_keys=True) == before


@pytest.mark.parametrize('field,bad', [
    ('hypothesis_ids', 17), ('hypothesis_ids', [17]), ('uses_resources', 'bad'),
    ('uses_resources', [{}]), ('feasibility_hint', 'UNCERTAIN'), ('feasibility_hint', []),
    ('mechanism', None), ('mechanism_key', 1), ('intervention_variable', None),
    ('strongest_objection', {}), ('self_rebuttal', []), ('validation_test', False),
])
def test_raw_idea_field_errors_are_repaired_before_construction(field, bad):
    data = payload()
    data['applications'][1][field] = bad
    issues = verify.check_separation(SC.normalize(data))
    assert any(field in issue and issue.startswith('FATAL-') for issue in issues)


def test_new_bundle_pins_catalog_and_digest_but_never_mutates_old_bundle(state):
    bundle = runtime.bundle()
    without_id = {k:v for k,v in bundle.items() if k != 'bundle_id'}
    assert bundle['bundle_id'] == 'bundle-'+digest(without_id)
    assert tuple(bundle['separation_catalog']) == KINDS
    altered = deepcopy(without_id)
    altered['separation_catalog']['SPACE']['description'] += ' change'
    assert digest(altered) != digest(without_id)
    state.scratch.update(workflow_version=WORKFLOW,ax_bundle=bundle)
    before = deepcopy(bundle)
    selected = SC.catalog_for(state)
    selected['SPACE']['principles'].clear()
    assert bundle == before and K.separation()['SPACE']['principles']
    old = legacy_bundle()
    state.scratch['ax_bundle'] = old
    old_before = deepcopy(old)
    catalog = SC.catalog_for(state)
    assert tuple(catalog) == ('TIME','SPACE','CONDITION','SYSTEM_LEVEL')
    data = SC.normalize(legacy_payload(),catalog=catalog)
    assert not verify.check_separation(data,catalog=catalog)
    assert len(data['applications']) == 4
    assert {a['catalog_version'] for a in data['applications']} == {SC.LEGACY_VERSION}
    assert SC.display_name(data['applications'][2]) == '조건 분리'
    assert old == old_before


@pytest.mark.parametrize('bad', [None, {}, [], {'SPACE':{}}, {'SPACE':'bad'}])
def test_invalid_new_snapshot_never_silently_falls_back_to_four(state, bad):
    state.scratch.update(workflow_version=WORKFLOW,ax_bundle=runtime.bundle())
    state.scratch['ax_bundle']['separation_catalog'] = bad
    with pytest.raises(ValueError,match='Invalid pinned'):
        SC.catalog_for(state)


def test_non_ax_explicit_generation_is_new_but_legacy_render_is_read_only(state):
    old = {'kind':'CONDITION','idea':'Stored temperature threshold meaning','supporting_principles':[19]}
    state.solve.separation_apps = [deepcopy(old)]
    assert SC.display_name(state.solve.separation_apps[0]) == '조건 분리'
    assert tuple(SC.catalog_for(state)) == KINDS
    assert state.solve.separation_apps == [old]
