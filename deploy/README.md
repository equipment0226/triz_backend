# GitHub 분리 저장소 → Railway 배포

운영 주소: https://trizfront-production.up.railway.app
n8n: https://primary-production-5df6a.up.railway.app
로컬 데모 접속 계정: `.deployment/demo-access.txt` (Git 제외).

## 1. 소스

- Backend: https://github.com/equipment0226/triz_backend
- Frontend: https://github.com/equipment0226/triz_front

각 저장소의 main 브랜치, 루트 Dockerfile, railway.json을 사용한다. 원본 작업공간에서는
`python deploy/export_repositories.py`로 `release/`의 두 clone을 갱신한다.
피드백 원문·실제 환경변수·로컬 데이터는 복사하지 않는다.

## 2. 기존 Railway 프로젝트

피드백의 PostgreSQL·Redis 서비스 ID와 일치하는 `elegant-freedom`의 production 환경을 사용한다.
기존 Primary/Worker(n8n), MySQL, Postgres, Redis를 유지한다.

## 3. Backend

GitHub backend 저장소를 연결하고 `/data` 영구 볼륨을 붙인다. 단일 replica를 사용한다.
API와 MCP는 동일 프로세스에서 `/agent/mcp`로 제공되므로 파일이 동일 볼륨에 남는다.
장시간 도구는 별도 스레드에서 실행하며 IPv4·IPv6 이중 리스너를 사용한다.

| 환경변수 | 값 |
|---|---|
| PORT | 8000 |
| APP_HOST | :: |
| ORCHESTRATOR | n8n |
| TRIZ_EMBED_MCP | true |
| TRIZ_MCP_URL | http://127.0.0.1:8000/agent/mcp |
| STORAGE_DIR | /data/storage |
| MYSQLHOST / MYSQLPORT / MYSQLDATABASE / MYSQLUSER / MYSQLPASSWORD | MySQL 서비스의 동일 변수에 대한 Railway reference |
| N8N_DISPATCH_URL | http://primary.railway.internal:5678/webhook/triz-dispatch |
| TRIZ_SERVICE_TOKEN | n8n credential과 같은 임의 토큰 |
| TRIZ_APP_TOKEN | Frontend gateway와 같은 별도 임의 토큰 |
| LLM_API_KEY / LLM_BASE_URL / LLM_MODEL_T1,T2,T3 | 사용 중인 공급자 설정 |

Backend에는 공개 도메인이 필요 없다. healthcheck `/healthz`는 DB 연결을 확인한다.

## 4. n8n

Primary와 Worker의 기존 PostgreSQL·Redis·encryption key는 유지한다.
`TRIZ_API_URL=http://<backend-private-domain>:8000`, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`를 설정한다.
Primary의 `WEBHOOK_URL`은 기존 공개 HTTPS 도메인으로 설정한다.
`deploy/n8n/triz-workflow.json`을 import하고 webhook과 HTTP 노드에 동일 Header Auth credential
(`Authorization: Bearer <TRIZ_SERVICE_TOKEN>`)을 연결한 다음 publish한다.
CLI publish 후에는 Primary 재시작으로 production webhook 등록을 확인한다.

## 5. Frontend

GitHub front 저장소를 연결한다. PORT=8080, BACKEND_URL=백엔드 private URL,
TRIZ_APP_TOKEN=백엔드와 동일, DEMO_USERNAME/DEMO_PASSWORD=데모 접근 계정을 설정한다.
Generate Domain으로 HTTPS 주소를 생성한다. 로그인 후 문제·첨부·보고서 모두 이 주소로 접근한다.

## 6. 실제 구동 확인

1. Frontend와 Backend healthcheck 통과.
2. 로그인 후 화면과 DB 이력 조회 성공.
3. 문제 1건 전송 → n8n worker → MCP → MySQL 기록.
4. 사전 질문에서 WAITING_HUMAN → 답변 후 다음 단계 진행.
5. 같은 epoch/stage 재시도에서 유료 작업 중복 실행 방지.
6. 첨부·단계·호출 기록과 보고서가 `/data/storage`에 보존.

GitHub push 성공과 서비스 구동 성공은 별도로 기록한다. 실제 호출 없이는 LLM 품질·비용을 확정하지 않는다.

공식 안내: [GitHub/Docker 서비스](https://docs.railway.com/services),
[환경변수 참조](https://docs.railway.com/variables), [CLI](https://docs.railway.com/cli).
