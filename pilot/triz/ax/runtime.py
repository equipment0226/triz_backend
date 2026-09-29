"""Compatibility adapter: stable 13-stage workflow, versioned stage products."""
import copy
import os
from pathlib import Path
from .. import prompts_registry, knowledge
from ..settings import settings
from . import WORKFLOW, RELEASE, enabled
from . import ledger
from .contracts import digest, GATES, Conflict

DEPENDENCIES = {
    'input': (), 'problem': ('input',), 'analysis': ('problem',),
    'definition': ('problem','analysis'), 'solve': ('definition',),
    'concepts': ('solve','analysis'), 'constraints': ('problem','concepts'),
    'evidence': ('concepts',), 'evaluation': ('constraints','evidence'),
    'coherence': ('problem','definition','concepts','constraints'),
    'selection': ('evaluation','constraints','evidence','coherence'), 'report_context': ('selection',),
    'report': ('selection','report_context'),
    'feedback': ('selection',),
}
OUTPUTS = {
    's0_bootstrap':('input',), 's0_research':('input',), 's1_intake':('input',),
    's2_confirm':('problem',), 's3_analyze':('problem','analysis'), 's4_define':('definition',),
    # S6 can consolidate legacy S5 inventories on an explicit rerun. Capture its
    # producer before concepts so their parent and the frozen report agree.
    # ledger.capture reuses the solve version when payload and parents are unchanged.
    's5_solve':('solve',), 's6_concept':('solve','concepts'), 's7_gate':('concepts','constraints'),
    's8_references':('concepts','constraints','evidence'), 's8_evaluate':('evaluation','selection'),
    's9_report':('report',), 's10_feedback':('feedback',),
}
MODEL_FIELDS=('model','base_url','temperature','max_tokens','json_mode',
              'supports_temperature','token_parameter','thinking_mode','cost_in','cost_out')


def new_runs_enabled():
    return os.getenv('TRIZ_AX_ENABLED',str(settings.triz.get('ax',{}).get('enabled',False))).lower()=='true'


