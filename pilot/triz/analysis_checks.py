"""Structural TRIZ contracts; meaning is reviewed against the confirmed boundary.

These checks never invent a component, cause, resource or contradiction to repair
an artifact. Invalid results return to the generator before typed state mutation.
"""
from __future__ import annotations

import math


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _reference(value, known):
    return isinstance(value, str) and value in known


def _rows(data, key, *, empty=False):
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        return [], [f"FATAL-ANALYSIS: {key}는 객체 배열이어야 한다. 전체 출력 객체를 복원하라."]
    rows = data[key]
    if not rows and not empty:
        return [], [f"FATAL-ANALYSIS: {key}가 비어 있다."]
    if any(not isinstance(row, dict) for row in rows):
        return [], [f"FATAL-ANALYSIS: {key}의 모든 항목은 객체여야 한다."]
    from . import schema
    models = {'components': schema.Component, 'function_edges': schema.FunctionEdge,
              'interaction_cells': schema.InteractionCell, 'su_fields': schema.SuFieldModel,
              'resources': schema.ResourceItem, 'constraints': schema.Constraint,
              'nodes': schema.CauseNode, 'technical_contradictions': schema.TechnicalContradiction,
              'physical_contradictions': schema.PhysicalContradiction,
              'trimming': schema.TrimmingItem, 'key_problems': schema.KeyProblem}
    issues = []
    explicit_ids = [row['id'] for row in rows if 'id' in row]
    if (any(not _text(key) for key in explicit_ids) or
            len({str(key) for key in explicit_ids}) != len(explicit_ids)):
        issues.append(f'FATAL-ANALYSIS: {key}에 명시한 ID는 비어 있지 않고 중복되지 않아야 한다.')
    if key in models:
        for i, row in enumerate(rows):
            try:
                models[key].model_validate(row)
            except ValueError as exc:
                # Repair needs the actual field and enum/type contract, not an
                # opaque row-level failure that produces the same bad output.
                errors = exc.errors(include_url=False, include_input=False) if hasattr(exc, 'errors') else []
                for error in errors[:6]:
                    field = '.'.join(str(part) for part in error.get('loc', ()))
                    path = f'{key}[{i}]' + ('.' + field if field else '')
                    issues.append(f"FATAL-ANALYSIS: {path}: {error.get('msg', '저장 스키마 형식 오류')}")
                if not errors:
                    issues.append(f'FATAL-ANALYSIS: {key}[{i}]의 필드 형식이 저장 스키마와 맞지 않는다.')
    return rows, issues


def _strings(value):
    return isinstance(value, list) and all(_text(x) for x in value)


def _required(row, fields, path):
    return [f"FATAL-ANALYSIS: {path}.{field}에 비어 있지 않은 문자열이 필요하다."
            for field in fields if not _text(row.get(field))]


