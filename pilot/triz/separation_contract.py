"""Run-local physical-contradiction approaches; no workflow or model calls."""
from copy import deepcopy

from . import knowledge as K

LEGACY_VERSION = 'legacy-separation-4-v1'
ALIASES = {'RELATION': 'CONDITION', 'RELATION_CONDITIONS': 'CONDITION'}


def canonical_kind(value):
    if not isinstance(value, str):
        return value
    value = value.strip().upper()
    return ALIASES.get(value, value)


def legacy_catalog():
    """Frozen pre-patch data, exclusively for old AX pins and old report labels."""
    return deepcopy(K._load('separation_legacy_v1.json'))


def is_legacy(catalog):
    return bool(catalog) and not any(row.get('catalog_version') for row in catalog.values())


def catalog_for(state=None):
    if state is not None:
        from .ax import enabled
        if enabled(state):
            bundle = state.scratch.get('ax_bundle')
            if not isinstance(bundle, dict) or not bundle.get('prompts'):
                raise ValueError('Missing AX execution bundle for separation contract')
            if 'separation_catalog' not in bundle:
                return legacy_catalog()
            catalog = bundle['separation_catalog']
            # A malformed new snapshot must never downgrade into four approaches.
            if (not isinstance(catalog, dict) or set(catalog) != set(K.separation())
                    or any(not isinstance(row, dict) or not row.get('catalog_version')
                           for row in catalog.values())):
                raise ValueError('Invalid pinned separation catalog')
            return deepcopy(catalog)
    return deepcopy(K.separation())


def _metadata(row, legacy):
    return {
        'approach_name': row['name_ko'],
        'approach_family': row.get('family', 'SEPARATE'),
        'catalog_version': row.get('catalog_version', LEGACY_VERSION),
        'catalog_sources': [] if legacy else [{
            'title': 'MATRIZ Wiki · Algorithm of resolving physical contradictions',
            'url': row['source_url'], 'section': row['source_section'],
            'accessed_on': row['source_accessed_on'],
        }],
        'recommended_principles': deepcopy(row['principles']),
        'principle_selection_policy': row.get('selection_policy', 'LEGACY'),
    }


