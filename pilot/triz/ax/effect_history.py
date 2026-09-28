"""Scoped immutable effect applications, reviews and selection observations.

Accept/drop is adoption only. A condition statement is USER_REPORTED, never a
physical test. Exact structured context matching deliberately favors abstention.
"""
import copy
import json
import re
import unicodedata
from collections import defaultdict
from sqlalchemy import Column, String, select
from . import ledger
from .contracts import canonical, digest, now, Conflict
from .mode_contract import contract
from .action_runtime import episode

applications = ledger.table('effect_applications', Column('application_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('tenant_id', String(64), nullable=False),
    Column('project_id', String(64), nullable=False), Column('payload', ledger.JSON, nullable=False),
    Column('created_at', String(40), nullable=False))
reviews = ledger.table('effect_reviews', Column('event_id', String(100), primary_key=True),
    Column('application_id', String(80), nullable=False), Column('run_id', String(64), nullable=False),
    Column('payload', ledger.JSON, nullable=False), Column('created_at', String(40), nullable=False))
selections = ledger.table('effect_selections', Column('selection_id', String(80), primary_key=True),
    Column('run_id', String(64), nullable=False), Column('payload', ledger.JSON, nullable=False),
    Column('created_at', String(40), nullable=False))


def norm(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).casefold().split())


def quantity(value, unit):
    """Only unambiguous scalar units convert; ranges and prose remain literal."""
    units = {'kw': (1000, 0, 'W'), 'w': (1, 0, 'W'), 'mm': (.001, 0, 'm'),
             'cm': (.01, 0, 'm'), 'm': (1, 0, 'm'), 'k': (1, -273.15, 'C'),
             '°c': (1, 0, 'C'), 'c': (1, 0, 'C'), '℃': (1, 0, 'C')}
    if norm(unit) in units and re.fullmatch(r'[-+]?\d+(\.\d+)?', str(value).strip()):
        scale, offset, canonical_unit = units[norm(unit)]
        return [round(float(value) * scale + offset, 8), canonical_unit]
    return [norm(value), norm(unit)]


def structured_context(state, required=()):
    if not required:
        from ..nodes import _required_functions
        required = _required_functions(state)
    constraints = sorted([dict(kind=c.kind, parameter=norm(c.parameter), statement=norm(c.statement),
        operator=c.operator, quantity=quantity(c.value, c.unit), hard=c.hard, zone=norm(c.zone))
        for c in state.constraints.items], key=canonical)
    return {'version':'effect-context-v1', 'normalization':'nfkc-scalar-units-v1',
        'domain':state.domain.problem_type,
        'functions':sorted(set(norm(x) for x in required if x)),
        'contradictions':sorted([[norm(c.if_action), norm(c.then_good), norm(c.but_bad), norm(c.coupling_mechanism)]
                                for c in state.definition.technical_contradictions]),
        'physical_contradictions':sorted([[norm(c.element), norm(c.parameter), norm(c.state_a), norm(c.state_b)]
                                         for c in state.definition.physical_contradictions]),
        'interactions':sorted([[norm(f.subject), norm(f.action), norm(f.object), f.kind] for f in state.analysis.function_edges]),
        'resources':sorted([[r.category, norm(r.name), norm(r.quantity_note), r.blocked_by_constraint] for r in state.analysis.resources]),
        'constraints':constraints}


def _catalog(state):
    return {e['id']: e for g in state.scratch['ax_bundle']['effects'] for e in g['effects']}


