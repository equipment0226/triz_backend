"""Sidecar contract tests. Fake reviews verify control flow, not legal accuracy."""
import copy
import hashlib
import json
from io import BytesIO
import zipfile
import pytest
from sqlalchemy import create_engine, insert, select, event, inspect
from fastapi import FastAPI
from fastapi.testclient import TestClient
from patent_draft.domain import PatentError, digest, PROFILE, ROLES
from patent_draft.repository import Repository, cases, tasks, TABLES
from patent_draft.legacy import LegacyReader
from patent_draft.models import Model, ModelProfile, reserve, settle, balance
from patent_draft.service import Service, OPERATIONS
from patent_draft import rules, forms
from patent_draft.intake import APPLICATION_QUESTIONS

INVENTION = {'title':'GPU 냉각 루프 분리','problem':'냉각수와 GPU 온도 상충',
    'features':[{'id':'F1','name':'냉각판','description':'GPU에서 열을 전달하는 냉각판','provenance':'DERIVED_PROPOSAL','source_ids':[]}],
    'effects':[{'id':'E1','description':'온도 제어','feature_ids':['F1'],'evidence_ids':[],'evidence_status':'HYPOTHESIS'}],
    'relations':[],'unknowns':['실측 열저항']}
CLAIMS = {'claims':[{'number':1,'text':'냉각판을 포함하는 냉각장치.','depends_on':[],'feature_ids':['F1'],'support_sections':['embodiments']}]}
DOCUMENT = {'title':'GPU 냉각 루프 분리','sections':[{'id':name,'heading':name,'text':'냉각판(F1)을 연결한다.',
    'feature_ids':['F1'],'source_ids':[],'omission_reason':None} for name in forms.SECTIONS],
    'abstract':'냉각판을 갖는 냉각 장치.','applicant':{'name':'시험용 출원인'},'inventors':[{'name':'시험 발명자'}]}
DRAWINGS = {'drawings':[{'number':1,'caption':'냉각판 구성','nodes':[{'id':'100','label':'냉각판','feature_id':'F1'}],
    'edges':[],'kind':'CONCEPT'}],'not_required_reason':None}
APPLICATION_ANSWERS = {'APPLICATION_CHANGES':'냉각판과 시설수 루프를 분리한다.',
    'APPLICATION_CONSTRAINTS':'시설수 입구 35°C, 기존 랙 배관을 유지해야 한다.',
    'APPLICATION_RISKS':'결로 및 유량 부족 위험이 있으며 실측 검증 전이다.'}


class FakeGateway:
    def __init__(self):
        self.calls=[]
        self.fail_role=None
        self.role_override=None
        self.questions=[]

    def generate(self, model, instruction, context, schema):
        self.calls.append((model.tier, copy.deepcopy(context)))
        kind=schema['title']
        outputs={'Invention':INVENTION,'Questions':{'questions':self.questions},'SearchPlan':{'queries':['GPU cooling plate'],'feature_ids':['F1'],'limitations':['abstract corpus']},
                 'ClaimChart':{'entries':[],'coverage_gaps':['fulltext needed']},'ClaimTree':CLAIMS,'DocumentAST':DOCUMENT,'DrawingSpec':DRAWINGS,
                 'Reconciliation':{'proposals':[],'questions':[],'unresolved_issue_ids':['test-issue']}}
        if kind=='Review':
            role=next(r for r in ROLES if 'Use role '+r+'.' in instruction)
            if role==self.fail_role:
                raise PatentError('PROVIDER_FAILURE','test provider failure',503)
            result={'role':self.role_override or role,'input_snapshot_id':context['snapshot_id'],
                'covered_artifact_ids':context['read_version_ids'],'summary':'TEST FIXTURE ONLY',
                'target_checks':[{'target_id':t['target_id'],'content_hash':t['content_hash'],'outcome':'PASS',
                    'explanation':'Test fixture only'} for t in context['review_targets']],
                'findings':[{'rule_id':r['rule_id'],'outcome':'PASS','severity':r['severity'],'explanation':'Test fixture; not semantic validation',
                    'evidence_ids':[context['artifact_versions']['invention']],
                    'affected_artifacts':[context['artifact_versions']['invention']],
                    'source_spans':[{'artifact_id':context['artifact_versions']['invention'],
                        'pointer':'/features/0/description','excerpt':context['invention']['features'][0]['description']}]}
                    for r in context['rule_obligations']]}
        else:
            result=outputs[kind]
        return {'value':copy.deepcopy(result),'usage':{'prompt_tokens':100,'completion_tokens':100},'cost_micro_usd':300}


class FakeSources:
    def local(self, queries, source_refs):
        return {'references':source_refs,'hits':[],'status':'PARTIAL','queries':queries,
                'diagnostics':[{'status':'PARTIAL','corpus_complete':False}], 'fulltext_coverage':'TITLE_ABSTRACT_ONLY','fto_performed':False}


