"""Separate bounded CPU worker: durable events -> reviewed data -> policy/rule lab."""
import json
from sqlalchemy import Column,String,Integer,select,update
from . import ledger,outbox,registry,rules
from .contracts import now

queue=ledger.table('learning_queue',Column('scope',String(80),primary_key=True),
    Column('tenant_id',String(64),nullable=False),Column('project_id',String(64),nullable=False),
    Column('revision',Integer,nullable=False),Column('processed_revision',Integer,nullable=False))

task_queue=ledger.table('learning_task_queue',Column('scope',String(80),primary_key=True),
    Column('tenant_id',String(64),nullable=False),Column('project_id',String(64),nullable=False),
    Column('task_kind',String(40),nullable=False),Column('feature_schema',String(80),nullable=False),
    Column('revision',Integer,nullable=False),Column('processed_revision',Integer,nullable=False))


def consume(c,event):
    if event['event_type'] in ('COMMON_EVALUATION','COMMON_EVALUATION_REVISED','ADAPTIVE_EPISODE_CLOSED','USAGE_RECONCILED'):
        h=ledger._head(c,event['run_id'],lock=True)
        if json.loads(h['bundle']).get('feature_schema') not in ('ax-state-action-v4','ax-state-action-v5'): return
        for kind,schema in (('routing_q',json.loads(h['bundle'])['feature_schema']),('effect_ranker','effect-application-utility-v2')):
            key=registry.task_scope(h['tenant_id'],h['project_id'],kind,schema)
            row=c.execute(select(task_queue).where(task_queue.c.scope==key).with_for_update()).mappings().first()
            if row:
                c.execute(update(task_queue).where(task_queue.c.scope==key).values(revision=row['revision']+1))
            else:
                c.execute(task_queue.insert().values(scope=key,tenant_id=h['tenant_id'],project_id=h['project_id'],
                    task_kind=kind,feature_schema=schema,revision=1,processed_revision=0))
        return
    if event['event_type'] not in ('REVIEW_CONFIRMED','EFFECT_REVIEW_CONFIRMED','OPTIONAL_TRANSITION'): return
    h=ledger._head(c,event['run_id'],lock=True)
    if json.loads(h['bundle']).get('feature_schema') in ('ax-state-action-v4','ax-state-action-v5'): return
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
        coherence_policy=registry.train_project(item['tenant_id'],item['project_id'],feature_schema='ax-features-v2')
        routing_policy=registry.train_project(item['tenant_id'],item['project_id'],feature_schema='ax-state-action-v3')
        from . import effect_ranker
        effect_model=effect_ranker.train_project(item['tenant_id'],item['project_id'])
        evolved=rules.research_project(item['tenant_id'],item['project_id'])
        with ledger.transaction() as c:
            c.execute(update(queue).where(queue.c.scope==item['scope'],queue.c.processed_revision<item['revision'])
                .values(processed_revision=item['revision']))
        results.append({'scope':item['scope'],'policy':policy,'coherence_policy':coherence_policy,
                        'routing_policy':routing_policy,'effect_ranker':effect_model,'rules':evolved})
    with ledger.store.engine.connect() as c:
        tasks=c.execute(select(task_queue).where(task_queue.c.revision>task_queue.c.processed_revision).limit(max_projects*2)).mappings().all()
    for item in tasks:
        try:
            if item['task_kind']=='routing_q':
                result=registry.train_project(item['tenant_id'],item['project_id'],feature_schema=item['feature_schema'])
            else:
                from . import effect_ranker
                result=effect_ranker.train_project(item['tenant_id'],item['project_id'],schema=item['feature_schema'])
            with ledger.transaction() as c:
                c.execute(update(task_queue).where(task_queue.c.scope==item['scope'],task_queue.c.processed_revision<item['revision'])
                    .values(processed_revision=item['revision']))
            results.append(dict(scope=item['scope'],task_kind=item['task_kind'],result=result))
        except Exception as exc:
            results.append(dict(scope=item['scope'],task_kind=item['task_kind'],status='RETRY_PENDING',error=type(exc).__name__))
    return {'delivered':delivered,'projects':results,'external_llm_calls':0,'at':now()}