def artifact_structure_facts(rubric_id, data):
    """Bounded facts from JSON labels, never a substitute for semantic review.

    BASIC is counted only from explicit ``rank == BASIC`` rows. Sharing the
    same subject or pointing at a PRODUCT does not make another edge BASIC.
    Names are compared exactly, as in the storage/reference contract.
    """
    if rubric_id != 'R3_FUNC':
        return {}
    if not isinstance(data, dict):
        return {'artifact_is_object': False}
    limit = 40
    components = data.get('components')
    edges = data.get('function_edges')
    component_rows = components if isinstance(components, list) else []
    edge_rows = edges if isinstance(edges, list) else []
    known = {row['name'] for row in component_rows
             if isinstance(row, dict) and isinstance(row.get('name'), str)}
    basics = [(i, row) for i, row in enumerate(edge_rows)
              if isinstance(row, dict) and row.get('rank') == 'BASIC']
    products = [(i, row) for i, row in enumerate(component_rows)
                if isinstance(row, dict) and row.get('level') == 'PRODUCT']
    unknown = []
    for i, row in enumerate(edge_rows):
        if not isinstance(row, dict):
            continue
        for field in ('subject', 'object'):
            if not _reference(row.get(field), known):
                unknown.append({'index': i, 'field': field, 'value': row.get(field)})

    def compact(value):
        if isinstance(value, str):
            return value[:240]
        return None  # Do not dump a malformed nested value into the verifier.

    return {
        'artifact_is_object': True,
        'source': 'deterministic_json_inspection',
        'scope': '구조 사실만 집계했다. BASIC 의미 적합성·컴포넌트 실재성·작용 타당성을 승인하지 않는다.',
        'basic_count_rule': 'rank가 정확히 BASIC인 간선만 센다. 동일 subject의 AUXILIARY/CORRECTIVE는 별개다.',
        'object_parameter_rule': 'object는 컴포넌트, parameter_affected는 그 대상의 속성이다. object가 속성명일 필요는 없다.',
        'components_is_array': isinstance(components, list),
        'function_edges_is_array': isinstance(edges, list),
        'component_count': len(component_rows),
        'function_edge_count': len(edge_rows),
        'basic_count': len(basics),
        'basic_indexes': [i for i, _ in basics[:limit]],
        'basic_functions': [dict(index=i, **{key: compact(row.get(key)) for key in (
            'subject', 'action', 'object', 'kind', 'level', 'rank', 'parameter_affected')})
            for i, row in basics[:limit]],
        'product_component_count': len(products),
        'product_components': [{'index': i, 'name': compact(row.get('name'))}
                               for i, row in products[:limit]],
        'unknown_endpoint_count': len(unknown),
        'unknown_endpoints': [dict(row, value=compact(row['value'])) for row in unknown[:limit]],
        'truncated_lists': [name for name, rows in (
            ('basic_functions', basics), ('product_components', products), ('unknown_endpoints', unknown))
            if len(rows) > limit],
    }


