import copy
from types import SimpleNamespace

import pytest

from triz import agent, digest, idea_consolidation as consolidation
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea, TechnicalContradiction
from triz.settings import settings


def test_all_46_are_given_to_agent_and_10_groups_keep_every_source(state, monkeypatch):
    contradiction = TechnicalContradiction()
    state.definition.technical_contradictions = [contradiction]
    originals = [RawIdea(id=f"IDEA-{n}", title=f"안 {n}", idea=f"기구 {n}",
                         track=["A_MATRIX", "G_FOS", "H_EFFECTS"][n % 3],
                         addresses=[contradiction.id], uses_resources=[f"자원 {n}"],
                         conditions=[f"조건 {n}"], hypothesis_ids=[f"H-{n}"],
                         resolution_status="TRADEOFF" if n == 45 else "UNSUPPORTED",
                         detail={"catalog_sources": [{"identifier": f"REF-{n}"}]})
                 for n in range(46)]
    state.solve.raw_ideas = originals
    groups = [{"keep_ids": [idea.id for idea in originals[start:start + 5]],
               "merge_reason": "동일한 개입·작동 원리·적용 조건을 서술한 원안"}
              for start in range(0, 40, 5)]
    groups.append({"keep_ids": [idea.id for idea in originals[40:42]], "merge_reason": "same mechanism and conditions"})
    groups.append({"keep_ids": [idea.id for idea in originals[42:]],
                   "merge_reason": "동일 기구와 개입 위치·조건의 표현 차이"})

    def run(ctx, **kwargs):
        assert kwargs["node"] == "s5_merge"
        packets = kwargs["vars"]["all_ideas"]
        assert [row["id"] for row in packets] == [idea.id for idea in originals]
        assert packets[-1]["resolution_status"] == "TRADEOFF"
        assert packets[-1]["detail"]["catalog_sources"] == [{"identifier": "REF-45"}]
        assert "min_ideas" not in kwargs["vars"] and "max_ideas" not in kwargs["vars"]
        assert kwargs["checker"]({"ideas": groups}) == []
        return {"ideas": groups}

    monkeypatch.setattr(agent, "run_agent", run)
    consolidation.consolidate(RunContext(state))
    assert len(state.solve.raw_ideas) == 10
    assert {sid for idea in state.solve.raw_ideas for sid in idea.source_idea_ids} == {i.id for i in originals}
    assert sum(len(idea.source_idea_ids) for idea in state.solve.raw_ideas) == 46
    last = state.solve.raw_ideas[-1]
    assert last.resolution_status == "TRADEOFF"
    assert last.conditions == [f"조건 {n}" for n in range(42, 46)]
    assert last.uses_resources == [f"자원 {n}" for n in range(42, 46)]
    assert last.hypothesis_ids == [f"H-{n}" for n in range(42, 46)]
    assert len(last.detail["source_details"]) == 4
    assert set(digest.idea_tracks(last)) == {"A_MATRIX", "G_FOS", "H_EFFECTS"}
    assert state.scratch["idea_consolidation"]["coverage_complete"]


@pytest.mark.parametrize("response", [
    None,
    {"ideas": []},
    {"ideas": [{"keep_ids": ["A"]}]},
    {"ideas": [{"keep_ids": ["A", "A"], "merge_reason": "같음"}, {"keep_ids": ["B"]}]},
    {"ideas": [{"keep_ids": ["A"]}, {"keep_ids": ["A", "B"], "merge_reason": "같음"}]},
    {"ideas": [{"keep_ids": ["A"]}, {"keep_ids": ["B"]}, {"keep_ids": ["NEW"]}]},
    {"ideas": [{"keep_ids": ["A", "B"]}]},
    {"ideas": [{"keep_ids": ["A", "B"], "merge_reason": " "}]},
    {"ideas": [{"keep_ids": ["A"], "conditions": "잘못된 배열"}, {"keep_ids": ["B"]}]},
])
def test_invalid_partition_never_replaces_originals(state, monkeypatch, response):
    state.solve.raw_ideas = [RawIdea(id="A", idea="첫 원안"), RawIdea(id="B", idea="둘째 원안")]
    before = copy.deepcopy(state.solve.raw_ideas)
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: response)
    with pytest.raises(AbortRun, match="전건 통합"):
        consolidation.consolidate(RunContext(state))
    assert state.solve.raw_ideas == before
    assert "idea_consolidation" not in state.scratch


def test_more_than_ten_outputs_are_rejected_without_silent_clipping(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id=f"IDEA-{n}", idea=f"독립 기구 {n}") for n in range(53)]
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: {
        "ideas": [{"keep_ids": [row["id"]]} for row in kw["vars"]["all_ideas"]]})
    with pytest.raises(AbortRun, match="10"):
        consolidation.consolidate(RunContext(state))
    assert len(state.solve.raw_ideas) == 53
    assert not consolidation.is_current(state)


def test_retry_reuses_completed_merge_but_changed_input_requires_new_comparison(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id="A", idea="기존 안", addresses=["INVALID"])]
    calls = []

    def run(ctx, **kwargs):
        calls.append(kwargs["vars"]["all_ideas"])
        return {"ideas": [{"keep_ids": [row["id"]]} for row in calls[-1]]}

    monkeypatch.setattr(agent, "run_agent", run)
    ctx = RunContext(state)
    consolidation.ensure_consolidated(ctx)
    assert len(calls) == 1
    assert state.solve.raw_ideas[0].addresses == []
    assert state.solve.raw_ideas[0].detail["source_details"][0]["addresses"] == ["INVALID"]
    assert consolidation.is_current(state)
    consolidation.ensure_consolidated(ctx)
    assert len(calls) == 1
    state.solve.raw_ideas[0].idea = "수정된 작동 기구"
    assert not consolidation.is_current(state)
    consolidation.ensure_consolidated(ctx)
    assert len(calls) == 2
    state.solve.raw_ideas.append(RawIdea(id="B", idea="새 기구"))
    consolidation.ensure_consolidated(ctx)
    assert len(calls) == 3
    assert [row["id"] for row in calls[-1]] == ["A", "B"]
    state.intake.frame.symptom = "운전 조건이 변경된 문제"
    assert not consolidation.is_current(state)
    consolidation.ensure_consolidated(ctx)
    assert len(calls) == 4


