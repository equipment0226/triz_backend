"""Shared, deterministic concept diagrams; never a rendering of inferred results."""
from html import escape
import math

from . import knowledge as K
from .separation_contract import LEGACY_VERSION, canonical_kind, legacy_catalog

WIDTH, HEIGHT = 720, 380
INK, LINE, GREEN, BLUE, ORANGE = '#253e34', '#547460', '#dce9ce', '#dfedf8', '#fae5ca'


def _text(value, x, y, size=17, anchor='middle', color=INK):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{color}">{escape(str(value))}</text>')


def _box(x, y, width, height, fill=GREEN, radius=12):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{LINE}" stroke-width="2"/>'


def _path(d, *, color=LINE, dash=False, width=3):
    dashed = ' stroke-dasharray="6 6"' if dash else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{dashed}/>'


def _arrow(x1, y1, x2, y2, color=LINE, dash=False):
    angle = math.atan2(y2-y1, x2-x1)
    bx, by = x2-10*math.cos(angle), y2-10*math.sin(angle)
    points = [(x2, y2), (bx+5*math.sin(angle), by-5*math.cos(angle)),
              (bx-5*math.sin(angle), by+5*math.cos(angle))]
    return _path(f'M{x1},{y1} L{x2},{y2}', color=color, dash=dash) + (
        f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="{color}"/>')


def _circle(x, y, r=24, fill=GREEN):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{LINE}" stroke-width="2"/>'


def _mechanism(kind, legacy=False):
    """Geometry distinguishes the mechanism, not only the caption or color."""
    if kind == 'SPACE':
        body = [_box(130, 107, 460, 112, 'white'), _box(142, 119, 216, 88, BLUE),
                _box(362, 119, 216, 88, GREEN), _path('M360,101 V227', dash=True),
                _text('부위 1 · 요구 A', 250, 167),
                _text('부위 2 · 요구 B', 470, 167), _text('같은 시스템 안의 서로 다른 위치', 360, 249, 15)]
        caption = ['상반된 요구를 서로 다른 위치에 배치한다.', '각 위치에서 필요한 기능과 두 위치 사이의 연결을 확인한다.']
    elif kind == 'TIME':
        body = [_arrow(95, 218, 635, 218), _text('시간', 650, 223, 14),
                _box(120, 109, 205, 83, BLUE), _box(395, 109, 205, 83, GREEN),
                _text('시점 t₁ · 요구 A', 222, 154), _text('시점 t₂ · 요구 B', 497, 154),
                _arrow(337, 150, 384, 150), _text('전환', 360, 130, 14),
                _path('M222,207 V230 M497,207 V230'), _text('동일 대상의 상태를 필요한 시점에 바꾼다', 360, 249, 15)]
        caption = ['상반된 요구가 필요한 시점을 구분한다.', '전환 시간·방법과 상태 전환 중의 기능 유지도 검토한다.']
    elif kind == 'CONDITION' and not legacy:
        body = [_box(275, 106, 170, 120, GREEN), _text('같은 시스템', 360, 150),
                _text('선택적 관계', 360, 178, 15), _circle(130, 164, 48, BLUE),
                _circle(590, 164, 48, ORANGE), _text('대상 1', 130, 171), _text('대상 2', 590, 171),
                _arrow(271, 147, 184, 147), _arrow(449, 183, 536, 183),
                _text('요구 A', 222, 130, 15), _text('요구 B', 497, 210, 15),
                _text('누구에게 / 어떤 대상에 대해 작용하는가', 360, 250, 15)]
        caption = ['서로 다른 대상과의 관계에 따라 상반된 요구를 충족한다.', '온도·하중의 임계값만 바뀌는 것을 관계 분리로 단정하지 않는다.']
    elif kind == 'CONDITION':
        body = [_arrow(110, 205, 610, 205), _path('M360,101 V227', dash=True),
                _box(130, 113, 200, 70, BLUE), _box(390, 113, 200, 70, GREEN),
                _text('조건 범위 1 · A', 230, 154), _text('조건 범위 2 · B', 490, 154),
                _text('온도·하중 등 저장된 조건 구분', 360, 249, 15)]
        caption = ['과거 4종 체계의 넓은 조건 분리를 설명하는 개념도이다.', '새 관계(조건) 분리로 재분류하지 않으며 실제 조건은 원 기록을 따른다.']
    elif kind == 'DIRECTION':
        body = [_box(260, 113, 200, 100, 'white')]
        body += [_path(f'M{x},121 V205', width=5) for x in range(275, 459, 20)]
        body += [_arrow(140, 163, 250, 163), _arrow(470, 163, 580, 163),
                 _arrow(360, 97, 360, 62), _arrow(360, 229, 360, 264),
                 _text('방향 x · A', 147, 140, 16), _text('방향 y · B', 453, 91, 16)]
        caption = ['같은 시스템도 작용 방향에 따라 서로 다른 응답을 갖게 한다.', '방향별 물성·운동·작용 경로와 실제 방향 조건을 확인한다.']
    elif kind == 'SYSTEM_LEVEL':
        body = [_box(136, 91, 448, 158, 'white'), _text('전체 수준 · 요구 B', 360, 120),
                _path('M205,183 H515', dash=True)]
        for x in (218, 360, 502):
            body += [_circle(x, 186, 40, BLUE), _text('부분 A', x, 191, 16)]
        caption = ['부분의 성질과 결합된 전체의 성질을 다르게 구성한다.', '항상 검토하는 접근이지만 해당 문제에서 성립한다는 뜻은 아니다.']
    elif kind == 'SATISFY':
        body = [_box(240, 121, 235, 104, GREEN), _text('두 기능을 함께 만드는', 357, 158, 16),
                _text('인과 메커니즘', 357, 187, 18), _arrow(480, 149, 540, 117),
                _arrow(480, 194, 540, 225), _box(547, 82, 135, 61, BLUE),
                _box(547, 204, 135, 61, ORANGE), _text('요구 A 충족', 614, 119, 15),
                _text('요구 B 충족', 614, 241, 15), _text('동일한 운전에서', 124, 153, 15),
                _text('필수 기능 유지', 124, 179, 15), _arrow(184, 171, 230, 171)]
        caption = ['두 요구를 함께 만족시키는 기능적 인과 경로를 찾는다.', '같은 속성의 A와 not-A가 설명 없이 동시에 성립한다고 주장하지 않는다.']
    elif kind == 'BYPASS':
        body = [_box(32, 141, 130, 62, BLUE), _text('필수 기능', 97, 179),
                _box(268, 84, 193, 61, '#f2f2ef'), _text('기존 모순 경로', 364, 121, 16),
                _arrow(168, 156, 259, 114, dash=True), _arrow(469, 114, 552, 156, dash=True),
                _path('M341,91 L387,137 M387,91 L341,137', color='#a56458', width=2),
                _box(251, 211, 226, 61, GREEN), _text('다른 기능 실현 방식', 364, 248, 16),
                _arrow(167, 189, 242, 238), _arrow(485, 238, 552, 189),
                _box(560, 141, 130, 62, BLUE), _text('같은 목적', 625, 179)]
        caption = ['필수 기능을 다른 방식으로 수행해 기존 모순의 전제를 없앤다.', '상위 목적·필수 기능·승인된 제약을 없애는 방식은 우회 해결이 아니다.']
    else:
        raise ValueError('Unknown physical contradiction approach')
    return ''.join(body), caption


def diagram(kind, *, legacy=False):
    kind = canonical_kind(kind)
    catalog = legacy_catalog() if legacy else K.separation()
    if kind not in catalog:
        raise ValueError('Unknown physical contradiction approach')
    row = catalog[kind]
    title = row['name_ko']
    family = '과거 4종 분리 체계' if legacy else '5가지 분리 접근' if row['family'] == 'SEPARATE' else '2가지 보완 접근'
    art, captions = _mechanism(kind, legacy)
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'role="img" aria-label="{escape(title, quote=True)} 개념도" '
            f'data-diagram="separation-concept" data-approach-kind="{kind}" '
            f'data-catalog-version="{escape(row.get("catalog_version", LEGACY_VERSION), quote=True)}" '
            'style="font-family:Arial,Malgun Gothic,sans-serif">',
            f'<title>{escape(title)} · 설명용 개념도</title>',
            '<desc>접근의 일반적인 작동 구분을 설명한다. 실제 적용안이나 검증된 결과를 나타내지 않는다.</desc>',
            f'<rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="#f5f7f0"/>',
            _text(title, 28, 36, 23, 'start'), _text(family+' · 설명용 개념도', 692, 35, 14, 'end'),
            f'<g data-mechanism="{kind.lower()}{"-legacy" if legacy else ""}">{art}</g>']
    from .visuals import wrap
    lines = [line for caption in captions for line in wrap(caption, 660, 14)]
    body += [_text(line, 360, 301+i*22, 14) for i, line in enumerate(lines)]
    body.append('</svg>')
    return ''.join(body)


