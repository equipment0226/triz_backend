# 독립 품질 검토 (1/1)

[제약 검토](../stages/09-s7-gate.md)

| 항목 | 저장값 |
|---|---|
| step_id / seq | STP-ee6a01ff / 787 |
| 실제 Stage / DB stage | s7_gate / S6_CONCEPT |
| node | s6_quality |
| Agent / Prompt | independent_auditor / P_VERIFIER_GENERIC |
| 등급 / 모델 | T3 / 호출 없음 |
| 상태 / 판정 | OK / PASS |
| KST 시작 / 종료 | 2026-09-30 13:25:59 / 2026-09-30 13:26:12 |
| 저장 비용 USD | 0.0085569 |
| 입력 / 출력 토큰 | 22199 / 1581 |
| 범위 | CURRENT_RERUN |

## Input · 실제 전달 변수

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `concepts` | 배열 1개 | [전체 값](../payloads/a319731624b07c2f7dc79c73.md) |
| `facts` | 객체 · user_query, frame, attachments, answers, deep_dive_answers, deep_dive_answer_turns … | [전체 값](../payloads/cda155e8088903c753502d7f.md) |
| `input_hash` | "8f2dcf296c5c74759f680ea587669a54beb82168c9e6fd67c36a77f4b2f801c4" | 전체 값 |
| `audit_contract` | "s6-audit-batches-v3-directions" | 전체 값 |
| `review_instruction` | 후보별 판단을 per_concept에 반드시 기록한다. 개입→매개 기능→결과의 물리적 타당성, 원래 모순 양측, 조건의 적용 범위와 원인 가설을 독립 검토한다. 경로 문자열의 존재는 타당성 증명이 아니다. 미실험은 설계 불성립과 구분한다. 능동 구동 … | [전체 값](../payloads/03fd37dcbd5c7337ad3b15bd.md) |

## Output · 최종 저장 결과

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdict` | "PASS" | 전체 값 |
| `score` | 0.7625 | 전체 값 |
| `per_criterion` | 배열 5개 | [전체 값](../payloads/c9d822bdaa85be5f3a7da27a.md) |
| `fatal_flaws` | [] | 전체 값 |
| `revision_instructions` | 배열 4개 | [전체 값](../payloads/ede3455ebd8ccefc7d3642bf.md) |
| `confidence` | 0.72 | 전체 값 |
| `per_concept` | 배열 1개 | [전체 값](../payloads/67d4c6d68b60beb256d7e600.md) |
| `rubric` | "R6_CONCEPT" | 전체 값 |

## 검증과 추적

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdicts` | 배열 1개 | [전체 값](../payloads/208f9f464c869c9641554c07.md) |
| `error` | "" | 전체 값 |
| `input_metadata` | 객체 · concepts, facts, input_hash, audit_contract, review_instruction | [전체 값](../payloads/3bb885cf464934f959072e85.md) |
| `prompt_text_fingerprints` | {} | 전체 값 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label … | [전체 값](../payloads/f1497ae946628a5f20faba67.md) |

출처: `steps.input_slice`, `output_json`, `verdicts`. 구조 검사 통과와 기술적 제약 판정은 서로 다릅니다. 중간 수정 응답은 새로 만들지 않았습니다. Step 비용은 실행 당시 원본이며 비용정정으로 덮어쓰지 않았습니다. 정정 반영 합계는 비용 비교표를 확인합니다.

[원본 비용·정정 비용 비교](../COSTS.md)
