"""Token-based estimates, with the requested fixed Flash off-peak test tariff.

These rates estimate cost; they are not a provider invoice. Historical receipts
remain unchanged. Cache discounts require counters returned by the provider.
"""
from decimal import Decimal, ROUND_CEILING
from urllib.parse import urlsplit

FLASH_MODELS = frozenset(('deepseek-flash', 'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp'))
FLASH_BASIS = 'deepseek-flash-off-peak-2026-09-30'
SOURCE_URL = 'https://api-docs.deepseek.com/quick_start/pricing/'


class ProviderUsageError(ValueError):
    """A received response cannot be priced from its reported token counts."""


def configured(current, pinned=None):
    result = {**current, **(pinned or {})}
    if pinned:
        # Old pins did not contain cache prices. Never inherit another model's
        # cache tariff from today's environment.
        result['cost_cache_in'] = pinned.get('cost_cache_in')
    return result


def resolve(config):
    official = urlsplit(str(config.get('base_url', ''))).hostname == 'api.deepseek.com'
    if official and str(config.get('model', '')).lower() in FLASH_MODELS:
        return dict(input_per_m=.15, cached_input_per_m=.003, output_per_m=.6,
                    basis=FLASH_BASIS, source_url=SOURCE_URL, period='off_peak_fixed')
    return dict(input_per_m=config['cost_in'], output_per_m=config['cost_out'],
                cached_input_per_m=config.get('cost_cache_in'), basis='configured_token_rates')


def _count(value):
    return type(value) is int and value >= 0


def calculate(usage, rates):
    tin = usage.get('prompt_tokens', usage.get('input_tokens'))
    tout = usage.get('completion_tokens', usage.get('output_tokens'))
    if not _count(tin) or not _count(tout):
        raise ProviderUsageError('Missing or invalid provider token counts')
    details = usage.get('prompt_tokens_details') or usage.get('input_tokens_details') or {}
    nested = details.get('cached_tokens') if isinstance(details, dict) else None
    hit = usage.get('prompt_cache_hit_tokens')
    miss = usage.get('prompt_cache_miss_tokens')
    cache_usage = 'provider'
    if hit is None:
        hit = nested
    if hit is None and miss is None:
        cache_usage = 'unreported'
    elif (hit is not None and (not _count(hit) or hit > tin) or
          miss is not None and (not _count(miss) or miss > tin) or
          nested is not None and (not _count(nested) or nested != hit)):
        cache_usage = 'invalid'
    else:
        if hit is None:
            hit = tin - miss
        if miss is None:
            miss = tin - hit
        if hit + miss != tin:
            cache_usage = 'invalid'
    if cache_usage != 'provider':
        hit = miss = None
    # Unknown cache use is not a fabricated miss count: only its estimate uses
    # the uncached rate. Output already includes reasoning tokens; do not add them.
    discounted = hit if hit is not None and rates.get('cached_input_per_m') is not None else 0
    amount = ((tin - discounted) * Decimal(str(rates['input_per_m'])) +
              discounted * Decimal(str(rates.get('cached_input_per_m') or 0)) +
              tout * Decimal(str(rates['output_per_m']))) / Decimal(1_000_000)
    return dict(cost_usd=str(amount), input_tokens=tin, output_tokens=tout,
                cache_hit_tokens=hit, cache_miss_tokens=miss, cache_usage=cache_usage,
                rates=dict(rates))


def reserve_microusd(config, input_bound, output_bound, attempts=1):
    """Reserve a full uncached request, never an assumed future cache hit."""
    rates = resolve(config)
    value = (Decimal(input_bound) * Decimal(str(rates['input_per_m'])) +
             Decimal(output_bound) * Decimal(str(rates['output_per_m']))) * attempts
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def to_microusd(cost_usd):
    return int((Decimal(str(cost_usd)) * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


def usage_dict(usage):
    if not usage:
        return {}
    if hasattr(usage, 'model_dump'):
        return usage.model_dump()
    if isinstance(usage, dict):
        return dict(usage)
    result = {key: getattr(usage, key) for key in ('prompt_tokens', 'completion_tokens',
        'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens') if hasattr(usage, key)}
    details = getattr(usage, 'prompt_tokens_details', None)
    if details is not None:
        result['prompt_tokens_details'] = (details if isinstance(details, dict) else
            {'cached_tokens': getattr(details, 'cached_tokens', None)})
    return result
