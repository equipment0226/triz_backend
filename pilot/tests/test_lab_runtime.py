"""Exercise native lab execution in fresh children, with no paid/network calls."""
import json
import os
from pathlib import Path
import subprocess
import sys

PILOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import json, os, socket, sys
from triz import lab_runtime as lab
original = lab._initialize

def initialize(root, budget):
    modules = original(root, budget)
    pipeline, store, ledger, engine = modules
    from triz import llm
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network call")
    socket.create_connection = no_network
    socket.socket.connect = no_network
    def fake_llm(**kwargs):
        return llm.LLMResult(data={"title":"Offline native pipeline", "lang":"en",
            "questions":[{"question":"Operating range?", "why_needed":"Boundary"}]},
            text='{"fixture":true}', tier=kwargs.get("tier", "T2"),
            model=kwargs["model_config"]["model"], tokens_in=11, tokens_out=7,
            cost_usd=.012, meta={"attempt":1})
    llm.chat_json = fake_llm
    fixture = os.environ.get("LAB_TEST_FIXTURE", "native")
    if fixture == "decide":
        from triz.context import HumanInterrupt
        def stage(ctx):
            payload = ctx.resume_payload()
            if payload is None:
                raise HumanInterrupt("DECIDE", "Keep or drop", {"conditional":[{"concept_id":"C-1"}]}, "S0")
            ctx.state.scratch["test_decisions"] = payload["decisions"]
        pipeline.PIPELINE[0] = (*pipeline.PIPELINE[0][:2], stage)
    elif fixture == "parallel":
        from concurrent.futures import ThreadPoolExecutor
        from sqlalchemy import select
        def stage(ctx):
            def write(number):
                # A nested connection lease must not roll back the enclosing
                # transaction, and every worker must share the same database.
                with ledger.transaction() as connection:
                    ledger._event(connection, ctx.state.run_id, "LAB_THREAD_FIXTURE", {"number":number})
                    with engine.connect() as nested:
                        assert nested is connection
                        assert nested.execute(select(ledger.heads.c.run_id)).scalar_one() == ctx.state.run_id
                    with engine.begin() as nested:
                        assert nested is connection
                        store.append_event(ctx.state.run_id, {"number":number})
            with ThreadPoolExecutor(max_workers=8) as workers:
                list(workers.map(write, range(40)))
            with engine.connect() as connection:
                assert connection.exec_driver_sql("PRAGMA database_list").all()[0][2] == ""
            ctx.state.scratch["thread_count"] = 40
        pipeline.PIPELINE[0] = (*pipeline.PIPELINE[0][:2], stage)
    elif fixture == "solutions":
        from triz.schema import ConceptSpec, ConstraintCheckResult
        from triz.ax.candidate_disposition import record
        def stage(ctx):
            good = ConceptSpec(id="C-KEEP", title="Retained", quality_status="PASS")
            bad = ConceptSpec(id="C-DROP", title="Rejected", quality_status="REJECT", quality_issues=["Fatal flaw"])
            ctx.state.concepts = [good, bad]
            ctx.state.constraint_checks = [ConstraintCheckResult(concept_id="C-KEEP", verdict="CONDITIONAL")]
            record(ctx.state, bad, "QUALITY_REJECT", ["Fatal flaw"])
            ctx.state.concepts = [good]
        pipeline.PIPELINE[0] = (*pipeline.PIPELINE[0][:2], stage)
    elif fixture == "unknown":
        def stage(ctx):
            ticket = ledger.acquire(ctx.state.run_id, 0, {"node":"offline-unknown", "request":{}}, 42000)
            ledger.settle(ticket, {"error":"Lost response"}, None, status="UNKNOWN")
            from triz.context import UsageUncertain
            raise UsageUncertain()
        pipeline.PIPELINE[0] = (*pipeline.PIPELINE[0][:2], stage)
    elif fixture == "failure":
        def stage(ctx):
            raise RuntimeError("fixture stage failure")
        pipeline.PIPELINE[0] = (*pipeline.PIPELINE[0][:2], stage)
    elif fixture == "intake-confirm":
        from triz import agent
        def agent_fixture(ctx, **kwargs):
            if kwargs["node"] == "s1_extract":
                return {"domain":{"industry":"Pumps", "target_system":"Feed pump"},
                    "frame":{"restated_problem":"Pump tradeoff", "symptom":"Pressure instability",
                             "confidence":.2, "missing_info":["Operating range"]},
                    "constraints":{"items":[]}}
            if kwargs["node"] == "s1_clarify":
                return {"questions":[{"question":"Operating range?", "why_needed":"Boundary"}]}
            if kwargs["node"] == "s2_candidates":
                return {"candidates":[{"id":"SYS-1", "name":"Feed pump"}], "confirm_question":"Correct pump?"}
            raise AssertionError("Unexpected fixture agent")
        agent.run_agent = agent_fixture
    return modules

