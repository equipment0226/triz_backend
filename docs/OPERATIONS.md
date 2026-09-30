# 설치와 운영

최종 갱신: 2026-09-30. 현재 코드의 동작과 기본값을 설명한다. 운영 서버의 실제 환경변수·모델·잔액을 확인한 문서는 아니다. 아래 실행 명령은 운영 절차 예시이며 이 문서 작성 중 실행하지 않았다.

## 백엔드 저장소에서 로컬 시작

백엔드 Git 저장소를 clone한 루트에 `pilot/`이 있는 구성을 기준으로 한다. 프런트는 [별도 저장소](https://github.com/equipment0226/triz_front/tree/5f4039073aee7a5168378d1035f18e3336980ef9)다. API만 실행해도 프런트 소스·빌드가 자동으로 생기지는 않는다.

Python 3.11을 준비한 뒤 PowerShell에서 실행한다.

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r pilot/requirements.txt
Copy-Item -LiteralPath pilot/.env.example -Destination pilot/.env
Set-Location pilot
../.venv/Scripts/python.exe run.py
```

기존 `.env`가 있으면 복사로 덮어쓰지 말고 필요한 항목만 편집한다. macOS/Linux에서는 `python3.11 -m venv .venv`와 `.venv/bin/python`을 사용한다. 의존성은 [requirements.txt](../pilot/requirements.txt), 환경 예시는 [.env.example](../pilot/.env.example), 실행 진입점은 [run.py](../pilot/run.py)다.

개발 기본 구성은 `ORCHESTRATOR=local`, SQLite `pilot/data/triz.db`, 파일 저장 `pilot/data/storage`다. 실제 분석 생성에는 모델 API 키가 필요하다. 환경을 로컬 DB·파일 경로로 분리한 다음 시작한다. API 시작 시 중단 복구 감시와 설정에 따른 AX worker가 동작하므로, 운영 DB를 연결한 상태의 단순 서버 시작은 읽기 전용 점검이 아니다.

OCR에는 Tesseract 실행 파일과 필요한 언어팩이 별도로 필요하다. `OCR_LANG` 기본값은 `eng`이며 한국어 자료에 필요한 언어팩과 값을 맞춘다. Docker 정의는 Tesseract·한국어 언어팩·나눔 글꼴을 설치한다. 특허 임베딩은 최초 사용 시 고정된 모델 파일을 내려받을 수 있어 저장 공간과 외부 다운로드 연결이 필요하다.

첨부 추출은 별도 worker에서 실행한다. 시간·메모리·동시 실행 설정과 실패 파일의 정리 범위는 [보안 점검](SECURITY.md)을 참고한다. 기존 프로젝트의 첨부는 이 정리 대상이 아니다.

프런트 개발 서버는 별도 저장소에서 `npm ci`, `npm run dev`로 시작한다. 해당 [Vite 설정](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/vite.config.js)은 `/api`를 `127.0.0.1:8000`으로 전달한다. 운영 [server.mjs](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/server.mjs)는 `BACKEND_URL`과 서버 보관 `TRIZ_APP_TOKEN`, 로그인 세션을 사용한다. 비밀값을 브라우저 번들에 넣지 않는다.

## 설정 우선순위와 실제 환경변수

[settings.py](../pilot/triz/settings.py)는 `pilot/.env`를 읽고 `config/triz.yaml`, `personas.yaml`, `rubrics.yaml`을 로드한다. 환경변수는 **코드에 연결된 항목에 한해서** 기본값/YAML을 덮어쓴다. 모든 YAML 키가 같은 이름의 환경변수로 자동 변환되는 구조는 아니다. 생성된 AX 실행은 자기 bundle의 설정을 사용할 수 있다.

| 영역 | 환경변수·기본 동작 |
| --- | --- |
| API | `APP_HOST=127.0.0.1`, `APP_PORT=8000`. `PORT`가 있으면 포트 우선. `LOG_LEVEL=INFO` |
| 인증 | `TRIZ_APP_TOKEN`, `REQUIRE_USER_AUTH`. 사용자 인증 기본은 app token 존재 시 true. `TRIZ_SERVICE_TOKEN`은 내부 실행/MCP용. `LEGACY_OWNER_EMAIL`은 기존 기록 소유자 연결 설정 |
| DB | `DATABASE_URL` → `MYSQL_URL` → `MYSQLHOST`와 `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLPORT`, `MYSQLDATABASE`. 없으면 `DB_PATH=./data/triz.db`의 SQLite. 상대 경로는 `pilot/` 기준 |
| 파일 | `STORAGE_DIR=./data/storage`, `MAX_UPLOAD_MB=25` |
| 실행 | `ORCHESTRATOR=local`, `N8N_DISPATCH_URL`, `TRIZ_MCP_URL=http://127.0.0.1:8001/mcp`, `TRIZ_EMBED_MCP=false` |
| 공통 LLM | `LLM_API_KEY`, `LLM_BASE_URL=https://api.deepseek.com/v1`, `LLM_TIMEOUT_SEC=300`, `LLM_MAX_RETRIES=2` |
| tier별 LLM | `LLM_MODEL_T1/T2/T3`의 **코드 기본은 모두 `deepseek-chat`**. 각 `LLM_API_KEY_T*`, `LLM_BASE_URL_T*`가 공통 값을 우선한다. 이는 운영 모델 확정값이 아니다. |
| 출력·추론 옵션 | `LLM_MAX_TOKENS_T1=16000`, T2/T3 `32000`; `LLM_TEMPERATURE_T1/T2/T3=0.1/0.3/0.7`. `LLM_JSON_MODE_T*`, `LLM_SUPPORTS_TEMPERATURE_T*`, `LLM_TOKEN_PARAMETER_T*`, `LLM_THINKING_MODE_T*` 지원. thinking 값은 빈 문자열/`enabled`/`disabled` |
| 가격 설정 | `COST_IN_PER_M_T*`, `COST_OUT_PER_M_T*`. 기본 0.28/0.42 USD/백만 토큰. 공식 DeepSeek Flash는 아래 비피크 산정 기준이 우선한다. 다른 모델은 설정 단가를 유지한다. |
| 실행 기본 변경 | `TRIZ_DEFAULT_MODE`, `PIPELINE_PARALLEL_WORKERS`, `TRIZ_PROJECT_BUDGET_USD`. 금액 값은 새 실행의 `run.budget_usd`와 `ax.hard_budget_usd`를 함께 설정한다. |
| AX | `TRIZ_AX_ENABLED`는 **새 실행**의 AX 활성화에 사용. `TRIZ_AX_WORKER_ENABLED` 기본 true는 API의 별도 worker 감시를 제어. 나머지 계약은 [triz.yaml](../pilot/config/triz.yaml)과 [mode_contract.py](../pilot/triz/ax/mode_contract.py) |
| 일반 웹 검색 | `SEARCH_PROVIDER=none`; `tavily`와 `TAVILY_API_KEY`로 일반 웹 검색 활성화 |
| 근거 공급자 | `EVIDENCE_PROVIDERS` 코드 기본 `crossref,openalex,arxiv,patentsview,tavily`. 키 필요한 provider는 해당 키가 있어야 사용. `.env.example`의 명시 목록은 이 기본값과 다를 수 있다. |
| 특허 검색 | `PATENT_SEARCH_PROVIDER=vector`, `PATENT_DATABASE_URL`, `QDRANT_URL`, `QDRANT_API_KEY`, `PATENT_VECTOR_COLLECTION=patents_e5_small_v1` |
| 특허 성능·규모 | `PATENT_EMBEDDING_THREADS=2`, `PATENT_SEARCH_TIMEOUT_SECONDS=20`, `PATENT_MIN_SCORE=0.75`, `PATENT_DB_MAX_BYTES=200000000000`, `PATENT_VECTOR_MAX_POINTS=10000000` |
| 별도 특허 공급 경로 | `FREE_PATENT_SEARCH=true`, `PATENTSVIEW_API_KEY`; BigQuery 명시 선택 시 `BIGQUERY_PROJECT_ID`, `BIGQUERY_LOCATION`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `BIGQUERY_MAX_BYTES_BILLED`, `BIGQUERY_MONTHLY_BYTE_LIMIT`, `BIGQUERY_TIMEOUT_SECONDS`, `BIGQUERY_CACHE_SECONDS` |

분석 중 최대 출력은 tier 기본값 외에도 `solutions.track_max_tokens`, `analysis.ceca_max_tokens` 등 호출별 설정의 영향을 받는다. T1/T2/T3는 코드상 역할 분류이지 서로 다른 상용 모델 이름을 보장하는 등급이 아니다.

현재 YAML의 새 프로젝트 예산 기본은 2 USD, 활성 실행 시간 예산은 90분이다. 환경변수와 실행별 bundle이 우선할 수 있다. 설정 변경이나 재개가 기존 프로젝트의 누적 비용·금액 한도를 초기화하지 않는다.

## Flash 테스트 비용 산정

공식 `api.deepseek.com`의 `deepseek-flash`, `deepseek-v4-flash`, `deepseek-v4-flash-vision-exp`는 요청에 따라 **비피크 단가를 고정 적용**한다. 2026-09-30 확인한 [공식 가격표](https://api-docs.deepseek.com/quick_start/pricing/) 기준으로, 100만 토큰당 입력 캐시 미적중 $0.15, 적중 $0.003, 출력 $0.60이다. 피크 시간대도 프로그램은 이 기준으로 추정하므로 실제 공급자 청구액과 다를 수 있다. Pro 등 다른 모델은 기존 설정 단가를 따른다.

계산식은 `(미적중 입력 × 0.15 + 적중 입력 × 0.003 + 출력 × 0.60) / 1,000,000` USD다. 출력에 포함된 reasoning 토큰은 다시 더하지 않는다. 캐시 사용량은 API 응답의 hit/miss 또는 `prompt_tokens_details.cached_tokens`로 확인한다. 카운터가 없거나 서로 맞지 않으면 캐시 사용량을 미확인으로 남기고 전체 입력에 미적중 단가를 적용한다.

TRIZ 분석과 특허 초안 작성이 같은 [계산 모듈](../pilot/triz/model_pricing.py)을 사용한다. 호출 전 예약액은 예상 캐시 할인을 넣지 않으며, 호출 후에는 각 응답의 실제 토큰과 캐시 카운터로 정산한다. 재시도 중 발생한 사용량도 합산한다. 계산 단가와 캐시 근거는 TRIZ 호출의 `meta.requests[].pricing`, 특허 호출의 `provider_receipt.boundary_contract.pricing`에 저장한다.

이 정책은 적용 이후 새 호출부터 사용한다. 과거 비용은 자동으로 정정하지 않는다. 진행 중인 분석의 기존 모델·추론 설정과 이미 완료된 호출의 재사용도 유지한다. 트랙 비용 예측은 단가 기준이 다른 과거 표본을 섞지 않는다. 표시 금액이 줄었다는 사실만으로 실제 추론 사용량이나 품질이 개선됐다고 판단하지 않는다.

사용자가 완료된 프로젝트의 비용 정정을 요청하면 [cost_restatements.py](../pilot/triz/ax/cost_restatements.py)로 실제 호출별 사용량을 재산정한다. 검토한 계획과 원본 task 집합이 같은지 확인한 뒤 `COST_RESTATEMENT_APPLIED` 이벤트를 한 번 기록한다. 완료 전이거나 사용량 미확인 호출이 있으면 적용하지 않는다. 정정 이벤트의 호출별 금액을 프로젝트 누적 비용·잔여 예산·보고서에 반영하며, 원본 task·API 응답·개별 Step의 당시 비용·보고서 snapshot은 보존한다. 새 호출을 만들거나 토큰 수를 바꾸지 않는다.

정정 이후 학습 데이터의 비용 항목도 이 값을 읽되, 정정 이전 시점의 데이터 조회는 당시 금액을 유지한다. 기존 피드백·검토 점수·학습 모델을 덮어쓰거나 정정만으로 모델을 자동 발행하지 않는다. 과거 Step 비용과 정정 후 합계를 비교할 때는 정정 이벤트의 task별 대조표를 함께 확인한다. 단계 귀속을 확인할 수 없는 호출은 `UNATTRIBUTED`로 남긴다.

## DB, 파일, 검색 구성

[store.py](../pilot/triz/store.py)는 실행 목록과 전체 상태 JSON, 단계 기록, LLM 호출, 이벤트, 피드백, RAG, 계정·세션을 SQL에 저장한다. [AX ledger](../pilot/triz/ax/ledger.py)는 같은 애플리케이션 DB에 `ax_*` 버전·작업·비용·평가·학습 테이블을 둔다. 특허 corpus는 `PATENT_DATABASE_URL`의 별도 저장소를 사용한다.

`STORAGE_DIR`에는 업로드와 `runs/{run_id}/` 상태·단계·호출 archive, 모델 캐시 등이 들어간다. DB만 백업하거나 볼륨만 남겨서는 완전한 복구 자료가 되지 않는다. 연결된 DB, 업로드/산출물 볼륨, 코드·설정 버전을 함께 보존한다. 백업과 복구는 별도 승인된 운영 작업으로 수행한다.

기본 특허 경로는 Qdrant ANN 검색→전용 SQL 서지 조회다. E5 임베딩 모델과 collection 차원이 맞아야 한다. `vector` 선택 시 실패를 BigQuery 유료 질의로 자동 대체하지 않는다. corpus 적재·벡터 생성·인덱스 재구축은 분석 API의 단순 상태 확인과 별개이며 데이터를 변경한다. [patent_corpus.py](../pilot/triz/patent_corpus.py), [vector_patents.py](../pilot/triz/tools/vector_patents.py), [scripts/patent_corpus.py](../pilot/scripts/patent_corpus.py)를 먼저 확인한다.

### 특허 corpus 적재·복구

[patent_ingest.py](../pilot/triz/patent_ingest.py)는 BigQuery 공개 특허의 필요한 서지·초록 열을 `tabledata.list`로 읽는다. SQL 분석 쿼리를 제출하는 검색 경로와 다르다. 공개일 2000-01-01 이상이고 제목이 있는 공개 문서를 보관하며, 제목은 1,500자·초록은 24,000자까지 저장한다. 청구항·명세서·도면 전문을 보관한 DB는 아니다.

원본 버전이 바뀌면 필요한 열을 다시 순회하고, 같은 내용의 해시는 SQL 갱신·재임베딩을 생략한다. 문서와 다음 페이지 토큰은 함께 커밋한다. Qdrant 저장 확인 후에만 `pending`을 해제한다. 삭제된 원본의 자동 삭제 전파는 없다. 공개일 최댓값이나 조회 표본만으로 전체 적재 완료를 판단하지 않는다.

승인된 적재 환경의 `pilot/`에서 사용하는 명령은 다음과 같다. `status`도 진입 시 `corpus.init()`을 호출하므로 엄격한 운영 읽기 전용 검사로 분류하지 않는다.

| 명령 | 범위 |
| --- | --- |
| `python scripts/patent_corpus.py probe` | 외부 메타데이터와 원본 표본 다운로드. SQL 분석 쿼리·corpus 적재 없음 |
| `python scripts/patent_corpus.py import --max-pages 10` | 원본 페이지를 특허 DB에 적재하고 체크포인트 저장 |
| `python scripts/patent_corpus.py index --max-batches 10` | pending 문서의 임베딩·Qdrant 적재·DB 완료 표시 |
| `python scripts/patent_corpus.py sync --max-pages 10 --max-batches 10` | 페이지 적재와 pending 색인을 교대로 처리 |
| `python scripts/patent_corpus.py status` | source의 `complete/scanned/accepted`와 `pending` 확인. 큰 테이블의 집계는 오래 걸릴 수 있음 |
| `python scripts/patent_corpus.py benchmark` | 실제 검색을 반복해 초기·예열 지연 측정. 전체 corpus의 회수율 보장은 아님 |

상한 `0`은 무제한이다. `sync`의 `--max-batches`는 색인 호출별 제한이므로 전체 작업의 총 배치 상한으로 해석하지 않는다. `source.complete=true`와 `pending=0`을 함께 확인해야 현재 원본 버전의 최초 구축 완료로 판단할 수 있다. 대규모 적재는 API 컨테이너와 CPU를 공유하지 않는 별도 작업 서비스에서 수행한다. 작업 서비스의 재배포 요청과 corpus 명령 실행은 구분한다. 배포 접수만으로 적재 완료나 반복 예약을 판단하지 않는다.

임베딩은 `intfloat/multilingual-e5-small`의 고정 commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384차원 ONNX int8 모델이다. 검색문/문서 prefix와 정규화를 포함해 현재 모델·collection 계약을 유지한다. `PATENT_MIN_SCORE`는 관련성 확률이 아니다. 외부 임베딩 API를 사용하지 않아도 CPU·메모리·볼륨·네트워크 비용은 발생한다. DB/벡터 건수 상한은 실제 디스크 사용량·WAL·색인·임시 공간을 완전히 측정하는 하드 쿼터가 아니다.

| 오류 | 조치 |
| --- | --- |
| `SOURCE_CHANGED_RESTART_IMPORT` | 같은 적재 명령으로 새 원본 버전부터 재개. 저장된 기존 문서는 유지 |
| `PATENT_DATABASE_CAPACITY_LIMIT`, `PATENT_VECTOR_CAPACITY_LIMIT` | 실제 볼륨·로그·색인 여유 확인 후 승인된 용량 조정. 임의 상한 해제 금지 |
| `INDEX_CONFIG_CHANGED_REBUILD_REQUIRED`, `VECTOR_COLLECTION_MISSING_REBUILD_REQUIRED`, `VECTOR_SCHEMA_MISMATCH` | 기존 설정을 복원하거나 별도 전체 재색인 계획 수립. 체크포인트 삭제로 완료 상태를 꾸미지 않음 |

### BigQuery 직접 검색

`PATENT_SEARCH_PROVIDER=bigquery`는 별도 명시적 경로다. Google OAuth 로그인 키와 서비스 계정 JSON은 다른 인증이다. 코드가 사용하는 프로젝트·서비스 계정 또는 ADC와 원본 접근 권한을 준비하고 [check_bigquery_patents.py](../pilot/scripts/check_bigquery_patents.py)를 확인한다. 기본 실행은 메타데이터·dry run이며, `--execute`는 실제 과금될 수 있는 검색을 실행한다. 실행 예시는 `pilot/`에서 `python scripts/check_bigquery_patents.py`다.

작업당 기본 상한은 256 GiB, UTC 월별 이 코드의 예약·사용 상한은 768 GiB다. 실행 전 추정량을 알 수 없거나 상한을 넘으면 진행하지 않는다. `LIMIT`만으로 스캔 비용이 줄어든다고 가정하지 않는다. 한 단계의 질의 묶음을 모으고 같은 묶음은 기본 24시간 캐시한다. 이는 결제 계정 전체의 잔여 무료량이나 다른 배포의 사용량을 보장하지 않는다.

예약·정산·캐시는 `STORAGE_DIR/bigquery_patents.sqlite3`에 남는다. 응답 유실 등의 미확인 작업은 예약을 유지하며 실제 완료 통계가 있어야 정산한다. 실제 job 상태를 확인하기 전에 파일을 삭제하거나 예산을 초기화하지 않는다. 이 검색 예약은 AX의 LLM 사용량 원장과 별개다.

### 과학효과 조사·검수·발행

[research_policy.json](../pilot/research/effects/research_policy.json)의 현재 조사 정책은 `conversation_only`, `external_llm_calls_allowed:false`다. 조사용 외부 LLM 추출·재검토를 실행하지 않는 계약이며 사용자 TRIZ 분석의 모델 호출과 구분된다. 오래된 `mine`·`refresh`·`sweep`·worker 명령을 자동 조사 재개 수단으로 실행하지 않는다.

편집 정본은 [catalog.tsv](../pilot/research/effects/catalog.tsv), 불변 ID 원장은 [identifiers.json](../pilot/research/effects/identifiers.json)이다. 참고 문헌·직접 읽은 문헌 연결·편집 별칭은 같은 디렉터리의 `references.json`, `accepted_literature_sources.json`, `literature_links.json`, `editorial_metadata.json`에 둔다. 배포용 결과는 `knowledge/effects.json`과 `effects_sources.json`이다.

재개 시 원시 `pilot/data/patent_effects_manual/page-*.json`, 불변 `manual_reviews/`, `manual-progress.json`과 `next-request.json`을 함께 대조한다. 오래된 문서의 고정 커서를 재사용하지 않는다. 이미 조회한 미검토 초록부터 읽고, 초록 없음·조회 수·직접 검토 수·채택 수를 구분한다. 상한까지의 순회는 엄밀한 DB 시점 snapshot이 아니므로 지나간 위치의 신규/변경 자료는 후속 순회의 대상이다.

[record_manual_effect_reviews.py](../pilot/scripts/record_manual_effect_reviews.py)는 직접 작성한 `LINK/DEFER/DESIGN_ONLY/REJECT_CLAIM` 결정을 원문 해시에 연결한다. 수정은 새 `review-id`로 남긴다. `LINK`는 기존 정본 키만 참조하며 출처 연결은 모든 조건·성능의 입증을 뜻하지 않는다. 인자 없는 실행도 진행 원장·다음 요청 파일을 **갱신**하므로 읽기 전용 점검이 아니다.

발행 전 `python pilot/scripts/publish_effects.py --check`로 정본 계약을 확인한다. `--check`를 뺀 발행은 ID·지식 JSON·발행 기록을 변경한다. 발행기는 사람이 작성한 결정을 검증·직렬화할 뿐 과학적 동등성·신규성·채택을 대신 판단하지 않는다. 프런트의 지식 동기화는 [별도 저장소의 sync-knowledge.py](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/scripts/sync-knowledge.py) 경로·입력 구성을 확인한 뒤 수행한다. 로컬 발행, Git 반영, 운영 배포, 실제 검색 사용은 각각 별도 상태다.

## n8n과 MCP

개발에서 `ORCHESTRATOR=local`이면 n8n/MCP 서비스 없이 pipeline을 실행할 수 있다. n8n을 사용하려면 다음 구성을 일치시킨다.

1. 백엔드에 `ORCHESTRATOR=n8n`, `N8N_DISPATCH_URL`, `TRIZ_SERVICE_TOKEN`, `TRIZ_MCP_URL`을 설정한다.
2. [triz-workflow.json](../deploy/n8n/triz-workflow.json)을 n8n에 가져온다. 파일은 기본 비활성 상태이며 credential을 포함하지 않는다.
3. Webhook과 HTTP Request의 Header Auth credential에 동일 서비스 인증을 연결한다. n8n의 `TRIZ_API_URL`은 백엔드의 접근 가능한 주소다.
4. 별도 MCP 프로세스이면 `pilot/`에서 `python -m triz.mcp_server`를 실행하고 `MCP_HOST`, `MCP_PORT`를 맞춘다. 기본 HTTP 경로는 `/mcp`다.
5. API 내장 방식은 `TRIZ_EMBED_MCP=true`, 같은 서버의 `/agent/mcp` 주소를 사용한다. 내장·별도 방식 중 실제 배포한 주소에 맞춘다.

`MCP_TRANSPORT=stdio`도 제공하지만 n8n의 현재 bridge는 streamable HTTP를 쓴다. `TRIZ_MCP_MODULE`은 프롬프트 도구 등록 필터다. 내부 경로의 Bearer 인증과 사용자 API의 app token·세션은 역할이 다르다.

n8n은 한 번에 한 단계 요청을 전달한다. 잠금과 stage/epoch 검사로 오래된 중복 전달을 거르고, 응답이 다음 단계 실행 가능 여부를 정한다. 응답을 잃은 모델 호출까지 무조건 재결제 없이 재실행할 수 있다는 의미는 아니다.

## AX CPU worker와 별도 특허 작성

API는 신규 AX가 켜져 있고 `TRIZ_AX_WORKER_ENABLED=true`이면 [ax/service.py](../pilot/triz/ax/service.py)로 별도 CPU 프로세스를 감시한다. 이 worker는 outbox를 소비하고 실제 평가 데이터로 정책·효과 모델을 갱신한다. 외부 LLM을 쓰지는 않지만 DB에 쓰는 작업이다.

worker를 별도 서비스에서 관리한다면 API의 자동 worker를 끄고 동일 DB·구성에서 실행한다.

```text
python scripts/ax_worker.py
```

`--once`도 한 번의 **갱신 실행**이며 읽기 전용 상태 조회 옵션이 아니다. [scripts/ax_ops.py](../pilot/scripts/ax_ops.py)의 train/promote/rollback/reconcile도 모두 변경 작업이다.

특허 초안 작성은 TRIZ의 검색 기능과 다른 프로세스다. `PATENT_ENABLED`, `PATENT_DISPATCH_ENABLED`, `PATENT_WORKER_ENABLED`, `PATENT_MCP_ENABLED` 및 별도 토큰·작업 큐·마이그레이션은 [patent_draft/README.md](../pilot/patent_draft/README.md)를 따른다. TRIZ n8n workflow와 특허 작성 workflow를 서로 대체하지 않는다.

[patent_draft/learning.py](../pilot/patent_draft/learning.py)는 호환되는 특허 namespace trainer가 없으면 `TELEMETRY_ONLY`를 반환한다. 기록 수집을 학습 완료로 표시하지 않는다. 과거 문서의 공급자·공식 서식 검증 상태는 해당 시점의 이력이며, 현재 코드나 README의 존재로 실제 운영 검증을 대체하지 않는다. 적용 조건 변경은 관련 산출물·검토·승인의 버전 유효성에 영향을 주므로 사건 전용 API를 사용한다.

## 읽기 위주의 상태 확인과 배포

| 확인 방법 | 의미·주의점 |
| --- | --- |
| `GET /healthz` | DB `SELECT 1`과 서비스 응답 확인. LLM을 호출하지 않는다. 반환 version만으로 배포 commit이나 모든 기능의 정상 동작을 입증하지 못한다. |
| `GET /api/health` | 설정·서비스 상태 확인. 인증 설정에 따라 노출 정보가 다르다. LLM 응답 검사가 아니다. |
| `GET /api/runs/{id}/view`, `/steps`, `/ax/diagnostics` | 저장된 진행·중단·비용·학습 진단을 읽는다. 소유자 권한 필요 |
| `python scripts/deployment_readiness.py` | 기존 DB의 `CREATED/QUEUED/RUNNING` 실행을 SELECT한다. 없으면 종료 코드 0, 있으면 2. 이 스크립트는 실행을 멈추거나 재개하지 않는다. |
| `GET /api/health/llm` | **실제 T1 모델 호출**. 일반 health로 취급하지 않는다. 사용자 인증 환경에서는 관리자 전용으로 차단된다. |

배포할 때는 변경한 commit·설정·DB 호환성을 먼저 확인하고, [VALIDATION](VALIDATION.md)의 필요한 검증 결과를 확보한다. 현재 backend 환경에서 `deployment_readiness.py`로 실행 중인 사례를 확인한다. 활성 실행이 있으면 종료를 기다리거나 별도 조율하며, 배포를 위해 임의 종료하지 않는다. 이 검사에서 ready가 나와도 대기 중 사용자 입력·미확인 비용·정책 호환성까지 검증된 것은 아니다.

API와 MCP가 서로 다른 프로세스/서비스라면 같은 코드·설정 계약인지 확인한다. DB·산출물 볼륨을 보존한 상태에서 배포하고, `/healthz`, 읽기 API, 배포 manifest/commit을 확인한다. 프런트가 별도이면 그 배포 버전도 기록한다. 새 버전 확인용으로 운영에 임의 문제를 만들거나 유료 분석을 호출하지 않는다.

현재 [Docker 정의](../Dockerfile)는 Python 3.11, `/app/pilot`, 내장 MCP와 `/data` 경로를 사용한다. [Railway 설정](../railway.json)은 `/healthz`와 한 replica를 지정하지만 저장소 루트의 `Dockerfile`을 기대한다. 실제 배포 checkout의 파일 배치와 서비스 설정을 확인해야 하며, 이 작업공간의 `deploy/` 파일 경로를 그대로 가정하지 않는다.

## 중단·재개와 사용량 미확인

1. 상태, `pending.kind`, 최근 단계·호출 기록, `interruption_reason`, AX 비용 예약·정산을 읽는다. 사용자 질문은 `/resume`, 일반 중단은 `/continue`의 대상이다.
2. 공급자 인증·결제·rate limit 오류, 시간 예산, 금액 예산, 필수 검토 실패를 구별한다. 중단을 PASS로 바꾸거나 누락 검토를 생략해 완료시키지 않는다.
3. `/continue`는 기존 한도와 누적 비용을 보존하고 활성 시간 계산을 새로 시작한다. `/rerun`은 명시한 단계와 후속 결과를 다시 만드는 별도 변경 작업이다.
4. UNKNOWN이면 `/ax/usage-recovery`를 조회한다. 미확인 예약은 확정 청구액이 아니며 0원이라고 판단해서도 안 된다. 서버가 허용한 항목에 한해 추가 과금 가능성 동의를 기록한 후 미완료 작업을 한 번 더 시도한다. 승인 불가·이미 재시도한 항목은 운영 확인 대상으로 남긴다.
5. 공급자의 실제 usage/청구 증거가 있으면 승인된 운영자가 `ax_ops.py reconcile` 경로로 정산한다. 추정 비용을 실제 사용량으로 기록하거나 DB에서 UNKNOWN을 직접 삭제하지 않는다.

부트 시와 30초 간격의 `recover_orphans()`는 고아 실행과 기록을 검사한다. 정상 장기 실행은 잠금으로 구별한다. 복구 감시가 모든 실패를 자동 재실행한다는 뜻은 아니다.

S5 초기 탐색과 아이디어 통합은 중단 전에 저장한 선택을 이어서 사용한다. 재개로 snapshot이 바뀌었더라도 원래 선택·고정 설정·분석 회차와 `input/problem/analysis/definition`의 불변 버전이 같고, 차이가 S5 결과 저장과 후속 참조 무효화에만 있음을 먼저 확인한다. 통합은 원안 목록도 같아야 한다. 확인되면 `ACTION_INPUT_CONTINUED`에 원래 입력과 현재 실행 snapshot을 연결한다. 원본 티켓·호출 식별자는 보존하므로, 저장된 응답과 기존 UNKNOWN 재시도 승인이 다른 호출로 바뀌지 않는다.

트랙이 이미 완료되고 통합만 중단됐다면 저장된 완료 이벤트와 원안의 존재를 확인한 뒤 통합부터 이어간다. 실제 입력 변경, 다른 프로젝트의 버전, 달라진 선택은 계속 거부한다. 오래된 티켓을 무조건 최신 snapshot으로 바꾸거나 원장의 실패·UNKNOWN을 성공으로 덮어쓰지 않는다.

## 비용·변경 여부가 다른 검증 명령

| 분류 | 예시 | 영향 |
| --- | --- | --- |
| 격리 회귀 | `python -m pytest tests/...` (`pilot/`에서) | [conftest.py](../pilot/tests/conftest.py)는 임시 SQLite·저장 디렉터리와 실제 LLM/외부 연결 차단을 사용한다. 테스트 도구 설치와 정확한 묶음은 [VALIDATION](VALIDATION.md) |
| 운영 읽기 점검 | `python scripts/deployment_readiness.py` | 기존 실행 상태 조회. 비밀 설정을 로그로 출력하지 않는다. |
| 오프라인 smoke | `python scripts/smoke.py` | LLM 없는 구조 점검이지만 실행 생성 등 저장 작업이 있으므로 격리 DB/파일에서만 사용. 현재 `solutions.min_solutions` 전제 등 오래된 검사가 있어 최신 계약 통과의 단독 기준으로 삼지 않는다. |
| 실제 호출 연결 확인 | `python scripts/smoke.py --llm`, `/api/health/llm` | 모델 호출 및 비용 발생 가능. 승인된 테스트 환경에서만 실행 |
| 유료 E2E | `python scripts/e2e.py --mode LITE` 또는 `FULL`/`DEEP` | 실제 분석·검색·DB 쓰기. 질문에 자동 응답하고 보류안 유지·가상 테스트 피드백도 제출하므로 운영 사례/학습 데이터와 반드시 분리 |
| 지식·보고서·학습 운영 작업 | corpus 적재, 효과 발행, `rerender.py`, `ax_worker.py`, `ax_ops.py` | 이름에 check/worker가 있다고 읽기 전용인 것은 아니다. 스크립트 범위와 변경·비용을 확인하고 승인된 작업으로 수행 |

이 문서의 상태 확인 절차와 모델 호출 절차를 분리해서 사용한다. 연결 성공, 코드 존재, 학습 가중치 변경만으로 품질 향상이나 추론비용 감소를 주장하지 않는다.
