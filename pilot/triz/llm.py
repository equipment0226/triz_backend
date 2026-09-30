"""LLM 게이트웨이.

- 티어(T1/T2/T3)별로 모델·키·엔드포인트를 분리할 수 있다. PoC는 단일 DeepSeek 키.
- 항상 JSON 출력을 강제하고, 실패 시 1회 형식 교정 재시도한다.
- 토큰/비용을 집계해 CostLedger에 누적한다.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from typing import Any

from openai import OpenAI

from .settings import settings
from . import model_pricing

log = logging.getLogger("triz.llm")

JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@dataclass
class LLMResult:
    data: Any
    text: str = ""
    tier: str = "T2"
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    raw_error: str = ""
    meta: dict = field(default_factory=dict)


class LLMError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    @property
    def terminal(self) -> bool:
        # These require an account/configuration change, not a JSON repair.
        return self.status_code in (401, 402, 403)


@lru_cache(maxsize=8)
def _client(tier: str, endpoint: str | None = None) -> OpenAI:
    tc = settings.tiers[tier]
    if not tc.api_key:
        raise LLMError("LLM_API_KEY 가 설정되지 않았습니다. pilot/.env 를 확인하세요.")
    return OpenAI(api_key=tc.api_key, base_url=endpoint or tc.base_url, timeout=settings.timeout, max_retries=0)


def _loads_with_extra_closers(text: str) -> Any:
    """Remove at most two unmatched closers; require the entire result to parse."""
    for attempt in range(3):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            pos = exc.pos
            if attempt == 2 or pos >= len(text) or text[pos] not in "]}":
                raise
            stack: list[str] = []
            in_str = esc = False
            pairs = {"}": "{", "]": "["}
            for ch in text[:pos]:
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                elif ch == '"':
                    in_str = True
                elif ch in "{[":
                    stack.append(ch)
                elif ch in "}]":
                    if not stack or stack.pop() != pairs[ch]:
                        raise exc
            # Matching closers can signal missing data (e.g. a trailing comma).
            # Never remove them, add values, or discard the enclosing object.
            if in_str or (stack and stack[-1] == pairs[text[pos]]):
                raise
            text = text[:pos] + text[pos + 1:]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Ambiguous duplicate JSON field: " + key)
        result[key] = value
    return result


def _insert_table_rows(text: str, error: json.JSONDecodeError) -> str:
    """Restore only an omitted table_rows label around complete string rows."""
    pos = error.pos
    if error.msg != 'Expecting property name enclosed in double quotes' or text[pos:pos + 1] != '[':
        raise error
    stack = []
    in_string = escaped = False
    for index, ch in enumerate(text[:pos]):
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch in '{[':
            stack.append((ch, index))
        elif ch in '}]':
            if not stack or stack.pop()[0] != {'}': '{', ']': '['}[ch]:
                raise error
    if not stack or stack[-1][0] != '{':
        raise error
    prefix = text[stack[-1][1]:pos].rstrip()
    if not prefix.endswith(','):
        raise error
    fields = json.loads(prefix[:-1] + '}', object_pairs_hook=_unique_object)
    columns = fields.get('table_columns')
    if (not fields or next(reversed(fields)) != 'table_columns' or 'table_rows' in fields
            or not isinstance(columns, list) or not columns or not all(isinstance(c, str) for c in columns)):
        raise error
    decoder = json.JSONDecoder()
    cursor = pos
    while True:
        row, end = decoder.raw_decode(text, cursor)
        if not isinstance(row, list) or len(row) != len(columns) or not all(isinstance(cell, str) for cell in row):
            raise error
        cursor = end
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if text[cursor:cursor + 1] == ',':
            following = cursor + 1
            while following < len(text) and text[following].isspace():
                following += 1
            if text[following:following + 1] == '[':
                cursor = following
                continue
        break
    # Retain an existing outer rows closer, or insert one before an object
    # delimiter. Never invent cells, discard a row, or close a truncated root.
    if text[cursor:cursor + 1] == ']':
        return text[:pos] + '"table_rows":[' + text[pos:]
    if text[cursor:cursor + 1] in ('}', ','):
        return text[:pos] + '"table_rows":[' + text[pos:cursor] + ']' + text[cursor:]
    raise error


def _loads_response(text: str) -> Any:
    try:
        return _loads_with_extra_closers(text)
    except json.JSONDecodeError as original:
        repaired = text
        # ARIZ can return this omission in several independently complete tables.
        for _ in range(16):
            try:
                return json.loads(repaired, object_pairs_hook=_unique_object)
            except json.JSONDecodeError as exc:
                try:
                    repaired = _insert_table_rows(repaired, exc)
                except (ValueError, IndexError):
                    raise original
        raise original


def extract_json(text: str) -> Any:
    """모델 출력에서 JSON 객체/배열을 최대한 관대하게 뽑아낸다."""
    if not text:
        raise ValueError("빈 응답")
    candidates: list[str] = []
    fence = JSON_FENCE.search(text)
    if fence:
        candidates.append(fence.group(1))
    candidates.append(text)

    for cand in candidates:
        cand = cand.strip()
        try:
            return _loads_response(cand)
        except json.JSONDecodeError:
            pass
        # 첫 {..} 또는 [..] 블록 스캔
        # Scan only the first/root container. A nested ranking/items array is
        # not a substitute for a malformed enclosing object and loses metadata.
        first = min((p for p in (cand.find("{"), cand.find("[")) if p >= 0), default=-1)
        if first < 0:
            continue
        opener, closer = cand[first], "}" if cand[first] == "{" else "]"
        start = first
        depth, in_str, esc = 0, False, False
        for i in range(start, len(cand)):
            ch = cand[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    chunk = cand[start : i + 1]
                    try:
                        return _loads_response(chunk)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"JSON root container is malformed: {exc.msg} at character {start + exc.pos}") from exc
    salvaged = salvage_truncated(text)
    if salvaged is not None:
        return salvaged
    raise ValueError("JSON 파싱 실패")


def salvage_truncated(text: str) -> Any:
    """출력이 잘려 끝 괄호가 없는 경우, 마지막 완결 항목까지만 복구한다."""
    start = min([p for p in (text.find("{"), text.find("[")) if p >= 0], default=-1)
    if start < 0:
        return None
    body = text[start:]
    # 끝에서부터 잘라가며 괄호를 닫아 파싱을 시도
    for cut in range(len(body), max(len(body) - 20000, 0), -1):
        frag = body[:cut].rstrip().rstrip(",")
        if not frag:
            break
        opens = []
        in_str = esc = False
        for ch in frag:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch in "{[":
                opens.append(ch)
            elif ch in "}]" and opens:
                opens.pop()
        if in_str:
            continue
        closed = frag + "".join("}" if o == "{" else "]" for o in reversed(opens))
        try:
            return json.loads(closed)
        except json.JSONDecodeError:
            continue
    return None


def _price(tier: str, tin: int, tout: int, config=None) -> float:
    tc = settings.tiers[tier]
    rates = model_pricing.resolve(model_pricing.configured(vars(tc), config))
    return float(model_pricing.calculate({'prompt_tokens':tin, 'completion_tokens':tout}, rates)['cost_usd'])


def _repair_excerpt(text: str, error: Exception) -> str:
    cause = error if isinstance(error, json.JSONDecodeError) else error.__cause__
    if isinstance(cause, json.JSONDecodeError) and cause.pos > 3000:
        # Keep the retry payload within the existing 4,000-character allowance,
        # but include the actual error even when it occurs late in the output.
        nearby = cause.doc[max(0, cause.pos - 300):cause.pos + 600]
        return text[:3000] + '\n[JSON 오류 위치 주변]\n' + nearby
    return text[:4000]


def recover_failed_json(usage: dict, expect: str = 'object') -> LLMResult | None:
    """Reparse a fully received, accounted response without a provider call."""
    records = usage.get('meta', {}).get('requests', [])
    if (not str(usage.get('raw_error', '')).startswith('ValueError: JSON root container is malformed')
            or not records or not all(r.get('usage') and not r.get('pricing_error') for r in records)
            or records[-1].get('finish_reason') != 'stop'
            or records[-1].get('response') != usage.get('text')):
        return None
    try:
        data = _loads_response(usage['text'].strip())
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict if expect == 'object' else list):
        return None
    result = LLMResult(**usage)
    result.data = data
    result.meta = dict(result.meta, durable_replay=True, format_recovery='complete-json-v1')
    return result


def chat_json(
    *,
    system: str,
    user: str,
    tier: str = "T2",
    temperature: float | None = None,
    max_tokens: int | None = None,
    expect: str = "object",  # "object" | "array"
    retries: int | None = None,
    model_config: dict | None = None,
) -> LLMResult:
    tc = settings.tiers[tier]
    if model_config:
        from types import SimpleNamespace
        tc = SimpleNamespace(**model_pricing.configured(vars(tc), model_config))
    is_reasoner = "reason" in tc.model.lower()
    attempts = retries if retries is not None else settings.max_retries
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    tokens_in = tokens_out = 0
    rates = model_pricing.resolve(vars(tc))
    cost_usd = Decimal(0)
    last_err = ""
    text = ""
    truncated = False
    request_records = []
    status_code = None
    actual_attempts = 0

    for attempt in range(attempts):
        actual_attempts = attempt + 1
        truncated = False
        text = ""
        kwargs: dict[str, Any] = {
            "model": tc.model,
            "messages": messages,
            tc.token_parameter: max_tokens or tc.max_tokens,
        }
        if tc.supports_temperature:
            kwargs["temperature"] = tc.temperature if temperature is None else temperature
        if tc.json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if tc.thinking_mode:
            kwargs["extra_body"] = {"thinking": {"type": tc.thinking_mode}}
        try:
            t0 = time.time()
            connection = _client(tier, tc.base_url) if model_config else _client(tier)
            resp = connection.chat.completions.create(**kwargs)
            elapsed = time.time() - t0
            choice = resp.choices[0]
            text = (choice.message.content or "").strip()
            truncated = getattr(choice, "finish_reason", "") == "length"
            usage = getattr(resp, "usage", None)
            usage_data = model_pricing.usage_dict(usage)
            request_records.append({"request": kwargs, "response": text,
                "provider_model":getattr(resp,'model',None),
                "finish_reason": getattr(choice, "finish_reason", ""),
                "usage": usage_data,
                "elapsed": elapsed})
            if usage:
                try:
                    charge = model_pricing.calculate(usage_data, rates)
                except model_pricing.ProviderUsageError:
                    request_records[-1]['pricing_error'] = 'invalid_provider_token_counts'
                    raise
                request_records[-1]['pricing'] = charge
                tokens_in += charge['input_tokens']
                tokens_out += charge['output_tokens']
                cost_usd += Decimal(charge['cost_usd'])
            if truncated:
                raise ValueError("응답 출력 한도 초과: 부분 JSON을 성공으로 처리하지 않습니다")
            data = extract_json(text)
            if expect == "array" and isinstance(data, dict):
                # {"items":[...]} 처럼 감싸진 경우 자동 언랩
                for key in ("items", "result", "results", "data", "list", "output"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break
                else:
                    arrays = [v for v in data.values() if isinstance(v, list)]
                    if len(arrays) == 1:
                        data = arrays[0]
            return LLMResult(
                data=data,
                text=text,
                tier=tier,
                model=tc.model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=float(cost_usd),
                meta={"elapsed": round(elapsed, 2), "attempt": attempt + 1,
                      "requested_model":tc.model,"provider_model":getattr(resp,'model',None),
                      "cost_basis":rates['basis'], "pricing_rates":rates,
                      "truncated": truncated, "requests": request_records},
            )
        except Exception as exc:  # noqa: BLE001
            status_code = getattr(exc, "status_code", None)
            last_err = f"{type(exc).__name__}: {exc}"
            if len(request_records) < actual_attempts:
                request_records.append({"request": kwargs, "response": "", "usage": {},
                    "finish_reason": "error", "status_code": status_code,
                    "error_type": type(exc).__name__, "elapsed": time.time() - t0})
            log.warning("LLM 호출 실패 (tier=%s, %d/%d): %s%s", tier, attempt + 1, attempts,
                        last_err, " [출력 길이 초과]" if truncated else "")
            if (isinstance(exc, model_pricing.ProviderUsageError) or
                    status_code in (401, 402, 403) or attempt + 1 >= attempts):
                break
            if truncated:  # 잘렸으면 분량을 줄여 다시 요청
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {
                        "role": "user",
                        "content": f"직전 응답이 {max_tokens or tc.max_tokens} 토큰 출력 한도를 넘어 잘렸다. "
                                   "필수 필드, 요청된 모든 대상 ID, 사용자 수치·단위·금지사항을 유지하라. "
                                   "중복 설명·원문 재인용·빈 선택 필드·들여쓰기를 제거하고 각 설명은 짧은 구절로 압축하라. "
                                   "선택 항목만 줄일 수 있으며 필수 평가 대상과 사용자 제약을 누락하지 마라. "
                                   "처음부터 **완결된 JSON**으로 다시 출력하라.",
                    },
                ]
            elif text:  # 형식 오류 → 교정 요청
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": _repair_excerpt(text, exc)},
                    {
                        "role": "user",
                        "content": "직전 응답이 유효한 JSON이 아니었다. 설명 없이 "
                        f"{'JSON 배열' if expect == 'array' else 'JSON 객체'}만 다시 출력하라. "
                        f"파서 오류: {last_err[:240]}. "
                        '표는 "table_columns":["열"],"table_rows":[["셀"]] 형식이며 '
                        '키 없는 행 배열을 쓰지 마라. 요청된 모든 단계와 내용은 유지하라.',
                    },
                ]
            time.sleep(1.5 * (attempt + 1))

    error = LLMError(f"LLM 응답 실패: {last_err}", status_code=status_code)
    error.usage = LLMResult(data=None, text=text, tier=tier, model=tc.model,
                           tokens_in=tokens_in, tokens_out=tokens_out, raw_error=last_err,
                           meta={"requests": request_records, "attempt": actual_attempts,
                                 "cost_basis":rates['basis'], "pricing_rates":rates,
                                 "status_code": status_code, "terminal": error.terminal},
                           cost_usd=float(cost_usd))
    raise error


def healthcheck() -> dict:
    try:
        r = chat_json(
            system='You reply only with JSON.',
            user='Reply exactly {"ok": true}',
            tier="T1",
            max_tokens=32,
            retries=1,
        )
        return {"ok": True, "model": r.model, "data": r.data}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
