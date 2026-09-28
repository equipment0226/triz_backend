"""Versioned action-dependent conservative linear Q; CPU only, no exploration."""
import copy
import math
from collections import Counter
from .contracts import digest

SCHEMA = 'ax-state-action-v3'
DIMENSIONS = 512
REWARD_CONTRACT = 'concept-proxy-cost-v1'


def state_features(state, phase='optional'):
    from .coherence import assess
    report = assess(state)
    return {'schema': SCHEMA, 'mode': state.control.mode.value, 'phase': phase,
            'domain':state.domain.problem_type,
            'remaining': max(0, 1 - state.cost.total_usd / max(.001, state.cost.budget_usd)),
            'gaps': sorted({g['kind'] for r in report['candidates'] for g in r['gaps']}),
            'uncovered': [o['id'] for o in report['coverage_gaps']],
            'tracks': sorted(state.solve.tracks_run),
            'candidates': {c.id: {'quality': c.quality_status,
                'conditional': bool(state.check_for(c.id) and state.check_for(c.id).verdict == 'CONDITIONAL')}
                for c in state.concepts},
            'attempts': min(1, len(state.scratch.get('ax_recovery', [])) / 6)}


def support_key(ticket):
    p = ticket.get('parameters', {})
    return '|'.join([ticket['action_type'], ','.join(p.get('tracks', [])),
                     ','.join(sorted(p.get('gap_kinds', []))), ticket.get('model_role', 'CODE')])


def support_region(features,ticket):
    return digest([features.get('mode'),features.get('domain'),features.get('phase'),support_key(ticket)])


def phi(state, ticket):
    if not isinstance(state, dict) or state.get('schema') != SCHEMA:
        raise ValueError('Routing state schema mismatch')
    p = ticket.get('parameters', {})
    target = p.get('candidate_id', '')
    action = ['action=' + ticket['action_type'], 'role=' + ticket.get('model_role', 'CODE')]
    action += ['track=' + x for x in p.get('tracks', [])]
    action += ['gap=' + x for x in p.get('gap_kinds', [])]
    action += ['function=' + x for x in p.get('required_functions', [])]
    if target:
        action += ['target=' + target, 'target_quality=' + state.get('candidates', {}).get(target, {}).get('quality', 'UNKNOWN')]
    context = ['mode=' + state.get('mode', 'UNKNOWN'), 'phase=' + state.get('phase', 'optional')]
    context += ['gap=' + x for x in state.get('gaps', [])]
    context += ['done=' + x for x in state.get('tracks', [])]
    terms = {x: 1.0 for x in action}
    terms.update({s + '*' + a: 1.0 for s in context for a in action})
    for a in action:
        terms['remaining*' + a] = float(state.get('remaining', 0))
        terms['attempts*' + a] = float(state.get('attempts', 0))
    terms['remaining*cost'] = float(state.get('remaining', 0)) * min(1, ticket.get('reserved_microusd', 0) / 1e6)
    terms['target_conditional'] = float(state.get('candidates', {}).get(target, {}).get('conditional', False))
    result = {}
    for name, value in terms.items():
        if not math.isfinite(value):
            raise ValueError('Non-finite routing feature')
        key = int(digest(name)[:8], 16) % DIMENSIONS
        result[key] = result.get(key, 0.0) + value
    scale = math.sqrt(max(1, sum(v * v for v in result.values())))
    return {k: v / scale for k, v in result.items()}


def validate(policy):
    if (policy.get('feature_schema') != SCHEMA or len(policy.get('weights', [])) != DIMENSIONS
            or any(not math.isfinite(w) for w in policy['weights'])):
        raise ValueError('Incompatible routing checkpoint; no padding is permitted')


def score(policy, features, ticket):
    validate(policy)
    return sum(policy['weights'][i] * v for i, v in phi(features, ticket).items())


def choose(policy, features, tickets, permitted, preferred):
    try:
        validate(policy)
        counts = policy.get('support', {})
        supported = [i for i in permitted if counts.get(support_key(tickets[i]), 0) >= 4
                     and policy.get('state_support',{}).get(support_region(features,tickets[i]),0)>=4]
        # Unobserved options (including unlabeled DEFER) cannot win on a large
        # extrapolated value. Two supported, distinct jobs still permit a choice.
        if len(supported) < 2:
            return preferred, {}, 'insufficient_action_support'
        scores = {i: score(policy, features, tickets[i]) for i in supported}
        return max(scores, key=lambda i: (scores[i], -i)), scores, None
    except (ValueError, TypeError, KeyError):
        return preferred, {}, 'incompatible_feature_schema'


