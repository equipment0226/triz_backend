"""Offline contracts for canonical standard details through existing flows."""
from copy import deepcopy
import xml.etree.ElementTree as ET

import pytest

from triz import agent, digest, knowledge as K, nodes, store, visuals
from triz.ax import runtime
from triz.context import RunContext
from triz.presentation import view
from triz.schema import ReportArtifact, SuFieldModel
from triz.standard_diagrams import validate_specs
from test_ariz_reformulation import configure_ariz, model_review, part5_payload


def test_s3_to_track_c_keeps_parent_and_submethods_through_storage_and_report(state, monkeypatch):
    catalog = {s['code']: s for s in K.standards()}
    wanted = ('1.1.8', '5.1.1')
    source_models = [
        SuFieldModel(id='SU-selective', label='선택적 최대 작용',
                     s1=catalog['1.1.8']['title_ko'], s2='처리 장치', field='열장',
                     completeness='COMPLETE', effect='EXCESSIVE'),
        SuFieldModel(id='SU-additive', label='첨가 제한 우회',
                     s1=catalog['5.1.1']['title_ko'], s2='처리 장치', field='기계장',
                     completeness='MISSING_F', effect='USEFUL_INSUFFICIENT'),
    ]
    state.domain.problem_type = 'PHYSICAL_TECHNICAL'
    state.intake.frame.restated_problem = '필요한 위치에만 물질과 작용을 제공한다.'
    calls = []
    expected_models = {}

    def respond(ctx, **kwargs):
        prompt = kwargs['prompt_id']
        if prompt == 'P_S3_SUFIELD':
            # Untrusted hints returned by a model must not become routing truth.
            return {'su_fields': [dict(m.model_dump(), standard_class_hint=['9.9.9'])
                                  for m in source_models]}
        if prompt == 'P_S3_FUNCTION_MODEL':
            from test_analysis_checks import functional_model
            return functional_model()
        if prompt == 'P_S3_RESOURCES':
            return {'resources': [], 'unavailable_reason': 'No resources supplied in this routing fixture'}
        if prompt == 'P_S3_CECA':
            return {'nodes': []}
        if prompt == 'P_S3_CONSTRAINTS':
            return {'constraints': [], 'taboo': []}
        if prompt != 'P_S5_TRACK_C':
            return {}
        calls.append(kwargs)
        code = next(c for c in wanted if kwargs['vars']['s1'] == catalog[c]['title_ko'])
        standard = catalog[code]
        block = kwargs['vars']['standards_block']
        assert standard['conditions'] in block
        for child in standard['substandards']:
            assert child['code'] in block
            assert child['transformation'] in block
            assert child['conditions'] in block
        assert set(kwargs['vars']) == {
            's1', 's2', 'field', 'completeness', 'effect',
            'target_system', 'resources', 'standards_block',
        }
        assert kwargs['tier'] == 'T2' and kwargs['rubric_id'] == 'R5_C'
        model = {'nodes': [
            {'id':'S1','label':f'{code} 실제 처리 대상'},
            {'id':'S2','label':'처리 장치'},
            {'id':'F','label':'공급 작용'},
        ], 'edges': [
            {'source':'F','target':'S2','label':'에너지 공급'},
            {'source':'S2','target':'S1','label':'조건부 처리'},
        ]}
        expected_models[code] = deepcopy(model)
        child = standard['substandards'][-1]
        data = {'applications': [{
            'standard_code':code, 'standard_title':'모델이 잘못 붙인 제목',
            'title':f'{code} 적용 검토', 'idea':'기존 자원을 적용 위치에서 사용한다.',
            'transformation':f"{code}의 {child['code']} 하위 기법: {child['transformation']}",
            'conditions':['실제 허용 여부는 미확인'], 'resulting_model':model,
        }]}
        assert kwargs['checker'](kwargs['normalizer'](data)) == []
        return data

    monkeypatch.setattr(agent, 'run_agent', respond)
    ctx = RunContext(state)
    nodes.s3_analyze(ctx)
    assert len(state.analysis.su_fields) == 2
    for actual, expected in zip(state.analysis.su_fields, source_models):
        assert actual.model_dump(exclude={'standard_class_hint'}) == expected.model_dump(exclude={'standard_class_hint'})
        assert actual.standard_class_hint == K.standard_hints(expected.completeness, expected.effect)
        assert all(code in K.standard_codes() for code in actual.standard_class_hint)
    nodes._track_c(ctx)
    assert len(calls) == 2
    assert [a['standard_code'] for a in state.solve.standard_apps] == list(wanted)
    assert len(state.solve.raw_ideas) == 2
    for app, idea, su, code in zip(state.solve.standard_apps, state.solve.raw_ideas,
                                  state.analysis.su_fields, wanted):
        standard = catalog[code]
        assert app['source_su_id'] == su.id
        assert app['ref'] == idea.source_ref == f'표준해 {code}'
        assert app['standard_title'] == standard['title_ko']
        assert app['resulting_model'] == idea.detail['resulting_model'] == expected_models[code]
        assert standard['substandards'][-1]['code'] in idea.detail['transformation']
        packet = digest.idea_packet(idea)
        for key, value in {
            'source_su_id':su.id, 'standard_code':code,
            'standard_title':standard['title_ko'],
            'catalog_transformation':standard['transformation'],
            'catalog_conditions':standard['conditions'],
            'catalog_limitations':standard['limitations'],
            'catalog_sources':standard['sources'],
        }.items():
            assert packet['support'][key] == value
        assert standard['conditions'] in idea.conditions

    state.report = ReportArtifact()
    store.save_state(state)
    restored = store.load_state(state.run_id)
    assert restored.solve.standard_apps == state.solve.standard_apps
    assert [digest.idea_packet(i) for i in restored.solve.raw_ideas] == [
        digest.idea_packet(i) for i in state.solve.raw_ideas]
    assert [i.detail['resulting_model'] for i in restored.solve.raw_ideas] == [expected_models[c] for c in wanted]
    applied = nodes._applied_principles(restored)
    for code in wanted:
        assert any(code in row['ref'] and catalog[code]['title_ko'] in row['ref'] for row in applied)
    report = view(restored)
    report_figures = {b['figure']['key']: b['figure']
                      for section in report['report_sections'] for b in section['blocks']
                      if b.get('type') == 'figure' and b['figure']['key'].startswith('standard-')}
    assert set(report_figures) == {'standard-0','standard-1'}
    for index, code in enumerate(wanted):
        figure = report_figures[f'standard-{index}']
        assert catalog[code]['title_ko'] in figure['title']
        parsed = ET.fromstring(figure['svg'])
        after = next(e for e in parsed.iter() if e.get('data-phase') == 'after')
        assert [(e.get('data-source'),e.get('data-target')) for e in after.iter()
                if e.get('class') == 'sis-edge'] == [('F','S2'),('S2','S1')]


