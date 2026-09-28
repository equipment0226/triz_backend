"""AI-only saved reviews reach effect utility without any user score or keep."""
import pytest
from test_ax_refactor import newrun
from test_unified_feedback_adaptive import adaptive_run, events
from test_unified_feedback_learning import isolated_learning_database
from test_targeted_f1_f5 import review_provider
from triz import llm, nodes, quality, rag
from triz.context import HumanInterrupt, RunContext
from triz.schema import Constraint
from triz.ax import adaptive_tracks, coordinator, ledger, learning_outcomes
from triz.ax.action_runtime import executing


def ai_reviewed_run(adaptive_run, monkeypatch, *, verdict='PASS', gate=None, active=True):
    state = adaptive_run('LITE')
    state.scratch['training_consent'] = 'PROJECT_ONLY'
    state.scratch['ax_bundle']['effects'][0]['function_ko'] = '열 제거'
    ctx = RunContext(state)
    review_provider(monkeypatch, state, verdict=verdict, gate=gate or 'CONDITIONAL')
    if not active:
        provider = llm.chat_json
        def no_effect_provider(**kwargs):
            result = provider(**kwargs)
            for row in result.data.get('concepts', []):
                row['active_effect_ids'] = []
            return result
        monkeypatch.setattr(llm, 'chat_json', no_effect_provider)
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: '')
    coordinator.route(ctx)
    tickets = adaptive_tracks.proposals(state)
    index = next(i for i, ticket in enumerate(tickets) if ticket.parameters.get('tracks') == ['H_EFFECTS'])
    chosen, decision = coordinator.decide(state, tickets, index,
        {'RUN_TRACK', 'STOP_EXPLORATION'}, 'adaptive:initial')
    with executing(ctx, chosen, decision, context='adaptive:initial', optional=False):
        nodes._run_tracks(ctx, ['H_EFFECTS'])
    quality.generate_concepts(ctx)
    if gate:
        state.constraints.items = [Constraint(id='limit', statement='No extra power')]
        if gate == 'CONDITIONAL':
            with pytest.raises(HumanInterrupt):
                nodes.s7_gate(ctx)
        else:
            nodes.s7_gate(ctx)
    return state


def effect_sample(state):
    observed = events(state)
    assert observed and all(row['dimension'] != 'user_utility' for row in observed)
    assert all(row['evaluation_stage'] not in ('s7_user', 's10_feedback') for row in observed)
    assert ledger.budget(state.run_id)['spent_microusd'] > 0
    manifest = learning_outcomes.effect_dataset('local', 'local', include_synthetic=True)
    assert len(manifest['samples']) == 1, manifest
    sample = manifest['samples'][0]
    assert sample['effect_id'] == 'E1' and sample['sample_weight'] == 1
    assert sample['selection_id'] and sample['application_id']
    assert sample['maturity'] == 'MODEL_REVIEW_PROXY'
    assert sample['outcome']['masks'] == {'concept_quality': True, 'user_utility': False}
    assert sample['outcome']['user_utility'] is None
    assert sample['outcome']['weights']['quality_weight'] == .7
    assert sample['outcome']['weights']['utility_weight'] == .3
    assert sample['label'] == pytest.approx(.7 * sample['outcome']['concept_quality'])
    assert set(sample['review_ids']) <= {row['event_id'] for row in observed}
    assert learning_outcomes.effect_dataset('local', 'local')['samples'] == []
    return sample, observed


@pytest.mark.parametrize('verdict, expected', [('PASS', .7), ('REVISE', 0.), ('REJECT', -.7)])
def test_ai_s6_review_alone_produces_exact_effect_utility(adaptive_run, monkeypatch, verdict, expected):
    state = ai_reviewed_run(adaptive_run, monkeypatch, verdict=verdict)
    sample, observed = effect_sample(state)
    assert sample['label'] == pytest.approx(expected)
    assert {row['dimension'] for row in observed} == {'concept_quality', 'coverage_quality'}
    assert all(row['active_effect_ids'] == ['E1'] for row in observed)
    assert set(sample['review_ids']) == {row['event_id'] for row in observed}
    if verdict == 'REJECT':
        assert state.concepts == []
        assert state.scratch['ax_excluded'][0]['active_effect_ids'] == ['E1']


@pytest.mark.parametrize('gate, expected, gate_value', [('FAIL', -.7, -1.), ('CONDITIONAL', .7, None)])
def test_ai_constraint_review_joins_effect_utility_without_user_answer(adaptive_run, monkeypatch, gate, expected, gate_value):
    state = ai_reviewed_run(adaptive_run, monkeypatch, gate=gate)
    sample, observed = effect_sample(state)
    assert sample['label'] == pytest.approx(expected)
    check = next(row for row in observed if row['dimension'] == 'constraint_quality')
    assert check['observed_value'] == gate_value
    assert check['observed_mask'] is (gate_value is not None)
    assert check['active_effect_ids'] == ['E1']
    assert (check['event_id'] in sample['review_ids']) is (gate == 'FAIL')
    assert check['reviewer_model_and_rubric_version']['actual_review']['verdict'] == gate
    if gate == 'CONDITIONAL':
        assert state.constraint_checks[0].verdict == gate
    else:
        assert state.concepts == []


def test_latest_ai_review_revision_replaces_old_reward_without_duplicate_weight(adaptive_run, monkeypatch):
    state = ai_reviewed_run(adaptive_run, monkeypatch)
    first, first_events = effect_sample(state)
    cid = state.concepts[0].id
    assert first['label'] == pytest.approx(.7)
    state.constraints.items = [Constraint(id='limit', statement='New review input')]
    review_provider(monkeypatch, state, verdict='REVISE')
    quality.generate_concepts(RunContext(state))
    assert state.concepts[0].id == cid
    latest, observed = effect_sample(state)
    assert latest['label'] == 0 and latest['sample_weight'] == 1
    assert not (set(latest['review_ids']) & {row['event_id'] for row in first_events})
    used = [row for row in observed if row['event_id'] in latest['review_ids']]
    assert {row['review_revision']['revision'] for row in used} == {2}
    assert {row['dimension'] for row in used} == {'concept_quality', 'coverage_quality'}
    quality.generate_concepts(RunContext(state))
    replayed, after = effect_sample(state)
    assert replayed['label'] == 0 and replayed['sample_weight'] == 1
    assert replayed['review_ids'] == latest['review_ids']
    assert after == observed


def test_ai_review_of_exposed_but_unused_effect_does_not_create_effect_sample(adaptive_run, monkeypatch):
    state = ai_reviewed_run(adaptive_run, monkeypatch, active=False)
    observed = events(state)
    assert observed and all(row['observed_value'] == 1 for row in observed)
    assert all(row['active_effect_ids'] == [] and row['active_effect_application_ids'] == [] for row in observed)
    assert learning_outcomes.effect_dataset('local', 'local', include_synthetic=True)['samples'] == []
