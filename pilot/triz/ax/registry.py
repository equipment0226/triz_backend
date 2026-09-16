"""Immutable checkpoints and audited, project-scoped next-run deployment pointers."""
import json
from sqlalchemy import Column,String,Integer,select,update
from . import ledger
from .contracts import canonical,digest,now,Conflict

versions=ledger.table('registry_versions',Column('version_id',String(80),primary_key=True),
    Column('kind',String(24),nullable=False),Column('tenant_id',String(64),nullable=False),
    Column('project_id',String(64),nullable=False),Column('payload',ledger.JSON,nullable=False),
    Column('content_hash',String(64),nullable=False),Column('created_at',String(40),nullable=False))
pointers=ledger.table('deployments',Column('scope',String(80),primary_key=True),
    Column('policy_id',String(80)),Column('previous_policy_id',String(80)),
    Column('shadow_policy_id',String(80)),Column('canary_percent',Integer,nullable=False),
    Column('rule_ids',ledger.JSON,nullable=False))
audit=ledger.table('registry_audit',Column('audit_id',String(80),primary_key=True),
    Column('scope',String(80),nullable=False),Column('payload',ledger.JSON,nullable=False),
    Column('created_at',String(40),nullable=False))
shadow=ledger.table('shadow_observations',Column('policy_id',String(80),primary_key=True),
    Column('decision_id',String(80),primary_key=True),Column('payload',ledger.JSON,nullable=False))


def scope(tenant,project):
    return digest([tenant,project])


def _pointer(c,tenant,project):
    key=scope(tenant,project)
    row=c.execute(select(pointers).where(pointers.c.scope==key).with_for_update()).mappings().first()
    if row: return dict(row)
    value={'scope':key,'policy_id':None,'previous_policy_id':None,'shadow_policy_id':None,'canary_percent':0,'rule_ids':'[]'}
    c.execute(pointers.insert().values(**value))
    return value


def _audit(c,tenant,project,payload):
    import uuid
    c.execute(audit.insert().values(audit_id='reg-'+uuid.uuid4().hex,scope=scope(tenant,project),payload=canonical(payload),created_at=now()))


def put(kind,tenant,project,payload):
    fingerprint=digest(payload)
    vid=kind+'-'+digest([tenant,project,fingerprint])[:58]
    with ledger.transaction() as c:
        _pointer(c,tenant,project)  # Serializes publication in this project.
        if not c.execute(select(versions.c.version_id).where(versions.c.version_id==vid)).first():
            c.execute(versions.insert().values(version_id=vid,kind=kind,tenant_id=tenant,project_id=project,
                payload=canonical(payload),content_hash=fingerprint,created_at=now()))
            _audit(c,tenant,project,{'action':'PUBLISHED_CANDIDATE','version_id':vid})
    return vid


def get(vid,tenant,project,c=None):
    if c is None:
        with ledger.store.engine.connect() as connection:
            return get(vid,tenant,project,connection)
    row=c.execute(select(versions).where(versions.c.version_id==vid,versions.c.tenant_id==tenant,
        versions.c.project_id==project)).mappings().first()
    if not row: raise ValueError('Registry version not found in project')
    payload=json.loads(row['payload'])
    if digest(payload)!=row['content_hash']: raise Conflict('Checkpoint integrity failure')
    return dict(row,payload=payload)


def reviews_current(payload,tenant,project,c):
    ids=payload.get('review_ids',[])
    if not ids: return False
    rows=c.execute(select(ledger.reviews).join(ledger.heads,ledger.heads.c.run_id==ledger.reviews.c.run_id)
        .join(ledger.store.runs,ledger.store.runs.c.run_id==ledger.heads.c.run_id)
        .where(ledger.heads.c.tenant_id==tenant,ledger.heads.c.project_id==project)).mappings().all()
    superseded={json.loads(r['payload']).get('supersedes_event_id') for r in rows}
    valid={r['event_id'] for r in rows if r['event_id'] not in superseded and json.loads(r['payload'])['consent']=='PROJECT_ONLY'}
    return set(ids)<=valid