def normalize(data, *, catalog=None):
    """Bind server provenance, leaving malformed/missing reviews visible to check."""
    catalog = K.separation() if catalog is None else catalog
    legacy = is_legacy(catalog)
    result = deepcopy(data)
    if not isinstance(result, dict) or not isinstance(result.get('applications'), list):
        return result
    for app in result['applications']:
        if not isinstance(app, dict):
            continue
        # Only _track_b can bind the actual selected PC after validation. A
        # standalone prompt result cannot establish its own source identity.
        app.pop('source_pc_id', None)
        kind = canonical_kind(app.get('kind'))
        app['kind'] = kind
        row = catalog.get(kind) if isinstance(kind, str) else None
        if row is None:
            continue
        app.update(_metadata(row, legacy))
        actual = app.get('supporting_principles')
        if legacy:
            status = 'LEGACY_UNREVIEWED'
        elif not isinstance(actual, list) or any(type(pid) is not int or str(pid) not in K.principles() for pid in actual):
            status = 'INVALID'
        elif not actual:
            status = 'UNSPECIFIED'
        elif row['selection_policy'] == 'UNRESTRICTED':
            status = 'UNRESTRICTED'
        elif any(pid not in row['principles'] for pid in actual):
            status = 'EXTENDED'
        else:
            status = 'RECOMMENDED'
        app['principle_selection_status'] = status
    return result


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def check(data, *, catalog=None):
    catalog = K.separation() if catalog is None else catalog
    legacy = is_legacy(catalog)
    prefix = 'DET-B1: ' if legacy else 'FATAL-SEPARATION: '
    if not isinstance(data, dict) or not isinstance(data.get('applications'), list):
        return [prefix+'applications 배열을 포함한 객체가 필요합니다.']
    apps = data['applications']
    if legacy:
        # Match the old presence-only contract for already-pinned executions.
        # Do not rewrite their meanings or require three reviews they never ran.
        kinds = {canonical_kind(a.get('kind')) for a in apps
                 if isinstance(a, dict) and isinstance(a.get('kind'), str)}
        missing = set(catalog) - kinds
        return [prefix+'다음 분리 원리가 검토되지 않았다: '+', '.join(sorted(missing))] if missing else []
    issues, seen = [], set()
    def fail(message):
        issues.append(prefix+message)
    for index, app in enumerate(apps, 1):
        if not isinstance(app, dict):
            fail(f'{index}번째 검토 결과는 객체여야 합니다.')
            continue
        kind = canonical_kind(app.get('kind'))
        if not isinstance(kind, str) or kind not in catalog:
            fail(f'{index}번째 결과의 kind가 카탈로그에 없습니다.')
            continue
        if kind in seen:
            fail(f'{kind} 검토 결과가 중복되었습니다.')
        seen.add(kind)
        if type(app.get('applicable')) is not bool:
            fail(f'{kind}: applicable은 bool이어야 합니다.')
        elif app['applicable']:
            for field in ('how', 'title', 'idea'):
                if not _text(app.get(field)):
                    fail(f'{kind}: 적용안의 {field} 설명이 필요합니다.')
            # Keep RawIdea construction inside the existing repair boundary;
            # do not coerce malformed evidence into invented resource/ID text.
            for field in ('uses_resources', 'hypothesis_ids'):
                if field in app and (not isinstance(app[field], list)
                        or any(not isinstance(value, str) for value in app[field])):
                    fail(f'{kind}: {field}는 문자열 배열이어야 합니다.')
            for field in ('mechanism', 'mechanism_key', 'intervention_variable',
                          'strongest_objection', 'self_rebuttal', 'validation_test'):
                if field in app and not isinstance(app[field], str):
                    fail(f'{kind}: {field}는 문자열이어야 합니다.')
            if 'feasibility_hint' in app and app['feasibility_hint'] not in ('HIGH', 'MID', 'LOW'):
                fail(f'{kind}: feasibility_hint는 HIGH/MID/LOW 중 하나여야 합니다.')
        elif not _text(app.get('not_applicable_reason')):
            fail(f'{kind}: 미적용 사유가 필요합니다.')
        actual = app.get('supporting_principles')
        if not isinstance(actual, list):
            fail(f'{kind}: supporting_principles는 실제 사용 ID 배열이어야 합니다.')
            continue
        if any(type(pid) is not int or str(pid) not in K.principles() for pid in actual):
            fail(f'{kind}: 유효한 40원리 정수 ID만 사용할 수 있습니다.')
            continue
        if len(actual) != len(set(actual)):
            fail(f'{kind}: 실제 사용 원리 ID가 중복되었습니다.')
        row = catalog[kind]
        extended = row['selection_policy'] != 'UNRESTRICTED' and any(pid not in row['principles'] for pid in actual)
        if (extended or (app.get('applicable') is True and not actual)) and not _text(app.get('principle_selection_reason')):
            fail(f'{kind}: 권장 밖 원리 선택 또는 원리 번호 미확인의 근거를 principle_selection_reason에 적어야 합니다.')
        for field, expected in _metadata(row, False).items():
            if field in app and app[field] != expected:
                fail(f'{kind}: {field}는 서버 카탈로그와 일치해야 합니다.')
    missing = [kind for kind in catalog if kind not in seen]
    if missing:
        fail('필수 접근 검토 누락: '+', '.join(missing))
    return issues


def display_name(application):
    """Read-only labels: historical CONDITION remains broad condition separation."""
    if not isinstance(application, dict):
        return '확인되지 않은 해결 접근'
    kind = canonical_kind(application.get('kind') or application.get('separation_type'))
    if not isinstance(kind, str):
        return '확인되지 않은 해결 접근'
    version = application.get('catalog_version')
    if version and version != LEGACY_VERSION and _text(application.get('approach_name')):
        return application['approach_name']
    # Without provenance, retain historical labels where defined. New kinds have
    # no historical interpretation and may use their canonical display name.
    row = legacy_catalog().get(kind) or K.separation().get(kind)
    return row['name_ko'] if row else '확인되지 않은 해결 접근'
