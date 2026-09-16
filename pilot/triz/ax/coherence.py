"""Versioned semantic obligations; structural checks never certify physics."""
from typing import Literal
from pydantic import Field, ValidationError
from .contracts import Contract, digest

VERSION = 'coherence-v1'


def enabled(state):
    return state.scratch.get('ax_bundle', {}).get('coherence_contract') == VERSION


class Condition(Contract):
    source_idea_id: str
    condition: str = Field(min_length=1)
    applicability: str = Field(min_length=1)


class Claim(Contract):
    text: str = Field(min_length=1)
    status: Literal['HYPOTHESIS', 'DERIVED', 'USER_REPORTED', 'OBSERVED'] = 'HYPOTHESIS'
    source_cause_id: str = ''
    evidence_refs: list[str] = []


class Mechanism(Contract):
    intervention: str = Field(min_length=1)
    target: str = Field(min_length=1)
    changed_variable: str = Field(min_length=1)
    mediating_functions: list[str] = Field(min_length=1)
    outcome: str = Field(min_length=1)
    operating_scope: str = Field(min_length=1)
    contribution: Literal['DIRECT', 'ENABLER', 'MONITOR_ONLY', 'PASSIVE_MITIGATION'] = 'DIRECT'
    control_mode: Literal['ACTIVE', 'PASSIVE', 'DIAGNOSTIC'] = 'PASSIVE'
    control_chain: dict[str, str] = {}
    conditions: list[Condition] = []
    claims: list[Claim] = []


def obligations(state):
    """Derived physical contradictions share the parent obligation, not its count."""
    rows = []
    technical = {t.id: t for t in state.definition.technical_contradictions}
    for t in technical.values():
        rows.append({'id': t.id, 'contradiction_ids': [t.id], 'description': t.label or t.if_action,
                     'improve': t.then_good, 'protect': t.but_bad,
                     'requirement_hash': digest(state.constraints.model_dump(mode='json'))})
    by_id = {r['id']: r for r in rows}
    for p in state.definition.physical_contradictions:
        if p.derived_from_tc_id in by_id:
            by_id[p.derived_from_tc_id]['contradiction_ids'].append(p.id)
        else:
            rows.append({'id': p.id, 'contradiction_ids': [p.id],
                         'description': p.label or f'{p.element}: {p.parameter}',
                         'improve': f'{p.state_a} — {p.reason_a}', 'protect': f'{p.state_b} — {p.reason_b}',
                         'requirement_hash': digest(state.constraints.model_dump(mode='json'))})
    return rows


def contract_instruction(state):
    if not enabled(state):
        return ''
    import json
    return '\n'.join([
        '각 concept에 coherence 객체를 추가한다. 아래 스키마를 따른다. 구조 존재는 실증이 아니다.',
        json.dumps(Mechanism.model_json_schema(), ensure_ascii=False),
        '원래 문제의 의무: ' + json.dumps(obligations(state), ensure_ascii=False),
        'validation_plan 각 항목에 obligation_refs:[{contradiction_id:실제 모순 ID,side:IMPROVE 또는 PROTECT}]를 명시한다.',
        '연결한 모순의 양측을 모두 포함하고 metric/experiment/success_criterion/failure_criterion을 구체화한다. 시험 개수로 자르지 않는다.',
        '능동 제어를 주장할 때 control_chain에 sensor,estimator,decision,actuator,target을 모두 명시한다. 수동/진단안에는 강제하지 않는다.',
        'conditions는 출처 아이디어 ID와 이 후보에 적용되는 이유를 명시한다. 다른 후보의 조건을 복사하지 않는다.',
        '출처 아이디어의 conditions는 빠짐없이 대응시킨다. condition에는 제공된 조건 원문을 그대로 쓰고, 해석·확인 방법은 applicability에 쓴다.',
        '미확인 조건도 삭제하지 않는다. applicability에 현장 확인·시험 방법을 적고 확인 완료를 주장하지 않는다.',
        '통합 아이디어의 source_details에 있는 원본 source_idea_id는 그 원본 조건에 한해 참조할 수 있다.',
        '사용자의 문제 제기·진술은 USER_REPORTED다. 제목이나 confirmed_facts라는 필드 이름만으로 OBSERVED로 올리지 않는다.',
        '관측 인용이 가능한 원인 노드: ' + json.dumps([n.model_dump(mode='json') for n in state.analysis.ceca.nodes
            if n.evidence_status=='OBSERVED' and n.evidence_refs] if state.analysis.ceca else [],ensure_ascii=False),
        '새 원인·효과 주장은 HYPOTHESIS다. OBSERVED는 제공된 원인 노드의 관측 내용과 근거를 그대로 인용할 때만 허용한다.',
        '정보 변화에서 물리 성능으로 넘어가는 매개 기능, 운전 범위와 원래 악화측을 피하는 경로를 빠뜨리지 않는다.'
    ])


