# 특허 초안: 적용 조건 필수 입력

2026-09-16 작업. 선택한 TRIZ 아이디어는 발명의 출발점이며, 실제 적용 조건을 확인한 발명정보와 동일시하지 않는다.

## 구현된 동작

1. 비공개 특허 case 생성과 동시에 변경사항·제약조건·위험요소의 필수 질문 3개를 서버에 저장한다. 작성 시작 전에 사용자가 직접 답변해야 한다. 일부 답변만 저장할 수 있지만 세 항목이 모두 채워지기 전에는 초안 모델 호출을 발급하지 않는다. 이 단계는 모델 키나 유료 예산 없이 사용할 수 있다.
2. 추가 기술 질문과 검토 중 역질문도 서버에 저장한다. 필수 질문에 답변하지 않으면 후속 작성·G1/G2 승인이 차단된다. '없음' 또는 '미확인'이라는 사용자의 명시적 답변은 허용하며, 미확인을 측정·검증된 사실로 승격하지 않는다.
3. 입력은 원본 TRIZ state를 변경하지 않고 patent 전용 artifact/snapshot에 기록한다. API와 MCP의 공통 governor, 그리고 실제 작업 실행 경계에서 필수 입력을 확인한다. 모델이 생성하는 질문은 필수 질문 ID와 원본 source, 사용자 입력, 승인·검토 설정을 덮어쓸 수 없다.
4. 답변 변경 시 관련 파생 초안의 현재 버전과 승인을 무효화한다. 옛 초안과 검토 기록은 삭제하지 않는다. 이전과 똑같은 문장을 재생성해도 바뀐 적용 조건의 승인으로 재사용할 수 없다. T3 검토는 현재 자료의 정확한 버전에만 유효하다.
5. 같은 답변을 다시 저장하면 산출물 버전과 예약 비용을 유지한다. 변경으로 실행하지 않게 된 대기 작업은 유료 호출 없이 예약을 해제한다. 이미 진행된 호출은 비용을 정산하되 옛 결과가 현재 초안을 덮어쓰지 못하게 한다. 옛 호출 완료 전에 새 입력으로 재개한 경우에도 새 작업이 유실되지 않는다.
6. 화면에서 답변 수정, 부분 저장, 새로고침, 로그인 복원, 저장 전 입력 유지가 가능하다. 기존 로그인 callback은 유지하고, 허용된 특허 route만 짧은 수명으로 복원한다. 답변 본문은 로그인 복원용 브라우저 저장소에 복사하지 않는다.
7. 기존 TRIZ 자동 조율과 도면 생성 범위는 변경하지 않았다. 필수 사용자 입력은 특허 초안 작성 흐름에 적용한다.

## 수정 파일

- `pilot/patent_draft/intake.py`: 고정된 필수 질문과 입력 완료 판정.
- `pilot/patent_draft/domain.py`: 질문 ID·수정 대상 계약.
- `pilot/patent_draft/service.py`: 생성·승인·MCP 실행 조건, 질문 답변 반영, 영향 버전 무효화, 예약 정산.
- `pilot/patent_draft/api.py`: 질문과 필수 입력 상태 읽기.
- `pilot/patent_draft/runtime.py`: 일시 중단된 사건이 다른 사건의 worker 실행을 막지 않도록 처리.
- `frontend/src/pages/Patent.jsx`: 필수 질문·편집·저장·복원 화면.
- `frontend/src/lib/patentNavigation.js`, `frontend/src/App.jsx`, `frontend/src/pages/Account.jsx`: 기존 로그인 경로를 이용한 특허 화면 복원.
- `pilot/tests/test_patent_intake.py`, `pilot/tests/test_patent_draft.py`, `pilot/tests/test_patent_mcp.py`, `frontend/tests/patent-intake.spec.js`: 제어 흐름·실제 MCP transport·브라우저 회귀시험.

## 검증 범위

실행 명령:

```powershell
.\.venv\Scripts\python.exe -m pytest pilot/tests -q
cd frontend
npm.cmd test -- tests/patent-intake.spec.js tests/ax-workflow.spec.js
npm.cmd run build
npm.cmd run test:server
```

브라우저 시험은 로컬 API fixture를 사용한다. 서버 계약시험은 격리 SQLite DB, 실제 service/reducer/API/MCP transport, 테스트 전용 모델 응답을 사용한다. 유료 모델의 기술·법률 판단 정확도나 실제 Google OAuth 공급자의 동작을 검증한 결과와 구분한다.

결과: 전체 backend **543 passed**(Qdrant 로컬 검색 관련 경고 1개), 필수 입력·로그인 복원 및 기존 AX 화면 browser **5 passed**, production frontend build 성공, gateway **1 passed**. 초기 MCP 시험은 기존 프로토콜의 JSON text 반환을 structuredContent로 가정한 테스트 오류와 singleton 수명 오류가 있었으며, 현재 설치 프로토콜에 맞춰 수정 후 전체 재실행으로 확인했다.

원본 보호 기준선의 16개 파일 hash를 확인한다. 전역 모델·예산·평가 설정, 기존 state/serializer/pipeline, 특허 코퍼스, 기존 MCP, frontend 인증 서버·gateway 파일은 변경하지 않는다.

## 배포와 잔여 범위

이 변경은 개발 작업공간의 특허 모듈에 적용했다. 운영 DB migration, 유료 모델 호출, main push와 특허 모듈 실제 배포는 수행하지 않았다. 새 환경변수나 운영 예산 증액은 없다. 필수 질문 생성·저장·수정 자체에는 모델 호출 비용이 들지 않는다.

확인한 운영 저장소 HEAD:

- backend `equipment0226/triz_backend`: `97551c68516f948118f00ba4c1afa8be8c4a6768`
- frontend `equipment0226/triz_front`: `e8d23d450c161be891c7cb208f777fbe5dcabb50`

특허 전체 모듈은 아직 배포 완료가 아니다. 필수 T3 실제 공급자 검증, KIPRIS live 권한·응답 검증, 공식 작성기 형식 검증은 `NOT_RUN`이다. 기존 trainer의 특허 namespace 계약은 지원되지 않아 RL 상태는 `TELEMETRY_ONLY`다. 규칙별 전체 근거 검증과 공식 서식의 정확한 레이아웃 등 나머지 구현·검증 범위는 별도로 남아 있다. 본 시험을 이 항목들의 완료 증거로 사용하지 않는다.
