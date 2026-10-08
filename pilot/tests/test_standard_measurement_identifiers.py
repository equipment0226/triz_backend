"""Measurement graph identifier repair preserves the modeled signal paths."""
from copy import deepcopy
from types import SimpleNamespace

from triz import agent, verify
from triz.context import RunContext


def measurement_application():
    return {'applications': [{'standard_code': '4.5.1',
        'resulting_su_field': 'M1 -> O; M2 -> O; M3 -> O',
        'resulting_model': {
            'nodes': [{'id': 'M1', 'label': 'Temperature measurement'},
                      {'id': 'M2', 'label': 'Stress measurement'},
                      {'id': 'M3', 'label': 'Cross-section measurement'},
                      {'id': 'O', 'label': 'Observer'}],
            'edges': [{'source': key, 'target': 'O', 'label': label, 'kind': 'useful'}
                      for key, label in [('M1', 'Temperature signal'),
                                         ('M2', 'Stress signal'), ('M3', 'Image signal')]],
        }}]}


def corrected_identifiers(output):
    corrected = deepcopy(output)
    app = corrected['applications'][0]
    mapping = {'M1': 'S3', 'M2': 'S4', 'M3': 'S5', 'O': 'S6'}
    for node in app['resulting_model']['nodes']:
        node['id'] = mapping[node['id']]
    for edge in app['resulting_model']['edges']:
        edge['source'], edge['target'] = mapping[edge['source']], mapping[edge['target']]
    app['resulting_su_field'] = 'S3 -> S6; S4 -> S6; S5 -> S6'
    return corrected


def labeled_relations(output):
    graph = output['applications'][0]['resulting_model']
    labels = {node['id']: node['label'] for node in graph['nodes']}
    return [(labels[edge['source']], labels[edge['target']], edge['label'], edge['kind'])
            for edge in graph['edges']]


def test_identifier_diagnostic_repairs_measurement_graph_without_changing_its_meaning():
    original = measurement_application()
    issues = verify.check_standards(original, ['4.5.1'])
    assert len(issues) == 1 and issues[0].startswith('FATAL-STD: DET-08-model:')
    assert "nodes[0].id='M1'" in issues[0] and 'S1, S2, S1a' in issues[0]
    assert 'edges.source/target' in issues[0] and 'label' in issues[0]
    repaired = corrected_identifiers(original)
    assert not verify.check_standards(repaired, ['4.5.1'])
    assert labeled_relations(repaired) == labeled_relations(original)
    assert original['applications'][0]['resulting_model']['nodes'][0]['id'] == 'M1'
    incomplete = deepcopy(repaired)
    incomplete['applications'][0]['resulting_model']['edges'][0]['source'] = 'M1'
    assert verify.check_standards(incomplete, ['4.5.1'])
    missing_label = deepcopy(repaired)
    missing_label['applications'][0]['resulting_model']['nodes'][0]['label'] = ''
    assert 'nodes[0].label' in verify.check_standards(missing_label, ['4.5.1'])[0]


def test_pinned_old_prompt_receives_actionable_identifier_rule_in_repair(state, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    original = measurement_application()
    corrected = corrected_identifiers(original)
    calls = []
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    # A pinned old generator prompt has no new ID rule; P_REPAIR still receives
    # live deterministic diagnostics regardless of the original prompt version.
    monkeypatch.setattr(runtime, 'render_prompt',
                        lambda state, prompt_id, **values: prompt_id + str(values))
    monkeypatch.setattr(agent, 'verify_artifact',
                        lambda *args, **kwargs: {'verdict': 'PASS', 'score': 1.})

    def chat(ctx, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            assert "nodes[0].id='M1'" not in kwargs['user']
            data = original
        else:
            assert "nodes[0].id='M1'" in kwargs['user']
            assert 'S1, S2, S1a' in kwargs['user']
            assert 'edges.source/target' in kwargs['user']
            data = corrected
        return SimpleNamespace(data=data, text='', model='offline', tokens_in=1,
                               tokens_out=1, cost_usd=0., meta={})

    monkeypatch.setattr(agent, 'tracked_chat', chat)
    result = agent.run_agent(RunContext(state), node='s5_track_c', label='Measurement standard',
        stage='S5', agent_id='standards_specialist', prompt_id='P_S5_TRACK_C', tier='T2',
        rubric_id='R5_C', checker=lambda data: verify.check_standards(data, ['4.5.1']),
        repair_attempts=1)
    assert len(calls) == 2 and state.steps[-1].status == 'OK'
    assert result == corrected and labeled_relations(result) == labeled_relations(original)
