"""Focused independent checks after the general reviewer passes an analysis.

This module validates review coverage and quoted evidence, not TRIZ semantics.
The separate reasoning call must establish those semantics before PASS.
"""
from __future__ import annotations

import json
from collections.abc import Mapping

VERSION = 'focused-analysis-v1-20261009'
RULES = {
    'R3_FUNC': {
        'COMPONENT_ONTOLOGY': '컴포넌트는 경계 안의 실제 요소·행위자·규칙·정보 대상이어야 한다. 성능 속성·목표값·하중·상태만을 가짜 부품으로 만들어 object 참조를 맞추지 않는다. 조직 규칙·데이터는 실제 기능 담당자나 대상으로 허용한다.',
        'BASIC_AND_ACTION': 'BASIC은 확정 경계의 실제 유익 작용을 대표하며 action은 subject가 object 속성을 변화·유지시키는 구체 작용이다. 목표·권고·관리한다·최적화한다만으로 대체하지 않는다. 대표 BASIC은 하나이며 공동목적의 다른 USEFUL/AUXILIARY도 허용한다. BASIC의 INSUFFICIENT/EXCESSIVE는 허용한다.',
        'EVIDENCE_STATUS': '요구값·허용값·목표·가능성·가설을 실제 관측 상태(OBSERVED)로 승격하지 않는다. notes와 같은 간선에 적용되는 명시 한정을 함께 읽는다. HARMFUL+HYPOTHESIS는 허용하며 유해성 자체가 관측 주장이 아니다.',
    },
    'R4_IFR': {
        'REQUIREMENT_VS_OBSERVATION': '허용 한계·내열 요구·목표 성능과 실제 현재 측정값을 구별한다. 예: 견뎌야 할 2000 K 이상은 현재 2000 K 관측이 아니다. IFR의 희망 결과를 현재 관측이라고 오독하지 말고 이미·현재·실측 같은 실제 상태 주장만 근거와 대조한다.',
        'RESOURCE_AVAILABILITY': '확인되지 않은 온도 구배·재료 특성·용량·정보·권한을 이미 존재하는 이용 가능 자원으로 승격하지 않는다. 이상적 희망·조건부 자원·가설은 명시되면 허용한다. 요구 경계값만으로 실제 이용 가능한 온도 구배를 확정하지 않는다.',
        'IDEALITY_CLAIMS': '이상성 비율의 수치·대소를 실제 산식·동일 기준의 분자 분모·측정 근거 없이 계산 결과처럼 확정하지 않는다. 정성적 개선 방향과 이상해결 목표는 허용한다.',
    },
    'R4_CONTRA': {
        'SAME_PROPERTY_OPPOSITES': '각 물리적 모순은 동일 요소의 동일 변수에 대한 양립 불가능한 상반 상태와 그 이유다. 검증 충실도 높음과 공개 깊이 낮음은 독립 속성이므로 PC가 아니다. 이름에 두 변수를 묶어도 같은 변수가 되지 않는다. 전체 맥락의 시간·공간·조건 분리는 허용하며 PC가 없으면 빈 배열과 적용 불가 설명을 허용한다.',
        'PC_REQUIREMENT_EVIDENCE': 'PC 양쪽 요구는 실제 문제·경계·제약 또는 명시된 인과 가설에 근거해야 한다. 요구를 관측으로 바꾸거나 경계 밖 목적을 강요하지 않는다. 독립 속성의 양립 가능한 설계를 억지 상반 상태로 만들지 않는다.',
    },
    'R3_CONSTRAINT': {
        'DIRECT_SOURCE_SCOPE': '신규 USER 제약은 직접 원문·질문 맥락이 대상·조건·수치·단위·의무 수준을 뒷받침해야 한다. 원문 정확 인용만으로 의미를 확정하지 않는다. 연봉 인상률 상한을 모든 금전 보상 상한으로 넓히지 않는다.',
        'ALTERNATIVES_AND_TABOO': '파생 taboo는 인용한 제약의 조건·예외·AND/OR 대안보다 엄격해질 수 없다. 비식별화 또는 사용 범위 제한은 둘 중 하나의 대안이며 비식별화 없는 모든 사용을 금지하지 않는다. 금지된 결과를 모든 수단의 금지로 넓히지 않는다.',
        'CONSTRAINT_SOURCE_STATUS': '기존 제약은 수정 대상이 아닌 아카이브다. 신규 DOMAIN 가설과 직접 USER 요구를 구별한다. 요구값의 실제 측정 근거가 없다는 이유로 USER HARD를 soft화하거나 INFERRED HARD를 직접 USER 확인으로 승격하지 않는다. 재출력 행 제거는 기존 저장 제약의 완화가 아니다.',
    },
    'R4_TRIM': {
        'TRIM_CONSTRAINT_SCOPE': '트리밍 판단에서 인용한 기존 제약의 원문 대상·조건·예외·의무를 보존한다. 열 배출 요구를 흡수재 총량 보존 의무로 바꾸는 등 다른 성능이나 특정 구현 보존 의무를 만들지 않는다. 제약에 없는 조건부 설계 가설은 가설로 명시할 수 있으나 확인된 HARD 의무로 표현하지 않는다.',
    },
}
CRITERIA = {
    'COMPONENT_ONTOLOGY': 'C3', 'BASIC_AND_ACTION': 'C1', 'EVIDENCE_STATUS': 'C3',
    'REQUIREMENT_VS_OBSERVATION': 'C3', 'RESOURCE_AVAILABILITY': 'C3', 'IDEALITY_CLAIMS': 'C3',
    'SAME_PROPERTY_OPPOSITES': 'C3', 'PC_REQUIREMENT_EVIDENCE': 'C3',
    'DIRECT_SOURCE_SCOPE': 'C1', 'ALTERNATIVES_AND_TABOO': 'C1', 'CONSTRAINT_SOURCE_STATUS': 'C1',
    'TRIM_CONSTRAINT_SCOPE': 'C1',
}


