"""Portable SVG diagrams with text-aware layout and complete relationship legends."""
from html import escape
import math
import hashlib
import unicodedata
import re

TERM_COLORS = {'개선':'#1764b5', '유익':'#1764b5', '악화':'#bd343b', '유해':'#bd343b',
               '적정':'#1764b5', '부족':'#111111', '과잉':'#bd343b'}


def rich_text(text):
    text = str(text)
    color = TERM_COLORS.get(text.strip())
    return f'<tspan fill="{color}" font-weight="700">{escape(text)}</tspan>' if color else escape(text)

def wrap(value, pixels, size=13):
    """Conservative glyph widths for Korean, Latin and unbroken identifiers."""
    lines = []
    for paragraph in str(value).split("\n"):
        line, used = "", 0
        for char in paragraph:
            advance = 0 if unicodedata.combining(char) else size * (1.05 if unicodedata.east_asian_width(char) in "WF" else .72)
            if line and used + advance > pixels:
                split = line.rfind(' ')
                if split > 0 and line[split+1:]:
                    lines.append(line[:split+1]); line = line[split+1:]
                    used = sum(0 if unicodedata.combining(c) else size * (1.05 if unicodedata.east_asian_width(c) in 'WF' else .72) for c in line)
                else:
                    lines.append(line); line, used = "", 0
            line += char; used += advance
        lines.append(line)
    return lines or [""]

def label(value, x, y, width=18, color="#273b43", size=13, pixels=None, anchor="middle", emphasize=False):
    emphasize = emphasize and str(value).strip() in TERM_COLORS
    chunks = wrap(value, pixels or width * size, size)
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-size="{size}">' + "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.55}">{rich_text(line) if emphasize else escape(line)}</tspan>' for i, line in enumerate(chunks)) + '</text>'

def _route(a, b, positions, rows, row_bounds, gutters, gap, lane, half_width=126, column_step=340):
    """Use the empty row corridors and column gutters, never a node interior."""
    x1, y1, h1 = positions[a]; x2, y2, h2 = positions[b]
    r1, r2 = rows[a], rows[b]
    offset = (lane % 5 - 2) * 8
    if a == b:
        right = x1 + half_width + 4
        outside = min((x for x in gutters if x > right), default=gutters[-1])
        above = row_bounds[r1][0] - gap / 2 + offset
        points = [(right,y1), (outside,y1), (outside,above), (x1,above), (x1,y1-h1/2-4)]
    elif r1 == r2 and abs(x2-x1) <= column_step:
        direction = 1 if x2 > x1 else -1
        points = [(x1+direction*(half_width+4),y1+offset), (x2-direction*(half_width+4),y2+offset)]
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


