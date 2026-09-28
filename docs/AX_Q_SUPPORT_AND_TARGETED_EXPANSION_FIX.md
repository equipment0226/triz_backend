# Q 지원 조건과 목표 기반 추가 탐색 패치

## 범위와 보존 기준

기준 요청: `TRIZ_PATCH_3_2_3_3_CODE_PROMPT.md`. 실제 수정 시작 기준은 최신 로컬
`da02899`이며 이전 `ad0eb24`의 ARIZ 복구와 최신 S5 체크포인트/UNKNOWN 보호를 보존한다.
구현 대상은 routing Q 지원·backup·metadata 및 A/G/H 추가 탐색의 목표 전달이다.
13단계, 모드별 필수 트랙, 최대 10개 대표안과 전체 원안 보존, 독립 검토,
보고서, 비용 상한, 동의·승인 정책은 유지한다. 효과 ranker 조건별 라벨, RAG,
새 학습 알고리즘, 운영 배포 및 유료 호출은 범위 밖이다.

## 수정 전 재현

`test_q01_nonterminal_regional_support_matches_online`: 실제 choose는 B를 고르지만,
evaluate가 지역 지원 없는 C의 Q=10을 사용하여 target=8, MSE=62.41을 산출했다.
기대 target=.16, MSE=.0036 테스트가 실패했다.

`test_e01_real_h_provider_receives_target_before_cache`: 실제 H handler, agent,
gateway를 사용하고 최하위 llm.chat_json만 가짜 응답과 usage로 교체했다.
기본 요청 뒤 목표를 전달한 추가 요청이 기존 cache를 사용하여 provider 호출이
기대 2회 대신 1회인 것으로 실패했다.

## 지원 판정과 backup

`routing_q.supported_action_indices`는 당시 legal mask와 고정된 train 관측 통계만
사용한다. action support와 mode/domain/phase 지역 support 모두 4 이상이어야 한다.
설정은 `SUPPORT_SETTINGS` 한 곳에 있다. holdout 관측은 support 생성에서 거절한다.
중복/음수/범위 밖 index, 비정상 count, schema/계약/유한 score를 확인한다.
LITE/FULL ARIZ 및 DEEP optional 금지는 높은 지원값으로 우회하지 못한다.
동일 작업의 복제 티켓은 독립 대안으로 세지 않으며 목표가 다른 작업은 구별한다.

`choose`와 `next_state_backup`은 같은 지원 집합과 낮은 index 우선 동점 규칙을
사용한다. `train`은 target weights, `evaluate`는 평가 모델 weights를 backup에
전달하며 지원 통계는 두 경우 모두 train에서 고정한 값이다.

| 상태 | Backup |
|---|---|
| 명시적 terminal | 0, 따라서 y=r |
| 독립 supported 대안 2개 이상 | 해당 집합의 최대 Q |
| 2개 미만이며 기록된 rule preferred가 supported | 그 행동 하나의 Q |
| legal 행동 하나이며 supported | 강제 행동 하나의 Q |
| unsupported/missing rule, 불완전 전이 | 값 None, TD/evaluation 제외 사유 기록 |

지원 부족을 terminal이나 0 bootstrap으로 바꾸지 않는다. 관측으로 적격이지만
전이가 불완전한 데이터는 `td_exclusion_reason`과 함께 남긴다. 학습 가능한 행이
없으면 COLLECTING이며 readiness의 최소 표본/문제군/동의 조건은 낮추지 않는다.
한 문제군만 있으면 독립 평가 집합을 만들 수 없으므로 train 관측으로 보존하고
readiness는 계속 실패한다. 기존 기준의 독립 holdout 요구는 유지한다.

CQL 정규화는 지원 여부와 별개로 A_legal 전체를 사용한다. 관측이 부족한 합법
행동의 과대 Q도 억제해야 하기 때문이다. 선형 phi 512차원, target 갱신 주기,
discount/alpha/reward 의미는 유지한다. 데이터는 next decision의 **전체 후보 목록**,
next_permitted, next_rule_preferred, action instance IDs, 선택 모드, episode를 저장한다.
필터링에 따른 ordinal index 이동이 없으며 현재 live state로 과거 mask를 복원하지 않는다.

