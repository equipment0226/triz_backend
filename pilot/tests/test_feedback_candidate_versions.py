"""Saved candidate versions, late score corrections and growing local datasets.

Provider results and usage are isolated fixtures, never production evidence.
"""
import pytest

from test_unified_feedback_adaptive import adaptive_run, newrun, events
from test_unified_feedback_learning import isolated_learning_database, observed_episode
from triz.ax import feedback_events as feedback, learning_outcomes as outcomes
from triz.ax import ledger, registry, routing_q, effect_ranker, effect_history
from triz.ax.contracts import CANDIDATE_PROJECTION, LEARNING_INTEGRITY


def reviewed_episode(adaptive_run, monkeypatch, *, problem_group=None):
    state = adaptive_run('LITE')
    if problem_group is not None:
        state.scratch['ax_problem_group'] = problem_group
    state.scratch['candidate_review_revisions'] = {
        'candidate-h': dict(contract='current-review-projection-v2', revision=1, input_hash='recorded-input')}
    candidate, _ = observed_episode(state, monkeypatch)
    feedback.model_review(state, candidate, {'verdict': 'PASS'}, stage='s6_quality',
                          step_id='saved-quality-review', rubric='fixture', model='fixture')
    candidate.quality_status = 'PASS'
    feedback.coverage_review(state, candidate, 'saved-quality-review', {})
    return state, candidate


def final(state, candidate, rating, submission):
    return feedback.final_feedback(state, dict(submission_id=submission,
        solution_feedback=[dict(concept_id=candidate.id, rating=rating)], training_consent='PROJECT_ONLY'))


def manifests(cutoff=None):
    return (outcomes.q_dataset('local', 'local', cutoff, include_synthetic=True),
            outcomes.effect_dataset('local', 'local', cutoff, include_synthetic=True))


