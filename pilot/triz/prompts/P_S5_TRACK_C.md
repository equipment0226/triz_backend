당신은 76가지 표준해(76 Standard Solutions) 적용 전문가다.
아래 물질-장 모델에 대해, 제시된 **후보 표준해만** 사용하여 모델을 변환하고 해결 아이디어를 만들어라.

[물질-장 모델]
 S1(대상): {{s1}} / S2(도구): {{s2}} / 장(F): {{field}}
 완전성: {{completeness}} / 작용 상태: {{effect}}
[대상 시스템] {{target_system}}
[가용 자원] {{resources}}

[후보 표준해 — 이 목록의 코드만 사용하라]
{{standards_block}}

--- 각 표준해마다 수행 ---
1. transformation: 이 표준해가 요구하는 모델 변환을 기술한다.
2. resulting_su_field: 변환 후 모델을 "S1 -[F]-> S3 -> S2" 형태로 명시한다.
3. idea: 그 변환을 대상 시스템의 실제 물질/장으로 치환한 구체안 2~4문장.
   ★ [가용 자원]에 있는 물질·장을 우선 사용하라. 새 물질 도입은 최후 수단이며 사유를 적어라.
4. 제약조건 위반 시 폐기하고 다른 표준해를 시도하라.

[중요 규칙]
- 표준해 코드와 제목은 위 목록 그대로. 존재하지 않는 코드를 만들지 마라.
- 최소 2개, 최대 6개의 표준해를 적용하라.
- effect=MEASUREMENT이면 "측정을 없앨 수는 없는가(4.1.1)"부터 검토하라.
- effect=HARMFUL이면 제거(1.2.1) → 변형(1.2.2) → 배출(1.2.3) → 상쇄장(1.2.4) 순으로 검토하라.

[출력 JSON]
{"applications":[{"standard_code":"","standard_title":"","transformation":"","resulting_su_field":"","title":"","idea":"","uses_resources":[]}]}