def svg(title, nodes, edges=(), columns=3, *, divided=False, circles=False, show_edge_legend=True, guide_kind=None):
    from . import report_diagram_style as guide
    # Report diagrams reuse Introduction cards and layouts, with the original
    # node/edge tuples intact. Legacy callers may still request the plain theme.
    if guide_kind:
        circles = False
    if circles:
        columns = min(4, len(nodes) or 1)
    columns = max(1, min(columns, len(nodes) or 1))
    if guide_kind:
        columns, cells = guide.cells_for(guide_kind, nodes, edges, columns)
    else:
        cells = {n[0]:(i//columns,i%columns) for i,n in enumerate(nodes)}
    column_step = 240 if circles else 340
    width, box_width, size = columns * column_step + 64, 180 if circles else 252, 14 if circles else 13
    gap = 80 if guide_kind else 70 if circles else 100
    header_height = len(wrap(title, width - 48, 16)) * 25 + 35
    heights = [180 if circles else max(72 if guide_kind else 90, len(wrap(n[1], box_width - 36, size)) * size * 1.55 + 42 + (16 if divided else 0)) for n in nodes]
    positions, rows, row_bounds, top = {}, {}, {}, header_height + (50 if guide_kind else gap)
    for row in sorted({r for r,c in cells.values()}):
        indices = [i for i,n in enumerate(nodes) if cells[n[0]][0] == row]
        row_height = max(heights[i] for i in indices)
        for i in indices:
            positions[nodes[i][0]] = (32 + column_step * (cells[nodes[i][0]][1] + .5), top + row_height / 2, row_height)
            rows[nodes[i][0]] = row
        row_bounds[row] = (top, top + row_height)
        top += row_height + gap
    gutters = [32 + i * column_step for i in range(columns + 1)]
    valid_edges = [(a, b, text, bad) for a, b, text, bad in edges if a in positions and b in positions]
    node_names = {n[0]: n[1].replace('\n', ' · ') for n in nodes}
    legends = [f'{i+1}. {node_names[a]} → {node_names[b]}: {text}' for i, (a, b, text, bad) in enumerate(valid_edges)] if show_edge_legend else []
    legend_heights = [len(wrap(t, width - 64, 12)) * 19 + 14 for t in legends]
    if guide_kind: top = top-gap+48
    height = max(220, top + sum(legend_heights) + (30 if guide_kind else 24 if show_edge_legend else 36-gap))
    marker = 'arrow-' + hashlib.sha256((title + repr(nodes)).encode()).hexdigest()[:12]
    theme = f' data-template="introduction" data-guide-kind="{escape(guide_kind,quote=True)}"' if guide_kind else ''
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title, quote=True)}"{theme} style="font-family:Arial,Malgun Gothic,sans-serif">',
        f'<rect width="100%" height="100%" rx="16" fill="{guide.BACKGROUND if guide_kind else "#f6f9f8"}"/>',
        f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#7b949a"/></marker></defs>',
        label(title, width / 2, 30, size=16, pixels=width-48, color=guide.INK if guide_kind else '#273b43')]
    if guide_kind == 'separation' and len(row_bounds):
        body.append(f'<path d="M{width/2},{header_height+35} V{top-35}" fill="none" stroke="#bac8af" stroke-dasharray="3 5"/>')
        for row in list(row_bounds)[1:]:
            y = row_bounds[row][0]-gap/2
            body.append(f'<path d="M48,{y} H{width-48}" fill="none" stroke="#bac8af" stroke-dasharray="3 5"/>')
    badges = []
    for i, (a, b, text, bad) in enumerate(valid_edges):
        points = guide.direct_path(a,b,positions,box_width) if guide_kind in ('contradiction','physical-contradiction','sufield','ceca','ariz') else None
        points = points or _route(a, b, positions, rows, row_bounds, gutters, gap, i, box_width/2, column_step)
        negative = bad or any(word in str(text) for word in ('유해', '악화'))
        positive = any(word in str(text) for word in ('유익', '개선'))
        color = '#bd343b' if negative else '#1764b5' if positive else '#63888d'
        if guide_kind:
            color = guide.HARMFUL if negative else guide.USEFUL if positive else guide.ARROW
        edge_marker = marker + '-' + str(i)
        body.append(f'<defs><marker id="{edge_marker}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="{color}"/></marker></defs>')
        dash = ' stroke-dasharray="5 4"' if bad else ''
        path = 'M' + ' L'.join(f'{x},{y}' for x,y in points)
        body.append(f'<path class="diagram-edge" data-source="{escape(str(a),quote=True)}" data-target="{escape(str(b),quote=True)}" data-label="{escape(str(text),quote=True)}" data-harmful="{str(bool(bad)).lower()}" d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"{dash} marker-end="url(#{edge_marker})"/>')
        start, end = max(zip(points, points[1:]), key=lambda pair: abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
        lx, ly = (start[0]+end[0])/2, (start[1]+end[1])/2
        badges.append(f'<circle class="diagram-edge-label" cx="{lx}" cy="{ly}" r="12" fill="white" stroke="{color}"/>' + label(i+1, lx, ly+4, size=11))
    for key, text, tone in nodes:
        x, y, h = positions[key]
        fill = {'bad':'#fbe8e7', 'good':'#e6f0fd', 'field':'#e0e8f7', 'changed':'#fff0d5', 'added':'#eae1f9'}.get(tone, '#fff')
        if guide_kind: fill = guide.fill_for(tone,guide_kind)
        stroke = guide.STROKE if guide_kind else '#cadbd7'
        body.append(f'<g class="diagram-node" data-node="{escape(str(key),quote=True)}" data-tone="{escape(str(tone),quote=True)}"><title>{escape(str(text))}</title>')
        if circles:
            body.append(f'<circle cx="{x}" cy="{y}" r="{box_width/2}" fill="{fill}" stroke="#cadbd7"/>')
        else:
            body.append(f'<rect x="{x-box_width/2}" y="{y-h/2}" width="{box_width}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}"/>')
        pixels, node_size = (120 if circles else box_width-36), size
        while circles and len(wrap(text, pixels, node_size))*node_size*1.55 > 120:
            node_size -= .5
        if divided and '\n' in text:
            first, rest = text.split('\n', 1)
            n1, n2 = len(wrap(first, pixels, node_size)), len(wrap(rest, pixels, node_size))
            total = (n1+n2)*node_size*1.55 + 16
            text_top = y-total/2
            body.append(label(first, x, text_top+node_size, pixels=pixels, size=node_size, color=guide.INK if guide_kind else '#273b43', emphasize=not guide_kind))
            line_y = text_top+n1*node_size*1.55+8
            body.append(f'<line class="diagram-divider" x1="{x-84}" x2="{x+84}" y1="{line_y}" y2="{line_y}" stroke="#9eb8c5" stroke-width="1"/>')
            body.append(label(rest, x, line_y+8+node_size, pixels=pixels, size=node_size, color=guide.INK if guide_kind else '#273b43', emphasize=not guide_kind))
        else:
            count = len(wrap(text, pixels, node_size))
            body.append(label(text, x, y-(count-1)*node_size*1.55/2+node_size*.35, pixels=pixels, size=node_size, color=guide.INK if guide_kind else '#273b43', emphasize=not guide_kind))
        body.append('</g>')
    # Paint every opaque badge after every path, so later arrows cannot cross a number.
    body.extend(badges)
    for i, (text, h) in enumerate(zip(legends, legend_heights)):
        body.append(label(text, 32, top, size=12, pixels=width-64, anchor='start')); top += h
    return ''.join(body) + '</svg>'

def standard_model(state, app):
    from .su_field_model import application_model
    return application_model(state,app)


def figures(state):
    # Resolve references before wrapping text; split SVG spans cannot be matched
    # safely by a string replacement after layout.
    from .report_style import report_state
    state = report_state(state)
    out = []
    def add(key, title, nodes, edges=(), columns=3, **options):
        if nodes:
            from .report_diagram_style import kind_for
            out.append({"key": key, "title": title, "compact": options.get('circles', False), "svg": svg(title, nodes, edges, columns, guide_kind=kind_for(key), **options)})
    a, d = state.analysis, state.definition
    if a.nine_windows:
        rows = [("SUPER", "상위 시스템"), ("SYS", "대상 시스템"), ("SUB", "하위 시스템")]
        times = [("PAST", "과거"), ("PRESENT", "현재"), ("FUTURE", "미래")]
        add("nine-windows", "시스템의 시간과 공간 · 9 Windows", [
            (f"{level}_{time}", f"{name} · {when}\n{a.nine_windows.cells.get(f'{level}_{time}', '미분석')}", "good" if time == "PRESENT" else "")
            for level, name in rows for time, when in times])
    names = list(dict.fromkeys([c.name for c in a.components] + [e.subject for e in a.function_edges] + [e.object for e in a.function_edges]))
    add("functions", "기능 모델 · 점선은 유해 작용", [(n, n, "") for n in names],
        [(e.subject, e.object, e.action + (' · 유해' if e.kind == 'HARMFUL' else ' · 유익') + ' · ' + {'NORMAL':'적정','INSUFFICIENT':'부족','EXCESSIVE':'과잉'}[e.level], e.kind == "HARMFUL") for e in a.function_edges], 4)
    for i, su in enumerate(a.su_fields):
        ns = [("F", "F · " + (su.field or "미확인 장"), "field"),
              ("S2", "S2 · " + (su.s2 or "미확인 도구"), ""),
              ("S1", "S1 · " + (su.s1 or "미확인 대상"), "bad" if su.effect == "HARMFUL" else "good")]
        edges = [("F", "S2", "에너지·작용", False), ("S2", "S1", "유해 작용" if su.effect == "HARMFUL" else "상호작용", su.effect == "HARMFUL")]
        if su.s3:
            ns.append(("S3", "S3 · " + su.s3, "good"))
        add(f"sufield-{i}", "물질–장 · " + (su.label or "상호작용"), ns, edges, 3, circles=True)
    if a.ceca:
        add("ceca", "원인과 결과 · 인과사슬", [(n.id, n.text, "bad" if n.node_type == "ROOT_CAUSE" else "") for n in a.ceca.nodes],
            [(p, n.id, n.logic if n.logic != "NONE" else "원인 탐색", False) for n in a.ceca.nodes for p in n.parents], 3)
    add("resources", "사용 가능한 시스템 자원", [(str(i), r.name + "\n" + ", ".join(r.usable_for), "bad" if r.blocked_by_constraint else "good") for i, r in enumerate(a.resources)], divided=True)
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
    add("trimming", "기능을 옮기는 트리밍", [(str(i), t.target_component + " → " + t.replacement_carrier + "\n" + t.replaced_function, "good") for i, t in enumerate(d.trimming)], divided=True)
    from .knowledge import param_name, principle_name
    from .report_groups import matrix_groups, separation_groups
    for group in matrix_groups(state)[0]:
        lookup = group['lookup']
        add(group['key'], group['title'] + '에 대한 모순행렬 결과 조회', [("pair", param_name(lookup.improving_param_id) + " 개선 / " + param_name(lookup.worsening_param_id) + " 악화", "field")] +
            [(str(pid), principle_name(pid), "good") for pid in lookup.principle_ids],
            [("pair", str(pid), "추천 원리", False) for pid in lookup.principle_ids])
    for group in separation_groups(state):
        add(group['key'], group['title'] + ' · 분리원리 적용',
            [(str(i), str(item.get('title') or item.get('how') or item.get('not_applicable_reason') or '적용 내용 미기재'), 'good' if item.get('applicable') else 'bad') for i, item in enumerate(group['apps'])])
    for i, app in enumerate(state.solve.standard_apps):
        from .knowledge import standards
        from .standard_diagrams import render_standard
        source = next((s for s in standards() if s['code']==app.get('standard_code')),None)
        if app.get('resulting_su_field') or app.get('resulting_model'):
            from .standard_application_diagrams import render_application
            out.append(dict(key=f'standard-{i}',**render_application(state,app,source)))
        elif source:
            out.append(dict(key=f'standard-{i}',title=f"{source['code']} {source['title_ko']} · 표준해 개념 구조",
                compact=True,svg=render_standard(source),
                note='구체적인 적용 구조가 저장되지 않아 표준해의 기본 구성만 표시합니다.'))
    add('fos', '타산업 기능 이식', [(str(i), str(item.get('leading_area') or '산업 미확인') + '\n' +
        str(item.get('transferred_feature') or item.get('idea') or item.get('title') or '적용 내용 보완 필요'), 'good')
        for i,item in enumerate(state.solve.fos_apps)], divided=True)
    trends = ordered_trends(state.solve.trend_apps)
    add('trends', '시스템 진화 방향', [(str(i), str(item.get('trend_id') or '') + ' · ' +
        str(item.get('trend_name') or '') + '\n' + str(item.get('idea') or item.get('next_stage') or ''), 'field')
        for i,item in enumerate(trends)], [(str(i),str(i+1),'TR 순서',False) for i in range(len(trends)-1)], divided=True, show_edge_legend=False)
    if trends and state.scratch.get('s_curve'):
        out.append(dict(key='s-curve', title='기술 성숙도 · S-커브', svg=s_curve_plot(state.scratch['s_curve']),
            compact=True, note='분석된 성장 단계의 위치를 표시한 개념도이며, 실측 성능이나 예측 수치가 아니다.'))
    from .ariz_report import diagrams as ariz_diagrams
    for diagram in ariz_diagrams(state):
        add(diagram['key'], diagram['title'], diagram['nodes'], diagram['edges'], 3)
        out[-1]['compact'] = True
    for i, c in enumerate(state.concepts):
        add(f"concept-{i}", c.title, [("goal", c.one_liner, "field")] +
            [(str(j), change, "good") for j, change in enumerate(c.changes_to_system)], [], 3)
    from .render import quadrant_points
    points = quadrant_points(state)
    if points:
        out.append(dict(key='quadrant', title='리스크 대비 기대효과', svg=quadrant_plot(points), compact=True))
    return out


def ordered_trends(apps):
    def key(app):
        numbers=re.findall(r'\d+',str(app.get('trend_id','')))
        return tuple(map(int,numbers)) if numbers else (9999,)
    return sorted(apps,key=key)


def s_curve_plot(data):
    stage=str(data.get('stage') or '')
    aliases={'EMERGENCE':'태동기','GROWTH':'성장기','MATURITY':'성숙기','DECLINE':'쇠퇴기'}
    stage=aliases.get(stage.upper(),stage)
    stages=['태동기','성장기','성숙기','쇠퇴기']
    selected=next((s for s in stages if s in stage),None)
    curve_y=lambda x:225-150/(1+math.exp(-(x-285)/40))
    points={name:(x,curve_y(x)) for name,x in zip(stages,[140,290,440,590])}
    curve_path='M'+' L'.join(f'{x},{curve_y(x):.2f}' for x in range(65,666,5))
    body=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 310" role="img" aria-label="기술 성숙도 S-커브 개념도" data-template="introduction" data-guide-kind="curve" style="font-family:Arial,Malgun Gothic,sans-serif">',
          '<rect width="720" height="310" rx="16" fill="#f4f7ed"/>']
    for i,name in enumerate(stages):
        x=65+i*150
        body.append(f'<rect x="{x}" y="50" width="150" height="190" fill="{"#e1ebc8" if name==selected else "#ffffff"}"/>')
        body.append(label(name,x+75,268,size=13))
    body+=['<path d="M65,45 V240 H670" fill="none" stroke="#a7b7a1" stroke-width="1.5"/>',
           f'<path d="{curve_path}" fill="none" stroke="#43684f" stroke-width="3.5" stroke-linecap="round"/>',
           label('기술 성능·성숙도',125,29,size=12),label('시간 / 기술 발전',603,295,size=12)]
    if selected:
        x,y=points[selected]
        body.append(f'<path d="M{x},{y} V240" stroke="#507658" stroke-dasharray="4 4"/>')
        body.append(label('현재 · '+selected,x,y-17,size=12))
    else:body.append(label('현재 단계 미확인',360,29,size=12))
    body.append('</svg>')
    return ''.join(body)


