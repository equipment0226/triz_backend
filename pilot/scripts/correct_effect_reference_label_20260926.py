"""Record the checked publisher label correction without changing a mechanism."""
import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'research/effects'
p=D/'additions-2026-09-26-03.tsv'
old='Journal of Fluid Mechanics · Rod-climbing rheometry revisited'
new='More et al. · Rod-climbing rheometry revisited (Soft Matter, 2023)'
raw=p.read_text(encoding='utf-8')
assert raw.count(old)==1
p.write_text(raw.replace(old,new),encoding='utf-8')
refs=json.loads((D/'references.json').read_text(encoding='utf-8'))
refs['research-20260926-viscoelastic-normal-stress-rod-climbing'][0]=new
(D/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ap=D/'audit-additions-2026-09-26-03.json'
a=json.loads(ap.read_text(encoding='utf-8'))
a['reference_label_corrections']=[{'key':'viscoelastic-normal-stress-rod-climbing','before':old,'after':new,'evidence':'https://pubmed.ncbi.nlm.nih.gov/37232105/','doi':'10.1039/d3sm00181d'}]
a['source_sha256']=hashlib.sha256(p.read_text(encoding='utf-8').encode()).hexdigest()
ap.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Corrected the journal label against PubMed; card count unchanged.')
