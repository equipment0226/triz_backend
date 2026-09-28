"""Acceptance fixtures are synthetic, isolated, and never deployment evidence."""
import json
import pytest
from sqlalchemy import select
from test_ax_refactor import newrun
from triz import nodes, store
from triz.context import RunContext
from triz.schema import ConceptSpec, ConstraintCheckResult, RawIdea
from triz.settings import settings
from triz.ax import ledger


@pytest.fixture
def adaptive_run(newrun, monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    def create(mode='FULL', user='local'):
        state = newrun(mode, user)
        state.scratch['synthetic'] = True
        return state
    return create


def candidate(state, cid='C1'):
    state.solve.raw_ideas.append(RawIdea(id='raw-' + cid, track='H_EFFECTS', title='fixture',
        idea='전도 경로', mechanism_key='conduction', detail={'source_effect_id':'E1', 'idea':'전도 경로'}))
    value = ConceptSpec(id=cid, title='fixture', working_principle='전도 경로',
        source_idea_ids=['raw-' + cid], mechanism_key='conduction')
    state.concepts.append(value)
    state.constraint_checks.append(ConstraintCheckResult(concept_id=cid, verdict='CONDITIONAL'))
    return value


def events(state):
    with store.engine.connect() as c:
        return [json.loads(raw) for raw in c.execute(select(ledger.events.c.payload).where(
            ledger.events.c.run_id == state.run_id, ledger.events.c.event_type == 'COMMON_EVALUATION')).scalars()]


def test_M04_new_full_does_not_require_every_eligible_track(adaptive_run):
    from triz.solve_contract import plan
    state = adaptive_run()
    expected, required, skipped = plan(state)
    assert set(expected) == {'A_MATRIX','B_SEPARATION','C_STANDARDS','E_TRIMMING','F_TRENDS','G_FOS','H_EFFECTS'}
    assert required == []


def test_M01_M12_deep_retains_all_registered_tracks(adaptive_run,monkeypatch):
    from test_ax_refactor import test_new_modes_pin_and_complete_every_track
    test_new_modes_pin_and_complete_every_track(adaptive_run,monkeypatch,'DEEP')


@pytest.mark.parametrize('mode',['LITE','FULL'])
def test_M05_mode_guard_blocks_ariz_in_direct_and_governed_paths(adaptive_run,mode):
    from triz.ax.coordinator import feasible
    from triz.ax.contracts import ActionTicket
    state=adaptive_run(mode)
    ticket=ActionTicket(action_type='RUN_TRACK',parameters={'tracks':['D_ARIZ']},allowed_tools=['legacy_tracks'],expected_outputs=['TrackResult'],reason='fixture')
    assert feasible(state,ticket,handlers={'RUN_TRACK'})
    with pytest.raises(ValueError): nodes._run_tracks(RunContext(state),['D_ARIZ'])


def test_M02_M07_missing_required_input_is_not_normal_stop(adaptive_run):
    from triz.ax import adaptive_tracks,mode_contract,coordinator
    from triz.ax.contracts import ActionTicket
    state=adaptive_run()
    state.scratch['ax_bundle']['run_contract']['explicit_required_tracks']=['A_MATRIX']
    state.definition.technical_contradictions=[]
    adaptive_tracks.prepare(state)
    state.scratch['adaptive_search']={'status':'READY_FOR_REVIEW'}
    coverage=mode_contract.coverage(state)
    assert 'A_MATRIX' in coverage['blocked_missing_input'] and not coverage['complete']
    assert 'A_MATRIX' not in coverage['not_applicable']
    stop=ActionTicket(action_type='STOP_EXPLORATION',allowed_tools=[],expected_outputs=['SearchPhaseResult'],reason='fixture')
    assert coordinator.feasible(state,stop,handlers={'STOP_EXPLORATION'})=='explicit_required_tracks_incomplete'


def test_U03_U04_explicit_keep_records_utility_without_technical_promotion(adaptive_run):
    state = adaptive_run(); candidate(state)
    state.scratch['resume_payload'] = {'decisions':{'C1':'accept'}, 'training_consent':'PROJECT_ONLY'}
    nodes.s7_gate(RunContext(state))
    observed = events(state)
    assert any(r['dimension'] == 'user_utility' and r['observed_value'] == .1 for r in observed)
    assert state.check_for('C1').verdict == 'CONDITIONAL'


def test_D07_final_feedback_uses_common_event_writer(adaptive_run, monkeypatch):
    state = adaptive_run(); candidate(state)
    monkeypatch.setattr(nodes.rag, 'write_feedback', lambda *args: 0)
    nodes.record_feedback(state, {'solution_feedback':[{'concept_id':'C1','rating':5}],
                                 'training_consent':'PROJECT_ONLY'})
    assert any(r['evaluation_stage'] == 's10_feedback' and r['observed_value'] == 1 for r in events(state))


@pytest.mark.parametrize('mode,minimum',[('LITE',1),('FULL',2)])
def test_M06_M08_fallback_executes_subset_then_stops_for_review(adaptive_run, monkeypatch, mode, minimum):
    from triz.ax import coordinator, mode_contract
    state=adaptive_run(mode);called=[]
    def handler(track):
        def invoke(ctx):
            called.append(track)
            ctx.state.solve.raw_ideas.append(RawIdea(id='r-'+track,track=track,title=track,idea='synthetic mechanism'))
        return invoke
    for track in mode_contract.TRACKS: monkeypatch.setitem(nodes.TRACK_FUNCS,track,handler(track))
    monkeypatch.setattr(nodes,'_evidence',lambda ctx:None)
    monkeypatch.setattr(nodes,'_merge',lambda ctx:False)
    coordinator.route(RunContext(state))
    nodes.s5_solve(RunContext(state))
    assert len(called)==minimum
    assert 'D_ARIZ' not in called
    coordinator.complete_required(RunContext(state))
    assert len(called)==minimum
    coverage=mode_contract.coverage(state)
    assert coverage['search_status']=='READY_FOR_REVIEW' and coverage['method_coverage'] is False
    assert coverage['not_selected']
    assert not state.scratch['adaptive_search']['technical_success']
    assert not state.report
    assert len(ledger.decision_history(state.run_id,state.user_id))==minimum+1