def candidate_check(state, candidate, required=None):
    required = required if required is not None else obligations(state)
    related = [o for o in required if set(o['contradiction_ids']) & set(candidate.addresses_contradictions)]
    gaps = []
    def gap(kind, text, refs=None):
        gaps.append({'kind': kind, 'description': text, 'obligation_ids': refs or [o['id'] for o in related]})
    raw = state.scratch.get('ax_mechanisms', {}).get(candidate.id)
    mechanism = None
    try:
        mechanism = Mechanism.model_validate(raw)
    except (ValidationError, TypeError):
        gap('MISSING_TRANSFER_PATH', '개입·물리량·매개 기능·운전 조건의 연결 기록 누락')
    if not related:
        gap('COVERAGE_GAP', '원래 핵심 문제와 연결되지 않은 후보')
    bindings = set()
    if not candidate.validation_plan:
        gap('INCOMPLETE_TEST_PLAN', '검증계획 미작성')
    aliases = {cid: o['id'] for o in required for cid in o['contradiction_ids']}
    for plan in candidate.validation_plan:
        if not all(str(plan.get(k, '')).strip() for k in ('metric', 'experiment', 'failure_criterion')) or not (plan.get('success_criterion') or plan.get('target')):
            gap('INCOMPLETE_TEST_PLAN', '측정 지표·실험·성공·반증 기준 보완 필요')
            continue
        for ref in plan.get('obligation_refs', []):
            if isinstance(ref, dict) and ref.get('contradiction_id') in aliases and ref.get('side') in ('IMPROVE', 'PROTECT'):
                bindings.add((aliases[ref['contradiction_id']], ref['side']))
    for obligation in related:
        for side in ('IMPROVE', 'PROTECT'):
            if (obligation['id'], side) not in bindings:
                gap('ADVERSE_SIDE_OMITTED' if side == 'PROTECT' else 'IMPROVEMENT_SIDE_OMITTED',
                    f"{obligation['description']} — {'악화 방지측' if side == 'PROTECT' else '개선측'} 검증계획 연결 누락", [obligation['id']])
    if mechanism:
        if mechanism.control_mode == 'ACTIVE' and not all(mechanism.control_chain.get(k, '').strip()
                for k in ('sensor', 'estimator', 'decision', 'actuator', 'target')):
            gap('MISSING_ACTUATION', '능동 제어의 감지→추정→판단→구동→대상 경로 누락')
        source_conditions={}
        for idea in state.solve.raw_ideas:
            if idea.id not in candidate.source_idea_ids:
                continue
            source_conditions.setdefault(idea.id,set()).update(c.strip() for c in idea.conditions)
            for detail in idea.detail.get('source_details',[]):
                if detail.get('source_idea_id'):
                    source_conditions.setdefault(detail['source_idea_id'],set()).update(c.strip() for c in detail.get('conditions',[]) if isinstance(c,str))
        for condition in mechanism.conditions:
            if (condition.source_idea_id not in candidate.source_idea_ids and
                    condition.condition.strip() not in source_conditions.get(condition.source_idea_id,set())):
                gap('CONDITION_SCOPE_LEAK', '다른 아이디어의 적용 조건 혼입')
        scoped={(c.source_idea_id,c.condition.strip()) for c in mechanism.conditions}
        for idea in state.solve.raw_ideas:
            if idea.id in candidate.source_idea_ids:
                for condition in idea.conditions:
                    ancestors={idea.id}|{d.get('source_idea_id') for d in idea.detail.get('source_details',[])}
                    if not any((owner,condition.strip()) in scoped and condition.strip() in source_conditions.get(owner,set()) for owner in ancestors):
                        gap('CONDITION_SCOPE_UNCONFIRMED', f'원리 적용 조건의 후보 내 성립 경로 확인 필요: {condition}')
        causes = {c.id: c for c in state.analysis.ceca.nodes} if state.analysis.ceca else {}
        for claim in mechanism.claims:
            if claim.status != 'OBSERVED':
                continue
            cause = causes.get(claim.source_cause_id)
            if (not cause or cause.evidence_status != 'OBSERVED' or claim.text != cause.text
                    or not claim.evidence_refs or not set(claim.evidence_refs) <= set(cause.evidence_refs)):
                gap('UNSUPPORTED_CAUSE', '새 근거 없이 원인 가설을 관측 사실로 승격할 수 없음')
    support=[]
    for idea in state.solve.raw_ideas:
        if idea.id not in candidate.source_idea_ids:
            continue
        for detail in [idea.detail]+idea.detail.get('source_details',[]):
            if detail.get('source_effect_id'):
                support.append({k:detail[k] for k in ('source_effect_id','catalog_function','catalog_conditions',
                    'catalog_limitations','catalog_sources','principle','transformation') if k in detail})
    return {'candidate_id': candidate.id, 'obligation_ids': [o['id'] for o in related],
            'candidate_hash': digest(candidate.model_dump(mode='json')),
            'source_effects':support,
            'mechanism': mechanism.model_dump(mode='json') if mechanism else None,
            'gaps': gaps, 'structural_status': 'INCOMPLETE' if gaps else 'COMPLETE',
            'concept_review': candidate.quality_status,
            'test_preparation': 'INCOMPLETE' if any('SIDE_OMITTED' in g['kind'] or g['kind'] == 'INCOMPLETE_TEST_PLAN' for g in gaps) else 'PREPARED'}


def assess(state):
    required = obligations(state)
    rows = [candidate_check(state, c, required) for c in state.concepts]
    covered = set()
    for row in rows:
        check = state.check_for(row['candidate_id'])
        if (row['mechanism'] and row['mechanism']['contribution'] in ('DIRECT', 'PASSIVE_MITIGATION')
                and not row['gaps'] and row['concept_review'] == 'PASS' and (not check or check.verdict != 'FAIL')):
            covered.update(row['obligation_ids'])
    uncovered = [dict(o, kind='COVERAGE_GAP', obligation_id=o['id']) for o in required if o['id'] not in covered]
    target = state.scratch['ax_bundle']['limits'].get('presentation_target', 5)
    return {'contract': VERSION, 'obligations': required, 'candidates': rows, 'coverage_gaps': uncovered,
            'scope_status': 'COVERED_AT_CONCEPT_LEVEL' if required and not uncovered else 'PARTIAL',
            'presentation_target': target, 'retained_count': len(rows),
            'shortfall': max(0, target-len(rows)), 'display_limit': None,
            'note': '후보별 대응 범위의 합집합이며 결합 설계의 호환성이나 실제 실증을 의미하지 않는다.'}
