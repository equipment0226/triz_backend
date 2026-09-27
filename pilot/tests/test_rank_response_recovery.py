"""Keep full S8 responses when a provider adds stray closing brackets."""
import copy
import json

import pytest

from test_full_candidate_ranking import _portfolio, _ranking
from triz import agent, llm, nodes
from triz.context import AbortRun, RunContext


def response(count=10):
    data = _ranking([f'C{i}' for i in range(count)])
    data['ranking_note'] = 'Check a literal ] and an escaped "quote" before approval.'
    data['portfolio_note'] = 'Validate all candidates.'
    data['roadmap'] = [{'phase': 'short', 'concept_id': 'C0',
                        'precondition': 'Measure takt time', 'owner': 'engineering'}]
    raw = json.dumps(data).replace(', "portfolio_note":', '], "portfolio_note":')
    raw = raw.replace(', "roadmap":', '], "roadmap":')
    return data, raw


@pytest.mark.parametrize('wrapper', ['{}', '```json\n{}\n```', 'Result:\n{}\nEnd.'])
def test_extra_closers_preserve_every_row_and_all_metadata(wrapper):
    expected, raw = response()
    assert llm.extract_json(wrapper.format(raw)) == expected


@pytest.mark.parametrize('raw', [
    '{"ranking":[{"concept_id":"C0","rank":1}],"ranking_note":unknown}',
    '{"ranking":[{"concept_id":"C0","rank":1}],"ranking_note":}',
    '{"ranking":[{"concept_id":"C0","rank":1}],}',
    '{"ranking":[{"concept_id":"C0","rank":1}],"note":"a"],"b":"b"],"c":"c"]}',
])
def test_invalid_root_is_not_replaced_by_nested_ranking(raw):
    with pytest.raises(ValueError):
        llm.extract_json(raw)


def test_valid_root_array_with_surrounding_prose_keeps_all_objects():
    assert llm.extract_json('Result: [{"a":1},{"a":2}]') == [{'a': 1}, {'a': 2}]


@pytest.mark.parametrize('durable_old_parser', [False, True])
def test_real_ranking_path_recovers_all_ten_without_paid_repair(state, monkeypatch, durable_old_parser):
    _portfolio(state, 10)
    expected, raw = response()
    requests = []

    def chat(ctx, **kwargs):
        requests.append(kwargs)
        data = copy.deepcopy(expected['ranking']) if durable_old_parser else llm.extract_json(raw)
        return llm.LLMResult(data=data, text=raw, model='offline',
                             meta={'durable_replay': durable_old_parser})

    monkeypatch.setattr(agent, 'tracked_chat', chat)
    nodes._rank(RunContext(state))
    assert len(requests) == 1
    assert [e.concept_id for e in state.evaluation.evaluations] == [f'C{i}' for i in range(10)]
    assert [e.rank for e in state.evaluation.evaluations] == list(range(1, 11))
    assert state.evaluation.ranking_note == expected['ranking_note']
    assert state.evaluation.portfolio_note == expected['portfolio_note']
    assert state.evaluation.roadmap == expected['roadmap']
    assert state.steps[-1].status == 'OK'
    assert state.steps[-1].output_json == expected


def test_recovered_syntax_does_not_accept_missing_candidate(state, monkeypatch):
    _portfolio(state, 10)
    _, raw = response(9)
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **kw:
        llm.LLMResult(data=llm.extract_json(raw), text=raw, model='offline'))
    with pytest.raises(AbortRun):
        nodes._rank(RunContext(state))
    assert len(state.concepts) == len(state.evaluation.evaluations) == 10


@pytest.mark.parametrize('data,expected', [
    ([{'rank': 1}, {'rank': 2}], {'items': [{'rank': 1}, {'rank': 2}]}),
    ([{'rank': 1}, 'unparsed'], {'items': [{'rank': 1}, 'unparsed']}),
    ([{'ranking': []}, {'ranking_note': 'note'}], {'ranking': [], 'ranking_note': 'note'}),
])
def test_object_coercion_never_overwrites_repeated_rows(state, monkeypatch, data, expected):
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **kw: llm.LLMResult(data=data, model='offline'))
    result = agent.run_agent(RunContext(state), node='s8_rank', label='Rank', stage='S8',
        agent_id='portfolio_manager', prompt_id='P_S8_RANK', vars={})
    assert result == expected
