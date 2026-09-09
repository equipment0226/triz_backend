"""Step-specific ARIZ presentation, retaining legacy text and recorded verdicts."""
import json
import re

PARTS={'1':'문제 분석','2':'작용 영역·시간과 자원','3':'이상해결책과 물리적 모순',
       '4':'자원 동원과 해결 방향','5':'지식베이스 적용','6':'문제 재정의','7':'해결안 검증'}
FIELDS={'idea_title':'해결안','ifr_satisfaction_pct':'IFR 충족도 (%)','is_tradeoff':'절충 여부',
        'constraint_ok':'제약 충족','note':'판정 근거','side_effects':'잠재 부작용',
        'title':'제목','idea':'적용안','name':'자원','resource':'자원','type':'종류',
        'in_oz':'OZ 내 존재','available_ot':'OT 중 가용','availability':'가용성',
        'description':'내용','likelihood':'발생 가능성','probability':'발생 가능성',
        'mitigation':'대응책','countermeasure':'대응책','effect':'부작용','risk':'위험'}

def value_text(value):
    if isinstance(value,bool): return '예' if value else '아니요'
    if isinstance(value,dict): return ' / '.join(f'{FIELDS.get(k,k)}: {value_text(v)}' for k,v in value.items())
    if isinstance(value,list): return ' / '.join(map(value_text,value))
    return str(value if value is not None else '—')

def content_text(value):
    """Keep one complete resource/proposal per row, including any named fields."""
    if isinstance(value,str):
        try:
            data=json.loads(value)
        except (ValueError,TypeError):
            return value
        return value_text(data) if isinstance(data,(dict,list)) else value
    return value_text(value)


def text_rows(value):
    """Split only explicit labels, numbering or paragraph boundaries; do not infer facts."""
    if not isinstance(value,str):
        value=value_text(value)
    try:
        data=json.loads(value)
    except (ValueError,TypeError): data=None
    if isinstance(data,dict): return [[FIELDS.get(k,k),value_text(v)] for k,v in data.items()]
    labels=r'(?:TC[12]|T[123](?:\([^)]*\))?|도구(?:\([^)]*\))?|대상(?:\([^)]*\))?|현재|요구|구현|사유|내부 자원|외부 자원|상위\s?시스템 자원|폐기물[·/ ]부산물 자원|파생 자원|상태\s?[AB]|유익 작용|유해 작용)'
    starts=list(re.finditer(r'(?<!\S)('+labels+r')\s*[:：]',value))
    if starts:
        rows=[]
        if value[:starts[0].start()].strip(): rows.append(['분석',value[:starts[0].start()].strip()])
        for i,m in enumerate(starts):
            end=starts[i+1].start() if i+1<len(starts) else len(value)
            rows.append([m.group(1),value[m.end():end].strip()])
        return rows
    paragraphs=[p.strip() for p in re.split(r'\n\s*\n|\n(?=\s*(?:[-•]|\d+[.)])\s)',value) if p.strip()]
    if len(paragraphs)==1:
        paragraphs=[p.strip() for p in re.split(r'(?<=[.!?])\s+(?=[가-힣A-Z(])',value) if p.strip()]
    return [[str(i+1),p] for i,p in enumerate(paragraphs)] or [['분석','기록 없음']]

def _record(state,node,key):
    for step in reversed(state.steps):
        if step.node==node and isinstance(step.output_json,dict) and step.output_json.get(key):
            return step.output_json[key]
    return []

def build(state):
    run=state.solve.ariz
    if not run: return dict(parts=[],verdicts=[],resources=[],proposals=[])
    verdicts=[v for v in (run.verdicts or _record(state,'s5_ariz_p7','verdicts')) if isinstance(v,dict)]
    parts={}
    for index,step in enumerate(run.steps):
        part=step.step_code.split('.')[0]
        structured=bool(step.table_columns and step.table_rows and all(len(row)==len(step.table_columns) for row in step.table_rows))
        columns=step.table_columns if structured else ['항목','분석 내용']
        rows=step.table_rows if structured else text_rows(step.output)
        if verdicts and step.step_code in ('7.1','7.2','7.3','7.4'):
            keys={'7.1':['idea_title','ifr_satisfaction_pct','note'],'7.2':['idea_title','is_tradeoff','note'],
                  '7.3':['idea_title','side_effects'],'7.4':['idea_title','constraint_ok','note']}[step.step_code]
            columns=[FIELDS[k] for k in keys]
            rows=[[value_text(v.get(k)) for k in keys] for v in verdicts]
        parts.setdefault(part,dict(title=f'Part {part} · '+PARTS.get(part,'분석 기록'),steps=[]))['steps'].append(
            dict(code=step.step_code,title=step.step_title,status=step.status,columns=columns,rows=rows,
                 key=f'ariz-step-{index}',output=step.output,structured=structured or (bool(verdicts) and step.step_code.startswith('7.'))))
    proposals=[dict(kind=kind,content=content_text(value))
        for kind,values in [('해결 방향',run.solution_directions),('실행 아이디어',run.final_ideas)] for value in values]
    return dict(parts=list(parts.values()),proposals=proposals,
        verdicts=verdicts,resources=[content_text(x) for x in run.sfr_inventory])

def diagrams(state):
    """Only explicit causal arrows and the defined OT chronology become diagrams."""
    run=state.solve.ariz
    if not run:return []
    out=[]
    for index,step in enumerate(run.steps):
        nodes,edges=[],[]
        if step.step_code=='1.3':
            for j,sentence in enumerate(re.split(r'(?<=[.!?])\s+|\n',step.output)):
                if not re.search(r'→|->',sentence):continue
                source,result=re.split(r'→|->',sentence,maxsplit=1)
                if len(source)>160 or len(result)>320:continue
                sid=f's{j}';nodes.append((sid,source.strip(),'field'))
                for k,effect in enumerate(re.split(r'\s+\+\s+',result)):
                    bad=bool(re.search(r'나쁨|유해|악화',effect));good=bool(re.search(r'좋음|유익|개선',effect))
                    eid=f'e{j}-{k}';nodes.append((eid,effect.strip(),'bad' if bad else 'good' if good else ''))
                    edges.append((sid,eid,'악화' if bad else '개선' if good else '영향',bad))
        elif step.step_code=='2.2':
            by_code={re.match(r'T[123]',k).group():v for k,v in text_rows(step.output) if re.match(r'T[123]',k)}
            if all(k in by_code for k in ('T1','T2','T3')):
                nodes=[(k,k+' · '+label+'\n'+by_code[k],'bad' if k=='T1' else 'field') for k,label in
                       [('T2','갈등 이전'),('T1','갈등 발생'),('T3','갈등 이후')]]
                edges=[('T2','T1','시간 경과',False),('T1','T3','시간 경과',False)]
        elif step.step_code=='4.1':
            parts=dict(text_rows(step.output))
            if all(k in parts for k in ('현재','요구','구현')):
                nodes=[(k,k+'\n'+parts[k],'field') for k in ('현재','요구','구현')]
                edges=[('현재','요구','요구 행동',False),('요구','구현','구현 검토',False)]
        if nodes:out.append(dict(key=f'ariz-step-{index}',title=f'ARIZ {step.step_code} · {step.step_title}',nodes=nodes,edges=edges))
    return out