@pytest.fixture
def patent(tmp_path,monkeypatch):
    from triz import store
    engine=create_engine('sqlite:///'+(tmp_path/'patent.db').as_posix(),connect_args={'check_same_thread':False})
    store.metadata.create_all(engine)
    state={'run_id':'source','raw_query':'GPU cooling','intake':{'frame':{'raw_query':'GPU cooling'}},
           'concepts':[{'id':'C1','title':'DLC solution','description':'Two cooling loops','evidence_ids':[]}],
           'evidence':[],'cost':{'budget_usd':5,'spent_usd':2.798},'report':{'html':'ORIGINAL'},'future_key':{'keep':[1,2]}}
    with engine.begin() as c:
        c.execute(insert(store.accounts).values(user_id='owner',email='equipment0226@gmail.com',name='Test owner',created_at=store._now()))
        c.execute(insert(store.runs).values(run_id='source',user_id='owner',title='DLC source'))
        c.execute(insert(store.states).values(run_id='source',state_json=json.dumps(state)))
        c.execute(insert(store.published_runs).values(run_id='source',consent_user_id='owner',basis='BETA'))
    repository=Repository(engine)
    legacy=LegacyReader(engine)
    before_schema=legacy.schema_fingerprint()
    repository.migrate()
    assert legacy.schema_fingerprint()==before_schema
    monkeypatch.setenv('PATENT_TEST_KEY','test-only')
    monkeypatch.setenv('PATENT_ENABLED','true')
    monkeypatch.setenv('PATENT_DISPATCH_ENABLED','true')
    profile=ModelProfile({t:Model(t,'test-reasoner' if t=='T3' else 'test-low','https://api.deepseek.com/v1',
        'PATENT_TEST_KEY','1','2',32768,8192,t=='T3') for t in ('T1','T2','T3')})
    gateway=FakeGateway()
    s=Service(repository,legacy,profile,gateway,FakeSources())
    yield s,gateway,engine,state
    engine.dispose()


def opened(s):
    source=s.legacy.preview('owner','source','C1')
    body={'source_run_id':'source','concept_id':'C1','expected_source_hash':source['source_hash'],
          'purpose':'test draft','jurisdiction':'KR','profile':'KR_GENERAL'}
    return s.open('owner',body,'create-once'),body


def mutation(case,payload=None):
    return {'expected_revision':case['revision'],'expected_epoch':case['epoch'],'input_snapshot_id':case['snapshot_id'],'payload':payload or {}}


def change(s,case,op,payload=None,key=None):
    return s.mutate('owner',case['case_id'],op,mutation(case,payload),key or f'{op}-{case["revision"]}')['case']


def authorize(s,case,cap=2_000_000):
    return change(s,case,'budget-authorizations',{'cap_micro_usd':cap,'allow_provider_transfer':True,
                  'purpose':'test drafting','retention_acknowledged':True})


def answered(s,case):
    return change(s,case,'answers',{'answers':APPLICATION_ANSWERS})


def drain(s,case,max_tasks=20):
    for _ in range(max_tasks):
        with s.repo.engine.connect() as c:
            raw=c.execute(select(tasks.c.body).where(tasks.c.case_id==case['case_id'],tasks.c.status=='QUEUED')).scalar()
        if not raw:
            return s.repo.get('owner',case['case_id'])
        s.execute('owner',json.loads(raw)['ticket'])
    raise AssertionError('unbounded workflow')


def drafted(s):
    case,_=opened(s)
    case=change(s,authorize(s,answered(s,case)),'start')
    case=drain(s,case)
    assert case['waiting_for']=='G1'
    material=s.material('owner',case)
    case=change(s,case,'approvals',{'approval_type':'G1','content_hash':digest(material['invention'])})
    case=drain(s,change(s,case,'resume'))
    assert case['waiting_for']=='G2'
    material=s.material('owner',case)
    case=change(s,case,'approvals',{'approval_type':'G2','content_hash':digest(material['claims'])})
    return drain(s,change(s,case,'resume'))


