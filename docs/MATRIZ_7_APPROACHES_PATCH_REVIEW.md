# MATRIZ 물리적 모순 7개 접근 패치 검토

작성일: 2026-09-29. 작업 지시: [CODEX_MATRIZ_7_APPROACHES_MINIMAL_PATCH.md](CODEX_MATRIZ_7_APPROACHES_MINIMAL_PATCH.md).

## 1. 실제 기준과 수정 파일

- 저장소: `equipment0226/triz_backend`.
- 기준 브랜치: `feat/ax-qlearn-refactor-20260928`.
- 실제 HEAD: `71b7d94cefe720cb11ffb9d012a0ab2f39dfef94`.
- 문서에 적힌 과거 검토 커밋 `60acf72`로 되돌리지 않았다. 최근 TRIZ76·merge·보고서·AX/RL 구현을 기준으로 작업했다.
- 작업 소스는 워크스페이스의 `pilot/`, Git 검토용 checkout은 `.deployment/release-ax-qlearn-backend/`이다. 자동 commit/push/deploy는 하지 않았다.

| 파일 (`pilot/` 기준) | 수정 이유 |
|---|---|
| `triz/knowledge/separation.json` | 기존 kind→dict 형태에서 7개 접근과 원문 권장 원리·출처·내부 버전 제공 |
| `triz/knowledge/separation_legacy_v1.json` (신규) | 과거 AX 실행 재현용 4종 원본 바이트 보존 |
| `triz/separation_contract.py` (신규) | 실행별 카탈로그 선택, 별칭 정규화, 메타데이터 결합, 결정론 검사, 표시명 공통화 |
| `triz/knowledge.py` | `separation_block(catalog=...)` 선택 인자 지원; 무인자 호출과 legacy 블록 보존 |
| `triz/prompts/P_S4_CONTRADICTIONS.md` | `separation_candidates`를 7개 접근의 힌트로 안내 |
| `triz/prompts/P_S5_TRACK_B.md` | 7개 검토와 적용/미적용 사유, 실제 원리, 가족별 해결 논리 명시 |
| `triz/prompts/P_S5_ARIZ_PART5.md` | 공유 지식을 7개 접근으로 설명하되 ARIZ 출력 계약 유지 |
| `config/rubrics.yaml` | R5_B 문구만 변경; criterion ID·가중치·다른 rubric 보존 |
| `triz/verify.py` | `check_separation()`을 실행별 공통 검사기로 연결 |
| `triz/nodes.py` | Track B의 검사·정규화·실제 PC 연결; ARIZ5 공유 카탈로그; 적용 원리 표시명 |
| `triz/ax/runtime.py` | 신규 bundle에 카탈로그 snapshot 및 helper 소스 해시 포함 |
| `triz/mcp_server.py` | 직접 Track B 호출 및 R5_B 별도 감사에만 실행별 계약 적용 |
| `triz/digest.py` | 버전 있는 Track B 출처를 merge/S6 입력까지 전달; 빈 추천 목록 보존 |
| `triz/render.py` | 공통 표시명 연결; S4 힌트와 연결된 결과 또는 pinned 카탈로그 참조 |
| `templates/report_full.md.j2` | 7종 표시와 ‘해결 방식’, ‘실제 사용 발명원리’ 표기 |
| `triz/visuals.py` | 기존 분리 도식의 제목을 ‘물리적 모순 해결 접근’으로 변경 |
| `tests/matriz7_fixtures.py` (신규) | 실제 서비스와 분리된 신규/legacy 모의 검토 자료 |
| `tests/test_matriz7_knowledge.py` (신규) | 원문 매핑, 원리 이름, 출처, placeholder, 의미 반례 지시 검사 |
| `tests/test_matriz7_contract.py` (신규) | 형식·중복·별칭·실제 원리·카탈로그·bundle 검사 |
| `tests/test_matriz7_execution.py` (신규) | PC 선택, 실제 실행기 수리, 캐시, legacy 원장 보존, ARIZ 계약 검사 |
| `tests/test_matriz7_mcp.py` (신규) | MCP 인자/envelope/profile/검사/수리/선택적 감사 정책 검사 |
| `tests/test_matriz7_reports.py` (신규) | 신규/구버전/다중 PC 보고서 및 merge→S6 출처 보존 검사 |
| `tests/test_unified_cost_harness.py` | 기존 모의 제공자의 Track B 응답만 새 7종 계약에 맞춤; 비용/검토 assertions 유지 |

