"""TRIZ 지식 자산 로더.

원칙: 39 파라미터·40 원리·모순행렬·76 표준해는 LLM 기억이 아니라 이 파일들에서만 온다.
"""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

KDIR = Path(__file__).resolve().parent / "knowledge"


def _load(name: str) -> Any:
    path = KDIR / name
    if not path.exists():
        return {}
    stat = path.stat()
    return _load_version(str(path), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=24)
def _load_version(filename: str, mtime_ns: int, size: int) -> Any:
    path = Path(filename)
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


# Application search directions, NOT official applicability scores. Each code
# refers to the same-numbered primary-source section; its additional premises
# remain in the canonical conditions. Never infer those premises from a tag.
STANDARD_HINT_RULES = {
    "INCOMPLETE": ("1.1.1",),
    "USEFUL_INSUFFICIENT": (
        "1.1.2", "1.1.3", "1.1.4", "1.1.5", "1.1.7",
        "2.1.1", "2.1.2", "2.2.1", "2.2.2", "2.2.3", "2.2.4",
        "2.2.5", "2.2.6", "2.3.1", "2.3.2", "2.3.3",
    ),
    "HARMFUL": ("1.2.1", "1.2.2", "1.2.3", "1.2.4", "1.2.5"),
    "EXCESSIVE": ("1.1.6", "1.1.8", "2.2.1"),
    "MEASUREMENT": (
        "4.1.1", "4.1.2", "4.1.3", "4.2.1", "4.2.2", "4.2.3", "4.2.4",
        "4.3.1", "4.3.2", "4.3.3", "4.4.1", "4.4.2", "4.4.3",
        "4.4.4", "4.4.5", "4.5.1", "4.5.2",
    ),
}


def standard_hints(completeness: str, effect: str) -> list[str]:
    hints = list(STANDARD_HINT_RULES["INCOMPLETE"]) if completeness in SU_TO_TAGS else []
    hints.extend(STANDARD_HINT_RULES.get(effect, ()) if effect != "INCOMPLETE" else ())
    return list(dict.fromkeys(hints))


def _standard_search_text(item: dict) -> str:
    """Only mechanism/condition text, without audit metadata or source URLs."""
    parts = [item["description"], item["transformation"]]
    for child in [*item.get("substandards", []), *item.get("variants", [])]:
        parts.extend(str(child.get(key, "")) for key in ("title_ko", "transformation", "conditions"))
    parts.extend(item.get("development_sequence", []))
    return " ".join(parts)


def candidate_standards(completeness: str, effect: str, limit: int = 12, required_functions=()) -> list[dict]:
    """Return unconfirmed candidates, keeping state anchors in a global search."""
    if limit <= 0:
        return []
    catalog = standards()
    by_code = {s['code']: s for s in catalog}
    hints = [code for code in standard_hints(completeness, effect) if code in by_code]
    # With one slot, examine whether measurement is needed before completing a
    # measuring model. With two slots both independent directions survive.
    anchors = (["4.1.1"] if effect == "MEASUREMENT" else [])
    anchors += ["1.1.1"] if completeness in SU_TO_TAGS else []
    anchors = [code for code in anchors if code in by_code][:limit]
    state_order = list(dict.fromkeys(anchors + hints))
    queries = [str(q).strip() for q in required_functions if str(q).strip()]
    matched = set()
    if queries:
        from .effect_catalog import select_effects, terms
        entries = [dict(id=s['code'], name=s['title_ko'], principle=_standard_search_text(s),
                        conditions=s['conditions'], domain='PHYSICAL') for s in catalog]
        ranked = select_effects([dict(function_ko='표준해 적용', effects=entries)], queries, limit=len(entries))
        query_terms = set(terms(' '.join(queries)))
        matched = {e['id'] for e in entries if query_terms.intersection(terms(
            ' '.join((e['name'], e['principle'], e['conditions']))))}
        reserved = min(limit, len(state_order), max(len(anchors), min(3, limit // 4)))
        state_picks = state_order[:reserved]
        functional = [e['id'] for e in ranked if e['id'] not in state_picks]
        order = anchors + functional[:limit-reserved] + state_picks + functional
    else:
        order = state_order or list(by_code)
    result = []
    for code in list(dict.fromkeys(order))[:limit]:
        item = deepcopy(by_code[code])
        item['candidate_basis'] = (["state_hint"] if code in hints else []) + (["function_search"] if code in matched else [])
        if not item['candidate_basis']:
            item['candidate_basis'] = ["catalog_exploration"]
        item['candidate_status'] = 'UNCONFIRMED'
        result.append(item)
    return result


def standards_block(items: list[dict]) -> str:
    lines = []
    for s in items:
        lines.append(f"{s['code']} {s['title_ko']}: {s['description']}\n   모델 변환: {s.get('transformation','-')}"
                     f"\n   조건: {s.get('conditions','미확인')}\n   한계: {s.get('limitations','미확인')} (편집상 공학 검토)")
        basis = ', '.join(s.get('candidate_basis', ['caller_selection']))
        lines.append(f"   후보 근거: {basis}; 조건 충족 미확인")
        for child in s.get('substandards', []):
            lines.append(f"   하위 {child['code']} {child['title_ko']}: {child['transformation']} / 조건: {child['conditions']}")
        for variant in s.get('variants', []):
            lines.append(f"   분기 {variant['title_ko']}: {variant['transformation']} / 조건: {variant['conditions']}")
        if s.get('development_sequence'):
            lines.append('   원전 발전 순서: ' + ' → '.join(s['development_sequence']))
    return '\n'.join(lines)


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
    from .effect_catalog import format_effects
    groups = effects()
    return format_effects(effect_candidates(required_functions,limit),len(groups),
                          sum(len(g['effects']) for g in groups),len(standards()))


def effect_candidates(required_functions=(), limit: int = 6) -> list[dict]:
    from .effect_catalog import select_effects
    references = _load('effects_sources.json')
    groups = [dict(group,effects=[dict(references.get(e.get('id'),{}),**e) for e in group['effects']]) for group in effects()]
    return select_effects(groups,required_functions,limit=max(0,limit)*4)


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
