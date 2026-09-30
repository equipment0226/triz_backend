"""Estimate completed producer executions from unique settled ledger tasks."""
import json
from collections import Counter
from sqlalchemy import select
from . import ledger
from .contracts import digest, now

CONTRACT='track-execution-cost-v2'
MAX_RUNS=64
MAX_ROWS=10000


def comparison(state):
    from .confirmed_context import build
    from ..model_pricing import resolve
    bundle=state.scratch['ax_bundle']
    size=len(json.dumps(build(state)['tokens'],ensure_ascii=False).encode('utf-8'))+len(state.raw_query.encode('utf-8'))
    return dict(contract=CONTRACT,models=digest(bundle['models']),prompts=digest(bundle['prompts']),
        pricing=digest({tier:resolve(config) for tier,config in bundle['models'].items()}),
        node_contract=digest({k:v for k,v in bundle.get('source_hashes',{}).items() if k.endswith(('nodes.py','agent.py','gateway.py'))}),
        input_size_bucket=max(0,size.bit_length()-1),input_size_kind='utf8_bytes_proxy')


def prior(state,track):
    from .. import nodes
    bundle=state.scratch['ax_bundle']; cfg=bundle['config']; models=bundle['models']
    count={'A_MATRIX':len(nodes._pick_tcs(state)), 'B_SEPARATION':len(nodes._pick_pcs(state)),
           'C_STANDARDS':min(2,len(state.analysis.su_fields))}.get(track,1)
    count=max(1,count)
    cap=max(models['T2']['max_tokens'],int(cfg.get('solutions',{}).get('track_max_tokens',8000)))
    if track=='A_MATRIX': cap=max(4000,int(cfg.get('solutions',{}).get('track_a_max_tokens',8000)))
    attempts=max(1,int(cfg.get('ax',{}).get('max_provider_attempts',2)))
    revisions=1+max(0,int(cfg.get('verification',{}).get('max_repair_attempts',2)))
    size=len(state.raw_query.encode('utf-8'))+len(json.dumps(state.constraints.model_dump(mode='json'),ensure_ascii=False).encode('utf-8'))+16000
    plan=[dict(node='s5_track_'+track[0].lower(),tier='T2',calls=count,max_tokens=cap)]
    if track=='A_MATRIX': plan.append(dict(node='s5_matrix_select',tier='T2',calls=count,max_tokens=max(models['T2']['max_tokens'],int(cfg.get('solutions',{}).get('track_max_tokens',8000)))))
    if track in ('A_MATRIX','B_SEPARATION','C_STANDARDS'):
        plan.append(dict(node='independent_verifier',tier='T3',calls=count,max_tokens=int(cfg.get('verification',{}).get('max_tokens',models['T3']['max_tokens']))))
    for p in plan: p.update(provider_attempt_cap=attempts,agent_revision_cap=revisions)
    from ..model_pricing import reserve_microusd
    total=sum(reserve_microusd(models[p['tier']],size,p['max_tokens'],attempts)*p['calls']*revisions for p in plan)
    return total,plan


