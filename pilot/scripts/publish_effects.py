"""Publish the explicitly edited compact catalog; never merge mined candidates.

The script validates and serializes editorial decisions in catalog.tsv. It does
not infer scientific equivalence, summarize entries or decide what to publish.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from triz.effect_mining import atomic_json

def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def build(directory, knowledge):
    authored=runpy.run_path(str(ROOT/'scripts/build_curated_effects.py'))
    base={e['mechanism_key']:e for g in authored['groups'].values() for e in g}
    refs={**authored['SOURCES'],**read(directory/'references.json',{})}
    registry=read(directory/'identifiers.json',{})
    literature={**read(directory/'accepted_literature_sources.json',{}),
                **{e.get('id'):e for g in read(ROOT/'data/effects_review/reviewed-catalog.json',[]) for e in g['effects']}}
    links=read(directory/'literature_links.json',{})
    groups=[]; evidence={}; counts=Counter(); names=set(); keys=set(); unsupported=[]
    for line in (directory/'catalog.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):continue
        if line.startswith('@'):
            number,function,domain=line[1:].split('|')
            group={'function_ko':function,'effects':[]}; groups.append(group)
            continue
        key,name,principle,conditions,reference_keys=line.split('|')
        if key in keys or name in names:raise ValueError('Duplicate editorial key or title: '+key)
        if not all([name.strip(),principle.strip(),conditions.strip()]):raise ValueError('Missing content: '+key)
        keys.add(key); names.add(name)
        if key not in registry:
            last=max([int(v.split('.')[1]) for v in registry.values() if v.startswith(number+'.')],default=0)
            registry[key]=f'{number}.{last+1}'
        identifier=registry[key]
        if not identifier.startswith(number+'.'):raise ValueError('Changing a function requires an explicit ID migration: '+key)
        prior=base.get(key,{})
        actual_domain=prior.get('domain',domain)
        if key in {'ion-exchange','surfactant-action','gelation','anodization','electrodeposition','cathodic-protection','passivation'}:actual_domain='CHEMICAL'
        group['effects'].append({'id':identifier,'name':name,'domain':actual_domain,'principle':principle,'conditions':conditions})
        sources=list(prior.get('sources',[]))
        if key in {'acoustic-streaming','hydrodynamic-lubrication'}:
            sources=[]  # Earlier broad analogies are replaced by dedicated references below.
        unresolved=[]
        for ref in filter(None,reference_keys.split(',')):
            if ref in refs:
                title,url=refs[ref]
                sources.append({'identifier':'REF-'+ref,'title':title,'url':url,'source_type':'REFERENCE','retrieval_scope':'reference_section'})
            else:unresolved.append(ref)
        for lid in links.get(key,[]):
            candidate=literature.get(lid)
            if not candidate:raise ValueError('Missing reviewed literature source: '+lid)
            if candidate:
                for source in candidate.get('sources',[]):
                    sources.append(dict(source,supports='문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님'))
        sources=list({s['url']:s for s in sources if s.get('url')}.values())
        status='참고 문헌과 편집 지식' if sources else '편집 지식; 연결 문헌 없음'
        evidence[identifier]={'mechanism_key':key,'name_en':prior.get('name_en',key.replace('-',' ')),
            'aliases':list(dict.fromkeys([name,key.replace('-',' '),*prior.get('aliases',[])])),
            'sources':sources,'evidence_level':status,
            'verification_scope':'원리·조건을 직접 편집한 참고 지식. 개별 현장 성능·실증을 의미하지 않음.'}
        counts['with_sources' if sources else 'editorial_knowledge_only']+=1
        if unresolved:unsupported.append({'key':key,'reference_topics':unresolved,'has_other_source':bool(sources)})
    ids=[e['id'] for g in groups for e in g['effects']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate stable identifier')
    if any(len(e['principle'])>160 or len(e['conditions'])>180 for g in groups for e in g['effects']):raise ValueError('Editorial entry is not concise')
    return groups,evidence,registry,dict(counts),unsupported

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    directory=ROOT/'research/effects'; knowledge=ROOT/'triz/knowledge'
    groups,evidence,registry,counts,topics=build(directory,knowledge)
    summary={'status':'CHECKED' if a.check else 'PUBLISHED','groups':len(groups),'effects':sum(len(g['effects']) for g in groups),**counts}
    if not a.check:
        atomic_json(directory/'identifiers.json',registry)
        atomic_json(knowledge/'effects_sources.json',evidence)
        atomic_json(knowledge/'effects.json',groups)
        atomic_json(directory/'reference_followups.json',topics)
        atomic_json(directory/'publication.json',dict(summary,at=datetime.now(timezone.utc).isoformat(),
            editorial_sha256=hashlib.sha256((directory/'catalog.tsv').read_bytes()).hexdigest(),
            scope='산업 공통의 대표 메커니즘을 기능별로 직접 편집. 전체 산업기술 또는 전체 특허를 망라한 목록이 아님.'))
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
