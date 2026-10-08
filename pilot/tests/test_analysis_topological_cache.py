"""Partial analysis resumes reuse PASS without allowing stale upstream evidence."""
import json
from collections import Counter
from types import SimpleNamespace

import pytest

from triz import agent, analysis_semantic_gate, digest, verification_contract as contract
from triz.context import AbortRun, RunContext
from triz.schema import (
    CauseEffectChain, CauseNode, Component, FunctionEdge, IFR, KeyProblem,
    NineWindows, PhysicalContradiction, ResourceItem, SuFieldModel,
    SystemCandidate, TechnicalContradiction, TrimmingItem,
)
from triz.settings import settings


NODES = {
    "s3_nine_windows": ("P_S3_NINE_WINDOWS", "R3_NW"),
    "s3_function_model": ("P_S3_FUNCTION_MODEL", "R3_FUNC"),
    "s3_sufield": ("P_S3_SUFIELD", "R3_SUF"),
    "s3_resources": ("P_S3_RESOURCES", "R3_RES"),
    "s3_ceca": ("P_S3_CECA", "R3_CECA"),
    "s3_constraints": ("P_S3_CONSTRAINTS", "R3_CONSTRAINT"),
    "s4_ifr": ("P_S4_IFR", "R4_IFR"),
    "s4_contradictions": ("P_S4_CONTRADICTIONS", "R4_CONTRA"),
    "s4_trimming": ("P_S4_TRIMMING", "R4_TRIM"),
    "s4_key_problem": ("P_S4_KEY_PROBLEM", "R4_KEY"),
}


def install_functions(state, suffix=""):
    state.analysis.components = [Component(name="Nozzle"), Component(name="Wafer")]
    state.analysis.function_edges = [FunctionEdge(
        subject="Nozzle", action="removes particles" + suffix, object="Wafer",
        rank="BASIC", parameter_affected="particle count")]


def install_parallel_results(state, suffix=""):
    state.analysis.ceca = CauseEffectChain(nodes=[CauseNode(
        id="N1", text="Cleaning loss" + suffix, node_type="ROOT_CAUSE")])
    state.analysis.resources = [ResourceItem(name="Existing fluid" + suffix)]
    state.analysis.su_fields = [SuFieldModel(id="SU1", s1="Wafer", s2="Nozzle", field="flow" + suffix)]


def install_definitions(state, suffix=""):
    state.definition.ifr = IFR(statement="Remove particles" + suffix)
    state.definition.technical_contradictions = [TechnicalContradiction(
        id="TC1", label="TC1", if_action="Increase flow" + suffix)]
    state.definition.physical_contradictions = [PhysicalContradiction(
        id="PC1", element="flow", state_a="high" + suffix, state_b="low")]
    state.definition.trimming = [TrimmingItem(target_component="Nozzle", risk_note=suffix)]
    state.definition.key_problems = [KeyProblem(title="Cleaning damage" + suffix)]


@pytest.fixture
def cached_analysis(state, monkeypatch):
    """Exercise real run_agent hashing, persisted steps and verifier packaging.

    Quality findings are outside this cache test: generated content and auditor
    scores are offline fixtures, while prompt assembly/cache checks remain real.
    """
    from triz import rag
    from triz.ax import runtime

    monkeypatch.setattr(rag, "lessons_block", lambda _: "")
    monkeypatch.setitem(settings.triz["verification"], "enabled", True)
    monkeypatch.setattr(runtime, "render_prompt", lambda _, prompt_id, **values:
        json.dumps({"prompt_id": prompt_id, "values": values}, ensure_ascii=False, default=str))
    boundary = SystemCandidate(id="SYS1", name="Cleaning module", description="Remove wafer particles")
    state.confirm.candidates = [boundary]
    state.confirm.chosen_candidate_id = boundary.id
    state.confirm.user_confirmed = True
    state.analysis.nine_windows = NineWindows(insights=["Cleaning during flow"])
    install_functions(state)
    install_parallel_results(state)
    install_definitions(state)

    calls = []
    current = {}

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        if kwargs.get("_node"):
            data = {"rows": ["cached complete artifact"]}
        elif 'focused semantic auditor' in kwargs['system']:
            data = {'checks': [{'id': key, 'status': 'PASS', 'reason': 'offline cache fixture', 'findings': []}
                               for key in analysis_semantic_gate.RULES[current['rubric']]]}
        else:
            rb = contract.effective_rubric(settings, current["rubric"])
            data = {"verdict": "PASS", "per_criterion": [
                {"id": row["id"], "score": 1.0} for row in rb["criteria"]]}
        return SimpleNamespace(data=data, model="offline", tokens_in=1, tokens_out=1, cost_usd=0, meta={})

    monkeypatch.setattr(agent, "tracked_chat", chat)

    def run(node):
        prompt_id, rubric_id = NODES[node]
        current["rubric"] = rubric_id
        return agent.run_agent(RunContext(state), node=node, label=node, stage=node[:2].upper(),
            agent_id="system_analyst", prompt_id=prompt_id, rubric_id=rubric_id,
            checker=lambda data: [] if data.get("rows") else ["missing artifact"])

    return run, calls


