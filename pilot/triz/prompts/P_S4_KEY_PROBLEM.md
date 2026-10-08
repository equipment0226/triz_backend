도출된 모순 중 실제로 풀 핵심 문제를 1~{{max_key}}개 선정하라.
[기술적 모순] {{technical_contradictions}}
[물리적 모순] {{physical_contradictions}}
[핵심 단점] {{key_disadvantages}}
[성공 기준] {{success_criteria}}

- 입력에 존재하는 모순 id만 contradiction_ids에 참조한다. 표시 label과 id를 혼동하거나 새 id를 만들지 않는다.
- why_key는 해당 모순/핵심 단점→사용자 손실·성공 기준의 인과 연결과 개입 가능한 경계를 설명한다. 자료에 없는 수율·금액·위험 순위를 사실처럼 쓰지 않는다.
- impact(1~5)는 성과 기여, tractability(1~5)는 확인 자원·제약 내 개입 가능성. 불확실한 원인은 가설과 검증 우선순위를 명시한다.
- 서로 다른 계층의 문제가 실제로 있을 때 다양성을 고려한다. 최소 2개 계층을 채우기 위해 확정 경계를 바꾸거나 문제를 생성하지 않는다.
- 동일 핵심 문제의 TC/PC 표현은 함께 연결할 수 있다. 중복 표현을 별도 프로젝트처럼 나누지 않는다.
- 선택되지 않은 입력 모순을 dropped에 실제 id와 제외/보류 이유로 기록한다. 같은 id가 선택과 dropped에 동시에 나타나면 안 된다.
- 도출된 유효 모순이 없다면 key_problems=[]로 남긴다. 빈 입력을 허구의 문제로 채우지 않는다.
[출력 JSON]
{"key_problems":[{"title":"","contradiction_ids":[],"why_key":"","impact":3,"tractability":3}],"dropped":[{"id":"","reason":""}]}
