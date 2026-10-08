"""Read-only reference validation, including observed Korean prose citations."""
from copy import deepcopy

from triz.analysis_checks import unknown_constraint_references


def test_known_references_and_unrelated_constraint_like_labels_pass():
    data = {'text': 'CON-abcd1234으로 준수하며 CON-abcd1234·CON-12345678을 확인',
            'CON-deadbeef': 'keys are not cited values',
            'other': ['CON-3', 'CON-XXXXXXXX', 'PREFIX-CON-deadbeef', 'CON-deadbeef-variant']}
    assert not unknown_constraint_references(data, ['CON-abcd1234', 'CON-12345678'])


def test_unknown_ids_in_nested_values_are_reported_once_without_mutation():
    data = {'ifr': {'constraint_conflicts': ['CON-42480556: 위반하지 않음',
        'CON-42480556을 준수한다', 'CON-38a5cb0b(이송 속도 저하 없음)']}}
    before = deepcopy(data)
    issues = unknown_constraint_references(data, ['CON-38a5bc0b'])
    assert len(issues) == 2
    assert '$.ifr.constraint_conflicts[0]' in issues[0]
    assert 'CON-42480556' in issues[0]
    assert 'CON-38a5cb0b' in issues[1]
    assert data == before


def test_declared_ids_require_explicit_constraint_discovery_exemption():
    data = {'constraints': [{'id': 'CON-abcd1234', 'statement': 'candidate'}],
            'taboo': [{'constraint_id': 'CON-abcd1234'}]}
    assert unknown_constraint_references(data, [])
    assert not unknown_constraint_references(data, [], declared_constraint_ids=['CON-abcd1234'])
    data['taboo'].append({'constraint_id': 'CON-deadbeef'})
    assert unknown_constraint_references(data, [], declared_constraint_ids=['CON-abcd1234'])


def test_inspection_limits_cannot_turn_unexamined_references_into_a_pass():
    assert unknown_constraint_references({'large': ['known', 'CON-deadbeef']}, [], max_nodes=2)
    assert unknown_constraint_references({'text': 'x' * 50 + ' CON-deadbeef'}, [], max_chars=10)
    issues = unknown_constraint_references(['CON-deadbeef', 'CON-abcd1234'], [], max_issues=1)
    assert len(issues) == 2 and '너무 많다' in issues[-1]
    cyclic = []
    cyclic.append(cyclic)
    assert unknown_constraint_references(cyclic, [], max_nodes=5)


def test_numeric_and_null_json_values_do_not_raise():
    assert not unknown_constraint_references({'items': [None, False, 42, 1.5]}, [])