@pytest.mark.parametrize("node", NODES)
def test_pass_cache_survives_own_and_downstream_completion_but_not_new_source(
        state, cached_analysis, node):
    run, calls = cached_analysis
    calls_per_run = 2 + int(analysis_semantic_gate.supported(NODES[node][1]))
    first = run(node)
    assert len(calls) == calls_per_run and state.steps[-1].status == "OK"

    # Simulate outputs committed after this node passed, before a sibling failed.
    if node == "s3_nine_windows":
        state.analysis.nine_windows = NineWindows(insights=["new own output"])
        install_functions(state, " downstream")
    elif node == "s3_function_model":
        install_functions(state, " own output")
    if node.startswith("s3_") and node != "s3_constraints":
        install_parallel_results(state, " own or sibling output")
    if node != "s4_key_problem":
        install_definitions(state, " downstream or own output")
    else:
        state.definition.key_problems = [KeyProblem(title="new own selection")]
        state.definition.trimming = [TrimmingItem(target_component="Nozzle", risk_note="sibling")]

    assert run(node) == first
    assert len(calls) == calls_per_run and state.steps[-1].status == "SKIPPED"

    # New primary evidence must invalidate both generation and review reuse.
    state.raw_query += " User correction: observed damage starts only after rinse."
    run(node)
    assert len(calls) == 2 * calls_per_run and state.steps[-1].status == "OK"


@pytest.mark.parametrize("node, upstream", [
    ("s3_function_model", "nine_windows"),
    ("s3_resources", "functions"),
    ("s3_sufield", "functions"),
    ("s3_ceca", "functions"),
    ("s3_constraints", "parallel"),
    ("s4_ifr", "parallel"),
    ("s4_contradictions", "parallel"),
    ("s4_trimming", "functions"),
    ("s4_key_problem", "definitions"),
])
def test_changed_real_upstream_artifact_invalidates_pass(state, cached_analysis, node, upstream):
    run, calls = cached_analysis
    calls_per_run = 2 + int(analysis_semantic_gate.supported(NODES[node][1]))
    run(node)
    if upstream == "nine_windows":
        state.analysis.nine_windows.insights.append("Changed operating window")
    elif upstream == "functions":
        install_functions(state, " corrected mechanism")
    elif upstream == "parallel":
        install_parallel_results(state, " corrected finding")
    else:
        install_definitions(state, " corrected contradiction")
    run(node)
    assert len(calls) == 2 * calls_per_run and state.steps[-1].status == "OK"


def test_contradiction_auditor_has_causes_but_never_its_own_prior_artifact(state, cached_analysis):
    run, calls = cached_analysis
    run("s4_contradictions")
    rendered, _ = json.JSONDecoder().raw_decode(calls[1]["user"])
    support = rendered["values"]["facts_block"]
    assert support["derived_causal_hypotheses"] == digest.causal_packet(state)
    assert "contradictions" not in support
    assert "technical_contradictions" not in support["analysis_context"]
    assert "physical_contradictions" not in support["analysis_context"]


