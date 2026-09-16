"""Real HTTP MCP transport with isolated DB and a test-only model provider."""
from contextlib import asynccontextmanager
import importlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from patent_draft.repository import tasks
from patent_draft.service import OPERATIONS
from test_patent_draft import patent, opened, authorize, answered, change


@pytest.fixture
def mcp_client(patent,monkeypatch):
    s,*_=patent
    import patent_draft.mcp as transport
    # Each fixture is a fresh server process; MCP managers cannot restart in place.
    transport=importlib.reload(transport)
    monkeypatch.setenv('PATENT_SERVICE_TOKEN','mcp-test-only-token')
    monkeypatch.setattr(transport,'service',lambda:s)
    monkeypatch.setattr(s.legacy,'principal',lambda token:{'owner-test':'owner','other-test':'other'}.get(token))
    @asynccontextmanager
    async def lifespan(app):
        async with transport.mcp.session_manager.run():
            yield
    app=FastAPI(lifespan=lifespan)
    app.mount('/patent-agent',transport.app)
    with TestClient(app,base_url='http://localhost:8000') as client:
        yield client,s


def rpc(client,method,params=None,owner='owner-test',service=True):
    headers={'Accept':'application/json, text/event-stream','x-triz-session':owner}
    if service:
        headers['Authorization']='Bearer mcp-test-only-token'
    return client.post('/patent-agent/mcp',headers=headers,json={
        'jsonrpc':'2.0','id':1,'method':method,**({'params':params} if params is not None else {})})


def output(result):
    # Existing protocol clients receive JSON text; newer clients may also get
    # structuredContent. Neither requires upgrading the legacy MCP connection.
    return result.get('structuredContent') or json.loads(next(c['text'] for c in result['content'] if c['type']=='text'))


def test_real_tools_list_auth_and_schema(mcp_client):
    client,s=mcp_client
    assert rpc(client,'tools/list',service=False).status_code==401
    response=rpc(client,'tools/list')
    assert response.status_code==200,response.text
    tools=response.json()['result']['tools']
    assert {t['name'] for t in tools}==set(OPERATIONS)|{'patent_open_case','patent_get_context'}
    assert len(tools)==19
    for tool in tools:
        if tool['name'] in OPERATIONS:
            assert 'ticket' in tool['inputSchema']['properties']


def test_real_bootstrap_context_and_cross_owner_denial(mcp_client):
    client,s=mcp_client
    source=s.legacy.preview('owner','source','C1')
    args={'request':{'source_run_id':'source','concept_id':'C1','expected_source_hash':source['source_hash'],
        'purpose':'transport test','jurisdiction':'KR','profile':'KR_GENERAL'},'idempotency_key':'mcp-create'}
    result=rpc(client,'tools/call',{'name':'patent_open_case','arguments':args}).json()['result']
    assert not result.get('isError'),result
    case=output(result)
    assert case['visibility']=='PRIVATE'
    assert case['budget']['spent_micro_usd']==0
    read={'name':'patent_get_context','arguments':{'request':{
        'case_id':case['case_id'],'snapshot_id':case['snapshot_id'],
        'requested_artifact_ids':[case['artifacts']['application_questions']], 'purpose':'owner intake'}}}
    result=rpc(client,'tools/call',read).json()['result']
    assert not result.get('isError'),result
    assert len(output(result)['artifacts'][0]['payload']['questions'])==3
    other=rpc(client,'tools/call',read,owner='other-test').json()['result']
    assert other['isError']
    assert case['title'] not in json.dumps(other,ensure_ascii=False)


def test_real_task_call_uses_same_intake_governor_and_idempotent_charge(mcp_client):
    client,s=mcp_client
    case,_=opened(s)
    case=change(s,authorize(s,answered(s,case)),'start')
    with s.repo.engine.connect() as c:
        ticket=json.loads(c.execute(select(tasks.c.body)).scalar())['ticket']
    args={'name':'patent_extract_invention','arguments':{'ticket':ticket}}
    first=rpc(client,'tools/call',args).json()['result']
    assert not first.get('isError'),first
    assert output(first)['status']=='COMPLETED'
    repeated=rpc(client,'tools/call',args).json()['result']
    assert output(repeated)==output(first)
    assert len(s.gateway.calls)==1
    assert s.gateway.calls[0][1]['application_context']['confirmed_by']=='owner'
    assert s.repo.get('owner',case['case_id'])['budget']['spent_micro_usd']==300
    spoof={'name':'patent_final_review','arguments':{'ticket':{**ticket,'tier':'T3','tool_name':'patent_final_review','review_role':'GLOBAL_FINAL'}}}
    assert rpc(client,'tools/call',spoof).json()['result']['isError']


def test_issued_task_cannot_bypass_missing_intake(mcp_client):
    client,s=mcp_client
    case,_=opened(s)
    case=authorize(s,case)
    # Simulate an incorrect scheduler. The execution boundary must still reject it.
    with s.repo.engine.begin() as c:
        ticket=s.issue(c,case,'patent_extract_invention')['ticket']
        s.repo.save(c,case,case['revision'])
    result=rpc(client,'tools/call',{'name':'patent_extract_invention','arguments':{'ticket':ticket}}).json()['result']
    assert result['isError']
    assert not s.gateway.calls
    assert s.repo.get('owner',case['case_id'])['budget']['spent_micro_usd']==0
