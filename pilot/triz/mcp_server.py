"""TRIZ MCP service. TRIZ_MCP_MODULE isolates prompt groups into separate deployments."""
import os
import secrets
import asyncio
import re
from copy import deepcopy
from functools import wraps
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from . import agent, knowledge, pipeline, prompts_registry as P, store
from .context import RunContext
from .settings import settings

module = os.getenv("TRIZ_MCP_MODULE", "all")

def threaded(fn):
    """Keep API polling responsive while synchronous analysis or OCR is running."""
    @wraps(fn)
    async def invoke(*args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)
    return invoke

mcp = FastMCP(f"TRIZ {module}", host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8001")), stateless_http=True, json_response=True)

@mcp.tool()
@threaded
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
@threaded
def triz_search_evidence(query: str, kind: str = "PATENT", limit: int = 4) -> list[dict]:
    """Retrieve actual patent or paper records; unavailable providers return no evidence."""
    from .tools.scholar import search_kind
    return search_kind(query, kind, max(1, min(limit, 8)))

@mcp.tool()
@threaded
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
@threaded
def triz_verify_artifact(run_id: str, rubric_id: str, artifact: dict, facts: str = "") -> dict:
    """Independently audit an artifact and archive model usage and verdict."""
    if rubric_id == 'R5_B':
        with store.run_lock(run_id):
            state = store.load_state(run_id)
            if not state:
                raise ValueError("Unknown run")
            return _verify_separation_artifact(state, artifact, facts)
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
@threaded
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

def _sufield_hints(result):
    result = deepcopy(result)
    if isinstance(result, dict):
        for model in result.get('su_fields') or []:
            if isinstance(model, dict):
                model['standard_class_hint'] = knowledge.standard_hints(
                    model.get('completeness', 'COMPLETE'), model.get('effect', 'USEFUL_INSUFFICIENT'))
    return result


def _track_c_candidates(variables):
    """Accept explicit parent headers/code lists; never infer codes from prose."""
    body = variables['standards_block']
    if not isinstance(body, str):
        raise ValueError('standards_block must be text containing explicit parent codes, or empty for selection')
    if not body.strip():
        resources = variables['resources']
        return knowledge.candidate_standards(variables['completeness'], variables['effect'],
            required_functions=[str(variables[k] or '') for k in ('s1', 's2', 'field')] +
                ([str(r) for r in resources] if isinstance(resources, list) else [str(resources or '')]))
    # A bare comma/space-separated code list or standards_block's unindented
    # parent headers are unambiguous. Indented canonical detail lines are not IDs.
    if re.fullmatch(r'\s*\d+(?:\.\d+){2,}(?:[\s,]+\d+(?:\.\d+){2,})*\s*', body):
        codes = re.findall(r'\d+(?:\.\d+){2,}', body)
    else:
        codes = []
        for line in body.splitlines():
            if not line.strip() or line[0].isspace():
                continue
            match = re.match(r'^(\d+(?:\.\d+){2,})(?=\s|$)', line)
            if not match:
                raise ValueError('Ambiguous standards_block: use explicit parent-code headers or a code list')
            codes.append(match.group(1))
    by_code = {s['code']: s for s in knowledge.standards()}
    if not codes or any(code not in by_code for code in codes):
        raise ValueError('standards_block must select valid parent standard codes only')
    return [deepcopy(by_code[code]) for code in dict.fromkeys(codes)]


def _track_b_artifact(state, node, prompt_id, variables):
    """Direct Track B keeps its run's catalog, prompt and rubric in one profile."""
    from . import separation_contract as SC, verify
    from .context import AbortRun
    from .ax import enabled as ax_enabled
    from .execution_config import profile
    token = profile.set(state.scratch.get('ax_bundle') if ax_enabled(state) else None)
    try:
        catalog = SC.catalog_for(state)
        call_variables = dict(variables, separation_block=knowledge.separation_block(catalog=catalog))
        normalize = lambda data: SC.normalize(data, catalog=catalog)
        check = lambda data: verify.check_separation(data, catalog=catalog)
        result = agent.run_agent(RunContext(state), node=node, label=node.replace('_', ' '),
            stage=state.control.current_stage, agent_id=f'mcp::{node}', prompt_id=prompt_id,
            vars=call_variables, tier=agent.routed_tier(node), default={},
            normalizer=normalize, checker=check, rubric_id='R5_B')
        result = normalize(result)
        issues = check(result)
        if issues:
            raise AbortRun('; '.join(issues))
        return {'artifact': result, 'run_id': state.run_id}
    finally:
        try:
            store.save_state(state)
        finally:
            profile.reset(token)


def _verify_separation_artifact(state, artifact, facts):
    """A model verdict cannot waive the run-local Track B data contract."""
    from . import separation_contract as SC, verify
    from .ax import enabled as ax_enabled
    from .execution_config import profile
    token = profile.set(state.scratch.get('ax_bundle') if ax_enabled(state) else None)
    try:
        if not settings.rubric('R5_B'):
            raise ValueError('Unknown rubric')
        catalog = SC.catalog_for(state)
        normalized = SC.normalize(artifact, catalog=catalog)
        issues = verify.check_separation(normalized, catalog=catalog)
        if issues:
            return {'verdict': 'REJECT', 'score': 0.0, 'source': 'deterministic',
                    'fatal_flaws': issues, 'revision_instructions': issues}
        return agent.verify_artifact(RunContext(state), 'R5_B', normalized, facts)
    finally:
        try:
            store.save_state(state)
        finally:
            profile.reset(token)


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
            if prompt_id == 'P_S5_TRACK_B':
                return _track_b_artifact(state, node, prompt_id, variables)
            options = {}
            call_variables = variables
            if prompt_id == 'P_S3_SUFIELD':
                options['normalizer'] = _sufield_hints
            elif prompt_id == 'P_S5_TRACK_C':
                from .catalog_binding import bind_standard
                from .verify import check_standards
                candidates = _track_c_candidates(variables)
                if not candidates:
                    raise ValueError('No valid parent standards available for Track C')
                allowed = [s['code'] for s in candidates]
                call_variables = dict(variables, standards_block=knowledge.standards_block(candidates))
                options['normalizer'] = lambda data: bind_standard(data, candidates)
            result = agent.run_agent(RunContext(state), node=node, label=node.replace("_", " "),
                stage=state.control.current_stage, agent_id=f"mcp::{node}", prompt_id=prompt_id,
                vars=call_variables, tier=agent.routed_tier(node), default={}, **options)
            if prompt_id == 'P_S3_SUFIELD':
                result = _sufield_hints(result)
            elif prompt_id == 'P_S5_TRACK_C':
                result = bind_standard(result, candidates)
                # Validate after the existing single direct call: attaching a
                # checker to run_agent would add paid repair attempts here.
                issues = check_standards(result, allowed)
                if issues:
                    store.save_state(state)
                    raise ValueError('; '.join(issues))
            store.save_state(state)
            return {"artifact": result, "run_id": run_id}
    mcp.add_tool(threaded(invoke), name=f"triz_{node}", description=(
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
