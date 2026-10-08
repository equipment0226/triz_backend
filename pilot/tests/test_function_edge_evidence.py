"""Function hypotheses must survive typed commit, persistence and repair aliases."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from triz import analysis_checks, store
from triz.schema import FunctionEdge, GlobalState


def artifact():
    return {'components': [
        {'name': 'rules', 'level': 'TARGET', 'role': 'defines allocations'},
        {'name': 'package', 'level': 'PRODUCT', 'role': 'compensation allocation'}],
        'function_edges': [
            {'subject': 'rules', 'action': 'sets', 'object': 'package', 'rank': 'BASIC',
             'kind': 'USEFUL', 'level': 'INSUFFICIENT', 'parameter_affected': 'allocation amount',
             'notes': 'Hypothesis: the allocation mechanism requires confirmation.',
             'evidence_status': 'HYPOTHESIS', 'evidence_refs': ['user_query: existing rules']}
        ], 'interaction_cells': [], 'mermaid': ''}


def test_hypothesis_survives_structural_check_typed_state_and_storage(state):
    data = artifact()
    before = deepcopy(data)
    assert not analysis_checks.function_model(data)
    state.analysis.function_edges = [FunctionEdge.model_validate(row) for row in data['function_edges']]
    expected = state.analysis.function_edges[0].model_dump()
    assert expected['notes'] == data['function_edges'][0]['notes']
    assert expected['evidence_status'] == 'HYPOTHESIS'
    assert expected['evidence_refs'] == ['user_query: existing rules']
    assert GlobalState.model_validate_json(state.model_dump_json()).analysis.function_edges[0].model_dump() == expected
    store.save_state(state)
    assert store.load_state(state.run_id).analysis.function_edges[0].model_dump() == expected
    assert data == before


@pytest.mark.parametrize('extra, expected', [
    ({'note': 'hypothesis only'}, 'hypothesis only'),
    ({'notes': '', 'note': 'hypothesis only'}, 'hypothesis only'),
    ({'notes': 'mechanism uncertain', 'note': 'needs measurement'}, 'mechanism uncertain\nneeds measurement'),
    ({'notes': 'same', 'note': 'same'}, 'same'),
])
def test_note_alias_is_preserved_under_canonical_notes(extra, expected):
    source = dict(subject='rules', action='sets', object='package', **extra)
    before = deepcopy(source)
    edge = FunctionEdge.model_validate(source)
    assert edge.notes == expected
    serialized = edge.model_dump()
    assert serialized['notes'] == expected and 'note' not in serialized
    assert FunctionEdge.model_validate(serialized).notes == expected
    assert source == before


def test_legacy_function_edges_do_not_need_new_fields_or_become_observed():
    data = artifact()
    row = data['function_edges'][0]
    for key in ('notes', 'evidence_status', 'evidence_refs'):
        row.pop(key)
    assert not analysis_checks.function_model(data)
    edge = FunctionEdge.model_validate(row)
    assert edge.notes == '' and edge.evidence_refs == [] and edge.evidence_status == 'HYPOTHESIS'


@pytest.mark.parametrize('status', ['OBSERVED', 'HYPOTHESIS', 'DERIVED'])
def test_explicit_evidence_status_round_trips(status):
    edge = FunctionEdge(evidence_status=status, notes='source qualification', evidence_refs=['user_answer: item 1'])
    assert FunctionEdge.model_validate_json(edge.model_dump_json()).model_dump() == edge.model_dump()


@pytest.mark.parametrize('field,value', [('evidence_status', 'FACT'), ('evidence_status', None),
                                       ('evidence_refs', 'source text'), ('evidence_refs', [123])])
def test_invalid_explicit_evidence_fields_fail_before_typed_commit(field, value):
    data = artifact()
    data['function_edges'][0][field] = value
    assert any('function_edges[0].' + field in message for message in analysis_checks.function_model(data))
    with pytest.raises(ValidationError):
        FunctionEdge.model_validate(data['function_edges'][0])


def test_evidence_defaults_are_not_shared_between_edges():
    first, second = FunctionEdge(), FunctionEdge()
    first.evidence_refs.append('source')
    assert second.evidence_refs == []
