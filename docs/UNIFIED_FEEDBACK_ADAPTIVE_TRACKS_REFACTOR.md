# 통합 평가 및 적응형 트랙 리팩토링 작업 기록

## 기준과 범위

2026-09-28 시작 시 backend `7d886e98e10bc6ce599f5f4fcd51b0e1a43eade4`,
frontend `6275e5cad31ede66b6909f750cb47284785f7673`, 두 저장소 모두
`feat/ax-qlearn-refactor-20260928`이며 staged/unstaged 변경은 없었다.
작업 프롬프트는 `TRIZ_UNIFIED_FEEDBACK_ADAPTIVE_Q_CODEX_PROMPT.md`이다.
이 두 HEAD 위에서 변경했으며 main으로 되돌리지 않았다.
루트 작업 사본에 먼저 존재한 backend `Dockerfile`, `README.md`, `deploy/README.md`의 차이는
이번 패치에 포함하지 않고 그대로 보존했다. 나머지 대상 파일은 시작 시 Git 사본과 비교했다.
운영 배포/데이터 변경/프로젝트 재개/유료 모델 호출은 수행하지 않는다.

## 구현 및 보존 매트릭스

| 경로 | 보존 | 변경 이유와 검증 |
|---|---|---|
| mode_contract / solve_contract / coordinator / S5 | 기존 frozen 계약, DEEP A~H 및 ARIZ, 트랙 체크포인트 | 새 계약의 eligible/required/executed 분리, 실제 Q/fallback subset 선택; M01–M12 |
| nodes S7/S10 / quality / meeting | 독립·제약·최종 검토, CONDITIONAL, 명시적 비용 동의 | 공통 immutable 평가와 원자적 outbox, 제거 전 계보; U03–U11, D01–D12 |
| Workspace HumanInput / Feedback | keep/drop·mitigation·별점, 조건의 읽기 전용 설명 | 상세 효과조건 폼과 신규 application_reviews 전송 제거; U01/U02/U12/C12 |
| action_runtime / routing_q | 실제 선택·비용·지원 범위와 backup, targeted prompt | 신규 초기 action 및 STOP, terminal reward revision, cutoff; Q01–Q14/C01–C09 |
| effect_history / effect_ranker / registry / worker | 과거 기록, 소유권·동의·task별 모델 포인터 | 같은 평가의 적용안 효용 학습, 선택 전 feature, 구 checkpoint 격리; Q15/Q16 |
| idea_consolidation / quality / report | 대표 최대10개, 모든 원안 처분·leaf·조건·보고서 | 변경 후보만 증분 검토, 기존 요약/특허/API 회귀; C10/C11/C13 |
| deterministic harness / diagnostics | 합성 표본과 실자료 구별 | B0/B1/B2 비용 원장 비교, 관측 mask·누락·준비 상태; C04/C05/C14 |

신규 실행만 v3 계약으로 생성한다. `adaptive_tracks.py`가 초기/후속 트랙과 STOP을 선택하고,
`incremental_review.py`가 변경된 대표안만 다시 검토한다. `feedback_events.py`의 공통 원천을
`learning_outcomes.py`가 Q와 효과 모델의 서로 다른 데이터셋으로 투영한다.
기존 승인·shadow·지원 범위와 task별 모델 포인터를 재사용하며 운영 정책을 활성화하지 않았다.

구버전 전체 실행 assertion은 v2 fixture에서 유지했다. 새 기본 계약의 의도적 차이는 v3 fixture에서 검증한다.
전체 회귀에서 발견한 구형 원장 request 형식, 고아 실행 복구, FastAPI 직접 호출 기본값과
자연어 hard/soft 표기 회귀를 수정했다. S8에서 발생한 후속 S7 질문의 답도 실제 게이트가 소비하도록 보완했다.
브라우저 AX 검사는 기준 HEAD에서도 사용하지 않던 별도 진행 카드 대신 현재 프로젝트 여정 UI를 검사한다.

## 추가 사용자 요청

- 피드백 입력 문구를 “실제 적용 가능성과 보완할 점을 알려 주세요.”로 변경했다.
- `Su-장`은 `Su-Field`, 물질로 시작하는 해당 모델 표현은 `물질-장 모델`로 정규화한다.
- 특허 카드의 제약/근거/조건에 내부 enum·필드 표현이 표시되지 않도록 표시 경계에서 변환한다.
- `raw-target-…`는 보존된 leaf 원안의 제목으로 치환한다. 계보를 찾지 못하면 원안 내용 확인 안내를 표시한다.
  저장 ID·URL·구조화된 출처를 변경하거나 제목으로 계보를 생성하지 않는다.
- 모바일은 보고서 장별 한 페이지와 번호 이동을 사용한다. 장 내용·그림·데스크톱·다운로드를 보존한다.

구체적인 계약은 `UNIFIED_FEEDBACK_DATA_AND_REWARD_CONTRACT.md`, 재현 명령과 66개 인수 항목 대응은
`UNIFIED_FEEDBACK_TEST_RESULTS.md`에 기록한다.

## 검증 원칙

격리 SQLite와 fake provider만 사용한다. 호출/토큰/비용은 모의 provider가 실제 반환한
usage와 task journal로 계산한다. 합성 테스트의 비용 차이를 운영 절감률로 해석하지 않는다.
실자료 학습·운영 활성화·실제 품질 및 비용 개선은 별도 증거 없이는 `not_evaluated_live`이다.
