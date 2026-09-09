"""TRIZ 지식 자산 로더.

원칙: 39 파라미터·40 원리·모순행렬·76 표준해는 LLM 기억이 아니라 이 파일들에서만 온다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

KDIR = Path(__file__).resolve().parent / "knowledge"


@lru_cache(maxsize=None)
def _load(name: str) -> Any:
    path = KDIR / name
    if not path.exists():
        return {}
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


# ───────────────────────────── 파라미터
def params(scheme: str = "ENG_39") -> dict[str, dict]:
    return _load("params_biz_31.json" if scheme == "BIZ_31" else "params_39.json")


def param_name(pid: int | str, scheme: str = "ENG_39") -> str:
    p = params(scheme).get(str(pid))
    return p.get("name_ko", f"#{pid}") if p else f"#{pid}"


def param_dictionary_text(scheme: str = "ENG_39") -> str:
    lines = []
    for pid, p in params(scheme).items():
        en = f" ({p['name_en']})" if p.get("name_en") else ""
        lines.append(f"#{pid} {p['name_ko']}{en}: {p.get('definition', '')}")
    return "\n".join(lines)


def valid_param(pid: int, scheme: str = "ENG_39") -> bool:
    return str(pid) in params(scheme)


# ───────────────────────────── 발명원리
def principles() -> dict[str, dict]:
    return _load("principles_40.json")


def principle(pid: int | str) -> dict:
    return principles().get(str(pid), {})


def principle_name(pid: int | str) -> str:
    return principle(pid).get("name_ko", f"원리{pid}")


def principle_hint(pid: int | str) -> str:
    p = principle(pid)
    return p.get("definition") or p.get("name_ko", "")


def principles_block(ids: list[int]) -> str:
    out = []
    for pid in ids:
        p = principle(pid)
        if not p:
            continue
        subs = " / ".join(p.get("sub", []))
        out.append(f"#{pid} {p['name_ko']}({p.get('name_en','')}): {p.get('definition','')}\n   하위 기법: {subs}")
    return "\n".join(out)


def all_principles_brief() -> str:
    return "\n".join(f"#{pid} {p['name_ko']}: {p.get('definition','')}" for pid, p in principles().items())


# ───────────────────────────── 모순 행렬
def matrix() -> dict:
    return _load("matrix_39x39.json")


def lookup_matrix(improving: int, worsening: int) -> tuple[list[int], str]:
    """(원리 번호 목록, 출처). 행렬 데이터가 없으면 빈 목록 + 'LLM_FALLBACK'."""
    cells = matrix().get("cells") or {}
    row = cells.get(str(improving)) or {}
    ids = row.get(str(worsening)) or []
    if ids:
        return [int(x) for x in ids], "MATRIX"
    return [], "LLM_FALLBACK"


def matrix_loaded() -> bool:
    return bool(matrix().get("cells"))


# ───────────────────────────── 76 표준해
def standards() -> list[dict]:
    return _load("standards_76.json").get("standards", [])


SU_TO_TAGS = {
    "MISSING_S2": ["MISSING_S2", "INCOMPLETE"],
    "MISSING_F": ["MISSING_F", "INCOMPLETE"],
    "INCOMPLETE": ["INCOMPLETE"],
}


def standard_hints(completeness: str, effect: str) -> list[str]:
    hints: list[str] = []
    if completeness in ("MISSING_S2", "MISSING_F", "INCOMPLETE"):
        hints += ["1.1.1", "1.1.2", "1.1.3"]
    if effect == "USEFUL_INSUFFICIENT":
        hints += ["1.1.4", "1.1.5", "2.1.1", "2.1.2", "2.2.1", "2.2.2", "2.2.4"]
    if effect == "HARMFUL":
        hints += ["1.2.1", "1.2.2", "1.2.3", "1.2.4"]
    if effect == "EXCESSIVE":
        hints += ["1.1.6", "1.1.7", "1.1.8", "2.2.1"]
    if effect == "MEASUREMENT":
        hints += ["4.1.1", "4.1.2", "4.1.3", "4.2.1", "4.2.2", "4.3.1"]
    return hints


def candidate_standards(completeness: str, effect: str, limit: int = 12) -> list[dict]:
    """물질-장 상태에 맞는 표준해 후보를 고른다."""
    tags = set(SU_TO_TAGS.get(completeness, [])) | {effect}
    hint_codes = set(standard_hints(completeness, effect))
    scored: list[tuple[int, dict]] = []
    for st in standards():
        score = 0
        if st["code"] in hint_codes:
            score += 3
        if tags & set(st.get("applicability", [])):
            score += 2
        if st.get("verified"):
            score += 1
        if score:
            scored.append((score, st))
    scored.sort(key=lambda x: -x[0])
    picked = [st for _, st in scored[:limit]]
    if not picked:
        picked = [st for st in standards() if st.get("verified")][:limit]
    return picked


def standards_block(items: list[dict]) -> str:
    return "\n".join(
        f"{s['code']} {s['title_ko']}: {s['description']}\n   모델 변환: {s.get('transformation','-')}"
        for s in items
    )


def standard_codes() -> set[str]:
    return {s["code"] for s in standards()}


# ───────────────────────────── 분리원리 / 트렌드 / 효과
def separation() -> dict:
    return _load("separation.json")


def separation_block() -> str:
    return "\n".join(
        f"- {k} ({v['name_ko']}): {v['question']}\n   연계 발명원리: "
        + ", ".join(f"{p}({principle_name(p)})" for p in v["principles"])
        for k, v in separation().items()
    )


def trends() -> list[dict]:
    return _load("trends.json")


def trends_block() -> str:
    return "\n".join(f"{t['id']} {t['name_ko']}: " + " → ".join(t["stages"]) for t in trends())


def effects() -> list[dict]:
    return _load("effects.json")


def effects_block(limit: int = 10, required_functions=()) -> str:
    import re
    def terms(value):
        words = re.findall(r"[\w]{2,}", value.lower())
        return {part for word in words for part in [word] + [word[i:i+2] for i in range(len(word)-1)]}
    query = terms(" ".join(required_functions))
    items = sorted(effects(), key=lambda item: -len(query & terms(item["function_ko"]))) if query else effects()
    out = [f"현재 로컬 카탈로그: 표준해 {len(standards())}개, 효과 기능군 {len(effects())}개. 미수록 지식을 검증된 카탈로그처럼 주장하지 않는다."]
    for item in items[:limit]:
        descriptions = "; ".join(f"{e['name']}: {e.get('principle','')} (조건: {e.get('conditions','미확인; 적용 전 확인')})" for e in item["effects"])
        out.append(f"- {item['function_ko']}: {descriptions}")
    return "\n".join(out)


def ariz_script() -> dict:
    return _load("ariz_85c.yaml")


def ariz_part(part_id: int) -> dict:
    for part in ariz_script().get("parts", []):
        if part["id"] == part_id:
            return part
    return {}


def ariz_part_steps_text(part_id: int) -> str:
    part = ariz_part(part_id)
    return "\n".join(
        f"{s['code']} {s['title']}" + (" (필수)" if s.get("required") else "")
        for s in part.get("steps", [])
    )
