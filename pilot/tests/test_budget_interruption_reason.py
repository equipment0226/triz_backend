"""Reservation refusal is public and auditable; replay never spends a second time."""
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from triz import agent, llm, pipeline, store
from triz.ax import WORKFLOW, gateway, ledger
from triz.ax.contracts import BudgetBusy, Conflict
from triz.context import BudgetExhausted, RunContext, UsageUncertain
from triz.settings import settings


@pytest.fixture
def budget_run(monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'hard_budget_usd', 6)
    state = pipeline.create_run('Offline reservation refusal fixture', workflow_version=WORKFLOW)
    state.scratch['ax_bundle']['limits']['validation_reserve_microusd'] = 120000
    state.scratch['ax_bundle']['config']['ax']['max_provider_attempts'] = 1
    state.scratch['ax_bundle']['models']['T2'].update(cost_in=0, cost_out=1)
    return state


def spend(state, amount, request=None):
    task = ledger.acquire(state.run_id, 0, request or {'fixture': 'settled'}, amount)
    ledger.settle(task, {}, amount)
    return task


def task_count(state):
    with store.engine.connect() as connection:
        return len(connection.execute(select(ledger.tasks.c.task_id)
            .where(ledger.tasks.c.run_id == state.run_id)).all())


def test_exact_shortfall_is_observed_before_any_task_is_created(budget_run):
    spend(budget_run, 5787587)
    before = ledger.budget(budget_run.run_id)
    with pytest.raises(ledger.BudgetRejected, match='required validation reserve retained') as caught:
        ledger.acquire(budget_run.run_id, 0, {'node': 's5_ariz_p1'}, 98603, minimum_remaining=120000)
    assert isinstance(caught.value, Conflict)
    assert caught.value.details == {
        'reason_code': 'BUDGET_RESERVATION_REJECTED', 'scope': 'project', 'node': 's5_ariz_p1',
        'limit_microusd': 6000000, 'spent_microusd': 5787587, 'reserved_microusd': 0,
        'requested_microusd': 98603, 'validation_reserve_microusd': 120000,
        'remaining_microusd': 212413, 'shortfall_microusd': 6190,
    }
    assert ledger.budget(budget_run.run_id) == before
    assert task_count(budget_run) == 1


@pytest.mark.parametrize('status', ['RUNNING', 'UNKNOWN'])
def test_temporary_reservations_and_unknown_usage_remain_distinct(budget_run, status):
    spend(budget_run, 5787587)
    pending = ledger.acquire(budget_run.run_id, 0, {'fixture': status}, 40000)
    if status == 'UNKNOWN':
        ledger.settle(pending, {}, None, status='UNKNOWN')
    expected = BudgetBusy if status == 'RUNNING' else ledger.BudgetRejected
    with pytest.raises(expected) as caught:
        ledger.acquire(budget_run.run_id, 0, {'node': 'next'}, 90000, minimum_remaining=120000)
    if status == 'UNKNOWN':
        assert caught.value.details['reserved_microusd'] == 40000
        assert caught.value.details['shortfall_microusd'] == 37587
        assert ledger.acquire(budget_run.run_id, 0, {'fixture': status}, 40000)['blocked'] == 'UNKNOWN'
    else:
        assert not isinstance(caught.value, ledger.BudgetRejected)
    assert task_count(budget_run) == 2


@pytest.mark.parametrize('scope', ['optional', 'initial_generation'])
def test_scoped_limits_keep_their_original_accounting_and_conflict_contract(budget_run, scope):
    def request(node):
        return {'node': node, 'request': {'semantic_episode_id': 'fixture-episode'},
                'action_context': {'optional': True, 'plan_class': 'INITIAL_SELECTION',
                                   'semantic_episode_id': 'fixture-episode'}}
    spend(budget_run, 100000, request('settled'))
    ledger.acquire(budget_run.run_id, 0, request('reserved'), 20000)
    limits = {'optional_limit' if scope == 'optional' else 'generation_limit': 150000}
    with pytest.raises(Conflict) as caught:
        ledger.acquire(budget_run.run_id, 0, request('next'), 40000, minimum_remaining=120000, **limits)
    assert isinstance(caught.value, ledger.BudgetRejected)
    assert caught.value.details['scope'] == scope
    assert caught.value.details['spent_microusd'] == 100000
    assert caught.value.details['reserved_microusd'] == 20000
    assert caught.value.details['shortfall_microusd'] == 10000
    # The project validation hold is not charged against these separate sublimits.
    assert caught.value.details['validation_reserve_microusd'] == 0
    assert task_count(budget_run) == 2


