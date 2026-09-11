"""One portable SVG renderer for the public library and report references."""
from html import escape
import math

from .standard_diagram_specs import specifications
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


def render_standard(standard, spec=None):
    code = standard['code']
    spec = spec or specifications()[code]
    assert spec['code'] == code
    marker = 'sis-' + code.replace('.','-')
    width = 760
    title = f"{code} {standard['title_ko']}"
    body = [f'<defs><marker id="{marker}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>']
    body += [label('STANDARD '+code,30,31,size=13,anchor='start',color='#6a8654'),label(standard['title_ko'],30,63,size=21,anchor='start',pixels=700)]
    top = 90 + (len(wrap(standard['title_ko'],700,21))-1)*32
    for phase in ('before','after'):
        graph = spec[phase]
        node_count = len(graph['nodes'])
        positions = {n['id']:(60+(i+.5)*640/node_count,top+139) for i,n in enumerate(graph['nodes'])}
        lines = [f"{i+1}  {e['label']}" for i,e in enumerate(graph['edges'])]
        legend_lines = [line for item in lines for line in wrap(item,650,15)]
        node_lines = max(len(wrap(n['label'],min(160,640/node_count-12),17)) for n in graph['nodes'])
        legend_top = top + 201 + node_lines*25
        panel_height = legend_top-top + len(legend_lines)*25 + 20
        body += [f'<g data-standard="{code}" data-phase="{phase}">',f'<rect x="16" y="{top}" width="728" height="{panel_height}" rx="18" fill="{"#f4f5ef" if phase=="before" else "#ecf3e1"}" stroke="#d8e2cd"/>',label(('변환 전 · ' if phase=='before' else '변환 후 · ')+graph['title'],37,top+33,size=17,anchor='start',pixels=688)]
        for i,e in enumerate(graph['edges']):
            x1,y1=positions[e['source']]; x2,y2=positions[e['target']]
            direction=1 if x2>x1 else -1
            gap=abs(x2-x1)
            if gap > 640/node_count*1.1:
                sx,ex=x1,x2; sy=ey=y1-43
                cy=y1-91
                d=f'M{sx},{sy} C{sx},{cy} {ex},{cy} {ex},{ey}'
                lx,ly=(sx+ex)/2,cy+10
            else:
                sx,ex=x1+direction*47,x2-direction*47
                sy=ey=y1; d=f'M{sx},{sy} L{ex},{ey}'
                lx,ly=(sx+ex)/2,y1
            color='#b05f51' if e['style']=='harmful' else '#547957'
            dash=' stroke-dasharray="5 5"' if e['style']=='harmful' else ''
            ends='' if e['style']=='link' else f' marker-end="url(#{marker})"'
            if e['style']=='both': ends+=f' marker-start="url(#{marker})"'
            body += [f'<path class="sis-edge" data-source="{e["source"]}" data-target="{e["target"]}" d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash}{ends}/>',f'<circle cx="{lx}" cy="{ly}" r="11" fill="white" stroke="{color}"/>',label(i+1,lx,ly+4,size=12,color=color)]
        for node in graph['nodes']:
            x,y=positions[node['id']]
            border = ' stroke-dasharray="4 4"' if node['kind']=='missing' else ''
            body += [f'<g class="sis-node" data-node="{escape(node["id"],quote=True)}" data-kind="{node["kind"]}"><title>{escape(node["label"])}</title>',f'<circle cx="{x}" cy="{y}" r="43" fill="white" stroke="#ccd9bd"{border}/>',glyph(node['kind'],x,y),label(node['label'],x,y+70,size=17,pixels=min(160,640/node_count-12)), '</g>']
        for i,line in enumerate(legend_lines): body.append(label(line,43,legend_top+i*25,size=15,anchor='start',pixels=650,color='#61765a'))
        body.append('</g>')
        top += panel_height + 45
        if phase=='before': body += [f'<path d="M380,{top-36} V{top-9}" stroke="#6f8b53" stroke-width="2" marker-end="url(#{marker})"/>']
    note_lines = wrap(spec['note'],690,16)
    body += [label(spec['note'],32,top-5,size=16,anchor='start',pixels=690,color='#647b55')]
    height = top + len(note_lines)*25 + 12
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title,quote=True)} 구조도" data-standard-code="{code}" style="font-family:Arial,Malgun Gothic,sans-serif"><title>{escape(title)} · 개념 변환</title><rect width="100%" height="100%" rx="20" fill="#fcfdf8"/>'+''.join(body)+'</svg>'
