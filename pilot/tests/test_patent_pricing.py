"""Patent billing uses provider cache usage without rewriting pinned profiles."""
from dataclasses import replace
from decimal import Decimal
import copy
import json

import httpx
import pytest
from sqlalchemy import select

from patent_draft.models import Gateway, Model, ModelProfile, reserve
from patent_draft.repository import tasks
from test_patent_draft import patent, opened, answered, authorize, change


def flash(name='deepseek-flash'):
    # Existing snapshots can still contain the former peak tariff.
    return Model('T2', name, 'https://api.deepseek.com/v1', 'PATENT_TEST_KEY',
                 '0.3', '1.2', 262144, 8192)


def reply(usage, *, finish='stop', content='{}', model='deepseek-flash'):
    return {'id': 'price-test', 'model': model, 'usage': usage,
            'choices': [{'finish_reason': finish, 'message': {'content': content}}]}


@pytest.mark.parametrize('name', ['deepseek-flash', 'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp'])
def test_flash_reservation_uses_offpeak_without_assuming_cache_hits(name):
    model = flash(name)
    assert model.cost(1_000_000, 1_000_000) == 750_000
    pricing = model.pricing({'prompt_tokens': 1_000_000, 'completion_tokens': 0})
    assert pricing['rates']['input_per_m'] == .15
    assert pricing['rates']['cached_input_per_m'] == .003
    assert pricing['rates']['output_per_m'] == .6
    assert pricing['cache_usage'] == 'unreported'


def test_other_model_and_endpoint_keep_their_configured_prices():
    pro = replace(flash(), model='deepseek-v4-pro', input_price='1.32', output_price='3.96')
    custom_endpoint = replace(flash(), base_url='https://models.example.test/v1')
    assert pro.cost(1_000_000, 1_000_000) == 5_280_000
    assert custom_endpoint.cost(1_000_000, 1_000_000) == 1_500_000


def test_existing_pinned_profile_roundtrips_without_schema_or_value_changes():
    snapshot = {'T2': flash().public()}
    original = copy.deepcopy(snapshot)
    model = ModelProfile.pinned(snapshot).models['T2']
    budget = {'cap_micro_usd': 1_000_000, 'spent_micro_usd': 0, 'reserved_micro_usd': 0,
              'review_plan_micro_usd': 0, 'uncertain_micro_usd': 0}
    assert reserve(budget, model) == 44_237
    assert ModelProfile.pinned(snapshot).snapshot() == original == snapshot
    assert snapshot['T2']['input_price'] == '0.3'
    assert snapshot['T2']['output_price'] == '1.2'


@pytest.mark.parametrize('cache_fields', [
    {'prompt_cache_hit_tokens': 900_000, 'prompt_cache_miss_tokens': 100_000},
    {'prompt_tokens_details': {'cached_tokens': 900_000}},
])
def test_gateway_prices_actual_cache_usage_and_records_its_basis(cache_fields):
    usage = {'prompt_tokens': 1_000_000, 'completion_tokens': 100_000, **cache_fields}
    gateway = Gateway(httpx.MockTransport(lambda request: httpx.Response(200, json=reply(usage))))
    result = gateway.generate(flash(), 'review', {}, {})
    pricing = result['boundary_contract']['pricing']
    assert result['usage'] == usage
    assert result['cost_micro_usd'] == 77_700
    assert Decimal(pricing['cost_usd']) == Decimal('.0777')
    assert pricing['cache_hit_tokens'] == 900_000
    assert pricing['cache_miss_tokens'] == 100_000
    assert pricing['cache_usage'] == 'provider'
    assert pricing['rates']['basis']


@pytest.mark.parametrize('cache_fields,state', [
    ({}, 'unreported'),
    ({'prompt_cache_hit_tokens': 1_000_001, 'prompt_cache_miss_tokens': 0}, 'invalid'),
])
def test_unreported_or_invalid_cache_usage_does_not_invent_a_discount(cache_fields, state):
    usage = {'prompt_tokens': 1_000_000, 'completion_tokens': 100_000, **cache_fields}
    gateway = Gateway(httpx.MockTransport(lambda request: httpx.Response(200, json=reply(usage))))
    result = gateway.generate(flash(), 'review', {}, {})
    assert result['cost_micro_usd'] == 210_000
    assert result['boundary_contract']['pricing']['cache_usage'] == state


@pytest.mark.parametrize('finish,content,error', [
    ('length', '{}', 'OUTPUT_INCOMPLETE'),
    ('stop', 'not-json', 'OUTPUT_SCHEMA_INVALID'),
])
def test_failed_output_retains_the_observed_discounted_charge(finish, content, error):
    usage = {'prompt_tokens': 1_000_000, 'completion_tokens': 100_000,
             'prompt_cache_hit_tokens': 900_000, 'prompt_cache_miss_tokens': 100_000}
    gateway = Gateway(httpx.MockTransport(lambda request:
        httpx.Response(200, json=reply(usage, finish=finish, content=content))))
    result = gateway.generate(flash(), 'review', {}, {})
    assert result['error'] == error
    assert result['cost_micro_usd'] == 77_700
    assert result['boundary_contract']['pricing']['cache_usage'] == 'provider'


def test_discounted_failure_is_saved_once_with_receipt_and_original_profile(patent):
    service, _, engine, _ = patent
    service.profile = ModelProfile({tier: replace(model, model='deepseek-flash',
        input_price='0.3', output_price='1.2') if tier != 'T3' else model
        for tier, model in service.profile.models.items()})
    snapshot = service.profile.snapshot()
    calls = []
    usage = {'prompt_tokens': 10_000, 'completion_tokens': 1_000,
             'prompt_cache_hit_tokens': 9_000, 'prompt_cache_miss_tokens': 1_000}
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=reply(usage, finish='length'))
    service.gateway = Gateway(httpx.MockTransport(respond))
    case, _ = opened(service)
    case = change(service, authorize(service, answered(service, case)), 'start')
    with engine.connect() as conn:
        body = conn.execute(select(tasks.c.body).where(
            tasks.c.case_id == case['case_id'], tasks.c.status == 'QUEUED')).scalar_one()
    ticket = json.loads(body)['ticket']
    assert service.execute('owner', ticket)['status'] == 'FAILED'
    assert service.execute('owner', ticket)['status'] == 'FAILED'
    current = service.repo.get('owner', case['case_id'])
    assert len(calls) == 1
    assert current['budget']['spent_micro_usd'] == 777
    assert current['model_config'] == snapshot
    receipts = service.repo.records('owner', case['case_id'], 'provider_receipt')
    assert len(receipts) == 1
    assert receipts[0]['usage'] == usage
    assert receipts[0]['boundary_contract']['pricing']['cache_usage'] == 'provider'
    costs = service.repo.records('owner', case['case_id'], 'cost')
    assert len(costs) == 1 and costs[0]['actual_micro_usd'] == 777
    # A tariff correction must not break the existing model-profile pin check.
    assert authorize(service, current, cap=3_000_000)['model_config'] == snapshot