def supported(rubric_id):
    return rubric_id in RULES


def request_packet(state, rubric_id, artifact):
    """Only direct reports, stored provenance and each rubric's relevant support."""
    from .constraint_sources import user_constraint_sources
    chosen = state.confirm.chosen() if state.confirm.user_confirmed else None
    context = {
        'direct_user_sources': user_constraint_sources(state),
        'boundary': {
            'user_confirmed': state.confirm.user_confirmed,
            'chosen': chosen.model_dump() if chosen else None,
            'target_system': state.domain.target_system,
            'physical_scope': state.domain.physical_scope,
            'operative_zone': state.confirm.operative_zone,
            'operative_time': state.confirm.operative_time,
        },
        'existing_constraints': [row.model_dump() for row in state.constraints.items],
        'source_policy': '직접 사용자 보고도 요구·허용값·가능성·실측을 구별한다. 기존 INFERRED/DOMAIN 및 이전 모델 산출물은 직접 관측의 증거가 아니다. 누락된 근거를 상상하지 않는다.',
    }
    # Older sessions preserve the user's answer but not its original question.
    # Keep self-contained reports available to the auditor without treating the
    # missing question as evidence for a new USER/HARD scope or obligation.
    brief = state.scratch.get('deep_dive', {})
    legacy_answers = brief.get('answers', []) if isinstance(brief, dict) else []
    context['legacy_user_reports'] = [
        {'source_path': f'scratch.deep_dive.answers[{i}]', 'text': text,
         'question_context': 'MISSING',
         'source_policy': '사용자 보고 원문이다. 질문 맥락이 없으므로 문장 자체가 완결된 관측 보고인 경우에만 그 범위의 근거로 읽는다. 요구·가능성·가설을 실측으로 바꾸지 않는다. 신규 USER/HARD 인증 경로가 아니다.'}
        for i, text in enumerate(legacy_answers if isinstance(legacy_answers, list) else [])
        if isinstance(text, str) and text.strip()]
    if rubric_id in ('R4_IFR', 'R4_CONTRA', 'R4_TRIM'):
        context['function_model'] = {
            'components': [row.model_dump() for row in state.analysis.components],
            'function_edges': [row.model_dump() for row in state.analysis.function_edges],
        }
    if rubric_id == 'R4_IFR':
        context['resources'] = [row.model_dump() for row in state.analysis.resources]
    if rubric_id == 'R4_CONTRA':
        context['causal_hypotheses'] = [row.model_dump() for row in state.analysis.ceca.nodes] if state.analysis.ceca else []
    # Raw extracted document text is primary evidence; extracted_facts are not.
    context['attachment_texts'] = [
        {'filename': row.filename, 'text': row.extracted_text}
        for row in state.intake.attachments if row.extracted_text]
    return {'contract': VERSION, 'rubric_id': rubric_id, 'rules': RULES[rubric_id],
            'artifact': artifact, 'context': context}