def function_model(data):
    components, issues = _rows(data, 'components')
    edges, edge_issues = _rows(data, 'function_edges')
    issues += edge_issues
    if issues:
        return issues
    if not isinstance(data.get('mermaid',''),str):
        issues.append('FATAL-FUNC: mermaid는 문자열이어야 한다. 없으면 빈 문자열로 기록하라.')
    names = [c.get('name') for c in components]
    if any(not _text(name) for name in names) or len(set(str(n) for n in names)) != len(names):
        issues.append('FATAL-FUNC: 컴포넌트 이름은 비어 있지 않고 중복되지 않아야 한다.')
    known = {n for n in names if _text(n)}
    basics = [e for e in edges if e.get('rank') == 'BASIC']
    if len(basics) != 1:
        issues.append(f'FATAL-BASIC: 대표 주기능(BASIC)은 정확히 1개여야 하는데 {len(basics)}개다.')
    elif basics[0].get('kind') != 'USEFUL':
        issues.append('FATAL-BASIC: BASIC은 반드시 USEFUL이어야 한다. 유해 입력·실패 현상을 주기능으로 삼지 마라.')
    if not any(c.get('level') == 'PRODUCT' for c in components):
        issues.append('FATAL-FUNC: 가공·처리 대상(PRODUCT) 컴포넌트가 없다.')
    if len(components) < 2:
        issues.append('FATAL-FUNC: 작용 주체와 처리 대상을 구분한 컴포넌트가 최소 2개 필요하다.')
    for i,c in enumerate(components):
        issues += _required(c, ('name','role'), f'components[{i}]')
        if c.get('level') not in ('SUPER','TARGET','SUB','ENVIRONMENT','PRODUCT'):
            issues.append(f'FATAL-FUNC: components[{i}].level이 유효하지 않다.')
    for i,e in enumerate(edges):
        issues += _required(e, ('subject','action','object','parameter_affected'), f'function_edges[{i}]')
        for key in ('subject','object'):
            if not _reference(e.get(key), known):
                issues.append(f"FATAL-FUNC: function_edges[{i}].{key} '{e.get(key)}'가 컴포넌트 목록에 없다.")
        if e.get('rank') not in ('BASIC','AUXILIARY','CORRECTIVE') or e.get('kind') not in ('USEFUL','HARMFUL'):
            issues.append(f'FATAL-FUNC: function_edges[{i}]의 rank/kind가 유효하지 않다.')
        if e.get('level') not in ('INSUFFICIENT','NORMAL','EXCESSIVE'):
            issues.append(f'FATAL-FUNC: function_edges[{i}].level이 유효하지 않다.')
        if any(v in str(e.get('action','')) for v in ('제공한다','개선한다','최적화한다','수행한다','관리한다')):
            issues.append(f"DET-05d: 모호한 기능 동사 '{e.get('action')}' — 작용 대상의 변화·유지를 구체화하라.")
    if not any(e.get('kind') == 'HARMFUL' or e.get('level') in ('INSUFFICIENT','EXCESSIVE') for e in edges):
        issues.append('FATAL-FUNC: 문제를 나타내는 유해·부족·과잉 기능이 없다.')
    connected = {e.get(key) for e in edges for key in ('subject','object') if _text(e.get(key))}
    for c in components:
        if c.get('level') == 'PRODUCT' and not _reference(c.get('name'), connected):
            issues.append(f"FATAL-FUNC: PRODUCT '{c.get('name')}'가 모든 기능에서 고립되어 있다.")
    cells, problems = _rows(data, 'interaction_cells', empty=True)
    issues += problems
    for i,cell in enumerate(cells):
        if not _reference(cell.get('a'), known) or not _reference(cell.get('b'), known):
            issues.append(f'FATAL-FUNC: interaction_cells[{i}]의 컴포넌트 참조를 수정하라.')
        if cell.get('sign') not in ('+','-','0','+-'):
            issues.append(f'FATAL-FUNC: interaction_cells[{i}].sign이 유효하지 않다.')
        if cell.get('sign') in ('-','+-') and not _text(cell.get('note')):
            issues.append(f'FATAL-FUNC: interaction_cells[{i}]의 유해 작용 근거(note)가 없다.')
    return issues


def nine_windows(data):
    if not isinstance(data,dict) or not isinstance(data.get('cells'),dict):
        return ['FATAL-NW: cells 객체와 insights 배열을 포함한 전체 9-Windows 결과가 필요하다.']
    expected = {f'{level}_{time}' for level in ('SUB','SYS','SUPER') for time in ('PAST','PRESENT','FUTURE')}
    issues = [f'FATAL-NW: cells.{key}가 비어 있다.' for key in sorted(expected) if not _text(data['cells'].get(key))]
    if any(not isinstance(value,str) for value in data['cells'].values()):
        issues.append('FATAL-NW: cells의 값은 문자열이어야 한다.')
    if not _strings(data.get('insights')) or not data.get('insights'):
        issues.append('FATAL-NW: 근거와 개입 여지를 설명하는 insights가 필요하다.')
    return issues


def sufields(data):
    rows, issues = _rows(data,'su_fields')
    for i,row in enumerate(rows):
        issues += _required(row, ('label','s1'),f'su_fields[{i}]')
        s2,field = _text(row.get('s2')),_text(row.get('field'))
        completeness = row.get('completeness')
        if completeness not in ('COMPLETE','INCOMPLETE','MISSING_S2','MISSING_F'):
            issues.append(f'FATAL-SUF: su_fields[{i}].completeness가 유효하지 않다.')
        elif ((completeness == 'COMPLETE' and not (s2 and field)) or
              (completeness == 'MISSING_S2' and (s2 or not field)) or
              (completeness == 'MISSING_F' and (field or not s2)) or
              (completeness == 'INCOMPLETE' and s2 and field)):
            issues.append(f'FATAL-SUF: su_fields[{i}]의 물질·장 유무와 completeness가 모순된다. 효과의 부족과 구조의 불완전을 구분하라.')
        if row.get('effect') not in ('USEFUL_SUFFICIENT','USEFUL_INSUFFICIENT','HARMFUL','EXCESSIVE','MEASUREMENT'):
            issues.append(f'FATAL-SUF: su_fields[{i}].effect가 유효하지 않다.')
        for key in ('s2','field'):
            if not isinstance(row.get(key),str):
                issues.append(f'FATAL-SUF: su_fields[{i}].{key}는 문자열이어야 하며 없으면 빈 문자열을 사용한다.')
    return issues


