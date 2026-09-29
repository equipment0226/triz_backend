# 문제·도메인·제약 추출

[문제 추출·역질의](../stages/03-s1-intake.md) · [전체 하위 처리](../PROCESS_INDEX.md)

| 항목 | 저장값 |
|---|---|
| 식별자 | `STP-2faef8a0` · seq 640 |
| 실제 실행 Stage | s1_intake |
| DB stage | S1_INTAKE |
| node | s1_extract |
| Agent | interviewer |
| Prompt | P_S1_EXTRACT |
| 모델 | T1 / deepseek-flash |
| 결과 | WARN / UNVERIFIED |
| KST 시작 → 종료 | 2026-09-30 06:50:32 → 2026-09-30 06:50:58 |
| 저장 비용 USD | 0.0063708 |
| 토큰 입력 / 출력 | 7328 / 3477 |

## Input · 실제 전달 변수

각 링크는 저장된 값을 전부 담습니다. 표의 말줄임은 미리보기만 줄인 것입니다.

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `raw_query` | Display 산업에서 (대형 OLED) 배면 증착을 위해 상면에 패턴이 존재하는 반송물을(pattern glass) 반대로 180도 로테이션 해주는 설비가 있다. Line LOB 향상을 위해 해당… | [펼쳐 보기](#field-fb4c93b0a881805a) |
| `attachment_facts` | [] | 표에 전체 값 표시 |
| `clarify_history` | [<br>  "Q: 현재 takt time과 목표 takt time은 각각 몇 초인가?\nA: 53초에서 50초",<br>  "Q: 시퀀스 단계별(투입/로테이션/배출/복귀) 소요 시간은 각각 몇 초인가?\nA: 로테이션이 최대 비중",<br>  "Q: 글라스의 크기·중량·관성모멘트는 대략 얼마인가?\nA: 대략 2m급, 수십 kg",<br>  "Q: 가감속 프로파일(가속 시간, 최고 각속도)은 어떻게 설정되어 있는가?\nA: 가속 시간이 길고 최고속도 낮음"<br>] | 표에 전체 값 표시 |

<a id="field-fb4c93b0a881805a"></a>

<details>
<summary>raw_query · 전체 값</summary>

```json
"Display 산업에서 (대형 OLED) 배면 증착을 위해 상면에 패턴이 존재하는 반송물을(pattern glass) 반대로 180도 로테이션 해주는 설비가 있다. \r\nLine LOB 향상을 위해 해당 장비의 takt time을 단축해야 하나, 단순히 전체 속도를 향상하기 위해서는 로테이션에 개입하는 모터 및 인덱서의 부하율, 강성, 하드웨어 안정성 등의 문제로 인해 제약이 존재하는 상황이다. \r\n장비는 투입 > 로테이션 > 배출 후, 다시 원위치로 돌아와 다음 패턴 글라스의 투입을 대기하는 시퀀스로 구성되어있다. \r\n괜찮은 해결책은?"
```

</details>

## Output · 최종 저장 결과

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `domain` | 객체 · industry, sub_domain, job_family, legacy_note, target_system, super_system, sub_systems … | [펼쳐 보기](#field-37c4810e5289ee24) |
| `frame` | 객체 · restated_problem, symptom, when_where, current_workaround, prior_attempts, success_criteria, missing_info … | [펼쳐 보기](#field-3bc6e2acda9b3bf7) |
| `constraints` | 객체 · items, open_questions | [펼쳐 보기](#field-56153222a60432c1) |
| `candidate_characteristics` | [<br>  "takt time 단축(속도)",<br>  "모터·인덱서 부하율 여유",<br>  "구조 강성",<br>  "하드웨어 안정성",<br>  "가감속 프로파일 공격성",<br>  "정착 시간",<br>  "베어링·접촉면 발열",<br>  "계면 고유진동수 이격도",<br>  "정렬·클램프 정밀도",<br>  "시퀀스 직렬성"<br>] | 표에 전체 값 표시 |
| `candidate_conflicts` | 배열 5개 | [펼쳐 보기](#field-57c824d72f73bfed) |

<a id="field-37c4810e5289ee24"></a>

<details>
<summary>domain · 전체 값</summary>

```json
{
  "industry": "디스플레이 제조 장비",
  "sub_domain": "대형 OLED 배면 증착 인라인 반송·로테이션 설비",
  "job_family": "생산기술·장비 엔지니어링",
  "legacy_note": "패턴 글라스를 180도 로테이션하는 서보 제어 가감속 프로파일 방식 구동계, 투입>로테이션>배출>원위치 복귀 시퀀스",
  "target_system": "로테이션 구동계 단독(모터·인덱서·회전축)",
  "super_system": "상위 대형 OLED 배면 증착 인라인 반송 라인 스케줄러",
  "sub_systems": [
    "모터·인덱서 출력축",
    "회전축·베어링 결합부",
    "클램프 계면",
    "서보 제어기·가감속 프로파일",
    "정렬·클램프 공정 유닛"
  ],
  "operating_env": "인라인 반송 라인 내 로테이션 스테이션, 2m급 대형 글라스(수십 kg) 취급, 서보 제어 운전",
  "domain_tags": [
    "takt time 단축(cycle time reduction)",
    "회전 동역학(rotational dynamics)",
    "가감속 프로파일(motion profile)",
    "서보 제어(servo control)",
    "부하율(load ratio)",
    "구조 강성(structural stiffness)",
    "고유진동수(natural frequency)",
    "베어링 발열(bearing heating)",
    "정착 시간(settling time)",
    "하드웨어 안정성(hardware stability)"
  ],
  "is_engineering": true,
  "problem_type": "PHYSICAL_TECHNICAL",
  "difficulty": "frontier",
  "physical_scope": "회전 동역학·구조 강성·동적 제어 — 180도 로테이션 구동계의 가감속 프로파일과 takt time 단축, 모터·인덱서 부하율·강성·하드웨어 안정성 간 상충"
}
```

</details>

<a id="field-3bc6e2acda9b3bf7"></a>

<details>
<summary>frame · 전체 값</summary>

```json
{
  "restated_problem": "대형 OLED 패턴 글라스 180도 로테이션 설비의 takt time을 53초에서 50초 이하로 단축하되, 모터·인덱서 부하율·강성·하드웨어 안정성 저하 없이 달성해야 한다.",
  "symptom": "로테이션 가속·감속·정지 구간이 takt의 지배적 병목이며, 전체 속도 상향 시 부하율·강성·안정성 제약에 걸린다.",
  "when_where": "로테이션 가속·감속·정지 구간(발생중), 모터·인덱서 출력축과 회전축 결합부",
  "current_workaround": "가속 시간이 길고 최고 각속도가 낮은 보수적 가감속 프로파일로 운전",
  "prior_attempts": [],
  "success_criteria": [
    "takt time <= 50초 달성",
    "모터·인덱서 부하율 허용 범위 이내 유지",
    "강성 저하 없음",
    "하드웨어 안정성 저하 없음"
  ],
  "missing_info": [
    "모터·인덱서 정격 토크 수치가 없어 부하율 여유의 절대적 판단이 불가하다.",
    "글라스 관성모멘트 실측값이 없어 각가속도 상향 시 필요 토크 산정이 불가하다.",
    "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)가 없어 단축 여지 산정이 불가하다.",
    "정렬·클램프 공정 소요 시간이 없어 직렬 구간 병목 비중 판단이 불가하다.",
    "단계별 타임스탬프 실측 분해 데이터가 없어 병목 구간 확정이 불가하다.",
    "운전 중 베어링·접촉면 온도 측정값이 없어 발열 한계 판단이 불가하다.",
    "회전축·베어링·클램프 계면 고유진동수가 없어 공진 위험 판단이 불가하다.",
    "강성·하드웨어 안정성 정량 허용 기준값이 없어 HARD 제약 위반 판정이 불가하다."
  ],
  "confidence": 0.6
}
```

</details>

<a id="field-56153222a60432c1"></a>

<details>
<summary>constraints · 전체 값</summary>

```json
{
  "items": [
    {
      "kind": "NUMERIC",
      "statement": "takt time을 50초 이하로 단축해야 한다",
      "parameter": "takt time",
      "operator": "<=",
      "value": "50",
      "unit": "s",
      "source": "USER",
      "confidence": 1.0,
      "hard": true,
      "rationale": "Line LOB 향상 목표"
    },
    {
      "kind": "NUMERIC",
      "statement": "현재 takt time은 53초이다",
      "parameter": "current takt time",
      "operator": "==",
      "value": "53",
      "unit": "s",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "현재 기준값"
    },
    {
      "kind": "MUST_NOT_HAVE",
      "statement": "모터 및 인덱서의 부하율이 허용 범위를 초과해서는 안 된다",
      "parameter": "load ratio",
      "operator": "<=",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": true,
      "rationale": "부하율 제약"
    },
    {
      "kind": "MUST_NOT_HAVE",
      "statement": "강성이 저하되어서는 안 된다",
      "parameter": "stiffness",
      "operator": ">=",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": true,
      "rationale": "강성 제약"
    },
    {
      "kind": "MUST_NOT_HAVE",
      "statement": "하드웨어 안정성이 저하되어서는 안 된다",
      "parameter": "hardware stability",
      "operator": ">=",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": true,
      "rationale": "안정성 제약"
    },
    {
      "kind": "PREFERENCE",
      "statement": "장비 시퀀스(투입>로테이션>배출>원위치 복귀)를 유지하는 것이 바람직하다",
      "parameter": "sequence",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "시퀀스 변경 가능성 미확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "정렬·클램프 공정 유닛 정지 후 정렬·클램프 공정이 로테이션과 직렬로 소요 시간을 추가한다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "정렬·클램프 공정 존재, 소요 시간 수치 미확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "로테이션 구동은 서보 제어 가감속 프로파일 방식이다",
      "parameter": "제어 방식",
      "operator": "==",
      "value": "서보 제어 가감속",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "구동 방식 확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "로테이션 가속·감속·정지 구간이 takt의 지배적 병목이다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "단계별 타임스탬프 분해 데이터 미확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "글라스는 2m급 대형이며 수십 kg 수준이다",
      "parameter": "glass size/weight",
      "operator": "==",
      "value": "2m급, 수십 kg",
      "unit": "",
      "source": "USER",
      "confidence": 0.6,
      "hard": false,
      "rationale": "추정: 실측 미확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "고속화 시 베어링·접촉면 발열이 증가할 수 있다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 0.6,
      "hard": false,
      "rationale": "추정: 직접 관측 근거 없음"
    },
    {
      "kind": "MUST_NOT_HAVE",
      "statement": "정렬·클램프 공정을 로테이션 감속 구간과 중첩(병렬화)할 수 없다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "중첩 불가(잘못하면 Slip 파손)"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "원위치 복귀는 역회전 방식이며 복귀 시 글라스가 없다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "복귀 동작 구조 확인"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "모터·인덱서 정격 토크와 현재 부하율은 미확인이다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "확인 필요 항목"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)는 미확인이다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "확인 필요 항목"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "회전축·베어링·클램프 계면 고유진동수는 미확인이다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "확인 필요 항목"
    },
    {
      "kind": "MUST_HAVE",
      "statement": "로테이션 구동계 전체 강성·하드웨어 안정성의 정량 허용 기준값은 미확인이다",
      "parameter": "",
      "operator": "==",
      "value": "",
      "unit": "",
      "source": "USER",
      "confidence": 1.0,
      "hard": false,
      "rationale": "확인 필요 항목"
    }
  ],
  "open_questions": [
    "모터·인덱서의 정격 토크와 현재 부하율은 얼마인가?",
    "글라스의 크기·중량·관성모멘트는 얼마인가?",
    "가감속 프로파일(가속 시간, 최고 각속도, 정착 시간)은 어떻게 설정되어 있는가?",
    "정지 후 정렬·클램프 공정의 소요 시간은 얼마인가?",
    "단계별 타임스탬프 분해(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기) 실측 데이터가 있는가?",
    "운전 중 베어링·접촉면 온도 측정값이 있는가?",
    "회전축·베어링·클램프 계면 고유진동수는 얼마인가?",
    "강성·하드웨어 안정성의 정량 허용 기준값은 얼마인가?"
  ]
}
```

</details>

<a id="field-57c824d72f73bfed"></a>

<details>
<summary>candidate_conflicts · 전체 값</summary>

```json
[
  "가속도(각가속도)를 높이면 takt time은 줄지만 모터·인덱서 부하율이 상승한다.",
  "최고 각속도를 높이면 takt time은 줄지만 베어링·접촉면 발열과 진동이 증가해 강성·안정성이 저하된다.",
  "가속 시간을 줄이면 takt time은 줄지만 가진 주파수가 계면 고유진동수에 접근해 공진 위험이 커진다.",
  "정착 시간을 줄이면 takt time은 줄지만 잔류 진동·오버슈트로 정렬·클램프 정밀도가 저하된다.",
  "정렬·클램프를 로테이션 감속 구간과 중첩하면 takt time은 줄지만 Slip 파손 위험이 발생한다."
]
```

</details>

## 검증과 추적

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `verdicts` | [<br>  {<br>    "verdict": "UNVERIFIED",<br>    "score": 0.0,<br>    "skipped": true,<br>    "source": "policy"<br>  }<br>] | 표에 전체 값 표시 |
| `error` | "" | 표에 전체 값 표시 |
| `input_metadata` | {<br>  "prompt_id": "P_S1_EXTRACT",<br>  "prompt_hash": "3e082e0ce8473db33b23bafd569c3cbf43b7982988d5339f16ea41450b77d2a3"<br>} | 표에 전체 값 표시 |
| `prompt_text_fingerprints` | {<br>  "system": {<br>    "sha256": "c203eafa84815bd6b883baf390d8aaf91480531420b3bb628de476843425ff84",<br>    "utf8_bytes": 7706<br>  },<br>  "user": {<br>    "sha256": "3e082e0ce8473db33b23bafd569c3cbf43b7982988d5339f16ea41450b77d2a3",<br>    "utf8_bytes": 16042<br>  }<br>} | 표에 전체 값 표시 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label, agent_id … | [펼쳐 보기](#field-693dcc39e4b8c5b9) |

<a id="field-693dcc39e4b8c5b9"></a>

<details>
<summary>step_metadata · 전체 값</summary>

```json
{
  "step_id": "STP-2faef8a0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "seq": 640,
  "stage": "S1_INTAKE",
  "node": "s1_extract",
  "label": "문제·도메인·제약 추출",
  "agent_id": "interviewer",
  "prompt_id": "P_S1_EXTRACT",
  "tier": "T1",
  "model": "deepseek-flash",
  "status": "WARN",
  "verify_attempts": 1,
  "verdict": "UNVERIFIED",
  "verdict_score": 0.0,
  "human_intervened": 0,
  "tokens_in": 7328,
  "tokens_out": 3477,
  "cost_usd": 0.0063708,
  "error": "",
  "started_at": "2026-09-29T21:50:32.914390",
  "ended_at": "2026-09-29T21:50:58.931797",
  "scope": "LATEST_RERUN"
}
```

</details>

출처: `steps.input_slice` / `steps.output_json` / `steps.verdicts`. 내부 수정 호출의 중간 원문은 이 Step의 최종 Output과 다릅니다. 모델 호출 횟수·비용·원문 해시는 [호출 원장](../CALLS.md)에서 확인할 수 있습니다.
