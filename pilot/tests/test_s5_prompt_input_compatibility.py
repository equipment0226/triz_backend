"""Final provider input is complete even when a pinned body has no new variables.

Synthetic old pins exercise compatibility; the production export did not include
its pinned prompt bodies, so this does not claim to reproduce their exact text.
"""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, nodes
from triz.ax import runtime
from triz.context import RunContext
from triz.schema import PhysicalContradiction, SystemCandidate, TechnicalContradiction


@pytest.mark.parametrize('track', ['F', 'G', 'H'])
@pytest.mark.parametrize('old_pin', [False, True])
def test_final_track_request_contains_problem_criteria_contradictions_and_boundary(state, monkeypatch, track, old_pin):
    state.intake.frame.restated_problem = 'CONFIRMED_PROBLEM_SENTINEL'
    state.intake.frame.symptom = 'OBSERVED_SYMPTOM_SENTINEL'
    state.intake.frame.success_criteria = ['SUCCESS_CRITERION_SENTINEL']
    state.domain.problem_type = 'PHYSICAL_TECHNICAL'
    state.domain.physical_scope = 'PHYSICAL_SCOPE_SENTINEL'
    state.domain.target_system = 'UNCONFIRMED_OLD_TARGET'
    candidate = SystemCandidate(name='CONFIRMED_TARGET_SENTINEL')
    state.confirm.candidates = [candidate]
    state.confirm.chosen_candidate_id = candidate.id
    state.confirm.user_confirmed = True
    state.confirm.operative_zone = 'OPERATIVE_ZONE_SENTINEL'
    state.confirm.operative_time = 'OPERATIVE_TIME_SENTINEL'
    state.confirm.user_amendments = ['USER_AMENDMENT_SENTINEL']
    state.definition.technical_contradictions = [TechnicalContradiction(
        if_action='TC_CHANGE_SENTINEL', then_good='TC_IMPROVEMENT_SENTINEL',
        but_bad='TC_PROTECTED_SIDE_SENTINEL')]
    state.definition.physical_contradictions = [PhysicalContradiction(
        element='PC_ELEMENT_SENTINEL', state_a='PC_STATE_A_SENTINEL', state_b='PC_STATE_B_SENTINEL')]
    # Avoid succeeding only because the same target appears in constraints or a
    # domain brief. The frame-only criterion must reach the real user string.
    state.constraints.items = []
    state.scratch.pop('deep_dive', None)
    state.scratch.pop('industry_profile', None)
    runtime.initialize(state)
    prompt_id = 'P_S5_TRACK_' + track
    if old_pin:
        state.scratch['ax_bundle'].pop('coherence_contract', None)
        state.scratch['ax_bundle']['prompts'][prompt_id] = (
            'PINNED_TRACK_POLICY_SENTINEL\nTarget: {{target_system}}\n'
            'Keep the established analysis policy and return applications.')
    original_prompts = deepcopy(state.scratch['ax_bundle']['prompts'])
    calls = []

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data={'applications': [], 'no_application_reason':
            'Operating limits remain unmeasured; no applicable mechanism is established.'},
            model='offline-test', tokens_in=1, tokens_out=1, cost_usd=0)

    monkeypatch.setattr(agent, 'tracked_chat', chat)
    getattr(nodes, '_track_' + track.lower())(RunContext(state))
    assert len(calls) == 1
    actual_user = calls[0]['user']
    for marker in ('CONFIRMED_PROBLEM', 'OBSERVED_SYMPTOM', 'SUCCESS_CRITERION',
                   'CONFIRMED_TARGET', 'OPERATIVE_ZONE', 'OPERATIVE_TIME', 'PHYSICAL_SCOPE',
                   'USER_AMENDMENT', 'TC_CHANGE', 'TC_IMPROVEMENT', 'TC_PROTECTED_SIDE',
                   'PC_ELEMENT', 'PC_STATE_A', 'PC_STATE_B'):
        assert marker + '_SENTINEL' in actual_user
    assert 'UNCONFIRMED_OLD_TARGET' not in actual_user
    if old_pin:
        assert 'PINNED_TRACK_POLICY_SENTINEL' in actual_user
    step = state.steps[-1]
    assert step.input_slice['user'] == actual_user
    assert step.input_slice['system'] == calls[0]['system']
    assert step.status == 'OK'
    assert state.scratch['ax_bundle']['prompts'] == original_prompts


def test_other_tracks_do_not_acquire_new_problem_block_or_cache_input(state, monkeypatch):
    calls = []

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data={'applications': []}, model='offline-test',
                               tokens_in=1, tokens_out=1, cost_usd=0)

    monkeypatch.setattr(agent, 'tracked_chat', chat)
    agent.run_agent(RunContext(state), node='s5_track_e', label='Existing trimming input',
                    stage='S5_SOLVE', agent_id='trimming_specialist', prompt_id='P_S5_TRACK_E',
                    vars={'target_system': 'Existing input', 'trimming_items': [], 'resources': []}, default={})
    assert 'S5 문제 입력 계약 v1' not in calls[0]['user']


def test_frame_change_invalidates_old_pin_cache_but_identical_input_reuses_it(state, monkeypatch):
    runtime.initialize(state)
    state.scratch['ax_bundle']['prompts']['P_S5_TRACK_F'] = 'PINNED POLICY: {{target_system}}'
    state.intake.frame.success_criteria = ['FIRST_CRITERION']
    calls = []

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data={'applications': [], 'no_application_reason':
            'A required operating measurement is missing.'}, model='offline-test',
            tokens_in=1, tokens_out=1, cost_usd=0)

    monkeypatch.setattr(agent, 'tracked_chat', chat)
    ctx = RunContext(state)
    nodes._track_f(ctx)
    nodes._track_f(ctx)
    assert len(calls) == 1 and state.steps[-1].status == 'SKIPPED'
    state.intake.frame.success_criteria = ['REVISED_CRITERION']
    nodes._track_f(ctx)
    assert len(calls) == 2 and state.steps[-1].status == 'OK'
    assert 'REVISED_CRITERION' in calls[-1]['user']
    assert 'FIRST_CRITERION' not in calls[-1]['user']
