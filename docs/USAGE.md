# 사용자 흐름과 API 안내

최종 갱신: 2026-09-30. 현재 웹 UI와 백엔드 코드를 기준으로 한다. 실행 모드의 상세 계약은 [MODES](MODES.md), 단계별 함수는 [STAGES](STAGES.md), 설치·운영은 [OPERATIONS](OPERATIONS.md)를 참조한다.

## 분석 시작

문제, 개선하려는 결과, 악화되는 현상, 지켜야 할 수치·조건을 적는다. 모르는 정보를 확정값으로 적을 필요는 없다. 필요하면 자료를 첨부한다. 서버는 최대 8개, 파일당 기본 25MB를 허용하며 크기는 `MAX_UPLOAD_MB` 설정을 따른다.

지원 형식은 PDF, XLSX, 텍스트/TXT/Markdown, CSV, JSON, YAML, LOG, PNG/JPG/JPEG/WEBP/BMP다. 이미지와 PDF의 OCR 추출이 충분하지 않으면 도면 관계나 핵심 수치를 본문으로 보완한다. 원문은 [docparse.py](../pilot/triz/tools/docparse.py)에서 페이지·시트·행 위치를 붙여 추출한다.

| UI 모드 | API 값 | 의미 |
| --- | --- | --- |
| 빠른 탐색 / FAST | `LITE` | 허용된 기법 중 제한된 초기 탐색 후 다음 행동 선택 |
| 표준 분석 / BALANCED | `FULL` | 더 넓은 허용 집합에서 초기 탐색과 후속 행동 선택 |
| 심층 분석 / Deep | `DEEP` | 등록된 전체 트랙을 검토하는 심층 계약 |

`FAST`, `BALANCED`는 설명용 이름이다. API의 `mode`에는 `LITE`, `FULL`, `DEEP`을 보낸다. 현재 신규 AX 실행과 과거 실행은 저장된 계약이 다를 수 있으므로 화면 이름만으로 실제 실행 트랙을 단정하지 않는다.

운영 UI에서는 Google 로그인을 사용한다. 현재 무료 베타 화면은 문제·분석 내용·해결안·보고서가 Sample Case에 공개되는 것에 대한 동의를 받는다. 이것과 학습 동의는 다른 항목이다. 검토·피드백의 프로젝트 범위 학습은 기본 `PROJECT_ONLY`이며 별도 선택 체크박스가 없다. API의 명시적 `NO_TRAINING` 입력은 지원한다.

## 분석 중 확인할 내용

작업 화면의 탭은 **분석 현황 → 문제 정의 → 해결안 → 보고서 → 피드백**이다. 분석 현황에는 다음 단계가 진행 순서로 나타난다.

1. 실행 계획
2. 산업·기술 심층 검토
3. 문제 추출·역질의
4. 대상 시스템 확정
5. 시스템·기능·자원·인과 분석
6. 이상해결책·모순 정의
7. 다중 기법 해결책 탐색
8. 개념 구체화
9. 제약 검토
10. 근거 자료·적용 조건 검토
11. 다직군 평가
12. 시각화 보고서
13. 피드백

진행 중 질문이 나오면 해당 화면에서 답변한다. 질문 종류는 다음과 같다.

| 화면 | 사용자가 하는 일 |
| --- | --- |
| 추가 질문(`CLARIFY`) | 추천 답변 또는 직접 입력으로 부족한 정보를 보완한다. 산업 검토 질문이면 산업 분류·검토 깊이도 선택한다. 비운 답은 알려진 사실로 간주되지 않는다. |
| 시스템 확인(`CONFIRM`) | 분석할 시스템 후보를 고르고 경계·조건을 보완한다. |
| 제약 보류안 결정(`DECIDE`) | 각 보류안을 **조건부 후보로 유지** 또는 **이번 제안에서 제외**로 결정한다. 모든 보류안의 선택이 필요하다. |
| 피드백 대기(`FEEDBACK`) | 보고서를 검토해 의견을 남기거나 **피드백은 나중에 남기고 완료**를 선택한다. |

유지 선택은 검토 가치에 대한 약한 긍정 효용 신호다. 기술적 `CONDITIONAL`, 부족한 증거, 미확인 조건이 자동으로 충족되지는 않는다. 화면의 유지 값은 API에서 `accept`, 제외는 `drop`이다.

과학효과 상세 조건을 별도로 입력하게 하던 질문 UI와 **기법 선택과 학습 상태** 카드는 현재 사용자 탭에 표시하지 않는다. 필요한 실행·학습 진단은 소유자용 API에 남아 있다.

## 해결안과 보고서

해결안 탭에서 작동 원리, 변경 사항, 예상 효과, 제약 판정, 검증 필요사항, 직군별 검토 의견과 근거를 확인한다. 특허·논문이 검색되었다는 사실과 해당 해결안의 적용 조건이 입증되었다는 사실은 구분해서 읽는다.

보고서의 분리 접근 도식은 저장된 각 적용안의 내용으로 그린다. 미적용 판단은 검토 기록으로 남는다. Su-Field/76표준해 도식도 저장된 실제 모델에 근거하며, 일반 소개용 도식을 적용 결과 대신 넣지 않는다. 소개 화면에서는 76개 표준해와 공식 하위·대안·발전 설명을 별도로 볼 수 있다.

