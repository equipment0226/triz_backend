"""Full S7/S8 coverage under retired local and pinned candidate quotas."""
import copy

import pytest

from triz import agent, meeting, nodes
from triz.context import AbortRun, RunContext
from triz.execution_config import profile
from triz.schema import ConceptEvaluation, ConceptSpec, Constraint, ReviewerScore
from triz.settings import settings


def _portfolio(state, count=15):
    state.concepts = [ConceptSpec(id=f'C{i}', title=f'candidate {i}', quality_status='PASS',
        source_idea_ids=[f'I{i}'], working_principle=f'independent mechanism {i}') for i in range(count)]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id=c.id, total_score=4, rank=i+1)
                                   for i, c in enumerate(state.concepts)]


def _ranking(ids):
    return {'ranking': [{'concept_id': cid, 'rank': i+1} for i, cid in enumerate(ids)],
            'ranking_note': 'every retained candidate has a rank',
            'portfolio_note': 'validate each candidate before implementation', 'roadmap': []}


@pytest.mark.parametrize('old_cap', [8, 10])
@pytest.mark.parametrize('pinned', [False, True])
def test_rank_retains_all_15_despite_local_or_pinned_old_limits(state, monkeypatch, old_cap, pinned):
    _portfolio(state)
    original_ids = [c.id for c in state.concepts]
    old_config = copy.deepcopy(settings.triz)
    old_config['solutions'].update(max_solutions=old_cap, max_concepts=old_cap)
    bundle = {'config': old_config, 'limits': {'detailed_candidates': 3, 'presentation_target': 5},
              'rubrics': settings.rubrics}
    if pinned:
        state.scratch['ax_bundle'] = bundle
    else:
        monkeypatch.setitem(settings.triz, 'solutions', old_config['solutions'])
    token = profile.set(bundle if pinned else None)
    captured = []
    def rank(ctx, **kw):
        assert kw['node'] == 's8_rank'
        captured.append(kw['vars'])
        assert kw['checker'](_ranking(list(reversed(original_ids)))) == []
        return _ranking(list(reversed(original_ids)))
    monkeypatch.setattr(agent, 'run_agent', rank)
    try:
        assert settings.cfg('solutions.max_solutions') == old_cap
        nodes._rank(RunContext(state))
    finally:
        profile.reset(token)
    assert [c.id for c in state.concepts] == original_ids
    assert [e.concept_id for e in state.evaluation.evaluations] == list(reversed(original_ids))
    assert [e.rank for e in state.evaluation.evaluations] == list(range(1, 16))
    assert captured[0]['candidate_count'] == 15
    assert len(captured[0]['aggregate_table']) == len(captured[0]['concept_meta']) == 15
    assert 'max_solutions' not in captured[0]


@pytest.mark.parametrize('malformation', [
    'no_response', 'missing', 'duplicate_id', 'invented_id', 'duplicate_rank', 'boolean_rank', 'empty',
])
def test_incomplete_ranking_stops_and_preserves_all_candidates_and_evaluations(state, monkeypatch, malformation):
    _portfolio(state)
    before_concepts = copy.deepcopy(state.concepts)
    before_evaluations = copy.deepcopy(state.evaluation.evaluations)
    state.evaluation.ranking_note = 'existing review note'
    response = _ranking([c.id for c in state.concepts])
    if malformation == 'no_response':
        response = None
    elif malformation == 'missing':
        response['ranking'].pop()
    elif malformation == 'duplicate_id':
        response['ranking'][-1]['concept_id'] = response['ranking'][0]['concept_id']
    elif malformation == 'invented_id':
        response['ranking'][-1]['concept_id'] = 'FABRICATED'
    elif malformation == 'duplicate_rank':
        response['ranking'][-1]['rank'] = 1
    elif malformation == 'boolean_rank':
        response['ranking'][0]['rank'] = True
    else:
        response['ranking'] = []
    monkeypatch.setattr(agent, 'run_agent', lambda *args, **kwargs: response)
    with pytest.raises(AbortRun):
        nodes._rank(RunContext(state))
    assert state.concepts == before_concepts
    assert state.evaluation.evaluations == before_evaluations
    assert state.evaluation.ranking_note == 'existing review note'


def test_all_15_reach_gate_then_soft_and_hard_failures_are_excluded_before_full_ranking(state, monkeypatch):
    _portfolio(state)
    all_ids = [c.id for c in state.concepts]
    state.constraints.items = [
        Constraint(id='SOFT', statement='preferred noise limit', kind='PREFERENCE', hard=False,
                   source='DOMAIN', confidence=.6),
        Constraint(id='HARD', statement='no liquid contamination', kind='MUST_NOT_HAVE', hard=True),
    ]
    seen, batches, evaluated = [], [], []
    def respond(ctx, **kw):
        if kw['node'].startswith('s7_gate'):
            batch = kw['vars']['concepts_for_gate']
            batches.append(len(batch))
            seen.extend(c['concept_id'] for c in batch)
            assert {r['constraint_id'] for r in kw['vars']['constraints_full']} == {'SOFT', 'HARD'}
            # Deliberately misleading summary PASS: per-constraint failures must govern.
            return {'results': [{'concept_id': c['concept_id'], 'verdict': 'PASS',
                'per_constraint': [{'constraint_id': rule.id,
                    'verdict': 'FAIL' if (c['concept_id'], rule.id) in {('C0', 'SOFT'), ('C1', 'HARD')} else 'PASS',
                    'reason': 'explicit candidate condition checked against the saved requirement'}
                    for rule in state.constraints.items]} for c in batch]}
        assert kw['node'] == 's8_rank'
        ids = [row['concept_id'] for row in kw['vars']['aggregate_table']]
        assert set(ids) == set(all_ids) - {'C0', 'C1'}
        return _ranking(ids)
    def evaluate(ctx):
        evaluated.extend(c.id for c in ctx.state.concepts)
        return [ReviewerScore(concept_id=c.id, reviewer_role='engineering', dimension='FEASIBILITY',
                              score=4, confidence=.8, rationale='conditional technical assessment')
                for c in ctx.state.concepts]
    monkeypatch.setattr(agent, 'run_agent', respond)
    monkeypatch.setattr(meeting, 'evaluate', evaluate)
    monkeypatch.setitem(settings.triz['solutions'], 'max_solutions', 8)
    nodes.s7_gate(RunContext(state))
    assert sorted(seen) == sorted(all_ids)
    assert sum(batches) == 15 and max(batches) <= 2
    assert {c.id for c in state.concepts} == set(all_ids) - {'C0', 'C1'}
    diagnostics = {r['concept_id']: r for r in state.scratch['constraint_normalization']}
    assert diagnostics['C0']['soft_failure_ids'] == ['SOFT']
    assert diagnostics['C1']['hard_failure_ids'] == ['HARD']
    assert len(state.scratch['excluded_concepts']) == 2
    nodes.s8_evaluate(RunContext(state))
    assert set(evaluated) == set(all_ids) - {'C0', 'C1'}
    assert len(state.concepts) == len(state.evaluation.evaluations) == 13
    assert {e.concept_id for e in state.evaluation.evaluations} == set(evaluated)
