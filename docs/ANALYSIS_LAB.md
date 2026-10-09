# Railway n8n: TRIZ API 검증

기존 개인 Project에 다음 두 워크플로가 있다. 둘 다 비활성 상태이며 첫 Form Trigger의 **Test URL**로 수동 실행한다.

- [TRIZ API 검증 — 수동 문제 분석](https://primary-production-5df6a.up.railway.app/workflow/TRIZAnalysisLabManual20261009)
- [TRIZ API 검증 — 해결안 개별 검증](https://primary-production-5df6a.up.railway.app/workflow/TRIZAnalysisLabInspect20261009)

## 문제 입력과 수동 재개

1. 수동 문제 분석을 열고 실행을 시작한 뒤 첫 노드의 Test URL을 연다. `raw_query`에 문제를 입력한다. `mode`는 STANDARD/QUICK/DEEP, `budget_usd`는 0 초과 5 이하이며 기본값은 5다. 첫 실행에서는 `continuation`, `human_response`를 비운다.
2. 마지막 출력의 `pending`을 확인한다. 기존 S0 도메인 확인과 S1·S2·S7의 사용자 확인/선택 요청을 그대로 표시하고 실행을 종료한다.
3. 출력의 `continuation` 전체를 복사한다. 다시 Test URL을 열어 이 값을 입력하고, `human_response`에 현재 `pending.interrupt_id`와 요청에 맞는 응답을 JSON 객체로 입력한다. 재개할 때 `raw_query`는 비워둔다.
4. 다음 확인 요청 또는 S9 보고서까지 진행한다. 완료 출력의 `solutions`, `steps`, `report`를 확인한다. 출력은 실행 화면에서 직접 복사해 보관한다.

예를 들어 시스템 선택 요청의 응답은 `{"interrupt_id":"현재 요청 ID","candidate_id":"표시된 시스템 후보 ID"}`다. S7 선택 응답은 `{"interrupt_id":"현재 요청 ID","decisions":{"표시된 해결안 ID":"accept","다른 해결안 ID":"drop"}}` 형태다. 실제 요청의 후보와 필수 조건을 먼저 확인한다. 응답을 별도 `payload` 객체로 감싸지 않는다.

`pending` 없이 FAILED/INTERRUPTED로 끝난 경우에도 진단과 과금 내역을 먼저 확인한다. 같은 출력의 `continuation`으로 새 수동 실행을 하면 기존 재개 가드를 적용한다. 통신 오류 뒤에는 자동 재시도하지 않는다. 서버에서 이미 유료 호출이 끝났을 수 있으므로, 오래된 출력으로 다시 실행하면 별도 과금이 발생할 수 있다. DB를 사용하지 않는 이 테스트 흐름은 네트워크 응답 유실 시 호출의 단 한 번 실행을 보장하지 않는다.

## 해결안별 확인

해결안 개별 검증의 Test URL에 분석 출력의 `continuation`을 입력한다. `candidate_id`에 `solutions[].concept_id`를 입력하면 해당 해결안만 표시하고, 비우면 모든 해결안을 각각의 item으로 표시한다. 제외된 후보도 포함한다.

`solution_validation`에는 후보 내용, 유지/제외 이유, 권고 여부, 품질 판정, 제약 검토, 검증 기록, 근거 연결, 개별 평가가 있다. 아직 실행하지 않은 평가나 확보하지 못한 근거는 비어 있다. 이 흐름은 기존 판정과 실제 근거를 읽으며 추가 모델 호출을 하지 않는다.

## 원본 실행과 데이터 범위

n8n의 12개 stage 노드는 기존 Railway API와 인증된 MCP 서버를 통해 원본 `pipeline.PIPELINE[:12]`를 실행한다. 단계 순서는 `s0_bootstrap → s0_research → s1_intake → s2_confirm → s3_analyze → s4_define → s5_solve → s6_concept → s7_gate → s8_references → s8_evaluate → s9_report`다. 각 stage 내부의 node/agent, 프롬프트 파일, 분기·병렬 실행, 검증·수정 규칙은 기존 함수가 제어한다. 내부 node를 별도 n8n 노드로 복제하지 않으며 실제 입력·출력·판정은 `steps`에 표시한다.

지식 파일과 원본 프롬프트를 그대로 읽는다. 특허검색은 기존 E5 임베딩과 Qdrant 전체 산업 유사도 검색, 기존 특허 SQL DB의 제목·초록·분류 조회 경로를 사용한다. 기존에 구축된 컬렉션과 고정 모델 캐시를 읽으며 새 수집·인덱싱을 하지 않는다. 원본 검색과 동일하게 청구항·명세서 전체를 조회하지 않으며, 구축 중인 코퍼스는 PARTIAL로 표시한다.

분석 실행은 요청마다 별도 프로세스의 메모리 SQLite를 사용한다. 상태와 과금 예약 기록은 서명된 `continuation`으로 전달하고 운영 분석 DB에는 저장하지 않는다. 보고서·SVG 임시 파일은 응답에 포함한 후 제거한다. S10 피드백, 보상 기록, 강화학습, 과거 학습 사례 주입은 실행하지 않는다. 분석에 필요한 품질 검증은 유지한다. 코드·프롬프트·지식 버전이 바뀌면 기존 continuation 재개를 거절한다. continuation은 서명된 값이며 암호화된 값은 아니므로 분석 내용과 함께 취급한다.

n8n은 기존 queue 모드를 사용하므로 실행 중 입력을 자체 PostgreSQL에 임시 기록한다. 성공·실패 결과 저장, 수동 실행 저장, 진행 저장은 모두 꺼져 있다. 실제 문제나 continuation을 노드 설정·pinData·staticData에 넣지 않는다. TRIZ 분석/피드백 DB에 저장하지 않는다는 설정과 n8n 실행 중 임시 기록은 별개다.

## API와 정의 재생성

서비스 인증이 필요한 API는 `GET /internal/lab/manifest`, `POST /internal/lab/begin`, `POST /internal/lab/stage`, `POST /internal/lab/inspect`다. manifest에서 원본 함수, 프롬프트 후보, 지식 파일, 소스 fingerprint를 확인한다. 인증은 기존 n8n의 `TRIZ Studio Service` Header Auth credential을 참조한다.

`pilot` 디렉터리에서 `python scripts/export_analysis_lab_workflows.py`로 `deploy/n8n/analysis-lab-manual.json`과 `analysis-lab-inspect.json`을 재생성한다. 실제 질의나 서비스 키를 정의 파일에 넣지 않는다.
