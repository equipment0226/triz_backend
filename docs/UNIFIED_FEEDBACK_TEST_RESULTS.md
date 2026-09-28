# 통합 피드백·적응형 탐색 검증 기록

2026-09-28 작업. 모든 모델 호출은 격리 테스트의 fake provider이다. SQLite/저장소도 테스트용이다.
운영 데이터 접근·변경, 운영 학습/정책 활성화, 배포, 유료 호출은 수행하지 않았다.
실제 품질·비용 효과는 `not_evaluated_live`이다.

## 실행 결과

- 신규 모드/공통 평가/학습/비용 통합 최종: **40 passed (56.28s)**. v4 지원·backup과 정산 시각 cutoff 회귀 포함.
- 프런트 production build: 성공. 기존 MaterialLibrary 번들 500KB 초과 경고는 남아 있다.
- 최종 브라우저 회귀: **11 passed (55.5s)**. 390px 모바일과 1366px 데스크톱 포함.
- 전체 backend: **1,237 passed, 1 warning (1085.68s)**. Qdrant 로컬 exact search 안내 경고만 남았다.

첫 전체 실행의 6개 실패는 원장 request 구형 형식, 고아 실행 복구, 직접 API 호출 Form 기본값,
기존 자연어 hard/soft 표시 호환을 수정해 해결했다. 해당 회귀 묶음은 42 passed였다.
기존 전체기법 테스트는 v2 계약으로 유지했으며 assertion을 새 정책에 맞춰 완화하지 않았다.
AX 브라우저 테스트의 옛 진행 카드 assertion은 기준 HEAD에서도 사용하지 않던 UI였으므로
현재 프로젝트 여정과 버전 검토 표시를 검사하도록 수정했다.

## 재현 명령

