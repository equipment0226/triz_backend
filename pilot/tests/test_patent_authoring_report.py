"""Structured stage lineage, keyword DB history, coherence Gate and real report bytes."""
import copy
import json
from io import BytesIO
import pytest
from sqlalchemy import select
from pypdf import PdfReader
from docx import Document
from fastapi import FastAPI
from fastapi.testclient import TestClient
from patent_draft.domain import PatentError
from patent_draft.repository import keywords, assets, tasks
from patent_draft.authoring import validate_result
from test_patent_draft import patent, change, drain
from test_patent_workflow import prepared


def test_citation_catalog_supplies_exact_nested_and_escaped_coordinates():
    from patent_draft.authoring import evidence_catalog,validate_basis
    context={'source':{'concept':{'steps':[{'a/b~c':'출구 유량을 독립적으로 제어한다.'}],'long':'원문'*2000}},
             'application_context':{'APPLICATION_CHANGES':'변경 없음','confirmed_by':'private-owner'}}
    catalog=evidence_catalog(context)
    assert any(ref['pointer']=='/concept/steps/0/a~1b~0c' for ref in catalog)
    assert all(ref['excerpt']!='private-owner' for ref in catalog)
    for ref in catalog:validate_basis(ref,context)
    assert len(evidence_catalog(context,limit=1))==1


def test_rejected_citation_is_auditable_but_never_accepted_as_artifact(patent):
    s,gateway,*_=patent
    generate=gateway.generate
    def fabricated(*args):
        value=generate(*args)
        if args[-1]['title']=='SynthesizedSolution':
            assert args[2]['evidence_catalog']
            value['value']['facts'][0]['basis'][0]['excerpt']='fabricated evidence'
        return value
    gateway.generate=fabricated
    case=drain(s,prepared(s))
    assert case['last_error'] is None and case['waiting_for']=='EVIDENCE_CLARIFICATION'
    assert 'synthesized_solution' not in case['artifacts']
    rejected=s.repo.records('owner',case['case_id'],'authoring_rejection')
    assert len(rejected)==1 and rejected[0]['candidate']['facts'][0]['basis'][0]['excerpt']=='fabricated evidence'


def test_structured_inputs_and_keyword_history_survive_revisions(patent):
    s,gateway,*_=patent
    case=drain(s,prepared(s))
    material=s.material('owner',case)
    first=case['artifacts']['drafting_keywords']
    first_source=case['artifacts']['synthesized_solution']
    with s.repo.engine.connect() as conn:
        rows=conn.execute(select(keywords).where(keywords.c.case_id==case['case_id'])).mappings().all()
        calls=[json.loads(r) for r in conn.execute(select(tasks.c.body)).scalars()]
    assert rows[0]['version_id']==first and rows[0]['source_version_id']==first_source
    assert json.loads(rows[0]['body'])['fact_ids']==['SF1']
    spec_call=next(c for c in calls if c['ticket']['tool_name']=='patent_draft_specification')
    assert first in spec_call['ticket']['read_version_ids']
    assert first_source in spec_call['ticket']['read_version_ids']
    assert spec_call['prompt_hash'] and spec_call['workflow_hash']
    assert case['artifacts']['workflow_contract'] not in spec_call['ticket']['read_version_ids']
    spec_parent=s.repo.record('owner',case['case_id'],case['artifacts']['specification'])
    assert first in spec_parent['parent_version_ids']
    case=change(s,case,'answers',{'answers':{'APPLICATION_CHANGES':'배관 구조를 변경해 두 루프를 직렬 연결'}})
    assert 'report' not in case['artifacts'] and 'drafting_keywords' not in case['artifacts']
    case=drain(s,case)
    assert case['artifacts']['drafting_keywords']!=first
    with s.repo.engine.connect() as conn:
        assert len(conn.execute(select(keywords)).all())==2
    assert s.repo.record('owner',case['case_id'],first)['payload']==material['drafting_keywords']


def test_synthesis_conflict_blocks_before_keywords_then_rechecks_answers(patent):
    s,gateway,*_=patent
    generate=gateway.generate
    def conflict(model,instruction,context,schema):
        result=generate(model,instruction,context,schema)
        if schema['title']=='SynthesizedSolution' and not context.get('answers',{}).get('SYN_CONFLICT'):
            result['value']['issues']=[{'id':'I1','description':'제약과 보완 조건 충돌','resolution':'','status':'OPEN',
                                       'blocking':True,'question_id':'SYN_CONFLICT'}]
            result['value']['questions']=[{'id':'SYN_CONFLICT','question':'어떤 제약을 유지하나요?',
                'reason':'기술 조건 충돌','affected_fields':['invention'],'blocking':True}]
        return result
    gateway.generate=conflict
    case=drain(s,prepared(s))
    assert case['waiting_for']=='QUESTIONS'
    assert 'drafting_keywords' not in case['artifacts']
    case=change(s,case,'answers',{'answers':{'SYN_CONFLICT':'시설수 온도 제약을 유지'}})
    case=drain(s,case)
    assert case['waiting_for']=='FINAL_REVIEW'


