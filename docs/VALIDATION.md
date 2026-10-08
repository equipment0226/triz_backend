# 검증 기록

## 2026-10-08 · 분석 필수 검증과 수리

변경 영향을 받는 **31개 테스트 파일, 574개 테스트가 통과**했습니다. BASIC의 필수 유익성·확정 경계, 필수 기준과 가중 점수 분리, 요소별 지적 전달, 부분 JSON에서 전체 스키마 복구, 수리 후 재검증·실패 중단, 분석 요소 참조와 관측/가설, 표준해 구조를 확인했습니다. 캐시·이전 bundle·유료 응답 재사용·사용량·S6 후보 검토·ARIZ·독립 직군 평가의 관련 회귀도 포함합니다.

과거 테스트의 provider 응답에 누락된 `meta`와 criterion별 점수를 보완하고, 표준해 보고서 fixture에 실제 적용 모델을 명시했습니다. 변경 전 별도 체크아웃에서 기존 fixture 실패를 재현해 런타임 회귀와 구분했습니다. 이 결과는 저장소 전체 테스트의 완주 결과가 아닙니다.

운영에 저장된 99개 실행의 최종 분석 산출물과 단계별 최신 원출력 973개를 새 코드로 오프라인 검사했고 검사기 예외는 0건입니다. 구조·참조 오류와 새 필수 필드 누락을 검출한 결과이며, 과거 실행 전체의 의미 오류율이나 새 모델의 정확도 향상을 입증하지 않습니다. 서로 다른 속성을 PC로 묶는 등의 의미 오류는 독립 검증 기준과 예시에 반영했으며 새 모델 출력 평가는 수행하지 않았습니다.

유료 모델 호출·운영 데이터 변경은 0회입니다. 근거 자료는 로컬 `.deployment/basic-function-audit-20261008/`의 `targeted-regressions.xml`, `test-manifest.json`, `analysis_checks_replay.json`, `nonbasic_audit.json`, `nonbasic-report.html`, `downstream_audit.json`입니다. 운영에 적용된 버전과 로컬 변경 상태는 변경 manifest를 별도로 확인해야 합니다. [분석 계약](ANALYSIS_QUALITY.md)

갱신일: 2026-09-30. 보고서 수정과 문서 정비의 확인 범위입니다. 운영 비용 절감이나 기술적 성능 향상을 입증하는 자료와는 구분합니다.

## 보고서 수정

| 항목 | 결과 | 확인한 내용 |
|---|---|---|
| 관련 회귀 테스트 | **346개 통과** | 분리 적용 도식·해결안 계보·표준해·보고서·표시 용어·기법 실행 상태 |
| 최종 표시 수정 후 재검증 | **210개 통과** | 해결 범위 서술 제거, 최종 해결안의 중복 분리 도식 제거, 기존 도식·출력·상태 보존 |
| 브라우저 확인 | **1440px / 390px 통과** | JavaScript 오류 0, 도식 텍스트 넘침 0 |
| Introduction 자산 | **185개 기존 도식 해시 동일** | 보고서 변경으로 설명용 자료가 바뀌지 않음 |
| 유료 모델 호출 | **0회** | 저장 데이터와 합성 fixture로 검사 |
| 운영 분석·피드백 데이터 변경 | **0건** | 새 분석·재추론·피드백 제출·운영 데이터 보정 미실행 |

분리원리는 `applicable=True`인 저장 적용안에 한해 도식을 만듭니다. 같은 원리라도 실제 적용 내용이 다르면 각각 다르게 표시합니다. 도식은 기법별 아이디어 섹션에만 남기고 최종 해결안에는 반복하지 않습니다. 타산업 기능 이식 뒤의 해결 범위·탐색 보완 서술도 보고서에서 제외합니다. 원본 상태와 기존 해결안 도식은 보존합니다.

76표준해는 저장된 `resulting_su_field` 또는 `resulting_model`이 있을 때 적용 그림을 표시합니다. 일반 표준해 그림, 하위 대안·분기·발전 순서 참고 그림은 보고서에 덧붙이지 않습니다. S3 물질-장 모델은 유지합니다.