@pytest.mark.parametrize('code', ['1.1.8','5.1.1'])
def test_ariz_part5_uses_shared_canonical_candidates_and_full_details_without_new_contract(state, monkeypatch, code):
    standard = next(s for s in K.standards() if s['code'] == code)
    configure_ariz(monkeypatch, [5])
    state.intake.frame.restated_problem = standard['title_ko'] + ' ' + standard['transformation']
    state.analysis.su_fields = [SuFieldModel(s1='대상', s2='도구', field='작용',
                                            effect='USEFUL_INSUFFICIENT')]
    canonical_candidates = K.candidate_standards
    canonical_block = K.standards_block
    selected, blocks, calls = [], [], []

    def candidates(*args, **kwargs):
        result = canonical_candidates(*args, **kwargs)
        selected.append(deepcopy(result))
        return result

    def block(items):
        result = canonical_block(items)
        blocks.append(result)
        return result

    # Science retrieval is outside this test and must not initialize AX ledgers.
    monkeypatch.setattr(runtime, 'effect_candidates', lambda *a, **k: [])
    monkeypatch.setattr(K, 'candidate_standards', candidates)
    monkeypatch.setattr(K, 'standards_block', block)

    def respond(ctx, **kwargs):
        calls.append(kwargs)
        if kwargs['node'] == 's5_ariz_p6':
            return model_review()
        assert kwargs['node'] == 's5_ariz_p5'
        assert kwargs['prompt_id'] == 'P_S5_ARIZ_PART5' and kwargs['tier'] == 'T2'
        assert set(kwargs['vars']) == {
            'part4','pc_macro','pc_micro','sfr_inventory',
            'standards_block','separation_block','effects_block',
        }
        assert kwargs['max_tokens'] == int(nodes.cfg('ariz.knowledge_max_tokens',16000))
        assert code in {s['code'] for s in selected[0]}
        assert kwargs['vars']['standards_block'] == blocks[0]
        for child in standard['substandards']:
            assert child['code'] in blocks[0]
            assert child['transformation'] in blocks[0]
        payload = part5_payload()
        payload['ideas'][0].update(standard_code=code, standard_title='모델의 임의 제목',
                                  source_step='5.1', conditions=['적용 전 조건 확인'],
                                  transformation=standard['substandards'][-1]['transformation'])
        normalized = kwargs['normalizer'](payload)
        assert kwargs['checker'](normalized) == []
        return payload

    monkeypatch.setattr(agent, 'run_agent', respond)
    before = state.analysis.model_dump()
    nodes._track_d_ariz(RunContext(state))
    assert [call['node'] for call in calls] == ['s5_ariz_p5','s5_ariz_p6']
    assert len(selected) == len(blocks) == 1
    assert state.analysis.model_dump() == before
    idea = state.solve.raw_ideas[0]
    assert idea.track == 'D_ARIZ' and idea.source_ref == 'ARIZ 5.1'
    packet = digest.idea_packet(idea)['support']
    assert packet['standard_code'] == code
    assert packet['standard_title'] == standard['title_ko']
    assert packet['catalog_conditions'] == standard['conditions']
    assert packet['catalog_sources'] == standard['sources']
    assert packet['transformation'] == standard['substandards'][-1]['transformation']
    assert all(step.status == 'DONE' for step in state.solve.ariz.steps)


