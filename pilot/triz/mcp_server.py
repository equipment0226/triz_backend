"""TRIZ MCP service. TRIZ_MCP_MODULE isolates prompt groups into separate deployments."""
import os
import secrets
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from . import agent, knowledge, pipeline, prompts_registry as P, store
from .context import RunContext
from .settings import settings

module = os.getenv("TRIZ_MCP_MODULE", "all")
mcp = FastMCP(f"TRIZ {module}", host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8001")), stateless_http=True, json_response=True)

@mcp.tool()
def triz_execute_stage(run_id: str, stage_index: int, epoch: int) -> dict:
    """Execute one checkpointed stage; stop at user questions. Retry with the same stage and epoch."""
    return pipeline.execute_stage(run_id, stage_index, epoch)

@mcp.tool()
def triz_query_matrix(improving: int, worsening: int) -> dict:
    """Deterministic lookup of the original 39x39 matrix; never infer missing entries."""
    if not 1 <= improving <= 39 or not 1 <= worsening <= 39:
        raise ValueError("Engineering parameter IDs must be between 1 and 39")
    ids, source = knowledge.lookup_matrix(improving, worsening)
    return {"principle_ids": ids, "source": source}

@mcp.tool()
def triz_get_engineering_parameters(keyword: str = "", number: int = 0) -> list[dict]:
    """Search the 39 engineering parameters by number or keyword."""
    return [dict(p, id=int(key)) for key, p in knowledge.params().items() if (not number or int(key) == number)
            and keyword.lower() in str(p).lower()]

@mcp.tool()
def triz_get_inventive_principles(keyword: str = "", number: int = 0) -> list[dict]:
    """Search the 40 inventive principles by number or keyword."""
    return [dict(p, id=int(key)) for key, p in knowledge.principles().items() if (not number or int(key) == number)
            and keyword.lower() in str(p).lower()]

@mcp.tool()
def triz_search_evidence(query: str, kind: str = "PATENT", limit: int = 4) -> list[dict]:
    """Retrieve actual patent or paper records; unavailable providers return no evidence."""
    from .tools.scholar import search_kind
    return search_kind(query, kind, max(1, min(limit, 8)))

@mcp.tool()
def triz_parse_attachment(run_id: str, attachment_id: str) -> dict:
    """Re-extract a stored attachment with provenance; does not accept arbitrary paths."""
    from .tools import docparse
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        item = next((a for a in state.intake.attachments if a.id == attachment_id), None) if state else None
        if not item or not item.storage_path:
            raise ValueError("Stored attachment not found")
        root = (settings.storage_dir / "uploads").resolve()
        path = (root / item.storage_path).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Invalid attachment path")
        item.extracted_text, item.extracted_facts = docparse.extract(path, item.filename)
        store.save_state(state)
        return {"filename": item.filename, "facts": item.extracted_facts}

@mcp.tool()
def triz_verify_artifact(run_id: str, rubric_id: str, artifact: dict, facts: str = "") -> dict:
    """Independently audit an artifact and archive model usage and verdict."""
    if not settings.rubric(rubric_id):
        raise ValueError("Unknown rubric")
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state:
            raise ValueError("Unknown run")
        result = agent.verify_artifact(RunContext(state), rubric_id, artifact, facts)
        store.save_state(state)
        return result

@mcp.tool()
def triz_render_report(run_id: str) -> dict:
    """Render the stored report and figures without another model call."""
    from . import render
    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state or not state.report:
            raise ValueError("Report is not ready")
        markdown = render.render_report(state, state.report.narrative)
        state.report.markdown = markdown
        render.save(state, markdown)
        store.save_state(state)
        return {"markdown": markdown, "report_url": f"/api/runs/{run_id}/report?format=html"}

def register_prompt(prompt_id):
    node = prompt_id.removeprefix("P_").lower()
    required = sorted(set(P.VAR.findall(P.raw(prompt_id))))
    def invoke(run_id: str, variables: dict) -> dict:
        missing = [key for key in required if key not in variables]
        if missing:
            raise ValueError("Missing template inputs: " + ", ".join(missing))
        with store.run_lock(run_id):
            state = store.load_state(run_id)
            if not state:
                raise ValueError("Unknown run")
            result = agent.run_agent(RunContext(state), node=node, label=node.replace("_", " "),
                stage=state.control.current_stage, agent_id=f"mcp::{node}", prompt_id=prompt_id,
                vars=variables, tier=agent.routed_tier(node), default={})
            store.save_state(state)
            return {"artifact": result, "run_id": run_id}
    mcp.add_tool(invoke, name=f"triz_{node}", description=(
        f"Execute the existing {prompt_id} TRIZ module. Required variables: {', '.join(required)}. "
        "Archives input/output and cost; returns artifact without advancing the workflow."))

for prompt_id in P.list_prompts():
    if prompt_id.startswith(("P_S", "P_EVIDENCE")) or prompt_id == "P_PERSONA_FACTORY":
        if module == "all" or prompt_id.lower() == f"p_{module.lower()}" or prompt_id.lower().startswith(f"p_{module.lower()}_"):
            register_prompt(prompt_id)

@mcp.resource("triz://workflow")
def workflow() -> str:
    import json
    return json.dumps(pipeline.stage_list(), ensure_ascii=False)

@mcp.prompt()
def triz(problem: str) -> str:
    """Start a guided TRIZ consultation from an engineering problem."""
    return f"TRIZ 문제: {problem}\n산업·난이도 확인 → 시스템·기능 분석 → 모순 → 해결안 → 검증 순서로 진행한다. 사용자 확인을 건너뛰지 않는다."

class ServiceAuth:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            header = dict(scope["headers"]).get(b"authorization", b"").decode()
            if not settings.service_token or not secrets.compare_digest(header, f"Bearer {settings.service_token}"):
                await JSONResponse({"detail": "Unauthorized"}, status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)

app = ServiceAuth(mcp.streamable_http_app())

if __name__ == "__main__":
    import uvicorn
    if os.getenv("MCP_TRANSPORT", "streamable-http") == "stdio":
        mcp.run(transport="stdio")
    else:
        uvicorn.run(app, host=os.getenv("MCP_HOST", "127.0.0.1"), port=int(os.getenv("MCP_PORT", "8001")))
