시스템 진화 관점에서 다음 해법을 도출한다. 기술 트렌드를 비기술 문제의 자연법칙으로 취급하지 않는다. 조직 문제는 역할·권한·정보·조정 방식의 전환으로 번역하고 부적합 트렌드는 제외한다.
[해소할 모순] {{contradictions}}

[대상 시스템] {{target_system}}
[구성] {{components}}
[가용 자원] {{resources}}

[트렌드 목록 — 각 트렌드의 단계]
{{trends_block}}

관련성이 있는 트렌드만 검토한다. 근거 없이 성장 단계나 성숙도를 확정하지 않는다:
- trend_id / trend_name
- current_stage: 현재 시스템이 그 트렌드의 어느 단계에 있는지와 근거
- next_stage: 바로 다음 단계
- title: 25자 이내 명칭
- idea: 다음 단계로 이행시키는 구체적 설계안 2~4문장

추가로:
- bottleneck: 시스템 요소의 불균등 변화 관점에서 가장 뒤처진 병목 요소를 지목하라.
- s_curve_stage: 태동기|성장기|성숙기|쇠퇴기 중 하나와 판단 근거
- s_curve_note: 성숙기·쇠퇴기라면 '개선'이 아니라 '대체 원리 탐색'을 제안하라.

[출력 JSON]
{"applications":[{"trend_id":"","trend_name":"","current_stage":"","next_stage":"","title":"","idea":""}],
 "bottleneck":"","s_curve_stage":"","s_curve_note":""}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