def test_source_immutable_private_bootstrap_and_replay(patent):
    s,gateway,engine,state=patent
    from triz import store
    writes=[]
    def trap(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().upper().startswith(('INSERT','UPDATE','DELETE','ALTER','DROP')):
            writes.append(statement)
            assert 'patent_draft_' in statement, statement
    event.listen(engine,'before_cursor_execute',trap)
    first,body=opened(s)
    assert s.open('owner',body,'create-once')==first
    assert first['visibility']=='PRIVATE' and not gateway.calls
    assert first['budget']['cap_micro_usd']==0
    assert s.material('owner',first)['source']['raw_publication']['published_run']['basis']=='BETA'
    with pytest.raises(PatentError,match='특허 초안'):
        s.repo.get('intruder',first['case_id'])
    with pytest.raises(PatentError) as error:
        s.open('owner',{**body,'purpose':'changed'},'create-once')
    assert error.value.code=='IDEMPOTENCY_CONFLICT'
    with engine.connect() as c:
        assert json.loads(c.execute(select(store.states.c.state_json)).scalar())==state
    assert writes


def test_version_and_role_spoof_blocked(patent):
    s,*_=patent
    case,_=opened(s)
    with pytest.raises(PatentError) as error:
        s.mutate('owner',case['case_id'],'pause',{**mutation(case),'expected_epoch':99},'bad')
    assert error.value.code=='VERSION_CONFLICT'
    case=change(s,authorize(s,answered(s,case)),'start')
    with s.repo.engine.connect() as c:
        ticket=json.loads(c.execute(select(tasks.c.body)).scalar())['ticket']
    with pytest.raises(PatentError) as error:
        s.execute('owner',{**ticket,'tier':'T3','review_role':'GLOBAL_FINAL'})
    assert error.value.code=='TASK_TICKET_INVALID'


def test_t3_reservation_before_any_generation(patent):
    s,gateway,*_=patent
    case,_=opened(s)
    case=change(s,authorize(s,answered(s,case),100),'start')
    assert case['execution_status']=='PAUSED_BUDGET' and not gateway.calls
    assert case['budget']['spent_micro_usd']==0


def test_mandatory_review_independence_and_global_coverage(patent):
    s,gateway,*_=patent
    case=drafted(s)
    reviews=s.current_reviews('owner',case)
    assert {r['role'] for r in reviews}==set(ROLES)
    assert all(r['tier']=='T3' for r in reviews)
    calls=[context for tier,context in gateway.calls if tier=='T3']
    assert 'independent_reviews' not in calls[0] and 'independent_reviews' not in calls[1]
    assert len(calls[2]['independent_reviews'])==2
    assert set(calls[2]['read_version_ids'])==set(case['artifacts'].values())
    assert case['editor_validation']=='NOT_RUN'


def test_t3_failure_preserves_unknown_cost_and_no_downgrade(patent):
    s,gateway,*_=patent
    gateway.fail_role='TECHNICAL_CONTENT'
    case=drafted(s)
    assert case['execution_status']=='PAUSED_DEPENDENCY'
    assert case['document_status']!='DRAFT_READY'
    assert case['budget']['uncertain_micro_usd']>0
    assert len([tier for tier,_ in gateway.calls if tier=='T3'])==1


def test_deterministic_package_notice_and_attachments(patent):
    s,*_=patent
    case=drafted(s)
    material=s.material('owner',case)
    a,manifest=forms.render(case,material,'ANNOTATED',[],[])
    b,manifest2=forms.render(case,material,'ANNOTATED',[],[])
    assert a==b and manifest==manifest2
    assert manifest['editor_validation']=='NOT_RUN'
    assert manifest['max_generated_images_per_case']==1
    with zipfile.ZipFile(BytesIO(a)) as z:
        assert all(any(n.startswith('editable/'+str(i)+'-') for n in z.namelist()) for i in range(14,18))
        assert forms.SAMPLE_IMAGE_NOTICE in z.read('text/17-drawings.md').decode()
        assert '<script' not in z.read('preview/15-specification-claims.html').decode()
        with zipfile.ZipFile(BytesIO(z.read('editable/17-drawings.docx'))) as word:
            assert forms.SAMPLE_IMAGE_NOTICE in word.read('word/document.xml').decode()


def test_new_schema_exact_allowlist(patent):
    s,_,engine,_=patent
    assert 'patent_documents' not in TABLES and 'patent_checkpoints' not in TABLES
    assert TABLES <= set(inspect(engine).get_table_names())


@pytest.mark.parametrize('rule_id',sorted(rules.RULES))
def test_rule_inventory_no_missing_handlers_or_blanket_pass(patent,rule_id):
    s,*_=patent
    case,_=opened(s)
    result={r['rule_id']:r for r in s.runtime_checks('owner',case,s.material('owner',case))}
    assert result[rule_id]['execution_status']!='ERROR',rule_id
    if rules.RULES[rule_id]['semantic_roles']:
        assert result[rule_id]['outcome']=='UNKNOWN'
        assert result[rule_id]['execution_status']=='NOT_RUN'


def test_api_acl_and_source_contract(patent,monkeypatch):
    s,*_=patent
    import patent_draft.api as api
    monkeypatch.setattr(api,'service',lambda:s)
    monkeypatch.setattr(s.legacy,'principal',lambda token: {'owner-token':'owner','other-token':'other'}.get(token))
    app=FastAPI()
    app.include_router(api.router)
    app.add_exception_handler(PatentError,api.error_handler)
    with TestClient(app) as c:
        assert c.get('/api/patent/cases').status_code==401
        headers={'x-triz-session':'owner-token','Idempotency-Key':'api-create'}
        source=c.get('/api/patent/source-runs/source/concepts/C1/preview',headers=headers).json()
        body={'source_run_id':'source','concept_id':'C1','expected_source_hash':source['source_hash'],
              'purpose':'test','jurisdiction':'KR','profile':'KR_GENERAL'}
        response=c.post('/api/patent/cases',headers=headers,json=body)
        assert response.status_code==201,response.text
        case=response.json()
        assert c.get('/api/patent/cases/'+case['case_id'],headers={'x-triz-session':'other-token'}).status_code==403
        assert c.post('/api/patent/cases',headers=headers,json={**body,'owner_id':'other'}).status_code==422
        assert c.get('/api/patent/cases/'+case['case_id']+'/events',headers=headers).headers['content-type'].startswith('text/event-stream')
