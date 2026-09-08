"""Deterministic, portable SVG figures generated only from structured artifacts."""
from html import escape
import math
import textwrap

def label(value, x, y, width=18, color="#273b43", size=13):
    chunks = textwrap.wrap(str(value), width=width) or [""]
    return f'<text x="{x}" y="{y}" text-anchor="middle" fill="{color}" font-size="{size}">' + "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else 19}">{escape(line)}</tspan>' for i, line in enumerate(chunks[:4])) + '</text>'

def svg(title, nodes, edges=(), columns=3):
    """nodes: (key, label, tone). Edges never inferred when the artifact has no relation."""
    columns = max(1, min(columns, len(nodes) or 1))
    width = max(360, columns * 240)
    height = max(220, math.ceil(len(nodes) / columns) * 180 + 65)
    positions = {n[0]: (120 + (i % columns) * 240, 100 + (i // columns) * 180) for i, n in enumerate(nodes)}
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title, quote=True)}">',
            '<rect width="100%" height="100%" rx="16" fill="#f6f9f8"/>',
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#7b949a"/></marker></defs>',
            label(title, width / 2, 30, 70, size=15)]
    for source, target, text, harmful in edges:
        if source not in positions or target not in positions:
            continue
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        dx, dy = x2 - x1, y2 - y1
        distance = max(1, math.hypot(dx, dy))
        trim = min(95, distance * .32)
        ax, ay, bx, by = x1 + dx / distance * trim, y1 + dy / distance * trim, x2 - dx / distance * trim, y2 - dy / distance * trim
        color = "#c66060" if harmful else "#63888d"
        dash = ' stroke-dasharray="5 4"' if harmful else ""
        body.append(f'<path d="M{ax},{ay} L{bx},{by}" stroke="{color}" stroke-width="2"{dash} marker-end="url(#arrow)"/>')
        body.append(label(text, (x1+x2)/2, (y1+y2)/2 - 12, 16, color, 11))
    for key, text, tone in nodes:
        x, y = positions[key]
        fill = {"bad": "#fbe8e7", "good": "#d9efea", "field": "#e0e8f7"}.get(tone, "#fff")
        body.append(f'<rect x="{x-98}" y="{y-42}" width="196" height="106" rx="12" fill="{fill}" stroke="#cadbd7"/>')
        body.append(label(text, x, y - 12))
    return "".join(body) + "</svg>"

