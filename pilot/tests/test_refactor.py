import asyncio
import json
import threading
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from triz import agent, domain, evidence, llm, pipeline, render, store, visuals
from triz.context import AbortRun, HumanInterrupt, RunContext
from triz.schema import ConceptSpec, ConstraintCheckResult, GlobalState, SuFieldModel
from triz.settings import settings

def test_industry_routes_and_quantum_is_not_forced():
    p = domain.classify("반도체 웨이퍼 식각 패턴 손상")
    assert p["industry_id"] == "semiconductor" and p["difficulty"] == "frontier"
    assert "화학공학" in p["disciplines"]
    assert domain.classify("database latency cache inconsistency")["industry_id"] == "software"
    assert domain.classify("일반 생활 문제")["difficulty"] == "routine"

def test_deep_dive_human_confirmation(state, monkeypatch):
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: {"questions":[{"question":"패턴 치수?"}],"unknowns":["계면 상태"]})
    ctx = RunContext(state)
    with pytest.raises(HumanInterrupt) as exc:
        domain.deep_dive(ctx)
    assert exc.value.request.payload["deep_dive"]
    state.scratch["resume_payload"] = {"answers":["20nm"],"industry_id":"semiconductor","difficulty":"frontier"}
    domain.deep_dive(ctx)
    assert state.scratch["deep_dive"]["answers"] == ["20nm"]
    assert "20nm" in domain.context(state,"s3_function_model")

def test_blind_review_does_not_receive_generated_hypotheses(state):
    state.scratch["industry_profile"] = domain.classify(state.raw_query)
    state.scratch["deep_dive"] = {"confirmed_facts":["measurement"], "competing_hypotheses":["secret-triz-origin"]}
    assert "secret-triz-origin" not in domain.context(state, "s8_review")
    assert "measurement" in domain.context(state, "s8_review")

@pytest.mark.parametrize("node,tier", [("s3_function_model","T2"),("s4_contradictions","T2"),("s5_ariz_part1","T2"),("s6_concept","T2"),("s1_extract","T1"),("s8_review","T3")])
def test_tier_routing(node, tier):
    assert agent.routed_tier(node,"T3") == tier

def test_checkpoint_duplicate_and_stale_delivery(state,monkeypatch):
    calls=[]
    def first(ctx): calls.append("first")
    def second(ctx): raise HumanInterrupt("CLARIFY","측정값 확인",{"questions":[]})
    monkeypatch.setattr(pipeline,"PIPELINE",[("first","시작",first),("second","확인",second)])
    r=pipeline.execute_stage(state.run_id,0,0)
    assert r["stage_index"]==1 and r["continue_execution"]
    pipeline.execute_stage(state.run_id,0,0)
    assert calls==["first"]
    r=pipeline.execute_stage(state.run_id,1,0)
    assert r["status"]=="WAITING_HUMAN" and not r["continue_execution"]
    monkeypatch.setattr(pipeline,"start",lambda rid:None)
    assert pipeline.resume(state.run_id,{"answers":["20nm"]})
    assert not pipeline.execute_stage(state.run_id,1,0)["continue_execution"]
    assert store.load_state(state.run_id).scratch["execution_epoch"]==1

def test_stage_failure_stops_downstream(state,monkeypatch):
    def fail(ctx): raise ValueError("bad measurement")
    monkeypatch.setattr(pipeline,"PIPELINE",[("first","시작",fail)])
    r=pipeline.execute_stage(state.run_id,0,0)
    assert r["status"]=="FAILED" and r["stage_index"]==0

def test_concurrent_worker_cannot_mutate(state):
    errors=[]
    def other():
        try:
            with store.run_lock(state.run_id): pass
        except RuntimeError as e: errors.append(str(e))
    with store.run_lock(state.run_id):
        t=threading.Thread(target=other);t.start();t.join()
    assert errors==["Run is busy"]

def test_budget_stops_before_model_call(state,monkeypatch):
    state.cost.budget_usd=0
    call=Mock();monkeypatch.setattr(llm,"chat_json",call)
    with pytest.raises(AbortRun):
        agent.tracked_chat(RunContext(state),system="rules",user="problem",tier="T2")
    call.assert_not_called()

def test_success_cache_and_complete_input_archive(state,monkeypatch):
    call=Mock(return_value=llm.LLMResult(data={"title":"Test"},text='{"title":"Test"}',model="test",tokens_in=10,tokens_out=4,cost_usd=.001))
    monkeypatch.setattr(llm,"chat_json",call)
    ctx=RunContext(state)
    kwargs=dict(node="s0_bootstrap",label="plan",stage="S0",agent_id="planner",prompt_id="P_S0_BOOTSTRAP",vars={"raw_query":"full input","attachment_summaries":[]})
    agent.run_agent(ctx,**kwargs); agent.run_agent(ctx,**kwargs)
    assert call.call_count==1 and state.cost.total_usd==pytest.approx(.001)
    assert state.steps[-1].status=="SKIPPED"
    step=store.get_step(state.run_id,state.steps[0].step_id)
    assert "full input" in step["input_slice"]["user"]
    assert list((settings.storage_dir/"runs"/state.run_id).glob("call-*.json"))
    from sqlalchemy import select
    with store.engine.connect() as conn:
        saved=conn.execute(select(store.llm_calls.c.payload).where(store.llm_calls.c.run_id==state.run_id)).scalar()
    assert json.loads(saved)["request"]["user"]==step["input_slice"]["user"]

