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


def compatible_body(prompt_id: str, body: str) -> str:
    """Keep old pins stored; render the explicitly requested full-review policy."""
    # The user retired the old candidate quotas and requested complete review.
    # These contracts must agree with the new validators on explicit reruns too.
    # The stored bundle itself is untouched; rendered prompts remain in traces.
    if prompt_id in {'P_S5_MERGE', 'P_S6_CONCEPT', 'P_S7_GATEKEEPER', 'P_S8_RANK'}:
        body = _read(prompt_id)
    if prompt_id in {f"P_S5_ARIZ_PART{part}" for part in (1, 2, 3, 4, 7)}:
        from . import knowledge as K
        part_id = int(prompt_id[-1])
        marker = f"[ARIZ Part{part_id} 완전성 계약 v1]"
        if marker not in body:
            codes = "·".join(step["code"] for step in K.ariz_part(part_id).get("steps", [])
                             if step.get("required"))
            body += (f"\n\n{marker}\nsteps에는 필수 {codes}를 각각 정확히 한 번 기록한다. "
                     "출력 예시의 첫 항목만 반환해서는 안 된다. 각 항목은 step_code, step_title, "
                     "status(DONE|SKIPPED|BLOCKED), 비어 있지 않은 output을 포함한다. "
                     "적용할 수 없는 방법은 SKIPPED와 해당 문제에서 적용 불가한 이유를 기록하고, "
                     "검토가 막힌 경우 BLOCKED와 부족한 정보를 기록한다. "
                     "표를 포함하면 table_columns는 문자열 배열, table_rows는 같은 열 수의 문자열 행 배열로 기록한다.\n")
    if prompt_id == "P_S5_ARIZ_PART5" and "[ARIZ Part5 완전성 계약 v1]" not in body:
        body += """

[ARIZ Part5 완전성 계약 v1]
steps에는 필수 5.1·5.3·5.4를 각각 정확히 한 번 기록한다. 각 항목은
step_code, step_title, status(DONE|SKIPPED|BLOCKED), 비어 있지 않은 output을 포함한다.
적용할 수 없거나 막혔으면 SKIPPED/BLOCKED와 구체적인 이유를 output에 기록한다.
ideas는 배열이며 각 아이디어에 title, idea, source_step(5.1~5.4)을 기록하고,
후속 검증에 사용할 요약을 final_ideas 문자열 배열에도 남긴다.
적합한 아이디어가 없으면 억지로 만들지 말고 ideas: [], final_ideas: []와 함께
unresolved_reason에 필수 지식베이스 검토 후에도 미해결인 이유를 명시한다.
"""
    if prompt_id == "P_S8_RANK":
        # Guard against accidentally restoring the retired late Part6 clause.
        body = re.sub(r"\n\[최종 해결책 수에 따른 ARIZ Part 6 추가 코멘트\].*?(?=\n\[출력 JSON\])",
                      "", body, flags=re.S)
        body = re.sub(r',\s*"problem_reformulation_review"\s*:\s*null', "", body)
        body = re.sub(r"\n검토 대상이면 null 대신[^\n]*", "", body)
    return body


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
    body = compatible_body(prompt_id, _read(prompt_id))

    def sub(m: re.Match[str]) -> str:
        return _stringify(vars_.get(m.group(1), ""))

    return VAR.sub(sub, body)


def list_prompts() -> list[str]:
    return sorted(p.stem for p in PROMPT_DIR.glob("*.md"))


def raw(prompt_id: str) -> str:
    return _read(prompt_id)
