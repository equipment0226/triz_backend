"""RAG index changes must not bypass an unchanged, already-paid S6 request."""
import copy
import json
import re

import pytest
from sqlalchemy import select, update
from test_ax_refactor import newrun
from triz import digest, llm, quality, rag, store
from triz.ax import ledger
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea, Constraint
from triz.settings import settings


def saved_prior(state):
    return quality._saved_prior_replay(state, state.solve.raw_ideas,
        digest.facts_packet(state), digest.contradictions_digest(state), 3)


@pytest.mark.parametrize('original_prior', ['', 'Recorded historical case input; score=0.912'])
def test_paid_replay_preserves_changed_retrieval_bytes_and_batch_boundaries(newrun, monkeypatch, original_prior):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 0)
    monkeypatch.setitem(settings.triz['run'], 'parallel_workers', 1)
    monkeypatch.setitem(settings.triz['feedback_rag'], 'max_influenced_concepts', 3)
    state = newrun()
    state.scratch['ax_bundle'].pop('concept_effect_contract', None)
    ideas = [RawIdea(id=f'R{i}', title=f'Representative {i}', idea=f'Mechanism {i}',
                    source_idea_ids=[f'R{i}', f'L{i}']) for i in range(6)]
    state.solve.raw_ideas = ideas
    retrieved = []
    def retrieve(_):
        retrieved.append(original_prior)
        return original_prior
    monkeypatch.setattr(rag, 'prior_cases_block', retrieve)
    requests = []
    def provider(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        ids = sorted(set(re.findall(r'"id":\s*"(R\d+)"', kwargs['user'])))
        assert ids
        result = {'concepts': [{'title': ident, 'source_idea_ids': [ident]} for ident in ids],
                  'excluded': [{'source_idea_ids': ['L0'], 'reason': 'Original source objection'}] if 'R0' in ids else []}
        return llm.LLMResult(data=result, text=json.dumps(result), model='offline-fixture',
                             cost_usd=.000123, tokens_in=10, tokens_out=20)
    monkeypatch.setattr(llm, 'chat_json', provider)
    monkeypatch.setattr(quality, 'audit_concepts', lambda ctx: None)
    with monkeypatch.context() as old:
        old.setattr(quality, 'normalize_concept_lineage', lambda data, *args: data)
        with pytest.raises(AbortRun):
            quality._generate_concepts(RunContext(state), ideas_override=ideas)
    before = [copy.deepcopy(step.input_slice) for step in state.steps if step.node == 's6_concept']
    assert len(before) == 2 and len(requests) == 2
    assert [len(row['vars']['ideas']) for row in before] == ([3, 3] if original_prior else [5, 1])
    assert saved_prior(state) == original_prior
    cost_before = ledger.budget(state.run_id)['spent_microusd']
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline prior replay')
    # An index refresh would change both the bytes and, for an empty old block,
    # the batch sizes. Unchanged paid inputs must bypass fresh retrieval.
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: pytest.fail('Historical paid replay retrieved new RAG'))
    monkeypatch.setattr(llm, 'chat_json', lambda **kw: pytest.fail('Historical paid replay called provider'))
    quality._generate_concepts(RunContext(state), ideas_override=ideas)
    after = [step.input_slice for step in state.steps if step.node == 's6_concept'][-2:]
    assert after == before
    assert len(state.concepts) == 6 and len(requests) == 2 and len(retrieved) == 1
    assert ledger.budget(state.run_id)['spent_microusd'] == cost_before
    with store.engine.connect() as connection:
        assert len(connection.execute(select(ledger.tasks.c.task_id)
            .where(ledger.tasks.c.run_id == state.run_id)).all()) == 2


@pytest.fixture
def completed_legacy(newrun, monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    state = newrun()
    state.scratch['ax_bundle'].pop('concept_effect_contract', None)
    state.solve.raw_ideas = [RawIdea(id='R', title='Saved source', idea='Saved mechanism')]
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: 'Recorded historical case')
    monkeypatch.setattr(quality, 'audit_concepts', lambda ctx: None)
    monkeypatch.setattr(llm, 'chat_json', lambda **kw: llm.LLMResult(
        data={'concepts': [{'title': 'Saved concept', 'source_idea_ids': ['R']}], 'excluded': []},
        text='', model='offline-fixture', cost_usd=.0001, tokens_in=1, tokens_out=1))
    quality._generate_concepts(RunContext(state), ideas_override=state.solve.raw_ideas)
    assert saved_prior(state) == 'Recorded historical case'
    return state


@pytest.mark.parametrize('change', ['idea', 'constraints', 'domain', 'injection', 'model', 'episode', 'new_contract'])
def test_changed_inputs_and_new_contract_do_not_freeze_old_retrieval(completed_legacy, change):
    state = completed_legacy
    if change == 'idea':
        state.solve.raw_ideas[0].idea = 'Changed mechanism'
    elif change == 'constraints':
        state.constraints.items = [Constraint(statement='New confirmed constraint')]
    elif change == 'domain':
        state.domain.operating_env = 'New confirmed environment'
    elif change == 'injection':
        state.control.injected_agents['s6_concept'] = [{'instruction': 'New expert requirement'}]
    elif change == 'model':
        state.scratch['ax_bundle']['models']['T2']['model'] = 'Changed model'
    elif change == 'episode':
        state.scratch['semantic_episode_id'] += ':changed'
    else:
        state.scratch['ax_bundle']['concept_effect_contract'] = 'explicit-active-effects-v1'
    assert saved_prior(state) is None


def test_historical_step_without_completed_task_does_not_freeze_retrieval(completed_legacy):
    state = completed_legacy
    with ledger.transaction() as connection:
        connection.execute(update(ledger.tasks).where(ledger.tasks.c.run_id == state.run_id)
                           .values(status='UNKNOWN'))
    assert saved_prior(state) is None


def test_changed_input_actually_retrieves_current_cases(completed_legacy, monkeypatch):
    state = completed_legacy
    state.domain.operating_env = 'Changed confirmed environment'
    retrieved = []
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: retrieved.append(True) or 'Current corrected cases')
    quality._generate_concepts(RunContext(state), ideas_override=state.solve.raw_ideas)
    assert retrieved == [True]
    assert state.steps[-1].input_slice['vars']['prior_cases_block'] == 'Current corrected cases'
