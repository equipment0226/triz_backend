"""Positive and negative contract tests; synthetic engineering assertions only."""
import copy
import pytest
from test_ax_phase1 import dlc, candidate, review_body
from triz.ax import coherence, validation, ledger, runtime, coordinator
from triz.context import RunContext
from triz.schema import TechnicalContradiction, CauseEffectChain, CauseNode, SuFieldModel, ReportArtifact


def record_test(s):
    ledger.submit_review(s.run_id,s.user_id,dict(review_body(s),decision_type='RECORD_TEST_RESULT',candidate_id='DLC-1',
        obligation_id='DLC-1:test:0',result='PASS',conditions='Synthetic fixture only',
        measurement={'fixture':True},evidence_refs=['fixture:measurement']))


def kinds(s):
    return {g['kind'] for g in coherence.assess(s)['candidates'][0]['gaps']}


def test_one_sided_pass_cannot_certify_original_contradiction(dlc):
    candidate(dlc)
    dlc.concepts[0].validation_plan[0]['obligation_refs']=[{'contradiction_id':'TC-DLC','side':'IMPROVE'}]
    runtime.checkpoint(dlc,'s6_concept')
    record_test(dlc)
    result=validation.selection(dlc)
    assert result['candidates'][0]['status']=='CONDITIONAL'
    assert 'ADVERSE_SIDE_OMITTED' in kinds(dlc)
    assert result['scope_status']=='PARTIAL'


def test_both_sides_and_actual_observation_control(dlc):
    candidate(dlc)
    assert not kinds(dlc)
    assert validation.selection(dlc)['candidates'][0]['status']=='CONDITIONAL'
    record_test(dlc)
    assert validation.selection(dlc)['recommended']==['DLC-1']
    assert len(coherence.obligations(dlc))==1  # Derived physical contradiction is not counted twice.


def test_missing_system_scope_is_reported_even_when_existing_candidate_passes(dlc):
    candidate(dlc)
    dlc.definition.technical_contradictions.append(TechnicalContradiction(id='TC-UNADDRESSED',label='펌프 전력 상충'))
    result=validation.selection(dlc)
    assert result['status']=='PARTIAL'
    assert any(g['obligation_id']=='TC-UNADDRESSED' for g in result['coverage_gaps'])


@pytest.mark.parametrize('mode,missing',[('ACTIVE',True),('PASSIVE',False),('DIAGNOSTIC',False)])
def test_actuation_required_only_for_active_control(dlc,mode,missing):
    candidate(dlc)
    dlc.scratch['ax_mechanisms']['DLC-1']['control_mode']=mode
    assert ('MISSING_ACTUATION' in kinds(dlc))==missing


def test_active_control_complete_path_is_still_a_hypothesis(dlc):
    candidate(dlc)
    dlc.scratch['ax_mechanisms']['DLC-1'].update(control_mode='ACTIVE',
        control_chain=dict(sensor='온도계',estimator='온도 추정',decision='유량 설정',actuator='밸브',target='유로'))
    assert not kinds(dlc)
    assert not validation.selection(dlc)['recommended']


@pytest.mark.parametrize('owner,expected',[('foreign',True),('IDEA-DLC',False)])
def test_condition_scope_ownership(dlc,owner,expected):
    candidate(dlc)
    dlc.concepts[0].source_idea_ids=['IDEA-DLC']
    dlc.scratch['ax_mechanisms']['DLC-1']['conditions']=[dict(source_idea_id=owner,condition='유량 유지',applicability='동일 유로 비교')]
    assert ('CONDITION_SCOPE_LEAK' in kinds(dlc))==expected


def test_merged_idea_accepts_its_exact_ancestor_condition_but_not_foreign_condition(dlc):
    from triz.schema import RawIdea
    candidate(dlc)
    dlc.concepts[0].source_idea_ids=['MERGED']
    dlc.solve.raw_ideas=[RawIdea(id='MERGED',conditions=['유량 유지'],source_idea_ids=['A','B'],
        detail={'source_details':[{'source_idea_id':'B','conditions':['유량 유지']}]})]
    dlc.scratch['ax_mechanisms']['DLC-1']['conditions']=[dict(source_idea_id='B',condition='유량 유지',applicability='동일 유로 비교')]
    assert not kinds(dlc)
    dlc.scratch['ax_mechanisms']['DLC-1']['conditions'][0]['condition']='다른 후보의 회수 조건'
    assert {'CONDITION_SCOPE_LEAK','CONDITION_SCOPE_UNCONFIRMED'}<=kinds(dlc)