def test_gateway_and_pipeline_retain_public_reason_and_exact_ledger_amounts(budget_run, monkeypatch):
    spend(budget_run, 5787587)
    budget_run.cost.total_usd = 5.787587
    provider = Mock(side_effect=AssertionError('Budget rejection must precede paid calls'))
    monkeypatch.setattr(llm, 'chat_json', provider)

    def stage(ctx):
        agent.run_agent(ctx, node='s5_ariz_p1', label='저장된 분석 단계', stage='S5_SOLVE',
            agent_id='fixture', prompt_id='P_S0_BOOTSTRAP', vars={'raw_query': 'fixture'},
            max_tokens=98603, system_override='JSON')

    monkeypatch.setattr(pipeline, 'PIPELINE', [('budget_fixture', '예산 확인', stage)])
    store.save_state(budget_run)
    result = pipeline.execute_stage(budget_run.run_id, 0)
    saved = store.load_state(budget_run.run_id)
    assert result['status'] == 'INTERRUPTED' and result['stage_index'] == 0
    assert saved.scratch['ax_interrupted_budget']['shortfall_microusd'] == 6190
    reason = saved.scratch['interruption_reason']
    assert '추가 모델 호출 예산이 부족' in reason and '필수 검토 보존 예산 $0.120000' in reason
    assert '$6.000000' in reason and '$0.098603' in reason and '$0.006190' in reason
    assert 'Insufficient budget' not in reason and 's5_ariz_p1' not in reason
    assert saved.steps[-1].status == 'FAILED' and saved.steps[-1].error == reason
    assert saved.control.warnings[-1] == reason and not saved.control.errors
    assert not provider.called and task_count(saved) == 1
    # Continue still allows a free replay; it neither replenishes nor pre-blocks.
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    assert pipeline.continue_run(saved.run_id)
    resumed = store.load_state(saved.run_id)
    assert 'ax_interrupted_budget' not in resumed.scratch
    assert resumed.cost.budget_usd == 6 and resumed.cost.total_usd == 5.787587


def test_cached_gateway_response_is_free_even_when_no_budget_remains(budget_run, monkeypatch):
    provider = Mock(return_value=llm.LLMResult(data={'saved': True}, tokens_in=8, tokens_out=4, cost_usd=.00001))
    monkeypatch.setattr(llm, 'chat_json', provider)
    ctx = RunContext(budget_run)
    original = gateway.chat(ctx, _node='s5_ariz_p1', system='JSON', user='saved request', max_tokens=98603)
    spend(budget_run, 5999990)
    before = ledger.budget(budget_run.run_id)
    replay = gateway.chat(ctx, _node='s5_ariz_p1', system='JSON', user='saved request', max_tokens=98603)
    assert replay.data == original.data and replay.meta['durable_replay']
    assert (replay.tokens_in, replay.tokens_out, replay.cost_usd) == (0, 0, 0)
    assert replay.meta['replay_source_usage'] == {
        'tokens_in': 8, 'tokens_out': 4, 'cost_usd': .00001, 'settled_microusd': 10}
    assert replay.meta['source_task_id']
    assert provider.call_count == 1 and before['remaining_microusd'] == 0
    assert ledger.budget(budget_run.run_id) == before and task_count(budget_run) == 2


def test_unknown_gateway_response_is_not_relabelled_as_budget_shortfall(budget_run, monkeypatch):
    monkeypatch.setattr(ledger, 'acquire', lambda *args, **kwargs: {'blocked': 'UNKNOWN'})
    with pytest.raises(UsageUncertain) as caught:
        gateway.chat(RunContext(budget_run), system='JSON', user='saved request')
    assert not isinstance(caught.value, BudgetExhausted)


def test_invalid_negative_reservation_remains_an_untyped_conflict(budget_run):
    with pytest.raises(Conflict) as caught:
        ledger.acquire(budget_run.run_id, 0, {'fixture': 'invalid'}, -1)
    assert not isinstance(caught.value, ledger.BudgetRejected)
