"""Rank individual catalog mechanisms, retaining scientific conditions and sources."""
from collections import Counter
import math
import re

def terms(value):
    words = re.findall(r'[a-z0-9]+|[가-힣]+', str(value).lower())
    stop = {'the','and','for','with','from','that','into','using','한다','또는','대한','통해','있는','위한'}
    return [part for word in words if len(word)>1 and word not in stop
            for part in ([word] + ([word[i:i+2] for i in range(len(word)-1)] if re.search('[가-힣]',word) else []))]

def flat_effects(groups):
    return [dict(effect,function_ko=group['function_ko'],id=effect.get('id') or f'BASE-{gi+1:02d}-{i+1:02d}')
            for gi,group in enumerate(groups) for i,effect in enumerate(group.get('effects',[]))]

def select_effects(groups, required_functions=(), limit=24):
    """Global lexical ranking over names, bilingual aliases, mechanism and conditions.

    A query for heat pipes can find a stored literature mechanism even if its
    function group is broad. No per-group truncation hides later catalog entries.
    Source count is not used as a correctness score.
    """
    entries = flat_effects(groups)
    query = set(terms(' '.join(required_functions)))
    if not query:
        # Spread default examples across functions rather than filling with group 1.
        positions=Counter()
        order=[]
        for i,e in enumerate(entries):
            order.append((positions[e['function_ko']],i,e))
            positions[e['function_ko']]+=1
        order.sort(key=lambda item:item[:2])
        return [e for _,_,e in order[:limit]]
    counts = []
    boosts = []
    for e in entries:
        name = ' '.join([e['name'],e.get('name_en',''),e.get('mechanism_key',''),*e.get('aliases',[])])
        body = ' '.join([name,e['function_ko'],e.get('principle',''),str(e.get('conditions','')),str(e.get('applications',[])),str(e.get('industries',[]))])
        counts.append(Counter(terms(body)))
        boosts.append(set(terms(name)) | set(terms(e['function_ko'])))
    df = Counter(t for c in counts for t in c)
    n = max(1,len(entries))
    avg = sum(sum(c.values()) for c in counts)/n or 1
    scored = []
    for i,(e,c) in enumerate(zip(entries,counts)):
        length = sum(c.values())
        score = 0
        for token in query & c.keys():
            freq=c[token]
            idf=math.log(1+(n-df[token]+.5)/(df[token]+.5))
            score += idf * (freq*2.2)/(freq+1.2*(.25+.75*length/avg)) * (1.6 if token in boosts[i] else 1)
        scored.append((score,i,e))
    scored.sort(key=lambda item:(-item[0],item[1]))
    return [e for _,_,e in scored[:limit]]

def format_effects(entries, total_groups, total_effects, standard_count):
    lines = [f'현재 로컬 카탈로그: 표준해 {standard_count}개, 효과 기능군 {total_groups}개, 효과 {total_effects}개. 관련 개별 효과 {len(entries)}개를 검색했다.',
             '출처의 초록·발췌와 실증은 다르다. 아래 조건·한계와 출처 범위를 보존하고 부적합한 효과는 제외한다.']
    for e in entries:
        lines.append(f"\n[{e['id']}] {e['name']} ({e.get('name_en','')}; {e.get('domain','PHYSICAL')})\n요구 기능: {e['function_ko']}\n원리: {e.get('principle','')}")
        for key,label in [('conditions','필요 조건'),('limitations','한계'),('inputs','입력'),('outputs','출력'),('parameters','설계 변수'),('applications','응용'),('equation','관계식'),('equation_scope','관계식 성립 범위'),('design_notes','검토 메모')]:
            value=e.get(key)
            if value: lines.append(f'{label}: '+(' / '.join(value) if isinstance(value,list) else str(value)))
        if e.get('evidence_level'): lines.append('근거 수준: '+e['evidence_level'])
        sources=e.get('sources',[])
        for source in sources[:4]:
            lines.append(f"출처 [{source.get('identifier') or source.get('title')}]: {source.get('url','')} (범위: {source.get('retrieval_scope','reference_document')})")
        if len(sources)>4: lines.append(f'전체 출처 {len(sources)}개는 카탈로그에 보존됨.')
        variants=e.get('variants',[])
        for v in variants[:2]: lines.append('다른 적용 조건: '+str(v.get('conditions',''))+' / 한계: '+str(v.get('limitations','')))
    return '\n'.join(lines)
