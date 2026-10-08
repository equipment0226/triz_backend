기존 제약을 보존하면서 누락된 직접 사용자 제약과 새 도메인 가설만 추가하라.
[산업] {{industry}} / 대상 {{target_system}} / 상위 {{super_system}}
[환경] {{operating_env}} / 구성 {{components}} / 자원 {{resources}}
[범위·시간] {{operative_zone}} / {{operative_time}}
[기존 제약 아카이브 — 출력에 재수록하지 않음] {{existing_constraints}}
[확인 HARD 제약 ID — USER/REGULATION 출처만] {{confirmed_hard_constraint_ids}}
[직접 사용자 원문 — 경로별 text와 질문 맥락] {{user_constraint_sources}}

- 출력은 전체 제약 목록이 아닌 추가분이다. 기존 ID/statement를 어느 배열에도 반복하지 않는다. 기존 USER/INFERRED/DOMAIN 등의 source, hard, confidence를 변경하지 않는다. 추가분에서 기존 행을 제외하는 것은 저장된 제약의 삭제·완화가 아니다.
- constraints 배열은 신규 DOMAIN 가설 전용이다. 원문에 확인되지 않은 조건만 '가설:'로 표시하고 source=DOMAIN, hard=false, confidence<=0.6으로 작성한다. 도메인 상식만으로 규격·금지·수치를 확정하지 않는다.
- user_constraints 배열에는 아직 저장되지 않은 직접 사용자 제약만 source=USER로 분리한다. source_path는 제공된 직접 원문 경로 그대로, source_quote는 해당 text의 정확한 직접 인용이다. 생성된 frame/confirmed_facts, 기존 INFERRED 제약, 질문의 제안 답안은 사용자 인용이 아니다. 사용자 선호는 hard=false, 명시 의무·상한·금지는 hard=true이고 인용 confidence=1이다.
- 원문과 질문을 함께 읽어 적용 대상·조건·수치·단위·의무 수준을 독립 검증한다. 예를 들어 연봉 인상률 질문의 '현재 연봉의 10% 이내로만 인상 가능'은 연봉 인상률<=10%의 직접 상한이다. 그 이유가 예산/협약 중 무엇인지 미상이어도 상한을 soft로 바꾸지 않는다. 이 제한을 스톡옵션·성과급을 포함한 전체 금전 보상 상한으로 확장하지 않는다.
- 새로운 직접 제약이 기존 가설을 구체화하더라도 기존 행을 고치거나 확신도를 올리지 않는다. 원문으로 확인된 범위만 새 USER 행에 쓰고, 기존 가설 중 아직 확인되지 않은 범위를 rationale에 구분한다. 같은 뜻의 제약이 이미 저장되어 있으면 다시 만들지 않는다.
- 고정된 물리 법칙과 그 법칙이 이 문제에 적용되는 조건을 구분한다. 재료·전압·법규 적용 범위가 불명확하면 확인 필요로 둔다.
- 사용자의 최신 수정과 명시한 예외를 존중한다. 기존 hard 제약은 임의로 완화하거나 새 hard 제약으로 확장하지 않는다.
- 물리는 재료 양립성·경계조건, 정보는 권한·일관성·인터페이스, 조직은 계약·유인·운영 조건을 살핀다. physical_scope 밖에 물리 제약을 추가하지 않는다.
- 관행·선호는 변경 가능한 변수이며 절대 금기가 아니다. zone은 실제 적용 위치 또는 행위자·의사결정 관계다.
- taboo의 confirmed=true는 제공된 확인 HARD ID의 실제 constraint_id와 일치하는 경우만 허용한다. 기존 INFERRED가 hard=true여도 직접 사용자 확인을 뜻하지 않는다. 이번 출력에서 새로 제안한 행에는 저장 ID가 아직 없으므로 confirmed=true의 근거로 삼지 않는다. ID를 전달받지 못했으면 만들지 말고 confirmed=false로 둔다.
- 위반 사례는 해당 제약과 같은 영역·조건에 한정한다. 수량 목표 없이 근거 있는 것만 적는다. 추가 발견이 없으면 빈 배열.
[출력 JSON]
{"constraints":[{"statement":"가설: ...","kind":"PREFERENCE","category":"OPERATION","zone":"","parameter":"","operator":"none","value":"","unit":"","source":"DOMAIN","hard":false,"confidence":0.6,"rationale":"","violation_example":""}],"user_constraints":[],"taboo":[{"item":"","zone":"","why":"","constraint_id":"","confirmed":false}]}
user_constraints의 각 행은 같은 제약 필드와 source_path/source_quote를 포함한다. 추가할 직접 제약·가설·금기가 없으면 해당 배열은 []로 둔다.
