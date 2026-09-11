from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pytest

from triz import knowledge as K, visuals, nodes, agent, digest, verify
from triz.standard_diagrams import validate_specs, render_standard
from triz.schema import SuFieldModel, ReportArtifact, GlobalState


def test_all_76_reference_diagrams_match_frontend_assets_and_report_numbers(state):
    catalog=K.standards()
    specs=validate_specs(catalog)
    assert len(specs)==76
    rendered=[]
    root=Path(__file__).resolve().parents[2]
    for entry in catalog:
        code=entry['code']
        svg=render_standard(entry,specs[code])
        xml=ET.fromstring(svg)
        assert xml.get('data-standard-code')==code
        asset_directory=root/'frontend/public/diagrams/standards'
        if asset_directory.exists():  # The standalone backend repo has no frontend.
            assert (asset_directory/(code+'.svg')).read_text(encoding='utf-8')==svg
        assert all(float(e.get('font-size'))>=11 for e in xml.iter() if e.get('font-size'))
        assert len([e for e in xml.iter() if e.get('data-phase')])==2
        rendered.append(svg)
    assert len(set(rendered))==76
    # Reverse order prevents an index-based lookup from passing accidentally.
    state.solve.standard_apps=[dict(standard_code=e['code'],standard_title='잘못된 모델 제목',idea='적용안') for e in reversed(catalog)]
    before=state.model_dump_json()
    result=visuals.figures(state)
    figures={f['key']:f for f in result}
    for i,entry in enumerate(reversed(catalog)):
        figure=figures[f'standard-{i}']
        assert figure['svg']==render_standard(entry)
        assert entry['title_ko'] in figure['title']
    assert before==state.model_dump_json()
    # Reports must reference every figure in their content, not just create SVGs.
    from triz.presentation import view
    state.report=ReportArtifact()
    sections=view(state)['report_sections']
    actual=[b['figure']['key'] for section in sections for b in section['blocks'] if b.get('type')=='figure']
    assert len([k for k in actual if k.startswith('standard-')])==76


def test_standard_diagrams_represent_distinct_mechanisms_not_only_changed_titles():
    specs=validate_specs(K.standards())
    protective=specs['1.2.3']['after']
    assert [(e['source'],e['target']) for e in protective['edges']]==[('F','S2')]
    assert 'S1' in {n['id'] for n in protective['nodes']}
    assert specs['1.1.2']['after']['nodes'][1]['kind']=='composite'
    assert specs['1.1.3']['after']['nodes'][1]['kind']=='layer'
    assert specs['2.4.2']['after']['nodes'][1]['kind']=='particles'
    assert specs['2.4.3']['after']['nodes'][1]['kind']=='fluid'
    assert '전기장' in specs['2.4.12']['after']['title']
    assert {n['id'] for n in specs['5.4.2']['after']['nodes']}=={'E','C','I','R'}
    assert specs['5.4.1']['after']['edges'][0]['style']=='both'
    assert specs['4.5.2']['after']['nodes'][-1]['label'].endswith('d²x/dt²')


def test_structured_model_keeps_prime_fields_directions_and_split_substances(state):
    source=SuFieldModel(s1='대상',s2='도구',field='기존 장')
    state.analysis.su_fields=[source]
    model=dict(nodes=[dict(id='S1a',label='대상 일부'),dict(id='S1b',label='대상의 다른 부분'),dict(id='F',label='기존 장'),dict(id="F'",label='추가 제어 장')],
        edges=[dict(source="F'",target='S1a',label='제어'),dict(source='S1a',target='S1b',label='상호작용'),dict(source='S1b',target='S1a',label='반작용')])
    ns,es,note=visuals.standard_model(state,dict(source_su_id=source.id,resulting_model=model))
    assert {n[0] for n in ns}=={'S1a','S1b','F','F′'}
    assert {e[:2] for e in es}=={('F′','S1a'),('S1a','S1b'),('S1b','S1a')}
    broken=dict(nodes=model['nodes'],edges=[dict(source='F99',target='S1a')])
    assert verify.check_standards({'applications':[dict(standard_code='5.1.2',resulting_model=broken)]})
    _,edges,note=visuals.standard_model(state,dict(source_su_id=source.id,resulting_model=broken))
    assert not edges and '검증 실패' in note


def test_legacy_arrows_and_field_paths_are_not_reversed_or_invented(state):
    _,es,_=visuals.standard_model(state,dict(resulting_su_field='S1(대상) ← S3(중간층) ← F(장) + F′(독립 장)'))
    assert {e[:2] for e in es}=={('S3','S1'),('F','S3')}
    _,es,_=visuals.standard_model(state,dict(resulting_su_field='S1a(부분 A) ↔ S1b(부분 B)'))
    assert {e[:2] for e in es}=={('S1a','S1b'),('S1b','S1a')}


@pytest.mark.parametrize('code',['2.4.12','4.5.2','5.4.2','5.5.3'])
def test_later_standards_are_retrievable_by_the_actual_problem(code):
    item=next(e for e in K.standards() if e['code']==code)
    assert code in [e['code'] for e in K.candidate_standards('COMPLETE','USEFUL_INSUFFICIENT',required_functions=[item['title_ko'],item['transformation']])]


def test_catalog_binding_reaches_next_stage_and_report_references(state,monkeypatch):
    standard=next(e for e in K.standards() if e['code']=='5.4.2')
    state.analysis.su_fields=[SuFieldModel(s1='대상',s2='장치',field='전기')]
    monkeypatch.setattr(K,'candidate_standards',lambda *a,**k:[standard])
    monkeypatch.setattr(agent,'run_agent',lambda *a,**k:{'applications':[
        dict(standard_code='5.4.2',standard_title='잘못된 이름',idea='저장 에너지 해제',conditions=['오동작 시험']),
        dict(standard_code='9.9.9',idea='존재하지 않는 표준해')]})
    nodes._track_c(SimpleNamespace(state=state))
    assert len(state.solve.standard_apps)==1 and state.solve.gaps
    app=state.solve.standard_apps[0]
    assert app['standard_title']==standard['title_ko']
    assert app['source_su_id']==state.analysis.su_fields[0].id
    assert standard['conditions'] in state.solve.raw_ideas[0].conditions
    packet=digest.idea_packet(state.solve.raw_ideas[0])
    assert packet['support']['catalog_transformation']==standard['transformation']
    assert packet['support']['catalog_limitations']==standard['limitations']
    restored=GlobalState.model_validate_json(state.model_dump_json())
    assert digest.idea_packet(restored.solve.raw_ideas[0])==packet
    assert any('5.4.2' in p['ref'] for p in nodes._applied_principles(restored))