def quadrant_plot(points):
    """Introduction's quadrant design with the unchanged evaluation coordinates."""
    legend_lines = [wrap(f'{i+1}. {p["title"]}', 650, 14) for i,p in enumerate(points)]
    height = 495 + sum(len(lines)*23+12 for lines in legend_lines)
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" role="img" aria-label="리스크 대비 기대효과" data-template="introduction" data-guide-kind="quadrant" style="font-family:Arial,Malgun Gothic,sans-serif">',
            '<rect width="100%" height="100%" rx="16" fill="#f4f7ed"/>',
            label('리스크 대비 기대효과',380,32,size=17,color='#284c42'),
            '<rect x="90" y="95" width="580" height="290" rx="12" fill="#fff" stroke="#ccd8c5"/>',
            '<path d="M102,95 H380 V240 H90 V107 Q90,95 102,95" fill="#e1ebc8"/>',
            '<path d="M380,95 V385 M90,240 H670" stroke="#aabca0" stroke-dasharray="4 4"/>',
            label('높은 효과',90,72,size=12,anchor='start'),
            label('낮은 효과',90,410,size=12,anchor='start'),
            label('낮은 리스크',90,445,size=12,anchor='start'),
            label('높은 리스크',670,445,size=12,anchor='end')]
    for text,x,y in [('즉시 실행',235,125),('전략 투자',525,125),('보완 과제',235,367),('보류',525,367)]:
        body.append(label(text,x,y,size=13,color='#657a68'))
    # Coincident scores remain coincident; only their label is combined.
    groups = {}
    for i,p in enumerate(points):
        x,y = 90+p['x']*580,385-p['y']*290
        groups.setdefault((x,y),[]).append(str(i+1))
        body.append(f'<circle class="evaluation-point" data-concept="{escape(p["id"],quote=True)}" data-x="{p["x"]}" data-y="{p["y"]}" cx="{x}" cy="{y}" r="6" fill="#31594b" stroke="white" stroke-width="2"><title>{escape(p["title"])}</title></circle>')
    for (x,y),numbers in groups.items():
        body.append(label(', '.join(numbers),x+10 if x<630 else x-10,y-11,size=12,
                          anchor='start' if x<630 else 'end',pixels=150,color='#284c42'))
    top = 480
    for lines in legend_lines:
        for line in lines:
            body.append(label(line,54,top,size=14,pixels=650,anchor='start',color='#284c42'))
            top += 23
        top += 12
    return ''.join(body)+'</svg>'
