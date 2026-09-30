# 특허·논문 검색 수집 상태

[근거 자료·적용 조건 검토](../stages/10-s8-references.md)

| 항목 | 저장값 |
|---|---|
| step_id / seq | STP-a1cef78f / 806 |
| 실제 Stage / DB stage | s8_references / S8_REFERENCES |
| node | s9_search_retrieval |
| Agent / Prompt | patent_researcher / — |
| 등급 / 모델 | — / 호출 없음 |
| 상태 / 판정 | WARN /  |
| KST 시작 / 종료 | 2026-09-30 13:37:55 / 2026-09-30 13:40:20 |
| 저장 비용 USD | 0.0 |
| 입력 / 출력 토큰 | 0 / 0 |
| 범위 | CURRENT_RERUN |

## Input · 실제 전달 변수

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `queries` | 배열 20개 | [전체 값](../payloads/e0a38c8607bf005d1cd3ae19.md) |

## Output · 최종 저장 결과

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `queries` | 객체 · PATENT:torsional stiffness coupling inertia tradeoff drive, PATENT:torque feedback acceleration profile load limit, PATENT:jerk limited motion profile peak torque reduction, PATENT:viscoelastic damping layer contact interface stiffness, PATENT:load ratio feedback adaptive acceleration clamping, PATENT:aircraft rotor vibration damping mount … | [전체 값](../payloads/5c6ca620c13e8bc4ed584b67.md) |

## 검증과 추적

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdicts` | [] | 전체 값 |
| `error` | "" | 전체 값 |
| `input_metadata` | 객체 · queries | [전체 값](../payloads/606dea5c29c16550dcba599b.md) |
| `prompt_text_fingerprints` | {} | 전체 값 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label … | [전체 값](../payloads/73c3235e98db9fd53573e943.md) |

출처: `steps.input_slice`, `output_json`, `verdicts`. 구조 검사 통과와 기술적 제약 판정은 서로 다릅니다. 중간 수정 응답은 새로 만들지 않았습니다. Step 비용은 실행 당시 원본이며 비용정정으로 덮어쓰지 않았습니다. 정정 반영 합계는 비용 비교표를 확인합니다.

[원본 비용·정정 비용 비교](../COSTS.md)
