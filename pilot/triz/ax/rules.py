"""Bounded declarative rule lab; generated text is never evaluated as code."""
import json
from collections import defaultdict
from sqlalchemy import select,update
from . import ledger,registry
from .contracts import RuleSpec,canonical,digest,Conflict


def validate(spec,state):
    rule=RuleSpec.model_validate(spec)
    catalog={e['id'] for g in state.scratch['ax_bundle']['effects'] for e in g['effects']}
    if set(rule.effect_ids)-catalog: raise ValueError('Rule references unknown effects')
    for vid in rule.source_versions:
        # Every source must belong to the same owner/project, not a guessed global ID.
        with ledger.store.engine.connect() as c:
            row=c.execute(select(ledger.artifacts.c.run_id).where(ledger.artifacts.c.version_id==vid)).scalar()
        if not row: raise ValueError('Rule source missing')
        source=ledger.head(row,state.user_id)
        current=ledger.head(state.run_id,state.user_id)
        if source['project_id']!=current['project_id']: raise ValueError('Rule source outside project')
    return rule


def patch(rule,domain,functions):
    """Return only additive obligations/suggestions. No arbitrary state mutation."""
    rule=RuleSpec.model_validate(rule)
    if domain!=rule.domain or not set(rule.required_functions)<=set(functions):
        return {'matched':False,'obligations':[],'suggestions':[]}
    value={'source_rule':digest(rule.model_dump(mode='json')),'provided_function':rule.provided_function,
           'applicability':rule.applicability,'status':'REQUIRES_VALIDATION'}
    return {'matched':True,
        'obligations':[dict(value,text=rule.obligation)] if rule.operation=='ADD_VERIFICATION' else [],
        'suggestions':[dict(value,operation=rule.operation,effect_ids=rule.effect_ids)] if rule.operation!='ADD_VERIFICATION' else []}


def apply(state):
    used=state.scratch.setdefault('ax_applied_rules',[])
    functions={a.get('catalog_function') for a in state.solve.effect_apps}
    protected=digest(state.constraints.model_dump(mode='json'))
    added=[]
    for stored in state.scratch['ax_bundle'].get('rule_catalog',[])[:12]:
        version=stored['version_id']
        if version in used: continue
        spec={k:v for k,v in stored.items() if k!='version_id'}
        rule=validate(spec,state)
        result=patch(spec,state.domain.problem_type,functions)
        if not result['matched']: continue
        for c in state.concepts:
            for obligation in result['obligations']:
                c.validation_plan.append({'metric':rule.provided_function,'experiment':obligation['text'],
                    'failure_criterion':'적용 조건 또는 보호 요구를 충족하지 못함','rule_version_id':version})
        used.append(version); added.append({'version_id':version,'patch':result})
    if digest(state.constraints.model_dump(mode='json'))!=protected:
        raise Conflict('Rule modified protected requirements')
    state.scratch['ax_rule_patches']=added
    return added


def research_project(tenant,project):
    """Observed applications seed verification rules; only cross-case checks deploy.

    This is deliberately restricted to ADD_VERIFICATION. A rule can require more
    verification but can never invent a passed test, modify a constraint or add a
    scientific effect to the editorial catalog.
    """
    groups=defaultdict(list)
    with ledger.store.engine.connect() as connection:
        heads=connection.execute(select(ledger.heads).where(ledger.heads.c.tenant_id==tenant,
            ledger.heads.c.project_id==project)).mappings().all()
    for h in heads:
        state=ledger.store.load_state(h['run_id'])
        if not state or state.scratch.get('acceptance_fixture'): continue
        reviews=[r for r in ledger.active_reviews(h['run_id'],h['owner_id'])
            if r['payload']['consent']=='PROJECT_ONLY' and r['payload']['decision_type'] in ('RECORD_TEST_RESULT','RECORD_FIELD_RESULT')
            and r['payload']['result']=='PASS']
        for r in reviews:
            # Only still-current candidate observations can seed deployable rules.
            if r['payload']['target_version_id']!=state.scratch.get('ax_members',{}).get('concepts'): continue
            candidate=state.concept(r['payload']['candidate_id'])
            if not candidate: continue
            refs={idea.source_ref for idea in state.solve.raw_ideas if idea.id in candidate.source_idea_ids and idea.track=='H_EFFECTS'}
            for app in state.solve.effect_apps:
                if app.get('ref') not in refs: continue
                if not app.get('source_effect_id') or not app.get('catalog_function') or not app.get('catalog_conditions'): continue
                key=(state.domain.problem_type,app['source_effect_id'],app['catalog_function'],str(app['catalog_conditions']))
                group=state.scratch.get('ax_problem_group') or digest(' '.join(state.raw_query.lower().split()))
                groups[key].append({'review_id':r['event_id'],'version':r['payload']['target_version_id'],
                    'problem_group':group,'run_id':h['run_id']})
    output=[]
    for (domain,effect,function,conditions),sources in groups.items():
        spec=RuleSpec(name=function+' 적용 조건 검증',domain=domain,required_functions=[function],
            provided_function=function,operation='ADD_VERIFICATION',effect_ids=[effect],
            obligation='해당 효과를 적용하기 전에 다음 조건을 시험으로 확인한다: '+conditions[:1100],
            applicability=conditions,source_versions=list(dict.fromkeys(x['version'] for x in sources))[:12]).model_dump(mode='json')
        positive=patch(spec,domain,[function]); negative=patch(spec,'UNKNOWN',[])
        checks={'additive_patch':positive['matched'] and bool(positive['obligations']),
            'negative_scope_rejected':not negative['matched'],
            'independent_problem_groups':len({x['problem_group'] for x in sources}),
            'field_performance_proven':False}
        payload={'rule':spec,'checks':checks,'review_ids':sorted({x['review_id'] for x in sources}),
                 'scope':'verification obligation only; no claim of generalized performance'}
        vid=registry.put('rule',tenant,project,payload)
        deploy=checks['additive_patch'] and checks['negative_scope_rejected'] and checks['independent_problem_groups']>=2
        if deploy:
            with ledger.transaction() as c:
                p=registry._pointer(c,tenant,project)
                if registry.reviews_current(payload,tenant,project,c):
                    old=json.loads(p['rule_ids'])
                    # A new revision supersedes the same function/effect operation.
                    kept=[v for v in old if registry.get(v,tenant,project,c)['payload']['rule']['effect_ids']!=[effect]]
                    ids=(kept+[vid])[-12:]
                    if ids!=old:
                        c.execute(update(registry.pointers).where(registry.pointers.c.scope==p['scope']).values(rule_ids=canonical(ids)))
                        registry._audit(c,tenant,project,{'action':'ADDITIVE_RULE_DEPLOYED','version_id':vid,'checks':checks})
        output.append({'version_id':vid,'status':'DEPLOYED_NEXT_RUN' if deploy else 'CANDIDATE','checks':checks})
    return output


def revoke(tenant,project,version_id,actor,reason):
    if not actor or not reason.strip(): raise ValueError('Revocation needs an actor and rationale')
    with ledger.transaction() as c:
        p=registry._pointer(c,tenant,project)
        ids=[v for v in json.loads(p['rule_ids']) if v!=version_id]
        c.execute(update(registry.pointers).where(registry.pointers.c.scope==p['scope']).values(rule_ids=canonical(ids)))
        registry._audit(c,tenant,project,{'action':'RULE_REVOKED','version_id':version_id,'actor':actor,'reason':reason})
