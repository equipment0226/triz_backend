"""Check the exported manual graph against the native stage contract."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest


PILOT = Path(__file__).resolve().parents[1]
DEPLOY = PILOT.parent / 'deploy' / 'n8n'


@pytest.fixture(scope='module')
def workflows():
    return [json.loads((DEPLOY / name).read_text(encoding='utf-8'))
            for name in ('analysis-lab-manual.json', 'analysis-lab-inspect.json')]


def _nodes(definition):
    return {node['name']: node for node in definition['nodes']}


def _targets(definition, source, branch=0):
    return [edge['node'] for edge in definition['connections'][source]['main'][branch]]


def test_exported_definitions_match_the_generator(workflows):
    source = PILOT / 'scripts' / 'export_analysis_lab_workflows.py'
    spec = importlib.util.spec_from_file_location('analysis_lab_export', source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    assert generator.export_workflows() == workflows


def test_manual_graph_dispatches_exact_native_order_and_stops_at_pending(workflows):
    from triz.pipeline import stage_list
    manual = workflows[0]
    native = stage_list()[:12]
    nodes = _nodes(manual)
    stages = [node for node in manual['nodes'] if node['type'].endswith('.httpRequest')
              and node['parameters']['url'].endswith('/stage')]
    actual_keys = [json.loads(re.search(r'stage_key:("[^"\\]*")',
                   node['parameters']['jsonBody']).group(1)) for node in stages]
    assert actual_keys == [stage['key'] for stage in native]
    assert all(node['name'].startswith(f'{index:02d} ') and native[index]['label'] in node['name']
               for index, node in enumerate(stages))
    assert 's10_feedback' not in actual_keys
    ready = next(node for node in manual['nodes'] if node['type'].endswith('.if'))
    assert ready['parameters']['conditions']['conditions'][0]['leftValue'] == '={{ $json.continue_execution }}'
    switch = next(node for node in manual['nodes'] if node['type'].endswith('.switch'))
    output = next(node for node in manual['nodes'] if node['type'].endswith('.noOp'))
    assert _targets(manual, ready['name'], 0) == [switch['name']]
    assert _targets(manual, ready['name'], 1) == [output['name']]
    assert output['name'] not in manual['connections']
    rules = switch['parameters']['rules']['values']
    assert [rule['conditions']['conditions'][0]['rightValue'] for rule in rules] == actual_keys
    assert all(rule['conditions']['conditions'][0]['leftValue'] == '={{ $json.next_stage_key }}' for rule in rules)
    assert switch['parameters']['options']['fallbackOutput'] == 'extra'
    for index, node in enumerate(stages):
        assert _targets(manual, switch['name'], index) == [node['name']]
        assert _targets(manual, node['name']) == [ready['name']]
    assert _targets(manual, switch['name'], len(stages)) == [output['name']]
    assert all(target in nodes for branches in manual['connections'].values()
               for branch in branches['main'] for target in [edge['node'] for edge in branch])


def test_manual_begin_and_resume_inputs_preserve_client_carried_state(workflows):
    manual = workflows[0]
    form = next(node for node in manual['nodes'] if node['type'].endswith('.formTrigger'))
    fields = form['parameters']['formFields']['values']
    assert [field['fieldLabel'] for field in fields] == [
        'raw_query', 'mode', 'budget_usd', 'continuation', 'human_response']
    mode = next(field for field in fields if field['fieldLabel'] == 'mode')
    assert {value['option'] for value in mode['fieldOptions']['values']} == {'STANDARD', 'QUICK', 'DEEP'}
    normalize = next(node for node in manual['nodes'] if node['type'].endswith('.code'))
    begin = next(node for node in manual['nodes'] if node['type'].endswith('.httpRequest')
                 and node['parameters']['url'].endswith('/begin'))
    ready = next(node for node in manual['nodes'] if node['type'].endswith('.if'))
    assert _targets(manual, form['name']) == [normalize['name']]
    assert _targets(manual, normalize['name']) == [begin['name']]
    assert _targets(manual, begin['name']) == [ready['name']]
    assert begin['parameters']['jsonBody'] == '={{ JSON.stringify($json) }}'


def _normalize(definition, payload):
    node = shutil.which('node')
    if not node:
        pytest.skip('Local Node is unavailable')
    code = next(item['parameters']['jsCode'] for item in definition['nodes'] if item['type'].endswith('.code'))
    script = '''let text = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => text += chunk);
process.stdin.on('end', () => {
  const request = JSON.parse(text);
  try {
    const result = new Function('$input', request.code)({first: () => ({json: request.payload})});
    process.stdout.write(JSON.stringify({result}));
  } catch (error) {
    process.stdout.write(JSON.stringify({error: error.name}));
  }
});'''
    result = subprocess.run([node, '-e', script], input=json.dumps({'code': code, 'payload': payload}),
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_actual_input_code_keeps_query_and_manual_response_without_paid_replay(workflows):
    manual = workflows[0]
    result = _normalize(manual, {'raw_query': '  fixture "problem"  '})['result'][0]['json']
    assert result == {'raw_query': 'fixture "problem"', 'mode': 'STANDARD', 'budget_usd': 5,
                      'continuation': '', 'human_response': None}
    response = {'interrupt_id': 'current-interrupt', 'answers': ['fixture answer']}
    result = _normalize(manual, {'continuation': ' lab1.fixture.signature ',
                               'human_response': json.dumps(response)})['result'][0]['json']
    assert result['raw_query'] == ''
    assert result['continuation'] == 'lab1.fixture.signature'
    assert result['human_response'] == response
    assert _normalize(manual, {'human_response': '[]'}) == {'error': 'Error'}
    assert _normalize(manual, {'human_response': '{invalid'}) == {'error': 'SyntaxError'}


def test_inspector_splits_whole_candidate_validation_records(workflows):
    inspection = workflows[1]
    form = next(node for node in inspection['nodes'] if node['type'].endswith('.formTrigger'))
    request = next(node for node in inspection['nodes'] if node['type'].endswith('.httpRequest'))
    split = next(node for node in inspection['nodes'] if node['type'].endswith('.splitOut'))
    assert [field['fieldLabel'] for field in form['parameters']['formFields']['values']] == ['continuation', 'candidate_id']
    assert request['parameters']['url'].endswith('/internal/lab/inspect')
    assert 'candidate_id:String($json.candidate_id' in request['parameters']['jsonBody']
    assert _targets(inspection, form['name']) == [request['name']]
    assert _targets(inspection, request['name']) == [split['name']]
    assert split['parameters'] == {'fieldToSplitOut': 'solutions', 'include': 'allOtherFields',
                                   'options': {'destinationFieldName': 'solution_validation'}}
    assert split['name'] not in inspection['connections']


def test_workflows_do_not_save_analysis_retry_paid_calls_or_embed_credentials(workflows):
    for definition in workflows:
        assert definition['active'] is False
        assert definition['pinData'] == {}
        assert definition['settings']['saveDataSuccessExecution'] == 'none'
        assert definition['settings']['saveDataErrorExecution'] == 'none'
        assert definition['settings']['saveManualExecutions'] is False
        assert definition['settings']['saveExecutionProgress'] is False
        assert len({node['id'] for node in definition['nodes']}) == len(definition['nodes'])
        for node in definition['nodes']:
            assert not node.get('retryOnFail', False)
            assert not node.get('continueOnFail', False)
            assert 'maxTries' not in node
            assert 'Authorization' not in json.dumps(node['parameters'])
            assert 'api_key' not in json.dumps(node['parameters']).lower()
            if node['type'].endswith('.httpRequest'):
                assert re.fullmatch(r'http://trizbackend\.railway\.internal:8000/internal/lab/(begin|stage|inspect)',
                                    node['parameters']['url'])
                assert node['parameters']['authentication'] == 'genericCredentialType'
                assert node['parameters']['genericAuthType'] == 'httpHeaderAuth'
                assert set(node['credentials']['httpHeaderAuth']) == {'id', 'name'}
                assert 'headerParameters' not in node['parameters']
        # Empty input defaults and pinData ensure no analysis query/token is embedded.
        forms = [node for node in definition['nodes'] if node['type'].endswith('.formTrigger')]
        assert all('fieldValue' not in field and 'defaultValue' not in field for node in forms
                   for field in node['parameters']['formFields']['values'])
