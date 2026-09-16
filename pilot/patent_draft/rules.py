"""Code invariants and full role-specific criteria; absent evidence remains UNKNOWN."""
import json
from pathlib import Path
from .domain import ClaimTree, Invention, DocumentAST, DrawingSpec, ROLES, SCOPE, PROFILE, digest
from .models import balance
from .forms import SECTIONS, requirements

PACK = json.loads((Path(__file__).with_name('config') / 'rules.json').read_text(encoding='utf-8'))
RULES = {r['rule_id']: r for r in PACK['rules']}


def obligations(role):
    return [r for r in RULES.values() if role in r['semantic_roles'] or role == 'GLOBAL_FINAL']


def valid(schema, value):
    if value is None:
        return None
    try:
        schema.model_validate(value)
        return True
    except (ValueError, TypeError):
        return False


def applicability(rule_id, case, material):
    """False is allowed only for confirmed absence or an optional product feature."""
    logic = RULES[rule_id]['applicability']['logic']
    facts = material.get('facts', {})
    if logic == 'always':
        return True
    if logic == 'software_or_ai_profile':
        return True if case['profile'] == 'KR_SOFTWARE_AI' else facts.get('software_or_ai')
    if logic == 'materials_chemical_process_or_special_domain':
        return True if case['profile'] in ('KR_MATERIAL_PROCESS','KR_SPECIAL_TRIAGE') else facts.get('materials_or_special_domain')
    if logic == 'conditional_filing_fact_relevant':
        keys = ('agent','priority','disclosure_exception','sequence','deposit','assignment')
        return True if any(facts.get(k) is True for k in keys) else False if all(facts.get(k) is False for k in keys) else None
    if logic == 'drawing_required_or_present':
        if material.get('drawings', {}).get('drawings'):
            return True
        return facts.get('drawings_required')
    if logic == 'advisory_requested_or_business_input_present':
        return 'economics' in material or bool(facts.get('business_review_requested'))
    if logic == 'rl_enabled_or_feedback_collected_or_training_claimed':
        return case.get('learning_status') != 'DISABLED'
    raise ValueError('Unimplemented applicability: '+logic)


def multiple_dependencies(claims):
    by_number = {c['number']: c for c in claims}
    def ancestors(number, seen):
        if number in seen or number not in by_number:
            return set()
        parent = by_number[number]
        result = set(parent['depends_on'])
        for n in parent['depends_on']:
            result |= ancestors(n, seen | {number})
        return result
    for claim in claims:
        if len(claim['depends_on']) > 1:
            if not claim.get('multiple_dependency_mode'):
                return None
            if claim['multiple_dependency_mode'] != 'ALTERNATIVE':
                return False
            if any(len(by_number[n]['depends_on']) > 1 for n in ancestors(claim['number'], set())):
                return False
    return True


