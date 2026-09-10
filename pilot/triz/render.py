"""리포트 렌더링.

- LLM이 아니라 Jinja2 템플릿이 문서를 만든다.
- 내부 ID(TC-…, CPT-…)는 렌더 단계에서 사람이 읽는 라벨로 치환한다.
- 단계별 시각화(mermaid)는 상태 데이터로부터 여기서 생성한다.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import digest, knowledge as K
from .labels import build_label_map, humanize, label_of
from .schema import GlobalState, RunMode
from .settings import settings

TEMPLATE_DIR = settings.root / "templates"

TRACK_KO = {
    "A_MATRIX": "모순행렬·40 발명원리", "B_SEPARATION": "분리 원리", "C_STANDARDS": "76 표준해",
    "D_ARIZ": "ARIZ-85C", "E_TRIMMING": "트리밍", "F_TRENDS": "진화 트렌드",
    "G_FOS": "기능지향탐색(FOS)", "H_EFFECTS": "물리효과",
}
QUADRANT_KO = {"QUICK_WIN": "즉시 실행", "BIG_BET": "전략 투자", "FILL_IN": "보완 과제", "AVOID": "보류"}
NOVELTY_KO = {"SAME_DOMAIN": "동일 분야 접근", "CROSS_DOMAIN": "타산업 이식", "NEW": "신규 제안"}
SCALE_KO = {"PARAMETER": "조건·규칙 조정", "PARTIAL": "부분 변경", "REDESIGN": "구조 재설계"}
CATEGORY_KO = {
    "USER_STATED": "사용자명시", "ENVIRONMENT": "운전환경", "MATERIAL_COMPAT": "재료양립성",
    "PHYSICS": "물리법칙", "REGULATION": "안전·규제", "OPERATION": "운영·보전",
    "INTERFACE": "인터페이스", "ECONOMIC": "경제성",
}
LEVEL_KO = {"SUPER": "상위 시스템", "TARGET": "대상 시스템", "SUB": "하위 부품",
            "ENVIRONMENT": "환경", "PRODUCT": "제품·대상물"}
COMPLETENESS_KO = {"COMPLETE": "완전", "INCOMPLETE": "불완전",
                   "MISSING_S2": "도구(S2) 없음", "MISSING_F": "장(F) 없음"}
SU_EFFECT_KO = {"USEFUL_SUFFICIENT": "유익·충분", "USEFUL_INSUFFICIENT": "유익·부족",
                "HARMFUL": "유해", "EXCESSIVE": "과잉", "MEASUREMENT": "측정"}
RESOURCE_KO = {"SUBSTANCE": "물질", "FIELD": "장", "SPACE": "공간", "TIME": "시간",
               "INFORMATION": "정보", "FUNCTIONAL": "기능", "SYSTEM_LEVEL": "시스템 계층"}
WHERE_KO = {"IN_SYSTEM": "시스템 내부", "IN_SUPERSYSTEM": "상위 시스템",
            "IN_ENVIRONMENT": "주변 환경", "WASTE": "폐자원", "DERIVED": "파생 자원"}
AVAIL_KO = {"FREE": "무상", "LOW_COST": "저비용", "COSTLY": "고비용"}
GRADE_KO = {"LOW": "낮음", "MID": "보통", "MED": "보통", "HIGH": "높음"}
MATURITY_KO = {"CONCEPT": "개념 단계", "CONCEPT_ONLY": "개념 단계",
               "PROTOTYPE_KNOWN": "시작품·문헌 확인", "PROVEN_ELSEWHERE": "타산업 검증",
               "COMMERCIAL_ELSEWHERE": "타산업 상용화", "COMMERCIAL_SAME": "동종업계 상용화"}
SOURCE_KO = {"PATENT": "특허", "PAPER": "논문", "STANDARD": "표준", "VENDOR": "벤더",
             "ARTICLE": "기술자료", "MODEL_KNOWLEDGE": "모델 지식",
             "INTERNAL_FEEDBACK": "내부 피드백"}

_ENUM_KO = {
    "S8_REFERENCES": "근거 적용성 검토",
    "GOAL": "목표 달성", "RESOLUTION": "모순 해소", "CAUSAL": "인과 근거",
    **TRACK_KO, **QUADRANT_KO, **NOVELTY_KO, **SCALE_KO, **CATEGORY_KO, **LEVEL_KO,
    **COMPLETENESS_KO, **SU_EFFECT_KO, **RESOURCE_KO, **WHERE_KO, **AVAIL_KO,
    **GRADE_KO, **MATURITY_KO, **SOURCE_KO,
    "USEFUL": "유익", "HARMFUL": "유해", "INSUFFICIENT": "부족", "NORMAL": "적정",
    "EXCESSIVE": "과잉", "DONE": "완료", "SKIPPED": "건너뜀", "BLOCKED": "중단",
    "BASIC": "기본기능", "AUXILIARY": "보조기능", "CORRECTIVE": "보정기능",
    "S0_BOOTSTRAP": "실행 계획", "S1_INTAKE": "문제 접수", "S2_CONFIRM": "대상 확정",
    "S3_ANALYZE": "시스템 분석", "S4_DEFINE": "문제 정의", "S5_SOLVE": "해결책 탐색",
    "S6_CONCEPT": "개념 구체화", "S7_CONSTRAINT": "제약 검문", "S8_EVALUATE": "평가",
    "S9_REPORT": "리포트", "S10_FEEDBACK": "피드백",
}
_ENUM_RE = re.compile(r"\b(" + "|".join(sorted(_ENUM_KO, key=len, reverse=True)) + r")\b")
_FENCE_RE = re.compile(r"```.*?```", re.S)


def _localize(md: str) -> str:
    """본문에 남은 내부 열거값을 한글로 바꿈. 코드 블록은 건드리지 않는다."""
    def swap(chunk: str) -> str:
        return _ENUM_RE.sub(lambda m: _ENUM_KO[m.group(1)], chunk)

    parts: list[str] = []
    last = 0
    for fence in _FENCE_RE.finditer(md):
        parts.append(swap(md[last:fence.start()]))
        parts.append(fence.group(0))
        last = fence.end()
    parts.append(swap(md[last:]))
    return "".join(parts)


def _safe(text: str, n: int = 24) -> str:
    text = re.sub(r'["\[\]:,\n()]', " ", str(text or ""))
    text = " ".join(text.split())
    return (text[:n - 1].strip() + "…") if len(text) > n else text


def _wrap(text: str, n: int = 34, width: int = 17) -> str:
    """노드 라벨을 여러 줄로 접어 가로로 터지거나 잘리는 것을 막는다."""
    t = _safe(text, n)
    if len(t) <= width:
        return t
    lines: list[str] = []
    cur = ""
    for word in t.split(" "):
        if cur and len(cur) + len(word) + 1 > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
        while len(cur) > width:  # 띄어쓰기 없는 긴 단어 처리
            lines.append(cur[:width])
            cur = cur[width:]
    if cur:
        lines.append(cur)
    return "<br/>".join(lines[:3])


def _safe_join(value: Any, sep: str = ", ", attribute: str | None = None) -> str:
    """LLM 산출물에 None이나 객체가 섞여 있어도 리포트가 띄도록 Jinja join을 대체한다."""
    if value in (None, ""):
        return ""
    if isinstance(value, (str, bytes)):
        return str(value)
    items = list(value)
    if attribute:
        items = [i.get(attribute) if isinstance(i, dict) else getattr(i, attribute, None)
                 for i in items]
    return sep.join(str(i) for i in items if i not in (None, ""))


def predicate(text: str) -> str:
    """'높아야 한다' 같은 종결형은 그대로, '높은 압력' 같은 명사구에만 서술어를 붙인다."""
    t = " ".join(str(text or "").split()).rstrip(".")
    if not t or t.endswith("다"):
        return t
    last = t[-1]
    if "가" <= last <= "힙":
        has_final = (ord(last) - 0xAC00) % 28 != 0
        return t + ("이어야 한다" if has_final else "여야 한다")
    return t + "여야 한다"


# ──────────────────────────────────── 시각화 생성기
def quadrant_mermaid(s: GlobalState) -> str:
    evs = [e for e in s.evaluation.evaluations if e.aggregate]
    if not evs:
        return ""
    lines = [
        "quadrantChart",
        '    title 리스크 대비 기대효과',
        '    x-axis "낮은 리스크" --> "높은 리스크"',
        '    y-axis "낮은 효과" --> "높은 효과"',
        '    quadrant-1 "전략 투자"',
        '    quadrant-2 "즉시 실행"',
        '    quadrant-3 "보완 과제"',
        '    quadrant-4 "보류"',
    ]
    # Plot measured aggregates directly; never move points into cosmetic quadrants.
    for e in evs:
        c = s.concept(e.concept_id)
        if not c:
            continue
        risk = e.aggregate.get("RISK", 3.0)
        benefit = (e.aggregate.get("QUALITY", 3.0) + e.aggregate.get("FEASIBILITY", 3.0)) / 2
        x = max(0, min(1, (5 - risk) / 4))
        y = max(0, min(1, (benefit - 1) / 4))
        lines.append(f'    "{_safe(c.title, 28)}": [{x:.3f}, {y:.3f}]')
    return "\n".join(lines)

def _pie(title: str, counts: dict[str, int]) -> str:
    if not counts:
        return ""
    lines = ["pie showData", f"    title {title}"]
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f'    "{_safe(k, 26)}" : {v}')
    return "\n".join(lines)


def track_pie_mermaid(s: GlobalState) -> str:
    counts: dict[str, int] = {}
    for idea in s.solve.raw_ideas:
        key = TRACK_KO.get(idea.track, idea.track or "기타")
        counts[key] = counts.get(key, 0) + 1
    return _pie("해결 트랙별 아이디어 기여", counts)


def novelty_pie_mermaid(s: GlobalState) -> str:
    counts: dict[str, int] = {}
    for c in s.concepts:
        key = NOVELTY_KO.get(c.novelty_class, c.novelty_class)
        counts[key] = counts.get(key, 0) + 1
    return _pie("해결책 신규성 구성", counts)


def solution_flow_mermaid(s: GlobalState) -> str:
    """핵심문제 → 모순 → 해결 개념으로 이어지는 전체 논리 흐름."""
    if not s.concepts:
        return ""
    lines = ["flowchart LR",
             "  classDef prob fill:#3b2530,stroke:#d9534f,color:#fff;",
             "  classDef con fill:#2b3350,stroke:#5b8def,color:#fff;",
             "  classDef sol fill:#243a2e,stroke:#4caf82,color:#fff;"]
    con_nodes: dict[str, str] = {}
    idx = 0
    for t in s.definition.technical_contradictions:
        idx += 1
        con_nodes[t.id] = f"C{idx}"
        lines.append(f'  C{idx}["기술모순<br/>{_wrap(t.label, 30, 15)}"]:::con')
    for p in s.definition.physical_contradictions:
        idx += 1
        con_nodes[p.id] = f"C{idx}"
        lines.append(f'  C{idx}["물리모순<br/>{_wrap(p.label or p.parameter, 30, 15)}"]:::con')
    for i, k in enumerate(s.definition.key_problems, 1):
        lines.append(f'  K{i}["{_wrap(k.title, 32, 15)}"]:::prob')
        for cid in k.contradiction_ids:
            if cid in con_nodes:
                lines.append(f"  K{i} --> {con_nodes[cid]}")
    for j, e in enumerate(s.evaluation.evaluations[:6], 1):
        c = s.concept(e.concept_id)
        if not c:
            continue
        lines.append(f'  S{j}["{e.rank}위<br/>{_wrap(c.title, 32, 15)}"]:::sol')
        linked = False
        for cid in c.addresses_contradictions:
            if cid in con_nodes:
                lines.append(f"  {con_nodes[cid]} --> S{j}")
                linked = True
        if not linked and con_nodes:
            lines.append(f"  {list(con_nodes.values())[0]} --> S{j}")
    return "\n".join(lines)


def roadmap_mermaid(s: GlobalState) -> str:
    rows = s.evaluation.roadmap or []
    if not rows:
        return ""
    phases: dict[str, list[str]] = {}
    for r in rows:
        c = s.concept(r.get("concept_id", ""))
        phases.setdefault(r.get("phase", "단기"), []).append(
            _wrap(c.title if c else r.get("concept_id", ""), 34, 17))
    order = [p for p in ("단기", "중기", "장기") if p in phases] + \
            [p for p in phases if p not in ("단기", "중기", "장기")]
    lines = ["flowchart LR"]
    for pi, phase in enumerate(order):
        lines.append(f'  subgraph P{pi}["{phase}"]')
        lines.append("    direction TB")
        for ci, title in enumerate(phases[phase]):
            lines.append(f'    P{pi}_{ci}["{title}"]')
        lines.append("  end")
        if pi:
            lines.append(f"  P{pi - 1}_0 --> P{pi}_0")
    return "\n".join(lines)


def _md_table(header: list[str], rows: list[list[str]], align: str = "---") -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(_cell(h) for h in header) + " |",
           "|" + "|".join([align] * len(header)) + "|"]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |"
            for r in rows]
    return "\n".join(out)

def _cell(value):
    return re.sub(r"\s*\n\s*", " ", str(value if value is not None else "")).replace("|", r"\|")


def constraint_matrix(s: GlobalState) -> dict:
    """개념 × 제약 판정 그리드."""
    cons = s.constraints.items
    mark = {"PASS": "○", "FAIL": "✕", "UNKNOWN": "?"}
    verdict_ko = {"PASS": "통과", "CONDITIONAL": "조건부", "FAIL": "탈락"}
    rows = []
    for e in s.evaluation.evaluations or []:
        c = s.concept(e.concept_id)
        chk = s.check_for(e.concept_id)
        if not c:
            continue
        per = {p.get("constraint_id"): (p.get("verdict") or "UNKNOWN")
               for p in (chk.per_constraint if chk else []) if isinstance(p, dict)}
        rows.append({"title": c.title, "verdict": (chk.verdict if chk else "CONDITIONAL") or "CONDITIONAL",
                     "cells": [per.get(con.id) or "—" for con in cons],
                     "mitigation": (chk.mitigation if chk else "") or ""})
    chunks = []
    for start in range(0, len(cons), 8):
        stop = min(start+8, len(cons))
        chunks.append(f"**제약 {start+1}–{stop} 판정**\n\n" + _md_table(
            ["해결책"] + [str(i) for i in range(start+1, stop+1)] + ["종합"],
            [[r['title']] + [mark.get(x, x) for x in r['cells'][start:stop]] + [verdict_ko.get(r['verdict'], r['verdict'])] for r in rows]))
    md = '\n\n'.join(chunks) if cons and rows else ''
    legend = "\n".join(f"{i}. {c.statement}" + (f" — {c.zone}" if c.zone else "")
                       for i, c in enumerate(cons, 1))
    return {"constraints": cons, "rows": rows, "md": md, "legend": legend}


def interaction_grid(s: GlobalState) -> dict:
    im = s.analysis.interaction_matrix
    if not im or not im.components:
        return {}
    names = im.components[:12]
    lookup: dict[tuple[str, str], str] = {}
    for cell in im.cells:
        lookup[(cell.a, cell.b)] = cell.sign
        lookup[(cell.b, cell.a)] = cell.sign
    grid = [[("·" if a == b else lookup.get((a, b), "0")) for b in names] for a in names]
    sign = {"+": "＋", "-": "－", "+-": "±", "0": "", "·": "·"}
    md = _md_table(
        [""] + [str(i) for i in range(1, len(names) + 1)],
        [[f"**{i}. {names[i - 1]}**"] + [sign.get(x, x) for x in row]
         for i, row in enumerate(grid, 1)],
    )
    return {"names": names, "grid": grid, "md": md}


def viz_bundle(s: GlobalState) -> dict:
    return {
        "quadrant": quadrant_mermaid(s),
        "track_pie": track_pie_mermaid(s),
        "novelty_pie": novelty_pie_mermaid(s),
        "flow": solution_flow_mermaid(s),
        "roadmap": roadmap_mermaid(s),
    }


# ──────────────────────────────────── 환경
def _env(labels: dict[str, str], keep_code: bool = False) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.globals.update(
        param=lambda pid, scheme="ENG_39": K.param_name(pid, scheme),
        principle=lambda pid: K.principle_name(pid),
        now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        TRACK_KO=TRACK_KO, QUADRANT_KO=QUADRANT_KO, NOVELTY_KO=NOVELTY_KO,
        SCALE_KO=SCALE_KO, CATEGORY_KO=CATEGORY_KO, LEVEL_KO=LEVEL_KO,
        COMPLETENESS_KO=COMPLETENESS_KO, SU_EFFECT_KO=SU_EFFECT_KO,
        RESOURCE_KO=RESOURCE_KO, WHERE_KO=WHERE_KO, AVAIL_KO=AVAIL_KO,
        GRADE_KO=GRADE_KO, MATURITY_KO=MATURITY_KO, SOURCE_KO=SOURCE_KO,
    )
    env.filters["lbl"] = lambda v: label_of(v, labels, keep_code)
    env.filters["hz"] = lambda v: humanize(str(v or ""), labels, keep_code)
    env.filters["pred"] = predicate
    env.filters["join"] = _safe_join
    env.filters["cell"] = _cell
    return env


def render_report(state: GlobalState, narrative: dict, template: str = "", *, diagram=None, references=None) -> str:
    from .visuals import figures
    from .report_style import reference_cards
    from .review_comments import by_concept
    labels = build_label_map(state)
    env = _env(labels)
    lite = state.control.mode == RunMode.LITE
    name = template or settings.cfg("report.lite_template" if lite else "report.template",
                                    "report_lite.md.j2" if lite else "report_full.md.j2")
    tpl = env.get_template(name)
    scheme = state.scratch.get("param_scheme", "ENG_39")

    concept_map = {c.id: c for c in state.concepts}
    evidence_map = {e.id: e for e in state.evidence}
    check_map = {c.concept_id: c for c in state.constraint_checks}
    evaluation_map = {e.concept_id: e for e in state.evaluation.evaluations}

    applied = []
    if state.analysis.nine_windows:
        applied.append("9-Windows")
    if state.analysis.function_edges:
        applied.append("기능분석(Function Analysis)")
    if state.analysis.su_fields:
        applied.append("물질-장 분석(Su-Field)")
    if state.analysis.ceca:
        applied.append("인과사슬분석(CECA)")
    if any(c.source == "DOMAIN" for c in state.constraints.items):
        applied.append("도메인 제약 발굴")
    if state.definition.ifr:
        applied.append("이상해결책(IFR)")
    if state.definition.technical_contradictions:
        applied.append("모순행렬·40 발명원리")
    if state.definition.physical_contradictions:
        applied.append("분리원리")
    if state.solve.standard_apps:
        applied.append("76 표준해")
    if state.solve.ariz:
        applied.append("ARIZ-85C")
    if state.definition.trimming:
        applied.append("트리밍")
    if state.solve.trend_apps:
        applied.append("진화 트렌드")
    if state.solve.fos_apps:
        applied.append("기능지향탐색(FOS)")
    if any(e.url for e in state.evidence):
        applied.append("문헌·특허 검색")

    from .report_groups import matrix_groups, separation_groups, effect_groups
    from .ariz_report import build as ariz_build, value_text as ariz_text
    from .visuals import ordered_trends
    matrix, unlinked_principles = matrix_groups(state)
    md = tpl.render(
        matrix_groups=matrix, unlinked_principles=unlinked_principles,
        separation_groups=separation_groups(state), effect_groups=effect_groups(state),
        ariz_report=ariz_build(state), ariz_text=ariz_text,
        ordered_trends=ordered_trends(state.solve.trend_apps),
        s=state, d=digest, narrative=narrative or {}, scheme=scheme,
        concept_map=concept_map, evidence_map=evidence_map, check_map=check_map,
        applied_tools=applied,
        excluded=state.scratch.get("excluded_concepts", []),
        s_curve=state.scratch.get("s_curve", {}),
        taboo=state.scratch.get("taboo", []),
        patents=state.scratch.get("principle_patents", {}),
        viz=viz_bundle(state),
        cmatrix=constraint_matrix(state),
        igrid=interaction_grid(state),
        figures=figures(state),
        diagram=diagram or (lambda key: ''),
        references=references or (lambda cid: '\n\n'.join(f"[{r['title']}]({r['url']})\n\n{r['description']}" for r in reference_cards(state, state.concept(cid)))),
        concept_indices={c.id: i for i, c in enumerate(state.concepts)},
        report_concepts=sorted(state.concepts, key=lambda c: evaluation_map[c.id].rank or 999 if c.id in evaluation_map else 999),
        evaluation_map=evaluation_map,
        reviewer_comments=by_concept(state),
    )
    from .report_style import plain_text
    return plain_text(_localize(humanize(md, labels)))


def save(state: GlobalState, markdown: str) -> Path:
    from . import store
    from .presentation import view
    from .visuals import figures
    store.archive(state.run_id, "report.md", markdown)
    for figure in figures(state):
        store.archive(state.run_id, f"{figure['key']}.svg", figure["svg"])
    html = render_html(state)
    store.archive(state.run_id, "report.html", html)
    path = settings.storage_dir / f"{state.run_id}.md"
    path.write_text(markdown, encoding="utf-8")
    return path

def render_html(state):
    from .presentation import view
    from .report_style import report_state
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    return env.get_template("report.html.j2").render(v=view(report_state(state)))
