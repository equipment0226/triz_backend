# Micro LED 워크플로 감사 — 2026-09-27

## 감사 기준과 결론

감사 기준 코드는 운영 ARIZ 수정본 `407a44ff029c21163d6eb4f5e35c0fdf59d34166`이다. 아래 파일·행 번호는 `.deployment/release-ariz-hotfix-backend`에 보관한 해당 버전을 기준으로 한다. 수정 중인 작업 트리의 최종 동작 또는 배포 완료를 이 문서로 주장하지 않는다. 운영 근거는 `.deployment/microled-workflow-20260927.json`의 `runs[0]`, `run-bbe70a45d710`, 실행 epoch 17이다. 원시 기록에는 사용자 문제와 모델 응답이 있으므로 필요한 요약만 싣는다.

이번 보고서 4.5 기술진화, 4.6 FOS, 4.7 과학기술효과가 빠진 직접 원인은 S5의 실행 경로 누락이다. 현재 solve에는 A/B/D만 있으며 F/G/H 산출물은 모두 0이다. 렌더링 단계로 전달되기 전에 이미 비어 있다. 빈 앱 목록일 때 절 제목까지 숨기는 템플릿이 누락을 더 알아보기 어렵게 했다.

완료 상태는 모든 기법 수행이나 해결책의 물리적 타당성을 뜻하지 않았다. 해당 실행은 `COMPLETED`지만 G3/G4는 `CONDITIONAL`이다. 모델 호출·입출력·구조 검사는 확인할 수 있으나 모델의 내부 추론, 공학적 정답, 실제 성능을 이 감사로 증명할 수 없다.

## 운영 기록에서 확인한 사실

| 항목 | 확인 결과 |
|---|---|
| 마지막 완료 | 2026-09-27 01:40:34 UTC |
| 모드 / 실제 트랙 | DEEP / A_MATRIX, B_SEPARATION, D_ARIZ |
| 남은 coordination 트랙 | H_EFFECTS 하나만 기록 |
| 이전 실행 bundle | `coherence_contract=null`, branches=3, initial_candidates=6, detailed_candidates=3, expansion_rounds 키 없음 |
| 확장 기록 | ax_expansion_rounds, ax_expansion_deferred 모두 없음 |
| 비용 | 누적 $1.000262 / 한도 $2; over_budget=false |
| 현재 앱 수 | trend_apps=0, fos_apps=0, effect_apps=0, standard_apps=0 |
| 현재 S3/S4 입력 | components=16, function_edges=12, su_fields=3, resources=25, TC=10, PC=4, trimming=9, key_problems=3 |
| 전체 단계 기록 | 155개; FAILED=0, SKIPPED=0. WARN만으로 생성 실패라고 해석할 수 없음 |
| 현재 원시 아이디어 | 제한 후 6개, 대표 track은 모두 A_MATRIX; 최종 개념 3개 |

과거 H 호출 seq 18, 59, 99는 모두 9월 16일에 수행됐다. 해당 호출을 9월 27일 재실행에서 H를 수행한 증거로 세면 안 된다. 새 solve로 초기화된 뒤 실제 새 S5 기록 seq 124–139에는 F/G/H가 없다.

## S0–S10의 입력·출력과 조건부 경로

13개 실행 단계가 S0–S10의 사용자 단계에 대응한다(`pipeline.py:16`). 아래의 “모델”은 기록된 호출을 뜻하며 독립적인 사실 검증을 뜻하지 않는다.

