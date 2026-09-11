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
    if explicit in valid:
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
    return groups


def effect_groups(state):
    names = {'PHYSICAL':'물리 효과', 'CHEMICAL':'화학 효과', 'GEOMETRIC':'기하학 효과', 'BIOLOGICAL':'생물학 효과', 'INFORMATIONAL':'정보·제어 효과'}
    groups = {}
    for app in state.solve.effect_apps:
        category = names.get(app.get('effect_domain'), app.get('effect_domain') or '미분류 효과')
        groups.setdefault(category, []).append(app)
    return [dict(title=k, apps=v) for k, v in groups.items()]
