# 76표준해·5+2 분리 접근 화면 및 보고서 갱신

2026-09-29. 기존 TRIZ76와 MATRIZ7 변경을 보존하고 Introduction, 자료도감, 보고서의 설명과 도식을 공통 지식에 맞췄다.

## 반영 내용

- 원전 대조된 76개 표준해 전체를 확인하고 기본 도식 26개의 기전·전제를 정정했다.
- 공식 하위 방법 11개, 번호 없는 대안 76개, 발전·적용 순서 13개의 상세 도식을 추가했다. 대안 번호는 공식 표준해 번호로 표시하지 않는다.
- 2.4.2의 입자와 입자 포함 물질의 발전은 독립된 두 경로로 표현한다. 원전의 조건·변환·정정 근거·출처·버전을 함께 표시한다.
- 공간·시간·관계(조건)·방향·시스템 수준의 5가지 분리, 동시 충족·우회의 2가지 보완 접근을 구분한다. 7개 전용 도식, 요약 도식, 과거 조건 분리 도식 총 9개를 공유한다.
- 우회의 고정 권장 원리 목록은 비어 있는 원전 계약을 유지하고 전체 40원리를 탐색하도록 연결한다.
- 보고서의 일반 설명 도식은 표준해별 한 번만 붙이며 실제 저장된 적용 구조와 검토 결과는 유지한다. 과거 4가지 분리 기록을 7가지 검토를 수행한 것처럼 바꾸지 않는다.
- 정적 자산은 공통 Python 렌더러에서 생성한다. 기본 76 + 상세 100 + 분리 9 = 총 185 SVG. `frontend/public/knowledge/diagram-manifest.json`에서 버전과 개별 SHA-256을 추적한다.

## 주요 파일

- 지식: `pilot/triz/knowledge/standards_76.json`, `separation.json`
- 공통 도식: `pilot/triz/standard_diagrams.py`, `standard_diagram_specs.py`, `standard_detail_specs.py`, `separation_diagrams.py`
- 보고서: `pilot/triz/visuals.py`, `render.py`, `pilot/templates/report_full.md.j2`
- 화면: `frontend/src/components/StandardsExplorer.jsx`, `StandardDetailSections.jsx`, `SeparationReference.jsx`, `GuideVisual.jsx`, `frontend/src/pages/MaterialLibrary.jsx`
- 동기화: `frontend/scripts/sync-knowledge.py`

## 검증

- 표준해 집중 회귀 33개 통과: 76 기본 SVG 일치, 전체 176개 도식의 구조·원문 조건, 공식 하위 번호/대안/발전 순서, 미등록 상세 추측 방지, 저장 모델 보존.
- 보고서 통합 6개 suite 53개 통과: 위 테스트와 일부 중복. 새 분리 도식 12개 검사, AX 고정 결과 보존, 참고 도식 배치와 중복 방지 포함.
- 프런트 관련 고유 회귀 9개 통과: 최신 지식 일치, 상세 탐색·검색, 7개 접근, BYPASS 40원리, 좁은 화면.
- 최종 Vite 빌드 성공. 기존 큰 청크 경고는 남아 있다.
- Edge에서 185개 SVG를 렌더링하고 텍스트 경계 이탈 0건 확인.
- 합성 보고서 38개 도식/11개 절을 모바일 390px와 데스크톱 1440px에서 확인. 페이지 넘침·중복 장 번호·브라우저 오류 없음. 저장 상태 불변, 모델 호출 0.

도식은 표준해의 관계·작동 원리를 설명하는 개념도이며, 실제 프로젝트의 물리적 성능 검증 결과를 뜻하지 않는다.

## 배포 추적

- 첫 MATRIZ7 백엔드 배포: `7ec9a79a-76a2-4dd3-bb8f-4dad1ae6d79d`, SUCCESS 및 런타임 16개 파일 일치 확인.
- 후속 화면·보고서 배포 영수증: `.deployment/knowledge-ui-release-20260929.json`.
- 기존 최신 Git 기준에 검토한 파일만 덧붙인 불변 아카이브를 배포하며 이전 main으로 롤백하지 않는다. 운영 데이터 변경과 유료 LLM 호출은 없다.

상세 근거: `.deployment/knowledge-ui-20260929/standards-audit.json`, `standards-tests.xml`, `visual-verification.json`, `.deployment/matriz7-research/report-diagrams.xml`.