def test_final_enriched_candidate_keeps_actual_utility_without_inheriting_old_review(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    before_q, before_effect = manifests()
    assert before_effect['samples'][0]['label'] == pytest.approx(.73)
    previous = events(state)
    cutoff = max(r['label_available_at'] for r in previous)
    candidate.evidence_ids = ['saved-patent-reference']
    candidate.transfer_conditions += ['Mechanical shuttle only; coating remains excluded.']
    assert final(state, candidate, 5, 'final-enriched')
    final_event = events(state)[-1]
    after_q, after_effect = manifests()
    terminal = next(s for s in after_q['samples'] if s['terminal'])
    result = terminal['dimensions']['terminal_outcome']
    assert result['user_utility'] == 1
    assert result['concept_quality'] is None
    assert result['masks'] == dict(concept_quality=False, user_utility=True)
    assert result['source_event_ids'] == [final_event['event_id']]
    assert result['total'] == pytest.approx(.3)
    assert result['candidate_projections'][0]['candidate_version'] == final_event['candidate_version']
    assert terminal['reward_revision'] != next(s for s in before_q['samples'] if s['terminal'])['reward_revision']
    assert after_effect['samples'][0]['label'] == pytest.approx(.3)
    assert after_effect['samples'][0]['application_id'] in final_event['active_effect_application_ids']
    assert after_effect['samples'][0]['review_ids'] == [final_event['event_id']]
    assert manifests(cutoff)[1]['samples'][0]['label'] == pytest.approx(.73)
    assert ledger.budget(state.run_id)['spent_microusd'] == sum(s['dimensions']['actual_microusd'] for s in after_q['samples'])
    assert events(state)[:-1] == previous  # No historical backfill or source mutation.


@pytest.mark.parametrize('mechanism_changed', [False, True])
def test_changed_candidate_has_no_effect_credit_when_effect_was_removed(adaptive_run, monkeypatch, mechanism_changed):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    candidate.active_effect_ids = []
    if mechanism_changed:
        candidate.mechanism_key = 'new-mechanism-without-scientific-effect'
    candidate.transfer_conditions = ['The final design omits the earlier scientific effect.']
    final(state, candidate, 5, 'without-effect')
    qm, em = manifests()
    assert next(s for s in qm['samples'] if s['terminal'])['dimensions']['terminal_outcome']['total'] == pytest.approx(.3)
    assert em['samples'] == []


def test_old_version_score_correction_does_not_replace_new_candidate(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    old_keep = next(r for r in events(state) if r['dimension'] == 'user_utility')
    candidate.transfer_conditions = ['New material transfer constraint.']
    final(state, candidate, 5, 'new-version')
    expected = manifests()[1]['samples'][0]
    feedback.revise(state.run_id, state.user_id, old_keep['event_id'], consent_scope='PROJECT_ONLY',
                    reason='Correct the historical keep, not the final candidate.', value=-.1, correct_value=True)
    projected = manifests()[1]['samples'][0]
    assert projected['label'] == expected['label'] == pytest.approx(.3)
    assert projected['review_ids'] == expected['review_ids']
    assert projected['application_id'] == expected['application_id']


@pytest.mark.parametrize('problem_count', [1, 8])
def test_more_problems_and_feedback_keep_one_latest_label_and_actual_cost(adaptive_run, monkeypatch, problem_count):
    saved = []
    for i in range(problem_count):
        state, candidate = reviewed_episode(adaptive_run, monkeypatch, problem_group='independent-fixture-' + str(i))
        candidate.transfer_conditions = ['Final mechanical transfer condition ' + str(i)]
        final(state, candidate, 5, 'first')
        first = events(state)[-1]
        final(state, candidate, 2, 'correction')
        assert final(state, candidate, 2, 'correction') is False
        last = events(state)[-1]
        saved.append((state, first, last))
    qm, em = manifests()
    assert len(qm['samples']) == 2 * problem_count
    assert len(em['samples']) == problem_count
    assert len({s['group'] for s in qm['samples']}) == problem_count
    assert len({s['group'] for s in em['samples']}) == problem_count
    assert all(s['label'] == pytest.approx(-.15) and s['sample_weight'] == 1 for s in em['samples'])
    assert {tuple(s['review_ids']) for s in em['samples']} == {(last['event_id'],) for _, _, last in saved}
    for state, first, last in saved:
        costs = [tid for s in qm['samples'] if s['run_id'] == state.run_id for tid in s['dimensions']['task_ids']]
        assert len(costs) == len(set(costs))
        before = outcomes.q_dataset('local', 'local', first['label_available_at'], include_synthetic=True)
        row = next(s for s in before['samples'] if s['run_id'] == state.run_id and s['terminal'])
        assert row['dimensions']['terminal_outcome']['total'] == pytest.approx(.3)
        feedback.revise(state.run_id, state.user_id, last['event_id'], consent_scope='PROJECT_ONLY',
                        reason='User corrects the normalized final rating.', value=-1., correct_value=True)
    qm, em = manifests()
    assert len(qm['samples']) == 2 * problem_count and len(em['samples']) == problem_count
    assert all(s['label'] == pytest.approx(-.3) for s in em['samples'])


def test_future_score_correction_and_privacy_withdrawal_have_distinct_cutoff_rules(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    candidate.transfer_conditions = ['Final conditions']
    final(state, candidate, 5, 'rated')
    original = events(state)[-1]
    cutoff = original['label_available_at']
    corrected = feedback.revise(state.run_id, state.user_id, original['event_id'],
        consent_scope='PROJECT_ONLY', reason='Score correction', value=-1., correct_value=True)
    assert manifests(cutoff)[1]['samples'][0]['label'] == pytest.approx(.3)
    assert manifests()[1]['samples'][0]['label'] == pytest.approx(-.3)
    feedback.revise(state.run_id, state.user_id, corrected, consent_scope='NO_TRAINING', reason='Withdraw this final feedback')
    current = feedback.current('local', 'local', cutoff, include_synthetic=True)
    assert original['event_id'] not in {r['event_id'] for r in current}
    assert corrected not in {r['event_id'] for r in current}


def test_same_design_preference_survives_review_invalidation_without_quality_promotion(adaptive_run, monkeypatch):
    state, candidate = reviewed_episode(adaptive_run, monkeypatch)
    final(state, candidate, 5, 'old-review')
    final_event = events(state)[-1]
    revision = dict(contract='current-review-projection-v2', revision=2, input_hash='changed-context')
    state.scratch['candidate_review_revisions'][candidate.id] = revision
    feedback.invalidate_review(state, candidate, revision)
    result = outcomes.outcome(events(state), state.scratch['ax_bundle']['run_contract']['feedback_settings'])
    assert result['masks'] == dict(concept_quality=False, user_utility=True)
    assert result['source_event_ids'] == [final_event['event_id']]
    assert result['total'] == pytest.approx(.3)


def test_final_precedence_is_per_candidate_not_per_shared_mechanism():
    settings = dict(quality_weight=.7, utility_weight=.3)
    common = dict(run_id='run', semantic_episode_id='episode', dimension='user_utility',
        mechanism_key='joint', reviewer_type='USER', observed_mask=True,
        label_available_at='2026-01-01', created_at='2026-01-01', review_revision={})
    final_row = dict(common, event_id='final', candidate_id='one', candidate_version='one-v1',
                     evaluation_stage='s10_feedback', observed_value=1.)
    kept_row = dict(common, event_id='kept', candidate_id='two', candidate_version='two-v1',
                    evaluation_stage='s7_user', observed_value=.1)
    result = outcomes.outcome([final_row, kept_row], settings)
    assert result['user_utility'] == pytest.approx(.55)
    assert result == outcomes.outcome([kept_row, final_row], settings)


def test_previous_projection_models_are_not_deployment_compatible():
    effect = dict(feature_schema=effect_ranker.UTILITY_SCHEMA, target_contract='candidate-utility-cost-v2')
    assert registry.compatible_model(effect) is False
    effect.update(candidate_projection_contract=CANDIDATE_PROJECTION, learning_integrity_contract=LEARNING_INTEGRITY)
    assert registry.compatible_model(effect)
    for schema in routing_q.ADAPTIVE_SCHEMAS:
        assert routing_q.contracts(schema)['candidate_projection_contract'] == CANDIDATE_PROJECTION
        assert routing_q.contracts(schema)['learning_integrity_contract'] == LEARNING_INTEGRITY
        model = dict(routing_q.contracts(schema), feature_schema=schema,
                     weights=[0.] * routing_q.DIMENSIONS, support={}, state_support={})
        assert registry.compatible_model(model)
        model.pop('candidate_projection_contract')
        assert not registry.compatible_model(model)


def test_pinned_old_effect_model_records_fallback_without_changing_saved_bundle(adaptive_run, monkeypatch):
    state, _ = reviewed_episode(adaptive_run, monkeypatch)
    model = dict(feature_schema=effect_ranker.UTILITY_SCHEMA,
                 target_contract='candidate-utility-cost-v2')
    bundle = state.scratch['ax_bundle']
    bundle.update(effect_ranker=model, effect_ranker_version='old-projection-model')
    effects = bundle['effects'][0]['effects']
    result = effect_history.rerank(state, effects, ['열 제거'])
    selection = list(state.scratch['ax_effect_selections'].values())[-1]
    assert selection['selection_method'] == 'LEXICAL_FALLBACK'
    assert selection['model_version'] is None
    assert selection['model_fallback_reason'] == 'incompatible_model_contract'
    assert all('model_score' not in effect['applicability_history'] for effect in result)
    assert bundle['effect_ranker'] == model
    assert bundle['effect_ranker_version'] == 'old-projection-model'


@pytest.mark.parametrize('same_review_revision', [False, True])
@pytest.mark.parametrize('other_uses_effect', [False, True])
def test_same_mechanism_other_candidate_cannot_change_effect_reward(
        adaptive_run, monkeypatch, same_review_revision, other_uses_effect):
    state, first = reviewed_episode(adaptive_run, monkeypatch)
    original = manifests()[1]['samples'][0]
    assert original['label'] == pytest.approx(.73)
    other = first.model_copy(deep=True)
    other.id = 'other-candidate'
    other.title = 'A separate candidate with its own effect adoption and rating'
    other.active_effect_ids = ['E1'] if other_uses_effect else []
    state.concepts.append(other)
    if same_review_revision:
        state.scratch['candidate_review_revisions'][other.id] = dict(
            state.scratch['candidate_review_revisions'][first.id])
    final(state, other, 1, 'other-candidate-final')
    other_event = events(state)[-1]
    qm, em = manifests()
    own = next(s for s in em['samples'] if s['application_id'] == original['application_id'])
    assert own['label'] == original['label']
    assert own['review_ids'] == original['review_ids']
    assert own['sample_weight'] == 1
    assert len(em['samples']) == (2 if other_uses_effect else 1)
    if other_uses_effect:
        other_sample = next(s for s in em['samples'] if s['application_id'] != own['application_id'])
        assert other_sample['label'] == pytest.approx(-.3)
        assert other_sample['review_ids'] == [other_event['event_id']]
        assert other_sample['sample_weight'] == 1
    # Track reward keeps its recorded-mechanism aggregation. The effect label
    # attributes only this candidate's observations to its saved applications.
    terminal = next(s for s in qm['samples'] if s['terminal'])
    result = terminal['dimensions']['terminal_outcome']
    assert len(result['components']) == 1
    assert result['total'] == pytest.approx(.565)


def test_invalidated_reported_test_cannot_create_observed_maturity_or_cost_only_q_sample(adaptive_run, monkeypatch):
    state, _ = reviewed_episode(adaptive_run, monkeypatch)
    source = events(state)[0]
    reported = dict(source, event_id='fixture-reported-test', dimension='reported_test_result',
                    evaluation_stage='recorded_test', reviewer_type='USER_REPORTED_TEST',
                    observed_value=1., observed_mask=True)
    invalidated = dict(reported, event_id='fixture-review-input-change',
                       dimension='review_validity', evaluation_stage='s6_input_invalidated',
                       observed_value=None, observed_mask=False,
                       review_revision=dict(contract='current-review-projection-v2', revision=2, input_hash='new-context'))
    rows = [reported, invalidated]
    summary = outcomes.outcome(rows, state.scratch['ax_bundle']['run_contract']['feedback_settings'])
    assert summary['masks'] == dict(concept_quality=False, user_utility=False)
    assert summary['source_event_ids'] == []
    assert summary['maturity'] == 'UNOBSERVED'
    monkeypatch.setattr(feedback, 'current', lambda *args, **kwargs: rows)
    assert ledger.budget(state.run_id)['spent_microusd'] > 0
    manifest = outcomes.q_dataset('local', 'local', include_synthetic=True)
    assert manifest['samples'] == []
    assert manifest['excluded']['unobserved_reward'] == 1
