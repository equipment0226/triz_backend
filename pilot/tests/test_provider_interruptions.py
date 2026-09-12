"""Terminal account errors stop work, retain checkpoints, and explain how to resume."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from openai import APIStatusError
from sqlalchemy import select

from triz import agent, llm, meeting, nodes, pipeline, store, titles
from triz.context import ProviderUnavailable, RunContext
from triz.schema import TechnicalContradiction
from triz.settings import settings
from test_independent_reviews import independent_case

CHAT_JSON = llm.chat_json
REAL_RUN_AGENT = agent.run_agent


def provider_error(status):
    return APIStatusError("private account detail", response=httpx.Response(status,
        request=httpx.Request("POST", "https://provider.invalid/chat/completions")), body={})


def response(data, finish="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish,
        message=SimpleNamespace(content=json.dumps(data)))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20))


def install_sdk(monkeypatch, side_effect):
    create = Mock(side_effect=side_effect)
    monkeypatch.setattr(llm, "_client", lambda tier:
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm, "chat_json", CHAT_JSON)
    return create


def run_node(ctx, node="test_generate", **kwargs):
    return agent.run_agent(ctx, node=node, label=node, stage="S0", agent_id="planner",
        prompt_id="P_S0_BOOTSTRAP", vars={"raw_query": "saved observation"}, **kwargs)


@pytest.mark.parametrize("status", [401, 402, 403])
def test_account_errors_never_retry_and_record_actual_request(monkeypatch, status):
    create = install_sdk(monkeypatch, [provider_error(status)])
    sleep = Mock()
    monkeypatch.setattr(llm.time, "sleep", sleep)
    with pytest.raises(llm.LLMError) as caught:
        llm.chat_json(system="JSON", user="test", retries=3)
    error = caught.value
    assert error.terminal and error.status_code == status
    assert create.call_count == 1 and not sleep.called
    assert error.usage.meta["attempt"] == 1
    assert error.usage.tokens_out == error.usage.cost_usd == 0
    request = error.usage.meta["requests"][0]
    assert request["status_code"] == status and request["finish_reason"] == "error"
    assert "private account detail" not in json.dumps(request)


@pytest.mark.parametrize("status", [429, 500])
def test_transient_errors_still_retry_and_account_for_success(monkeypatch, status):
    create = install_sdk(monkeypatch, [provider_error(status), response({"ok": True})])
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)
    result = llm.chat_json(system="JSON", user="test", retries=3)
    assert result.data == {"ok": True} and create.call_count == 2
    assert result.meta["attempt"] == len(result.meta["requests"]) == 2
    assert result.meta["requests"][0]["status_code"] == status
    assert result.tokens_in == 10 and result.tokens_out == 20


def test_account_error_after_truncation_retains_consumed_usage(monkeypatch):
    create = install_sdk(monkeypatch, [response({"partial": True}, "length"), provider_error(402)])
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)
    with pytest.raises(llm.LLMError) as caught:
        llm.chat_json(system="JSON", user="test", retries=3)
    usage = caught.value.usage
    assert create.call_count == usage.meta["attempt"] == 2
    assert caught.value.terminal and usage.tokens_in == 10 and usage.tokens_out == 20
    assert usage.cost_usd > 0 and usage.data is None


def test_s5_output_limit_reaches_provider_and_invalidates_only_changed_cache(state, monkeypatch):
    monkeypatch.setattr(settings.tiers['T2'], 'max_tokens', 4000)
    monkeypatch.setitem(settings.triz['solutions'], 'track_max_tokens', 8000)
    create = install_sdk(monkeypatch, [response({'ok': True}) for _ in range(3)])
    ctx = RunContext(state)
    run_node(ctx, 's5_track_h')
    assert create.call_args.kwargs['max_tokens'] == 8000
    run_node(ctx, 's5_track_h')
    assert create.call_count == 1
    monkeypatch.setitem(settings.triz['solutions'], 'track_max_tokens', 12000)
    run_node(ctx, 's5_track_h')
    assert create.call_count == 2
    assert create.call_args.kwargs['max_tokens'] == 12000
    run_node(ctx, 's4_other')
    assert create.call_args.kwargs['max_tokens'] == 4000


def test_ariz_knowledge_call_keeps_tables_and_effect_binding_with_larger_limit(state, monkeypatch):
    from triz import knowledge
    monkeypatch.setattr(settings.tiers['T2'], 'max_tokens', 4000)
    monkeypatch.setitem(settings.triz['ariz'], 'enabled_parts', [5])
    effect = knowledge.effect_candidates(['electrostatic chuck ESC'], limit=1)[0]
    monkeypatch.setattr(knowledge, 'effect_candidates', lambda *args, **kwargs: [effect])
    data = {'steps': [dict(step_code=f'5.{i}', step_title='적용 검토', output='조건을 확인한다.',
            status='DONE', table_columns=['조건', '검토'], table_rows=[['잔류 전하', '해제 확인']])
            for i in range(1, 5)],
        'final_ideas': ['정전기 척 적용 검토'],
        'ideas': [dict(title='정전기 척 적용 검토', idea='잔류 전하와 해제 조건을 확인한다.',
            source_step='5.4', source_effect_id=effect['id'], effect_name=effect['name'],
            mechanism='전기장에 의한 인력', conditions=['잔류 전하 관리'])]}
    create = install_sdk(monkeypatch, [response(data)])
    nodes._track_d_ariz(RunContext(state))
    assert create.call_count == 1
    assert create.call_args.kwargs['max_tokens'] == 16000
    assert [s.step_code for s in state.solve.ariz.steps] == ['5.1', '5.2', '5.3', '5.4']
    assert state.steps[-1].output_json['steps'][3]['table_rows'] == [['잔류 전하', '해제 확인']]
    saved_idea = state.steps[-1].output_json['ideas'][0]
    assert saved_idea['source_effect_id'] == effect['id']
    assert '잔류 전하 관리' in saved_idea['conditions']
    assert effect['conditions'] in saved_idea['conditions']


def test_pipeline_preserves_checkpoint_and_answers_then_resumes_after_account_recovery(state, monkeypatch):
    create = install_sdk(monkeypatch, [response({"checkpoint": 1}), provider_error(402), response({"done": True})])
    checked = Mock(return_value=[])
    def stage(ctx):
        assert run_node(ctx, "first") == {"checkpoint": 1}
        run_node(ctx, "second", checker=checked)
    monkeypatch.setattr(pipeline, "PIPELINE", [("test", "test", stage)])
    state.scratch["resume_payload"] = {"answers": ["retain 95%"]}
    store.save_state(state)
    result = pipeline.execute_stage(state.run_id, 0)
    saved = store.load_state(state.run_id)
    assert result["status"] == "INTERRUPTED" and result["stage_index"] == 0
    assert saved.scratch["provider_status"] == 402 and not checked.called
    assert saved.scratch["resume_payload"]["answers"] == ["retain 95%"]
    assert [s.status for s in saved.steps] == ["OK", "FAILED"]
    assert saved.cost.request_count == 2 and len(saved.scratch["agent_cache"]) == 1
    reason = saved.scratch["interruption_reason"]
    assert "잔액 부족" in reason and "충전" in reason and "private" not in reason
    notice = next(n for n in store.pending_notifications(saved.user_id) if n["run_id"] == saved.run_id)
    assert notice["description"] == reason
    retry = next(e for e in store.read_events(saved.run_id) if e["type"] == "retry_required")
    assert retry["message"] == reason
    with store.engine.connect() as conn:
        calls = [json.loads(p) for p in conn.execute(select(store.llm_calls.c.payload)
            .where(store.llm_calls.c.run_id == saved.run_id)).scalars()]
    assert sum(c["meta"]["attempt"] for c in calls) == 2
    assert calls[-1]["meta"]["status_code"] == 402
    monkeypatch.setattr(pipeline, "start", lambda rid: None)
    assert pipeline.continue_run(saved.run_id)
    assert "provider_status" not in store.load_state(saved.run_id).scratch
    assert pipeline.execute_stage(saved.run_id, 0, epoch=1)["status"] == "COMPLETED"
    saved = store.load_state(saved.run_id)
    assert create.call_count == 3 and checked.call_count == 1
    assert [s.status for s in saved.steps] == ["OK", "FAILED", "SKIPPED", "OK"]
    assert saved.cost.request_count == 3


def test_queued_parallel_calls_stop_before_sdk_and_release_reservations(state, monkeypatch):
    create = install_sdk(monkeypatch, [provider_error(402)])
    ctx = RunContext(state)
    ctx.call_slots = threading.BoundedSemaphore(1)
    barrier = threading.Barrier(4)
    def call(index):
        barrier.wait(timeout=5)
        with pytest.raises(ProviderUnavailable):
            run_node(ctx, f"parallel_{index}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(call, range(4)))
    assert create.call_count == state.cost.request_count == 1
    assert ctx.budget["reserved"] == pytest.approx(0)
    assert len(state.steps) == 4 and all(s.status == "FAILED" and s.ended_at for s in state.steps)


def test_isolated_tracks_share_terminal_provider_stop(state, monkeypatch):
    create = install_sdk(monkeypatch, [provider_error(402)])
    ctx = RunContext(state)
    ctx.call_slots = threading.BoundedSemaphore(1)
    barrier = threading.Barrier(2)
    def track(child):
        barrier.wait(timeout=5)
        run_node(child)
    monkeypatch.setattr(nodes, "TRACK_FUNCS", {"A_MATRIX": track, "G_FOS": track})
    with pytest.raises(ProviderUnavailable):
        nodes._run_tracks(ctx, ["A_MATRIX", "G_FOS"])
    assert create.call_count == state.cost.request_count == 1
    assert ctx.budget["reserved"] == pytest.approx(0)
    assert len(state.steps) == 2 and all(s.status == "FAILED" for s in state.steps)


def test_terminal_verifier_error_does_not_commit_unverified_artifact(state, monkeypatch):
    create = install_sdk(monkeypatch, [response({"technical_contradictions": []}), provider_error(402)])
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    monkeypatch.setitem(settings.triz["verification"], "critical_rubrics", ["R4_CONTRA"])
    ctx = RunContext(state)
    with pytest.raises(ProviderUnavailable):
        run_node(ctx, rubric_id="R4_CONTRA")
    assert create.call_count == 2 and state.cost.request_count == 2
    step = state.steps[-1]
    assert step.status == "FAILED" and step.output_json == {"technical_contradictions": []}
    assert step.tokens_out == 20 and not state.scratch["agent_cache"]
    assert not step.verdicts


def test_title_repair_does_not_hide_terminal_failure(state, monkeypatch):
    create = install_sdk(monkeypatch, [provider_error(402)])
    with pytest.raises(ProviderUnavailable):
        titles.ensure_title(RunContext(state), "")
    assert create.call_count == 1 and "title_source" not in state.scratch


def test_review_provider_failure_resumes_only_unfinished_role(independent_case, monkeypatch):
    state, respond, _, roster_calls = independent_case
    monkeypatch.setitem(settings.triz["run"], "parallel_workers", 1)
    local = threading.local()
    role_requests = []
    def run(ctx, **kwargs):
        local.call, local.ctx = kwargs, ctx
        return REAL_RUN_AGENT(ctx, **kwargs)
    def create(**kwargs):
        role = local.call["vars"]["role_id"]
        role_requests.append(role)
        if role == "B" and role_requests.count("B") == 1:
            raise provider_error(402)
        return response(respond(local.ctx, **local.call))
    install_sdk(monkeypatch, create)
    monkeypatch.setattr(agent, "run_agent", run)
    monkeypatch.setattr(agent, "verify_artifact", lambda *a, **kw: {"verdict": "PASS", "score": 1.0})
    with pytest.raises(ProviderUnavailable):
        meeting.evaluate(RunContext(state))
    saved = store.load_state(state.run_id)
    assert "independent:A" in saved.evaluation.meeting.completed_calls
    assert "independent:B" not in saved.evaluation.meeting.completed_calls
    assert not saved.evaluation.evaluations and not saved.evaluation.meeting.final_reviews
    scores = meeting.evaluate(RunContext(saved))
    assert role_requests == ["A", "B", "B"] and len(roster_calls) == 1
    assert len(scores) == 8 and saved.evaluation.meeting.status == "COMPLETED"
    assert all(len(r.concept_comments) == 2 for r in saved.evaluation.meeting.final_reviews)


def test_track_a_keeps_all_principles_and_has_room_for_mechanism_fields(state, monkeypatch):
    state.definition.technical_contradictions = [TechnicalContradiction(improving_param_id=1, worsening_param_id=2)]
    monkeypatch.setattr(nodes.K, "lookup_matrix", lambda *args: ([1, 2, 3, 4, 5, 6], "MATRIX"))
    captured = []
    def respond(ctx, **kwargs):
        captured.append(kwargs)
        return {"applications": [{"principle_id": i, "idea": f"Mechanism {i}"} for i in range(1, 7)]}
    monkeypatch.setattr(agent, "run_agent", respond)
    nodes._track_a(RunContext(state))
    assert len(captured) == 1 and captured[0]["max_tokens"] == 8000
    assert len(state.solve.principle_apps) == len(state.solve.raw_ideas) == 6
