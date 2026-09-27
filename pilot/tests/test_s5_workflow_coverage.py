"""Exercise real routing/dispatch/merge boundaries; no model or physical validation."""
import pytest

from triz import agent, nodes, solve_contract
from triz.ax import coordinator
from triz.context import AbortRun, RunContext
from triz.schema import ARIZRun, RawIdea, RunMode, SuFieldModel, TrimmingItem
from test_ax_phase1 import dlc


@pytest.mark.parametrize('mode', list(RunMode))
@pytest.mark.parametrize('old_bundle', [False, True])
@pytest.mark.parametrize('branches', [1, 3])
def test_mode_tracks_finish_before_merge_even_with_old_pin(dlc, monkeypatch, mode, old_bundle, branches):
    dlc.control.mode = mode
    dlc.analysis.su_fields = [SuFieldModel(s1='panel', s2='carrier', field='mechanical')]
    dlc.definition.trimming = [TrimmingItem(target_component='carrier')]
    if old_bundle:
        dlc.scratch['ax_bundle'].pop('coherence_contract')
        dlc.scratch['ax_bundle']['limits'].pop('expansion_rounds', None)
    dlc.scratch['ax_bundle']['limits']['branches'] = branches
    dlc.scratch['ax_expansion_rounds'] = 99  # Optional expansion exhaustion must not drop requirements.
    called = []
    actual_batches = []
    real_run = nodes._run_tracks

    def run_batch(ctx, tracks):
        actual_batches.append(list(tracks))
        real_run(ctx, tracks)

    def producer(track):
        def run(ctx):
            assert ctx.state.definition.technical_contradictions[0].id == 'TC-DLC'
            assert ctx.state.domain.target_system == dlc.domain.target_system
            called.append(track)
            idea = RawIdea(track=track, title=track, idea='Preserve measured yield while shortening motion')
            ctx.state.solve.raw_ideas.append(idea)
            if track == 'D_ARIZ':
                ctx.state.solve.ariz = ARIZRun()
            elif track != 'E_TRIMMING':
                getattr(ctx.state.solve, solve_contract.OUTPUT_FIELDS[track]).append({'idea': idea.idea})
            if track == 'F_TRENDS':
                ctx.state.scratch['s_curve'] = {'stage': 'NEW'}
        return run

    for track in solve_contract.TRACKS:
        monkeypatch.setitem(nodes.TRACK_FUNCS, track, producer(track))
    monkeypatch.setattr(nodes, '_run_tracks', run_batch)
    monkeypatch.setattr(nodes, '_evidence', lambda ctx: None)

    def merge(ctx):
        assert set(called) == set(solve_contract.DEFAULTS[mode.value])
        return False

    monkeypatch.setattr(nodes, '_merge', merge)
    ctx = RunContext(dlc)
    coordinator.route(ctx)
    nodes.s5_solve(ctx)
    assert len(called) == len(set(called))
    assert all(len(batch) <= branches for batch in actual_batches)
    assert not dlc.scratch['ax_coordination']['pending_tracks']
    assert set(dlc.solve.tracks_run) == set(solve_contract.DEFAULTS[mode.value])
    assert all(r['status'] == 'COMPLETED' for r in dlc.scratch['ax_track_execution'].values())
    if mode != RunMode.LITE:
        assert dlc.scratch['s_curve']['stage'] == 'NEW'


def test_nonphysical_and_missing_inputs_get_explicit_reasons(dlc):
    dlc.control.mode = RunMode.DEEP
    dlc.domain.problem_type = 'INFORMATION_SOFTWARE'
    coordinator.route(RunContext(dlc))
    statuses = dlc.scratch['ax_track_execution']
    assert statuses['C_STANDARDS']['status'] == 'NOT_APPLICABLE'
    assert statuses['E_TRIMMING']['status'] == 'NOT_APPLICABLE'
    assert {'D_ARIZ', 'F_TRENDS', 'G_FOS', 'H_EFFECTS'} <= set(dlc.control.enabled_tracks)


