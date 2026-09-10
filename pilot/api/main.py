"""TRIZ product API and optional colocated MCP service."""
from __future__ import annotations

import json
import queue
import uuid
import asyncio
import hashlib
import secrets
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Header, Depends, Request, Query
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from triz import events, llm, pipeline, rag, store
from triz.knowledge import principles, params
from triz.schema import Attachment
from triz.settings import settings
from triz.tools import docparse

async def monitor_interrupted_runs():
    while True:
        await asyncio.sleep(30)
        try:
            await asyncio.to_thread(pipeline.recover_orphans)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Execution recovery check failed')


@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(pipeline.recover_orphans)
    if settings.patent_search_provider == 'vector' and settings.qdrant_url:
        import threading
        from triz.tools.vector_patents import warmup
        threading.Thread(target=warmup, name='patent-model-warmup', daemon=True).start()
    monitor = asyncio.create_task(monitor_interrupted_runs())
    try:
        if settings.embed_mcp:
            from triz.mcp_server import mcp
            async with mcp.session_manager.run():
                yield
        else:
            yield
    finally:
        monitor.cancel()
        with suppress(asyncio.CancelledError):
            await monitor

app = FastAPI(title="TRIZ Studio", version="2.0.0", lifespan=lifespan)
WEB_DIR = settings.root.parent / "frontend" / "dist"

if settings.embed_mcp:
    from triz.mcp_server import app as mcp_app
    app.mount("/agent", mcp_app)

@app.middleware("http")
async def app_auth(request, call_next):
    if request.url.path.startswith("/api") and settings.app_token:
        supplied = request.headers.get("x-triz-app-token", "")
        if not secrets.compare_digest(supplied, settings.app_token):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    public_read = request.method in ("GET", "HEAD") and request.url.path.startswith("/api/public/")
    if request.url.path.startswith("/api") and settings.require_user_auth and not public_read:
        user = await asyncio.to_thread(store.session_user, request.headers.get("x-triz-session", ""))
        if not user:
            return JSONResponse({"detail": "Google 로그인 후 사용할 수 있습니다."}, status_code=401)
        request.state.user_id = user["id"]
        parts = request.url.path.strip("/").split("/")
        if len(parts) >= 3 and parts[:2] == ["api", "runs"]:
            owner = await asyncio.to_thread(store.run_owner, parts[2])
            if owner != user["id"]:
                return JSONResponse({"detail": "실행 기록이 없습니다."}, status_code=404)
        if request.url.path in ("/api/rag", "/api/health/llm"):
            return JSONResponse({"detail": "관리자 전용 기능입니다."}, status_code=403)
    return await call_next(request)

def gateway_auth(x_triz_app_token: str = Header(default="")):
    if not settings.app_token or not secrets.compare_digest(x_triz_app_token, settings.app_token):
        raise HTTPException(401, "Unauthorized")

class AccountBody(BaseModel):
    subject: str
    email: str
    name: str

@app.post("/internal/auth/sessions", dependencies=[Depends(gateway_auth)])
def register_account(body: AccountBody):
    if not body.subject or len(body.subject) > 255 or len(body.email) > 320 or len(body.name) > 500:
        raise HTTPException(422, "Invalid account")
    return store.create_session(body.subject, body.email, body.name)

@app.get("/internal/auth/session", dependencies=[Depends(gateway_auth)])
def account_session(x_triz_session: str = Header(default="")):
    return {"user": store.session_user(x_triz_session)}

@app.delete("/internal/auth/session", dependencies=[Depends(gateway_auth)])
def logout_account(x_triz_session: str = Header(default="")):
    store.revoke_session(x_triz_session)
    return {"ok": True}

@app.get("/healthz")
def readiness():
    from sqlalchemy import text
    with store.engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True, "version": "2.0.0"}

def service_auth(authorization: str = Header(default="")):
    if not settings.service_token or not secrets.compare_digest(authorization, f"Bearer {settings.service_token}"):
        raise HTTPException(401, "Unauthorized")

class StageBody(BaseModel):
    run_id: str
    stage_index: int
    epoch: int

