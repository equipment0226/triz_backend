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


def svg(title, nodes, edges=(), columns=3, *, divided=False, circles=False, show_edge_legend=True):
    if circles:
        columns = min(4, len(nodes) or 1)
    columns = max(1, min(columns, len(nodes) or 1))
    column_step = 240 if circles else 340
    width, box_width, size = columns * column_step + 64, 180 if circles else 252, 14 if circles else 13
    gap = 70 if circles else 100
    header_height = len(wrap(title, width - 48, 16)) * 25 + 35
    heights = [180 if circles else max(90, len(wrap(n[1], box_width - 36, size)) * size * 1.55 + 42 + (16 if divided else 0)) for n in nodes]
    positions, rows, row_bounds, top = {}, {}, {}, header_height + gap
    for row in range(math.ceil(len(nodes) / columns)):
        indices = range(row * columns, min(len(nodes), (row + 1) * columns))
        row_height = max(heights[i] for i in indices)
        for i in indices:
            positions[nodes[i][0]] = (32 + column_step * (i % columns + .5), top + row_height / 2, row_height)
            rows[nodes[i][0]] = row
        row_bounds[row] = (top, top + row_height)
        top += row_height + gap
    gutters = [32 + i * column_step for i in range(columns + 1)]
    valid_edges = [(a, b, text, bad) for a, b, text, bad in edges if a in positions and b in positions]
    node_names = {n[0]: n[1].replace('\n', ' · ') for n in nodes}
    legends = [f'{i+1}. {node_names[a]} → {node_names[b]}: {text}' for i, (a, b, text, bad) in enumerate(valid_edges)] if show_edge_legend else []
    legend_heights = [len(wrap(t, width - 64, 12)) * 19 + 14 for t in legends]
    height = max(220, top + sum(legend_heights) + (24 if show_edge_legend else 36 - gap))
    marker = 'arrow-' + hashlib.sha256((title + repr(nodes)).encode()).hexdigest()[:12]
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title, quote=True)}" style="font-family:Arial,Malgun Gothic,sans-serif">',
        '<rect width="100%" height="100%" rx="16" fill="#f6f9f8"/>',
        f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#7b949a"/></marker></defs>',
        label(title, width / 2, 30, size=16, pixels=width-48)]
    badges = []
    for i, (a, b, text, bad) in enumerate(valid_edges):
        points = _route(a, b, positions, rows, row_bounds, gutters, gap, i, box_width/2, column_step)
        negative = bad or any(word in str(text) for word in ('유해', '악화'))
        positive = any(word in str(text) for word in ('유익', '개선'))
        color = '#bd343b' if negative else '#1764b5' if positive else '#63888d'
        edge_marker = marker + '-' + str(i)
        body.append(f'<defs><marker id="{edge_marker}" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="{color}"/></marker></defs>')
        dash = ' stroke-dasharray="5 4"' if bad else ''
        path = 'M' + ' L'.join(f'{x},{y}' for x,y in points)
        body.append(f'<path class="diagram-edge" d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"{dash} marker-end="url(#{edge_marker})"/>')
        start, end = max(zip(points, points[1:]), key=lambda pair: abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
        lx, ly = (start[0]+end[0])/2, (start[1]+end[1])/2
        badges.append(f'<circle class="diagram-edge-label" cx="{lx}" cy="{ly}" r="12" fill="white" stroke="{color}"/>' + label(i+1, lx, ly+4, size=11))
    for key, text, tone in nodes:
        x, y, h = positions[key]
        fill = {'bad':'#fbe8e7', 'good':'#e6f0fd', 'field':'#e0e8f7', 'changed':'#fff0d5', 'added':'#eae1f9'}.get(tone, '#fff')
        body.append(f'<g class="diagram-node" data-tone="{tone}"><title>{escape(str(text))}</title>')
        if circles:
            body.append(f'<circle cx="{x}" cy="{y}" r="{box_width/2}" fill="{fill}" stroke="#cadbd7"/>')
        else:
            body.append(f'<rect x="{x-box_width/2}" y="{y-h/2}" width="{box_width}" height="{h}" rx="12" fill="{fill}" stroke="#cadbd7"/>')
        pixels, node_size = (120 if circles else box_width-36), size
        while circles and len(wrap(text, pixels, node_size))*node_size*1.55 > 120:
            node_size -= .5
        if divided and '\n' in text:
            first, rest = text.split('\n', 1)
            n1, n2 = len(wrap(first, pixels, node_size)), len(wrap(rest, pixels, node_size))
            total = (n1+n2)*node_size*1.55 + 16
            top = y-total/2
            body.append(label(first, x, top+node_size, pixels=pixels, size=node_size, emphasize=True))
            line_y = top+n1*node_size*1.55+8
            body.append(f'<line class="diagram-divider" x1="{x-84}" x2="{x+84}" y1="{line_y}" y2="{line_y}" stroke="#9eb8c5" stroke-width="1"/>')
            body.append(label(rest, x, line_y+8+node_size, pixels=pixels, size=node_size, emphasize=True))
        else:
            count = len(wrap(text, pixels, node_size))
            body.append(label(text, x, y-(count-1)*node_size*1.55/2+node_size*.35, pixels=pixels, size=node_size, emphasize=True))
        body.append('</g>')
    # Paint every opaque badge after every path, so later arrows cannot cross a number.
    body.extend(badges)
    for i, (text, h) in enumerate(zip(legends, legend_heights)):
        body.append(label(text, 32, top, size=12, pixels=width-64, anchor='start')); top += h
    return ''.join(body) + '</svg>'

def standard_model(state, app):
    """Read stated substances/fields and arrows; '+' alone does not imply a link."""
    from .report_groups import sources
    source_ids = sources(state, app, 'su')
    originals = [s for s in state.analysis.su_fields if s.id in source_ids]
    original = originals[0] if len(originals) == 1 else None
    base = {'S1':original.s1, 'S2':original.s2, 'S3':original.s3, 'F':original.field} if original else {}
    raw = str(app.get('resulting_su_field') or '')
    pattern = re.compile(r"(?<![A-Za-z0-9])(S[1-9]|F\d*)([′'’*]?)(?![A-Za-z0-9])")
    items = []
    position = 0
    while match := pattern.search(raw, position):
        key, prime = match.groups()
        end = match.end()
        after = end
        while after < len(raw) and raw[after].isspace(): after += 1
        description = ''
        if after < len(raw) and raw[after] in '(（':
            depth, end = 1, after+1
            while end < len(raw) and depth:
                if raw[end] in '(（': depth += 1
                elif raw[end] in ')）': depth -= 1
                end += 1
            description = raw[after+1:end-1] if depth == 0 else raw[after+1:end]
        items.append(dict(key=key, prime=prime, description=description.strip(), start=match.start(), end=end))
        position = end
    substances = [x for x in items if x['key'].startswith('S')]
    fields = [x for x in items if x['key'].startswith('F')]
    if not substances:
        substances = [dict(key=k, prime='', description=v, start=0, end=0) for k, v in base.items() if k.startswith('S') and v]
    if not fields and base.get('F'):
        fields = [dict(key='F', prime='', description=base['F'], start=0, end=0)]
    nodes = {}
    for item in fields + substances:
        key = item['key']
        text = item['description'] or base.get(key) or '상세 명칭 미기재'
        tone = 'field' if key.startswith('F') else ''
        if item['prime'] or (base.get(key) and text != base[key]): tone = 'changed'
        elif original and not base.get(key): tone = 'added'
        nodes[key] = (key, key + item['prime'] + '\n' + text, tone)
    edges = []
    for a, b in zip(substances, substances[1:]):
        between = raw[a['end']:b['start']]
        if re.search(r'[-=]+\s*>|→|⇒|⟶', between) and a['key'] != b['key']:
            field = next((f for f in fields if a['end'] <= f['start'] < b['start']), None)
            edge_label = (field['key'] + field['prime'] + ' · ' + (field['description'] or base.get(field['key'], '작용'))) if field else '작용 전달'
            edges.append((a['key'], b['key'], edge_label, False))
            if field:
                edges.append((field['key'], b['key'], '작용장', False))
    note = '주황: 변경된 물질·장 · 보라: 추가된 물질·장. 명시된 화살표만 연결하며 +로만 추가된 요소의 연결은 추정하지 않는다.'
    if not original:
        note += ' 원본 물질–장 모델 연결 미확인: 변경 비교에 한계가 있다.'
    if not nodes:
        nodes['unknown'] = ('unknown', '변환 모델의 물질·장\n구조 정보 확인 필요', '')
    return list(nodes.values()), edges, note


def figures(state):
    out = []
    def add(key, title, nodes, edges=(), columns=3, **options):
        if nodes:
            out.append({"key": key, "title": title, "compact": options.get('circles', False), "svg": svg(title, nodes, edges, columns, **options)})
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
        ns, es, note = standard_model(state, app)
        title = f"{app.get('standard_code', '')} {app.get('standard_title') or app.get('title') or '표준해'} · 변환 모델"
        add(f'standard-{i}', title, ns, es, 3, circles=True)
        if out and out[-1]['key'] == f'standard-{i}':
            out[-1]['note'] = note
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
    body=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 310" role="img" aria-label="기술 성숙도 S-커브 개념도" style="font-family:Arial,Malgun Gothic,sans-serif">',
          '<rect width="720" height="310" rx="16" fill="#f6f9f8"/>']
    for i,name in enumerate(stages):
        x=65+i*150
        body.append(f'<rect x="{x}" y="50" width="150" height="190" fill="{"#e4ede0" if name==selected else "#f1f5f1"}"/>')
        body.append(label(name,x+75,268,size=13))
    body+=['<path d="M65,45 V240 H670" fill="none" stroke="#889b91" stroke-width="1.5"/>',
           f'<path d="{curve_path}" fill="none" stroke="#537e61" stroke-width="3"/>',
           label('기술 성능·성숙도',125,29,size=12),label('시간 / 기술 발전',603,295,size=12)]
    if selected:
        x,y=points[selected]
        body.append(f'<path d="M{x},{y} V240" stroke="#507658" stroke-dasharray="4 4"/>')
        body.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#244f36" stroke="white" stroke-width="3"/>')
        body.append(label('현재 · '+selected,x,y-17,size=12))
    else:body.append(label('현재 단계 미확인',360,29,size=12))
    body.append('</svg>')
    return ''.join(body)
