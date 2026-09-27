"""Required S5 coverage is independent of optional AX recovery and bundle age."""
from . import domain
from .settings import settings

TRACKS = ('A_MATRIX', 'B_SEPARATION', 'C_STANDARDS', 'D_ARIZ',
          'E_TRIMMING', 'F_TRENDS', 'G_FOS', 'H_EFFECTS')
DEFAULTS = {
    'LITE': ['A_MATRIX', 'B_SEPARATION', 'E_TRIMMING'],
    'FULL': ['A_MATRIX', 'B_SEPARATION', 'C_STANDARDS', 'E_TRIMMING', 'F_TRENDS', 'H_EFFECTS'],
    'DEEP': list(TRACKS),
}
OUTPUT_FIELDS = dict(zip(TRACKS, ('principle_apps', 'separation_apps', 'standard_apps',
                                'ariz', 'raw_ideas', 'trend_apps', 'fos_apps', 'effect_apps')))


def plan(state):
    mode = state.control.mode.value
    expected = list(dict.fromkeys(DEFAULTS[mode] + list(settings.cfg('tracks.' + mode, []))
                                  + list(state.control.enabled_tracks)))
    allowed = domain.select_tracks(state, expected)
    expected = [t for t in TRACKS if t in expected or t in allowed]
    reasons = {}
    for t in expected:
        if t not in allowed:
            reasons[t] = '문제의 물리적 적용 범위가 없어 이 분석 기법을 적용하지 않습니다.'
        elif t == 'A_MATRIX' and not state.definition.technical_contradictions:
            reasons[t] = 'S4에서 기술적 모순이 도출되지 않았습니다.'
        elif t == 'B_SEPARATION' and not state.definition.physical_contradictions:
            reasons[t] = 'S4에서 물리적 모순이 도출되지 않았습니다.'
        elif t == 'C_STANDARDS' and not state.analysis.su_fields:
            reasons[t] = 'S3에서 표준해 적용 대상 물질–장 모델이 도출되지 않았습니다.'
        elif t == 'E_TRIMMING' and not state.definition.trimming:
            reasons[t] = 'S4에서 구체화할 트리밍 후보가 도출되지 않았습니다.'
    required = [t for t in expected if t not in reasons]
    if 'D_ARIZ' in required:
        required = ['D_ARIZ'] + [t for t in required if t != 'D_ARIZ']
    return expected, required, reasons


def application_count(state, track):
    value = getattr(state.solve, OUTPUT_FIELDS[track])
    if track == 'E_TRIMMING':
        return sum(idea.track == track for idea in value)
    return int(value is not None) if track == 'D_ARIZ' else len(value)


def concept_review_limit(state):
    """Apply the current DEEP review breadth without changing the pinned budget."""
    limit = int(state.scratch['ax_bundle']['limits']['detailed_candidates'])
    return max(8, limit) if state.control.mode.value == 'DEEP' else limit


def check_applications(data):
    """Empty analysis must be justified, not confused with successful generation."""
    if not isinstance(data, dict) or not isinstance(data.get('applications'), list):
        return ['FATAL-S5-OUTPUT: applications 배열을 제공해야 합니다.']
    apps = data['applications']
    if not apps:
        if not isinstance(data.get('no_application_reason'), str) or not data['no_application_reason'].strip():
            return ['FATAL-S5-EMPTY: 적용안이 없으면 검토한 조건과 배제 근거를 no_application_reason에 적으세요.']
        return []
    if any(not isinstance(a, dict) or not isinstance(a.get('idea'), str) or not a['idea'].strip() for a in apps):
        return ['FATAL-S5-IDEA: 각 applications 항목에 실제 적용 기구를 설명하는 idea가 필요합니다.']
    return []


APPLICATION_CONTRACT = (
    '\n\n[S5 적용 결과 계약 v1]\n'
    'applications 배열을 반드시 반환한다. 각 적용안의 idea에 대상 문제에 적용할 구체적 기구를 설명한다. '
    '검토 후 적용할 수 있는 안이 없으면 applications: []와 no_application_reason을 반환한다. '
    'no_application_reason에는 검토한 적용 조건과 배제 근거를 적는다. 개수를 채우기 위해 적용안을 만들지 마라.'
)
