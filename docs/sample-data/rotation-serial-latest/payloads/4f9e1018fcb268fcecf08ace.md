# 저장 데이터 · 4f9e1018fcb2

정규 JSON SHA-256: `4f9e1018fcb268fcecf08ace1821a2b2d1ee433e0c20e3164c419823b4d6a3b0`

```json
{
  "intervention": "서보 제어기에 부하율·온도 피드백과 진동·온도 판정 경로를 병렬로 추가하고, 부하율 임계값 미만 조건에서만 가속도를 조정하며 임계값 근접 시 하향한다.",
  "target": "서보 제어기 가감속 프로파일(가속도 상향/하향 임계값)",
  "changed_variable": "가속도 상향/하향 임계값",
  "mediating_functions": [
    "부하율·온도 실시간 계측 → 가속도 조정 신호 변환",
    "진동·온도 계측 → 강성·안정성 위반 판정 신호 변환",
    "임계값 근접 검출 → 가속도 하향 명령"
  ],
  "outcome": "부하율 허용 범위를 초과하지 않으면서 가감속 구간 시간을 줄이고, 강성·안정성 위반 여부를 판정할 수 있다.",
  "operating_scope": "로테이션 가속·감속·정지 구간(부하 상태). 기준값 확정 전에는 가속도 상향 폭 0으로 운전.",
  "contribution": "DIRECT",
  "control_mode": "ACTIVE",
  "control_chain": {
    "sensor": "모터·인덱서 부하율 센서, 베어링·접촉면 온도 센서, 회전축 진동 센서",
    "estimator": "부하율·온도·진동 실측값에서 임계값 도달 여부 및 강성·안정성 위반 여부 추정",
    "decision": "부하율이 임계값 미만이면 가속도 상향, 임계값 근접 시 하향, 진동·온도가 임계 도달 시 상향 중단",
    "actuator": "서보 제어기 가감속 프로파일 파라미터(가속도)",
    "target": "서보 모터 출력축 → 인덱서 → 회전축 → 베어링 접촉면의 토크·각가속도 전달 계면"
  },
  "conditions": [
    {
      "source_idea_id": "IDEA-88a36ccc",
      "condition": "부하율이 임계값 미만인 조건에서만 가속도를 조정하고, 임계값 근접 시 하향하여 부하율 허용 범위 요구를 보존한다.",
      "applicability": "부하율 임계값은 미확인(CON-4fd896a3: 70% 수준 위험 추정)이므로, 부하율 로그와 정격 토크 실측 후 산정한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-88a36ccc",
      "condition": "강성·안정성 정량 허용 기준값(CON-cc073e11)을 설계 입력으로 반영한다.",
      "applicability": "기준값이 미확인이므로 진동·온도 계측으로 기준선을 수립하고, 기준값 확정 전에는 가속도 상향 폭을 0으로 둔다. 확인 완료를 주장하지 않는다."
    }
  ],
  "claims": [
    {
      "text": "생산 takt 요구(50초 이하) 미달로 인한 라인 생산성 손실",
      "status": "OBSERVED",
      "source_cause_id": "N1",
      "evidence_refs": [
        "CON-1f3bada2",
        "CON-58b5c6a1"
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
      "text": "정렬·클램프를 감속 구간과 중첩하면 Slip 파손이 발생한다",
      "status": "OBSERVED",
      "source_cause_id": "N8",
      "evidence_refs": [
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
      "text": "부하율·온도 실시간 감시로 임계값 미만 구간에서만 가속도를 조정하면 부하율 허용 범위를 초과하지 않으면서 가감속 구간 시간을 줄일 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": []
    },
    {
      "text": "진동·온도 계측값이 임계에 도달하는 시점을 실시간 검출하는 동적 판정 임계를 두면, 기준값을 고정 상한으로 확정하지 않고도 강성·안정성 위반 판정이 가능하다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": []
    }
  ]
}
```
