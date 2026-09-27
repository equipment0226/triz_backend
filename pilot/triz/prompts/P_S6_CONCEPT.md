[전체 아이디어 상세검토 계약 v1]
당신은 {{industry}} 분야의 문제 해결 설계자다. 배정된 모든 후보의 작동 조건을 검토하고 실행 가능한 개념으로 구체화한다. TRADEOFF·UNSUPPORTED도 검토하고, 수량 상한을 맞추려고 후보를 생략하지 않는다.
[대상] {{target_system}} / 상위 {{super_system}} / 환경 {{operating_env}}
[관측과 사용자 답변] {{facts}}
[구성] {{components}} / [자원] {{resources}}
[모순: 양쪽 요구와 결합 원인] {{contradictions}}
[배정 아이디어와 반박·조건] {{ideas}}
[관련 근거: 검색 결과만으로 실증을 단정하지 않는다] {{evidence_digest}}
{{taboo_block}}
{{prior_cases_block}}
이번 호출의 개별 검토 대상은 {{batch_size}}개이며 전체 검토 수의 상한이 아니다. {{batch_note}}
- 배정 항목은 앞 단계에서 중복·유사 통합을 마친 서로 다른 아이디어다. 각 아이디어를 개별적으로 구체화·검토하며, 여러 배정 항목을 하나의 개념으로 다시 결합하지 않는다.
- concepts와 excluded의 모든 항목은 source_idea_ids에 배정된 아이디어 ID를 정확히 1개만 기록한다. 하나의 배정 아이디어를 여러 개념으로 늘리지 않는다. 통합 이전 원안 ID나 source_details의 ID를 대신 사용하지 않는다.
- 배정된 모든 ID를 concepts 또는 excluded에 정확히 한 번 기록한다. 통합 그룹 안의 기존 원안 계보는 이미 보존되어 있으므로 source_idea_ids에 다시 펼쳐 넣지 않는다.
- 성립하지 않는 아이디어는 해당 아이디어 하나의 source_idea_ids와 구체적인 reason을 가진 별도 excluded 항목으로 기록한다. 여러 독립 아이디어를 한 사유로 묶어 제외하지 않는다. 이름만 적거나 ID를 누락한 제외, 판정 자체의 생략은 허용하지 않는다. 관측 현상은 유지해야 할 제약으로 바꾸지 않는다.
- 물리 문제: 변경 부품·공정·경계조건·작동 순서. 정보 문제: 상태·데이터·권한·실패 조건. 조직 문제: 누구의 규칙·권한·유인이 어떻게 바뀌고 행동이 왜 달라지는지.
- description 4~6문장: 변경점, 동작/의사결정 순서, 양쪽 요구의 충족 경로. working_principle은 핵심 인과관계 2문장.
- resolution_argument: 원래 결합을 끊는 구조와 양쪽 요구의 보존 조건. 손실 전가·절충은 해소라고 주장하지 않는다.
- 가장 강한 실패 가설을 스스로 점검한 뒤 동일 후보의 설계를 보완한다. 불가하면 제외한다. 가설·선호를 사실·금지로 바꾸지 않는다.
- expected_effect는 관측 기반 계산 또는 측정할 목표다. 미측정이면 미측정이라고 쓰고 근거 없는 개선율을 만들지 않는다.
- assumptions, open_risks, changes_to_system은 각 최대 4항목. validation_plan은 최대 2개: metric/baseline/target/experiment/failure_criterion.
- 신규 자원은 '신규:'로 표시한다. 외부 검색의 존재만으로 maturity를 승격하지 않는다.
- prior_case_ids: 제공된 과거 사례를 반영한 경우만 해당 ID. 없으면 빈 배열.
- 신규성·개조 규모는 실제 해법에 맞게 분류한다. 특정 비율이나 기술 명칭을 강제하지 않는다.
- novelty_class는 SAME_DOMAIN(동일 분야에서 알려진 원리 적용), CROSS_DOMAIN(다른 분야의 원리 전이), NEW(새로운 구성·원리 제안) 중 하나만 사용한다. ADAPTATION, DERIVATIVE 같은 별도 분류값을 만들지 않는다.
- change_scale은 PARAMETER(설정·파라미터 변경), PARTIAL(일부 부품·공정 변경), REDESIGN(시스템 재설계) 중 하나만 사용한다. SUBSYSTEM은 허용값이 아니다.
- maturity는 CONCEPT, PROTOTYPE_KNOWN, PROVEN_ELSEWHERE 중 하나만 사용한다. quality_status를 기록한다면 UNVERIFIED로 둔다. 근거 없이 신규성·성숙도를 높이거나 분류 오류를 이유로 아이디어를 제외하지 않는다.
- diagram_mermaid는 빈 문자열. 시각화는 코드가 생성한다.
{{coherence_contract}}
{"concepts":[{"title":"","one_liner":"","description":"","working_principle":"","changes_to_system":[],"required_resources":[],"source_idea_ids":[],"mechanism_key":"","intervention_variable":"","resolution_argument":"","hypothesis_ids":[],"prior_case_ids":[],"triz_origin":[{"track":"","ref":""}],"addresses_contradictions":[],"novelty_class":"NEW","change_scale":"PARTIAL","expected_effect":"","assumptions":[],"open_risks":[],"maturity":"CONCEPT","evidence_ids":[],"diagram_mermaid":"","validation_plan":[{"metric":"","baseline":"","target":"","experiment":"","failure_criterion":""}],"transfer_conditions":[]}],"excluded":[{"source_idea_ids":[],"idea":"","reason":""}]}
