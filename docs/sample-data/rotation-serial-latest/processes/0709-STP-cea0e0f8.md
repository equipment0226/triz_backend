# 미해결 부분 보완

[근거 자료·적용 조건 검토](../stages/10-s8-references.md) · [전체 하위 처리](../PROCESS_INDEX.md)

| 항목 | 저장값 |
|---|---|
| 식별자 | `STP-cea0e0f8` · seq 709 |
| 실제 실행 Stage | s8_references |
| DB stage | S6_CONCEPT |
| node | ax_repair_gap-23e4763bd7081652230dfb23_1 |
| Agent | effects_specialist |
| Prompt | P_AX_RECOVERY |
| 모델 | T2 / deepseek-flash |
| 결과 | OK / PASS |
| KST 시작 → 종료 | 2026-09-30 07:35:17 → 2026-09-30 07:35:36 |
| 저장 비용 USD | 0.0099558 |
| 토큰 입력 / 출력 | 17094 / 4023 |

Stage 귀속은 `stage_start` 이벤트 구간으로 확인했습니다. DB의 stage 문자열도 위 표에 그대로 남겼습니다.

## Input · 실제 전달 변수

각 링크는 저장된 값을 전부 담습니다. 표의 말줄임은 미리보기만 줄인 것입니다.

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `action` | "REPAIR_CANDIDATE" | 표에 전체 값 표시 |
| `baseline` | 객체 · source_idea_ids, active_effect_ids, mechanism_key, intervention_variable, resolution_argument, hypothesis_ids, prior_case_ids … | [펼쳐 보기](#field-e55c1ccd716d4661) |
| `blockers` | [<br>  {<br>    "kind": "IMPROVEMENT_SIDE_OMITTED",<br>    "description": "TC2: 부하율·강성 보호를 위해 가속도를 하향 → takt 초과 — 개선측 검증계획 연결 누락",<br>    "obligation_ids": [<br>      "TC-c8cf7951"<br>    ]<br>  }<br>] | 표에 전체 값 표시 |
| `requirements` | 객체 · items, open_questions | [전체 값](../payloads/78dee04ccc0592811507ece3.md) |
| `analysis` | 객체 · obligations, resources, existing_mechanisms, contract | [전체 값](../payloads/b5ea6e489c472fc41f8c05d2.md) |
| `schema` | 객체 · $defs, additionalProperties, properties, required, title, type | [펼쳐 보기](#field-ae50c5bb99003b30) |

<a id="field-e55c1ccd716d4661"></a>

<details>
<summary>baseline · 전체 값</summary>

```json
{
  "source_idea_ids": [
    "IDEA-374f5bee"
  ],
  "active_effect_ids": [],
  "mechanism_key": "복귀 구간 유휴 시간에 정렬·클램프 준비 동작 선행 배치",
  "intervention_variable": "복귀 구간 중 정렬·클램프 준비 동작 시퀀스",
  "resolution_argument": "정렬·클램프는 여전히 로테이션 정지 후에만 수행(중첩 없음)하므로 Slip 파손 위험(TC3/TC4의 PROTECT)을 보존한다. 동시에 준비 동작을 복귀 구간으로 옮겨 정지 후 스트로크를 줄여 직렬 시간 손실(TC4의 IMPROVE)을 줄인다. 시간 결합을 '정지 후 직렬'에서 '복귀 중 준비 + 정지 후 마무리'로 분리한다.",
  "hypothesis_ids": [
    "H2",
    "H3"
  ],
  "prior_case_ids": [],
  "quality_status": "REVISE",
  "quality_issues": [
    "핵심 인과('복귀 구간 준비 동작 → 정지 후 스트로크 감소')가 HYPOTHESIS로만 제시되고 정량 추정이 없어 takt 3초 단축 기여분을 판단할 수 없다.",
    "validation_plan의 실패 기준이 미확인 '강성·안정성 허용 기준'에 의존해 반증이 실질적으로 불가능하다.",
    "TC2: 부하율·강성 보호를 위해 가속도를 하향 → takt 초과 — 개선측 검증계획 연결 누락",
    "기존 자원 확인 또는 신규 도입 표시 필요: 정렬 액추에이터의 위치 결정 부수 효과",
    "기존 자원 확인 또는 신규 도입 표시 필요: 클램프 계면의 마찰 고정 기능"
  ],
  "id": "CPT-S6-ac128a6d03303a81",
  "title": "복귀 구간 정렬·클램프 사전 준비",
  "one_liner": "원위치 복귀(역회전, 무부하) 구간 동안 정렬·클램프 유닛을 다음 사이클 초기 위치로 복귀·개방 준비시켜 정지 후 정렬 스트로크를 줄인다.",
  "description": "정렬·클램프 유닛은 로테이션 정지 후에만 작동해야 하므로(CON-8b834790) 그 직렬 소요 시간이 takt에 누적된다. 원위치 복귀 구간은 글라스가 없어 정렬·클램프 유닛이 유휴이므로, 이 구간에 유닛을 초기 위치로 복귀시키고 클램프를 개방 상태로 준비한다. 다음 정지 시 정렬 액추에이터는 이미 초기 위치에서 출발해 스트로크가 줄고, 그만큼 직렬 구간 시간이 감소한다.",
  "working_principle": "복귀 구간의 무부하 유휴 시간에 정렬·클램프 준비 동작을 선행 배치하면 다음 정지 시 정렬 스트로크가 줄어 직렬 누적 시간이 감소한다.",
  "changes_to_system": [
    "정렬·클램프 유닛의 시퀀스를 복귀 구간까지 확장(준비 동작 선행)",
    "서보 제어기 시퀀스에 복귀 구간 정렬·클램프 준비 스텝 추가",
    "정렬 액추에이터 초기 위치 복귀 로직 추가"
  ],
  "required_resources": [
    "원위치 복귀 구간(역회전, 글라스 없음)의 무부하 시간",
    "정렬 액추에이터의 위치 결정 부수 효과",
    "클램프 계면의 마찰 고정 기능"
  ],
  "triz_origin": [
    {
      "track": "A_MATRIX",
      "ref": "원리20 유익작용의 지속(Continuity of useful action)"
    },
    {
      "track": "D_ARIZ",
      "ref": "ARIZ 5.1"
    },
    {
      "track": "E_TRIMMING",
      "ref": "트리밍 규칙D/정렬·클램프 공정 유닛"
    }
  ],
  "addresses_contradictions": [
    "TC-c8cf7951",
    "TC-097b79ff"
  ],
  "novelty_class": "SAME_DOMAIN",
  "evidence_ids": [],
  "expected_effect": "정렬·클램프 직렬 구간 소요 시간 감소분만큼 takt 단축. 목표 50초 이하 달성 여부는 정렬·클램프 실측 소요 시간에 의존하며 현재 미측정.",
  "assumptions": [
    "복귀 구간 중 정렬·클램프 유닛 동작이 허용된다(미확인)",
    "정렬·클램프 준비 동작 시간이 복귀 구간 내에 들어온다(미확인)",
    "복귀 구간 중 정렬·클램프 유닛 동작이 허용될 것(미확인)",
    "정렬·클램프 준비 동작 시간이 복귀 구간 내에 들어올 것(미확인)",
    "두 작용이 양립하기 어렵거나 별도로 수행되며 한 작용의 휴지기에 다른 유익한 작용을 넣을 수 있을 때.",
    "전환 시간·관측 지연 허용 여부 미확인",
    "복귀 구간 단축 허용 여부 미확인",
    "복귀 구간 단축 허용 여부 확인(미확인)",
    "시퀀스 유지 선호와의 충돌 검토"
  ],
  "open_risks": [
    "복귀 진동과 정렬·클램프 준비 동작이 간섭해 강성·안정성 HARD 제약을 위반할 수 있다",
    "시퀀스 유지 선호(CON-67ea8d4a, soft)와 충돌할 수 있다"
  ],
  "diagram_mermaid": "",
  "maturity": "CONCEPT",
  "change_scale": "PARTIAL",
  "validation_plan": [
    {
      "metric": "정지 후 정렬·클램프 소요 시간 및 총 takt time",
      "baseline": "현재 takt 53초, 정렬·클램프 소요 시간 미확인",
      "target": "총 takt 50초 이하, 정렬·클램프 직렬 소요 시간 감소",
      "experiment": "복귀 구간에 정렬·클램프 준비 동작을 추가한 상태에서 복귀 진동과 다음 정지 시 정렬 시간을 측정한다.",
      "failure_criterion": "복귀 진동이 강성·안정성 허용 기준을 초과하거나 총 takt가 50초를 초과하면 실패",
      "obligation_refs": [
        {
          "contradiction_id": "TC-097b79ff",
          "side": "IMPROVE"
        },
        {
          "contradiction_id": "TC-097b79ff",
          "side": "PROTECT"
        }
      ]
    },
    {
      "metric": "복귀 구간 진동·강성",
      "baseline": "미확인",
      "target": "강성·안정성 정량 허용 기준 내",
      "experiment": "복귀 구간 정렬·클램프 준비 동작 시 진동 스펙트럼을 측정해 허용 기준과 비교한다.",
      "failure_criterion": "진동이 허용 기준을 초과하면 실패",
      "obligation_refs": [
        {
          "contradiction_id": "TC-c8cf7951",
          "side": "PROTECT"
        }
      ]
    }
  ],
  "transfer_conditions": [
    "복귀 구간에 유휴 시간이 존재하는 회전 이송 설비",
    "정지 후 직렬 공정이 존재하는 인라인 설비"
  ]
}
```

</details>

<a id="field-ae50c5bb99003b30"></a>

<details>
<summary>schema · 전체 값</summary>

```json
{
  "$defs": {
    "Claim": {
      "additionalProperties": false,
      "properties": {
        "text": {
          "minLength": 1,
          "title": "Text",
          "type": "string"
        },
        "status": {
          "default": "HYPOTHESIS",
          "enum": [
            "HYPOTHESIS",
            "DERIVED",
            "USER_REPORTED",
            "OBSERVED"
          ],
          "title": "Status",
          "type": "string"
        },
        "source_cause_id": {
          "default": "",
          "title": "Source Cause Id",
          "type": "string"
        },
        "evidence_refs": {
          "default": [],
          "items": {
            "type": "string"
          },
          "title": "Evidence Refs",
          "type": "array"
        }
      },
      "required": [
        "text"
      ],
      "title": "Claim",
      "type": "object"
    },
    "Condition": {
      "additionalProperties": false,
      "properties": {
        "source_idea_id": {
          "title": "Source Idea Id",
          "type": "string"
        },
        "condition": {
          "minLength": 1,
          "title": "Condition",
          "type": "string"
        },
        "applicability": {
          "minLength": 1,
          "title": "Applicability",
          "type": "string"
        }
      },
      "required": [
        "source_idea_id",
        "condition",
        "applicability"
      ],
      "title": "Condition",
      "type": "object"
    },
    "Mechanism": {
      "additionalProperties": false,
      "properties": {
        "intervention": {
          "minLength": 1,
          "title": "Intervention",
          "type": "string"
        },
        "target": {
          "minLength": 1,
          "title": "Target",
          "type": "string"
        },
        "changed_variable": {
          "minLength": 1,
          "title": "Changed Variable",
          "type": "string"
        },
        "mediating_functions": {
          "items": {
            "type": "string"
          },
          "minItems": 1,
          "title": "Mediating Functions",
          "type": "array"
        },
        "outcome": {
          "minLength": 1,
          "title": "Outcome",
          "type": "string"
        },
        "operating_scope": {
          "minLength": 1,
          "title": "Operating Scope",
          "type": "string"
        },
        "contribution": {
          "default": "DIRECT",
          "enum": [
            "DIRECT",
            "ENABLER",
            "MONITOR_ONLY",
            "PASSIVE_MITIGATION"
          ],
          "title": "Contribution",
          "type": "string"
        },
        "control_mode": {
          "default": "PASSIVE",
          "enum": [
            "ACTIVE",
            "PASSIVE",
            "DIAGNOSTIC"
          ],
          "title": "Control Mode",
          "type": "string"
        },
        "control_chain": {
          "additionalProperties": {
            "type": "string"
          },
          "default": {},
          "title": "Control Chain",
          "type": "object"
        },
        "conditions": {
          "default": [],
          "items": {
            "$ref": "#/$defs/Condition"
          },
          "title": "Conditions",
          "type": "array"
        },
        "claims": {
          "default": [],
          "items": {
            "$ref": "#/$defs/Claim"
          },
          "title": "Claims",
          "type": "array"
        }
      },
      "required": [
        "intervention",
        "target",
        "changed_variable",
        "mediating_functions",
        "outcome",
        "operating_scope"
      ],
      "title": "Mechanism",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "title": {
      "maxLength": 300,
      "minLength": 1,
      "title": "Title",
      "type": "string"
    },
    "working_principle": {
      "maxLength": 4000,
      "minLength": 1,
      "title": "Working Principle",
      "type": "string"
    },
    "resolution_argument": {
      "maxLength": 4000,
      "minLength": 1,
      "title": "Resolution Argument",
      "type": "string"
    },
    "changes_to_system": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Changes To System",
      "type": "array"
    },
    "required_resources": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Required Resources",
      "type": "array"
    },
    "assumptions": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Assumptions",
      "type": "array"
    },
    "open_risks": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Open Risks",
      "type": "array"
    },
    "validation_plan": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "maxItems": 8,
      "minItems": 1,
      "title": "Validation Plan",
      "type": "array"
    },
    "provided_functions": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Provided Functions",
      "type": "array"
    },
    "required_functions": {
      "items": {
        "type": "string"
      },
      "maxItems": 12,
      "title": "Required Functions",
      "type": "array"
    },
    "subproblem": {
      "default": "",
      "title": "Subproblem",
      "type": "string"
    },
    "addresses_contradictions": {
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "title": "Addresses Contradictions",
      "type": "array"
    },
    "coherence": {
      "$ref": "#/$defs/Mechanism"
    }
  },
  "required": [
    "title",
    "working_principle",
    "resolution_argument",
    "changes_to_system",
    "required_resources",
    "assumptions",
    "open_risks",
    "validation_plan",
    "provided_functions",
    "required_functions",
    "addresses_contradictions",
    "coherence"
  ],
  "title": "RepairProposal",
  "type": "object"
}
```

</details>

## Output · 최종 저장 결과

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `title` | "복귀 구간 정렬·클램프 사전 준비 — 개선측 검증계획 보강 및 조건 정합화" | 표에 전체 값 표시 |
| `working_principle` | 원위치 복귀 구간(역회전, 글라스 없음)은 정렬·클램프 유닛이 유휴인 무부하 시간이다. 이 구간에 정렬 액추에이터를 다음 사이클 초기 위치로 복귀시키고 클램프를 개방 상태로 준비시켜 두면, 다음 정… | [펼쳐 보기](#field-84db32ee888b4f4c) |
| `resolution_argument` | TC4(정렬·클램프 직렬 유지 → takt 초과)의 개선측(직렬 시간 감소)을 '복귀 구간 준비 동작 선행'으로 달성하면서, 보호측(Slip 방지)은 '접촉·고정은 정지 후에만'이라는 제약을 그대로… | [펼쳐 보기](#field-e3b8ebdb035b1736) |
| `changes_to_system` | [<br>  "정렬·클램프 유닛의 시퀀스를 복귀 구간까지 확장(준비 동작 선행)",<br>  "서보 제어기 시퀀스에 복귀 구간 정렬·클램프 준비 스텝 추가",<br>  "정렬 액추에이터 초기 위치 복귀 로직 추가",<br>  "복귀 구간 진동·정렬 액추에이터 동작 간섭 감시(진단) 채널 추가"<br>] | 표에 전체 값 표시 |
| `required_resources` | [<br>  "원위치 복귀 구간(역회전, 글라스 없음)의 무부하 시간",<br>  "정렬 액추에이터의 위치 결정 부수 효과",<br>  "클램프 계면의 마찰 고정 기능",<br>  "신규: 복귀 구간 정렬·클램프 준비 동작의 완료를 확인하는 위치 센서(또는 서보 위치 피드백)",<br>  "신규: 복귀 구간 진동 측정 수단(가속도계 또는 서보 전류 리플 관측)"<br>] | 표에 전체 값 표시 |
| `assumptions` | 배열 5개 | [펼쳐 보기](#field-fcb160a47db4ba39) |
| `open_risks` | 배열 5개 | [펼쳐 보기](#field-74941bf367b2a1a5) |
| `validation_plan` | 배열 4개 | [펼쳐 보기](#field-10ce4422503d4184) |
| `provided_functions` | [<br>  "복귀 구간 무부하 유휴 시간에 정렬·클램프 준비 동작을 선행 배치",<br>  "정지 후 정렬 스트로크 감소로 직렬 누적 시간 감소",<br>  "감속 구간 중첩 금지 제약 하에서 Slip 방지 보존"<br>] | 표에 전체 값 표시 |
| `required_functions` | [<br>  "정렬 액추에이터의 초기 위치 복귀",<br>  "클램프 개방 상태 준비",<br>  "복귀 구간 준비 동작 완료 확인",<br>  "복귀 구간 진동·정렬 동작 간섭 감시"<br>] | 표에 전체 값 표시 |
| `subproblem` | "" | 표에 전체 값 표시 |
| `addresses_contradictions` | [<br>  "TC-097b79ff",<br>  "TC-c8cf7951",<br>  "TC-b5b764b0"<br>] | 표에 전체 값 표시 |
| `coherence` | 객체 · intervention, target, changed_variable, mediating_functions, outcome, operating_scope, contribution … | [펼쳐 보기](#field-570ce3578c688a06) |

<a id="field-84db32ee888b4f4c"></a>

<details>
<summary>working_principle · 전체 값</summary>

```json
"원위치 복귀 구간(역회전, 글라스 없음)은 정렬·클램프 유닛이 유휴인 무부하 시간이다. 이 구간에 정렬 액추에이터를 다음 사이클 초기 위치로 복귀시키고 클램프를 개방 상태로 준비시켜 두면, 다음 정지 시 정렬 스트로크가 줄어 정지 후 직렬 소요 시간이 감소한다. 정렬·클램프의 실제 접촉·고정 동작은 여전히 로테이션 정지 후에만 수행하므로 감속 구간 중첩 금지(CON-8b834790)를 위반하지 않고 Slip 파손 위험을 보존한다. 이 후보는 로테이션 가감속 프로파일을 변경하지 않으므로 TC1/TC2의 부하율·강성 상충에 직접 개입하지 않으며, TC4의 직렬 누적 시간을 줄이는 경로로 takt에 기여한다."
```

</details>

<a id="field-e3b8ebdb035b1736"></a>

<details>
<summary>resolution_argument · 전체 값</summary>

```json
"TC4(정렬·클램프 직렬 유지 → takt 초과)의 개선측(직렬 시간 감소)을 '복귀 구간 준비 동작 선행'으로 달성하면서, 보호측(Slip 방지)은 '접촉·고정은 정지 후에만'이라는 제약을 그대로 유지해 보존한다. 시간 결합을 '정지 후 전량 직렬'에서 '복귀 중 준비 + 정지 후 마무리'로 분리하는 것이 핵심이다. TC2(부하율·강성 보호를 위해 가속도 하향 → takt 초과)에 대해서는 이 후보가 가속도를 상향하지 않으므로 TC2의 개선측(부하율·강성 유지)을 훼손하지 않는다는 점을 검증계획에 명시한다. 즉 이 후보는 TC2의 보호측(takt 초과)을 직접 해소하지 않으므로, TC2 해소는 별도 후보(가속도 상향 또는 프로파일 상향)에 위임되며, 이 후보 단독으로는 3초 전량을 담당한다고 주장하지 않는다."
```

</details>

<a id="field-fcb160a47db4ba39"></a>

<details>
<summary>assumptions · 전체 값</summary>

```json
[
  "복귀 구간 중 정렬·클램프 유닛 동작이 허용된다(미확인, CON-67ea8d4a 시퀀스 유지 선호와의 정합성 검토 필요)",
  "정렬·클램프 준비 동작 시간이 복귀 구간 내에 들어온다(미확인, 복귀 구간 소요 시간 미확인)",
  "정렬 액추에이터가 정지 후 마무리 스트로크만으로 정렬 정밀도를 확보할 수 있다(미확인)",
  "복귀 구간 진동이 정렬·클램프 준비 동작과 간섭하지 않는다(미확인)",
  "정렬·클램프 소요 시간이 실측되면 이 후보의 takt 기여분을 정량화할 수 있다(미확인)"
]
```

</details>

<a id="field-74941bf367b2a1a5"></a>

<details>
<summary>open_risks · 전체 값</summary>

```json
[
  "복귀 진동과 정렬·클램프 준비 동작이 간섭해 강성·안정성 HARD 제약(CON-88d264f2, CON-f82435ee)을 위반할 수 있다. 정량 허용 기준값 미확인이므로 위반 판정 기준이 별도로 필요하다.",
  "시퀀스 유지 선호(CON-67ea8d4a, soft)와 충돌할 수 있다.",
  "정렬·클램프 소요 시간이 실측되지 않아 이 후보의 takt 기여분을 정량화할 수 없다.",
  "이 후보 단독으로 3초 전량을 단축한다는 보장이 없다. TC2 해소는 별도 후보에 위임된다.",
  "정렬 액추에이터의 초기 위치 복귀가 정지 후 마무리 스트로크를 줄이지 못할 가능성(스트로크 분해 미확인)"
]
```

</details>

<a id="field-10ce4422503d4184"></a>

<details>
<summary>validation_plan · 전체 값</summary>

```json
[
  {
    "metric": "정지 후 정렬·클램프 직렬 소요 시간 및 총 takt time",
    "baseline": "현재 takt 53초(CON-87d3c928, soft), 정렬·클램프 소요 시간 미확인",
    "target": "총 takt 50초 이하(CON-2e5d6859, HARD), 정렬·클램프 직렬 소요 시간 감소",
    "experiment": "복귀 구간에 정렬·클램프 준비 동작을 추가한 상태에서 단계별 타임스탬프(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기)를 실측 분해하고, 준비 동작 유무 조건에서 정지 후 정렬·클램프 소요 시간과 총 takt를 비교한다.",
    "success_criterion": "총 takt가 50초 이하이고 정렬·클램프 직렬 소요 시간이 준비 동작 도입 전 대비 감소",
    "failure_criterion": "총 takt가 50초를 초과하거나 정렬·클램프 직렬 소요 시간이 감소하지 않으면 실패",
    "obligation_refs": [
      {
        "contradiction_id": "TC-097b79ff",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-097b79ff",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "복귀 구간 진동·강성·하드웨어 안정성",
    "baseline": "미확인(고유진동수·강성 정량 허용 기준값 미확인, CON-f512b60e, CON-0255b86a)",
    "target": "강성·안정성 정량 허용 기준 내(기준값 확인 후 설정)",
    "experiment": "복귀 구간 정렬·클램프 준비 동작 시 진동 스펙트럼을 측정하고, 준비 동작 유무 조건을 비교한다. 강성·안정성 정량 허용 기준값이 확인되면 그 기준과 비교한다.",
    "success_criterion": "진동·변형이 허용 기준 내로 유지",
    "failure_criterion": "진동·변형이 허용 기준을 초과하거나, 허용 기준값이 미확인이라 판정 불가하면 실패로 간주하고 기준값 확보를 선행한다",
    "obligation_refs": [
      {
        "contradiction_id": "TC-097b79ff",
        "side": "PROTECT"
      },
      {
        "contradiction_id": "TC-c8cf7951",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "모터·인덱서 부하율 및 구동계 강성(TC2 개선측 보존 확인)",
    "baseline": "부하율 60% 수준(CON-f3ea19b8, soft, 정확 수치 미확인), 강성 정량 기준 미확인",
    "target": "부하율 허용 범위 내(CON-bae6ac73, HARD), 강성 저하 없음(CON-88d264f2, HARD)",
    "experiment": "이 후보는 로테이션 가감속 프로파일을 변경하지 않으므로, 준비 동작 도입 전후의 부하율 로그와 구동계 진동·변형을 비교해 부하율·강성이 악화되지 않음을 확인한다.",
    "success_criterion": "부하율이 허용 범위 내이고 구동계 강성·안정성이 저하되지 않음",
    "failure_criterion": "부하율이 허용 범위를 초과하거나 강성·안정성이 저하되면 실패",
    "obligation_refs": [
      {
        "contradiction_id": "TC-c8cf7951",
        "side": "IMPROVE"
      }
    ]
  },
  {
    "metric": "정렬 정밀도(Slip·정렬 오차)",
    "baseline": "미확인",
    "target": "기존 정렬 정밀도 이상 유지",
    "experiment": "준비 동작 도입 후 정지 시 정렬·클램프를 수행하고 글라스 변위·정렬 오차를 측정해 기존 조건과 비교한다.",
    "success_criterion": "정렬 오차가 기존 조건 이하",
    "failure_criterion": "정렬 오차가 기존 조건을 초과하거나 Slip이 발생하면 실패",
    "obligation_refs": [
      {
        "contradiction_id": "TC-097b79ff",
        "side": "PROTECT"
      },
      {
        "contradiction_id": "TC-b5b764b0",
        "side": "PROTECT"
      }
    ]
  }
]
```

</details>

<a id="field-570ce3578c688a06"></a>

<details>
<summary>coherence · 전체 값</summary>

```json
{
  "intervention": "복귀 구간(역회전, 글라스 없음) 동안 정렬 액추에이터를 다음 사이클 초기 위치로 복귀시키고 클램프를 개방 상태로 준비시키는 시퀀스 스텝을 추가한다. 정렬·클램프의 실제 접촉·고정 동작은 로테이션 정지 후에만 수행한다.",
  "target": "정렬·클램프 공정 유닛의 시퀀스 및 서보 제어기 시퀀스",
  "changed_variable": "복귀 구간 중 정렬·클램프 준비 동작 시퀀스(준비 동작의 시간 위치)",
  "mediating_functions": [
    "복귀 구간 무부하 유휴 시간에 준비 동작을 배치해 정지 후 스트로크를 감소시킨다",
    "접촉·고정을 정지 후로 제한해 감속 구간 중첩 금지 제약을 보존한다",
    "정렬 액추에이터 초기 위치 복귀가 다음 정지 시 마무리 스트로크만 남긴다"
  ],
  "outcome": "정지 후 정렬·클램프 직렬 소요 시간이 감소하고 총 takt가 단축된다. 단축량은 정렬·클램프 실측 소요 시간에 의존하며 현재 미측정이다.",
  "operating_scope": "복귀 구간에 유휴 시간이 존재하고, 정지 후 직렬 정렬·클램프 공정이 존재하는 회전 이송 설비. 로테이션 가감속 프로파일은 변경하지 않는다.",
  "contribution": "DIRECT",
  "control_mode": "PASSIVE",
  "control_chain": {},
  "conditions": [
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "복귀 구간 중 정렬·클램프 유닛 동작이 허용된다(미확인)",
      "applicability": "현장에서 복귀 구간 중 정렬·클램프 유닛 구동 허용 여부를 확인한다. 시퀀스 유지 선호(CON-67ea8d4a, soft)와의 정합성을 검토한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "정렬·클램프 준비 동작 시간이 복귀 구간 내에 들어온다(미확인)",
      "applicability": "복귀 구간 소요 시간과 정렬·클램프 준비 동작 소요 시간을 실측해 준비 동작이 복귀 구간 내에 들어오는지 확인한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "복귀 구간 중 정렬·클램프 유닛 동작이 허용될 것(미확인)",
      "applicability": "상동. 현장 확인·시험 방법으로 판정하며 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "정렬·클램프 준비 동작 시간이 복귀 구간 내에 들어올 것(미확인)",
      "applicability": "상동. 실측으로 판정하며 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "두 작용이 양립하기 어렵거나 별도로 수행되며 한 작용의 휴지기에 다른 유익한 작용을 넣을 수 있을 때.",
      "applicability": "복귀 구간(무부하 유휴)에 정렬·클램프 준비 동작을 넣을 수 있는지, 두 작용이 시간적으로 분리 가능한지 현장에서 확인한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "전환 시간·관측 지연 허용 여부 미확인",
      "applicability": "복귀 구간 준비 동작과 정지 후 마무리 사이의 전환 시간, 위치 센서 관측 지연 허용 여부를 현장에서 확인한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "복귀 구간 단축 허용 여부 미확인",
      "applicability": "복귀 구간 시간 단축이 허용되는지 현장에서 확인한다. 이 후보는 복귀 구간 단축을 전제하지 않으나, 준비 동작 배치가 복귀 구간 시간에 영향을 줄 수 있으므로 확인한다. 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "복귀 구간 단축 허용 여부 확인(미확인)",
      "applicability": "상동. 현장 확인 방법으로 판정하며 확인 완료를 주장하지 않는다."
    },
    {
      "source_idea_id": "IDEA-374f5bee",
      "condition": "시퀀스 유지 선호와의 충돌 검토",
      "applicability": "장비 시퀀스(투입>로테이션>배출>원위치 복귀) 유지 선호(CON-67ea8d4a, soft)와 이 후보의 준비 동작 선행이 충돌하는지 검토한다. soft 제약이므로 절대 금지로 취급하지 않는다."
    }
  ],
  "claims": [
    {
      "text": "정렬·클램프 공정 유닛이 로테이션 정지 후 직렬로 소요 시간을 추가한다",
      "status": "OBSERVED",
      "source_cause_id": "N4",
      "evidence_refs": [
        "CON-9f449042",
        "CON-8b834790"
      ]
    },
    {
      "text": "서보 제어기가 감속 구간과 정렬·클램프의 중첩을 차단하여 직렬 시간을 누적시킨다",
      "status": "OBSERVED",
      "source_cause_id": "N5",
      "evidence_refs": [
        "CON-8b834790"
      ]
    },
    {
      "text": "복귀 구간의 무부하 유휴 시간에 정렬·클램프 준비 동작을 선행 배치하면 다음 정지 시 정렬 스트로크가 줄어 직렬 누적 시간이 감소한다",
      "status": "HYPOTHESIS",
      "source_cause_id": "N4",
      "evidence_refs": [
        "CON-fe966295"
      ]
    },
    {
      "text": "복귀 구간 중 정렬·클램프 준비 동작이 복귀 진동과 간섭해 강성·안정성 HARD 제약을 위반할 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "N5",
      "evidence_refs": [
        "CON-88d264f2",
        "CON-f82435ee"
      ]
    },
    {
      "text": "이 후보는 로테이션 가감속 프로파일을 변경하지 않으므로 TC2의 개선측(부하율·강성 유지)을 훼손하지 않는다",
      "status": "DERIVED",
      "source_cause_id": "",
      "evidence_refs": [
        "CON-bae6ac73",
        "CON-88d264f2"
      ]
    }
  ]
}
```

</details>

## 검증과 추적

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `verdicts` | [<br>  {<br>    "verdict": "PASS",<br>    "score": 1.0,<br>    "source": "none"<br>  }<br>] | 표에 전체 값 표시 |
| `error` | "" | 표에 전체 값 표시 |
| `input_metadata` | {<br>  "prompt_id": "P_AX_RECOVERY",<br>  "prompt_hash": "445a1b22d00abc552189c42d27c52d42f77cf42550d479b25aa210f60f840c19"<br>} | 표에 전체 값 표시 |
| `prompt_text_fingerprints` | {<br>  "system": {<br>    "sha256": "4a14475e4d994e97b9e784cf0ad62f9d20b4077aebfe36ac1833d25301d6577b",<br>    "utf8_bytes": 6781<br>  },<br>  "user": {<br>    "sha256": "445a1b22d00abc552189c42d27c52d42f77cf42550d479b25aa210f60f840c19",<br>    "utf8_bytes": 48995<br>  }<br>} | 표에 전체 값 표시 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label, agent_id … | [펼쳐 보기](#field-7d5e14f302a8b531) |

<a id="field-7d5e14f302a8b531"></a>

<details>
<summary>step_metadata · 전체 값</summary>

```json
{
  "step_id": "STP-cea0e0f8",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "seq": 709,
  "stage": "S6_CONCEPT",
  "node": "ax_repair_gap-23e4763bd7081652230dfb23_1",
  "label": "미해결 부분 보완",
  "agent_id": "effects_specialist",
  "prompt_id": "P_AX_RECOVERY",
  "tier": "T2",
  "model": "deepseek-flash",
  "status": "OK",
  "verify_attempts": 1,
  "verdict": "PASS",
  "verdict_score": 1.0,
  "human_intervened": 0,
  "tokens_in": 17094,
  "tokens_out": 4023,
  "cost_usd": 0.0099558,
  "error": "",
  "started_at": "2026-09-29T22:35:17.106315",
  "ended_at": "2026-09-29T22:35:36.661672",
  "scope": "LATEST_RERUN"
}
```

</details>

출처: `steps.input_slice` / `steps.output_json` / `steps.verdicts`. 내부 수정 호출의 중간 원문은 이 Step의 최종 Output과 다릅니다. 모델 호출 횟수·비용·원문 해시는 [호출 원장](../CALLS.md)에서 확인할 수 있습니다.
