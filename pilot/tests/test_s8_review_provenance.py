"""Policy-only WARN is accepted only through complete current meeting evidence."""
import copy
import pytest
from test_ax_refactor import newrun
from test_unified_feedback_adaptive import adaptive_run, events
from test_unified_feedback_learning import isolated_learning_database
from test_ai_effect_reward_projection import ai_reviewed_run
from triz import meeting, personas
from triz.ax import feedback_events, learning_outcomes
from triz.context import RunContext
from triz.schema import Persona
from triz.settings import settings


@pytest.fixture
def completed_review(adaptive_run, monkeypatch):
    state = ai_reviewed_run(adaptive_run, monkeypatch)
    monkeypatch.setitem(settings.triz['evaluation'], 'mode', 'independent')
    # This is the actual production policy: optional R8 rubric verification is
    # skipped after the deterministic complete score-matrix checker succeeds.
    critical = [key for key in settings.cfg('verification.critical_rubrics', []) if key != 'R8_REVIEW']
    monkeypatch.setitem(settings.triz['verification'], 'critical_rubrics', critical)
    roles = [Persona(persona_id='A', role_name='Technical reviewer', dimensions=['FEASIBILITY']),
             Persona(persona_id='B', role_name='Outcome reviewer', dimensions=['GOAL'])]
    monkeypatch.setattr(personas, 'build_personas', lambda ctx: roles)
    scores = meeting.evaluate(RunContext(state))
    steps = [step for step in state.steps if step.node == 's8_review_independent']
    assert len(scores) == len(steps) == 2
    assert all(step.status == 'WARN' and step.verdicts[-1]['source'] == 'policy' for step in steps)
    assert state.evaluation.meeting.status == 'COMPLETED'
    assert len(feedback_events.meeting_review_sources(state, scores)) == 2
    return state, scores, steps


def test_completed_policy_warn_scores_enter_ai_effect_reward_without_user_feedback(completed_review):
    state, scores, steps = completed_review
    before = copy.deepcopy(state.evaluation.meeting.model_dump())
    feedback_events.meeting_reviews(state, scores)
    rows = events(state)
    actual = [row for row in rows if row['dimension'] == 'evaluation_quality']
    assert len(actual) == 2
    assert all(row['observed_value'] == .5 and row['active_effect_ids'] == ['E1'] for row in actual)
    assert {row['source_step_id'] for row in actual} == {step.step_id for step in steps}
    assert all(row['reviewer_model_and_rubric_version']['source_status'] == 'WARN' for row in actual)
    assert not any(row['dimension'] == 'user_utility' for row in rows)
    manifest = learning_outcomes.effect_dataset('local', 'local', include_synthetic=True)
    assert len(manifest['samples']) == 1, manifest
    sample = manifest['samples'][0]
    assert sample['label'] == pytest.approx(.35)  # .7 * min(S6=1, coverage=1, S8=.5)
    assert {row['event_id'] for row in actual} <= set(sample['review_ids'])
    assert sample['maturity'] == 'MODEL_REVIEW_PROXY'
    assert state.evaluation.meeting.model_dump() == before
    feedback_events.meeting_reviews(state, scores)
    assert events(state) == rows  # immutable observation identity prevents amplification


@pytest.mark.parametrize('case', ['failed', 'running_step', 'ordinary_warn', 'fatal', 'error',
    'wrong_persona', 'wrong_node', 'partial_output', 'partial_comments', 'unaccepted', 'wrong_hash', 'source_mismatch'])
