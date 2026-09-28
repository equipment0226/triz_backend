"""Versioned action-dependent conservative linear Q; CPU only, no exploration."""
import copy
import math
from collections import Counter
from .contracts import digest

SCHEMA = 'ax-state-action-v3'
DIMENSIONS = 512
REWARD_CONTRACT = 'concept-proxy-cost-v1'
SUPPORT_CONTRACT = 'action-region-support-v1'
BACKUP_CONTRACT = 'supported-rule-backup-v1'
SUPPORT_SETTINGS = {'version': SUPPORT_CONTRACT, 'minimum_count': 4}


def contracts():
    return dict(support_contract=SUPPORT_CONTRACT, backup_contract=BACKUP_CONTRACT,
                support_settings=dict(SUPPORT_SETTINGS), exploration_contract='triz-targeted-expansion-v1')


def validate_contract(policy):
    validate(policy)
    if any(policy.get(k) != v for k, v in contracts().items()):
        raise ValueError('Incompatible support/backup/handler contract')
    for table in ('support', 'state_support'):
        if not isinstance(policy.get(table), dict) or any(type(n) is not int or n < 0 for n in policy[table].values()):
            raise ValueError('invalid_support_count')


def _legal(features, tickets, permitted):
    if not isinstance(features, dict) or features.get('schema') != SCHEMA:
        raise ValueError('incompatible_contract')
    if (not isinstance(permitted, list) or any(type(i) is not int or i < 0 or i >= len(tickets) for i in permitted)
            or len(set(permitted)) != len(permitted)):
        raise ValueError('invalid_legal_mask')
    # Static mode constraints supplement the immutable governor mask; no live state lookup.
    return [i for i in permitted if features.get('mode') != 'DEEP'
            and not (features.get('mode') in ('LITE', 'FULL')
                     and 'D_ARIZ' in tickets[i].get('parameters', {}).get('tracks', []))]


def _job(ticket):
    p = copy.deepcopy(ticket.get('parameters', {}))
    for key in ('attempt', 'timestamp', 'execution_epoch', 'input_snapshot_id'):
        p.pop(key, None)
    return digest([ticket['action_type'], ticket.get('target_version_ids', []), p, ticket.get('model_role', 'CODE')])


def supported_action_indices(policy, features, tickets, permitted):
    """Pure support audit using fixed train counts and the recorded legal mask."""
    result = dict(legal=[], supported=[], independent=[], rejected={}, error=None)
    try:
        legal = _legal(features, tickets, permitted)
        result['legal'] = legal
        validate_contract(policy)
        seen = set()
        for i, ticket in enumerate(tickets):
            if i not in legal:
                result['rejected'][i] = 'illegal'
                continue
            phi(features, ticket)  # Includes finite-feature validation even on fallback.
            if policy['support'].get(support_key(ticket), 0) < SUPPORT_SETTINGS['minimum_count']:
                result['rejected'][i] = 'action_support_missing'
            elif policy['state_support'].get(support_region(features, ticket), 0) < SUPPORT_SETTINGS['minimum_count']:
                result['rejected'][i] = 'state_support_missing'
            else:
                result['supported'].append(i)
                job = _job(ticket)
                if job not in seen:
                    result['independent'].append(i)
                    seen.add(job)
                else:
                    result['rejected'][i] = 'duplicate_job'
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        result.update(supported=[], independent=[], error='incompatible_contract', detail=str(exc))
    return result


def next_state_backup(*, support_model, value_model, transition):
    """Limited deployed policy: greedy only with two independent supported jobs."""
    def answer(status, value=None, mask=None, **extra):
        return dict(status=status, value=value, mask=mask or [], **extra)
    if transition.get('td_exclusion_reason'):
        return answer('SKIP_INVALID_TRANSITION', reason=transition['td_exclusion_reason'])
    if transition.get('terminal') is True:
        return answer('TERMINAL', 0.0)
    if transition.get('terminal') is not False:
        return answer('SKIP_INVALID_TRANSITION', reason='missing_terminal_flag')
    if (transition.get('next_semantic_episode_id') is not None and
            transition.get('next_semantic_episode_id') != transition.get('semantic_episode_id')):
        return answer('SKIP_INVALID_TRANSITION', reason='cross_episode')
    if any(k not in transition for k in ('next_features', 'next_actions', 'next_permitted')):
        return answer('SKIP_INVALID_TRANSITION', reason='incomplete_next_decision')
    for key, expected in contracts().items():
        if key in transition and transition[key] != expected:
            return answer('SKIP_INVALID_TRANSITION', reason='incompatible_contract')
    if 'next_contracts' in transition and transition['next_contracts'] != contracts():
        return answer('SKIP_INVALID_TRANSITION', reason='incompatible_next_contract')
    actions = transition['next_actions']; features = transition['next_features']
    audit = supported_action_indices(support_model, features, actions, transition['next_permitted'])
    if audit['error'] or not audit['legal']:
        return answer('SKIP_INVALID_TRANSITION', reason=audit['error'] or 'empty_legal', diagnostics=audit)
    mask = audit['independent']
    if len(mask) >= 2:
        status = 'SUPPORTED_GREEDY'
    elif len(audit['legal']) == 1 and audit['legal'][0] in audit['supported']:
        status, mask = 'SUPPORTED_FORCED', audit['legal']
    else:
        preferred = transition.get('next_rule_preferred')
        if type(preferred) is not int or preferred not in audit['supported']:
            return answer('SKIP_UNSUPPORTED_FALLBACK', reason='unsupported_or_missing_rule', diagnostics=audit)
        status, mask = 'SUPPORTED_RULE', [preferred]
    try:
        values = {i: score(value_model, features, actions[i]) for i in mask}
        if any(not math.isfinite(v) for v in values.values()):
            raise ValueError('nonfinite_score')
        chosen = max(values, key=lambda i: (values[i], -i))
        return answer(status, values[chosen], mask, selected=chosen, diagnostics=audit)
    except (ValueError, TypeError, KeyError, OverflowError):
        return answer('SKIP_INVALID_TRANSITION', reason='nonfinite_or_incompatible_score', diagnostics=audit)


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