주요 테스트: [분리 도식](../pilot/tests/test_separation_application_diagrams.py), [해결안 계보](../pilot/tests/test_separation_solution_groups.py), [해결안별 보고서](../pilot/tests/test_solution_specific_separation_report.py), [표준해 도식](../pilot/tests/test_standard_diagrams.py), [보고서·Introduction 분리](../pilot/tests/test_report_introduction_design.py).

## 문서·흐름도

| 항목 | 결과 |
|---|---|
| UI Stage 순서 | `pipeline.PIPELINE`의 13개 항목과 AST 대조 |
| Stage 상세 흐름 | 13개 모두 입력·출력 표와 개별 흐름도 포함 |
| 전체 흐름 | 중간 검증, 과학효과, 특허·논문 검색 위치 표기 |
| 학습 흐름 | AI 검토, 제약 keep/drop, 해결안 피드백을 효과/Q 각각의 데이터·보상에 연결 |
| 모드 흐름 | 빠른·표준·심층 각각 작성; 빠른·표준 도식에 보상·학습 계수 표기 |
| Mermaid | **27개 실제 브라우저 렌더·독립 SVG XML 검사 통과** |
| 가독성 표본 | Stage 도식 2개에서 한글·영문·화살표·라벨 확인 |
| 코드 근거 | 모드 계약, 검증기, 평가 수집, quality, Q/효과 학습, worker·registry 호출 대조 |

T등급과 실제 모델명, AX와 Q-learning, 보고서 총점과 학습 quality, 학습 생성과 활성 정책 사용을 구분했습니다. 현재 AI 검토는 효과 학습뿐 아니라 Q의 회차 최종 quality에도 기여합니다.

## 검증 산출물

다음은 작업공간에 보관한 로컬 자료입니다. 배포용 백엔드 Git에는 포함하지 않습니다.

| 로컬 경로 | 내용 |
|---|---|
| `.deployment/report-application-20260929/regressions-final.xml` | 최종 회귀 결과 346 pass |
| `.deployment/report-application-20260929/browser-verification.json` | 화면별 렌더 결과 |
| `.deployment/report-application-20260929/change-manifest.json` | 보고서 변경 경로·해시 |
| `.deployment/docs-refresh-20260929/report-final-regressions.xml` | 최종 추가 수정 후 210 pass |
| `.deployment/report-final-20260930/change-manifest.json` | 최종 배포 코드·테스트 해시 |
| `.deployment/report-final-20260930/browser-verification.json` | 최종 표시 수정 후 데스크톱·모바일 확인 |
| `.deployment/public-report-final-20260930.json` | 공개 보고서 3건의 최종 표시 확인 |
| `.deployment/docs-refresh-20260929/stage-evidence.json` | Stage와 소스 근거 |
| `.deployment/docs-refresh-20260929/learning-evidence.json` | 학습 수식·호출·링크 근거 |
| `.deployment/docs-refresh-20260929/mermaid-render-results.json` | 실제 렌더와 SVG 검사 |
| `.deployment/docs-refresh-20260929/rendered/` | SVG 27개와 표본 PNG |
| `.deployment/docs-refresh-20260929/cleanup-manifest.json` | 삭제 파일·해시·대체 사유 |
| `.deployment/docs-refresh-20260929/superseded-documents.zip` | 정리 전 Markdown 원본 |

Git에 있던 문서는 이전 커밋에서도 복구할 수 있습니다. 런타임 프롬프트·라이선스·원전 검토·연구 자료·PDF는 삭제 대상에서 제외했습니다.

## 확인 범위의 한계

전체 테스트 스위트를 다시 실행한 것은 아닙니다. 보고서 변경에 관련된 회귀 범위와 문서 검증을 수행했습니다. 기존 기록의 렌더 동작은 확인하되, 유료 모델로 새 문제를 생성해 끝까지 실행하는 검증은 하지 않았습니다.

운영 비용·품질 개선, 정책 활성화율, 학습 표본 증가 효과를 새로 실험하지 않았습니다. 실제 반영을 판단하려면 공통 평가 → 유효 자료셋 → 검증 모델 → 활성 포인터 → 다음 실행의 선택을 연결해야 합니다. [학습 문서](LEARNING.md)에 확인 순서가 있고, 배포 결과는 [변경 기록](CHANGELOG.md)에 있습니다.
