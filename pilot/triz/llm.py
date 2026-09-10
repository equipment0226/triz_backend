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
from functools import lru_cache
from typing import Any

from openai import OpenAI

from .settings import settings

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
def _client(tier: str) -> OpenAI:
    tc = settings.tiers[tier]
    if not tc.api_key:
        raise LLMError("LLM_API_KEY 가 설정되지 않았습니다. pilot/.env 를 확인하세요.")
    return OpenAI(api_key=tc.api_key, base_url=tc.base_url, timeout=settings.timeout, max_retries=0)


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
            return json.loads(cand)
        except json.JSONDecodeError:
            pass
        # 첫 {..} 또는 [..] 블록 스캔
        for opener, closer in (("{", "}"), ("[", "]")):
            start = cand.find(opener)
            if start < 0:
                continue
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
                            return json.loads(chunk)
                        except json.JSONDecodeError:
                            break
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


def _price(tier: str, tin: int, tout: int) -> float:
    tc = settings.tiers[tier]
    return (tin / 1_000_000) * tc.cost_in + (tout / 1_000_000) * tc.cost_out


def chat_json(
    *,
    system: str,
    user: str,
    tier: str = "T2",
    temperature: float | None = None,
    max_tokens: int | None = None,
    expect: str = "object",  # "object" | "array"
    retries: int | None = None,
) -> LLMResult:
    tc = settings.tiers[tier]
    is_reasoner = "reason" in tc.model.lower()
    attempts = retries if retries is not None else settings.max_retries
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    tokens_in = tokens_out = 0
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
        try:
            t0 = time.time()
            resp = _client(tier).chat.completions.create(**kwargs)
            elapsed = time.time() - t0
            choice = resp.choices[0]
            text = (choice.message.content or "").strip()
            truncated = getattr(choice, "finish_reason", "") == "length"
            usage = getattr(resp, "usage", None)
            request_records.append({"request": kwargs, "response": text,
                "finish_reason": getattr(choice, "finish_reason", ""),
                "usage": usage.model_dump() if usage and hasattr(usage, "model_dump") else {},
                "elapsed": elapsed})
            if usage:
                tokens_in += getattr(usage, "prompt_tokens", 0) or 0
                tokens_out += getattr(usage, "completion_tokens", 0) or 0
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
                cost_usd=_price(tier, tokens_in, tokens_out),
                meta={"elapsed": round(elapsed, 2), "attempt": attempt + 1,
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
            if status_code in (401, 402, 403) or attempt + 1 >= attempts:
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
                    {"role": "assistant", "content": text[:4000]},
                    {
                        "role": "user",
                        "content": "직전 응답이 유효한 JSON이 아니었다. 설명 없이 "
                        f"{'JSON 배열' if expect == 'array' else 'JSON 객체'}만 다시 출력하라.",
                    },
                ]
            time.sleep(1.5 * (attempt + 1))

    error = LLMError(f"LLM 응답 실패: {last_err}", status_code=status_code)
    error.usage = LLMResult(data=None, text=text, tier=tier, model=tc.model,
                           tokens_in=tokens_in, tokens_out=tokens_out, raw_error=last_err,
                           meta={"requests": request_records, "attempt": actual_attempts,
                                 "status_code": status_code, "terminal": error.terminal},
                           cost_usd=_price(tier, tokens_in, tokens_out))
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
