import re
from triz import render
from triz.presentation import view
from triz.report_content import render_markdown
from triz.report_style import plain_text
from triz.schema import ReportArtifact, ConceptSpec, ConceptEvaluation, TechnicalContradiction, Constraint
from triz import visuals
import xml.etree.ElementTree as ET


def test_problem_specific_tables_and_legacy_provenance(state):
    from triz.schema import MatrixLookup, KeyProblem, PhysicalContradiction, RawIdea
    from triz.report_groups import matrix_groups, separation_groups
    t1 = TechnicalContradiction(label='온도와 손상', improving_param_id=17, worsening_param_id=31)
    t2 = TechnicalContradiction(label='속도와 진동', improving_param_id=9, worsening_param_id=11)
    state.definition.technical_contradictions = [t1, t2]
    state.definition.key_problems = [KeyProblem(title='가열 시 기판 손상', contradiction_ids=[t1.id]),
                                     KeyProblem(title='고속 이송 시 흔들림', contradiction_ids=[t2.id])]
    state.solve.matrix_lookups = [MatrixLookup(improving_param_id=17, worsening_param_id=31, principle_ids=[1]),
                                  MatrixLookup(improving_param_id=9, worsening_param_id=11, principle_ids=[1])]
    apps = [dict(principle_id=1, principle_name='분할', title='열 구간 분할', idea='열을 구역별로 제어'),
            dict(principle_id=1, principle_name='분할', title='지지 구간 분할', idea='지지를 구역별로 제어')]
    state.solve.principle_apps = apps
    state.solve.raw_ideas = [RawIdea(track='A_MATRIX', detail=app, addresses=[tc.id]) for app, tc in zip(apps, [t1,t2])]
    groups, unlinked = matrix_groups(state)
    assert not unlinked and groups[0]['apps'] == [apps[0]] and groups[1]['apps'] == [apps[1]]
    p1, p2 = PhysicalContradiction(label='단단함과 유연함'), PhysicalContradiction(label='고온과 저온')
    state.definition.physical_contradictions = [p1, p2]
    state.solve.separation_apps = [dict(source_pc_id=p1.id, kind='SPACE', applicable=True, title='공간 분리', idea='지지 분리'),
                                   dict(source_pc_id=p2.id, kind='TIME', applicable=False, not_applicable_reason='동시 요구')]
    assert [len(g['apps']) for g in separation_groups(state)] == [1,1]
    state.report = ReportArtifact()
    before = state.model_dump_json()
    data = view(state)
    blocks = next(s['blocks'] for s in data['report_sections'] if s['title'].startswith('4.'))
    keys = [b.get('figure',{}).get('key') for b in blocks]
    i1, i2 = keys.index('matrix-0'), keys.index('matrix-1')
    between = ''.join(b.get('html','') for b in blocks[i1+1:i2])
    assert '열을 구역별로 제어' in between and '지지를 구역별로 제어' not in between
    assert '가열 시 기판 손상에 대한 모순행렬 결과 조회' in ''.join(b.get('html','') for b in blocks)
    assert '단단함과 유연함에 대한' in ''.join(b.get('html','') for b in blocks)
    assert state.model_dump_json() == before


def test_unlinked_applications_are_preserved_without_guessing(state):
    from triz.report_groups import separation_groups
    from triz.schema import PhysicalContradiction
    state.definition.physical_contradictions = [PhysicalContradiction(label='A'), PhysicalContradiction(label='B')]
    state.solve.separation_apps = [dict(title='출처가 없는 적용안', applicable=False)]
    assert separation_groups(state)[0]['key'] == 'separation-unlinked'


def test_standard_model_parses_prime_field_and_does_not_invent_plus_link(state):
    from triz.schema import SuFieldModel
    source = SuFieldModel(s1='진동 신호', s2='데이터 수집 장치', field='연속 샘플링')
    state.analysis.su_fields = [source]
    app = dict(source_su_id=source.id, standard_code='4.1.1', standard_title='측정',
        resulting_su_field="S1(진동 신호) -[F'(최소 샘플링)]-> S2(데이터 수집 장치) + S3(압축/요약 모듈)")
    nodes, edges, _ = visuals.standard_model(state, app)
    assert {n[0]:n[2] for n in nodes} == {'F′':'changed', 'S1':'', 'S2':'', 'S3':'added'}
    assert ('S1','S2') in [e[:2] for e in edges]
    assert not any('S3' in e[:2] for e in edges)
    state.solve.standard_apps = [app]
    state.solve.effect_apps = [dict(effect_domain='PHYSICAL', effect_name='압전 효과', required_function='진동 감지',
        principle='힘을 전하로', title='센서', idea='센서 부착', conditions='온도 제한'),
        dict(effect_domain='PHYSICAL', effect_name='열전 효과', required_function='전력 생성', idea='전력 공급')]
    state.report = ReportArtifact()
    data = view(state)
    assert [f for f in data['figures'] if f['key']=='standard-0'][0]['compact']
    assert not any(f['key']=='effects' for f in data['figures'])
    text = ''.join(b.get('html','') for s in data['report_sections'] for b in s['blocks'])
    assert '압전 효과' in text and '열전 효과' in text and text.count('<h4>물리 효과</h4>') == 1


