# 저장 데이터 · ec2a187b5663

정규 JSON SHA-256: `ec2a187b5663db8fbc8beeff93c47e0d1e7f500c15b4b811044020f04e6b8056`

```json
[
  {
    "concept_id": "CPT-S6-cd71ef3a6bbe17a8",
    "per_constraint": [
      {
        "constraint_id": "CON-1f3bada2",
        "verdict": "UNKNOWN",
        "reason": "개념에 takt time 수치 없음. '가속 여유 확보'만 언급, 50초 이하 충족 근거 없음"
      },
      {
        "constraint_id": "CON-58b5c6a1",
        "verdict": "UNKNOWN",
        "reason": "개념에 현재 takt time 53초 관련 수치·언급 없음"
      },
      {
        "constraint_id": "CON-7d37c553",
        "verdict": "UNKNOWN",
        "reason": "'동일 전력 예산에서 가속 여유 확보'만 언급, 부하율 변화 수치 없음"
      },
      {
        "constraint_id": "CON-fdcc301c",
        "verdict": "UNKNOWN",
        "reason": "'강성·안정성 영향 검증을 선행한다'는 가정만 있고 강성 저하 여부 미판정"
      },
      {
        "constraint_id": "CON-b038b5ea",
        "verdict": "UNKNOWN",
        "reason": "'강성·안정성 영향 검증을 선행한다'는 가정만 있고 안정성 저하 여부 미판정"
      },
      {
        "constraint_id": "CON-1f6c5cbf",
        "verdict": "PASS",
        "reason": "개념은 전력 회수·토크 보조만 추가, 시퀀스 변경 언급 없음"
      },
      {
        "constraint_id": "CON-39c6c05e",
        "verdict": "PASS",
        "reason": "정렬·클램프 직렬 소요 시간 구조를 변경하지 않음"
      },
      {
        "constraint_id": "CON-11c69fc8",
        "verdict": "PASS",
        "reason": "'서보 모터의 토크 제어 기능' 활용, 서보 제어 방식 유지"
      },
      {
        "constraint_id": "CON-f99689fe",
        "verdict": "PASS",
        "reason": "가속 구간 토크 보조로 가감속 구간 병목을 다룸, 위반 아님"
      },
      {
        "constraint_id": "CON-d5d4d9b9",
        "verdict": "UNKNOWN",
        "reason": "글라스 2m급·수십 kg 관련 언급 없음"
      },
      {
        "constraint_id": "CON-e9a84575",
        "verdict": "UNKNOWN",
        "reason": "베어링·접촉면 발열 관련 언급 없음"
      },
      {
        "constraint_id": "CON-b76ecf8e",
        "verdict": "PASS",
        "reason": "정렬·클램프 병렬화 언급 없음, 중첩 시도 없음"
      },
      {
        "constraint_id": "CON-36a299e8",
        "verdict": "PASS",
        "reason": "원위치 복귀 역회전 구조 변경 언급 없음"
      },
      {
        "constraint_id": "CON-16c8a185",
        "verdict": "PASS",
        "reason": "정격 토크·부하율 미확인 상태를 전제로만 다룸, 위반 아님"
      },
      {
        "constraint_id": "CON-6a1787d3",
        "verdict": "PASS",
        "reason": "가감속 프로파일 파라미터 미확인 전제, 위반 아님"
      },
      {
        "constraint_id": "CON-7cf7abd3",
        "verdict": "PASS",
        "reason": "고유진동수 미확인 전제, 위반 아님"
      },
      {
        "constraint_id": "CON-cc073e11",
        "verdict": "PASS",
        "reason": "강성·안정성 정량 기준 미확인 전제, 위반 아님"
      },
      {
        "constraint_id": "CON-215562ab",
        "verdict": "UNKNOWN",
        "reason": "현재 부하율 60% 관련 수치·언급 없음"
      },
      {
        "constraint_id": "CON-b743bd0a",
        "verdict": "UNKNOWN",
        "reason": "정렬·클램프 4초 관련 언급 없음"
      },
      {
        "constraint_id": "CON-4fd896a3",
        "verdict": "UNKNOWN",
        "reason": "부하율 70% 위험 관련 수치·언급 없음"
      }
    ],
    "verdict": "CONDITIONAL",
    "violated_ids": [],
    "mitigation": "회생 전력 재투입이 takt time 50초 이하 달성, 부하율 허용 범위 내 유지, 강성·안정성 저하 없음을 정량 검증해야 함. 특히 부하율 변화와 takt 단축량 실측 필요.",
    "requires_user_decision": true
  }
]
```
