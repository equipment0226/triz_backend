# Track A 발명원리 적용(TC-da1055a5)

[다중 기법 해결책 탐색](../stages/07-s5-solve.md)

| 항목 | 저장값 |
|---|---|
| step_id / seq | STP-2cae9b7c / 748 |
| 실제 Stage / DB stage | s5_solve / S5_SOLVE |
| node | s5_track_a |
| Agent / Prompt | inventor_a / P_S5_TRACK_A |
| 등급 / 모델 | T2 / deepseek-flash |
| 상태 / 판정 | WARN / UNVERIFIED |
| KST 시작 / 종료 | 2026-09-30 13:05:02 / 2026-09-30 13:05:23 |
| 저장 비용 USD | 0.0062763 |
| 입력 / 출력 토큰 | 8233 / 3172 |
| 범위 | CURRENT_RERUN |

## Input · 실제 전달 변수

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `industry` | "디스플레이 제조 장비" | 전체 값 |
| `target_system` | "로테이션 구동계(서보 모터·인덱서·회전축·베어링)" | 전체 값 |
| `super_system` | "대형 OLED 배면 증착 인라인 반송 라인" | 전체 값 |
| `if_action` | "서보 제어 가감속 프로파일의 가속도·최고 각속도를 상향한다" | 전체 값 |
| `then_good` | "가속·감속 구간 시간이 줄어 로테이션 사이클 시간이 단축되고 takt이 50초 이하에 근접한다" | 전체 값 |
| `but_bad` | "모터·인덱서 부하율이 상승하고 베어링·접촉면 발열이 증가하여 HARD 제약(CON-7d37c553, CON-b038b5ea) 위반 위험이 커진다" | 전체 값 |
| `improving_id` | 39 | 전체 값 |
| `improving_name` | "생산성" | 전체 값 |
| `improving_def` | "단위 시간당 수행되는 유효 작업량 또는 산출량. 처리량, 수율 반영." | 전체 값 |
| `worsening_id` | 21 | 전체 값 |
| `worsening_name` | "동력" | 전체 값 |
| `worsening_def` | "단위 시간당 수행되는 일. 출력, 처리 능력의 물리적 근원." | 전체 값 |
| `resources` | 배열 22개 | [전체 값](../payloads/31b50c7b7cbd865e813421ee.md) |
| `su_fields` | 배열 3개 | [전체 값](../payloads/36199bcb1af2c17e9adc5b94.md) |
| `matrix_note` | "모순 행렬 조회 + 교차검토 추가 2건" | 전체 값 |
| `principles_block` | #35 속성 변경(Parameter changes): 물리 상태·농도·밀도·유연성·온도 등 파라미터를 바꾼다. 하위 기법: 물리적 상태 변경 / 농도·점도 변경 / 유연성 변경 / 온도 변경 #20 유익작용의 지속(Continuity of useful… | [전체 값](../payloads/ab5364c602b35ba590e62801.md) |
| `ideas_per_principle` | 1 | 전체 값 |

## Output · 최종 저장 결과

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `applications` | 배열 5개 | [전체 값](../payloads/3d37aa6d9481dbb1f642c279.md) |

## 검증과 추적

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `verdicts` | [{"verdict": "UNVERIFIED", "score": 0.0, "skipped": true, "source": "policy"}] | 전체 값 |
| `error` | "" | 전체 값 |
| `input_metadata` | {"prompt_id": "P_S5_TRACK_A", "prompt_hash": "1fa0521cbf0d595b860530dc37e10858e869a25d3efac12e7fe5057c81fa4a33"} | 전체 값 |
| `prompt_text_fingerprints` | {"system": {"sha256": "9673487b77f6e6cff6555d401424c0344ba6dda8365865b278ad83d3ddc06ef8", "utf8_bytes": 6842}, "user": {"sha256": "1fa0521cbf0d595b860530dc37e10858e869a25d3efac12e7fe5057c81fa4a33", "utf8_bytes": 19209}} | 전체 값 |
| `step_metadata` | 객체 · step_id, run_id, seq, stage, node, label … | [전체 값](../payloads/e25de69089af74397f2f0cee.md) |

출처: `steps.input_slice`, `output_json`, `verdicts`. 구조 검사 통과와 기술적 제약 판정은 서로 다릅니다. 중간 수정 응답은 새로 만들지 않았습니다. Step 비용은 실행 당시 원본이며 비용정정으로 덮어쓰지 않았습니다. 정정 반영 합계는 비용 비교표를 확인합니다.

[원본 비용·정정 비용 비교](../COSTS.md)
