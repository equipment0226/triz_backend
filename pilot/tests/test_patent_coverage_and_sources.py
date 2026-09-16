"""Missing review coverage, owner facts, cache reuse and document presentation."""
import copy
import logging
from io import BytesIO
import zipfile
import pytest
from pydantic import ValidationError
from test_patent_draft import patent,drafted,change
from patent_draft import coverage,forms
from patent_draft.domain import Facts,PatentError,digest
from patent_draft.sources import Kipris,SourceService,SecretQueryFilter,public_document
import httpx


@pytest.mark.parametrize('mutation',['missing','duplicate','hash','foreign'])
def test_review_cannot_claim_complete_coverage_with_missing_or_forged_targets(mutation):
    material={'claims':{'claims':[{'number':1,'text':'첫 청구항'},{'number':2,'text':'둘째 청구항'}]},
              'specification':{'sections':[{'id':'effects','text':'기술 효과'}],'abstract':'기술 요약'}}
    targets=coverage.targets(material,{'claims':'v-claims','specification':'v-spec'})
    checks=[{'target_id':t['target_id'],'content_hash':t['content_hash']} for t in targets]
    coverage.validate(checks,targets)
    if mutation=='missing':checks.pop()
    elif mutation=='duplicate':checks.append(checks[0])
    elif mutation=='hash':checks[-1]['content_hash']=digest('different abstract')
    else:checks[-1]['target_id']='foreign-version'
    with pytest.raises(PatentError,match='개별 검토'):
        coverage.validate(checks,targets)


def test_unknown_facts_do_not_become_not_applicable():
    for value in (None,True,False):
        facts=Facts.model_validate({'priority':value}).model_dump(exclude_unset=True)
        result=next(x for x in forms.requirements(facts) if x['id']=='priority')
        assert result['status']=={None:'NEEDS_FACTS',True:'REQUIRED',False:'NOT_APPLICABLE'}[value]
    with pytest.raises(ValidationError):Facts.model_validate({'priority':'false'})
    with pytest.raises(ValidationError):Facts.model_validate({'arbitrary_fact':True})


def test_fact_patch_retires_derived_drafts_without_erasing_originals(patent):
    s,*_=patent
    case=drafted(s)
    case=change(s,case,'answers',{'facts':{'priority':None}})
    # Owner facts are independently versioned and strict patch validation applies.
    before=case['artifacts']['facts']
    case=change(s,case,'patches',{'target_type':'facts','before_hash':digest({'priority':None}),
        'replacement':{'priority':True},'change_kind':'TECHNICAL','change_reason':'우선권 사실 확인','issue_ids':[]})
    patch=s.repo.records('owner',case['case_id'],'patch_proposal')[-1]
    case=change(s,case,'apply-patch',{'patch_id':patch['id']})
    assert s.material('owner',case)['facts']['priority'] is True
    assert not {'invention','claims','specification','drawings'} & case['artifacts'].keys()
    assert s.repo.record('owner',case['case_id'],before)['payload']=={'priority':None}


def test_linked_detail_reused_without_ann_search_or_second_kr_call(patent,monkeypatch):
    s,*_=patent
    calls=[]
    monkeypatch.setenv('KIPRIS_API_KEY','test-service-key-never-log')
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200,content=b'<response><resultCode>00</resultCode><applicationNumber>1020200000001</applicationNumber><inventionTitle>Cooling plate</inventionTitle></response>')
    source=SourceService(s.repo,Kipris(httpx.MockTransport(handler)))
    value=source.enrich('1020200000001','issue-1',['claims'])
    source.enrich('1020200000001','issue-2',['description'])
    from triz.tools import vector_patents
    monkeypatch.setattr(vector_patents,'search_batch',lambda *a,**k:pytest.fail('Cached linked document must precede ANN'))
    result=source.local(['cooling'],[{'application_number':'1020200000001'}])
    assert len(calls)==1 and result['cached_details'][0]['raw_sha256']==value['raw_sha256']
    assert result['status']=='PARTIAL' and result['fto_performed'] is False
    with pytest.raises(PatentError,match='공개 원문'):
        public_document({**value,'private_invention':'must not enter public cache'})


def test_service_key_is_redacted_before_http_log_handlers():
    secret='test-service-key-never-log'
    record=logging.LogRecord('httpx',logging.INFO,'',0,'GET %s',('https://plus.kipris.or.kr/api?ServiceKey='+secret+'&applicationNumber=1020200000001',),None)
    assert SecretQueryFilter().filter(record)
    assert secret not in record.getMessage() and 'REDACTED' in record.getMessage()


def test_filing_documents_show_readable_terms_and_owner_supplied_names(patent):
    s,*_=patent
    case=drafted(s);material=s.material('owner',case)
    original=copy.deepcopy(material)
    material['facts']={'applicant_name':'직접 입력 출원인','inventor_names':'직접 입력 발명자'}
    material['specification']['sections'][0]['heading']='internal_title'
    material['claims']['claims'][0]['text']='QUICK_WIN 개념, change_scale=PARAMETER, BIG_BET 구성.'
    blob,manifest=forms.render(case,material,'ANNOTATED',[],[])
    with zipfile.ZipFile(BytesIO(blob)) as z:
        application=z.read('text/14-application.md').decode()
        claims=z.read('text/15-specification-claims.md').decode()
        assert '직접 입력 출원인' in application and '시험용 출원인' not in application
        assert 'QUICK WIN' in claims and 'BIG BET' in claims and '변경 범위: 파라미터 조정' in claims
        assert not any(token in claims for token in ('QUICK_WIN','BIG_BET','change_scale=','internal_title'))
    assert manifest['editor_validation']=='NOT_RUN'
    assert s.material('owner',case)==original