def observations(state,cutoff=None):
    cutoff=cutoff or now(); expected=comparison(state); excluded=Counter(); samples=[]
    with ledger.store.engine.connect() as c:
        heads=c.execute(select(ledger.heads).where(ledger.heads.c.owner_id==state.user_id,
            ledger.heads.c.project_id==state.scratch.get('ax_project_id',state.user_id))
            .order_by(ledger.heads.c.run_id).limit(MAX_RUNS)).mappings().all()
        for head in heads:
            saved=ledger.store.load_state(head['run_id'])
            if not saved or saved.scratch.get('training_consent')!='PROJECT_ONLY' or saved.scratch.get('synthetic') or saved.scratch.get('acceptance_fixture'):
                excluded['scope_or_synthetic']+=1;continue
            consent_rows=c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id==head['run_id'],
                ledger.events.c.event_type=='COMMON_EVALUATION').limit(MAX_ROWS+1)).scalars().all()
            if len(consent_rows)>MAX_ROWS or any(json.loads(r).get('training_consent_scope')=='NO_TRAINING' for r in consent_rows):
                excluded['withdrawn_or_unconsented_observations']+=1;continue
            events=c.execute(select(ledger.events).where(ledger.events.c.run_id==head['run_id'],
                ledger.events.c.event_type=='ACTION_INSTANCE_RESULT',ledger.events.c.created_at<=cutoff).limit(MAX_ROWS+1)).mappings().all()
            tasks=c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==head['run_id']).limit(MAX_ROWS+1)).mappings().all()
            attempts=c.execute(select(ledger.attempts).where(ledger.attempts.c.run_id==head['run_id']).limit(MAX_ROWS+1)).mappings().all()
            if any(len(rows)>MAX_ROWS for rows in (events,tasks,attempts)):
                excluded['bounded_query_overflow']+=1;continue
            results={}
            for event in sorted(events,key=lambda e:(e['created_at'],e['event_id'])):
                row=json.loads(event['payload']);results[row['action_instance_id']]=row
            requests={}
            for attempt in attempts:
                request=json.loads(attempt['details']).get('request',{})
                if isinstance(request,dict): requests.setdefault(attempt['task_id'],[]).append(request)
            for aid,row in results.items():
                ticket=row.get('ticket',{}); tracks=ticket.get('parameters',{}).get('tracks',[])
                if ticket.get('action_type') not in ('GENERATE_BASELINE','RUN_TRACK') or len(tracks)!=1: continue
                parent=results.get(row.get('parent_action_instance_id'))
                if parent and parent.get('ticket',{}).get('action_type') in ('GENERATE_BASELINE','RUN_TRACK') and parent['ticket'].get('parameters',{}).get('tracks')==tracks:
                    continue  # The logical single-track parent owns the entire subtree.
                if row.get('cost_comparison')!=expected:
                    excluded['unknown_or_different_comparison']+=1;continue
                if row.get('status')!='COMPLETED' or (row.get('parent_action_instance_id') and (not parent or parent.get('status')!='COMPLETED')):
                    excluded['partial_execution']+=1;continue
                owned={aid}; changed=True
                while changed:
                    newer={k for k,v in results.items() if v.get('parent_action_instance_id') in owned}-owned
                    owned.update(newer);changed=bool(newer)
                if any(results[k].get('status')!='COMPLETED' or any(s['status']=='FAILED' for s in results[k].get('producer_step_statuses',[])) for k in owned):
                    excluded['partial_execution']+=1;continue
                selected=[]; mismatch=False
                if any('task_ids' not in results[k] for k in owned):
                    excluded['unknown_task_lineage']+=1;continue
                for task in tasks:
                    refs=requests.get(task['task_id'],[])
                    matched=[r for r in refs if r.get('action_context',{}).get('action_instance_id') in owned]
                    if not matched: continue
                    if any(r.get('action_context',{}).get('semantic_episode_id')!=row['semantic_episode_id'] for r in matched): mismatch=True
                    # The physical task already includes all provider retries; never sum its attempt rows too.
                    selected.append(task)
                if {t['task_id'] for t in selected}!={tid for k in owned for tid in results[k]['task_ids']}:
                    excluded['unknown_task_lineage']+=1;continue
                if mismatch or any(t['actual'] is None or not t['settled_at'] or t['settled_at']>cutoff or t['status'] not in ('COMPLETED','FAILED','RECONCILED') for t in selected):
                    excluded['unsettled_or_unknown_lineage']+=1;continue
                if not selected or sum(t['actual'] for t in selected)==0:
                    excluded['cache_only_or_no_paid_usage']+=1;continue
                samples.append(dict(logical_track_execution_id=aid,run_id=head['run_id'],semantic_episode_id=row['semantic_episode_id'],
                    track=tracks[0],plan_class=row.get('plan_class'),action_instance_ids=sorted(owned),
                    task_ids=sorted(t['task_id'] for t in selected),actual_producer_cost=sum(t['actual'] for t in selected),
                    actual_followup_cost_if_attributable=None,completed_at=row['completed_at'],
                    all_settled_at=max(t['settled_at'] for t in selected),settlement_status='SETTLED',cache_reuse_class='PAID_GENERATION',comparison=expected))
    return dict(samples=samples,excluded=dict(excluded),cutoff=cutoff,comparison=expected)


def estimate(state,track,history=None):
    history=history if history is not None else observations(state)
    rows=[r for r in history['samples'] if r['track']==track]
    values=sorted(r['actual_producer_cost'] for r in rows)
    fallback,plan=prior(state,track)
    return dict(estimated=True,cost_contract=CONTRACT,prior_microusd=fallback,
        estimate_microusd=values[len(values)//2] if values else fallback,reservation_microusd=max([fallback]+values),
        support=len(rows),sample_ids=[r['logical_track_execution_id'] for r in rows],samples=rows,
        cutoff=history['cutoff'],comparison=history['comparison'],excluded=history['excluded'],
        input_size_kind='utf8_bytes_proxy',planned_calls=plan,shared_merge_and_review='separate_existing_reserve',
        basis='median-completed-track-total' if rows else 'pinned-node-price-cap-prior')
