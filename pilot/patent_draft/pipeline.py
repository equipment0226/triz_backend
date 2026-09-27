"""Checkpointed Patent stages and Gates, shared by local, n8n and MCP execution."""
from sqlalchemy import select
from .repository import tasks
from .domain import digest, ROLES
from .intake import complete as intake_complete, unanswered
from . import workflow


def advance(service, c, owner, case):
    if case['execution_status'] not in ('QUEUED','RUNNING','WAITING_HUMAN'):
        return
    service.retire_stale_queued(c, case)
    if c.execute(select(tasks.c.task_id).where(tasks.c.case_id == case['case_id'], tasks.c.status.in_(['QUEUED','RUNNING']))).first():
        return
    material = service.material(owner, case, c)
    if material.get('evidence_clarification'):
        case['execution_status'],case['waiting_for']='WAITING_HUMAN','EVIDENCE_CLARIFICATION'
        return
    approvals = service.approvals(owner, case, c)
    if not intake_complete(material):
        case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'APPLICATION_CONTEXT'
        return
    if unanswered(material):
        case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'QUESTIONS'
        return
    sequence = workflow.drafting_nodes(material, ('P1','P2'))
    for kind, operation in sequence:
        if kind not in material:
            service.issue(c, case, operation)
            case['execution_status'] = 'QUEUED'
            return
    if not workflow.automatic(case) and approvals.get('G1') != digest(material['invention']):
        case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'G1'
        return
    if not workflow.automatic(case) and 'claims' not in material:
        service.issue(c, case, 'patent_draft_claims')
        return
    if not workflow.automatic(case) and approvals.get('G2') != digest(material['claims']):
        case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'G2'
        return
    for kind, operation in workflow.drafting_nodes(material, ('P3',)):
        if kind not in material:
            service.issue(c, case, operation)
            return
    if workflow.automatic(case) and 'document_coherence' not in material:
        service.issue(c, case, 'patent_review_document_flow')
        return
    if workflow.automatic(case) and 'report' not in material:
        service.issue(c, case, 'patent_render_report')
        return
    current = {r['role']: r for r in service.current_reviews(owner, case, c)}
    from .coverage import delivery_scope
    scope=delivery_scope(case,material)
    if not any(r.get('scope')==scope for r in service.repo.records(owner,case['case_id'],'delivery_scope',c)):
        service.repo.append(c,case['case_id'],'delivery_scope',{'scope':scope,'content_manifest_hash':digest(scope)})
    for role in ROLES[:2]:
        if role not in current:
            service.issue(c, case, 'patent_review_content', role)
            return
    issues = [f for r in service.current_reviews(owner, case, c) if r['role'] in ROLES
              for f in r['findings'] if f['outcome'] in ('FAIL','UNKNOWN')]
    issues.extend({'rule_id':'DOCUMENT_COHERENCE','outcome':f['outcome'],
                   'explanation':f['explanation'], 'repair_instruction':f['repair_instruction'],
                   'affected_artifacts':[case['artifacts']['document_coherence']]}
                  for f in material.get('document_coherence',{}).get('checks',[]) if f['outcome']!='PASS')
    issues.extend({'rule_id':'CONTENT_TARGET','outcome':f['outcome'],
                   'explanation':f['explanation'],'target_id':f['target_id'],
                   'affected_artifacts':r['covered_artifact_ids']}
                  for r in service.current_reviews(owner,case,c) if r['role'] in ROLES
                  for f in r.get('target_checks',[]) if f['outcome'] in ('FAIL','UNKNOWN'))
    if issues:
        if case['repair_rounds'] < 2:
            service.issue(c, case, 'patent_reconcile_issues', payload={'issues': issues})
            case['repair_rounds'] += 1
        else:
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'OPEN_ISSUES'
        return
    if 'GLOBAL_FINAL' not in current:
        service.issue(c, case, 'patent_final_review', 'GLOBAL_FINAL')
        return
    if workflow.automatic(case) and (approvals.get('G1') != digest(material['invention']) or approvals.get('G2') != digest(material['claims'])):
        case['document_status'] = 'DRAFT_WITH_OPEN_ISSUES'
        case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'FINAL_REVIEW'
        return
    checks = service.runtime_checks(owner, case, material, c)
    attachments_complete=all(d.get('parse_status')=='TEXT_EXTRACTED' for d in material.get('attachments',{}).get('documents',[]))
    ready = attachments_complete and all(r['outcome'] in ('PASS','NOT_APPLICABLE') for r in checks if r['severity'] == 'BLOCKER') and all(
        f['outcome'] in ('PASS','NOT_APPLICABLE') for r in service.current_reviews(owner, case, c)
        for f in [*r['findings'],*r.get('target_checks',[])])
    case['document_status'] = 'DRAFT_READY' if ready else 'DRAFT_WITH_OPEN_ISSUES'
    case['execution_status'] = 'COMPLETED' if ready else 'WAITING_HUMAN'
    case['waiting_for'] = None if ready else 'OPEN_ISSUES'