카탈로그 helper는 Track B 전용이다. 일반 agent 실행기, schema, DB, 캐시 프레임워크를 새로 만들지 않았다.

## 2. 최종 지식과 출처

2026-09-29에 [MATRIZ Wiki: Algorithm of resolving physical contradictions](https://wiki.matriz.org/docs/triz/problem-solving-tools-5890/contradictions/physical-contradiction-6056/algorithm-for-resolving-physical-contradictions/)를 직접 확인했다. 지시문 매핑과 현재 공개 원문의 차이는 없었다.

| kind | 표시명 | family | 권장 원리 ID, 원문 순서 |
|---|---|---|---|
| SPACE | 공간 분리 | SEPARATE | 1, 2, 3, 7, 4, 17 |
| TIME | 시간 분리 | SEPARATE | 9, 10, 11, 15, 34 |
| CONDITION | 관계(조건) 분리 | SEPARATE | 3, 17, 19, 31, 32, 40 |
| DIRECTION | 방향 분리 | SEPARATE | 4, 14, 17, 32, 35, 40 |
| SYSTEM_LEVEL | 시스템 수준 분리 | SEPARATE | 1, 5, 12, 33 |
| SATISFY | 상반 요구의 동시 충족 | SATISFY | 13, 28, 35, 36, 37, 38, 39 |
| BYPASS | 모순 요구 우회 | BYPASS | `[]`: 고정 추천 묶음 없이 전체 40원리 탐색 가능 |

분리 5개, 동시 충족, 우회로 구별한다. `CONDITION` 저장 키는 유지하되 신규 실행에서 서로 다른 대상에 대한 관계라는 의미를 사용한다. SYSTEM_LEVEL은 공식 제어 질문 없이 항상 검토하며, 실제 구체안이 항상 성립한다는 뜻은 아니다.

`matriz-pc-7-2026-09-29`는 내부 snapshot 버전이고 날짜는 접근일이다. 협회의 공식 개정일·판번호로 표시하지 않는다. 각 항목에는 실제 원문 절 제목도 저장한다.

지시문에 제공된 교재 인용문과의 차이는 방향 분리 누락, 번호-명칭 불일치, SATISFY의 24/30, BYPASS의 제한된 추천 묶음이다. 기존 카탈로그에서 7=Nested doll, 4=Asymmetry, 5=Merging을 대조했다. 교재 원본·판본이 없어 교재 자체의 오기나 개정 이력을 단정하지 않는다. `principles_40.json`은 변경하지 않았다.

권장 원리를 실제 사용 목록으로 복사하지 않는다. 권장 밖 유효 원리는 사유와 함께 `EXTENDED`, BYPASS의 선택은 `UNRESTRICTED`, 번호를 특정하지 못한 적용안은 사유와 함께 `UNSPECIFIED`로 기록한다. 추천 ID가 빈 BYPASS에서 실제 원리 24를 쓰는 것은 정상이다.

## 3. 생성·검사·계보·보고서 연결

```text
S4 physical_contradictions + separation_candidates(힌트)
  → 기존 _pick_pcs 선택(최대 2개, 정책 동일)
  → PC별 _track_b / run_agent 1회 생성
      실행별 separation_block + 기존 inventor_b/T2/R5_B
  → 공통 normalize + check_separation + 기존 수리 루프
  → 각 PC의 7개 검토를 separation_apps에 보존
  → 유효한 applicable is True만 B_SEPARATION RawIdea
  → 기존 _merge의 source_details
  → digest.idea_packet → 기존 S6 → 보고서
```

- 7개 검토는 필수지만 7개 적용안을 강제하지 않는다. 적용 가능한 접근 0개 또는 1개도 형식 계약상 허용하며, 그 수만으로 `redefine_hint`를 만들지 않는다.
- 잘못된 envelope/원소 타입, kind 누락·중복·미지 값, 별칭 정규화 후 중복, bool 이외 applicable, 적용안 본문/미적용 사유 누락, 잘못된 원리 ID를 `FATAL-SEPARATION`으로 검사한다.
- `True`를 원리 ID 1로 받아들이지 않는다. 권장 밖 원리나 미확인 번호에는 설명을 요구한다.
- 독립 코드 검토에서 발견한 `hypothesis_ids=17`, 잘못된 `uses_resources`/`feasibility_hint` 등이 RawIdea 생성에서 실패하는 경로도 같은 수리 경계로 옮겼다. 기존 모델·DB는 변경하지 않았다.
- source_pc_id는 모델 출력에서 제거하고 `_track_b`가 실제 선택 PC의 ID를 결합한다. `addresses=[pc.id]`, `track=B_SEPARATION`, detail, 실제 원리, 추천 원리, 출처와 버전을 보존한다.
- `_add_ideas`, `_merge`, 병렬 트랙 실행 코드는 변경하지 않았다. S6 입력 whitelist가 새 provenance를 누락하므로 `digest.idea_packet`의 버전 있는 분리 출처만 보완했다. BYPASS의 `recommended_principles=[]`도 유지한다.
- 보고서 표는 실제 `supporting_principles`를 ‘실제 사용 발명원리’로 표시한다. SATISFY/BYPASS를 ‘동시 충족 분리’/‘우회 분리’라고 붙이지 않는다. 다중 PC 그룹 연결을 유지한다.

## 4. MCP 경로

| 경로 | 동작 |
|---|---|
| `triz_execute_stage` | 기존 `pipeline.execute_stage → nodes._track_b`를 그대로 사용 |
| 직접 `triz_s5_track_b(run_id, variables)` | 기존 tool명/인자/`{artifact,run_id}` 유지; 서버 실행별 카탈로그 블록으로 입력 사본을 구성하고 공통 checker/normalizer/R5_B 연결 |
| `triz_verify_artifact(..., rubric_id='R5_B')` | 실행별 계약을 먼저 검사; 잘못된 결과는 LLM 전에 deterministic REJECT; 유효한 결과만 기존 감사 정책에 전달 |

직접 호출의 client separation_block은 신뢰하지 않는다. AX prompt/rubric/catalog가 섞이지 않도록 이 두 분기에만 기존 ContextVar profile을 설정하고 성공·예외·저장 실패에도 복원한다. 원본 variables를 변경하지 않고, 직접 호출은 solve에 추가하거나 단계를 전진시키지 않는다. PC ID가 없는 입력에서 ID를 추정하지 않는다.

다른 prompt/rubric 분기의 정책, MCP 목록, 필수 template 변수는 유지한다. R5_B의 기존 검증 enable/skip 정책도 유지한다. 현재 선택적 감사 정책이 반환하는 `UNVERIFIED`를 물리 타당성 PASS로 바꾸지 않는다. 형식 검사가 통과했다고 모델 감사나 물리 검증이 수행되었다고 주장하지 않는다.

## 5. 실행 중 상태와 과거 자료 호환

- 신규 AX bundle: `separation_catalog` deep copy를 기존 bundle digest에 포함한다. Track B와 ARIZ5가 동일 snapshot을 읽는다.
- 이전 AX bundle: snapshot 키가 없는 경우에만 보존된 4종 자료를 사용한다. 당시 pinned prompt/rubric를 유지하고 결과를 `legacy-separation-4-v1`로 구분한다. 저장 bundle/bundle_id/ledger를 갱신하지 않는다.
- 새 snapshot 키가 존재하지만 잘못된 경우에는 오류를 내며 4종 fallback으로 통과시키지 않는다.
- 과거 4종 자료 SHA256: `f97bcf3580b3ac6a93cb9a4a72fefcc144de15dcc172083a739ee88078384e20`.
- 기존 완료 결과를 새 검사기로 일괄 재검증하거나 DIRECTION/SATISFY/BYPASS 행을 만들어 넣지 않는다. 메타데이터 없는 CONDITION의 표시명은 기존 ‘조건 분리’로 유지한다. 저장된 frozen 보고서는 수정하지 않는다.
- non-AX의 새 생성/명시적 재실행은 7종을 사용한다. 과거 자료의 단순 렌더는 의미를 바꾸지 않는다.
- 기존 agent 캐시를 그대로 사용한다. 버전이 들어간 렌더 입력이 캐시 키를 바꾸며, 캐시 재사용 시 공통 검사도 실행한다. 테스트에서 기존 4종 캐시→신규 7종 생성 시 실제 모의 provider가 다시 호출되고, 동일한 7종 재시도는 검증된 캐시를 사용하는 것을 확인했다.
- legacy 재개 테스트에서 실제 임시 SQLite ledger의 head/bundle/epoch와 사용자 승인 상태를 전후 비교했다. 운영 실행을 수정하여 확인한 것은 아니다.

## 6. 테스트 결과

외부 네트워크 및 실제 LLM 호출을 차단하고 임시 SQLite/스토리지에서 실행했다.

| 검사 | 실제 결과 |
|---|---|
| 신규 MATRIZ7 테스트 5개 파일 | **157 통과**, 실패 없음 |
| 기존 관련 회귀 27개 파일 | **536 통과 / 27 실패** |
| 기준 HEAD에서 동일 회귀 | **537 통과 / 26 실패**; 26개 실패의 이름·오류 메시지가 수정본과 동일 |
| 기준 HEAD + 동일 프런트 자산으로 SVG 검사 | **1 실패**, 수정본의 추가 SVG 실패와 동일 |
| 기존 smoke, 임시 저장소 wrapper | **7 통과 / 1 실패**; 기준 HEAD에서도 동일 |
| 비용 harness 별도 실행 | **1 통과**; 위 회귀에도 포함되므로 합계 중복 계산하지 않음 |

신규 테스트 명령(워크스페이스 루트):

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest pilot/tests/test_matriz7_contract.py pilot/tests/test_matriz7_knowledge.py pilot/tests/test_matriz7_mcp.py pilot/tests/test_matriz7_reports.py pilot/tests/test_matriz7_execution.py -q --disable-warnings --tb=short --junitxml=.deployment/matriz7-research/targeted.xml
```

관련 회귀에서 실행한 동일 파일 목록과 재현 명령:

```powershell
$matrizRegressionFiles = @(
  'test_triz76_contract.py', 'test_triz76_flow.py', 'test_triz76_mcp.py',
  'test_ariz_required_parts.py', 'test_ariz_reformulation.py', 'test_ariz_completeness_compatibility.py',
  'test_s5_prompt_input_compatibility.py', 'test_s5_workflow_coverage.py',
  'test_ax_phase1.py', 'test_ax_refactor.py', 'test_ax_ariz_routing.py',
  'test_ax_targeted_expansion.py', 'test_ax_s6_consolidation_snapshot.py',
  'test_unified_feedback_adaptive.py', 'test_unified_feedback_learning.py', 'test_unified_cost_harness.py',
  'test_routing_q_support_contract.py', 'test_full_idea_review.py', 'test_merge_current_ids.py',
  'test_s6_lineage_normalization.py', 'test_s6_lineage_replay.py',
  'test_report_layout.py', 'test_report_display_terms.py', 'test_ax_full_report.py',
  'test_standard_diagrams.py', 'test_project_budget.py', 'test_budget_interruption_reason.py'
) | ForEach-Object { 'pilot/tests/' + $_ }
.venv/Scripts/python.exe -X utf8 -m pytest @matrizRegressionFiles -q --disable-warnings --tb=short --junitxml=.deployment/matriz7-research/regressions.xml
```

기준 비교는 아직 변경하지 않은 `.deployment/release-ax-qlearn-backend`를 working directory로 지정하여 같은 27개 파일을 실행했다. Python과 XML 출력만 워크스페이스 절대경로를 사용했다. 기준 소스를 테스트한 후에만 수정 파일을 Git 검토용 checkout에 반영한다.

독립 backend checkout에는 `frontend/`가 없어 SVG 테스트가 자산 비교 부분을 생략했다. 따라서 기준 HEAD의 동일 테스트·카탈로그·렌더러를 유지한 채 자산 탐색 경로만 현재 워크스페이스와 맞춰 추가 실행했다. 이때 수정본과 동일한 `2.2.2` SVG 제목 불일치가 재현됐다. 27개 실패 모두 변경 전 코드에서 재현됐으며, 이번 변경에서 추가된 실패는 확인되지 않았다.

```powershell
.venv/Scripts/python.exe -X utf8 .deployment/matriz7-research/baseline_frontend_check.py
```

기존 smoke는 다음 wrapper로 동일 `pilot/scripts/smoke.py`의 8개 함수를 실행했다. DB와 샘플 보고서 출력만 임시 경로를 사용하며 assertion을 바꾸지 않았다.

```powershell
.venv/Scripts/python.exe -X utf8 .deployment/matriz7-research/run_smoke.py
.venv/Scripts/python.exe -X utf8 .deployment/matriz7-research/run_smoke.py .deployment/release-ax-qlearn-backend
```

실패 원인 분류:

- 25건: 기존 테스트의 모의 `SimpleNamespace` 응답에 현재 agent 실행기가 읽는 `meta`가 없음.
- 1건: `test_e09_optional_budget_still_defers_without_call`이 예산 초과 동작을 기대하는 기존 방식과 현재 `BudgetExhausted` 경로의 불일치.
- 1건: 기존 TRIZ76 도식 생성 결과와 별도 프런트 정적 SVG 제목의 불일치.
- smoke 1건: `t_settings`가 현재 설정에 없는 `solutions.min_solutions`를 필수로 기대함.

이번 계약 때문에 실패하던 비용 harness의 4종 모의 응답은 7종으로 고쳤다. 비용·정산·검토 품질 assertions는 유지했고 통과했다. 무관한 기존 테스트·전역 agent·예산·프런트 SVG는 수정하지 않았다.

원시 결과: `.deployment/matriz7-research/{targeted,regressions,regressions-baseline,baseline-same-frontend,cost-harness}.xml`, `smoke.txt`, `smoke-baseline.txt`. 이름/오류 메시지별 기준 비교는 `validation-summary.json`에 기록한다. 별도 전체 저장소 테스트와 유료 서비스 end-to-end는 실행하지 않았다.

## 7. 변경 경계와 별도 로컬 차이

Git의 고정 `71b7d94` blob과 AST/내용을 비교했다. 감사 자료: `.deployment/matriz7-research/diff-audit.json`.

- 동일: `schema.py`, Track enum, `store.py`/DB 및 ledger, `pipeline.py` 13단계와 인덱스, `agent.py`, `_pick_pcs`, `_add_ideas`, `_merge`, `_run_tracks`, S6~S8/HITL, RL·Q·보상·모드·예산·tier·skip·승급 정책.
- Track B 외 A/C/E/F/G/H 구현은 동일하다. ARIZ는 Part5의 공유 separation_block 선택만 변경했으며 Part1~7 순서, steps/ideas, 필수 step 코드, 자체 checker와 토큰 설정을 유지한다.
- S3/Su-Field, 표준해 후보 선정과 힌트, 40원리, 모순행렬, TRIZ76 관련 MCP/프롬프트를 변경하지 않았다.
- 현재 `pilot/triz/knowledge/standards_76.json`에는 HEAD 대비 문구 2필드의 별도 로컬 차이가 있다. 이번 작업에서 수정하거나 되돌리지 않았으며 MATRIZ7 반영 목록에서 제외한다. 변경 발생 시점은 단정하지 않는다. 하나는 액체의 겉보기 밀도를 통한 부유체 제어의 제목, 다른 하나는 5.1.1.9의 ‘응집 상태’→‘물리적 상태(고체·액체·기체 등)’ 표현이다.
- 루트에만 존재하는 `pilot/.gitignore`, `pilot/web/*` 등 별도 파일도 이번 변경으로 포함하지 않는다.

## 8. 관측 한계와 별도 프런트엔드 의존성

- 외부 LLM/API end-to-end, 운영 실행 재개, 유료 추론, 물리적 설계 성능은 검증하지 않았다. 신규 회귀 테스트의 의미 반례는 요구 삭제 우회, 무근거 동시 충족, 온도만 바꾼 관계 분리에 관한 prompt/rubric 지시 존재를 확인한다. 모델의 실제 판단 정확도를 입증하지 않는다.
- 생성 호출은 PC당 1회지만 입력이 늘었다. separation_block은 500→3,927자, Track B 템플릿은 1,328→2,625자, ARIZ5 템플릿은 1,691→1,967자다. 이는 문자 길이 관측이며 토큰 사용량이나 비용 측정이 아니다. 전역 예산·출력 토큰을 올리지 않았고 비용·품질 개선을 주장하지 않는다.
- 프런트엔드는 별도 checkout이며 이번에 수정하지 않았다. `frontend/src/data/introduction.js:31,35,54`, `frontend/src/components/GuideVisual.jsx:20`, `frontend/src/pages/MaterialLibrary.jsx:75`에는 아직 4종 안내/도식이 있다. 소개 문구·4개 상자 및 정적 지식 배포를 별도 동기화해야 한다. 이 안내가 바뀌었다고 보고하지 않는다.
- 기존 `B_SEPARATION` 트랙의 일반 명칭 ‘분리 원리’는 호환성상 유지한다. 개별 7종 결과와 보고서 절은 상위 표현 ‘물리적 모순 해결 접근’을 사용한다.
- 운영 배포, commit/push는 수행하지 않았다.
