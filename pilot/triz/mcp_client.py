"""A deterministic n8n-to-MCP bridge; no agent model is needed to select a stage."""
import json
from datetime import timedelta
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from .settings import settings

async def execute_stage(run_id, stage_index, epoch):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {settings.service_token}"},
            timeout=httpx.Timeout(3600, connect=30), follow_redirects=True) as client:
        async with streamable_http_client(settings.mcp_url, http_client=client) as (read, write, _):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(hours=1)) as session:
                await session.initialize()
                result = await session.call_tool("triz_execute_stage", dict(
                    run_id=run_id, stage_index=stage_index, epoch=epoch))
                if result.isError:
                    raise RuntimeError("MCP stage execution failed")
                if result.structuredContent:
                    return result.structuredContent
                return json.loads(next(c.text for c in result.content if c.type == "text"))
