# 수집 기준과 데이터 한계

[사례 개요](README.md)

추출 시각(UTC): `2026-09-29T23:10:18.093193+00:00`. 원본 run 상태 갱신 시각: `2026-09-29T22:58:30+00:00`. 읽기 전용 SELECT로 수집했고, 재추론·운영 데이터 수정·신규 유료 모델 호출은 하지 않았습니다.

## 출처와 선택 조건

| DB 테이블 / 필드 | 선택·사용 기준 |
|---|---|
| runs / run_states | 대상 run_id의 제목·모드·상태·최종 context 선택 필드. 전체 state는 게시하지 않음 |
| steps | 이번 node_start의 step_id 92개 + 상속 STP-ba943100. input_slice.vars·output_json·verdicts 전체 |
| run_events | 해당 run_id 및 event.id >=45932, 완료46304까지. 전체 353개 |
| ax_snapshots | epoch>=47 + 상속 S0 완료 snapshot. members를 그대로 연결 |
| ax_artifact_versions | epoch>=47 산출물 32개. 이전 입력 버전은 ID로 표시 |
| ax_tasks / ax_task_attempts | epoch>=47 task 95개. 요청·응답 전문 제외, fingerprint와 usage·정산 보존 |
| ax_decisions / ax_events | 같은 최신 구간만 선택 |
| feedback_logs | 이번 완료 시 제출된 8개 해결안 평점 |

`rag_docs`는 위 8개 피드백 중 실제 사례가 되는 6개 concept ID와 이번 작성 시각으로 한정해 추가 확인했습니다. 소유자 식별 필드를 서버에서 제외한 후 문서에 연결했습니다.

## 의미를 보존한 표시

시간대 없는 Step/event 시각은 동일 이벤트의 AX UTC 시각과 대조해 UTC로 읽고 본문에 KST(+09:00)로 표시했습니다. 원본 시각은 상세 값에 보존했습니다. 스냅샷·산출물의 content hash는 DB 원본 식별자입니다. 게시 파일의 SHA-256은 `manifest.json`에 별도로 기록했습니다.

JSON이 담긴 문자열은 가독성을 위해 내용을 펼쳤습니다. 같은 값은 해시별 Markdown 한 곳에 저장해 여러 Step에서 함께 링크합니다. 큰 배열·객체는 항목으로 나눴으며 항목 자체는 생략하지 않았습니다. 표의 짧은 미리보기와 전체 값 링크를 구분해 읽으면 됩니다.

## 재구성하지 않은 것

원본 전체 state, 계정·인증 정보, 정적 전체 지식 카탈로그, 과거 회차 Step 투영본, 반복된 system/user 프롬프트 전문, provider 원문과 보고서 전문은 제외했습니다. 실제 내부 helper의 독립 로그, 저장되지 않은 HTTP 응답 원문·외부 검색 원문, 중간 수정 응답을 새로 만들지 않았습니다. 검색 원시 hit 전체와 피드백 이후 학습·승격이 완료됐는지는 이 자료만으로 보장하지 않습니다.

`s0_bootstrap` input artifact의 본문은 이전 회차 자료라 중복 수집하지 않았습니다. 대신 해당 S0 Step의 실제 입출력과 마지막 완료 snapshot의 정확한 버전 ID를 제공합니다. `report_context` 안에 포함된 과거 전체 Step 목록도 이번 92개와 중복돼 본문에서 제외하고 원본 개수와 최신 Step ID만 남겼습니다.

## 비용 해석

최신 95 task의 actual 정산 합계는 `0.760452 USD`입니다. 모델 result_usage 합계는 `0.7604091 USD`, 최신 Step 비용 합계는 `0.7604095 USD`입니다. microUSD 단위 정산과 소수 반올림 차이를 보존했습니다. 누적 `7.611395 USD`에는 이전 회차가 들어갑니다. 이 한 사례로 비용·품질 개선을 주장하지 않습니다.

## 원본 context와 제출 피드백

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `context` | 객체 · updated_at, raw_query, domain, confirm, cost, workflow_version, epoch … | [전체 값](payloads/c4b30d46ec527ac620e7ac8e.md) |
| `feedback_logs` | 배열 8개 | [펼쳐 보기](#field-8eba5907ae14c460) |
| `scope` | 객체 · run_id, epoch_range, start_event_id, inherited_s0_step, exclusions, redacted_keys | [펼쳐 보기](#field-88af333ff8e6c6ee) |

<a id="field-8eba5907ae14c460"></a>

<details>
<summary>feedback_logs · 전체 값</summary>

```json
[
  {
    "id": 163,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-099405e4edc0a658",
    "rating": 5,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 164,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-32d46b742a89c1c2",
    "rating": 5,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 165,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-b6dfcbd4dd9d8841",
    "rating": 4,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 166,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-d2c3056109ec002a",
    "rating": 5,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 167,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-ac128a6d03303a81",
    "rating": 5,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 168,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-783786b342651a96",
    "rating": 3,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 169,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-33d3b8f2d4fa57e5",
    "rating": 3,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  },
  {
    "id": 170,
    "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
    "concept_id": "CPT-S6-de9b1cabaf6dacce",
    "rating": 2,
    "adopted": null,
    "reason_tags": [],
    "comment": "",
    "created_at": "2026-09-29T22:58:13+00:00"
  }
]
```

</details>

<a id="field-88af333ff8e6c6ee"></a>

<details>
<summary>scope · 전체 값</summary>

```json
{
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "epoch_range": [
    47,
    52
  ],
  "start_event_id": 45932,
  "inherited_s0_step": "STP-ba943100",
  "exclusions": [
    "account identifiers and credentials",
    "whole run state",
    "older-episode payloads",
    "static bundle/catalogues",
    "rendered system/user prompt duplicates",
    "provider response bodies",
    "rendered report duplicate",
    "report_context nested historical step projection"
  ],
  "redacted_keys": {}
}
```

</details>
