# F1–F5 검증 결과

운영 데이터·유료 provider를 사용하지 않았다. 테스트는 임시 SQLite와 격리 저장소를 사용하며 외부 네트워크와 실제 LLM 호출은 기본적으로 실패하도록 설정한다. 새 통합 테스트는 실제 producer, merge, S6, S7, S8, report, feedback, dataset, worker, registry 함수를 호출하고 LLM provider 응답만 대체한다.

## 수정 전 확인

명령: `.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests/test_targeted_f1_f5.py -q --tb=short`

**5 failed (15.09s)**. F1은 같은 ID의 새 REVISE 대신 live PASS 유지, F2는 자동 FAIL을 dropped 목록에 기록, F3은 제약 변경 전후 phi 동일, F4는 실행 단위 비용 계약/출처 부재, F5는 기준선·가중 평가 계약 부재로 실패했다. F4의 수치 집계 반례는 수정 후 실제 격리 원장으로 별도 검증했다. 참고 감사의 함수 본문을 복사한 stub 실행 결과가 아니다.

## 실행 기록

- 기존 연결 회귀 93개 통과: unified adaptive/learning/cost harness, routing support, targeted expansion와 초기 신규 review 테스트.
- 중간 신규 집중 회귀 47개 통과(65.80s).
- 후속 전체 관련 회귀 157개 통과(172.64s). 이후 추가한 중단된 merge 재개·기존 결제 키·검토 입력 무효화 출처는 최종 재실행 대상이다.
- 비용/UNKNOWN 연결 31개 통과(30.08s), 실제 adaptive producer 비용 집계 및 재개 경계 포함 비용 테스트 17개 통과(27.37s).
- 브라우저 6개 통과(34.7s): `npm.cmd test -- tests/unified-feedback.spec.js tests/report-pagination.spec.js tests/ax-full-report.spec.js --reporter=line`. 최초 sandbox 실행은 Vite의 상위 폴더 접근 제한으로 시작하지 못했고, 로컬 테스트 권한으로 재실행했다.

중간 테스트 수를 합산해 서로 다른 테스트의 개수라고 주장하지 않는다.

최종 결과:

| 범위 | 명령 / 로그 | 실제 결과 |
|---|---|---|
| 전체 백엔드 | `.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests -q --tb=short --junitxml=.deployment/f1-f5-suite-results.xml` | **1,293 passed, 1 warning**, 1178.64s |
| 마지막 코드의 관련 회귀·통합 | 아래 14개 파일을 같은 pytest 명령에 지정. `.deployment/f1-f5-final-regression-results.xml`, `f1-f5-final-regression-output.txt` | **159 passed**, 182.35s |
| 추가 인수 확인 | I의 `test_R03_project_default_and_explicit_no_training_remain_distinct`, V의 `test_F2_07_no_candidate_stop_has_technical_reason` | **2 passed**, 9.13s |
| 프런트 보존 | 위 Playwright 3개 spec, `.deployment/f1-f5-browser-output.txt` | **6 passed**, 34.7s |
| 정적·diff 확인 | 변경 Python AST parse, backend `git diff --check`, frontend `git status --short` | 통과, 프런트 worktree clean |

최종 관련 회귀 파일은 신규 T/V/Q/C/G/I 6개와 `test_unified_feedback_adaptive.py`, `test_unified_feedback_learning.py`, `test_unified_cost_harness.py`, `test_routing_q_support_contract.py`, `test_ax_targeted_expansion.py`, `test_unknown_usage_recovery.py`, `test_ax_full_report.py`, `test_ax_recovery_persistence.py`다. 전체 suite 실행 중 추가 보완한 재개·출처 경계는 이 마지막 회귀에서 다시 실행했다. 이후 production 코드 변경 없이 추가 인수 테스트 2개만 확인했다.