def choose_legacy(policy, features, tickets, permitted, preferred):
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


def choose(policy, features, tickets, permitted, preferred):
    audit = supported_action_indices(policy, features, tickets, permitted)
    fallback = preferred if preferred in audit['legal'] else next(iter(audit['legal']), None)
    if audit['error']:
        return fallback, {}, 'incompatible_feature_schema'
    if len(audit['independent']) < 2:
        return fallback, {}, 'insufficient_action_support'
    try:
        scores = {i: score(policy, features, tickets[i]) for i in audit['independent']}
        if any(not math.isfinite(v) for v in scores.values()):
            raise ValueError('Nonfinite score')
        return max(scores, key=lambda i: (scores[i], -i)), scores, None
    except (ValueError, TypeError, KeyError, OverflowError):
        return fallback, {}, 'incompatible_feature_schema'


def support_model(samples):
    """Only eligible observations from the training partition contribute counts."""
    counts, regions = Counter(), Counter()
    for row in samples:
        if row.get('split', 'train') != 'train':
            raise ValueError('Holdout observations cannot build support')
        actions = row['actions']; index = row['executed_index']
        if type(index) is not int or index not in _legal(row['features'], actions, row['permitted']) or not math.isfinite(row['reward']):
            raise ValueError('Invalid logged action or reward')
        for key, expected in contracts().items():
            if key in row and row[key] != expected:
                raise ValueError('Mixed support/backup/handler contracts')
        phi(row['features'], actions[index])
        counts[support_key(actions[index])] += 1
        regions[support_region(row['features'], actions[index])] += 1
    return dict(contracts(), feature_schema=SCHEMA, weights=[0.] * DIMENSIONS,
                support=dict(counts), state_support=dict(regions))


def _metrics(policy, samples, backups):
    action_count = region_count = 0
    for row in samples:
        audit = supported_action_indices(policy, row['features'], row['actions'], row['permitted'])
        index = row['executed_index']
        action_count += index in audit['legal'] and audit['rejected'].get(index) not in ('action_support_missing', 'illegal') and not audit['error']
        region_count += index in audit['supported']
    return dict(samples=len(samples), td_used=sum(b['value'] is not None for b in backups),
                excluded=dict(Counter(b.get('reason', b['status']) for b in backups if b['value'] is None)),
                backup_statuses=dict(Counter(b['status'] for b in backups)),
                action_support_coverage=action_count / len(samples) if samples else 0,
                state_support_coverage=region_count / len(samples) if samples else 0)


def train(samples, *, epochs=180, learning_rate=.05, discount=.8, alpha=.03):
    if not samples or len(samples)>2000 or not 1 <= epochs <= 2000:
        raise ValueError('Bounded nonempty training batch required')
    model = support_model(samples)
    model.update(discount=discount, alpha=alpha)
    rows = []; backups = []
    for row in samples:
        backup = next_state_backup(support_model=model, value_model=model, transition=row)
        backups.append(backup)
        if backup['value'] is not None:
            rows.append((row, [phi(row['features'], a) for a in row['actions']]))
    weights = [0.0] * DIMENSIONS
    target = list(weights)
    initial = digest(weights)
    losses = []
    dot = lambda w, x: sum(w[i] * v for i, v in x.items())
    for epoch in range(epochs):
        gradient = [0.0] * DIMENSIONS
        loss = 0.0
        for row, xs in rows:
            legal = _legal(row['features'], row['actions'], row['permitted']); selected = row['executed_index']
            qs = {i: dot(weights, xs[i]) for i in legal}
            backup = next_state_backup(support_model=model, value_model=dict(model, weights=target), transition=row)
            if backup['value'] is None:
                raise ValueError('Backup became invalid during training')
            y = row['reward'] + discount * backup['value']
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
        losses.append(loss / len(rows) if rows else None)
    return dict(model, **{'algorithm': 'linear-conservative-state-action-q-v3', 'feature_schema': SCHEMA,
            'weights': weights, 'discount': discount, 'alpha': alpha,
            'epochs': epochs, 'reward_contract': REWARD_CONTRACT,
            'training': {**_metrics(model, samples, backups), 'status': 'TRAINED' if rows else 'COLLECTING',
                         'unversioned_observations': sum(any(k not in r for k in contracts()) for r in samples),
                         'parameters_changed': initial != digest(weights),
                         'loss_first': losses[0], 'loss_last': losses[-1]},
            'support_actions': sorted({r['actions'][r['executed_index']]['action_type'] for r in samples})})


