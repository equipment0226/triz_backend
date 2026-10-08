확인된 제약과 발견한 가설·변경 가능한 관행을 구분하라.
[산업] {{industry}} / 대상 {{target_system}} / 상위 {{super_system}}
[환경] {{operating_env}} / 구성 {{components}} / 자원 {{resources}}
[범위·시간] {{operative_zone}} / {{operative_time}}
[사용자가 확인한 제약] {{user_constraints}}

- 발견한 조건은 원문에 확인되지 않으면 '가설:'로 표시하고 hard=false, confidence<=0.6으로 작성한다. 도메인 상식만으로 규격·금지·수치를 확정하지 않는다.
- 고정된 물리 법칙과 그 법칙이 이 문제에 적용되는 조건을 구분한다. 재료·전압·법규 적용 범위가 불명확하면 확인 필요로 둔다.
- 사용자의 최신 수정과 명시한 예외를 존중한다. 기존 hard 제약은 임의로 완화하거나 새 hard 제약으로 확장하지 않는다.
- 물리는 재료 양립성·경계조건, 정보는 권한·일관성·인터페이스, 조직은 계약·유인·운영 조건을 살핀다. physical_scope 밖에 물리 제약을 추가하지 않는다.
- 관행·선호는 변경 가능한 변수이며 절대 금기가 아니다. zone은 실제 적용 위치 또는 행위자·의사결정 관계다.
- taboo의 confirmed=true는 제공된 확인 hard 제약의 실제 constraint_id와 일치하는 경우만 허용한다. ID를 전달받지 못했으면 만들지 말고 confirmed=false로 둔다.
- 위반 사례는 해당 제약과 같은 영역·조건에 한정한다. 수량 목표 없이 근거 있는 것만 적는다. 추가 발견이 없으면 빈 배열.
[출력 JSON]
{"constraints":[{"statement":"","kind":"PREFERENCE","category":"OPERATION","zone":"","parameter":"","operator":"none","value":"","unit":"","hard":false,"confidence":0.6,"rationale":"","violation_example":""}],"taboo":[{"item":"","zone":"","why":"","constraint_id":"","confirmed":false}]}