def bundle(state=None):
    root=Path(__file__).resolve().parents[1]
    data={'workflow':WORKFLOW,'release_version':RELEASE,'coherence_contract':'coherence-v1','coordinator_hitl':False,'policy_version':'rules-v1','feature_schema':'ax-features-v2',
          'action_catalog':'ax-actions-v1','rule_catalog_version':'empty-v1',
          'concept_effect_contract':'explicit-active-effects-v1',
          'rag_case_contract':'latest-final-feedback-case-v2',
          'rule_catalog':[], 'policy':None,
          'models':{t:{k:getattr(c,k) for k in MODEL_FIELDS} for t,c in settings.tiers.items()},
          'prompts':{p:prompts_registry.raw(p) for p in prompts_registry.list_prompts()},
          'effects':copy.deepcopy(knowledge.effects()),
          'effect_sources':copy.deepcopy(knowledge._load('effects_sources.json')),
          'separation_catalog':copy.deepcopy(knowledge.separation()),
          'config':copy.deepcopy(settings.triz),'rubrics':copy.deepcopy(settings.rubrics),
          'limits':{'branches':3,'recovery_targets':2,'repairs_per_blocker':2,'depth':2,
                    'validation_reserve_microusd':120000,'idea_review_policy':'full-idea-review-v1',
                    'recovery_additions':4,'expansion_rounds':1,'portfolio_completion_v1':True},
          'source_hashes':{str(p.relative_to(root.parent)).replace('\\','/'):digest(p.read_text(encoding='utf-8')) for p in
                           [root/'nodes.py',root/'quality.py',root/'verify.py',root/'render.py',root/'reformulation.py',
                            root/'display_terms.py',root/'report_style.py',root/'solve_contract.py',root/'digest.py',
                            root/'agent.py',root/'prompts_registry.py',root/'evidence.py',root/'idea_consolidation.py',root/'separation_contract.py',
                            root/'ax/runtime.py',root/'ax/coordinator.py',root/'ax/coherence.py',
                            root/'ax/coherence_recovery.py',root/'ax/validation.py',root/'ax/report.py',
                            root/'ax/learning.py',root/'ax/mode_contract.py',root/'ax/action_runtime.py',
                            root/'ax/routing_q.py',root/'ax/exploration_context.py',root/'ax/usage_recovery.py',root/'ax/effect_history.py',root/'ax/effect_ranker.py',
                            root/'ax/registry.py',root/'ax/worker.py',root/'ax/feedback_events.py',root/'ax/learning_outcomes.py',
                            root/'ax/adaptive_tracks.py',root/'ax/incremental_review.py',
                            root/'ax/concept_effects.py',root/'ax/source_lineage.py',root/'ax/recovery.py',
                            root/'rag.py',root/'store.py',root/'ax/ledger.py',
                            root/'ax/candidate_disposition.py',root/'ax/confirmed_context.py',root/'ax/track_cost.py',root/'ax/gateway.py',root.parent/'templates/report_full.md.j2',
                            root.parent/'templates/report_reformulation.md.j2',
                            root.parent/'templates/report.html.j2',root.parent/'templates/report_ax_appendix.md.j2']}}
    if state is not None and settings.triz.get('ax', {}).get('run_contract_version', 'ax-run-v2') in ('ax-run-v2','ax-run-v3'):
        from .mode_contract import pin
        data['run_contract'] = pin(state.control.mode.value,
            smart=settings.triz.get('ax', {}).get('smart_orchestration_enabled', True),
            version=settings.triz['ax']['run_contract_version'], settings=settings.triz['ax'].get('adaptive', {}),
            required=state.scratch.get('explicit_required_tracks', []))
        data['feature_schema'] = 'ax-state-action-v3'
        from .routing_q import contracts
        data.update(contracts())
        if data['run_contract']['version']=='ax-run-v3':
            data['feature_schema'] = 'ax-state-action-v5'
            data.update(contracts(data['feature_schema']))
        data['action_catalog'] = 'ax-action-instances-v3'
        data['limits'].update({k: v for k, v in data['run_contract']['profile'].items() if k != 'tracks'})
        data['effect_history_cutoff'] = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    if state is not None:
        from .registry import for_run
        data.update(for_run(state,feature_schema=data['feature_schema']))
        if data.get('run_contract'):
            rc = data['run_contract']
            if not rc['smart_orchestration_enabled']:
                data['policy'] = None
                data.pop('shadow_policy', None)
                data['policy_version'] = 'rules-v1'
            elif data.get('policy'):
                rc['routing_policy_mode'] = 'CANARY'
            elif data.get('shadow_policy'):
                rc['routing_policy_mode'] = 'SHADOW'
            if rc['mode']!='DEEP':
                rc['effect_reranking_mode']='ACTIVE' if data.get('effect_ranker') else 'SHADOW' if data.get('shadow_effect_ranker') else 'BASELINE'
    data['bundle_id']='bundle-'+digest(data)
    return data


def initialize(state):
    state.scratch['workflow_version']=WORKFLOW
    state.scratch['ax_bundle']=bundle(state)
    if state.scratch['ax_bundle'].get('run_contract'):
        state.scratch['mode_locked'] = True
        state.scratch['semantic_episode_id'] = state.run_id + ':0'
        state.scratch['semantic_generation'] = 0
    state.cost.budget_usd=float(state.scratch['ax_bundle']['config'].get('ax',{}).get('hard_budget_usd',2.0))
    state.scratch['ax_gates']={key:{'label':label,'status':'NOT_RUN'} for key,label,_ in GATES}
    ledger.bootstrap(state,state.scratch['ax_bundle'])
    ledger.capture(state,{'input':section(state,'input')},DEPENDENCIES,'run_created')


