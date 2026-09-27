"""A legacy S6 rerun must publish the exact inventory its concepts reviewed."""
from test_ax_phase1 import dlc, candidate

from triz import agent, pipeline, quality, rag, store
from triz.ax import ledger, report, runtime
from triz.context import RunContext
from triz.schema import ConceptEvaluation, ConstraintCheckResult, RawIdea


def _finish_snapshot(state):
    state.constraint_checks = [ConstraintCheckResult(concept_id=c.id, verdict='PASS') for c in state.concepts]
    state.evaluation.evaluations = [ConceptEvaluation(concept_id=c.id, rank=i+1)
                                   for i, c in enumerate(state.concepts)]
    for stage in ('s7_gate', 's8_references', 's8_evaluate'):
        runtime.checkpoint(state, stage)
    runtime.before_stage(RunContext(state), 's9_report')
    return state.scratch['ax_report_snapshot_id']


def test_legacy_s6_rerun_captures_10_group_inventory_and_exact_concept_parent(dlc, monkeypatch):
    dlc.solve.raw_ideas = [RawIdea(id=f'I{i}', title=f'original {i}', idea=f'original mechanism {i}',
                                  addresses=['TC-DLC']) for i in range(46)]
    runtime.checkpoint(dlc, 's5_solve')
    candidate(dlc)
    old_report_snapshot = _finish_snapshot(dlc)
    old_solve_version = dlc.scratch['ax_members']['solve']
    old_report = report.project(dlc)
    assert len(old_report.solve.raw_ideas) == 46
    dlc.status = 'COMPLETED'
    store.save_state(dlc)
    monkeypatch.setattr(pipeline, 'start', lambda run_id: None)
    assert pipeline.rerun_from(dlc.run_id, 's6_concept')
    state = store.load_state(dlc.run_id)
    monkeypatch.setattr(rag, 'prior_cases_block', lambda state: '')
    def respond(ctx, **kw):
        if kw['node'] == 's5_merge':
            ideas = kw['vars']['all_ideas']
            assert len(ideas) == 46
            groups = [ideas[i:i+5] for i in range(0, 45, 5)] + [ideas[45:]]
            return {'ideas': [{'keep_ids': [idea['id'] for idea in group],
                'merge_reason': 'same intervention, mechanism and protected conditions'} for group in groups]}
        return {'concepts': [{'title': idea['title'], 'source_idea_ids': [idea['id']],
            'working_principle': idea['idea'], 'addresses_contradictions': ['TC-DLC'],
            'resolution_argument': 'both requirements need physical verification',
            'validation_plan': [{'experiment': 'controlled comparison'}]}
            for idea in kw['vars']['ideas']], 'excluded': []}
    monkeypatch.setattr(agent, 'run_agent', respond)
    monkeypatch.setattr(agent, 'verify_artifact', lambda ctx, rubric, data, facts: {
        'verdict': 'PASS', 'per_concept': [{'concept_id': c['concept_id'], 'verdict': 'PASS'}
                                        for c in data['concepts']]})
    ctx = RunContext(state)
    runtime.before_stage(ctx, 's6_concept')
    quality.generate_concepts(ctx)
    runtime.checkpoint(state, 's6_concept')
    snapshot = ledger.snapshot(state.run_id, state.scratch['ax_snapshot_id'], state.user_id)
    assert len(snapshot['artifacts']['solve']['payload']['raw_ideas']) == 10
    assert state.scratch['ax_members']['solve'] != old_solve_version
    assert state.scratch['ax_members']['solve'] in snapshot['artifacts']['concepts']['parents']
    assert old_solve_version not in snapshot['artifacts']['concepts']['parents']
    assert not {'constraints', 'evidence', 'evaluation', 'selection', 'report_context', 'report'} & snapshot['members'].keys()
    assert len(ledger.snapshot(state.run_id, old_report_snapshot, state.user_id)
               ['artifacts']['solve']['payload']['raw_ideas']) == 46
    _finish_snapshot(state)
    projected = report.project(state)
    assert len(projected.solve.raw_ideas) == len(projected.concepts) == 10
    assert projected.scratch['ax_candidate_review']['completed_ideas'] == 10
    assert {i for idea in projected.solve.raw_ideas for i in idea.source_idea_ids} == {f'I{i}' for i in range(46)}
    markdown = report.markdown(state)
    assert '**10' in markdown and 'original 45' in markdown
    assert '**10' in markdown and 'original 45' in markdown


def test_s6_reuses_unchanged_solve_version_and_invalidates_downstream_outputs(dlc):
    dlc.solve.raw_ideas = [RawIdea(id='I1', title='same inventory', addresses=['TC-DLC'])]
    runtime.checkpoint(dlc, 's5_solve')
    candidate(dlc)
    _finish_snapshot(dlc)
    before = dict(dlc.scratch['ax_members'])
    runtime.checkpoint(dlc, 's6_concept')
    after = dlc.scratch['ax_members']
    assert after['solve'] == before['solve']
    assert after['concepts'] == before['concepts']
    assert not {'constraints', 'evidence', 'evaluation', 'selection', 'report_context', 'report'} & after.keys()
    snap = ledger.snapshot(dlc.run_id, dlc.scratch['ax_snapshot_id'], dlc.user_id)
    assert after['solve'] in snap['artifacts']['concepts']['parents']