| 단계 | 핵심 입력 → 산출물 | 실행 조건·검증 | 이번 실행의 근거 |
|---|---|---|---|
| S0 실행 계획 | 원문·첨부 → 모드·언어·도메인·tracks | 명시 mode는 mode_locked로 보존. 미지정 때만 suggested_mode 사용. 설정의 모드별 tracks를 읽음(`nodes.py:37`, `pipeline.py:53`) | 9/16 seq 1 모델 결과를 유지 |
| S0 산업 검토 | 원문·산업 정책·첨부 → deep_dive·질문·답변 | 모델 호출 후 산업/난이도·답변 확인. 경로 변경 시 재검토. 답변 완료는 새 연구 생성과 구분(`domain.py:129`) | 9/16 seq 43 유지; 이번 S5 재실행에서 새 호출 없음 |
| S1 문제 추출 | 원문·첨부 사실·질의답변 → domain/frame/constraints | 빈 응답은 중단. 충분성 부족 시 제한된 역질의. 일부 필드 누락은 후속 확인에 남음(`nodes.py:68`) | 9/16 seq 44 유지 |
| S2 범위 확정 | domain·재정의 문제 → 시스템 후보·공간·시간·사용자 확정 | 후보가 없으면 원문 기반 후보로 대체하되 사용자 확정에서 멈춤. 확인 답변의 후보 ID를 검증(`nodes.py:156`) | 9/16 seq 45 후보 결과와 사용자 확정 유지 |
| S3 분석 | 확정 범위·문제 → 9-Windows, 기능모델, 자원, CECA, Su-Field, 추가 제약 | 9-Windows→기능모델은 순차. 자원/CECA 등은 병렬. Su-Field는 비 LITE이면서 물리 범위인 경우 수행. 내재 제약은 가설로 추가(`nodes.py:216`) | 9/16 seq 86–91 유지. 단순 미호출이 아닌 의도적인 선행 결과 재사용 |
| S4 정의 | 기능·인과·자원·경계 → IFR, TC/PC, trimming, 핵심 문제 | IFR/모순/trimming 병렬 후 핵심 문제 선정. 모순 형식 checker 존재. S5 진입에서 TC 또는 PC 존재 검사(`nodes.py:379`, `coordinator.py:99`) | 9/16 seq 92–95 유지; 현재 후속 기법의 입력은 존재 |
| S5 다중 기법 | definition·analysis·카탈로그 → 앱, ARIZ, raw_ideas, 통합 | 당시 AX route가 모드의 전체 트랙을 3개 baseline으로 덮어씀. DEEP 검사는 D/ARIZ 객체만 확인. 별도 검색은 pre-S5 사실 기반으로 병렬(`nodes.py:907`) | 새 seq 124–139. A/B/D, 검색, merge 호출. F/G/H/C/E 없음 |
| S6 개념 | 선택 아이디어·모순·사실·자원·검색 결과 → 개념·품질 판정 | TRADEOFF 제외, 아이디어 수 제한, 출처 ID·중복 검사. 독립 품질 호출. REVISE/UNVERIFIED는 PASS와 구별하며 유지 가능(`quality.py:9`) | 새 seq 140 개념 모델, 141 품질 모델. 개념 3개 |
| S7 제약 | 개념·전체 제약 → 후보별 PASS/CONDITIONAL/FAIL | 누락 판정은 CONDITIONAL, 수치 위반 보조 검사. FAIL 제외. 필요한 경우 사용자 판단에서 멈춤; 사용자 유지가 PASS로 승격시키지는 않음(`nodes.py:1127`) | 새 seq 142–144 모델 검토. G3 CONDITIONAL |
| S8 근거 | 후보·작동 기전·제약·검색 결과 → 출처 카드·매핑·전이 조건 | 실제 검색 공급자 결과를 매핑. 낮은 적합도·부족한 snippet은 지원 근거로 올리지 않음. 초록/메타데이터 확인과 성능 검증 구별(`evidence.py:157`) | 새 seq 145 검색 도구, 146 모델 매핑 |
| S8 평가 | 검토된 개념·제약·근거 → 독립 직군 점수·순위·로드맵 | 후보가 없으면 빈 평가/재정의 경로. 독립 평가 이후 ranking. 구 prompt에서 새 ARIZ Part6 산출 계약이 반영되지 않음(`nodes.py:1248`, `reformulation.py`) | 새 seq 147–154 모델. seq 155 Part6은 정적 기록; 모델 응답으로 오인하면 안 됨 |
| S9 보고서 | versioned selection/context/solve 등 → markdown/HTML | AX는 모델 요약 호출 없이 저장 산출물 투영·렌더. F/G/H 필드 손실 필터는 확인되지 않음. 앱이 비면 기존 template에서 절 자체를 숨김(`nodes.py:1408`, `report_full.md.j2:448`) | 새 보고서 생성. 별도 s9_narrative 모델 호출 없음 |
| S10 피드백 | 사용자 피드백 → feedback·RAG | 답변 없으면 확인 대기; solution_feedback이 있을 때만 정제 모델. 빈 피드백 완료와 새 모델 분석을 구별(`nodes.py:1486`) | feedback 빈 값, s10_distill 호출 없음 |

