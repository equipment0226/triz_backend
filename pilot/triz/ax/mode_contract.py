"""Pinned new-run contracts. Missing version means the persisted legacy behavior."""
from copy import deepcopy

VERSION = 'ax-run-v2'
PROFILE_VERSION = 'triz-modes-v2'
TRACKS = ('A_MATRIX', 'B_SEPARATION', 'C_STANDARDS', 'D_ARIZ',
          'E_TRIMMING', 'F_TRENDS', 'G_FOS', 'H_EFFECTS')
PROFILES = {
    'LITE': dict(tracks=['A_MATRIX', 'B_SEPARATION', 'E_TRIMMING', 'H_EFFECTS'],
                 recovery_targets=1, repairs_per_blocker=1, recovery_additions=1,
                 expansion_rounds=1, max_optional_rounds=2, optional_budget_microusd=200000),
    'FULL': dict(tracks=[t for t in TRACKS if t != 'D_ARIZ'],
                 recovery_targets=2, repairs_per_blocker=2, recovery_additions=4,
                 expansion_rounds=2, max_optional_rounds=6, optional_budget_microusd=600000),
    'DEEP': dict(tracks=list(TRACKS), recovery_targets=0, repairs_per_blocker=0,
                 recovery_additions=0, expansion_rounds=0, max_optional_rounds=0, optional_budget_microusd=0),
}


def contract(state):
    value = state.scratch.get('ax_bundle', {}).get('run_contract', {})
    return value if value.get('version') == VERSION else {}


def optional_enabled(state):
    value = contract(state)
    return value.get('smart_orchestration_enabled', True)


def pin(mode, *, smart=True):
    profile = deepcopy(PROFILES[mode])
    optional = smart and mode != 'DEEP'
    return dict(version=VERSION, mode_profile_version=PROFILE_VERSION, mode=mode,
                profile=profile, trace_and_snapshot_enabled=True, coherence_checks_enabled=True,
                portfolio_preservation_enabled=True, smart_orchestration_enabled=optional,
                routing_policy_mode='RULE_BASED' if optional else 'OFF',
                bounded_recovery_enabled=optional, effect_history_enabled=True,
                effect_reranking_mode='ADVISORY' if mode == 'DEEP' else 'BASELINE',
                training_collection_scope='PROJECT_ONLY_WITH_EXPLICIT_CONSENT',
                model_roles={'LITE': 'T1', 'REASONING': 'T2', 'INDEPENDENT_REVIEW': 'T3',
                             'FLASH': 'T2', 'EXPERT': 'T2'})


def execution_plan(state):
    from .. import domain
    value = contract(state)
    expected = list(value['profile']['tracks'])
    skipped, blocked = {}, {}
    for track in expected:
        if track == 'C_STANDARDS' and not domain.physical_allowed(state):
            skipped[track] = '물리적 대상이 없는 문제이므로 물질–장 분석은 적용하지 않습니다.'
        elif ((track == 'A_MATRIX' and not state.definition.technical_contradictions)
              or (track == 'B_SEPARATION' and not state.definition.physical_contradictions)
              or (track == 'C_STANDARDS' and not state.analysis.su_fields)
              or (track == 'E_TRIMMING' and not state.definition.trimming)):
            blocked[track] = '기법 실행에 필요한 선행 분석 입력이 없습니다. 적용 불가로 간주하지 않습니다.'
    required = [t for t in expected if t not in skipped and t not in blocked]
    return expected, required, skipped, blocked


def validate_tracks(state, tracks):
    value = contract(state)
    if not value:
        return
    if state.control.mode.value != value['mode']:
        raise ValueError('Pinned mode changed; an explicit new run is required')
    if set(tracks) - set(value['profile']['tracks']):
        raise ValueError('Track is forbidden by the pinned mode profile')


def coverage(state):
    value = contract(state)
    if not value:
        return {}
    execution = state.scratch.get('ax_track_execution', {})
    planned = value['profile']['tracks']
    buckets = {key: [] for key in ('executed', 'not_applicable', 'blocked_missing_input',
                                  'failed', 'budget_unrun', 'pending')}
    names = {'COMPLETED': 'executed', 'REVIEWED_NO_APPLICATION': 'executed',
             'NOT_APPLICABLE': 'not_applicable', 'BLOCKED_MISSING_INPUT': 'blocked_missing_input',
             'FAILED': 'failed', 'NOT_RUN_BUDGET': 'budget_unrun'}
    for track in planned:
        buckets[names.get(execution.get(track, {}).get('status'), 'pending')].append(track)
    return dict(contract=PROFILE_VERSION, mode=value['mode'], planned=planned, **buckets,
                complete=not any(buckets[k] for k in ('blocked_missing_input', 'failed', 'budget_unrun', 'pending')))