def test_verifier_failure_is_not_pass(state,monkeypatch):
    def fail(**kwargs): raise llm.LLMError("unavailable")
    monkeypatch.setattr(llm,"chat_json",fail)
    assert agent.verify_artifact(RunContext(state),"R4_CONTRA",{},"")["verdict"]=="UNVERIFIED"

def test_sufield_renders_all_present_substances_without_invented_s3(state):
    state.analysis.su_fields=[SuFieldModel(s1="wafer <script>",s2="brush",field="mechanical",effect="HARMFUL")]
    f=visuals.figures(state)[0]["svg"]
    assert "S1" in f and "S2" in f and "F ·" in f and "S3" not in f
    assert "<script>" not in f and "&lt;script&gt;" in f
    state.analysis.su_fields[0].s3="fluid"
    assert "S3" in visuals.figures(state)[0]["svg"]

def test_report_exports_are_portable(state):
    from triz.schema import ReportArtifact
    state.analysis.su_fields=[SuFieldModel(s1="wafer",s2="brush",field="mechanical")]
    state.concepts=[ConceptSpec(title="Hybrid",one_liner="Mechanism",validation_plan=[{"metric":"defects","experiment":"A/B"}])]
    md=render.render_report(state,{"executive_summary":"Summary"})
    state.report=ReportArtifact(markdown=md,narrative={"executive_summary":"Summary"})
    render.save(state,md)
    folder=settings.storage_dir/"runs"/state.run_id
    assert (folder/"report.html").exists() and (folder/"sufield-0.svg").exists()
    assert "<svg" in (folder/"report.html").read_text(encoding="utf-8")
    assert "{{" not in md

def test_patent_paper_providers_are_separate(monkeypatch):
    from triz.tools import scholar
    monkeypatch.setattr(scholar,"enabled_providers",lambda:["crossref"])
    spy=Mock(return_value=[]); monkeypatch.setattr(scholar,"search",spy)
    assert scholar.search_kind("pressure vibration","PATENT")==[]
    assert spy.call_args.args[2]==[]

def test_evidence_matching_requires_provenance_and_transfer(state,monkeypatch):
    c=ConceptSpec(title="Contact separation"); state.concepts=[c]
    state.scratch["evidence_candidates"]=[{"source_type":"PATENT","title":"Real patent","identifier":"US1234567","url":"https://patents.google.com/patent/US1234567","year":"2020","snippet":"contact separation","provider":"patentsview"}]
    monkeypatch.setattr(evidence,"discover",lambda ctx:None)
    monkeypatch.setattr(agent,"run_agent",lambda *a,**k:{"matches":[{"index":0,"concept_id":c.id,"confidence":.9,"mechanism_mapping":"same means","transfer_conditions":["vacuum compatibility"]}],"additions":[{"index":99,"title":"invented"}]})
    evidence.attach(RunContext(state))
    assert len(c.evidence_ids)==1 and c.maturity=="CONCEPT"
    assert state.evidence[0].provider=="patentsview"
    assert state.scratch["evidence_gaps"][0]["missing"]==["PAPER"]
    assert not state.scratch["patent_additions"]

def test_conditional_acceptance_preserves_uncertainty(state):
    from triz.nodes import s7_gate
    state.concepts=[ConceptSpec(title="Option")]
    cid=state.concepts[0].id
    state.constraint_checks=[ConstraintCheckResult(concept_id=cid,verdict="CONDITIONAL",requires_user_decision=True)]
    state.scratch["resume_payload"]={"decisions":{cid:"accept"}}
    s7_gate(RunContext(state))
    assert state.constraint_checks[0].verdict=="CONDITIONAL"

def test_api_upload_limits_and_product_view(state,monkeypatch):
    from api.main import app
    client=TestClient(app)
    assert client.post('/internal/execute',json=dict(run_id=state.run_id,stage_index=0,epoch=0)).status_code==401
    assert client.get('/api/runs/'+state.run_id+'/view').json()["guide"]
    assert client.post('/api/runs',data={'query':'test'},files={'files':('bad.exe',b'x','application/octet-stream')}).status_code==415
    monkeypatch.setattr(settings,"max_upload_bytes",10)
    assert client.post('/api/runs',data={'query':'test'},files={'files':('big.txt',b'xxxxxxxxxxx','text/plain')}).status_code==413

