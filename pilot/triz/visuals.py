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

def _route(a, b, positions, rows, row_bounds, gutters, gap, lane):
    """Use the empty row corridors and column gutters, never a node interior."""
    x1, y1, h1 = positions[a]; x2, y2, h2 = positions[b]
    r1, r2 = rows[a], rows[b]
    offset = (lane % 5 - 2) * 8
    if a == b:
        right = x1 + 130
        outside = min((x for x in gutters if x > right), default=gutters[-1])
        above = row_bounds[r1][0] - gap / 2 + offset
        points = [(right,y1), (outside,y1), (outside,above), (x1,above), (x1,y1-h1/2-4)]
    elif r1 == r2 and abs(x2-x1) <= 340:
        direction = 1 if x2 > x1 else -1
        points = [(x1+direction*130,y1+offset), (x2-direction*130,y2+offset)]
    elif r1 == r2:
        above = row_bounds[r1][0] - gap / 2 + offset
        points = [(x1+offset,y1-h1/2-4), (x1+offset,above), (x2+offset,above), (x2+offset,y2-h2/2-4)]
    else:
        direction = 1 if r2 > r1 else -1
        source_y = (row_bounds[r1][1] + gap/2 if direction > 0 else row_bounds[r1][0] - gap/2) + offset
        target_y = (row_bounds[r2][0] - gap/2 if direction > 0 else row_bounds[r2][1] + gap/2) + offset
        gutter = min(gutters, key=lambda x: abs(x-x1)+abs(x-x2)) + offset
        points = [(x1+offset,y1+direction*(h1/2+4)), (x1+offset,source_y),
                  (gutter,source_y), (gutter,target_y), (x2+offset,target_y), (x2+offset,y2-direction*(h2/2+4))]
    simplified = []
    for point in points:
        if simplified and point == simplified[-1]: continue
        while len(simplified) >= 2 and ((simplified[-2][0] == simplified[-1][0] == point[0]) or (simplified[-2][1] == simplified[-1][1] == point[1])):
            simplified.pop()
        simplified.append(point)
    return simplified


def svg(title, nodes, edges=(), columns=3):
    columns = max(1, min(columns, len(nodes) or 1))
    width, box_width, size = columns * 340 + 64, 252, 13
    gap = 100
    header_height = len(wrap(title, width - 48, 16)) * 25 + 35
    heights = [max(90, len(wrap(n[1], box_width - 36, size)) * size * 1.55 + 42) for n in nodes]
    positions, rows, row_bounds, top = {}, {}, {}, header_height + gap
    for row in range(math.ceil(len(nodes) / columns)):
        indices = range(row * columns, min(len(nodes), (row + 1) * columns))
        row_height = max(heights[i] for i in indices)
        for i in indices:
            positions[nodes[i][0]] = (32 + 340 * (i % columns + .5), top + row_height / 2, row_height)
            rows[nodes[i][0]] = row
        row_bounds[row] = (top, top + row_height)
        top += row_height + gap
    gutters = [32 + i * 340 for i in range(columns + 1)]
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
        points = _route(a, b, positions, rows, row_bounds, gutters, gap, i)
        color = '#c66060' if bad else '#63888d'
        dash = ' stroke-dasharray="5 4"' if bad else ''
        path = 'M' + ' L'.join(f'{x},{y}' for x,y in points)
        body.append(f'<path class="diagram-edge" d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"{dash} marker-end="url(#{marker})"/>')
        start, end = max(zip(points, points[1:]), key=lambda pair: abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
        lx, ly = (start[0]+end[0])/2, (start[1]+end[1])/2
        body.append(f'<circle class="diagram-edge-label" cx="{lx}" cy="{ly}" r="12" fill="white" stroke="{color}"/>')
        body.append(label(i+1, lx, ly+4, size=11))
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
