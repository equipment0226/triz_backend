"""Owner resolution of invalid citations without regenerating the failed analysis."""
import copy
import json
from .authoring import validate_basis,validate_result,SynthesizedSolution,DocumentCoherence
from .domain import PatentError,digest

SCHEMAS={'synthesized_solution':SynthesizedSolution,'document_coherence':DocumentCoherence}


def source_value(ref,context):
    try:
        value=context[ref['artifact']]
        if ref['pointer']:
            if not ref['pointer'].startswith('/'):return None
            for key in ref['pointer'][1:].split('/'):
                key=key.replace('~1','/').replace('~0','~')
                value=value[int(key)] if isinstance(value,list) else value[key]
        return value
    except (KeyError,TypeError,IndexError,ValueError):return None


def build(kind,candidate,context,ticket):
    if kind not in SCHEMAS:return None
    candidate=SCHEMAS[kind].model_validate(candidate).model_dump()
    issues=[]
    collections=('facts','changes') if kind=='synthesized_solution' else ('checks',)
    for collection in collections:
        for index,item in enumerate(candidate[collection]):
            invalid=[]
            for ref in item['basis']:
                try:validate_basis(ref,context)
                except PatentError:
                    value=source_value(ref,context)
                    invalid.append({**ref,'source_text':value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2) if value is not None else None,
                        'reason':'인용문이 지정한 원문과 일치하지 않습니다.' if isinstance(value,str) else '인용 위치가 원문 문장이 아니거나 존재하지 않습니다.'})
            if invalid:
                issue_id='EVC_'+digest([ticket['task_id'],collection,index])[:20]
                statement=item.get('statement') or item.get('explanation') or item.get('after')
                issues.append({'id':issue_id,'collection':collection,'index':index,
                    'statement':statement,'references':invalid,
                    'question':'이 분석 내용을 어떻게 반영할까요? 확인한 내용으로 수정하거나, 미확인으로 남기거나, 제외해 주세요.'})
    if not issues:return None
    return {'artifact_type':kind,'task_id':ticket['task_id'],'input_snapshot_id':ticket['input_snapshot_id'],
        'read_version_ids':ticket['read_version_ids'],'tool_name':ticket['tool_name'],
        'review_role':ticket['review_role'],'candidate':candidate,'issues':issues,
        'gate_id':'G1' if kind=='synthesized_solution' else 'G2',
        'questions':[{'id':i['id'],'question':i['question'],'reason':'분석 내용: '+i['statement'],
            'affected_fields':['invention'] if kind=='synthesized_solution' else ['specification'],'blocking':True} for i in issues]}


def install(service,conn,case,value):
    if set(value['read_version_ids'])!=set(service.readset(case,value['review_role'],value['tool_name'])):
        raise PatentError('EVIDENCE_INPUT_CHANGED','근거 입력이 변경되어 해당 분석을 확인 대상으로 사용할 수 없습니다.')
    version=service.repo.artifact(conn,case,'evidence_clarification',value,value['read_version_ids'],producer='EVIDENCE_VALIDATOR')
    case['execution_status'],case['waiting_for'],case['last_error']='WAITING_HUMAN','EVIDENCE_CLARIFICATION',None
    case['evidence_gate']=value['gate_id']
    return version


