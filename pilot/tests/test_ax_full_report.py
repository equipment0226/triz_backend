"""Full report parity and snapshot immutability, without any model calls."""
import re
from triz import render, presentation
from triz.ax import runtime, report, ledger
from triz.context import RunContext
from report_design_fixture import example_report


def freeze(state):
    runtime.initialize(state)
    for stage in ('s1_intake', 's2_confirm', 's3_analyze', 's4_define', 's5_solve',
                  's6_concept', 's7_gate', 's8_references', 's8_evaluate'):
        runtime.checkpoint(state, stage)
    runtime.before_stage(RunContext(state), 's9_report')
    return state


def test_full_template_sections_and_all_diagrams_match_legacy(state):
    fixture = example_report()
    fixture.run_id, fixture.user_id = state.run_id, state.user_id
    legacy = presentation.view(fixture)
    freeze(fixture)
    before = fixture.model_dump(mode='json')
    actual = presentation.view(fixture)
    assert [s['title'] for s in actual['report_sections'][:-1]] == [s['title'] for s in legacy['report_sections']]
    diagrams = lambda v: [(b['figure']['key'], b['figure']['svg']) for s in v['report_sections']
                         for b in s['blocks'] if b['type'] == 'figure']
    assert diagrams(actual) == diagrams(legacy)
    assert len(diagrams(actual)) > 8
    md, html = render.render_report(fixture, {}), render.render_html(fixture)
    for marker in ('미세 패턴 손상', '3. 문제 정의 (TRIZ)', '4. 해결책 도출 과정', 'ARIZ-85C', '부록 C.'):
        assert marker in md and marker in html
    assert fixture.model_dump(mode='json') == before
    # Mutable live state must not change any frozen report or its diagrams.
    fixture.raw_query = 'MUTATED INPUT'
    fixture.analysis.function_edges.clear()
    fixture.concepts[0].title = 'MUTATED TITLE'
    fixture.scratch['s_curve'] = {'stage': 'MUTATED SCRATCH'}
    assert render.render_report(fixture, {}) == md
    assert render.render_html(fixture) == html
    assert diagrams(presentation.view(fixture)) == diagrams(actual)


def test_old_ax_snapshot_restores_analysis_without_mutation_or_invented_metadata(state):
    fixture = example_report()
    fixture.run_id, fixture.user_id = state.run_id, state.user_id
    runtime.initialize(fixture)
    for stage in ('s3_analyze', 's4_define', 's5_solve', 's6_concept', 's7_gate', 's8_evaluate'):
        runtime.checkpoint(fixture, stage)
    fixture.scratch['ax_report_snapshot_id'] = fixture.scratch['ax_snapshot_id']
    before = ledger.head(fixture.run_id)
    md = report.markdown(fixture)
    assert '미세 패턴 손상' in md and 'ARIZ-85C' in md
    assert '메타데이터가 고정되지 않음' in md and '비용 기록 미고정' in md
    assert ledger.head(fixture.run_id) == before
    assert '3. 문제 정의 (TRIZ)' in render.render_html(fixture)


def test_api_downloads_and_bundle_use_the_same_frozen_analysis(state):
    import io,zipfile
    from fastapi.testclient import TestClient
    from api.main import app
    from triz import store,visuals
    fixture=example_report()
    fixture.run_id,fixture.user_id=state.run_id,state.user_id
    freeze(fixture)
    projected=report.project(fixture)
    expected={f['key']+'.svg':f['svg'] for f in visuals.figures(projected)}
    fixture.analysis.function_edges.clear()
    fixture.concepts[0].title='LATER MUTATION MUST NOT ENTER REPORT'
    store.save_state(fixture)
    original=store.load_state(fixture.run_id).model_dump(mode='json')
    client=TestClient(app)
    responses={fmt:client.get(f'/api/runs/{fixture.run_id}/report',params={'format':fmt}) for fmt in ('md','html','bundle')}
    assert all(r.status_code==200 for r in responses.values())
    archive=zipfile.ZipFile(io.BytesIO(responses['bundle'].content))
    assert archive.read('report.md').decode()==responses['md'].text
    assert archive.read('report.html').decode()==responses['html'].text
    assert 'LATER MUTATION' not in responses['html'].text
    assert {n for n in archive.namelist() if n.endswith('.svg')}==set(expected)
    for name,svg in expected.items():
        assert archive.read(name).decode()==svg
    assert store.load_state(fixture.run_id).model_dump(mode='json')==original
