"""Per-call analysis reasoning policy; never modifies the pinned model bundle."""
from urllib.parse import urlsplit

from .model_pricing import FLASH_MODELS


def analysis_model_config(config, enabled=False):
    """Copy a model config and opt official Flash calls into reasoning only.

    The caller selects analysis generation/review calls explicitly. Other calls,
    providers and models retain every configured option. Output limits and token
    prices are unchanged: completion usage already includes reasoning tokens.
    """
    actual = dict(config)
    if enabled is not True:
        return actual
    try:
        official = urlsplit(str(actual.get('base_url', ''))).hostname == 'api.deepseek.com'
    except ValueError:
        official = False
    if official and str(actual.get('model', '')).lower() in FLASH_MODELS:
        actual['thinking_mode'] = 'enabled'
        actual['supports_temperature'] = False
    return actual
