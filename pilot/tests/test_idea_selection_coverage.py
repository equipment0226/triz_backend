import pytest

from triz import agent, digest, nodes
from triz.context import RunContext
from triz.schema import RawIdea, TechnicalContradiction


def test_unique_mechanisms_do_not_hide_later_tracks_within_fixed_cap():
    ideas = [RawIdea(track=track, idea=f'{track}-{n}', mechanism_key=f'{track}-{n}',
                     addresses=['TC1'])
             for track, count in [('A_MATRIX', 20), ('F_TRENDS', 2), ('G_FOS', 2), ('H_EFFECTS', 2)]
             for n in range(count)]
    selected = digest.select_ideas(ideas, 8)
    assert len(selected) == 8
    assert {i.track for i in selected[:4]} == {'A_MATRIX', 'F_TRENDS', 'G_FOS', 'H_EFFECTS'}
    assert len({i.id for i in selected}) == 8
    assert selected == digest.select_ideas(ideas, 8)


def test_track_balance_also_rotates_problems_and_mechanisms():
    ideas = [RawIdea(track='A', addresses=['TC1'], mechanism_key='repeat', idea=str(n)) for n in range(4)]
    independent = RawIdea(track='A', addresses=['TC1'], mechanism_key='independent')
    other_problem = RawIdea(track='A', addresses=['TC2'], mechanism_key='other')
    ideas += [independent, other_problem]
    selected = digest.select_ideas(ideas, 3)
    assert selected == [ideas[0], other_problem, independent]
    assert digest.select_ideas(ideas, 0) == []
    assert len(digest.select_ideas(ideas, 100)) == len(ideas)


@pytest.mark.parametrize('bundle', [None, {'limits': {}}, {'limits': {'portfolio_completion_v1': True}}])
def test_merge_preserves_unaccounted_ideas_for_all_bundle_generations(state, monkeypatch, bundle):
    if bundle is not None:
        state.scratch['ax_bundle'] = bundle
    tc = TechnicalContradiction()
    state.definition.technical_contradictions = [tc]
    first, omitted = [RawIdea(track=track, addresses=[tc.id], mechanism_key=track)
                      for track in ('A_MATRIX', 'H_EFFECTS')]
    state.solve.raw_ideas = [first, omitted]
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: {'ideas': [{'keep_ids': [first.id]}]})
    nodes._merge(RunContext(state))
    assert [i.id for i in state.solve.raw_ideas] == [first.id, omitted.id]
    assert state.scratch['ax_portfolio_trace'][-1]['unaccounted_preserved'] == 1


def test_repeated_merge_keeps_source_tracks_in_review_packet(state, monkeypatch):
    tc = TechnicalContradiction()
    state.definition.technical_contradictions = [tc]
    sources = [RawIdea(track=t, addresses=[tc.id], mechanism_key=t)
               for t in ('A_MATRIX', 'H_EFFECTS', 'G_FOS')]
    state.solve.raw_ideas = sources[:2]
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: {
        'ideas': [{'keep_ids': [i.id for i in state.solve.raw_ideas]}]})
    nodes._merge(RunContext(state))
    state.solve.raw_ideas.append(sources[2])
    nodes._merge(RunContext(state))
    merged = state.solve.raw_ideas[0]
    assert set(merged.source_idea_ids) == {i.id for i in sources}
    assert set(digest.idea_tracks(merged)) == {'A_MATRIX', 'H_EFFECTS', 'G_FOS'}
    packet = digest.idea_packet(merged)
    assert {s['source_track'] for s in packet['support']['source_details']} == {
        'A_MATRIX', 'H_EFFECTS', 'G_FOS'}
    assert set(packet['support']['source_tracks']) == {'A_MATRIX', 'H_EFFECTS', 'G_FOS'}


def test_shared_source_tracks_count_once_and_do_not_duplicate_merged_idea():
    merged = RawIdea(track='A', detail={'source_tracks': ['A', 'H']}, mechanism_key='merged')
    a, h, f = [RawIdea(track=t, mechanism_key=t) for t in ('A', 'H', 'F')]
    selected = digest.select_ideas([merged, a, h, f], 2)
    assert selected == [merged, f]
