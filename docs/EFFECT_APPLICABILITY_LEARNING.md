# 조건별 과학효과 이력과 학습

## 기록 단위

`effect_history.collect`가 H의 `effect_apps`, ARIZ Part5를 포함한 raw idea의 catalog binding, 통합 `source_details`와 leaf ID, 후보 출처를 같은 `EffectApplication`으로 수집한다. 각 기록은 소유자/프로젝트/run/semantic episode, 카탈로그·출처 해시, 작동 기구, 요구 기능, 조건 ID, 원안·작업·후보 버전 및 당시 후보 snapshot을 갖는다. 존재하지 않는 효과 ID를 유사한 이름의 카탈로그 항목으로 대체하지 않는다. 카탈로그 밖의 제안은 별도 가설이다.

S6, S7(탈락안 제거 전), S8 게이트 결과를 기존 판정의 약한 관측으로 남긴다. 결합 후보의 전체 성공을 각 효과의 독립 성공으로 복제하지 않는다. 자동 게이트의 `PASS`는 현장 실증 라벨이 아니다.

`EffectSelection`은 lexical 순서, 노출 후보, 이력 보정·모델 점수·모델 버전·선정 방법을 별도로 기록한다. 노출은 사용과 다르며 실제 사용은 application에서 확인한다. 미선택은 negative가 아니고 존재하지 않는 선택 확률을 채우지 않는다.

## 기존 보류 요청 호환

기존 입력은 그대로 유효하다.

```json
{"decisions":{"C1":"accept","C2":"drop"}}
```

새 보류 응답의 `effect_applications`가 소유자가 확인할 수 있는 application/condition ID를 제공한다. 선택 확장은 다음 형식이다.

```json
{
  "decisions":{"C1":"accept"},
  "application_reviews":[{
    "candidate_id":"C1",
    "effect_application_id":"eapp-실제응답ID",
    "condition_id":"condition-실제응답ID",
    "decision":"condition_confirmed",
    "reason_code":"resource_available",
    "value":null,"unit":null,
    "comment":"사용자 확인 내용",
    "evidence_refs":[],
    "training_consent":"NO_TRAINING"
  }]
}
```

`condition_confirmed`, `condition_rejected`, `economics_rejected`, `unknown`을 지원한다. 서버는 현재 소유 실행·후보 버전·application·condition을 확인한다. 모든 보류 후보를 유지/제외해야 하는 기존 계약과 stale interrupt 검사는 유지한다.

| 입력 | 의미/후속 동작 | 학습 |
|---|---|---|
| accept | CONDITIONAL 유지 | 선호/채택 관측만, 기술 성공 아님 |
| drop | 원본 snapshot 보존 후 제외 | 과학효과 실패 아님 |
| condition_confirmed | USER_REPORTED, 변경 후보 S7 재검토 | 명시 동의 시 조건 적합성 proxy |
| condition_rejected | 그 적용·조건에 대한 부적합, 변경 후보 재검토 | 명시 동의 시 조건 부적합 proxy |
| economics_rejected | 경제성/채택 차원 | 물리 부적합 학습 제외 |
| unknown/미응답 | 미확인 유지 | negative 생성 안 함 |

확인된 한 조건으로 후보 전체를 PASS로 올리지 않는다. 조건을 반영한 delta 재검토는 기존 S7 handler를 사용하며 새 HITL 관문을 만들지 않는다. 원래 제약은 수정하지 않는다. 사용자 답변을 먼저 idempotent하게 기록하고 재검토 중 공급자 중단 시 pending 응답을 재사용한다. 동일 origin 답변·관측은 다시 학습 보상이 되지 않는다.

## 동의·정정·삭제

동의 기본값은 `NO_TRAINING`. 자동 검토와 legacy accept/drop에서 동의를 추정하지 않는다. `PROJECT_ONLY` 관측만 해당 소유자의 기존 프로젝트 범위 안에서 조회/학습한다. 별도 조직 공용 모델을 만들지 않았다.

`GET /api/runs/{run_id}/ax/effect-reviews`로 소유자의 관측 ID를 읽고, `POST .../effect-reviews/revisions`로 `event_id`, `expected_epoch`, `snapshot_id`, `supersedes_event_id`, `training_consent`, `reason` 및 선택적 `judgment`를 보낸다. 정정/철회는 append-only다. 과거 후보가 현재 목록에서 제외되어도 당시 application snapshot에 연결된다. 다른 사용자의 run 또는 임의 condition은 허용하지 않는다.

철회·정정·삭제된 run의 관측은 dataset/이력 및 다음 실행의 모델 적격성에서 제외한다. 이미 학습한 weight의 자동 소거를 주장하지 않는다. 영향받은 모델은 신규 run에 로드되지 않으며 재학습이 필요하다.

## 검색과 별도 ranker

전체 카탈로그의 기존 어휘 검색·기능별 후보 조합을 유지한다. 문제 구조에는 기능, 모순 양측, 상호작용, 자원, 운전 관련 제약을 포함한다. NFKC/공백/대소문자와 명확한 단일 수치의 W/kW, m/cm/mm, C/K를 결정적으로 정규화한다. 범위·자유문장·미상 단위는 추정하지 않는다.

기본 이력 보정은 같은 구조·조건의 다른 실행에 한정된다. 한 실행의 반복 리뷰는 독립 사례로 늘리지 않으며 충돌하는 조건에는 보수적으로 부적합을 우선한다. 보정값은 `sum(labels)/(independent_runs+2)`이고 성공확률이 아니다. 최대 6개 lexical band 안에서만 순서를 바꾸어 기존 후보 노출을 보존한다. DEEP은 주석만 붙이고 순서를 바꾸지 않는다. 새 효과는 0 보정의 미관측 상태다.

별도 CPU ranker는 문제×효과 상호작용의 정규화 선형 모델이다. 적어도 16개 명시 조건 관측, train의 독립 문제군 4개·holdout 2개, 양/음 라벨을 요구한다. 최대 2,000개 표본을 문제군 단위로 유지한다. 운영 경로에서는 동의된 데이터만 사용하고 fixture/synthetic 표식을 제외한다. 학습 후 독립 holdout 기준을 통과하면 별도 shadow pointer만 저장한다. 추론은 학습된 효과와 호환 domain/자원/제약 지원 범위에 제한하고 불명확하거나 부적격이면 기본 검색으로 돌아간다.

예측 점수는 조건부 개념 검토 proxy다. 관련성 ground truth가 없는 자료로 ranking metric이나 반사실적 정책 가치·성공확률을 보고하지 않는다. 검토 가능한 이력·모델이 없으면 COLLECTING 상태에서도 기존 검색은 계속 작동한다.

## 워커와 확인

`EFFECT_REVIEW_CONFIRMED → outbox → worker.consume/tick → routing/effect dataset → readiness → CPU train → registry → shadow → 명시 운영자 canary → 다음 신규 bundle`로 이어진다. routing과 effect의 feature schema/checkpoint/pointer는 분리된다. 모델이 작업 도중 바뀌지 않는다.

격리 smoke: `python pilot/scripts/ax_offline_smoke.py`. 자동 LLM 검토·사용자 보고·실제 시험은 다른 근거 수준이다. 기존 AX Review API의 실제 시험 등록은 측정값·조건·자료·후보/의무를 요구하며 새 보류 UI의 단순 진술을 실증으로 바꾸지 않는다.
