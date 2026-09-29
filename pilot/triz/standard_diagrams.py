"""One portable SVG renderer for the public library and report references."""
from html import escape
from copy import deepcopy

from .standard_diagram_specs import specifications
from .standard_detail_specs import detail_specifications
from .visuals import label, wrap

KINDS = {'substance','field','missing','composite','layer','environment','process',
         'pattern','shield','magnet','magnetic','pulse','segmented','particles',
         'hollow','porous','capillary','flexible','gradient','phase','wave','fluid',
         'current','chains','system','sensor','copy','foam','energy','critical'}


def validate_specs(catalog):
    specs = specifications()
    codes = {item['code'] for item in catalog}
    assert set(specs) == codes, f'Diagram/catalog mismatch: {set(specs) ^ codes}'
    for code, spec in specs.items():
        for panel in ('before','after'):
            graph = spec[panel]
            nodes = graph['nodes']
            keys = {n['id'] for n in nodes}
            assert len(keys) == len(nodes) and 1 <= len(nodes) <= 4, code
            assert all(n['kind'] in KINDS and n['label'] for n in nodes), code
            assert all(e['source'] in keys and e['target'] in keys and e['style'] in ('action','harmful','link','both') for e in graph['edges']), code
    return specs


def glyph(kind, x, y):
    """Distinct physical motifs, drawn without remote assets or font icons."""
    stroke = '#4c725e'
    body = []
    rect = lambda a,b,w,h,**kw: f'<rect x="{a}" y="{b}" width="{w}" height="{h}" rx="{kw.get("rx",5)}" fill="{kw.get("fill","none")}" stroke="{stroke}" stroke-width="2"/>'
    path = lambda d: f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
    if kind in ('field','wave','pulse','current','gradient'):
        if kind == 'pulse': body += [path('M-27,5 H-19 V-14 H-6 V12 H7 V-14 H20 V5 H28')]
        elif kind == 'current': body += [path('M-26,2 H-9 L-2,-16 L6,18 L13,2 H28')]
        elif kind == 'gradient':
            body += [path(f'M{a},18 V{-h}') for a,h in [(-24,0),(-12,8),(0,16),(12,24),(24,30)]]
        else:
            body += [path('M-29,0 Q-22,-25 -14,0 T1,0 T16,0 T31,0')]
    elif kind in ('magnet','magnetic'):
        body += [path('M-23,-20 V6 Q-23,29 0,29 Q23,29 23,6 V-20 H9 V6 Q9,14 0,14 Q-9,14 -9,6 V-20 Z'),label('N',-16,-26,size=11),label('S',16,-26,size=11)]
    elif kind in ('particles','porous','foam','chains','fluid','composite'):
        if kind != 'particles': body += [rect(-31,-27,62,54,fill='#f0f5e7',rx=10)]
        if kind == 'fluid': body += [path('M-28,-8 Q-14,-17 0,-8 T28,-8')]
        for i in range(9 if kind in ('chains','particles') else 6):
            a = (i%3-1)*16
            b = (i//3-1)*16 + (8 if kind not in ('chains','particles') else 0)
            if kind == 'chains': a += (i//3-1)*3
            radius = 6 if kind in ('porous','foam') else 3.7
            body.append(f'<circle cx="{a}" cy="{b}" r="{radius}" fill="{"white" if kind in ("porous","foam") else "#809c67"}" stroke="{stroke}" stroke-width="1"/>')
        if kind == 'chains': body += [path(f'M{a-3},-16 L{a+3},16') for a in (-16,0,16)]
    elif kind == 'layer': body += [rect(-26,-23,52,46),path('M-33,-30 H33 V30 H-33 Z')]
    elif kind == 'shield': body += [path('M0,-31 L28,-19 V3 Q22,23 0,32 Q-22,23 -28,3 V-19 Z'),path('M-13,0 L-2,11 L15,-11')]
    elif kind == 'segmented': body += [rect(a,b,21,21,fill='#dce8c7') for a in (-25,4) for b in (-25,4)]
    elif kind == 'hollow': body += [rect(-29,-27,58,54,fill='#dce8c7'),rect(-14,-13,28,26,fill='white')]
    elif kind == 'capillary': body += [rect(-29,-27,58,54),*[path(f'M{a},-25 V25') for a in (-18,-6,6,18)]]
    elif kind == 'flexible':
        body += [path('M-28,19 L-10,-14 L10,14 L28,-19')]
        body += [f'<circle cx="{a}" cy="{b}" r="5" fill="white" stroke="{stroke}" stroke-width="2"/>' for a,b in [(-28,19),(-10,-14),(10,14),(28,-19)]]
    elif kind == 'pattern': body += [rect(-30,-27,60,54),*[rect(a,-24,8,48,fill=f'rgb({150+i*17},190,140)') for i,a in enumerate((-26,-14,-2,10))]]
    elif kind == 'phase': body += [f'<circle cx="0" cy="0" r="29" fill="#dce8c7" stroke="{stroke}" stroke-width="2"/>',path('M0,-29 V29'),path('M4,-5 Q13,-16 27,-5')]
    elif kind == 'environment': body += [path('M-31,17 Q-30,-1 -16,-1 Q-14,-27 6,-17 Q24,-26 29,-4 Q42,11 25,20 H-21'),path('M-6,-2 V13 M-12,7 L-6,14 L0,7')]
    elif kind == 'sensor': body += [rect(-29,-23,58,42),path('M-23,5 L-14,5 L-7,-10 L2,12 L10,-3 L23,-3'),path('M0,20 V29 M-17,30 H17')]
    elif kind == 'copy': body += [rect(-28,-25,43,45),rect(-13,-12,43,45,fill='#edf3df')]
    elif kind == 'energy': body += [rect(-26,-18,47,36),rect(21,-8,6,16),path('M-14,0 H-3 M-8,-6 V6 M6,0 H15')]
    elif kind == 'critical': body += [path('M-28,19 L0,-29 L28,19 Z'),path('M0,-11 V4'),f'<circle cx="0" cy="12" r="2.5" fill="{stroke}"/>']
    elif kind == 'missing': body += [label('?',0,13,size=38,color='#98a294')]
    elif kind == 'system': body += [rect(-30,-24,60,48),rect(-23,-15,18,30,fill='#dce8c7'),rect(4,-15,18,30)]
    elif kind == 'process': body += [path('M-26,0 H21 M8,-13 L22,0 L8,13')]
    else: body += [f'<circle cx="0" cy="0" r="27" fill="#dce8c7" stroke="{stroke}" stroke-width="2"/>']
    return f'<g transform="translate({x},{y})">'+''.join(body)+'</g>'


def _marker(marker):
    return f'<defs><marker id="{marker}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>'


def _graph_panel(graph, title, top, marker, *, attributes='', before=False):
    """Draw an explicit mechanism graph; each long edge gets its own lane."""
    count = len(graph['nodes'])
    indices = {node['id']: i for i, node in enumerate(graph['nodes'])}
    long_edges = [i for i, edge in enumerate(graph['edges'])
                  if abs(indices[edge['source']] - indices[edge['target']]) > 1]
    heading_height = len(wrap(title, 688, 17)) * 27
    node_y = top + heading_height + 100 + len(long_edges) * 22
    positions = {node['id']: (60 + (i + .5) * 640 / count, node_y)
                 for i, node in enumerate(graph['nodes'])}
    node_width = min(178, 640 / count - 12)
    node_lines = max(len(wrap(node['label'], node_width, 17)) for node in graph['nodes'])
    legend_top = node_y + 75 + node_lines * 27
    legend_lines = [line for i, edge in enumerate(graph['edges'])
                    for line in wrap(f"{i + 1}  {edge['label']}", 650, 15)]
    height = legend_top - top + len(legend_lines) * 25 + 16
    fill = '#f4f5ef' if before else '#ecf3e1'
    body = [f'<g {attributes}>', f'<rect x="16" y="{top}" width="728" height="{height}" rx="18" fill="{fill}" stroke="#d8e2cd"/>',
            label(title, 37, top + 33, size=17, anchor='start', pixels=688)]
    for i, edge in enumerate(graph['edges']):
        x1, y1 = positions[edge['source']]
        x2, y2 = positions[edge['target']]
        direction = 1 if x2 > x1 else -1
        if i in long_edges:
            cy = node_y - 91 - long_edges.index(i) * 22
            d = f'M{x1},{y1 - 43} C{x1},{cy} {x2},{cy} {x2},{y2 - 43}'
            lx, ly = (x1 + x2) / 2, (y1 - 43) * .25 + cy * .75
        else:
            d = f'M{x1 + direction * 47},{y1} L{x2 - direction * 47},{y2}'
            lx, ly = (x1 + x2) / 2, y1
        color = '#b05f51' if edge['style'] == 'harmful' else '#547957'
        dash = ' stroke-dasharray="5 5"' if edge['style'] == 'harmful' else ''
        ends = '' if edge['style'] == 'link' else f' marker-end="url(#{marker})"'
        if edge['style'] == 'both':
            ends += f' marker-start="url(#{marker})"'
        body.extend([f'<path class="sis-edge" data-source="{escape(edge["source"], quote=True)}" data-target="{escape(edge["target"], quote=True)}" data-style="{edge["style"]}" d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash}{ends}/>',
                     f'<circle cx="{lx}" cy="{ly}" r="11" fill="white" stroke="{color}"/>',
                     label(i + 1, lx, ly + 4, size=12, color=color)])
    for node in graph['nodes']:
        x, y = positions[node['id']]
        border = ' stroke-dasharray="4 4"' if node['kind'] == 'missing' else ''
        body.extend([f'<g class="sis-node" data-node="{escape(node["id"], quote=True)}" data-kind="{node["kind"]}"><title>{escape(node["label"])}</title>',
                     f'<circle cx="{x}" cy="{y}" r="43" fill="white" stroke="#ccd9bd"{border}/>',
                     glyph(node['kind'], x, y), label(node['label'], x, y + 70, size=17, pixels=node_width), '</g>'])
    for i, line in enumerate(legend_lines):
        body.append(label(line, 43, legend_top + i * 25, size=15, anchor='start', pixels=650, color='#61765a'))
    body.append('</g>')
    return body, top + height


def _paragraph(body, text, top, *, color='#647b55', size=16):
    if not text:
        return top
    body.append(label(text, 32, top, size=size, anchor='start', pixels=690, color=color))
    return top + len(wrap(text, 690, size)) * size * 1.55 + 12


def _svg(body, title, code, height, *, detail_key=None):
    detail_attr = f' data-standard-detail="{escape(detail_key, quote=True)}"' if detail_key else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" role="img" '
            f'aria-label="{escape(title, quote=True)} 개념도" data-standard-code="{escape(code, quote=True)}"{detail_attr} '
            f'style="font-family:Arial,Malgun Gothic,sans-serif"><title>{escape(title)} · 개념도</title>'
            '<rect width="100%" height="100%" rx="20" fill="#fcfdf8"/>' + ''.join(body) + '</svg>')


def render_standard(standard, spec=None):
    code = standard['code']
    spec = spec or specifications()[code]
    assert spec['code'] == code
    marker = 'sis-' + code.replace('.', '-')
    body = [_marker(marker), label('STANDARD ' + code, 30, 31, size=13, anchor='start', color='#6a8654'),
            label(standard['title_ko'], 30, 63, size=21, anchor='start', pixels=700)]
    top = 93 + (len(wrap(standard['title_ko'], 700, 21)) - 1) * 33
    for phase in ('before', 'after'):
        heading = ('변환 전 · ' if phase == 'before' else '변환 후 · ') + spec[phase]['title']
        panel, bottom = _graph_panel(spec[phase], heading, top, marker,
                                     attributes=f'data-standard="{code}" data-phase="{phase}"', before=phase == 'before')
        body.extend(panel)
        top = bottom + 45
        if phase == 'before':
            body.append(f'<path d="M380,{bottom + 9} V{top - 9}" stroke="#6f8b53" stroke-width="2" marker-end="url(#{marker})"/>')
    top = _paragraph(body, spec['note'], top - 6)
    top = _paragraph(body, '변환 원리 · ' + standard.get('transformation', ''), top)
    top = _paragraph(body, '원전 적용 조건 · ' + standard.get('conditions', ''), top)
    top = _paragraph(body, '개념도 · 표준해의 관계를 설명하며 실제 적용·검증 결과가 아닙니다. 분기와 하위 방법은 각 상세 도식에서 확인합니다.', top, size=13)
    return _svg(body, f"{code} {standard['title_ko']}", code, top + 8)


def supplemental_details(standard):
    """Stable metadata for separately rendered official methods and branches.

    Variant keys are stable editorial indexes within this catalog snapshot.
    They intentionally have no ``code`` so they cannot become official numbers.
    """
    details = []
    parent_code = standard['code']
    for sub in standard.get('substandards', []):
        details.append(dict(key='sub-' + sub['code'], kind='substandard', code=sub['code'],
                            parent_code=parent_code, title=sub['title_ko'],
                            transformation=sub.get('transformation', ''), conditions=sub.get('conditions', ''),
                            sources=deepcopy(sub.get('sources', []))))
    for i, variant in enumerate(standard.get('variants', []), 1):
        details.append(dict(key=f'variant-{i}', kind='variant', parent_code=parent_code,
                            title=variant['title_ko'], transformation=variant.get('transformation', ''),
                            conditions=variant.get('conditions', ''), sources=deepcopy(variant.get('sources', []))))
    if standard.get('development_sequence'):
        details.append(dict(key='sequence', kind='sequence', parent_code=parent_code, title='발전·적용 순서',
                            transformation=standard.get('transformation', ''), conditions=standard.get('conditions', ''),
                            sources=deepcopy(standard.get('sources', [])), steps=list(standard['development_sequence'])))
    return details


# Physical motifs for each explicitly reviewed sequence; unknown groups fail
# rather than receiving an invented generic physical interpretation.
SEQUENCE_KINDS = {
    '2.2.3': ['substance', 'hollow', 'porous', 'capillary', 'pattern'],
    '2.2.4': ['flexible', 'flexible', 'flexible'],
    '2.4.2': [['particles', 'particles', 'particles'], ['substance', 'segmented', 'particles', 'fluid']],
    '2.4.11': ['current', 'composite', 'environment', 'pulse', 'pattern', 'wave'],
    '3.1.3': ['system', 'gradient', 'composite', 'system'],
    '3.1.4': ['system', 'segmented', 'substance', 'system'],
    '4.5.2': ['sensor', 'sensor', 'sensor'],
    '5.2.1': ['field', 'environment', 'substance'],
    '5.2.2': ['environment', 'substance'],
    '5.2.3': ['field', 'environment', 'substance'],
    '5.3.5': ['phase', 'phase'],
    '5.4.2': ['energy', 'critical'],
    '5.5.2': ['missing', 'particles'],
}


def _sequence_paths(code, steps):
    if code == '2.4.2':
        # These are two independent development axes, not consecutive stages.
        assert len(steps) == 2
        return [(step.split(':', 1)[0], [part.strip() for part in step.split(':', 1)[1].split('→')])
                for step in steps]
    return [('발전·적용 경로', steps)]


def _sequence(body, code, steps, top, marker):
    paths = _sequence_paths(code, steps)
    kinds = SEQUENCE_KINDS[code]
    for path_index, (path_title, stages) in enumerate(paths):
        motif_kinds = kinds[path_index] if code == '2.4.2' else kinds
        assert len(motif_kinds) == len(stages), f'Unreviewed development sequence: {code}'
        body.append(f'<g data-sequence-path="{path_index + 1}">')
        top = _paragraph(body, path_title, top, size=17)
        for i, (stage, kind) in enumerate(zip(stages, motif_kinds)):
            height = max(98, 30 + len(wrap(stage, 548, 17)) * 27)
            body.extend([f'<g data-sequence-stage="{i + 1}" data-kind="{kind}">',
                         f'<rect x="32" y="{top}" width="696" height="{height}" rx="15" fill="#ecf3e1" stroke="#d8e2cd"/>',
                         glyph(kind, 85, top + height / 2),
                         label(stage, 137, top + 32, size=17, anchor='start', pixels=548), '</g>'])
            top += height
            if i < len(stages) - 1:
                transition = '이 경로로 불가능하면' if code.startswith('5.2.') else '다음 단계'
                body.extend([f'<path class="sequence-edge" data-source-stage="{i + 1}" data-target-stage="{i + 2}" d="M85,{top + 5} V{top + 36}" stroke="#547957" stroke-width="2" fill="none" marker-end="url(#{marker})"/>',
                             label(transition, 117, top + 25, size=13, anchor='start')])
                top += 44
        body.append('</g>')
        top += 35
    return top


def validate_detail_specs(catalog):
    specs = detail_specifications()
    expected = {item['code'] + '--' + detail['key'] for item in catalog
                for detail in supplemental_details(item) if detail['kind'] != 'sequence'}
    assert set(specs) == expected, f'Detail diagram/catalog mismatch: {set(specs) ^ expected}'
    for key, graph in specs.items():
        ids = {node['id'] for node in graph['nodes']}
        assert len(ids) == len(graph['nodes']) and 1 <= len(ids) <= 4, key
        assert all(node['kind'] in KINDS and node['label'] for node in graph['nodes']), key
        assert graph['edges'], key
        assert all(edge['source'] in ids and edge['target'] in ids and
                   edge['style'] in ('action', 'harmful', 'link', 'both') for edge in graph['edges']), key
    sequences = {item['code'] for item in catalog if item.get('development_sequence')}
    assert sequences == set(SEQUENCE_KINDS), f'Unreviewed sequences: {sequences ^ set(SEQUENCE_KINDS)}'
    return specs


def render_standard_detail(standard, detail_key):
    detail = next((item for item in supplemental_details(standard) if item['key'] == detail_key), None)
    if detail is None:
        raise KeyError(f"Unknown standard detail: {standard['code']}--{detail_key}")
    code = standard['code']
    marker = 'sis-detail-' + code.replace('.', '-') + '-' + detail_key.replace('.', '-')
    kind_title = {'substandard': '공식 하위 방법', 'variant': '원전의 대안 분기 · 별도 공식 번호 없음',
                  'sequence': '원전의 발전·적용 순서'}[detail['kind']]
    heading = detail.get('code', code) + ' · ' + detail['title']
    body = [_marker(marker), label(kind_title, 30, 31, size=13, anchor='start', color='#6a8654'),
            label(heading, 30, 63, size=21, anchor='start', pixels=700)]
    top = 93 + (len(wrap(heading, 700, 21)) - 1) * 33
    if detail['kind'] == 'sequence':
        graph = specifications()[code]['after']
        graph_title = '변환 기전 · ' + graph['title']
    else:
        # No guessed fallback for a branch absent from the reviewed graph table.
        graph = detail_specifications()[code + '--' + detail_key]
        graph_title = '변환 기전 · ' + detail['title']
    panel, top = _graph_panel(graph, graph_title, top, marker, attributes='data-detail-mechanism="true"')
    body.extend(panel)
    top += 35
    if detail['kind'] == 'sequence':
        top = _sequence(body, code, detail['steps'], top, marker)
    top = _paragraph(body, '변환 원리 · ' + detail['transformation'], top)
    top = _paragraph(body, '원전 적용 조건 · ' + detail['conditions'], top)
    top = _paragraph(body, '개념도 · 실제 적용·검증 결과가 아닙니다. 화살표의 의미는 각 관계 설명을 따릅니다.', top, size=13)
    return _svg(body, heading, code, top + 8, detail_key=detail_key)
