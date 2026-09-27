"""Validate and serialize conversation-authored reference cards, never infer new ones."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from triz.effect_mining import atomic_json

D=ROOT/'research/effects'
def read(name,default):
    p=D/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('batch',type=Path)
    p.add_argument('--apply',action='store_true')
    p.add_argument('--campaign',default='2026-09-26',help='ISO date identifying the explicitly initialized research campaign')
    a=p.parse_args()
    datetime.strptime(a.campaign,'%Y-%m-%d')
    progress_name=f'resume-{a.campaign}.json'
    assert (D/progress_name).exists(),'Initialize an explicit campaign before installing batches'
    progress=read(progress_name,{})
    target=progress.get('target',1200)
    raw=a.batch.read_text(encoding='utf-8')
    rows=[l.split('|') for l in raw.splitlines() if l and not l.startswith('#')]
    assert rows and all(len(r)==10 and all(v.strip() for v in r) for r in rows),'Invalid authored row'
    lines=(D/'catalog.tsv').read_text(encoding='utf-8').splitlines()
    existing={r[0]:r for l in lines if l and not l.startswith(('#','@')) for r in [l.split('|')]}
    keys={r[0] for r in rows};names={r[2] for r in rows}
    assert len(keys)==len(rows) and len(names)==len(rows),'Duplicate new key/title'
    assert not keys&existing.keys(),'Already installed or duplicate key'
    assert not names&{r[1] for r in existing.values()},'Duplicate existing title'
    assert not {r[3] for r in rows}&{r[2] for r in existing.values()},'Exact duplicate principle'
    refs=read('references.json',{});meta=read('editorial_metadata.json',{})
    observations=read('reference_observations.json',{})
    redirects=read('mechanism_redirects.json',{})
    grouped=defaultdict(list);review=[]
    group_headers={int(l.split('|')[0][1:]):l.split('|') for l in lines if l.startswith('@')}
    for key,group,name,principle,conditions,title,url,scope,nearest,boundary in rows:
        assert int(group) in group_headers
        assert len(principle)<=160 and len(conditions)<=180,key
        assert url.startswith('https://') and scope in {'reference_section','publisher_abstract','stored_search_excerpt'},key
        related=[redirects.get(k,k) for k in nearest.split(',')]
        assert all(k in existing or k in keys for k in related), (key,related)
        assert key not in related
        ref='research-'+a.campaign.replace('-','')+'-'+key
        assert ref not in refs
        refs[ref]=[title,url]
        observations[ref]=dict(retrieval_scope=scope,accessed_at=a.campaign,review_method='conversation_reasoning',
            supports='공개 문헌의 원리·조건을 대화에서 검토한 참고 근거. 초록·검색 발췌 범위는 원문 전체 검증과 구분하며 개별 응용의 성능을 보장하지 않는다.')
        meta[key]={'aliases':[key.replace('-',' ')]}
        grouped[int(group)].append('|'.join([key,name,principle,conditions,ref]))
        review.append(dict(key=key,group=int(group),related_keys=related,decision='KEEP_WITH_EXPLICIT_BOUNDARY',
                          boundary=boundary,source_url=url,retrieval_scope=scope))
    out=[];current=None
    for line in lines:
        if line.startswith('@'):
            if current is not None:out.extend(grouped.pop(current,[]))
            current=int(line.split('|')[0][1:])
        out.append(line)
    if current is not None:out.extend(grouped.pop(current,[]))
    assert not grouped
    count=len(existing)+len(rows)
    assert count<=target, f'Batch exceeds explicitly requested canonical target: {count}>{target}'
    audit=dict(batch=a.batch.name,method='conversation_reasoning',external_llm_calls=0,
        before=len(existing),added=len(rows),after=count,target=target,
        source_sha256=hashlib.sha256(raw.encode()).hexdigest(),decisions=review)
    if a.apply:
        audit_path=D/('audit-'+a.batch.stem+'.json')
        assert not audit_path.exists(),'Batch audit already exists'
        atomic_json(audit_path,audit)
        (D/'catalog.tsv').write_text('\n'.join(out)+'\n',encoding='utf-8')
        for name,value in [('references.json',refs),('reference_observations.json',observations),('editorial_metadata.json',meta)]:
            atomic_json(D/name,value)
        progress.update(effects=count,remaining_to_target=max(0,target-count),last_batch=a.batch.name,
                        updated_at=datetime.now(timezone.utc).isoformat(),status='IN_PROGRESS')
        progress.update(campaign_new_effects=count-progress.get('campaign_initial_effects',1200),
                        new_effects=count-progress.get('after_existing_merge',950),
                        completed_batches=len(list(D.glob(f'audit-additions-{a.campaign}-*.json'))),
                        current_campaign_validation='PENDING',service_deployed=False,
                        git_publish_requested=True,
                        service_deployment_deferred=progress.get('service_deployment_deferred',True))
        atomic_json(D/progress_name,progress)
    print(json.dumps({k:v for k,v in audit.items() if k!='decisions'}))

if __name__=='__main__':main()
