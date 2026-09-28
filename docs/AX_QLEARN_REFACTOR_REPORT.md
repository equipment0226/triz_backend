# AX / QLearn 구현 결과

작업일: 2026-09-28. 대상은 이 작업공간의 `pilot/` 및 기존 보류 화면이다. 배포 사본(`release/`, `.deployment/`)과 운영 DB, 원격 저장소는 변경하지 않았다. Git 메타데이터가 없는 소스 사본이므로 변경 전 파일은 `.tmp/ax-refactor-before/`에 보관했다.

## 실행 경로

`pipeline.create_run → runtime.initialize → mode_contract.pin`이 신규 실행에 `ax-run-v2`를 고정한다. `runtime.before_stage → coordinator.route → nodes._run_tracks → complete_required`는 모드의 필수 트랙을 모두 처리한다. 병렬 작업 수는 동시성 한도이며 총 기법 수가 아니다.

| 신규 모드 | 필수 계획 | 선택적 탐색/복구 한도 | 선택적 호출 예산 |
|---|---|---|---|
| LITE | A/B/E/H | 총 결정 2회, 추가 탐색 1회, 복구 대상·시도·추가안 각각 1 | 0.20 USD 이내 |
| FULL | A/B/C/E/F/G/H | 총 결정 6회, 추가 탐색 2회, 대상 2·대상별 2회·추가안 4 | 0.60 USD 이내 |
| DEEP | A/B/C/D/E/F/G/H | 0 | 0 |

이 수치는 운영 개선이 입증된 최적값이 아니라 보수적 초기 실행 한도다. 기존 프로젝트 총 cap(기본 2 USD)과 검토 예약 0.12 USD를 늘리지 않는다. 실제 호출 예약은 기존 모델·가격·token 설정으로 계산하며 선택적 상한보다 크면 추가 호출만 종료한다. UNKNOWN 비용 예약은 해제하지 않는다. 신규 프로파일의 단일 출처는 `ax/mode_contract.py`; YAML의 기존 `tracks` 항목은 구버전/비-AX 호환 경로에 남겼다.

기존 `PASS/CONDITIONAL/FAIL`, 단계 키·순서, API 필수 입력은 유지한다. 완료 투영은 `COMPLETED`, `REVIEWED_NO_APPLICATION`, `NOT_APPLICABLE`, `BLOCKED_MISSING_INPUT`, `FAILED`, `NOT_RUN_BUDGET`, `PENDING`을 구별한다. 보고서의 모드 실행 완료와 개념/실증 완료는 별도로 표시한다.

DEEP에서도 원안 통합·coherence·불변 snapshot·예산 gateway·보고서는 작동한다. routing Q와 자율 복구/추가 탐색은 실행하지 않는다. 신규 LITE/FULL의 ARIZ 금지는 계획·governor·직접 트랙 실행기에 모두 적용한다. 구버전 bundle을 조용히 신규 계약으로 바꾸지 않는다.

## 추가 작업과 학습 연결

- S5는 미대응 모순에 대해 허용된 A/H/G 트랙의 실제 추가 작업과 종료안을 제안한다. 선택된 트랙을 기존 실행기로 실행하고 기존 원안과 함께 같은 통합·품질 경로로 보낸다.
- S6/S7 경계에서는 `coherence_recovery.targets`의 서로 다른 대상/누락에 대한 실제 복구 티켓과 종료안을 함께 비교한다. 선택된 대상만 기존 복구 handler와 T2 역할 설정으로 실행하고 새 후보만 T3 독립 검토한다. 추가 후보의 S7 검토는 유지한다.
- `ActionTicket`은 선택적 인스턴스·snapshot 필드를 추가했다. `action_runtime.executing`은 실행 직전 권한/모드/버전을 재확인하고 명시 context를 gateway로 전달한다. 병렬 기본 트랙, 추가 탐색, 통합의 결과·부모 작업·산출물 버전 연결을 이벤트에 남긴다. 전역 `ax_last_decision`은 구버전 표시만으로 남고 신규 비용 귀속을 대신하지 않는다.
- 통신 epoch와 `semantic_episode_id`를 분리했다. 의미 재계획은 이전 제어 투영을 archive하고 downstream 완료 마커·복구·선정·효과 투영을 무효화한다. 비용은 초기화하지 않는다. 동일 논리 호출의 완료/UNKNOWN 예약은 transport 재개에서도 재사용한다.
- `routing_q.py`는 상태×행동의 결정적 interaction 특징을 가진 보수적 선형 Q다. 모드·domain·phase·실행 기법·gap·대상 품질·예상 비용·잔여 예산을 사용한다. 동일 action type의 다른 트랙/대상을 구별한다. v1/v2의 8/12차원 weight를 padding하지 않는다.
- 지원되는 실제 대안이 2개 이상 있을 때만 Q 선택을 사용한다. 지원 없는 대안은 고득점으로 실행하지 않는다. 한 대안만 허용되면 FORCED, 모델 shape/지원 부족이면 규칙 fallback을 기록한다. 라벨 없는 DEFER에 보상을 만들지 않는다.
- 실행 결과, 명시 `OPTIONAL_TRANSITION`, 리뷰 이용 가능 시각과 episode로 routing dataset을 만든다. 미실행·미정산·라벨 없음·교차 episode는 제외한다. 개념 적용성 proxy는 ±0.5, 명시 시험/현장 관측은 ±1, 직접 귀속 정산비용은 `min(0.25, 0.1 × 비용/총예산)`으로 분리 저장한다. 이는 초기 설계 가정이다. 통합·이후 공통 검토 비용은 별도 공통 비용이며 여러 후보에 중복 청구하지 않는다.
- 효과 학습은 별도 `effect_ranker.py`의 정규화 선형 회귀다. routing Q의 checkpoint/pointer를 사용하지 않는다. 자세한 관측·동의 계약은 [EFFECT_APPLICABILITY_LEARNING.md](EFFECT_APPLICABILITY_LEARNING.md)에 기록했다.
- 기존 outbox/CPU worker는 효과 검토 및 optional transition 이벤트까지 소비한다. v1/v2/v3 routing과 effect ranker를 task/schema/scope별 pointer로 분리했다. 데이터 충분성·독립 시간 holdout·offline 평가 후 shadow만 저장하며 자동 canary 승격은 하지 않는다. 운영자 내부 호출 `promote_task`에는 명시 actor/이유·20건/5실행 이상의 적격 shadow·최대 25% 제한이 필요하다.