def section(state,key):
    dump=lambda obj:obj.model_dump(mode='json')
    if key=='input':
        return {'raw_query':state.raw_query,'intake':dump(state.intake),'domain':dump(state.domain),
                'deep_dive':state.scratch.get('deep_dive',{})}
    if key=='problem':
        return {'confirm':dump(state.confirm),'requirements':dump(state.constraints),
                'frame':dump(state.intake.frame),'scope':state.domain.problem_type}
    if key=='constraints':
        return {'requirements':dump(state.constraints),'results':[dump(x) for x in state.constraint_checks]}
    if key=='concepts':
        from .mode_contract import contract
        from .action_runtime import candidate_actions
        return {'candidates':[dump(x) for x in state.concepts],
                **({k:state.scratch[k] for k in ('candidate_review_revisions','candidate_dispositions') if k in state.scratch}),
                'candidate_actions':{c.id:candidate_actions(state,c) for c in state.concepts} if contract(state) else {},
                'action_results':state.scratch.get('ax_action_results',{}),
                'excluded':state.scratch.get('ax_excluded',[]),
                'baseline':state.scratch.get('ax_baseline_candidates',[]),
                'recovery':state.scratch.get('ax_recovery',[]),
                'rule_patches':state.scratch.get('ax_rule_patches',[])}
    if key=='evidence':
        return {'sources':[dump(x) for x in state.evidence],
                'mappings':state.scratch.get('evidence_mappings',{}),
                'gaps':state.scratch.get('evidence_gaps',[])}
    if key=='selection':
        return state.scratch.get('ax_selection',{'status':'NOT_RUN','candidates':[]})
    if key=='coherence':
        from .coherence import assess
        return assess(state)
    if key=='solve':
        return dict(dump(state.solve),effect_applicability=state.scratch.get('ax_effect_applicability',[]),
                    effect_applications=state.scratch.get('ax_effect_applications',[]),
                    raw_inventory=state.scratch.get('ax_idea_inventory', []),
                    action_results=state.scratch.get('ax_action_results', {}))
    value=getattr(state,key)
    return dump(value) if value is not None else {}


def descendants(keys):
    found=set(keys)
    while True:
        more={k for k,parents in DEPENDENCIES.items() if set(parents)&found}
        if more<=found:
            return found
        found|=more


def checkpoint(state,stage,*,interrupted=False):
    if not enabled(state):
        return
    from .mode_contract import contract
    if contract(state) and stage in ('s5_solve','s6_concept','s8_references'):
        from .effect_history import collect, gate_reviews
        if stage == 's5_solve':
            collect(state)
        else:
            gate_reviews(state, stage)
    keys=OUTPUTS.get(stage,())
    sections={key:section(state,key) for key in keys}
    # Remove dependent members whenever a producer is rerun, even if text repeats.
    invalidated=descendants(keys)-set(keys)
    if stage=='s10_feedback':
        invalidated=set()
    if stage=='s8_evaluate' and not interrupted:
        from .validation import selection
        state.scratch['ax_selection']=selection(state)
        sections['selection']=state.scratch['ax_selection']
    from .coherence import enabled as coherence_enabled
    if coherence_enabled(state) and set(keys)&{'definition','concepts','constraints','evaluation'}:
        state.scratch['ax_coherence']=section(state,'coherence')
        # Capture producer versions first; selection reads this exact coherence version.
        selection_payload=sections.pop('selection',None)
        sections['coherence']=state.scratch['ax_coherence']
        if selection_payload is not None:
            sections['selection']=selection_payload
    for key,label,stages in GATES:
        if stage in stages:
            gates=state.scratch['ax_gates']
            if interrupted:
                gates[key]={'label':label,'status':'WAITING' if state.pending else 'INTERRUPTED'}
            elif stage==stages[-1] or (key=='G4' and stage=='s9_report'):
                status='PASS'
                if key=='G1' and not state.confirm.user_confirmed:
                    status='CONDITIONAL'
                if key=='G2' and not (state.definition.technical_contradictions or state.definition.physical_contradictions):
                    status='CONDITIONAL'
                if key=='G3' and (not state.concepts or any(c.quality_status!='PASS' or
                    not state.check_for(c.id) or state.check_for(c.id).verdict!='PASS' for c in state.concepts)):
                    status='CONDITIONAL'
                if key=='G4':
                    status='PASS' if state.scratch.get('ax_selection',{}).get('recommended') else 'CONDITIONAL'
                gates[key]={'label':label,'status':status}
            else:
                gates[key]={'label':label,'status':'RUNNING'}
    ledger.capture(state,sections,DEPENDENCIES,stage+(':interrupted' if interrupted else ''),invalidated=invalidated)
    from .mode_contract import adaptive
    if adaptive(state) and stage=='s9_report' and not interrupted:
        from .action_runtime import emit, episode
        emit(state,'ADAPTIVE_EPISODE_CLOSED',dict(semantic_episode_id=episode(state),
            candidate_ids=sorted(c.id for c in state.concepts), terminal_decision_id=state.scratch.get('ax_optional_previous'),
            report_snapshot_id=state.scratch['ax_snapshot_id']))
    if contract(state):
        from .action_runtime import emit
        for aid,result in state.scratch.get('ax_action_results',{}).items():
            outputs=[]
            if 'solve' in keys and result.get('produced_raw_idea_ids'):
                outputs.append(state.scratch['ax_members']['solve'])
            if 'concepts' in keys and result.get('candidate_ids'):
                outputs.append(state.scratch['ax_members']['concepts'])
            if outputs:
                emit(state,'ACTION_OUTPUT_LINKED',dict(action_instance_id=aid,output_version_ids=outputs,
                    parent_action_instance_ids=result.get('parent_action_instance_ids',[])))


