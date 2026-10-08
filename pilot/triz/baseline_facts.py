"""Separate primary current-state reports from obligations on future solutions."""
import json

ROLE_CONTRACT = (
    '\n[현재 사실과 준수 제약의 구분]\n'
    '사용자가 말한 모든 숫자가 개선 후 유지해야 할 제약은 아니다. 현재 측정값·운전값·비용·구성비·'
    '문제 발생 횟수·과거 시도는 baseline_facts에 원문과 질문 맥락을 보존한다. '
    '사용자가 명시한 목표·상한·하한·금지·필수 조건·설계 하중·변경 불가 조건은 items의 제약으로 유지한다. '
    '현재값이라는 단어만으로 실제 고정 운전 조건이나 규정·물리 조건을 제거하지 않는다. '
    '모호하면 원문과 충돌을 밝히고 확인 대상으로 남긴다. '
    '예: 현재 에너지 사용 6GWh는 기준선이며 개선 후 ==6 유지 제약이 아니다. '
    '45% 절감 목표는 제약이다. 현재 PEB80℃라는 답변만으로 80℃ 변경 금지를 만들지 않는다. '
    '계측 오차·시험 하중 같은 기준정보는 성능 계산과 검증 조건에 계속 반영하되 그 숫자를 성능 목표로 혼동하지 않는다. '
    'baseline_facts는 기존 데이터의 삭제나 실제 의무 완화를 뜻하지 않는다. '
    'baseline_facts 각 행은 {statement,source_path,source_quote,context}이며 정확한 원문 인용과 '
    '현재 상태임을 설명하는 질문 맥락을 보존한다. items와 동일 사실을 중복 출력하지 않는다.\n'
)


def sources(state):
    from .constraint_sources import user_constraint_sources
    result = user_constraint_sources(state)
    for index, attachment in enumerate(state.intake.attachments):
        if attachment.extracted_text.strip():
            result[f'intake.attachments[{index}].extracted_text'] = {
                'text': attachment.extracted_text, 'question': '', 'filename': attachment.filename}
    return result


def extraction_supplement(state):
    return (ROLE_CONTRACT + '출력 constraints에는 items, baseline_facts, open_questions를 둔다. '
            'source_path와 source_quote는 아래 직접 원문 경로와 정확히 일치해야 한다.\n'
            + json.dumps(sources(state), ensure_ascii=False))


def check_extraction(data, state):
    from .schema import BaselineFact, Constraint
    from .constraint_sources import validate_user_constraint_source
    if not isinstance(data, dict) or not isinstance(data.get('constraints', {}), dict):
        return ['FATAL-INTAKE: constraints는 객체여야 한다.']
    active_rows = data.get('constraints', {}).get('items', [])
    if not isinstance(active_rows, list):
        return ['FATAL-INTAKE: constraints.items는 제약 객체의 배열이어야 한다.']
    issues = []
    for index, row in enumerate(active_rows):
        try:
            item = Constraint.model_validate(row)
            if not isinstance(row, dict) or not item.statement.strip():
                raise ValueError('Missing constraint statement')
        except (ValueError, TypeError):
            issues.append(f'FATAL-INTAKE: constraints.items[{index}]는 유효한 제약 객체와 비어 있지 않은 statement가 필요하다.')
    rows = data.get('constraints', {}).get('baseline_facts', [])
    if not isinstance(rows, list):
        return ['FATAL-INTAKE: constraints.baseline_facts는 배열이어야 한다.']
    ids = set()
    active_statements = {' '.join(row.get('statement', '').split())
        for row in active_rows
        if isinstance(row, dict) and isinstance(row.get('statement'), str)}
    source_rows = sources(state)
    for index, row in enumerate(rows):
        prefix = f'FATAL-INTAKE: baseline_facts[{index}]'
        try:
            fact = BaselineFact.model_validate(row)
        except (ValueError, TypeError):
            issues.append(prefix + '에 statement/source_path/source_quote/context 형식이 필요하다.')
            continue
        if not fact.statement.strip():
            issues.append(prefix + '.statement가 비어 있다.')
        if ' '.join(fact.statement.split()) in active_statements:
            issues.append(prefix + '가 active items와 같은 사실을 중복한다. 현재 상태와 실제 의무를 원문에 따라 구분하라.')
        if fact.id in ids:
            issues.append(prefix + '.id가 중복된다.')
        ids.add(fact.id)
        for error in validate_user_constraint_source(row, source_rows):
            issues.append(prefix + ': ' + error)
    return issues
