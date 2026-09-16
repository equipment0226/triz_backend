"""Compatibility adapter: stable 13-stage workflow, versioned stage products."""
import copy
import os
from pathlib import Path
from .. import prompts_registry, knowledge
from ..settings import settings
from . import WORKFLOW, enabled
from . import ledger
from .contracts import digest, GATES, Conflict

DEPENDENCIES = {
    'input': (), 'problem': ('input',), 'analysis': ('problem',),
    'definition': ('problem','analysis'), 'solve': ('definition',),
    'concepts': ('solve','analysis'), 'constraints': ('problem','concepts'),
    'evidence': ('concepts',), 'evaluation': ('constraints','evidence'),
    'selection': ('evaluation','constraints','evidence'), 'report': ('selection',),
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
    data={'workflow':WORKFLOW,'coordinator_hitl':False,'policy_version':'rules-v1','feature_schema':'ax-features-v1',
          'action_catalog':'ax-actions-v1','rule_catalog_version':'empty-v1',
          'rule_catalog':[], 'policy':None,
          'models':{t:{k:getattr(c,k) for k in MODEL_FIELDS} for t,c in settings.tiers.items()},
          'prompts':{p:prompts_registry.raw(p) for p in prompts_registry.list_prompts()},
          'effects':copy.deepcopy(knowledge.effects()),
          'effect_sources':copy.deepcopy(knowledge._load('effects_sources.json')),
          'config':copy.deepcopy(settings.triz),'rubrics':copy.deepcopy(settings.rubrics),
          'limits':{'branches':3,'recovery_targets':2,'repairs_per_blocker':2,'depth':2,
                    'validation_reserve_microusd':60000,'initial_candidates':6,'detailed_candidates':3},
          'source_hashes':{p.name:digest(p.read_text(encoding='utf-8')) for p in
                           [root/'nodes.py',root/'quality.py',root/'verify.py']}}
    if state is not None:
        from .registry import for_run
        data.update(for_run(state))
    data['bundle_id']='bundle-'+digest(data)
    return data


def initialize(state):
    state.scratch['workflow_version']=WORKFLOW
    state.scratch['ax_bundle']=bundle(state)
    state.cost.budget_usd=float(state.scratch['ax_bundle']['config'].get('ax',{}).get('hard_budget_usd',1.0))
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
        from .coordinator import stage_action
        stage_action(state,'FETCH_EVIDENCE','concepts')
    if key=='s7_gate' and not state.scratch.get('resume_payload'):
        from . import recovery,rules
        recovery.run(ctx)
        rules.apply(state)
    if key=='s9_report':
        from .validation import selection
        state.scratch['ax_selection']=selection(state)
        ledger.capture(state,{'selection':state.scratch['ax_selection']},DEPENDENCIES,'report_selection')
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
    return select_effects(groups,required,limit=limit*4)


def public_view(state):
    if not enabled(state):
        return None
    return {'workflow':WORKFLOW,'snapshot_id':state.scratch.get('ax_snapshot_id'),
            'epoch':state.scratch.get('execution_epoch',0),'gates':state.scratch.get('ax_gates',{}),
            'coordination':state.scratch.get('ax_coordination',{}),
            'coordinator_hitl':False,
            'selection':state.scratch.get('ax_selection',{}),
            'learning':{'policy_version':state.scratch['ax_bundle']['policy_version'],
                        'mode':'POLICY' if state.scratch['ax_bundle'].get('policy') else 'RULE_BASED',
                        'updates_apply_to':'next_run'},
            'report_snapshot_id':state.scratch.get('ax_report_snapshot_id')}
