"""Read-only projection of pinned AX artifacts into the shared TRIZ report."""
import copy
from . import ledger

CONTEXT_KEYS = ('title', 'param_scheme', 'excluded_concepts', 's_curve', 'taboo',
                'principle_patents', 'patent_additions', 'related_references',
                'evidence_mappings', 'evidence_gaps', 'search_status',
                'ax_coordination', 'ax_coherence', 'ax_recovery')


def context(state):
    """Capture report-only metadata alongside the selection, before rendering."""
    return {'created_at': state.created_at.isoformat(),
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


def markdown(state, *, diagram=None, references=None):
    from ..render import render_report
    projected = project(state)
    return render_report(projected, projected.report.narrative, template='report_full.md.j2',
                         diagram=diagram, references=references)


def html_report(state):
    from ..render import render_html
    return render_html(project(state))
