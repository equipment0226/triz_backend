# 특허 인덱서 복구 기록

2026-09-22 KST. 사용자 요청에 따라 Crash 서비스와 DB를 점검하고 적재를 재개했다.

## 확인한 원인과 조치

- 실제 Crash는 `triz-patent-indexer`였다. MySQL·Qdrant는 응답했고 다른 Worker와 DB 서비스도 정상 상태였다. 데이터베이스 재생성·초기화는 하지 않았다.
- 이전 배포 `80b542a9-d6f3-465e-a832-18a7dcb92a83`의 2026-09-21 18:33:46 UTC 로그에 `ResponseHandlingException`, 재시도 4회 후 PAUSED가 기록되어 있다. source.complete=false였으므로 **작업 완료로 인한 종료가 아니라 오류 종료**였다.
- Qdrant 클라이언트 응답 처리 계층의 예외까지 확인했으며 내부 transport 예외가 로그에 남지 않아 네트워크·서버 지연 등 구체적인 하위 원인은 확정하지 않았다.
- 기존 체크포인트를 유지해 재시작했다. 원본 수집과 벡터 적재가 다시 진행되는 것을 여러 시점의 증가량과 IMPORT·INDEX 로그로 확인했다.
- Qdrant 요청의 실제 설정 `PATENT_SEARCH_TIMEOUT_SECONDS`를 20초에서 60초로 변경하고 이전 이미지로 재배포했다. 초기에는 사용되지 않는 `PATENT_SEARCH_TIMEOUT`을 설정했으나 런타임 20초가 유지되는 것을 발견해 정확한 설정명으로 수정했다. 수정 후 유효값 60초를 직접 확인했다.
- 현재 인덱서 배포 `07c13401-874d-48cb-a3f9-812f55c96e56`, SUCCESS. sleepApplication=false, ON_FAILURE, restartPolicyMaxRetries=10을 유지했다. 이번 조치는 복구와 시간 여유 확대이며 확인되지 않은 하위 원인의 영구 해결을 의미하지 않는다.
- 컨테이너 메모리 한도 24 GB, 초기 사용량 약 204 MB, oom/oom_kill=0. Qdrant green / optimizer ok. 데이터 볼륨·소스 체크포인트·벡터 식별자를 보존했다.

## 적재 관찰

- 복구 전후 기준 22:50 UTC: MySQL 8,117,570건, 벡터 대기 811건, Qdrant 8,116,823포인트.
- 23:28:56 UTC: MySQL 8,161,655건, 벡터 대기 804건, Qdrant 8,160,851포인트, green / optimizer ok.
- 23:32:57 UTC 로그: source.scanned=11,472,000, accepted=8,167,118, complete=false. 이어서 INDEX 로그가 계속 발생했다.
- 최종 23:35:07 UTC(08:35:07 KST): MySQL 8,169,516건, 대기 211건, Qdrant 8,169,305포인트, green / optimizer ok. 기준 대비 원본 51,946건·벡터 52,482포인트 증가했다.
- 최종 런타임 제한시간 60초, 메모리 사용량 약 2.01 GB / 한도 24 GB, oom/oom_kill=0. 과학효과 배포 중에도 인덱서 배포 ID와 처리 흐름이 유지됐다.
- DB·체크포인트·벡터 수는 한 트랜잭션의 스냅샷이 아니므로 조회 시차에 따른 소폭 차이가 있을 수 있다.

증거: `.deployment/recovery-before-20260922.json`, `indexer-structured-20260922.json`, `recovery-actions-20260922.json`, `indexer-timeout-corrected-20260922.json`, `indexer-resources-confirmed-20260922.json`, `patent-runtime-predeploy500-20260922.json`, `worker-after500-20260922.json`.
