"""Serialize final, explicitly authored review corrections; no semantic inference."""
import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'research/effects'
assert not (D/'final-editorial-corrections-2026-09-26.json').exists(), 'One-time final corrections already applied'
def read(n):return json.loads((D/n).read_text(encoding='utf-8'))
def write(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
observations=read('reference_observations.json')
changes=[]
for number in [4,5]:
    name=f'additions-2026-09-26-{number:02}.tsv'
    p=D/name; raw=p.read_text(encoding='utf-8'); out=[]
    audit_name='audit-'+p.stem+'.json';audit=read(audit_name)
    old_hash=audit['source_sha256']
    for line in raw.splitlines():
        if line and not line.startswith('#'):
            row=line.split('|');old=row[7];row[7]='stored_search_excerpt'
            observations['research-20260926-'+row[0]]['retrieval_scope']=row[7]
            if old!=row[7]:changes.append(dict(key=row[0],old_scope=old,new_scope=row[7]))
            line='|'.join(row)
        out.append(line)
    raw='\n'.join(out)+'\n';p.write_text(raw,encoding='utf-8')
    audit['source_sha256']=hashlib.sha256(raw.encode()).hexdigest()
    audit['scope_correction']={'previous_sha256':old_hash,'reason':'Conservatively identify retained evidence as search excerpts; no assertion of full-text access.'}
    for decision in audit['decisions']:decision['retrieval_scope']='stored_search_excerpt'
    write(audit_name,audit)
refs=read('references.json')
extra='repair-20260926-mpc-primary-paper'
refs[extra]=['Marcel Keller · MP-SPDZ: A Versatile Framework for Multi-Party Computation (2020)','https://www.acsu.buffalo.edu/~mblanton/cse715/mp-spdz.pdf']
observations[extra]=dict(retrieval_scope='reference_section',accessed_at='2026-09-26',review_method='conversation_reasoning',supports='확인한 초록 및 도입부: 비밀 입력의 공동 계산, 공격자 모델, 비밀분산을 포함한 구현 기초. 논문 전체의 보안 증명 검증을 뜻하지 않는다.')
conditions={
'norrish-carbonyl-alpha-photocleavage':' 중합 광개시의 한 경로와 겹치는 카보닐 광절단 세부 기전이다.',
'magnetic-relaxation-loss-heating':' 교류 자기장 가열 계열의 자화·회전 이완 손실로 범위를 한정한다.',
'debye-mobile-charge-screening':' 전기 이중층 상호작용을 구성하는 차폐 기전이다.',
'collapse-heated-bubble-sonoluminescence':' 기포 붕괴 계열의 압축가열·발광 경로이다.',
'feshbach-bound-channel-scattering-tuning':' 이산·연속 채널 결합 계열의 산란 제어 경로이다.',
'autophagosomal-sequestration-lysosomal-degradation':' 표적 분해의 가능한 세부 경로 중 하나이다.',
'electrocyclic-conjugated-ring-switching':' 연결 관계를 유지하는 E/Z 광이성질화와 구분한다.',
}
out=[]
for line in (D/'catalog.tsv').read_text(encoding='utf-8').splitlines():
    if line and not line.startswith(('#','@')):
        row=line.split('|')
        if row[0] in conditions:
            row[3]+=conditions[row[0]]
            assert len(row[3])<=180
        if row[0]=='secret-shared-multiparty-computation':row[4]+=','+extra
        line='|'.join(row)
    out.append(line)
(D/'catalog.tsv').write_text('\n'.join(out)+'\n',encoding='utf-8')
write('references.json',refs);write('reference_observations.json',observations)
write('final-editorial-corrections-2026-09-26.json',dict(
    source_scope_corrections=changes,additional_primary_reference=extra,
    appended_conditions=conditions,
    rationale='Explicit final review decisions. Batch rows retain the initial authored content; canonical conditions add the final boundaries. No cards added or removed.',
    external_llm_calls=0))
print(json.dumps(dict(scope_corrections=len(changes),condition_clarifications=len(conditions),additional_primary_references=1)))