def resolve(service,conn,owner,case,payload):
    version=case['artifacts'].get('evidence_clarification')
    if not version or payload.get('clarification_version_id')!=version:
        raise PatentError('EVIDENCE_CONFIRMATION_CHANGED','확인할 근거가 변경됐습니다. 최신 내용을 확인해 주세요.')
    if set(payload)!={'clarification_version_id','resolutions'} or not isinstance(payload['resolutions'],list):
        raise PatentError('EVIDENCE_RESOLUTION_INVALID','각 불일치 항목의 반영 방법을 선택해 주세요.',422)
    clarification=service.repo.record(owner,case['case_id'],version,conn)['payload']
    if set(clarification['read_version_ids'])!=set(service.readset(case,clarification['review_role'],clarification['tool_name'])):
        raise PatentError('EVIDENCE_INPUT_CHANGED','분석 입력이 변경됐습니다. 최신 근거를 확인해 주세요.')
    supplied=payload['resolutions'];ids=[r.get('issue_id') for r in supplied if isinstance(r,dict)]
    if len(ids)!=len(supplied) or any(not isinstance(i,str) for i in ids) or len(ids)!=len(set(ids)) or set(ids)!={i['id'] for i in clarification['issues']}:
        raise PatentError('EVIDENCE_RESOLUTION_INVALID','모든 불일치 항목을 한 번씩 확인해 주세요.',422)
    material=service.material(owner,case,conn);answers=dict(material.get('answers',{}));candidate=copy.deepcopy(clarification['candidate'])
    choices={r['issue_id']:r for r in supplied};excluded={};kind=clarification['artifact_type']
    for issue in clarification['issues']:
        choice=choices[issue['id']];action=choice.get('action');text=choice.get('text','')
        if set(choice)-{'issue_id','action','text'} or action not in ('CORRECT','UNVERIFIED','EXCLUDE') or not isinstance(text,str) or len(text)>3000:
            raise PatentError('EVIDENCE_RESOLUTION_INVALID','올바른 반영 방법과 3,000자 이하의 보완 내용을 입력해 주세요.',422)
        text=text.strip()
        if action=='CORRECT' and not text:
            raise PatentError('EVIDENCE_RESOLUTION_INVALID','확인하거나 수정한 기술 내용을 입력해 주세요.',422)
        if action=='EXCLUDE' and issue['collection']!='checks':
            answers[issue['id']]='사용자가 해당 분석 내용을 제외함. '+text
            excluded.setdefault(issue['collection'],set()).add(issue['index']);continue
        response=text if action=='CORRECT' else '사용자 확인: 이 분석은 근거 미확인 상태로 남깁니다. '+text
        answers[issue['id']]=response
        item=candidate[issue['collection']][issue['index']]
        # User text is new owner evidence. Never relabel the invalid quote as source evidence.
        valid=[]
        for ref in item['basis']:
            try:validate_basis(ref,material);valid.append(ref)
            except PatentError:pass
        item['basis']=[*valid,{'artifact':'answers','pointer':'/'+issue['id'],'excerpt':response[:3000]}]
        if issue['collection']=='facts':
            item['statement']=text if action=='CORRECT' else item['statement']
            item['status']='USER_REPORTED' if action=='CORRECT' else 'UNKNOWN'
            item['rationale']='사용자 보완을 반영함. 원문 인용 검증 또는 측정 검증을 의미하지 않음.'
        elif issue['collection']=='changes':
            item['before']='변경 전 내용은 원문 근거가 확인되지 않아 보류함.'
            item['after']=text if action=='CORRECT' else '미확인 제안: '+item['after']
            item['reason']='사용자 보완: '+response
        else:
            # A user cannot turn an invalid AI review into an independent PASS.
            item['outcome']='UNKNOWN';item['explanation']='인용 불일치에 대한 사용자 보완: '+response
            item['repair_instruction']='사용자 보완과 실제 문서를 대조해 독립 검토에서 다시 확인할 것.'
    for collection,indexes in excluded.items():candidate[collection]=[v for i,v in enumerate(candidate[collection]) if i not in indexes]
    if kind=='synthesized_solution':
        if not candidate['facts']:
            raise PatentError('EVIDENCE_FACT_REQUIRED','초안을 작성할 기술 내용이 모두 제외되었습니다. 최소 한 항목에 확인한 내용을 입력해 주세요.',422)
        def statements(categories):
            return '\n'.join(('미확인 제안: ' if f['status'] in ('UNKNOWN','INFERRED') else '')+f['statement'] for f in candidate['facts'] if f['category'] in categories)
        # Rebuild summaries from retained facts so removed/corrected claims cannot survive in prose.
        candidate['problem']=statements({'PROBLEM'}) or '사용자 보완을 반영한 해결 과제는 기술 사실과 함께 검토해야 합니다.'
        candidate['revised_solution']=statements({'PROBLEM','COMPONENT','MECHANISM','CONSTRAINT','EFFECT','RISK'})
        candidate['working_principle']=statements({'MECHANISM','COMPONENT'}) or '작동 원리는 후속 기술 검토에서 확인해야 합니다.'
        if candidate['changes']:candidate['revised_solution']+='\n사용자 변경사항:\n'+'\n'.join(c['after'] for c in candidate['changes'])
    candidate=SCHEMAS[kind].model_validate(candidate).model_dump()
    validate_result(kind,candidate,{**material,'answers':answers})
    service.invalidate(conn,case,{kind},'OWNER_EVIDENCE_RESOLVED')
    answer_version=service.repo.artifact(conn,case,'answers',answers,[version,*([case['artifacts']['answers']] if 'answers' in case['artifacts'] else [])],producer='OWNER_EVIDENCE_RESOLUTION')
    accepted=service.repo.artifact(conn,case,kind,candidate,[version,answer_version,*clarification['read_version_ids']],producer='OWNER_EVIDENCE_RESOLUTION')
    if kind=='synthesized_solution':service.repo.artifact(conn,case,'synthesis_questions',{'questions':candidate['questions']},[accepted],producer='OWNER_EVIDENCE_RESOLUTION')
    service.repo.append(conn,case['case_id'],'evidence_resolution',{'actor':owner,'clarification_version_id':version,
        'accepted_version_id':accepted,'resolutions':supplied,'method':'OWNER_CORRECTION_NO_REGENERATION'})
    case['artifacts'].pop('evidence_clarification',None);case.pop('evidence_gate',None)
    case['last_error']=None;case['execution_status']='WAITING_HUMAN';case['waiting_for']=None
    service.retire_stale_queued(conn,case)
    try:service.auto_resume(conn,owner,case)
    except PatentError as exc:
        if 'BUDGET' not in exc.code:raise
        case['execution_status'],case['last_error']='PAUSED_BUDGET',exc.code
    return {'accepted_version_id':accepted,'analysis_regenerated':False}
