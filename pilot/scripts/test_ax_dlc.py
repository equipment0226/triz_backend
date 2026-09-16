"""Opt-in live DLC workflow acceptance. Isolated DB; no manual-effect extraction.

Run explicitly, outside pytest. All interview answers preserve unspecified values.
Exploration acknowledgements are scripted test inputs, never training labels.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--directory',type=Path,required=True)
parser.add_argument('--resume',action='store_true')
parser.add_argument('--budget-usd',type=float,default=.60)
args=parser.parse_args()
directory=args.directory.resolve()
directory.mkdir(parents=True,exist_ok=True)
os.environ['DATABASE_URL']='sqlite:///'+(directory/'test.db').as_posix()
os.environ['STORAGE_DIR']=str(directory/'storage')
os.environ['ORCHESTRATOR']='local'
os.environ['PATENT_SEARCH_PROVIDER']='none'
os.environ['FREE_PATENT_SEARCH']='false'
os.environ['EVIDENCE_PROVIDERS']='crossref,openalex,arxiv'
sys.path.insert(0,str(ROOT))
from triz import pipeline,store
from triz.ax import WORKFLOW,ledger
from triz.settings import settings
if not 0<args.budget_usd<=.60: raise ValueError('Test budget must be positive and <= $0.60')
settings.triz.setdefault('ax',{})['hard_budget_usd']=args.budget_usd

pipeline.start=lambda run_id:None
runfile=directory/'run-id.txt'
if args.resume:
    s=store.load_state(runfile.read_text().strip())
    if s.status in ('FAILED','INTERRUPTED'):
        pipeline.continue_run(s.run_id)
else:
    s=pipeline.create_run('DLC 데이터센터 냉각수 온도와 GPU 온도 상충 해결',mode='FULL',workflow_version=WORKFLOW)
    s.scratch['acceptance_fixture']='DLC; scripted interview; NO_TRAINING'
    store.save_state(s)
    runfile.write_text(s.run_id)

for _ in range(40):
    s=store.load_state(s.run_id)
    if s.status=='COMPLETED':
        break
    if s.pending:
        p=s.pending
        if p.kind=='CLARIFY':
            questions=p.payload.get('questions',[])
            payload={'skip':True,'answers':['미제공. 실제 온도·열부하·유량·허용 GPU 온도 수치를 가정하지 말고 추가 측정 조건으로 남긴다.']*len(questions)}
        elif p.kind=='CONFIRM':
            payload={'candidate_id':s.confirm.candidates[0].id if s.confirm.candidates else '',
                'amendment':'냉각수 온도 상승을 통한 냉각 에너지 절감과 GPU 온도 상승 상충. 장비·온도·유량·열부하 수치는 미제공. 시험 결과 없음.'}
        elif p.kind=='DECIDE':
            payload={'decisions':{c['concept_id']:'accept' for c in p.payload.get('conditional',[])}}
        elif p.kind=='FEEDBACK':
            payload={'solution_feedback':[]}
        else:
            raise RuntimeError('Unsupported test interrupt: '+p.kind)
        payload['interrupt_id']=p.interrupt_id
        pipeline.resume(s.run_id,payload)
        s=store.load_state(s.run_id)
    key=pipeline.PIPELINE[s.control.stage_index][0]
    print(json.dumps({'stage':key,'status':'START','cost':s.cost.total_usd}),flush=True)
    result=pipeline.execute_stage(s.run_id,s.control.stage_index,s.scratch['execution_epoch'])
    print(json.dumps(result),flush=True)
    if result['status'] in ('FAILED','INTERRUPTED'):
        break
s=store.load_state(s.run_id)
result={'run_id':s.run_id,'status':s.status,'stage_index':s.control.stage_index,'cost':ledger.budget(s.run_id),
    'gates':s.scratch.get('ax_gates'),'coordination':s.scratch.get('ax_coordination'),
    'selection':s.scratch.get('ax_selection'),'errors':s.control.errors,
    'warnings':s.control.warnings,'physical_testing':'NOT_PERFORMED','training_consent':'NO_TRAINING'}
(directory/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ('run_id','status','stage_index','cost','errors')},ensure_ascii=False),flush=True)
store.engine.dispose()
sys.exit(0 if s.status=='COMPLETED' and s.concepts and not result['selection']['recommended'] else 1)
