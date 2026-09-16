"""Reports compile the pinned selection snapshot, without generating new claims."""
import html
import json
from . import ledger

LABELS={'READY':'검증 통과','CONDITIONAL':'조건부 검토','REJECTED':'제외','NOT_RUN':'미실행','UNKNOWN':'미확인','PASS':'통과','FAIL':'실패'}


def manifest(state):
    sid=state.scratch.get('ax_report_snapshot_id') or state.scratch['ax_snapshot_id']
    snap=ledger.snapshot(state.run_id,sid,state.user_id)
    values={k:v['payload'] for k,v in snap['artifacts'].items()}
    return sid,values


def markdown(state):
    sid,v=manifest(state)
    selection=v.get('selection',{})
    rows=selection.get('candidates',[])
    status={r['candidate_id']:r for r in rows}
    lines=['# TRIZ 분석 보고서','',v.get('input',{}).get('raw_query',state.raw_query),'',
           '## 검증·선택','', '검증 통과 후보: '+str(len(selection.get('recommended',[]))),
           '','생성된 기구와 기대 효과는 설계 가설입니다. 시험 결과가 없는 후보는 조건부 검토로 표시합니다.','']
    for c in v.get('concepts',{}).get('candidates',[]):
        r=status.get(c['id'],{'status':'CONDITIONAL','missing':['선택 판정 없음']})
        lines += ['### '+c['title'],'', '**'+LABELS.get(r['status'],r['status'])+'**','',
            c.get('one_liner',''),'', '작동 원리(가설): '+c.get('working_principle',''),'',
            '모순 해소 근거(가설): '+c.get('resolution_argument',''),'',
            '기대 효과(미검증): '+c.get('expected_effect',''),'']
        for text in r.get('missing',[]):
            lines.append('- '+text)
        lines += ['', '적용 조건: '+'; '.join(c.get('assumptions',[])+c.get('transfer_conditions',[])),
            '', '시험 계획 및 결과:','']
        for o in r.get('obligations',[]):
            lines.append('- '+LABELS.get(o['status'],o['status'])+': '+json.dumps(o['description'],ensure_ascii=False))
        lines.append('')
    lines += ['## 분석 근거','']
    for c in v.get('definition',{}).get('technical_contradictions',[]):
        lines += ['- '+c.get('if_action','')+' → '+c.get('then_good','')+' / '+c.get('but_bad','')]
    lines += ['', '## 참고 자료','']
    for e in v.get('evidence',{}).get('sources',[]):
        lines += ['- '+e.get('title','')+' — '+e.get('url','')+' (자료 범위: '+e.get('evidence_scope','metadata')+')']
    lines += ['', '분석 버전: '+sid]
    return '\n'.join(lines)


def html_report(state):
    # Escaping also protects reports from source text containing HTML or scripts.
    from ..report_content import render_markdown
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><title>TRIZ 분석 보고서</title><style>body{max-width:960px;margin:40px auto;padding:20px;font:16px/1.8 system-ui;overflow-wrap:anywhere}h2{border-bottom:1px solid #ccc}</style><body>'+render_markdown(markdown(state))+'</body></html>'
