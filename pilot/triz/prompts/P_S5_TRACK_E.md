아래 트리밍 후보들을 실제 설계 변경안으로 구체화하라.

[트리밍 후보] {{trimming_items}}
[가용 자원] {{resources}}
[대상 시스템] {{target_system}}

각 후보에 대해:
- title: 25자 이내 명칭
- idea: 제거 후 구성이 어떻게 바뀌는지, 기능을 이어받는 주체가 무엇을 갖춰야 하는지 2~4문장
- removed_harm: 제거로 함께 사라지는 유해 기능
- new_risk: 새로 생길 수 있는 문제
- benefit: 예상되는 비용/복잡도 감소 효과(정성 또는 추정치, 가정 명시)

[출력 JSON]
{"applications":[{"target_component":"","rule":"C","title":"","idea":"","removed_harm":"","new_risk":"","benefit":"","uses_resources":[]}]}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