## 확정된 실행 경로 결함

### 1. 필수 기법을 선택적 확장에 결합

`coordinator.py:106–136`은 DEEP의 D와 TC/PC의 A/B를 우선 배치하고 처음 3개만 남긴다. C/E/G는 `coherence_enabled` 블록 안에서만 추가된다. H는 뒤에 붙지만 3개 밖으로 밀리면 pending이다. F는 생성 후보와 pending 어디에도 추가되지 않는다. `nodes.py:913`은 S0에서 설정한 전체 모드 트랙 대신 이 결과를 사용한다.

운영 bundle의 `coherence_contract=null` 때문에 C/E/G 분기를 건너뛰며, `expand()`도 `coordinator.py:144`에서 즉시 반환한다. 이번 예산 초과나 모델 실패가 원인은 아니다.

새 coherence bundle도 완전하지 않다. 모든 선행 입력과 충분한 예산을 가진 DEEP를 당시 함수로 재현하면 baseline D/A/B, pending C/H/E/G가 되고 한 번 확장으로 C/H/E만 실행된다. G는 남고 F는 예약되지 않는다(`coordinator.py:148`, `161`). 재현은 원본 함수 AST와 외부 호출 stub을 사용했으며 모델·운영 DB 호출은 없었다.

모드별 필수 coverage를 별도 계약으로 확정하고 3 branch 제한은 한 batch의 크기에 적용해야 한다. `need_more`, 후보 수, optional expansion round가 필수 기법 수행을 생략할 근거가 되어서는 안 된다. 필요한 입력이 없는 기법은 근거 있는 NOT_APPLICABLE, 수행했으나 적용안을 못 찾은 경우는 NO_APPLICABLE_RESULT, 예산/호출 문제는 미완료로 구별해야 한다. 빈 리스트만으로 이 상태들을 추정하지 않는다.

### 2. 완료 검사에 기법 coverage가 없음

`nodes.py:935`의 DEEP 검사는 D 실행과 ARIZ 객체만 본다. G3는 개념 품질·제약을, G4는 추천 존재를 검사한다(`runtime.py:145`). `_unresolved_failures`는 실제 FAILED 호출만 찾으므로 아예 예약되지 않은 호출을 발견하지 못한다(`pipeline.py:87`). 필수 기법 미완료는 S5 종료와 보고서 완료 전에 별도로 막아야 한다. 조건부 보고서는 생성할 수 있어도 미수행을 성공으로 표시하면 안 된다.

### 3. 과거 bundle과 현재 코드가 다른 계약을 가질 수 있음

실행은 고정 bundle의 설정·prompt를 사용하지만 Python 코드는 현재 배포본이다(`pipeline.py:154`, `runtime.py:156`). `_upgrade`는 pipeline stage version을 바꾸며 coherence/기법 계약을 보완하지 않는다. 이전 bundle을 조용히 새 bundle로 교체하는 것도 재현성을 해친다. 기존 bundle에서 필수 coverage를 해석하는 명시적인 호환 경로와 실제 실행 계약 버전 기록이 필요하다.

