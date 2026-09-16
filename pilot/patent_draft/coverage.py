"""Deterministic review targets and delivery scope for an immutable snapshot."""
from .domain import digest, PatentError
from .drawings import svg


def targets(material, versions):
    result=[]
    fields={'invention':('features','effects'),'claims':('claims',),'specification':('sections',),'drawings':('drawings',),'attachments':('documents',)}
    for kind,version in sorted(versions.items()):
        value=material[kind]
        # The whole artifact binds metadata as well as each material claim/paragraph/figure.
        result.append({'target_id':version,'content_hash':digest(value),'artifact_type':kind,'pointer':''})
        for field in fields.get(kind,()):
            for index,item in enumerate(value.get(field,[])):
                pointer=f'/{field}/{index}'
                result.append({'target_id':version+pointer,'content_hash':digest(item),'artifact_type':kind,'pointer':pointer})
                if kind=='attachments':
                    for page_index,page in enumerate(item.get('pages',[])):
                        page_pointer=f'{pointer}/pages/{page_index}'
                        result.append({'target_id':version+page_pointer,'content_hash':digest(page),
                                       'artifact_type':kind,'pointer':page_pointer})
        if kind=='specification':
            result.append({'target_id':version+'/abstract','content_hash':digest(value.get('abstract')),
                           'artifact_type':kind,'pointer':'/abstract'})
    return result


def validate(checks, expected):
    wanted={t['target_id']:t['content_hash'] for t in expected}
    actual={t['target_id']:t['content_hash'] for t in checks}
    if len(actual)!=len(checks) or actual!=wanted:
        raise PatentError('REVIEW_TARGET_COVERAGE_INVALID','청구항·설명 문단·효과·도면의 개별 검토가 누락됐습니다.',503)


def delivery_scope(case,material):
    import hashlib
    figures=svg(material.get('drawings',{'drawings':[]}))
    return {'snapshot_id':case['snapshot_id'],'epoch':case['epoch'],
        'content_hashes':{k:digest(v) for k,v in sorted(material.items())},
        'figure_hashes':{k:hashlib.sha256(v).hexdigest() for k,v in sorted(figures.items())},
        'rulepack_version':case['rulepack_version'],'policy_version':case['policy_version'],
        'model_config_hash':digest(case['model_config']),'form_version':case['form_version'],
        'form_registry_hash':case.get('form_registry_hash')}
