"""Versioned approach names and provenance survive reports and S6 handoffs."""
from copy import deepcopy

import pytest

from triz import agent, digest, idea_consolidation, nodes, quality, render, store, visuals
from triz.context import RunContext
from triz.presentation import view
from triz.report_groups import separation_groups
from triz.schema import PhysicalContradiction, RawIdea, ReportArtifact
from test_ax_full_report import freeze


NAMES = {
    'SPACE':'공간 분리', 'TIME':'시간 분리', 'CONDITION':'관계(조건) 분리',
    'DIRECTION':'방향 분리', 'SYSTEM_LEVEL':'시스템 수준 분리',
    'SATISFY':'상반 요구의 동시 충족', 'BYPASS':'모순 요구 우회',
}
RECOMMENDED = {
    'SPACE':[1,2,3,7,4,17], 'TIME':[9,10,11,15,34],
    'CONDITION':[3,17,19,31,32,40], 'DIRECTION':[4,14,17,32,35,40],
    'SYSTEM_LEVEL':[1,5,12,33], 'SATISFY':[13,28,35,36,37,38,39], 'BYPASS':[],
}
SOURCE = {
    'url':'https://wiki.matriz.org/docs/triz/problem-solving-tools-5890/contradictions/physical-contradiction-6056/algorithm-for-resolving-physical-contradictions/',
    'section':'Algorithm of resolving physical contradictions', 'accessed_on':'2026-09-29',
}


def application(kind, pc_id, *, applicable=True):
    return dict(kind=kind, applicable=applicable, source_pc_id=pc_id,
        title=NAMES[kind] + ' 적용안', idea='필수 기능을 유지하는 구현안을 검토한다.' if applicable else '',
        how='요구가 성립하는 작동 범위와 인과 경로를 구분한다.' if applicable else '',
        not_applicable_reason='' if applicable else '현재 자료만으로 성립 경로를 확인하지 못했다.',
        supporting_principles=([24] if kind == 'BYPASS' else RECOMMENDED[kind][:1]) if applicable else [],
        catalog_version='matriz-7-report-fixture-2026-09-29', approach_name=NAMES[kind],
        approach_family=kind if kind in ('SATISFY','BYPASS') else 'SEPARATE',
        catalog_sources=[dict(SOURCE)], recommended_principles=list(RECOMMENDED[kind]),
        principle_selection_policy='UNRESTRICTED' if kind == 'BYPASS' else 'RECOMMENDED_FIRST',
        principle_selection_status='UNRESTRICTED' if kind == 'BYPASS' else 'RECOMMENDED',
        principle_selection_reason='필요한 실제 구현에 사용한 원리만 기록했다.',
        conditions=['적용 환경의 적합성은 미확인'], mechanism='기능을 보존하는 작동 범위의 변경')


def report_fixture(state):
    pc = PhysicalContradiction(id='PC-current', label='지지 강성과 변형 적응',
        element='지지 구조', parameter='강성', state_a='단단해야 한다', reason_a='하중 지지',
        state_b='유연해야 한다', reason_b='형상 적응')
    state.definition.physical_contradictions = [pc]
    state.solve.separation_apps = [application(kind, pc.id, applicable=kind != 'SYSTEM_LEVEL') for kind in NAMES]
    state.report = ReportArtifact()
    return pc


def approach_rows(markdown):
    return [line for line in markdown.splitlines() if line.startswith('| ') and
            any(line.startswith('| ' + name + ' |') for name in [*NAMES.values(),'조건 분리'])]


@pytest.mark.parametrize('frozen', [False, True])
def test_all_seven_report_labels_and_actual_principles_do_not_relabel_as_separations(state, frozen):
    report_fixture(state)
    if frozen:
        freeze(state)
    before = state.model_dump_json()
    markdown = render.render_report(state, {})
    assert '물리적 모순 해결 접근' in markdown
    assert '| 해결 접근 | 적용 | 해결 방식 | 아이디어 | 실제 사용 발명원리 |' in markdown
    rows = approach_rows(markdown)
    assert len(rows) == 7
    for name in NAMES.values():
        assert any(line.startswith('| ' + name + ' |') for line in rows)
    assert next(r for r in rows if r.startswith('| 시간 분리 |')).split('|')[-2].strip() == '9'
    assert next(r for r in rows if r.startswith('| 모순 요구 우회 |')).split('|')[-2].strip() == '24'
    assert '우회 분리' not in markdown and '동시 충족 분리' not in markdown
    assert all(kind not in '\n'.join(rows) for kind in NAMES)
    figure = next(f for f in view(state)['figures'] if f['key'] == 'separation-0')
    assert '물리적 모순 해결 접근' in figure['title']
    assert state.model_dump_json() == before
    if frozen:
        state.solve.separation_apps.clear()
        assert render.render_report(state, {}) == markdown


