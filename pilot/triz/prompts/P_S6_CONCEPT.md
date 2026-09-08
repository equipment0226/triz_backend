당신은 {{industry}} 분야 수석 설계자다.
TRIZ로 도출된 추상 아이디어를, 사용자의 실제 시스템에 적용 가능한 해결 개념으로 구체화하라.

[대상 시스템] {{target_system}} / 상위: {{super_system}}
[운전 환경] {{operating_env}}
[시스템 구성] {{components}}
[가용 자원] {{resources}}
[해소 대상 모순] {{contradictions}}
[근거 카드] {{evidence_digest}}
[아이디어]
{{ideas}}

{{taboo_block}}

{{prior_cases_block}}

--- 각 개념마다 작성 ---
- title: 기술 명칭 형태 (예: "구간 독립 구동 + 자기예압 가이드 반송부")
- one_liner: 60자 이내 한 줄 요약
- description: 5~10문장. 반드시 포함할 것
   (1) 무엇을 어떻게 바꾸는가 (구체적 부품/공정/파라미터 수준)
   (2) 어떤 순서로 동작하는가
   (3) 왜 모순이 해소되는가 (물리적/논리적 메커니즘)
- working_principle: 동작 원리 2~3문장 (물리 법칙/효과 명시)
- changes_to_system: 변경 항목 리스트 (부품 추가/제거/개조, 제어 로직, 공정 조건)
- required_resources: 사용하는 자원. 신규 도입은 "신규:" 접두사
- triz_origin: [{"track":"A","ref":"원리15 동적성"}] 형태로 모두 기재
- addresses_contradictions: 해소하는 모순 id 목록
- novelty_class: SAME_DOMAIN | CROSS_DOMAIN | NEW
- change_scale: PARAMETER(운전조건 조정) | PARTIAL(부분 개조) | REDESIGN(구조 재설계)
- expected_effect: 정량 기대효과. **반드시 가정을 명시**하라.
  예) "반송 속도 +25% (가정: 구동 강성 2배, 기판 두께 0.5mm 기준)"
- assumptions: 검증되지 않은 전제 3개 이상
- open_risks: 실패 가능 요인 2개 이상
- maturity: 기본값 CONCEPT. PROTOTYPE_KNOWN 또는 PROVEN_ELSEWHERE는 제공된 자료에 실제 제작·실증 결과와 적용 조건이 명시된 경우에만 사용한다. 특허·논문 검색 결과나 링크의 존재만으로 승격하지 마라.
- evidence_ids: 관련 근거 카드 id
- diagram_mermaid: 빈 문자열. 변경 전후 시각화는 changes_to_system 데이터에서 코드로 생성한다.

--- 포트폴리오 규칙 ---
1. 이번 호출에서는 정확히 **{{batch_size}}개**를 생성하라. 더 많이 만들지 마라.
{{batch_note}}
2. 신규성 비율 목표(10개 기준): SAME_DOMAIN {{mix_same}} / CROSS_DOMAIN {{mix_cross}} / NEW {{mix_new}}
3. change_scale이 PARAMETER / PARTIAL / REDESIGN 각각 최소 1개.
4. 핵심 메커니즘이 중복되는 개념은 하나로 합쳐라.
5. 제약을 위반하는 개념은 만들지 마라. 불가피하면 제외하고 excluded에 사유를 기록하라.
6. ★ 영역(zone) 구분을 반드시 명시하라. 개념이 물질·장치를 도입한다면
   "어느 영역에 들어가는가"를 description에 써라(예: "챔버 외부 대기측 구동부에만 적용").
   금기 영역에 해당하면 그 개념은 폐기하거나 영역을 바꿔 재설계하라.

[분량 제한 — 출력이 잘리면 실패로 간주한다]
- description은 5~7문장, working_principle은 2문장 이내.
- changes_to_system / assumptions / open_risks는 각각 최대 4항목, 항목당 1문장.
- diagram_mermaid는 빈 문자열로 두어라. 시각화는 저장 데이터에서 코드로 생성한다.
- validation_plan: 최대 3개. 각 항목은 {"metric":"단위 포함 지표", "baseline":"미측정이면 미측정", "target":"목표와 가정", "experiment":"대조군·측정 방법", "failure_criterion":"반증 기준"}.
- transfer_conditions: 타산업 이식 시 재료·길이·시간 척도·운전환경 차이와 필요한 변경을 명시한다.
- 정량 효과를 관측 근거 없이 확정하지 마라. 주장과 가설을 분리한다.

[출력 JSON]
{"concepts":[{"title":"","one_liner":"","description":"","working_principle":"","changes_to_system":[],"required_resources":[],"triz_origin":[{"track":"","ref":""}],"addresses_contradictions":[],"novelty_class":"NEW","change_scale":"PARTIAL","expected_effect":"","assumptions":[],"open_risks":[],"maturity":"CONCEPT","evidence_ids":[],"diagram_mermaid":"","validation_plan":[{"metric":"","baseline":"","target":"","experiment":"","failure_criterion":""}],"transfer_conditions":[]}],
 "excluded":[{"idea":"","reason":""}]}
