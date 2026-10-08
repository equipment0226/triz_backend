"""Offline regressions for observed analysis failures and downstream propagation."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_checks as checks, digest, nodes, verify
from triz.context import AbortRun, RunContext
from triz.schema import Component, FunctionEdge
from triz.settings import settings
from triz.verification_contract import effective_rubric


def functional_model():
    return {
        'components': [
            {'name': 'tank', 'level': 'TARGET', 'role': 'contains liquid'},
            {'name': 'liquid', 'level': 'PRODUCT', 'role': 'stored product'},
            {'name': 'ambient air', 'level': 'ENVIRONMENT', 'role': 'external heat source'},
        ],
        'function_edges': [
            {'subject': 'tank', 'action': 'contains', 'object': 'liquid',
             'parameter_affected': 'retained quantity', 'kind': 'USEFUL', 'rank': 'BASIC', 'level': 'NORMAL'},
            {'subject': 'ambient air', 'action': 'heats', 'object': 'liquid',
             'parameter_affected': 'temperature', 'kind': 'HARMFUL', 'rank': 'AUXILIARY', 'level': 'NORMAL'},
        ], 'interaction_cells': [], 'mermaid': '',
    }


def commit_function(state, data):
    state.analysis.components = [Component.model_validate(row) for row in data['components']]
    state.analysis.function_edges = [FunctionEdge.model_validate(row) for row in data['function_edges']]


def test_useful_storage_function_passes_but_heat_intrusion_basic_must_repair():
    data = functional_model()
    assert not verify.check_function_model(data)
    data['function_edges'][0]['rank'] = 'AUXILIARY'
    data['function_edges'][1]['rank'] = 'BASIC'
    assert any('FATAL-BASIC' in item for item in verify.check_function_model(data))


@pytest.mark.parametrize('data', [{}, {'name': 'single component'}, {'components': [{'name': 'Li+'}, {}]},
                                 {'components': [], 'function_edges': []}])
def test_observed_partial_outputs_cannot_be_committed(data):
    assert verify.check_function_model(data)


@pytest.mark.parametrize('change', ['missing_basic', 'two_basics', 'harmful_basic', 'unknown_endpoint', 'no_parameter'])
def test_ifr_cannot_start_from_invalid_saved_basic(state, monkeypatch, change):
    data = functional_model()
    if change == 'missing_basic':
        data['function_edges'][0]['rank'] = 'AUXILIARY'
    elif change == 'two_basics':
        data['function_edges'][1]['rank'] = 'BASIC'
    elif change == 'harmful_basic':
        data['function_edges'][0]['kind'] = 'HARMFUL'
    elif change == 'unknown_endpoint':
        data['function_edges'][0]['object'] = 'not in model'
    else:
        data['function_edges'][0]['parameter_affected'] = ''
    commit_function(state, data)
    def forbidden(*args, **kwargs):
        pytest.fail('Invalid saved BASIC reached a downstream model call')
    monkeypatch.setattr(agent, 'run_agent', forbidden)
    with pytest.raises(AbortRun):
        nodes.s4_define(RunContext(state))


@pytest.mark.parametrize('malformation', ['harmful_basic', 'single_component'])
def test_repaired_function_is_revalidated_then_consumed_by_ifr(state, monkeypatch, malformation):
    good = functional_model()
    bad = deepcopy(good)
    bad['function_edges'][0]['rank'] = 'AUXILIARY'
    bad['function_edges'][1]['rank'] = 'BASIC'
    if malformation == 'single_component':
        bad = {'name': 'tank', 'level': 'TARGET', 'role': 'contains liquid'}
    rb = effective_rubric(settings, 'R3_FUNC')
    verdict = {'verdict': 'PASS', 'per_criterion': [{'id': row['id'], 'score': 1} for row in rb['criteria']]}
    responses = [bad, good, verdict]
    from triz.analysis_semantic_gate import RULES
    responses.append({'checks': [{'id': key, 'status': 'PASS', 'reason': 'offline valid storage function', 'findings': []}
                                 for key in RULES['R3_FUNC']]})
    calls = []
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data=responses.pop(0), meta={}, tokens_in=3, tokens_out=5,
                               cost_usd=0, model='offline', text='')
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    fixed = agent.run_agent(RunContext(state), node='s3_function_model', stage='S3',
        label='Function analysis', agent_id='system_analyst', prompt_id='P_S3_FUNCTION_MODEL',
        rubric_id='R3_FUNC', checker=verify.check_function_model, repair_attempts=1)
    commit_function(state, fixed)
    assert state.steps[-1].status == 'OK'
    assert [v['verdict'] for v in state.steps[-1].verdicts] == ['REVISE', 'PASS']
    assert 'FATAL-' in calls[1]['user']
    assert 'tank' in digest.basic_function(state) and 'heats' not in digest.basic_function(state)
    assert not responses


def test_unrepaired_harmful_basic_stops_without_mutating_analysis(state, monkeypatch):
    original = state.analysis.model_dump()
    bad = functional_model()
    bad['function_edges'][0]['kind'] = 'HARMFUL'
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **k: SimpleNamespace(
        data=deepcopy(bad), meta={}, tokens_in=1, tokens_out=1, cost_usd=0, model='offline', text=''))
    with pytest.raises(AbortRun):
        agent.run_agent(RunContext(state), node='s3_function_model', stage='S3', label='Function',
                        agent_id='system_analyst', prompt_id='P_S3_FUNCTION_MODEL',
                        rubric_id='R3_FUNC', checker=verify.check_function_model, repair_attempts=1)
    assert state.steps[-1].status == 'FAILED'
    assert state.analysis.model_dump() == original


def test_missing_nine_windows_and_inconsistent_sufield_are_repairable():
    assert checks.nine_windows({'cells': {}, 'insights': []})
    base = {'label': 'heat transfer', 's1': 'liquid', 's2': 'air', 'field': 'thermal',
            'completeness': 'COMPLETE', 'effect': 'USEFUL_INSUFFICIENT'}
    assert not checks.sufields({'su_fields': [base]})
    assert checks.sufields({'su_fields': [dict(base, completeness='MISSING_F')]})


def test_absence_is_recorded_without_fake_resources_or_trimming():
    assert not checks.resources({'resources': [], 'unavailable_reason': 'No resources confirmed in the supplied boundary'})
    assert checks.resources({'resources': []})
    assert not checks.trimming({'trimming': []}, ['tank'])
    assert checks.trimming({'trimming': [{'target_component': 'tank', 'replaced_function': 'contains liquid',
        'rule': 'C', 'replacement_carrier': '', 'feasibility': 'HIGH', 'risk_note': 'unverified'}]}, ['tank'], ['tank'])


def test_generated_constraints_cannot_overwrite_confirmed_requirements():
    row = {'statement': 'No downtime', 'rationale': 'Unconfirmed operating assumption', 'hard': False, 'confidence': .5}
    assert not checks.discovered_constraints({'constraints': [row], 'taboo': []})
    assert checks.discovered_constraints({'constraints': [dict(row, hard=True)], 'taboo': []})
    assert checks.discovered_constraints({'constraints': [], 'taboo': [
        {'item': 'shutdown', 'why': 'stated rule', 'confirmed': True, 'constraint_id': 'missing'}]}, ['actual'])


def test_key_selection_cannot_retain_dropped_or_unknown_contradictions():
    kp = {'title': 'retain liquid', 'contradiction_ids': ['TC1'], 'why_key': 'initial loss', 'impact': 4, 'tractability': 3}
    assert not checks.key_problems({'key_problems': [kp], 'dropped': [{'id': 'TC2', 'reason': 'secondary'}]}, ['TC1','TC2'])
    assert checks.key_problems({'key_problems': [kp], 'dropped': [{'id': 'TC1', 'reason': 'duplicate'}]}, ['TC1'])
    assert checks.key_problems({'key_problems': [kp], 'dropped': []}, ['TC2'])


def test_contradiction_ids_and_parameter_pair_are_checked():
    tc = {'label': 'TC1', 'if_action': 'increase insulation', 'then_good': 'less loss', 'but_bad': 'more mass',
          'coupling_mechanism': 'added material', 'rationale': 'candidate change',
          'improving_param_id': 22, 'worsening_param_id': 2, 'cause_node_ids': ['N1']}
    data = {'technical_contradictions': [tc], 'physical_contradictions': [],
            'physical_not_applicable_reason': 'No opposite requirements on one property established'}
    assert not verify.check_contradictions(data, cause_ids=['N1'])
    assert verify.check_contradictions(data, cause_ids=['N2'])
    tc['worsening_param_id'] = 22
    assert verify.check_contradictions(data, cause_ids=['N1'])


def test_short_ceca_preserves_uncertainty_without_forcing_fictitious_depth():
    data = {'nodes': [
        {'id': 'N1', 'text': 'liquid loss', 'parents': [], 'node_type': 'TARGET_DISADVANTAGE',
         'evidence_status': 'OBSERVED', 'evidence_refs': ['user observation']},
        {'id': 'N2', 'text': 'hypothesis: heat crosses the insulation', 'parents': ['N1'], 'node_type': 'ROOT_CAUSE',
         'evidence_status': 'HYPOTHESIS', 'evidence_refs': [], 'falsification_test': 'Compare measured losses at two temperatures'},
    ]}
    assert not verify.check_ceca(data)
    data['nodes'][1]['evidence_status'] = 'OBSERVED'
    assert verify.check_ceca(data)


@pytest.mark.parametrize('value', [None, [], 0, 'partial', {}, {'nodes': [None]}, {'nodes': [{'id': []}]}])
def test_malformed_analysis_returns_issues_instead_of_checker_crash(value):
    for checker in (verify.check_function_model, verify.check_ceca, verify.check_contradictions,
                    checks.nine_windows, checks.sufields, checks.resources, checks.discovered_constraints,
                    checks.ifr, lambda d: checks.trimming(d, []), lambda d: checks.key_problems(d, [])):
        assert checker(value), checker.__name__
