import json
from pathlib import Path
from collections import Counter
from types import SimpleNamespace

import pytest

from triz import knowledge
from triz.effect_catalog import select_effects, format_effects
from triz.effect_mining import validate_output, prepare_documents, export_catalog, mine


def test_canonical_76_standard_numbers_and_semantics():
    standards=knowledge.standards()
    expected={(f'{prefix}.{i}') for prefix,size in [('1.1',8),('1.2',5),('2.1',2),('2.2',6),('2.3',3),('2.4',12),('3.1',5),('3.2',1),('4.1',3),('4.2',4),('4.3',3),('4.4',5),('4.5',2),('5.1',4),('5.2',3),('5.3',5),('5.4',2),('5.5',3)] for i in range(1,size+1)}
    assert len(standards)==76
    assert {s['code'] for s in standards}==expected
    assert Counter(s['code'][0] for s in standards)=={'1':13,'2':23,'3':6,'4':17,'5':17}
    by_code={s['code']:s for s in standards}
    assert '초과분' in by_code['1.1.6']['description']
    assert '다른 물질' in by_code['1.1.7']['description']
    assert '주파수' in by_code['2.3.2']['description']
    assert '상호 작용' in by_code['5.1.2']['description'] or '서로 작용' in by_code['5.1.2']['description']
    for s in standards:
        assert s['conditions'] and s['limitations'] and s['sources']
        assert s['verification_scope']


def test_global_effect_retrieval_finds_late_mechanism_and_keeps_source_conditions():
    unrelated={'name':'마찰','domain':'PHYSICAL','principle':'마찰 계수 제어','conditions':'접촉면'}
    target={'id':'FX-HEAT','name':'열관','name_en':'heat pipe','aliases':['capillary condensation'],
            'domain':'PHYSICAL','principle':'증발과 응축에 의한 열 전달','conditions':'냉각부와 심지가 필요',
            'limitations':'모세관 한계와 건조','sources':[{'identifier':'NASA-1','url':'https://nasa.gov/reference','retrieval_scope':'abstract'}]}
    groups=[{'function_ko':'기타','effects':[unrelated]*100},{'function_ko':'열 이동','effects':[target]}]
    picked=select_effects(groups,['heat pipe capillary'],limit=1)
    assert picked[0]['id']=='FX-HEAT'
    block=format_effects(picked,2,101,76)
    for text in ['NASA-1','냉각부와 심지','모세관 한계','abstract','FX-HEAT']:
        assert text in block


def extraction():
    return {'effects':[{'name':'모세관 이동','name_en':'capillary transport','mechanism_key':'capillary-transport','aliases':['모세관'],
        'function_ko':'유체를 이동·분배한다','domain':'PHYSICAL','principle':'젖음성에 의한 압력차로 이동한다.',
        'conditions':'젖는 표면','limitations':'높이와 점성 손실','inputs':['액체'],'outputs':['이동'],'parameters':['반경'],
        'applications':['심지'],'design_notes':'설계 검토 제안: 높이를 측정한다.',
        'source_support':[{'id':'D000001','span':'capillary pressure drives the liquid'}]}],
        'reviews':[{'id':'D000001','status':'EXTRACTED','reason':''}]}


def source():
    return {'identifier':'paper-1','source_type':'PAPER','title':'Transport','url':'https://example.org/paper',
            'snippet':'The capillary pressure drives the liquid through the porous wick.', 'retrieval_scope':'stored_search_excerpt'}


def test_extraction_rejects_fabricated_citations_and_reports_unreviewed_sources():
    docs=prepare_documents([source()])
    good=validate_output(extraction(),docs)
    assert len(good['effects'])==1
    invented=extraction(); invented['effects'][0]['source_support'][0]['span']='unobserved infinite energy generation'
    result=validate_output(invented,docs)
    assert not result['effects'] and result['reviews'][0]['status']=='NO_MECHANISM'
    missing=extraction(); missing['reviews']=[]
    with pytest.raises(ValueError,match='INCOMPLETE_SOURCE_REVIEW'):
        validate_output(missing,docs)
    foreign=extraction(); foreign['effects'][0]['source_support'][0]['id']='foreign'
    assert not validate_output(foreign,docs)['effects']


