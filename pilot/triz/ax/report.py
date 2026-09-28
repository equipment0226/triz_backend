"""Read-only projection of pinned AX artifacts into the shared TRIZ report."""
import copy
from . import ledger

CONTEXT_KEYS = ('title', 'title_source', 'param_scheme', 'excluded_concepts', 's_curve', 'taboo',
                'principle_patents', 'patent_additions', 'related_references',
                'evidence_mappings', 'evidence_gaps', 'search_status',
                'ax_coordination', 'ax_coherence', 'ax_recovery',
                'ax_track_execution', 'ax_solve_start_seq', 'ax_candidate_review',
                'idea_consolidation', 'constraint_normalization', 'ax_idea_inventory',
                'ax_effect_applications', 'ax_action_results', 'semantic_episode_id',
                'candidate_review_revisions','candidate_dispositions','s6_lineage_reviews')

TRACK_LABELS = {
    'A_MATRIX': '모순행렬·발명원리', 'B_SEPARATION': '분리 원리',
    'C_STANDARDS': '76 표준해', 'D_ARIZ': 'ARIZ-85C', 'E_TRIMMING': '트리밍',
    'F_TRENDS': '기술 진화 트렌드', 'G_FOS': '기능지향탐색·특성 전이',
    'H_EFFECTS': '과학·기술 효과',
}
TRACK_STATUSES = {
    'COMPLETED': '실행 완료', 'REVIEWED_NO_APPLICATION': '검토 완료·적용안 없음',
    'NOT_APPLICABLE': '적용 대상 아님', 'PENDING': '실행 대기', 'FAILED': '실행 실패',
    'UNRECORDED': '현재 실행 상태 기록 없음',
    'BLOCKED_MISSING_INPUT': '선행 입력 부족·재개 필요', 'NOT_RUN_BUDGET': '예산 부족·미실행',
}


def execution_view(solve, control, scratch):
    """Describe saved execution evidence without inferring model success or quality."""
    records = scratch.get('ax_track_execution')
    records = records if isinstance(records, dict) else {}
    expected = set(records) if records else set(control.get('enabled_tracks') or [])
    fields = {'A_MATRIX': 'principle_apps', 'B_SEPARATION': 'separation_apps',
              'C_STANDARDS': 'standard_apps', 'F_TRENDS': 'trend_apps',
              'G_FOS': 'fos_apps', 'H_EFFECTS': 'effect_apps'}
    counts = {track: len(solve.get(field) or []) for track, field in fields.items()}
    counts['D_ARIZ'] = len((solve.get('ariz') or {}).get('steps') or [])
    counts['E_TRIMMING'] = sum(i.get('track') == 'E_TRIMMING' for i in solve.get('raw_ideas') or [])
    views = {}
    for track, name in TRACK_LABELS.items():
        if track not in expected and not counts.get(track):
            continue
        record = records.get(track)
        record = record if isinstance(record, dict) else {}
        status = record.get('status', 'UNRECORDED')
        status = status if status in TRACK_STATUSES else 'UNRECORDED'
        reason = str(record.get('reason') or '').strip()
        if not reason:
            reason = {
                'REVIEWED_NO_APPLICATION': '검토 결과 적용안이 없으나 구체적인 사유는 저장되지 않았다.',
                'NOT_APPLICABLE': '적용 대상이 아닌 것으로 기록되었으나 구체적인 사유는 저장되지 않았다.',
                'PENDING': '이번 해결 탐색에서 아직 실행 결과가 기록되지 않았다.',
                'FAILED': '이번 해결 탐색의 실행 실패로 적용 결과를 확인할 수 없다.',
                'UNRECORDED': '이전 형식에는 현재 회차의 실행 상태가 저장되지 않았다. 누적 호출 이력만으로 이번 실행을 판단할 수 없다.',
                'COMPLETED': '이번 회차의 실행 완료 기록이 있다. 내용의 검증 여부는 별도로 확인한다.',
                'BLOCKED_MISSING_INPUT': '필수 기법의 선행 입력이 부족하여 분석이 부분 완료되었습니다.',
                'NOT_RUN_BUDGET': '예산 부족으로 필수 기법이 미실행 상태입니다.',
            }[status]
        empty = reason
        if status == 'COMPLETED' and not counts.get(track):
            empty = '실행 완료로 기록되었지만 이 절에 표시할 적용안 또는 ARIZ 단계가 저장되지 않았다. ' + reason
        views[track] = {'track': track, 'name': name, 'status': status,
                         'label': TRACK_STATUSES[status], 'reason': reason,
                         'output_count': record.get('output_count', counts.get(track, 0)),
                         'stored_count': counts.get(track, 0), 'empty_message': empty}
    return views


def trace_view(steps, scratch):
    """The explicit S5 boundary separates earlier evidence from the current solve."""
    # A report row must not retain another copy of every prompt/model response.
    columns = ('seq', 'stage', 'label', 'agent_id', 'tier', 'verify_attempts',
               'status', 'human_intervened')
    rows = []
    for step in steps:
        row = {key: step[key] for key in columns if key in step}
        if 'verdicts' in step:
            row['verdicts'] = ([{'verdict': step['verdicts'][-1].get('verdict', '-')}]
                               if step['verdicts'] else [])
        rows.append(row)
    boundary = scratch.get('ax_solve_start_seq')
    if not isinstance(boundary, int) or isinstance(boundary, bool) or boundary < 0:
        return {'bounded': False, 'groups': [{'title': '누적 실행 이력', 'steps': rows}]}
    earlier = [step for step in rows if step.get('seq', 0) <= boundary]
    current = [step for step in rows if step.get('seq', 0) > boundary]
    groups = []
    if earlier:
        groups.append({'title': '이전 이력·이어받은 상위 단계', 'steps': earlier})
    groups.append({'title': '현재 해결 탐색 회차', 'steps': current})
    return {'bounded': True, 'start_seq': boundary, 'groups': groups}


