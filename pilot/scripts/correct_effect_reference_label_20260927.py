"""Record the primary publisher's exact title after checking its first-page excerpt."""
import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'research/effects'
p=D/'additions-2026-09-27-chemistry-03.tsv'
old='Recent studies of sulfonyl compounds, Pure and Applied Chemistry 68, 825–830, section 1'
new='Mechanisms of reactions of sulfonyl compounds with nucleophiles in protic media'
raw=p.read_text(encoding='utf-8')
assert raw.count(old)==1
p.write_text(raw.replace(old,new),encoding='utf-8')
refs=json.loads((D/'references.json').read_text(encoding='utf-8'))
refs['research-20260927-episulfone-extrusion-alkene-formation'][0]=new
(D/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ap=D/'audit-additions-2026-09-27-chemistry-03.json'
a=json.loads(ap.read_text(encoding='utf-8'))
a['reference_label_corrections']=[dict(key='episulfone-extrusion-alkene-formation',before=old,after=new,
    evidence='https://publications.iupac.org/pac/68/4/0825/index.html')]
a['source_sha256']=hashlib.sha256(p.read_text(encoding='utf-8').encode()).hexdigest()
ap.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Publisher title corrected; content and count unchanged.')
