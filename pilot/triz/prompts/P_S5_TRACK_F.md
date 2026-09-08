기술 시스템 진화 법칙(Trends of Engineering System Evolution)에 비추어 다음 세대 해법을 도출하라.

[대상 시스템] {{target_system}}
[구성] {{components}}
[가용 자원] {{resources}}

[트렌드 목록 — 각 트렌드의 단계]
{{trends_block}}

각 트렌드마다(최소 5개 트렌드 검토):
- trend_id / trend_name
- current_stage: 현재 시스템이 그 트렌드의 어느 단계에 있는지와 근거
- next_stage: 바로 다음 단계
- title: 25자 이내 명칭
- idea: 다음 단계로 이행시키는 구체적 설계안 2~4문장

추가로:
- bottleneck: 부품의 불균등 발전 관점에서 가장 뒤처진 병목 요소를 지목하라.
- s_curve_stage: 태동기|성장기|성숙기|쇠퇴기 중 하나와 판단 근거
- s_curve_note: 성숙기·쇠퇴기라면 '개선'이 아니라 '대체 원리 탐색'을 제안하라.

[출력 JSON]
{"applications":[{"trend_id":"","trend_name":"","current_stage":"","next_stage":"","title":"","idea":""}],
 "bottleneck":"","s_curve_stage":"","s_curve_note":""}