def collect(state):
    if not contract(state):
        return []
    catalog = _catalog(state)
    from .source_lineage import trace
    raw = trace(state)['records']
    candidate_sources = {candidate.id: trace(state, candidate.source_idea_ids)
                         for candidate in state.concepts}
    # H's structured output is also retained before any raw idea has been merged.
    for index, app in enumerate(state.solve.effect_apps):
        if not any(row.get('source_effect_id') == app.get('source_effect_id') and
                   row.get('idea') == app.get('idea') for row in raw.values()):
            raw['effect-app-' + str(index)] = dict(app, source_track='H_EFFECTS')
    output = []
    ctx = structured_context(state)
    family = state.scratch.get('ax_problem_group') or digest(ctx)
    h = ledger.head(state.run_id, state.user_id)
    catalog_version = digest(state.scratch['ax_bundle']['effects'])
    for raw_id, row in raw.items():
        detail = dict(row.get('detail') or {}, **{k:v for k,v in row.items() if k != 'detail'})
        effect_id = detail.get('source_effect_id')
        if not effect_id and not detail.get('effect_name') and not detail.get('catalog_evidence_level'):
            continue
        valid = effect_id in catalog
        effect = catalog.get(effect_id, {})
        conditions = detail.get('conditions') or detail.get('catalog_conditions') or effect.get('conditions') or []
        if isinstance(conditions, str):
            conditions = [conditions]
        linked = []
        for candidate in state.concepts:
            sources = candidate_sources[candidate.id]
            if sources['complete'] and raw_id in sources['leaves']:
                linked.append(candidate)
        for candidate in linked or [None]:
            candidate_version = digest(candidate.model_dump(mode='json')) if candidate else None
            value = dict(contract='effect-application-v1', owner_id=state.user_id,
                tenant_id=h['tenant_id'], project_id=h['project_id'], run_id=state.run_id,
                semantic_episode_id=episode(state), effect_id=effect_id if valid else None,
                proposed_effect_id=effect_id or detail.get('proposed_effect_id'), catalog_status='BOUND' if valid else 'OUTSIDE_CATALOG_HYPOTHESIS',
                catalog_version=catalog_version,
                source_version=digest(state.scratch['ax_bundle']['effect_sources'].get(effect_id, {})),
                mechanism_key=detail.get('catalog_mechanism_key') or effect.get('mechanism_key', ''),
                intended_function=detail.get('catalog_function') or effect.get('function_ko', ''),
                applied_mechanism=detail.get('idea') or detail.get('principle', ''),
                source_track=detail.get('source_track') or detail.get('track', 'UNKNOWN'),
                source_step=detail.get('source_step'), source_raw_idea_ids=[raw_id],
                structured_context=ctx, problem_signature=digest(ctx), problem_family=family,
                candidate_id=candidate.id if candidate else None, candidate_version=candidate_version,
                candidate_snapshot=candidate.model_dump(mode='json') if candidate else None,
                conditions=[dict(condition_id='condition-' + digest([raw_id, text])[:24], text=str(text),
                                 status='UNKNOWN', value=None, unit=None) for text in conditions],
                action_instance_ids=sorted(aid for aid, result in state.scratch.get('ax_action_results', {}).items()
                    if raw_id in result.get('produced_raw_idea_ids', []) or
                    (candidate and candidate.id in result.get('candidate_ids', []))),
                evidence_level='GENERATED_APPLICATION_NOT_TESTED')
            aid = 'eapp-' + digest([state.run_id, episode(state), raw_id, effect_id, candidate_version])[:56]
            value['application_id'] = aid
            output.append(value)
    with ledger.transaction() as c:
        current = ledger._head(c, state.run_id, lock=True)
        if current['epoch'] != state.scratch.get('execution_epoch', 0):
            raise Conflict('Effect application input is stale')
        for value in output:
            aid = value['application_id']
            if not c.execute(select(applications.c.application_id).where(applications.c.application_id == aid)).first():
                c.execute(applications.insert().values(application_id=aid, run_id=state.run_id,
                    tenant_id=h['tenant_id'], project_id=h['project_id'], payload=canonical(value), created_at=now()))
    state.scratch['ax_effect_applications'] = output
    return output


