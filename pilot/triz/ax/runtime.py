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
    's5_solve':('solve',), 's6_concept':('concepts',), 's7_gate':('concepts','constraints'),
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
          'rule_catalog':[], 'policy':None,
          'models':{t:{k:getattr(c,k) for k in MODEL_FIELDS} for t,c in settings.tiers.items()},
          'prompts':{p:prompts_registry.raw(p) for p in prompts_registry.list_prompts()},
          'effects':copy.deepcopy(knowledge.effects()),
          'effect_sources':copy.deepcopy(knowledge._load('effects_sources.json')),
          'config':copy.deepcopy(settings.triz),'rubrics':copy.deepcopy(settings.rubrics),
          'limits':{'branches':3,'recovery_targets':2,'repairs_per_blocker':2,'depth':2,
                    'validation_reserve_microusd':120000,'initial_candidates':12,'detailed_candidates':8,
                    'presentation_target':5,'recovery_additions':4,'expansion_rounds':1},
          'source_hashes':{str(p.relative_to(root.parent)).replace('\\','/'):digest(p.read_text(encoding='utf-8')) for p in
                           [root/'nodes.py',root/'quality.py',root/'verify.py',root/'render.py',
                            root/'ax/runtime.py',root/'ax/coordinator.py',root/'ax/coherence.py',
                            root/'ax/coherence_recovery.py',root/'ax/validation.py',root/'ax/report.py',
                            root/'ax/learning.py',root.parent/'templates/report_full.md.j2',
                            root.parent/'templates/report.html.j2',root.parent/'templates/report_ax_appendix.md.j2']}}
    if state is not None:
        from .registry import for_run
        data.update(for_run(state,feature_schema=data['feature_schema']))
    data['bundle_id']='bundle-'+digest(data)
    return data


def initialize(state):
    state.scratch['workflow_version']=WORKFLOW
    state.scratch['ax_bundle']=bundle(state)
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
        return {'candidates':[dump(x) for x in state.concepts],
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
        return dict(dump(state.solve),effect_applicability=state.scratch.get('ax_effect_applicability',[]))
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
        ledger.capture(state,{'solve':section(state,'solve')},DEPENDENCIES,'effect_applicability')
    if key=='s8_references':
        from .coherence import enabled as coherence_enabled
        if coherence_enabled(state):
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
    if key=='s7_gate' and not state.scratch.get('resume_payload'):
        from . import recovery,rules
        recovery.run(ctx)
        rules.apply(state)
    if key=='s9_report':
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
    body=state.scratch['ax_bundle']['prompts'][prompt_id]
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
    if not coherence_enabled(state) or len(required)<2:
        return select_effects(groups,required,limit=limit*4)
    # Global catalog access per function prevents a common function swallowing
    # a less common one; industry names never restrict eligible effects.
    pools=[select_effects(groups,[function],limit=limit*4) for function in required]
    output=[]; seen=set()
    for rank in range(limit*4):
        for pool in pools:
            if rank<len(pool) and pool[rank]['id'] not in seen:
                output.append(pool[rank]); seen.add(pool[rank]['id'])
                if len(output)>=limit*4:
                    return output
    return output


def public_view(state):
    if not enabled(state):
        return None
    return {'workflow':state.scratch['workflow_version'],
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
