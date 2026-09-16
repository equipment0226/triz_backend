"""CPU-only conservative offline Q learning. No provider calls or LLM fine tuning.

The linear Q network has 12 action heads and 8 state features. A Bellman loss
updates its actual weights; a masked log-sum-exp penalty discourages unsupported
values. Evaluation describes logged support, not counterfactual field success.
"""
import copy
import json
import math
from collections import Counter,defaultdict
from sqlalchemy import select
from . import ledger
from .contracts import ACTIONS,digest,now

FEATURES=8
FEATURE_SCHEMAS={'ax-features-v1':8,'ax-features-v2':12}


def q_values(policy,x):
    size=FEATURE_SCHEMAS.get(policy.get('feature_schema','ax-features-v1'))
    if size is None or len(x)!=size or any(not math.isfinite(v) for v in x):
        raise ValueError('Invalid feature vector')
    weights=policy['weights']
    if len(weights)!=len(ACTIONS) or any(len(w)!=size for w in weights):
        raise ValueError('Invalid Q checkpoint')
    values=[sum(a*b for a,b in zip(row,x)) for row in weights]
    if any(not math.isfinite(v) for v in values):
        raise ValueError('Non-finite Q checkpoint')
    return values


def choose(policy,x,actions,permitted,preferred=None):
    supported=set(policy.get('support_actions',[]))
    choices=[i for i in permitted if actions[i] in supported]
    if not choices:
        return preferred if preferred in permitted else permitted[0]
    q=q_values(policy,x)
    return max(choices,key=lambda i:(q[ACTIONS.index(actions[i])],-i))


