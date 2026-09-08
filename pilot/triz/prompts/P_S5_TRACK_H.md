아래 '요구 기능'을 실현할 수 있는 물리·화학·기하학적 효과를 제시하라.

[요구 기능]
{{required_functions}}
[대상 시스템] {{target_system}} / 운전 환경: {{operating_env}}

[효과 카탈로그 — 우선 사용. 목록 밖 효과는 name 앞에 "추가:"를 붙여라]
{{effects_block}}

각 효과마다:
- effect_name / effect_domain(PHYSICAL|CHEMICAL|GEOMETRIC|BIOLOGICAL)
- principle: 무엇이 무엇을 일으키는가 (1~2문장)
- title: 25자 이내 명칭
- idea: 본 시스템 적용안 2~3문장 (어떤 부위에 어떤 형태로)
- conditions: 필요 조건과 한계 (온도범위, 재료, 전력, 환경 제약)

요구 기능당 최소 2개의 서로 다른 효과를 제시하라.

[출력 JSON]
{"applications":[{"required_function":"","effect_name":"","effect_domain":"PHYSICAL","principle":"","title":"","idea":"","conditions":""}]}
