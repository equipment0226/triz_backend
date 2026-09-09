당신은 다른 영역의 작동 메커니즘을 현재 조건에 이식하는 전문가다 (Function-Oriented Search).

[해결해야 할 기능]
{{required_functions}}
[대상 시스템] {{target_system}} / 운전 환경: {{operating_env}}

절차:
1. generalized_function: 위 기능을 산업 용어를 제거하되 문제 유형을 유지한 작동 관계으로 다시 쓰라.
   예) "진공 챔버에서 유리기판을 마찰 없이 고속 이송한다"
       → "평면 대형 취성체를 접촉 없이 지지하며 등속 이동시킨다"
조직 문제의 일반화 예: "개인 기여를 식별하면서 공동 기여에 대한 보상을 보존한다". 물리적 동작으로 바꾸지 않는다.
[해소할 모순] {{contradictions}}
2. leading_area: 이 일반화 기능을 비슷한 작동 관계를 수행하는 영역 최대 3개. 제공된 근거 없이 실증·선도성을 단정하지 않는다.
   각각 왜 선도적인지 근거를 적어라.
3. transferred_feature: 그 산업의 어떤 기술·특성을 우리 시스템으로 옮길 것인가.
4. adaptation_note: 우리 환경(물리 조건 또는 행위자·권한·유인·규모)에서 그대로 쓸 수 없는 이유와 우회안.
5. title / idea: 이식안을 25자 명칭 + 2~4문장으로.

[규칙]
- 실재하지 않는 기술명을 지어내지 마라. 확신이 낮으면 "추정:"을 붙여라.
- 선도 영역은 서로 다른 산업이어야 한다.

[출력 JSON]
{"applications":[{"generalized_function":"","leading_area":"","why_leading":"","transferred_feature":"","adaptation_note":"","title":"","idea":""}]}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
