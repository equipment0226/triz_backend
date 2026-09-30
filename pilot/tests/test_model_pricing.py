"""Observed cache usage, fixed off-peak estimates and durable paid-call reuse."""
import copy
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from triz import llm, model_pricing, store
from triz.ax import gateway, ledger, track_cost
from triz.context import RunContext
from triz.settings import settings
from test_ax_refactor import newrun

CHAT_JSON = llm.chat_json
FLASH = dict(model='deepseek-flash', base_url='https://api.deepseek.com/v1',
             cost_in=.3, cost_out=1.2)


@pytest.mark.parametrize('model', sorted(model_pricing.FLASH_MODELS))
def test_offpeak_policy_accepts_official_flash_aliases(model):
    config = dict(FLASH, model=model)
    before = copy.deepcopy(config)
    rates = model_pricing.resolve(config)
    assert (rates['input_per_m'], rates['cached_input_per_m'], rates['output_per_m']) == (.15, .003, .6)
    assert rates['basis'] == model_pricing.FLASH_BASIS
    assert config == before


@pytest.mark.parametrize('overrides', [dict(model='deepseek-pro'), dict(model='deepseek-chat'),
    dict(base_url='https://other.invalid/v1'), dict(base_url='https://api.deepseek.com.other.invalid')])
def test_other_models_and_providers_keep_configured_rates(overrides):
    rates = model_pricing.resolve(dict(FLASH, **overrides))
    assert rates['input_per_m'] == .3 and rates['output_per_m'] == 1.2
    assert rates['cached_input_per_m'] is None


def test_mixed_cache_and_reasoning_output_have_one_charge():
    usage = dict(prompt_tokens=1_000_000, completion_tokens=250_000,
        prompt_cache_hit_tokens=900_000, prompt_cache_miss_tokens=100_000,
        completion_tokens_details={'reasoning_tokens': 200_000})
    charge = model_pricing.calculate(usage, model_pricing.resolve(FLASH))
    assert Decimal(charge['cost_usd']) == Decimal('.1677')
    assert charge['cache_usage'] == 'provider'
    assert charge['cache_hit_tokens'] == 900_000 and charge['cache_miss_tokens'] == 100_000


@pytest.mark.parametrize('cache', [dict(prompt_cache_hit_tokens=80), dict(prompt_cache_miss_tokens=20),
    dict(prompt_tokens_details={'cached_tokens':80})])
def test_provider_counter_complement_and_sdk_cache_details(cache):
    charge = model_pricing.calculate(dict(prompt_tokens=100, completion_tokens=20, **cache),
                                     model_pricing.resolve(FLASH))
    assert charge['cache_hit_tokens'] == 80 and charge['cache_miss_tokens'] == 20
    assert Decimal(charge['cost_usd']) == Decimal('.00001524')


@pytest.mark.parametrize('cache,status', [({}, 'unreported'),
    ({'prompt_cache_hit_tokens':-1}, 'invalid'),
    ({'prompt_cache_hit_tokens':101}, 'invalid'),
    ({'prompt_cache_hit_tokens':True}, 'invalid'),
    ({'prompt_cache_hit_tokens':80, 'prompt_cache_miss_tokens':30}, 'invalid'),
    ({'prompt_cache_hit_tokens':80, 'prompt_tokens_details':{'cached_tokens':70}}, 'invalid')])
def test_unknown_or_invalid_cache_is_not_invented(cache, status):
    charge = model_pricing.calculate(dict(prompt_tokens=100, completion_tokens=20, **cache),
                                     model_pricing.resolve(FLASH))
    assert charge['cache_usage'] == status
    assert charge['cache_hit_tokens'] is charge['cache_miss_tokens'] is None
    assert Decimal(charge['cost_usd']) == Decimal('.000027')


def test_reservation_does_not_assume_future_cache_hits():
    assert model_pricing.reserve_microusd(FLASH, 1_000_000, 250_000, attempts=2) == 600_000
    assert model_pricing.reserve_microusd(FLASH, 1, 1) == 1


def response(finish='stop'):
    return SimpleNamespace(model='deepseek-flash', choices=[SimpleNamespace(
        finish_reason=finish, message=SimpleNamespace(content='{"ok":true}'))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20,
            prompt_cache_hit_tokens=80, prompt_cache_miss_tokens=20))


def sdk(monkeypatch, responses):
    create = Mock(side_effect=responses)
    monkeypatch.setattr(llm, '_client', lambda *args: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm, 'chat_json', CHAT_JSON)
    monkeypatch.setattr(llm.time, 'sleep', lambda _: None)
    return create