def resources(data):
    rows,issues = _rows(data,'resources',empty=True)
    if isinstance(data,dict) and not isinstance(data.get('unavailable_reason',''),str):
        issues.append('FATAL-RES: unavailable_reason은 문자열이어야 한다.')
    if not rows and not issues and not _text(data.get('unavailable_reason')):
        issues.append('FATAL-RES: 가용 자원이 없으면 unavailable_reason으로 확인 범위와 이유를 밝혀라.')
    for i,row in enumerate(rows):
        issues += _required(row,('name','quantity_note'),f'resources[{i}]')
        if row.get('category') not in ('SUBSTANCE','FIELD','SPACE','TIME','INFORMATION','FUNCTIONAL','SYSTEM_LEVEL'):
            issues.append(f'FATAL-RES: resources[{i}].category가 유효하지 않다.')
        if row.get('where') not in ('IN_SYSTEM','IN_SUPERSYSTEM','IN_ENVIRONMENT','WASTE','DERIVED'):
            issues.append(f'FATAL-RES: resources[{i}].where가 유효하지 않다.')
        if row.get('availability') not in ('FREE','LOW_COST','COSTLY'):
            issues.append(f'FATAL-RES: resources[{i}].availability가 유효하지 않다.')
        if not _strings(row.get('usable_for')) or (not row.get('usable_for') and row.get('blocked_by_constraint') is not True):
            issues.append(f'FATAL-RES: resources[{i}].usable_for에 기능 활용 후보를 명시하라.')
        if not isinstance(row.get('blocked_by_constraint'),bool):
            issues.append(f'FATAL-RES: resources[{i}].blocked_by_constraint는 불리언이어야 한다.')
    return issues


def discovered_constraints(data,confirmed_hard_ids=(),existing_ids=()):
    rows,issues = _rows(data,'constraints',empty=True)
    taboo,more = _rows(data,'taboo',empty=True)
    issues += more
    known = set(confirmed_hard_ids)
    for i,row in enumerate(rows):
        issues += _required(row,('statement','rationale'),f'constraints[{i}]')
        if _reference(row.get('id'),set(existing_ids)):
            issues.append(f'FATAL-CONSTRAINT: constraints[{i}]가 기존 제약 ID를 재정의한다. 새 가설만 추가하라.')
        confidence = row.get('confidence')
        if (row.get('hard') is not False or isinstance(confidence,bool) or
                not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not 0 <= confidence <= .6):
            issues.append(f'FATAL-CONSTRAINT: constraints[{i}]의 미확인 도메인 가설은 hard=false, confidence 0~0.6이어야 한다.')
        if row.get('operator','none') != 'none' and not _text(row.get('value')):
            issues.append(f'FATAL-CONSTRAINT: constraints[{i}]의 수치/집합 제약에 값이 없다.')
    for i,item in enumerate(taboo):
        issues += _required(item,('item','why'),f'taboo[{i}]')
        if not isinstance(item.get('confirmed',False),bool):
            issues.append(f'FATAL-CONSTRAINT: taboo[{i}].confirmed는 불리언이어야 한다.')
        if item.get('confirmed') is True and not _reference(item.get('constraint_id'), known):
            issues.append(f'FATAL-CONSTRAINT: taboo[{i}]가 인용한 확인된 hard 제약이 없다.')
    return issues


