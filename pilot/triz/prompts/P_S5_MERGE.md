여러 트랙의 후보를 모순 해소와 인과 근거로 통합한다. 새 해법·사실·출처를 창작하지 않는다.
[아이디어] {{all_ideas}}
[핵심 문제] {{key_problems}}
[모순] {{contradictions}}
[인과 경로와 가설] {{causal_packet}}
[재정의 신호] {{redefinition_hints}}
[검색 자료: 미검증 조건을 반박하는 데 사용] {{evidence}}
각 후보의 결합 원인, 개입 변수, 개선 목표 달성 경로와 악화 목표 보존 경로를 확인한다.
같은 모순·같은 개입 변수·같은 작동 방식이면 병합한다. 모든 원본 ID를 keep_ids에 보존한다. 서버가 원본의 출처·자원·조건·가설·메커니즘을 복원하므로 같은 내용을 다시 출력하지 않는다. 조건이 상충하면 resolution_argument에 설명하고 UNSUPPORTED로 둔다.
resolution_status: RESOLVED(조건부로 양쪽 요구 성립 경로를 설명), TRADEOFF(절충·손실 이전), UNSUPPORTED(경로/근거 부족). RESOLVED는 실증 완료를 의미하지 않는다.
핵심 가설이 틀렸을 때의 실패, 가장 강한 반박과 이를 구분할 관측을 검토한다. 원본에 없는 판단만 짧게 추가한다. 기존 해법이 다른 가설에서 유효하면 그 조건을 명시한다. 선행 문제 정의를 임의로 바꾸지 않는다.
addresses는 실제 해소할 모순 ID만. 모순과 관련 없는 후보는 제외한다.
최대 {{max_ideas}}개. {{min_ideas}}개는 탐색 목표일 뿐 수량·트랙·신규성 할당을 채우기 위해 약한 안을 남기지 않는다.
need_more는 핵심 모순 미해결, 단일 가설 의존, 부적합 근거일 때 true. 개수만으로 true로 하지 않는다.
novelty_class는 SAME_DOMAIN/CROSS_DOMAIN/NEW. 외부 검증 근거가 없으면 ‘검증됨’을 주장하지 않는다.
출력은 선택·병합 판단의 차이만 기록한다. 후보마다 필수 필드는 keep_ids, addresses, resolution_status, resolution_argument 4개다. resolution_argument는 양쪽 요구의 성립 여부와 결정적 조건을 120자 이내로 쓴다.
첫 keep_id의 제목·설명을 그대로 쓰면 title/idea를 생략한다. 여러 원본을 병합해 실제로 달라진 경우에만 title/idea/mechanism/intervention_variable을 추가한다. 새로 확인한 조건·반박·관측이 있으면 conditions/strongest_objection/validation_test를 추가하되 각 1문장이다. 원본과 같은 값, 빈 선택 필드, track/source_refs는 출력하지 않는다.
{"ideas":[{"keep_ids":[],"addresses":[],"resolution_status":"UNSUPPORTED","resolution_argument":""}],"coverage_note":"","gaps":[],"need_more":false}
