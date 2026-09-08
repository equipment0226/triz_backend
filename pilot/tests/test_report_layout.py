import re
from triz import render
from triz.presentation import view
from triz.report_content import render_markdown
from triz.report_style import plain_text
from triz.schema import ReportArtifact, ConceptSpec, ConceptEvaluation, TechnicalContradiction, Constraint
from triz import visuals
import xml.etree.ElementTree as ET


def test_report_plain_register_preserves_facts():
    assert plain_text('냉각합니다. 필요합니다. 조건입니다. 가능합니다. 생깁니다. 됩니다. 다릅니다. 없습니다. 했습니다.') == '냉각한다. 필요하다. 조건이다. 가능하다. 생긴다. 된다. 다르다. 없다. 했다.'
    assert plain_text('105℃ / 100% https://example.com/합니다 `합니다`') == '105℃ / 100% https://example.com/합니다 `합니다`'


def test_report_places_each_contradiction_and_additional_concept_without_mutating_state(state):
    state.definition.technical_contradictions = [TechnicalContradiction(label=f'모순 {i}', if_action=f'동작 {i}', then_good='개선합니다.', but_bad='악화됩니다.') for i in range(2)]
    c = ConceptSpec(title='추가 해결책', description='냉각합니다.')
    state.concepts = [c]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id=c.id, rank=99)]
    state.report = ReportArtifact(narrative={'executive_summary':'가능합니다.'})
    before = state.model_dump_json()
    data = view(state)
    blocks = [b for section in data['report_sections'] for b in section['blocks']]
    keys = [b['figure']['key'] for b in blocks if b['type'] == 'figure']
    assert keys.count('tc-0') == keys.count('tc-1') == keys.count('concept-0') == 1
    assert 'nine-windows' not in keys
    first = next(i for i,b in enumerate(blocks) if b.get('figure',{}).get('key') == 'tc-0')
    second = next(i for i,b in enumerate(blocks) if b.get('figure',{}).get('key') == 'tc-1')
    assert any('동작 1' in b.get('html','') for b in blocks[first+1:second])
    html = render.render_html(state)
    assert '[추가 도출]' in html and '[99위]' not in html
    assert '냉각한다.' in html and '냉각합니다.' not in html
    assert '해결안 상세' not in html
    assert state.model_dump_json() == before


def test_matrix_escapes_cell_separators_and_splits_wide_tables(state):
    c = ConceptSpec(title='설계 A | B\n냉각')
    state.concepts = [c]
    state.constraints.items = [Constraint(statement=f'제약 {i}') for i in range(17)]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id=c.id, rank=1)]
    html = render_markdown(render.constraint_matrix(state)['md'])
    assert html.count('<table') == 3
    assert '설계 A | B 냉각' in html
    assert '<col style="width:35.000%">' in html
    for columns in re.findall(r'<colgroup>(.*?)</colgroup>', html):
        assert abs(sum(map(float,re.findall(r'width:([\d.]+)%', columns))) - 100) < .01
    for row in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        assert len(re.findall(r'<t[hd]>',row)) <= 10


def test_arrows_and_relation_labels_avoid_every_box_in_all_directions():
    nodes = [(str(i), '긴 설명 ' * (i*7+1), '') for i in range(9)]
    edges = [(a[0],b[0],'연결',False) for a in nodes for b in nodes]
    root = ET.fromstring(visuals.svg('상자 우회 검증',nodes,edges,columns=3))
    ns = {'s':'http://www.w3.org/2000/svg'}
    boxes = [tuple(float(r.get(k)) for k in ('x','y','width','height')) for r in root.findall('.//s:g/s:rect',ns)]
    paths = root.findall('s:path',ns)
    assert len(paths) == len(edges)
    for path in paths:
        points = [tuple(map(float, p.split(','))) for p in re.findall(r'[ML]([\d.]+,[\d.]+)',path.get('d'))]
        assert len(points) >= 2
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            assert x1 == x2 or y1 == y2
            for x,y,w,h in boxes:
                horizontal = y1 == y2 and y < y1 < y+h and max(x1,x2) > x and min(x1,x2) < x+w
                vertical = x1 == x2 and x < x1 < x+w and max(y1,y2) > y and min(y1,y2) < y+h
                assert not (horizontal or vertical), (path.get('d'), (x,y,w,h))
    for circle in root.findall('s:circle',ns):
        cx,cy,r = (float(circle.get(k)) for k in ('cx','cy','r'))
        assert all(cx+r <= x or cx-r >= x+w or cy+r <= y or cy-r >= y+h for x,y,w,h in boxes)
