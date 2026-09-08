# BigQuery 특허 조회 연결

특허 DB를 복제하지 않고 `patents-public-data.patents.publications`를 읽는다.
공개번호·영문 제목·영문 초록·공개일을 기존 해결안 적용성 검토에 전달한다.
Google Patents 웹페이지를 다시 요청하지 않으므로 웹 검색의 503 차단과 독립적이다.
원문 링크는 데이터에서 읽은 공개번호로 구성한다. 링크 페이지 접근 성공이나 청구항·실증 성능 검증을 뜻하지 않는다.

## Railway 설정 순서

1. Google Cloud의 사용자 프로젝트(현재 특허 조회 프로젝트는 `project-fb0bcce1-74c5-472d-a91`)에서 BigQuery API를 활성화한다.
2. 서비스 계정을 만들고 **사용자 프로젝트**에 `BigQuery Job User` (`roles/bigquery.jobUser`) 역할을 부여한다. 공개 데이터 조회에 프로젝트 전체 Owner/Editor 역할은 필요하지 않다.
3. 서비스 계정 JSON을 Railway **triz_backend** Variables의 `GOOGLE_SERVICE_ACCOUNT_JSON`에 넣는다. `BIGQUERY_PROJECT_ID`에는 쿼리 실행 프로젝트 ID를 넣는다. Google 로그인의 `GOOGLE_CLIENT_SECRET`과는 다른 인증이다. 키를 저장소·채팅·로그에 넣지 않는다. ADC를 이미 구성한 실행 환경에서는 JSON 대신 ADC를 사용할 수 있다.
4. 아래 상한 변수를 확인하고 재배포한다. 기본값을 올리거나 결제 설정을 변경할 필요가 있는지는 먼저 dry run으로 판단한다.
5. 백엔드 컨테이너의 `/app/pilot`에서 `python scripts/check_bigquery_patents.py`를 실행한다. 기본 동작은 무료 dry run이며 실제 특허 조회 작업을 실행하지 않는다. 성공 시 테이블 갱신 시각·행 수·예상 처리량을 출력한다. 인증·권한·테이블 스키마·비용 상한 실패 시 안전한 오류 코드만 출력한다.
6. dry run이 상한 내에서 통과하면 `python scripts/check_bigquery_patents.py --execute`로 기본 샘플 검색 3개를 한 작업으로 확인한다. 이후 `PATENT_SEARCH_PROVIDER=bigquery`를 설정하고 재배포한다.

등록된 인증 정보가 없으면 연동 코드는 배포할 수 있지만 실제 데이터 조회와 운영 전환은 완료할 수 없다.

2026-09-08 운영 검증에서 인증·dry run·실제 조회가 통과했다. 기본 샘플 검색 3개를 한 작업으로 실행해
총 18건의 후보를 받았으며 실제 처리량은 약 214.62 GiB였다. 256 GiB 작업 상한 이내이나
768 GiB 월 상한에서는 같은 규모의 캐시 미적중 작업을 약 3회 실행할 수 있다. 같은 검색 묶음의
캐시 재사용은 추가 조회를 실행하지 않는다. 한 분석이 두 단계에서 서로 다른 검색 묶음을 사용한다는 점에 유의한다.

## 설정 및 비용 통제

| 변수 | 기본값 | 의미 |
|---|---|---|
| `PATENT_SEARCH_PROVIDER` | `legacy` | `bigquery` 선택 시 특허 조회를 BigQuery로 전환. 기존 논문 검색은 유지 |
| `BIGQUERY_PROJECT_ID` | 없음 | 사용자 소유 쿼리 실행 프로젝트 |
| `BIGQUERY_LOCATION` | `US` | 공개 데이터의 조회 위치 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 없음 | 서비스 계정 JSON. 없으면 ADC 사용 |
| `BIGQUERY_MAX_BYTES_BILLED` | `274877906944` | 작업당 최대 256 GiB |
| `BIGQUERY_MONTHLY_BYTE_LIMIT` | `824633720832` | 이 배포가 실행하는 작업의 UTC 월별 합계 최대 768 GiB |
| `BIGQUERY_TIMEOUT_SECONDS` | `90` | 쿼리 실행·결과 대기 제한, 초과 시 취소 요청 |
| `BIGQUERY_CACHE_SECONDS` | `86400` | 같은 검색 묶음의 결과 재사용 시간 |

- 한 분석 단계의 특허 검색어를 하나의 parameterized SELECT로 묶는다. SQL 생성·DDL·전체 데이터 복사는 하지 않는다. 일반적인 분석은 해결안 도출 전과 근거 검토 단계에서 각각 조회한다.
- 실행 전 dry run으로 예상 바이트를 확인한다. 예상량에 여유분을 더한 값과 작업 상한 중 작은 값을 `maximum_bytes_billed`로 전송한다. 예상량이 상한을 넘거나 알 수 없으면 실제 조회를 실행하지 않는다.
- 영문 핵심어 중 최소 2개, 약 2/3 이상이 제목·초록에 등장한 문헌을 후보로 삼는다. 제목 일치·초록 유무·공개일로 순서를 정하고 같은 패밀리를 합친다. 검색어당 최대 6개를 기존 agent의 기능·작동 원리 대조에 넘긴다. 영문 제목이 없는 문헌은 검색 대상에서 제외되며 초록이 없는 자료를 강한 해결 근거로 승격하지 않는다.
- 월 사용량과 실행 중 예약량은 영구 볼륨의 `STORAGE_DIR/bigquery_patents.sqlite3`에 원자적으로 기록한다. 재시작해도 유지된다. 완료 작업은 실제 청구 바이트로 정산한다. 시간 초과·네트워크 단절 등 결과가 불명확한 작업은 상한 예약을 유지하여 재시도로 예산이 풀리지 않는다. 운영자가 BigQuery 작업 ID로 결과를 확인하기 전에는 이 파일을 초기화하지 않는다.
- 하나의 영구 볼륨을 공유하는 현재 배포 범위의 제한이다. 별도 배포·다른 프로젝트·다른 앱의 사용량은 포함하지 않는다. 결제 계정 전체의 무료 잔여량을 보장하지 않으므로 Google Cloud에서도 프로젝트/사용자별 쿼리 일일 할당량을 설정한다.
- 무료 처리량은 무제한 검색을 뜻하지 않는다. 공개 테이블은 매우 크고 `LIMIT`이나 일반 WHERE 조건만으로 스캔 비용이 줄어들지는 않는다. **기본 상한으로 조회가 가능할지는 인증 후 실제 dry run으로 확인해야 한다.** 초과 시 자동으로 상한을 올리지 않는다.
- 동일 검색 묶음은 24시간 캐시하며 실패는 0건으로 캐시하지 않는다. 실패 이유·job ID·예상/청구 바이트는 분석 추론 이력의 검색 단계에 남는다. 상한·인증 오류는 분석 현황과 보고서에 표시하고 해결책 카드에는 근거 미확보 문구를 추가하지 않는다.
- 기존 저장 보고서를 자동으로 다시 분석하지 않는다. 재조회 시 이전 공급자의 0건 기록과 실패 기록은 재시도 대상이 되며, 이미 확보한 근거는 유지된다.

## 공식 자료

- [Google 공개 특허 스키마](https://github.com/google/patents-public-data/blob/master/tables/dataset_Google%20Patents%20Public%20Datasets.md)
- [BigQuery 비용 추정·상한·사용 할당량](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [BigQuery IAM 역할](https://docs.cloud.google.com/bigquery/docs/access-control)
- [Python BigQuery 클라이언트](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.client.Client)
