# AX / QLearn 변경 계획 및 보존 기준

2026-09-28. 기준: 현재 작업공간 소스. 루트에 Git 메타데이터/AGENTS.md가 없으므로 HEAD·브랜치·diff는 확인 불가. 배포용 별도 체크아웃은 수정하지 않는다. 변경 전 소스는 `.tmp/ax-refactor-before`에 보관한다(비밀 설정 제외).

## 보존 매트릭스

| 기능 | 현재 구현 | 보존 | 변경 이유 | 회귀 검증 |
|---|---|---|---|---|
| 13단계/중단·재개 | pipeline.py, context.py | 단계 키·순서·기존 payload·사용량 | 의미 변경 episode와 transport epoch 분리 | execution_lifecycle, gate_resume, provider_interruptions |
| 필수 기법 | solve_contract.plan, coordinator.complete_required, nodes._run_tracks | 최신 전 기법 배치·완료 트랙 재사용 | 신규 LITE A/B/E/H, FULL A/B/C/E/F/G/H, DEEP 전 기법 | mode tracks 및 신규 계약 테스트 |
| ARIZ | nodes._track_d_ariz | 최신 Part 1–7 중 구현된 1/2/3/4/5/6/7; Part6 제안 전용 | LITE/FULL 실행기에서도 금지 | ariz 관련 회귀 |
| 통합·원본 | idea_consolidation.consolidate, nodes._merge | 최대 10개 대표 선정, 전 원안 처분 이유·leaf 출처, tradeoff 의미 | 원시 재고/작업 출처 분리 | idea_consolidation, ax_portfolio_completion |
| 검토/복구 | quality, coherence, coherence_recovery | 원본 유지·새 후보 독립 검토·S7 재검토 | DEEP optional 0, 실제 다중 작업 선택 | ax_coherence*, pipeline_quality |
| 정산/스냅샷 | ledger, gateway | fence·UNKNOWN 예약·불변 snapshot·프로젝트 cap | 작업별 명시 귀속 | ax_phase1, project_budget |
| 효과 선택/검토 | runtime.effect_candidates, catalog_binding, s7_gate | lexical 후보 생성·legacy accept/drop·CONDITIONAL | 조건·동의별 이력, 별도 ranker | 신규 효과 이력/권한/학습 테스트 |
| Q 학습 | learning, registry, worker | v1/v2 읽기·CPU worker·수동 canary | 행동별 특징·지원 영역·명시 transition·task별 pointer | ax_learning 및 신규 Q 테스트 |
| 보고서 | render, presentation, ax.report | 본문·도식·라벨·동결 snapshot | 진단은 선택 확장만 | ax_full_report, summary_labels |
| 특허/RAG/MCP | patent_draft, rag, mcp_* | 기존 입력·권한·검색·도구 이름 | 변경 없음 | 기존 전체 회귀 |

## 신규 실행 계약

공통 trace/coherence/portfolio/budget는 유지하며 optional orchestration/recovery/routing은 DEEP에서 끈다. 기존 bundle은 새 계약을 추정해서 붙이지 않는다. 신규 bundle에 모드·카탈로그·모델·정책·예산을 고정한다. 기존 2 USD cap은 올리지 않는다. LITE optional 한도는 FULL보다 작으며 검토 예약을 우선한다. 미입력/실패/예산 미완료/진짜 적용 불가를 구별한다.

최신 코드에는 이미 `complete_required`, 원안 전수 통합 및 최대 10개 대표 선정, Part6, 일부 replan 무효화가 있다. 요청 문서의 과거 문제 설명을 근거로 이를 되돌리지 않는다.

## 순서

1. 격리 SQLite 기준선 회귀, 변경 전 사본 및 보존 매트릭스.
2. 신규 모드 계약과 필수 실행/optional 분리.
3. 명시 작업 인스턴스·실행/정산 귀속·semantic 재계획.
4. 공통 효과 사용/검토 수집·기존 보류 화면 확장·조건 이력.
5. 별도 routing Q/effect ranker CPU 학습·registry·worker·fallback.
6. 신규/기존 회귀와 offline smoke, 변경/제한/검증 문서.

외부 LLM·운영 DB·배포·push는 수행하지 않는다. 합성 학습 결과는 실성능 향상으로 표시하지 않는다.
