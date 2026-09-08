# Railway 배포 기록

기준일: 2026-09-08. 프로젝트 `elegant-freedom`, 환경 `production`.

## 접속 및 소스

- 서비스: https://trizfront-production.up.railway.app
- n8n: https://primary-production-5df6a.up.railway.app
- Backend: https://github.com/equipment0226/triz_backend (`main`)
- Frontend: https://github.com/equipment0226/triz_front (`main`)

두 저장소 모두 푸시 완료. Railway 소스에 각 GitHub 저장소가 연결되어 있다.
프런트의 첫 실행은 동일 커밋의 CLI 업로드로 시작했고, 이후 GitHub 연결과 재배포를 확인했다.
백엔드에는 공개 도메인을 만들지 않았다.

## 운영 구성

| 서비스 | 구성 |
|---|---|
| triz_front | Node 24 + React/Vite 빌드 + 인증된 API 프록시, 공개 HTTPS |
| triz_backend | Python 3.11 + FastAPI + 내장 MCP 52개 도구, private network |
| triz_backend-volume | `/data`, 첨부와 전체 상태·호출·단계·보고서 파일 |
| MySQL | 기존 MySQL 9.4 서비스, TRIZ 업무 데이터 |
| Primary / Worker | 기존 n8n 2.37.10, Redis queue 실행 |
| Postgres / Redis | 기존 n8n 내부 데이터와 큐 |

Primary·Worker의 기존 DB 연결과 encryption key는 유지했다. 사용자가 승인한 LLM 키와
별도의 신규 서비스 토큰·gateway 토큰을 Railway 환경변수에 설정했다.
실제 키와 데모 접속 비밀번호는 GitHub에 포함하지 않았다.

## 확인한 동작

- 인증 없는 `/api` 접근 차단, 인증 후 화면·이력·API 정상 응답.
- 실제 Edge 브라우저에서 홈페이지 → Sample Case → 분석 workspace 표시. JavaScript 오류 없음.
- 가상 제조 사례 1건과 텍스트 첨부 전송 → n8n worker → MCP → 실제 DeepSeek 호출.
- 사전 심층 질문에서 WAITING_HUMAN 정지 → 답변 전송 → 후속 분석 단계 진행.
- 실제 MySQL의 단계·모델 호출 저장, `/data/storage`의 첨부·상태·단계·호출 파일 보존 확인.
- 재배포 후 같은 MySQL 기록과 영구 파일 접근 확인.
- Jinja 보고서 템플릿을 운영 컨테이너에서 컴파일 확인.
- FEEDBACK 대기 중 동일 단계 요청 2회 재전송 시 추가 LLM 호출 없음. 이전 epoch 요청 거부 확인.

가상 사례는 배포 동작 검증용이다. 현업 실측 데이터나 답변 정확도의 검증 사례로 취급하지 않는다.
실제 모델 결과로 해결안 10개, 도식 29개, 전문가 6명의 평가를 포함한 보고서를 생성했다.
HTML 다운로드(약 106 KB)와 ZIP 31개 파일의 무결성을 확인했다. 해결안 10개 모두 근거 미확보 항목이
있어 표시되며, 이를 검증된 특허 기반 해결 사례로 취급하지 않는다. 현재 테스트는 보고서 생성 후
FEEDBACK 대기 상태로 보관한다. 품질 평가를 가장한 피드백을 RAG에 입력하지 않았다.

해당 1건의 기록: 단계 39개, 모델 호출 기록 49개, 입력 401,315 / 출력 107,109 토큰.
설정 단가 기반 누적 비용 추정은 약 $0.236이다. 연결 수정·재시도와 검증 과정을 포함한 단일
가상 사례의 기록이므로 정상 운영 평균이나 청구서 금액으로 일반화하지 않는다.

## 배포 과정에서 수정한 문제

1. 분리된 백엔드 이미지에 보고서 템플릿이 포함되도록 export 허용 목록 보완.
2. Railway 내부 IPv4 연결과 localhost MCP 연결을 위해 IPv4/IPv6 이중 리스너 적용.
3. 내장 MCP의 동기 분석이 API event loop를 막지 않도록 장시간 도구를 별도 스레드에서 실행.

로컬 백엔드 회귀 30개, 스모크 8개, 기존 UI 회귀 5개 통과. 운영 gateway HTTP 테스트와
MCP lifespan/프로토콜·IPv4/IPv6 접속 검사 통과. 실제 API·브라우저 점검은 fixture UI 회귀와 별도로 수행했다.

## 운영 방법

1. 원본 수정 후 `python deploy/export_repositories.py`로 `release/`의 두 저장소 사본을 갱신한다.
2. 해당 저장소에서 diff 확인 → commit → `git push origin main`.
3. Railway에서 해당 서비스의 배포가 SUCCESS인지 확인한다.
4. 사이트 로그인 후 이력·문제 분석·다운로드를 확인한다. DB와 `/data` 볼륨을 삭제하지 않는다.

데모 로그인 정보: 원본 작업공간 `.deployment/demo-access.txt`.
본인 계정으로 설정한 n8n 관리자 비밀번호는 이 파일과 별개다.

전체 산업별 품질 평가, 다중 사용자 격리, S3 확장, 부하·장애 복구 훈련은 후속 범위다.
