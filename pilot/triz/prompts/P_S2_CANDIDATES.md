사용자의 문제 대상 시스템을 확정하기 위한 후보를 제시하라.

[도메인]
{{domain}}

[문제 재진술]
{{restated_problem}}

[첨부 사실]
{{attachment_facts}}

--- 생성 규칙 ---
- 후보는 {{min_candidates}}~{{max_candidates}}개. 각 후보는 "문제가 발생할 수 있는 시스템 경계"의 서로 다른 해석이어야 한다.
  (예: ① 반송 구동부 ② 반송 구동부+가이드레일 ③ 증착 소스와 기판 간 상대운동계)
- 각 후보마다:
  * name / scope(SUPER|TARGET|SUB) / description(3문장 이내)
  * diagram_mermaid: 상위시스템 → 대상시스템 → 하위요소 계층과 주요 흐름을 담은 mermaid flowchart.
    - 반드시 `flowchart TB` 로 시작한다.
    - 문제 발생 노드에 `:::problem` 을 붙이고 `classDef problem fill:#ffd6d6,stroke:#d33,stroke-width:2px;` 를 포함한다.
    - 노드 라벨은 큰따옴표로 감싼다. 괄호·특수문자는 라벨 안에서만 사용한다.
  * similarity_reason: 사용자 상황과 무엇이 일치하는지
- 첨부 도면이 있다면 도면의 구성요소 명칭을 그대로 사용하라. 새 이름을 짓지 마라.

마지막으로 다음을 정의하라.
- problem_zone: 문제가 드러나는 영역
- operative_zone: 작용이 실제로 일어나는 최소 작용 범위 (공간·정보 경계 또는 의사결정 관계)
- operative_time: 문제가 발생하는 시간 구간 (이전/발생중/이후 구분)
- confirm_question: 사용자에게 물을 1문장 확인 질문

[출력 JSON]
{"candidates":[{"name":"","scope":"TARGET","description":"","diagram_mermaid":"","similarity_reason":"","super_system":"","operative_zone":"","operative_time":""}],
 "problem_zone":"","operative_zone":"","operative_time":"","confirm_question":""}