def test_mining_is_resumable_and_export_keeps_canonical_sources(tmp_path):
    calls=[]
    def fake(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data=extraction(),tokens_in=100,tokens_out=50,cost_usd=.01,model='fixture')
    result=mine([source()],tmp_path,llm_call=fake,emit=lambda _:None)
    assert not result['failed_batches'] and len(calls)==1
    result=mine([source()],tmp_path,llm_call=fake,emit=lambda _:None)
    assert len(calls)==1
    catalog=export_catalog(result,[])
    effect=catalog[0]['effects'][0]
    assert effect['sources'][0]['url']==source()['url']
    assert effect['sources'][0]['retrieval_scope']=='stored_search_excerpt'
    assert effect['evidence_level']=='문헌 발췌 기반 · 실증 별도 확인'
    assert len(export_catalog(result,catalog)[0]['effects'])==1


def test_atomic_catalog_updates_are_visible_without_restart(tmp_path,monkeypatch):
    monkeypatch.setattr(knowledge,'KDIR',tmp_path)
    p=tmp_path/'effects.json'
    p.write_text('[{"function_ko":"a","effects":[]}]',encoding='utf-8')
    assert knowledge.effects()[0]['function_ko']=='a'
    p.write_text('[{"function_ko":"updated-function","effects":[]}]',encoding='utf-8')
    assert knowledge.effects()[0]['function_ko']=='updated-function'


def test_compact_editorial_catalog_and_agent_references_agree():
    groups=knowledge.effects()
    entries=[e for g in groups for e in g['effects']]
    assert len({e['id'] for e in entries})==len(entries)
    assert len({e['name'] for e in entries})==len(entries)
    assert all(set(e)=={'id','name','domain','principle','conditions'} for e in entries)
    assert all(e['conditions'] and len(e['principle'])<=160 for e in entries)
    esc=next(e for e in entries if e['id']=='1.4')
    assert esc['name']=='정전기척(ESC)' and '밀착' in esc['principle']
    esc_group=next(g for g in groups if esc in g['effects'])
    assert '비접촉' not in esc_group['function_ko']
    assert any(e['domain']=='INFORMATIONAL' for e in entries)
    candidate=knowledge.effect_candidates(['electrostatic chuck ESC'],limit=1)[0]
    assert candidate['id']=='1.4' and candidate['sources']
    assert candidate['principle']==esc['principle']


def test_source_registry_keeps_ids_and_abstracts_when_a_new_snapshot_is_reordered():
    a=source(); b=dict(source(),identifier='paper-2',title='Second')
    first=prepare_documents([a,b])
    third=dict(source(),identifier='paper-3',title='Third')
    next_snapshot=prepare_documents([third,b,a],first)
    assert [(d['id'],d['source']['identifier']) for d in next_snapshot]==[
        ('D000001','paper-1'),('D000002','paper-2'),('D000003','paper-3')]
    abstract=dict(a,abstract='Complete stored abstract with extra scientific information.',retrieval_scope='stored_patent_abstract')
    enriched=prepare_documents([abstract],first)
    again=prepare_documents([a],enriched)
    assert again[0]['body']==abstract['abstract']


def test_agent_cannot_relabel_a_catalog_id_or_supply_its_own_sources(state,monkeypatch):
    from triz import agent,nodes
    item=next(e for e in knowledge.effect_candidates(['ESC'],limit=6) if e['id']=='1.4')
    monkeypatch.setattr(knowledge,'effect_candidates',lambda *a,**k:[item])
    monkeypatch.setattr(agent,'run_agent',lambda *a,**k:{'applications':[{
        'source_effect_id':'1.4','effect_name':'허구의 자기부상','effect_domain':'BIOLOGICAL',
        'principle':'임의의 원리','title':'고정','idea':'웨이퍼 고정',
        'catalog_sources':[{'url':'https://example.org/invented'}]}]})
    nodes._track_h(SimpleNamespace(state=state))
    applied=state.solve.effect_apps[-1]
    assert applied['effect_name']==item['name']
    assert applied['principle']==item['principle']
    assert applied['catalog_conditions']==item['conditions']
    assert applied['catalog_sources']==item['sources']
    assert item['conditions'] in state.solve.raw_ideas[-1].conditions
    from triz.digest import idea_packet
    packet=idea_packet(state.solve.raw_ideas[-1])
    assert packet['support']['source_effect_id']=='1.4'
    assert packet['support']['catalog_sources']==item['sources']
    assert packet['support']['catalog_conditions']==item['conditions']
