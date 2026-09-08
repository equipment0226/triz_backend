"""LLM 출력 → Pydantic 모델 안전 변환.

LLM은 종종 스키마에 없는 열거값이나 타입을 만들어낸다.
이때 예외로 파이프라인을 죽이지 말고, 문제 필드만 버리고 기본값으로 되돌린다.
"""
from __future__ import annotations

import logging
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

log = logging.getLogger("triz.coerce")
T = TypeVar("T", bound=BaseModel)


def build(model: Type[T], data: Any, **overrides: Any) -> T | None:
    """dict → 모델. 실패한 필드는 제거하고 기본값으로 대체한다. 끝내 실패하면 None."""
    if not isinstance(data, dict):
        return None
    payload = {k: v for k, v in data.items() if k in model.model_fields}
    payload.update(overrides)

    for _ in range(len(model.model_fields) + 1):
        try:
            return model(**payload)
        except ValidationError as exc:
            dropped = False
            for err in exc.errors():
                loc = err.get("loc") or ()
                key = loc[0] if loc else None
                if isinstance(key, str) and key in payload:
                    log.debug("필드 폐기 %s.%s = %r (%s)", model.__name__, key,
                              payload[key], err.get("type"))
                    payload.pop(key)
                    dropped = True
            if not dropped:
                break
    try:
        return model(**{k: v for k, v in overrides.items() if k in model.model_fields})
    except ValidationError:
        return None


def build_list(model: Type[T], items: Any, **overrides: Any) -> list[T]:
    if not isinstance(items, list):
        return []
    out: list[T] = []
    for item in items:
        obj = build(model, item, **overrides)
        if obj is not None:
            out.append(obj)
    return out