def before_stage(ctx,key):
    if not enabled(ctx.state):
        return
    state=ctx.state
    h=ledger.head(state.run_id)
    if h['epoch']!=state.scratch.get('execution_epoch',0):
        raise Conflict('Execution no longer owns this epoch')
    if h['bundle']['bundle_id']!=state.scratch['ax_bundle']['bundle_id']:
        raise Conflict('Execution bundle changed')
    # Resuming pins a new epoch to the unchanged immutable inputs before dispatch.
    ledger.capture(state,{},DEPENDENCIES,'stage_read_set')
    if key=='s5_solve':
        from .coordinator import route
        route(ctx)
    if key=='s6_concept':
        from .coordinator import stage_action
        stage_action(state,'CHECK_APPLICABILITY','solve')
        state.scratch['ax_effect_applicability']=[{
            'id':'app-'+digest(a)[:24],'source_effect_id':a.get('source_effect_id'),
            'required_function':a.get('catalog_function',''),
            'mechanism':a.get('principle',''),'conditions':a.get('conditions',[]),
            'sources':a.get('catalog_sources',[]),'status':'UNKNOWN',
            'reason':'정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음',
            'validation_obligations':['운전 범위와 자원 충족 확인','효과와 후보 기구 연결 확인']}
            for a in state.solve.effect_apps]
        from .mode_contract import contract
        if contract(state):
            from .effect_history import collect
            apps=collect(state)
            state.scratch['ax_effect_applicability'] = [dict(id=a['application_id'],source_effect_id=a['effect_id'],
                required_function=a['intended_function'],mechanism=a['applied_mechanism'],
                conditions=[c['text'] for c in a['conditions']],status='UNKNOWN',sources=[],
                reason='조건과 구현 연결은 개념 검토 대상이며 실증을 뜻하지 않습니다.',
                validation_obligations=['운전 조건 확인','원래 모순 양측의 독립 검토']) for a in apps]
        ledger.capture(state,{'solve':section(state,'solve')},DEPENDENCIES,'effect_applicability')
    if key=='s8_references':
        from .coherence import enabled as coherence_enabled
        from .mode_contract import adaptive
        if adaptive(state):
            from .adaptive_tracks import followup
            if state.scratch.get('adaptive_gate_pending_ids') and (state.scratch.get('resume_payload') or state.scratch.get('ax_gate_response_pending')):
                from ..nodes import s7_gate
                s7_gate(ctx)
                checkpoint(state,'s7_gate')
            added=followup(ctx,'after_constraints')
            if added:
                from ..nodes import s7_gate
                s7_gate(ctx)
                checkpoint(state,'s7_gate')
        elif coherence_enabled(state):
            from . import recovery
            added=recovery.run(ctx,phase='after_constraints')
            if added:
                # Recheck only new candidates; never clear approvals/checks on the baseline.
                from ..context import RunContext
                from ..nodes import s7_gate
                branch=state.model_copy(deep=True)
                branch.concepts=[c for c in branch.concepts if c.id in added]
                branch.constraint_checks=[]
                branch.scratch['ax_autonomous_gate']=True
                branch.steps,branch.cost,branch.control=state.steps,state.cost,state.control
                child=RunContext(branch)
                child.lock,child.budget,child.call_slots=ctx.lock,ctx.budget,ctx.call_slots
                child.persist=ctx.persist
                s7_gate(child)
                state.concepts=[c for c in state.concepts if c.id not in added]+branch.concepts
                state.constraint_checks.extend(branch.constraint_checks)
                for name in ('excluded_concepts','ax_excluded','ax_constraint_failures'):
                    if name in branch.scratch:
                        state.scratch[name]=branch.scratch[name]
                checkpoint(state,'s7_gate')
        from .coordinator import stage_action
        stage_action(state,'FETCH_EVIDENCE','concepts')
    if key=='s7_gate' and not state.scratch.get('resume_payload') and not state.scratch.get('ax_gate_response_pending'):
        from . import recovery,rules
        from .mode_contract import adaptive
        if adaptive(state):
            from .adaptive_tracks import followup
            followup(ctx,'after_concepts')
        else:
            recovery.run(ctx)
        rules.apply(state)
    if key=='s9_report':
        from .mode_contract import contract
        from .mode_contract import adaptive
        if contract(state) and not adaptive(state) and state.scratch.get('ax_optional_previous'):
            from .action_runtime import emit, episode
            emit(state,'OPTIONAL_TRANSITION',dict(semantic_episode_id=episode(state),
                decision_id=state.scratch['ax_optional_previous'],next_decision_id=None,terminal_reason='OPTIONAL_PHASES_COMPLETED'))
            state.scratch.pop('ax_optional_previous',None)
        from .validation import selection
        from .coherence import enabled as coherence_enabled
        if coherence_enabled(state):
            state.scratch['ax_coherence']=section(state,'coherence')
            ledger.capture(state,{'coherence':state.scratch['ax_coherence']},DEPENDENCIES,'final_coherence')
        state.scratch['ax_selection']=selection(state)
        ledger.capture(state,{'selection':state.scratch['ax_selection']},DEPENDENCIES,'report_selection')
        from .report import context
        ledger.capture(state,{'report_context':context(state)},DEPENDENCIES,'report_context')
        state.scratch['ax_report_snapshot_id']=state.scratch['ax_snapshot_id']
        from .coordinator import stage_action
        stage_action(state,'FINALIZE' if state.scratch['ax_selection']['recommended'] else 'DEFER','selection')


