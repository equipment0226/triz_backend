# F1–F5 targeted fixes

Baseline: backend `3f5be6c847fee00c4b9a5a2ca536a4f201673d1f`, frontend `32c71d70059296fabd0305fb003ed49fd0491467`. Existing release worktrees were clean. No reset, deployment, production writes or paid provider calls are part of this change.

## Before implementation

| Defect | Production path | Baseline finding | Failing regression | Minimal correction | Regression boundary |
|---|---|---|---|---|---|
| F1 | incremental_review.generate, quality.audit_concepts, learning_outcomes.outcome | old candidate takes precedence over new cache; empty all can mark review complete | current_revision tests | versioned exact-input review projection and explicit disposition completeness | interrupted portfolio, audit history, cutoff, frozen report |
| F2 | nodes.s7_gate, adaptive_tracks.followup, coherence_recovery.targets | automatic FAIL shares user-drop list and prevents followup | candidate_disposition tests | typed design disposition, preserve exclusion lineage and evaluate automatic-failure alternatives | keep/drop idempotency, modes, recovery limits |
| F3 | adaptive_tracks.state_features, routing_q.phi and schema consumers | confirmed constraints/resources absent from phi | confirmed_context tests | additive pinned feature schema with canonical semantic interactions | old pinned schemas, immutable decisions, support and backup |
| F4 | adaptive_tracks.estimate/run, action_runtime, ledger | call median differs from logical execution total; pending action checked after estimates | execution_cost tests | scoped settled unique-task execution aggregation and explicit prior | UNKNOWN, retries, scope, shared review reserve |
| F5 | effect_ranker.train/evaluate/train_project, registry | MSE < 1 admits model worse than zero on small utilities | baseline_gate tests | weighted baselines, explicit support and versioned pure eligibility | legacy pinned model, task pointers, synthetic exclusion |

These are code inspection findings. Executed failing/passing results and acceptance coverage will be recorded separately; no production quality or cost improvement is inferred.

## 구현 계약

- **F1 — `current-review-projection-v2`**: 대표안의 실제 입력과 공통 검토 문맥으로 캐시를 식별한다. 변경된 입력은 먼저 현재 승인을 UNVERIFIED로 전환하고 원래 포트폴리오를 저장한다. 완료된 새 검토 객체를 현재 후보로 구성하며, 빈 concepts/excluded는 완료가 아니다. 같은 입력은 완료 캐시를 재사용한다. 과거 캐시 입력으로 되돌아가는 경우에도 현재 revision을 기록하고 기존 provider/audit 캐시를 재사용한다. 공통 평가 기록에는 입력 hash와 revision이 붙고, 현재 outcome은 해당 revision의 구조 검토 완료까지 확인한다. 다른 revision의 과거 품질 판정은 현재 최솟값에 섞지 않는다. 동일 설계에 대한 keep 효용은 별도로 유지하지만 새 REJECT를 뒤집지 않는다. 보고서 후보 artifact 및 report context에도 review/disposition sidecar가 고정된다.
- **F2 — `candidate_dispositions`**: USER_DROP, CONSTRAINT_FAIL, QUALITY_REJECT, LEGACY_UNKNOWN_ORIGIN을 구분한다. 삭제 전에 설계 fingerprint, 원안, 효과, 실제 action, 사유, snapshot, episode를 저장한다. 제목·raw ID 변경으로 같은 제외 설계를 우회할 수 없다. 후속 작업은 현재 gate 후보군과 episode를 기준으로 판단하므로 과거 실패 이력과 현재 전체 사용자 거절을 혼동하지 않는다. 구형 기록은 저장된 gate 결정·공통 사용자 이벤트·제약 실패에서만 출처를 복원한다. 자동 탈락의 다른 접근은 실제 proposals/governor 및 독립·제약 검토를 거친다.
- **F3 — `ax-state-action-v5` / `confirmed-context-v1`**: 현재 확정 문제 설명, 기능, 모순의 양측, 자원, 제약, 적용 환경을 분해한 토큰을 실제 phi의 행동별 상호작용에 넣는다. 도메인도 포함한다. source ID와 snapshot은 provenance이며 예측 토큰이 아니다. 명확한 단위만 변환하고 순서·공백을 정규화한다. 최대 512개 토큰/토큰당 512자로 제한하며 hard·금지 제약을 우선하고 생략·문자 절단 수를 기록한다. 기존 v3/v4 phi와 고정 정책은 유지한다. 새 run만 v5를 pin하고 데이터셋/worker/registry/diagnostics까지 전달한다. 과거 decision은 당시 저장 특징을 그대로 사용하며 최신 상태로 backfill하지 않는다.
- **F4 — `track-execution-cost-v2`**: 같은 scope에서 최근 제한된 실행 집합(최대 64 runs, run당 각 조회 최대 10,000행)을 조회하고 한 의사결정의 트랙 제안들이 결과를 공유한다. 실제 RUN_TRACK 단독 실행과 GENERATE_BASELINE을 포함한 부모·자식 실행을 모두 처리한다. 한 논리적 트랙의 고유 task.actual을 합산하며 attempt 로그를 다시 더하지 않는다. 호출 ID 계보, 완료 상태, 정산 cutoff, 모델·가격·prompt/node 계약, 입력 크기 bucket을 확인한다. UNKNOWN/부분/귀속 불명/합성/권한 없음/철회/미래 정산/무과금 재사용은 신규 유료 생성 평균에 섞지 않는다. 표본과 cutoff는 ticket에 저장한다. 신규 메타데이터는 결제 idempotency hash에서 제외하여 기존 유료 호출의 재사용을 유지한다.
- **F5 — `utility-weighted-baselines-v1`**: train/eval 모두 sample_weight 기준 WMSE를 사용한다. 미관측 라벨은 제외하고 실제 0은 유지하며 잘못된 weight/label/prediction은 거절한다. train에서 고정한 가중 평균과 ZERO를 동일 행·가중치의 기준선으로 사용한다. 지원된 예측 0과 미지원 fallback 0을 구분한다. pure eligibility는 기존 readiness, 유효 모델, supported 2개 이상/독립 문제군 2개 이상/가중 지원 비율 0.5 이상, supported의 강한 기준선 대비 절대 개선 `>1e-12`, 전체 fallback의 강한 기준선 대비 악화 없음(tolerance `1e-14`)을 요구한다. 이는 초기 명시 정책이며 운영 자료에서 추정한 임계값이 아니다. ranking은 `not_evaluated`다. shadow·승격·신규 run load가 같은 계약과 gate 결과를 검사하며 effect/Q pointer를 혼용하지 않는다. 이미 고정된 과거 모델/보고서는 소급 변경하지 않는다.