def test_legacy_condition_and_mixed_pc_reports_keep_provenance_and_unknown_names_private(state):
    current = report_fixture(state)
    legacy = PhysicalContradiction(id='PC-legacy', label='과거 온도 조건',
        element='공정', parameter='온도', state_a='고온', state_b='저온')
    state.definition.physical_contradictions.insert(0, legacy)
    old = [dict(kind=kind, source_pc_id=legacy.id, applicable=True,
                title='과거 기록 ' + str(i), how='과거에 저장한 조건 구분', idea='과거 원안 유지',
                supporting_principles=[35])
           for i, kind in enumerate(('TIME','SPACE','CONDITION','SYSTEM_LEVEL'))]
    unknown = dict(kind='FUTURE_PRIVATE_KIND', source_pc_id=legacy.id, applicable=False,
                   not_applicable_reason='과거 분류 확인 필요')
    state.solve.separation_apps = old + [unknown] + state.solve.separation_apps
    state.solve.raw_ideas = [RawIdea(id='legacy-idea', track='B_SEPARATION',
        source_ref='CONDITION 분리', title='과거 조건 제어', idea='과거 방식',
        addresses=[legacy.id], detail=deepcopy(old[2]))]
    before = state.model_dump_json()
    groups = separation_groups(state)
    assert [len(g['apps']) for g in groups] == [5,7]
    assert all(a['source_pc_id'] == legacy.id for a in groups[0]['apps'])
    assert all(a['source_pc_id'] == current.id for a in groups[1]['apps'])
    markdown = render.render_report(state, {})
    rows = approach_rows(markdown)
    assert any(r.startswith('| 조건 분리 |') for r in rows)
    assert any(r.startswith('| 관계(조건) 분리 |') for r in rows)
    assert 'FUTURE_PRIVATE_KIND' not in markdown
    assert '7종 검토 완료' not in markdown
    assert state.solve.raw_ideas[0].source_ref == 'CONDITION 분리'
    assert state.model_dump_json() == before
    figures = [f for f in visuals.figures(state) if f['key'].startswith('separation-')]
    assert [f['key'] for f in figures] == ['separation-0','separation-1']


