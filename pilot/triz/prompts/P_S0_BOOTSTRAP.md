사용자 질의를 읽고 실행 계획 메타데이터만 판단하라. 문제를 풀려고 하지 마라.

[사용자 질의]
{{raw_query}}

[첨부 요약]
{{attachment_summaries}}

판단 항목:
1. lang: 질의의 주 언어 (ko/en 등)
2. problem_type: PHYSICAL_TECHNICAL | INFORMATION_SOFTWARE | ORGANIZATIONAL_BUSINESS | MIXED.
   회사의 산업과 실제 문제 유형을 구분한다. 반도체 회사의 보상·협업 문제는 ORGANIZATIONAL_BUSINESS다.
   difficulty: routine | advanced | frontier. 산업명 대신 경쟁 원인, 상충의 중첩, 관측 부족, 기존 실패로 판단한다.
   정보가 적다는 이유로 단순 문제라고 단정하지 않는다.
   physical_scope: MIXED일 때 실제 물리 하위문제와 경계. 확인되지 않으면 빈 문자열.
   is_engineering: 물리적 기술 시스템 문제면 true, 비즈니스·프로세스·생활 문제면 false
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
{"lang":"ko","is_engineering":true,"problem_type":"PHYSICAL_TECHNICAL","difficulty":"advanced","physical_scope":"","complexity":"MID","suggested_mode":"FULL","domain_guess":"","title":""}