## 비용 추정의 범위

격리 원장 예제에서 A의 고유 task 5개 × 100,000 microUSD = 500,000 microUSD, H의 task 1개 = 200,000 microUSD다. 관측 수는 각각 1이며 원장 합계는 700,000 microUSD다. 중복 부모/자식 이벤트나 attempt 로그를 추가해도 이 합계는 늘지 않는다.

관측이 없으면 실제 pinned 모델의 가격과 node token cap, 대상 모순 수, provider attempt cap 및 agent repair cap으로 명시적인 prior를 만든다. UTF-8 크기는 입력 토큰 수가 아닌 proxy다. 공유 merge·필수 후속 검토는 기존 별도 reserve를 사용한다. prior는 보장 상한이 아니며 원자적 gateway 예약·정산을 대체하지 않는다. 운영 데이터의 과거 실행에 새 비교/호출 계보가 없으면 관측 표본으로 추정해 복원하지 않는다.

## 보존 및 미실시

13단계 REST/MCP/n8n envelope, DEEP 전 트랙, LITE/FULL 허용 집합·ARIZ 제한, 필수 검토, 보상 가중치·약한 keep/drop, 최대 대표안 10개와 원안 계보를 변경하지 않았다. 최신 `project-default-v1`과 명시 NO_TRAINING·철회를 유지한다. 프런트 소스 변경은 없다. 최근 표시 문구·코드 노출 방지·모바일 장별 페이지·분석 현황 카드 제거도 유지한다.

구현과 오프라인 검증 후 사용자의 별도 지시로 커밋·push·백엔드 배포를 진행한다. 운영 DB의 수동 수정, 운영 학습 정책의 수동 활성화, 외부 유료 LLM 호출은 수행하지 않는다. 이 패치는 오프라인 정확성과 연결을 검증한다. 실제 프로젝트의 새 계약 표본이 충분한지, 운영 holdout에서 기준선을 개선하는지, 필수 검토 품질을 유지하면서 실제 총비용이 감소하는지는 별도 운영 승인과 실측이 필요하다. 확인되지 않은 학습 효과나 절감률을 주장하지 않는다.