@app.post("/internal/execute", dependencies=[Depends(service_auth)])
async def execute_mcp_stage(body: StageBody):
    from triz.mcp_client import execute_stage
    return await execute_stage(body.run_id, body.stage_index, body.epoch)


# ───────────────────────────────── 모델
class ResumeBody(BaseModel):
    payload: dict[str, Any] = {}


class RerunBody(BaseModel):
    stage: str
    instruction: str = ""


class InjectBody(BaseModel):
    node: str
    role_name: str
    instruction: str


class FeedbackBody(BaseModel):
    overall_rating: int = 0
    missing_perspective: str = ""
    would_reuse: Optional[bool] = None
    solution_feedback: list[dict[str, Any]] = []

# ───────────────────────────────── 상태/설정
@app.get("/api/health")
def health() -> dict:
    if settings.require_user_auth:
        return {"ok": True, "llm_configured": settings.llm_ready}
    return {
        "ok": True,
        "llm_configured": settings.llm_ready,
        "models": {t: c.model for t, c in settings.tiers.items()},
        "base_url": settings.tiers["T1"].base_url,
        "search_provider": settings.search_provider,
        "db": store.stats(),
        "rag": rag.stats(),
    }


@app.get("/api/health/llm")
def health_llm() -> dict:
    return llm.healthcheck()


@app.get("/api/config")
def get_config() -> dict:
    return {"triz": settings.triz, "stages": pipeline.stage_list(),
            "persona_groups": sorted(settings.personas.get("seeds", {}).keys())}


@app.get("/api/knowledge/{name}")
def knowledge(name: str) -> Any:
    if name == "principles":
        return principles()
    if name == "params":
        return params()
    raise HTTPException(404, "unknown knowledge set")


# ───────────────────────────────── 실행
@app.post("/api/runs")
async def create_run(
    request: Request,
    query: str = Form(...),
    mode: Optional[str] = Form(None),
    public_consent: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
) -> dict:
    if settings.require_user_auth and not public_consent:
        raise HTTPException(422, "무료 베타의 문제·분석·보고서 공개에 동의한 뒤 분석을 시작해 주세요.")
    if not settings.llm_ready:
        raise HTTPException(400, "LLM_API_KEY가 설정되지 않았습니다. pilot/.env를 확인하세요.")
    if not query.strip() or len(query) > 20000:
        raise HTTPException(422, "문제를 1~20,000자 이내로 입력해 주세요.")
    if mode and mode.upper() not in ("LITE", "FULL", "DEEP"):
        raise HTTPException(422, "분석 모드를 확인해 주세요.")
    if len(files) > 8:
        raise HTTPException(413, "첨부는 최대 8개입니다.")
    attachments: list[Attachment] = []
    updir = settings.storage_dir / "uploads"
    updir.mkdir(parents=True, exist_ok=True)
    for f in files or []:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in docparse.ALLOWED_EXT:
            raise HTTPException(415, "지원하지 않는 첨부 형식입니다.")
        safe = f"{uuid.uuid4().hex}{ext}"
        dest = updir / safe
        data = await f.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, "첨부 파일 크기 제한을 초과했습니다.")
        dest.write_bytes(data)
        try:
            text, facts = await asyncio.to_thread(docparse.extract, dest, f.filename)
        except Exception as exc:
            raise HTTPException(422, "첨부 내용을 읽을 수 없습니다. 파일 형식을 확인해 주세요.") from exc
        attachments.append(Attachment(filename=f.filename, mime=f.content_type or "",
                                      kind=docparse.kind_of(f.filename),
                                      extracted_text=text, extracted_facts=facts,
                                      storage_path=safe, sha256=hashlib.sha256(data).hexdigest()))
    state = pipeline.create_run(query, mode=mode, attachments=attachments, user_id=getattr(request.state, "user_id", "local"))
    if public_consent:
        store.publish_run(state.run_id, state.user_id)
    await asyncio.to_thread(pipeline.start, state.run_id)
    return {"run_id": state.run_id}


@app.get("/api/runs")
def list_runs(request: Request, page: int | None = Query(None, ge=1), search: str = Query('', max_length=200)):
    if page is not None:
        return store.runs_page(page, search, user_id=getattr(request.state, 'user_id', 'local'))
    return store.list_runs(user_id=getattr(request.state, "user_id", None))

