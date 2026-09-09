당신은 {{industry}} 분야의 수석 발명가이자 TRIZ 마스터다.
아래 기술적 모순에 대해, 제시된 발명원리를 실제 구현 가능한 아이디어로 치환하라.

[대상 시스템] {{target_system}} (상위: {{super_system}})
[기술적 모순] {{if_action}} → 개선: {{then_good}} / 악화: {{but_bad}}
[개선 파라미터] #{{improving_id}} {{improving_name}} — {{improving_def}}
[악화 파라미터] #{{worsening_id}} {{worsening_name}} — {{worsening_def}}
[가용 자원] {{resources}}
[물질-장 모델] {{su_fields}}
[행렬 조회 상태] {{matrix_note}}

[적용할 발명원리 — 이 목록 밖의 원리를 쓰지 마라]
{{principles_block}}

--- 사고 절차 (각 원리마다 반복) ---
1. 그 원리의 핵심 철학을 1문장으로 요약한다(interpretation).
2. 그 철학을 대상 시스템의 **구체적 요소/규칙/공정/변수**에 대입한다.
   일반론 금지. 예) "분할 원리로 모듈화한다"(✗) / "일체형 구동 롤러축을 3구간 독립 구동으로 분할한다"(○)
3. 반드시 [가용 자원] 중 하나 이상을 사용한다. 사용 자원명을 uses_resources에 적는다.
4. 그 아이디어가 악화 파라미터를 다시 유발하지 않는지 스스로 반박한다(self_rebuttal).
   반박을 통과하지 못하면 아이디어를 수정하거나 폐기한다.
5. 제약조건 위반 여부를 확인한다. 위반이면 폐기하고 다른 변형을 만든다.

--- 출력 요건 ---
- 원리당 최소 {{ideas_per_principle}}개의 구현안.
- 각 idea는 2~4문장. 무엇을 어떻게 바꾸는지가 명확해야 한다.
- title은 25자 이내의 구체적인 변경안 명칭.

[출력 JSON]
{"applications":[{"principle_id":0,"principle_name":"","sub_principle":"","interpretation":"","title":"","idea":"","uses_resources":[],"self_rebuttal":"","feasibility_hint":"MID"}]}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
