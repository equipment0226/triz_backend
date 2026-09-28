"""Frozen generation intent. Audit identities never supply semantic novelty."""
import copy
import json
from .contracts import digest, Conflict

SCHEMA = 'triz-targeted-expansion-v1'
PROMPTS = {'P_S5_TRACK_A', 'P_S5_MATRIX_FALLBACK', 'P_S5_TRACK_G', 'P_S5_TRACK_H'}
MAX_PRIOR = 16
MAX_PRIOR_BYTES = 24000


def enabled(state):
    return state.scratch.get('ax_bundle', {}).get('exploration_contract') == SCHEMA


def build(state, obligation_ids, gap_kinds):
    from .coherence import obligations
    from ..idea_consolidation import _sources
    available = obligations(state)
    aliases = {cid: o for o in available for cid in [o['id'], *o['contradiction_ids']]}
    if not obligation_ids or any(i not in aliases for i in obligation_ids):
        raise Conflict('Unknown or stale targeted obligation')
    selected = {aliases[i]['id']: aliases[i] for i in obligation_ids}
    targets = [dict(obligation_id=o['id'], **{k: o[k] for k in ('contradiction_ids', 'description', 'improve', 'protect')})
               for _, o in sorted(selected.items())]
    refs = {cid for o in targets for cid in o['contradiction_ids']}
    # The current schema has no exact contradiction -> function edge mapping.
    # Preserve that absence, using both sides only as search clues.
    functions = list(dict.fromkeys(side for o in targets for side in (o['improve'], o['protect']) if side))
    inventory = {r['source_idea_id']: r for r in state.scratch.get('ax_idea_inventory', [])}
    inventory.update({r['source_idea_id']: r for r in _sources(state.solve.raw_ideas)})
    prior = []
    for sid, row in sorted(inventory.items()):
        addresses = set(row.get('addresses', []))
        if addresses and not addresses.intersection(refs):
            continue
        prior.append(dict(source_idea_ids=[sid], mechanism_key=row.get('mechanism_key', ''),
            mechanism=str(row.get('mechanism') or row.get('idea', ''))[:1200],
            intervention=str(row.get('intervention_variable', ''))[:600],
            conditions=copy.deepcopy(row.get('conditions', [])),
            resolution_status=row.get('resolution_status', 'UNSUPPORTED'),
            relation='RECORDED_TARGET' if addresses else 'TARGET_MAPPING_UNRECORDED',
            gap_reason={'status': 'HYPOTHESIS_OR_MISSING_EVIDENCE',
                        'text': str(row.get('strongest_objection') or '해결 및 적용 조건 검증 기록 부족')[:1200]},
            validation_test=str(row.get('validation_test', ''))[:800]))
    prior.sort(key=lambda row: (row['relation'] != 'RECORDED_TARGET', row['source_idea_ids']))
    bounded = []; size = 0
    for row in prior:
        row_size = len(json.dumps(row, ensure_ascii=False).encode('utf-8'))
        if len(bounded) < MAX_PRIOR and size + row_size <= MAX_PRIOR_BYTES:
            bounded.append(row); size += row_size
    return dict(schema=SCHEMA, target_obligations=targets, required_functions=functions,
        function_mapping='UNAVAILABLE_TARGET_SIDES_AS_SEARCH_CLUES', gap_kinds=sorted(set(gap_kinds)),
        prior_mechanisms=bounded, prior_digest_omitted=len(prior) - len(bounded),
        prior_inventory_hash=digest(prior),
        required_new_direction='미해결 원인에 대응하는 다른 기구 또는 개입·조건의 명시적 수정을 제안한다. '
            '같은 효과도 다른 적용 방식으로 사용할 수 있다. 새 기여가 없으면 no_application_reason으로 설명한다. '
            'UNSUPPORTED와 검토 가설은 불가능성의 증거가 아니다. 타산업 사례만으로 작동 검증을 주장하지 않는다.',
        preserve_requirements=True, constraints=state.constraints.model_dump(mode='json'))


def validate(payload, semantic_hash, state=None):
    if (not isinstance(payload, dict) or payload.get('schema') != SCHEMA
            or payload.get('preserve_requirements') is not True or digest(payload) != semantic_hash
            or not payload.get('target_obligations') or not payload.get('required_functions')):
        raise Conflict('Invalid targeted context/hash')
    if state is not None:
        from .coherence import obligations
        known = {o['id']: o for o in obligations(state)}
        for target in payload['target_obligations']:
            original = known.get(target.get('obligation_id'))
            if not original or any(target.get(k) != original[k] for k in ('contradiction_ids', 'improve', 'protect')):
                raise Conflict('Foreign or stale targeted obligation')
        if 'constraints' in payload and payload['constraints'] != state.constraints.model_dump(mode='json'):
            raise Conflict('Stale targeted requirements')
    return payload


def current(state):
    from .action_runtime import active_action
    action = active_action.get()
    if not enabled(state) or not action or not action.get('optional'):
        return None
    if action.get('run_id') != state.run_id:
        raise Conflict('Foreign targeted action context')
    p = action['ticket']['parameters']
    payload = p.get('exploration_context')
    if payload is None:
        return None
    return validate(payload, p.get('semantic_context_hash'), state)


def target_tcs(state, context):
    refs = {cid for o in context['target_obligations'] for cid in o['contradiction_ids']}
    refs.update(p.derived_from_tc_id for p in state.definition.physical_contradictions
                if p.id in refs and p.derived_from_tc_id)
    selected = {cid for kp in state.definition.key_problems for cid in kp.contradiction_ids}
    selected.update(p.derived_from_tc_id for p in state.definition.physical_contradictions
                    if p.id in selected and p.derived_from_tc_id)
    return [tc for tc in state.definition.technical_contradictions if tc.id in refs
            and (not selected or tc.id in selected)]


def render(context):
    return '\n\n[목표 기반 추가 탐색 계약 ' + SCHEMA + ']\n' + json.dumps(
        context, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