def test_versioned_track_b_metadata_survives_merge_digest_s6_and_storage(state, monkeypatch):
    pc = report_fixture(state)
    # Compatible fixture variants exercise provenance transport, not physical validity.
    originals = [application('SPACE',pc.id), application('BYPASS',pc.id)]
    for app in originals:
        app['ref'] = app['approach_name']
    nodes._add_ideas(state, 'B_SEPARATION', originals, ref_key='ref', addresses=[pc.id])
    original_ids = [i.id for i in state.solve.raw_ideas]
    original_refs = [i.source_ref for i in state.solve.raw_ideas]
    original_dump = [i.model_dump(mode='json') for i in state.solve.raw_ideas]
    captured = []

    def respond(ctx, **kwargs):
        if kwargs['node'] == 's5_merge':
            assert kwargs['vars']['allowed_idea_ids'] == original_ids
            return {'ideas':[{'keep_ids':original_ids,
                             'merge_reason':'동일한 개입 위치와 양립하는 적용 조건을 보존하는 시험용 통합'}],
                    'deferred':[]}
        assert kwargs['node'] == 's6_concept'
        packets = kwargs['vars']['ideas']
        captured.extend(deepcopy(packets))
        assert len(packets) == 1
        sources = packets[0]['support']['source_details']
        assert [s['kind'] for s in sources] == ['SPACE','BYPASS']
        assert sources[1]['recommended_principles'] == []
        assert sources[1]['supporting_principles'] == [24]
        for actual, expected in zip(sources, originals):
            for key in ('source_pc_id','catalog_version','approach_name','approach_family',
                        'catalog_sources','recommended_principles','supporting_principles',
                        'principle_selection_policy','principle_selection_status','principle_selection_reason'):
                assert actual[key] == expected[key]
        return {'concepts':[dict(title='통합 원안의 후속 검토', source_idea_ids=[packets[0]['id']],
            addresses_contradictions=[pc.id], triz_origin=[{'track':'B_SEPARATION','ref':ref} for ref in original_refs],
            working_principle='시험 fixture에서 저장한 인과 경로', open_risks=['실증 미수행'])], 'excluded':[]}

    monkeypatch.setattr(agent, 'run_agent', respond)
    monkeypatch.setattr(quality, 'audit_concepts', lambda ctx: None)
    monkeypatch.setattr(quality.rag, 'prior_cases_block', lambda _: '')
    ctx = RunContext(state)
    idea_consolidation.consolidate(ctx)
    merged = state.solve.raw_ideas[0]
    assert merged.source_idea_ids == original_ids
    assert merged.source_ref == ' + '.join(original_refs)
    assert [row['source_ref'] for row in merged.detail['source_details']] == original_refs
    assert [row['source_idea_id'] for row in merged.detail['source_details']] == original_ids
    assert [row['detail'] for row in original_dump] == originals
    before = deepcopy(merged)
    packet = digest.idea_packet(merged)
    assert merged == before
    assert packet['support']['source_details'][1]['recommended_principles'] == []
    quality._generate_concepts(ctx, ideas_override=[merged])
    assert len(captured) == 1 and len(state.concepts) == 1
    assert state.concepts[0].source_idea_ids == [merged.id]
    assert state.concepts[0].triz_origin == [{'track':'B_SEPARATION','ref':ref} for ref in original_refs]
    assert state.concepts[0].quality_status == 'UNVERIFIED'
    store.save_state(state)
    restored = store.load_state(state.run_id)
    assert restored.solve.raw_ideas[0].detail == merged.detail
    assert restored.concepts[0].triz_origin == state.concepts[0].triz_origin
    assert digest.idea_packet(restored.solve.raw_ideas[0]) == packet


def test_empty_actual_principles_and_bypass_recommendations_remain_explicit_without_changing_legacy_packet():
    app = application('BYPASS','PC-source')
    app['supporting_principles'] = []
    app['principle_selection_status'] = 'UNSPECIFIED'
    current = RawIdea(id='current',track='B_SEPARATION',detail=app)
    support = digest.idea_packet(current)['support']
    assert support['recommended_principles'] == []
    assert support['supporting_principles'] == []
    legacy = RawIdea(id='old',track='B_SEPARATION',source_ref='CONDITION 분리',
        detail={'kind':'CONDITION','supporting_principles':[35],'how':'온도 조건을 나눈다.'})
    before = legacy.model_dump_json()
    packet = digest.idea_packet(legacy)
    assert packet['support'] == {'how':'온도 조건을 나눈다.','source_tracks':['B_SEPARATION']}
    assert packet['source_ref'] == 'CONDITION 분리'
    assert legacy.model_dump_json() == before


def test_s4_hint_names_use_linked_or_pinned_version_without_rewriting_legacy_candidates(state):
    from triz import knowledge as K
    from triz.ax import WORKFLOW
    pc = PhysicalContradiction(id='PC-hints', separation_candidates=['CONDITION','DIRECTION','SATISFY','BYPASS','PRIVATE_HINT'])
    state.definition.physical_contradictions = [pc]
    assert render.separation_candidate_names(state, pc) == [
        '조건 분리','방향 분리','상반 요구의 동시 충족','모순 요구 우회','확인되지 않은 해결 접근']
    state.solve.separation_apps = [application('CONDITION', pc.id)]
    assert render.separation_candidate_names(state, pc)[0] == '관계(조건) 분리'
    state.solve.separation_apps.clear()
    state.scratch.update(workflow_version=WORKFLOW,
                         ax_bundle={'separation_catalog':deepcopy(K.separation())})
    before = state.model_dump_json()
    assert render.separation_candidate_names(state, pc)[0] == '관계(조건) 분리'
    assert state.model_dump_json() == before
    assert pc.separation_candidates == ['CONDITION','DIRECTION','SATISFY','BYPASS','PRIVATE_HINT']
    state.scratch.pop('workflow_version')
    assert render.separation_candidate_names(state, pc)[0] == '조건 분리'
