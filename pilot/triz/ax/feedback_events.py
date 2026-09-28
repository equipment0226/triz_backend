"""One immutable evaluation stream and outbox, shared by both learning tasks.

Service retention is independent of training permission. Values are observations
or explicitly versioned ordinal policy values, never physical validation.
"""
import json
from sqlalchemy import select
from . import ledger
from .contracts import canonical, digest, now, Conflict
from .mode_contract import unified, contract
from .action_runtime import episode, candidate_actions

VERSION = 'common-candidate-evaluation-v1'
KIND = 'COMMON_EVALUATION'


def problem_family(state):
    if state.scratch.get('ax_problem_group'): return state.scratch['ax_problem_group']
    # Conservatively group wording/order variants by their recorded problem structure.
    def text(value): return ' '.join(str(value or '').casefold().split())
    contradictions=sorted((text(c.then_good),text(c.but_bad),text(c.coupling_mechanism)) for c in state.definition.technical_contradictions)
    physical=sorted((text(c.element),text(c.parameter),text(c.state_a),text(c.state_b)) for c in state.definition.physical_contradictions)
    return digest([state.domain.problem_type,text(state.domain.target_system),contradictions,physical]) if contradictions or physical else digest(text(state.raw_query))


def consent(state, payload=None):
    supplied = (payload or {}).get('training_consent')
    if supplied is not None and supplied not in ('NO_TRAINING', 'PROJECT_ONLY'):
        raise ValueError('Invalid training consent')
    return supplied or state.scratch.get('training_consent', 'NO_TRAINING')


def lineage(state, candidate):
    """Follow stored IDs; no title matching or reconstruction of missing producers."""
    from .effect_history import applications
    inventory = {r.get('id') or r.get('source_idea_id'): r for r in state.scratch.get('ax_idea_inventory', [])}
    inventory.update({i.id:i.model_dump(mode='json') for i in state.solve.raw_ideas})
    leaves, versions, missing, visiting = set(), set(), set(), set()
    def walk(ident):
        if not ident or ident in visiting:
            return
        visiting.add(ident)
        raw = inventory.get(ident)
        if raw is None:
            missing.add(ident); return
        versions.add(digest(raw))
        source = set(raw.get('source_idea_ids', [])) - {ident}
        details = raw.get('detail', {}).get('source_details', [])
        for detail in details:
            sid = detail.get('source_idea_id')
            if sid and sid not in inventory:
                inventory[sid] = dict(detail, id=sid)
            if sid and sid != ident:
                source.add(sid)
        if source:
            for sid in sorted(source): walk(sid)
        else:
            leaves.add(ident)
    for ident in candidate.source_idea_ids: walk(ident)
    actions = candidate_actions(state, candidate)
    active = set(candidate.active_effect_ids)
    with ledger.store.engine.connect() as c:
        apps = [json.loads(r) for r in c.execute(select(applications.c.payload).where(applications.c.run_id == state.run_id)).scalars()]
    apps = [a for a in apps if a.get('candidate_id') == candidate.id and a.get('effect_id') in active
            and a.get('candidate_version') == digest(candidate.model_dump(mode='json'))
            and a.get('catalog_status') == 'BOUND' and set(a.get('source_raw_idea_ids', [])) <= leaves
            and a.get('semantic_episode_id') == episode(state)]
    # Versions collected before audit may differ only by the subsequent verdict.
    # The snapshot in this event is authoritative; the application remains a source reference.
    unique = {}
    for app in sorted(apps, key=lambda a:a['application_id']):
        unique.setdefault(app['effect_id'], app)
    return dict(source_raw_idea_ids=sorted(leaves), source_action_instance_ids=actions,
        merge_versions=sorted(versions), active_effect_application_ids=sorted(a['application_id'] for a in unique.values()),
        active_effect_ids=sorted(unique), attribution='OBSERVED_JOINT_LINEAGE' if leaves and actions and not missing else 'UNKNOWN_ATTRIBUTION',
        missing_source_ids=sorted(missing), mechanism_key=candidate.mechanism_key or digest(candidate.working_principle),
        candidate_snapshot=candidate.model_dump(mode='json'))