## 최근 기능과 호환성

최신 소스의 ARIZ Part6 제안 기록을 유지했다. 요청 문서의 과거 설명을 이유로 삭제하지 않았다. ARIZ Part8/9는 추가하지 않았다.

최신 `representative-ideas-max10-v2` 전 원안 비교·대표안 최대 10개·비선정 원안별 사유를 유지했다. 수량만으로 후보를 생성하는 과거 quota 경로를 복원하지 않았다. 신규 원시 재고는 통합 전 leaf 출처를 저장하며, 80개 원안 중 10개를 선정한 테스트에서도 80개 출처와 나머지 처분 이유를 보존한다. 대용량 통합은 현재 전체 문맥/명시 길이 제한을 유지한다. 새 계층적 batching을 추가하지 않았으며 실제 공급자 문맥 한도 초과 시 원안을 보존하고 중단한다.

기존 전체 보고서 본문·도식·라벨·참고자료·부록·frozen projection 경로는 유지했다. AX 부록에 모드 범위 설명만 추가했다. 기존 v1 fixture는 명시 legacy 계약으로 회귀하고, v2 신규 실행을 별도 fixture로 검증한다. 특허·RAG·MCP 도구 계약은 변경하지 않았다.

## 변경 파일군

- 신규: `ax/mode_contract.py`, `ax/action_runtime.py`, `ax/routing_q.py`, `ax/effect_history.py`, `ax/effect_ranker.py`.
- 연결: `pipeline.py`, `nodes.py`, `solve_contract.py`, `idea_consolidation.py`, `catalog_binding.py`, `effect_catalog.py`, `presentation.py`(보고서 API 해결안도 frozen snapshot 사용).
- AX 기존 계층: `runtime.py`, `coordinator.py`, `coherence_recovery.py`, `recovery.py`, `contracts.py`, `gateway.py`, `ledger.py`, `learning.py`, `registry.py`, `worker.py`, `rules.py`, `report.py`, `api.py`.
- 설정·표시: `pilot/config/triz.yaml`, `pilot/templates/report_ax_appendix.md.j2`, `frontend/src/pages/Workspace.jsx`.
- 검증: `pilot/tests/test_ax_refactor.py`, 기존 legacy fixture/네트워크 guard, `pilot/scripts/ax_offline_smoke.py`.

추가 테이블은 `ax_effect_applications`, `ax_effect_reviews`, `ax_effect_selections`, `ax_task_deployments`다. 기존 테이블/컬럼을 삭제·변경하지 않는다. 기존 SQLAlchemy additive init에 등록했고 SQLite에서 검증했다. 운영 MySQL DDL은 실행하지 않았다.

## 검증 범위와 배포 전 확인

[테스트 결과](AX_QLEARN_TEST_RESULTS.md)를 참조한다. 구조·연결 검증을 완료했으며 현업 정확도/비용 향상, 물리 성능, 실제 공급자 latency·token 상한은 평가하지 않았다. MySQL 실행, n8n 원격 배포, 실제 브라우저 사용자 조작은 미검증이다. frontend는 빌드 검증했다.

운영에서는 초기 COLLECTING/규칙 실행이 정상이다. 시험 관측이 없더라도 명시 동의된 조건별 개념 proxy로 학습할 수 있으나 부족한 독립 사례나 라벨을 만들어 채우지 않는다. 효과 이력의 정합성은 보수적인 구조·조건 일치에 기반한다. 자유문장 물리 조건의 동등성/부등식 범위를 자동 입증하지 않는다. 조건 재검토는 변경 후보에 한정되며 그 후보의 S7 제약을 재검토하고 확인하지 않은 의무를 남긴다.

배포 전에는 별도 테스트 MySQL에서 additive table 생성/동시 예약/권한 검증, 기존 DB 백업, 신규 FULL/DEEP의 정해진 cap 아래 승인된 공급자 smoke가 필요하다. 이 작업에서는 배포하지 않았다.

롤백은 신규 실행의 `ax.run_contract_version: legacy` 또는 기존 `TRIZ_AX_ENABLED=false`로 시작한다. 특정 모델은 `registry.rollback_task`로 해당 task/schema만 되돌릴 수 있다. 기존 v2 실행은 현재 호환 실행기로 마무리한다. v3 특징을 해석하지 못하는 과거 실행기로 진행 중 bundle을 강제로 돌리지 않는다. 추가 테이블·관측·비용 기록을 삭제하지 않는다. 소스 복원이 필요하면 변경 전 사본과 변경 목록을 비교해 대상 파일만 복원하며 이후 사용자 변경을 덮어쓰지 않는다.

변경 파일 목록: `.tmp/ax-changed-files.json`. 소스 검토용 unified diff: `.tmp/ax-refactor.diff`.