def test_retry_accounts_for_each_real_cache_usage_and_saves_basis(monkeypatch):
    create = sdk(monkeypatch, [response('length'), response()])
    result = CHAT_JSON(system='JSON', user='example', model_config=FLASH, retries=2)
    assert result.data == {'ok':True} and create.call_count == 2
    assert result.tokens_in == 200 and result.tokens_out == 40
    assert result.cost_usd == pytest.approx(.00003048)
    assert result.meta['cost_basis'] == model_pricing.FLASH_BASIS
    assert [r['pricing']['cache_hit_tokens'] for r in result.meta['requests']] == [80,80]
    assert all(r['usage']['prompt_cache_miss_tokens'] == 20 for r in result.meta['requests'])


def test_failed_truncation_keeps_observed_discounted_cost(monkeypatch):
    sdk(monkeypatch, [response('length')])
    with pytest.raises(llm.LLMError) as caught:
        CHAT_JSON(system='JSON', user='example', model_config=FLASH, retries=1)
    assert caught.value.usage.cost_usd == pytest.approx(.00001524)
    assert caught.value.usage.meta['requests'][0]['pricing']['cache_usage'] == 'provider'


def test_old_nonflash_pin_never_inherits_current_flash_cache_price(monkeypatch):
    monkeypatch.setattr(settings.tiers['T2'], 'cost_cache_in', .003)
    sdk(monkeypatch, [response()])
    result = CHAT_JSON(system='JSON', user='example', retries=1,
        model_config=dict(FLASH, model='deepseek-pro', cost_in=1.32, cost_out=3.96))
    assert result.cost_usd == pytest.approx((100*1.32 + 20*3.96)/1_000_000)
    assert result.meta['pricing_rates']['cached_input_per_m'] is None


@pytest.mark.parametrize('usage', [{'total_tokens':120},
    {'prompt_tokens':None, 'completion_tokens':20},
    {'prompt_tokens':100, 'completion_tokens':-1},
    {'prompt_tokens':True, 'completion_tokens':20}])
def test_invalid_token_totals_stay_unknown_without_another_paid_attempt(newrun, monkeypatch, usage):
    state = newrun()
    state.scratch['ax_bundle']['models']['T2'].update(FLASH)
    invalid = response()
    invalid.usage = SimpleNamespace(**usage)
    create = sdk(monkeypatch, [invalid, response()])
    with pytest.raises(llm.LLMError):
        gateway.chat(RunContext(state), _node='s5_track_h', system='JSON', user='example', tier='T2')
    assert create.call_count == 1
    budget = ledger.budget(state.run_id)
    assert budget['spent_microusd'] == 0 and budget['reserved_microusd'] > 0
    with store.engine.connect() as conn:
        task = conn.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==state.run_id)).mappings().one()
    assert task['status'] == 'UNKNOWN' and task['actual'] is None


def test_ax_settlement_and_replay_keep_pinned_request_and_one_charge(newrun, monkeypatch):
    state = newrun()
    config = state.scratch['ax_bundle']['models']['T2']
    config.update(FLASH)
    before = copy.deepcopy(config)
    create = sdk(monkeypatch, [response()])
    ctx = RunContext(state)
    args = dict(_node='s5_track_h', system='JSON', user='example', tier='T2')
    result = gateway.chat(ctx, **args)
    assert result.cost_usd == pytest.approx(.00001524)
    assert ledger.budget(state.run_id)['spent_microusd'] == 16
    with store.engine.connect() as conn:
        task = dict(conn.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==state.run_id)).mappings().one())
    replay = gateway.chat(ctx, **args)
    assert create.call_count == 1
    assert replay.cost_usd == 0 and replay.meta['durable_replay']
    assert config == before and config['cost_in'] == .3
    with store.engine.connect() as conn:
        after = dict(conn.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==state.run_id)).mappings().one())
    assert after == task
    assert ledger.budget(state.run_id)['spent_microusd'] == 16


def test_track_prior_resolves_old_flash_price_and_versions_cost_comparison(newrun):
    state = newrun()
    for config in state.scratch['ax_bundle']['models'].values():
        config.update(FLASH)
    prior, plan = track_cost.prior(state, 'H_EFFECTS')
    comparison = track_cost.comparison(state)
    for config in state.scratch['ax_bundle']['models'].values():
        config.update(cost_in=.15, cost_out=.6)
    assert track_cost.prior(state, 'H_EFFECTS') == (prior, plan)
    assert track_cost.comparison(state)['pricing'] == comparison['pricing']
    assert comparison != {key:value for key,value in comparison.items() if key != 'pricing'}
