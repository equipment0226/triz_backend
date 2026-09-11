아래 '요구 기능'을 실현할 수 있는 물리·화학·기하학적 효과를 제시하라.

[요구 기능]
{{required_functions}}
[대상 시스템] {{target_system}} / 운전 환경: {{operating_env}}

[효과 카탈로그 — 우선 사용. 목록 밖 효과는 name 앞에 "추가:"를 붙여라]
{{effects_block}}

실제 physical_scope에만 적용한다. [해소할 모순] {{contradictions}}
카탈로그의 필요 조건이 성립하지 않으면 제외한다.
각 효과마다:
- effect_name / effect_domain(PHYSICAL|CHEMICAL|GEOMETRIC|BIOLOGICAL|INFORMATIONAL)
- principle: 무엇이 무엇을 일으키는가 (1~2문장)
- title: 25자 이내 명칭
- idea: 본 시스템 적용안 2~3문장 (어떤 부위에 어떤 형태로)
- conditions: 필요 조건과 한계 (온도범위, 재료, 전력, 환경 제약)

요구 기능당 서로 다른 효과를 비교하되, 조건과 근거가 부족하면 적은 수를 제시하고 부족한 이유를 설명한다.
카탈로그 효과를 사용하면 source_effect_id에 대괄호 안의 ID를 그대로 기록한다.
출처가 없는 편집 지식에 문헌·실험 검증을 주장하지 않는다. 카탈로그의 필요 조건을 적용안에도 보존한다.
출처 범위가 초록·발췌문이면 본문 검토나 실증 완료라고 표현하지 않는다. 문헌의 적용 조건을 현재 시스템에서 충족하는지 별도로 판단한다.
필요 조건과 한계를 효과 이름보다 우선하며, 카탈로그 밖 효과의 source_effect_id는 null로 둔다.

[출력 JSON]
{"applications":[{"required_function":"","source_effect_id":null,"effect_name":"","effect_domain":"PHYSICAL","principle":"","title":"","idea":"","conditions":""}],"gaps":[]}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
