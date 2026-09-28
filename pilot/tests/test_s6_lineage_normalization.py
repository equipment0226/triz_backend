"""A merged leaf objection is preserved without inventing another candidate."""
import copy
import pytest
from triz import quality, pipeline, store
from triz.context import ConceptReviewIncomplete, RunContext
from triz.schema import RawIdea


def example():
    idea = RawIdea(id='REP', title='Independent representative', source_idea_ids=['REP', 'LEAF'])
    data = {'concepts': [{'title': 'Independent concept', 'source_idea_ids': ['REP'],
                         'open_risks': ['Existing risk']}],
            'excluded': [{'source_idea_ids': ['LEAF'], 'reason': 'Merged source has an unconfirmed operating condition.'}]}
    return idea, data


def test_merged_leaf_objection_reaches_independent_audit_and_remains_traceable(state, monkeypatch):
    idea, raw = example()
    original = copy.deepcopy(raw)
    state.solve.raw_ideas = [idea]
    seen = []
    def generate(ctx, **kwargs):
        result = kwargs['normalizer'](raw)
        assert kwargs['checker'](result) == []
        return result
    def audit(ctx):
        seen.extend(ctx.state.concepts)
        assert all(c.quality_status == 'UNVERIFIED' for c in ctx.state.concepts)
    monkeypatch.setattr(quality.agent, 'run_agent', generate)
    monkeypatch.setattr(quality, 'audit_concepts', audit)
    monkeypatch.setattr(quality.rag, 'prior_cases_block', lambda _: '')
    quality._generate_concepts(RunContext(state), ideas_override=[idea])
    assert len(seen) == 1 and seen[0].source_idea_ids == ['REP']
    assert original['excluded'][0]['reason'] in seen[0].open_risks[-1]
    assert state.scratch['excluded_concepts'] == []
    note = state.scratch['s6_lineage_reviews'][seen[0].id][0]
    assert note == {'representative_id': 'REP', 'source_idea_id': 'LEAF',
                    'original_exclusion': original['excluded'][0]}
    assert raw == original


def test_normalization_is_idempotent_and_does_not_change_the_paid_response():
    idea, raw = example()
    before = copy.deepcopy(raw)
    normalized = quality.normalize_concept_lineage(raw, [idea])
    assert quality.check_concept_batch(normalized, {'REP'}) == []
    assert quality.normalize_concept_lineage(normalized, [idea]) == normalized
    assert len(normalized['source_lineage_reviews']) == 1
    assert len(normalized['concepts'][0]['open_risks']) == 2
    assert raw == before


@pytest.mark.parametrize('case', ['unknown', 'missing_parent', 'duplicate_parent', 'duplicate_leaf',
    'other_representative', 'ambiguous_leaf', 'leaf_concept', 'missing_reason', 'invalid_schema',
    'other_assigned_missing', 'invalid_risks', 'invalid_row'])
def test_uncertain_or_incomplete_dispositions_remain_invalid(case):
    idea, raw = example()
    assigned, portfolio = [idea], [idea]
    if case == 'unknown': raw['excluded'][0]['source_idea_ids'] = ['UNKNOWN']
    if case == 'missing_parent': raw['concepts'] = []
    if case == 'duplicate_parent': raw['concepts'].append(copy.deepcopy(raw['concepts'][0]))
    if case == 'duplicate_leaf': raw['excluded'].append(copy.deepcopy(raw['excluded'][0]))
    if case == 'other_representative': portfolio = [idea, RawIdea(id='LEAF', title='Another representative')]
    if case == 'ambiguous_leaf': portfolio = [idea, RawIdea(id='OTHER', title='Another', source_idea_ids=['LEAF'])]
    if case == 'leaf_concept': raw['concepts'][0]['source_idea_ids'] = ['LEAF']
    if case == 'missing_reason': raw['excluded'][0]['reason'] = ''
    if case == 'invalid_schema': raw['concepts'][0]['change_scale'] = 'INVENTED_ENUM'
    if case == 'other_assigned_missing': assigned = [idea, RawIdea(id='OTHER', title='Another')]
    if case == 'invalid_risks': raw['concepts'][0]['open_risks'] = 'wrong-shape'
    if case == 'invalid_row': raw['concepts'].append(None)
    before = copy.deepcopy(raw)
    result = quality.normalize_concept_lineage(raw, assigned, portfolio)
    assert result == before and raw == before
    assert quality.check_concept_batch(result, {i.id for i in assigned})


def test_safe_interruption_explains_validation_without_internal_ids(state, monkeypatch):
    def invalid_response(ctx):
        raise ConceptReviewIncomplete()
    monkeypatch.setattr(pipeline, 'PIPELINE', [('s6_concept', 'Concept review', invalid_response)])
    state.status = 'RUNNING'
    state.control.stage_index = 0
    store.save_state(state)
    pipeline.execute_stage(state.run_id, 0)
    saved = store.load_state(state.run_id)
    assert saved.status == 'INTERRUPTED'
    assert saved.scratch['interruption_reason'] == str(ConceptReviewIncomplete())
    assert '원안 연결' in saved.scratch['interruption_reason']
    assert 'FATAL-' not in saved.scratch['interruption_reason']


@pytest.mark.parametrize('notes', [None, 17, {}, 'not-a-list'])
def test_optional_non_list_lineage_metadata_does_not_interrupt_valid_candidates(state, monkeypatch, notes):
    idea, raw = example()
    raw['excluded'] = []
    raw['source_lineage_reviews'] = notes
    state.solve.raw_ideas = [idea]
    monkeypatch.setattr(quality.agent, 'run_agent', lambda ctx, **kw: kw['normalizer'](raw))
    monkeypatch.setattr(quality, 'audit_concepts', lambda ctx: None)
    monkeypatch.setattr(quality.rag, 'prior_cases_block', lambda _: '')
    quality._generate_concepts(RunContext(state), ideas_override=[idea])
    assert len(state.concepts) == 1
    assert state.concepts[0].source_idea_ids == ['REP']
    assert not state.scratch.get('s6_lineage_reviews')
