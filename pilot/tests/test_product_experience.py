from types import SimpleNamespace
from fastapi.testclient import TestClient
from triz import store,pipeline
from triz.schema import HumanRequest

def test_paginated_library_and_notifications_enforce_owner_and_search(monkeypatch):
    from api.main import app
    from triz.settings import settings
    monkeypatch.setattr(settings,'app_token','fixture')
    monkeypatch.setattr(settings,'require_user_auth',True)
    account=store.create_session('pagination-owner','owner@test.invalid','Owner')
    other=store.create_session('pagination-other','other@test.invalid','Other')
    owner=account['user']['id']
    for i in range(23):
        state=pipeline.create_run('페이지 처리 검증',user_id=owner,mode=['LITE','FULL','DEEP'][i%3])
        state.scratch['title']=f'검색용 프로젝트 {i:02}'
        if i==22:
            state.status='WAITING_HUMAN';state.pending=HumanRequest(kind='CLARIFY',title='조건 확인',payload={})
        store.save_state(state)
        store.publish_run(state.run_id,owner)
    client=TestClient(app)
    headers={'X-TRIZ-APP-TOKEN':'fixture','X-TRIZ-SESSION':account['token']}
    a=client.get('/api/runs?page=1',headers=headers).json()
    b=client.get('/api/runs?page=2',headers=headers).json()
    assert len(a['items'])==20 and len(b['items'])==3 and a['total']==23
    assert not {r['run_id'] for r in a['items']}&{r['run_id'] for r in b['items']}
    assert client.get('/api/runs?page=2&search=프로젝트%2000',headers=headers).json()['total']==1
    public=client.get('/api/public/runs?page=1&search=검색용',headers={'X-TRIZ-APP-TOKEN':'fixture'}).json()
    assert public['total']==23 and all('mode' in r and 'user_id' not in r for r in public['items'])
    waiting=client.get('/api/notifications',headers=headers).json()
    assert len(waiting)==1 and waiting[0]['id']==state.pending.interrupt_id
    headers['X-TRIZ-SESSION']=other['token']
    assert client.get('/api/notifications',headers=headers).json()==[]
    assert client.get('/api/runs?page=1',headers=headers).json()['total']==0
    state.pending=None;state.status='RUNNING';store.save_state(state)
    assert store.pending_notifications(owner)==[]

def test_invalid_title_retries_and_preserves_input(state,monkeypatch):
    from triz import agent
    from triz.titles import ensure_title,valid_title
    from triz.context import RunContext
    original=state.raw_query
    calls=[]
    def response(*args,**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data={'title':'' if len(calls)==1 else '웨이퍼 세정력과 패턴 손상 개선'})
    monkeypatch.setattr(agent,'tracked_chat',response)
    title=ensure_title(RunContext(state),original[:40])
    assert title=='웨이퍼 세정력과 패턴 손상 개선' and len(calls)==2
    assert state.raw_query==original and valid_title(title,original)
    assert not valid_title('진동 데이터를 사용하고싶은데',original)

def test_title_fallback_is_bounded_without_cutting_raw_text(state,monkeypatch):
    from triz import agent
    from triz.titles import ensure_title
    from triz.context import RunContext
    monkeypatch.setattr(agent,'tracked_chat',lambda *a,**k:SimpleNamespace(data={}))
    state.domain.target_system='진동 데이터 수집 시스템'
    assert ensure_title(RunContext(state),'')=='진동 데이터 수집 시스템 개선 과제'
