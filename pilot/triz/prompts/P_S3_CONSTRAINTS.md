문제 유형에 맞는 내재 제약과 변경 가능한 관행을 구분한다.
[산업] {{industry}} / 대상 {{target_system}} / 상위 {{super_system}}
[환경] {{operating_env}} / 구성 {{components}} / 자원 {{resources}}
[작용 범위·시간] {{operative_zone}} / {{operative_time}}
[사용자가 확인한 제약] {{user_constraints}}
물리 문제는 물질 양립성·경계조건, 정보 문제는 권한·일관성·인터페이스, 조직 문제는 이해관계자·의사결정 권한·운영·경제 조건을 점검한다.
명시되지 않은 제약은 가설이다. hard=false, confidence<=0.6으로 작성한다. 숫자·법규·금지를 창작하지 않는다.
관행과 선호는 바꿀 수 있는 설계 변수다. 관행을 절대 금기로 만들지 않는다. 각 제약의 zone은 공간 또는 행위자·의사결정 범위다.
taboo는 이미 확인된 hard 제약의 constraint_id를 인용할 수 있을 때만 confirmed=true다. 개수를 채우지 않는다.
{"constraints":[{"statement":"","kind":"PREFERENCE","category":"OPERATION","zone":"","parameter":"","operator":"none","value":"","unit":"","hard":false,"confidence":0.6,"rationale":"","violation_example":""}],"taboo":[{"item":"","zone":"","why":"","constraint_id":"","confirmed":false}]}