def train(samples, *, epochs=180, learning_rate=.05, discount=.8, alpha=.03):
    if not samples or len(samples)>2000 or not 1 <= epochs <= 2000:
        raise ValueError('Bounded nonempty training batch required')
    rows = []
    for row in samples:
        actions = row['actions']
        index = row['executed_index']
        if index not in row['permitted'] or not math.isfinite(row['reward']):
            raise ValueError('Invalid logged action or reward')
        rows.append((row, [phi(row['features'], a) for a in actions],
                     [phi(row['next_features'], a) for a in row.get('next_actions', [])]))
    weights = [0.0] * DIMENSIONS
    target = list(weights)
    support = Counter(support_key(r['actions'][r['executed_index']]) for r in samples)
    state_support=Counter(support_region(r['features'],r['actions'][r['executed_index']]) for r in samples)
    initial = digest(weights)
    losses = []
    dot = lambda w, x: sum(w[i] * v for i, v in x.items())
    for epoch in range(epochs):
        gradient = [0.0] * DIMENSIONS
        loss = 0.0
        for row, xs, next_xs in rows:
            legal = row['permitted']; selected = row['executed_index']
            qs = {i: dot(weights, xs[i]) for i in legal}
            next_values = [dot(target, x) for x, a in zip(next_xs, row.get('next_actions', []))
                           if support.get(support_key(a), 0) >= 4]
            y = row['reward'] + (discount * max(next_values) if next_values and not row['terminal'] else 0)
            error = max(-5, min(5, qs[selected] - y))
            maximum = max(qs.values()); total = sum(math.exp(q - maximum) for q in qs.values())
            loss += .5 * error ** 2 + alpha * (maximum + math.log(total) - qs[selected])
            for i in legal:
                derivative = (error if i == selected else 0) + alpha * (math.exp(qs[i] - maximum) / total - (i == selected))
                for k, v in xs[i].items():
                    gradient[k] += derivative * v / len(rows)
        weights = [w - learning_rate * g for w, g in zip(weights, gradient)]
        if epoch % 10 == 0:
            target = list(weights)
        losses.append(loss / len(rows))
    return {'algorithm': 'linear-conservative-state-action-q-v3', 'feature_schema': SCHEMA,
            'weights': weights, 'support': dict(support), 'discount': discount, 'alpha': alpha,
            'state_support':dict(state_support),
            'epochs': epochs, 'reward_contract': REWARD_CONTRACT,
            'training': {'parameters_changed': initial != digest(weights),
                         'loss_first': losses[0], 'loss_last': losses[-1]},
            'support_actions': sorted({r['actions'][r['executed_index']]['action_type'] for r in samples})}


def evaluate(policy, samples):
    errors = []; zero = []; supported = 0
    for s in samples:
        ticket = s['actions'][s['executed_index']]
        value = score(policy, s['features'], ticket)
        next_values = [score(policy, s['next_features'], a) for a in s.get('next_actions', [])
                       if policy['support'].get(support_key(a), 0) >= 4]
        target = s['reward'] + (policy['discount'] * max(next_values) if next_values and not s['terminal'] else 0)
        errors.append((value - target) ** 2); zero.append(s['reward'] ** 2)
        supported += policy['support'].get(support_key(ticket), 0) >= 4
    return {'samples': len(samples), 'bellman_mse': sum(errors) / len(errors) if errors else None,
            'zero_q_mse': sum(zero) / len(zero) if zero else None,
            'logged_action_support': supported / len(samples) if samples else 0,
            'field_improvement_established': False, 'off_policy_value_estimate': None}


