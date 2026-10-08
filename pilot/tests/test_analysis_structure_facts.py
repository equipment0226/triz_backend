"""Regression tests for misleading counts and unrepairable schema diagnostics."""
from copy import deepcopy
import json

from triz import analysis_checks as checks, verify


def model():
    return {'components': [
        {'name': 'controller', 'level': 'TARGET', 'role': 'calculates motion'},
        {'name': 'stage', 'level': 'PRODUCT', 'role': 'positioned assembly'}],
        'function_edges': [
            {'subject': 'controller', 'action': 'positions', 'object': 'stage',
             'kind': 'USEFUL', 'level': 'INSUFFICIENT', 'rank': 'BASIC', 'parameter_affected': 'position'},
            {'subject': 'controller', 'action': 'damps', 'object': 'stage',
             'kind': 'USEFUL', 'rank': 'CORRECTIVE', 'parameter_affected': 'vibration'}]}


def test_shared_subject_and_product_object_do_not_change_actual_basic_count():
    data = model()
    before = deepcopy(data)
    facts = checks.artifact_structure_facts('R3_FUNC', data)
    assert facts['basic_count'] == 1 and facts['basic_indexes'] == [0]
    assert facts['basic_functions'][0] == {
        'index': 0, 'subject': 'controller', 'action': 'positions', 'object': 'stage',
        'kind': 'USEFUL', 'level': 'INSUFFICIENT', 'rank': 'BASIC', 'parameter_affected': 'position'}
    assert facts['product_components'] == [{'index': 1, 'name': 'stage'}]
    assert facts['unknown_endpoint_count'] == 0
    assert data == before


def test_facts_report_harmful_basic_and_missing_endpoint_without_endorsing_or_fabricating():
    data = model()
    data['function_edges'][0].update(kind='HARMFUL', object='stage precision')
    facts = checks.artifact_structure_facts('R3_FUNC', data)
    assert facts['basic_count'] == 1
    assert facts['basic_functions'][0]['kind'] == 'HARMFUL'
    assert facts['unknown_endpoints'] == [{'index': 0, 'field': 'object', 'value': 'stage precision'}]
    assert len(data['components']) == 2


def test_missing_or_malformed_artifact_facts_do_not_crash_or_infer_basic():
    assert checks.artifact_structure_facts('R3_FUNC', []) == {'artifact_is_object': False}
    facts = checks.artifact_structure_facts('R3_FUNC', {'components': {}, 'function_edges': [None, {'object': {}}]})
    assert facts['basic_count'] == 0 and not facts['components_is_array']
    assert facts['unknown_endpoint_count'] == 2
    assert all(row['value'] is None for row in facts['unknown_endpoints'])
    assert checks.artifact_structure_facts('R4_IFR', object()) == {}


def test_structure_facts_are_bounded_while_counts_remain_exact():
    data = model()
    data['function_edges'] = [dict(data['function_edges'][0], action='a' * 10000)] * 100
    facts = checks.artifact_structure_facts('R3_FUNC', data)
    assert facts['basic_count'] == 100
    assert len(facts['basic_functions']) == 40
    assert facts['truncated_lists'] == ['basic_functions']
    assert len(json.dumps(facts, ensure_ascii=False)) < 22000


def test_ceca_repair_receives_exact_enum_field_and_graph_errors_in_same_attempt():
    data = {'nodes': [
        {'id': 'N1', 'text': 'loss', 'node_type': 'TARGET_DISADVANTAGE', 'parents': ['N2'],
         'evidence_status': 'OBSERVED', 'evidence_refs': ['user']},
        {'id': 'N2', 'text': 'cause', 'node_type': 'INTERMEDIATE_DISADVANTAGE', 'parents': ['N1'],
         'evidence_status': 'HYPOTHESIS', 'evidence_refs': [], 'falsification_test': 'measure response'},
        {'id': 'N3', 'text': 'disconnected root', 'node_type': 'ROOT_CAUSE', 'parents': [],
         'evidence_status': 'HYPOTHESIS', 'evidence_refs': [], 'falsification_test': 'measure cause'}]}
    before = deepcopy(data)
    issues = verify.check_ceca(data)
    assert any('nodes[1].node_type' in issue and "'INTERMEDIATE'" in issue for issue in issues)
    assert any('순환 참조' in issue for issue in issues)
    assert any('연결되지 않은 원인' in issue for issue in issues)
    assert len(issues) == len(set(issues))
    assert data == before  # No enum synonym repair, parent reversal or invented edges.


def test_resource_schema_error_names_the_invalid_category_and_allowed_values():
    issues = checks.resources({'resources': [{'name': 'waste heat', 'category': 'ENERGY',
        'quantity_note': 'measured', 'where': 'WASTE', 'availability': 'FREE',
        'usable_for': ['warming'], 'blocked_by_constraint': False}]})
    assert any('resources[0].category' in issue and "'FIELD'" in issue for issue in issues)


def test_function_schema_and_missing_references_remain_strict():
    data = model()
    data['function_edges'][0]['object'] = 'stage precision'
    data['function_edges'][0]['action'] = '관리한다'
    data['function_edges'][0]['level'] = 'NORMAL'
    data['function_edges'][1]['level'] = 'INSUFFICIENT'
    data['interaction_cells'] = []
    issues = checks.function_model(data)
    assert any('stage precision' in issue and '컴포넌트 목록에 없다' in issue for issue in issues)
    assert any('DET-05d' in issue for issue in issues)