train/evaluate는 전체 표본·TD 사용 수·제외 이유·action/state coverage·backup 상태
빈도를 기록한다. `bellman_mse`의 비교 기준은 같은 행과 같은 고정 target에 대한
0 예측 오차인 `zero_prediction_same_target_mse`로 명명했다. 이전 reward² 기준과
섞어 비교하지 않는다. 빈 평가 MSE는 None이며 승인되지 않는다.

## 목표 문맥 전달과 캐시

호출 경로는 `_expand_instances` → `exploration_context.build` → 선택한
ticket.parameters → `action_runtime.executing`의 ContextVar → `copy_context`
worker → `_pick_tcs` / `_required_functions` → `agent.run_agent` → gateway/ledger다.
부모 solve 초기화 전에 미대응 모순 양측, 핵심 제약, 기존 원안/leaf 출처·기구·조건,
미해결 검토 가설을 고정한다. 최대 16개, 24KB의 관련 기구 digest를 사용하며 모순
양측과 핵심 제약은 자르지 않는다. 원본 재고는 그대로 유지한다.

현재 schema에는 모순과 function edge의 exact 매핑이 없다. 이 부재를 명시하고
개선측·보호측을 검색 단서로 사용한다. H는 기존 후보 검색·이력 재정렬을 그대로
사용하며 같은 효과의 새로운 적용을 금지하지 않는다. G는 목표 기능과 이전 방식의
미검증 한계를 받는다. A는 대상 TC 또는 기록된 PC 부모만 사용하고 사용자 선택을
지킨다. 행렬 값은 바꾸지 않는다. foreign/stale 목표는 거절하며 전체 문제로 되돌리지 않는다.

중앙 suffix는 P_S5_TRACK_A/G/H와 P_S5_MATRIX_FALLBACK allowlist에만 cache key
계산 전에 붙는다. baseline, merge, 독립 verifier, S7/S8에는 추가 지시문을 붙이지 않는다.
정확한 payload, semantic_context_hash, exploration_contract, prompt_hash 및 실제
system/user payload hash를 step.input_slice에 보존하고 작업 결과에도 semantic hash를 남긴다.
Q 점수·순위·성공확률은 생성 지시문에 포함하지 않는다.

같은 의미의 재시도는 run-local cache와 durable ledger 결과를 재사용한다. 신규
목표·조건·기구·미해결 이유는 의미 hash를 바꾼다. targeted ledger identity에서는
실제 요청과 frozen intent, run/tenant/project/episode를 유지하고 audit identity,
attempt, transport epoch의 차이는 제거한다. UNKNOWN은 같은 예약으로 계속 막힌다.
새 raw ID는 targeted context와 실제 출력으로 결정하여 재시도 중복 append를 막는다.
기존 통합이 전 원안을 비교하고 대표 최대 10개와 개별 deferred 사유·출처·조건을 유지한다.
새 출력이 없으면 NO_NEW_INFORMATION과 no_application_reason을 남긴다. 해결 상태를
자동 승격하거나 quota를 채우지 않는다. optional branch 저장은 부모 체크포인트를
경유하여 완료된 기본 트랙 재고를 덮어쓰지 않는다.

## 버전과 호환

dataset/checkpoint/new run bundle에 `action-region-support-v1`,
`supported-rule-backup-v1`, `triz-targeted-expansion-v1`을 고정한다. 신규 정책 로드와
shadow/canary 승격은 shape뿐 아니라 세 의미 계약을 검사한다. 메타데이터가 없는
이전 artifact는 읽을 수 있지만 자동 승격되지 않는다. 직접 주어진 unversioned
오프라인 표본은 기존 함수 호출 호환을 위해 계산할 수 있어도 배포 근거로 승인되지 않는다.
이미 pinned된 run은 `choose_legacy`와 기존 생성 경로를 사용한다. 계약이 없는
과거 decision은 신규 handler 의미의 데이터에 자동 합치지 않는다. API 필수 입력,
DB table/column/enum, 기존 동의·shadow·canary 승인 조건을 변경하지 않았다.

