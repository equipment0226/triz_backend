이번 문제 해결에 **실제로 적용된 TRIZ 원리**로 같은 종류의 모순을 해결한 **선행 특허**를 찾으려 한다.
산업·재료·장치가 달라도 좋다. 오히려 **다른 산업에서 같은 원리로 같은 모순을 푼 사례**가 가장 가치 있다.

[해결하려는 모순]
{{contradictions}}

[실제로 적용된 원리·표준해]
{{principles}}

[대상 시스템 — 참고용, 쿼리를 이 산업에 가두지 마라]
{{target_system}} / {{industry}}

--- 쿼리 작성 규칙 ---
- **영어**로 작성한다. 특허 데이터베이스 검색어다.
- 원리별로 2개씩 만든다.
  - `q_mechanism`: 원리의 **물리적 동작 메커니즘**을 서술한 검색어. 산업 용어를 넣지 마라.
    예) 원리 15(동적성) → "variable stiffness element adapting contact pressure during operation"
  - `q_conflict`: 해결하려는 **모순 자체**를 서술한 검색어. 역시 산업 중립적으로.
    예) "seal maintaining high contact pressure while reducing wear"
- 특정 회사명·상표명·본 과제 고유명사를 넣지 마라.
- 5~10 단어. 불리언 연산자나 따옴표를 쓰지 마라.

[출력 JSON]
{"queries":[{"principle_ref":"원리 15 동적성","principle_summary":"작동 중 특성을 가변시킨다","q_mechanism":"","q_conflict":""}]}
