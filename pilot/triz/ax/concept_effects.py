"""Pinned explicit adoption contract; source exposure alone is never adoption."""
import json

VERSION = 'explicit-active-effects-v1'


def enabled(state):
    return state.scratch.get('ax_bundle', {}).get('concept_effect_contract') == VERSION


def sources(state, source_ids):
    from .source_lineage import trace
    lineage = trace(state, source_ids)
    if not lineage['complete']:
        return []
    return [{**record, 'source_idea_id': key} for key, record in sorted(lineage['records'].items())
            if isinstance(record.get('source_effect_id'), str) and record['source_effect_id']]


def allowed(state, source_ids):
    return {row['source_effect_id'] for row in sources(state, source_ids)}


def validate(raw, allowed_ids):
    values = raw.get('active_effect_ids') if isinstance(raw, dict) else None
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        return ['active_effect_ids를 명시적인 문자열 배열로 기록하세요. 실제 남긴 효과가 없으면 []를 기록하세요.']
    if len(values) != len(set(values)):
        return ['active_effect_ids에 중복된 효과를 기록할 수 없습니다.']
    if set(values) - set(allowed_ids):
        return ['active_effect_ids는 해당 후보의 배정 원안에 저장된 source_effect_id만 허용합니다.']
    return []


def check_batch(state, data):
    issues = []
    if not isinstance(data, dict) or not isinstance(data.get('concepts'), list):
        return issues  # The coverage/schema checker reports structural errors.
    for row in data['concepts']:
        if not isinstance(row, dict):
            continue
        ids = row.get('source_idea_ids')
        if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
            continue
        issues.extend('FATAL-S6-COVERAGE: ' + issue for issue in validate(row, allowed(state, ids)))
    return issues


def instruction(state, source_ids):
    return ('\n\n[과학효과 실제 채택 기록 계약 ' + VERSION + ']\n'
        'concepts의 모든 항목에 active_effect_ids 필드를 반드시 기록한다. '
        'JSON 형식: {"source_idea_ids":["배정 원안 ID"],"active_effect_ids":[]}. '
        '최종 working_principle에 실제 유지한 과학효과만 명시한다. '
        '해당 원안의 아래 저장 근거에 있는 source_effect_id만 사용할 수 있다. '
        '검색 노출, 다른 원안의 효과, 제거한 효과, 추정한 효과는 포함하지 않는다. '
        '효과를 사용하지 않았거나 저장 근거가 없으면 빈 배열 []를 명시한다. '
        '효과 ID는 근거 연결용 필드에만 넣고 사용자용 제목과 설명에는 넣지 않는다.\n'
        + json.dumps({i: sources(state, [i]) for i in source_ids}, ensure_ascii=False, sort_keys=True))
