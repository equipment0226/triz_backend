"""Recover report relationships from saved provenance, without rewriting analysis."""
from .report_style import plain_text


def _same(a, b):
    keys = [k for k in ('title', 'idea', 'how', 'not_applicable_reason', 'resulting_su_field') if a.get(k)]
    return bool(keys) and all(plain_text(str(a[k])).strip() == plain_text(str(b.get(k, ''))).strip() for k in keys)


def sources(state, app, kind):
    collections = {'tc':state.definition.technical_contradictions,
                   'pc':state.definition.physical_contradictions, 'su':state.analysis.su_fields}
    valid = {c.id for c in collections[kind]}
    explicit = app.get('source_' + kind + '_id')
    if isinstance(explicit, str) and explicit in valid:
        return {explicit}
    node = {'tc':'s5_track_a', 'pc':'s5_track_b', 'su':'s5_track_c'}[kind]
    matched = set()
    for step in state.steps:
        if step.node != node or not isinstance(step.output_json, dict):
            continue
        if any(_same(app, candidate) for candidate in step.output_json.get('applications', []) if isinstance(candidate, dict)):
            matched.update(identifier for identifier in valid if identifier in step.label)
    if matched:
        return matched
    for idea in state.solve.raw_ideas:
        if _same(app, idea.detail):
            matched.update(set(idea.addresses) & valid)
    if matched:
        return matched
    # An unambiguous single source is safe; never guess by list position.
    return valid if len(valid) == 1 else set()


def matrix_groups(state):
    groups, used = [], set()
    for index, lookup in enumerate(state.solve.matrix_lookups):
        tcs = [t for t in state.definition.technical_contradictions if
               (lookup.source_tc_id == t.id if lookup.source_tc_id else
                (t.improving_param_id, t.worsening_param_id) ==
                (lookup.improving_param_id, lookup.worsening_param_id))]
        ids = {t.id for t in tcs}
        problems = [k.title for k in state.definition.key_problems if ids.intersection(k.contradiction_ids)]
        title = ' / '.join(dict.fromkeys(problems or [t.label or t.if_action for t in tcs]))
        title = title or f'개선 파라미터 {lookup.improving_param_id} · 악화 파라미터 {lookup.worsening_param_id}'
        apps = []
        for i, app in enumerate(state.solve.principle_apps):
            if sources(state, app, 'tc') & ids:
                apps.append(app); used.add(i)
        groups.append(dict(key=f'matrix-{index}', title=title, lookup=lookup, apps=apps))
    return groups, [app for i, app in enumerate(state.solve.principle_apps) if i not in used]


def separation_groups(state):
    from .knowledge import separation
    from .separation_contract import canonical_kind
    groups, used = [], set()
    for index, pc in enumerate(state.definition.physical_contradictions):
        apps = []
        for i, app in enumerate(state.solve.separation_apps):
            if pc.id in sources(state, app, 'pc'):
                apps.append(app); used.add(i)
        if apps:
            groups.append(dict(key=f'separation-{index}', title=pc.label or f'{pc.element}의 {pc.parameter}',
                contradiction=f'{pc.element}의 {pc.parameter}: {pc.state_a} / {pc.state_b}', apps=apps))
    unlinked = [a for i, a in enumerate(state.solve.separation_apps) if i not in used]
    if unlinked:
        groups.append(dict(key='separation-unlinked', title='대상 모순 연결 확인이 필요한 적용안',
            contradiction='저장된 분석 기록에 대상 모순을 확인할 연결 정보가 없다.', apps=unlinked))
    known = separation()
    pcs = {pc.id: pc for pc in state.definition.physical_contradictions}
    for group in groups:
        group['diagrams'] = []
        for index, app in enumerate(group['apps']):
            kind = canonical_kind(app.get('kind'))
            if app.get('applicable') is not True or not isinstance(kind, str) or kind not in known:
                continue
            # Each proposal has its own content, even when it uses the same
            # approach as another proposal. Context requires a recorded PC id.
            pc_id = app.get('source_pc_id')
            pc = pcs.get(pc_id) if isinstance(pc_id, str) else None
            group['diagrams'].append(dict(key=f"{group['key']}-application-{index}",
                application=app, contradiction=pc.model_dump(mode='json') if pc else None))
    return groups


