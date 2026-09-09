사용자 질의를 읽고 실행 계획 메타데이터만 판단하라. 문제를 풀려고 하지 마라.

[사용자 질의]
{{raw_query}}

[첨부 요약]
{{attachment_summaries}}

판단 항목:
1. lang: 질의의 주 언어 (ko/en 등)
2. is_engineering: 물리적 기술 시스템 문제면 true, 비즈니스·프로세스·생활 문제면 false
3. complexity: LOW|MID|HIGH (관련 부품/이해관계자 수, 모순의 중첩도)
4. suggested_mode: LITE|FULL|DEEP
   - LITE: 단순 생활/소규모 문제, 정보량이 적음
   - FULL: 일반적인 실무 기술/업무 문제
   - DEEP: 난제, 신규 개발, 특허 지향, 기존 방법으로 해결 실패 이력
5. domain_guess: 산업/직군 추정 (확신 없으면 빈 문자열)
6. title: 대상 시스템과 개선 목표 또는 상충 관계를 요약한 15~30자의 완결된 명사구 제목.
   원문 앞부분을 잘라 붙이지 마라. 구어체·오타를 정리하고 단어 중간을 자르지 마라.
   예: "진동 데이터 샘플링과 저장 용량 최적화". 빈 제목이나 말줄임표는 금지한다.

[출력 JSON]
{"lang":"ko","is_engineering":true,"complexity":"MID","suggested_mode":"FULL","domain_guess":"","title":""}
