"""Nineteen typed MCP tools sharing the API governor, reducer and ACL."""
from contextvars import ContextVar
import json
import os
import secrets
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from .domain import Bootstrap, ReadRequest, TaskTicket, PatentError
from .runtime import service
from .repository import cases
from .service import OPERATIONS
from .access import require_tester

principal = ContextVar('patent_mcp_principal', default=None)
authorized_service = ContextVar('patent_mcp_service', default=False)
mcp = FastMCP('TRIZ Patent Draft', stateless_http=True, json_response=True,
    instructions='Private patent drafts. Only issued task tickets may execute work. All verdicts remain subject to the deterministic governor.')


def owner_required():
    owner = principal.get()
    if not owner:
        raise PatentError('AUTH_REQUIRED', 'Owner session is required', 401)
    return require_tester(service().legacy,owner)


@mcp.tool()
def patent_open_case(request: Bootstrap, idempotency_key: str) -> dict:
    """Create a private case from the owner's pinned solution; no model charge."""
    return service().open(owner_required(), request.model_dump(), idempotency_key)


@mcp.tool()
def patent_get_context(request: ReadRequest) -> dict:
    """Read only explicitly requested versions from an authorized pinned snapshot."""
    owner = owner_required()
    s = service()
    snapshot = s.repo.record(owner, request.case_id, request.snapshot_id)
    if snapshot['kind'] != 'snapshot' or not set(request.requested_artifact_ids) <= set(snapshot['members'].values()):
        raise PatentError('READSET_INVALID', 'Requested versions are outside the snapshot', 403)
    return {'snapshot': snapshot, 'artifacts': [s.repo.record(owner, request.case_id, v) for v in request.requested_artifact_ids]}


def handler(name):
    def execute(ticket: TaskTicket) -> dict:
        """Execute a server-issued ticket; ownership, role, tier, readset and reservation are checked."""
        if not authorized_service.get():
            raise PatentError('AUTH_REQUIRED', 'Authenticated MCP service is required', 401)
        if ticket.tool_name != name:
            raise PatentError('TASK_TICKET_INVALID', 'Ticket names a different tool', 403)
        s = service()
        owner = principal.get()
        if owner is None:
            with s.repo.engine.connect() as c:
                owner = c.execute(select(cases.c.owner_id).where(cases.c.case_id == ticket.case_id)).scalar()
        if owner is None:
            raise PatentError('NOT_FOUND', 'Case not found', 404)
        require_tester(s.legacy,owner)
        return s.execute(owner, ticket.model_dump())
    execute.__name__ = name
    return execute


for name in OPERATIONS:
    mcp.add_tool(handler(name), name=name,
        description=f'{name}: {OPERATIONS[name][0]} execution; exact issued ticket required; no legacy mutation or review downgrade.')


class AuthenticatedMCP:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope['headers']}
        token = os.getenv('PATENT_SERVICE_TOKEN', '')
        allowed = bool(token and secrets.compare_digest(headers.get('authorization',''), 'Bearer '+token))
        if not allowed:
            await send({'type':'http.response.start','status':401,'headers':[(b'content-type', b'application/json')]})
            await send({'type':'http.response.body','body':b'{"error":"Unauthorized"}'})
            return
        owner = service().legacy.principal(headers.get('x-triz-session',''))
        a, b = principal.set(owner), authorized_service.set(True)
        try:
            await self.app(scope, receive, send)
        finally:
            principal.reset(a)
            authorized_service.reset(b)


app = AuthenticatedMCP(mcp.streamable_http_app())
