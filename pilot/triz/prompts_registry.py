"""프롬프트 레지스트리.

triz/prompts/*.md 를 읽어 {{변수}} 치환만 수행한다(경량 템플릿).
파일을 수정하면 서버 재시작 없이 즉시 반영된다(파일 mtime 기반 캐시).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
_CACHE: dict[str, tuple[float, str]] = {}
VAR = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def _read(prompt_id: str) -> str:
    path = PROMPT_DIR / f"{prompt_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"프롬프트 파일 없음: {path}")
    mtime = path.stat().st_mtime
    cached = _CACHE.get(prompt_id)
    if cached and cached[0] == mtime:
        return cached[1]
    body = path.read_text(encoding="utf-8")
    if body.startswith("---"):  # YAML 프런트매터 제거
        end = body.find("\n---", 3)
        if end > 0:
            body = body[end + 4 :]
    _CACHE[prompt_id] = (mtime, body.strip())
    return body.strip()


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def render(prompt_id: str, **vars_: Any) -> str:
    body = _read(prompt_id)

    def sub(m: re.Match[str]) -> str:
        return _stringify(vars_.get(m.group(1), ""))

    return VAR.sub(sub, body)


def list_prompts() -> list[str]:
    return sorted(p.stem for p in PROMPT_DIR.glob("*.md"))


def raw(prompt_id: str) -> str:
    return _read(prompt_id)