def _write(c, state, candidate, *, origin, stage, dimension, value, evidence, scope,
           reviewer='USER', source_step_id=None, detail=None, supersedes=None, lineage_data=None, consent_version=None):
    head = ledger._head(c, state.run_id, lock=True)
    ledger.authorize(head, state.user_id)
    if head['epoch'] != state.scratch.get('execution_epoch', 0):
        raise Conflict('Stale evaluation input')
    snapshot = candidate.model_dump(mode='json')
    # Quality flags are outcomes, not the identity of the technical design.
    version = digest({k:v for k,v in snapshot.items() if k not in ('quality_status','quality_issues')})
    key = digest([origin, candidate.id, version, dimension, reviewer])
    eid = 'eval-' + digest([state.run_id, key])[:56]
    existing = c.execute(select(ledger.events.c.payload).where(ledger.events.c.event_id == eid)).scalar()
    if existing:
        old = json.loads(existing)
        if old['observed_value'] != value or old['training_consent_scope'] != scope:
            raise Conflict('Evaluation submission identity conflict; use a new revision')
        return eid
    stamp = now()
    data = dict(contract=VERSION, event_id=eid, logical_observation_key=key, supersedes_event_id=supersedes,
        run_id=state.run_id, tenant_id=head['tenant_id'], project_id=head['project_id'], semantic_episode_id=episode(state),
        candidate_id=candidate.id, candidate_version=version, source_snapshot_id=head['snapshot_id'],
        review_revision=dict(state.scratch.get('candidate_review_revisions',{}).get(candidate.id,{})),
        evaluation_stage=stage, reviewer_type=reviewer,
        reviewer_model_and_rubric_version=detail or {}, dimension=dimension, observed_value=value,
        observed_mask=value is not None, evidence_level=evidence, source_step_id=source_step_id,
        source_event_id=origin, evidence_refs=sorted(candidate.evidence_ids), created_at=stamp, label_available_at=stamp,
        training_consent_scope=scope, consent_version=consent_version or state.scratch.get('training_consent_version','explicit-project-consent-v1'),
        synthetic=bool(state.scratch.get('synthetic') or state.scratch.get('acceptance_fixture')),
        problem_family=problem_family(state),
        **(lineage_data or {}))
    ledger._event(c, state.run_id, KIND, data, event_id=eid)
    return eid


def user_decisions(state, decisions, payload, origin):
    if not unified(state): return []
    from .effect_history import collect
    collect(state)
    scope = consent(state, payload)
    facts = {cid:lineage(state, state.concept(cid)) for cid in decisions if state.concept(cid)}
    settings = contract(state)['feedback_settings']
    with ledger.transaction() as c:
        submission = 'gate-submission-' + digest([state.run_id, origin])[:48]
        content = dict(decisions=dict(sorted(decisions.items())), scope=scope)
        prior = c.execute(select(ledger.events.c.payload).where(ledger.events.c.event_id==submission)).scalar()
        if prior and json.loads(prior)!=content: raise Conflict('Gate submission identity conflict')
        if not prior: ledger._event(c,state.run_id,'GATE_DECISIONS_SUBMITTED',content,event_id=submission)
        ids = [_write(c, state, state.concept(cid), origin=submission, stage='s7_user', dimension='user_utility',
            value=settings['keep' if choice=='accept' else 'drop'], evidence='EXPLICIT_USER_PREFERENCE', scope=scope,
            detail={'normalization':'weak-keep-drop-v1','choice':choice}, lineage_data=facts[cid],
            consent_version='explicit-project-consent-v1' if payload.get('training_consent') is not None else None)
            for cid, choice in sorted(decisions.items()) if cid in facts and choice in ('accept','drop')]
    state.scratch['training_consent'] = scope
    if payload.get('training_consent') is not None: state.scratch['training_consent_version']='explicit-project-consent-v1'
    return ids


def final_feedback(state, payload):
    """Submission, raw service feedback and evaluation/outbox share a transaction."""
    from .effect_history import collect
    collect(state)
    rows = sorted(payload.get('solution_feedback') or [], key=canonical)
    scope = consent(state, payload)
    origin = payload.get('submission_id') or 'feedback-' + digest([rows, scope, payload.get('overall_rating')])
    submission = 'submission-' + digest([state.run_id, origin])[:48]
    facts = {r['concept_id']:lineage(state, state.concept(r['concept_id'])) for r in rows if state.concept(r.get('concept_id',''))}
    ids = []
    with ledger.transaction() as c:
        old = c.execute(select(ledger.events.c.payload).where(ledger.events.c.event_id == submission)).scalar()
        content_hash = digest([rows, scope])
        if old:
            if json.loads(old)['content_hash'] != content_hash: raise Conflict('Feedback submission conflict')
            return False
        ledger._event(c, state.run_id, 'FEEDBACK_SUBMITTED', {'content_hash':content_hash,'origin':origin,'rows':rows,'scope':scope}, event_id=submission)
        for row in rows:
            candidate = state.concept(row.get('concept_id',''))
            if candidate is None: continue
            rating = row.get('rating')
            value = (rating-3)/2 if type(rating) in (int,float) and 1 <= rating <= 5 else None
            if value is None and row.get('adopted_explicit') is True and type(row.get('adopted')) is bool:
                value = 1.0 if row['adopted'] else -1.0
            ids.append(_write(c, state, candidate, origin=submission, stage='s10_feedback', dimension='user_utility',
                value=value, evidence='EXPLICIT_USER_PREFERENCE' if value is not None else 'UNOBSERVED', scope=scope,
                detail={'normalization':'rating-1-to-5-v1','rating':rating,'adopted_explicit':row.get('adopted_explicit',False)},
                lineage_data=facts[candidate.id],
                consent_version='explicit-project-consent-v1' if payload.get('training_consent') is not None else None))
            c.execute(ledger.store.feedback.insert().values(run_id=state.run_id, concept_id=candidate.id,
                rating=rating if type(rating) is int else 0, adopted=row.get('adopted'),
                reason_tags=canonical(row.get('reason_tags',[])), comment=row.get('comment',''), created_at=ledger.store._now()))
    state.scratch['training_consent'] = scope
    if payload.get('training_consent') is not None: state.scratch['training_consent_version']='explicit-project-consent-v1'
    return True