def _write_review(c, state, app, payload):
    value = dict(payload, application_id=app['application_id'], candidate_version=app['candidate_version'],
                 semantic_episode_id=app['semantic_episode_id'])
    identity = {k:v for k,v in value.items() if k != 'label_available_at'}
    eid = value.get('event_id') or 'erev-' + digest([state.run_id, identity])[:56]
    value['event_id'] = eid
    old = c.execute(select(reviews).where(reviews.c.event_id == eid)).mappings().first()
    if old:
        stored = json.loads(old['payload'])
        if old['run_id'] != state.run_id or {k:v for k,v in stored.items() if k != 'label_available_at'} != {k:v for k,v in value.items() if k != 'label_available_at'}:
            raise Conflict('Effect review event identity conflict')
        return eid
    c.execute(reviews.insert().values(event_id=eid, application_id=app['application_id'], run_id=state.run_id,
                                      payload=canonical(value), created_at=now()))
    ledger._event(c, state.run_id, 'EFFECT_REVIEW_CONFIRMED', {'review_id':eid})
    return eid


def gate_reviews(state, gate):
    apps = collect(state)
    if not apps:
        return
    per_candidate = defaultdict(set)
    for app in apps:
        per_candidate[app['candidate_id']].add(app['effect_id'])
    with ledger.transaction() as c:
        for app in apps:
            candidate = state.concept(app['candidate_id']) if app['candidate_id'] else None
            if not candidate:
                continue
            check = state.check_for(candidate.id)
            judgment = check.verdict if gate == 's7_gate' and check else candidate.quality_status
            _write_review(c, state, app, dict(origin_event_id='gate-' + digest([gate, app['candidate_version'], judgment])[:40],
                gate=gate, reviewer_type='AUTOMATED_GATE', evidence_level='WEAK_CONCEPT_REVIEW',
                dimension='joint_candidate_quality' if len(per_candidate[candidate.id]) > 1 else 'implementation_quality',
                judgment=judgment, attribution='joint_application' if len(per_candidate[candidate.id]) > 1 else 'candidate_level',
                reason_code='existing_gate_result', training_consent='NO_TRAINING',
                evidence_refs=list(candidate.evidence_ids), label_available_at=now()))


def validate_reviews(state, rows):
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError('application_reviews must be a bounded list')
    apps = {a['application_id']:a for a in state.scratch.get('ax_effect_applications', [])}
    allowed = {'condition_confirmed', 'condition_rejected', 'economics_rejected', 'unknown'}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid effect review')
        app = apps.get(row.get('effect_application_id'))
        candidate = state.concept(row.get('candidate_id'))
        if (not app or not candidate or app['candidate_id'] != candidate.id
                or app['candidate_version'] != digest(candidate.model_dump(mode='json'))):
            raise Conflict('Unknown or stale effect application/candidate')
        if row.get('condition_id') not in {x['condition_id'] for x in app['conditions']}:
            raise Conflict('Unknown effect condition')
        if row.get('decision') not in allowed or row.get('training_consent', 'NO_TRAINING') not in ('NO_TRAINING', 'PROJECT_ONLY'):
            raise ValueError('Invalid effect decision or consent')
        if not isinstance(row.get('evidence_refs', []), list):
            raise ValueError('evidence_refs must be a list')
    return apps


