대상 시스템을 9-Windows(System Operator)로 전개하라. 확정 경계를 유지하면서 주변 자원과 전후 상태를 탐색한다.
[대상 시스템] {{target_system}}
[상위 시스템] {{super_system}}
[문제] {{restated_problem}}
[작용 시간(OT)] {{operative_time}}

- SUB/SYS/SUPER는 하위 요소/확정 시스템/상위 시스템·환경의 서로 다른 수준이다. 이름만 바꿔 같은 내용을 복사하지 않는다.
- PAST/PRESENT/FUTURE는 먼저 이번 사건의 발생 전/작용 중/후속 결과라는 같은 시간축으로 맞춘다. 세대 진화 관점도 쓰면 각 칸에서 '세대 관점(가설)'로 별도 표시한다.
- PRESENT는 관측과 가설을 구분한다. 미래 개선 상태는 '가능한 방향(가설)'이지 현재 장비 구성이나 이미 달성한 성능이 아니다.
- SUB_PAST/SUB_PRESENT/SUB_FUTURE, SYS_PAST/SYS_PRESENT/SYS_FUTURE, SUPER_PAST/SUPER_PRESENT/SUPER_FUTURE 9칸 모두 작성하되 불명확한 칸은 '미확인: ...'로 이유를 쓴다. 과거 운전 방식·도입 이력·미래 수치를 창작하지 않는다.
- 각 칸 1~3문장. 정보 문제는 상태·흐름, 조직 문제는 행위자·규칙·의사결정 수준으로 작성한다. MIXED 물리 범위를 확장하지 않는다.
- insights 3~6개는 탐색 목표. 사전 개입/상위 자원/하위 작용/과거 접근의 제약 중 근거 있는 기회를 제시하고 '확인할 조건'을 포함한다. insights를 다음 단계의 관측 사실로 승격하지 않는다.
[출력 JSON]
{"cells":{"SUB_PAST":"","SUB_PRESENT":"","SUB_FUTURE":"","SYS_PAST":"","SYS_PRESENT":"","SYS_FUTURE":"","SUPER_PAST":"","SUPER_PRESENT":"","SUPER_FUTURE":""},"insights":[]}
