"""Portable SVG diagrams with text-aware layout and complete relationship legends."""
from html import escape
import math
import hashlib
import unicodedata

def wrap(value, pixels, size=13):
    """Conservative glyph widths for Korean, Latin and unbroken identifiers."""
    lines = []
    for paragraph in str(value).split("\n"):
        line, used = "", 0
        for char in paragraph:
            advance = 0 if unicodedata.combining(char) else size * (1.05 if unicodedata.east_asian_width(char) in "WF" else .72)
            if line and used + advance > pixels:
                lines.append(line); line, used = "", 0
            line += char; used += advance
        lines.append(line)
    return lines or [""]

def label(value, x, y, width=18, color="#273b43", size=13, pixels=None, anchor="middle"):
    chunks = wrap(value, pixels or width * size, size)
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-size="{size}">' + "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.55}">{escape(line)}</tspan>' for i, line in enumerate(chunks)) + '</text>'

def svg(title, nodes, edges=(), columns=3):
    columns = max(1, min(columns, len(nodes) or 1))
    width, box_width, size = max(360, columns * 300 + 24), 252, 13
    header_height = len(wrap(title, width - 48, 16)) * 25 + 35
    heights = [max(90, len(wrap(n[1], box_width - 36, size)) * size * 1.55 + 42) for n in nodes]
    positions, top = {}, header_height
    for row in range(math.ceil(len(nodes) / columns)):
        indices = range(row * columns, min(len(nodes), (row + 1) * columns))
        row_height = max(heights[i] for i in indices)
        for i in indices:
            positions[nodes[i][0]] = (width / columns * (i % columns + .5), top + row_height / 2, row_height)
        top += row_height + 70
    valid_edges = [(a, b, text, bad) for a, b, text, bad in edges if a in positions and b in positions]
    node_names = {n[0]: n[1] for n in nodes}
    legends = [f'{i+1}. {node_names[a]} → {node_names[b]}: {text}' for i, (a, b, text, bad) in enumerate(valid_edges)]
    legend_heights = [len(wrap(t, width - 64, 12)) * 19 + 14 for t in legends]
    height = max(220, top + sum(legend_heights) + 24)
    marker = 'arrow-' + hashlib.sha256((title + repr(nodes)).encode()).hexdigest()[:12]
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title, quote=True)}" style="font-family:Arial,Malgun Gothic,sans-serif">',
        '<rect width="100%" height="100%" rx="16" fill="#f6f9f8"/>',
        f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#7b949a"/></marker></defs>',
        label(title, width / 2, 30, size=16, pixels=width-48)]
    for i, (a, b, text, bad) in enumerate(valid_edges):
        x1, y1, h1 = positions[a]; x2, y2, h2 = positions[b]
        dx, dy = x2-x1, y2-y1
        if not dx and not dy:
            continue  # The legend preserves self-relations without drawing a zero-length arrow.
        def boundary(h):
            return min((box_width/2+4)/abs(dx) if dx else float('inf'), (h/2+4)/abs(dy) if dy else float('inf'))
        t1, t2 = boundary(h1), boundary(h2)
        color = '#c66060' if bad else '#63888d'
        dash = ' stroke-dasharray="5 4"' if bad else ''
        body.append(f'<path d="M{x1+dx*t1},{y1+dy*t1} L{x2-dx*t2},{y2-dy*t2}" fill="none" stroke="{color}" stroke-width="2"{dash} marker-end="url(#{marker})"/>')
        body.append(f'<circle cx="{(x1+x2)/2}" cy="{(y1+y2)/2}" r="12" fill="white" stroke="{color}"/>')
        body.append(label(i+1, (x1+x2)/2, (y1+y2)/2+4, size=11))
    for key, text, tone in nodes:
        x, y, h = positions[key]
        fill = {'bad':'#fbe8e7', 'good':'#d9efea', 'field':'#e0e8f7'}.get(tone, '#fff')
        body.append(f'<g class="diagram-node"><title>{escape(str(text))}</title><rect x="{x-box_width/2}" y="{y-h/2}" width="{box_width}" height="{h}" rx="12" fill="{fill}" stroke="#cadbd7"/>')
        body.append(label(text, x, y-h/2+29, pixels=box_width-36, size=size) + '</g>')
    for i, (text, h) in enumerate(zip(legends, legend_heights)):
        body.append(label(text, 32, top, size=12, pixels=width-64, anchor='start')); top += h
    return ''.join(body) + '</svg>'

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
