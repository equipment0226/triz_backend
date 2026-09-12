"""Report design changes must preserve every recorded relationship and value."""
import copy
import re
import xml.etree.ElementTree as ET

import pytest

from triz import visuals
from report_design_fixture import example_report

NS = {'s':'http://www.w3.org/2000/svg'}



def semantic_graph(svg):
    root = ET.fromstring(svg)
    nodes = [(n.get('data-node'),n.find('s:title',NS).text,n.get('data-tone')) for n in root.findall('s:g[@class="diagram-node"]',NS)]
    edges = [(e.get('data-source'),e.get('data-target'),e.get('data-label'),e.get('data-harmful')) for e in root.findall('s:path[@class="diagram-edge"]',NS)]
    return nodes,edges


def test_all_report_templates_keep_original_graphs_and_state(monkeypatch):
    state = example_report()
    before = state.model_dump_json()
    original_svg = visuals.svg
    compared = []
    def checked(title,nodes,edges=(),columns=3,**options):
        original_data = copy.deepcopy((nodes,edges))
        result = original_svg(title,nodes,edges,columns,**options)
        legacy = original_svg(title,nodes,edges,columns,**{k:v for k,v in options.items() if k!='guide_kind'})
        assert semantic_graph(result) == semantic_graph(legacy)
        assert original_data == (nodes,edges)
        compared.append(options['guide_kind'])
        return result
    monkeypatch.setattr(visuals,'svg',checked)
    from triz.presentation import view
    from triz.render import render_html
    data = view(state)
    html = render_html(state)
    assert state.model_dump_json() == before
    assert {'function','sufield','ceca','resources','flow','contradiction','physical-contradiction',
            'trimming','matrix','separation','ariz','trends','fos','validation'} <= set(compared)
    rendered = [b['figure']['key'] for s in data['report_sections'] for b in s['blocks'] if b['type']=='figure']
    assert rendered.count('quadrant') == 1
    assert html.count('data-guide-kind="quadrant"') == 1


def node_boxes(svg):
    root = ET.fromstring(svg)
    return {g.get('data-node'):tuple(float(g.find('s:rect',NS).get(k)) for k in ('x','y','width','height'))
            for g in root.findall('s:g[@class="diagram-node"]',NS)}


def test_branches_and_su_field_match_the_guide_without_invented_edges():
    figures = {f['key']:f['svg'] for f in visuals.figures(example_report())}
    for key,parent,left,right in [('tc-0','action','good','bad'),('pc-0','element','a','b'),('sufield-0','F','S2','S1')]:
        boxes = node_boxes(figures[key])
        p,a,b = boxes[parent],boxes[left],boxes[right]
        assert p[1]+p[3] < a[1] == b[1]
        assert a[0] < p[0] < b[0]
    _,edges = semantic_graph(figures['sufield-0'])
    assert [(a,b) for a,b,*_ in edges] == [('F','S2'),('S2','S1')]
    assert 'S3' in node_boxes(figures['sufield-0'])
    assert not any('S3' in e[:2] for e in edges)


@pytest.mark.parametrize('kind',['ceca','ariz','matrix','separation','resources'])
def test_graph_routes_and_legends_clear_long_cards(kind):
    nodes = [('pair' if i==0 else str(i),'긴 설명과 조건 105℃ <확인> & '+('기존 내용을 유지한다. '* (i+1)), 'good') for i in range(7)]
    edges = [(nodes[0][0],n[0],'연결',False) for n in nodes[1:]]
    root = ET.fromstring(visuals.svg('긴 내용 검토',nodes,edges,guide_kind=kind,divided=True))
    boxes = node_boxes(ET.tostring(root,encoding='unicode')).values()
    for path in root.findall('s:path[@class="diagram-edge"]',NS):
        points = [tuple(map(float,p.split(','))) for p in re.findall(r'[ML]([-\d.]+,[-\d.]+)',path.get('d'))]
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            for x,y,w,h in boxes:
                assert not (y1==y2 and y<y1<y+h and max(x1,x2)>x and min(x1,x2)<x+w)
                assert not (x1==x2 and x<x1<x+w and max(y1,y2)>y and min(y1,y2)<y+h)
    labels = root.findall('s:text[@text-anchor="start"]',NS)
    assert labels and min(float(t.get('y')) for t in labels) > max(y+h for x,y,w,h in boxes)


def test_quadrant_coordinates_equal_markdown_and_preserve_coincident_scores():
    from triz.render import quadrant_mermaid, quadrant_points
    state = example_report()
    state.evaluation.evaluations[1].aggregate = dict(state.evaluation.evaluations[0].aggregate)
    points = quadrant_points(state)
    root = ET.fromstring(visuals.quadrant_plot(points))
    circles = root.findall('s:circle[@class="evaluation-point"]',NS)
    assert len(circles) == 2
    for circle,point in zip(circles,points):
        assert float(circle.get('data-x')) == point['x']
        assert float(circle.get('data-y')) == point['y']
        assert f'[{point["x"]:.3f}, {point["y"]:.3f}]' in quadrant_mermaid(state)
    assert circles[0].get('cx') == circles[1].get('cx')
    assert circles[0].get('cy') == circles[1].get('cy')
    state.evaluation.evaluations=[]
    assert not any(f['key']=='quadrant' for f in visuals.figures(state))


def test_curve_keeps_recorded_stage_without_example_forecast():
    result = visuals.s_curve_plot({'stage':'MATURITY'})
    assert '현재 · 성숙기' in result and '다음 변화' not in result
    assert '<circle' not in result
