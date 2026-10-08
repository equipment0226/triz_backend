문제 해결에 동원할 기존 자원과 가용성 확인이 필요한 후보를 구분하라.
[컴포넌트] {{components}}
[상위 시스템] {{super_system}}
[운전 환경] {{operating_env}}
[영역/시간] {{operative_zone}} / {{operative_time}}
[사용 금지 제약] {{must_not_have}}

자원은 이미 존재하거나 쉽게 접근 가능한 물질·에너지·시간·공간·정보·기능이다. 도입하려는 해결책, 새 예산·인력·설비를 '기존 무료 자원'으로 둔갑시키지 않는다.
카테고리:
SUBSTANCE(기존 물질·부품·부산물), FIELD(기존 장), SPACE(기존 공간), TIME(사용 가능한 시간), INFORMATION(기존 기록·신호), FUNCTIONAL(전용할 수 있는 기존 기능), SYSTEM_LEVEL(상위·인접·환경 자원).
조직의 기존 권한·규칙은 FUNCTIONAL, 기록은 INFORMATION으로 기술하며 물리적 힘으로 치환하지 않는다. MIXED의 물리 자원은 physical_scope를 따른다.

- name은 실제 위치와 원천을 적는다. 예: '커플링-하우징 축방향 간극(치수 미확인)'. 근거 없는 '2mm 간극'을 넣지 않는다.
- where=IN_SYSTEM/IN_SUPERSYSTEM/IN_ENVIRONMENT/WASTE/DERIVED. DERIVED이면 기존 원천과 변환에 필요한 에너지·공정·권한을 quantity_note에 적는다.
- availability=FREE/LOW_COST/COSTLY는 확인된 획득·전환 비용이다. 공짜라는 근거가 없으면 보수적으로 COSTLY와 '확인 필요'를 적는다.
- quantity_note에 '확인:' 또는 '가설:'로 존재 근거, 가용량/시간, 접근 조건과 미측정 항목을 구분한다. 미측정 수치를 추정 사실로 쓰지 않는다.
- usable_for에는 대체/보강할 기능과 필요한 용량·타이밍·접근 조건을 적는다. 열이 존재해도 충분한 온도·열량이 있다는 뜻은 아니다.
- 제약으로 금지되면 blocked_by_constraint=true와 해당 제약 근거를 quantity_note에 쓴다. blocked 자원은 IFR 강화의 무조건 사용 가능 자원이 아니다.
- {{min_resources}}개와 카테고리별 개수는 탐색 목표일 뿐이다. 근거 없는 후보를 채우지 않는다. 확인된 자원이 없으면 빈 배열과 unavailable_reason에 실제 탐색 결과·미확인 사유를 적는다.
[출력 JSON]
{"resources":[{"category":"SUBSTANCE","name":"","where":"IN_SYSTEM","availability":"FREE","quantity_note":"","usable_for":[],"blocked_by_constraint":false}],"unavailable_reason":""}
