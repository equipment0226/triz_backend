"""Serialize seven explicitly researched missing reference links, no model calls."""
import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'research/effects'
def read(name):return json.loads((D/name).read_text(encoding='utf-8'))
refs=read('references.json');observations=read('reference_observations.json')
repairs={r[0]:r[1:] for l in (D/'source-repairs-2026-09-26.tsv').read_text(encoding='utf-8').splitlines() if l and not l.startswith('#') for r in [l.split('|')]}
assert len(repairs)==7
out=[];matched=set()
for line in (D/'catalog.tsv').read_text(encoding='utf-8').splitlines():
    key=line.split('|')[0]
    if key in repairs:
        title,url,scope,support=repairs[key];ref='repair-20260926-'+key
        assert ref not in refs, 'Repair already applied'
        refs[ref]=[title,url]
        observations[ref]=dict(retrieval_scope=scope,accessed_at='2026-09-26',review_method='conversation_reasoning',supports=support)
        fields=line.split('|');fields[4]=','.join(filter(None,[fields[4],ref]));line='|'.join(fields);matched.add(key)
    out.append(line)
assert matched==repairs.keys()
for name,value in [('references.json',refs),('reference_observations.json',observations)]:
    (D/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'catalog.tsv').write_text('\n'.join(out)+'\n',encoding='utf-8')
print(json.dumps({'source_links_added':len(matched),'new_effects':0}))
