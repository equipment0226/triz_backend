# Patent (Test) 구현 전 확인 — 2026-09-16

이 문서는 현재 코드의 확인 결과다. 첨부 설계 문서를 구현 완료의 근거로 사용하지 않는다.

## 현재 기준선

- 작업 루트 `C:/Users/equip/Desktop/triz` 자체는 Git 저장소가 아니다. 원본 개발 코드를 allowlist로 `release/` 사본에 내보내는 구조다.
- backend: `equipment0226/triz_backend`, `main`, HEAD `189415b` (신규 US$2 및 기존 예산 명시적 상향).
- frontend: `equipment0226/triz_front`, `main`, HEAD `c15f345` (기존 배포 AX 화면). `triz_frontend`가 아니다.
- root/상위 경로/두 release 저장소에서 적용되는 AGENTS.md는 발견되지 않았다. 강제 reset/checkout/clean은 수행하지 않았다.
- 구현 전 backend 410 tests 통과. frontend build, gateway 1 test, AX browser 1 test 통과.
- Railway backend `3fc9f2d6-6553-4416-a73a-4748b27b8ed3` SUCCESS. 33개 소스 hash, 실제 MySQL, 임시 DB의 US$2 프로젝트 분리·재개 예산 보존을 검증했다. 모델 호출 0회.
- 사용자 지정 예외 프로젝트는 총 US$5. 이 예산 변경은 특허 기능 이전의 별도 요청이며 이후 patent 모듈에서 전역 설정을 변경하지 않는다.
- 미커밋 항목: 기존 V3 운영·설계·검토 문서와 평가 결과, frontend 디자인 검증 스크립트. 추가 직접검토 특허 40건의 과학효과 출처 갱신도 별도 사용자 요청이다. 모두 보존한다.
- 설계 원본은 `concept/`에 보관하고 GitHub 제외 규칙을 두 저장소에 반영했다. 첨부 패키지 로컬 사본은 `concept/patent_implementation_v1/`이다.

## 실제 확장 지점

| 영역 | 확인한 구현 | 특허 모듈 적용 경계 |
|---|---|---|
| 인증 | backend `app_auth`, `x-triz-session`, DB session_user. frontend HttpOnly 세션 및 same-origin proxy | 기존 로그인 유지. 신규 router는 전역 auth flag와 무관하게 실제 사용자·case ACL 강제 |
| 상태 | `store.run_states.state_json`, `GlobalState`, 13개 기존 stage | raw SELECT로 읽기. `_upgrade`, `save_state`, 기존 mutating MCP 금지 |
| 원장 | `triz/ax/ledger.py`, 별도 AX metadata, artifact/snapshot/edge/attempt/outbox | AX 원본의 snapshot 조회는 재사용 가능. writer는 run head와 원본 state projection에 결합되어 patent extension으로 사용 불가 |
| gate | `ax/validation.py`는 원래 TRIZ candidate/test obligation 전용 | 원본 gate를 참고자료로 읽으며 특허 T3/법률 판단 PASS로 승계하지 않음 |
| 조율 | `ax/coordinator.py` 및 bounded recovery. coordinator HITL 없음 | 기존 동작 유지. 특허는 독립 governor/reducer와 명시적 기술·범위 확인 |
| RL | `ax/learning.py` 실제 CPU Q trainer, 8 features/12 고정 action. registry는 기존 TRIZ review/run 의미에 결합 | namespace 계약 확인 adapter 필요. 호환 trainer 미설정 시 TELEMETRY_ONLY, 기존 정책/원장에 특허 보상 주입 금지 |
| 모델 | 기존 `settings.tiers` 및 `llm.chat_json`, 실행 bundle 고정 | 별도 PATENT_* profile/가격/usage. 세 필수 검토는 T3, silent downgrade 금지 |
| 특허 | `patent_corpus` 압축 BLOB·checkpoint, Qdrant 전체 산업 검색. 기존 search_batch k≤10 | read-only fetch/decode/ANN primitive만 사용. 전체 적재·색인·BigQuery 실행 금지 |
| MCP | 설치 FastMCP, stateless streamable HTTP, service bearer auth | 같은 SDK의 별도 특허 registry/실제 tools/list-call 시험. 기존 mutating 도구 호출 금지 |
| frontend | App의 메뉴, query route, Workspace 내부에서 export하는 Solutions를 CaseStudy도 공유 | Patent (Test)를 Sample Case와 About us 사이. 신규 route 분기 및 owner-only optional callback |
| 배포 | export allowlist → release clone → Railway CLI. 현재 MySQL·n8n·별도 AX CPU worker | 신규 feature flags 기본 OFF, 신규 migration 명시 실행, 별도 durable 특허 worker/n8n ID 전달 |

## 보존·검증 계획

새 metadata와 `patent_*` 테이블을 사용하며 기존 테이블/컬럼/기본값/NULL/enum/index/state/report/특허 BLOB을 변경하지 않는다. 기존 코퍼스에는 이미 `patent_documents`와 `patent_checkpoints`가 있으므로 신규 migration allowlist는 접두어만으로 허용하지 않고 정확한 신규 테이블 목록으로 제한한다.

읽기 원본 연결과 새 writer 연결을 분리한다. 원본 SELECT는 일관된 transaction/전후 hash로 확인하며 `store.load_state`의 init 부작용을 피한다. 시험에서 원본 write trap과 schema fingerprint를 비교한다. API·MCP는 공통 service/governor/reducer를 사용한다.

공급자·KIPRIS·공식 작성기·특허 namespace trainer의 live 검증은 현재 NOT_RUN이다. 실제 adapter와 계약·실패 시험을 구현하고 credentials/가격/capability 검증 없이 운영 호출 또는 완료 표시를 하지 않는다. 특허 초안 생성 유료 예산은 이번 기존 TRIZ 예산 승인과 별도다.
