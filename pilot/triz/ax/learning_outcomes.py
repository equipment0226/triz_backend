"""Rebuild bounded outcomes and transitions from immutable, scoped observations."""
import json
from collections import Counter, defaultdict
from sqlalchemy import select, or_
from . import ledger, feedback_events, routing_q
from .contracts import digest, now

REWARD = 'candidate-utility-cost-v2'


def outcome(events, settings, active_candidates=None):
    """Pure, order-independent projection. Missing user answers remain masked."""
    groups = defaultdict(list)
    latest={}; completed=set(); designs={}
    for event in events:
        revision=event.get('review_revision',{})
        if event.get('evaluation_stage','').startswith('s6_') and revision:
            key=(event.get('run_id'),event.get('semantic_episode_id'),event['candidate_id'])
            latest[key]=max(latest.get(key,0),revision.get('revision',0))
            if event.get('dimension')=='coverage_quality': completed.add((key,revision.get('revision',0)))
            if key not in designs or revision.get('revision',0)>=designs[key][0]: designs[key]=(revision.get('revision',0),event.get('candidate_version'))
    for event in events:
        key=(event.get('run_id'),event.get('semantic_episode_id'),event['candidate_id'])
        if event['dimension'] in ('concept_quality','coverage_quality','constraint_quality','evaluation_quality') and key in latest:
            if event.get('review_revision',{}).get('revision',0)!=latest[key]: continue
            if (key,latest[key]) not in completed: continue
        if event['dimension']=='user_utility' and key in designs and event.get('candidate_version')!=designs[key][1]: continue
        if event.get('observed_mask') and event.get('observed_value') is not None:
            groups[event.get('mechanism_key') or event['candidate_version']].append(event)
    components = []
    for mechanism, rows in sorted(groups.items()):
        utilities = [r for r in rows if r['dimension']=='user_utility']
        final = [r for r in utilities if r['evaluation_stage']=='s10_feedback']
        user_by_candidate={}
        for row in sorted(final or utilities,key=lambda r:(r['label_available_at'],r['event_id'])):
            user_by_candidate[row['candidate_id']]=row
        utility_values=sorted({r['observed_value'] for r in user_by_candidate.values()})
        utility_value=sum(utility_values)/len(utility_values) if utility_values else None
        qualities = [r for r in rows if r['dimension'] in ('concept_quality','constraint_quality','evaluation_quality','coverage_quality','reported_test_result')]
        by_dimension = {}
        for row in sorted(qualities,key=lambda r:(r['label_available_at'],r['event_id'])):
            by_dimension[(row['dimension'],row['reviewer_type'],row['candidate_id'])] = row
        quality = min((r['observed_value'] for r in by_dimension.values()), default=None)
        if active_candidates is not None and not any(r['candidate_id'] in active_candidates for r in rows) and quality is not None:
            quality = min(0.,quality)
        components.append(dict(mechanism=mechanism, concept_quality=quality,
            user_utility=utility_value,
            masks=dict(concept_quality=quality is not None,user_utility=utility_value is not None),
            source_event_ids=sorted({r['event_id'] for r in by_dimension.values()} | {r['event_id'] for r in user_by_candidate.values()})))
    quality = [r['concept_quality'] for r in components if r['masks']['concept_quality']]
    utility = [r['user_utility'] for r in components if r['masks']['user_utility']]
    q = sum(quality)/len(quality) if quality else None
    u = sum(utility)/len(utility) if utility else None
    value = settings['quality_weight']*(q or 0)+settings['utility_weight']*(u or 0)
    return dict(contract=REWARD, components=components, concept_quality=q,user_utility=u,
        review_projection_contract='current-review-projection-v2' if latest else 'legacy-review-projection-v1',
        masks=dict(concept_quality=q is not None,user_utility=u is not None), total=max(-1.,min(1.,value)),
        aggregation='mean-over-unique-recorded-mechanisms-v1',weights=settings,
        source_event_ids=sorted({eid for row in components for eid in row['source_event_ids']}),
        maturity='USER_BACKED' if utility else 'USER_REPORTED_TEST' if any(r['dimension']=='reported_test_result' for r in events) else 'MODEL_REVIEW_PROXY' if quality else 'UNOBSERVED')


