import copy,json
from types import SimpleNamespace
import pytest
from triz import agent, idea_consolidation as merge, quality, rag
from triz.context import RunContext, AbortRun
from triz.schema import RawIdea


def legacy_ideas():
    return [RawIdea(id='CURRENT-A',title='rotation support',idea='support the glass',
        source_idea_ids=['CURRENT-A','ARCHIVED-B'], detail={
            'source_details':[{'id':'ARCHIVED-B','source_idea_id':'ARCHIVED-B',
                'source_idea_ids':['ARCHIVED-B'], 'title':'prior support variant',
                'conditions':['preserve contact area'], 'mechanism':'distributed support'}],
            'consolidation':{'input_idea_ids':['CURRENT-A','ARCHIVED-B'],'merge_reason':'same support'}}),
        RawIdea(id='CURRENT-C',idea='adjust motion profile')]


def test_only_current_ids_are_present_and_source_semantics_are_retained():
    source=legacy_ideas()[0]
    before=copy.deepcopy(source)
    packet=merge.review_packet(source)
    assert packet['id']=='CURRENT-A'
    assert 'ARCHIVED-B' not in json.dumps(packet)
    assert packet['detail']['source_details'][0]['conditions']==['preserve contact area']
    assert packet['detail']['source_details'][0]['mechanism']=='distributed support'
    assert source==before


def test_remerge_sends_explicit_allowlist_and_preserves_all_leaf_lineage(state,monkeypatch):
    state.solve.raw_ideas=legacy_ideas()
    def respond(ctx,**kw):
        assert kw['vars']['allowed_idea_ids']==['CURRENT-A','CURRENT-C']
        assert 'ARCHIVED-B' not in json.dumps(kw['vars']['all_ideas'])
        assert 'ARCHIVED-B' not in kw['facts']
        return {'ideas':[{'keep_ids':['CURRENT-A','CURRENT-C'],'merge_reason':'compatible intervention conditions'}]}
    monkeypatch.setattr(agent,'run_agent',respond)
    merge.consolidate(RunContext(state))
    assert state.solve.raw_ideas[0].source_idea_ids==['CURRENT-A','ARCHIVED-B','CURRENT-C']
    assert 'ARCHIVED-B' in json.dumps(state.scratch['idea_consolidation']['source_ideas'])


def test_archived_ids_are_never_silently_accepted_as_current_ids(state,monkeypatch):
    state.solve.raw_ideas=legacy_ideas()
    before=copy.deepcopy(state.solve.raw_ideas)
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:{'ideas':[{'keep_ids':['ARCHIVED-B']},{'keep_ids':['CURRENT-C']}]})
    with pytest.raises(AbortRun,match='ARCHIVED-B'):merge.consolidate(RunContext(state))
    assert state.solve.raw_ideas==before


def test_stage_is_s6_before_legacy_reconsolidation_fails(state,monkeypatch):
    state.control.current_stage='S8_EVALUATE'
    def fail(ctx):
        assert ctx.state.control.current_stage=='S6_CONCEPT'
        raise AbortRun('deliberate')
    monkeypatch.setattr(merge,'ensure_consolidated',fail)
    with pytest.raises(AbortRun):quality.generate_concepts(RunContext(state))
    assert state.control.current_stage=='S6_CONCEPT'
