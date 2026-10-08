"""Supplied invalid standard graphs must not become downstream solution ideas."""
from types import SimpleNamespace

import pytest

from triz import agent, verify
from triz.context import AbortRun, RunContext


@pytest.mark.parametrize("output", [
    {"applications": [{"standard_code": "9.9.9"}]},
    {"applications": [{"standard_code": []}]},
    {"applications": [{"standard_code": "1.2.1", "resulting_model": {
        "nodes": [{"id": "S1", "label": ""}], "edges": []}}]},
    {"applications": [{"standard_code": "1.2.1", "resulting_model": {
        "nodes": [{"id": "S1", "label": "product"}],
        "edges": [{"source": "S2", "target": "S1"}]}}]},
    {"applications": ["invalid application"]},
    {"applications": None},
    [],
])
def test_invalid_supplied_standard_structures_are_fatal(output):
    issues = verify.check_standards(output, ["1.2.1"])
    assert issues and all(issue.startswith("FATAL-STD:") for issue in issues)


def test_empty_or_text_only_standard_does_not_require_an_invented_graph():
    assert not verify.check_standards({"applications": [], "not_applicable_reason": "No supported conditions"})
    assert not verify.check_standards({"applications": [{
        "standard_code": "1.2.1", "resulting_su_field": "Intermediate layer separates tool and product"}]})


def test_failed_standard_graph_repair_stops_noncritical_track_without_extra_verifier(state, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    monkeypatch.setattr(rag, "lessons_block", lambda state: "")
    monkeypatch.setattr(runtime, "render_prompt", lambda state, prompt_id, **values: str(values))
    calls = []
    output = {"applications": [{"standard_code": "1.2.1", "resulting_model": {
        "nodes": [{"id": "S1", "label": ""}], "edges": []}}]}
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data=output, text="", model="offline", tokens_in=1,
                               tokens_out=1, cost_usd=0., meta={})
    monkeypatch.setattr(agent, "tracked_chat", chat)
    monkeypatch.setattr(agent, "verify_artifact", lambda *args, **kwargs:
                        pytest.fail("Deterministic failure must not spend on an independent verifier"))
    with pytest.raises(AbortRun):
        agent.run_agent(RunContext(state), node="s5_track_c", label="Standard application",
            stage="S5", agent_id="standards_specialist", prompt_id="P_S5_TRACK_C", tier="T2",
            rubric_id="R5_C", checker=lambda data: verify.check_standards(data, ["1.2.1"]),
            repair_attempts=1)
    assert len(calls) == 2
    assert state.steps[-1].status == "FAILED"
    assert all(v["source"] == "deterministic" for v in state.steps[-1].verdicts)
    assert not state.scratch["agent_cache"]
