# TRIZ Studio v2

TRIZ PoC를 산업별 심층 분석·MCP·n8n·MySQL·React/Vite 기반의 공유 데모로 개편했다. [전체 설계](../docs/TRIZ_MASTER_SPEC.md), [피드백 반영표](../docs/FEEDBACK_IMPLEMENTATION.md), [배포 안내](../deploy/README.md)를 참고한다.

## 로컬 개발

저장소 루트에서 실행한다. Python 3.11+, Node 22.12+ 또는 24를 사용한다.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r pilot/requirements.txt
# .env가 없을 때만 복사한다. 기존 키는 보존한다.
Copy-Item pilot/.env.example pilot/.env
```

`pilot/.env`에 `LLM_API_KEY`를 설정한다. 로컬은 `ORCHESTRATOR=local`, `DATABASE_URL` 미설정 시 SQLite다. 기존 `pilot/data/triz.db`의 보고서를 계속 조회할 수 있다.

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.venv/Scripts/python.exe pilot/run.py
```

브라우저에서 `http://127.0.0.1:8000`을 연다. 이전 정적 UI 대신 React 빌드를 제공한다. 프론트엔드를 수정할 때 별도 터미널의 `frontend/`에서 `npm.cmd run dev`를 실행하면 `http://127.0.0.1:5173`이 API 요청을 8000 포트로 전달한다.

## 모델 역할

| 티어 | 역할 |
|---|---|
| T1 | 추출·질문·서술·피드백 정제 |
| T2 | 산업 심층 분석·기능/인과/모순·TRIZ 발명·개념·제약·특허 적용성 |
| T3 | 독립 검증·다직군 평가 |

기본은 모두 `deepseek-chat`이다. 고성능 모델을 연결할 대상은 **T2**다.

```dotenv
LLM_MODEL_T2=your-reasoning-model
LLM_BASE_URL_T2=https://your-compatible-server/v1
LLM_API_KEY_T2=
# 필요한 모델에서만 설정
LLM_JSON_MODE_T2=false
LLM_SUPPORTS_TEMPERATURE_T2=false
LLM_TOKEN_PARAMETER_T2=max_tokens
```

OpenAI 호환 Chat Completions 형식의 외부 AI 서버를 지원한다. 기존 `.env`에서 T3를 고급 추론용으로 지정했다면 새 역할에 맞게 T2 설정을 조정한다. 모델별 입력/출력 단가는 `COST_IN_PER_M_T*`, `COST_OUT_PER_M_T*`로 맞춘다.

## MCP 직접 실행

`pilot/.env`의 `TRIZ_SERVICE_TOKEN`을 임의의 충분히 긴 문자열로 설정한다. 저장소 루트에서:

```powershell
cd pilot
../.venv/Scripts/python.exe -m triz.mcp_server
```

서버: `http://127.0.0.1:8001/mcp`, Bearer 인증. `TRIZ_MCP_MODULE=s3` 같은 설정으로 그룹별 별도 프로세스를 배포할 수 있다. 기본 all 서버는 52개 도구를 제공한다. `MCP_TRANSPORT=stdio`도 지원한다.

프롬프트 도구는 `run_id`와 해당 템플릿의 `variables`를 받는다. 도구 설명에 필수 변수가 명시된다. 단독 도구는 산출물을 반환·기록하며, 자동 단계 진행은 `triz_execute_stage`가 담당한다.

## 검색·첨부·보고서

- 특허: `PATENTSVIEW_API_KEY` 또는 `TAVILY_API_KEY`가 필요하다. 미설정이면 특허 근거 부족으로 남는다.
- 논문: `EVIDENCE_PROVIDERS`로 Crossref/arXiv/OpenAlex 등 사용 공급자를 고른다. 공급자 정책 변경이나 장애 시 없는 근거를 만들지 않는다.
- 첨부: PDF, XLSX/CSV, 텍스트, 이미지. 기본 25MB/파일, 8개/요청.
- OCR: 로컬에 Tesseract와 필요한 언어팩을 설치한 경우 동작한다. 컨테이너 이미지에는 영문·한글 OCR을 포함한다. 문자를 추출하며 도면의 기하 관계를 확정하지 않는다.
- 보고서: HTML, Markdown, SVG 묶음. HTML에서 브라우저 인쇄로 PDF 저장이 가능하다.
- 파일 저장: `pilot/data/storage/runs/{run_id}/`, 원본은 `uploads/`, DB와 별도 영속 볼륨으로 보존한다.

## 검증

```powershell
# 저장소 루트
.venv/Scripts/python.exe -m pip install pytest
.venv/Scripts/python.exe -m pytest pilot/tests -q
.venv/Scripts/python.exe pilot/scripts/smoke.py
cd frontend
npm.cmd run build
npm.cmd test
```

브라우저 검증은 설치된 Microsoft Edge의 headless 모드를 사용한다. 다른 OS에서는 `playwright.config.js`의 channel을 환경에 맞게 변경하거나 Playwright Chromium을 설치해 사용한다. 테스트는 임시 DB와 모델 응답 fixture를 사용하며 유료 LLM을 호출하지 않는다.

실제 n8n/MySQL 컨테이너 연동과 실제 모델의 비용·정확도 평가는 별도다. [배포 안내](../deploy/README.md)에 연동 확인 절차가 있다.
