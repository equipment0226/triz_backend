"""Bounded semantic features from currently stored problem inputs, never labels."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from .contracts import digest

CONTRACT='confirmed-context-v1'
LIMIT=512
TEXT_LIMIT=512
IGNORED={'id','created_at','updated_at','timestamp','source','confidence','rationale','evidence_ids',
         'derived_from_tc','derived_from_tc_ids','hypothesis_ids','evidence_refs'}
UNITS={'mm':('m','0.001'),'cm':('m','0.01'),'m':('m','1'),
       'mW':('W','0.001'),'W':('W','1'),'kW':('W','1000'),
       'g':('kg','0.001'),'kg':('kg','1'),'ms':('s','0.001'),'s':('s','1')}


def normalized(value):
    if hasattr(value,'model_dump'): value=value.model_dump(mode='json')
    if isinstance(value,str): return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())
    if isinstance(value,list): return sorted((normalized(v) for v in value),key=repr)
    if isinstance(value,dict):
        value=dict(value)
        unit=value.get('unit','').strip() if isinstance(value.get('unit'),str) else ''
        if unit in UNITS and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)',str(value.get('value','')).strip()):
            try:
                canonical,factor=UNITS[unit]
                number=Decimal(str(value['value']).strip())*Decimal(factor)
                value.update(value=format(number.normalize(),'f'),unit=canonical)
            except InvalidOperation: pass
        return {k:(' '.join(v.split()) if k=='unit' and isinstance(v,str) else normalized(v)) for k,v in sorted(value.items())
            if k not in IGNORED and not k.endswith('_ids') and k!='derived_from_tc_id'}
    return value


def build(state):
    source=dict(domain={k:getattr(state.domain,k) for k in ('problem_type','physical_scope','target_system','super_system','sub_systems','operating_env')},
        problem={k:getattr(state.intake.frame,k) for k in ('restated_problem','symptom','when_where','success_criteria')},
        functions=state.analysis.function_edges,technical=state.definition.technical_contradictions,
        physical=state.definition.physical_contradictions,resources=state.analysis.resources,constraints=state.constraints.items)
    data=normalized(source)
    groups={}
    def flatten(path,value,out):
        if isinstance(value,dict):
            for k,v in value.items(): flatten(path+'.'+k,v,out)
        elif isinstance(value,list):
            if not value: out.add(path+'=UNKNOWN')
            for v in value: flatten(path,v,out)
        else:
            token=str(value) if value not in ('',None) else 'UNKNOWN'
            out.add(path+'='+token)
    for key,value in data.items():
        tokens=set(); flatten(key,value,tokens); groups[key]=tokens
    # Preserve associations between constraint subject and polarity/numeric bounds.
    critical=set()
    for row in data['constraints']:
        subject=row.get('parameter') or row.get('statement') or 'UNKNOWN'
        for key in ('kind','hard','operator','value','unit','zone'):
            token='constraint:'+subject+':'+key+'='+str(row.get(key,'UNKNOWN'))
            groups['constraints'].add(token)
            if row.get('hard') or row.get('kind')=='must_not_have': critical.add(token)
    # Deterministic priority: prohibitions/hard constraints precede auxiliary context.
    ordered=sorted(critical)
    for key in ('constraints','resources','technical','physical','functions','domain','problem'):
        ordered.extend(sorted(groups[key]-critical))
    selected=ordered[:LIMIT]
    tokens=[t[:TEXT_LIMIT] for t in selected]
    omitted={key:sum(t not in selected for t in values) for key,values in groups.items()}
    return dict(contract=CONTRACT,tokens=tokens,limit=LIMIT,omitted=omitted,
        text_limit=TEXT_LIMIT,truncated_text_count=sum(len(t)>TEXT_LIMIT for t in selected),
        provenance=dict(semantic_hash=digest(data),input_snapshot_id=state.scratch.get('ax_snapshot_id'),
            versions=dict(state.scratch.get('ax_members',{}))))