모바일 또는 터치 화면에서는 **한 장이 한 페이지**다. 장 번호, 목차 선택, 이전/다음 버튼으로 이동한다. 장 내부의 표·도식·하위 절은 같은 페이지에 남고, 목차 번호는 한 번만 붙는다. 데스크톱에서는 장들이 이어서 표시된다. 일부 상세 기록은 펼치기 안에 있다.

**보고서 다운로드**는 HTML 파일을 받는다. 브라우저에서 열어 인쇄하거나 PDF로 저장할 수 있다. API에는 Markdown과 HTML·Markdown·SVG 묶음 ZIP도 있다. 다운로드는 저장된 데이터의 렌더링이며 새 분석 호출이 아니다.

피드백 탭은 해결안별 1~5점과 **실제 적용 가능성과 보완할 점** 의견을 받는다. 점수를 선택한 해결안만 제출된다. 피드백을 나중에 남겨도 되며, 학습 반영은 저장된 평가·대상·범위·시점과 해당 정책의 적격성 검사에 따른다. 제출 즉시 모든 다음 분석의 순위가 바뀐다고 보장하지 않는다. 자세한 데이터 흐름은 [LEARNING](LEARNING.md)을 본다.

## 멈췄을 때

`WAITING_HUMAN`이면 화면의 질문에 답한다. `INTERRUPTED` 또는 `FAILED`이면 안내와 최근 완료 단계를 확인한 뒤 **이어서 실행**을 사용한다. 저장된 단계에서 재개하며, 새 프로젝트 생성이나 과거 단계 전체 재실행과는 다르다.

예산 소진은 같은 프로젝트의 남은 금액을 새로 만들어 주지 않는다. 공급자 계정 오류도 재개 버튼만으로 해결되지는 않는다. 응답 유실로 사용량이 미확인인 경우에는 이전 비용 예약을 유지한 상태에서 추가 재시도 비용 가능성을 안내한다. 사용자가 동의하고 서버가 재시도를 허용할 때만 진행한다. 복구할 수 없는 항목은 운영자가 확인한다. 절차는 [OPERATIONS](OPERATIONS.md)에 있다.

UI 근거: 고정 버전의 [Workspace.jsx](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/src/pages/Workspace.jsx), [Shared.jsx](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/src/components/Shared.jsx), [reportPages.js](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/src/lib/reportPages.js), [usageRecovery.js](https://github.com/equipment0226/triz_front/blob/5f4039073aee7a5168378d1035f18e3336980ef9/src/lib/usageRecovery.js).

## 개발자 API

라우트 구현은 [api/main.py](../pilot/api/main.py), AX 확장은 [ax/api.py](../pilot/triz/ax/api.py)에 있다. 운영 프런트 서버가 `x-triz-app-token`과 사용자 세션을 연결한다. 내부 서비스용 Bearer 토큰과 혼용하지 않는다. 인증이 켜진 환경에서 실행 ID는 소유자 범위로 제한된다.

| 메서드·경로 | 용도·입력 |
| --- | --- |
| `POST /api/runs` | multipart `query`, `mode`, `files`, 공개 동의 등. `Idempotency-Key`로 같은 접수의 중복 생성을 방지. `202`와 `run_id` 반환 |
| `GET /api/runs`, `GET /api/runs/{id}/view` | 소유 실행 목록과 UI용 상태·질문·해결안·보고서 블록 |
| `GET /api/runs/{id}`, `GET /api/runs/{id}/steps`, `GET /api/runs/{id}/steps/{step_id}` | 저장 상태와 단계 실행 기록 |
| `GET /api/runs/{id}/events` | 진행 이벤트 스트림 |
| `POST /api/runs/{id}/resume` | `{"payload":{...}}`. 추가 질문은 `answers`, 시스템 확정은 `candidate_id`·`amendment`, 보류안은 `decisions` 사용. `interrupt_id`를 보내면 현재 질문과 일치하는지 검사 |
| `POST /api/runs/{id}/continue` | 입력 대기가 없는 중단 실행을 저장 단계에서 재개 |
| `POST /api/runs/{id}/rerun` | `stage`, `instruction`. 지정 단계 재실행이며 후속 결과를 다시 만들 수 있는 변경 작업 |
| `POST /api/runs/{id}/feedback` | `solution_feedback`의 `concept_id`, `rating`, `comment` 등. 피드백 대기 중이면 S10 재개, 완료 후이면 저장 피드백 경로 사용 |
| `GET /api/runs/{id}/report` | 기본 `md`, `format=html`, `format=file`, `format=bundle` 지원 |
| `GET /api/runs/{id}/report/context` | 해결안·평가·근거 요약 |
| `GET /api/runs/{id}/ax/diagnostics` | 비용·선택·학습 준비 상태 진단 |
| `GET /api/runs/{id}/ax/evaluations`, `/ax/effect-reviews` | 공통 평가 및 효과 검토 이력 |
| `GET` / `POST /api/runs/{id}/ax/usage-recovery` | 미확인 호출 조회 / 특정 task의 추가 재시도 승인. POST에는 `task_id`, `expected_epoch`, `acknowledge_possible_duplicate_charge:true` 필요 |
| `GET /api/public/runs`, `GET /api/public/runs/{id}/view` | 공개 동의가 저장된 사례 조회 |

`/internal/execute`는 n8n이 쓰는 서비스 경로다. 일반 UI는 이 경로를 직접 호출하지 않는다. 별도 특허 작성의 사건·문서 API는 [patent_draft 안내](../pilot/patent_draft/README.md)를 따른다.
