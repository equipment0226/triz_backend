"""Analysis-only reasoning, budget admission and independent repair context."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from triz import agent, llm, model_pricing, store, verification_contract, verify
from triz.context import AbortRun, RunContext
from triz.settings import settings


CHAT_JSON = llm.chat_json


def sdk(state, monkeypatch):
    tier = settings.tiers['T2']
    for key, value in dict(model='deepseek-flash', base_url='https://api.deepseek.com/v1',
                           thinking_mode='disabled', supports_temperature=True,
                           max_tokens=32000).items():
        monkeypatch.setattr(tier, key, value)
    monkeypatch.setattr(settings, 'max_retries', 1)
    calls, receipts, reserves = [], [], []
    def create(**kwargs):
        calls.append(deepcopy(kwargs))
        return SimpleNamespace(model='deepseek-flash', choices=[SimpleNamespace(
            finish_reason='stop', message=SimpleNamespace(content='{"ok":true}'))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=200))
    monkeypatch.setattr(llm, '_client', lambda *args: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm, 'chat_json', CHAT_JSON)
    monkeypatch.setattr(store, 'save_call', lambda run_id, receipt: receipts.append(deepcopy(receipt)))
    calculate = model_pricing.reserve_microusd
    def reserve(config, *args):
        value = calculate(config, *args)
        reserves.append((deepcopy(config), args, value))
        return value
    monkeypatch.setattr(model_pricing, 'reserve_microusd', reserve)
    return calls, receipts, reserves


def test_non_ax_reasoning_uses_same_config_in_reservation_receipt_and_sdk(state, monkeypatch):
    calls, receipts, reserves = sdk(state, monkeypatch)
    before = deepcopy(vars(settings.tiers['T2']))
    ctx = RunContext(state)
    result = agent.tracked_chat(ctx, _node='s3_function_model', _analysis_reasoning=True,
        system='JSON', user='offline reasoning', tier='T2', temperature=0.0, max_tokens=700)
    request = receipts[0]['request']
    assert result.data == {'ok': True}
    assert calls[0]['extra_body'] == {'thinking': {'type': 'enabled'}}
    assert 'temperature' not in calls[0] and calls[0]['max_tokens'] == 700
    assert '_analysis_reasoning' not in calls[0] and '_analysis_reasoning' not in request
    assert request['model_config'] == reserves[0][0]
    assert request['model_config']['supports_temperature'] is False
    assert 'api_key' not in request['model_config']
    assert reserves[0][1][1] == 700
    assert vars(settings.tiers['T2']) == before
    assert state.cost.request_count == 1 and state.cost.total_usd == pytest.approx(.000135)
    assert ctx.budget['reserved'] == 0


@pytest.mark.parametrize('signal', [False, None, 1, 'true'])
def test_non_ax_unflagged_or_nonboolean_signal_preserves_provider_request(state, monkeypatch, signal):
    calls, receipts, reserves = sdk(state, monkeypatch)
    ctx = RunContext(state)
    common = dict(system='JSON', user='unchanged route', tier='T2', max_tokens=500)
    agent.tracked_chat(ctx, **common)
    agent.tracked_chat(ctx, _analysis_reasoning=signal, **common)
    assert calls[0] == calls[1]
    assert receipts[0]['request'] == receipts[1]['request']
    assert 'model_config' not in receipts[1]['request']
    assert '_analysis_reasoning' not in receipts[1]['request']
    assert reserves[0] == reserves[1]


def test_reasoning_request_cannot_bypass_pre_call_budget_reservation(state, monkeypatch):
    calls, receipts, reserves = sdk(state, monkeypatch)
    state.cost.budget_usd = 0
    ctx = RunContext(state)
    with pytest.raises(AbortRun):
        agent.tracked_chat(ctx, _analysis_reasoning=True, system='JSON', user='bounded', tier='T2')
    assert reserves[0][0]['thinking_mode'] == 'enabled'
    assert not calls and not receipts
    assert ctx.budget['reserved'] == 0 and state.cost.request_count == 0


@pytest.mark.parametrize('rubric_id, configured, expected_tokens, flagged', [
    ('R3_FUNC', 8000, 16000, True), ('R3_FUNC', 20000, 20000, True),
    ('R6_CONCEPT', 8000, 8000, False),
])
def test_only_critical_verifier_gets_reasoning_token_floor_and_scoped_prior_reviews(
        state, monkeypatch, rubric_id, configured, expected_tokens, flagged):
    from triz.ax import runtime
    rendered, calls = [], []
    monkeypatch.setitem(settings.triz['verification'], 'enabled', True)
    monkeypatch.setitem(settings.triz['verification'], 'max_tokens', configured)
    monkeypatch.setitem(settings.triz['verification'], 'critical_rubrics', [rubric_id])
    def render(state, prompt_id, **values):
        rendered.append(deepcopy(values))
        return json.dumps(values, ensure_ascii=False)
    monkeypatch.setattr(runtime, 'render_prompt', render)
    rb = verification_contract.effective_rubric(settings, rubric_id)
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return llm.LLMResult(data={'verdict': 'PASS', 'per_criterion': [
            {'id': c['id'], 'score': 1.0} for c in rb['criteria']]})
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    previous = [{'verdict': 'REVISE', 'source': 'model', 'revision_instructions': [f'finding-{i}'],
                 'per_criterion': [], 'element_findings': [], 'private_trace': 'omit'} for i in range(7)]
    before = deepcopy(previous)
    data = {'components': [{'name': 'tool', 'level': 'TARGET'}, {'name': 'product', 'level': 'PRODUCT'}],
            'function_edges': [{'subject': 'tool', 'action': 'moves', 'object': 'product',
                                'rank': 'BASIC', 'kind': 'USEFUL'}]}
    verdict = agent.verify_artifact(RunContext(state), rubric_id, data, 'context', previous_verdicts=previous)
    assert verdict['verdict'] == 'PASS'
    assert calls[0]['max_tokens'] == expected_tokens
    assert (calls[0].get('_analysis_reasoning') is True) is flagged
    facts = rendered[0]['facts_block']
    if flagged:
        assert facts['deterministic_inventory']['basic_count'] == 1
        history = facts['prior_reviews_model_opinions']
        assert len(history) == 5 and history[0]['revision_instructions'] == ['finding-2']
        assert all('private_trace' not in row for row in history)
        assert 'prior_reviews_model_opinions' not in facts['observations']
    else:
        assert 'prior_reviews_model_opinions' not in facts and 'deterministic_inventory' not in facts
    assert previous == before


def test_repaired_critical_output_is_reaudited_with_prior_review_as_opinion(state, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values: str(values))
    monkeypatch.setitem(settings.triz['verification'], 'enabled', True)
    calls, reviews = [], []
    original = {'components': [
        {'name': 'tool', 'level': 'TARGET', 'role': 'moves the product'},
        {'name': 'product', 'level': 'PRODUCT', 'role': 'transported part'}],
        'function_edges': [{'subject': 'tool', 'action': 'moves', 'object': 'product',
            'rank': 'BASIC', 'kind': 'USEFUL', 'level': 'INSUFFICIENT',
            'parameter_affected': 'position', 'notes': 'unsupported mechanism'}],
        'interaction_cells': [], 'mermaid': ''}
    fixed = deepcopy(original)
    fixed['function_edges'][0]['notes'] = 'supported mechanism'
    outputs = [original, fixed]
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return llm.LLMResult(data=outputs.pop(0))
    def review(ctx, rubric_id, data, facts, **kwargs):
        reviews.append((deepcopy(data), deepcopy(kwargs)))
        return ({'verdict': 'REVISE', 'revision_instructions': ['Ground the mechanism in the source'], 'score': .5}
                if len(reviews) == 1 else {'verdict': 'PASS', 'score': 1.})
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    monkeypatch.setattr(agent, 'verify_artifact', review)
    result = agent.run_agent(RunContext(state), node='s3_function_model', stage='S3', label='function model',
        agent_id='system_analyst', prompt_id='P_S3_FUNCTION_MODEL', rubric_id='R3_FUNC',
        checker=verify.check_function_model, repair_attempts=1)
    assert result == fixed
    assert all(call['_analysis_reasoning'] is True for call in calls)
    assert reviews[0][1] == {}
    assert reviews[1][1]['previous_verdicts'][0]['revision_instructions'] == ['Ground the mechanism in the source']
    assert reviews[1][0] == result and state.steps[-1].status == 'OK'