def render_prompt(state,prompt_id,**values):
    if not enabled(state):
        return prompts_registry.render(prompt_id,**values)
    pinned=state.scratch['ax_bundle']['prompts']
    # The new mandatory Part6 is the only explicitly allowed missing-prompt fallback.
    body=(prompts_registry.raw(prompt_id) if prompt_id=='P_S5_ARIZ_PART6' and prompt_id not in pinned
          else pinned[prompt_id])
    body=prompts_registry.compatible_body(prompt_id,body)
    return prompts_registry.VAR.sub(lambda m:prompts_registry._stringify(values.get(m.group(1),'')),body)


def effect_candidates(state,required,limit=6):
    if not enabled(state):
        return knowledge.effect_candidates(required,limit)
    from ..effect_catalog import select_effects
    b=state.scratch['ax_bundle']
    allowed={'INFORMATIONAL'} if state.domain.problem_type=='INFORMATION_SOFTWARE' else None
    if state.domain.problem_type=='ORGANIZATIONAL_BUSINESS':
        allowed={'INFORMATIONAL'}
    groups=[dict(g,effects=[dict(b['effect_sources'].get(e['id'],{}),**e) for e in g['effects']
        if allowed is None or e.get('domain') in allowed]) for g in b['effects']]
    from .coherence import enabled as coherence_enabled
    from .effect_history import rerank
    if not coherence_enabled(state) or len(required)<2:
        return rerank(state, select_effects(groups,required,limit=limit*4), required)
    # Global catalog access per function prevents a common function swallowing
    # a less common one; industry names never restrict eligible effects.
    pools=[select_effects(groups,[function],limit=limit*4) for function in required]
    output=[]; seen=set()
    for rank in range(limit*4):
        for pool in pools:
            if rank<len(pool) and pool[rank]['id'] not in seen:
                output.append(pool[rank]); seen.add(pool[rank]['id'])
                if len(output)>=limit*4:
                    return rerank(state, output, required)
    return rerank(state, output, required)


