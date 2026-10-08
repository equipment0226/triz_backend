원인-결과 사슬(CECA)을 작성하라. 기능 분석의 단점을 출발점으로 손실의 작동 경로와 검증할 가설을 구분한다.
[표면 문제] {{symptom}}
[유해/부족 기능] {{problem_functions}}
[컴포넌트 모델 — 자동 생성 주장 포함] {{components}}
[성공 기준] {{success_criteria}}

- TARGET_DISADVANTAGE는 프로젝트의 필요 성과가 달성되지 않는 손실이다. 개선 목표 자체나 해결책을 원인으로 넣지 않는다.
- 각 노드는 하나의 단점/인과 주장. id=N1,N2,..., parents는 이 원인이 유발하는 바로 위 결과 노드의 id다. 즉 저장 방향은 원인 노드→parents의 결과이며, 그림은 결과에서 원인을 내려다본다.
- TARGET_DISADVANTAGE.parents=[]이다. 예: N1=인재 이탈 손실 parents=[], N2=이직 의도 parents=[N1], N3=보상 격차 parents=[N2], N4=성장 기회 부족 parents=[N2]. N3/N4가 OR 원인이라고 N2.parents를 [N3,N4]로 바꾸면 안 된다. 원인 그룹은 logic/comment로 설명하고 결과→원인을 parents에 역저장하지 않는다.
- 결과에 동시에 필요한 복수 원인은 AND, 독립적인 대안 원인은 OR. 같은 결과를 가리키는 원인 노드들의 logic에 일관된 결합을 표시하고 comment로 어떤 원인들이 묶이는지 설명한다. 단일 원인 연결은 NONE. 서로 다른 결합이 필요하면 중간 단점 노드로 분리한다.
- OBSERVED는 사용자 관측/첨부에 직접 뒷받침되는 내용만. evidence_refs에 실제 입력 근거를 적는다. 사용자 목표, 생성된 컴포넌트 역할, 앞 단계 가설은 관측 증거가 아니다.
- DERIVED는 확인된 전제와 명시된 논리/관계로 도출할 때만. 원인 방향이 미확인·복수 설명 가능하면 HYPOTHESIS.
- 가설은 text의 '가설:' 또는 '추정:'과 hypothesis_ids, falsification_test를 쓴다. 관측 가능한 대조 조건과 반증 결과를 명시한다. 경쟁 가설을 원인 확정으로 합치지 않는다.
- {{min_depth}}단은 탐색 목표, 최대 6단. 근거가 부족하면 짧은 사슬과 미확인 사유가 허구의 깊이보다 옳다. 자연 법칙 또는 이 프로젝트에서 통제할 수 없는 경계에서 ROOT_CAUSE로 멈춘다. ROOT_CAUSE 표시가 원인 입증을 의미하지 않는다.
- KEY_DISADVANTAGE는 해결하면 초기 손실에 영향을 줄 수 있는 개입 지점 1~3개. 비용이 낮다는 근거가 없으면 단정하지 않는다.
- 제거 시 다른 유익 기능을 훼손하거나 동일 요소에 상반 요구를 만드는 지점만 is_contradiction_seed=true. comment에 보존할 유익 기능을 명시한다.
- 물리는 관련 계면·작용, 정보는 상태 전이, 조직은 규칙→행위자의 선택→결과로 설명한다. '노후화/관리 부족'에서 멈추거나 권한을 힘으로 치환하지 않는다.
- 순환 참조, 중복 ID, 동의어 반복, 이름만 있는 결과→결과 연결, 해결책·센서 추가를 원인처럼 기록하는 것을 금지한다.
- 수리 지시도 이 저장 방향과 대조한다. 제출 전 모든 원인이 초기 손실로 이어지는지, 결과·원인 양방향 2-cycle과 자기참조가 없는지 전체 그래프를 재검사한다.
mermaid는 flowchart TD, 큰따옴표 노드 라벨.
[출력 JSON]
{"nodes":[{"id":"N1","text":"","node_type":"TARGET_DISADVANTAGE","parents":[],"logic":"NONE","is_contradiction_seed":false,"comment":"","evidence_status":"HYPOTHESIS","evidence_refs":[],"hypothesis_ids":[],"falsification_test":""}],"mermaid":""}
