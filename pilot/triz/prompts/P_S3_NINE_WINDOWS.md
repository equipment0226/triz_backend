대상 시스템을 9-Windows(System Operator)로 전개하라.
목적은 문제를 시간축과 시스템 계층축으로 넓혀, 대상 시스템 밖의 해결 가능성과 자원을 드러내는 것이다.

[대상 시스템] {{target_system}}
[상위 시스템] {{super_system}}
[문제] {{restated_problem}}
[작용 시간(OT)] {{operative_time}}

9칸을 모두 채워라. 각 칸은 2~3문장, 구체적 명사 위주.
- SUB_PAST / SUB_PRESENT / SUB_FUTURE      : 하위 요소(부품·재료·신호) 관점
- SYS_PAST / SYS_PRESENT / SYS_FUTURE      : 대상 시스템 관점
- SUPER_PAST / SUPER_PRESENT / SUPER_FUTURE: 상위 시스템·환경·이해관계자 관점
* PAST  = 문제 발생 직전 상태 및 이 시스템의 이전 세대
* FUTURE= 문제 발생 직후 결과 및 이 시스템의 차세대 방향

이어서 insights를 3~6개 도출하라. 각 insight는 다음 중 하나여야 한다.
 (a) 상위 시스템에서 해결 가능한 여지
 (b) 문제 발생 이전 시점에 개입할 여지(예방)
 (c) 하위/미시 수준에서의 개입 여지
 (d) 이전 세대에서 이미 버려진 접근과 그 이유

[출력 JSON]
{"cells":{"SUB_PAST":"","SUB_PRESENT":"","SUB_FUTURE":"","SYS_PAST":"","SYS_PRESENT":"","SYS_FUTURE":"","SUPER_PAST":"","SUPER_PRESENT":"","SUPER_FUTURE":""},
 "insights":[]}
