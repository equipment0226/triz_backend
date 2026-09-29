# 저장 데이터 · a7dfc04fe68a

원본 값의 정규 JSON SHA-256: `a7dfc04fe68ac0ab951f3f7d92f05ff513cec79da1484d8909038ade086913ba`

```json
[
  {
    "action": "REPAIR_CANDIDATE",
    "ancestor_regression": [
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축 허용 여부(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 인덱서 정지 위치 정밀도 기준(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축이 허용될 것(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 서보 제어기가 다중 프로파일 세트 전환을 지원할 것(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간에 글라스가 없음(확인됨)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축 허용 여부 미확인",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 부하율·진동 측정 필요",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 원위치 복귀 구간 단축 허용 여부 확인 필요(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 단계별 타임스탬프 실측 분해 데이터 필요(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 부하율 로그와 프로파일 파라미터의 동시 기록 필요",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축이 허용되어야 함(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 고속화가 베어링 발열을 누적시키지 않아야 함(온도 미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 종료 시 정지 정밀도가 다음 사이클 투입에 영향을 주지 않아야 함(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      }
    ],
    "attempt": 1,
    "blocker_id": "gap-99452800a5dc788ae3d52b55",
    "candidate_id": "CPT-S6-32d46b742a89c1c2",
    "decision_id": "dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e",
    "derived_candidate_id": "CPT-AX-883412a0b8ef",
    "gap_kinds": [
      "IMPROVEMENT_SIDE_OMITTED",
      "ADVERSE_SIDE_OMITTED"
    ],
    "obligation_ids": [
      "TC-ba15f1e6",
      "TC-c8cf7951"
    ],
    "phase": "before_constraints",
    "preserved_baseline_id": "CPT-S6-32d46b742a89c1c2",
    "proposal": {
      "addresses_contradictions": [
        "TC-ba15f1e6",
        "TC-c8cf7951",
        "PC-8efb2898"
      ],
      "assumptions": [
        "서보 제어기가 2세트 프로파일 전환을 지원한다(미확인)",
        "복귀 구간 가속도 상향이 인덱서 정지 위치 정밀도를 허용 범위 내로 유지한다(미확인)",
        "복귀 구간 단축 허용 여부(미확인)",
        "인덱서 정지 위치 정밀도 기준(미확인)",
        "복귀 구간에 글라스가 없음(확인됨, CON-fe966295)",
        "부하 구간 파라미터를 현행값으로 고정하면 부하율·강성이 현행 수준 이하로 악화되지 않는다(추정)",
        "복귀 구간 고속화가 베어링 발열을 누적시키지 않아야 함(온도 미확인)",
        "복귀 종료 시 정지 정밀도가 다음 사이클 투입에 영향을 주지 않아야 함(미확인)"
      ],
      "changes_to_system": [
        "서보 제어기에 부하/무부하 2세트 프로파일 파라미터 등록 및 시퀀스 상태 기반 전환 로직 추가",
        "복귀 구간 가속 시간·최고 각속도 상향 설정값 적용",
        "부하 구간 파라미터를 현행값 하한으로 고정하는 클램프 설정",
        "복귀 구간 부하율·진동·정지 위치 오차 로깅 채널 추가"
      ],
      "coherence": {
        "changed_variable": "부하 구간·무부하 구간별 가속 시간 및 최고 각속도",
        "claims": [
          {
            "evidence_refs": [
              "CON-fe966295"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "복귀 구간은 글라스가 없어 회전 관성모멘트가 감소하므로 동일 토크로 더 높은 각가속도를 얻을 수 있다"
          },
          {
            "evidence_refs": [
              "CON-fe966295",
              "CON-f3ea19b8"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "복귀 구간 가속도 상향은 부하 구간보다 부하율 상승 폭이 작다"
          },
          {
            "evidence_refs": [
              "CON-bae6ac73",
              "CON-88d264f2",
              "CON-f82435ee"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "부하 구간 파라미터를 현행값으로 고정하면 부하율·강성·안정성이 현행 수준 이하로 악화되지 않는다"
          },
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "복귀 구간 단축분이 부하 구간 고정에 따른 takt 손실을 상회해야 50초 이하 목표에 기여한다"
          },
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "N1",
            "status": "OBSERVED",
            "text": "패턴 글라스 인라인 설비의 takt time이 53초로 목표 50초 이하를 초과하여 라인 LOB 향상 목표를 달성하지 못하고 생산 손실이 발생한다"
          },
          {
            "evidence_refs": [
              "CON-9f449042",
              "CON-8b834790"
            ],
            "source_cause_id": "N4",
            "status": "OBSERVED",
            "text": "정렬·클램프 공정 유닛이 로테이션 정지 후 직렬로 소요 시간을 추가한다"
          },
          {
            "evidence_refs": [
              "CON-8b834790"
            ],
            "source_cause_id": "N5",
            "status": "OBSERVED",
            "text": "서보 제어기가 감속 구간과 정렬·클램프의 중첩을 차단하여 직렬 시간을 누적시킨다"
          }
        ],
        "conditions": [
          {
            "applicability": "CON-f1a96104로 확인됨. 서보 제어기가 2세트 프로파일 저장·전환을 지원하는지는 미확인 — 제어기 사양서 및 파라미터 세트 수 확인 필요.",
            "condition": "서보 제어 가감속 프로파일 방식이다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-fe966295로 확인됨. 복귀 구간에 글라스가 없어 관성모멘트가 감소한다는 전제의 근거. 복귀 구간 실측 시간은 미확인 — 단계별 타임스탬프 분해로 확인 필요.",
            "condition": "원위치 복귀는 역회전 방식이며 복귀 시 글라스가 없다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-a25b3ab7. 현장 제어기 파라미터 덤프로 현행값 확인 필요. 확인 전에는 상향 폭을 정량화하지 않는다.",
            "condition": "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)는 미확인이다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-03a2c34e. 정격 토크 확인 및 부하율 로그로 부하 구간 고정 시 여유 확인 필요. soft로 부하율 60% 수준(CON-f3ea19b8)이나 정확 수치 미확인.",
            "condition": "모터·인덱서 정격 토크와 현재 부하율은 미확인이다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-f512b60e. 복귀 구간 상향 시 가진 주파수가 고유진동수에 접근하는지 진동 스펙트럼 측정으로 확인 필요.",
            "condition": "회전축·베어링·클램프 계면 고유진동수는 미확인이다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-0255b86a. HARD 제약(CON-88d264f2, CON-f82435ee) 위반 판정 기준값 확인 필요. 기준값 없이는 저하 판정 불가.",
            "condition": "로테이션 구동계 전체 강성·하드웨어 안정성의 정량 허용 기준값은 미확인이다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-489f9a78(추정). 복귀 구간 고속화 연속 운전 시 베어링 온도 추이 측정으로 확인 필요. 온도 측정값 미확인.",
            "condition": "고속화 시 베어링·접촉면 발열이 증가할 수 있다",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-8b834790. 이 후보는 정렬·클램프 중첩을 하지 않으므로 제약과 충돌하지 않음. 정렬·클램프 소요 시간은 미확인(CON-9f449042) — 실측 분해 필요.",
            "condition": "정렬·클램프 공정을 로테이션 감속 구간과 중첩(병렬화)할 수 없다",
            "source_idea_id": "IDEA-303c6e1e"
          }
        ],
        "contribution": "DIRECT",
        "control_chain": {
          "actuator": "서보 모터·인덱서 구동(가속 시간·최고 각속도 파라미터 적용)",
          "decision": "서보 제어기의 프로파일 세트 선택 로직(부하 구간=현행 고정, 무부하 구간=상향 세트)",
          "estimator": "현재 시퀀스 단계 판정 로직(부하/무부하 구간 분류)",
          "sensor": "시퀀스 상태 신호(글라스 유무) — 기존 시퀀스 제어 신호 활용(미확인)",
          "target": "로테이션 구동계 가감속 프로파일"
        },
        "control_mode": "ACTIVE",
        "intervention": "서보 제어기에 부하/무부하 2세트 가감속 프로파일을 등록하고 시퀀스 상태 신호로 전환하며, 부하 구간 파라미터는 현행값을 하한으로 고정하고 복귀 구간만 가속 시간 단축·최고 각속도 상향한다.",
        "mediating_functions": [
          "시퀀스 상태 신호(글라스 유무)가 프로파일 세트 선택을 결정한다",
          "무부하 구간에서 회전 관성모멘트 감소가 동일 토크 대비 각가속도를 증가시킨다",
          "부하 구간 파라미터 고정이 부하율·강성·안정성 HARD 제약을 현행 수준으로 보존한다"
        ],
        "operating_scope": "글라스 탑재 로테이션 구간과 무부하 원위치 복귀(역회전) 구간을 포함한 1 사이클 전체. 정렬·클램프 직렬 구간은 변경 대상이 아니며 감속 구간과의 중첩은 하지 않는다(CON-8b834790).",
        "outcome": "복귀 구간 단축분만큼 takt이 감소하고, 부하 구간 부하율·강성·안정성은 현행 수준으로 유지된다. 목표 50초 이하 달성 여부는 복귀 구간 실측 시간과 단축 허용 폭 확인 후 판정(미측정).",
        "target": "180도 로테이션 구동계의 서보 가감속 프로파일(부하 구간·무부하 복귀 구간)"
      },
      "open_risks": [
        "복귀 구간 고속화가 베어링 발열을 누적시켜 다음 사이클 정착 시간에 영향을 줄 수 있다(온도 미확인)",
        "복귀 종료 정지 위치 오차가 다음 투입에 영향을 줄 수 있다(미확인)",
        "복귀 구간 단축분이 3초 목표에 미달할 경우 부하 구간 조정 없이는 50초 이하 달성 불가(복귀 구간 실측 시간 미확인)",
        "부하 구간 파라미터 고정으로 인한 takt 손실이 복귀 구간 단축분을 상회할 가능성(단계별 타임스탬프 미확인)"
      ],
      "provided_functions": [
        "부하 구간과 무부하 구간에 서로 다른 가감속 프로파일을 적용하는 기능",
        "시퀀스 상태 신호에 따라 프로파일 세트를 전환하는 기능"
      ],
      "required_functions": [
        "글라스 유무를 판별해 프로파일을 선택하는 기능",
        "복귀 구간 정지 위치 오차를 허용 범위 내로 유지하는 기능",
        "부하 구간 부하율·강성을 현행 수준 이상으로 유지하는 기능"
      ],
      "required_resources": [
        "기존: 서보 제어기의 다중 프로파일 세트 저장·전환 기능(미확인 — 현장 확인 필요)",
        "기존: 시퀀스 상태 신호(글라스 유무)",
        "기존: 서보 모터·인덱서 부하율 로그",
        "신규: 복귀 구간 정지 위치 오차 측정 수단(미확인 — 기존 인덱서 위치 피드백으로 대체 가능성 확인 필요)"
      ],
      "resolution_argument": "가속도 파라미터 하나가 takt와 부하율을 동시에 지배하는 결합을, 시간축을 '글라스 유무'로 분할해 끊는다. 부하 구간은 낮은 가속도로 부하율·강성을 보존하고, 무부하 구간은 높은 가속도로 takt를 단축한다. 두 요구가 서로 다른 시간 구간에 배타적으로 배정되므로 절충이 아니다. TC-c8cf7951(부하율·강성 보호를 위해 가속도를 하향 → takt 초과)의 개선측(부하율·강성 유지)은 부하 구간 파라미터를 현행값 이하로 내리지 않는 조건으로, 악화 방지측(takt 50초 이하 유지)은 복귀 구간 단축분이 부하 구간 고정에 따른 손실을 상회하는 조건으로 각각 검증한다.",
      "subproblem": "",
      "title": "부하별 가변 가감속 프로파일 — TC-c8cf7951 양측 검증계획 보강 및 자원 표시 정정",
      "validation_plan": [
        {
          "baseline": "현재 복귀 구간 시간(미확인)",
          "experiment": "복귀 구간 가속도만 단계 상향하며 복귀 시간·정지 위치 오차·부하율·진동을 동시 측정",
          "failure_criterion": "정지 위치 오차가 허용 기준 초과 또는 부하율 허용 범위 초과",
          "metric": "복귀 구간 시간 및 인덱서 정지 위치 오차",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "복귀 구간 시간이 유의하게 감소하고 정지 위치 오차가 허용 기준 내",
          "target": "복귀 구간 시간 단축 및 정지 위치 오차 허용 기준 내"
        },
        {
          "baseline": "현재 운전 온도(미확인)",
          "experiment": "복귀 구간 고속화 연속 운전 시 베어링 온도 추이 측정",
          "failure_criterion": "온도가 허용 기준 초과 또는 다음 사이클 정착 시간 증가",
          "metric": "복귀 구간 베어링 온도",
          "obligation_refs": [
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "온도가 허용 기준 내 유지 및 다음 사이클 정착 시간 불변",
          "target": "허용 온도 기준 내(기준값 미확인)"
        },
        {
          "baseline": "현행 부하 구간 파라미터에서의 부하율(soft 60% 수준)·진동·강성 지표(미확인)",
          "experiment": "부하 구간 파라미터를 현행값으로 고정한 채 복귀 구간만 상향 운전하고, 부하 구간 부하율·진동·강성 지표를 현행 기준 대비 측정",
          "failure_criterion": "부하 구간 부하율 허용 범위 초과 또는 강성·안정성 지표 저하",
          "metric": "부하 구간 부하율·진동·강성 지표",
          "obligation_refs": [
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "IMPROVE"
            }
          ],
          "success_criterion": "부하 구간 부하율·진동·강성 지표가 현행 대비 악화 없음(허용 기준 내)",
          "target": "부하 구간 파라미터 현행값 고정 시 부하율·진동·강성 지표가 현행 수준 이하로 악화되지 않음"
        },
        {
          "baseline": "현재 takt 53초(CON-87d3c928, soft)",
          "experiment": "부하 구간 파라미터 현행 고정 + 복귀 구간 상향 조건에서 단계별 타임스탬프 분해로 총 takt 측정",
          "failure_criterion": "총 takt time 50초 초과 — 이 경우 복귀 구간 단축만으로는 목표 미달로 판정하고 부하 구간 조정 또는 타 구간 단축 필요",
          "metric": "총 takt time",
          "obligation_refs": [
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "총 takt time 50초 이하 달성",
          "target": "takt time 50초 이하(CON-2e5d6859, HARD)"
        }
      ],
      "working_principle": "서보 제어기에 부하 구간(글라스 탑재)과 무부하 구간(원위치 복귀, 역회전) 두 개의 가감속 프로파일 세트를 저장하고, 시퀀스 상태 신호(글라스 유무)로 전환한다. 복귀 구간은 글라스가 없어 회전 관성모멘트가 감소하므로 동일 토크로 더 높은 각가속도를 얻을 수 있고, 이 구간의 가속도 상향은 부하율 상승 폭이 부하 구간보다 작다. 부하 구간은 부하율·진동 한계 내에서 단계적으로만 상향해 HARD 제약(부하율·강성·안정성)을 유지한다. 이 후보의 takt 단축분은 복귀 구간 단축분에 한정되며, 부하 구간 가속도 하향으로 인한 takt 증가분과 상쇄되지 않도록 부하 구간 파라미터는 현행값을 하한으로 고정한다."
    },
    "status": "UNRESOLVED"
  },
  {
    "action": "REPAIR_CANDIDATE",
    "ancestor_regression": [
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축이 허용될 것(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 서보 제어기가 다중 프로파일 세트 전환을 지원할 것(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축 허용 여부 미확인",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 원위치 복귀 구간 단축 허용 여부 확인 필요(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      },
      {
        "description": "원리 적용 조건의 후보 내 성립 경로 확인 필요: 복귀 구간 단축이 허용되어야 함(미확인)",
        "kind": "CONDITION_SCOPE_UNCONFIRMED",
        "obligation_ids": [
          "TC-ba15f1e6",
          "TC-c8cf7951"
        ]
      }
    ],
    "attempt": 2,
    "blocker_id": "gap-99452800a5dc788ae3d52b55",
    "candidate_id": "CPT-S6-32d46b742a89c1c2",
    "decision_id": "dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287",
    "derived_candidate_id": "CPT-AX-99cdf59f74f3",
    "gap_kinds": [
      "IMPROVEMENT_SIDE_OMITTED",
      "ADVERSE_SIDE_OMITTED"
    ],
    "obligation_ids": [
      "TC-ba15f1e6",
      "TC-c8cf7951"
    ],
    "phase": "before_constraints",
    "preserved_baseline_id": "CPT-S6-32d46b742a89c1c2",
    "proposal": {
      "addresses_contradictions": [
        "TC-ba15f1e6",
        "TC-c8cf7951",
        "PC-8efb2898"
      ],
      "assumptions": [
        "서보 제어기가 2세트 프로파일 전환을 지원한다(미확인)",
        "복귀 구간 가속도 상향이 인덱서 정지 위치 정밀도를 허용 범위 내로 유지한다(미확인)",
        "복귀 구간 단축 허용 여부(미확인)",
        "인덱서 정지 위치 정밀도 기준(미확인)",
        "복귀 구간에 글라스가 없음(확인됨)",
        "복귀 구간 부하율·진동 측정 필요",
        "단계별 타임스탬프 실측 분해 데이터 필요(미확인)",
        "부하율 로그와 프로파일 파라미터의 동시 기록 필요",
        "복귀 구간 고속화가 베어링 발열을 누적시키지 않아야 함(온도 미확인)",
        "복귀 종료 시 정지 정밀도가 다음 사이클 투입에 영향을 주지 않아야 함(미확인)",
        "부하 구간 가속도 하향 시 takt 초과 판정 기준이 50초(HARD)로 설정되어 있다(확인됨)"
      ],
      "changes_to_system": [
        "서보 제어기에 부하/무부하 2세트 프로파일 파라미터 등록 및 시퀀스 상태 기반 전환 로직 추가",
        "복귀 구간 가속 시간·최고 각속도 상향 설정값 적용",
        "복귀 구간 부하율·진동·정지 위치 오차 로깅 채널 추가",
        "부하 구간 가속도 하향 시 takt 초과 여부를 판정하는 개선측 검증 항목 추가",
        "부하 구간 가속도 하향 시 부하율·강성·안정성 유지 여부를 판정하는 악화방지측 검증 항목 추가"
      ],
      "coherence": {
        "changed_variable": "부하 구간·무부하 구간별 가속 시간 및 최고 각속도",
        "claims": [
          {
            "evidence_refs": [
              "CON-fe966295"
            ],
            "source_cause_id": "N5",
            "status": "HYPOTHESIS",
            "text": "복귀 구간은 글라스가 없어 회전 관성모멘트가 감소하므로 동일 토크로 더 높은 각가속도를 얻을 수 있다"
          },
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "부하 구간 가속도 하향 시 takt time이 50초를 초과할 수 있다"
          },
          {
            "evidence_refs": [
              "CON-bae6ac73",
              "CON-88d264f2",
              "CON-f82435ee"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "부하 구간 가속도 하향 시 부하율·강성·안정성이 유지된다"
          },
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "N1",
            "status": "OBSERVED",
            "text": "패턴 글라스 인라인 설비의 takt time이 53초로 목표 50초 이하를 초과하여 라인 LOB 향상 목표를 달성하지 못하고 생산 손실이 발생한다"
          },
          {
            "evidence_refs": [
              "CON-9f449042",
              "CON-8b834790"
            ],
            "source_cause_id": "N4",
            "status": "OBSERVED",
            "text": "정렬·클램프 공정 유닛이 로테이션 정지 후 직렬로 소요 시간을 추가한다"
          },
          {
            "evidence_refs": [
              "CON-8b834790"
            ],
            "source_cause_id": "N5",
            "status": "OBSERVED",
            "text": "서보 제어기가 감속 구간과 정렬·클램프의 중첩을 차단하여 직렬 시간을 누적시킨다"
          }
        ],
        "conditions": [
          {
            "applicability": "서보 제어기 사양서 및 파라미터 세트 저장·전환 기능을 현장에서 확인한다. 확인 완료를 주장하지 않는다.",
            "condition": "서보 제어기가 2세트 프로파일 전환을 지원한다(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "복귀 구간 가속도 단계 상향 시험에서 정지 위치 오차를 측정하여 허용 기준 내 여부를 판정한다. 확인 완료를 주장하지 않는다.",
            "condition": "복귀 구간 가속도 상향이 인덱서 정지 위치 정밀도를 허용 범위 내로 유지한다(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "현장 운전 조건에서 복귀 구간 단축 시 다음 사이클 투입 정밀도 영향을 측정하여 허용 여부를 판정한다. 확인 완료를 주장하지 않는다.",
            "condition": "복귀 구간 단축 허용 여부(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "설비 사양서 및 현장 측정으로 정지 위치 정밀도 허용 기준을 확인한다. 확인 완료를 주장하지 않는다.",
            "condition": "인덱서 정지 위치 정밀도 기준(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "CON-fe966295로 확인된 사실. 복귀 구간 무부하 조건의 근거로 사용한다.",
            "condition": "복귀 구간에 글라스가 없음(확인됨)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "복귀 구간 고속화 시험에서 부하율 로그와 진동을 동시 측정한다. 확인 완료를 주장하지 않는다.",
            "condition": "복귀 구간 부하율·진동 측정 필요",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기 구간별 타임스탬프를 실측 분해한다. 확인 완료를 주장하지 않는다.",
            "condition": "단계별 타임스탬프 실측 분해 데이터 필요(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "부하율 로그와 프로파일 파라미터를 동시 기록하여 상관을 분석한다. 확인 완료를 주장하지 않는다.",
            "condition": "부하율 로그와 프로파일 파라미터의 동시 기록 필요",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "복귀 구간 고속화 연속 운전 시 베어링 온도 추이를 측정한다. 확인 완료를 주장하지 않는다.",
            "condition": "복귀 구간 고속화가 베어링 발열을 누적시키지 않아야 함(온도 미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          },
          {
            "applicability": "복귀 종료 정지 위치 오차와 다음 사이클 투입 정밀도의 상관을 측정한다. 확인 완료를 주장하지 않는다.",
            "condition": "복귀 종료 시 정지 정밀도가 다음 사이클 투입에 영향을 주지 않아야 함(미확인)",
            "source_idea_id": "IDEA-303c6e1e"
          }
        ],
        "contribution": "DIRECT",
        "control_chain": {
          "actuator": "서보 모터·인덱서 구동계",
          "decision": "부하/무부하 프로파일 세트 선택 및 부하 구간 가속도 하향 폭 결정",
          "estimator": "단계별 타임스탬프와 부하율 로그 결합 분석으로 구간별 병목 및 부하율 추정",
          "sensor": "시퀀스 상태 신호(글라스 유무), 서보 모터·인덱서 부하율 로그, 진동·온도 센서(신규)",
          "target": "가감속 프로파일 파라미터 세트"
        },
        "control_mode": "ACTIVE",
        "intervention": "서보 제어기에 부하/무부하 2세트 가감속 프로파일을 등록하고 시퀀스 상태 신호로 전환하며, 부하 구간 가속도 하향 시 takt 초과 여부(개선측)와 부하율·강성·안정성 유지 여부(악화방지측)를 각각 독립 검증 항목으로 분리한다.",
        "mediating_functions": [
          "시퀀스 상태 신호(글라스 유무)가 프로파일 세트 선택을 결정한다",
          "무부하 구간에서 회전 관성모멘트 감소가 동일 토크 대비 각가속도 상승을 매개한다",
          "부하 구간 가속도 하향이 부하율·강성·안정성 유지로 매개된다",
          "부하 구간 가속도 하향 시 takt 초과 여부 판정이 개선측 검증으로 매개된다"
        ],
        "operating_scope": "글라스 유무로 구분되는 로테이션 구간 및 원위치 복귀 구간. 부하 구간 가속도는 부하율·진동 한계 내에서만 상향. 복귀 구간 단축 허용 여부 확인 전까지는 검증 단계에 한정.",
        "outcome": "복귀 구간 단축분만큼 takt 감소. 목표 50초 이하 달성 여부는 복귀 구간 실측 시간과 단축 허용 폭 확인 후 판정(미측정). TC-c8cf7951 양측 검증 경로가 닫히고 실패 조건이 확정된다.",
        "target": "서보 제어기의 가감속 프로파일 파라미터 세트 및 시퀀스 상태 기반 전환 로직"
      },
      "open_risks": [
        "복귀 구간 고속화가 베어링 발열을 누적시켜 다음 사이클 정착 시간에 영향을 줄 수 있다(온도 미확인)",
        "복귀 종료 정지 위치 오차가 다음 투입에 영향을 줄 수 있다(미확인)",
        "부하 구간 가속도 하향으로 takt가 50초를 초과할 경우 대체 단축 수단이 확보되지 않을 수 있다(미확인)",
        "복귀 구간 단축 허용 여부가 확인되지 않아 실패 조건이 확정되지 않는다(미확인)"
      ],
      "provided_functions": [
        "부하 구간과 무부하 구간에 서로 다른 가감속 프로파일을 적용하는 기능",
        "시퀀스 상태 신호로 프로파일 세트를 전환하는 기능",
        "복귀 구간 부하율·진동·정지 위치 오차를 로깅하는 기능"
      ],
      "required_functions": [
        "부하 구간에서 부하율·강성·안정성을 허용 범위 내로 유지하는 기능",
        "무부하 복귀 구간에서 takt를 단축하는 기능",
        "부하 구간 가속도 하향 시 takt 초과 여부를 판정하는 기능",
        "부하 구간 가속도 하향 시 부하율·강성·안정성 유지 여부를 판정하는 기능"
      ],
      "required_resources": [
        "서보 제어기의 다중 프로파일 세트 저장·전환 기능(미확인)",
        "시퀀스 상태 신호(글라스 유무)",
        "서보 모터·인덱서 부하율 로그",
        "신규: 복귀 구간 정지 위치 오차 측정 수단(미확인)",
        "신규: 부하 구간 진동·온도 동시 로깅 채널(미확인)"
      ],
      "resolution_argument": "가속도 파라미터 하나가 takt와 부하율을 동시에 지배하는 결합을, 시간축을 '글라스 유무'로 분할해 끊는다. 부하 구간은 낮은 가속도로 부하율·강성을 보존하고, 무부하 구간은 높은 가속도로 takt를 단축한다. 두 요구가 서로 다른 시간 구간에 배타적으로 배정되므로 절충이 아니다. TC-c8cf7951의 개선측(부하율·강성 유지)과 악화방지측(takt 초과 회피)은 서로 다른 시간 구간에 배정되므로 동일 파라미터 상에서 충돌하지 않는다. 단, 복귀 구간 단축 허용 여부와 정지 위치 정밀도 기준이 미확인이므로, 이 두 항목을 실패 조건 확정을 위한 검증 항목으로 명시한다.",
      "subproblem": "TC-c8cf7951의 개선측(부하율·강성 보호를 위해 가속도를 하향)과 악화방지측(takt 초과)이 각각 검증계획에 연결되지 않아 모순 양측의 검증 경로가 닫히지 않았고, 복귀 구간 단축 허용 여부와 정지 위치 정밀도 기준이 미확인인 채 성립 조건으로만 남아 실패 조건이 확정되지 않았다.",
      "title": "부하별 가변 가감속 프로파일 — TC-c8cf7951 양측 검증계획 보강 및 실패조건 확정",
      "validation_plan": [
        {
          "baseline": "현재 복귀 구간 시간(미확인)",
          "experiment": "복귀 구간 가속도만 단계 상향하며 복귀 시간·정지 위치 오차·부하율·진동을 동시 측정",
          "failure_criterion": "정지 위치 오차가 허용 기준 초과 또는 부하율 허용 범위 초과",
          "metric": "복귀 구간 시간 및 인덱서 정지 위치 오차",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "복귀 구간 시간이 단축되고 정지 위치 오차가 허용 기준 내이며 부하율이 허용 범위 내",
          "target": "복귀 구간 시간 단축 및 정지 위치 오차 허용 기준 내"
        },
        {
          "baseline": "현재 운전 온도(미확인)",
          "experiment": "복귀 구간 고속화 연속 운전 시 베어링 온도 추이 측정",
          "failure_criterion": "온도가 허용 기준 초과 또는 다음 사이클 정착 시간 증가",
          "metric": "복귀 구간 베어링 온도",
          "obligation_refs": [
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "온도가 허용 기준 내이고 다음 사이클 정착 시간이 증가하지 않음",
          "target": "허용 온도 기준 내(기준값 미확인)"
        },
        {
          "baseline": "현재 takt time 53초(soft, CON-87d3c928)",
          "experiment": "부하 구간 가속도를 단계 하향하며 단계별 타임스탬프로 takt를 측정하고, 50초 초과 여부를 판정",
          "failure_criterion": "takt time이 50초를 초과",
          "metric": "부하 구간 가속도 하향 시 takt time",
          "obligation_refs": [
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "IMPROVE"
            }
          ],
          "success_criterion": "부하 구간 가속도 하향 상태에서도 takt time이 50초 이하를 유지",
          "target": "takt time 50초 이하(HARD, CON-2e5d6859)"
        },
        {
          "baseline": "현재 부하율 60% 수준(soft, CON-f3ea19b8), 강성·안정성 정량 기준 미확인",
          "experiment": "부하 구간 가속도 하향 운전 시 부하율 로그·진동 스펙트럼·변형을 측정하여 하향 전후 비교",
          "failure_criterion": "부하율 허용 범위 초과 또는 진동·변형이 하향 전 대비 악화",
          "metric": "부하 구간 부하율·강성·하드웨어 안정성",
          "obligation_refs": [
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "부하율이 허용 범위 내이고 진동·변형이 하향 전 대비 악화되지 않음",
          "target": "부하율 허용 범위 내, 강성·안정성 저하 없음(정량 기준 미확인)"
        },
        {
          "baseline": "복귀 구간 단축 허용 여부 미확인, 정지 위치 정밀도 기준 미확인",
          "experiment": "현장 운전 조건에서 복귀 구간 단축 시 다음 사이클 투입 정밀도 영향을 측정하여 허용 기준을 설정",
          "failure_criterion": "복귀 구간 단축이 불가하거나 정지 위치 정밀도 기준이 확정되지 않음",
          "metric": "복귀 구간 단축 허용 여부 및 정지 위치 정밀도 기준",
          "obligation_refs": [
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "복귀 구간 단축이 허용되고 정지 위치 정밀도 허용 기준이 확정됨",
          "target": "복귀 구간 단축 허용 여부와 정지 위치 정밀도 허용 기준 확정"
        }
      ],
      "working_principle": "서보 제어기에 부하 구간(글라스 탑재)과 무부하 구간(원위치 복귀, 역회전) 두 개의 가감속 프로파일 세트를 저장하고, 시퀀스 상태 신호(글라스 유무)로 전환한다. 무부하 복귀 구간은 글라스 질량만큼 회전 관성모멘트가 감소하므로 동일 토크에서 더 높은 각가속도를 얻을 수 있고, 이 구간의 가속도 상향은 부하율 상승 폭이 부하 구간보다 작다. 부하 구간은 부하율·진동 한계 내에서 단계적으로만 상향한다. TC-c8cf7951(부하율·강성 보호를 위해 가속도를 하향 → takt 초과)의 양측을 닫기 위해, (a) 부하 구간 가속도 하향 시 takt가 50초를 초과하는지 확인하는 개선측 시험과 (b) 하향으로 확보한 부하율·강성·안정성 여유가 실제로 유지되는지 확인하는 악화방지측 시험을 각각 독립 검증 항목으로 분리한다."
    },
    "status": "UNRESOLVED"
  },
  {
    "action": "REPAIR_CANDIDATE",
    "ancestor_regression": [],
    "attempt": 1,
    "blocker_id": "gap-ee8407b02217eddd77e4bfbd",
    "candidate_id": "CPT-S6-099405e4edc0a658",
    "decision_id": "dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943",
    "derived_candidate_id": "CPT-AX-dfc90064be15",
    "gap_kinds": [
      "QUALITY_REVIEW"
    ],
    "obligation_ids": [
      "TC-c8cf7951"
    ],
    "phase": "before_constraints",
    "preserved_baseline_id": "CPT-S6-099405e4edc0a658",
    "proposal": {
      "addresses_contradictions": [
        "TC-ba15f1e6",
        "TC-c8cf7951",
        "TC-4f7ba034",
        "TC-9a13d136",
        "TC-b5b764b0",
        "TC-097b79ff"
      ],
      "assumptions": [
        "추정: 부하율이 실제 60% 수준이다(첨부 답변, 정확 수치 미확인)",
        "추정: 가감속 프로파일이 보수적으로 설정되어 변경 여지가 있다(첨부 답변)",
        "추정: 부하율·진동·온도 상한 수치가 미확인이라 상대 증가율 잠정 게이트(부하율 +10%p, 진동 +20%, 온도 +5K)를 임시로 사용한다 — 실측 기준값 확보 시 대체",
        "추정: 글라스 관성모멘트 실측값 미확인",
        "추정: 정렬·클램프 소요 시간 미확인",
        "추정: 서보 드라이브가 회생 제동을 지원할 것(미확인)",
        "추정: 회생 전력 처리 용량이 충분할 것(미확인)"
      ],
      "changes_to_system": [
        "가속 시간·최고 각속도·정착 시간을 '판정 지표 여유율 임계'로 정의한 단계 상향 절차 도입",
        "각 단계에서 부하율·진동 진폭·온도·정착 시간 동시 측정 및 게이트 판정",
        "고유진동수 미확인 기간에는 진동 스펙트럼 감시 하 제한 상향, 이격비 확인 시 상향 폭 확대",
        "감속 구간 회생 제동 토크 활용은 기능·전력 용량 확인 시 적용하는 조건부 항목으로 분리",
        "상한 수치 미확인 지표에 대해 현재 운전점 대비 상대 증가율 잠정 게이트 병기(임시값 명시)"
      ],
      "coherence": {
        "changed_variable": "가속 시간, 최고 각속도, 정착 시간, 감속 구간 제동 토크",
        "claims": [
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "N1",
            "status": "OBSERVED",
            "text": "패턴 글라스 인라인 설비의 takt time이 53초로 목표 50초 이하를 초과하여 라인 LOB 향상 목표를 달성하지 못하고 생산 손실이 발생한다"
          },
          {
            "evidence_refs": [
              "CON-9f449042",
              "CON-8b834790"
            ],
            "source_cause_id": "N4",
            "status": "OBSERVED",
            "text": "정렬·클램프 공정 유닛이 로테이션 정지 후 직렬로 소요 시간을 추가한다"
          },
          {
            "evidence_refs": [
              "CON-8b834790"
            ],
            "source_cause_id": "N5",
            "status": "OBSERVED",
            "text": "서보 제어기가 감속 구간과 정렬·클램프의 중첩을 차단하여 직렬 시간을 누적시킨다"
          },
          {
            "evidence_refs": [
              "CON-f1a96104",
              "CON-6f1aa3c0"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "가속 시간·최고 각속도·정착 시간을 판정 지표 여유율 임계로 단계 상향하면 takt이 단축된다"
          },
          {
            "evidence_refs": [
              "CON-f512b60e",
              "CON-88d264f2",
              "CON-f82435ee"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "가속도 상향 시 가진 주파수가 계면 고유진동수에 접근해 공진으로 강성·안정성 HARD 위반이 발생할 수 있다"
          },
          {
            "evidence_refs": [
              "CON-489f9a78"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "고속화로 베어링·접촉면 발열이 증가해 열변형으로 정착 시간·정렬 정밀도가 저하될 수 있다"
          },
          {
            "evidence_refs": [
              "CON-bae6ac73",
              "CON-03a2c34e"
            ],
            "source_cause_id": "",
            "status": "USER_REPORTED",
            "text": "부하율 허용 범위 수치가 미확인이라 HARD 제약 위반 판정 기준이 부재하다"
          }
        ],
        "conditions": [
          {
            "applicability": "서보 드라이브 부하율 로그를 실측하여 60% 수준 여부와 정확 수치를 확인한다. 확인 전에는 상대 증가율 잠정 게이트로만 운전하고 확인 완료를 주장하지 않는다.",
            "condition": "부하율이 실제 60% 수준이다(첨부 답변, 정확 수치 미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "서보 제어기 프로파일 파라미터 설정 권한 보유 주체와 변경 가능 범위를 현장에서 확인한다. 권한 미확인 시 신규 자원으로 표시한다.",
            "condition": "프로파일 변경 여지가 있다(첨부 답변)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "부하율 로그 실측으로 확인한다. 미확인 상태에서는 절대 게이트로 사용하지 않는다.",
            "condition": "부하율 60% 여유 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "파라미터 설정 권한·범위를 현장 확인한다.",
            "condition": "프로파일 변경 여지 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "진동·변형·온도 허용 기준값 존재 여부와 수치를 확인한다. 미확인 시 상대 증가율 잠정 게이트를 임시 사용하고 임시값임을 명시한다.",
            "condition": "강성·안정성 정량 허용 기준값 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "본 후보는 회전 동역학·동적 제어 범위의 파라미터 상향으로, 장 분포·공간 구조 재설계를 요구하지 않는다. 해당 조건은 본 후보에 적용되지 않음(적용 제외).",
            "condition": "모델의 효율 개선에 특정 장 분포, 물질의 공간 구조 또는 에너지 집중·비작용 구역이 필요할 때.",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "부하율 로그 실측으로 확인한다.",
            "condition": "부하율이 실제 60% 수준으로 확인될 때",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "기준값 미확인이므로 진동 스펙트럼 감시 하 제한 상향으로 운전하고, 기준값 확인 시 절대 게이트로 전환한다.",
            "condition": "가속도 상향 시 진동·온도가 강성·안정성 허용 기준 내일 때(기준값 미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "모터·인덱서 정격 토크와 부하율 허용 범위 수치를 확인한다. 미확인 상태에서는 절대 게이트로 사용하지 않는다.",
            "condition": "부하율 허용 범위 수치 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "회전축·베이링·클램프 계면 고유진동수를 측정한다. 미확인 기간에는 제한 상향만 허용한다.",
            "condition": "계면 고유진동수 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "글라스·스테이지 관성모멘트를 실측하여 가속 시간 단축 한계를 산정한다.",
            "condition": "관성모멘트 실측값 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "드라이브 사양·회생 저항 구성을 확인한다. 미지원 시 감속 구간 단축분은 확보 불가로 처리한다.",
            "condition": "서보 드라이브가 회생 제동을 지원할 것(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "회생 전력량과 저항·회수 용량을 확인한다. 부족 시 감속 구간 단축분 제한.",
            "condition": "회생 전력 처리 용량이 충분할 것(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          }
        ],
        "contribution": "DIRECT",
        "control_chain": {
          "actuator": "서보 제어기 프로파일 파라미터 설정(가속 시간·최고 각속도·정착 시간), 감속 구간 회생 제동 토크 설정(기능 확인 시)",
          "decision": "여유율 임계(절대 상한 확인 시 절대값, 미확인 시 상대 증가율 잠정값) 초과 직전 조합을 운전점으로 채택, 초과 시 즉시 하향",
          "estimator": "각 지표의 상한 대비 사용률(여유율) 산정 및 가진 주파수-고유진동수 이격비 추정",
          "sensor": "부하율 로그(서보 드라이브), 진동 센서(회전축·베어링·클램프 계면), 온도 센서(베어링·접촉면), 단계별 타임스탬프 계측",
          "target": "가속·감속 구간 시간 및 takt time"
        },
        "control_mode": "ACTIVE",
        "intervention": "가속 시간·최고 각속도·정착 시간을 '판정 지표 여유율 임계'로 정의한 단계 상향 절차로 변경하고, 각 단계에서 부하율·진동·온도·정착 시간을 동시 측정해 임계 초과 직전 조합을 운전점으로 채택한다. 고유진동수 미확인 기간에는 진동 스펙트럼 감시 하 제한 상향, 이격비 확인 시 상향 폭 확대. 회생 제동은 기능·용량 확인 시 조건부 적용.",
        "mediating_functions": [
          "프로파일 파라미터 상향 → 가속·감속 구간 시간 감소 → takt 감소",
          "부하율·진동·온도·정착 시간 동시 계측 → 여유율 산정 → 상향 폭 결정",
          "진동 스펙트럼 감시 → 가진 주파수-고유진동수 이격 판정 → 공진 회피",
          "회생 제동 토크 → 감속 시간 단축 → 정착 시간 감소"
        ],
        "operating_scope": "로테이션 가속·감속·정지 구간. 정렬·클램프 직렬 구간 및 감속 구간 중첩은 대상 외(중첩 불가 제약 유지). 고유진동수·상한 수치 미확인 기간에는 제한 상향 범위 내에서만 운전.",
        "outcome": "판정 지표 여유가 허용하는 최대 상향 폭에서 takt 단축. 50초 이하 달성 여부는 단계 상향 실측으로 판정(미측정).",
        "target": "서보 제어 가감속 프로파일(가속 시간, 최고 각속도, 정착 시간) 및 감속 구간 제동 방식"
      },
      "open_risks": [
        "부하율 허용 범위 수치 미확인으로 HARD 제약 위반 판정 기준 부재 — 잠정 게이트는 실측 기준값이 아니므로 확정 판정에 사용 불가",
        "계면 고유진동수 미확인으로 가속도 상향 시 공진으로 강성·안정성 HARD 위반 가능",
        "강성·하드웨어 안정성 정량 허용 기준값 미확인으로 저하 판정 기준 부재",
        "회생 제동 기능·전력 처리 용량 미확인으로 감속 구간 단축분 확보 불확실",
        "정착 시간 단축이 서보 대역폭 한계에 근접하면 오버슈트·잔류 진동으로 정렬 정밀도 저하 가능",
        "고속화 시 베어링·접촉면 발열 증가(추정: 직접 관측 근거 없음)로 열변형 위험"
      ],
      "provided_functions": [
        "가속·감속 구간 시간 단축을 통한 takt 감소",
        "판정 지표 여유율 기반 상향 폭 결정",
        "진동 스펙트럼 감시를 통한 공진 조기 검출"
      ],
      "required_functions": [
        "부하율·진동·온도·정착 시간 동시 계측",
        "고유진동수 측정",
        "상한 수치 확인 전 잠정 게이트 판정",
        "회생 제동 기능·전력 용량 확인"
      ],
      "required_resources": [
        "기존: 서보 제어기 프로파일 파라미터 설정 권한(첨부 답변: 변경 여지 있음, 권한 보유 주체 미확인)",
        "기존: 서보 모터·인덱서 부하율 로그(첨부 답변: 60% 수준)",
        "기존: 단계별 타임스탬프 계측 데이터(첨부 답변: 가속·감속과 정렬·클램프 양쪽 유사)",
        "신규: 진동 측정 채널(회전축·베어링·클램프 계면) — 고유진동수·가진 주파수 이격 감시용",
        "신규: 베어링·접촉면 온도 측정 채널 — 열변형 감시용",
        "신규: 부하율·진동·온도·정착 시간 동시 로깅 및 게이트 판정 도구",
        "기존(조건부): 서보 제어기 회생 제동 기능 — 미확인, 기능·전력 처리 용량 확인 시 적용"
      ],
      "resolution_argument": "TC-ba15f1e6(가속도 상향 → takt 단축 vs 부하율·강성 악화)과 TC-c8cf7951(부하율·강성 보호 위해 가속도 하향 → takt 초과)은 동일 파라미터(가속도)가 개선측과 보호측을 동시에 지배해 물리적 모순(PC)으로 닫힌다. 이 후보는 모순을 '파라미터 값을 크게/작게'로 푸는 대신, 상향 폭을 판정 지표 여유율의 함수로 만들어 개선측(takt 단축)을 보호측(부하율·강성·안정성)의 실측 여유가 허용하는 만큼만 소진한다. 즉 가속도를 '상향한다/하지 않는다'의 이분법에서 '여유율 임계까지 상향한다'는 연속 제어로 바꾼다. 이때 보호측 상한 수치가 미확인이므로 상한을 창작하지 않고, (a) 상한 수치 확인 시 절대 게이트, (b) 미확인 시 현재 운전점 대비 상대 증가율 잠정 게이트를 병기한다. 고유진동수 미확인은 공진 회피를 '선행 조건'이 아니라 '감시 하 제한 상향'으로 처리해, 확인 전에도 takt 단축 실험을 진행하되 진동 스펙트럼 급증 시 즉시 하향하는 반증 경로를 둔다. 회생 제동은 기능·용량 미확인이므로 조건부 적용으로 분리해, 기능 부재 시에도 가속 시간 단축만으로 부분 단축이 성립하게 한다. 결과적으로 TC-ba15f1e6의 양측(IMPROVE: takt 단축, PROTECT: 부하율·강성·안정성)과 TC-c8cf7951의 양측을 모두 검증 계획에 포함한다.",
      "subproblem": "부하율 허용 범위 수치·계면 고유진동수·강성·안정성 정량 허용 기준값이 미확인인 상태에서, HARD 제약 위반 판정 기준을 창작하지 않고도 가속도 상향 폭을 결정하는 절차를 확립한다.",
      "title": "가감속 프로파일 단계적 상향 — 판정 기준·자원 귀속·단계 폭 절차 보강",
      "validation_plan": [
        {
          "baseline": "현재 takt 53초(soft), 부하율 60% 수준(soft), 프로파일 보수적 설정",
          "experiment": "가속 시간·최고 각속도를 단계 상향하며 각 단계에서 단계별 타임스탬프와 부하율·진동·온도를 동시 측정하고, 게이트 임계(절대 상한 확인 시 절대값, 미확인 시 상대 증가율 잠정값) 초과 직전 조합을 운전점으로 채택",
          "failure_criterion": "부하율 허용 범위 초과 또는 진동·온도 허용 기준 초과 또는 takt 50초 초과",
          "metric": "단계별 타임스탬프(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기), 부하율, 진동 진폭, 온도, 정착 시간",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "takt 50초 이하 달성 및 모든 게이트 지표가 임계 이내",
          "target": "takt 50초 이하(HARD), 부하율 허용 범위 내, 진동·온도 허용 기준 내"
        },
        {
          "baseline": "고유진동수 미확인",
          "experiment": "모터·인덱서 출력축과 회전축 결합부 고유진동수 측정, 가속도 상향 단계별 진동 스펙트럼 비교",
          "failure_criterion": "가진 주파수가 고유진동수에 근접해 진동 진폭 급증",
          "metric": "계면 고유진동수 및 가진 주파수 이격비",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "이격비 목표 충족 및 진동 진폭 급증 없음",
          "target": "가진 주파수가 고유진동수 대비 충분히 이격(추정: 2배 이상)"
        },
        {
          "baseline": "온도 측정값 미확인, 정착 시간 파라미터 미확인",
          "experiment": "가속도 상향 운전 중 베어링·접촉면 온도와 정착 시간·정렬 오차를 동시 측정",
          "failure_criterion": "온도 허용 초과 또는 열변형으로 정착 시간·정렬 정밀도 저하",
          "metric": "베어링·접촉면 온도 및 정착 시간·정렬 오차",
          "obligation_refs": [
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-9a13d136",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-9a13d136",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "온도·정렬 오차 허용 내에서 정착 시간 단축",
          "target": "온도 허용 범위 내, 정착 시간 단축 시 정렬 오차 허용 내"
        },
        {
          "baseline": "정렬·클램프 소요 시간 미확인, 양쪽 유사 지배(첨부 답변)",
          "experiment": "정렬·클램프 소요 시간을 실측 분해하여 로테이션 구간과 비중 비교",
          "failure_criterion": "정렬·클램프 직렬 구간이 지배적이어서 프로파일 조정만으로 50초 미달",
          "metric": "정렬·클램프 소요 시간 및 로테이션 구간 비중",
          "obligation_refs": [
            {
              "contradiction_id": "TC-b5b764b0",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-b5b764b0",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-097b79ff",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-097b79ff",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "로테이션 프로파일 상향만으로 50초 이하 달성",
          "target": "로테이션 프로파일 조정만으로 50초 달성 가능 여부 판정"
        }
      ],
      "working_principle": "서보 제어 가감속 프로파일의 가속 시간·최고 각속도·정착 시간을 단계적으로 상향하면 가속·감속 구간 시간이 줄어 takt이 단축된다. 이 후보의 미해결 블로커는 세 가지다. (1) 부하율 60% 여유와 프로파일 변경 여지가 미확인 전제인데 성립 근거로 쓰였다. (2) 부하율 허용 범위 수치와 계면 고유진동수가 미확인이라 HARD 제약 위반 판정 기준이 없고, 단계 상향 폭 결정 절차가 구체화되지 않았다. (3) 프로파일 설정 권한·부하율 로그·회생 제동 기능의 기존/신규 귀속이 표시되지 않았다. 보강 원리는 다음과 같다. 먼저 상향 폭을 파라미터 값이 아니라 '판정 지표의 여유율'로 정의한다. 각 단계에서 부하율·진동 진폭·온도·정착 시간을 동시 측정하고, 각 지표의 상한 대비 사용률이 임계(추정: 80%)를 넘지 않는 최대 상향 폭을 채택한다. 상한 수치가 미확인인 지표는 상한을 새로 만들지 않고, 현재 운전점 대비 상대 증가율 한계(추정: 부하율 +10%p, 진동 진폭 +20%, 온도 +5K)를 잠정 게이트로 쓰되 이는 실측 기준값 확보 전의 임시값임을 명시한다. 둘째, 가진 주파수와 계면 고유진동수의 이격을 상향 허용의 선행 조건으로 둔다. 고유진동수 미확인 상태에서는 상향을 '진동 스펙트럼 감시 하의 제한 상향'으로만 허용하고, 이격비(추정: 2배 이상) 확인 시에만 상향 폭을 확대한다. 셋째, 감속 구간은 회생 제동 토크로 정착 시간을 줄이되 회생 기능·전력 처리 용량이 미확인이므로 '기능 확인 시 적용' 조건부로 둔다. 이 보강은 takt 50초 이하(HARD)와 부하율·강성·안정성 보존(HARD)을 동시에 만족하는 운전점을 실측으로 탐색하는 절차를 제공하며, 수치를 지어내지 않고 미확인 항목을 조건·가정·위험에 남긴다."
    },
    "status": "UNRESOLVED"
  },
  {
    "action": "REPAIR_CANDIDATE",
    "ancestor_regression": [],
    "attempt": 2,
    "blocker_id": "gap-ee8407b02217eddd77e4bfbd",
    "candidate_id": "CPT-S6-099405e4edc0a658",
    "decision_id": "dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586",
    "derived_candidate_id": "CPT-AX-385d85af4f23",
    "gap_kinds": [
      "QUALITY_REVIEW"
    ],
    "obligation_ids": [
      "TC-c8cf7951"
    ],
    "phase": "before_constraints",
    "preserved_baseline_id": "CPT-S6-099405e4edc0a658",
    "proposal": {
      "addresses_contradictions": [
        "TC-ba15f1e6",
        "TC-c8cf7951",
        "TC-4f7ba034",
        "TC-9a13d136",
        "TC-b5b764b0",
        "TC-097b79ff"
      ],
      "assumptions": [
        "부하율이 실제 60% 수준이다(첨부 답변, 정확 수치 미확인)",
        "가감속 프로파일이 보수적으로 설정되어 변경 여지가 있다(첨부 답변)",
        "가속·감속과 정렬·클램프 양쪽이 유사하게 지배적이다(첨부 답변)",
        "글라스는 2m급 대형, 수십 kg 수준이다(추정: 실측 미확인)",
        "부하율 허용 범위 수치가 확인 가능하다(미확인)",
        "계면 고유진동수가 측정 가능하다(미확인)",
        "강성·하드웨어 안정성 정량 허용 기준값이 확인 가능하다(미확인)",
        "서보 드라이브가 회생 제동을 지원한다(미확인)"
      ],
      "changes_to_system": [
        "가속 시간·최고 각속도·정착 시간 파라미터를 단계 상향(1단계: 가속 시간 -10%, 2단계: -20%, 3단계: -30% 등 사다리식, 추정: 구체 스텝은 임계값 확정 후 결정)",
        "부하율 허용 범위·계면 진동 허용·베어링 온도 허용의 세 게이트 임계값을 먼저 확정하는 사전 절차 추가",
        "단계별 타임스탬프(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기)와 부하율·진동·온도를 동시 계측하는 로깅 구성",
        "감속 구간 회생 제동 토크 활용 설정(회생 제동 기능·전력 처리 용량 확인 후 적용)",
        "게이트 위반 시 자동으로 직전 단계 운전점으로 복귀하는 파라미터 롤백 절차"
      ],
      "coherence": {
        "changed_variable": "가속 시간, 최고 각속도, 정착 시간, 게이트 임계값(부하율 허용 범위, 계면 진동 허용, 온도 허용)",
        "claims": [
          {
            "evidence_refs": [
              "CON-2e5d6859",
              "CON-87d3c928"
            ],
            "source_cause_id": "N1",
            "status": "OBSERVED",
            "text": "패턴 글라스 인라인 설비의 takt time이 53초로 목표 50초 이하를 초과하여 라인 LOB 향상 목표를 달성하지 못하고 생산 손실이 발생한다"
          },
          {
            "evidence_refs": [
              "CON-9f449042",
              "CON-8b834790"
            ],
            "source_cause_id": "N4",
            "status": "OBSERVED",
            "text": "정렬·클램프 공정 유닛이 로테이션 정지 후 직렬로 소요 시간을 추가한다"
          },
          {
            "evidence_refs": [
              "CON-8b834790"
            ],
            "source_cause_id": "N5",
            "status": "OBSERVED",
            "text": "서보 제어기가 감속 구간과 정렬·클램프의 중첩을 차단하여 직렬 시간을 누적시킨다"
          },
          {
            "evidence_refs": [
              "CON-f1a96104",
              "CON-6f1aa3c0"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "가속 시간·최고 각속도를 단계 상향하면 가속·감속 구간 시간이 줄어 takt이 단축된다"
          },
          {
            "evidence_refs": [
              "CON-f512b60e",
              "CON-88d264f2"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "가속도 상향 시 가진 주파수가 계면 고유진동수에 접근해 공진으로 강성·안정성 HARD 위반이 발생할 수 있다"
          },
          {
            "evidence_refs": [
              "CON-489f9a78"
            ],
            "source_cause_id": "",
            "status": "HYPOTHESIS",
            "text": "고속화로 베어링·접촉면 발열이 증가해 열변형으로 정착 시간·정렬 정밀도가 저하될 수 있다"
          },
          {
            "evidence_refs": [
              "CON-bae6ac73",
              "CON-03a2c34e"
            ],
            "source_cause_id": "",
            "status": "DERIVED",
            "text": "부하율 허용 범위 수치가 확정되기 전에는 상향 폭을 결정할 수 없다"
          }
        ],
        "conditions": [
          {
            "applicability": "서보 제어기 부하율 로그를 실측해 60% 수준인지 확인한다. 확인 전에는 상향 폭을 결정하지 않는다.",
            "condition": "부하율이 실제 60% 수준이다(첨부 답변, 정확 수치 미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "서보 제어기 파라미터 설정 권한과 변경 가능 범위를 현장에서 확인한다. 확인 전에는 상향 실험을 시작하지 않는다.",
            "condition": "프로파일 변경 여지가 있다(첨부 답변)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "부하율 로그 실측으로 확인한다. 미확인 상태를 확인 완료로 주장하지 않는다.",
            "condition": "부하율 60% 여유 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "파라미터 설정 권한·범위를 확인한다.",
            "condition": "프로파일 변경 여지 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "기준값 정의서 또는 설비 사양에서 확인한다. 미확인 시 게이트 임계값을 확정할 수 없다.",
            "condition": "강성·안정성 정량 허용 기준값 확인",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "본 수리안은 회전 동역학·구조 강성·동적 제어 범위의 파라미터 조정안으로, 장 분포·공간 구조 재설계를 요구하지 않는다. 해당 조건은 본 후보에 적용되지 않는다.",
            "condition": "모델의 효율 개선에 특정 장 분포, 물질의 공간 구조 또는 에너지 집중·비작용 구역이 필요할 때.",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "부하율 로그 실측으로 확인한다.",
            "condition": "부하율이 실제 60% 수준으로 확인될 때",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "계면 진동·온도 측정값과 허용 기준값을 대조한다. 기준값 미확인 시 판정 불가로 남긴다.",
            "condition": "가속도 상향 시 진동·온도가 강성·안정성 허용 기준 내일 때(기준값 미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "모터·인덱서 정격 토크와 허용 부하율을 사양서에서 확인한다.",
            "condition": "부하율 허용 범위 수치 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "모터·인덱서 출력축과 회전축 결합부 고유진동수를 측정한다.",
            "condition": "계면 고유진동수 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "글라스·스테이지 관성모멘트를 실측 또는 계산으로 확인한다.",
            "condition": "관성모멘트 실측값 확인(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "서보 드라이브 사양에서 회생 제동 기능 지원 여부를 확인한다.",
            "condition": "서보 드라이브가 회생 제동을 지원할 것(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          },
          {
            "applicability": "회생 저항·전력 회수 구성의 용량을 확인한다.",
            "condition": "회생 전력 처리 용량이 충분할 것(미확인)",
            "source_idea_id": "IDEA-db0428fa"
          }
        ],
        "contribution": "DIRECT",
        "control_chain": {
          "actuator": "서보 제어기 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간) 설정 변경",
          "decision": "세 게이트 임계값 대비 위반 판정 및 다음 단계 상향/롤백 결정",
          "estimator": "단계별 타임스탬프와 부하율·진동·온도의 결합 분석으로 게이트 위반 여부 및 takt 기여 분해",
          "sensor": "부하율 로그(서보 제어기), 계면 진동 센서(신규), 베어링·접촉면 온도 센서(신규), 단계별 타임스탬프 계측",
          "target": "가감속 프로파일 파라미터 및 운전점"
        },
        "control_mode": "ACTIVE",
        "intervention": "가속 시간·최고 각속도·정착 시간을 사다리식으로 단계 상향하되, 부하율·계면 진동·베어링 온도의 세 게이트 임계값을 먼저 확정하고 각 단계에서 세 값을 동시 측정해 위반 직전 조합을 운전점으로 채택한다.",
        "mediating_functions": [
          "가속 시간 감소 → 가속 구간 시간 감소 → takt 감소",
          "최고 각속도 상향 → 정속 구간 시간 감소 → takt 감소",
          "각가속도 상향 → 토크 상승 → 부하율 상승(보호측 악화)",
          "가진력 증가 → 계면 진동 증가(보호측 악화)",
          "마찰 발열 증가 → 베어링·접촉면 온도 상승(보호측 악화)",
          "게이트 임계값 확정 → 상향 폭 결정 가능 → 모순의 시간축 분리"
        ],
        "operating_scope": "로테이션 가속·정속·감속 구간 및 정지 후 정착 구간. 정렬·클램프 직렬 구간은 본 수리안의 직접 대상이 아니며(중첩 불가 제약 유지), 원위치 복귀(무부하) 구간은 별도 검토 대상이다.",
        "outcome": "세 게이트를 위반하지 않는 최대 상향 운전점에서 takt이 단축된다. 50초 이하 달성 여부는 단계 상향 실측으로만 판정되며, 달성 실패 시 H2(정렬·클램프 병목) 지지로 판정된다.",
        "target": "서보 제어 가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간) 및 이를 감시하는 게이트 임계값"
      },
      "open_risks": [
        "부하율 허용 범위 수치 미확인으로 게이트 임계값을 확정하지 못하면 상향 폭 결정이 불가능하다",
        "계면 고유진동수 미확인으로 가속도 상향 시 가진 주파수가 고유진동수에 접근해 공진으로 강성·안정성 HARD 위반이 발생할 수 있다",
        "강성·안정성 정량 허용 기준값 미확인으로 '저하' 판정 자체가 불가능하다",
        "고속화 시 베어링·접촉면 발열 증가로 열변형이 정착 시간·정렬 정밀도를 저하시킬 수 있다(온도 측정값 미확인)",
        "회생 제동 기능·전력 처리 용량 미확인으로 감속 구간 단축이 실현되지 않을 수 있다",
        "프로파일 상향만으로 3초를 확보하지 못하면 정렬·클램프 직렬 구간(H2) 개선이 별도로 필요하다"
      ],
      "provided_functions": [
        "가속·감속 구간 소요 시간 단축(takt 감소)",
        "부하율·진동·온도 상한 게이트로 HARD 제약 위반 사전 검출",
        "단계별 운전점 채택 및 롤백"
      ],
      "required_functions": [
        "부하율 허용 범위 수치 확정",
        "계면 고유진동수 측정",
        "강성·안정성 정량 허용 기준값 확정",
        "운전 중 베어링·접촉면 온도 측정",
        "회생 제동 기능·전력 처리 용량 확인"
      ],
      "required_resources": [
        "서보 제어기 프로파일 파라미터 설정 권한(기존 자원 확인 필요)",
        "서보 모터·인덱서 부하율 로그(기존 자원 확인 필요)",
        "단계별 타임스탬프 계측 데이터(기존 자원 확인 필요)",
        "신규: 계면 진동 측정 센서(회전축·베어링·클램프 계면, 고유진동수 파악용)",
        "신규: 베어링·접촉면 온도 측정 수단(운전 중 연속 측정)",
        "신규: 부하율·진동·온도 게이트 임계값 확정을 위한 기준값 정의서",
        "서보 제어기 회생 제동 기능(미확인, 기존 자원 확인 필요)"
      ],
      "resolution_argument": "모순 TC-ba15f1e6(가속도 상향→takt 단축 vs 부하율·강성 악화)과 TC-c8cf7951(가속도 하향→부하율·강성 보호 vs takt 초과)은 동일 파라미터(가속도)가 개선측과 보호측을 동시에 지배하기 때문에 발생한다. 이 수리안은 파라미터를 없애지 않고, 파라미터 상향 폭을 '측정 가능한 보호측 상한'에 종속시켜 두 모순을 시간축에서 분리한다. 즉 (1) 보호측 상한값(부하율 허용 범위, 계면 진동 허용, 온도 허용)을 먼저 확정하고, (2) 그 상한까지 가속도를 단계 상향하며, (3) 각 단계에서 개선측(takt)과 보호측(부하율·진동·온도)을 동시 측정한다. 개선측이 목표(50초 이하)에 도달하기 전에 보호측이 상한에 닿으면 그 운전점이 해이고, 목표에 도달하지 못하면 프로파일 조정만으로는 불충분하다는 판정(H2 지지)이 나온다. 이는 '상한을 모르는 상태에서 상향 폭을 정하는' 기존 후보의 결함을, 상한 확정 절차를 메커니즘 내부로 끌어들여 제거한다. 감속 구간은 회생 제동 토크를 활용해 정착 시간을 줄이되, 회생 제동 기능·전력 처리 용량이 미확인이므로 '기능 확인 후 적용' 조건부로 둔다.",
      "subproblem": "",
      "title": "가감속 프로파일 단계 상향 + 부하율·진동·온도 상한 게이트 (미확인 전제 명시형 수리안)",
      "validation_plan": [
        {
          "baseline": "현재 takt 53초, 부하율 60% 수준(soft, 정확 수치 미확인)",
          "experiment": "가속 시간·최고 각속도를 사다리식으로 단계 상향하며 각 단계에서 단계별 타임스탬프와 부하율·진동·온도를 동시 측정. 세 게이트 중 하나라도 위반이 확인되면 직전 단계를 운전점으로 채택",
          "failure_criterion": "부하율 허용 범위 초과 또는 진동·온도 허용 기준 초과 또는 takt 50초 초과",
          "metric": "단계별 타임스탬프(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기), 부하율, 계면 진동, 베어링·접촉면 온도",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-c8cf7951",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "takt 50초 이하 달성 및 세 게이트 모두 허용 범위 내",
          "target": "takt 50초 이하, 부하율 허용 범위 내, 진동·온도 허용 기준 내"
        },
        {
          "baseline": "고유진동수 미확인",
          "experiment": "모터·인덱서 출력축과 회전축 결합부 고유진동수를 측정하고, 가속도 상향 단계별 진동 스펙트럼을 비교해 가진 주파수와의 이격을 확인",
          "failure_criterion": "가진 주파수가 고유진동수에 근접해 진동 진폭 급증",
          "metric": "계면 고유진동수 및 가진 주파수 이격비",
          "obligation_refs": [
            {
              "contradiction_id": "TC-ba15f1e6",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "전 단계에서 가진 주파수가 고유진동수 대비 충분히 이격",
          "target": "가진 주파수가 고유진동수 대비 충분히 이격(추정: 2배 이상)"
        },
        {
          "baseline": "온도 측정값 미확인, 정착 시간 파라미터 미확인",
          "experiment": "가속도 상향 운전 중 베어링·접촉면 온도와 정착 시간·정렬 오차를 동시 측정해 열변형 영향을 판정",
          "failure_criterion": "온도 상승으로 정착 시간·정렬 오차가 허용 기준 초과",
          "metric": "베어링·접촉면 온도 및 정착 시간·정렬 오차",
          "obligation_refs": [
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-4f7ba034",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-9a13d136",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-9a13d136",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "온도 허용 범위 내이며 정착 시간·정렬 오차가 허용 기준 내",
          "target": "온도 허용 범위 내, 정착 시간·정렬 오차 허용 기준 내"
        },
        {
          "baseline": "소요 시간 수치 미확인",
          "experiment": "정렬·클램프 소요 시간을 실측 분해하여 로테이션 구간과의 비중을 비교. 프로파일 상향만으로 50초 달성 가능한지 판정",
          "failure_criterion": "프로파일 상향만으로 50초 미달(H2 지지, 정렬·클램프 개선 별도 필요)",
          "metric": "정렬·클램프 소요 시간 및 로테이션 구간 대비 비중",
          "obligation_refs": [
            {
              "contradiction_id": "TC-b5b764b0",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-b5b764b0",
              "side": "PROTECT"
            },
            {
              "contradiction_id": "TC-097b79ff",
              "side": "IMPROVE"
            },
            {
              "contradiction_id": "TC-097b79ff",
              "side": "PROTECT"
            }
          ],
          "success_criterion": "프로파일 상향만으로 50초 이하 달성(H2 기각)",
          "target": "H2 판정: 정렬·클램프가 실질 병목인지 여부 확정"
        }
      ],
      "working_principle": "서보 제어 가감속 프로파일의 가속 시간을 줄이고 최고 각속도를 올리면 가속·감속 구간 소요 시간이 줄어 takt이 단축된다. 이때 가속도 상향은 토크(=관성모멘트×각가속도)를 키워 모터·인덱서 부하율을 올리고, 가진력 증가로 계면 진동을 키우며, 마찰 발열을 늘린다. 따라서 상향 폭을 '부하율 상한, 계면 진동 상한, 베어링·접촉면 온도 상한'이라는 세 개의 측정 게이트로 제한한다. 각 단계마다 단계별 타임스탬프와 부하율·진동·온도를 동시 측정하고, 세 게이트 중 하나라도 위반이 확인되면 직전 단계 조합을 운전점으로 채택한다. 부하율 허용 범위 수치와 계면 고유진동수, 강성·안정성 정량 기준값이 미확인이므로, 이 수리안은 '게이트 임계값을 먼저 확정하는 절차'를 메커니즘의 필수 선행 조건으로 포함한다. 임계값이 확정되기 전에는 상향 폭을 결정할 수 없고, 따라서 takt 50초 이하 달성 여부는 실측으로만 판정된다."
    },
    "status": "UNRESOLVED"
  }
]
```
