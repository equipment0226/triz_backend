"""Required ARIZ execution records repair or stop before downstream work."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, knowledge, nodes, prompts_registry, verify
from triz.ax import runtime
from triz.context import AbortRun, RunContext
from triz.settings import settings
from ariz_fixtures import ariz_payload
from test_ariz_reformulation import configure_ariz, model_review


PARTS = (1, 2, 3, 4, 7)


def required(part):
    return [step["code"] for step in knowledge.ariz_part(part)["steps"] if step.get("required")]


@pytest.mark.parametrize("part", PARTS)
@pytest.mark.parametrize("defect", ["missing", "duplicate", "empty_output", "missing_status",
    "invalid_status", "invalid_table", "ragged_table", "nonobject_step", "nonarray_steps"])
def test_required_step_or_format_defects_are_fatal(part, defect):
    data = ariz_payload(part)
    if defect == "missing":
        data["steps"].pop()
    elif defect == "duplicate":
        data["steps"].append(deepcopy(data["steps"][0]))
    elif defect == "empty_output":
        data["steps"][0]["output"] = " "
    elif defect == "missing_status":
        data["steps"][0].pop("status")
    elif defect == "invalid_status":
        data["steps"][0]["status"] = "PENDING"
    elif defect == "invalid_table":
        data["steps"][0]["table_rows"] = "This must not be silently dropped."
    elif defect == "ragged_table":
        data["steps"][0].update(table_columns=["condition", "finding"], table_rows=[["one cell"]])
    elif defect == "nonobject_step":
        data["steps"].append("not an ARIZStep")
    elif defect == "nonarray_steps":
        data["steps"] = {row["step_code"]: row for row in data["steps"]}
    issues = verify.check_ariz(data, required(part))
    assert issues and all(issue.startswith("FATAL-") for issue in issues)


def test_optional_method_can_record_reason_for_not_applying_without_inventing_a_result():
    data = ariz_payload(3)
    data["steps"].append({"step_code": "3.6", "status": "SKIPPED",
        "output": "No matching standard solution was identified for the current contact geometry."})
    assert verify.check_ariz(data, required(3)) == []
    data["steps"][-1]["output"] = ""
    assert verify.check_ariz(data, required(3))


@pytest.mark.parametrize("part", PARTS)
def test_default_result_stops_before_any_later_part(state, monkeypatch, part):
    configure_ariz(monkeypatch, [4, 7] if part == 7 else [part])
    calls = []
    def respond(ctx, **kwargs):
        node = kwargs["node"]
        calls.append(node)
        if node == f"s5_ariz_p{part}":
            return {}
        return model_review() if node == "s5_ariz_p6" else ariz_payload(4)
    monkeypatch.setattr(agent, "run_agent", respond)
    with pytest.raises(AbortRun, match=f"Part{part} 검토가 완전하지"):
        nodes._track_d_ariz(RunContext(state))
    assert calls[-1] == f"s5_ariz_p{part}"
    assert state.solve.ariz is None


@pytest.mark.parametrize("part", PARTS)
@pytest.mark.parametrize("repair_succeeds", [False, True])
def test_real_agent_repairs_required_steps_or_marks_failure(state, monkeypatch, part, repair_succeeds):
    configure_ariz(monkeypatch, [4, 7] if part == 7 else [part])
    monkeypatch.setitem(settings.triz["verification"], "max_repair_attempts", 1)
    # These tests exercise the deterministic contract, independently of reviewer models.
    monkeypatch.setitem(settings.triz["verification"], "skip_nodes", ["s5_ariz_p1", "s5_ariz_p3"])
    target_calls = []
    def chat(ctx, **kwargs):
        node = kwargs["_node"]
        if node == f"s5_ariz_p{part}":
            target_calls.append(kwargs)
            data = ariz_payload(part)
            if len(target_calls) == 1 or not repair_succeeds:
                data["steps"].pop()
        elif node == "s5_ariz_p6":
            data = model_review()
        else:
            assert node == "s5_ariz_p4"
            data = ariz_payload(4)
        return SimpleNamespace(data=data, model="offline", tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, "tracked_chat", chat)
    if repair_succeeds:
        nodes._track_d_ariz(RunContext(state))
        assert state.solve.ariz is not None
    else:
        with pytest.raises(AbortRun, match="치명적 결함"):
            nodes._track_d_ariz(RunContext(state))
        assert state.solve.ariz is None
    assert len(target_calls) == 2
    assert required(part)[-1] in target_calls[1]["user"]
    trace = next(step for step in state.steps if step.node == f"s5_ariz_p{part}")
    assert trace.status == ("OK" if repair_succeeds else "FAILED")
    assert trace.verify_attempts == 2


@pytest.mark.parametrize("part", PARTS)
def test_old_pin_gets_only_required_output_contract_without_changing_pinned_bundle(state, part):
    runtime.initialize(state)
    prompt_id = f"P_S5_ARIZ_PART{part}"
    state.scratch["ax_bundle"]["prompts"][prompt_id] = "Pinned policy: preserve the problem boundary."
    before = deepcopy(state.scratch["ax_bundle"])
    rendered = runtime.render_prompt(state, prompt_id)
    assert rendered.startswith("Pinned policy: preserve the problem boundary.")
    assert all(code in rendered for code in required(part))
    assert "SKIPPED" in rendered and "output" in rendered
    assert prompts_registry.compatible_body(prompt_id, rendered) == rendered
    assert state.scratch["ax_bundle"] == before
