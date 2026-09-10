import json
from unittest.mock import Mock

import pytest

from triz import agent, llm, nodes, pipeline, store
from triz.context import RunContext
from triz.settings import settings


@pytest.mark.parametrize("cached", [False, True])
def test_structured_narrative_completes_report_and_survives_resume(state, monkeypatch, cached):
    narrative = {
        "executive_summary": ["현상 확인", "경계 유지"],
        "contradiction_narrative": "두 요구를 함께 충족한다.",
        "limitation_note": {"추가 검증": "측정 필요"},
        "next_steps": ["실험 설계", {"조건": "95% 유지"}],
    }
    chat = Mock(return_value=llm.LLMResult(
        data=narrative, text=json.dumps(narrative, ensure_ascii=False),
        model="offline-test", tokens_in=10, tokens_out=20, cost_usd=.001))
    monkeypatch.setattr(llm, "chat_json", chat)
    monkeypatch.setattr(pipeline, "PIPELINE", [("s9_report", "시각화 보고서", nodes.s9_report)])
    epoch = 0
    if cached:
        nodes.s9_report(RunContext(state))
        # A failed report can already have a successful summary in its call cache.
        state.report = None
        state.status = "FAILED"
        store.save_state(state)
        monkeypatch.setattr(pipeline, "start", lambda run_id: None)
        assert pipeline.continue_run(state.run_id)
        epoch = store.load_state(state.run_id).scratch["execution_epoch"]

    result = pipeline.execute_stage(state.run_id, 0, epoch)

    assert result["status"] == "COMPLETED"
    saved = store.load_state(state.run_id)
    assert saved.report.narrative == {
        "executive_summary": "현상 확인, 경계 유지",
        "contradiction_narrative": "두 요구를 함께 충족한다.",
        "limitation_note": "추가 검증: 측정 필요",
        "next_steps": "실험 설계, 조건: 95% 유지",
    }
    assert "현상 확인, 경계 유지" in saved.report.markdown
    assert saved.report.word_count == len(saved.report.markdown)
    assert saved.steps[-1].status == ("SKIPPED" if cached else "OK")
    folder = settings.storage_dir / "runs" / state.run_id
    assert (folder / "report.md").read_text(encoding="utf-8") == saved.report.markdown
    assert "현상 확인, 경계 유지" in (folder / "report.html").read_text(encoding="utf-8")
    chat.assert_called_once()
    assert chat.call_args.kwargs["max_tokens"] is None
    assert isinstance(narrative["next_steps"], list)


@pytest.mark.parametrize("override", [None, "7000"])
def test_larger_output_limits_are_scoped_to_ceca_and_ariz_validation(state, monkeypatch, override):
    if override is not None:
        monkeypatch.setitem(settings.triz["analysis"], "ceca_max_tokens", override)
        monkeypatch.setitem(settings.triz["ariz"], "validation_max_tokens", override)
    monkeypatch.setitem(settings.triz["ariz"], "enabled_parts", [4, 7])
    calls = {}

    def respond(ctx, **kwargs):
        calls[kwargs["node"]] = kwargs
        return {"solution_directions": ["실험 조건을 분리한다"]} if kwargs["node"] == "s5_ariz_p4" else {}

    monkeypatch.setattr(agent, "run_agent", respond)
    nodes.s3_analyze(RunContext(state))
    nodes._track_d_ariz(RunContext(state))

    expected = int(override) if override is not None else 8000
    expanded = {node: call["max_tokens"] for node, call in calls.items() if "max_tokens" in call}
    assert expanded == {"s3_ceca": expected, "s5_ariz_p7": expected}
    assert "s3_function_model" in calls and "s5_ariz_p4" in calls
