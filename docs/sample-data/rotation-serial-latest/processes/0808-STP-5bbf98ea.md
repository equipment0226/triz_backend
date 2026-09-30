# 특허·논문 적용성 검토

[근거 자료·적용 조건 검토](../stages/10-s8-references.md)

| 항목 | 저장값 |
|---|---|
| step_id / seq | STP-5bbf98ea / 808 |
| 실제 Stage / DB stage | s8_references / S8_REFERENCES |
| node | s9_evidence_match_1 |
| Agent / Prompt | patent_researcher / P_EVIDENCE_MATCH |
| 등급 / 모델 | T2 / deepseek-flash |
| 상태 / 판정 | OK / PASS |
| KST 시작 / 종료 | 2026-09-30 13:41:28 / 2026-09-30 13:41:53 |
| 저장 비용 USD | 0.0066681 |
| 입력 / 출력 토큰 | 13259 / 2242 |
| 범위 | CURRENT_RERUN |

## Input · 실제 전달 변수

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `concepts` | 배열 3개 | [전체 값](../payloads/224125cf07b5078e64aec47f.md) |
| `candidates` | 배열 16개 | [전체 값](../payloads/d56b21f22543882f8daa9d30.md) |
| `constraints` | 배열 20개 | [전체 값](../payloads/6f6510694d859ed4a31bce6a.md) |
| `required_kinds` | ["PAPER", "PATENT"] | 전체 값 |
| `max_matches_per_kind` | 2 | 전체 값 |
| `max_additions` | 3 | 전체 값 |

## Output · 최종 저장 결과

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `matches` | 배열 5개 | [전체 값](../payloads/655fbb70232b8023834b6e2d.md) |
| `additions` | 배열 3개 | [전체 값](../payloads/b7c7e05d2dd58c4cd9dc7ea5.md) |

## 검증과 추적

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdicts` | [{"verdict": "PASS", "score": 1.0, "source": "none"}] | 전체 값 |
| `error` | "" | 전체 값 |
| `input_metadata` | {"prompt_id": "P_EVIDENCE_MATCH", "prompt_hash": "ccc3b67f3e80a92cbe7b2eb0a89a627b5597469445519f420d5cc013a21db53d"} | 전체 값 |
| `prompt_text_fingerprints` | {"system": {"sha256": "9673487b77f6e6cff6555d401424c0344ba6dda8365865b278ad83d3ddc06ef8", "utf8_bytes": 6842}, "user": {"sha256": "ccc3b67f3e80a92cbe7b2eb0a89a627b5597469445519f420d5cc013a21db53d", "utf8_bytes": 41479}} | 전체 값 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label … | [전체 값](../payloads/05167c22418bd546f8c22940.md) |

출처: `steps.input_slice`, `output_json`, `verdicts`. 구조 검사 통과와 기술적 제약 판정은 서로 다릅니다. 중간 수정 응답은 새로 만들지 않았습니다. Step 비용은 실행 당시 원본이며 비용정정으로 덮어쓰지 않았습니다. 정정 반영 합계는 비용 비교표를 확인합니다.

[원본 비용·정정 비용 비교](../COSTS.md)
