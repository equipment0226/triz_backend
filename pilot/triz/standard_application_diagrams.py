"""One report figure: library artwork, saved application graph, no invented edges."""
from hashlib import sha256
from html import escape

from .standard_diagrams import glyph
from .standard_diagram_specs import specifications
from .su_field_model import application_model, check_model
from .visuals import label, wrap


def _panel(graph, phase, top, marker):
    nodes, edges = graph['nodes'], graph['edges']
    columns = min(4, len(nodes))
    step = 680 / columns
    heading = {'before':'변환 전 · ', 'after':'변환 후 · ', 'unconfirmed':''}[phase] + graph['title']
    heading_height = len(wrap(heading, 680, 17)) * 27
    cursor = top + heading_height + 130
    positions, rows, bounds = {}, {}, {}
    for row in range((len(nodes) + columns - 1) // columns):
        group = nodes[row * columns:(row + 1) * columns]
        text_height = max(len(wrap(n['label'], step - 20, 17)) * 27 for n in group)
        for column, node in enumerate(group):
            positions[node['id']] = (40 + (column + .5) * step, cursor, column)
            rows[node['id']] = row
        bounds[row] = (cursor - 88, cursor + 70 + text_height)
        cursor += 170 + text_height
    legend_top = bounds[max(bounds)][1] + 48
    legends = [f"{i + 1}  {e['source']} → {e['target']} · {e['label']}" for i, e in enumerate(edges)]
    legend_lines = [line for item in legends for line in wrap(item, 664, 15)]
    bottom = legend_top + len(legend_lines) * 25 + 24
    body = [f'<g data-phase="{phase}"><rect x="16" y="{top}" width="728" height="{bottom-top}" rx="18" fill="{"#f4f5ef" if phase=="before" else "#ecf3e1"}" stroke="#d8e2cd"/>',
            label(heading, 37, top + 33, size=17, anchor='start', pixels=680)]
    badges = []
    for i, edge in enumerate(edges):
        a, b = edge['source'], edge['target']
        x1, y1, c1 = positions[a]; x2, y2, c2 = positions[b]
        offset = (i % 5 - 2) * 6
        if a == b:
            outside = x1 + step/2 - 9
            points = [(x1+45,y1),(outside,y1),(outside,y1-63),(x1,y1-63),(x1,y1-44)]
        elif rows[a] == rows[b] and abs(c1-c2) == 1:
            direction = 1 if x2 > x1 else -1
            points = [(x1+direction*45,y1+offset),(x2-direction*45,y2+offset)]
        elif rows[a] == rows[b]:
            lane = y1-64-(i%3)*8
            points = [(x1,y1-44),(x1,lane),(x2,lane),(x2,y2-44)]
        else:
            # Travel in column/row gutters; never through the text under a motif.
            gx1 = 40+(c1+1)*step-5
            gx2 = 40+c2*step+5
            sy = bounds[rows[a]][1]+12+offset
            ty = bounds[rows[b]][0]+offset
            outside = 733-(i%3)*3
            points = [(x1+45,y1),(gx1,y1),(gx1,sy),(outside,sy),
                      (outside,ty),(gx2,ty),(gx2,y2),(x2-45,y2)]
        color = {'harmful':'#b05f51','neutral':'#7c8277'}.get(edge['style'],'#547957')
        dash = ' stroke-dasharray="5 5"' if edge['style']=='harmful' else ''
        d = 'M'+' L'.join(f'{x},{y}' for x,y in points)
        body.append(f'<path class="sis-edge" data-source="{escape(a,quote=True)}" data-target="{escape(b,quote=True)}" data-style="{edge["style"]}" d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"{dash} marker-end="url(#{marker})"/>')
        p, q = max(zip(points,points[1:]), key=lambda pair: abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
        x, y = (p[0]+q[0])/2, (p[1]+q[1])/2
        badges += [f'<circle cx="{x}" cy="{y}" r="11" fill="white" stroke="{color}"/>',label(i+1,x,y+4,size=12,color=color)]
    for node in nodes:
        x,y,_ = positions[node['id']]
        tone = node.get('tone','')
        fill = {'changed':'#fff0d5','added':'#eae1f9'}.get(tone,'white')
        body += [f'<g class="sis-node" data-node="{escape(node["id"],quote=True)}" data-kind="{node["kind"]}" data-tone="{tone}"><title>{escape(node["label"])}</title>',
                 f'<circle cx="{x}" cy="{y}" r="43" fill="{fill}" stroke="#ccd9bd"/>',
                 glyph(node['kind'],x,y),label(node['label'],x,y+69,size=17,pixels=step-20),'</g>']
    body.extend(badges)
    for i,line in enumerate(legend_lines):
        body.append(label(line,43,legend_top+i*25,size=15,anchor='start',pixels=664,color='#61765a'))
    if not edges:
        body.append(label('명시된 작용 연결 없음',43,legend_top,size=14,anchor='start',pixels=664,color='#61765a'))
    body.append('</g>')
    return ''.join(body), bottom


def render_application(state, app, standard=None):
    """Preserve every saved node/edge, including split substances and extra fields.

    Reference motifs only decorate matching roles; reference edges are never
    copied into an application. The canonical transformation remains the caption.
    An ambiguous original model is not silently substituted from another solution.
    """
    from .report_groups import sources
    code = str(app.get('standard_code') or '')
    spec = specifications().get(code)
    canonical = spec['after'] if spec else None
    motifs = {n['id']: n['kind'] for n in canonical['nodes']} if canonical else {}
    ns, es, note = application_model(state, app)
    unconfirmed = '적용 후 구조가 명시되지 않아' in note
    graph = dict(title='적용 구조 확인 필요' if unconfirmed else '해결책의 물질·장과 작용', nodes=[], edges=[])
    for identifier, text, tone in ns:
        motif = motifs.get(identifier)
        # A primed field is a separate node, never merged into its base field.
        if not motif and identifier.endswith('′') and identifier[:-1] not in {n[0] for n in ns}:
            motif = motifs.get(identifier[:-1])
        motif = motif or ('field' if identifier.startswith('F') else 'substance')
        graph['nodes'].append(dict(id=identifier,label=text,kind=motif,tone=tone))
    graph['edges'] = [dict(source=a,target=b,label=text,style='harmful' if bad else 'action') for a,b,text,bad in es]
    model = app.get('resulting_model')
    if model is not None and not check_model(model):
        for edge, saved in zip(graph['edges'], model['edges']):
            if saved.get('kind') == 'neutral':
                edge['style'] = 'neutral'
    originals = [s for s in state.analysis.su_fields if s.id in sources(state,app,'su')]
    panels = []
    if len(originals)==1 and not unconfirmed:
        original = originals[0]
        values = [('F',original.field),('S2',original.s2),('S1',original.s1),('S3',original.s3)]
        nodes = [dict(id=k,label=k+'\n'+v,kind='field' if k=='F' else 'substance') for k,v in values if v]
        ids = {n['id'] for n in nodes}
        edges = []
        if {'F','S2'} <= ids and original.completeness not in ('MISSING_F','MISSING_S2'):
            edges.append(dict(source='F',target='S2',label='에너지·작용',style='action'))
        if {'S2','S1'} <= ids and original.completeness!='MISSING_S2':
            effect = {'HARMFUL':'유해 작용','EXCESSIVE':'과잉 작용','USEFUL_INSUFFICIENT':'부족한 작용','MEASUREMENT':'측정 작용'}.get(original.effect,'유익 작용')
            edges.append(dict(source='S2',target='S1',label=effect,style='harmful' if original.effect in ('HARMFUL','EXCESSIVE') else 'action'))
        if nodes:
            panels.append(('before',dict(title=original.label or '분석된 문제 구조',nodes=nodes,edges=edges)))
    panels.append(('unconfirmed' if unconfirmed else 'after',graph))
    title = f"{code} {standard['title_ko']}" if standard else f'{code} 물질–장 적용'
    marker = 'sia-'+sha256(repr((title,panels)).encode()).hexdigest()[:16]
    body = [f'<defs><marker id="{marker}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>',
            label('STANDARD '+code+' · APPLICATION',30,31,size=13,anchor='start',pixels=700,color='#6a8654'),
            label(title,30,63,size=21,anchor='start',pixels=700)]
    top = 90+(len(wrap(title,700,21))-1)*33
    for i,(phase,panel) in enumerate(panels):
        drawing,bottom = _panel(panel,phase,top,marker)
        body.append(drawing)
        top = bottom+45
        if i<len(panels)-1:
            body.append(f'<path d="M380,{bottom+9} V{top-9}" stroke="#6f8b53" stroke-width="2" marker-end="url(#{marker})"/>')
    principle = '적용 원리 · '+spec['note'] if spec else '표준해 번호와 적용 원리 확인 필요'
    body.append(label(principle,32,top-5,size=16,anchor='start',pixels=690,color='#647b55'))
    height = top+len(wrap(principle,690,16))*25+12
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" role="img" aria-label="{escape(title,quote=True)} 적용 구조도" data-standard-code="{escape(code,quote=True)}" data-diagram="standard-application" style="font-family:Arial,Malgun Gothic,sans-serif"><title>{escape(title)} · 실제 적용 변환</title><rect width="100%" height="100%" rx="20" fill="#fcfdf8"/>'+''.join(body)+'</svg>'
    return dict(title=title+' · 물질–장 적용',svg=svg,compact=True,note=note)
