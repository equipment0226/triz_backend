# 피드백 반영표

기준: `feedback/feedback.md`, 2026-09-08. 코드 구현과 실제 외부 서비스 검증을 구분한다.

| 피드백 | 반영 내용 | 주요 파일 | 검증/조건 |
|---|---|---|---|
| 1. n8n·MCP·MySQL, 속도·확장성 | n8n 큐용 import workflow, 인증된 MCP bridge, 52개 MCP 도구, MySQL 저장, 단계/epoch 잠금, 독립 트랙 병렬화, 티어별 서버 설정 | `deploy/`, `triz/mcp_server.py`, `mcp_client.py`, `pipeline.py`, `store.py`, `nodes.py` | MCP 초기화·호출, 체크포인트·중복·동시성·병렬 격리 테스트. 실제 Docker/MySQL/n8n 연동은 환경 부재로 미검증 |
| 2. 산업별 분석 깊이, T2, 프롬프트, 페르소나, 첨부 | 산업 7종·난이도 3종 카탈로그, 사전 심층 질문, 반도체 복합 이론·적용 조건·실험, T2 핵심 추론, 산업별 검토자, PDF 표/OCR/XLSX/측정값 출처 | `config/industries.yaml`, `triz/domain.py`, `agent.py`, `personas.py`, `prompts/`, `tools/docparse.py` | 라우팅·스위칭·답변 반영·블라인드 컨텍스트·Excel/업로드 검사. 현업 품질은 실제 모델 평가 필요 |
| 3. 시각화·보고서·인격 아이콘·설계 최신화 | 상태 기반 SVG, S1/S2/F와 실제 S3, 기능/인과/9 Windows/자원/IFR/모순/트리밍/기법/개념 도식, HTML·MD·ZIP, 전문가 아이콘 | `triz/visuals.py`, `presentation.py`, `render.py`, `templates/report_visual.md.j2`, `report.html.j2`, `docs/TRIZ_MASTER_SPEC.md` | 도식 존재·escaping·독립 HTML·파일 저장, 브라우저 렌더 검사 |
| 4. 특허 탐색 교정, 타산업 이식, 솔루션별 근거, 추가 후보 | S5 사전 타산업 탐색 + 최종 특허·논문 분리 검색, index 기반 대조, 이식 조건 요구, 동일 수단은 연결/새 수단은 별도 후보, 검색 링크/성숙도 과장 제거 | `triz/evidence.py`, `tools/scholar.py`, `prompts/P_EVIDENCE_*`, 보고서 템플릿 | 공급자 분리·검증 범위·근거 부족·없는 index 거부. 특허 공급자 키와 실제 검색 결과 필요 |
| 5. React/Vite 데모, 5개 메뉴, PC·모바일 호환, 사용자 중심 흐름 | 자체 제작 도형, 공개 기업 활용 사례, Tool 소개, 새 문제·첨부·모드, 캐릭터 안내, 질문/확정/보류 판단, 단계 의견·전문가, 해결안·도식·보고서·피드백, 이력 검색, 빈 About us | `frontend/` | Vite build, Edge PC/모바일 Playwright. 분석 데이터는 테스트 fixture 사용 |
| 6. 깊이와 정확도를 유지하면서 토큰 절감 | 입력 압축, 실행 내 캐시, 제한된 검색 컨텍스트, 핵심 검증, 재시도·승급 상한, SDK 재시도 중첩 제거, 예약 예산, 코드 기반 도식·형식 | `triz/agent.py`, `llm.py`, `prompts_registry.py`, `config/triz.yaml` | 예산 이전 중단·성공 재사용·실패를 PASS로 오인하지 않는 테스트. 절감률 실측은 미수행 |
| 7. 모든 결과 DB와 파일 저장, 향후 S3 | MySQL 상태·단계·이벤트·피드백, 원본 첨부 SHA, 전체 입력과 출력 파일, 단계 스냅샷, 보고서·SVG, SQLite 이전 도구 | `triz/store.py`, `context.py`, `render.py`, `scripts/migrate_sqlite.py` | 임시 DB 저장·파일 보존·MySQL DDL 테스트. 현재 API/MCP 공유 볼륨 필요, S3 미구현 |
| 8. 답변 품질 개선 | 고정 부품 수 강제 제거, 도메인 이론의 성립 조건, 관측/가설 분리, 검증 지표·대조 실험·반증 기준, 이식 조건, 제약 보류 유지 | `triz/domain.py`, `verify.py`, `schema.py`, `prompts/P_S3_FUNCTION_MODEL.md`, `P_S6_CONCEPT.md` | 구조·회귀 검증 완료. 실제 반도체 등 현업 정확도는 T2 공급자와 전문가 평가 필요 |

## 운영 반영 전 필요한 실제 검증

1. 대상 n8n에서 import 후 Header Auth credential을 두 노드에 연결하고 workflow 활성화.
2. MySQL·Redis·PostgreSQL 연결과 API/MCP의 공유 storage 구성.
3. 실제 LLM·특허 공급자 키로 대표 문제 수행.
4. 동일 예산·입력 기준으로 PoC/v2 지연·토큰·비용과 현업 품질 비교.

현재 구현을 외부 서비스 배포 완료나 정확도 향상 실측 완료로 해석하지 않는다. 상세한 구성·정책·한계는 최신 마스터 설계서에 있다.
