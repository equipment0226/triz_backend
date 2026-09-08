from types import SimpleNamespace

from triz import evidence
from triz.context import RunContext
from triz.schema import ConceptSpec
from triz.tools import bigquery_patents as bq
from scripts.refresh_project_patents import batches, plans_for, fingerprint


def test_historical_queries_keep_concept_mapping_and_deduplicate(state):
    concept = ConceptSpec(title='Seal')
    state.concepts = [concept]
    state.steps = [SimpleNamespace(node='s9_evidence_plan', output_json={'queries':[
        {'kind':'PATENT', 'query':'Spring Preload', 'concept_ids':[concept.id]},
        {'kind':'PATENT', 'query':'spring preload', 'concept_ids':['unknown']},
        {'kind':'PAPER', 'query':'paper lookup'}]})]
    state.scratch['search_cache'] = {'PATENT:thermal cooling':[], 'PAPER:paper lookup':[]}
    plans = plans_for(state)
    assert set(plans) == {'PATENT:spring preload','PATENT:thermal cooling'}
    assert plans['PATENT:spring preload']['concept_ids'] == [concept.id]


def test_all_99_queries_fit_two_bounded_batches():
    keys = [f'query {i}' for i in range(99)]
    groups = batches(keys)
    assert [len(g) for g in groups] == [50, 49]
    assert sorted(k for g in groups for k in g) == sorted(keys)
    for group in groups:
        assert bq._parameters(['spring preload '+k for k in group], 6)


def test_match_only_does_not_repeat_external_searches(state, monkeypatch):
    monkeypatch.setattr(evidence, 'discover', lambda ctx: (_ for _ in ()).throw(AssertionError('No repeated searches')))
    evidence.attach(RunContext(state), discover_sources=False)


def test_resume_signature_ignores_new_evidence_but_detects_changed_solution(state):
    concept = ConceptSpec(title='Seal')
    state.concepts = [concept]
    original = fingerprint(state)
    concept.evidence_ids.append('E1')
    concept.transfer_conditions.append('Check operating pressure')
    assert fingerprint(state) == original
    concept.working_principle = 'Changed mechanism'
    assert fingerprint(state) != original