def evaluate(policy, samples):
    validate_contract(policy)
    errors = []; zero = []; supported = 0; backups = []
    for s in samples:
        try:
            index = s['executed_index']
            if (type(index) is not int or index not in _legal(s['features'], s['actions'], s['permitted'])
                    or not math.isfinite(s['reward'])):
                raise ValueError('Invalid current observation')
            value = score(policy, s['features'], s['actions'][index])
            if not math.isfinite(value):
                raise ValueError('Nonfinite current score')
        except (ValueError, TypeError, KeyError, IndexError, OverflowError):
            backups.append(dict(status='SKIP_INVALID_OBSERVATION', value=None, reason='invalid_current_observation'))
            continue
        backup = next_state_backup(support_model=policy, value_model=policy, transition=s)
        backups.append(backup)
        if backup['value'] is None:
            continue
        ticket = s['actions'][s['executed_index']]
        target = s['reward'] + policy['discount'] * backup['value']
        if not math.isfinite(target):
            backups[-1] = dict(status='SKIP_INVALID_TRANSITION', value=None, reason='nonfinite_target')
            continue
        errors.append((value - target) ** 2); zero.append(target ** 2)
        supported += s['executed_index'] in supported_action_indices(policy, s['features'], s['actions'], s['permitted'])['supported']
    return {**_metrics(policy, samples, backups), 'bellman_mse': sum(errors) / len(errors) if errors else None,
            'zero_prediction_same_target_mse': sum(zero) / len(zero) if zero else None,
            'logged_action_support': supported / len(errors) if errors else 0,
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
            if any(p.get(k) != v for k, v in contracts().items()):
                excluded['incompatible_support_backup_or_handler_contract'] += 1; continue
            if p.get('selection_mode')=='FORCED':
                excluded['forced_action']+=1; continue
            if not result or result['status']!='COMPLETED':
                excluded['missing_or_failed_result']+=1; continue
            if result.get('actual_microusd') is None:
                excluded['unsettled_usage']+=1; continue
            judgments=labels.get(did, [])
            if not judgments:
                excluded['unobserved_reward']+=1; continue
            td_exclusion = None
            if not transition:
                td_exclusion = 'open_optional_transition'
                transition = {}
            next_id=transition.get('next_decision_id')
            next_row=decisions.get(next_id)
            if next_id and (not next_row or next_row['payload']['semantic_episode_id']!=p['semantic_episode_id']
                            or next_row['created_at'] < d['created_at']):
                td_exclusion = 'cross_episode_or_future_transition'
                next_row = None
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
                next_actions=[a['ticket'] for a in nxt['actions']] if nxt else [],
                next_permitted=[i for i,a in enumerate(nxt['actions']) if a['allowed']] if nxt else [],
                next_rule_preferred=nxt.get('rule_preferred') if nxt else None,
                next_action_instance_ids=[a['ticket'].get('action_instance_id') for a in nxt['actions']] if nxt else [],
                next_selection_mode=nxt.get('selection_mode') if nxt else None,
                next_semantic_episode_id=nxt.get('semantic_episode_id') if nxt else None,
                next_contracts={k: nxt.get(k) for k in contracts()} if nxt else None,
                td_exclusion_reason=td_exclusion,
                terminal=next_id is None and bool(transition.get('terminal_reason')),terminal_reason=transition.get('terminal_reason'),
                reward=quality-cost,dimensions=dict(concept_or_observed_judgment=quality,normalized_cost=cost,
                    actual_microusd=result['actual_microusd']),reward_contract=REWARD_CONTRACT,
                maturity='TECHNICAL' if any(j['maturity']=='TECHNICAL' for j in judgments) else 'CONCEPT_PROXY',
                feature_schema=SCHEMA,review_ids=sorted({j['id'] for j in judgments}),behavior_probability=None,
                **contracts()))
    rows,limited=bounded_families(rows)
    excluded['cpu_batch_limit']+=limited
    families=sorted({r['group'] for r in rows},key=lambda g:max(r['available_at'] for r in rows if r['group']==g))
    # A single family cannot supply independent train and evaluation partitions.
    # Keep it as observation-only training data; readiness still requires holdout.
    holdout=set(families[-max(1,len(families)//4):]) if len(families) >= 2 else set()
    for row in rows:
        row['split']='holdout' if row['group'] in holdout else 'train'
    return dict(schema='ax-dataset-v3',feature_schema=SCHEMA,task_kind='routing_q',samples=rows,
                excluded=dict(excluded),cutoff=cutoff,synthetic=False,tenant_id=tenant,project_id=project, **contracts())


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
