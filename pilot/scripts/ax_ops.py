"""Local operator CLI for audited policy/rule and unknown-cost reconciliation."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triz.ax import ledger,registry,rules

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['train','rules','promote','rollback','revoke-rule','reconcile'])
    p.add_argument('--tenant',required=True);p.add_argument('--project',required=True)
    p.add_argument('--version');p.add_argument('--actor');p.add_argument('--reason')
    p.add_argument('--task');p.add_argument('--actual-microusd',type=int)
    args=p.parse_args();ledger.init()
    if args.command=='train': result=registry.train_project(args.tenant,args.project)
    elif args.command=='rules': result=rules.research_project(args.tenant,args.project)
    elif args.command=='promote': result=registry.promote_policy(args.tenant,args.project,args.version,args.actor,args.reason or '')
    elif args.command=='rollback': result=registry.rollback(args.tenant,args.project,args.actor,args.reason or '')
    elif args.command=='revoke-rule': result=rules.revoke(args.tenant,args.project,args.version,args.actor,args.reason or '')
    else:
        if args.actual_microusd is None or not args.task:p.error('Reconcile needs --task and --actual-microusd')
        from sqlalchemy import select
        with ledger.store.engine.connect() as c:
            rid=c.execute(select(ledger.tasks.c.run_id).where(ledger.tasks.c.task_id==args.task)).scalar_one()
        h=ledger.head(rid)
        if (h['tenant_id'],h['project_id'])!=(args.tenant,args.project): raise ValueError('Task outside project')
        result=ledger.reconcile(args.task,args.actual_microusd,args.reason or '',args.actor)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
