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

[최종 해결책 수에 따른 ARIZ Part 6 추가 코멘트]
{{problem_reformulation_context}}
이 객체가 비어 있으면 problem_reformulation_review는 null이다.
객체가 있으면 보고서에 표시할 Solution이 3개 이하이므로 현재 응답 안에서 다음 세 항목을 한 번씩 검토한다.
- 6.1: 현재 미니문제에 서로 다른 문제가 섞였는지 검토하고, 핵심 문제부터 순차적으로 풀도록 나누는 문제 문장을 제안한다. 후속 분석 시 ARIZ 1.1 검토 대상이다.
- 6.2: 주기능을 유지하며 다른 기술적/시스템 모순을 선택할 수 있는지 검토하고, 비교할 이익·손실과 변경할 문제 문장을 제안한다. 단순한 갈등 요소 쌍 교체가 아니라 ARIZ 1.4의 모순 선택을 검토한다.
- 6.3: 같은 목표를 상위 시스템 수준에서 다루도록 미니문제를 다시 표현해 제안한다. 후속 분석 시 ARIZ 1.1 검토 대상이다.
각 항목은 observation(이번 문제의 구체적인 검토 근거)과 suggestion(“문제를 이렇게 바꿔보는 것은 어떨까요?” 형식의 제안)을 각 1~2문장으로 쓴다. 적용 근거가 부족하거나 변경이 부적절하면 이유와 먼저 확인할 사항을 쓴다. 세 가지 변경을 억지로 권장하지 않는다.
필수 요구조건·금기·성공 기준을 낮추거나 새 사실을 만들어내지 않는다. 상위 시스템이나 대안 모순이 기록에 없으면 가정 또는 확인할 질문으로 명시한다.
이 검토는 보고서의 부가 의견이다. 현재 문제 정의, 해결책 수·내용·순위, 기존 roadmap 판단은 그대로 유지한다. 제안을 새로운 해결책으로 세거나 선행 분석 재실행·새 해법 검증을 완료했다고 쓰지 않는다.

[출력 JSON]
{"ranking":[{"concept_id":"","rank":1,"reason":""}],
 "ranking_note":"","portfolio_note":"",
 "roadmap":[{"phase":"단기","concept_id":"","precondition":"","owner":""}],
 "problem_reformulation_review":null}
검토 대상이면 null 대신 {"items":[{"step_code":"6.1","observation":"","suggestion":""},{"step_code":"6.2","observation":"","suggestion":""},{"step_code":"6.3","observation":"","suggestion":""}]}를 출력한다.
