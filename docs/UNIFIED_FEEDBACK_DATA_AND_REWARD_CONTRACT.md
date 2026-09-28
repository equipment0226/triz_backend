# 통합 평가·적응형 탐색 계약

신규 실행은 `ax-run-v3` / `triz-modes-v3-adaptive-feedback`를 고정한다.
저장된 `ax-run-v2`와 legacy 실행은 원래 계약으로 재개한다. 모델 설정·가격·프롬프트·카탈로그·보상 상수는 실행 bundle에 고정된다.

## 모드와 실행

| 모드 | 허용 기법 | 필수 범위 | 기본 초기 폭 | 생성 한도(µUSD) |
|---|---|---|---|---|
| LITE | A/B/E/H | 사용자가 명시한 허용 기법 | 1 | 600,000 |
| FULL | A/B/C/E/F/G/H | 사용자가 명시한 허용 기법 | 2 | 1,200,000 |
| DEEP | 등록 A~H | 적용 가능한 전체, ARIZ 포함 | 전체 | 기존 전체 실행 예산 |

최소 폭은 적용 가능한 집합에 한정한다. 선행 입력 부족은 적용 불가와 다르다.
`NOT_SELECTED_BY_POLICY`, `NOT_RUN_BUDGET`, `BLOCKED_MISSING_INPUT`, `FAILED`, `NOT_APPLICABLE`를 구분한다.
Q는 governor가 허용한 ticket에서만 선택한다. 적격 정책·상태 지원이 없으면 저장된 비용 추정과 명시적 종료 규칙으로 fallback한다.
최소 폭 이후 merge가 추가 탐색 불필요를 보고하면 규칙은 STOP을 우선한다. 검토에서 실제 gap이 발견되면 제한된 후속 기법/수리를 선택할 수 있다.
STOP은 탐색 phase의 종료이며 성공이나 episode terminal을 뜻하지 않는다. S6 독립 검토, S7 제약 검토, S8 평가, 보고서가 계속된다.
보고서 snapshot 이후의 실제 종료 이벤트가 episode를 닫는다. 늦은 피드백은 보상 revision이다.

## 공통 평가

`ax_events.COMMON_EVALUATION`과 기존 outbox를 같은 트랜잭션에 쓴다.
S6 독립 검토·구조적 의무 확인, S7 실제 제약 검토·명시적 keep/drop, S8 역할별 점수,
S10 최종 평가와 기존 시험 결과 제출을 어댑터로 연결한다.
무제약 자동 PASS, 응답 없음, 기본 adopted=false는 긍정 관측이 아니다.

각 기록은 run/owner/project/episode, 후보 버전과 snapshot, source step/event,
원안 leaf/action/merge/effect application, 검토자·rubric·실제 응답, 차원·값·mask,
발생/라벨 사용 가능 시각, 동의 범위, synthetic provenance를 보존한다.
계보를 찾지 못하면 `UNKNOWN_ATTRIBUTION`; 제목으로 ID를 추측하지 않는다.
drop은 삭제 전에 후보와 계보를 기록한다. ID는 표시 이름 변환과 별도로 저장한다.

keep=+0.10, drop=-0.10은 효용 설계 상수이다. 조건부 판정·미확인 효과 조건을 변경하지 않는다.
명시적 1~5점만 `(rating-3)/2`로 정규화한다. 0·누락·기본값은 None/masked이다.
명시적 adopted 응답은 `adopted_explicit=true`일 때만 관측이다.
시험 자료는 `USER_REPORTED_TEST_NOT_INDEPENDENTLY_VALIDATED`; 물리적 진실로 자동 승격하지 않는다.

## 두 학습 과제

| 과제 | feature/target | 입력과 출력 |
|---|---|---|
| 실행전략 Q | `ax-state-action-v4` / `candidate-utility-cost-v2` | 실제 decision 시점 특징·legal mask·후속 decision, 정산 비용과 최종 outcome |
| 효과 우선순위 | `effect-application-utility-v2` | 선택 전 문맥·카탈로그 snapshot → 후보 적용안의 공동 대리 효용 |

고유 기구 단위에서 평가를 합친다. 같은 차원·검토자의 최신 관측을 사용하며 서로 다른 검토자의 충돌은 보존한다.
기술 proxy는 실제 관련 차원들의 보수적 최소값, 효용은 keep보다 명시적 최종 피드백 우선이다.
후보 복제로 총량을 늘리지 않고 기구별 평균을 사용한다. 현재 후보군에서 제외된 기구에 양의 품질을 부여하지 않는다.
구조적 완결성은 물리적 검증과 별도 근거 수준이다.

`outcome = clamp(0.7 * quality + 0.3 * utility, -1, 1)`이며 없는 차원은 mask를 유지한다.
각 실제 전이에 `-lambda_cost * settled_cost / pinned_budget`를 한 번 적용하고,
최종 outcome은 terminal에만 한 번 더한다. 상수는 설정값이며 경험적 최적값이 아니다.
사용량 UNKNOWN·미정산·cutoff 이후 정산은 해당 학습 표본을 제외한다. 물리적 task ID로 비용을 중복 제거한다.
새 피드백/정산에 따라 reward revision hash를 바꾸고 이전 revision과 함께 독립 표본으로 학습하지 않는다.