def public_view(state):
    if not enabled(state):
        return None
    from .mode_contract import coverage, contract
    return {'workflow':state.scratch['workflow_version'],
            'run_contract':contract(state), 'mode_coverage':coverage(state),
            'diagnostics':diagnostics(state),
            'release_version':state.scratch['ax_bundle'].get('release_version',state.scratch['workflow_version']),
            'snapshot_id':state.scratch.get('ax_snapshot_id'),
            'epoch':state.scratch.get('execution_epoch',0),'gates':state.scratch.get('ax_gates',{}),
            'coordination':state.scratch.get('ax_coordination',{}),
            'coordinator_hitl':False,
            'selection':state.scratch.get('ax_selection',{}),
            'learning':{'policy_version':state.scratch['ax_bundle']['policy_version'],
                        'mode':'POLICY' if state.scratch['ax_bundle'].get('policy') else 'RULE_BASED',
                        'updates_apply_to':'next_run'},
            'report_snapshot_id':state.scratch.get('ax_report_snapshot_id')}


def diagnostics(state):
    """Read-only counts; no collection, training, mutation or prompt disclosure."""
    from .mode_contract import contract, coverage
    if not contract(state):
        return {}
    results=list(state.scratch.get('ax_action_results',{}).values())
    portfolio=state.scratch.get('idea_consolidation',{})
    bundle=state.scratch['ax_bundle']
    from .mode_contract import unified
    extra={}
    if unified(state):
        import json
        from collections import Counter
        from sqlalchemy import select
        from .feedback_events import KIND
        with ledger.store.engine.connect() as c:
            rows=[json.loads(r) for r in c.execute(select(ledger.events.c.payload).where(
                ledger.events.c.run_id==state.run_id,ledger.events.c.event_type==KIND)).scalars()]
        budget=ledger.budget(state.run_id,state.user_id)
        extra=dict(common_evaluation_count_by_source=dict(Counter(r['evaluation_stage'] for r in rows)),
            missing_or_rejected_label_reasons=dict(Counter('unobserved' if not r['observed_mask'] else 'no_training_consent'
                for r in rows if not r['observed_mask'] or r['training_consent_scope']=='NO_TRAINING')),
            candidate_to_action_effect_lineage_integrity=dict(Counter(r.get('attribution','UNKNOWN_ATTRIBUTION') for r in rows)),
            reward_contract=contract(state)['reward_contract'],actual_cost=budget['spent_microusd'],
            unresolved_reserve=budget['reserved_microusd'],remaining_budget=budget['remaining_microusd'],
            mandatory_review_reserve=bundle['limits']['validation_reserve_microusd'],
            live_quality_cost_evaluation='not_evaluated_live')
    return dict(feature_schema=bundle.get('feature_schema'),context_contract=bundle.get('context_contract'),
        cost_contract=bundle.get('cost_contract'),effect_evaluation_contract=(bundle.get('effect_ranker') or {}).get('evaluation_contract'),
        mode_coverage=coverage(state), raw_idea_count=len(state.scratch.get('ax_idea_inventory',[])),
        merged_family_count=len(state.solve.raw_ideas), detailed_candidate_count=len(state.concepts),
        final_count=len(state.scratch.get('ax_selection',{}).get('recommended',[])),
        unaccounted_raw_count=len(portfolio.get('unaccounted_idea_ids',[])),
        uncovered_obligation_count=len(state.scratch.get('ax_coherence',{}).get('coverage_gaps',[])),
        mandatory_actions=sum(not r['optional'] for r in results), optional_actions=sum(r['optional'] for r in results),
        unknown_usage_actions=sum(r.get('usage_status')=='UNKNOWN' for r in results),
        policy_usage=state.scratch.get('ax_policy_usage',{'selection_mode':'NOT_USED'}),
        effect_applications=len(state.scratch.get('ax_effect_applications',[])),
        effect_history_hits=sum(e.get('independent_runs',0)>0 for sel in state.scratch.get('ax_effect_selections',{}).values() for e in sel['candidates']),
        effect_ranker_version=bundle.get('effect_ranker_version'),
        routing_mode=contract(state)['routing_policy_mode'],effect_mode=contract(state)['effect_reranking_mode'],
        routing_readiness='DEPLOYED' if bundle.get('policy') else 'SHADOW' if bundle.get('shadow_policy') else 'COLLECTING',
        effect_readiness='DEPLOYED' if bundle.get('effect_ranker') else 'SHADOW' if bundle.get('shadow_effect_ranker') else 'COLLECTING', **extra)
