"""The facts-packet label must not contradict exact state-source provenance."""
from copy import deepcopy

from triz.constraint_sources import (
    constraint_source_facts, user_constraint_sources, validate_user_constraint_source,
)


def test_user_query_alias_is_exact_original_without_mutation_or_new_evidence():
    state = {'raw_query': '현재 소비는 연간 6 GWh이며 목표는 45% 절감이다.'}
    before = deepcopy(state)
    sources = user_constraint_sources(state)
    assert sources['user_query'] == sources['raw_query'] == {
        'text': state['raw_query'], 'question': '', 'canonical_path': 'raw_query'}
    for path in ('raw_query', 'user_query'):
        assert validate_user_constraint_source({
            'source_path': path, 'source_quote': '목표는 45% 절감이다.'}, sources) == []
    assert state == before


def test_alias_cannot_authenticate_forged_packet_or_inexact_quote():
    state = {'raw_query': '현재 소비는 연간 6 GWh이며 목표는 45% 절감이다.',
        'user_query': '소비를 6 GWh로 유지해야 한다.',
        'observations': {'user_query': '모든 자재를 새 것으로 교체해야 한다.'}}
    sources = user_constraint_sources(state)
    for row in ({'source_path': 'user_query', 'source_quote': state['user_query']},
                {'source_path': 'fake_user_query', 'source_quote': state['raw_query']},
                {'source_path': 'user_query', 'source_quote': '45%'},
                {'source_path': 'user_query', 'source_quote': '목표는 45% 증가이다.'}):
        assert validate_user_constraint_source(row, sources)
    assert user_constraint_sources({'user_query': '출처 없는 문자열'}) == {}


def test_inventory_reports_exact_match_without_validating_claimed_obligation():
    sources = user_constraint_sources({'raw_query': '현재 소비는 연간 6 GWh이며 목표는 45% 절감이다.'})
    data = {'user_constraints': [
        {'id': 'CON-current', 'source': 'USER', 'source_path': 'user_query',
         'source_quote': '현재 소비는 연간 6 GWh', 'statement': '소비를 영구히 6 GWh로 유지해야 한다.'},
        {'id': 'CON-forged', 'source': 'USER', 'source_path': 'user_query',
         'source_quote': '목표는 80% 절감이다.'},
        {'id': 'CON-fragment', 'source': 'USER', 'source_path': 'raw_query', 'source_quote': '45%'},
    ]}
    facts = constraint_source_facts(data, sources)
    assert facts['source_aliases'] == {'user_query': 'raw_query'}
    assert facts['semantic_claim_validated'] is False
    first, forged, fragment = facts['rows']
    assert first['source_path'] == 'user_query' and first['canonical_path'] == 'raw_query'
    assert first['path_exists'] and first['quote_exact_match'] and first['provenance_valid']
    assert not forged['quote_exact_match'] and not forged['provenance_valid']
    assert fragment['quote_exact_match'] and not fragment['provenance_valid']