def test_new_user_boundary_invalidates_pass(state, cached_analysis):
    run, calls = cached_analysis
    run("s3_nine_windows")
    state.confirm.user_amendments.append("Analyze the rinse module only")
    run("s3_nine_windows")
    assert len(calls) == 4 and state.steps[-1].status == "OK"


def test_actual_s3_resume_after_constraint_failure_reuses_every_prior_pass(
        state, cached_analysis, monkeypatch):
    from triz import nodes

    # Keep the real stage scheduler, typed commits, deterministic checks, cache
    # lookup and stored PASS validation. Only model generation/review are mocked.
    state.domain.problem_type = "PHYSICAL_TECHNICAL"
    state.analysis.nine_windows = None
    state.analysis.components = []
    state.analysis.function_edges = []
    state.analysis.ceca = None
    state.analysis.resources = []
    state.analysis.su_fields = []
    outputs = {
        "s3_nine_windows": {
            "cells": {f"{level}_{time}": "Hypothesis: operating context requires confirmation"
                      for level in ("SUB", "SYS", "SUPER") for time in ("PAST", "PRESENT", "FUTURE")},
            "insights": ["Check flow during the rinse period"]},
        "s3_function_model": {
            "components": [
                {"name": "Nozzle", "level": "TARGET", "role": "Directs cleaning fluid"},
                {"name": "Wafer", "level": "PRODUCT", "role": "Surface being cleaned"}],
            "function_edges": [{"subject": "Nozzle", "action": "removes particles",
                "object": "Wafer", "parameter_affected": "particle count", "kind": "USEFUL",
                "rank": "BASIC", "level": "INSUFFICIENT"}],
            "interaction_cells": [], "mermaid": ""},
        "s3_resources": {"resources": [ResourceItem(name="Existing fluid",
            quantity_note="Quantity not measured", usable_for=["particle transport"]).model_dump()]},
        "s3_sufield": {"su_fields": [SuFieldModel(id="SU1", label="Cleaning flow",
            s1="Wafer", s2="Nozzle", field="Fluid motion").model_dump()]},
        "s3_ceca": {"nodes": [
            CauseNode(id="N1", text="Particles remain on wafer", node_type="TARGET_DISADVANTAGE",
                      falsification_test="Inspect the wafer surface").model_dump(),
            CauseNode(id="N2", text="Flow cannot reach recessed surfaces", node_type="ROOT_CAUSE",
                      parents=["N1"], falsification_test="Measure local flow").model_dump()], "mermaid": ""},
        "s3_constraints": {"constraints": [], "user_constraints": [], "taboo": []},
    }
    generated, audited = [], []
    fail_discovery = [True]

    def chat(ctx, **kwargs):
        node = kwargs["_node"]
        generated.append(node)
        if node == "s3_constraints" and fail_discovery[0]:
            raise AbortRun("offline interrupted discovery")
        return SimpleNamespace(data=outputs[node], model="offline", tokens_in=1,
                               tokens_out=1, cost_usd=0, meta={})

    def review(ctx, rubric_id, data, facts, **kwargs):
        audited.append(rubric_id)
        rb = contract.effective_rubric(settings, rubric_id)
        return {"verdict": "PASS", "per_criterion": [
            {"id": row["id"], "score": 1.0} for row in rb["criteria"]]}

    monkeypatch.setattr(agent, "tracked_chat", chat)
    monkeypatch.setattr(agent, "verify_artifact", review)
    with pytest.raises(AbortRun, match="offline interrupted discovery"):
        nodes.s3_analyze(RunContext(state))
    assert len(audited) == 5
    assert state.analysis.ceca and state.analysis.resources and state.analysis.su_fields

    fail_discovery[0] = False
    nodes.s3_analyze(RunContext(state))
    assert Counter(generated) == Counter({node: (2 if node == "s3_constraints" else 1)
                                         for node in outputs})
    assert len(audited) == 6  # Resume audited only the failed constraint node.
    assert {step.node for step in state.steps if step.status == "SKIPPED"} == set(outputs) - {"s3_constraints"}