def context(state):
    """Capture report-only metadata alongside the selection, before rendering."""
    from .mode_contract import coverage
    from .runtime import diagnostics
    return {'created_at': state.created_at.isoformat(),
            'mode_coverage':coverage(state), 'learning_summary':diagnostics(state),
            'cost': state.cost.model_dump(mode='json'),
            'control': state.control.model_dump(mode='json'),
            'steps': [s.model_dump(mode='json') for s in state.steps],
            'scratch': {k: copy.deepcopy(state.scratch[k]) for k in CONTEXT_KEYS if k in state.scratch},
            'narrative': copy.deepcopy(state.report.narrative) if state.report else {}}


def manifest(state):
    sid = state.scratch.get('ax_report_snapshot_id') or state.scratch['ax_snapshot_id']
    snap = ledger.snapshot(state.run_id, sid, state.user_id)
    return sid, {k: v['payload'] for k, v in snap['artifacts'].items()}


def project(state):
    """Never mix a frozen report with subsequently edited live analysis."""
    if getattr(state, '_ax_report_projection', False):
        return state
    from ..schema import GlobalState, ReportArtifact
    sid, v = manifest(state)
    inp, problem, checks = v.get('input', {}), v.get('problem', {}), v.get('constraints', {})
    meta = v.get('report_context', {})
    scratch = copy.deepcopy(meta.get('scratch', {}))
    scratch.update(evidence_mappings=v.get('evidence', {}).get('mappings', {}),
                   evidence_gaps=v.get('evidence', {}).get('gaps', []))
    missing = [name for key, name in (
        ('input', '문제 입력'), ('problem', '문제 범위'), ('analysis', '시스템 분석'),
        ('definition', 'TRIZ 문제 정의'), ('solve', '해결책 도출'),
        ('constraints', '제약 검토'), ('evaluation', '평가'), ('selection', '최종 검토')) if key not in v]
    if not meta:
        missing.append('이전 보고서 버전에 단계 이력·비용·부가 분석 메타데이터가 고정되지 않음')
    for section,field,label in (('analysis','nine_windows','9-Windows'),('analysis','components','구성요소'),
        ('analysis','function_edges','기능 모델'),('analysis','resources','가용 자원'),('analysis','ceca','인과사슬'),
        ('definition','ifr','이상 해결책')):
        if section in v and not v[section].get(field):
            missing.append(label+' 분석 기록 없음 — 미실행 또는 미저장 여부 확인 필요')
    intake = copy.deepcopy(inp.get('intake', {}))
    if problem.get('frame'):
        intake['frame'] = problem['frame']
    narrative = copy.deepcopy(meta.get('narrative') or v.get('report', {}).get('narrative') or {})
    narrative.setdefault('executive_summary', '\n\n'.join(filter(None, [
        intake.get('frame', {}).get('restated_problem') or inp.get('raw_query', ''),
        v.get('evaluation', {}).get('portfolio_note', '')])))
    narrative.setdefault('limitation_note', '후보의 기대 효과는 설계 가설이며, 실제 시험 결과와 개념 검토를 구분한다.')
    scratch['ax_report_details'] = {'snapshot_id': sid, 'missing': missing,
        'selection': v.get('selection', {}), 'metadata_missing': not bool(meta),
        'render_version': 'triz-full-ax-v2', 'coherence': v.get('coherence', {}),
        'effect_applicability': v.get('solve', {}).get('effect_applicability', [])}
    scratch['ax_report_tracks'] = execution_view(v.get('solve', {}), meta.get('control', {}), scratch)
    scratch['ax_report_trace'] = trace_view(meta.get('steps', []), scratch)
    scratch['ax_report_mode_coverage'] = copy.deepcopy(meta.get('mode_coverage', {}))
    scratch.setdefault('excluded_concepts', [
        {'idea': c.get('title', ''), 'reason': '; '.join(c.get('quality_issues', []))}
        for c in v.get('concepts', {}).get('excluded', [])])
    data = dict(run_id=state.run_id, user_id=state.user_id,
        raw_query=inp.get('raw_query', ''), intake=intake, domain=inp.get('domain', {}),
        confirm=problem.get('confirm', {}), constraints=checks.get('requirements') or problem.get('requirements', {}),
        analysis=v.get('analysis', {}), definition=v.get('definition', {}), solve=v.get('solve', {}),
        concepts=v.get('concepts', {}).get('candidates', []),
        evidence=v.get('evidence', {}).get('sources', []), constraint_checks=checks.get('results', []),
        evaluation=v.get('evaluation', {}), control=meta.get('control', {}), cost=meta.get('cost', {}),
        steps=meta.get('steps', []), scratch=scratch,
        report=ReportArtifact(narrative=narrative, template_id='report_full'))
    scratch['report_date'] = meta.get('created_at', '')[:16].replace('T', ' ') or '기록 미고정'
    if meta.get('created_at'):
        data['created_at'] = meta['created_at']
    result = GlobalState.model_validate(data)
    object.__setattr__(result, '_ax_report_projection', True)
    return result


def markdown(state, *, diagram=None, references=None, detail=None):
    from ..render import render_report
    projected = project(state)
    return render_report(projected, projected.report.narrative, template='report_full.md.j2',
                         diagram=diagram, references=references, detail=detail)


def html_report(state):
    from ..render import render_html
    return render_html(project(state))
