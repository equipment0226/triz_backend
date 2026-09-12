"""Synthetic report input shared by offline and read-only deployment checks."""
from triz.schema import GlobalState


def example_report():
    """Synthetic data only; suitable for browser and portable-report checks."""
    return GlobalState.model_validate(dict(run_id='introduction-design-review',raw_query='설비 세정의 생산성과 미세 패턴 보호',
        intake=dict(frame=dict(symptom='유속을 높이면 파티클은 줄지만 미세 패턴의 손상이 증가한다.')),
        analysis=dict(
            components=[dict(name=n) for n in ['세정액','웨이퍼','노즐','제어기']],
            function_edges=[dict(subject='세정액',object='웨이퍼',action='파티클 제거',kind='USEFUL'),
                dict(subject='세정액',object='웨이퍼',action='미세 패턴 손상',kind='HARMFUL',level='EXCESSIVE'),
                dict(subject='제어기',object='노즐',action='유속 제어'),dict(subject='노즐',object='세정액',action='분사')],
            su_fields=[dict(id='SU-example',label='세정 작용',s1='웨이퍼의 미세 패턴',s2='고속 세정액',field='유체의 운동 에너지',effect='HARMFUL',s3='추가 검토 중인 보호층')],
            ceca=dict(nodes=[dict(id='a',text='유속 증가',node_type='ROOT_CAUSE'),dict(id='b',text='패턴 강성 부족',node_type='ROOT_CAUSE'),
                dict(id='c',text='기계적 응력 집중',parents=['a','b'],logic='AND'),dict(id='d',text='미세 패턴 손상',parents=['c'],node_type='TARGET_DISADVANTAGE')]),
            resources=[dict(name='기존 제어기의 운전 로그',usable_for=['세정 조건별 손상 검토','시간 구간별 유속 조정']),
                dict(name='노즐과 웨이퍼 사이의 공간',category='SPACE',usable_for=['분사 경로 조정']),
                dict(name='추가 고온 공정',blocked_by_constraint=True,usable_for=['강성 조정은 온도 제약으로 사용 불가'])]),
        definition=dict(ifr=dict(x_element='기존 유속 제어',statement='패턴을 보호하면서 파티클을 제거한다.'),
            technical_contradictions=[dict(id='TC-example',label='세정 효율과 패턴 보호',if_action='세정액 유속을 20% 높인다.',then_good='파티클 제거 속도가 증가한다.',but_bad='패턴에 가해지는 기계적 응력이 커진다.',improving_param_id=9,worsening_param_id=31)],
            physical_contradictions=[dict(id='PC-example',label='유속의 반대 요구',element='세정액',parameter='유속',state_a='높아야 한다',reason_a='파티클을 충분히 제거해야 하므로',state_b='낮아야 한다',reason_b='미세 패턴을 보호해야 하므로')],
            trimming=[dict(target_component='추가 센서',replacement_carrier='기존 제어기',replaced_function='운전 로그로 이상 조건을 감지한다.')]),
        solve=dict(matrix_lookups=[dict(improving_param_id=9,worsening_param_id=31,principle_ids=[1,10,19,35])],
            separation_apps=[dict(source_pc_id='PC-example',kind=k,applicable=active,title=t) for k,active,t in
                [('TIME',True,'시간을 나누어 짧게 고속 세정'),('SPACE',True,'위치별 유속 차등 적용'),('CONDITION',False,'조건 판정에 필요한 센서 부족'),('SYSTEM_LEVEL',False,'상위 공정 변경 제약')]],
            ariz=dict(steps=[dict(step_code='1.3',step_title='모순 모델',output='TC1: 유속 증가 → 세정 효율 개선 + 패턴 손상 악화.'),
                dict(step_code='2.2',step_title='작용 시간',output='T1(갈등): 고속 세정 중. T2(이전): 세정액 공급 전. T3(이후): 세정 종료 후.'),
                dict(step_code='4.1',step_title='자원 행동 모델',output='현재: 일정한 유속. 요구: 파티클 제거와 패턴 보호. 구현: 기존 제어기의 시간별 유속 제어.')]),
            trend_apps=[dict(trend_id='TR-02',trend_name='동적 특성 증가',idea='조건별 유속을 조정한다.'),dict(trend_id='TR-12',trend_name='S-커브',idea='현재 기술의 성숙도를 검토한다.')],
            fos_apps=[dict(leading_area='항공 산업',transferred_feature='국소 유동 제어')]),
        concepts=[dict(id='CPT-one',title='시간 구간별 유속 제어',one_liner='기존 제어기를 사용하여 유속을 시간 구간별로 조정한다.',changes_to_system=['제어기의 운전 시퀀스 조정','패턴 손상과 파티클 제거율을 함께 검토한다.']),
            dict(id='CPT-two',title='분사 경로 분리',one_liner='패턴의 위치에 따라 분사 경로를 분리한다.')],
        evaluation=dict(evaluations=[dict(concept_id='CPT-one',aggregate=dict(RISK=4,QUALITY=4.5,FEASIBILITY=4),rank=1),
                                    dict(concept_id='CPT-two',aggregate=dict(RISK=2,QUALITY=3,FEASIBILITY=2),rank=2)]),
        scratch=dict(s_curve=dict(stage='성숙기')),report=dict(narrative=dict(executive_summary='설비 세정의 생산성과 패턴 보호를 함께 검토한다.'))))
