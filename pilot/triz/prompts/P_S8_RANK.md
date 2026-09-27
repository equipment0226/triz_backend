평가 점수를 바탕으로 최종 추천 포트폴리오를 구성하라.

[집계 결과]
{{aggregate_table}}

[개념 메타]
{{concept_meta}}

[소수 의견]
{{dissent}}

--- 규칙 ---
1. 최종 {{min_solutions}}~{{max_solutions}}개를 선정하라. 총점순만으로 뽑지 마라.
2. 근거가 성립하는 후보 안에서 지향할 구성(억지 할당 금지):
   - QUICK_WIN(저위험·고효과) 최소 2개
   - BIG_BET(고위험·고효과) 최소 1개 (파급력 큰 구조 변경)
   - change_scale=PARAMETER인 즉시 적용안 최소 1개
   - novelty_class 3종 각각 최소 1개
3. rank는 "파급력 × 실행가능성" 기준. 동점이면 가역성이 높은 쪽을 상위로.
4. 탈락시키더라도 소수 의견이 강한 개념은 dissent에 사유를 보존하라.
미검증·수정 필요 후보는 검증된 추천처럼 표현하지 않는다. improvements를 roadmap의 선행 검증/설계 보완 과제로 반영한다.
5. ranking_note: 왜 이 순서인지 3~5문장.
6. portfolio_note: 어떤 순서로 실행하면 좋은지 (단기/중기/장기).
7. roadmap: 각 항목 {"phase":"단기|중기|장기","concept_id":"","precondition":"","owner":""}

[출력 JSON]
{"ranking":[{"concept_id":"","rank":1,"reason":""}],
 "ranking_note":"","portfolio_note":"",
 "roadmap":[{"phase":"단기","concept_id":"","precondition":"","owner":""}]}
