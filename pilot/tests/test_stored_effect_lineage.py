"""Saved source resolution, without a model or historical adoption inference."""
import copy
import pytest
from triz.schema import RawIdea, ConceptSpec
from triz.ax.source_lineage import trace
from triz.ax.action_runtime import candidate_actions
from triz.ax import effect_history
from test_ax_refactor import newrun


def effect_leaf(ident='leaf', effect='E1'):
    return dict(id=ident, source_idea_id=ident, source_track='H_EFFECTS',
                source_effect_id=effect, idea='saved conduction source')


def test_current_representative_preserves_same_id_original_leaf(state):
    original = effect_leaf('first')
    other = effect_leaf('second', 'E2')
    state.solve.raw_ideas = [RawIdea(id='first', title='merged',
        source_idea_ids=['first', 'second'],
        detail={'source_details': [original, other]})]
    before = copy.deepcopy(state.model_dump())
    result = trace(state, ['first'])
    assert result['complete']
    assert result['leaves'] == ['first', 'second']
    assert result['records']['first']['source_effect_id'] == 'E1'
    assert result['records']['second']['source_effect_id'] == 'E2'
    assert state.model_dump() == before


def test_self_only_source_is_a_leaf_not_a_cycle(state):
    state.solve.raw_ideas = [RawIdea(id='leaf', source_idea_ids=['leaf'],
                                    detail={'source_effect_id': 'E1'})]
    result = trace(state, ['leaf'])
    assert result['complete'] and result['leaves'] == ['leaf']
    assert result['cycles'] == []


def test_retained_repair_resolves_old_representative_and_producer(state):
    state.scratch['ax_idea_inventory'] = [
        {'id': 'old', 'source_idea_ids': ['middle']},
        {'id': 'middle', 'source_idea_ids': ['leaf']}, effect_leaf()]
    state.solve.raw_ideas = [RawIdea(id='new', title='current unrelated source')]
    state.scratch['ax_action_results'] = {
        'producer': {'produced_raw_idea_ids': ['leaf']},
        'unrelated': {'produced_raw_idea_ids': ['new']}}
    candidate = ConceptSpec(id='repair', source_idea_ids=['old'])
    result = trace(state, candidate.source_idea_ids)
    assert result['complete'] and result['leaves'] == ['leaf']
    assert candidate_actions(state, candidate) == ['producer']
    assert candidate.active_effect_ids == []


def test_nested_source_details_are_traced_from_saved_packets(state):
    state.solve.raw_ideas = [RawIdea(id='current', detail={'source_details': [
        {'source_idea_id': 'middle', 'source_details': [effect_leaf()]}]})]
    result = trace(state, ['current'])
    assert result['complete'] and result['leaves'] == ['leaf']
    assert result['records']['leaf']['source_effect_id'] == 'E1'
    from triz.ax import concept_effects
    sources = concept_effects.sources(state, ['current'])
    assert len(sources) == 1
    assert sources[0]['source_idea_id'] == 'leaf'
    assert sources[0]['source_effect_id'] == 'E1'


@pytest.mark.parametrize('broken,expected', [
    ([{'id': 'old', 'source_idea_ids': ['missing', 'leaf']}, effect_leaf()],
     {'missing': ['missing'], 'cycles': []}),
    ([{'id': 'old', 'source_idea_ids': ['middle', 'leaf']},
      {'id': 'middle', 'source_idea_ids': ['old']}, effect_leaf()],
     {'missing': [], 'cycles': ['old']}),
])
def test_incomplete_ancestry_does_not_infer_producer(state, broken, expected):
    state.scratch['ax_idea_inventory'] = broken
    state.scratch['ax_action_results'] = {
        'producer': {'produced_raw_idea_ids': ['leaf']},
        'direct': {'candidate_ids': ['repair']}}
    candidate = ConceptSpec(id='repair', source_idea_ids=['old'])
    result = trace(state, ['old'])
    assert not result['complete']
    for field, value in expected.items():
        assert result[field] == value
    assert candidate_actions(state, candidate) == ['direct']


def test_conflicting_saved_effect_records_abstain(state):
    state.solve.raw_ideas = [RawIdea(id='rep', detail={'source_details': [
        effect_leaf('leaf', 'E1'), effect_leaf('leaf', 'E2')]})]
    result = trace(state, ['rep'])
    assert not result['complete'] and result['conflicts'] == ['leaf']


def test_effect_collection_links_prior_representative_without_claiming_adoption(newrun):
    state = newrun()
    state.scratch['ax_idea_inventory'] = [
        {'id': 'old', 'source_idea_ids': ['middle']},
        {'id': 'middle', 'detail': {'source_details': [effect_leaf()]}},
        effect_leaf()]
    state.solve.raw_ideas = [RawIdea(id='new', title='unrelated replacement')]
    state.scratch['ax_action_results'] = {'producer': {'produced_raw_idea_ids': ['leaf']}}
    state.concepts = [ConceptSpec(id='repair', source_idea_ids=['old'])]
    apps = effect_history.collect(state)
    linked = [app for app in apps if app['candidate_id'] == 'repair']
    assert len(linked) == 1
    assert linked[0]['source_raw_idea_ids'] == ['leaf']
    assert linked[0]['action_instance_ids'] == ['producer']
    assert linked[0]['effect_id'] == 'E1'
    assert linked[0]['candidate_snapshot']['active_effect_ids'] == []
    assert state.concepts[0].active_effect_ids == []


def test_effect_collection_does_not_link_broken_ancestry(newrun):
    state = newrun()
    state.scratch['ax_idea_inventory'] = [
        {'id': 'old', 'source_idea_ids': ['missing', 'leaf']}, effect_leaf()]
    state.concepts = [ConceptSpec(id='repair', source_idea_ids=['old'], active_effect_ids=['E1'])]
    apps = effect_history.collect(state)
    assert apps and all(app['candidate_id'] is None for app in apps)


def test_common_feedback_keeps_both_explicit_merged_effects(newrun):
    from triz.ax import feedback_events
    state = newrun()
    state.solve.raw_ideas = [RawIdea(id='first', title='merged',
        source_idea_ids=['first', 'second'], detail={'source_details': [
            effect_leaf('first', 'E1'), effect_leaf('second', 'E2')]})]
    state.scratch['ax_action_results'] = {
        'first-producer': {'produced_raw_idea_ids': ['first']},
        'second-producer': {'produced_raw_idea_ids': ['second']}}
    candidate = ConceptSpec(id='candidate', source_idea_ids=['first'],
                            active_effect_ids=['E1', 'E2'])
    state.concepts = [candidate]
    apps = effect_history.collect(state)
    observed = feedback_events.lineage(state, candidate)
    assert observed['source_raw_idea_ids'] == ['first', 'second']
    assert observed['source_action_instance_ids'] == ['first-producer', 'second-producer']
    assert observed['active_effect_ids'] == ['E1', 'E2']
    assert observed['active_effect_application_ids'] == sorted(app['application_id'] for app in apps)
    assert observed['attribution'] == 'OBSERVED_JOINT_LINEAGE'
    # An outcome change requires an exact new application snapshot; an old
    # application must not silently stand in for the current candidate.
    candidate.quality_status = 'PASS'
    assert feedback_events.lineage(state, candidate)['active_effect_ids'] == []
    effect_history.collect(state)
    assert feedback_events.lineage(state, candidate)['active_effect_ids'] == ['E1', 'E2']