def test_deployed_api_requires_gateway_token(monkeypatch):
    from api.main import app
    monkeypatch.setattr(settings, "app_token", "gateway-test")
    client = TestClient(app)
    assert client.get('/healthz').json()['ok']
    assert client.get('/api/runs').status_code == 401
    assert client.get('/api/runs', headers={'X-TRIZ-APP-TOKEN':'gateway-test'}).status_code == 200
    assert client.post('/internal/execute', json=dict(run_id='none',stage_index=0,epoch=0)).status_code == 401

def test_railway_port_precedes_local_port(monkeypatch):
    from triz.settings import Settings
    monkeypatch.setenv('PORT', '9000')
    monkeypatch.setenv('APP_PORT', '8000')
    assert Settings().port == 9000

def test_xlsx_extraction_keeps_sheet_and_measurements(tmp_path):
    from openpyxl import Workbook
    from triz.tools.docparse import extract
    p=tmp_path/'measurements.xlsx'; book=Workbook();book.active.title='process'
    book.active.append(['pressure','20 MPa']);book.save(p)
    text,facts=extract(p)
    assert 'process 행1' in text and any('20 MPa' in f for f in facts)

def test_mcp_catalog_and_deterministic_knowledge():
    from triz.mcp_server import mcp, triz_get_engineering_parameters, triz_query_matrix
    tools=asyncio.run(mcp.list_tools())
    names={t.name for t in tools}
    assert {'triz_s3_function_model','triz_s3_sufield','triz_s4_contradictions','triz_s6_concept','triz_execute_stage'} <= names
    assert triz_get_engineering_parameters(number=9)[0]['id']==9
    with pytest.raises(ValueError):triz_query_matrix(0,40)

def test_mcp_stage_does_not_block_api_event_loop(monkeypatch):
    from triz.mcp_server import triz_execute_stage
    entered, release = threading.Event(), threading.Event()
    def slow_stage(*args):
        entered.set()
        assert release.wait(timeout=3), 'MCP blocked the event loop'
        return {'continue_execution':False}
    monkeypatch.setattr(pipeline, 'execute_stage', slow_stage)
    async def exercise():
        task = asyncio.create_task(triz_execute_stage('fixture',0,0))
        try:
            assert await asyncio.to_thread(entered.wait, 1)
            await asyncio.sleep(0)
        finally:
            release.set()
        assert not (await asyncio.wait_for(task,1))['continue_execution']
    asyncio.run(exercise())

def test_mysql_schema_compiles_with_large_text():
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects.mysql import dialect
    for t in store.metadata.sorted_tables:
        ddl=str(CreateTable(t).compile(dialect=dialect()))
        assert 'CREATE TABLE' in ddl
    assert 'LONGTEXT' in str(CreateTable(store.states).compile(dialect=dialect()))

def test_real_mcp_protocol_initialize_list_and_call():
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from triz.mcp_server import mcp, app
    async def exercise():
        async with mcp.session_manager.run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), headers={'Authorization':'Bearer offline-test-service'}) as client:
                async with streamable_http_client('http://127.0.0.1:8001/mcp', http_client=client) as (read,write,_):
                    async with ClientSession(read,write) as session:
                        await session.initialize()
                        result=await session.call_tool('triz_query_matrix',{'improving':9,'worsening':27})
                        assert not result.isError
                        payload=result.structuredContent or json.loads(result.content[0].text)
                        assert 'principle_ids' in payload
    asyncio.run(exercise())

def test_solution_tracks_run_concurrently_with_isolated_outputs(state,monkeypatch):
    from triz import nodes
    from triz.schema import RawIdea
    barrier=threading.Barrier(2)
    def track_a(ctx):
        ctx.state.solve.raw_ideas.append(RawIdea(title="matrix",track="A_MATRIX",novelty_class="NEW"))
        barrier.wait(timeout=3)
    def track_g(ctx):
        barrier.wait(timeout=3)
        assert not ctx.state.solve.raw_ideas
        ctx.state.solve.raw_ideas.append(RawIdea(title="transfer",track="G_FOS",novelty_class="CROSS_DOMAIN"))
    monkeypatch.setattr(nodes,"TRACK_FUNCS",{"A_MATRIX":track_a,"G_FOS":track_g})
    nodes._run_tracks(RunContext(state),["A_MATRIX","G_FOS"])
    assert [i.title for i in state.solve.raw_ideas]==["matrix","transfer"]
    assert state.solve.raw_ideas[0].novelty_class=="NEW"

def test_rerun_invalidates_downstream_report_and_ideas(state,monkeypatch):
    from triz.schema import RawIdea, ReportArtifact
    state.status="COMPLETED"
    state.solve.raw_ideas=[RawIdea(title="old idea")]
    state.concepts=[ConceptSpec(title="old concept")]
    state.report=ReportArtifact(markdown="old report")
    store.save_state(state)
    monkeypatch.setattr(pipeline,"start",lambda rid:None)
    assert pipeline.rerun_from(state.run_id,"s5_solve","New constraint")
    loaded=store.load_state(state.run_id)
    assert not loaded.solve.raw_ideas and not loaded.concepts and loaded.report is None
