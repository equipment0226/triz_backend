"""Case-local evidence for runtime rules; missing evidence is not a PASS."""
import base64,hashlib,json
from sqlalchemy import select
from .domain import digest,ROLES,PROFILE
from .repository import tasks,TABLES,assets
from .sql_guard import verified


def collect(service,owner,case,material,conn):
    records=service.repo.records(owner,case['case_id'],conn=conn)
    by_kind={}
    for record in records:
        by_kind.setdefault(record['kind'],[]).append(record)
    task_rows={r['task_id']:dict(r) for r in conn.execute(select(tasks).where(tasks.c.case_id==case['case_id'])).mappings()}
    bodies={tid:json.loads(row['body']) for tid,row in task_rows.items()}
    executed=[(task_rows[tid],b) for tid,b in bodies.items() if task_rows[tid]['fence']>0]
    guards={r['task_id']:r for r in by_kind.get('execution_guard',[])}
    fences=(all(t['task_id'] in guards and guards[t['task_id']]['ticket_hash']==digest(b['ticket'])
                and guards[t['task_id']]['fence']<=t['fence'] for t,b in executed) if executed else None)
    reviews=service.current_reviews(owner,case,conn)
    def reviewed(r):
        task=task_rows.get(r.get('task_id'));body=bodies.get(r.get('task_id'),{})
        ticket=body.get('ticket',{})
        return bool(task and task['status']=='COMPLETED' and ticket.get('tier')=='T3'
            and ticket.get('review_role')==r['role'] and ticket.get('epoch')==case['epoch']
            and set(ticket['read_version_ids'])==set(r['covered_artifact_ids'])
            and r.get('model_config_hash')==digest(case['model_config']))
    covered={r['role'] for r in reviews if reviewed(r)}
    enrichment=[b['ticket'] for b in bodies.values() if b['ticket']['tool_name']=='patent_enrich_sources']
    targeted=[]
    for ticket in enrichment:
        p=service.repo.record(owner,case['case_id'],ticket['operation_payload_ref'],conn)
        targeted.append(bool(p.get('issue_id') and p.get('missing_fields') and p.get('authorized_api_calls')==1))
    artifacts={r['id']:r for r in by_kind.get('artifact',[])}
    integrity=all(v in artifacts and artifacts[v]['artifact_type']==kind and
        artifacts[v]['content_hash']==digest(material[kind]) for kind,v in case['artifacts'].items())
    patches=by_kind.get('patch_applied',[])
    patch_valid=all(any(p['after_version_id']==a['id'] and p['actor']==owner and
        p['before_version_id'] in a['parent_version_ids'] and p['before_version_id'] in artifacts
        and artifacts[p['before_version_id']]['content_hash']==p['before_hash'] for p in patches)
        for a in artifacts.values() if a.get('producer')=='OWNER_APPROVED_PATCH')
    detail=material.get('source_detail',{}).get('documents',{})
    parse=None
    from .sources import public_document
    public_values=[*detail.values(),*material.get('sources',{}).get('cached_details',[])]
    cache_scope=True
    try:
        for value in public_values:
            public_document({k:v for k,v in value.items() if k!='reused_cache'})
    except Exception:
        cache_scope=False
    if detail:
        parse=cache_scope
    provider=[r for r in by_kind.get('provider_receipt',[]) if r.get('boundary_contract')]
    all_provider=[b for _,b in executed if b['ticket']['tier']!='CODE']
    boundary=(all(any(r['task_id']==b['ticket']['task_id'] and r['boundary_contract'].get('version')=='patent-untrusted-data-v1'
                     and r['boundary_contract'].get('tools_enabled') is False for r in provider)
                  for b in all_provider) if all_provider else None)
    from .coverage import delivery_scope,targets,validate
    scope=delivery_scope(case,material)
    delivery=any(r.get('scope')==scope and r.get('content_manifest_hash')==digest(scope)
                 for r in by_kind.get('delivery_scope',[]))
    for review in reviews:
        if review['role']=='GLOBAL_FINAL':
            try:
                validate(review.get('target_checks',[]),targets(material,{k:v for k,v in case['artifacts'].items() if v in service.readset(case,'GLOBAL_FINAL')}))
            except Exception:
                covered.discard('GLOBAL_FINAL')
    export_valid=True
    for record in by_kind.get('export',[]):
        manifest=record['manifest']
        row=conn.execute(select(assets.c.sha256,assets.c.content).where(assets.c.case_id==case['case_id'],assets.c.asset_id==record['asset_id'])).first()
        if not row or hashlib.sha256(row.content).hexdigest()!=row.sha256 or manifest.get('manifest_hash')!=digest({k:v for k,v in manifest.items() if k!='manifest_hash'}):
            export_valid=False
    from .learning import govern_operation
    decisions={r['task_id']:r for r in by_kind.get('governor_decision',[])}
    mask=all(tid in decisions and decisions[tid]['ticket_hash']==digest(body['ticket'])
        and decisions[tid]['policy_version']==case['policy_version'] and all(
            decisions[tid].get(k)==v for k,v in govern_operation(body['ticket']['tool_name']).items())
        for tid,body in bodies.items()) if bodies else None
    feedback=by_kind.get('feedback',[])
    maturity=all(r.get('reward') is None and r.get('behavior_probability') is None and
        r.get('namespace')=='patent_draft' and r.get('owner_id')==owner and r.get('training_eligible') is False
        and r.get('maturity')=='USER_SUBMITTED_UNVERIFIED' for r in feedback)
    maturity=maturity and len({r['dedupe_key'] for r in feedback})==len(feedback)
    return {'acl_verified':case['owner_id']==owner and all(r.get('owner_id',owner)==owner for r in records),
        'untrusted_context_enforced':boundary,
        'public_cache_isolated':cache_scope,'economics_internal_only':None if 'economics' not in material else
            not any(k in material.get('specification',{}) for k in ('economics','valuation','fto')),
        'export_manifest_bound':delivery and export_valid,
        'targeted_enrichment_only':all(targeted),'ticket_fence_verified':fences,
        'review_conflicts_preserved':all(r in reviews for r in by_kind.get('review',[]) if
            r['epoch']==case['epoch'] and set(r['covered_artifact_ids'])==set(service.readset(case,r['role'])) and r.get('model_profile')==PROFILE),
        'readset_invalidation':integrity,
        'legacy_readonly':verified(service.legacy.engine) and verified(service.repo.engine,TABLES),
        'dispatch_flag_checked':all(g.get('dispatch_enabled') is True for g in guards.values()) if guards else None,
        'mcp_contracts_registered':registered_tools(),
        'safe_action_mask':mask,'feedback_maturity':maturity,
        'patch_provenance':patch_valid,'approvals':service.approvals(owner,case,conn),
        'independent_reviews':set(ROLES[:2])<=covered,
        'global_coverage':'GLOBAL_FINAL' in covered,
        'schema_preservation_verified':case.get('legacy_schema_hash')==service.legacy.schema_fingerprint(),
        'source_parse_verified':parse}


def registered_tools():
    from .mcp import mcp
    from .service import OPERATIONS
    try:
        registered={t.name:t for t in mcp._tool_manager.list_tools()}
        if set(registered)!=set(OPERATIONS)|{'patent_open_case','patent_get_context'}:
            return False
        return all('ticket' in registered[name].parameters.get('required',[]) for name in OPERATIONS)
    except (AttributeError,TypeError):
        return None