def test_successful_branches_survive_failure_and_continue_without_duplicates(state, monkeypatch):
    attempts = []
    def success(ctx):
        attempts.append('F')
        ctx.state.solve.trend_apps = [{'idea': 'new'}]
        ctx.state.scratch['s_curve'] = {'stage': 'fresh'}
    def failed(ctx):
        attempts.append('G')
        raise AbortRun('provider unavailable')
    state.scratch['s_curve'] = {'stage': 'stale'}
    monkeypatch.setitem(nodes.TRACK_FUNCS, 'F_TRENDS', success)
    monkeypatch.setitem(nodes.TRACK_FUNCS, 'G_FOS', failed)
    with pytest.raises(AbortRun):
        nodes._run_tracks(RunContext(state), ['F_TRENDS', 'G_FOS'])
    assert state.solve.tracks_run == ['F_TRENDS']
    assert state.scratch['s_curve']['stage'] == 'fresh'
    def finish(ctx):
        attempts.append('G')
        ctx.state.solve.fos_apps = [{'idea': 'transfer'}]
    monkeypatch.setitem(nodes.TRACK_FUNCS, 'G_FOS', finish)
    nodes._run_tracks(RunContext(state), ['F_TRENDS', 'G_FOS'])
    assert attempts.count('F') == 1 and attempts.count('G') == 2
    assert len(state.solve.trend_apps) == 1
    assert state.scratch['s_curve']['stage'] == 'fresh'


@pytest.mark.parametrize('track', ['F_TRENDS', 'G_FOS', 'H_EFFECTS'])
@pytest.mark.parametrize('output', [{}, {'applications': []}, {'applications': [{'idea': ''}]}])
def test_blank_generation_cannot_finish_s5(state, monkeypatch, track, output):
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **k: output)
    with pytest.raises(AbortRun, match='불완전'):
        nodes._run_tracks(RunContext(state), [track])
    assert track not in state.solve.tracks_run
    assert state.scratch['ax_track_execution'][track]['status'] == 'FAILED'


@pytest.mark.parametrize('track', ['F_TRENDS', 'G_FOS', 'H_EFFECTS'])
def test_explicit_no_application_review_is_preserved(state, monkeypatch, track):
    reason = '입력에 작동 범위 측정이 없어 후보 효과의 적용 조건 충족을 판단할 수 없습니다.'
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **k: {'applications': [], 'no_application_reason': reason})
    nodes._run_tracks(RunContext(state), [track])
    assert state.scratch['ax_track_execution'][track] == {
        'status': 'REVIEWED_NO_APPLICATION', 'reason': reason, 'output_count': 0}


def test_failed_default_return_cannot_mark_track_done(state, monkeypatch):
    def failed(ctx):
        step = ctx.start_step(node='s5_track_a', label='A', stage='S5', agent_id='inventor_a',
                              prompt_id='P_S5_TRACK_A', tier='T2')
        ctx.finish_step(step, 'FAILED')
        # Real run_agent can return its default after recording a provider error.
    monkeypatch.setitem(nodes.TRACK_FUNCS, 'A_MATRIX', failed)
    with pytest.raises(AbortRun, match='호출 실패'):
        nodes._run_tracks(RunContext(state), ['A_MATRIX'])
    assert 'A_MATRIX' not in state.solve.tracks_run
    assert state.scratch['ax_track_execution']['A_MATRIX']['status'] == 'FAILED'


def test_empty_evidence_retry_clears_old_candidate_mapping(state):
    from triz import evidence
    state.scratch.update(related_references=[{'concept_id': 'old'}],
                         evidence_mappings={'old': {'patent': {}}}, evidence_candidates=[])
    evidence.attach(RunContext(state), discover_sources=False)
    assert state.scratch['related_references'] == []
    assert state.scratch['evidence_mappings'] == {}


def test_old_partial_solve_is_revalidated_only_on_s5_entry(dlc):
    dlc.solve.tracks_run = ['A_MATRIX']
    dlc.solve.principle_apps = [{'idea': 'old partial output'}]
    dlc.scratch['s_curve'] = {'stage': 'stale'}
    coordinator.route(RunContext(dlc))
    assert not dlc.solve.tracks_run and not dlc.solve.principle_apps
    assert 's_curve' not in dlc.scratch
    assert dlc.scratch['ax_solve_compatibility']['previous_tracks'] == ['A_MATRIX']


def test_deep_old_three_concept_cap_uses_current_breadth_without_mutating_pin(dlc):
    dlc.control.mode = RunMode.DEEP
    dlc.scratch['ax_bundle']['limits']['detailed_candidates'] = 3
    budget = dlc.cost.budget_usd
    assert solve_contract.concept_review_limit(dlc) == 8
    assert dlc.scratch['ax_bundle']['limits']['detailed_candidates'] == 3
    assert dlc.cost.budget_usd == budget