## 테스트 범위

`test_routing_q_support_contract.py`는 nonterminal 높은 미지원 Q, next region,
action/state 독립 지원, 모드 금지, 공통 train/eval mask, rule/forced/terminal,
불완전 전이 제외, 실제 immutable next decision index, 잘못된 mask/count/schema,
holdout 배제, CQL legal 집합, COLLECTING, 구 checkpoint 차단, 복제 작업을 검사한다.

`test_ax_targeted_expansion.py`는 실제 coordinator·thread·A/G/H·agent·gateway를
통과한다. policy 선택만 고정하고 최하위 LLM에 가짜 응답/usage를 제공한다. 기본/추가
provider text, 실제 캐시 재사용, epoch/attempt 변경, UNKNOWN/optional 예산, 병렬
run 격리, context 예외 복원, PC 부모와 사용자 선택, 같은 효과의 다른 적용, 원안
12개를 통합해 대표 10개와 deferred 2개를 모두 보존하는 경로를 검증한다.
네트워크 guard와 별도 SQLite를 사용하며 운영 자료를 학습/테스트 fixture로 사용하지 않는다.

사용자의 추가 요청으로 배터리 프로젝트는 운영 journal을 **읽기 전용**으로 확인했다.
발견한 UNKNOWN 재개 전 비용 발생 경로는 `pipeline.execute_stage` 사전 확인으로
막았다. 자세한 근거와 잔여 제한은 `BATTERY_RESTART_FIX_20260928.md`에 기록했다.
Q 패치 검증에 운영 DB나 유료 모델을 사용하지 않았으며 배포·원격 Git 변경은 하지 않았다.

구현 정합성 검증은 정확도·비용효율·과학적 타당성 개선의 실증이 아니다. 효과 ranker의
조건별 라벨 문제는 이번 범위 밖이며 해결했다고 주장하지 않는다.

## 최종 검증 결과

- 기존 AX/ARIZ, routing Q, 재개·비용·동시 실행, S5 필수 기법, gate/독립 검토,
  원안 통합·최대10개, 전체 후보 순위, 보고서·review refresh 회귀: **627 passed**
  (510.43초). 기존 assertion을 삭제하거나 완화하지 않았다.
- 이후 추가한 실제 12개 원안 통합, A의 PC 부모/사용자 선택, optional 예산 종료,
  bounded digest, 구 checkpoint의 실제 shadow/promotion/load 차단 5개도 통과했다.
  총 632개 서로 다른 시나리오를 검증했다.
- 마지막 공통 지원 검사·checkpoint 검증 변경 뒤 `test_routing_q_support_contract.py`
  및 `test_ax_refactor.py` 56개를 재검증했다. 추가 registry 테스트 1개도 통과했다.
- `test_ax_targeted_expansion.py`: 18 passed. `test_restart_checkpoints.py`의
  UNKNOWN stage 사전 차단을 포함한 복구 회귀도 통과했다.
- `git diff --check` 통과. 운영 배포, 프로젝트 자동 재개, 미확인 비용 정산,
  GitHub push, 유료 LLM 호출은 수행하지 않았다. 운영에서의 완주·성능 평가는 미수행이다.

실행 명령은 `.venv/Scripts/python.exe -X utf8 -m pytest ... -q --tb=short`이며,
포괄 회귀는 `pilot/tests/test_`에서 AX/ARIZ/routing_q/restart/execution_lifecycle/
concurrent_project_recovery/provider_interruptions/project_budget/retry_notifications/
gate_resume/s5/full_idea_review/full_candidate_ranking/idea/merge/report/review_refresh/
constraint_verdict/independent_reviews 파일을 선택했다. 추가·영향 재검증은 위에
명시한 테스트 파일/함수를 직접 실행했다.
