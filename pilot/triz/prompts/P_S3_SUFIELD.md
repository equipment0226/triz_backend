물질-장 분석(Su-Field)의 현재 문제 모델을 작성하라. 해결책 모델을 현재 상태로 넣지 않는다.
[문제 기능들] {{problem_functions}}
[컴포넌트] {{components}}
[영역/시간] OZ={{operative_zone}} / OT={{operative_time}}

- 물리 문제가 아니거나 MIXED의 확인된 physical_scope 밖이라면 물질·장을 강제하지 않는다. 이 단계의 해당 물리 작용이 없으면 su_fields=[].
- 최대 {{max_models}}개, 모델 하나에 문제 작용 하나. 같은 두 요소가 유익·유해 작용을 함께 하면 각각 분리한다.
- s1=작용 받는 물질/대상(Article), s2=작용 가하는 도구 물질(Tool). 앱 표기는 항상 S2 --F--> S1이다. 물질 명칭은 components와 일치시킨다.
- field는 실제 두 물질의 상호작용을 매개하는 장/작용이다: Me(기계), Th(열), Ch(화학), El(전기), Mag(자기), EM(전자기), Ac(음향), Op(광), Gr(중력), Hy(유체), Bio(생물). '정책·인센티브·정보 부족·제어 알고리즘'을 기계적 힘이나 물리 장으로 바꾸지 않는다. In 표기는 앱의 정보 신호 확장이며 실제 물리 신호 경로가 확인될 때만 설명과 함께 쓴다.
- s1/s2에 온도·압력·진동 같은 파라미터나 고장 이름을 물질처럼 넣지 않는다. field를 명명할 수 없으면 빈 값과 MISSING_F/INCOMPLETE로 남긴다.
- completeness=COMPLETE는 S1/S2/F가 존재한다는 뜻이지 정상 작동한다는 뜻이 아니다. COMPLETE+HARMFUL, COMPLETE+USEFUL_INSUFFICIENT가 가능하다.
- s2만 없으면 MISSING_S2, F만 없으면 MISSING_F, 복수 결손은 INCOMPLETE. 없는 요소를 형식 충족용으로 추가하지 않는다.
- effect=USEFUL_SUFFICIENT/USEFUL_INSUFFICIENT/HARMFUL/EXCESSIVE/MEASUREMENT. 강도가 과도하다는 것과 작용 자체가 유해하다는 것을 구별한다.
- s3는 관측된 제3물질이 있을 때만 기록하는 앱 확장이다. 표준해에서 새로 넣을 물질을 현재 자원으로 쓰지 않는다. 원전의 기본 문제 모델 S1/S2/F와 확장된 해법 모델을 혼동하지 않는다.
- 미확인 메커니즘은 label에 '가설:'과 조건을 표시한다. diagram_mermaid는 빈 문자열로 둔다. 관계 도식은 코드가 생성한다.
[출력 JSON]
{"su_fields":[{"label":"","s1":"","s2":"","s3":"","field":"","completeness":"COMPLETE","effect":"HARMFUL","diagram_mermaid":""}]}