def figures(state):
    out = []
    def add(key, title, nodes, edges=(), columns=3):
        if nodes:
            out.append({"key": key, "title": title, "svg": svg(title, nodes, edges, columns)})
    a, d = state.analysis, state.definition
    if a.nine_windows:
        rows = [("SUPER", "상위 시스템"), ("SYS", "대상 시스템"), ("SUB", "하위 시스템")]
        times = [("PAST", "과거"), ("PRESENT", "현재"), ("FUTURE", "미래")]
        add("nine-windows", "시스템의 시간과 공간 · 9 Windows", [
            (f"{level}_{time}", f"{name} · {when}\n{a.nine_windows.cells.get(f'{level}_{time}', '미분석')}", "good" if time == "PRESENT" else "")
            for level, name in rows for time, when in times])
    names = list(dict.fromkeys([c.name for c in a.components] + [e.subject for e in a.function_edges] + [e.object for e in a.function_edges]))
    add("functions", "기능 모델 · 점선은 유해 작용", [(n, n, "") for n in names],
        [(e.subject, e.object, e.action, e.kind == "HARMFUL") for e in a.function_edges], 4)
    for i, su in enumerate(a.su_fields):
        ns = [("F", "F · " + (su.field or "미확인 장"), "field"),
              ("S2", "S2 · " + (su.s2 or "미확인 도구"), ""),
              ("S1", "S1 · " + (su.s1 or "미확인 대상"), "bad" if su.effect == "HARMFUL" else "good")]
        edges = [("F", "S2", "에너지·작용", False), ("S2", "S1", "유해 작용" if su.effect == "HARMFUL" else "상호작용", su.effect == "HARMFUL")]
        if su.s3:
            ns.append(("S3", "S3 · " + su.s3, "good"))
        add(f"sufield-{i}", "물질–장 · " + (su.label or "상호작용"), ns, edges, 3)
    if a.ceca:
        add("ceca", "원인과 결과 · 인과사슬", [(n.id, n.text, "bad" if n.node_type == "ROOT_CAUSE" else "") for n in a.ceca.nodes],
            [(p, n.id, n.logic if n.logic != "NONE" else "원인 탐색", False) for n in a.ceca.nodes for p in n.parents], 3)
    add("resources", "사용 가능한 시스템 자원", [(str(i), r.name + "\n" + ", ".join(r.usable_for[:1]), "bad" if r.blocked_by_constraint else "good") for i, r in enumerate(a.resources)])
    if d.ifr:
        add("ifr", "이상해결책으로 가는 방향", [("now", state.intake.frame.symptom, "bad"),
            ("resource", d.ifr.x_element or "활용 자원 검토", "field"), ("ideal", d.ifr.statement, "good")],
            [("now", "resource", "자원 활용", False), ("resource", "ideal", "이상성 향상", False)])
    for i, c in enumerate(d.technical_contradictions):
        add(f"tc-{i}", "기술적 모순 · " + c.label,
            [("action", c.if_action, ""), ("good", c.then_good, "good"), ("bad", c.but_bad, "bad")],
            [("action", "good", "개선", False), ("action", "bad", "악화", True)])
    for i, c in enumerate(d.physical_contradictions):
        add(f"pc-{i}", "물리적 모순 · " + (c.label or c.parameter),
            [("a", c.state_a + "\n" + c.reason_a, "good"), ("element", c.element + " · " + c.parameter, "field"),
             ("b", c.state_b + "\n" + c.reason_b, "bad")], [("element", "a", "요구", False), ("element", "b", "동시 요구", True)])
    add("trimming", "기능을 옮기는 트리밍", [(str(i), t.target_component + " → " + t.replacement_carrier + "\n" + t.replaced_function, "good") for i, t in enumerate(d.trimming)])
    from .knowledge import param_name, principle_name
    for i, lookup in enumerate(state.solve.matrix_lookups):
        add(f"matrix-{i}", "모순행렬 · 지식 자산 조회", [("pair", param_name(lookup.improving_param_id) + " 개선 / " + param_name(lookup.worsening_param_id) + " 악화", "field")] +
            [(str(pid), principle_name(pid), "good") for pid in lookup.principle_ids],
            [("pair", str(pid), "추천 원리", False) for pid in lookup.principle_ids])
    for key, title, apps in (("standards", "물질–장 표준해 적용", state.solve.standard_apps),
                             ("separation", "분리원리 적용", state.solve.separation_apps),
                             ("trends", "시스템 진화 방향", state.solve.trend_apps),
                             ("fos", "타산업 기능 이식", state.solve.fos_apps),
                             ("effects", "공학 효과 적용", state.solve.effect_apps)):
        add(key, title, [(str(i), str(item.get("title") or item.get("interpretation") or item.get("idea") or item.get("ref") or "적용 내용 보완 필요"), "good") for i, item in enumerate(apps)])
    if state.solve.ariz:
        steps = state.solve.ariz.steps
        add("ariz", "ARIZ · 문제와 해법의 전개", [(str(i), s.step_title + "\n" + s.output, "field") for i, s in enumerate(steps)],
            [(str(i), str(i+1), "다음 검토", False) for i in range(len(steps)-1)], 3)
    for i, c in enumerate(state.concepts):
        add(f"concept-{i}", c.title, [("goal", c.one_liner, "field")] +
            [(str(j), change, "good") for j, change in enumerate(c.changes_to_system)], [], 3)
    return out
