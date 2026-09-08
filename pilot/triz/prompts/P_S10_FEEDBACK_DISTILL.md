사용자 피드백을 다음 검색에 재사용 가능한 구조로 정제하라. 평가하지 말고 정제만 하라.

[문제 요약] {{problem_digest}}
[모순] {{contradiction_digest}}
[개념 + 점수 + 코멘트]
{{feedback_raw}}

출력 항목:
- accepted_patterns: 4점 이상 개념들의 공통 메커니즘을 1~2문장으로 일반화한 문장 리스트
- rejected_patterns: 2점 이하 개념들의 공통 실패 사유 (도메인 제약 형태로 표현)
- domain_lesson: 이 도메인에서 다음에 반드시 고려해야 할 점 1~3문장
- generalized_problem: 산업 용어를 제거한 문제 진술 1문장 (벡터 검색 키가 된다)

[출력 JSON]
{"accepted_patterns":[],"rejected_patterns":[],"domain_lesson":"","generalized_problem":""}
