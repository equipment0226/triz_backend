# v2 로컬 검증 기록

기준일: 2026-09-08. Windows, Python 3.11, Node 24, Microsoft Edge headless.

| 검증 | 결과 |
|---|---|
| 기존 오프라인 스모크 | 8개 통과 |
| 백엔드 회귀 테스트 | 30개 통과 (배포 인증·PORT·MCP 비동기 실행 포함) |
| 실제 MCP 초기화·도구 호출 | 백엔드 테스트에 포함, ASGI transport 사용 |
| 브라우저 시나리오 | 5개 통과 |
| React/Vite production build | 성공 |
| n8n workflow JSON 참조 | 5개 노드 및 모든 연결 참조 확인 |
| Compose YAML | 7개 서비스 파싱 확인 |
| MySQL DDL | SQLAlchemy MySQL dialect 컴파일 확인 |
| 기존 PoC 저장 데이터 | 기존 6개 실행의 상태 조회 확인; 실제 모델을 통한 재개는 미실행 |
| 운영용 프런트 gateway | 실제 HTTP 인증·프록시·내부 경로 격리 테스트 통과 |
| 동일 서비스의 MCP | API lifespan + 52개 도구 + 실제 프로토콜 호출 통과 |
| IPv4/IPv6 리스너 | 실제 로컬 서버 양쪽 접속 통과 |

회귀 테스트의 DB는 임시 SQLite이고 모델 호출은 fixture다. MySQL DDL 컴파일은 실제 MySQL 실행 검증이 아니다. MCP 프로토콜 테스트는 공식 SDK client의 initialize/call과 서버 처리를 사용하지만 외부 네트워크/프록시 테스트는 아니다.

브라우저 테스트는 1440px 데스크톱 홈과 390px 모바일 화면, 메뉴 이동, 문제/첨부 전송, 이력 조회, 역질의 답변, 내부 코드 비노출, SVG·근거 부족·보고서 링크를 확인한다. 캡처는 `frontend/test-results/landing-desktop.png`, `frontend/test-results/intake-mobile.png`에 생성된다. 해당 분석 데이터는 실제 모델 응답이 아니다.

로컬 Docker Compose 자체는 미실행이다. 이후 Railway 배포에서 MySQL/PostgreSQL/Redis/n8n을 연결하고 workflow import·publish, 실제 큐 전달, DeepSeek 호출, 질문 대기·재개와 DB/파일 저장을 확인했다. 가상 입력 1건은 해결안 10개·도식 29개·평가자 6명의 보고서 생성과 HTML/ZIP 다운로드까지 확인했다. 특허 API 품질과 산업별 정확도·비용 비교 평가는 별도다. 연결 절차는 [Railway 배포 안내](../deploy/RAILWAY.md), 운영 확인 내역은 [배포 기록](DEPLOYMENT_STATUS.md)에 있다.

재현:

```powershell
.venv/Scripts/python.exe -m pytest pilot/tests -q
.venv/Scripts/python.exe pilot/scripts/smoke.py
cd frontend
npm.cmd run build
npm.cmd test
```
