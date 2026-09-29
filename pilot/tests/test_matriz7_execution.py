"""Offline execution boundaries: selected PCs, repair, cache and frozen runs."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, knowledge as K, nodes, store
from triz import separation_contract as SC
from triz.ax import WORKFLOW, ledger, runtime
from triz.context import AbortRun, RunContext
from triz.execution_config import profile
from triz.schema import KeyProblem, PhysicalContradiction
from triz.settings import settings
from matriz7_fixtures import KINDS, legacy_bundle, legacy_payload, payload


def pcs(state, count=1):
    state.definition.physical_contradictions = [PhysicalContradiction(
        id=f'PC-{i}', element=f'Element {i}', parameter='stiffness',
        state_a='rigid', reason_a='insertion', state_b='flexible', reason_b='operation')
        for i in range(count)]


def response(data):
    return SimpleNamespace(data=deepcopy(data), model='offline',
        tokens_in=10, tokens_out=20, cost_usd=0, meta={})


@pytest.mark.parametrize('selected', [False, True])
def test_selected_pc_limit_one_call_each_and_no_cross_pc_ideas(state, monkeypatch, selected):
    pcs(state, 3)
    if selected:
        state.definition.key_problems = [KeyProblem(id='KP', contradiction_ids=['PC-2'])]
    calls = []
    def run(ctx, **kw):
        calls.append(kw)
        assert kw['agent_id'] == 'inventor_b' and kw['tier'] == 'T2'
        assert kw['rubric_id'] == 'R5_B' and 'max_tokens' not in kw
        assert kw['vars']['separation_block'] == K.separation_block()
        data = payload()
        data['applications'][1]['source_pc_id'] = 'model-invented'
        assert not kw['checker'](kw['normalizer'](data))
        return data
    monkeypatch.setattr(agent, 'run_agent', run)
    nodes._track_b(RunContext(state))
    expected = ['PC-2'] if selected else ['PC-0', 'PC-1']
    assert len(calls) == len(expected)
    assert len(state.solve.separation_apps) == 7 * len(expected)
    assert len(state.solve.raw_ideas) == len(expected)
    for index, pc_id in enumerate(expected):
        rows = state.solve.separation_apps[index*7:(index+1)*7]
        assert tuple(row['kind'] for row in rows) == KINDS
        assert {row['source_pc_id'] for row in rows} == {pc_id}
        idea = state.solve.raw_ideas[index]
        assert idea.addresses == [pc_id] and idea.track == 'B_SEPARATION'
        assert idea.detail['source_pc_id'] == pc_id
        assert idea.detail['supporting_principles'] == [9]
        assert idea.detail['catalog_sources'] and idea.detail['catalog_version']
        assert idea.source_ref == '시간 분리'
    assert state.solve.gaps == []  # One applicable approach does not redefine a PC.


@pytest.mark.parametrize('bad', [None, {}, {'applications': []}, legacy_payload()])
def test_final_node_guard_rejects_invalid_default_or_bypassed_checker(state, monkeypatch, bad):
    pcs(state)
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: deepcopy(bad))
    with pytest.raises(AbortRun, match='검토가 완전하지'):
        nodes._track_b(RunContext(state))
    assert not state.solve.raw_ideas and not state.solve.separation_apps


@pytest.mark.parametrize('repaired', [False, True])
@pytest.mark.parametrize('malformed', ['old_four', 'raw_idea_fields'])
def test_real_agent_uses_existing_repair_limit_and_never_leaks_fatal_rows(state, monkeypatch, repaired, malformed):
    pcs(state)
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 1)
    calls = []
    bad = legacy_payload() if malformed == 'old_four' else payload()
    if malformed == 'raw_idea_fields':
        bad['applications'][1]['hypothesis_ids'] = 17
    def chat(ctx, **kw):
        calls.append(kw)
        return response(payload() if repaired and len(calls) == 2 else bad)
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    if repaired:
        nodes._track_b(RunContext(state))
        assert len(state.solve.raw_ideas) == 1 and len(state.solve.separation_apps) == 7
    else:
        with pytest.raises(AbortRun, match='치명적 결함'):
            nodes._track_b(RunContext(state))
        assert state.steps[-1].status == 'FAILED'
        assert not state.solve.raw_ideas and not state.solve.separation_apps
    assert len(calls) == 2
    assert all(call['_node'] == 's5_track_b' and call['tier'] == 'T2' for call in calls)
    saved = store.get_step(state.run_id, state.steps[-1].step_id)
    assert saved['verify_attempts'] == 2 and saved['verdicts'][0]['source'] == 'deterministic'


def test_old_cache_cannot_satisfy_new_generation_but_identical_new_cache_reuses(state, monkeypatch):
    pcs(state)
    calls = []
    def chat(ctx, **kw):
        calls.append(kw)
        return response(payload() if 'DIRECTION' in kw['user'] else legacy_payload())
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    # Explicit PASS simulates an already reviewed cache item, with no auditor call.
    monkeypatch.setattr(agent, 'verify_artifact', lambda *a, **kw: {'verdict':'PASS','score':1})
    with monkeypatch.context() as old:
        old.setattr(SC, 'catalog_for', lambda state: SC.legacy_catalog())
        original = runtime.render_prompt
        old.setattr(runtime, 'render_prompt', lambda state, prompt_id, **kw:
            'Legacy TIME SPACE CONDITION SYSTEM_LEVEL\n'+kw['separation_block']
            if prompt_id == 'P_S5_TRACK_B' else original(state, prompt_id, **kw))
        nodes._track_b(RunContext(state))
    original_rows = deepcopy(state.solve.separation_apps)
    original_idea = state.solve.raw_ideas[0].model_dump()
    assert len(calls) == 1 and len(original_rows) == 4
    nodes._track_b(RunContext(state))
    assert len(calls) == 2 and len(state.solve.separation_apps) == 11
    assert state.solve.separation_apps[:4] == original_rows
    assert state.solve.raw_ideas[0].model_dump() == original_idea
    nodes._track_b(RunContext(state))
    assert len(calls) == 2 and state.steps[-1].status == 'SKIPPED'
    assert len(state.scratch['agent_cache']) == 2


def test_legacy_resume_keeps_bundle_ledger_epoch_and_user_approval(state, monkeypatch):
    pcs(state)
    bundle = legacy_bundle()
    state.scratch.update(workflow_version=WORKFLOW, ax_bundle=bundle, execution_epoch=3,
        pending_user_approval={'accepted': False, 'decision_id': 'review-original'})
    ledger.bootstrap(state, bundle)
    before = deepcopy(bundle), ledger.head(state.run_id), deepcopy(state.scratch['pending_user_approval'])
    requests = []
    def chat(ctx, **kw):
        requests.append(kw)
        assert 'Legacy four approaches' in kw['user'] and 'DIRECTION' not in kw['user']
        assert settings.rubric('R5_B')['description'] == 'Legacy four separation principles'
        return response(legacy_payload())
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    token = profile.set(bundle)  # execute_stage supplies this existing scope.
    try:
        nodes._track_b(RunContext(state))
    finally:
        profile.reset(token)
    assert len(requests) == 1 and len(state.solve.separation_apps) == 4
    assert {row['catalog_version'] for row in state.solve.separation_apps} == {SC.LEGACY_VERSION}
    assert state.scratch['ax_bundle'] == before[0]
    assert ledger.head(state.run_id) == before[1]
    assert state.scratch['pending_user_approval'] == before[2]
    assert state.scratch['execution_epoch'] == 3


@pytest.mark.parametrize('legacy', [False, True])
def test_ariz5_consumes_same_catalog_without_track_b_shape_or_sequence_change(state, monkeypatch, legacy):
    from test_ariz_reformulation import configure_ariz, part5_payload, model_review
    from ariz_fixtures import ariz_payload
    if legacy:
        state.scratch.update(workflow_version=WORKFLOW, ax_bundle=legacy_bundle())
    configure_ariz(monkeypatch, [5, 7])
    calls = []
    def run(ctx, **kw):
        calls.append(kw)
        if kw['node'] == 's5_ariz_p5':
            assert kw['vars']['separation_block'] == K.separation_block(catalog=SC.catalog_for(state))
            assert ('DIRECTION' in kw['vars']['separation_block']) is not legacy
            assert kw['tier'] == 'T2' and kw['max_tokens'] == settings.cfg('ariz.knowledge_max_tokens', 16000)
            data = part5_payload()
            assert 'applications' not in data
        elif kw['node'] == 's5_ariz_p6':
            data = model_review()
        else:
            data = ariz_payload(7)
        assert not kw['checker'](data)
        return data
    monkeypatch.setattr(agent, 'run_agent', run)
    nodes._track_d_ariz(RunContext(state))
    assert [call['node'] for call in calls] == ['s5_ariz_p5','s5_ariz_p6','s5_ariz_p7']
    assert [step.step_code for step in state.solve.ariz.steps] == [
        '5.1','5.3','5.4','6.1','6.2','6.3','7.1','7.2','7.3','7.4']
    assert len(state.solve.raw_ideas) == 1 and state.solve.raw_ideas[0].track == 'D_ARIZ'
    assert state.solve.separation_apps == []