def test_all_76_parent_codes_remain_report_linked_without_rewriting_reference_assets(state):
    catalog = list(reversed(K.standards()))
    assert len(catalog) == 76
    assert set(validate_specs(catalog)) == {s['code'] for s in catalog}
    state.solve.standard_apps = [
        {'standard_code':s['code'],'standard_title':'부정확한 생성 제목','idea':'적용 조건 검토',
         # Reports display saved application graphs, not unrequested reference figures.
         'resulting_model': {'nodes': [{'id': 'S1', 'label': 'test product'},
                                       {'id': 'S2', 'label': 'test carrier'},
                                       {'id': 'F', 'label': 'test field'}],
                             'edges': [{'source': 'S2', 'target': 'S1', 'label': 'test action'}]}}
        for s in catalog
    ]
    state.report = ReportArtifact()
    before = state.model_dump_json()
    expected = {f'standard-{i}':s for i,s in enumerate(catalog)}
    figures = {f['key']:f for f in visuals.figures(state) if f['key'].startswith('standard-')}
    assert set(figures) == set(expected)
    for key, standard in expected.items():
        figure = figures[key]
        assert ET.fromstring(figure['svg']).get('data-standard-code') == standard['code']
        assert standard['title_ko'] in figure['title']
    linked = [b['figure']['key'] for section in view(state)['report_sections']
              for b in section['blocks'] if b.get('type') == 'figure'
              and b['figure']['key'].startswith('standard-')]
    assert len(linked) == 76 and set(linked) == set(expected)
    assert state.model_dump_json() == before