def _split(rows):
    rows, limited = routing_q.bounded_families(rows)
    groups = sorted({r['group'] for r in rows},key=lambda g:(max(r['available_at'] for r in rows if r['group']==g),g))
    holdout = set(groups[-max(1,len(groups)//4):]) if len(groups)>1 else set()
    for row in rows: row['split'] = 'holdout' if row['group'] in holdout else 'train'
    return rows, limited


def q_dataset(tenant, project, cutoff=None, *, include_synthetic=False, schema=routing_q.CONFIRMED_SCHEMA):
    cutoff = cutoff or now()
    labels = feedback_events.current(tenant,project,cutoff,include_synthetic=include_synthetic)
    samples, excluded = [], Counter()
    with ledger.store.engine.connect() as c:
        heads = c.execute(select(ledger.heads).where(ledger.heads.c.tenant_id==tenant,ledger.heads.c.project_id==project)).mappings().all()
    for head in heads:
        bundle = json.loads(head['bundle'])
        if bundle.get('feature_schema')!=schema: continue
        with ledger.store.engine.connect() as c:
            stream = [dict(r,payload=json.loads(r['payload'])) for r in c.execute(select(ledger.events).where(
                ledger.events.c.run_id==head['run_id'],ledger.events.c.created_at<=cutoff)).mappings()]
            tasks = [dict(r) for r in c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==head['run_id'],ledger.tasks.c.created_at<=cutoff)).mappings()]
            task_episodes={r.task_id:json.loads(r.details).get('request',{}).get('request',{}).get('semantic_episode_id')
                for r in c.execute(select(ledger.attempts.c.task_id,ledger.attempts.c.details).where(ledger.attempts.c.run_id==head['run_id']))}
        decisions = [d for d in ledger.decision_history(head['run_id'],head['owner_id']) if d['created_at']<=cutoff and d['payload'].get('feature_schema')==schema]
        episodes = defaultdict(list)
        for d in decisions: episodes[d['payload']['semantic_episode_id']].append(d)
        results = {e['payload']['action_instance_id']:e['payload'] for e in stream if e['event_type']=='ACTION_INSTANCE_RESULT'}
        endings = {e['payload']['semantic_episode_id']:e for e in stream if e['event_type']=='ADAPTIVE_EPISODE_CLOSED'}
        for episode, ds in episodes.items():
            events = [r for r in labels if r['run_id']==head['run_id'] and r['semantic_episode_id']==episode]
            excluded['unknown_attribution']+=sum(r.get('attribution')=='UNKNOWN_ATTRIBUTION' for r in events)
            events=[r for r in events if r.get('attribution')!='UNKNOWN_ATTRIBUTION']
            if not events:
                excluded['no_consented_observation']+=1; continue
            if episode not in endings:
                excluded['open_episode']+=1; continue
            end = endings[episode]
            eligible_tasks = tasks  # Partition below by immutable task creation time; each task appears once.
            # Later semantic episodes have their own begin boundary and cannot consume old costs.
            ds.sort(key=lambda d:(d['payload']['decision_sequence'],d['created_at'],d['decision_id']))
            other_starts = [min(x['created_at'] for x in other) for key,other in episodes.items() if key!=episode]
            next_start = min((t for t in other_starts if t>ds[0]['created_at']),default=None)
            previous_start = max((t for t in other_starts if t<ds[0]['created_at']),default=None)
            if next_start: eligible_tasks = [t for t in eligible_tasks if t['created_at']<next_start]
            if previous_start: eligible_tasks = [t for t in eligible_tasks if t['created_at']>=ds[0]['created_at']]
            if task_episodes:
                if any(task_episodes.get(t['task_id']) is None for t in eligible_tasks):
                    excluded['missing_usage_episode']+=1;continue
                eligible_tasks=[t for t in tasks if task_episodes.get(t['task_id'])==episode]
            if any(t['actual'] is None or not t['settled_at'] or t['settled_at']>cutoff for t in eligible_tasks):
                excluded['unsettled_usage']+=1; continue
            summary = outcome(events,bundle['run_contract']['feedback_settings'],end['payload']['candidate_ids'])
            if summary['maturity']=='UNOBSERVED':
                excluded['unobserved_reward']+=1; continue
            if any(not results.get(d['payload']['executed_action_instance']) or results[d['payload']['executed_action_instance']]['status']!='COMPLETED' for d in ds):
                excluded['missing_or_failed_action_result']+=1; continue
            revision = digest([summary,[(t['task_id'],t['actual']) for t in sorted(eligible_tasks,key=lambda t:t['task_id'])]])
            for i,d in enumerate(ds):
                p=d['payload']; nxt=ds[i+1]['payload'] if i+1<len(ds) else None
                next_time=ds[i+1]['created_at'] if nxt else None
                costs = [t for t in eligible_tasks if (i==0 or t['created_at']>=d['created_at']) and (next_time is None or t['created_at']<next_time)]
                actual = sum(t['actual'] for t in costs)
                penalty = bundle['run_contract']['feedback_settings']['lambda_cost']*actual/max(1,head['budget'])
                terminal = nxt is None
                tickets=[a['ticket'] for a in p['actions']]
                samples.append(dict(run_id=head['run_id'],decision_id=d['decision_id'],semantic_episode_id=episode,
                    features=p['features'],actions=tickets,permitted=p['permitted_actions'],executed_index=p['executed_index'],
                    action=routing_q.support_key(tickets[p['executed_index']]),
                    next_features=nxt['features'] if nxt else p['features'],next_actions=[a['ticket'] for a in nxt['actions']] if nxt else [],
                    next_permitted=nxt['permitted_actions'] if nxt else [],next_rule_preferred=nxt.get('rule_preferred') if nxt else None,
                    next_semantic_episode_id=episode,next_contracts=routing_q.contracts(schema),
                    terminal=terminal,terminal_reason='MANDATORY_REVIEW_AND_REPORT_COMPLETED' if terminal else None,
                    reward=-penalty+(summary['total'] if terminal else 0), reward_revision=revision,
                    dimensions=dict(normalized_cost=penalty,actual_microusd=actual,task_ids=sorted(t['task_id'] for t in costs),terminal_outcome=summary if terminal else None),
                    feature_schema=schema, group=events[0]['problem_family'],maturity=summary['maturity'],
                    available_at=max([end['created_at']]+[r['label_available_at'] for r in events]+[t['settled_at'] for t in costs]),
                    review_ids=summary['source_event_ids'],behavior_probability=None,selection_mode=p['selection_mode'],
                    synthetic=any(r.get('synthetic') for r in events),
                    **routing_q.contracts(schema)))
    samples,limited=_split(samples);excluded['cpu_batch_limit']+=limited
    return dict(schema='ax-dataset-v4',feature_schema=schema,task_kind='routing_q',samples=samples,
        synthetic=include_synthetic,excluded=dict(excluded),cutoff=cutoff,tenant_id=tenant,project_id=project)


def effect_dataset(tenant, project, cutoff=None, *, include_synthetic=False):
    from . import effect_history, effect_ranker
    cutoff=cutoff or now();excluded=Counter();samples=[]
    labels=feedback_events.current(tenant,project,cutoff,include_synthetic=include_synthetic)
    with ledger.store.engine.connect() as c:
        apps={r['application_id']:json.loads(r['payload']) for r in c.execute(select(effect_history.applications).where(
            effect_history.applications.c.tenant_id==tenant,effect_history.applications.c.project_id==project)).mappings()}
        selections={}
        for r in c.execute(select(effect_history.selections).where(effect_history.selections.c.created_at<=cutoff)).mappings():
            selections.setdefault(r['run_id'],[]).append(dict(json.loads(r['payload']),created_at=r['created_at'],selection_id=r['selection_id']))
    grouped=defaultdict(list)
    for r in labels: grouped[(r['run_id'],r['semantic_episode_id'],r.get('mechanism_key') or r['candidate_version'])].append(r)
    for _, rows in sorted(grouped.items()):
        row=max(rows,key=lambda r:(r['label_available_at'],r['event_id']))
        observed=[r for r in rows if r['observed_mask']]
        if not observed: excluded['unobserved']+=1;continue
        if row['attribution']=='UNKNOWN_ATTRIBUTION':
            excluded['unknown_attribution']+=1;continue
        head=ledger.head(row['run_id'])
        settings=head['bundle']['run_contract']['feedback_settings']
        summary=outcome(rows,settings)
        if not any(summary['masks'].values()):
            excluded['no_current_observed_revision']+=1;continue
        with ledger.store.engine.connect() as c:
            unsettled=c.execute(select(ledger.tasks.c.task_id).where(ledger.tasks.c.run_id==row['run_id'],
                ledger.tasks.c.created_at<=cutoff, or_(ledger.tasks.c.actual.is_(None),
                ledger.tasks.c.settled_at.is_(None), ledger.tasks.c.settled_at>cutoff))).first()
        if unsettled: excluded['unsettled_usage']+=1;continue
        active={apps[aid]['effect_id']:apps[aid] for aid in row['active_effect_application_ids'] if aid in apps}
        for effect,app in sorted(active.items()):
            pre=[s for s in selections.get(row['run_id'],[]) if effect in s.get('exposed_ids',[])
                and s['created_at']<=row['created_at'] and s.get('feature_snapshot')
                and s.get('semantic_episode_id')==row['semantic_episode_id']
                and s.get('catalog_version')==app['catalog_version']
                and s.get('source_action_instance_id') in app.get('action_instance_ids',[])]
            if not pre: excluded['missing_selection_time_features']+=1;continue
            selected=min(pre,key=lambda s:(s['created_at'],s['selection_id']))
            context=selected['feature_snapshot'];definition=selected['catalog_definitions'].get(effect)
            if not definition: excluded['missing_catalog_definition']+=1;continue
            samples.append(dict(feature_schema='effect-application-utility-v2',features=effect_ranker.features(context,definition),
                context=context,application=definition,effect_id=effect,label=summary['total'],dimension='candidate_application_utility',
                sample_weight=1/max(1,len(active)),group=row['problem_family'],run_id=row['run_id'],available_at=row['label_available_at'],
                review_ids=summary['source_event_ids'],selection_id=selected['selection_id'],application_id=app['application_id'],
                synthetic=any(r.get('synthetic') for r in rows),
                maturity=summary['maturity'],outcome=summary,attribution='SHARED_CANDIDATE_PROXY_NOT_INDIVIDUAL_PROOF'))
    samples,limited=_split(samples);excluded['cpu_batch_limit']+=limited
    return dict(schema='effect-application-utility-v2',task_kind='effect_ranker',samples=samples,excluded=dict(excluded),
                cutoff=cutoff,synthetic=include_synthetic,tenant_id=tenant,project_id=project)
