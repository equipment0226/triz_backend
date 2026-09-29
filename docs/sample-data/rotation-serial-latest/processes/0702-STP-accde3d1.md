# 제약 검토 10–10/10

[제약 검토](../stages/09-s7-gate.md) · [전체 하위 처리](../PROCESS_INDEX.md)

| 항목 | 저장값 |
|---|---|
| 식별자 | `STP-accde3d1` · seq 702 |
| 실제 실행 Stage | s7_gate |
| DB stage | S7_CONSTRAINT |
| node | s7_gate_10 |
| Agent | gatekeeper |
| Prompt | P_S7_GATEKEEPER |
| 모델 | T2 / deepseek-flash |
| 결과 | OK / PASS |
| KST 시작 → 종료 | 2026-09-30 07:26:15 → 2026-09-30 07:26:25 |
| 저장 비용 USD | 0.0025053 |
| 토큰 입력 / 출력 | 4647 / 926 |

Stage 귀속은 `stage_start` 이벤트 구간으로 확인했습니다. DB의 stage 문자열도 위 표에 그대로 남겼습니다.

## Input · 실제 전달 변수

각 링크는 저장된 값을 전부 담습니다. 표의 말줄임은 미리보기만 줄인 것입니다.

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `constraints_full` | 배열 18개 | [펼쳐 보기](#field-fc5a781c7a171944) |
| `concepts_for_gate` | 배열 1개 | [펼쳐 보기](#field-f923f4ee3833d735) |

<a id="field-fc5a781c7a171944"></a>

<details>
<summary>constraints_full · 전체 값</summary>

```json
[
  {
    "constraint_id": "CON-2e5d6859",
    "kind": "NUMERIC",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "takt time을 50초 이하로 단축해야 한다",
    "parameter": "takt time",
    "operator": "<=",
    "value": "50",
    "unit": "s",
    "hard": true,
    "rationale": "Line LOB 향상 목표",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-87d3c928",
    "kind": "NUMERIC",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "현재 takt time은 53초이다",
    "parameter": "current takt time",
    "operator": "==",
    "value": "53",
    "unit": "s",
    "hard": false,
    "rationale": "현재 기준값",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-bae6ac73",
    "kind": "MUST_NOT_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "모터 및 인덱서의 부하율이 허용 범위를 초과해서는 안 된다",
    "parameter": "load ratio",
    "operator": "<=",
    "value": "",
    "unit": "",
    "hard": true,
    "rationale": "부하율 제약",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-88d264f2",
    "kind": "MUST_NOT_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "강성이 저하되어서는 안 된다",
    "parameter": "stiffness",
    "operator": ">=",
    "value": "",
    "unit": "",
    "hard": true,
    "rationale": "강성 제약",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-f82435ee",
    "kind": "MUST_NOT_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "하드웨어 안정성이 저하되어서는 안 된다",
    "parameter": "hardware stability",
    "operator": ">=",
    "value": "",
    "unit": "",
    "hard": true,
    "rationale": "안정성 제약",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-67ea8d4a",
    "kind": "PREFERENCE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "장비 시퀀스(투입>로테이션>배출>원위치 복귀)를 유지하는 것이 바람직하다",
    "parameter": "sequence",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "시퀀스 변경 가능성 미확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-9f449042",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "정렬·클램프 공정 유닛 정지 후 정렬·클램프 공정이 로테이션과 직렬로 소요 시간을 추가한다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "정렬·클램프 공정 존재, 소요 시간 수치 미확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-f1a96104",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "로테이션 구동은 서보 제어 가감속 프로파일 방식이다",
    "parameter": "제어 방식",
    "operator": "==",
    "value": "서보 제어 가감속",
    "unit": "",
    "hard": false,
    "rationale": "구동 방식 확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-6f1aa3c0",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "로테이션 가속·감속·정지 구간이 takt의 지배적 병목이다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "단계별 타임스탬프 분해 데이터 미확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-81c154fe",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "글라스는 2m급 대형이며 수십 kg 수준이다",
    "parameter": "glass size/weight",
    "operator": "==",
    "value": "2m급, 수십 kg",
    "unit": "",
    "hard": false,
    "rationale": "추정: 실측 미확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-489f9a78",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "고속화 시 베어링·접촉면 발열이 증가할 수 있다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "추정: 직접 관측 근거 없음",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-8b834790",
    "kind": "MUST_NOT_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "정렬·클램프 공정을 로테이션 감속 구간과 중첩(병렬화)할 수 없다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "중첩 불가(잘못하면 Slip 파손)",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-fe966295",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "원위치 복귀는 역회전 방식이며 복귀 시 글라스가 없다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "복귀 동작 구조 확인",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-03a2c34e",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "모터·인덱서 정격 토크와 현재 부하율은 미확인이다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "확인 필요 항목",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-a25b3ab7",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)는 미확인이다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "확인 필요 항목",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-f512b60e",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "회전축·베어링·클램프 계면 고유진동수는 미확인이다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "확인 필요 항목",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-0255b86a",
    "kind": "MUST_HAVE",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "로테이션 구동계 전체 강성·하드웨어 안정성의 정량 허용 기준값은 미확인이다",
    "parameter": "",
    "operator": "==",
    "value": "",
    "unit": "",
    "hard": false,
    "rationale": "확인 필요 항목",
    "source": "USER",
    "confidence": 1.0,
    "violation_example": ""
  },
  {
    "constraint_id": "CON-f3ea19b8",
    "kind": "NUMERIC",
    "category": "USER_STATED",
    "zone": "시스템 전체",
    "statement": "현재 부하율은 60% 수준으로 여유가 있다",
    "parameter": "load ratio",
    "operator": "==",
    "value": "60",
    "unit": "%",
    "hard": false,
    "rationale": "첨부 답변, 정확 수치 미확인",
    "source": "USER",
    "confidence": 0.6,
    "violation_example": ""
  }
]
```

</details>

<a id="field-f923f4ee3833d735"></a>

<details>
<summary>concepts_for_gate · 전체 값</summary>

```json
[
  {
    "concept_id": "CPT-S6-783786b342651a96",
    "title": "클램프 패드 유연막 분산 접촉",
    "description": "클램프 계면의 강성 접촉 패드를 두께 (추정: 1~3mm)의 고마찰 엘라스토머 유연막으로 교체한다. 유연막이 접촉면을 넓혀 마찰력 분포를 균일화하고 국부 응력 집중을 완화하여 감속 중 Slip 임계를 상향한다. 유연막이 미세 진동을 흡수해 정착 시간도 단축될 수 있다.",
    "changes_to_system": [
      "클램프 계면의 강성 접촉 패드를 고마찰 엘라스토머 유연막으로 교체",
      "유연막 두께·재질 선정 및 정렬 정밀도 영향 평가"
    ],
    "required_resources": [
      "신규: 고마찰 엘라스토머 시트(내열 온도가 운전 온도 이상)",
      "기존 클램프 기구"
    ],
    "expected_effect": "감속 중 Slip 임계 상향 및 정착 시간 단축 가능성. 정렬 오차·Slip 발생률 변화는 미측정이며 개선율을 단정하지 않는다.",
    "assumptions": [
      "유연막 마찰계수가 기존 강성 패드 이상이다",
      "유연막 압축 변형이 정렬 정밀도 허용 범위 내이다",
      "유연막 내열 온도가 운전 온도 이상이다",
      "유연막 마찰계수가 기존 강성 패드 이상",
      "유연막 압축 변형이 정렬 정밀도 허용 범위 내",
      "유연막 내열 온도가 운전 온도 이상",
      "가속·감속 방향 하중 방향 확인",
      "비대칭 배치가 스테이지 질량 균형을 해치지 않음",
      "복귀 구간 무부하 확인",
      "클램프력 가변 액추에이터(비례 밸브 등) 확보",
      "감속 구간 클램프력 상향이 글라스 파손 한계 이내",
      "정지 후 클램프 해제-재클램프 시간이 직렬 구간에 추가되지 않음"
    ]
  }
]
```

</details>

## Output · 최종 저장 결과

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `results` | 배열 1개 | [펼쳐 보기](#field-342019824933c533) |

<a id="field-342019824933c533"></a>

<details>
<summary>results · 전체 값</summary>

```json
[
  {
    "concept_id": "CPT-S6-783786b342651a96",
    "per_constraint": [
      {
        "constraint_id": "CON-2e5d6859",
        "verdict": "UNKNOWN",
        "reason": "개념은 클램프 계면 유연막 교체만 언급, takt time 수치 없음"
      },
      {
        "constraint_id": "CON-87d3c928",
        "verdict": "UNKNOWN",
        "reason": "현재 takt 53초 언급 없음, 개념은 클램프 계면만 변경"
      },
      {
        "constraint_id": "CON-bae6ac73",
        "verdict": "UNKNOWN",
        "reason": "모터·인덱서 부하율 영향 미확인, 유연막이 부하율에 미치는 영향 없음"
      },
      {
        "constraint_id": "CON-88d264f2",
        "verdict": "UNKNOWN",
        "reason": "강성 저하 여부 미확인, 유연막이 강성에 미치는 영향 평가 없음"
      },
      {
        "constraint_id": "CON-f82435ee",
        "verdict": "UNKNOWN",
        "reason": "하드웨어 안정성 영향 미확인, 유연막 교체가 안정성에 미치는 영향 없음"
      },
      {
        "constraint_id": "CON-67ea8d4a",
        "verdict": "PASS",
        "reason": "시퀀스 변경 없음, 클램프 계면만 교체"
      },
      {
        "constraint_id": "CON-9f449042",
        "verdict": "PASS",
        "reason": "정렬·클램프 공정 유지, 유연막 교체는 공정 추가 아님"
      },
      {
        "constraint_id": "CON-f1a96104",
        "verdict": "PASS",
        "reason": "서보 제어 가감속 프로파일 방식 유지, 구동 방식 변경 없음"
      },
      {
        "constraint_id": "CON-6f1aa3c0",
        "verdict": "PASS",
        "reason": "가감속 구간 병목 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-81c154fe",
        "verdict": "PASS",
        "reason": "글라스 2m급 수십 kg 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-489f9a78",
        "verdict": "PASS",
        "reason": "고속화 시 발열 증가 가능성 유지, 개념은 고속화를 주장하지 않음"
      },
      {
        "constraint_id": "CON-8b834790",
        "verdict": "PASS",
        "reason": "정렬·클램프와 로테이션 감속 구간 중첩 없음, 개념은 중첩을 주장하지 않음"
      },
      {
        "constraint_id": "CON-fe966295",
        "verdict": "PASS",
        "reason": "원위치 복귀 역회전 방식 유지, 개념은 복귀 방식을 변경하지 않음"
      },
      {
        "constraint_id": "CON-03a2c34e",
        "verdict": "PASS",
        "reason": "모터·인덱서 정격 토크 미확인 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-a25b3ab7",
        "verdict": "PASS",
        "reason": "가감속 프로파일 파라미터 미확인 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-f512b60e",
        "verdict": "PASS",
        "reason": "고유진동수 미확인 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-0255b86a",
        "verdict": "PASS",
        "reason": "강성·안정성 정량 기준값 미확인 사실 유지, 개념은 이를 변경하지 않음"
      },
      {
        "constraint_id": "CON-f3ea19b8",
        "verdict": "UNKNOWN",
        "reason": "현재 부하율 60% 수준 언급 없음, 유연막이 부하율에 미치는 영향 미확인"
      }
    ],
    "verdict": "CONDITIONAL",
    "violated_ids": [],
    "mitigation": "takt time 50초 이하 달성 여부와 모터·인덱서 부하율·강성·하드웨어 안정성에 대한 유연막의 영향을 정량 확인 필요. 유연막이 강성을 저하시키지 않음을 입증해야 함.",
    "requires_user_decision": true
  }
]
```

</details>

## 검증과 추적

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `verdicts` | [<br>  {<br>    "verdict": "PASS",<br>    "score": 1.0,<br>    "source": "none"<br>  }<br>] | 표에 전체 값 표시 |
| `error` | "" | 표에 전체 값 표시 |
| `input_metadata` | {<br>  "prompt_id": "P_S7_GATEKEEPER",<br>  "prompt_hash": "eb1392702bd5c0b494e89af92a617be8a4c402e7d82996e72b6086e2c11c525b"<br>} | 표에 전체 값 표시 |
| `prompt_text_fingerprints` | {<br>  "system": {<br>    "sha256": "0278f909c882cabb7fb78609187d4e34f9de3ce9ec7718beec20ada49d1585bb",<br>    "utf8_bytes": 106<br>  },<br>  "user": {<br>    "sha256": "eb1392702bd5c0b494e89af92a617be8a4c402e7d82996e72b6086e2c11c525b",<br>    "utf8_bytes": 15573<br>  }<br>} | 표에 전체 값 표시 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label, agent_id … | [펼쳐 보기](#field-ab01f67877269acc) |

<a id="field-ab01f67877269acc"></a>

<details>
<summary>step_metadata · 전체 값</summary>

```json
{
  "step_id": "STP-accde3d1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "seq": 702,
  "stage": "S7_CONSTRAINT",
  "node": "s7_gate_10",
  "label": "제약 검토 10–10/10",
  "agent_id": "gatekeeper",
  "prompt_id": "P_S7_GATEKEEPER",
  "tier": "T2",
  "model": "deepseek-flash",
  "status": "OK",
  "verify_attempts": 1,
  "verdict": "PASS",
  "verdict_score": 1.0,
  "human_intervened": 0,
  "tokens_in": 4647,
  "tokens_out": 926,
  "cost_usd": 0.0025053,
  "error": "",
  "started_at": "2026-09-29T22:26:15.290595",
  "ended_at": "2026-09-29T22:26:25.501822",
  "scope": "LATEST_RERUN"
}
```

</details>

출처: `steps.input_slice` / `steps.output_json` / `steps.verdicts`. 내부 수정 호출의 중간 원문은 이 Step의 최종 Output과 다릅니다. 모델 호출 횟수·비용·원문 해시는 [호출 원장](../CALLS.md)에서 확인할 수 있습니다.
