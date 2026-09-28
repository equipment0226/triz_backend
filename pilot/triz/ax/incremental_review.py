"""Review changed representative inputs only; persist the owning portfolio."""
import copy
from .contracts import digest
from ..context import RunContext
from ..schema import ConceptSpec

CONTRACT = 'current-review-projection-v2'


def complete_entry(concepts, excluded, audited):
    return bool(concepts or excluded) and all(c['id'] in audited for c in concepts) and all(r.get('reason') for r in excluded)


def generate(ctx):
    from .. import quality, digest as packets, verify
    from ..idea_consolidation import ensure_consolidated
    state=ctx.state
    ensure_consolidated(ctx)
    ideas=list(state.solve.raw_ideas)
    bundle=state.scratch['ax_bundle']
    common=dict(facts=packets.facts_packet(state),causal=packets.causal_packet(state),
        contradictions=packets.contradictions_digest(state),constraints=verify.constraints_full(state),
        evidence=[e.model_dump(mode='json') for e in state.evidence],models=bundle['models'],
        prompts=bundle['prompts'],rubrics=bundle['rubrics'],review_policy=bundle['config'].get('verification'),
        prior_cases=state.scratch.get('prior_case_ids',[]),injected_instructions=state.control.injected_agents)
    keys={i.id:digest([CONTRACT,common,i.model_dump(mode='json')]) for i in ideas}
    cache=state.scratch.setdefault('adaptive_concept_cache',{})
    changed=[i for i in ideas if not cache.get(keys[i.id],{}).get('complete') or
        state.scratch.get('review_inputs',{}).get(i.id,{}).get('input_hash')!=keys[i.id]]
    old={c.id:c for c in state.concepts}
    common_hash=digest(common)
    changed_context=state.scratch.get('current_review_context')!=common_hash
    if changed:
        changed_ids={i.id for i in changed}
        sequence=state.scratch.get('review_revision_sequence',0)+1
        state.scratch['review_revision_sequence']=sequence
        inputs=state.scratch.setdefault('review_inputs',{})
        for idea in changed:
            inputs[idea.id]=dict(contract=CONTRACT,input_hash=keys[idea.id],revision=sequence)
        # Invalidate only affected approvals before provider work, preserving the portfolio.
        from .feedback_events import invalidate_review
        for c in old.values():
            if changed_ids.intersection(c.source_idea_ids) or changed_context or set(c.source_idea_ids)-set(keys):
                ref=next((inputs[i] for i in c.source_idea_ids if i in changed_ids),dict(contract=CONTRACT,input_hash=common_hash,revision=sequence))
                state.scratch.setdefault('candidate_review_revisions',{})[c.id]=dict(ref)
                c.quality_status='UNVERIFIED'
                c.quality_issues=['검토 입력 변경: 현재 입력의 독립 검토 대기']
                invalidate_review(state,c,ref)
        state.scratch['current_review_context']=common_hash
        ctx.persist()
        branch=state.model_copy(deep=True)
        branch.concepts=[]
        branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
        for name in ('agent_cache','s6_quality_batches','candidate_review_revisions','candidate_dispositions'):
            branch.scratch[name]=state.scratch.setdefault(name,[] if name=='candidate_dispositions' else {})
        child=RunContext(branch)
        child.lock,child.budget,child.call_slots=ctx.lock,ctx.budget,ctx.call_slots
        child.persist=ctx.persist
        quality._generate_concepts(child,ideas_override=changed)
        for name in ('ax_mechanisms','ax_action_results'):
            state.scratch.setdefault(name,{}).update(branch.scratch.get(name,{}))
        for idea in changed:
            cache[keys[idea.id]]=dict(contract=CONTRACT,source_idea_id=idea.id,
                concepts=[c.model_dump(mode='json') for c in branch.concepts if idea.id in c.source_idea_ids],
                audited_ids=branch.scratch.get('ax_candidate_review',{}).get('audit_completed_concept_ids',[]),
                excluded=[copy.deepcopy(r) for r in branch.scratch.get('excluded_concepts',[]) if idea.id in r.get('source_idea_ids',[])])
            entry=cache[keys[idea.id]]
            entry['complete']=complete_entry(entry['concepts'],entry['excluded'],entry['audited_ids'])
        archive={digest(r):r for r in state.scratch.get('ax_excluded',[])+branch.scratch.get('ax_excluded',[])}
        state.scratch['ax_excluded']=list(archive.values())
        state.scratch.setdefault('ax_portfolio_trace',[]).extend(branch.scratch.get('ax_portfolio_trace',[])[len(state.scratch.get('ax_portfolio_trace',[])):])
    from .candidate_disposition import blocked
    output={}
    for idea in ideas:
        for raw in cache.get(keys[idea.id],{}).get('concepts',[]):
            current=ConceptSpec.model_validate(raw)
            if not blocked(state,current):
                output[current.id]=current
    # Explicit repairs have independent lineage and are not representatives to regenerate.
    for c in old.values():
        if c.id.startswith('CPT-AX-') and not blocked(state,c): output[c.id]=c
    state.concepts=list(output.values())
    prior=state.scratch.get('excluded_concepts',[])
    excluded={digest(r):r for r in prior}
    for idea in ideas:
        for row in cache[keys[idea.id]]['excluded']: excluded[digest(row)]=row
    state.scratch['excluded_concepts']=list(excluded.values())
    completed=[i.id for i in ideas if cache.get(keys[i.id],{}).get('complete')]
    state.scratch['ax_candidate_review']=dict(contract='idea-retention-v2',policy=CONTRACT,
        available_ideas=len(ideas),assigned_ideas=len(ideas),review_limit=None,completed_ideas=len(completed),
        completed_idea_ids=completed,unassigned_idea_ids=[],unreviewed_idea_ids=[i.id for i in ideas if i.id not in completed],
        audit_completed_concept_ids=sorted({cid for idea in ideas for cid in cache[keys[idea.id]].get('audited_ids',[]) if cid in output}),
        audit_unreviewed_concept_ids=sorted(set(output)-{cid for idea in ideas for cid in cache[keys[idea.id]].get('audited_ids',[])}),
        changed_idea_ids=[i.id for i in changed],reused_idea_ids=[i.id for i in ideas if i not in changed])
    ctx.persist()