효과는 최종 후보의 명시적 `active_effect_ids`와 저장된 leaf/application이 일치할 때만 귀속한다.
검색 노출·제거된 효과·outside-catalog 가설에는 긍정 표본을 만들지 않는다.
여러 효과에 귀속하면 각 weight는 `1 / unique_active_effect_count`; 총량은 1이다.
검색 후 후보점수·사용자 답변은 선택 전 특징에 넣지 않는다. 효과 점수는 성공 확률이나 과학 법칙 판정이 아니다.

문제군 전체를 시간 holdout으로 분리한다. 명시적 문제군이 없으면 기록된 문제 구조를 보수적으로 묶는다.
Q 지원 수는 train의 독립 문제군 수이며 holdout/synthetic으로 채우지 않는다.
propensity가 없으므로 IPS/DR이나 실행하지 않은 대안의 성과를 계산하지 않는다.

## 동의·정정·권한

2026-09-28 후속 요청에 따라 신규 분석의 기본값은 `PROJECT_ONLY`이다. 선택 체크박스를 제거하고
최초 입력 화면에 기본 반영 안내를 표시한다. keep/drop/최종 피드백은 저장된 프로젝트 설정을 이어받는다.
기본 적용은 `project-default-v1`로 기록하여 사용자의 명시적 동의 기록과 구분한다.
명시적 `NO_TRAINING` 요청·기존 미동의 기록·철회는 그대로 존중하며 소급 변경하지 않는다.
project_id가 없으면 user_id를 프로젝트 범위로 사용한다. 다른 계정이나 회사 전체로 확장하지 않는다.
미동의 상태에서도 분석·피드백·보고서는 동작한다. 과거 미동의 자동 검토를 나중 동의로 소급 학습하지 않는다.

소유자 `GET /api/runs/{run}/ax/evaluations`로 원천 기록을 조회하고,
`POST /api/runs/{run}/evaluations/{event}/revision`에 동의 범위·이유·선택적 정정값을 보내 새 revision을 기록한다.
기존 이벤트/보고서는 덮어쓰지 않는다. 철회는 dataset과 active/shadow 모델의 적격성에 즉시 반영한다.
paid-call 경계에서 고정 모델/참조 사례의 동의를 다시 확인한다. 철회된 고정 입력은 추가 호출을 막고 새 분석의 fallback으로 안내한다.

## 큐·캐시·migration

기존 events/outbox에 추가하고 `ax_learning_task_queue`를 additive 생성한다.
scope는 tenant/project/task/schema이며 task별 revision을 독립적으로 완료한다. 한 task의 실패가 다른 task를 완료 처리하지 않는다.
신규 공통 이벤트는 구형 v1/v2/v3 학습 branch로 보내지 않는다. 신규 Q와 효과 checkpoint는 task별 pointer를 사용한다.
구 checkpoint의 shape만 같아도 신규 계약에서 자동 활성화하지 않는다. shadow/제한 적용은 기존 승인 기준을 유지한다.

대표안 입력·모델·rubric·제약·근거·추가 지시가 같은 경우 완료한 구체화/검토를 재사용한다.
변경된 대표안만 다시 구체화하고 S7도 변경 후보만 호출한다. 실패/불완전 검토는 성공 cache로 재사용하지 않는다.
branch.persist는 부모 portfolio를 저장한다. 의미 변경은 새 episode, 전송 재시도/보고서 열람/UNKNOWN 복구는 새 탐색이 아니다.
기존 UNKNOWN 1회 명시 승인, 원 예약 유지, 2차 UNKNOWN 차단을 보존한다.

## 향후 배포·복구 순서 (이번 작업에서 실행하지 않음)

1. 운영 DB 백업 후 신규 backend를 먼저 배포하여 additive 테이블·v3 reader/runner를 제공한다.
2. 상세 조건 입력을 제거한 frontend를 배포한다. 구형 실행의 keep/drop와 frozen 보고서 호환을 확인한다.
3. owner diagnostics에서 실제 readiness를 확인한다. 데이터 부족은 정상적인 COLLECTING/fallback이다.
4. 정책 적용은 별도의 shadow 관측/명시적 승인 후 제한 적용한다. 테스트 fixture를 승인 근거로 사용하지 않는다.
5. 문제가 있으면 신규 생성 기본값을 ax-run-v2로 낮추고 신규 학습 pointer 적용을 중단한다.
   진행 중 v3를 읽지 못하는 구 binary로 되돌리거나 원장을 삭제하지 않는다. v3 호환 runner와 frozen 자료를 유지한다.

읽기 전용 진단은 인증된 소유자의 `GET /api/runs/{run}/ax/diagnostics`이다.
실제 운영 데이터 진단·학습·활성화·배포·유료 호출은 이번 작업에서 수행하지 않았다.

## 논문 1.6 정합성 메모

빠른/표준은 기본 목록 전체 수행 후 추가 작업만 Q로 선택하는 구조에서 허용 집합 내 초기·후속 선택 구조로 바뀐다.
심층은 전 기법 범위를 유지한다. 공통 실제 평가와 정산 비용은 실행전략 Q와 별도 효과 우선순위 모델에 사용한다.
자동 검토는 proxy, keep는 약한 사용자 효용이며 물리적 타당성 검증이 아니다.
아래 테스트 비용은 연결 검증이다. 실서비스 품질/비용 개선과 CQL 논문의 보장은 별도 실험 없이 주장하지 않는다.
