# 기능 분석(컴포넌트/상호작용/기능도)

[시스템·기능·자원·인과 분석](../stages/05-s3-analyze.md)

| 항목 | 저장값 |
|---|---|
| step_id / seq | STP-e066ffae / 735 |
| 실제 Stage / DB stage | s3_analyze / S3_ANALYZE |
| node | s3_function_model |
| Agent / Prompt | system_analyst / P_S3_FUNCTION_MODEL |
| 등급 / 모델 | T2 / deepseek-flash |
| 상태 / 판정 | OK / PASS |
| KST 시작 / 종료 | 2026-09-30 12:59:37 / 2026-09-30 13:00:34 |
| 저장 비용 USD | 0.0218793 |
| 입력 / 출력 토큰 | 36559 / 9093 |
| 범위 | CURRENT_RERUN |

## Input · 실제 전달 변수

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `industry` | "디스플레이 제조 장비" | 전체 값 |
| `chosen_system` | 객체 · id, name, scope, description, diagram_mermaid, similarity_reason … | [전체 값](../payloads/6a71bbae9da17a79f4dfbec7.md) |
| `problem_zone` | "로테이션 가속·감속·정지 구간과 그 직후 정렬·클램프 구간의 직렬 합산 시간이 takt 50초를 초과하게 만드는 구동계·계면 영역" | 전체 값 |
| `operative_zone` | "서보 모터 출력축 → 인덱서 → 회전축 → 베어링 접촉면의 토크·각가속도 전달 계면" | 전체 값 |
| `attachment_facts` | [] | 전체 값 |
| `nw_insights` | 배열 6개 | [전체 값](../payloads/1ba029fcb727a031731ae0e3.md) |
| `min_components` | 14 | 전체 값 |
| `max_components` | 28 | 전체 값 |
| `min_harmful` | 2 | 전체 값 |

## Output · 최종 저장 결과

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `components` | 배열 18개 | [전체 값](../payloads/a8674410b076cde3893e7d90.md) |
| `interaction_cells` | 배열 15개 | [전체 값](../payloads/fbf40bc0a7f4313f41bc1437.md) |
| `function_edges` | 배열 13개 | [전체 값](../payloads/97c9c7dee93f47a192c4992e.md) |
| `mermaid` | flowchart LR "서보 제어기" -->\|"가감속 프로파일 명령 전달"\| "서보 모터" "서보 모터" -->\|"토크 전달"\| "인덱서" "인덱서" -->\|"회전 운동 전달"\| "회전축" "베어링" -->\|"회전축 지지"\| "회전축" "회전축" -… | [전체 값](../payloads/4531965cc9b600a6aa126c7b.md) |

## 검증과 추적

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdicts` | 배열 2개 | [전체 값](../payloads/89fd1d366a0650f7a1cd1256.md) |
| `error` | "" | 전체 값 |
| `input_metadata` | {"prompt_id": "P_S3_FUNCTION_MODEL", "prompt_hash": "8e1cd9d0545d54b7d936903bef9e99e56d080f4fe0aa23618e4f9365f29a0c6c"} | 전체 값 |
| `prompt_text_fingerprints` | {"system": {"sha256": "c1fd152300d68199b46a99a2700298307566dd37b09330c42a170a4301b6d86d", "utf8_bytes": 6058}, "user": {"sha256": "8e1cd9d0545d54b7d936903bef9e99e56d080f4fe0aa23618e4f9365f29a0c6c", "utf8_bytes": 21592}} | 전체 값 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label … | [전체 값](../payloads/7fcfc779a9e4575deecfd60f.md) |

출처: `steps.input_slice`, `output_json`, `verdicts`. 구조 검사 통과와 기술적 제약 판정은 서로 다릅니다. 중간 수정 응답은 새로 만들지 않았습니다. Step 비용은 실행 당시 원본이며 비용정정으로 덮어쓰지 않았습니다. 정정 반영 합계는 비용 비교표를 확인합니다.

[원본 비용·정정 비용 비교](../COSTS.md)