@app.get('/api/notifications')
def notifications(request: Request):
    return store.pending_notifications(getattr(request.state, 'user_id', 'local'))

@app.get("/api/public/runs")
def public_runs(page: int | None = Query(None, ge=1), search: str = Query('', max_length=200)):
    """The beta's explicitly public, read-only case library; no account/session data."""
    if page is not None:
        return store.runs_page(page, search, public=True)
    fields = ('run_id', 'title', 'mode', 'industry', 'target_system', 'status', 'started_at')
    return [{key: row.get(key) for key in fields} for row in store.public_runs_list()]

@app.get("/api/public/runs/{run_id}/view")
def public_run_view(run_id: str):
    from triz.presentation import view
    if not store.is_published(run_id):
        raise HTTPException(404, "공개된 분석 사례가 없습니다.")
    state = store.load_state(run_id)
    if not state:
        raise HTTPException(404, "분석 사례가 없습니다.")
    data = view(state)
    data['pending'] = None
    return data

@app.get("/api/public/runs/{run_id}/report")
def public_report(run_id: str):
    if not store.is_published(run_id):
        raise HTTPException(404, "공개된 분석 사례가 없습니다.")
    return get_report(run_id, format='html')


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    state = store.load_state(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    return json.loads(state.model_dump_json())

@app.get("/api/runs/{run_id}/view")
def get_run_view(run_id: str):
    from triz.presentation import view
    state = store.load_state(run_id)
    if not state:
        raise HTTPException(404, "실행 기록이 없습니다.")
    return view(state)


@app.delete("/api/runs/{run_id}")
def delete_run(run_id: str) -> dict:
    store.delete_run(run_id)
    events.clear(run_id)
    return {"ok": True}


@app.get("/api/runs/{run_id}/events")
def stream_events(run_id: str) -> StreamingResponse:
    async def gen():
        cursor = 0
        while True:
            batch = await asyncio.to_thread(store.read_events, run_id, cursor)
            for ev in batch:
                cursor = ev["event_id"]
                yield f"id: {cursor}\ndata: {json.dumps(ev, ensure_ascii=False, default=str)}\n\n"
            if not batch:
                yield ": ping\n\n"
                await asyncio.sleep(2)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/runs/{run_id}/resume")
def resume(run_id: str, body: ResumeBody) -> dict:
    try:
        ok = pipeline.resume(run_id, body.payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"재개 실패: {exc}") from exc
    if not ok:
        raise HTTPException(400, "대기 중인 사용자 입력이 없습니다.")
    return {"ok": True}


@app.post("/api/runs/{run_id}/rerun")
def rerun(run_id: str, body: RerunBody) -> dict:
    try:
        ok = pipeline.rerun_from(run_id, body.stage, body.instruction)
    except Exception as exc:
        raise HTTPException(500, f"재실행 실패: {exc}") from exc
    if not ok:
        raise HTTPException(400, "재실행할 수 없습니다. 실행 기록이나 단계 이름을 확인하세요.")
    return {"ok": True}


@app.post("/api/runs/{run_id}/continue")
def continue_run(run_id: str) -> dict:
    try:
        ok = pipeline.continue_run(run_id)
    except Exception as exc:
        raise HTTPException(500, f"이어서 실행 실패: {exc}") from exc
    if not ok:
        raise HTTPException(400, "이어서 실행할 수 있는 상태가 아닙니다.")
    return {"ok": True}


@app.post("/api/runs/{run_id}/inject-agent")
def inject_agent(run_id: str, body: InjectBody) -> dict:
    try:
        ok = pipeline.inject_agent(run_id, body.node, body.role_name, body.instruction)
    except Exception as exc:
        raise HTTPException(500, f"전문가 투입 실패: {exc}") from exc
    if not ok:
        raise HTTPException(400, "에이전트를 투입할 수 없습니다.")
    return {"ok": True}


# ───────────────────────────────── 단계 조회
@app.get("/api/runs/{run_id}/steps")
def list_steps(run_id: str) -> list[dict]:
    return store.list_steps(run_id)


@app.get("/api/runs/{run_id}/steps/{step_id}")
def get_step(run_id: str, step_id: str) -> dict:
    step = store.get_step(run_id, step_id)
    if not step:
        raise HTTPException(404, "step not found")
    return step


@app.get("/api/runs/{run_id}/report")
def get_report(run_id: str, format: str = "md"):
    state = store.load_state(run_id)
    if not state or not state.report:
        raise HTTPException(404, "리포트가 아직 생성되지 않았습니다.")
    if format in ("html", "bundle"):
        from triz import render
        if format == "html":
            return HTMLResponse(render.render_html(state), headers={"Content-Disposition": 'attachment; filename="triz-report.html"'})
        from triz.report_style import report_state
        from triz.visuals import figures
        current = report_state(state)
        import io, zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr('report.html', render.render_html(current))
            z.writestr('report.md', render.render_report(current, current.report.narrative))
            for figure in figures(current):
                z.writestr(figure['key'] + '.svg', figure['svg'])
        return StreamingResponse(iter([buffer.getvalue()]), media_type="application/zip",
                                 headers={"Content-Disposition": 'attachment; filename="triz-report.zip"'})
    # Old reports receive the current presentation without rerunning inference.
    from triz import render
    from triz.report_style import report_state
    current = report_state(state)
    markdown = render.render_report(current, current.report.narrative)
    headers = {"Content-Disposition": f'attachment; filename="triz_report_{run_id}.md"'} if format == "file" else {}
    return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8", headers=headers)


@app.get("/api/runs/{run_id}/report/context")
def get_report_context(run_id: str) -> dict:
    """해결책 선택 · 피드백 보드가 쓰는 요약 데이터."""
    state = store.load_state(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    solutions = [
        {
            "concept_id": c.id, "title": c.title, "one_liner": c.one_liner,
            "description": c.description, "novelty_class": c.novelty_class,
            "expected_effect": c.expected_effect,
            "rank": next((e.rank for e in state.evaluation.evaluations
                          if e.concept_id == c.id), 0),
            "total_score": next((e.total_score for e in state.evaluation.evaluations
                                 if e.concept_id == c.id), 0),
            "quadrant": next((e.quadrant for e in state.evaluation.evaluations
                              if e.concept_id == c.id), ""),
            "verdict": (state.check_for(c.id).verdict if state.check_for(c.id) else ""),
            "quality_status": c.quality_status,
            "quality_issues": c.quality_issues,
            "resolution_argument": c.resolution_argument,
            "evidence": [{"title": ev.title or ev.claim, "url": ev.url,
                          "identifier": ev.identifier, "year": ev.year,
                          "source_type": ev.source_type}
                         for ev in state.evidence if ev.id in c.evidence_ids],
        }
        for c in state.concepts
    ]
    solutions.sort(key=lambda x: (x["rank"] or 999))
    return {"solutions": solutions}


@app.post("/api/runs/{run_id}/feedback")
def submit_feedback(run_id: str, body: FeedbackBody) -> dict:
    """완주 후에도 해결책을 골라 피드백을 보내 지식그래프에 반영한다."""
    state = store.load_state(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    if state.pending and state.pending.kind == "FEEDBACK" and pipeline.resume(run_id, body.model_dump()):
        return {"ok": True, "mode": "resumed"}
    if state.pending or state.status in ("RUNNING", "QUEUED"):
        raise HTTPException(409, "현재 분석을 마친 뒤 피드백을 남겨 주세요.")
    from triz import nodes

    with store.run_lock(run_id):
        state = store.load_state(run_id)
        if not state or state.pending or state.status in ("RUNNING", "QUEUED"):
            raise HTTPException(409, "현재 분석을 마친 뒤 피드백을 남겨 주세요.")
        written = nodes.record_feedback(state, body.model_dump())
        store.save_state(state)
    return {"ok": True, "mode": "post_run", "records": written}


@app.get("/api/rag")
def list_rag(collection: str = rag.COLLECTION) -> list[dict]:
    return store.rag_all(collection)


# ───────────────────────────────── 정적 파일
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host=settings.host, port=settings.port,
                reload=False, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
