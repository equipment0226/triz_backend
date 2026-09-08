# v2 로컬 검증 기록

기준일: 2026-09-08. Windows, Python 3.11, Node 24, Microsoft Edge headless.

| 검증 | 결과 |
|---|---|
| 기존 오프라인 스모크 | 8개 통과 |
| 백엔드 회귀 테스트 | 27개 통과 |
| 실제 MCP 초기화·도구 호출 | 백엔드 테스트에 포함, ASGI transport 사용 |
| 브라우저 시나리오 | 5개 통과 |
| React/Vite production build | 성공 |
| n8n workflow JSON 참조 | 5개 노드 및 모든 연결 참조 확인 |
| Compose YAML | 7개 서비스 파싱 확인 |
| MySQL DDL | SQLAlchemy MySQL dialect 컴파일 확인 |
| 기존 PoC 저장 데이터 | 기존 6개 실행의 상태 조회 확인; 실제 모델을 통한 재개는 미실행 |

회귀 테스트의 DB는 임시 SQLite이고 모델 호출은 fixture다. MySQL DDL 컴파일은 실제 MySQL 실행 검증이 아니다. MCP 프로토콜 테스트는 공식 SDK client의 initialize/call과 서버 처리를 사용하지만 외부 네트워크/프록시 테스트는 아니다.

브라우저 테스트는 1440px 데스크톱 홈과 390px 모바일 화면, 메뉴 이동, 문제/첨부 전송, 이력 조회, 역질의 답변, 내부 코드 비노출, SVG·근거 부족·보고서 링크를 확인한다. 캡처는 `frontend/test-results/landing-desktop.png`, `frontend/test-results/intake-mobile.png`에 생성된다. 해당 분석 데이터는 실제 모델 응답이 아니다.

Docker가 설치되지 않아 MySQL/PostgreSQL/Redis/n8n 컨테이너 기동·workflow import 및 실제 큐 전달은 미실행이다. 외부 LLM·특허 API를 통한 전체 문제 해결, 답변 정확도와 실제 비용/지연 비교도 미수행이다. 연결 절차는 [배포 안내](../deploy/README.md)에 있다.

재현:

```powershell
.venv/Scripts/python.exe -m pytest pilot/tests -q
.venv/Scripts/python.exe pilot/scripts/smoke.py
cd frontend
npm.cmd run build
npm.cmd test
```
