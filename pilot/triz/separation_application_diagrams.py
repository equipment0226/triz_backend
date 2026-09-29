"""Read-only diagrams of saved separation proposals, without inferred mappings."""
from hashlib import sha256
from html import escape
import json
import unicodedata

from . import knowledge as K
from .separation_contract import LEGACY_VERSION, canonical_kind, legacy_catalog

WIDTH, PAD, GAP = 840, 24, 28
INK, STROKE, GREEN, BLUE, PAPER = '#253e34', '#547460', '#e5efd9', '#e2edf6', '#fcfdf8'
NOTE = '분석에 기록된 적용 내용이며 실증 결과는 별도입니다.'


def wrap(value, pixels, size):
    """Conservative Korean and wide-Latin widths without deleting source text."""
    def width(char):
        if unicodedata.combining(char):
            return 0
        return size*(1.08 if unicodedata.east_asian_width(char) in 'WF' or char in 'MWmw@%' else .72)
    lines=[]
    for paragraph in str(value).split('\n'):
        line, used='', 0
        for char in paragraph:
            advance=width(char)
            if line and used+advance>pixels:
                split=line.rfind(' ')
                if split>0 and line[split+1:]:
                    lines.append(line[:split+1]); line=line[split+1:]
                    used=sum(width(c) for c in line)
                else:
                    lines.append(line); line,used='',0
            line+=char; used+=advance
        lines.append(line)
    return lines or ['']