def ifr(data):
    if not isinstance(data,dict):
        return ['FATAL-IFR: IFR은 전체 JSON 객체여야 한다.']
    issues = _required(data,('statement','x_element','ideality_note','intensified'),'ifr')
    from .schema import IFR
    try:
        IFR.model_validate(data)
    except ValueError:
        issues.append('FATAL-IFR: IFR 필드 형식이 저장 스키마와 맞지 않는다.')
    for key in ('without','constraint_conflicts'):
        if not _strings(data.get(key)):
            issues.append(f'FATAL-IFR: {key}는 문자열 배열이어야 한다. 없으면 []를 사용한다.')
    return issues


def trimming(data,component_names,basic_subjects=()):
    rows,issues = _rows(data,'trimming',empty=True)
    known,basics = set(component_names),set(basic_subjects)
    for i,row in enumerate(rows):
        issues += _required(row,('target_component','replaced_function','risk_note'),f'trimming[{i}]')
        target,rule = row.get('target_component'),row.get('rule')
        if not _reference(target, known):
            issues.append(f'FATAL-TRIM: trimming[{i}].target_component가 현재 컴포넌트 목록에 없다.')
        if rule not in ('A','B','C','D'):
            issues.append(f'FATAL-TRIM: trimming[{i}].rule이 유효하지 않다.')
        if (rule != 'A' or _reference(target, basics)) and not _text(row.get('replacement_carrier')):
            issues.append(f'FATAL-TRIM: trimming[{i}]의 유익 기능을 인수할 주체가 없다.')
        if _text(row.get('replacement_carrier')) and row['replacement_carrier'].strip() == str(target).strip():
            issues.append(f'FATAL-TRIM: trimming[{i}]에서 제거할 부품이 자신의 기능을 그대로 인수할 수 없다.')
        if row.get('feasibility') not in ('HIGH','MID','LOW'):
            issues.append(f'FATAL-TRIM: trimming[{i}].feasibility가 유효하지 않다.')
    return issues


def key_problems(data,contradiction_ids):
    rows,issues = _rows(data,'key_problems')
    dropped,more = _rows(data,'dropped',empty=True)
    issues += more
    known,selected,dropped_ids = set(contradiction_ids),set(),set()
    for i,row in enumerate(rows):
        issues += _required(row,('title','why_key'),f'key_problems[{i}]')
        ids = row.get('contradiction_ids')
        if not _strings(ids) or not ids:
            issues.append(f'FATAL-KEY: key_problems[{i}].contradiction_ids가 비어 있거나 유효한 문자열 배열이 아니다.')
        else:
            selected.update(ids)
            if not set(ids) <= known or len(set(ids)) != len(ids):
                issues.append(f'FATAL-KEY: key_problems[{i}]에 미등록·중복 모순 ID가 있다.')
        for key in ('impact','tractability'):
            score = row.get(key)
            if isinstance(score,bool) or not isinstance(score,int) or not 1 <= score <= 5:
                issues.append(f'FATAL-KEY: key_problems[{i}].{key}는 1~5 정수여야 한다.')
    for i,row in enumerate(dropped):
        issues += _required(row,('id','reason'),f'dropped[{i}]')
        key = row.get('id')
        if not _text(key) or key not in known:
            issues.append(f'FATAL-KEY: dropped[{i}].id가 현재 모순 목록에 없다.')
        elif key in dropped_ids or key in selected:
            issues.append(f'FATAL-KEY: dropped[{i}]가 중복되거나 선정된 모순을 동시에 탈락시켰다.')
        if _text(key):
            dropped_ids.add(key)
    missing = known - selected - dropped_ids
    if missing:
        issues.append('FATAL-KEY: 미선정 모순의 탈락 이유가 없다: '+', '.join(sorted(missing)))
    return issues