### 4. s_curve가 재실행 사이에 남고 다른 트랙이 덮어쓸 수 있음

당시 `rerun_from()`은 solve를 비우면서 `scratch.s_curve`를 지우지 않는다(`pipeline.py:394–404`). `_run_tracks`는 이전 scratch를 모든 branch에 복사한 뒤 F/G/H 순서로 병합하며, 모든 branch의 s_curve를 복사한다(`nodes.py:974`, `1006`). 이전 s_curve가 있으면 F의 새 결과를 G/H의 이전 복사본이 덮어쓸 수 있다. 이번 MicroLED state에는 s_curve가 없어 이 현상의 발생을 주장하지 않는다. 코드상 위험은 명확하며 새 solve에서 삭제하고 F만 해당 결과의 생산자로 취급해야 한다.

## 후보 전달·재실행·의존성의 추가 확인

### 아이디어 선택 편향과 누락

`digest.select_ideas()`는 `(addresses, mechanism_key 또는 track)`별로 round-robin한다. 기전 키가 고유하면 사실상 입력 순서가 된다(`digest.py:37`). `_run_tracks`는 A부터 H 순서로 아이디어를 저장한다. A의 고유 기전 20개 뒤에 F/G/H 각 2개를 넣고 limit=12를 적용한 결정론적 재현에서는 A만 12개 선택된다. 이는 트랙 완료와 별개로 후반의 기전이 개념 입력에서 빠질 수 있음을 보인다. 특정 트랙의 최종 추천을 보장할 이유는 없지만, 검토할 원천 후보의 선택은 문제·트랙·기전을 균형 있게 보존해야 한다.

통합은 source_idea_ids와 상세 근거를 합치지만 대표 track은 첫 원천만 보존한다(`nodes.py:1055–1078`). 여러 기법에서 얻은 같은 아이디어가 통합되는 것은 타당하다. 원천 track 정보도 보존해야 후보 다양성 감사가 정확하다. 구 bundle에서는 `portfolio_completion_v1`이 없으므로 통합 모델이 응답에서 누락한 원천 아이디어도 버려진다(`nodes.py:1088–1096`). 누락은 명시적인 제외 판정이 아니므로 구 bundle에도 미계상 원천 보존이 필요하다. 기존 후보 제한 자체를 늘릴 필요는 없다.

### 재실행 경계

`continue_run()`은 동일 단계·같은 revision을 이어가며 비용과 완료된 확장 round를 보존한다(`pipeline.py:361`). `rerun_from()`은 S5 또는 그 이전에서 solve/후속 결과와 확장 상태를 비운다. S6 이후 재실행은 solve를 보존하므로 빠진 F/G/H를 새로 만들지 않는다. 보고서만 다시 만들면 미수행 기법이 복원되지 않는다. 이미 끝난 트랙의 결과를 다시 append하지 않도록 동일 revision의 batch 완료 기록이 필요하다.

추가 정리 대상으로 `s_curve`, `ax_mechanisms`, `ax_portfolio_trace`, `evidence_mappings`, `related_references`, `search_status` 등 파생 scratch의 생산 단계·유효 revision을 명시해야 한다. 모든 캐시를 무조건 지우는 것은 부적절하다. 같은 검색어의 공급자 결과는 재사용할 수 있지만 이전 concept ID의 매핑·이전 후보의 적용 판정과 현재 사용 여부는 구별해야 한다. `evidence.attach()`의 입력 없음 조기 반환은 related_references 초기화보다 앞에 있다(`evidence.py:163`, `192`). 이 문서에서는 stale 매핑이 이번 보고서에 노출됐다고 주장하지 않는다.

S3의 도메인 제약은 이전 constraints를 유지한 채 문장 일치만 중복 제거하여 추가한다(`nodes.py:355–367`). S3 재실행에서는 사용자 제약과 기존 확인 사항을 보존하되 새 분석에서 만든 가설 제약이 문구 변경으로 누적되는지 검증이 필요하다. 현 기록만으로 잘못된 제약이 실제 누적됐다는 결론은 내리지 않는다.

