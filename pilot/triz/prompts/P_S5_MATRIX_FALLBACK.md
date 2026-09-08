아래 기술적 모순을 해결하기 위해 40가지 발명원리 중 가장 유망한 {{count}}개를 선별하라.
(모순 행렬 데이터가 탑재되지 않아 전문가 판단으로 대체하는 단계다.)

[기술적 모순] {{if_action}} → 개선: {{then_good}} / 악화: {{but_bad}}
[개선 파라미터] #{{improving_id}} {{improving_name}} — {{improving_def}}
[악화 파라미터] #{{worsening_id}} {{worsening_name}} — {{worsening_def}}
[대상 시스템] {{target_system}}

[40 발명원리 목록]
{{principles_brief}}

선별 기준:
1. 이 파라미터 쌍의 전형적 해결 방향과 부합하는가
2. 대상 시스템의 물리적 특성에 적용 가능한가
3. 서로 다른 접근을 제공하는가(비슷한 원리만 고르지 마라)

각 선택에 대해 why(1문장)를 적어라. 반드시 위 목록의 번호만 사용하라.

[출력 JSON]
{"principle_ids":[],"selections":[{"principle_id":0,"why":""}]}