@pytest.mark.parametrize('status,observed,text,invalid',[
    ('HYPOTHESIS',False,'원인 가설',False),('OBSERVED',False,'원인 가설',True),
    ('OBSERVED',True,'관측된 원인',False),('OBSERVED',True,'다른 결과',True)])
def test_claim_promotion_needs_exact_observed_source(dlc,status,observed,text,invalid):
    candidate(dlc)
    dlc.analysis.ceca=CauseEffectChain(nodes=[CauseNode(id='N1',text='관측된 원인',
        evidence_status='OBSERVED' if observed else 'HYPOTHESIS',evidence_refs=['measurement:1'])])
    dlc.scratch['ax_mechanisms']['DLC-1']['claims']=[dict(text=text,status=status,source_cause_id='N1',evidence_refs=['measurement:1'])]
    assert ('UNSUPPORTED_CAUSE' in kinds(dlc))==invalid


def test_more_than_five_qualified_concepts_are_all_reported(dlc):
    from triz import render,presentation
    candidate(dlc)
    base=dlc.concepts[0]
    dlc.concepts=[]
    for i in range(7):
        c=base.model_copy(deep=True,update={'id':f'CPT-MORE-{i}','title':f'독립 냉각 경로 {i}','mechanism_key':str(i)})
        dlc.concepts.append(c)
        dlc.scratch['ax_mechanisms'][c.id]=copy.deepcopy(dlc.scratch['ax_mechanisms']['DLC-1'])
    from triz.schema import ConstraintCheckResult
    dlc.constraint_checks=[ConstraintCheckResult(concept_id=c.id,verdict='PASS') for c in dlc.concepts]
    for stage in ('s6_concept','s7_gate','s8_evaluate'):
        runtime.checkpoint(dlc,stage)
    runtime.before_stage(RunContext(dlc),'s9_report')
    dlc.report=ReportArtifact()
    result=validation.selection(dlc)
    assert len(result['candidates'])==7 and result['display_limit'] is None
    md=render.render_report(dlc,{})
    assert all(c.title in md for c in dlc.concepts)
    assert len(presentation.view(dlc)['solutions'])==7


def test_standard_track_selected_for_sufield_and_effects_deferred(dlc):
    dlc.analysis.su_fields=[SuFieldModel(s1='GPU',s2='냉각수',field='열',effect='USEFUL_INSUFFICIENT')]
    coordinator.route(RunContext(dlc))
    assert dlc.control.enabled_tracks==['A_MATRIX','B_SEPARATION','C_STANDARDS']
    assert 'H_EFFECTS' in dlc.scratch['ax_coordination']['pending_tracks']


def test_existing_pinned_bundle_keeps_legacy_validation_contract(dlc):
    candidate(dlc)
    dlc.scratch['ax_bundle'].pop('coherence_contract')
    dlc.scratch.pop('ax_mechanisms')
    dlc.concepts[0].validation_plan[0].pop('obligation_refs')
    runtime.checkpoint(dlc,'s6_concept')
    record_test(dlc)
    assert validation.selection(dlc)['recommended']==['DLC-1']


def test_old_workflow_remains_readable_and_new_version_is_fixed(dlc):
    from triz.ax import enabled,WORKFLOW,RELEASE
    assert WORKFLOW=='triz-ax-v3.1' and RELEASE=='triz-ax-v3.1.2'
    assert dlc.scratch['ax_bundle']['release_version']==RELEASE
    original=copy.deepcopy(dlc.scratch['ax_bundle'])
    dlc.scratch['workflow_version']='triz-ax-v3.1'
    assert enabled(dlc)
    assert dlc.scratch['ax_bundle']==original
    assert 'templates/report_full.md.j2' in original['source_hashes']