def _value(value, missing):
    if value is None or value == '' or value == [] or value == {}:
        return missing
    if isinstance(value, str):
        return value if value.strip() else missing
    if isinstance(value, (list, tuple)):
        return '\n'.join(_value(item, '내용 기록 없음') for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def _fields(source, prefix, definitions, *, exclude=()):
    """Keep available content once within a source block, without filling gaps."""
    result, seen = [], set(exclude)
    for field, heading in definitions:
        value = _value(source.get(field), '')
        if value and value not in seen:
            result.append((prefix+'.'+field, heading, value))
            seen.add(value)
    return result


def _text(text, x, y, *, size=16, color=INK):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="start">{escape(str(text))}</text>')


def _card(key, title, fields, width, *, fill='white'):
    """Measure every line before placement; no clipping or content truncation."""
    lines = []
    cursor = 29
    for line in wrap(title, width-36, 17):
        lines.append(('heading', line, cursor, 17))
        cursor += 27
    cursor += 5
    for field, heading, value in fields:
        for line in wrap(heading, width-36, 14):
            lines.append((field, line, cursor, 14))
            cursor += 22
        for line in wrap(value, width-36, 16):
            lines.append((field, line, cursor, 16))
            cursor += 25
        cursor += 11
    return dict(key=key, title=title, width=width, height=cursor+7, lines=lines, fill=fill)


def _draw_card(card, x, y):
    body = [f'<g class="separation-application-node" data-node="{card["key"]}" '
            f'data-x="{x}" data-y="{y}" data-width="{card["width"]}" data-height="{card["height"]}">',
            f'<rect x="{x}" y="{y}" width="{card["width"]}" height="{card["height"]}" '
            f'rx="14" fill="{card["fill"]}" stroke="{STROKE}" stroke-width="1.7"/>']
    for field, text, top, size in card['lines']:
        body.append(f'<g data-field="{escape(field, quote=True)}">'+
                    _text(text, x+18, y+top, size=size, color='#59704e' if size==14 else INK)+'</g>')
    body.append('</g>')
    return ''.join(body)


def _edge(points, marker, source, target, *, curved=False):
    if curved:
        start, control, finish = points
        path = f'M{start[0]},{start[1]} Q{control[0]},{control[1]} {finish[0]},{finish[1]}'
    else:
        path = 'M'+' L'.join(f'{x},{y}' for x,y in points)
    return (f'<path class="separation-application-edge" data-source="{source}" data-target="{target}" '
            f'data-relationship="saved-reference" d="{path}" fill="none" stroke="{STROKE}" '
            f'stroke-width="2" stroke-linejoin="round" marker-end="url(#{marker})"/>')


def _core(kind, cards, top, marker):
    """Different reading layouts, never inferred spatial/temporal assignments."""
    full = WIDTH-2*PAD
    half = (full-GAP)/2
    body, positions = [], {}

    def place(key, width, x, y):
        title, fields, fill = cards[key]
        card = _card(key, title, fields, width, fill=fill)
        positions[key] = dict(x=x, y=y, w=width, h=card['height'])
        body.append(_draw_card(card, x, y))
        return y+card['height']

    def edge(start, end, points, curved=False):
        body.append(_edge(points, marker, start, end, curved=curved))

    if kind == 'SPACE':
        # Side-by-side *requirements*, not invented physical areas.
        bottom = max(place('requirement-a', half, PAD, top),
                     place('requirement-b', half, PAD+half+GAP, top))
        how_y = bottom+56
        end = place('application-how', full, PAD, how_y)
        for key in ('requirement-a','requirement-b'):
            p = positions[key]; x = p['x']+p['w']/2
            edge(key, 'application-how', [(x,p['y']+p['h']), (x,how_y-4)])
        body.append(f'<path d="M{WIDTH/2},{top} V{bottom}" stroke="#b6c5ad" stroke-dasharray="4 6" fill="none"/>')
    elif kind == 'TIME':
        # The source does not supply machine-readable event ordering. Both
        # demands refer independently to the complete, unparsed saved wording.
        bottom = place('application-how', full, PAD, top)
        row = bottom+62
        end = max(place('requirement-a', half, PAD, row),
                  place('requirement-b', half, PAD+half+GAP, row))
        for key in ('requirement-a','requirement-b'):
            p = positions[key]; x = p['x']+p['w']/2
            edge('application-how', key, [(WIDTH/2,bottom), (WIDTH/2,bottom+28), (x,bottom+28), (x,row-4)])
    elif kind == 'CONDITION':
        small, middle, gap = 220, 296, 28
        columns = [('requirement-a',small,PAD), ('application-how',middle,PAD+small+gap),
                   ('requirement-b',small,PAD+small+gap+middle+gap)]
        end = max(place(key,width,x,top) for key,width,x in columns)
        how = positions['application-how']
        a, b = positions['requirement-a'], positions['requirement-b']
        edge('requirement-a','application-how',[(a['x']+a['w'],top+38),(how['x']-4,top+38)])
        edge('requirement-b','application-how',[(b['x'],top+70),(how['x']+how['w']+4,top+70)])
    elif kind == 'DIRECTION':
        narrow, wide = 282, full-282-64
        a_bottom = place('requirement-a', narrow, PAD, top)
        b_bottom = place('requirement-b', narrow, PAD, a_bottom+GAP)
        right = PAD+narrow+64
        end = max(b_bottom, place('application-how',wide,right,top))
        how = positions['application-how']
        for i,key in enumerate(('requirement-a','requirement-b')):
            p = positions[key]; y = p['y']+p['h']/2; lane = right-40+i*16
            edge(key,'application-how',[(p['x']+p['w'],y),(lane,y),(lane,top+42+i*42),(how['x']-4,top+42+i*42)])
    elif kind == 'SYSTEM_LEVEL':
        demand_bottom = max(place('requirement-a',half,PAD,top),
                            place('requirement-b',half,PAD+half+GAP,top))
        how_y = demand_bottom+76
        end = place('application-how',full-48,PAD+24,how_y)
        body.insert(0, f'<rect x="{PAD}" y="{how_y-24}" width="{full}" height="{end-how_y+48}" '
                       'rx="20" fill="#f0f4e8" stroke="#bac9ad" stroke-width="2"/>')
        for key in ('requirement-a','requirement-b'):
            p=positions[key]; x=p['x']+p['w']/2
            edge(key,'application-how',[(x,p['y']+p['h']),(x,how_y-28)])
        end += 24
    elif kind == 'SATISFY':
        demand_bottom = max(place('requirement-a',half,PAD,top),
                            place('requirement-b',half,PAD+half+GAP,top))
        junction_y = demand_bottom+38
        how_y = demand_bottom+82
        end = place('application-how',full-96,PAD+48,how_y)
        for key in ('requirement-a','requirement-b'):
            p=positions[key]; x=p['x']+p['w']/2
            edge(key,'application-how',[(x,p['y']+p['h']),(x,junction_y),(WIDTH/2,junction_y),(WIDTH/2,how_y-4)])
        body.append(f'<circle cx="{WIDTH/2}" cy="{junction_y}" r="5" fill="{STROKE}"/>')
    else:  # BYPASS: frame the saved contradiction; no invented discarded method.
        left, right = 298, full-298-68
        a_bottom = place('requirement-a',left-28,PAD+14,top+20)
        b_bottom = place('requirement-b',left-28,PAD+14,a_bottom+GAP)
        body.insert(0,f'<rect x="{PAD}" y="{top}" width="{left}" height="{b_bottom-top+20}" '
                      'rx="18" fill="none" stroke="#aebaa5" stroke-dasharray="6 6"/>')
        how_x = PAD+left+68
        end = max(b_bottom+20, place('application-how',right,how_x,top+58))
        edge('requirement-a','application-how',[(PAD+left,top+36),(how_x+right/2,top-3),(how_x+right/2,top+54)],curved=True)
        edge('requirement-b','application-how',[(PAD+left,b_bottom-24),(how_x-24,b_bottom-24),
                                               (how_x-24,top+112),(how_x-4,top+112)])
    return ''.join(body), end


def render_application(application: dict, *, contradiction: dict | None = None,
                       solution: dict | None = None) -> dict:
    if not isinstance(application, dict) or application.get('applicable') is not True:
        raise ValueError('A saved application with applicable=True is required')
    kind = canonical_kind(application.get('kind'))
    if not isinstance(kind,str) or kind not in K.separation():
        raise ValueError('Unknown physical contradiction approach')
    if contradiction is not None and not isinstance(contradiction,dict):
        raise ValueError('contradiction must be a saved dictionary or None')
    if solution is not None and not isinstance(solution,dict):
        raise ValueError('solution must be a saved dictionary or None')
    contradiction, solution = contradiction or {}, solution or {}
    old = legacy_catalog()
    legacy = kind in old and (not application.get('catalog_version') or application.get('catalog_version') == LEGACY_VERSION)
    name = (old if legacy else K.separation())[kind]['name_ko']
    selected_title = _value(solution.get('title') or application.get('title'), '분리 적용안')
    title = selected_title+' · '+name
    marker = 'sep-app-'+sha256(json.dumps([application,contradiction,solution],ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()[:16]
    body = [f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
            f'<path d="M0,0 L8,4 L0,8" fill="none" stroke="{STROKE}" stroke-width="1.6"/></marker></defs>']
    cursor = 33
    for line in wrap(title, WIDTH-2*PAD, 22):
        body.append(_text(line,PAD,cursor,size=22)); cursor+=34
    cursor += 8
    context_fields = _fields(contradiction,'contradiction',[('element','대상'),('parameter','속성')])
    if context_fields:
        prefix='대상' if _value(contradiction.get('element'),'') else '속성'
        context=prefix+' · '+' / '.join(value for _,_,value in context_fields)
        lines=wrap(context,WIDTH-2*PAD-36,16)
        context_height=len(lines)*25+25
        body.append(f'<g class="separation-application-node" data-node="contradiction" '
                    f'data-x="{PAD}" data-y="{cursor}" data-width="{WIDTH-2*PAD}" data-height="{context_height}">'
                    f'<rect x="{PAD}" y="{cursor}" width="{WIDTH-2*PAD}" height="{context_height}" '
                    f'rx="12" fill="#f0f4e8" stroke="{STROKE}" stroke-width="1.7"/>')
        # Both source values share a compact banner; field provenance still
        # covers its complete wrapped text rather than dropping either value.
        for field,_,_ in context_fields:
            body.append(f'<g data-field="{field}">')
        body.extend(_text(line,PAD+18,cursor+28+i*25) for i,line in enumerate(lines))
        body.extend('</g>' for _ in context_fields)
        body.append('</g>')
        cursor+=context_height+22
    elif not contradiction:
        body.append(_text('대상 모순 연결 정보 없음',PAD,cursor+4,size=14))
        cursor += 28
    provenance = _value(solution.get('provenance_label'),'')
    if provenance:
        body.append(f'<g data-provenance-label="{escape(provenance,quote=True)}">'+
                    _text('원안의 분리 방식',PAD,cursor+4,size=17)+'</g>')
        cursor += 28
    axis = {'SPACE':'공간 구분','TIME':'시간 구분','CONDITION':'조건 구분' if legacy else '관계 구분',
            'DIRECTION':'방향 구분','SYSTEM_LEVEL':'시스템 수준 구분','SATISFY':'동시 충족 제안','BYPASS':'우회 방식 제안'}[kind]
    cards = {
        'requirement-a':('상반 요구 A',_fields(contradiction,'contradiction',[
            ('state_a','요구'),('reason_a','필요 이유')]),BLUE),
        'requirement-b':('상반 요구 B',_fields(contradiction,'contradiction',[
            ('state_b','요구'),('reason_b','필요 이유')]),'#faead6'),
        'application-how':(axis+' · 적용 방식',_fields(application,'application',[
            ('title','적용안'),('how','적용 방식')],exclude=[selected_title]),GREEN),
    }
    if cards['requirement-a'][1] and cards['requirement-b'][1]:
        core,bottom = _core(kind,cards,cursor,marker)
        body.append(core); cursor=bottom+24
    else:
        # A missing relation is not an invitation to fabricate two requirements.
        for key in ('requirement-a','requirement-b','application-how'):
            heading,fields,fill = cards[key]
            if not fields:
                continue
            card=_card(key,heading,fields,WIDTH-2*PAD,fill=fill)
            body.append(_draw_card(card,PAD,cursor)); cursor+=card['height']+22
    sections = [
        ('proposal','아이디어와 작동 원리',_fields(application,'application',[
            ('idea','아이디어'),('mechanism','작동 원리')],exclude=[_value(application.get('how'),'')])),
        ('solution','해결안의 작동 방식',_fields(solution,'solution',[
            ('title','해결책'),('working_principle','작동 원리'),('one_liner','요약'),
            ('changes_to_system','시스템 변경')],exclude=[selected_title])),
        ('conditions','적용 조건과 검증',_fields(application,'application',[
            ('conditions','필요 조건'),('validation_test','검증 계획')])),
    ]
    for key,heading,fields in sections:
        if not fields:
            continue
        card=_card(key,heading,fields,WIDTH-2*PAD)
        body.append(_draw_card(card,PAD,cursor)); cursor+=card['height']+22
    for line in wrap(NOTE,WIDTH-2*PAD,14):
        body.append(_text(line,PAD,cursor,size=14,color='#59704e')); cursor+=23
    height=cursor+18
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" role="img" '
         f'aria-label="{escape(title,quote=True)} 저장된 제안 도식" data-diagram="separation-application" '
         f'data-approach-kind="{kind}" data-layout="{kind.lower()}" '
         'style="font-family:Arial,Malgun Gothic,sans-serif">'
         f'<title>{escape(title)}</title><desc>{escape(NOTE)}</desc>'
         f'<rect width="100%" height="100%" rx="20" fill="{PAPER}"/>'+''.join(body)+'</svg>')
    return dict(title=title,compact=True,svg=svg,note=NOTE)