def _stack(items, title):
    """Embed the exact shared SVG bodies, one legible full-width concept per row."""
    height = 80 + len(items)*(HEIGHT+18)
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
              f'role="img" aria-label="{escape(title, quote=True)}" data-diagram="separation-concept-group" '
              'style="font-family:Arial,Malgun Gothic,sans-serif">',
              _text(title, 24, 28, 20, 'start'),
              _text('설명용 개념도 · 실제 적용 내용과 판정은 저장된 검토 표를 따른다.', 24, 54, 14, 'start')]
    for i, (kind, legacy) in enumerate(items):
        svg = diagram(kind, legacy=legacy)
        result.append(svg.replace('<svg ', f'<svg x="0" y="{80+i*(HEIGHT+18)}" width="{WIDTH}" height="{HEIGHT}" ', 1))
    if not items:
        result.append(_text('분류를 확인할 수 없어 접근 개념도를 표시하지 않는다.', 24, 76, 15, 'start'))
    return ''.join(result)+'</svg>'


def overview():
    """A compact index for introduction cards; full mechanism diagrams are separate."""
    from .visuals import wrap
    catalog = K.separation()
    body = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 470" role="img" '
            'aria-label="5가지 분리와 2가지 보완 접근" data-diagram="separation-overview" '
            'style="font-family:Arial,Malgun Gothic,sans-serif">',
            '<rect width="720" height="470" rx="18" fill="#f5f7f0"/>',
            _text('물리적 모순 해결 · 5가지 분리 + 2가지 보완 접근', 24, 33, 20, 'start'),
            _text('분리 접근 5가지', 24, 73, 17, 'start'),
            _text('보완 접근 2가지', 470, 73, 17, 'start')]
    questions = {'SPACE':'어디에서?', 'TIME':'언제?', 'CONDITION':'누구에게 / 어떤 대상에 대해?',
                 'DIRECTION':'어느 방향으로?', 'SYSTEM_LEVEL':'부분과 전체의 성질을 구분 · 항상 검토'}
    for i, kind in enumerate(k for k,v in catalog.items() if v['family']=='SEPARATE'):
        y = 88+i*66
        body += [f'<g data-approach-kind="{kind}">', _box(24,y,420,58,'white'),
                 _text(catalog[kind]['name_ko'], 42, y+23, 17, 'start'),
                 _text(questions[kind], 42, y+45, 14, 'start'), '</g>']
    summaries = {'SATISFY':['기능적 인과 경로를 찾아', '두 요구를 함께 만족'],
                 'BYPASS':['필수 기능과 목적은 유지', '기존 모순의 전제를 우회']}
    for i, kind in enumerate(('SATISFY','BYPASS')):
        y = 88+i*165
        body += [f'<g data-approach-kind="{kind}">', _box(470,y,226,157,BLUE if i==0 else GREEN)]
        for j, line in enumerate(wrap(catalog[kind]['name_ko'], 194, 17)):
            body.append(_text(line, 486, y+29+j*25, 17, 'start'))
        for j, line in enumerate(summaries[kind]):
            body.append(_text(line, 486, y+105+j*23, 14, 'start'))
        body.append('</g>')
    body += [_text('분류 안내용 개념도 · 실제 검토 여부와 적용 가능성은 분석 기록을 따른다.', 24, 445, 14, 'start'), '</svg>']
    return ''.join(body)


def for_applications(applications):
    """Only illustrate stored approach kinds; never fill in unexecuted reviews."""
    items = []
    current, old = K.separation(), legacy_catalog()
    for app in applications:
        kind = canonical_kind(app.get('kind'))
        if not isinstance(kind, str) or kind not in current:
            continue
        legacy = kind in old and (not app.get('catalog_version') or app.get('catalog_version') == LEGACY_VERSION)
        key = (kind, legacy)
        if key not in items:
            items.append(key)
    return _stack(items, '저장된 검토 항목에 해당하는 해결 접근의 개념')


def assets():
    """Canonical static filenames shared by frontend documentation and reports."""
    return {**{kind.lower()+'.svg': diagram(kind) for kind in K.separation()},
            'overview.svg': overview(), 'legacy_condition.svg': diagram('CONDITION', legacy=True)}