def user_reviews(state, rows, decisions, origin):
    if not contract(state):
        if rows:
            raise ValueError('Effect reviews require a versioned new run')
        return []
    apps = validate_reviews(state, rows)
    changed = set()
    with ledger.transaction() as c:
        h = ledger._head(c, state.run_id, lock=True)
        ledger.authorize(h, state.user_id)
        if h['epoch'] != state.scratch.get('execution_epoch', 0):
            raise Conflict('Review epoch changed')
        for index, row in enumerate(rows):
            app = apps[row['effect_application_id']]
            judgment = {'condition_confirmed':'COMPATIBLE', 'condition_rejected':'INCOMPATIBLE',
                        'economics_rejected':'EXCLUDED_ECONOMICS', 'unknown':'UNKNOWN'}[row['decision']]
            payload = dict(event_id='erev-' + digest([state.run_id, origin, index, row])[:56],
                origin_event_id=origin, gate='s7_user', reviewer_type='USER', evidence_level='USER_REPORTED',
                dimension='economics' if row['decision'] == 'economics_rejected' else 'condition_compatibility',
                judgment=judgment, condition_id=row['condition_id'], value=row.get('value'), unit=row.get('unit'),
                reason_code=row.get('reason_code', row['decision']), comment=row.get('comment', ''),
                evidence_refs=row.get('evidence_refs', []), training_consent=row.get('training_consent', 'NO_TRAINING'),
                attribution='explicit_condition', label_available_at=state.scratch.get('ax_response_received_at', now()))
            _write_review(c, state, app, payload)
            if judgment in ('COMPATIBLE', 'INCOMPATIBLE') and decisions.get(app['candidate_id']) != 'drop':
                changed.add(app['candidate_id'])
                state.scratch.setdefault('ax_condition_facts', {})[row['condition_id']] = dict(payload)
        for app in apps.values():
            if app['candidate_id'] in decisions:
                _write_review(c, state, app, dict(origin_event_id=origin, gate='s7_user', reviewer_type='USER',
                    evidence_level='PREFERENCE', dimension='adoption', judgment=decisions[app['candidate_id']],
                    reason_code='legacy_candidate_selection', training_consent='NO_TRAINING',
                    label_available_at=state.scratch.get('ax_response_received_at', now())))
    return sorted(changed)


def observations(tenant, project, *, cutoff=None):
    cutoff = cutoff or now()
    with ledger.store.engine.connect() as c:
        rows = c.execute(select(reviews.c.payload, reviews.c.created_at, applications.c.payload.label('application'))
            .join(applications, reviews.c.application_id == applications.c.application_id)
            .join(ledger.store.runs,ledger.store.runs.c.run_id==applications.c.run_id)
            .where(applications.c.tenant_id == tenant, applications.c.project_id == project)).mappings().all()
    superseded = {json.loads(r['payload']).get('supersedes_event_id') for r in rows}
    result = []
    for r in rows:
        p = json.loads(r['payload']); app = json.loads(r['application'])
        if (p['event_id'] in superseded or p.get('training_consent') != 'PROJECT_ONLY'
                or p.get('label_available_at', r['created_at']) > cutoff or r['created_at'] > cutoff
                or p.get('dimension') != 'condition_compatibility'
                or p.get('judgment') not in ('COMPATIBLE', 'INCOMPATIBLE') or not app.get('effect_id')):
            continue
        result.append(dict(review=p, application=app, label=1 if p['judgment'] == 'COMPATIBLE' else -1))
    return result