저장소 루트 PowerShell, 의존성 설치 완료 상태:

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests -q --tb=short
.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests/test_unified_feedback_adaptive.py pilot/tests/test_unified_feedback_learning.py pilot/tests/test_unified_cost_harness.py -q --tb=short
.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests/test_unified_cost_harness.py -q -s
```

마지막 명령은 실제 provider 없이 producer→merge→독립 검토→제약 검토→역할 평가→보고서→최종 피드백을 실행하는 deterministic smoke이다.
역할 평가 공급자는 같은 점수·rubric을 반환하는 fixture adapter이며 gateway 비용 기록과 S8 집계/순위 함수는 실제 경로다.
Q 학습은 순수 CPU fixture이며 합성 데이터로 운영 registry 승인을 우회하지 않는다.

frontend 디렉터리:

```powershell
npm.cmd run build
npx.cmd playwright test tests/unified-feedback.spec.js tests/report-pagination.spec.js tests/usage-recovery.spec.js tests/submission.spec.js tests/ax-workflow.spec.js tests/ax-full-report.spec.js tests/patent-workflow.spec.js --reporter=line
```

## 합성 비용 비교

동일 입력·모델·가격·제약·검토 기준을 사용한다. fake 호출당 10µUSD를 실제 task 원장에 기록한다.

| 구성 | 실제 호출 수 | 확정 µUSD | 미정산 예약 | 실제 기법 | 검토 대표안 | 관측 품질 / 제약 |
|---|---:|---:|---:|---|---:|---|
| B0 구계약 LITE | 11 | 110 | 0 | A/B/E/H | 1 | REVISE / CONDITIONAL |
| B1 신규 규칙 fallback | 8 | 80 | 0 | A | 1 | REVISE / CONDITIONAL |
| B2 CPU fixture Q + 효과 reranker | 7 | 70 | 0 | H | 1 | REVISE / CONDITIONAL |

이는 호출 경로와 원장 합계의 연결 검증이다. B2는 운영 관측으로 승인된 정책이 아니며,
한 문제 fixture의 차이를 기대 절감률·과학적 타당성·현업 품질 개선으로 해석하지 않는다.
평균/상위 분위 비용, 실패율, 사용자 효용의 일반화 비교는 실제 paired 실험 미실시로 평가하지 않았다.
표본 부족은 COLLECTING/fallback이고 합성 provenance가 있는 dataset은 운영 학습에서 제외된다.

## 66개 인수 항목 대응

아래는 인수 요구와 실행한 코드 경로의 대응표다. 항목마다 별도 1개 테스트를 만든다는 의미는 아니다.
신규 통합과 기존 공유 경계의 회귀를 함께 사용한다. 짧은 파일 별칭은 모두 `pilot/tests/` 기준이다.

- A = `test_unified_feedback_adaptive.py`
- L = `test_unified_feedback_learning.py`
- H = `test_unified_cost_harness.py`
- R = `test_ax_refactor.py`
- S = `test_routing_q_support_contract.py`
- T = `test_ax_targeted_expansion.py`
- P = `test_ax_phase1.py`
- B = `frontend/tests/unified-feedback.spec.js`

| ID | 실행 근거 / 관측 경계 |
|---|---|
| M01 | A `test_M01_M12_deep_retains_all_registered_tracks`; R 전체 A~H executor/DEEP ARIZ |
| M02 | A `test_M02_M07_missing_required_input_is_not_normal_stop`; R missing-input/partial; P budget/UNKNOWN |
| M03 | L `test_M03_Q01_Q03_trained_weights_change_actual_first_handler` 두 정책, A LITE fallback |
| M04 | A `test_M04_new_full_does_not_require_every_eligible_track` 및 FULL 실제 subset |
| M05 | A direct/governed mode guard; R executor ARIZ 금지; `test_ax_ariz_routing.py` |
| M06 | A `test_M06_M08_fallback_executes_subset_then_stops_for_review`에서 old complete_required 재호출 |
| M07 | A missing-required-input 및 fallback 상태; R optional budget; `test_restart_checkpoints.py` |
| M08 | A LITE=1/FULL=2 초기 폭·생성 한도, H 같은 검토/제약 기준 |
| M09 | H STOP 이후 실제 S6/S7/S8/보고서; A READY_FOR_REVIEW와 technical_success=false |
| M10 | L 증분 검토 및 `test_M10_delta_gate_answer_is_consumed_at_reference_resume`; `test_ax_recovery_persistence.py` |
| M11 | L `test_U08_M11_conflicting_clones_do_not_amplify_terminal_utility`; drop 후 포트폴리오 제외 |
| M12 | R 전체 모드 v2 fixture 유지; T old_pinned_run; `test_ax_full_report.py` |
| U01 | B 실제 브라우저에 상세 효과 조건 질문 없음 |
| U02 | B application_reviews 없는 keep/continue 전송, 실제 요청 envelope 확인 |
| U03 | A keep=.1, L 공통 이벤트→Q/효과 투영 및 가중치 |
| U04 | A 기술 CONDITIONAL 보존; L delta gate resume; H 최종 CONDITIONAL |
| U05 | L `test_U05_U10_missing_defaults_are_unobserved` |
| U06 | L `test_U06_U11_D10_drop_retains_lineage_and_no_consent_is_excluded` |
| U07 | L final 동일 submission 재전송·시험결과 중복; P outbox idempotency; UNKNOWN 재시도 |
| U08 | L 서로 다른 후보 keep/drop 보존·순서 불변; 최종 평가 재투영 |
| U09 | L late_feedback_revises_only_terminal의 rating 1/5 parameter |
| U10 | L missing_defaults의 rating=0/누락/adopted=false/bool parameter |
| U11 | L NO_TRAINING 제외; B 미동의 keep/최종 피드백/보고서 |
| U12 | B legacy 조건 payload가 폼을 재생성하지 않음; `test_manual_effect_reviews.py` reader |
| D01 | L real H producer/gateway/raw/event 계보; H 실제 merge/후보/평가/보고서 |
| D02 | `test_ax_coherence.py`, `test_ax_coherence_recovery.py` 독립 audit; L 증분 audit |
| D03 | L `test_D03_D04_D09_exposure_and_removed_effect_do_not_label_catalog` 무제약 PASS |
| D04 | L active_effect_ids 변경 후 노출/제거 효과 투영 제외 |
| D05 | L `test_D05_D06_joint_effect_weight_conserved`, Q task ID 비용 중복 제외 |
| D06 | L 여러 raw의 E1 반복에도 2개 unique effect, weight 합=1 |
| D07 | A final writer; L keep 양쪽 dataset·기존 시험 제출 adapter; H S6/S7/S8 common writer |
| D08 | L 시험 결과 evidence_level과 효용 분리; A keep의 기술 상태 보존 |
| D09 | L OUTSIDE_CATALOG만 남은 후보 효과 dataset 비움 |
| D10 | L drop 원안 snapshot/UNKNOWN_ATTRIBUTION; 표시 제목과 source ID 분리 |
| D11 | L `test_D11_Q15_effect_prediction_uses_selection_snapshot` 최종 평가 바뀌어도 feature 동일 |
| D12 | L outcome 입력 순서·clone·중복 이벤트 불변, late reward revision |
| Q01 | L CPU q.train 결과로 actual TRACK_FUNCS 첫 handler 변경; H real H producer |
| Q02 | L 공통 이벤트 투영·worker 두 task 호출/실패 격리·CPU train; 운영 승인은 미실시 |
| Q03 | L 동일 품질/상이한 비용 합성 sequence의 학습 선호 반전 |
| Q04 | L 초기 decision이 Q dataset 두 전이에 포함; old optional-only filter 없음 |
| Q05 | A DEEP는 Q 선택 없음; L 실제 decision/result/closure만 투영 |
| Q06 | L STOP 실제 action result와 하나의 terminal; H STOP 이후 필수 검토 |
| Q07 | L late feedback의 terminal만 갱신, task 비용 1회 귀속 |
| Q08 | L cutoff 이전 final label/미래 usage 정산 제외; S 실제 next 상태 지원; 신규 v4 backup 재검증 |
| Q09 | R semantic_rerun_archives_state_without_resetting_budget; T 전송 epoch 캐시; 신규 v4 cross_episode |
| Q10 | S choose/train/evaluate support 공유; L 신규 v4 동일 mask 및 미지원 고Q 배제 |
| Q11 | S unsupported_rule; L 신규 v4 SKIP_UNSUPPORTED_FALLBACK, value=None, terminal=false |
| Q12 | L 독립 8문제군 support, holdout/synthetic reject; S holdout/cross-episode |
| Q13 | L v3/v4 동일 shape 불호환; S old checkpoint shadow/load 거부 |
| Q14 | A 실제 RULE_BASED fallback; B COLLECTING/규칙 표시; 가상 Q값 없음 |
| Q15 | L effect 선택 snapshot·CPU 학습·실제 rerank 순서; worker task/schema 분리 |
| Q16 | L owner revision·withdraw·frozen report; `test_ax_learning.py` registry pin/withdrawal; R cutoff |
| C01 | H 모든 실행 task.actual 합=budget.spent=호출수×단가; L Q 비용 합 |
| C02 | L UNKNOWN task로 Q/효과 표본 제외; P 미정산 예약 보존; estimate는 별도 필드 |
| C03 | L actual task_ids unique와 원장 총비용 일치; H 여러 원안→한 후보 |
| C04 | H 실 호출 수·tracks만 보고하고 live_status=not_evaluated_live |
| C05 | H 동일 입력/모델/가격/검토로 B0/B1/B2 실제 호출 차이 |
| C06 | T agent+durable retry; L 변경 없는 증분 검토 재사용 |
| C07 | T 실제 provider prompt와 semantic hash, 대상/조건 변경 cache invalidation |
| C08 | T parallel context/cost isolation; P stale response; R stale_action_output |
| C09 | `test_unknown_usage_recovery.py` 원 예약·1회 승인·2차 차단·브라우저 usage-recovery |
| C10 | R 80 raw DEEP; T actual addition max10/all leaf; H adaptive merge unaccounted=[] |
| C11 | L unchanged 후보 ID/audit 재사용, 변경 원안만 재생성; R S7 changed-candidate |
| C12 | B keep→continue→final→다음 run COLLECTING mock API 브라우저 흐름 |
| C13 | 전체 backend API/MCP/n8n/report/patent 회귀 및 ax-full-report/patent-workflow 브라우저 |
| C14 | H/L synthetic 제외·관측 mask·not_evaluated_live; 승인/운영 실험 미실시 명시 |

추가 UI 요청은 `test_display_labels.py`, `test_report_display_terms.py`와
`frontend/tests/report-pagination.spec.js`에서 내부 raw ID/특허 enum 표시, URL·저장 상태 보존,
용어, 장별 전체 내용·번호 이동·그림·XSS 정화·데스크톱·다운로드를 검증한다.

## 최종 확인

전체 backend 1,237개, 최종 신규 통합 묶음 40개, 브라우저 11개가 통과했고 프런트 build가 성공했다.
전체 실행 중 추가/보완한 v4 backup·delta 게이트 재개·정산 cutoff는 최종 40개 묶음으로 다시 확인했다.
개수는 서로 중복되므로 합산하지 않는다. 전체 실행 JUnit 결과는 로컬 `.deployment/unified-feedback-pytest.xml`이다.

backend 40개, frontend 9개 변경 파일을 원래 HEAD 위의 Git 작업 사본에 반영했다.
변경 파일 동일성, 미관련 파일 제외, 두 저장소 `git diff --check`를 확인했다.
main 롤백·커밋·push·운영 배포는 수행하지 않았다.
코드 구현과 mock 통합 검증은 완료했으며 실데이터 학습·운영 활성화·실제 비용/품질 개선은 미실시다.
이 문서의 합성 수치는 운영 학습 완료나 실제 절감 근거가 아니다.