def dataset(tenant_id,project_id,*,cutoff=None,feature_schema='ax-features-v1'):
    size=FEATURE_SCHEMAS[feature_schema]
    cutoff=cutoff or now()
    samples=[]
    exclusions=Counter()
    with ledger.store.engine.connect() as c:
        runs=c.execute(select(ledger.heads).where(ledger.heads.c.tenant_id==tenant_id,
            ledger.heads.c.project_id==project_id)).mappings().all()
    for h in runs:
        state=ledger.store.load_state(h['run_id'])
        if not state or state.scratch.get('acceptance_fixture'):
            exclusions['test_or_missing_run']+=1
            continue
        decisions=[d for d in ledger.decision_history(h['run_id'],h['owner_id']) if d['created_at']<=cutoff]
        if h['bundle'] and json.loads(h['bundle']).get('feature_schema','ax-features-v1')!=feature_schema:
            exclusions['different_feature_schema']+=1
            continue
        # Equal timestamps have a deterministic insertion order only if explicit order exists.
        decisions.sort(key=lambda d:(d['created_at'],d['decision_id']))
        by_decision=defaultdict(list)
        for r in ledger.active_reviews(h['run_id'],h['owner_id']):
            p=r['payload']
            if r['created_at']>cutoff or p['consent']!='PROJECT_ONLY' or not p.get('decision_id'):
                exclusions['unconsented_unlinked_or_late']+=1
                continue
            if p['decision_type'] in ('RECORD_TEST_RESULT','RECORD_FIELD_RESULT') and p['result'] in ('PASS','FAIL'):
                if feature_schema=='ax-features-v2' and p['result']=='PASS':
                    from .coherence import candidate_check
                    candidate=state.concept(p.get('candidate_id'))
                    if (not candidate or p['target_version_id']!=state.scratch.get('ax_members',{}).get('concepts')
                            or candidate_check(state,candidate)['gaps']):
                        exclusions['incomplete_or_stale_positive_technical_label']+=1
                        continue
                maturity='FIELD' if p['decision_type']=='RECORD_FIELD_RESULT' else 'TEST'
                value=(2.0 if maturity=='FIELD' else 1.0)*(1 if p['result']=='PASS' else -1)
            elif p['decision_type'] in ('APPROVE_EXPLORATION','REJECT_EXPLORATION'):
                maturity='PREFERENCE'
                value=.05*(1 if p['decision_type']=='APPROVE_EXPLORATION' else -1)
            else:
                exclusions['missing_technical_or_preference_label']+=1
                continue
            by_decision[p['decision_id']].append((r,value,maturity))
        for i,d in enumerate(decisions):
            labels=by_decision.get(d['decision_id'])
            if not labels:
                continue
            p=d['payload']
            if len(p['features'])!=size:
                exclusions['invalid_feature_shape']+=1
                continue
            selected=p['actions'][p['executed_index']]
            if not selected['allowed'] or p['governor_override']:
                exclusions['override_not_policy_action']+=1
                continue
            nxt=decisions[i+1]['payload'] if i+1<len(decisions) else None
            if nxt is None and state.status!='COMPLETED':
                exclusions['unfinished_transition']+=1
                continue
            # Multiple branches/revisions are not summed as multiple successes.
            technical=[x for x in labels if x[2]!='PREFERENCE']
            chosen=technical or labels
            value=sum(x[1] for x in chosen)/len(chosen)
            with ledger.store.engine.connect() as c:
                attempts=c.execute(select(ledger.attempts.c.details).where(ledger.attempts.c.run_id==h['run_id'])).scalars().all()
            usage=[json.loads(a) for a in attempts if json.loads(a).get('request',{}).get('decision_id')==d['decision_id']]
            if any(a.get('actual_microusd') is None for a in usage):
                exclusions['unsettled_usage']+=1
                continue
            cost=sum(a.get('actual_microusd',0) for a in usage)/1e6
            group=state.scratch.get('ax_problem_group') or digest(' '.join(state.raw_query.lower().split()))
            samples.append({'decision_id':d['decision_id'],'run_id':h['run_id'],'group':group,
                'available_at':d['created_at'],'features':p['features'],'action':selected['ticket']['action_type'],
                'allowed':list(dict.fromkeys(a['ticket']['action_type'] for a in p['actions'] if a['allowed'])),
                'next_features':nxt['features'] if nxt else [0.0]*size,
                'next_allowed':list(dict.fromkeys(a['ticket']['action_type'] for a in nxt['actions'] if a['allowed'])) if nxt else [],
                'terminal':nxt is None,'reward':max(-2,min(2,value-cost)),
                'dimensions':{'observed_judgment':value,'cost_usd':cost,'field_observed':any(x[2]=='FIELD' for x in chosen)},
                'maturity':'TECHNICAL' if technical else 'PREFERENCE','feature_schema':feature_schema,'review_ids':[x[0]['event_id'] for x in chosen],
                'review_hashes':[x[0]['content_hash'] for x in chosen],
                'behavior_probability':p.get('behavior_probability')})
    # Bound the CPU batch while retaining complete families, newest first.
    grouped=defaultdict(list)
    for s in samples: grouped[s['group']].append(s)
    selected=[]
    for group in sorted(grouped,key=lambda g:max(s['available_at'] for s in grouped[g]),reverse=True):
        if len(selected)+len(grouped[group])<=2000:
            selected.extend(grouped[group])
        else:
            exclusions['cpu_batch_limit']+=len(grouped[group])
    samples=selected
    # Entire problem families remain together. Latest families form the time holdout.
    latest={g:max(s['available_at'] for s in samples if s['group']==g) for g in {s['group'] for s in samples}}
    ordered=sorted(latest,key=lambda g:(latest[g],g))
    holdout=set(ordered[-max(1,len(ordered)//4):]) if ordered else set()
    for s in samples:
        s['split']='holdout' if s['group'] in holdout else 'train'
    manifest={'schema':'ax-dataset-v1','feature_schema':feature_schema,'action_catalog':'ax-actions-v1',
        'tenant_id':tenant_id,'project_id':project_id,'cutoff':cutoff,'samples':samples,
        'excluded':dict(exclusions),'synthetic':False,'split':'problem-group time holdout; exact-query fallback'}
    manifest['dataset_id']='dataset-'+digest(manifest)
    return manifest


def readiness(manifest):
    samples=manifest['samples']
    training=[s for s in samples if s['split']=='train']
    holdout=[s for s in samples if s['split']=='holdout']
    counts=Counter(s['action'] for s in training)
    reasons=[]
    if manifest.get('synthetic'): reasons.append('synthetic_dataset')
    if len(samples)<32: reasons.append('fewer_than_32_confirmed_decisions')
    if len({s['group'] for s in samples})<8: reasons.append('insufficient_independent_problems')
    if len({s['group'] for s in holdout})<2: reasons.append('insufficient_time_holdout')
    if len([a for a,n in counts.items() if n>=4])<2: reasons.append('insufficient_action_support')
    if sum(s['maturity']=='TECHNICAL' for s in samples)<8: reasons.append('insufficient_technical_observations')
    if {s['group'] for s in training}&{s['group'] for s in holdout}: reasons.append('split_leakage')
    return {'ready':not reasons,'reasons':reasons,'action_support':dict(counts),'samples':len(samples)}


def train(samples,*,epochs=180,learning_rate=.025,discount=.8,alpha=.05,feature_schema=None):
    if not samples or epochs<1 or epochs>2000:
        raise ValueError('Bounded nonempty training batch required')
    feature_schema=feature_schema or samples[0].get('feature_schema','ax-features-v1')
    size=FEATURE_SCHEMAS[feature_schema]
    if any(len(s['features'])!=size or len(s['next_features'])!=size or
           s.get('feature_schema',feature_schema)!=feature_schema for s in samples):
        raise ValueError('Mixed feature schemas cannot share a checkpoint')
    weights=[[0.0]*size for _ in ACTIONS]
    target=copy.deepcopy(weights)
    support=sorted({s['action'] for s in samples})
    policy={'algorithm':'linear-conservative-offline-q-v1','weights':weights,'support_actions':support,
            'feature_schema':feature_schema,'action_catalog':'ax-actions-v1',
            'discount':discount,'alpha':alpha,'epochs':epochs}
    initial=digest(weights)
    losses=[]
    for epoch in range(epochs):
        loss=0.0
        gradients=[[0.0]*size for _ in ACTIONS]
        for s in samples:
            x=s['features']; q=q_values(policy,x); a=ACTIONS.index(s['action'])
            legal=[ACTIONS.index(k) for k in s['allowed']]
            if a not in legal: raise ValueError('Logged action violates its mask')
            next_q=[sum(w*v for w,v in zip(target[ACTIONS.index(k)],s['next_features']))
                    for k in s['next_allowed'] if k in support]
            y=s['reward']+(discount*max(next_q) if not s['terminal'] and next_q else 0)
            error=max(-5,min(5,q[a]-y))
            highest=max(q[j] for j in legal)
            denominator=sum(math.exp(q[j]-highest) for j in legal)
            loss += .5*error*error+alpha*(highest+math.log(denominator)-q[a])
            for j in legal:
                derivative=(error if j==a else 0)+alpha*(math.exp(q[j]-highest)/denominator-(1 if j==a else 0))
                for f in range(size):
                    gradients[j][f]+=derivative*x[f]/len(samples)
        for j in range(len(ACTIONS)):
            for f in range(size):
                weights[j][f]-=learning_rate*gradients[j][f]
        if epoch%10==0: target=copy.deepcopy(weights)
        losses.append(loss/len(samples))
    q_values(policy,[1.0]*size)
    policy['training']={'initial_weights_hash':initial,'final_weights_hash':digest(weights),
        'parameters_changed':initial!=digest(weights),'loss_first':losses[0],'loss_last':losses[-1]}
    return policy


def evaluate(policy,samples):
    errors=[]; baseline=[]; supported=0
    for s in samples:
        q=q_values(policy,s['features'])[ACTIONS.index(s['action'])]
        next_values=[q_values(policy,s['next_features'])[ACTIONS.index(a)] for a in s['next_allowed'] if a in policy['support_actions']]
        target=s['reward']+(policy['discount']*max(next_values) if not s['terminal'] and next_values else 0)
        errors.append((q-target)**2)
        baseline.append(s['reward']**2)
        supported+=s['action'] in policy['support_actions']
    return {'samples':len(samples),'bellman_mse':sum(errors)/len(errors) if errors else None,
        'zero_q_mse':sum(baseline)/len(baseline) if baseline else None,
        'logged_action_support':supported/len(samples) if samples else 0,
        'off_policy_value_estimate':None,'field_improvement_established':False}
