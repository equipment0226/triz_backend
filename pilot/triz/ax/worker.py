"""Separate bounded CPU worker: durable events -> reviewed data -> policy/rule lab."""
import json
from sqlalchemy import Column,String,Integer,select,update
from . import ledger,outbox,registry,rules
from .contracts import now

queue=ledger.table('learning_queue',Column('scope',String(80),primary_key=True),
    Column('tenant_id',String(64),nullable=False),Column('project_id',String(64),nullable=False),
    Column('revision',Integer,nullable=False),Column('processed_revision',Integer,nullable=False))


def consume(c,event):
    if event['event_type']!='REVIEW_CONFIRMED': return
    h=ledger._head(c,event['run_id'],lock=True)
    key=registry.scope(h['tenant_id'],h['project_id'])
    row=c.execute(select(queue).where(queue.c.scope==key).with_for_update()).mappings().first()
    if row:
        c.execute(update(queue).where(queue.c.scope==key).values(revision=row['revision']+1))
    else:
        c.execute(queue.insert().values(scope=key,tenant_id=h['tenant_id'],project_id=h['project_id'],revision=1,processed_revision=0))


def tick(max_events=100,max_projects=1):
    ledger.init()
    delivered=0
    for _ in range(min(1000,max_events)):
        event=outbox.claim()
        if not event: break
        outbox.deliver(event,'ax-learning-v1',consume)
        delivered+=1
    with ledger.store.engine.connect() as c:
        work=c.execute(select(queue).where(queue.c.revision>queue.c.processed_revision).limit(max_projects)).mappings().all()
    results=[]
    for item in work:
        policy=registry.train_project(item['tenant_id'],item['project_id'])
        evolved=rules.research_project(item['tenant_id'],item['project_id'])
        with ledger.transaction() as c:
            c.execute(update(queue).where(queue.c.scope==item['scope'],queue.c.processed_revision<item['revision'])
                .values(processed_revision=item['revision']))
        results.append({'scope':item['scope'],'policy':policy,'rules':evolved})
    return {'delivered':delivered,'projects':results,'external_llm_calls':0,'at':now()}
