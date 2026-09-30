# 저장 데이터 · 54a5abd8fad4

정규 JSON SHA-256: `54a5abd8fad48f4ca355ea9cd66c490afe248babac0b93aae57d706abe99ecf6`

```json
{
  "intervention": "서보 제어기에 부하 구간용 보수 프로파일과 무부하 복귀 구간용 별도 프로파일 세트를 등록하고, 글라스 클램프 체결 신호로 두 세트를 전환한다.",
  "target": "서보 제어기의 가감속 프로파일 파라미터 세트(부하/무부하 분리)",
  "changed_variable": "복귀 구간(무부하) 가속 시간·최고 각속도·정착 시간 프로파일 파라미터",
  "mediating_functions": [
    "글라스 유무(부하 상태) 검출 신호가 프로파일 세트 선택을 결정",
    "무부하 복귀 구간에서 회전체 관성모멘트 감소가 동일 토크에서 더 높은 각가속도를 허용",
    "부하 구간 프로파일 불변이 부하율·강성·안정성 HARD 제약을 보존"
  ],
  "outcome": "복귀 구간 시간이 단축되어 전체 takt이 50초 이하로 낮아질 수 있다. 부하 구간 부하율은 불변으로 유지된다. 복귀 구간 단축 폭은 미측정이며, 복귀 구간 시간 비중과 무부하 관성모멘트 실측 후 산정한다.",
  "operating_scope": "서보 제어 가감속 프로파일 방식의 180도 로테이션 구동계. 부하 구간(투입~배출, 글라스 있음)과 무부하 복귀 구간(역회전, 글라스 없음)이 구분되는 운전 조건. 시퀀스(투입>로테이션>배출>원위치 복귀) 유지.",
  "contribution": "DIRECT",
  "control_mode": "ACTIVE",
  "control_chain": {
    "sensor": "글라스 클램프 체결 센서(신규: 글라스 유무 검출 신호)",
    "estimator": "제어기 내부 부하 상태 판정(클램프 체결 신호 기반)",
    "decision": "부하/무부하 프로파일 세트 선택",
    "actuator": "서보 모터·인덱서 가감속 프로파일 명령",
    "target": "회전축 각가속도·최고 각속도"
  },
  "conditions": [
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "복귀 구간에 글라스가 없어 관성모멘트가 부하 구간보다 작다(사용자 명시)",
      "applicability": "CON-36a299e8(원위치 복귀는 역회전 방식이며 복귀 시 글라스가 없다)로 확인됨. 복귀 구간 무부하 관성모멘트 J_unload는 실측 필요(미확인)."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "서보 제어기가 복수 프로파일 세트 전환을 지원한다(미확인)",
      "applicability": "서보 제어기 사양서·설정 화면에서 복수 프로파일 세트 등록·전환 기능 지원 여부를 현장 확인한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "부하 구간 부하율 60~70% 추정(정확 수치 미확인)",
      "applicability": "CON-215562ab(현재 부하율 60% 수준), CON-4fd896a3(70% 수준이면 위험)으로 확인됨. 정확 수치는 부하율 로그 실측으로 확인 필요."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "가감속 프로파일 파라미터 미확인",
      "applicability": "CON-6a1787d3(가속 시간, 최고 각속도, 정착 시간 미확인). 서보 제어기 파라미터 설정값을 현장에서 확인한다."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "부하율 허용 범위 수치 미확인",
      "applicability": "CON-7d37c553(모터·인덱서 부하율이 허용 범위를 초과해서는 안 된다, 허용 수치 미확인). 정격 토크·부하율 로그로 허용 범위를 확정한다."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "강성·안정성 정량 허용 기준값 미확인",
      "applicability": "CON-cc073e11(로테이션 구동계 전체 강성·하드웨어 안정성의 정량 허용 기준값 미확인). 진동·변형 측정으로 기준값을 확정한다."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "단계별 타임스탬프 실측 데이터로 복귀 구간 시간 비중 확인 필요",
      "applicability": "첨부 answers[0](실측 데이터 존재, 구간별 수치 미확인). 단계별 타임스탬프 분해로 복귀 구간 시간 비중을 확인한다."
    },
    {
      "source_idea_id": "IDEA-037c9e7b",
      "condition": "복귀 구간 고속화가 정착 시간·잔류 진동에 영향을 주지 않을 것(미확인)",
      "applicability": "복귀 종료 정착 시간·잔류 진동을 측정하여 허용 범위 내 여부를 확인한다. 확인 완료를 주장하지 않는다."
    }
  ],
  "claims": [
    {
      "text": "복귀 구간에 글라스가 없어 관성모멘트가 부하 구간보다 작다",
      "status": "USER_REPORTED",
      "source_cause_id": "N8",
      "evidence_refs": [
        "CON-36a299e8"
      ]
    },
    {
      "text": "정렬·클램프를 로테이션 감속 구간과 중첩하면 Slip 파손이 발생한다",
      "status": "OBSERVED",
      "source_cause_id": "N8",
      "evidence_refs": [
        "CON-b76ecf8e"
      ]
    },
    {
      "text": "정렬·클램프 유닛이 로테이션과 직렬로 4초 내외 고정 지연을 추가한다",
      "status": "OBSERVED",
      "source_cause_id": "N7",
      "evidence_refs": [
        "CON-b743bd0a",
        "CON-b76ecf8e"
      ]
    },
    {
      "text": "회전축·베어링·클램프 계면 고유진동수가 미확인이라 공진 회피 대역을 설정할 수 없다",
      "status": "OBSERVED",
      "source_cause_id": "N11",
      "evidence_refs": [
        "CON-7cf7abd3",
        "CON-cc073e11"
      ]
    },
    {
      "text": "복귀 구간 전용 프로파일 적용 시 복귀 구간 시간이 단축되어 전체 takt이 50초 이하로 낮아질 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": []
    },
    {
      "text": "복귀 구간 고속화로 베어링 발열이 누적되어 다음 부하 사이클 정착 시간을 악화시킬 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": [
        "CON-e9a84575"
      ]
    },
    {
      "text": "복귀 구간 고속화가 회전축·베어링 계면 공진 대역을 통과할 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "N11",
      "evidence_refs": [
        "CON-7cf7abd3"
      ]
    }
  ]
}
```