def train_project(tenant,project,feature_schema='ax-features-v1'):
    from . import learning
    manifest=learning.dataset(tenant,project,feature_schema=feature_schema)
    ready=learning.readiness(manifest)
    if not ready['ready']: return dict(ready,status='COLLECTING')
    dataset_id=put('dataset',tenant,project,manifest)
    model=learning.train([s for s in manifest['samples'] if s['split']=='train'],feature_schema=feature_schema)
    evaluation=learning.evaluate(model,[s for s in manifest['samples'] if s['split']=='holdout'])
    eligible=(model['training']['parameters_changed'] and evaluation['logged_action_support']==1 and
        evaluation['bellman_mse'] is not None and evaluation['bellman_mse']<=evaluation['zero_q_mse'])
    payload={'model':model,'dataset_id':dataset_id,'readiness':ready,'evaluation':evaluation,
        'offline_eligible':eligible,'review_ids':sorted({r for s in manifest['samples'] for r in s['review_ids']})}
    policy_id=put('policy',tenant,project,payload)
    if eligible:
        with ledger.transaction() as c:
            p=_pointer(c,tenant,project)
            if reviews_current(payload,tenant,project,c):
                c.execute(update(pointers).where(pointers.c.scope==p['scope']).values(shadow_policy_id=policy_id))
                _audit(c,tenant,project,{'action':'SHADOW','policy_id':policy_id})
    return {'status':'SHADOW' if eligible else 'EVALUATION_FAILED','policy_id':policy_id,
        'evaluation':evaluation,'parameters_changed':model['training']['parameters_changed']}


def for_run(state,feature_schema='ax-features-v1'):
    tenant=state.user_id; project=state.scratch.get('ax_project_id',state.user_id)
    # init is additive and also supports first V3 run on an existing installation.
    ledger.init()
    with ledger.store.engine.connect() as c:
        pointer=c.execute(select(pointers).where(pointers.c.scope==scope(tenant,project))).mappings().first()
        if not pointer: return {}
        result={}
        for field in ('policy_id','shadow_policy_id'):
            vid=pointer[field]
            if not vid: continue
            payload=get(vid,tenant,project,c)['payload']
            if payload['model'].get('feature_schema','ax-features-v1')!=feature_schema: continue
            if not reviews_current(payload,tenant,project,c): continue
            if field=='policy_id' and int(digest(state.run_id)[:8],16)%100>=pointer['canary_percent']: continue
            result['policy' if field=='policy_id' else 'shadow_policy']=payload['model']
            result['policy_version' if field=='policy_id' else 'shadow_policy_version']=vid
        result['rule_catalog']=[]
        for vid in json.loads(pointer['rule_ids']):
            payload=get(vid,tenant,project,c)['payload']
            if reviews_current(payload,tenant,project,c):
                result['rule_catalog'].append(dict(payload['rule'],version_id=vid))
        result['rule_catalog_version']='rules-'+digest(result['rule_catalog'])[:32]
        return result


def observe_shadow(policy_id,decision_id,payload):
    with ledger.transaction() as c:
        if not c.execute(select(shadow).where(shadow.c.policy_id==policy_id,shadow.c.decision_id==decision_id)).first():
            c.execute(shadow.insert().values(policy_id=policy_id,decision_id=decision_id,payload=canonical(payload)))


def promote_policy(tenant,project,policy_id,actor,reason,percent=10):
    if not actor or not reason.strip() or not 1<=percent<=25: raise ValueError('Operator, rationale and bounded canary required')
    with ledger.transaction() as c:
        p=_pointer(c,tenant,project)
        data=get(policy_id,tenant,project,c)['payload']
        observations=[json.loads(v) for v in c.execute(select(shadow.c.payload).where(shadow.c.policy_id==policy_id)).scalars()]
        if not data.get('offline_eligible') or not reviews_current(data,tenant,project,c): raise Conflict('Offline data not eligible or consent withdrawn')
        if len(observations)<20 or len({o['run_id'] for o in observations})<5 or any(not o['legal'] or not o['supported'] for o in observations):
            raise Conflict('Insufficient clean shadow runs')
        c.execute(update(pointers).where(pointers.c.scope==p['scope']).values(previous_policy_id=p['policy_id'],
            policy_id=policy_id,canary_percent=percent))
        _audit(c,tenant,project,{'action':'CANARY','policy_id':policy_id,'percent':percent,'actor':actor,'reason':reason})


def rollback(tenant,project,actor,reason):
    if not actor or not reason.strip(): raise ValueError('Operator and rationale required')
    with ledger.transaction() as c:
        p=_pointer(c,tenant,project)
        c.execute(update(pointers).where(pointers.c.scope==p['scope']).values(policy_id=p['previous_policy_id'],
            previous_policy_id=None,shadow_policy_id=None,canary_percent=10 if p['previous_policy_id'] else 0))
        _audit(c,tenant,project,{'action':'ROLLBACK','actor':actor,'reason':reason,'from':p['policy_id'],'to':p['previous_policy_id']})