### 산출물 의존성

AX ledger는 input→problem→analysis→definition→solve→concepts→constraints/evidence→evaluation→selection→report의 의존성을 기록하고 생산 단계가 재실행되면 후속 버전을 무효화한다(`runtime.py:11–26`, `113`). 이는 유용하지만 데이터 내용의 충분성을 증명하는 검사가 아니다. report는 selection을 통해 solve까지 연결되지만 s_curve 같은 scratch 데이터는 report_context에서 별도 수집된다. 따라서 scratch의 버전 경계도 함께 지켜야 한다.

ARIZ Part5 seq 137은 9,077 output tokens를 생성했지만 5.1/5.2만 있고 ideas는 비어 있었다. 호출 상태는 OK였다. Part5의 모든 세부 항목을 필수로 볼지, 적용 불가 또는 후보 없음으로 볼지 명시적인 계약과 결과 검사가 필요하다. Part6 seq 155의 정적 질문은 모델이 6.1–6.3을 분석했다는 증거가 아니다. 구 pinned ranking prompt에 새 필드 요청이 실제로 없었다는 IO 감사 결과와 일치한다.

## 회귀 검증 제안과 범위

1. DEEP + 모든 선행 입력 + 충분한 예산에서 필수 8개 기법의 실행/명시적 적용 불가를 확인한다. 후보가 이미 충분해도 필수 coverage는 완료해야 한다.
2. coherence_contract가 없는 구 bundle도 모드별 계약을 지키는지 확인한다. 고정 prompt/설정을 교체했다면 새 revision에 드러나야 한다.
3. batch는 최대 3개이고 예산 부족이면 미수행 상태를 보존해 중단해야 한다. 완료 플래그만 붙여 통과해서는 안 된다.
4. continue와 새 S5 rerun을 구별한다. 완료 batch는 중복 append되지 않고, 새 solve는 s_curve와 파생 적용 판정을 새로 생산해야 한다.
5. 후반 트랙의 독립 기전을 포함하는 제한 선택, 통합된 source provenance, 모델이 누락한 원천 후보를 검증한다. 최종 추천에 트랙별 할당량을 강제하지 않는다.
6. 보고서는 빈 절을 감추지 않고 수행 여부·적용 불가·후보 없음·미완료를 구별한다. 과거 회차의 H 호출을 이번 회차 실행으로 세지 않는다.
7. S0–S4 재사용, S6–S8 실제 모델 호출, S9 결정론적 렌더, S10 선택적 정제를 구분해 표시한다. 토큰과 단계 로그는 호출 증거이며 과학적 타당성 증명은 아니다.

이 문서는 수정 전 원인과 운영 증거를 보존하는 감사 기록이다. 수정 후 테스트 결과·배포 SHA·운영 재실행 결과는 별도 검증 기록으로 연결해야 한다.

## 후보 전달 보조 수정의 로컬 검증

감사 후 허가된 범위에서 `digest.select_ideas`와 `nodes._merge`를 수정했다. 선택은 기존 limit 안에서 원천 기법의 선택 횟수, 대상 문제, 기전을 차례로 고려한다. 최종 추천의 트랙 할당량이나 예산은 바꾸지 않았다. 통합 결과에는 원천별 `source_track`과 전체 `source_tracks`를 보존하고, 모델이 응답에서 빠뜨린 원천 아이디어는 구 bundle에서도 후속 검토 대상으로 남긴다.

오프라인 검증은 `.venv/Scripts/python.exe -X utf8 -m pytest`로 실행했다. 대상은 `test_idea_selection_coverage.py`, `test_pipeline_quality.py`, `test_retry_notifications.py`, `test_ax_portfolio_completion.py`, `test_ax_coherence.py`였다. 첫 실행에서 67개가 통과했고, coordinator 수정과 동시에 갱신되던 한 routing 기대값이 실패했다. 해당 routing 테스트와 신규 선택·출처 보존 테스트를 현재 파일로 다시 실행해 8개 모두 통과했다. 모델 API 호출은 테스트 fixture에서 차단했다. 이는 배포 후 Micro LED 재실행 검증을 대신하지 않는다.

