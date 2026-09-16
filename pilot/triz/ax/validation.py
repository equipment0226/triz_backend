"""Recommendation maturity is independent of preference, rank and generation."""


def selection(state):
    from . import ledger
    versions=state.scratch.get('ax_members',{})
    observations=[r['payload'] for r in ledger.active_reviews(state.run_id,state.user_id)
        if r['payload']['target_version_id']==versions.get('concepts') and
        r['payload']['decision_type'] in ('RECORD_TEST_RESULT','RECORD_FIELD_RESULT')]
    rows=[]
    for candidate in state.concepts:
        check=state.check_for(candidate.id)
        missing=[]
        if candidate.quality_status!='PASS':
            missing.append('독립 기구 검토 미통과')
        if not check or check.verdict!='PASS':
            missing.append('필수 제약 검증 미완료')
        elif state.constraints.hard_items():
            verified={r.get('constraint_id') for r in check.per_constraint if r.get('verdict')=='PASS'}
            if {r.id for r in state.constraints.hard_items()}-verified:
                missing.append('필수 제약별 판정 누락')
        if not candidate.resolution_argument or not candidate.addresses_contradictions:
            missing.append('모순 해소 연결 미확인')
        if not candidate.working_principle or not candidate.validation_plan:
            missing.append('작동 기구 또는 검증 계획 누락')
        # A generated test plan or bibliography never certifies a performed test.
        obligations=[]
        for i,plan in enumerate(candidate.validation_plan):
            oid=candidate.id+':test:'+str(i)
            recorded=[r for r in observations if r['obligation_id']==oid and r['candidate_id']==candidate.id]
            # Conflicting unsuperseded observations cannot silently replace a failure.
            status=('FAIL' if any(r['result']=='FAIL' for r in recorded) else
                    'PASS' if recorded and all(r['result']=='PASS' for r in recorded) else 'NOT_RUN')
            obligations.append({'id':oid,'description':plan,'status':status,
                'review_ids':[r['event_id'] for r in recorded],'required_for_recommendation':True})
        if not obligations or any(o['status']!='PASS' for o in obligations):
            missing.append('계획한 성능·적용 시험 결과 미등록')
        status='REJECTED' if (check and check.verdict=='FAIL') or candidate.quality_status=='REJECT' or any(o['status']=='FAIL' for o in obligations) else (
               'CONDITIONAL' if missing else 'READY')
        rows.append({'candidate_id':candidate.id,'status':status,'missing':missing,'obligations':obligations,
                     'evidence_ids':candidate.evidence_ids,'quality_status':candidate.quality_status,
                     'constraint_verdict':check.verdict if check else 'UNKNOWN'})
    return {'candidates':rows,'recommended':[r['candidate_id'] for r in rows if r['status']=='READY'],
            'conditional':[r['candidate_id'] for r in rows if r['status']=='CONDITIONAL'],
            'status':'COMPLETE' if rows else 'NO_CANDIDATES',
            'scope':'개념 검토와 실제 시험 결과를 구분한 판정'}