lab._initialize = initialize
native_response = lab._response
def response(*args, **kwargs):
    result = native_response(*args, **kwargs)
    result["test_archive_names"] = [p.name for p in (args[6] / "storage").rglob("*") if p.is_file()]
    return result
lab._response = response
lab.main()
'''


def invoke(payload, *, fixture="native", env=None):
    child_env = dict(os.environ, PYTHONIOENCODING="utf-8", LAB_TEST_FIXTURE=fixture)
    if env:
        child_env.update(env)
    result = subprocess.run([sys.executable, "-c", CHILD], input=json.dumps(payload),
        cwd=PILOT, env=child_env, capture_output=True, encoding="utf-8", timeout=40)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output.get("continuation_payload"), result.stderr + str(output)
    return output


def begin(**kwargs):
    return invoke(dict(action="begin", raw_query="An offline engineering contradiction", mode="FULL", **kwargs))


def stage(previous, *, fixture="native", stage_key=None, human_response=None):
    payload = dict(action="stage", stage_key=stage_key or previous["next_stage_key"],
                   continuation_payload=previous["continuation_payload"])
    if human_response is not None:
        payload["human_response"] = human_response
    return invoke(payload, fixture=fixture)


def test_begin_is_model_free_and_native_axiom_journal_is_portable(tmp_path):
    canary = tmp_path / "production.db"
    canary.write_bytes(b"untouched production sentinel")
    storage = tmp_path / "production-storage"
    output = invoke(dict(action="begin", raw_query="offline query", mode="QUICK", budget_usd=5.0),
        env={"DATABASE_URL":"sqlite:///" + canary.as_posix(), "STORAGE_DIR":str(storage),
             "PATENT_DATABASE_URL":"mysql+pymysql://patent-read-only.invalid/patents",
             "LLM_API_KEY":"secret-canary-key"})
    assert canary.read_bytes() == b"untouched production sentinel"
    assert not storage.exists()
    assert output["next_stage_key"] == "s0_bootstrap"
    assert output["cost"]["request_count"] == 0
    assert output["budget"]["limit_microusd"] == 5_000_000
    state = output["continuation_payload"]["state"]
    bundle = state["scratch"]["ax_bundle"]
    assert bundle["run_contract"]["version"] == "ax-run-v3"
    assert bundle["config"]["feedback_rag"]["enabled"] is False
    assert state["scratch"]["training_consent"] == "NO_TRAINING"
    assert "secret-canary-key" not in json.dumps(output)
    assert len(output["continuation_payload"]["journal"]["ax_snapshots"]) == 1
    advanced = stage(output)
    assert advanced["next_stage_key"] == "s0_research"
    assert advanced["cost"]["request_count"] == 1
    assert advanced["budget"]["spent_microusd"] == 12_000
    assert advanced["budget"]["reserved_microusd"] == 0
    assert advanced["steps"][0]["prompt_id"] == "P_S0_BOOTSTRAP"
    assert not any(name.endswith(".json") for name in advanced["test_archive_names"])
    assert len(advanced["continuation_payload"]["journal"]["llm_calls"]) == 1


def test_native_research_gate_requires_current_manual_response_and_keeps_cost():
    planned = stage(begin())
    paused = stage(planned)
    assert paused["status"] == "WAITING_HUMAN"
    assert paused["pending"]["kind"] == "CLARIFY"
    assert paused["next_stage_key"] == "s0_research"
    assert paused["cost"]["request_count"] == 2
    unchanged = stage(paused)
    assert unchanged["continuation_payload"] == paused["continuation_payload"]
    wrong = stage(paused, human_response={"interrupt_id":"wrong", "skip":True})
    assert wrong["error"] and wrong["pending"] == paused["pending"]
    resumed = stage(paused, human_response={"interrupt_id":paused["pending"]["interrupt_id"], "skip":True})
    assert resumed["next_stage_key"] == "s1_intake"
    assert resumed["pending"] is None
    assert resumed["budget"]["spent_microusd"] == 24_000
    assert resumed["cost"]["request_count"] == 2
    assert resumed["continuation_payload"]["state"]["scratch"]["execution_epoch"] == 1


def test_wrong_stage_cannot_skip_a_native_stage():
    initial = begin()
    rejected = stage(initial, stage_key="s7_gate")
    assert rejected["error"]
    assert not rejected["continue_execution"]
    assert rejected["continuation_payload"] == initial["continuation_payload"]
    assert rejected["cost"]["request_count"] == 0


def test_native_decide_guard_rejects_missing_choices_before_epoch_change():
    paused = stage(begin(), fixture="decide")
    request = paused["pending"]["interrupt_id"]
    rejected = stage(paused, fixture="decide", human_response={"interrupt_id":request, "decisions":{}})
    assert rejected["error"]
    assert rejected["continuation_payload"] == paused["continuation_payload"]
    accepted = stage(paused, fixture="decide", human_response={"interrupt_id":request,
        "decisions":{"C-1":"accept"}, "training_consent":"PROJECT_ONLY"})
    state = accepted["continuation_payload"]["state"]
    assert state["scratch"]["test_decisions"] == {"C-1":"accept"}
    assert state["scratch"]["training_consent"] == "NO_TRAINING"
    assert not [row for row in accepted["continuation_payload"]["journal"]["ax_events"]
                if row["event_type"] == "COMMON_EVALUATION"]


def test_parallel_native_journal_transactions_share_memory_and_keep_nested_writes():
    output = stage(begin(), fixture="parallel")
    assert output["status"] == "RUNNING"
    assert output["continuation_payload"]["state"]["scratch"]["thread_count"] == 40
    journal = output["continuation_payload"]["journal"]
    assert len([row for row in journal["ax_events"] if row["event_type"] == "LAB_THREAD_FIXTURE"]) == 40
    assert len([row for row in journal["run_events"] if "number" in json.loads(row["payload"])]) == 40
    advanced = stage(output)
    assert advanced["status"] == "WAITING_HUMAN"
    assert len([row for row in advanced["continuation_payload"]["journal"]["ax_events"]
                if row["event_type"] == "LAB_THREAD_FIXTURE"]) == 40


def test_candidate_output_keeps_rejected_design_and_conditional_verdict():
    output = stage(begin(), fixture="solutions")
    solutions = {row["concept_id"]:row for row in output["solutions"]}
    assert solutions["C-DROP"]["disposition"] == "EXCLUDED"
    assert solutions["C-DROP"]["candidate"]["title"] == "Rejected"
    assert solutions["C-DROP"]["validation"]["quality_status"] == "REJECT"
    assert solutions["C-KEEP"]["validation"]["constraint_check"]["verdict"] == "CONDITIONAL"
    assert not solutions["C-KEEP"]["recommended"]
    assert output["continuation_payload"]["solutions"] == output["solutions"]


def test_unknown_usage_reservation_survives_manual_retry_without_duplicate_call():
    interrupted = stage(begin(), fixture="unknown")
    assert interrupted["status"] == "INTERRUPTED"
    assert interrupted["budget"]["reserved_microusd"] == 42000
    retried = stage(interrupted, fixture="unknown")
    assert retried["status"] == "INTERRUPTED"
    assert retried["budget"]["reserved_microusd"] == 42000
    assert len(retried["continuation_payload"]["journal"]["ax_task_attempts"]) == 1


def test_native_failure_returns_checkpoint_and_trace_for_manual_inspection():
    failed = stage(begin(), fixture="failure")
    assert failed["status"] == "FAILED"
    assert failed["next_stage_key"] == "s0_bootstrap"
    assert not failed["continue_execution"]
    assert failed["diagnostics"]["traces"][0]["error_type"] == "RuntimeError"
    assert failed["continuation_payload"]["state"]["control"]["errors"] == ["fixture stage failure"]


def test_contract_change_and_state_journal_mismatch_are_rejected():
    output = begin()
    output["continuation_payload"]["contract_fingerprint"] = "other-deployment"
    payload = dict(action="stage", stage_key="s0_bootstrap", continuation_payload=output["continuation_payload"])
    child = subprocess.run([sys.executable, "-c", CHILD], input=json.dumps(payload), cwd=PILOT,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True, encoding="utf-8", timeout=40)
    result = json.loads(child.stdout)
    assert result["status"] == "INVALID_REQUEST"
    assert "contract changed" in result["error"]
    output = begin()
    output["continuation_payload"]["state"]["raw_query"] = "different query"
    payload["continuation_payload"] = output["continuation_payload"]
    child = subprocess.run([sys.executable, "-c", CHILD], input=json.dumps(payload), cwd=PILOT,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True, encoding="utf-8", timeout=40)
    assert "state and journal disagree" in json.loads(child.stdout)["error"]


def plan(previous, *, fixture="native", human_response=None):
    payload = dict(action="begin", continuation_payload=previous["continuation_payload"])
    if human_response is not None:
        payload["human_response"] = human_response
    return invoke(payload, fixture=fixture)


def at_stage(output, index, *, pending=None, concepts=None, checks=None):
    """A fixture starts at a native gate with a matching portable projection."""
    state = output["continuation_payload"]["state"]
    state["control"]["stage_index"] = index
    state["status"] = "WAITING_HUMAN" if pending else "RUNNING"
    state["pending"] = pending
    if concepts is not None:
        state["concepts"] = concepts
    if checks is not None:
        state["constraint_checks"] = checks
    journal = output["continuation_payload"]["journal"]
    journal["run_states"][0]["state_json"] = json.dumps(state)
    journal["runs"][0]["status"] = state["status"]
    output["next_stage_key"] = ["s0_bootstrap", "s0_research", "s1_intake", "s2_confirm",
        "s3_analyze", "s4_define", "s5_solve", "s6_concept", "s7_gate", "s8_references",
        "s8_evaluate", "s9_report"][index]
    return output


def test_manual_begin_resume_only_plans_native_s0_s1_s2_gates():
    initial = invoke(dict(action="begin", raw_query="Offline pump contradiction"))
    assert initial["continuation_payload"]["state"]["control"]["mode"] == "FULL"
    research = stage(stage(initial))
    planned = plan(research, human_response={"interrupt_id":research["pending"]["interrupt_id"], "skip":True})
    assert planned["next_stage_key"] == "s0_research" and planned["pending"] is None
    assert planned["cost"] == research["cost"]
    intake = stage(stage(planned), fixture="intake-confirm")
    assert intake["pending"]["kind"] == "CLARIFY"
    planned = plan(intake, fixture="intake-confirm", human_response={"interrupt_id":intake["pending"]["interrupt_id"], "skip":True})
    assert planned["next_stage_key"] == "s1_intake" and planned["pending"] is None
    confirmed = stage(stage(planned, fixture="intake-confirm"), fixture="intake-confirm")
    assert confirmed["pending"]["kind"] == "CONFIRM"
    assert confirmed["next_stage_key"] == "s2_confirm"
    planned = plan(confirmed, fixture="intake-confirm", human_response={
        "interrupt_id":confirmed["pending"]["interrupt_id"], "candidate_id":"SYS-1"})
    assert planned["next_stage_key"] == "s2_confirm" and planned["pending"] is None
    result = stage(planned, fixture="intake-confirm")
    assert result["next_stage_key"] == "s3_analyze"
    assert result["stage_outputs"]["confirm"]["user_confirmed"] is True
    assert result["cost"]["request_count"] == 2


def test_manual_begin_resume_native_s7_keeps_conditional_and_records_drop():
    pending = dict(interrupt_id="INT-S7", kind="DECIDE", title="Keep or drop", stage="S7",
        payload={"conditional":[{"concept_id":"C-KEEP"}, {"concept_id":"C-DROP"}]})
    output = at_stage(begin(), 8, pending=pending,
        concepts=[{"id":"C-KEEP", "title":"Keep", "quality_status":"PASS"},
                  {"id":"C-DROP", "title":"Drop", "quality_status":"PASS"}],
        checks=[{"concept_id":"C-KEEP", "verdict":"CONDITIONAL", "requires_user_decision":True},
                {"concept_id":"C-DROP", "verdict":"CONDITIONAL", "requires_user_decision":True}])
    planned = plan(output, human_response={"interrupt_id":"INT-S7", "decisions":{"C-KEEP":"accept", "C-DROP":"drop"}})
    assert planned["next_stage_key"] == "s7_gate" and planned["pending"] is None
    result = stage(planned)
    assert result["next_stage_key"] == "s8_references"
    solutions = {row["concept_id"]:row for row in result["solutions"]}
    assert solutions["C-KEEP"]["validation"]["constraint_check"]["verdict"] == "CONDITIONAL"
    assert solutions["C-DROP"]["disposition"] == "EXCLUDED"
    assert solutions["C-DROP"]["exclusions"][0]["reason_kind"] == "USER_DROP"


def test_native_report_is_inline_and_completes_without_feedback_stage():
    result = stage(at_stage(begin(), 11))
    assert result["status"] == "COMPLETED", result["diagnostics"]
    assert result["next_stage_key"] is None
    assert result["stage_index"] == 12
    assert not result["continue_execution"]
    assert result["pending"] is None
    assert result["report"]["markdown"]
    assert any(name.endswith("report.html") for name in result["report"]["files"])
    assert "report.md" in result["test_archive_names"]
    assert "report.html" in result["test_archive_names"]
    assert not any(name.endswith(".json") for name in result["test_archive_names"])
    assert result["continuation_payload"]["state"]["feedback"] is None


def test_child_independently_rejects_initial_and_restored_budget_above_five():
    def invalid(payload):
        child = subprocess.run([sys.executable, "-c", CHILD], input=json.dumps(payload), cwd=PILOT,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True, encoding="utf-8", timeout=40)
        assert child.returncode == 0
        return json.loads(child.stdout)
    result = invalid(dict(action="begin", raw_query="Offline", budget_usd=6.0))
    assert result["status"] == "INVALID_REQUEST"
    assert result["continuation_payload"] is None
    output = begin()
    continuation = output["continuation_payload"]
    continuation["state"]["cost"]["budget_usd"] = 6.0
    continuation["journal"]["run_states"][0]["state_json"] = json.dumps(continuation["state"])
    continuation["journal"]["ax_runs"][0]["budget"] = 6_000_000
    result = invalid(dict(action="stage", stage_key="s0_bootstrap", continuation_payload=continuation))
    assert result["status"] == "INVALID_REQUEST"
    assert "budget must remain within $5" in result["error"]
