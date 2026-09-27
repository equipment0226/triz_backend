import copy
import pytest
from triz import agent, idea_consolidation as merge, render, prompts_registry
from triz.ax import report
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea


def response(ids):
    return {'ideas':[{'keep_ids':[i], 'selection_reason':'Addresses the observed cause with fewer unverified assumptions'}
                     for i in ids[-10:]],
            'deferred':[{'keep_ids':[i], 'reason':'Requires an unavailable actuation resource; retained for later review'}
                        for i in ids[:-10]]}


def test_all_sources_preserved_agent_can_select_late_ideas_and_sixteen_are_deferred(state, monkeypatch):
    state.solve.raw_ideas=[RawIdea(id=f'I{i}',title=f'original-{i}',idea=f'mechanism-{i}') for i in range(26)]
    ids=[i.id for i in state.solve.raw_ideas]
    def run(ctx, **kw):
        assert len(kw['vars']['all_ideas']) == len(ids)
        assert {i['id'] for i in kw['vars']['all_ideas']} == set(ids)
        assert 'constraints' in kw['vars']
        result=response(ids)
        assert kw['checker'](result)==[]
        return result
    monkeypatch.setattr(agent,'run_agent',run)
    merge.consolidate(RunContext(state))
    assert [i.id for i in state.solve.raw_ideas]==ids[-10:]
    record=state.scratch['idea_consolidation']
    assert len(record['source_ideas'])==26 and len(record['deferred'])==16
    assert record['coverage_complete'] and record['max_ideas']==10
    assert merge.is_current(state)
    # Snapshot metadata contains the full history, including deferred sources.
    frozen=report.context(state)['scratch']['idea_consolidation']
    assert frozen==record and frozen is not record
    markdown=render.render_report(state, {}, template='report_full.md.j2')
    assert all(f'original-{i}' in markdown for i in range(26))
    assert '최대 10개' in markdown and '상세검토 보류' in markdown
    assert '<details><summary>전체 원안' in markdown
    assert '<details open' not in markdown
    state.intake.frame.symptom = 'Updated operating condition'
    merge.ensure_consolidated(RunContext(state))
    assert len(state.scratch['idea_consolidation']['source_ideas']) == 26


@pytest.mark.parametrize('bad',['over_limit','missing','duplicate','no_reason','grouped_deferred','no_selection_reason'])
def test_invalid_dispositions_never_replace_source_inventory(state,monkeypatch,bad):
    state.solve.raw_ideas=[RawIdea(id=f'I{i}',idea=f'm{i}') for i in range(12)]
    before=copy.deepcopy(state.solve.raw_ideas)
    result=response([i.id for i in before])
    if bad=='over_limit':
        result['ideas'].append({'keep_ids':result['deferred'].pop()['keep_ids'],'selection_reason':'reason'})
    elif bad=='missing':result['deferred'].pop()
    elif bad=='duplicate':result['deferred'][0]['keep_ids']=result['ideas'][0]['keep_ids']
    elif bad=='no_reason':result['deferred'][0]['reason']=''
    elif bad=='grouped_deferred':result['deferred']=[{'keep_ids':['I0','I1'],'reason':'generic'}]
    else:result['ideas'][0].pop('selection_reason')
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:result)
    with pytest.raises(AbortRun):merge.consolidate(RunContext(state))
    assert state.solve.raw_ideas==before and 'idea_consolidation' not in state.scratch


def test_old_prompt_pin_uses_hard_ten_contract():
    body=prompts_registry.compatible_body('P_S5_MERGE','old unlimited prompt')
    assert '최대 10개' in body and 'deferred' in body
    assert '상한은 없다' not in body


def test_legacy_unlimited_merge_is_not_reused(state):
    state.solve.raw_ideas=[RawIdea(id=f'I{i}') for i in range(11)]
    state.scratch['idea_consolidation']={'contract':'all-ideas-consolidation-v1','coverage_complete':True}
    assert not merge.is_current(state)


def test_agent_repairs_eleven_outputs_to_ten_with_explicit_deferred_source(state,monkeypatch):
    from types import SimpleNamespace
    state.solve.raw_ideas=[RawIdea(id=f'I{i}',idea=f'm{i}') for i in range(11)]
    ids=[i.id for i in state.solve.raw_ideas]
    calls=[]
    def chat(ctx,**kw):
        calls.append(kw['user'])
        data={'ideas':[{'keep_ids':[i]} for i in ids]} if len(calls)==1 else response(ids)
        return SimpleNamespace(data=data,tokens_in=1,tokens_out=1,cost_usd=0,model='offline')
    monkeypatch.setattr(agent,'tracked_chat',chat)
    monkeypatch.setattr(agent,'verify_artifact',lambda *a,**kw:{'verdict':'PASS'})
    merge.consolidate(RunContext(state))
    assert len(calls)==2 and 'FATAL-CONSOLIDATION' in calls[1]
    assert len(state.solve.raw_ideas)==10
    assert len(state.scratch['idea_consolidation']['source_ideas'])==11