def test_all_number_badges_are_painted_after_every_arrow():
    root = ET.fromstring(visuals.svg('흐름', [('a','A',''),('b','B',''),('c','C','')],
        [('a','c','개선',False),('b','c','악화',True)]))
    children = list(root)
    paths = [i for i,c in enumerate(children) if c.get('class') == 'diagram-edge']
    badges = [i for i,c in enumerate(children) if c.get('class') == 'diagram-edge-label']
    assert max(paths) < min(badges)


def test_semantic_emphasis_does_not_change_urls_or_allow_html():
    html = render_markdown('개선 및 악화 [개선](https://example.org/개선) `<script>` <script>evil()</script>')
    assert 'report-term' not in html
    assert '<script>' not in html
    assert 'href="https://example.org/' in html
    table = render_markdown('| 종류 | 수준 |\n|:---|---:|\n|유익 개선|적정|\n|유해 악화|과잉|\n|일반|부족|')
    assert 'color:#1764b5' in table and 'color:#bd343b' in table and 'color:#111111' in table
    assert 'text-align:right' not in table and 'text-align:left' not in table
    assert 'report-term' not in render_markdown('|개선|악화|\n|---|---|\n|유익|유해|', emphasize_tables=False)
    standalone = render_markdown('|항목|값|\n|---|---|\n|종류|**유해**|\n|종류| 유익 |')
    assert standalone.count('class="report-term"') == 2
    phrases = render_markdown('|내용|\n|---|\n|**유해** 작용|\n|유익한 기능|\n|기능 개선|\n|유해 / 유익|\n|핵심 문제|')
    assert 'report-term' not in phrases
    assert 'font-weight="700"' in visuals.label('유해',0,0,emphasize=True)
    assert 'font-weight="700"' not in visuals.label('유해 작용',0,0,pixels=28,emphasize=True)
    assert 'font-weight="700"' not in visuals.label('유익\n개선',0,0,emphasize=True)


def test_diagram_titles_plain_and_arrows_match_meaning():
    root=ET.fromstring(visuals.svg('점선은 유해 작용', [('a','유익 개선',''),('b','유해 악화','')],
        [('a','b','유해',True),('b','a','유익',False)]))
    ns={'s':'http://www.w3.org/2000/svg'}
    title=root.find('s:text',ns)
    assert title is not None and not title.findall('.//s:tspan[@font-weight]',ns)
    paths=root.findall('s:path',ns)
    assert [p.get('stroke') for p in paths]==['#bd343b','#1764b5']
    for p in paths:
        identifier=p.get('marker-end')[5:-1]
        marker=root.find(f'.//s:marker[@id="{identifier}"]/s:path',ns)
        assert marker.get('fill')==p.get('stroke')


def test_ariz_steps_trends_and_fos_are_structured_without_aggregate_diagram(state):
    from triz.schema import ARIZRun, ARIZStep, Component
    state.analysis.components=[Component(name='하위 예시',level='SUB'),Component(name='대상 예시',level='TARGET'),Component(name='상위 예시',level='SUPER')]
    state.solve.ariz=ARIZRun(steps=[ARIZStep(step_code='1.3',step_title='모순',output='TC1: 고속 → 생산성 개선 + 진동 악화.'),
        ARIZStep(step_code='2.2',step_title='작용 시간',output='T1(갈등): 가공 중. T2(이전): 투입 전. T3(이후): 배출 후.')],
        solution_directions=['속도 조건별 분리로 진동을 줄인다.'],final_ideas=['기존 제어기를 이용한다.'])
    state.solve.trend_apps=[dict(trend_id='TR10',trend_name='열 번째',idea='두 번째'),dict(trend_id='TR2',trend_name='두 번째',idea='첫 번째')]
    state.scratch['s_curve']={'stage':'성숙기','note':'개념 판단'}
    state.solve.fos_apps=[dict(leading_area='항공 산업',transferred_feature='진동 절연',generalized_function='진동 전달 감소',adaptation_note='설비 크기에 맞춤')]
    state.report=ReportArtifact(narrative={'executive_summary':'유익한 개선과 유해한 악화를 검토한다.'})
    data=view(state)
    text=''.join(b.get('html','') for s in data['report_sections'] for b in s['blocks'])
    assert text.index('상위 예시')<text.index('대상 예시')<text.index('하위 예시')
    assert '해결 방향 및 실행 아이디어' in text and '항공 산업(진동 절연)' in text
    assert '해결 방향 1' not in text and '실행 아이디어 1' not in text
    assert '| 항목 | 분석 내용' not in text
    assert re.search(r'1\.3 모순</h5>\s*<table',text)
    assert text.index('TR2')<text.index('TR10')
    assert 'report-term' not in data['report_sections'][0]['blocks'][0]['html']
    figures={f['key']:f for f in data['figures']}
    assert 'ariz' not in figures and 'ariz-step-0' in figures and 'ariz-step-1' in figures
    assert '현재 · 성숙기' in figures['s-curve']['svg']
    assert 'diagram-divider' in figures['fos']['svg'] and '항공 산업' in figures['fos']['svg']
    assert 'diagram-edge' in figures['trends']['svg']
    assert figures['trends']['title'] == '시스템 진화 방향'
    assert 'TR 번호 순서' not in figures['trends']['svg']
    assert 'text-anchor="start"' not in figures['trends']['svg']


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