def checks(case, material, reviews, runtime):
    """runtime is constructed by server from ACL, storage, tickets and observations."""
    inv, clm, doc, draw = (material.get(x) for x in ('invention', 'claims', 'specification', 'drawings'))
    search = material.get('sources')
    feature_ids = {f['id'] for f in (inv or {}).get('features', [])}
    sections = {s['id']: s for s in (doc or {}).get('sections', [])}
    claims = (clm or {}).get('claims', [])
    drawings = (draw or {}).get('drawings', [])
    approvals = runtime.get('approvals', {})
    ledger = case['budget']
    observations = {
        'SEC01': runtime.get('acl_verified'), 'SEC02': case.get('visibility') == 'PRIVATE',
        'SEC03': case.get('scope_policy_version') == SCOPE,
        'SEC04': bool(case.get('provider_authorization')),
        'SEC05': runtime.get('untrusted_context_enforced'), 'SEC06': runtime.get('public_cache_isolated'),
        'TECH02': valid(Invention, inv),
        'SEARCH01': None if not search else bool(search.get('diagnostics')),
        'SEARCH03': None if not search else search.get('status') in ('OK', 'EMPTY', 'PARTIAL', 'UNAVAILABLE'),
        'SEARCH05': None if not search else all(h.get('publication_number') and h.get('publication_date') and h.get('kind_code') for h in search.get('hits', [])) if search.get('hits') else None,
        'SEARCH08': runtime.get('source_parse_verified'), 'SEARCH09': runtime.get('targeted_enrichment_only'),
        'SEARCH10': None if not search else search.get('fto_performed') is False,
        'PAT05': case.get('inherited_legal_verdict') is None,
        'CLM04': valid(ClaimTree, clm),
        'CLM05': None if not clm else multiple_dependencies(claims) if valid(ClaimTree, clm) else False,
        'CLM06': valid(ClaimTree, clm),
        'CLM09': None if not clm else approvals.get('G2') == digest(clm),
        'SPEC07': None if not doc else set(SECTIONS) <= sections.keys() and all(s.get('text') or s.get('omission_reason') for s in sections.values()),
        'DRAW03': None if not draw or not inv else all(n.get('feature_id') in feature_ids for d in drawings for n in d['nodes']) if drawings else bool(draw.get('not_required_reason')),
        'DRAW04': None if not draw else all(d.get('kind') in ('CONCEPT', 'FILING_CANDIDATE') for d in drawings),
        'DRAW06': None if not draw or not doc else bool(sections.get('drawing_description', {}).get('text') or draw.get('not_required_reason')),
        'OPS01': all(case.get(k) for k in ('source_hash', 'rulepack_version', 'policy_version', 'form_version', 'model_profile')),
        'OPS02': False if any(valid(s,m) is False for s,m in ((Invention,inv),(ClaimTree,clm),(DocumentAST,doc),(DrawingSpec,draw)))
            else None if any(m is None for m in (inv,clm,doc,draw)) else True,
        'OPS03': runtime.get('ticket_fence_verified'),
        'OPS04': all(type(ledger.get(k)) is int and ledger[k] >= 0 for k in ('cap_micro_usd','spent_micro_usd','reserved_micro_usd','uncertain_micro_usd','review_plan_micro_usd')) and balance(ledger) >= 0,
        'OPS05': runtime.get('review_conflicts_preserved'), 'OPS06': runtime.get('readset_invalidation'),
        'OPS07': None if 'questions' not in material else all(q.get('reason') and q.get('affected_fields') for q in material['questions'].get('questions', [])),
        'OPS08': all(k in case for k in ('execution_status','document_status','evidence_status','editor_validation')),
        'OPS09': None if not doc else {'form14','form15','form16','form17'} <= {r['id'] for r in requirements(material.get('facts', {}))},
        'OPS10': case.get('editor_validation') in ('NOT_RUN','FAILED','PASSED') and not case.get('submission_file_created', False),
        'OPS11': runtime.get('export_manifest_bound'),
        'ECO01': None if 'economics' not in material else valid(__import__('patent_draft.domain', fromlist=['Economics']).Economics, material['economics']),
        'ECO02': None if 'economics' not in material else bool(material['economics'].get('limitations')),
        'ECO03': runtime.get('economics_internal_only'),
        'CMP01': runtime.get('schema_preservation_verified'), 'CMP02': runtime.get('legacy_readonly'),
        'CMP03': case.get('legacy_adapter') == 'READ_ONLY_NO_GATE_EQUIVALENCE',
        'CMP04': case.get('model_profile') == PROFILE, 'CMP05': runtime.get('dispatch_flag_checked'),
        'MCP01': runtime.get('mcp_contracts_registered'), 'MCP02': runtime.get('ticket_fence_verified'),
        'MCP03': case.get('filing_status') == 'NOT_FILED',
        'MOD01': None if not case.get('model_config') else all(t in case['model_config'] for t in ('T1','T2','T3')) and case['model_config']['T3']['reasoning'],
        'MOD02': runtime.get('independent_reviews'), 'MOD03': runtime.get('global_coverage'),
        'CON01': runtime.get('ticket_fence_verified'), 'CON02': runtime.get('readset_invalidation'),
        'CON03': runtime.get('review_conflicts_preserved'), 'CON04': runtime.get('patch_provenance'),
        'RL01': case.get('policy_version') == case.get('initial_policy_version'),
        'RL02': runtime.get('safe_action_mask'), 'RL03': runtime.get('feedback_maturity'),
        'RL04': case.get('learning_status') in ('TELEMETRY_ONLY','ADAPTER_READY','TRAINING_VERIFIED'),
        'CST01': case.get('review_plan_reserved', False), 'CST02': ledger.get('uncertain_micro_usd', -1) >= 0,
        'DAT01': runtime.get('public_cache_isolated'),
    }
    output = []
    for rule_id, rule in RULES.items():
        applies = applicability(rule_id, case, material)
        roles = rule['semantic_roles']
        findings = [f for r in reviews if r.get('role') in roles for f in r.get('findings', []) if f['rule_id'] == rule_id]
        if applies is False:
            outcome, execution = 'NOT_APPLICABLE', 'SUCCEEDED'
        elif applies is None:
            covered = {r['role'] for r in reviews if any(f['rule_id'] == rule_id for f in r.get('findings', []))}
            outcome = 'UNKNOWN'
            execution = 'SUCCEEDED' if not roles or set(roles) <= covered else 'NOT_RUN'
        elif roles:
            covered = {r['role'] for r in reviews if any(f['rule_id'] == rule_id for f in r['findings'])}
            outcome = 'FAIL' if any(f['outcome'] == 'FAIL' for f in findings) else 'UNKNOWN' if not set(roles) <= covered or any(f['outcome'] == 'UNKNOWN' for f in findings) else 'PASS' if all(f['outcome'] == 'PASS' for f in findings) else 'NOT_APPLICABLE'
            execution = 'SUCCEEDED' if set(roles) <= covered else 'NOT_RUN'
        elif rule_id not in observations:
            outcome, execution = 'UNKNOWN', 'ERROR'
        else:
            value = observations[rule_id]
            outcome = 'UNKNOWN' if value is None else 'PASS' if value else 'FAIL'
            execution = 'SUCCEEDED'
        output.append({'rule_id': rule_id, 'execution_status': execution, 'outcome': outcome,
                       'severity': rule['severity'], 'criterion': rule['criterion'],
                       'required_evidence': rule['required_evidence'], 'applicability': applies,
                       'not_applicable_reason': ('확인된 사건 사실 또는 요청하지 않은 선택 기능에 따라 적용 대상이 아닙니다.' if applies is False else None),
                       'error_code': 'CONFIGURATION_ERROR' if execution == 'ERROR' else None})
    return output