## 후속 패치 독립 검토와 F/G/H 입력 검증

후속 작업 트리에서 모드 필수 기법의 batch 실행, 완료한 branch의 재사용, F만 s_curve를 생산·병합하는 처리를 확인했다. 일반 LLM 오류가 FAILED step을 남기고 기본값으로 반환되는 경우에도 트랙 완료로 커밋하지 않도록, 해당 branch가 생성한 실패 기록을 검사하는 보완이 추가됐다. 구형 tracks_run만 남은 S5를 명시적으로 재개할 때는 이전 표시를 새 완료 계약의 증거로 간주하지 않고 solve를 초기화·재검증하며 호환 사유를 기록한다. 완료 프로젝트를 자동 재실행하는 처리는 아니다.

독립 검토에서 발견한 `ax_recovery_phases` 재실행 정리 누락과 구형 AX의 legacy escalation 우회 경로도 수정된 것을 확인했다. source_hashes에는 새 solve_contract·digest·agent와 관련 실행 파일이 추가됐다. 후보 전달은 S5 원천 아이디어를 삭제하지 않고 S6의 제한된 상세 검토와 분리하는 방향으로 변경됐다. 구형 DEEP의 상세 후보 3개 상한은 별도의 호환 함수에서 최소 8개 검토 범위로 해석하며, 프로젝트 금액 한도와 비용 예약은 유지한다. 이러한 변경은 최종 추천 개수를 보장하지 않는다.

F/G/H의 최신 프롬프트에는 모순 placeholder가 있지만 이전 고정 본문에 같은 placeholder가 없으면 `prompt_vars`에 값을 넣어도 실제 요청에는 들어가지 않는다. 최신 본문에도 frame의 재정의 문제와 성공 기준은 직접 포함되지 않았으며, 제약이나 산업 설명에 우연히 중복됐을 때만 전달될 수 있었다. 실제 운영 export에는 pinned prompt 본문이 없어 Micro LED 당시 본문의 placeholder 존재 여부까지는 확인할 수 없다.

이를 보완해 F/G/H 요청에 한정한 `S5 문제 입력 계약 v1` 블록을 `agent.py`에서 실제 user 문자열 뒤에 추가했다. 이 블록에는 문제 정의·증상·성공 기준·기존 시도, 사용자가 확정한 대상·공간·시간·물리 범위·보완 사항, 기술/물리 모순이 들어간다. 기존 고정 프롬프트 본문은 보존한다. 다른 기법의 입력과 캐시는 이 변경으로 무효화하지 않는다.

`test_s5_prompt_input_compatibility.py`의 8개 오프라인 테스트가 7.55초에 모두 통과했다. 실제 F/G/H 실행기에서 `tracked_chat`에 전달되는 최종 문자열과 `step.input_slice.user`를 확인했으며, 최신 본문과 새 변수가 없는 합성 구형 본문 각각에서 핵심 입력이 전달됐다. 동일 입력은 캐시를 재사용하고 성공 기준 변경은 구형 본문에서도 캐시를 무효화한다. 이는 운영 원본 pin을 복구한 시험이나 모델 분석의 정확성 시험이 아니다.

별도 routing/coverage 회귀는 41개 통과 후 변경 중인 Part6 mock 1개가 실패했고, mock 갱신 후 해당 항목 재실행이 통과했다. 추가 provider 회귀에서는 16개가 통과했고 Part5만 응답하도록 작성된 기존 mock에 새 Part6 응답이 없어 실패한 항목을 ARIZ 담당에게 전달했다. 통합 테스트의 최종 결과와 운영 배포·재실행 결과는 별도 배포 기록을 기준으로 한다.
