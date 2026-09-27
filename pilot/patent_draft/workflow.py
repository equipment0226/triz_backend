"""Versioned authoring contract, pinned to each case before any model work."""
import json
from pathlib import Path
from .domain import digest, PatentError


def load_contract():
    from .prompts_registry import load_prompts
    root = Path(__file__).parent / 'config'
    process = json.loads((root / 'process.json').read_text(encoding='utf-8'))
    template = json.loads((root / 'templates/kr_general.json').read_text(encoding='utf-8'))
    prompts = load_prompts()
    value = {**process, 'template_id': template['id'], 'sections': template['sections'],
             'documents': template['documents'], 'common_prompt': prompts['common'], 'prompts': prompts}
    from .forms import SECTIONS
    if [s['id'] for s in value['sections']] != list(SECTIONS):
        raise PatentError('WORKFLOW_INVALID', '초안 서식과 작성 프로세스가 일치하지 않습니다.', 503)
    ids = [n['id'] for n in value['nodes']]
    if len(ids) != len(set(ids)) or any(e['from'] not in ids or e['to'] not in ids for e in value['edges']):
        raise PatentError('WORKFLOW_INVALID', '노드 연결을 확인해야 합니다.', 503)
    return {**value, 'contract_hash': digest(value)}


def automatic(case):
    return case.get('workflow_mode') == 'AUTOMATIC'


def source_context(state, concept_id):
    """Allowlisted DB context; no costs, sessions, scratch or other ideas."""
    intake = state.get('intake') or {}
    return {
        'raw_query': state.get('raw_query', ''),
        **{key: state.get(key, {}) for key in ('domain', 'constraints', 'confirm', 'analysis', 'definition')},
        'clarifications': intake.get('clarify_turns', []),
        'attachments': [{k: a[k] for k in ('id', 'filename', 'extracted_text', 'extracted_facts') if k in a}
                        for a in intake.get('attachments', [])],
        'constraint_checks': [x for x in state.get('constraint_checks', []) if x.get('concept_id') == concept_id],
    }


def mapping(source, contract):
    def read(path):
        value = source
        for key in path.split('.'):
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value
    return {'sections': [{**section, 'inputs': [
        {'source_path': path, 'value': read(path), 'evidence_status': 'SOURCE_NOT_REVERIFIED'}
        for path in section['source_paths'] if read(path) not in (None, '', [], {})
    ]} for section in contract['sections']]}


def instruction(kind, material, fallback):
    import re
    contract = material.get('workflow_contract')
    if not contract:
        return ('Legacy guided case: where synthesized_solution or drafting_keywords is absent, use the pinned '
                'source, application_context and answers directly. Do not invent intermediate artifacts.\n' + fallback)
    prompt = contract['common_prompt'] + '\n' + contract['prompts'].get(kind, fallback)
    # Bind template variables to separately supplied typed JSON; never interpolate
    # source documents into the trusted system instruction.
    return re.sub(r'\{\{\s*([a-z_]+)\s*\}\}', lambda m: '[input JSON: '+('drafting_template' if m[1]=='workflow_contract' else m[1])+']', prompt)


def progress(case, material, reviews, task_states=(), approvals=None, records=()):
    contract = material.get('workflow_contract', {})
    clarification=material.get('evidence_clarification')
    edges=list(contract.get('edges',[]))
    if clarification:
        target='P1.K' if clarification['artifact_type']=='synthesized_solution' else 'P4.D'
        edges.append({'from':clarification['gate_id'],'to':target,'when':'인용 불일치에 대한 사용자 보완 적용; 같은 분석을 재생성하지 않음'})
    roles = {r['role'] for r in reviews}
    waits = {'G0': 'APPLICATION_CONTEXT', 'G1': 'QUESTIONS', 'G2': 'PATCH_REVIEW', 'G3': 'FINAL_REVIEW'}
    def state(node):
        clarification=material.get('evidence_clarification')
        if clarification and (node['id']==clarification['gate_id'] or node.get('tool')==clarification['tool_name']):
            return 'WAITING'
        if case.get('waiting_for') == waits.get(node['id']) and node['id'] in waits:
            return 'WAITING'
        if node['type'] == 'gate':
            from .intake import complete, unanswered
            passed = {'G0': complete(material) and bool(case.get('provider_authorization')),
                      'G1': 'questions' in material and not unanswered(material),
                      'G2': 'GLOBAL_FINAL' in roles,
                      'G3': set(approvals or {}) == {'G1','G2'}}
            return 'COMPLETED' if passed.get(node['id']) else 'PENDING'
        matching = [t for t in task_states if t['tool_name'] == node.get('tool') and t['review_role'] == node.get('review_role')]
        active = next((t for t in matching if t['status'] in ('QUEUED','RUNNING')), None)
        if active:
            return active['status']
        if node['id'] == 'P5.1' and case.get('execution_status') == 'COMPLETED':
            return 'COMPLETED'
        if node['id'] == 'P5.2' and any(r.get('manifest', {}).get('snapshot_id') == case['snapshot_id'] for r in records):
            return 'COMPLETED'
        if node['outputs'] and all(k in material or k in roles for k in node['outputs']):
            return 'COMPLETED'
        failed = next((t for t in matching if t['status'] in ('FAILED','UNCERTAIN')), None)
        return failed['status'] if failed else 'PENDING'
    return {'version': contract.get('version'), 'mode': case.get('workflow_mode', 'GUIDED'),
            'stages': contract.get('stages', []), 'edges': edges,
            'nodes': [{**node, 'status': state(node),
                       'inputs':[*node['inputs'],*(['evidence_clarification'] if clarification and node['id']==clarification['gate_id'] else [])],
                       'prompt_text': contract.get('prompts', {}).get(node.get('prompt'), ''),
                       'prompt_file': 'prompts/' + node['prompt'] + '.md' if node.get('prompt') else None}
                      for node in contract.get('nodes', [])],
            'review_count': len(reviews), 'waiting_for': case.get('waiting_for')}


def drafting_nodes(material, stages):
    contract = material.get('workflow_contract') or load_contract()
    return [(n['outputs'][0], n['tool']) for n in contract['nodes']
            if n['stage'] in stages and n['type'] == 'subprocess' and n['tool']
            and (material.get('workflow_contract') or not n.get('automatic_only'))]


def describe(service, owner, case, material, reviews):
    from sqlalchemy import select
    from .repository import tasks
    with service.repo.engine.connect() as conn:
        rows = conn.execute(select(tasks.c.status, tasks.c.body).where(tasks.c.case_id == case['case_id'])).all()
    states = []
    for row in rows:
        ticket = json.loads(row.body)['ticket']
        if ticket['epoch'] == case['epoch'] and set(ticket['read_version_ids']) == set(service.readset(case, ticket['review_role'], ticket['tool_name'])):
            states.append({'status': row.status, 'tool_name':ticket['tool_name'], 'review_role':ticket['review_role']})
    return progress(case, material, reviews, states, service.approvals(owner, case),
                    service.repo.records(owner, case['case_id'], 'export'))
