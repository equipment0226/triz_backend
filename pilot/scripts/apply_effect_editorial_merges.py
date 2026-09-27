"""Serialize explicit conversation-reviewed merges, retaining identifiers and evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from triz.effect_mining import atomic_json
from publish_effects import build

D=ROOT/'research/effects'
def read(name):return json.loads((D/name).read_text(encoding='utf-8'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decisions',type=Path)
    parser.add_argument('--campaign',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    datetime.strptime(args.campaign,'%Y-%m-%d')
    progress=read(f'resume-{args.campaign}.json')
    decisions=json.loads(args.decisions.read_text(encoding='utf-8'))
    assert isinstance(decisions,list) and decisions,'Explicit nonempty decisions required'
    lines=(D/'catalog.tsv').read_text(encoding='utf-8').splitlines()
    cards={r[0]:r for line in lines if line and not line.startswith(('#','@')) for r in [line.split('|')]}
    _,evidence,registry,_,_=build(D,ROOT/'triz/knowledge')
    removed={d['source'] for d in decisions}
    assert len(removed)==len(decisions),'Repeated source'
    metadata=read('editorial_metadata.json')
    links=read('literature_links.json')
    literature=read('accepted_literature_sources.json')
    redirects=read('mechanism_redirects.json')
    originals=[]
    for decision in decisions:
        source,target,reason=[decision[k] for k in ('source','target','reason')]
        assert source in cards and target in cards and target not in removed
        assert reason.strip() and source!=target
        prior=metadata.pop(source,{})
        item=metadata.setdefault(target,{})
        item['legacy_ids']=list(dict.fromkeys([*item.get('legacy_ids',[]),registry[source],*prior.get('legacy_ids',[])]))
        item['aliases']=list(dict.fromkeys([*item.get('aliases',[]),cards[source][1],source.replace('-',' '),*prior.get('aliases',[])]))
        sid='MERGED-'+args.campaign.replace('-','')+'-'+source
        assert sid not in literature
        literature[sid]={'sources':evidence[registry[source]]['sources']}
        links[target]=list(dict.fromkeys([*links.get(target,[]),*links.pop(source,[]),sid]))
        redirects[source]=target
        originals.append(dict(**decision,original_card=cards[source],original_metadata=prior,original_evidence=evidence[registry[source]]))
        if 'target_fields' in decision:
            fields=decision['target_fields']
            assert len(fields)==3 and all(isinstance(v,str) and v.strip() and '|' not in v for v in fields)
            item['aliases']=list(dict.fromkeys([*item['aliases'],cards[target][1]]))
            cards[target][1:4]=fields
    for old,target in list(redirects.items()):
        seen={old}
        while target in redirects:
            assert target not in seen,'Redirect cycle'
            seen.add(target);target=redirects[target]
        assert target in cards and target not in removed
        redirects[old]=target
    output=[]
    for line in lines:
        if not line or line.startswith(('#','@')):output.append(line);continue
        key=line.split('|')[0]
        if key not in removed:
            row=cards[key]
            assert len(row[2])<=160 and len(row[3])<=180,key
            output.append('|'.join(row))
    audit_name='audit-'+args.decisions.stem
    archive=D/(audit_name+'-before')
    audit_path=D/(audit_name+'.json')
    assert not archive.exists() and not audit_path.exists(),'Merge batch already applied'
    summary=dict(method='conversation_reasoning',external_llm_calls=0,before=len(cards),
        merged=len(removed),after=len(cards)-len(removed),campaign=args.campaign,
        decisions_sha256=hashlib.sha256(args.decisions.read_bytes()).hexdigest())
    if args.apply:
        archive.mkdir()
        for name in ['catalog.tsv','identifiers.json','editorial_metadata.json','literature_links.json',
                     'accepted_literature_sources.json','mechanism_redirects.json']:
            shutil.copy2(D/name,archive/name)
        (D/'catalog.tsv').write_text('\n'.join(output)+'\n',encoding='utf-8')
        for name,value in [('identifiers.json',registry),('editorial_metadata.json',metadata),
                ('literature_links.json',links),('accepted_literature_sources.json',literature),('mechanism_redirects.json',redirects)]:
            atomic_json(D/name,value)
        atomic_json(audit_path,dict(**summary,decisions=originals))
        count=summary['after']
        progress.update(effects=count,remaining_to_target=max(0,progress['target']-count),
            campaign_new_effects=count-progress['campaign_initial_effects'],
            new_effects=count-progress['campaign_initial_effects'],
            merged_during_campaign=progress.get('merged_during_campaign',0)+len(removed),
            updated_at=datetime.now(timezone.utc).isoformat(),current_campaign_validation='PENDING',
            last_merge_batch=args.decisions.name)
        atomic_json(D/f'resume-{args.campaign}.json',progress)
    print(json.dumps(summary))

if __name__=='__main__':main()
