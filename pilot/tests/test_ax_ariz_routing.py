"""ARIZ is a DEEP analysis track, independent of the Part 6 report threshold."""
import pytest

from triz import agent, nodes, pipeline, store
from triz.ax import coordinator, runtime
from triz.context import AbortRun, RunContext
from triz.schema import ConceptSpec, RunMode, SuFieldModel
from test_ax_phase1 import dlc


@pytest.mark.parametrize('solution_count', [0, 3, 4])
def test_deep_ariz_is_in_baseline_even_with_full_optional_queue(dlc, solution_count):
    dlc.control.mode = RunMode.DEEP
    dlc.analysis.su_fields = [SuFieldModel(s1='glass', s2='clamp', field='mechanical')]
    dlc.concepts = [ConceptSpec(id=f'C{i}', title=f'Candidate {i}') for i in range(solution_count)]
    dlc.scratch['ax_expansion_rounds'] = 1

    coordinator.route(RunContext(dlc))

    plan = dlc.scratch['ax_coordination']
    assert plan['tracks'] == ['D_ARIZ', 'A_MATRIX', 'B_SEPARATION']
    assert len(plan['tracks']) <= dlc.scratch['ax_bundle']['limits']['branches']
    assert 'D_ARIZ' not in plan['pending_tracks']
    assert {'C_STANDARDS', 'H_EFFECTS'} <= set(plan['pending_tracks'])


def test_explicit_ariz_selection_is_not_discarded_by_full_route(dlc):
    dlc.control.enabled_tracks = ['D_ARIZ']
    coordinator.route(RunContext(dlc))
    assert 'D_ARIZ' in dlc.control.enabled_tracks


@pytest.mark.parametrize('mode', [RunMode.LITE, RunMode.FULL])
def test_quick_and_standard_do_not_force_ariz_into_baseline(dlc, mode):
    dlc.control.mode = mode
    dlc.control.enabled_tracks = []
    coordinator.route(RunContext(dlc))
    assert 'D_ARIZ' not in dlc.control.enabled_tracks


@pytest.mark.parametrize('mode', [RunMode.LITE, RunMode.FULL, RunMode.DEEP])
def test_legacy_solve_dispatches_ariz_only_when_deep_or_selected(state, monkeypatch, mode):
    state.control.mode = mode
    state.control.enabled_tracks = []
    called = []
    monkeypatch.setattr(nodes, '_evidence', lambda ctx: None)
    monkeypatch.setattr(nodes, '_merge', lambda ctx: False)

    def respond(ctx, **kwargs):
        called.append(kwargs['node'])
        if kwargs['node'] == 's5_ariz_p4':
            return {'solution_directions': ['Preserve stiffness while reducing motion time']}
        return {}

    monkeypatch.setattr(agent, 'run_agent', respond)
    nodes.s5_solve(RunContext(state))
    if mode == RunMode.DEEP:
        assert called == [f's5_ariz_p{i}' for i in (1, 2, 3, 4, 5, 7)]
        assert state.solve.ariz is not None
        assert state.solve.tracks_run == ['D_ARIZ']
    else:
        assert called == [] and state.solve.ariz is None


def test_deep_cannot_silently_complete_without_ariz_result(state, monkeypatch):
    state.control.mode = RunMode.DEEP
    monkeypatch.setattr(nodes, '_evidence', lambda ctx: None)
    monkeypatch.setattr(nodes, '_run_tracks', lambda ctx, tracks: None)
    monkeypatch.setattr(nodes, '_merge', lambda ctx: pytest.fail('Must stop before portfolio assembly'))
    with pytest.raises(AbortRun, match='ARIZ 실행기록'):
        nodes.s5_solve(RunContext(state))


@pytest.mark.parametrize('stage, clears', [('s4_define', True), ('s5_solve', True), ('s6_concept', False)])
def test_new_solve_revision_resets_only_its_expansion_state(dlc, monkeypatch, stage, clears):
    dlc.status = 'COMPLETED'
    transient = {'ax_coordination': {'tracks': ['A_MATRIX'], 'expansions': [{'tracks': ['H_EFFECTS']}]},
        'ax_expansion_rounds': 1, 'ax_expansion_deferred': 'budget',
        'ax_idea_inventory': [{'id': 'old'}], 'ax_effect_applicability': [{'id': 'old'}]}
    dlc.scratch.update(transient)
    store.save_state(dlc)
    monkeypatch.setattr(pipeline, 'start', lambda run_id: None)

    assert pipeline.rerun_from(dlc.run_id, stage)

    saved = store.load_state(dlc.run_id)
    if clears:
        assert not set(transient) & set(saved.scratch)
        if stage == 's5_solve':
            saved.control.mode = RunMode.DEEP
            runtime.before_stage(RunContext(saved), 's5_solve')
            assert saved.scratch['ax_coordination']['tracks'][0] == 'D_ARIZ'
            assert 'ax_expansion_rounds' not in saved.scratch
    else:
        assert {k: saved.scratch[k] for k in transient} == transient


def test_continue_interrupted_solve_keeps_completed_expansion_round(dlc, monkeypatch):
    dlc.status = 'INTERRUPTED'
    dlc.control.stage_index = 6
    dlc.scratch['ax_expansion_rounds'] = 1
    store.save_state(dlc)
    monkeypatch.setattr(pipeline, 'start', lambda run_id: None)
    assert pipeline.continue_run(dlc.run_id)
    assert store.load_state(dlc.run_id).scratch['ax_expansion_rounds'] == 1