def dataset(tenant, project, cutoff=None):
    import json
    from collections import defaultdict
    from sqlalchemy import select
    from . import ledger, effect_history
    from .contracts import now
    cutoff = cutoff or now(); rows = []; excluded = Counter()
    effect_labels = effect_history.observations(tenant, project, cutoff=cutoff)
    with ledger.store.engine.connect() as c:
        heads = c.execute(select(ledger.heads.c.run_id,ledger.heads.c.owner_id,ledger.heads.c.budget)
            .where(ledger.heads.c.tenant_id==tenant, ledger.heads.c.project_id==project,
                   ledger.heads.c.run_id.in_(select(ledger.decisions.c.run_id)))).mappings().all()
    for h in heads:
        decisions = {d['decision_id']:d for d in ledger.decision_history(h['run_id'],h['owner_id'])
                     if d['created_at']<=cutoff and d['payload'].get('feature_schema')==SCHEMA}
        if not decisions:
            continue
        state = ledger.store.load_state(h['run_id'])
        if not state or state.scratch.get('acceptance_fixture') or state.scratch.get('synthetic'):
            excluded['test_or_missing_run'] += 1
            continue
        with ledger.store.engine.connect() as c:
            events = [dict(r,payload=json.loads(r['payload'])) for r in c.execute(select(ledger.events)
                .where(ledger.events.c.run_id==h['run_id'],ledger.events.c.created_at<=cutoff)
                .order_by(ledger.events.c.created_at)).mappings()]
        results = {}; transitions = {}
        for event in events:
            p=event['payload']
            if event['event_type']=='ACTION_INSTANCE_RESULT' and p.get('optional'):
                results[p['action_instance_id']]=p
            if event['event_type']=='OPTIONAL_TRANSITION':
                transitions[p['decision_id']]=p
        labels = defaultdict(list)
        for row in effect_labels:
            app=row['application']; review=row['review']
            if app['run_id']!=h['run_id']:
                continue
            causal=[results[aid] for aid in app['action_instance_ids'] if aid in results]
            if len(causal)!=1:
                excluded['joint_or_unknown_action_attribution']+=1
                continue
            did=causal[0].get('decision_id')
            labels[did].append(dict(value=.5*row['label'], maturity='CONCEPT_PROXY', id=review['event_id'],
                available_at=review['label_available_at'], group=app['problem_family'], origin=review['origin_event_id']))
        for review in ledger.active_reviews(h['run_id'],h['owner_id']):
            p=review['payload']
            if review['created_at']>cutoff or p['consent']!='PROJECT_ONLY' or not p.get('decision_id'):
                continue
            if p['decision_type'] in ('RECORD_TEST_RESULT','RECORD_FIELD_RESULT') and p['result'] in ('PASS','FAIL'):
                # submit_review already checks immutable candidate/obligation/decision lineage.
                artifact=ledger.artifact(h['run_id'],p['target_version_id'],h['owner_id'])
                labels[p['decision_id']].append(dict(value=1 if p['result']=='PASS' else -1,
                    maturity='TECHNICAL',id=review['event_id'],available_at=review['created_at'],
                    group=state.scratch.get('ax_problem_group') or digest(effect_history.structured_context(state)),
                    origin=review['event_id']))
        for did,d in decisions.items():
            p=d['payload']; result=results.get(p.get('executed_action_instance')); transition=transitions.get(did)
            if p.get('selection_mode')=='FORCED':
                excluded['forced_action']+=1; continue
            if not result or result['status']!='COMPLETED':
                excluded['missing_or_failed_result']+=1; continue
            if result.get('actual_microusd') is None:
                excluded['unsettled_usage']+=1; continue
            judgments=labels.get(did, [])
            if not judgments:
                excluded['unobserved_reward']+=1; continue
            if not transition:
                excluded['open_optional_transition']+=1; continue
            next_id=transition.get('next_decision_id')
            next_row=decisions.get(next_id)
            if next_id and (not next_row or next_row['payload']['semantic_episode_id']!=p['semantic_episode_id']):
                excluded['cross_episode_or_future_transition']+=1; continue
            unique={j['origin']:j for j in judgments}
            judgments=list(unique.values())
            # Conservative aggregation: an explicit negative is not outweighed by popularity.
            quality=min(j['value'] for j in judgments)
            cost=min(.25,.1*result['actual_microusd']/max(1,h['budget']))
            tickets=[a['ticket'] for a in p['actions']]
            permitted=[i for i,a in enumerate(p['actions']) if a['allowed']]
            nxt=next_row['payload'] if next_row else None
            rows.append(dict(decision_id=did,run_id=h['run_id'],semantic_episode_id=p['semantic_episode_id'],
                group=judgments[0]['group'],available_at=max(j['available_at'] for j in judgments),
                features=p['features'],actions=tickets,executed_index=p['executed_index'],permitted=permitted,
                action=support_key(tickets[p['executed_index']]),next_features=nxt['features'] if nxt else p['features'],
                next_actions=[a['ticket'] for a in nxt['actions'] if a['allowed']] if nxt else [],
                terminal=next_id is None,terminal_reason=transition.get('terminal_reason'),
                reward=quality-cost,dimensions=dict(concept_or_observed_judgment=quality,normalized_cost=cost,
                    actual_microusd=result['actual_microusd']),reward_contract=REWARD_CONTRACT,
                maturity='TECHNICAL' if any(j['maturity']=='TECHNICAL' for j in judgments) else 'CONCEPT_PROXY',
                feature_schema=SCHEMA,review_ids=sorted({j['id'] for j in judgments}),behavior_probability=None))
    rows,limited=bounded_families(rows)
    excluded['cpu_batch_limit']+=limited
    families=sorted({r['group'] for r in rows},key=lambda g:max(r['available_at'] for r in rows if r['group']==g))
    holdout=set(families[-max(1,len(families)//4):])
    for row in rows:
        row['split']='holdout' if row['group'] in holdout else 'train'
    return dict(schema='ax-dataset-v3',feature_schema=SCHEMA,task_kind='routing_q',samples=rows,
                excluded=dict(excluded),cutoff=cutoff,synthetic=False,tenant_id=tenant,project_id=project)


def bounded_families(rows, limit=2000):
    from collections import defaultdict
    groups=defaultdict(list)
    for row in rows:
        groups[row['group']].append(row)
    kept=[]
    for key in sorted(groups,key=lambda k:max(r['available_at'] for r in groups[k]),reverse=True):
        if len(kept)+len(groups[key])<=limit:
            kept.extend(groups[key])
    return kept,len(rows)-len(kept)
