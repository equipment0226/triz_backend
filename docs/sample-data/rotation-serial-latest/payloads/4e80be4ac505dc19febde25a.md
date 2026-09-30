# 저장 데이터 · 4e80be4ac505

정규 JSON SHA-256: `4e80be4ac505dc19febde25a743ddbac04d334efe727be1e4ddea7ba8887a4d8`

```json
[
  {
    "category": "SUBSTANCE",
    "name": "글라스 지지체·척의 질량(회전체 관성 질량)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 글라스 수십 kg + 지지체·척 자체 질량, 실측 미확인",
    "usable_for": [
      "회전체 관성모멘트 J 산정 입력으로 사용하여 가속 토크 요구량 계산",
      "경량화 여지 판단(질량 저감 시 동일 토크로 각가속도 상향 가능)"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SUBSTANCE",
    "name": "회전축-베어링 접촉면의 윤활제(그리스/오일)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 베어링 내 봉입량, 실측 미확인",
    "usable_for": [
      "마찰 계수 저감으로 동일 토크에서 가속 여유 확보",
      "발열 저감(고속화 시 온도 상승 억제)"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SUBSTANCE",
    "name": "정렬·클램프 유닛의 클램프 패드 접촉면",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 클램프 개수 미확인",
    "usable_for": [
      "클램프 응답 속도 향상 시 정렬·클램프 4초 단축 여지 검토",
      "Slip 방지 마찰 계면으로 활용"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FIELD",
    "name": "서보 모터·인덱서에서 발생하는 감속 시 회생 전력(역기전력)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 감속 구간 에너지량, 실측 미확인",
    "usable_for": [
      "회생 저항 대신 재사용 경로 확보 시 에너지 회수(단, 강성·안정성 영향 검증 선행 필요)"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FIELD",
    "name": "회전축-베어링 접촉면에서 발생하는 마찰열",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 운전 중 온도 측정값 미확인",
    "usable_for": [
      "온도 계측 시 고속화 한계 판정 지표로 전용",
      "열변형-정렬 정밀도 상관 검증 입력"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FIELD",
    "name": "구동계 운전 중 발생하는 진동(가진력)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 고유진동수·진폭 미확인",
    "usable_for": [
      "가속도 상향 시 공진 대역 통과 여부 판정 신호로 전용",
      "정착 시간 판정 지표"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FIELD",
    "name": "중력(글라스 자중)",
    "where": "IN_ENVIRONMENT",
    "availability": "FREE",
    "quantity_note": "수십 kg × g, 실측 미확인",
    "usable_for": [
      "회전 중 자중 방향 변화를 이용한 정렬 보조(추정: 미검증)",
      "클램프 부하 산정 입력"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SPACE",
    "name": "모터 출력축-인덱서 커플링과 하우징 사이 축방향 간극",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 수 mm 수준, 실측 미확인",
    "usable_for": [
      "진동 절연 요소 삽입 공간(단, 강성 저하 HARD 제약 검증 선행)",
      "센서(진동·온도) 부착 공간"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SPACE",
    "name": "회전축-베어링 접촉면 주변 미사용 공간",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 미확인",
    "usable_for": [
      "온도·진동 센서 부착",
      "윤활 보급 경로 추가"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SPACE",
    "name": "글라스 지지체·척의 비접촉 면적(글라스 배면 이외 영역)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 2m급 글라스 대비 지지체 면적 미확인",
    "usable_for": [
      "정렬 기준면·센서 타깃 추가 배치"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "TIME",
    "name": "원위치 복귀(역회전) 구간 — 글라스 없음",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 복귀 구간 시간 미확인",
    "usable_for": [
      "무부하 상태이므로 부하 상태보다 높은 각속도·각가속도 적용 가능(부하 상태별 프로파일 분리)",
      "복귀 구간에서 정렬·클램프 유닛 사전 동작(무부하 선행 배치) 검토"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "TIME",
    "name": "로테이션 정지 후 정렬·클램프 4초 구간",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "4초 내외(첨부 answers[1])",
    "usable_for": [
      "정렬·클램프 응답 속도 향상 시 단축 여지 검토",
      "감속 구간과 중첩 불가(HARD soft 제약)이므로 직렬 단축만 가능"
    ],
    "blocked_by_constraint": true
  },
  {
    "category": "TIME",
    "name": "투입·배출 구간의 대기 시간",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 단계별 타임스탬프 실측 데이터 존재(첨부 answers[0]), 수치 미확인",
    "usable_for": [
      "대기 구간을 가속 준비(사전 토크 인가)에 전용",
      "병렬화 가능 구간 식별"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "INFORMATION",
    "name": "단계별 타임스탬프 실측 데이터(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "실측 데이터 존재(첨부 answers[0]), 구간별 수치 미확인",
    "usable_for": [
      "가감속 병목(H1)과 직렬 공정 병목(H2) 판별",
      "takt 50초 달성 경로 계산 입력"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "INFORMATION",
    "name": "서보 제어기의 가감속 프로파일 파라미터 세트(가속 시간·최고 각속도·정착 시간)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "보수적 설정 추정(첨부 answers[3]), 수치 미확인",
    "usable_for": [
      "가속도 상향 여유 판정",
      "부하 상태별 프로파일 분리 설계 입력"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "INFORMATION",
    "name": "모터·인덱서 부하율 로그(현재 60~70% 추정)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "60~70% 수준(첨부 answers[2]), 정확 수치 미확인",
    "usable_for": [
      "가속도 상향 시 부하율 한계 도달 지점 판정",
      "HARD 제약(부하율) 위반 여부 검증"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "INFORMATION",
    "name": "운전 중 베어링·접촉면 온도 이력",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 측정값 미확인",
    "usable_for": [
      "고속화 시 발열 한계 판정",
      "열변형-정렬 정밀도 상관 검증"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FUNCTIONAL",
    "name": "서보 모터의 토크 제어 기능(가감속 프로파일 명령)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "기존 기능",
    "usable_for": [
      "부하 상태별(부하/무부하) 프로파일 분리 적용",
      "정착 시간 단축 튜닝"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FUNCTIONAL",
    "name": "인덱서의 180도 분할 회전 기능",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "기존 기능",
    "usable_for": [
      "분할 정지 위치를 정렬 기준으로 전용",
      "정지 구간 정밀도 활용"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FUNCTIONAL",
    "name": "정렬·클램프 유닛의 클램프 기능(부수 효과: 글라스 고정)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "기존 기능, 4초 내외",
    "usable_for": [
      "클램프 응답 속도 향상 시 직렬 지연 단축",
      "Slip 방지 기능으로 가속도 상향 허용 범위 확대"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "FUNCTIONAL",
    "name": "원위치 복귀 역회전 기능(글라스 없음)",
    "where": "IN_SYSTEM",
    "availability": "FREE",
    "quantity_note": "기존 기능",
    "usable_for": [
      "무부하 구간 고속 프로파일 적용",
      "복귀 중 정렬·클램프 사전 동작 검토"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SYSTEM_LEVEL",
    "name": "대형 OLED 배면 증착 인라인 반송 라인의 상위 takt 스케줄러",
    "where": "IN_SUPERSYSTEM",
    "availability": "FREE",
    "quantity_note": "라인 전체 takt 50초 목표",
    "usable_for": [
      "로테이션 외 타 공정 시간 조정 여지 확인",
      "라인 수준 병렬화 검토"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SYSTEM_LEVEL",
    "name": "증착·반송 공정(상위 라인 내 타 공정)의 유휴 시간",
    "where": "IN_SUPERSYSTEM",
    "availability": "FREE",
    "quantity_note": "추정: 미확인",
    "usable_for": [
      "로테이션 시간 증가분을 타 공정 유휴로 흡수 검토"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "SYSTEM_LEVEL",
    "name": "주변 열환경(라인 주변 온도·냉각 매체)",
    "where": "IN_ENVIRONMENT",
    "availability": "FREE",
    "quantity_note": "추정: 미확인",
    "usable_for": [
      "베어링·접촉면 발열 냉각 보조"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "DERIVED",
    "name": "부하 상태별 분리 가감속 프로파일(부하 구간 보수, 무부하 복귀 구간 공격)",
    "where": "DERIVED",
    "availability": "FREE",
    "quantity_note": "기존 파라미터 세트 조합으로 도출",
    "usable_for": [
      "단일 파라미터 상향 없이 takt 단축",
      "부하율·강성·안정성 HARD 제약 동시 만족 검토"
    ],
    "blocked_by_constraint": false
  },
  {
    "category": "DERIVED",
    "name": "단계별 타임스탬프 실측 데이터와 부하율 로그의 결합 분석",
    "where": "DERIVED",
    "availability": "FREE",
    "quantity_note": "기존 데이터 조합",
    "usable_for": [
      "H1/H2/H3 지배 메커니즘 판별",
      "takt 50초 달성 경로 정량 계산"
    ],
    "blocked_by_constraint": false
  }
]
```
