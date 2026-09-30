# 5. 시스템·기능·자원·인과 분석

[전체 실제 흐름](../README.md)

호출자: [`nodes.s3_analyze()`](https://github.com/equipment0226/triz_backend/blob/5ce8ec233b3d58d2005530a4e9b3113f5fc235f2/pilot/triz/nodes.py#L225). 함수별 실제 입력·출력은 아래 Step 기록에 연결했습니다.

| 실행 구간 시작 KST | 시작 event | 완료 event | 중단 event |
|---|---|---|---|
| 2026-09-30 12:59:01 | 46333 | 46356 | — |

```mermaid
flowchart TD
    I["저장 입력 snapshot / Step Input"] --> S["s3_analyze"]
    S --> P0["s3_nine_windows · 1 Step"]
    P0 --> O["최종 snapshot / Step Output"]
    S --> P1["s3_function_model · 1 Step"]
    P1 --> O["최종 snapshot / Step Output"]
    S --> P2["s3_sufield · 1 Step"]
    P2 --> O["최종 snapshot / Step Output"]
    S --> P3["s3_resources · 1 Step"]
    P3 --> O["최종 snapshot / Step Output"]
    S --> P4["s3_ceca · 1 Step"]
    P4 --> O["최종 snapshot / Step Output"]
    S --> P5["s3_constraints · 1 Step"]
    P5 --> O["최종 snapshot / Step Output"]
```

화살표는 기록의 입력·처리·출력 관계입니다. 하위 Step 사이의 순차·병렬 실행을 새로 추정하지 않습니다. 시작 순서는 아래 표와 이벤트 원장을 따릅니다.

## 최종 Input · 마지막 재개에서 읽은 버전

| 입력 snapshot | 전체 입력 버전 |
|---|---|
| snap-34e7956f50d143cabd2ac774fe607f25 | [읽기](../snapshots/snap-34e7956f50d143cabd2ac774fe607f25.md) |

## 최종 Output · 완료 시점

[완료 snapshot](../snapshots/snap-598fb131ae484180abf1e4ae394d3457.md) · epoch 55 · 2026-09-30 13:01:37 KST

| 산출물 | 버전 ID | 전체 Output |
|---|---|---|
| problem | av-d52c84a3bfe447e0b85db367ed3459fa | [읽기](../artifacts/problem-av-d52c84a3bfe447e0b85db367ed3459fa.md) |
| analysis | av-72242c38d08e49739ffe9b62eb5affca | [읽기](../artifacts/analysis-av-72242c38d08e49739ffe9b62eb5affca.md) |

## 하위 process · 실제 시작 순서

| seq / step_id | node · 전체 Input/Output | Agent / Prompt | 상태 / 판정 | USD |
|---|---|---|---|---|
| 734 / STP-33dced34 | [s3_nine_windows](../processes/0734-STP-33dced34.md) | system_analyst / P_S3_NINE_WINDOWS | OK / PASS | 0.0038766 |
| 735 / STP-e066ffae | [s3_function_model](../processes/0735-STP-e066ffae.md) | system_analyst / P_S3_FUNCTION_MODEL | OK / PASS | 0.0218793 |
| 736 / STP-09f7535e | [s3_sufield](../processes/0736-STP-09f7535e.md) | sufield_specialist / P_S3_SUFIELD | WARN / UNVERIFIED | 0.0027756 |
| 737 / STP-83596e18 | [s3_resources](../processes/0737-STP-83596e18.md) | resource_analyst / P_S3_RESOURCES | WARN / UNVERIFIED | 0.0056019 |
| 738 / STP-13f959e1 | [s3_ceca](../processes/0738-STP-13f959e1.md) | root_cause_analyst / P_S3_CECA | OK / PASS | 0.0090561 |
| 739 / STP-9013f39e | [s3_constraints](../processes/0739-STP-9013f39e.md) | constraint_analyst / P_S3_CONSTRAINTS | OK / PASS | 0.0065646 |

## 모델 호출과 비용

이번 Stage 구간에 생성된 task는 10개입니다. 실행 당시 actual 합계는 0.049758 USD, 비용정정 반영 합계는 0.022021 USD입니다. 예약액 reserve는 소비액이 아닙니다. Step와 task 사이의 직접 외래키가 없어 병렬 호출을 시간만으로 특정 Step에 붙이지 않았습니다.

[task·usage·가격 근거](../CALLS.md) · [시작·중단·재개 이벤트](../EVENTS.md)

`_pick_tcs`, `_add_ideas`, 집계·해시와 같이 독립 Step이 없는 helper의 중간값은 재구성하지 않았습니다. 호출자의 실제 전달 변수, 최종 Output, 저장 산출물로 확인할 수 있는 범위만 담았습니다.
