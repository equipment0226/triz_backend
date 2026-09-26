"""Check editorial identity and evidence preservation; not scientific equivalence."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/effects';K=ROOT/'triz/knowledge'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
resume=read(D/'resume-2026-09-26.json')
target_count=resume['target']
assert type(target_count) is int and target_count>0,('Invalid research target',target_count)
groups=read(K/'effects.json');sources=read(K/'effects_sources.json')
entries=[e for g in groups for e in g['effects']]
current={e['id']:e for e in entries}
legacy={old:e['id'] for e in entries for old in e.get('legacy_ids',[])}
assert len(current)==len(entries)
assert len({e['name'] for e in entries})==len(entries)
assert set(legacy).isdisjoint(current)
assert len(legacy)==sum(len(e.get('legacy_ids',[])) for e in entries)
assert current.keys()==sources.keys()
assert all(s['sources'] for s in sources.values())
before=read(D/'audit-2026-09-26-before/effects.json')
old_sources=read(D/'audit-2026-09-26-before/effects_sources.json')
old_entries=[e for g in before for e in g['effects']]
for e in old_entries:
    old=e['id'];target=legacy.get(old,old)
    assert target in current,('Lost old ID',old)
    prior_urls={s['url'] for s in old_sources[old]['sources']}
    new_urls={s['url'] for s in sources[target]['sources']}
    assert prior_urls<=new_urls,('Lost old source',old,prior_urls-new_urls)
campaign_baseline='audit-2026-09-26-before1500'
campaign_groups=read(D/campaign_baseline/'effects.json')
campaign_sources=read(D/campaign_baseline/'effects_sources.json')
campaign_entries=[e for g in campaign_groups for e in g['effects']]
campaign_ids={e['id'] for e in campaign_entries}
assert len(campaign_ids)==len(campaign_entries)==1200,('Invalid 1200-effect baseline',len(campaign_entries))
assert campaign_ids==campaign_sources.keys(),('Baseline source IDs do not match effect IDs',campaign_baseline)
for e in campaign_entries:
    old=e['id'];target=legacy.get(old,old)
    assert target in current,('Lost campaign baseline ID',old)
    prior_urls={s['url'] for s in campaign_sources[old]['sources']}
    new_urls={s['url'] for s in sources[target]['sources']}
    assert prior_urls<=new_urls,('Lost campaign baseline source URL',old,prior_urls-new_urls)
    prior_refs={(s.get('identifier'),s['url']) for s in campaign_sources[old]['sources']}
    new_refs={(s.get('identifier'),s['url']) for s in sources[target]['sources']}
    assert prior_refs<=new_refs,('Lost campaign baseline source identity',old,prior_refs-new_refs)
keys={s['mechanism_key'] for s in sources.values()}
redirects=read(D/'mechanism_redirects.json')
assert all(old not in keys and new in keys for old,new in redirects.items())
campaign_merge_path=D/'campaign-merge-decisions-2026-09-26.json'
campaign_merges=read(campaign_merge_path) if campaign_merge_path.exists() else []
assert isinstance(campaign_merges,list), 'Campaign merge decisions must be a list'
campaign_redirects={}
for decision in campaign_merges:
    key=decision['key'];target=decision['target']
    assert key not in campaign_redirects and key!=target,('Duplicate or self campaign merge',key)
    assert decision['decision'] and decision['reason'],('Missing campaign merge decision or rationale',key)
    assert decision['source_ref'] and decision['source_url'].startswith('https://'),('Missing campaign merge source evidence',key)
    assert redirects.get(key)==target and key not in keys and target in keys,('Invalid campaign merge redirect',key,target)
    target_evidence=next(s for s in sources.values() if s['mechanism_key']==target)
    assert any(s.get('identifier')=='REF-'+decision['source_ref'] and s['url']==decision['source_url']
               for s in target_evidence['sources']),('Lost campaign merge source evidence',key,target)
    campaign_redirects[key]=target
new_audits=[read(p) for p in sorted(D.glob('audit-additions-2026-09-26-*.json'))]
new_keys=set()
for audit in new_audits:
    source=D/audit['batch']
    assert hashlib.sha256(source.read_text(encoding='utf-8').encode()).hexdigest()==audit['source_sha256']
    for row in audit['decisions']:
        key=row['key'];target=campaign_redirects.get(key,key)
        assert target in keys and key not in new_keys
        assert row['boundary'] and all(redirects.get(k,k) in keys for k in row['related_keys'])
        new_keys.add(key)
        evid=next(s for s in sources.values() if s['mechanism_key']==target)
        observed=next(s for s in evid['sources'] if s['url']==row['source_url'])
        assert observed['retrieval_scope']==row['retrieval_scope']
        assert observed['review_method']=='conversation_reasoning'
assert campaign_redirects.keys()<=new_keys,('Campaign merge did not originate in a research batch',campaign_redirects.keys()-new_keys)
merged=read(D/'merged-evidence-2026-09-26.json')
net_new=len(new_keys)-len(campaign_merges)
assert len(entries)==len(old_entries)-len(merged)+net_new
cross_review_path=D/'final-cross-review-1500-2026-09-26.tsv'
cross_review=[line.split('|') for line in cross_review_path.read_text(encoding='utf-8').splitlines()
              if line and not line.startswith('#')]
assert all(len(row)==4 and row[2] and row[3] and
           all(redirects.get(key,key) in keys for key in row[:2]) for row in cross_review)
assert resume['effects']==len(entries), 'Resume count disagrees with published catalog'
progress=read(D/'manual-progress.json')
assert progress['cursor']=='AT-512674-A1' and progress['completed_pages']==81
assert not (ROOT/'data/patent_effects_manual/page-000082.json').exists()
result=dict(before=len(old_entries),merged=len(merged),new=net_new,gross_new=len(new_keys),
            withdrawn_new=len(campaign_merges),effects=len(entries),
            target=target_count,remaining=max(0,target_count-len(entries)),with_sources=len(sources),
            original_ids_preserved=len(old_entries),original_source_urls_preserved=True,
            campaign_baseline=campaign_baseline,campaign_initial_effects=len(campaign_entries),
            campaign_new_effects=len(entries)-len(campaign_entries),
            campaign_gross_additions=sum(a['added'] for a in new_audits if a['target']==target_count),
            campaign_merged_new=len(campaign_merges),final_cross_review_pairs=len(cross_review),
            campaign_original_ids_preserved=len(campaign_entries),
            campaign_original_source_urls_preserved=True,campaign_original_source_identifiers_preserved=True,
            redirect_targets_valid=True,source_observation_scopes_preserved=True,
            patent_cursor_advanced=False,external_llm_calls=0,
            catalog_sha256=hashlib.sha256((D/'catalog.tsv').read_text(encoding='utf-8').encode('utf-8')).hexdigest(),
            catalog_hash_basis='UTF-8 text with LF newlines',
            caveat='Identity/schema/evidence-link checks only; not experimental validation or all-pairs semantic proof.')
(D/'verification-2026-09-26.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
