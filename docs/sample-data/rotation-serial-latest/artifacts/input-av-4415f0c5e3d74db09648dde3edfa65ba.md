# input · 저장 산출물

[산출물·스냅샷 목록](../ARTIFACTS.md)

| 항목 | 저장값 |
|---|---|
| version_id | av-4415f0c5e3d74db09648dde3edfa65ba |
| epoch | 49 |
| content_hash | cc4e3150bc9d128851d79b4c7ff087679f0a88d1a40b70650973d13d4393b3dc |
| created_at | 2026-09-29T21:53:17.483164+00:00 |
| available_at | 2026-09-29T21:53:17.483182+00:00 |
| supersedes | av-04f9e092ef9d43c49ab2f224bd4be2ff |

## Payload

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `deep_dive` | 객체 · answer_turns, answers, competing_hypotheses, confirmed_facts, questions, skipped, theory_checks … | [펼쳐 보기](#field-6bb6eb402653a802) |
| `domain` | 객체 · difficulty, domain_tags, industry, is_engineering, job_family, legacy_note, operating_env … | [펼쳐 보기](#field-5ebbc649aaea046f) |
| `intake` | 객체 · attachments, candidate_characteristics, candidate_conflicts, clarify_turns, frame | [펼쳐 보기](#field-e6a1522548192e01) |
| `raw_query` | Display 산업에서 (대형 OLED) 배면 증착을 위해 상면에 패턴이 존재하는 반송물을(pattern glass) 반대로 180도 로테이션 해주는 설비가 있다. Line LOB 향상을 위해 해당… | [펼쳐 보기](#field-fb4c93b0a881805a) |

<a id="field-6bb6eb402653a802"></a>

<details>
<summary>deep_dive · 전체 값</summary>

```json
{
  "answer_turns": [
    {
      "answer": "양쪽이 유사하다",
      "question": "단계별 타임스탬프 분해(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기) 실측 데이터가 있는가?"
    },
    {
      "answer": "부하율 60% 수준, 여유 있음",
      "question": "모터·인덱서의 정격 토크와 현재 부하율은 얼마인가?"
    },
    {
      "answer": "보수적으로 설정되어 변경 여지 있음",
      "question": "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)는 어떻게 설정되어 있으며, 변경 가능한가?"
    }
  ],
  "answers": [
    "양쪽이 유사하다",
    "부하율 60% 수준, 여유 있음",
    "보수적으로 설정되어 변경 여지 있음"
  ],
  "competing_hypotheses": [
    {
      "discriminating_test": "가속 시간·최고 각속도를 단계적으로 상향하며 단계별 타임스탬프와 부하율·온도·진동을 동시 측정",
      "id": "H1",
      "mechanism": "가감속 프로파일이 보수적으로 설정되어 가속 시간·최고 각속도 상향만으로 takt 단축 가능(부하율 60% 여유 활용)",
      "observation": "부하율 60%, 프로파일 변경 여지 있음"
    },
    {
      "discriminating_test": "정렬·클램프 소요 시간을 실측 분해하여 로테이션 구간과의 비중 비교",
      "id": "H2",
      "mechanism": "정렬·클램프 직렬 구간이 실질 병목이며 로테이션 프로파일 조정만으로는 50초 달성 불가",
      "observation": "양쪽이 유사하게 지배적이라는 답변"
    },
    {
      "discriminating_test": "모터·인덱서 출력축과 회전축 결합부의 고유진동수 측정 및 가속도 상향 시 진동 스펙트럼 비교",
      "id": "H3",
      "mechanism": "가속도 상향 시 가진 주파수가 계면 고유진동수에 접근해 공진으로 강성·안정성 저하(HARD 위반)",
      "observation": "고유진동수 미확인"
    },
    {
      "discriminating_test": "가속도 상향 운전 중 베어링·접촉면 온도와 정착 시간·정렬 오차 동시 측정",
      "id": "H4",
      "mechanism": "고속화로 베어링·접촉면 발열이 증가해 열변형으로 정착 시간·정렬 정밀도 저하",
      "observation": "발열 증가 가능성 언급, 온도 미확인"
    }
  ],
  "confirmed_facts": [
    {
      "fact": "takt time을 50초 이하로 단축해야 한다(HARD)",
      "source": "제약 CON-f4381085, CON-5dda9265"
    },
    {
      "fact": "현재 takt time은 53초이다(soft)",
      "source": "제약 CON-e65c44f1"
    },
    {
      "fact": "모터·인덱서 부하율 허용 범위 초과 금지(HARD), 강성 저하 금지(HARD), 하드웨어 안정성 저하 금지(HARD)",
      "source": "제약 CON-bb334d98, CON-fb9494fe, CON-77617550"
    },
    {
      "fact": "시퀀스: 투입>로테이션>배출>원위치 복귀(역회전, 복귀 시 글라스 없음)",
      "source": "제약 CON-bb35b0c8, CON-b6c1fe9a"
    },
    {
      "fact": "로테이션 구동은 서보 제어 가감속 프로파일 방식",
      "source": "제약 CON-37a27106"
    },
    {
      "fact": "가속·감속·정지 구간이 takt의 지배적 병목(soft)",
      "source": "제약 CON-0cb179e8"
    },
    {
      "fact": "글라스 2m급 대형, 수십 kg(추정: 실측 미확인)",
      "source": "제약 CON-d29f49b7"
    },
    {
      "fact": "정렬·클램프 공정이 로테이션과 직렬로 소요 시간 추가, 감속 구간과 중첩 불가(soft)",
      "source": "제약 CON-2f0940f1, CON-0f181771"
    },
    {
      "fact": "첨부 답변: 가속·감속과 정렬·클램프 양쪽이 유사하게 지배적",
      "source": "첨부 answers[0]"
    },
    {
      "fact": "첨부 답변: 부하율 60% 수준, 여유 있음",
      "source": "첨부 answers[1]"
    },
    {
      "fact": "첨부 답변: 가감속 프로파일 보수적 설정, 변경 여지 있음",
      "source": "첨부 answers[2]"
    },
    {
      "fact": "고속화 시 베어링·접촉면 발열 증가 가능(추정: 직접 관측 근거 없음)",
      "source": "제약 CON-f796dcd7"
    }
  ],
  "questions": [
    {
      "proposed_answers": [
        "기준값 존재, 수치 확인 가능",
        "기준값 미설정",
        "기준값은 있으나 수치 미확인"
      ],
      "question": "가속도 상향 시 강성·안정성 저하를 판정할 정량 허용 기준값(진동, 변형, 온도)이 설정되어 있는가?",
      "why_needed": "HARD 제약 위반 판정 기준이 없으면 개선안 검증이 불가능하다."
    },
    {
      "proposed_answers": [
        "정지 후 시작, 소요 시간 확인 가능",
        "정지 전 일부 중첩 가능",
        "소요 시간 미확인"
      ],
      "question": "정렬·클램프 공정의 소요 시간은 얼마이며, 로테이션 정지 후 시작되는가?",
      "why_needed": "H2 검증 및 직렬 구간 단축 여지 판단에 필요하다."
    },
    {
      "proposed_answers": [
        "시도 이력 있음, 진동 문제 발생",
        "시도 이력 있음, 발열 문제 발생",
        "시도 이력 없음"
      ],
      "question": "과거에 가속도 상향 또는 프로파일 변경을 시도한 이력과 그 결과(실패 원인)가 있는가?",
      "why_needed": "기존 실패 시도가 H3·H4 중 어느 것을 지지하는지 판단한다."
    },
    {
      "proposed_answers": [
        "복귀 구간 단축 허용",
        "복귀 구간 단축 불가",
        "검토 필요"
      ],
      "question": "원위치 복귀(역회전, 무부하) 구간의 시간을 단축하는 것이 허용되는가?",
      "why_needed": "복귀 구간은 글라스가 없어 부하·강성 제약이 상대적으로 완화될 수 있다."
    }
  ],
  "skipped": true,
  "theory_checks": [
    {
      "applies_if": "부하율 60%로 토크 여유가 있고 관성모멘트가 확인될 때",
      "exclude_if": "부하율이 실제 80% 이상이거나 관성모멘트가 정격 토크 대비 과대할 때",
      "observation": "가감속 구간이 takt 지배적이며 프로파일이 보수적이라는 답변",
      "theory": "회전 동역학(각가속도-토크-관성)"
    },
    {
      "applies_if": "가속도 상향으로 가진 주파수가 계면 고유진동수에 접근할 때",
      "exclude_if": "가진 주파수가 고유진동수 대비 충분히 이격(추정: 2배 이상)으로 확인될 때",
      "observation": "고유진동수 미확인, 강성 정량 기준 미확인",
      "theory": "구조 강성·진동(고유진동수 이격)"
    },
    {
      "applies_if": "고속화로 베어링·접촉면 온도가 허용 상승할 때",
      "exclude_if": "운전 중 온도 측정값이 허용 범위 내로 확인될 때",
      "observation": "발열 증가 가능성만 언급, 온도 측정값 미확인",
      "theory": "열변형·마찰(베어링 발열)"
    },
    {
      "applies_if": "정착 시간 단축이 잔류 진동·오버슈트 없이 가능할 때",
      "exclude_if": "정착 시간이 이미 서보 대역폭 한계에 근접해 있을 때",
      "observation": "정착 시간 파라미터 미확인, 프로파일 변경 여지 있음",
      "theory": "동적 제어·안정성(정착 시간, 서보 대역폭)"
    }
  ],
  "unknowns": [
    "모터·인덱서 정격 토크 수치",
    "글라스 관성모멘트 실측값",
    "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)",
    "정렬·클램프 공정 소요 시간",
    "단계별 타임스탬프 실측 분해 데이터",
    "운전 중 베어링·접촉면 온도 측정값",
    "회전축·베어링·클램프 계면 고유진동수",
    "강성·하드웨어 안정성 정량 허용 기준값"
  ]
}
```

</details>

<a id="field-5ebbc649aaea046f"></a>

<details>
<summary>domain · 전체 값</summary>

```json
{
  "difficulty": "frontier",
  "domain_tags": [
    "takt time 단축(cycle time reduction)",
    "서보 가감속 프로파일(motion profile)",
    "회전 동역학(rotational dynamics)",
    "구조 강성(structural stiffness)",
    "진동·공진(vibration/resonance)",
    "부하율(load ratio)",
    "정착 시간(settling time)",
    "베어링 발열(bearing heating)",
    "대형 유리 반송(large glass handling)",
    "인덱서(indexer)"
  ],
  "industry": "디스플레이 제조 장비",
  "is_engineering": true,
  "job_family": "생산기술·설비 엔지니어링",
  "legacy_note": "투입>로테이션>배출>원위치 복귀(역회전) 시퀀스, 서보 제어 가감속 프로파일 구동, 정렬·클램프 공정이 로테이션과 직렬 배치",
  "operating_env": "디스플레이 라인 인라인, 2m급 대형 글라스 반송, 연속 takt 운전",
  "physical_scope": "회전 동역학·구조 강성·동적 제어 — 180도 로테이션 구동계의 가감속 프로파일과 takt time 단축, 모터·인덱서 부하율·강성·하드웨어 안정성 간 상충",
  "problem_type": "PHYSICAL_TECHNICAL",
  "sub_domain": "대형 OLED 배면 증착용 패턴 글라스 180도 로테이션 설비",
  "sub_systems": [
    "서보 모터",
    "인덱서",
    "회전축·베어링",
    "클램프·정렬 유닛",
    "제어기(가감속 프로파일)"
  ],
  "super_system": "패턴 글라스 반송·증착 인라인 설비",
  "target_system": "로테이션 구동계 단독(모터·인덱서·회전축)"
}
```

</details>

<a id="field-e6a1522548192e01"></a>

<details>
<summary>intake · 전체 값</summary>

```json
{
  "attachments": [],
  "candidate_characteristics": [
    "takt time 단축(속도)",
    "모터·인덱서 부하율",
    "구동계 강성",
    "하드웨어 안정성",
    "가감속 프로파일의 정착 시간",
    "베어링·접촉면 발열",
    "정렬·클램프 정밀도",
    "진동·공진 여유"
  ],
  "candidate_conflicts": [
    "가속도를 높이면 takt time은 줄지만 모터·인덱서 부하율과 발열이 증가한다.",
    "최고 각속도를 높이면 takt time은 줄지만 가진 주파수가 계면 고유진동수에 접근해 강성·안정성이 저하된다.",
    "정착 시간을 줄이면 takt time은 줄지만 잔류 진동·오버슈트로 정렬·클램프 정밀도가 나빠진다.",
    "정렬·클램프를 감속 구간과 병렬화하면 takt time은 줄지만 Slip 파손 위험이 커진다."
  ],
  "clarify_turns": [
    {
      "answered": true,
      "proposed_answers": [
        "현재 10초대, 목표 8초대",
        "현재 20초대, 목표 15초대",
        "현재 30초대, 목표 20초대",
        "잘 모르겠다"
      ],
      "question": "현재 takt time과 목표 takt time은 각각 몇 초인가?",
      "user_answer": "53초에서 50초",
      "why_needed": "단축 목표 폭을 알아야 회전 속도 상향 여유와 제약 충돌 여부를 판단할 수 있다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "로테이션이 최대 비중",
        "복귀·대기가 최대 비중",
        "투입·배출이 최대 비중",
        "잘 모르겠다"
      ],
      "question": "시퀀스 단계별(투입/로테이션/배출/복귀) 소요 시간은 각각 몇 초인가?",
      "user_answer": "로테이션이 최대 비중",
      "why_needed": "어느 구간이 takt을 지배하는지에 따라 해결 방향이 달라진다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "대략 1m급, 수 kg",
        "대략 2m급, 수십 kg",
        "대략 3m급, 수백 kg",
        "잘 모르겠다"
      ],
      "question": "글라스의 크기·중량·관성모멘트는 대략 얼마인가?",
      "user_answer": "대략 2m급, 수십 kg",
      "why_needed": "회전 동역학 계산으로 필요 토크와 부하율 여유를 산정할 수 있다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "가속 시간이 길고 최고속도 낮음",
        "가속 시간 짧고 최고속도 높음",
        "정속 위주, 가감속 거의 없음",
        "잘 모르겠다"
      ],
      "question": "가감속 프로파일(가속 시간, 최고 각속도)은 어떻게 설정되어 있는가?",
      "user_answer": "가속 시간이 길고 최고속도 낮음",
      "why_needed": "프로파일 조정만으로 takt을 줄일 수 있는지 판단할 수 있다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "정격 토크·부하율 수치 확인 가능",
        "정격 토크만 확인 가능",
        "수치 미확인"
      ],
      "question": "모터·인덱서의 정격 토크와 현재 부하율(60% 수준)의 정확한 수치를 확인할 수 있는가?",
      "user_answer": "",
      "why_needed": "부하율 여유의 절대적 판단과 각가속도 상향 시 필요 토크 산정이 불가하다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "중량·관성모멘트 실측값 있음",
        "중량만 있음",
        "둘 다 미확인"
      ],
      "question": "글라스의 중량과 회전축 중심 기준 관성모멘트 실측값이 있는가?",
      "user_answer": "",
      "why_needed": "각가속도 상향 시 필요 토크와 모터 부하율 증가분을 정량 산정할 수 없다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "세 파라미터 모두 확인 가능",
        "일부만 확인 가능",
        "미확인"
      ],
      "question": "현재 가감속 프로파일의 가속 시간, 최고 각속도, 정착 시간 설정값을 알 수 있는가?",
      "user_answer": "",
      "why_needed": "프로파일 파라미터가 없으면 takt 단축 여지와 부하율·진동 영향 산정이 불가하다."
    },
    {
      "answered": true,
      "proposed_answers": [
        "기준값 존재, 수치 확인 가능",
        "기준값 미설정",
        "기준값은 있으나 수치 미확인"
      ],
      "question": "가속도 상향 시 강성·안정성 저하를 판정할 정량 허용 기준값(진동·변형·온도)이 설정되어 있는가?",
      "user_answer": "기준값 존재, 수치 확인 가능",
      "why_needed": "HARD 제약 위반 판정 기준이 없으면 개선안 검증이 불가능하다."
    }
  ],
  "frame": {
    "confidence": 0.8,
    "current_workaround": "가감속 프로파일을 보수적으로 설정하여 운전(가속 시간 길고 최고 각속도 낮음)",
    "missing_info": [
      "모터·인덱서 정격 토크와 현재 부하율 정확 수치가 필요하다(부하율 여유 판정)",
      "글라스 관성모멘트 실측값이 필요하다(각가속도-토크 산정)",
      "가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)가 필요하다(단축 여지 판정)",
      "정렬·클램프 공정 소요 시간이 필요하다(직렬 병목 비중 판정)",
      "단계별 타임스탬프 실측 분해 데이터가 필요하다(병목 위치 확정)",
      "회전축·베어링·클램프 계면 고유진동수가 필요하다(공진 위험 판정)",
      "강성·하드웨어 안정성 정량 허용 기준값이 필요하다(HARD 제약 위반 판정)",
      "운전 중 베어링·접촉면 온도 측정값이 필요하다(발열 한계 판정)"
    ],
    "prior_attempts": [],
    "raw_query": "Display 산업에서 (대형 OLED) 배면 증착을 위해 상면에 패턴이 존재하는 반송물을(pattern glass) 반대로 180도 로테이션 해주는 설비가 있다. \r\nLine LOB 향상을 위해 해당 장비의 takt time을 단축해야 하나, 단순히 전체 속도를 향상하기 위해서는 로테이션에 개입하는 모터 및 인덱서의 부하율, 강성, 하드웨어 안정성 등의 문제로 인해 제약이 존재하는 상황이다. \r\n장비는 투입 > 로테이션 > 배출 후, 다시 원위치로 돌아와 다음 패턴 글라스의 투입을 대기하는 시퀀스로 구성되어있다. \r\n괜찮은 해결책은?",
    "restated_problem": "패턴 글라스 180도 로테이션 설비의 takt time을 53초에서 50초 이하로 단축하되, 모터·인덱서 부하율·강성·하드웨어 안정성 저하 없이 달성해야 한다.",
    "success_criteria": [
      "takt time <= 50초 달성",
      "모터·인덱서 부하율 허용 범위 내 유지",
      "강성·하드웨어 안정성 저하 없음"
    ],
    "symptom": "로테이션 가속·감속·정지 구간이 takt의 지배적 병목이며, 전체 속도 상향 시 부하율·강성·안정성 제약에 부딪힘",
    "when_where": "로테이션 가속·감속·정지 구간, 모터·인덱서 출력축과 회전축 결합부"
  }
}
```

</details>

<a id="field-fb4c93b0a881805a"></a>

<details>
<summary>raw_query · 전체 값</summary>

```json
"Display 산업에서 (대형 OLED) 배면 증착을 위해 상면에 패턴이 존재하는 반송물을(pattern glass) 반대로 180도 로테이션 해주는 설비가 있다. \r\nLine LOB 향상을 위해 해당 장비의 takt time을 단축해야 하나, 단순히 전체 속도를 향상하기 위해서는 로테이션에 개입하는 모터 및 인덱서의 부하율, 강성, 하드웨어 안정성 등의 문제로 인해 제약이 존재하는 상황이다. \r\n장비는 투입 > 로테이션 > 배출 후, 다시 원위치로 돌아와 다음 패턴 글라스의 투입을 대기하는 시퀀스로 구성되어있다. \r\n괜찮은 해결책은?"
```

</details>

## 계보

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `parents` | [] | 표에 전체 값 표시 |
| `provenance` | 객체 · action_instance_ids, approval_status, bundle_id, decision_id, decision_ids, evidence_status, reason … | [펼쳐 보기](#field-d93fa363019553eb) |

<a id="field-d93fa363019553eb"></a>

<details>
<summary>provenance · 전체 값</summary>

```json
{
  "action_instance_ids": [],
  "approval_status": "UNREVIEWED",
  "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
  "decision_id": "dec-e4d464594c69ae2a90b4c3534394bbc5c01b37f4a578251bfd9232baf64f",
  "decision_ids": [],
  "evidence_status": "ASSERTED",
  "reason": "s1_intake",
  "semantic_episode_id": null,
  "workflow": "triz-ax-v3.1"
}
```

</details>
