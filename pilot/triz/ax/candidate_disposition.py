"""Recorded exclusions; presentation IDs do not identify a technical design."""
from .contracts import digest, now
from .action_runtime import episode, candidate_actions

KINDS={'USER_DROP','CONSTRAINT_FAIL','QUALITY_REJECT','LEGACY_UNKNOWN_ORIGIN'}


def design_version(candidate):
    def canonical(value):
        if isinstance(value,str): return ' '.join(value.casefold().split())
        if isinstance(value,list): return sorted((canonical(v) for v in value),key=repr)
        if isinstance(value,dict): return {k:canonical(v) for k,v in sorted(value.items())}
        return value
    raw=candidate.model_dump(mode='json')
    fields=('working_principle','intervention_variable','changes_to_system','required_resources',
            'active_effect_ids','assumptions','transfer_conditions')
    return digest(canonical({k:raw.get(k) for k in fields}))


def record(state,candidate,kind,reason,source=None):
    if kind not in KINDS: raise ValueError('Unknown candidate disposition')
    from .feedback_events import lineage
    facts=lineage(state,candidate)
    row=dict(candidate_id=candidate.id,candidate_design_version=design_version(candidate),reason_kind=kind,
        source_step_or_event_id=source,input_snapshot_id=state.scratch.get('ax_snapshot_id'),
        semantic_episode_id=episode(state),original_leaf_ids=facts['source_raw_idea_ids'],
        observed_reason=reason,candidate_snapshot=candidate.model_dump(mode='json'),
        action_instance_ids=candidate_actions(state,candidate),active_effect_ids=list(candidate.active_effect_ids))
    row['disposition_id']='disposition-'+digest(row)
    rows=state.scratch.setdefault('candidate_dispositions',[])
    if not any(r['disposition_id']==row['disposition_id'] for r in rows):
        row['created_at']=now(); rows.append(row)
    return row


def records(state):
    rows=list(state.scratch.get('candidate_dispositions',[]))
    known={r['candidate_id'] for r in rows}
    decisions=state.scratch.get('gate_decisions',{}).get('decisions',{})
    failures=state.scratch.get('ax_constraint_failures',{})
    legacy=set(state.scratch.get('adaptive_dropped_candidates',[]))-known
    observed={}
    if legacy:
        import json
        from sqlalchemy import select
        from . import ledger
        with ledger.store.engine.connect() as connection:
            values=connection.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id==state.run_id,
                ledger.events.c.event_type=='COMMON_EVALUATION').order_by(ledger.events.c.created_at.desc()).limit(5000)).scalars()
            for raw in values:
                event=json.loads(raw)
                if (event.get('candidate_id') in legacy and event.get('evaluation_stage')=='s7_user'
                    and event.get('reviewer_model_and_rubric_version',{}).get('choice')=='drop'):
                    observed.setdefault(event['candidate_id'],event)
    for cid in legacy:
        event=observed.get(cid)
        if event and event.get('candidate_snapshot'):
            from ..schema import ConceptSpec
            rows.append(dict(candidate_id=cid,reason_kind='USER_DROP',semantic_episode_id=event['semantic_episode_id'],
                candidate_design_version=design_version(ConceptSpec.model_validate(event['candidate_snapshot'])),
                source_step_or_event_id=event['event_id'],candidate_snapshot=event['candidate_snapshot']))
            continue
        kind='USER_DROP' if decisions.get(cid)=='drop' else 'CONSTRAINT_FAIL' if cid in failures else 'LEGACY_UNKNOWN_ORIGIN'
        rows.append(dict(candidate_id=cid,reason_kind=kind,semantic_episode_id=episode(state)))
    return rows


def blocked(state,candidate):
    version=design_version(candidate)
    return any((r.get('candidate_design_version')==version or (not r.get('candidate_design_version') and r['candidate_id']==candidate.id))
        for r in records(state) if r.get('semantic_episode_id')==episode(state))


def all_user_dropped(state):
    rows=[r for r in records(state) if r.get('semantic_episode_id')==episode(state)]
    cohort=state.scratch.get('adaptive_gate_cohort')
    if cohort:
        latest={r['candidate_id']:r for r in rows}
        return not state.concepts and all(latest.get(cid,{}).get('reason_kind')=='USER_DROP' for cid in cohort)
    return not state.concepts and bool(rows) and all(r['reason_kind']=='USER_DROP' for r in rows)