def test_bad_source_is_not_accepted_merely_because_meeting_finished(completed_review, case):
    state, scores, steps = completed_review
    step = next(step for step in steps if step.agent_id == 'persona::A')
    key = 'independent:A'
    if case == 'failed': step.status = 'FAILED'
    elif case == 'running_step': step.status = 'RUNNING'
    elif case == 'ordinary_warn': step.verdicts[-1] = {'verdict': 'REVISE', 'source': 'deterministic'}
    elif case == 'fatal': step.verdicts[-1]['fatal_flaws'] = ['Fatal review flaw']
    elif case == 'error': step.error = 'Provider failed'
    elif case == 'wrong_persona': step.agent_id = 'persona::other'
    elif case == 'wrong_node': step.node = 's8_review_initial'
    elif case == 'partial_output': step.output_json['scores'] = []
    elif case == 'partial_comments': step.output_json['concept_comments'] = {}
    elif case == 'unaccepted': state.evaluation.meeting.completed_calls.pop(key)
    elif case == 'wrong_hash': state.evaluation.meeting.completed_call_inputs[key] = 'superseded-call'
    else: step.output_json['scores'][0]['rationale'] = 'Different original response'
    accepted = feedback_events.meeting_review_sources(state, scores)
    assert len(accepted) == 1 and accepted[0][1]['reviewer_role'] == 'Outcome reviewer'
    feedback_events.meeting_reviews(state, scores)
    learned = [row for row in events(state) if row['dimension'] == 'evaluation_quality']
    assert len(learned) == 1 and learned[0]['reviewer_type'].startswith('Outcome reviewer:')


@pytest.mark.parametrize('case', ['partial_meeting', 'missing_final', 'changed_candidate', 'wrong_episode', 'wrong_epoch'])
def test_partial_or_changed_meeting_context_abstains(completed_review, case):
    state, scores, _ = completed_review
    if case == 'partial_meeting': state.evaluation.meeting.status = 'RUNNING'
    elif case == 'missing_final': state.evaluation.meeting.final_reviews.pop()
    elif case == 'changed_candidate': state.concepts[0].working_principle = 'Changed current design'
    elif case == 'wrong_episode': state.scratch['semantic_episode_id'] += ':new'
    else: state.scratch['execution_epoch'] += 1
    assert feedback_events.meeting_review_sources(state, scores) == []
    before = events(state)
    feedback_events.meeting_reviews(state, scores)
    assert events(state) == before


@pytest.mark.parametrize('value', [0, 6, float('nan'), True, '4'])
def test_malformed_raw_score_is_not_clamped_into_learning(completed_review, value):
    state, scores, steps = completed_review
    step = next(step for step in steps if step.agent_id == 'persona::A')
    step.output_json['scores'][0]['score'] = value
    state.evaluation.meeting.completed_calls['independent:A']['scores'][0]['score'] = value
    accepted = feedback_events.meeting_review_sources(state, scores)
    assert len(accepted) == 1 and accepted[0][1]['reviewer_role'] == 'Outcome reviewer'


def test_unaccepted_superseded_and_wrong_persona_score_arguments_are_excluded(completed_review):
    state, scores, _ = completed_review
    raw = next(score for score in scores if score.reviewer_role == 'Technical reviewer')
    for changes in ({'score': 5}, {'rationale': 'Superseded score'}, {'reviewer_role': 'Unknown reviewer'}):
        assert feedback_events.meeting_review_sources(state, [raw.model_copy(update=changes)]) == []


@pytest.mark.parametrize('case', ['missing_final_score', 'duplicate_final_score', 'missing_accepted_score', 'missing_accepted_comments'])
def test_completed_role_requires_the_entire_exact_final_score_matrix(completed_review, case):
    state, scores, _ = completed_review
    final = next(review for review in state.evaluation.meeting.final_reviews if review.reviewer_id == 'A')
    if case == 'missing_final_score': final.scores.pop()
    elif case == 'duplicate_final_score': final.scores.append(final.scores[0].model_copy(deep=True))
    elif case == 'missing_accepted_score': state.evaluation.meeting.completed_calls['independent:A']['scores'].pop()
    else: state.evaluation.meeting.completed_calls['independent:A']['concept_comments'] = {}
    accepted = feedback_events.meeting_review_sources(state, scores)
    assert len(accepted) == 1 and accepted[0][1]['reviewer_role'] == 'Outcome reviewer'
