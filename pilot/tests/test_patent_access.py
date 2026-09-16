"""Closed beta authorization uses a real, unexpired stored account/session."""
import hashlib,time
import pytest
from sqlalchemy import insert,update
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_patent_draft import patent,opened,change,answered,authorize
from patent_draft.domain import PatentError


@pytest.fixture
def client(patent,monkeypatch):
    s,_,engine,_=patent
    from triz import store
    import patent_draft.api as api
    monkeypatch.setattr(api,'service',lambda:s)
    with engine.begin() as c:
        c.execute(insert(store.accounts).values(user_id='other',email='other@example.com',name='Other',created_at=store._now()))
        for token,owner,expiry in [('tester-session','owner',time.time()+100),('other-session','other',time.time()+100),('expired-session','owner',time.time()-1)]:
            c.execute(insert(store.sessions).values(token_hash=hashlib.sha256(token.encode()).hexdigest(),user_id=owner,expires_at=expiry))
    app=FastAPI();app.include_router(api.router);app.add_exception_handler(PatentError,api.error_handler)
    with TestClient(app) as c:yield c,s,engine


@pytest.mark.parametrize('token,expected',[('tester-session',200),('other-session',403),('expired-session',401),('',401)])
def test_only_existing_tester_account_can_read_or_discover_drafts(client,token,expected):
    c,s,_=client
    case,_=opened(s)
    for path in ('/cases','/source-solutions','/capabilities','/cases/'+case['case_id'],'/cases/'+case['case_id']+'/questions'):
        response=c.get('/api/patent'+path,headers={'x-triz-session':token,'x-triz-email':'equipment0226@gmail.com','x-triz-user-id':'owner'})
        assert response.status_code==expected
        if expected!=200:
            assert response.json()['detail']=='준비 중 입니다.'
            assert case['title'] not in response.text


def test_disabled_feature_and_direct_mutation_cannot_bypass_closed_test(client,monkeypatch):
    c,s,_=client
    case,_=opened(s)
    with pytest.raises(PatentError,match='준비 중'):
        s.open('other',{},'forged')
    response=c.post('/api/patent/cases/'+case['case_id']+'/resume',headers={'x-triz-session':'other-session'},
        json={'expected_revision':case['revision'],'expected_epoch':case['epoch'],'input_snapshot_id':case['snapshot_id'],'payload':{}})
    assert response.status_code==403
    monkeypatch.setenv('PATENT_ENABLED','false')
    response=c.get('/api/patent/cases',headers={'x-triz-session':'tester-session'})
    assert response.status_code==503 and response.json()['detail']=='준비 중 입니다.'


def test_allowance_is_rechecked_before_worker_executes_issued_work(client):
    _,s,engine=client
    from triz import store
    from patent_draft.repository import tasks
    from sqlalchemy import select
    import json
    case,_=opened(s)
    case=change(s,authorize(s,answered(s,case)),'start')
    with engine.begin() as c:
        ticket=json.loads(c.execute(select(tasks.c.body)).scalar())['ticket']
        c.execute(update(store.accounts).where(store.accounts.c.user_id=='owner').values(email='other@example.com'))
    with pytest.raises(PatentError,match='준비 중'):
        s.execute('owner',ticket)
    assert not s.gateway.calls