전체 suite의 경고 1개는 Qdrant local exact search에서 search_params가 적용되지 않는다는 기존 라이브러리 안내다. 테스트 실패는 없다. 최초 기존 회귀에서 실패했던 미동의 fixture는 최신 프로젝트 기본 적용을 거꾸로 되돌리는 대신 명시 `NO_TRAINING`을 설정해 테스트 의도를 유지했다.

## 50개 인수 항목 대응

경로는 모두 `pilot/tests/` 기준이다. 아래 약칭은 실제 테스트 파일을 가리킨다.

- **T**: `test_targeted_f1_f5.py`
- **V**: `test_targeted_review_disposition.py`
- **Q**: `test_targeted_context_gate.py`
- **C**: `test_targeted_track_cost.py`
- **G**: `test_targeted_registry_gate.py`
- **I**: `test_targeted_offline_integration.py`
- **UA/UL/UC**: `test_unified_feedback_adaptive.py` / `test_unified_feedback_learning.py` / `test_unified_cost_harness.py`

| ID | 테스트·검증 경계 |
|---|---|
| F1-01 | T `test_F1_01_latest_same_design_replaces_old_pass`: 같은 ID, live/cache/issues/current outcome |
| F1-02 | V `test_F1_02_06_08_revision_outcome_and_frozen_report`: REVISE→PASS와 이전 이벤트 보존 |
| F1-03 | V `test_F1_03_04_07_no_stale_pass_on_bad_review[REJECT]`: 현재 제외·leaf·처분·수리 대상 |
| F1-04 | 같은 V 테스트의 MISSING/EMPTY: 미검증 및 실패 시 저장된 부모 포트폴리오 |
| F1-05 | T F1-01의 동일 입력 재실행: provider 호출 증가 없음 |
| F1-06 | V `test_F1_06_keep_survives_as_utility_but_never_overrides_reject`: keep=.1, REJECT=-1, 합성 효용=-.67 |
| F1-07 | V `test_F1_07_explicit_disposition_completeness` 및 EMPTY: 빈 결과 완료 금지 |
| F1-08 | V F1-02: 실제 frozen markdown 불변·새 snapshot PASS·과거 cutoff 결과 |
| F2-01 | T F2-01 + V `test_F2_01_04_05_real_alternative_after_automatic_failure`: 실제 S7 자동 FAIL→H 실행→S6→S7 |
| F2-02 | V REJECT 및 `test_F2_01_02_07_automatic_failure_reaches_real_budget_evaluation`: 실제 targets/governor |
| F2-03 | V `test_F2_03_04_05_06_design_exclusion_and_legacy`, `test_F2_03_04_cohort_separates_historical_failures` |
| F2-04 | 같은 V 설계·cohort 테스트: 혼합 제외와 후속 전체 사용자 Drop 구분 |
| F2-05 | V 설계 fingerprint 테스트 및 실제 다른 설계의 S6/S7 통과 |
| F2-06 | V 중복 disposition 및 LEGACY_UNKNOWN_ORIGIN; UL 사용자 결정·revision 재전송 |
| F2-07 | V 실제 예산 부족 판정, USER_DECLINED, `test_F2_07_no_candidate_stop_has_technical_reason`; UA `test_M02_M07_missing_required_input_is_not_normal_stop` |
| F2-08 | UA 모드/ARIZ 제한; `test_ax_refactor.py` DEEP optional 금지; 기존 recovery 횟수 회귀 |
| F3-01 | T `test_F3_01_confirmed_context_reaches_phi` |
| F3-02 | Q `test_F3_02_semantic_fields_reach_action_interactions` 6개 파라미터 |
| F3-03 | Q `test_F3_03_04_canonical_context_and_provenance`: mm/m, 순서, 공백, 모호한 단위 |
| F3-04 | 같은 Q 테스트: source ID·snapshot 변경과 의미 토큰 분리 |
| F3-05 | Q `test_F3_05_07_real_training_context_preferences_and_legacy`: 실제 Q train/choose |
| F3-06 | I 실제 생성 후 피드백에도 저장된 최초 decision 특징 불변 |
| F3-07 | Q v4 checkpoint/v5 특징 불일치 fallback, 기존 pinned v4 특징 유지 |
| F3-08 | I 실제 v5 decision→dataset→worker→registry→다음 run 및 diagnostics |
| F3-09 | `test_routing_q_support_contract.py`, UL adaptive support/backup/holdout 회귀 |
| F4-01 | C `test_F4_01_02_03_06_08_logical_totals_deduplicate_parent_child`: A=.50/H=.20, 제안 비교 |
| F4-02 | 같은 C 테스트 및 `test_F4_02_03_repeated_attempt_log_does_not_duplicate_task` |
| F4-03 | C의 서로 다른 유료 task 합계와 같은 task 로그 재전송 구분 |
| F4-04 | C unknown/future 및 `test_F4_04_missing_task_attribution_fails_closed`; `test_unknown_usage_recovery.py` |
| F4-05 | C different_model/different_size: 고정 비교 계약 분리 |
| F4-06 | C `test_F4_06_cache_only_execution_does_not_lower_generation_average`: support는 호출 수가 아닌 실행 수 |
| F4-07 | T 계약 출처 및 C `test_F4_07_prior_uses_node_caps_and_price_units` |
| F4-08 | C 원장 합계·부모/자식 중복 없음, UC 동일 모델/가격/검토 비용, 기존 governor reserve 회귀 |
| F4-09 | C synthetic/no_consent/different_owner/future 및 common scope/철회 회귀 |
| F4-10 | C pending STOP, 기존 결제 키 재사용, 완료 producer 계보 유지, merge 중단 후 UNKNOWN 재호출 차단 |
| F5-01 | T `test_F5_01_small_utility_baseline_counterexample`: .0409 > .0009 거절 |
| F5-02 | Q `test_F5_02_03_weighted_train_and_evaluation`: holdout 변경과 고정 train mean |
| F5-03 | 같은 Q WMSE 및 UL `test_D05_D06_joint_effect_weight_conserved` |
| F5-04 | Q `test_F5_04_supported_zero_and_unsupported_zero` |
| F5-05 | Q invalid numeric 파라미터, 빈/미관측/0 weight; pure gate 모델·coverage 유효성 검사 |
| F5-06 | Q `test_F5_05_06_09_empty_missing_zero_and_tie`: 0 기준선·동률·미관측 구분 |
| F5-07 | Q `test_F5_07_08_actual_regression_can_pass_and_old_artifact_cannot`: 실제 회귀 출력의 별도 holdout 그룹 평가 |
| F5-08 | G 실제 set_task_shadow/promote_task/promote_policy/for_run 거절, 과거 pinned read 유지 |
| F5-09 | Q 미관측 라벨, UL 노출/제거 효과는 라벨 아님, I 공동 이벤트 연결 |
| R-01 | UA·`test_ax_refactor.py`·I: 모드별 트랙 및 필수 검토 |
| R-02 | UA keep CONDITIONAL, I S7/S8, 브라우저 unified-feedback |
| R-03 | I `test_R03_project_default_and_explicit_no_training_remain_distinct`, UL owner/철회/NO_TRAINING |
| R-04 | 전체 suite의 merge/leaf/효과/정합성/보고서/특허 테스트와 브라우저 장별 페이지·frozen 보고서 |
| R-05 | I `test_R05_R06_F3_06_08_real_pipeline_to_worker_and_next_run`: provider 경계만 대체한 실제 연결 |
| R-06 | 임시 SQLite/네트워크 차단, I synthetic 제외 및 worker COLLECTING/다음 run fallback |

## 해석 제한

수치 예제와 양성 gate 통과 예제는 격리 fixture의 산술·코드 검증이다. 운영 모델을 승인하거나 운영 데이터로 학습한 결과가 아니다. 실제 총추론비용 감소, 현장 품질 향상, 운영 모델의 기준선 개선은 측정하지 않았다. 운영 데이터에서 새 비용·검토 계보와 충분한 독립 holdout이 확보되기 전에는 해당 신규 모델을 사용할 근거가 없다.