def model_review(state, candidate, row, *, stage, step_id, rubric, model, scope=None):
    if not unified(state): return None
    from .effect_history import collect
    collect(state)
    facts = lineage(state, candidate)
    verdict = row.get('verdict')
    ordinal = {'PASS':1.,'REVISE':0.,'REJECT':-1.,'FAIL':-1.}
    value = ordinal.get(verdict)
    if stage == 's7_gate' and verdict == 'CONDITIONAL': value = None
    with ledger.transaction() as c:
        return _write(c, state, candidate, origin='review-'+digest([step_id,rubric,row]), stage=stage,
            dimension='constraint_quality' if stage=='s7_gate' else 'concept_quality', value=value,
            evidence='MODEL_REVIEW_PROXY', scope=scope or consent(state), reviewer='INDEPENDENT_REVIEW' if stage=='s6_quality' else 'CONSTRAINT_REVIEW',
            source_step_id=step_id, detail={'model':model,'rubric':rubric,'normalization':'ordinal-verdict-v1','actual_review':row}, lineage_data=facts)


def coverage_review(state,candidate,step_id,checks):
    if not unified(state): return
    from .effect_history import collect
    collect(state)
    value={'PASS':1.,'REVISE':0.,'REJECT':-1.}.get(candidate.quality_status)
    with ledger.transaction() as c:
        _write(c,state,candidate,origin='coverage-'+digest([step_id,candidate.id,checks,candidate.quality_status]),
            stage='s6_quality',dimension='coverage_quality',value=value,evidence='STRUCTURAL_REVIEW_PROXY',
            scope=consent(state),reviewer='DETERMINISTIC_OBLIGATION_CHECK',source_step_id=step_id,
            detail={'normalization':'ordinal-completeness-v1','actual_checks':checks,'issues':candidate.quality_issues},
            lineage_data=lineage(state,candidate))


def invalidate_review(state,candidate,revision):
    """An observed input invalidation is not an independent model review."""
    if not unified(state): return
    from .effect_history import collect
    collect(state)
    facts=lineage(state,candidate)
    with ledger.transaction() as connection:
        return _write(connection,state,candidate,origin='input-change-'+digest([candidate.id,revision]),
            stage='s6_input_invalidated',dimension='review_validity',value=None,
            evidence='DETERMINISTIC_INPUT_CHANGE',scope=consent(state),reviewer='INPUT_VALIDITY_CHECK',
            detail={'current_review_input':dict(revision),'reason':'review_input_changed'},lineage_data=facts)


def recorded_test(c,state,candidate,body):
    """Adapt an existing validated test submission without asserting measured truth."""
    if not unified(state) or body.decision_type not in ('RECORD_TEST_RESULT','RECORD_FIELD_RESULT'): return
    previous=None
    if body.supersedes_event_id:
        rows=c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id==state.run_id,ledger.events.c.event_type==KIND)).scalars()
        previous=next((r['event_id'] for r in map(json.loads,rows) if r.get('source_event_id')==body.supersedes_event_id),None)
    _write(c,state,candidate,origin=body.event_id,stage='recorded_test',dimension='reported_test_result',
        value={'PASS':1.,'FAIL':-1.}.get(body.result),evidence='USER_REPORTED_TEST_NOT_INDEPENDENTLY_VALIDATED',
        scope=body.consent,reviewer='USER_REPORTED_TEST:'+str(body.obligation_id),supersedes=previous,
        detail={'actual_submission':body.model_dump(mode='json'),'normalization':'ordinal-reported-result-v1'},
        lineage_data=lineage(state,candidate),consent_version='explicit-project-consent-v1')