def test_fabricated_keyword_links_and_citations_are_rejected(patent):
    s,*_=patent
    case=drain(s,prepared(s));material=s.material('owner',case)
    value=copy.deepcopy(material['drafting_keywords']);value['keywords'][0]['fact_ids']=['NONEXISTENT']
    with pytest.raises(PatentError,match='키워드'):
        validate_result('drafting_keywords',value,material)
    synthesis=copy.deepcopy(material['synthesized_solution']);synthesis['facts'][0]['basis'][0]['excerpt']='invented excerpt'
    with pytest.raises(PatentError,match='근거'):
        validate_result('synthesized_solution',synthesis,material)


def test_coherence_failure_does_not_reach_final_gate_but_draft_report_is_available(patent):
    s,gateway,*_=patent
    generate=gateway.generate
    def fail_flow(*args):
        result=generate(*args)
        if args[-1]['title']=='DocumentCoherence':
            result['value']['checks'][0].update(outcome='FAIL',explanation='문제와 해결 수단의 연결이 없음',repair_instruction='해결 수단 문단에 연결 관계를 설명')
        return result
    gateway.generate=fail_flow
    case=drain(s,prepared(s))
    assert case['waiting_for']=='PATCH_REVIEW'
    assert 'report' in case['artifacts']
    assert not s.approvals('owner',case)
    reconciliation=next(ctx for _,ctx in gateway.calls if 'issues' in ctx)
    assert any(i['rule_id']=='DOCUMENT_COHERENCE' for i in reconciliation['issues'])


def test_saved_word_pdf_are_one_document_with_korean_and_drawings(patent,tmp_path):
    s,*_=patent
    case=drain(s,prepared(s));material=s.material('owner',case);report=material['report']
    files={}
    with s.repo.engine.connect() as conn:
        for fmt in ('docx','pdf'):
            files[fmt]=conn.execute(select(assets.c.content).where(assets.c.asset_id==report['files'][fmt]['asset_id'])).scalar()
    assert files['pdf'].startswith(b'%PDF-')
    pdf=PdfReader(BytesIO(files['pdf']));pdf_text='\n'.join(p.extract_text() for p in pdf.pages)
    word=Document(BytesIO(files['docx']));word_text='\n'.join(p.text for p in word.paragraphs)
    for content in ('GPU 냉각 루프 분리','과제의 해결 수단','청구항 1','요약서','냉각판을 포함하는 냉각장치.'):
        assert content in pdf_text and content in word_text
    assert len(word.inline_shapes)==1
    assert all(section['text'] in word_text for section in report['sections'])
    for fmt,data in files.items():(tmp_path/('report.'+fmt)).write_bytes(data)


def test_direct_report_download_and_keyword_history_enforce_owner_acl(patent,monkeypatch):
    from patent_draft import api
    s,*_=patent;case=drain(s,prepared(s));owner=['owner']
    monkeypatch.setattr(api,'service',lambda:s)
    app=FastAPI();app.include_router(api.router);app.add_exception_handler(PatentError,api.error_handler)
    app.dependency_overrides[api.principal]=lambda:owner[0]
    client=TestClient(app)
    prefix='/api/patent/cases/'+case['case_id']
    result=client.get(prefix+'/report/pdf')
    assert result.status_code==200 and result.headers['content-type']=='application/pdf'
    assert 'attachment' in result.headers['content-disposition'] and '.pdf' in result.headers['content-disposition']
    assert client.get(prefix+'/report/docx').headers['content-type'].endswith('wordprocessingml.document')
    assert client.get(prefix+'/keywords').json()['items'][0]['current']
    owner[0]='other'
    assert client.get(prefix+'/report/pdf').status_code==404
    assert client.get(prefix+'/keywords').status_code==404


def test_existing_guided_draft_can_save_report_without_losing_reviews(patent):
    from test_patent_draft import drafted
    s,*_=patent
    case=drafted(s)
    reviews=s.current_reviews('owner',case)
    approvals=s.approvals('owner',case)
    before_status=case['document_status']
    case=change(s,case,'reports')
    assert s.material('owner',case)['report']['files']['pdf']
    assert s.current_reviews('owner',case)==reviews
    assert s.approvals('owner',case)==approvals
    assert case['document_status']==before_status