def render_request(packet):
    return (
        '별도 집중 의미 검증이다. 일반 검증의 PASS를 근거로 삼지 말고 아래 규칙만 독립 검사하라. '
        '문체·동의어·개선 가능성·더 자세한 설명은 결함이 아니다. 제공된 현재 전체 artifact와 근거를 읽고 '
        '각 rule ID를 정확히 한 번 PASS 또는 REVISE로 판정하라. 적용할 항목이 없으면 그 이유를 적어 PASS다. '
        '실제 위반이 있으면 정확한 JSON Pointer artifact_path, 해당 위치의 현재 값에서 따온 artifact_quote, '
        '규칙 또는 context의 JSON Pointer evidence_path와 정확한 evidence_quote, issue와 실행 가능한 '
        'suggested_correction을 findings에 작성하라. artifact_path는 /artifact로 시작하지 않고 artifact 내부를 '
        '가리킨다. evidence_path는 /context 또는 /rules로 시작한다. 숫자나 문자열이 아니면 해당 값의 JSON 표현을 '
        '인용한다. 존재하지 않는 경로·상상한 값·생략한 한정·과거 산출물을 현재 결함으로 인용하지 않는다. '
        'JSON 문자열 인용의 공백·철자도 원문 그대로 사용한다. PASS의 findings는 []; REVISE는 근거 있는 findings가 '
        '하나 이상 필요하다. 이전 지적에 얽매이지 말고 현재 결과를 검증하며 동일 명제의 가설 한정을 함께 읽어라. '
        '점수는 출력하지 않는다. 전체 JSON만 반환한다:\n'
        '{"checks":[{"id":"rule ID","status":"PASS 또는 REVISE","reason":"판정 이유",'
        '"findings":[{"artifact_path":"/필드/0/속성","artifact_quote":"현재 값의 정확한 인용",'
        '"evidence_path":"/context/... 또는 /rules/ID","evidence_quote":"근거의 정확한 인용",'
        '"issue":"실제 위반","suggested_correction":"해당 범위의 구체 수정"}]}]}\n'
        + json.dumps(packet, ensure_ascii=False)
    )


def unavailable(reason):
    return {'verdict': 'UNVERIFIED', 'score': 0., 'verification_unavailable': True,
            'source': VERSION, 'error': reason, 'checks': [],
            'revision_instructions': [], 'element_findings': []}


def _pointer(value, path):
    if not isinstance(path, str) or not path.startswith('/'):
        raise ValueError('JSON Pointer must start with /')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(value, Mapping):
            value = value[part]
        elif isinstance(value, list) and part.isdigit():
            value = value[int(part)]
        else:
            raise ValueError('Unknown JSON Pointer')
    return value


def _quote_matches(value, quote):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return isinstance(quote, str) and bool(quote.strip()) and quote in text


def normalize_review(raw, packet):
    """Unverifiable allegations cannot become either a repair order or a PASS."""
    if not isinstance(raw, dict) or not isinstance(raw.get('checks'), list):
        return unavailable('집중 검증 checks 배열이 누락되었다.')
    expected = set(packet['rules'])
    rows = raw['checks']
    ids = [row.get('id') if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(key, str) for key in ids) or len(ids) != len(expected) or set(ids) != expected:
        return unavailable('집중 검증의 규칙별 판정이 누락·중복되거나 알 수 없는 ID가 있다.')
    findings, instructions = [], []
    for row in rows:
        status = row.get('status')
        if status not in ('PASS', 'REVISE') or not isinstance(row.get('reason'), str) or not row['reason'].strip():
            return unavailable('집중 검증 판정 상태 또는 이유가 유효하지 않다.')
        details = row.get('findings')
        if not isinstance(details, list) or (status == 'PASS' and details) or (status == 'REVISE' and not details):
            return unavailable('집중 검증 판정과 실행 가능한 지적이 일치하지 않는다.')
        for finding in details:
            if not isinstance(finding, dict) or any(not isinstance(finding.get(key), str) or not finding[key].strip()
                    for key in ('artifact_path', 'artifact_quote', 'evidence_path', 'evidence_quote', 'issue', 'suggested_correction')):
                return unavailable('집중 검증 지적에 경로·인용·구체 수정안이 필요하다.')
            try:
                actual = _pointer(packet['artifact'], finding['artifact_path'])
                if not finding['evidence_path'].startswith(('/context/', '/rules/')):
                    raise ValueError('Evidence must refer to supplied context or rule')
                evidence = _pointer(packet, finding['evidence_path'])
                if not _quote_matches(actual, finding['artifact_quote']) or not _quote_matches(evidence, finding['evidence_quote']):
                    raise ValueError('Exact quotation mismatch')
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                return unavailable(f"집중 검증 {row['id']}의 artifact_path={finding['artifact_path']}, "
                    f"evidence_path={finding['evidence_path']} 또는 정확한 인용을 확인할 수 없다: {exc}")
            findings.append({'path': finding['artifact_path'], 'issue': finding['issue'],
                'suggested_correction': finding['suggested_correction'],
                'evidence': f"{finding['evidence_path']}: {finding['evidence_quote']}",
                'artifact_quote': finding['artifact_quote'], 'criterion_id': CRITERIA[row['id']],
                'focused_check_id': row['id']})
            instructions.append(f"{finding['artifact_path']}: {finding['suggested_correction']}")
    verdict = 'REVISE' if findings else 'PASS'
    if raw.get('verdict', verdict) != verdict:
        return unavailable('집중 검증 전체 판정이 규칙별 판정과 모순된다.')
    return {'verdict': verdict, 'score': 0. if findings else 1., 'source': VERSION,
            'checks': rows, 'element_findings': findings,
            'revision_instructions': list(dict.fromkeys(instructions))}
