# Railway·특허 수집·지식효과 검토 재개 기록

2026-09-16, Asia/Seoul. 사용자 요청에 따라 `elegant-freedom / production`을 복구했다. V3 설계 구현과는 별도 운영 작업이다.

## 재기동 결과

최초 재기동은 중지 전 배포를 `deploymentRedeploy(usePreviousImageTag: true)`로 복구했다. 그 재기동에서는 로컬 미배포 코드를 올리거나 새 모델 설정을 적용하지 않았다. [Railway 배포 API 안내](https://docs.railway.com/integrations/api/manage-deployments).

이후 사용자의 별도 “배포” 승인으로 10:39 KST에 AX V3 및 직접검토 출처 갱신의 운영 반영을 완료했다. 현재 모델·요율, 최종 배포 ID와 검증 결과는 [AX V3 배포 기록](TRIZ_AX_V3_DEPLOYMENT_20260916.md)을 따른다.

| 복구 순서 | 서비스 | 확인 결과 |
|---|---|---|
| 저장소 | Postgres, Redis, MySQL, MySQL-mGgL, triz-patent-vectors | 5개 SUCCESS |
| 애플리케이션 | Primary, Worker, triz_backend, triz_front | 4개 SUCCESS |
| 특허 수집 | triz-patent-indexer | SUCCESS, 기존 import/index 체크포인트에서 진행 |

09:01:02 확인 시 10개 서비스에 각각 활성 배포 1개가 있다. 중지 기록의 6개 볼륨 ID·서비스 연결·마운트 경로가 모두 일치하고 삭제 대기 볼륨이 없다.

- [운영 사이트](https://trizstudio.online): 홈페이지·healthz 정상, Google 로그인 설정 정상, 미로그인 실행 API는 401.
- 공개 분석 이력 48건 조회 성공. 업무 DB의 실행 상태 집계는 COMPLETED 48건.
- backend 내부 `/healthz`와 n8n Primary `/healthz`: HTTP 200.
- 새 유료 문제 분석을 생성하는 전체 흐름 시험은 이번 복구 검증에 포함하지 않았다.
- 중지 때 해제된 GitHub 자동 배포 트리거와 cron은 이번 작업에서 변경하지 않았다. 특허 워커는 현재 실행을 이어가며, 전체 적재가 끝나면 종료하는 기존 방식이다. 이후 정기 갱신 스케줄은 별도 설정이 필요하다.

로컬 증빙: `.deployment/restart-20260916-actions.json`, `restart-20260916-status.json`, `restart-20260916-runtime-1.json`, `restart-20260916-runtime-2.json`, `restart-20260916-vectors.json`. 복구 스크립트는 프로젝트·서비스·볼륨 정체성을 확인하고 이미 배포가 있는 서비스의 중복 재배포를 건너뛴다.

## 특허 수집·벡터 적재의 실제 진행

| 관측 시각(KST) | MySQL 특허 문서 | 벡터 적재 확인 문서 | 적재 대기 | 원본 순회 건수 |
|---|---:|---:|---:|---:|
| 09:01:43 | 5,716,444 | 5,715,931 | 513 | 8,053,000 |
| 09:05:52 | 5,722,990 | 5,722,694 | 296 | 8,062,000 |

두 관측 사이 문서 6,546건, 적재 확인 6,763건이 증가했다. 원본 체크포인트도 9,000건 전진했다. `source.complete=false`이며 전체 수집은 계속 진행 중이다. 이 수치는 해당 시점 누적량이며 새로 재개한 이번 작업만의 전체 수집량은 아니다.

09:06:24 Qdrant의 `patents_e5_small_v1`은 5,723,246 points, indexed_vectors 5,722,990, optimizer `ok`, collection status `yellow`로 응답했다. 적재와 인덱스 최적화가 진행되는 관측값이며 모든 인덱스가 완료됐다고 기록하지 않는다. DB·Qdrant 수치는 서로 다른 시각의 관측이므로 일치 여부를 단일 트랜잭션 검증처럼 해석하지 않는다.

## 지식효과 검토 재개

기존 `research_policy.json`의 `conversation_only`, `external_llm_calls_allowed=false`를 유지했다. 취소되었던 서버 자동 LLM 추출 서비스를 새로 만들지 않고, 보존된 커서 `AR-031180-A1` 다음의 공개 특허 40건을 받아 초록을 직접 검토했다.

| 이번 40건의 판단 | 수량 |
|---|---:|
| 기존 정본 원리 연결 LINK | 15 |
| 추가 조건·기구 확인 보류 DEFER | 16 |
| 설계 구성으로 보존 DESIGN_ONLY | 9 |

서로 다른 센싱 방식, 석고와 시멘트 수화, 전단농화와 시간 의존 농화, 신경망 사용과 지도학습을 동일한 효과로 자동 연결하지 않았다. 특허의 치료·성능 주장을 일반적 실증 결과로 바꾸지 않았다.

- 기록: `pilot/research/effects/manual-patents-2026-09-16-01.tsv`.
- 불변 검토: `pilot/research/effects/manual_reviews/2026-09-16-01.json`; 각 판단이 초록 fingerprint/content hash를 참조.
- 원시 페이지: `pilot/data/patent_effects_manual/page-000008.json`.
- 누적 8페이지 백업: `pilot/research/effects/manual_archives/2026-09-16-01.json.gz`.
- 연결 근거는 연구용 `literature_links.json`, `accepted_literature_sources.json`에 반영했다. 정본 항목 수는 19개 기능군·269개이며 새로운 원리를 무리하게 추가하지 않았다. 이번 근거 추가분은 운영 이미지에 배포하지 않았다.

누적 조회는 **1,440건**, 직접 읽은 초록은 **992건**, 초록 없음 448건, 미검토 초록 0건이다. 누적 판단은 LINK 422 / DEFER 328 / DESIGN_ONLY 240 / REJECT_CLAIM 2이다. 다음 커서는 `AR-031824-A1`, 기존 순회 상한은 `ZA-F202500713-S`다.

다음 검토는 `next-request.json`을 사용하여 **page-000009.json**으로 가져오면 된다. 코드만으로 의미 판단하거나 대화 종료 뒤 자동 추출이 계속되는 구조는 아니다. 특허 수집 서버의 지속 실행과 이 직접 검토 경로를 구분한다. 전체 특허에 대한 효과 검토는 미완료다.

## 검증

- V3 동봉 `validate_contracts.py`: 통과; schema/예제 관계·거부 조건·비용 산술 범위.
- `record_manual_effect_reviews.py`: 40개 판단의 유효한 정본 키·원문 연결, 누적 커서·미검토 수 확인.
- `publish_effects.py --check`: 19개 기능군, 269개 효과, 문헌 연결 247개, 편집 지식만 22개. 발행 가능한 구조 확인이며 실증 검사는 아님.
- 기존 `test_manual_effect_reviews.py`, `test_effect_catalog.py`: **12 passed**.
- 압축 백업을 다시 읽어 8페이지 원본 JSON과 동일함을 확인.

V3 코드 반영의 승인 대상은 [구현 전략](TRIZ_AX_V3_IMPLEMENTATION_STRATEGY.md)에 정리했다.
# 후속 확인 — 2026-09-16 10:03~10:10 KST

특허 DB 5,800,577건, 벡터 색인 5,800,102건, 대기 475건을 확인했다. 재개 직후의 5,716,444건보다 84,133건 증가했다. 전체 원천 순회는 계속 진행 중이다. 사업 DB, backend `/healthz`, n8n Primary `/healthz`는 정상 응답했다.

n8n Worker의 `sleepApplication=true`와 SLEEPING 상태를 발견했다. 큐 Worker는 HTTP 수신 대기 서비스가 아니므로 절전을 해제하고 기존 서비스 인스턴스를 재배포했다. 새 deployment `e22f9fcc-f2ff-401f-b8c0-d7e2b6f9b763`는 SUCCESS다. 원래 6개 볼륨은 그대로 보존했다. [Railway 절전 동작 문서](https://docs.railway.com/deployments/serverless)에 따라 컨테이너 재생성까지 수행했다.

직접검토 두 번째 묶음 40건: LINK 18, DEFER 14, DESIGN_ONLY 7, REJECT_CLAIM 1. 누적 직접 읽은 초록은 1,032건, 초록 없는 자료 448건, 미검토 0건, 다음 커서 `AR-032666-A4`다. 청구항·전문을 검토한 수가 아니다. 외부 LLM 추출 호출은 0이며, serving JSON의 연결 출처를 보강했다.