def ceca_structure(data):
    nodes, issues = _rows(data, 'nodes')
    if not nodes:
        return issues
    if not isinstance(data.get('mermaid',''),str):
        issues.append('FATAL-CECA: mermaid는 문자열이어야 한다.')
    for i, node in enumerate(nodes):
        issues += _required(node, ('id', 'text'), f'nodes[{i}]')
        if not _strings(node.get('parents')):
            issues.append(f'FATAL-CECA: nodes[{i}].parents는 ID 문자열 배열이어야 한다.')
        if node.get('evidence_status') not in ('OBSERVED','HYPOTHESIS','DERIVED'):
            issues.append(f'FATAL-CECA: nodes[{i}]의 관측/가설/도출 상태를 명시하라.')
        if not _strings(node.get('evidence_refs')):
            issues.append(f'FATAL-CECA: nodes[{i}].evidence_refs는 출처 문자열 배열이어야 한다.')
        elif node.get('evidence_status') == 'OBSERVED' and not node['evidence_refs']:
            issues.append(f'FATAL-CECA: nodes[{i}]의 관측 주장에 근거 출처가 없다.')
        if node.get('evidence_status') == 'HYPOTHESIS' and not _text(node.get('falsification_test')):
            issues.append(f'FATAL-CECA: nodes[{i}]의 가설에 반증/확인 실험이 없다.')
    return issues


def contradictions(data, scheme, cause_ids=None):
    from . import knowledge as K
    tcs, issues = _rows(data, 'technical_contradictions', empty=True)
    pcs, more = _rows(data, 'physical_contradictions', empty=True)
    issues += more
    if issues:
        return issues
    if not tcs and (not _strings(data.get('mapping_notes')) or not data['mapping_notes']):
        issues.append('FATAL-CONTRA: TC가 없으면 mapping_notes에 미도출/사전 매핑 불가 이유를 기록하라.')
    if not isinstance(data.get('physical_not_applicable_reason',''),str):
        issues.append('FATAL-CONTRA: physical_not_applicable_reason은 문자열이어야 한다.')
    if not _strings(data.get('mapping_notes',[])):
        issues.append('FATAL-CONTRA: mapping_notes는 문자열 배열이어야 한다.')
    explicit_ids = [row['id'] for row in [*tcs, *pcs] if 'id' in row]
    if len({str(key) for key in explicit_ids}) != len(explicit_ids):
        issues.append('FATAL-CONTRA: TC와 PC 사이에도 ID가 중복될 수 없다.')
    labels = [tc.get('label') for tc in tcs]
    if any(not _text(label) for label in labels) or len({str(label) for label in labels}) != len(labels):
        issues.append('FATAL-CONTRA: 기술적 모순 label은 비어 있지 않고 고유해야 한다.')
    known_labels = {label for label in labels if _text(label)}
    for i, tc in enumerate(tcs):
        issues += _required(tc, ('label','if_action','then_good','but_bad','coupling_mechanism','rationale'), f'technical_contradictions[{i}]')
        imp, wor = tc.get('improving_param_id'), tc.get('worsening_param_id')
        if (isinstance(imp,bool) or isinstance(wor,bool) or not isinstance(imp,int) or not isinstance(wor,int)
                or not K.valid_param(imp,scheme) or not K.valid_param(wor,scheme)):
            issues.append(f'FATAL-CONTRA: TC[{i}]의 개선/악화 파라미터는 {scheme}의 유효한 정수 ID여야 한다.')
        elif imp == wor:
            issues.append(f'FATAL-CONTRA: TC[{i}]의 개선/악화 파라미터가 같다. 동일 속성의 상반 요구이면 PC로 표현하라.')
        if cause_ids is not None:
            refs = tc.get('cause_node_ids')
            if not _strings(refs) or not refs or not set(refs) <= set(cause_ids):
                issues.append(f'FATAL-CONTRA: TC[{i}]는 현재 CECA 원인 노드를 정확한 ID로 참조해야 한다.')
    if not pcs and not _text(data.get('physical_not_applicable_reason')):
        issues.append('FATAL-CONTRA: PC가 없으면 동일 속성의 상반 요구가 성립하지 않는 이유를 physical_not_applicable_reason에 기록하라.')
    if pcs and _text(data.get('physical_not_applicable_reason')):
        issues.append('FATAL-CONTRA: PC가 있으면서 PC 미적용 이유를 기록할 수 없다.')
    for i, pc in enumerate(pcs):
        issues += _required(pc, ('label','element','parameter','state_a','reason_a','state_b','reason_b'), f'physical_contradictions[{i}]')
        if _text(pc.get('state_a')) and pc['state_a'].strip() == str(pc.get('state_b','')).strip():
            issues.append(f'FATAL-CONTRA: PC[{i}]의 두 상태가 동일하다.')
        if pc.get('derived_from_tc_label') and not _reference(pc.get('derived_from_tc_label'),known_labels):
            issues.append(f'FATAL-CONTRA: PC[{i}].derived_from_tc_label이 현재 TC label을 참조하지 않는다.')
    pc_labels = [pc.get('label') for pc in pcs]
    if len({str(label) for label in pc_labels}) != len(pc_labels):
        issues.append('FATAL-CONTRA: 물리적 모순 label은 고유해야 한다.')
    return issues