def current(tenant, project, cutoff=None, *, include_synthetic=False):
    cutoff = cutoff or now()
    with ledger.store.engine.connect() as c:
        rows = c.execute(select(ledger.events.c.payload).join(ledger.heads,ledger.heads.c.run_id==ledger.events.c.run_id)
            .where(ledger.events.c.event_type==KIND,ledger.heads.c.tenant_id==tenant,ledger.heads.c.project_id==project)).scalars().all()
    values = [json.loads(r) for r in rows]
    superseded = {r.get('supersedes_event_id') for r in values}
    # Withdrawal invalidates eligibility now, even for an older training cutoff.
    return [r for r in values if r['event_id'] not in superseded and r['label_available_at'] <= cutoff
            and r['training_consent_scope']=='PROJECT_ONLY' and (include_synthetic or not r['synthetic'])]


def meeting_reviews(state, scores):
    if not unified(state): return
    from .effect_history import collect
    collect(state)
    for score in scores:
        candidate = state.concept(score.concept_id)
        if candidate is None: continue
        raw = score.model_dump(mode='json')
        persona=next((p.persona_id for p in state.evaluation.reviewers if p.role_name==score.reviewer_role),None)
        # Link the actual score to a stored meeting output, not to the aggregate.
        step = next((s for s in reversed(state.steps) if s.status in ('OK','SKIPPED')
                     and canonical(raw) in canonical(s.output_json)), None)
        if step is None:
            # Meeting outputs may include other fields; match all supplied score fields.
            def contains(value):
                if isinstance(value,dict):
                    core=('concept_id','dimension','score','rationale')
                    return all(value.get(k)==raw[k] for k in core) or any(contains(v) for v in value.values())
                return isinstance(value,list) and any(contains(v) for v in value)
            step = next((s for s in reversed(state.steps) if s.status in ('OK','SKIPPED')
                and s.agent_id=='persona::'+str(persona) and contains(s.output_json)),None)
        if step is None: continue
        with ledger.transaction() as c:
            _write(c,state,candidate,origin='meeting-'+digest([step.step_id,raw]),stage='s8_evaluate',
                dimension='evaluation_quality',value=max(-1.,min(1.,(score.score-3)/2)),
                evidence='MODEL_REVIEW_PROXY',scope=consent(state),reviewer=score.reviewer_role+':'+score.dimension,
                source_step_id=step.step_id,detail={'actual_review':raw,'rubric':state.scratch['ax_bundle']['rubrics'],
                'normalization':'rating-1-to-5-v1'},lineage_data=lineage(state,candidate))


def revise(run_id, owner, event_id, *, consent_scope, reason, value=None, correct_value=False):
    """Owner-only additive correction/withdrawal; frozen outputs are untouched."""
    if consent_scope not in ('NO_TRAINING','PROJECT_ONLY') or not reason.strip():
        raise ValueError('Explicit consent scope and correction reason required')
    if correct_value and (type(value) not in (int,float) or not -1<=value<=1):
        raise ValueError('Corrected normalized value must be between -1 and 1')
    with ledger.transaction() as c:
        head=ledger._head(c,run_id,lock=True);ledger.authorize(head,owner)
        old=c.execute(select(ledger.events.c.payload).where(ledger.events.c.event_id==event_id,
            ledger.events.c.run_id==run_id,ledger.events.c.event_type==KIND)).scalar()
        if not old: raise ValueError('Evaluation not found in this run')
        old=json.loads(old)
        revision=dict(old,supersedes_event_id=event_id,training_consent_scope=consent_scope,consent_version='explicit-project-consent-v1',
            observed_value=value if correct_value else old['observed_value'],correction_reason=reason)
        revision['observed_mask']=revision['observed_value'] is not None
        eid='eval-'+digest([event_id,consent_scope,reason,value,correct_value])[:56]
        if not c.execute(select(ledger.events.c.event_id).where(ledger.events.c.event_id==eid)).first():
            # Only the current leaf can be corrected, avoiding divergent revisions.
            all_rows=c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id==run_id,
                ledger.events.c.event_type==KIND)).scalars()
            if any(json.loads(r).get('supersedes_event_id')==event_id for r in all_rows):
                raise Conflict('Evaluation already superseded')
            revision.update(event_id=eid,created_at=now(),label_available_at=now())
            ledger._event(c,run_id,KIND,revision,event_id=eid)
        return eid
