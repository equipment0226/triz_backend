"""n8n transports issued task IDs; MCP executes the exact persisted ticket."""
import json
import os
from datetime import timedelta
import httpx
from sqlalchemy import select
from .domain import PatentError
from .repository import tasks, cases


def ticket_for(service, task_id):
    with service.repo.engine.connect() as conn:
        row = conn.execute(select(tasks.c.body, cases.c.owner_id).join(cases, tasks.c.case_id == cases.c.case_id)
                           .where(tasks.c.task_id == task_id)).first()
    if not row:
        raise PatentError('NOT_FOUND', '작업을 찾을 수 없습니다.', 404)
    return row.owner_id, json.loads(row.body)['ticket']


async def execute_mcp(ticket):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    url, token = os.getenv('PATENT_MCP_URL'), os.getenv('PATENT_SERVICE_TOKEN')
    if not url or not token:
        raise PatentError('MCP_NOT_CONFIGURED', '특허 MCP 연결 설정이 필요합니다.', 503)
    async with httpx.AsyncClient(headers={'Authorization': 'Bearer ' + token},
                                 timeout=httpx.Timeout(3600, connect=30)) as client:
        async with streamable_http_client(url, http_client=client) as (read, write, _):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(hours=1)) as session:
                await session.initialize()
                result = await session.call_tool(ticket['tool_name'], {'ticket': ticket})
                if result.isError:
                    raise PatentError('MCP_EXECUTION_FAILED', '특허 MCP 작업 결과를 확인해야 합니다.', 503)
                return result.structuredContent or json.loads(next(c.text for c in result.content if c.type == 'text'))


def next_task(service, owner, case_id):
    with service.repo.engine.connect() as conn:
        case = service.repo.get(owner, case_id, conn)
        if case['execution_status'] not in ('QUEUED', 'RUNNING'):
            return None
        return conn.execute(select(tasks.c.task_id).where(tasks.c.case_id == case_id, tasks.c.status == 'QUEUED')
                            .order_by(tasks.c.task_id)).scalar()


async def execute_stage(service, task_id):
    owner, ticket = ticket_for(service, task_id)
    result = await execute_mcp(ticket)
    following = next_task(service, owner, ticket['case_id']) if result.get('status') in ('COMPLETED', 'STALE') else None
    case = service.repo.get(owner, ticket['case_id'])
    return {'task_id': following, 'node_id': node_for(service, following) if following else None,
            'gate_id': {'APPLICATION_CONTEXT':'G0','QUESTIONS':'G1','EVIDENCE_CLARIFICATION':case.get('evidence_gate','G1'),'PATCH_REVIEW':'G2','OPEN_ISSUES':'G2','FINAL_REVIEW':'G3'}.get(case.get('waiting_for')),
            'continue_execution': bool(following), 'result': result}


def node_for(service, task_id):
    with service.repo.engine.connect() as conn:
        raw = conn.execute(select(tasks.c.body).where(tasks.c.task_id == task_id)).scalar()
    body = json.loads(raw) if raw else {}
    if body.get('node_id'):
        return body['node_id']
    from .workflow import load_contract
    ticket = body.get('ticket', {})
    return next((n['id'] for n in load_contract()['nodes'] if n['tool'] == ticket.get('tool_name')
                 and n.get('review_role') == ticket.get('review_role')), None)


def dispatch_task(task_id, node_id=None):
    url, token = os.getenv('PATENT_N8N_WEBHOOK_URL'), os.getenv('PATENT_SERVICE_TOKEN')
    if not url or not token:
        raise PatentError('N8N_NOT_CONFIGURED', '특허 n8n 연결 설정이 필요합니다.', 503)
    response = httpx.post(url, json={'task_id': task_id, 'node_id': node_id}, headers={'Authorization': 'Bearer ' + token}, timeout=30)
    response.raise_for_status()