def unknown_constraint_references(data, known_ids, *, declared_constraint_ids=(),
                                  max_nodes=20000, max_chars=2000000, max_issues=25):
    """Check explicit CON-xxxxxxxx references in JSON values without rewriting them.

    Only the constraint-discovery caller may pass IDs declared by its own
    ``constraints`` rows. Other artifacts must resolve to the supplied state IDs;
    an arbitrary ``constraints`` key in model output never grants an exemption.
    ASCII boundaries intentionally allow Korean particles immediately after IDs.
    Exceeding the inspection budget returns an issue instead of a partial PASS.
    """
    import re

    known = {value for value in (*known_ids, *declared_constraint_ids) if isinstance(value, str)}
    pattern = re.compile(r'(?<![A-Za-z0-9_-])CON-[0-9a-fA-F]{8}(?![A-Za-z0-9_-])')
    pending = [(data, '$')]
    visited = chars = 0
    seen_unknown = set()
    issues = []
    while pending:
        value, path = pending.pop()
        visited += 1
        if visited > max_nodes:
            return issues + ['FATAL-CONSTRAINT-REF: 제약 참조 검사 항목 한도를 초과했다. 출력 구조를 줄여 다시 제출하라.']
        if isinstance(value, dict):
            if visited + len(pending) + len(value) > max_nodes:
                return issues + ['FATAL-CONSTRAINT-REF: 제약 참조 검사 항목 한도를 초과했다. 출력 구조를 줄여 다시 제출하라.']
            pending.extend((item, (path + '.' + str(key)[:80])[-300:]) for key, item in reversed(list(value.items())))
        elif isinstance(value, list):
            if visited + len(pending) + len(value) > max_nodes:
                return issues + ['FATAL-CONSTRAINT-REF: 제약 참조 검사 항목 한도를 초과했다. 출력 구조를 줄여 다시 제출하라.']
            pending.extend((value[index], (path + f'[{index}]')[-300:]) for index in range(len(value) - 1, -1, -1))
        elif isinstance(value, str):
            chars += len(value)
            if chars > max_chars:
                return issues + ['FATAL-CONSTRAINT-REF: 제약 참조 검사 문자 한도를 초과했다. 출력을 줄여 다시 제출하라.']
            for match in pattern.finditer(value):
                ref = match.group()
                if ref not in known and ref not in seen_unknown:
                    if len(issues) >= max_issues:
                        return issues + ['FATAL-CONSTRAINT-REF: 미등록 제약 참조가 너무 많다. 현재 제약 ID만 사용해 전체 출력을 수정하라.']
                    seen_unknown.add(ref)
                    issues.append(f'FATAL-CONSTRAINT-REF: {path}의 {ref}가 현재 제약 목록에 없다. 정확한 ID를 인용하거나 근거 없는 참조를 제거하라.')
    return issues
