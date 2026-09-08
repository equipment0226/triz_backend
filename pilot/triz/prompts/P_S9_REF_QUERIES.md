최종 선정된 해결책마다 실제 문헌·특허를 찾기 위한 **영문 검색 쿼리**를 만들어라.
검색엔진에 그대로 넣을 문자열이며, 한국어 고유명사는 영문 기술용어로 바꿔야 한다.

[산업/시스템] {{industry}} / {{target_system}}
[도메인 키워드] {{domain_tags}}

[해결책 목록]
{{concepts}}

각 해결책마다 쿼리 2개를 만들어라.
1. q_tech  : 그 해결책의 **핵심 메커니즘**을 학술 논문에서 찾기 위한 쿼리
   - 제품명·회사명·한국어 제외. 물리 현상 + 대상 + 목적으로 구성.
   - 예) "thermophoretic particle deposition suppression optical window vacuum chamber"
2. q_patent: 같은 메커니즘의 **특허**를 찾기 위한 쿼리
   - 장치/방법 표현을 포함. 예) "apparatus preventing contamination viewport plasma chamber shutter"

[규칙]
- 각 쿼리는 4~10단어. 불용어와 따옴표를 넣지 마라.
- 너무 일반적인 단어(system, method, improve)만으로 구성하지 마라.
- 해결책의 고유 메커니즘이 반드시 들어가야 한다.

[출력 JSON]
{"queries":[{"concept_id":"","q_tech":"","q_patent":""}]}
