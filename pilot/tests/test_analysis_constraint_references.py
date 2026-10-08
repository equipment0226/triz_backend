from types import SimpleNamespace

import pytest

from triz import agent
from triz.analysis_checks import unknown_constraint_references as check
from triz.context import AbortRun, RunContext


def test_current_references_allow_korean_particles_and_reject_unknown_ids():
    assert not check({'statement': 'CON-1234abcd을 준수'}, ['CON-1234abcd'])
    assert check({'statement': 'CON-deadbeef으로 금지'}, ['CON-1234abcd'])
    assert not check({'CON-deadbeef': 'dictionary key is not a reference'}, [])


def test_new_constraint_declarations_need_explicit_caller_authorization():
    data = {'constraints': [{'id': 'CON-deadbeef'}], 'statement': 'CON-deadbeef'}
    assert check(data, [])
    assert not check(data, [], declared_constraint_ids=['CON-deadbeef'])


@pytest.mark.parametrize('kwargs,data', [
    ({'max_nodes': 2}, {'nested': [1, 2, 3]}),
    ({'max_chars': 5}, {'text': 'long output'}),
    ({'max_issues': 1}, ['CON-deadbeef', 'CON-1234abcd']),
])
def test_inspection_limit_never_turns_into_partial_pass(kwargs, data):
    assert check(data, [], **kwargs)


def test_analysis_node_checks_references_before_independent_review(state, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    monkeypatch.setattr(rag, 'lessons_block', lambda _: '')
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values: str(values))
    monkeypatch.setattr(agent, 'tracked_chat', lambda *a, **k: SimpleNamespace(
        data={'statement': 'CON-deadbeef requires zero downtime'}, meta={},
        text='', tokens_in=1, tokens_out=1, cost_usd=0., model='offline'))
    monkeypatch.setattr(agent, 'verify_artifact', lambda *a, **k: pytest.fail('Unknown ID reached semantic review'))
    with pytest.raises(AbortRun):
        agent.run_agent(RunContext(state), node='s4_ifr', label='IFR', stage='S4',
                        agent_id='triz_master', prompt_id='P_S4_IFR', rubric_id='R4_IFR', repair_attempts=0)
    assert state.steps[-1].status == 'FAILED'
    assert any('FATAL-CONSTRAINT-REF' in issue for issue in state.steps[-1].verdicts[-1]['revision_instructions'])
