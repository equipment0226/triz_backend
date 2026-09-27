"""Offline admission counts for complete, unmodified text-only patent requests."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from .domain import PatentError

ROOT = Path(__file__).with_name('tokenizers')
DEEPSEEK_MODELS = {'deepseek-flash', 'deepseek-v4-flash', 'deepseek-v4-pro'}
PREFLIGHT_ERRORS = frozenset({'PROVIDER_NOT_ALLOWED', 'REVIEW_COVERAGE_LIMIT', 'INPUT_TOKENIZER_UNAVAILABLE'})


@lru_cache(maxsize=1)
def tokenizers():
    # Vendored data only: no runtime downloads, model code, or document uploads.
    from tokenizers import Tokenizer
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    loaded = []
    for version in ('v4', 'v41'):
        name = version + '/tokenizer.json'
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest['files'][name]:
            raise ValueError('tokenizer checksum mismatch')
        tokenizer = Tokenizer.from_str(raw.decode('utf-8'))
        tokenizer.no_truncation()
        tokenizer.no_padding()
        loaded.append(tokenizer)
    return loaded


def measure(model, messages):
    """Count content with published vocabularies, plus a conservative framing margin.

    The API's usage remains authoritative. Both V4 text vocabularies are counted
    because the flash alias can change; the larger result controls admission.
    No text, schema, citation, or review target is removed or rewritten.
    """
    content = [m['content'] for m in messages]
    byte_count = sum(len(text.encode('utf-8')) for text in content)
    if urlparse(model.base_url).hostname == 'api.deepseek.com' and model.model in DEEPSEEK_MODELS:
        try:
            count = max(sum(len(t.encode(text, add_special_tokens=False).ids) for text in content)
                        for t in tokenizers())
        except Exception:
            raise PatentError('INPUT_TOKENIZER_UNAVAILABLE', '모델 입력량 검사기를 불러오지 못했습니다. 자료와 예산을 보존한 채 중지했습니다.', 503) from None
        # Covers chat delimiters, JSON mode instructions, and service template drift.
        margin = max(1024, (count + 19) // 20) + 32 * len(messages)
        method = 'deepseek-v4-v41-content-max-with-margin-v1'
    else:
        # Unknown models keep a conservative byte bound, not a guessed chars/4 ratio.
        count, margin, method = byte_count, 128 + 32 * len(messages), 'utf8-upper-bound-v1'
    return {'method': method, 'content_tokens': count, 'framing_margin': margin,
            'admission_tokens': count + margin, 'input_limit': model.input_limit,
            'content_bytes': byte_count}
