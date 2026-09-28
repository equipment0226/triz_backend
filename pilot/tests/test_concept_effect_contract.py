"""Explicit generator adoption reaches saved common evaluations, offline only."""
import copy

import pytest

from test_ax_refactor import newrun
from test_unified_feedback_adaptive import adaptive_run, events
from test_unified_feedback_learning import isolated_learning_database
from triz import nodes, quality, rag, store
from triz.context import AbortRun, HumanInterrupt, RunContext
from triz.schema import RawIdea, Constraint
from triz.ax import concept_effects, coordinator, adaptive_tracks, feedback_events, learning_outcomes, ledger
from triz.ax.action_runtime import executing, emit, episode
from triz.ax.contracts import ActionTicket


@pytest.mark.parametrize('value', [None, 'E1', [1], [''], ['E1', 'E1'], ['E2']])
def test_explicit_ids_reject_missing_invalid_duplicate_and_other_source(adaptive_run, value):
    state = adaptive_run()
    state.solve.raw_ideas = [RawIdea(id='one', detail={'source_effect_id': 'E1'}),
                             RawIdea(id='two', detail={'source_effect_id': 'E2'})]
    row = dict(title='Fixture', source_idea_ids=['one'])
    if value is not None:
        row['active_effect_ids'] = value
    assert concept_effects.check_batch(state, {'concepts': [row]})
    for active in ([], ['E1']):
        row['active_effect_ids'] = active
        assert concept_effects.check_batch(state, {'concepts': [row]}) == []


def test_source_exposure_does_not_fill_omitted_adoption(adaptive_run, monkeypatch):
    state = adaptive_run()
    state.solve.raw_ideas = [RawIdea(id='one', detail={'source_effect_id': 'E1'})]
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: '')
    monkeypatch.setattr(quality.agent, 'run_agent', lambda *a, **kw:
        {'concepts': [{'title': 'Fixture', 'source_idea_ids': ['one']}], 'excluded': []})
    monkeypatch.setattr(quality, 'audit_concepts', lambda _: pytest.fail('Invalid output audited'))
    with pytest.raises(AbortRun, match='active_effect_ids'):
        quality._generate_concepts(RunContext(state), ideas_override=state.solve.raw_ideas)
    assert state.concepts == []


def test_generation_review_rating_effect_dataset_and_settled_cost_join(adaptive_run, monkeypatch):
    from test_targeted_f1_f5 import review_provider
    state = adaptive_run('LITE')
    state.scratch['training_consent'] = 'PROJECT_ONLY'
    state.scratch['ax_bundle']['effects'][0]['function_ko'] = '열 제거'
    ctx = RunContext(state)
    review_provider(monkeypatch, state, verdict='PASS', gate='CONDITIONAL')
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: '')
    coordinator.route(ctx)
    tickets = adaptive_tracks.proposals(state)
    index = next(i for i, t in enumerate(tickets) if t.parameters.get('tracks') == ['H_EFFECTS'])
    chosen, decision = coordinator.decide(state, tickets, index, {'RUN_TRACK', 'STOP_EXPLORATION'}, 'adaptive:initial')
    with executing(ctx, chosen, decision, context='adaptive:initial', optional=False):
        nodes._run_tracks(ctx, ['H_EFFECTS'])
    quality.generate_concepts(ctx)
    candidate = state.concepts[0]
    assert candidate.active_effect_ids == ['E1']
    assert candidate.quality_status == 'PASS'
    step = next(s for s in state.steps if s.node == 's6_concept')
    assert concept_effects.VERSION in step.input_slice['user']
    assert '"active_effect_ids":[]' in step.input_slice['user']
    assert step.output_json['concepts'][0]['active_effect_ids'] == ['E1']
    state.constraints.items = [Constraint(id='limit', statement='No extra power')]
    with pytest.raises(HumanInterrupt):
        nodes.s7_gate(ctx)
    feedback_events.final_feedback(state, {'submission_id': 'actual-score',
        'solution_feedback': [{'concept_id': candidate.id, 'rating': 5}]})
    stop = ActionTicket(action_type='STOP_EXPLORATION', parameters={'phase': 'initial'},
        reason='Fixture stop', expected_outputs=['SearchPhaseResult'], allowed_tools=[])
    chosen, decision = coordinator.decide(state, [stop], 0, {'STOP_EXPLORATION'}, 'adaptive:initial')
    with executing(ctx, chosen, decision, context='adaptive:initial', optional=False):
        pass
    emit(state, 'ADAPTIVE_EPISODE_CLOSED', dict(semantic_episode_id=episode(state),
        candidate_ids=[candidate.id], terminal_decision_id=decision,
        report_snapshot_id=state.scratch['ax_snapshot_id']))
    rows = [r for r in events(state) if r['candidate_id'] == candidate.id]
    assert {'s6_quality', 's7_gate', 's10_feedback'} <= {r['evaluation_stage'] for r in rows}
    assert all(r['active_effect_ids'] == ['E1'] and r['active_effect_application_ids'] for r in rows)
    conditional = next(r for r in rows if r['evaluation_stage'] == 's7_gate')
    assert conditional['observed_value'] is None
    manifest = learning_outcomes.effect_dataset('local', 'local', include_synthetic=True)
    assert len(manifest['samples']) == 1, manifest
    sample = manifest['samples'][0]
    assert sample['effect_id'] == 'E1' and sample['sample_weight'] == 1
    assert sample['label'] > 0 and set(sample['review_ids']) <= {r['event_id'] for r in rows}
    assert ledger.budget(state.run_id)['spent_microusd'] > 0
    assert learning_outcomes.effect_dataset('local', 'local')['samples'] == []


def test_old_bundle_prompt_and_response_remain_legacy(adaptive_run, monkeypatch):
    from triz import llm
    state = adaptive_run()
    state.scratch['ax_bundle'].pop('concept_effect_contract')
    state.solve.raw_ideas = [RawIdea(id='one', detail={'source_effect_id': 'E1'})]
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: '')
    monkeypatch.setattr(quality, 'audit_concepts', lambda _: None)
    raw = {'concepts': [{'title': 'Old saved response', 'source_idea_ids': ['one']}], 'excluded': []}
    monkeypatch.setattr(llm, 'chat_json', lambda **kw: llm.LLMResult(
        data=copy.deepcopy(raw), text='', cost_usd=.00001, tokens_in=1, tokens_out=1))
    quality._generate_concepts(RunContext(state), ideas_override=state.solve.raw_ideas)
    assert state.concepts[0].active_effect_ids == []
    assert concept_effects.VERSION not in state.steps[-1].input_slice['user']
    assert state.steps[-1].output_json == raw
