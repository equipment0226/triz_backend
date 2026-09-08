도출된 모순 중 실제로 풀 문제를 1~{{max_key}}개 선정하라.

[기술적 모순] {{technical_contradictions}}
[물리적 모순] {{physical_contradictions}}
[핵심 단점] {{key_disadvantages}}
[성공 기준] {{success_criteria}}

선정 기준:
- impact(1~5): 이 모순을 풀면 성공 기준에 얼마나 직접 기여하는가
- tractability(1~5): 가용 자원과 제약 안에서 다룰 수 있는가
- 서로 다른 계층(부품/시스템/상위시스템)의 문제를 최소 2개 섞어라(해법 다양성 확보)

각 항목에 title, contradiction_ids(위 모순의 id 문자열), why_key(2문장), impact, tractability 기재.
선정되지 않은 모순은 dropped에 {"id":"","reason":""} 형태로 사유를 남겨라.

[출력 JSON]
{"key_problems":[{"title":"","contradiction_ids":[],"why_key":"","impact":3,"tractability":3}],
 "dropped":[{"id":"","reason":""}]}