def rerank(state, candidates, required):
    if not contract(state):
        return candidates
    h = ledger.head(state.run_id, state.user_id); b = state.scratch['ax_bundle']
    ctx = structured_context(state)
    from .mode_contract import unified
    history = [] if unified(state) else observations(h['tenant_id'], h['project_id'], cutoff=b['effect_history_cutoff'])
    scores = defaultdict(dict)
    for row in history:
        app = row['application']
        if app['structured_context'] == ctx and app['run_id'] != state.run_id:
            existing=scores[app['effect_id']].get(app['run_id'],1)
            scores[app['effect_id']][app['run_id']] = min(existing,row['label'])
    scored = []
    for index, effect in enumerate(candidates):
        counts = list(scores[effect['id']].values())
        adjustment = sum(counts) / (len(counts) + 2) if counts else 0.0
        annotated = copy.deepcopy(effect)
        annotated['applicability_history'] = {'independent_runs':len(counts), 'score':adjustment,
            'meaning':'condition-compatible concept proxy; not success probability',
            'conditions_confirmed_for_current_run':False}
        scored.append((index, annotated, adjustment))
    from . import effect_ranker
    model = b.get('effect_ranker')
    from .registry import compatible_model
    incompatible = bool(model and not compatible_model(model))
    if incompatible: model = None
    if model:
        for index, effect, adjustment in scored:
            effect['applicability_history']['model_score'] = effect_ranker.predict(model, ctx, effect)
    shadow_model=b.get('shadow_effect_ranker')
    if shadow_model and not compatible_model(shadow_model): shadow_model = None
    if shadow_model:
        from .registry import observe_shadow
        shadow_scores={effect['id']:effect_ranker.predict(shadow_model,ctx,effect) for _,effect,_ in scored}
        observe_shadow(b['shadow_effect_ranker_version'],'esel-'+digest([state.run_id,ctx,required])[:56],
            dict(run_id=state.run_id,scores=shadow_scores,legal=True,
                 supported=effect_ranker.compatibility_key(ctx) in shadow_model.get('supported_contexts',[]),
                 counterfactual_result=None))
    if state.control.mode.value != 'DEEP':
        # Bounded movement within lexical bands keeps less familiar mechanisms exposed.
        scored.sort(key=lambda x: (x[0] // 6, -(x[2] + .25 * x[1]['applicability_history'].get('model_score', 0)), x[0]))
    value = dict(contract='effect-selection-v1', semantic_episode_id=episode(state),
        required_functions=list(required), problem_signature=digest(ctx),
        candidates=[dict(effect_id=e['id'], lexical_rank=i, **e['applicability_history']) for i,e,_ in scored],
        selection_method='ADVISORY' if state.control.mode.value == 'DEEP' else 'BOUNDED_HISTORY',
        model_version=b.get('effect_ranker_version') if model else None, propensity=None, used=False,
        model_fallback_reason='incompatible_model_contract' if incompatible else None,
        exposed_ids=[e['id'] for _,e,_ in scored])
    if unified(state):
        from .action_runtime import active_action
        value.update(contract='effect-selection-v2',feature_snapshot=ctx,
            catalog_version=digest(b['effects']),source_action_instance_id=(active_action.get() or {}).get('action_instance_id'),
            catalog_definitions={e['id']:copy.deepcopy(e) for e in candidates},
            selection_method='ADVISORY' if state.control.mode.value=='DEEP' else 'LEARNED_UTILITY' if model else 'LEXICAL_FALLBACK')
    sid = 'esel-' + digest([state.run_id, value])[:56]
    with ledger.transaction() as c:
        if not c.execute(select(selections.c.selection_id).where(selections.c.selection_id == sid)).first():
            c.execute(selections.insert().values(selection_id=sid, run_id=state.run_id, payload=canonical(value), created_at=now()))
    state.scratch.setdefault('ax_effect_selections', {})[sid] = value
    return [e for _,e,_ in scored]


def revise_review(run_id, actor, body):
    """Consent withdrawal/correction refers to the historical immutable target."""
    with ledger.transaction() as c:
        h=ledger._head(c,run_id,lock=True); ledger.authorize(h,actor)
        if h['epoch']!=body['expected_epoch'] or h['snapshot_id']!=body['snapshot_id']:
            raise Conflict('Review revision snapshot changed')
        old=c.execute(select(reviews).where(reviews.c.event_id==body['supersedes_event_id'],reviews.c.run_id==run_id)).mappings().first()
        if not old:
            raise Conflict('Unknown historical review')
        previous=json.loads(old['payload'])
        if previous.get('reviewer_type')!='USER':
            raise Conflict('Automated review cannot be reclassified as user evidence')
        all_rows=c.execute(select(reviews.c.payload).where(reviews.c.run_id==run_id)).scalars().all()
        if any(json.loads(p).get('supersedes_event_id')==body['supersedes_event_id'] and json.loads(p)['event_id']!=body['event_id'] for p in all_rows):
            raise Conflict('Review already superseded')
        payload=dict(previous,event_id=body['event_id'],supersedes_event_id=body['supersedes_event_id'],
            training_consent=body['training_consent'],comment=body['reason'],label_available_at=now())
        if body.get('judgment'):
            if previous['dimension']!='condition_compatibility':
                raise ValueError('Adoption/economics cannot be converted into physical applicability')
            payload['judgment']=body['judgment']
        app=json.loads(c.execute(select(applications.c.payload).where(applications.c.application_id==old['application_id'])).scalar_one())
        state=ledger.store.load_state(run_id)
        eid=_write_review(c,state,app,payload)
        return dict(event_id=eid,applied_to_artifact=False)
