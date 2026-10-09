"""Export the manual native-stage lab and individual solution inspector for n8n."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

PILOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PILOT))
from triz.lab_manifest import build_manifest

PREFIX = 'TRIZ API 검증'
MANUAL_ID = 'TRIZAnalysisLabManual20261009'
INSPECT_ID = 'TRIZAnalysisLabInspect20261009'
API_BASE = 'http://trizbackend.railway.internal:8000'
CREDENTIAL = {'httpHeaderAuth': {'id': 'TRIZStudioV2Auth', 'name': 'TRIZ Studio Service'}}
SETTINGS = {'executionOrder': 'v1', 'executionTimeout': 14400,
    'saveDataSuccessExecution': 'none', 'saveDataErrorExecution': 'none',
    'saveManualExecutions': False, 'saveExecutionProgress': False, 'timezone': 'Asia/Seoul'}


def node(name, kind, version, x, y, parameters, **extra):
    return {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'triz-analysis-lab/' + name)),
        'name': name, 'type': 'n8n-nodes-base.' + kind, 'typeVersion': version,
        'position': [x, y], 'parameters': parameters, **extra}


def form(name, fields, description):
    return node(name, 'formTrigger', 2.4, 0, 0,
        {'formTitle': name, 'formDescription': description,
         'formFields': {'values': fields}, 'responseMode': 'onReceived', 'options': {}},
        webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'triz-analysis-lab/form/' + name)),
        notes='워크플로는 비활성 상태입니다. 이 노드의 Test URL에서 수동 입력합니다. 실제 질의·continuation을 노드 설정이나 pinData에 저장하지 마세요.')


def field(label, description):
    return {'fieldLabel': label, 'fieldType': 'textarea', 'placeholder': description,
        'requiredField': False}


def http(name, path, body, x, y, notes=''):
    return node(name, 'httpRequest', 4.2, x, y,
        {'method': 'POST', 'url': API_BASE + '/internal/lab/' + path,
         'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth',
         'sendBody': True, 'specifyBody': 'json', 'jsonBody': body,
         'options': {'timeout': 3600000}}, credentials=CREDENTIAL, retryOnFail=False,
        notes=notes, notesInFlow=True)


def edge(target):
    return {'node': target, 'type': 'main', 'index': 0}


def workflow(wid, title, nodes, connections, description):
    return {'id': wid, 'name': PREFIX + ' — ' + title, 'active': False,
        'nodes': nodes, 'connections': connections, 'settings': dict(SETTINGS),
        'pinData': {}, 'tags': [], 'description': description}


def export_workflows():
    manifest = build_manifest()
    stages = manifest['stages']
    fields = [field('raw_query', '처음 실행할 때 문제를 입력합니다. 재개할 때는 비워둡니다.'),
        {'fieldLabel': 'mode', 'fieldType': 'dropdown', 'fieldOptions': {
            'values': [{'option': mode} for mode in ('STANDARD', 'QUICK', 'DEEP')]}, 'requiredField': False},
        field('budget_usd', '기본 5. 0 초과 5 이하. 동일 테스트 전체 호출 한도입니다.'),
        field('continuation', '재개할 때 이전 최종 출력의 continuation 전체를 복사합니다.'),
        field('human_response', '확인·선택 응답 JSON. 현재 pending.interrupt_id를 포함해야 합니다.')]
    form_node = form('수동 질의 또는 확인 후 재개', fields,
        '처음에는 raw_query를 입력합니다. 확인이 필요하면 종료 출력의 pending을 읽고, '
        'continuation과 human_response를 입력해 다시 실행합니다. 피드백·학습 단계는 실행하지 않습니다.')
    normalize = node('입력 JSON 확인', 'code', 2, 250, 0, {'jsCode': '''const input = $input.first().json;
const text = (key) => String(input[key] ?? '').trim();
let human = null;
if (text('human_response')) {
  human = JSON.parse(text('human_response'));
  if (!human || typeof human !== 'object' || Array.isArray(human)) throw new Error('human_response는 JSON 객체여야 합니다.');
}
return [{json: {raw_query: text('raw_query'), mode: text('mode') || 'STANDARD',
  budget_usd: text('budget_usd') ? Number(text('budget_usd')) : 5,
  continuation: text('continuation'), human_response: human}}];'''})
    begin = http('새 분석 또는 사용자 응답 반영', 'begin', '={{ JSON.stringify($json) }}', 510, 0,
        '기존 MCP 서버의 triz_lab_execute를 사용합니다. 새 분석을 만들거나 현재 확인 응답을 반영하고 다음 stage만 결정합니다. 운영 run을 생성하지 않습니다.')
    ready = node('실행할 stage 있음?', 'if', 2.2, 780, 0, {'conditions': {
        'options': {'caseSensitive': True, 'typeValidation': 'strict', 'version': 2},
        'conditions': [{'id': 'ready', 'leftValue': '={{ $json.continue_execution }}',
            'rightValue': True, 'operator': {'type': 'boolean', 'operation': 'true', 'singleValue': True}}],
        'combinator': 'and'}, 'options': {}})
    rules, stage_nodes = [], []
    connections = {form_node['name']: {'main': [[edge(normalize['name'])]]},
        normalize['name']: {'main': [[edge(begin['name'])]]},
        begin['name']: {'main': [[edge(ready['name'])]]},
        ready['name']: {'main': [[edge('기존 stage 순서')], [edge('출력 · 사용자 확인 또는 완료')]]}}
    for stage in stages:
        key = stage['key']
        title = f"{stage['index']:02d} {key} · {stage['label']}"
        rules.append({'conditions': {'options': {'caseSensitive': True, 'typeValidation': 'strict', 'version': 2},
            'conditions': [{'id': key, 'leftValue': '={{ $json.next_stage_key }}', 'rightValue': key,
                'operator': {'type': 'string', 'operation': 'equals'}}], 'combinator': 'and'},
            'renameOutput': True, 'outputKey': key})
        prompts = ', '.join(stage.get('literal_prompt_ids', []))
        knowledge = ', '.join(stage.get('knowledge_files', []))
        notes = ('원본 함수: ' + stage['function'] + '\n기존 node·agent·prompt를 그대로 실행합니다. '
            '분기·병렬 순서는 원본 함수가 제어하며 실제 실행 순서는 출력 steps에서 확인합니다.\n'
            '프롬프트 후보: ' + prompts + '\n지식 자료: ' + knowledge)
        stage_nodes.append(http(title, 'stage', '= {{}}', 1310, stage['index'] * 180 - 500, notes))
        stage_nodes[-1]['parameters']['jsonBody'] = ('={{ JSON.stringify({continuation:$json.continuation, '
            'stage_key:' + json.dumps(key) + '}) }}')
        connections[title] = {'main': [[edge('실행할 stage 있음?')]]}
    switch = node('기존 stage 순서', 'switch', 3.2, 1040, 0,
        {'rules': {'values': rules}, 'options': {'fallbackOutput': 'extra'}})
    connections[switch['name']] = {'main': [[edge(item['name'])] for item in stage_nodes]
        + [[edge('출력 · 사용자 확인 또는 완료')]]}
    output = node('출력 · 사용자 확인 또는 완료', 'noOp', 1, 1670, 760, {},
        notes='pending은 수동 확인 요청입니다. 다음 실행 폼에 continuation과 응답을 넣습니다. '
        'solutions는 제외된 후보까지 포함한 개별 검증 결과입니다. steps는 node/agent/prompt/input/output/verdict 기록입니다. '
        'S9 보고서는 inline 출력이며 S10 피드백·강화학습은 없습니다.', notesInFlow=True)
    manual = workflow(MANUAL_ID, '수동 문제 분석', [form_node, normalize, begin, ready, switch, *stage_nodes, output],
        connections, '기존 TRIZ의 12단계와 동일 prompt/agent/knowledge/MCP/Qdrant를 사용하는 memory-only 수동 분석. 사용자 확인 시 종료하고 출력으로 재개.')
    inspect_form = form('해결안 개별 검증 입력', [field('continuation', '기존 수동 분석 출력의 continuation 전체'),
        field('candidate_id', '특정 concept_id를 입력하거나 비워서 모든 해결안을 표시')],
        '기존 분석의 품질 판정, 제약 검토, 실제 근거, 독립 평가와 제외 이유를 해결안별로 확인합니다. 추가 모델 호출은 없습니다.')
    inspect_http = http('해결안별 판정·근거 조회', 'inspect',
        '={{ JSON.stringify({continuation:String($json.continuation || "").trim(), '
        'candidate_id:String($json.candidate_id || "").trim()}) }}', 350, 0,
        '서명된 출력 값만 읽습니다. 운영 분석 DB 조회·저장과 추가 모델 호출은 없습니다.')
    split = node('해결안 하나씩 출력', 'splitOut', 1, 700, 0,
        {'fieldToSplitOut': 'solutions', 'include': 'allOtherFields',
         'options': {'destinationFieldName': 'solution_validation'}},
        notes='각 item의 solution_validation에 생성 후보, 포함/제외 이유, 품질 검토, 제약 조건, 근거, 개별 평가를 표시합니다.', notesInFlow=True)
    inspection = workflow(INSPECT_ID, '해결안 개별 검증', [inspect_form, inspect_http, split],
        {inspect_form['name']: {'main': [[edge(inspect_http['name'])]]},
         inspect_http['name']: {'main': [[edge(split['name'])]]}},
        '추가 과금 없이 기존 테스트 출력의 해결안을 개별 검증하는 흐름. 채택/보상 피드백이나 학습 데이터를 저장하지 않음.')
    return [manual, inspection]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=PILOT.parent / 'deploy' / 'n8n')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for definition, name in zip(export_workflows(), ('analysis-lab-manual.json', 'analysis-lab-inspect.json')):
        path = args.output_dir / name
        path.write_text(json.dumps(definition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        files.append(str(path))
    print(json.dumps({'files': files, 'workflow_count': 2, 'stage_count': 12}, ensure_ascii=False))


if __name__ == '__main__':
    main()