def effect_groups(state):
    names = {'PHYSICAL':'물리 효과', 'CHEMICAL':'화학 효과', 'GEOMETRIC':'기하학 효과', 'BIOLOGICAL':'생물학 효과', 'INFORMATIONAL':'정보·제어 효과'}
    groups = {}
    for app in state.solve.effect_apps:
        category = names.get(app.get('effect_domain'), app.get('effect_domain') or '미분류 효과')
        groups.setdefault(category, []).append(app)
    return [dict(title=k, apps=v) for k, v in groups.items()]


def _separation_source_leaves(idea):
    """Read the explicit source packets written by idea_consolidation._sources.

    A representative keeps its first raw ID, so looking up that ID in the current
    inventory again would lose its original application. Use its saved packet.
    """
    from copy import deepcopy

    detail = idea.detail
    packets = detail.get('source_details')
    if packets is None:
        # A multi-source representative without saved packets has lost the
        # application-level lineage; its retained base detail is insufficient.
        if any(ident != idea.id for ident in idea.source_idea_ids):
            return []
        row = idea.model_dump(mode='json', exclude={'detail'})
        row.update(deepcopy(detail))
        row.update(source_idea_id=idea.id, source_track=idea.track, addresses=list(idea.addresses))
        return [row]
    if not isinstance(packets, list) or not packets:
        return []
    allowed = {ident for ident in idea.source_idea_ids if isinstance(ident, str) and ident}
    result = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        ident = packet.get('source_idea_id')
        if not isinstance(ident, str) or ident not in allowed:
            continue
        # The current merge contract stores flattened original leaves. Unknown
        # nested representatives are not reinterpreted as applied mechanisms.
        ancestry = packet.get('source_idea_ids', [])
        if (not isinstance(ancestry, list) or packet.get('source_details')
                or any(not isinstance(source, str) or source != ident for source in ancestry)):
            continue
        result.append(deepcopy(packet))
    return result


def separation_solution_groups(state):
    """Join final concepts to recorded Track B origins through explicit IDs only.

    These are derivation records, not assertions that every merged approach was
    retained in the final mechanism. No app/title similarity or PC fallback is
    used to attach an application to a solution.
    """
    import json
    from copy import deepcopy
    from .separation_contract import canonical_kind

    known_kinds = {'SPACE', 'TIME', 'CONDITION', 'DIRECTION', 'SYSTEM_LEVEL', 'SATISFY', 'BYPASS'}
    ideas, duplicate_ideas = {}, set()
    for idea in state.solve.raw_ideas:
        if idea.id in ideas:
            duplicate_ideas.add(idea.id)
        ideas[idea.id] = idea
    pcs, duplicate_pcs = {}, set()
    for pc in state.definition.physical_contradictions:
        if pc.id in pcs:
            duplicate_pcs.add(pc.id)
        pcs[pc.id] = pc

    groups = []
    for concept_index, concept in enumerate(state.concepts):
        leaves, signatures, conflicting = {}, {}, set()
        for source_id in dict.fromkeys(concept.source_idea_ids):
            if source_id in duplicate_ideas or source_id not in ideas:
                continue
            for leaf in _separation_source_leaves(ideas[source_id]):
                ident = leaf['source_idea_id']
                signature = json.dumps(leaf, ensure_ascii=False, sort_keys=True, default=str)
                if ident in signatures and signatures[ident] != signature:
                    conflicting.add(ident)
                else:
                    signatures[ident] = signature
                    leaves.setdefault(ident, leaf)
        app_index = 0
        for source_id, application in leaves.items():
            kind = canonical_kind(application.get('kind'))
            if (source_id in conflicting or application.get('source_track') != 'B_SEPARATION'
                    or application.get('applicable') is not True
                    or not isinstance(kind, str) or kind not in known_kinds):
                continue
            pc_id = application.get('source_pc_id')
            if not pc_id:
                addresses = application.get('addresses')
                linked = ({value for value in addresses if isinstance(value, str) and value in pcs}
                          if isinstance(addresses, list) else set())
                pc_id = next(iter(linked)) if len(linked) == 1 else None
            pc = pcs.get(pc_id) if isinstance(pc_id, str) and pc_id not in duplicate_pcs else None
            solution = concept.model_dump(mode='json')
            solution['provenance_label'] = '도출 원안의 분리 적용 기록'
            groups.append(dict(key=f'concept-separation-{concept_index}-{app_index}',
                application=deepcopy(application),
                contradiction=pc.model_dump(mode='json') if pc else None,
                solution=solution))
            app_index += 1
    return groups