def test_nested_consolidation_keeps_leaf_sources_and_unions_metadata(state, monkeypatch):
    originals = [RawIdea(id=name, track=track, idea=f"원안 {name}", source_ref=f"REF-{name}",
                         uses_resources=[name], conditions=[f"조건 {name}"],
                         detail={"catalog_sources": [{"identifier": f"PAPER-{name}"}]})
                 for name, track in [("A", "A_MATRIX"), ("B", "H_EFFECTS"), ("C", "G_FOS")]]
    state.solve.raw_ideas = originals[:2]
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: {
        "ideas": [{"keep_ids": [row["id"] for row in kw["vars"]["all_ideas"]],
                   "merge_reason": "동일한 작동 기구·개입 위치·조건"}]})
    consolidation.consolidate(RunContext(state))
    state.solve.raw_ideas.append(originals[-1])
    consolidation.ensure_consolidated(RunContext(state))
    merged = state.solve.raw_ideas[0]
    assert merged.source_idea_ids == ["A", "B", "C"]
    assert merged.conditions == ["조건 A", "조건 B", "조건 C"]
    assert merged.uses_resources == ["A", "B", "C"]
    sources = merged.detail["source_details"]
    assert [row["source_idea_id"] for row in sources] == ["A", "B", "C"]
    assert [row["catalog_sources"][0]["identifier"] for row in sources] == ["PAPER-A", "PAPER-B", "PAPER-C"]
    assert len(state.scratch["idea_consolidation_history"]) == 2


def test_input_length_stops_before_model_and_keeps_all_ideas(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id="A", idea="매우 긴 기구 설명" * 100)]
    before = copy.deepcopy(state.solve.raw_ideas)
    monkeypatch.setitem(settings.triz.setdefault("solutions", {}), "consolidation_max_input_bytes", 100)
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: pytest.fail("oversized input must not call a model"))
    with pytest.raises(AbortRun, match="길이 한도"):
        consolidation.consolidate(RunContext(state))
    assert state.solve.raw_ideas == before


def test_large_complete_inventory_has_no_implicit_byte_cutoff(state, monkeypatch):
    originals = [RawIdea(id=f'A-{i}', idea='전체 원안과 출처를 보존한다. ' * 180) for i in range(46)]
    state.solve.raw_ideas = originals
    seen = []
    def respond(ctx, **kwargs):
        packets = kwargs['vars']['all_ideas']
        seen.extend(packets)
        return {'ideas': [{'keep_ids': [row['id'] for row in packets], 'merge_reason': 'same mechanism and conditions'}]}
    monkeypatch.setattr(agent, 'run_agent', respond)
    consolidation.consolidate(RunContext(state))
    assert state.scratch['idea_consolidation']['input_bytes'] > 240000
    assert len(seen) == 46
    assert len(state.solve.raw_ideas) == 1
    assert [row['idea'] for row in seen] == [idea.idea for idea in originals]


def test_duplicate_input_ids_stop_before_model(state, monkeypatch):
    state.solve.raw_ideas = [RawIdea(id="A", idea="다른 원안"), RawIdea(id="A", idea="충돌한 ID")]
    monkeypatch.setattr(agent, "run_agent", lambda *a, **kw: pytest.fail("ambiguous input must not call a model"))
    with pytest.raises(AbortRun, match="ID가 중복"):
        consolidation.consolidate(RunContext(state))


@pytest.mark.parametrize("repair_succeeds", [True, False])
def test_actual_agent_repairs_missing_coverage_or_stops_without_partial_commit(state, monkeypatch, repair_succeeds):
    state.solve.raw_ideas = [RawIdea(id="A", idea="첫 원안"), RawIdea(id="B", idea="둘째 원안")]
    original = copy.deepcopy(state.solve.raw_ideas)
    calls = []

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        rows = [{"keep_ids": ["A"]}]
        if len(calls) > 1 and repair_succeeds:
            rows.append({"keep_ids": ["B"]})
        return SimpleNamespace(data={"ideas": rows}, tokens_in=10, tokens_out=20,
                               cost_usd=0, model="offline-test")

    monkeypatch.setattr(agent, "tracked_chat", chat)
    monkeypatch.setattr(agent, "verify_artifact", lambda *a, **kw: {"verdict": "PASS"})
    monkeypatch.setitem(settings.triz.setdefault("verification", {}), "max_repair_attempts", 1)
    if repair_succeeds:
        consolidation.consolidate(RunContext(state))
        assert consolidation.is_current(state)
        assert state.steps[-1].status == "OK"
    else:
        with pytest.raises(AbortRun, match="치명적 결함"):
            consolidation.consolidate(RunContext(state))
        assert state.solve.raw_ideas == original
        assert state.steps[-1].status == "FAILED"
        assert "idea_consolidation" not in state.scratch
    assert len(calls) == (2 if repair_succeeds else 4)
    assert "누락된 입력 ID: B" in calls[-1]["user"]
    assert state.steps[-1].verify_attempts == len(calls)
