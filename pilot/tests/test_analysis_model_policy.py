"""Explicit analysis mode uses one actual config for provider, journal and cost."""
import copy
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from triz import llm, model_pricing, store
from triz.analysis_model_policy import analysis_model_config
from triz.ax import gateway, ledger
from triz.context import RunContext
from test_ax_refactor import newrun

CHAT_JSON = llm.chat_json
FLASH = dict(model='deepseek-flash', base_url='https://api.deepseek.com/v1',
             thinking_mode='disabled', supports_temperature=True, temperature=.3,
             max_tokens=32000, cost_in=.15, cost_out=.6, cost_cache_in=.003)


@pytest.mark.parametrize('model', sorted(model_pricing.FLASH_MODELS))
def test_official_flash_reasoning_changes_only_two_options_and_keeps_pin(model):
    config = dict(FLASH, model=model)
    before = copy.deepcopy(config)
    actual = analysis_model_config(config, True)
    assert actual == dict(config, thinking_mode='enabled', supports_temperature=False)
    assert actual is not config and config == before
    assert model_pricing.reserve_microusd(actual, 1000, 100, 2) == model_pricing.reserve_microusd(config, 1000, 100, 2)


@pytest.mark.parametrize('enabled', [False, None, 1, 'true'])
def test_explicit_boolean_opt_in_is_required(enabled):
    config = dict(FLASH)
    assert analysis_model_config(config) == config
    assert analysis_model_config(config, enabled) == config
    assert analysis_model_config(config, enabled) is not config


@pytest.mark.parametrize('overrides', [
    {'model':'deepseek-pro'}, {'model':'deepseek-chat'}, {'model':'another-model'},
    {'base_url':'https://other.invalid/v1'},
    {'base_url':'https://api.deepseek.com.other.invalid/v1'},
    {'base_url':'https://api.deepseek.com@other.invalid/v1'},
    {'base_url':'https://other.invalid/api.deepseek.com'},
    {'base_url':'api.deepseek.com/v1'}, {'base_url':'https://[invalid'},
])
def test_other_models_endpoints_and_invalid_urls_keep_options(overrides):
    config = dict(FLASH, **overrides)
    assert analysis_model_config(config, True) == config


def setup_provider(state, monkeypatch):
    state.scratch['ax_bundle']['models']['T2'].update(FLASH)
    state.scratch['ax_bundle']['config']['ax']['max_provider_attempts'] = 1
    calls = []
    def create(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        return SimpleNamespace(model='deepseek-flash', choices=[SimpleNamespace(
            finish_reason='stop', message=SimpleNamespace(content='{"ok":true}'))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=200,
                prompt_cache_hit_tokens=0, prompt_cache_miss_tokens=100,
                completion_tokens_details={'reasoning_tokens':150}))
    monkeypatch.setattr(llm, '_client', lambda *args: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm, 'chat_json', CHAT_JSON)
    return calls


@pytest.mark.parametrize('node', ['s3_function_model', 's4_contradictions', 'independent_verifier'])
def test_gateway_uses_actual_config_for_provider_reserve_and_saved_request(newrun, monkeypatch, node):
    state = newrun(); calls = setup_provider(state, monkeypatch)
    pinned = copy.deepcopy(state.scratch['ax_bundle']['models']['T2'])
    reserves, saved = [], []
    original_reserve = model_pricing.reserve_microusd
    def reserve(config, *args):
        amount = original_reserve(config, *args)
        reserves.append((copy.deepcopy(config), args, amount))
        return amount
    monkeypatch.setattr(model_pricing, 'reserve_microusd', reserve)
    monkeypatch.setattr(store, 'save_call', lambda run_id, value: saved.append(copy.deepcopy(value)))
    result = gateway.chat(RunContext(state), _node=node, _analysis_reasoning=True,
        system='JSON', user='offline analysis mode', tier='T2', temperature=0.0, max_tokens=700)
    assert result.data == {'ok':True}
    assert calls[0]['extra_body'] == {'thinking':{'type':'enabled'}}
    assert 'temperature' not in calls[0]
    assert calls[0]['max_tokens'] == 700
    assert '_analysis_reasoning' not in calls[0]
    actual = dict(pinned, thinking_mode='enabled', supports_temperature=False)
    assert reserves[0][0] == actual
    assert reserves[0][1][1] == 700
    assert state.scratch['ax_bundle']['models']['T2'] == pinned
    assert saved[0]['request']['model_config'] == actual
    assert '_analysis_reasoning' not in saved[0]['request']
    with store.engine.connect() as c:
        task = c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == state.run_id)).mappings().one()
        attempt = c.execute(select(ledger.attempts).where(ledger.attempts.c.task_id == task['task_id'])).mappings().one()
    recorded = json.loads(attempt['details'])['request']['request']
    assert recorded['model_config'] == actual and '_analysis_reasoning' not in recorded
    assert task['reserve'] == reserves[0][2]
    assert task['actual'] == 135  # 100 input + 200 completion; no extra reasoning charge.
    assert result.meta['requests'][0]['request']['extra_body'] == {'thinking':{'type':'enabled'}}


def test_unflagged_routes_and_paid_replays_preserve_mode_identity(newrun, monkeypatch):
    state = newrun(); calls = setup_provider(state, monkeypatch)
    ctx = RunContext(state)
    request = dict(_node='s3_function_model', system='JSON', user='same request', tier='T2')
    first = gateway.chat(ctx, **request)
    assert calls[0]['extra_body'] == {'thinking':{'type':'disabled'}}
    assert 'temperature' in calls[0]
    assert gateway.chat(ctx, _analysis_reasoning=False, **request).meta['durable_replay']
    enabled = gateway.chat(ctx, _analysis_reasoning=True, **request)
    assert not enabled.meta.get('durable_replay')
    assert calls[1]['extra_body'] == {'thinking':{'type':'enabled'}}
    assert gateway.chat(ctx, _analysis_reasoning=True, **request).meta['durable_replay']
    assert gateway.chat(ctx, **request).meta['durable_replay']
    assert len(calls) == 2
    assert first.cost_usd == enabled.cost_usd
    assert state.scratch['ax_bundle']['models']['T2']['thinking_mode'] == 'disabled'


@pytest.mark.parametrize('override', [{'model':'deepseek-pro'}, {'base_url':'https://other.invalid/v1'}])
def test_explicit_signal_keeps_other_provider_model_route_unchanged(newrun, monkeypatch, override):
    state = newrun(); calls = setup_provider(state, monkeypatch)
    state.scratch['ax_bundle']['models']['T2'].update(override)
    pinned = copy.deepcopy(state.scratch['ax_bundle']['models']['T2'])
    gateway.chat(RunContext(state), _node='s3_function_model', _analysis_reasoning=True,
        system='JSON', user='other configured route', tier='T2')
    assert calls[0]['extra_body'] == {'thinking':{'type':'disabled'}}
    assert 'temperature' in calls[0]
    assert state.scratch['ax_bundle']['models']['T2'] == pinned
