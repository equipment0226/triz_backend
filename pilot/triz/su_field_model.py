"""Read explicit application graphs without guessing missing interactions."""
import re

IDENTIFIER = re.compile(r"(?:S[1-9]\d*[a-z]?|F\d*)(?:[′'’*])?")


def key(value):
    return str(value).replace("'",'′').replace('’','′')


def check_model(model):
    if not isinstance(model,dict): return ['resulting_model이 객체가 아님']
    nodes=model.get('nodes'); edges=model.get('edges')
    if not isinstance(nodes,list) or not 1 <= len(nodes) <= 12: return ['모델 노드는 1~12개 필요']
    if not isinstance(edges,list) or len(edges)>24: return ['모델 간선 배열 필요(최대 24개)']
    ids=[]
    for node in nodes:
        if not isinstance(node,dict) or not IDENTIFIER.fullmatch(str(node.get('id',''))) or not isinstance(node.get('label'),str) or not node['label'].strip():
            return ['모델 노드의 식별자·명칭 누락']
        ids.append(key(node['id']))
    if len(set(ids))!=len(ids): return ['모델 노드 식별자 중복']
    for edge in edges:
        if not isinstance(edge,dict) or key(edge.get('source')) not in ids or key(edge.get('target')) not in ids:
            return ['간선이 존재하지 않는 노드를 참조']
        if edge.get('kind','useful') not in ('useful','harmful','neutral') or not isinstance(edge.get('label',''),str):
            return ['간선의 작용 종류·설명 형식 오류']
    return []


def application_model(state,app):
    from .report_groups import sources
    originals=[s for s in state.analysis.su_fields if s.id in sources(state,app,'su')]
    original=originals[0] if len(originals)==1 else None
    base={'S1':original.s1,'S2':original.s2,'S3':original.s3,'F':original.field} if original else {}
    notes=['주황: 변경된 요소 · 보라: 추가 요소. 명시된 작용만 연결한다.']
    if not original: notes.append('원본 물질–장 모델 연결 미확인: 변경 비교에 한계가 있다.')

    def node(identifier,description):
        identifier=key(identifier)
        plain=identifier.rstrip('′*')
        old=base.get(plain)
        text=description or old or '상세 명칭 미기재'
        tone='field' if identifier.startswith('F') else ''
        if plain != identifier or (old and text!=old): tone='changed'
        elif original and not old: tone='added'
        return (identifier,identifier+'\n'+text,tone)

    model=app.get('resulting_model')
    if model is not None:
        errors=check_model(model)
        if not errors:
            nodes=[node(n['id'],n['label']) for n in model['nodes']]
            edges=[(key(e['source']),key(e['target']),e.get('label') or '명시된 작용',e.get('kind')=='harmful') for e in model['edges']]
            return nodes,edges,' '.join(notes)
        notes.append('구조화 모델 검증 실패: '+'; '.join(errors)+'. 텍스트에 명시된 관계만 표시한다.')

    raw=str(app.get('resulting_su_field') or '')
    pattern=re.compile(r"(?<![A-Za-z0-9])((?:S[1-9]\d*[a-z]?|F\d*)(?:[′'’*])?)(?![A-Za-z0-9])")
    items=[]; position=0
    while match:=pattern.search(raw,position):
        end=match.end(); after=end
        while after<len(raw) and raw[after].isspace(): after+=1
        description=''
        if after<len(raw) and raw[after] in '(（':
            depth=1; end=after+1
            while end<len(raw) and depth:
                if raw[end] in '(（': depth+=1
                elif raw[end] in ')）': depth-=1
                end+=1
            description=raw[after+1:end-1] if depth==0 else raw[after+1:end]
        items.append(dict(key=key(match.group(1)),description=description.strip(),start=match.start(),end=end))
        position=end
    nodes={item['key']:node(item['key'],item['description']) for item in items}
    edges=[]
    def connect(a,b,between,label):
        if a['key']==b['key']: return
        forward=bool(re.search(r'[-=]+\s*>|→|⇒|⟶',between))
        backward=bool(re.search(r'<\s*[-=]+|←|⇐|⟵',between))
        if re.search(r'↔|⇄|⇆|⇔',between): forward=backward=True
        for source,target,enabled in [(a,b,forward),(b,a,backward)]:
            edge=(source['key'],target['key'],label,False)
            if enabled and edge not in edges: edges.append(edge)
    # Direct F→S, S→S and reversed/bidirectional relationships.
    for a,b in zip(items,items[1:]):
        connect(a,b,raw[a['end']:b['start']],'명시된 작용')
    substances=[item for item in items if item['key'].startswith('S')]
    for a,b in zip(substances,substances[1:]):
        fields=[f for f in items if f['key'].startswith('F') and a['end']<=f['start']<b['start']]
        between=raw[a['end']:b['start']]
        if fields and re.search(r'[-=]\s*\[',between):
            connect(a,b,between,' · '.join(f['key'] for f in fields)+' 작용')
    if not nodes:
        nodes={k:node(k,v) for k,v in base.items() if v}
        notes.append('적용 후 구조가 명시되지 않아 원본 요소만 표시한다. 변환 구조로 해석하지 않는다.')
    if not nodes: nodes={'unknown':('unknown','적용 구조 확인 필요','')}
    notes.append('+로만 나열한 요소의 연결은 추정하지 않는다.')
    return list(nodes.values()),edges,' '.join(notes)
