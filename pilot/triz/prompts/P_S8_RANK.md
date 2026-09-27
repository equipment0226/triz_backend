[전체 후보 순위 계약 v1]
기술 검토와 제약 검토를 거쳐 전달된 모든 후보의 실행 우선순위를 정한다.
후보 수: {{candidate_count}}

[집계 결과]
{{aggregate_table}}

[개념 메타]
{{concept_meta}}

[소수 의견]
{{dissent}}

--- 규칙 ---
1. 모든 입력 concept_id를 ranking에 정확히 한 번씩 포함한다. 개수 상한이나 최소 수량은 없다.
2. 기법·신규성·개조 규모별 할당량을 채우지 않는다. 순위는 후보의 삭제나 기술적 적합성 인증이 아니다.
3. rank는 "파급력 × 실행가능성" 기준. 동점이면 가역성이 높은 쪽을 상위로.
4. 후보를 생략하지 않는다. 소수 의견과 반대 근거를 보존한다. rank는 1부터 전체 후보 수까지 중복 없이 지정한다.
미검증·수정 필요 후보는 검증된 추천처럼 표현하지 않는다. improvements를 roadmap의 선행 검증/설계 보완 과제로 반영한다.
5. ranking_note: 왜 이 순서인지 3~5문장.
6. portfolio_note: 어떤 순서로 실행하면 좋은지 (단기/중기/장기).
7. roadmap: 각 항목 {"phase":"단기|중기|장기","concept_id":"","precondition":"","owner":""}

[출력 JSON]
{"ranking":[{"concept_id":"","rank":1,"reason":""}],
 "ranking_note":"","portfolio_note":"",
 "roadmap":[{"phase":"단기","concept_id":"","precondition":"","owner":""}]}
