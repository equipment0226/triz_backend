"""Review changed representative inputs only; persist the owning portfolio."""
import copy
from .contracts import digest
from ..context import RunContext
from ..schema import ConceptSpec


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
    keys={i.id:digest([common,i.model_dump(mode='json')]) for i in ideas}
    cache=state.scratch.setdefault('adaptive_concept_cache',{})
    changed=[i for i in ideas if not cache.get(keys[i.id],{}).get('complete')]
    old={c.id:c for c in state.concepts}
    if changed:
        branch=state.model_copy(deep=True)
        branch.concepts=[]
        branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
        for name in ('agent_cache','s6_quality_batches'):
            branch.scratch[name]=state.scratch.setdefault(name,{})
        child=RunContext(branch)
        child.lock,child.budget,child.call_slots=ctx.lock,ctx.budget,ctx.call_slots
        child.persist=ctx.persist
        quality._generate_concepts(child,ideas_override=changed)
        for name in ('ax_mechanisms','ax_action_results'):
            state.scratch.setdefault(name,{}).update(branch.scratch.get(name,{}))
        for idea in changed:
            cache[keys[idea.id]]=dict(source_idea_id=idea.id,
                complete=all(c.id in branch.scratch.get('ax_candidate_review',{}).get('audit_completed_concept_ids',[])
                    for c in branch.concepts if idea.id in c.source_idea_ids),
                concepts=[c.model_dump(mode='json') for c in branch.concepts if idea.id in c.source_idea_ids],
                audited_ids=branch.scratch.get('ax_candidate_review',{}).get('audit_completed_concept_ids',[]),
                excluded=[copy.deepcopy(r) for r in branch.scratch.get('excluded_concepts',[]) if idea.id in r.get('source_idea_ids',[])])
        state.scratch.setdefault('ax_portfolio_trace',[]).extend(branch.scratch.get('ax_portfolio_trace',[])[len(state.scratch.get('ax_portfolio_trace',[])):])
    dropped=set(state.scratch.get('adaptive_dropped_candidates',[]))
    output={}
    for idea in ideas:
        for raw in cache[keys[idea.id]]['concepts']:
            if raw['id'] not in dropped:
                output[raw['id']]=old.get(raw['id']) or ConceptSpec.model_validate(raw)
    # Explicit repairs have independent lineage and are not representatives to regenerate.
    for c in old.values():
        if c.id.startswith('CPT-AX-') and c.id not in dropped: output[c.id]=c
    state.concepts=list(output.values())
    prior=state.scratch.get('excluded_concepts',[])
    excluded={digest(r):r for r in prior}
    for idea in ideas:
        for row in cache[keys[idea.id]]['excluded']: excluded[digest(row)]=row
    state.scratch['excluded_concepts']=list(excluded.values())
    state.scratch['ax_candidate_review']=dict(contract='idea-retention-v2',policy='delta-representative-review-v1',
        available_ideas=len(ideas),assigned_ideas=len(ideas),review_limit=None,completed_ideas=len(ideas),
        completed_idea_ids=[i.id for i in ideas],unassigned_idea_ids=[],unreviewed_idea_ids=[],
        audit_completed_concept_ids=sorted({cid for idea in ideas for cid in cache[keys[idea.id]].get('audited_ids',[]) if cid in output}),
        audit_unreviewed_concept_ids=sorted(set(output)-{cid for idea in ideas for cid in cache[keys[idea.id]].get('audited_ids',[])}),
        changed_idea_ids=[i.id for i in changed],reused_idea_ids=[i.id for i in ideas if i not in changed])
    ctx.persist()
