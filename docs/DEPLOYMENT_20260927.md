# 2026-09-27 누적 변경 배포

> 이 문서는 당일 첫 배포 시점의 기록이다. 이후 ARIZ·워크플로 및 보고서 개선 배포는 [WORKFLOW_RELEASE_20260927.md](WORKFLOW_RELEASE_20260927.md)에 기록했다. 그 배포의 공개 브라우저 검증에서는 `https://trizstudio.online` 접속이 정상화됐다. 아래 도메인 정지 상태와 해결책 수 조건은 당시 관측·정책이다.

Railway `elegant-freedom / production`에 backend와 frontend 누적 변경을 배포했다. 과학효과 1,500개, ARIZ Part 6 보고서 추가 의견, 기존 특허 작성·복구 기능과 화면 변경을 모두 포함한다.

| 대상 | Git 커밋 | Railway 배포 ID |
|---|---|---|
| Backend | `85edd3b60f59f869fcbde51883b18c21d89ed8fb` | `d97c512c-6c56-4ff1-8421-cee9f7179250` |
| Frontend | `5d210e15ef3883a4ba9264a16eb1f488f2497483` | `bd17247c-ecb6-47ef-a059-795d4c6afb71` |

두 저장소의 `deploy/all-updates-20260927` 브랜치를 푸시했다. 기존 release clone의 미커밋 작업은 유지하고 별도 worktree에서 정본 소스를 통합했다. main과 PR은 변경하지 않았다.

## 운영 확인

- 두 새 배포와 기존 의존 서비스의 상태는 SUCCESS다.
- 기존 7개 볼륨 ID·서비스 연결·마운트 경로가 같고 backend/frontend 운영 설정 해시가 배포 전후 일치한다.
- backend 실행 파일·프롬프트·지식·템플릿 등 216개 파일의 해시가 준비한 소스와 일치한다.
- backend와 n8n 내부 healthcheck HTTP 200. Railway 기본 주소에서 홈페이지·healthcheck·로그인 설정·공개 이력 58건 조회가 정상이며 미로그인 분석 API는 401이다.
- 실제 브라우저에서 과학효과 1,500개 표시, 대표 항목 3개 상세, 이전 ID 리디렉션을 확인했다. 브라우저 오류 0건.
- frontend 정적 지식도 backend와 같은 1,500개로 동기화했다. ARIZ Part 6 정의는 6.1~6.3이며, backend에서 추가 코멘트 렌더링을 확인했다.
- 실제 유료 분석이나 외부 LLM 조사 호출은 생성하지 않았다.

## 검증

backend 전체 테스트 실행은 756개 통과, 테스트 worker의 5초 제한으로 인한 타이밍 실패 1개였다. 제품 코드 대신 해당 테스트의 잠금 유지 방식을 명시적 해제로 수정했고, 해당 lifecycle 파일의 33개 테스트가 통과했다. frontend 빌드와 서버 테스트 1개도 통과했다. 수정 후 전체 757개를 다시 실행한 것은 아니다.

## 조사와 검색용 적재 범위

2026-09-27 09:16 KST 관측:

| 구분 | 수량·상태 |
|---|---|
| 과학효과 정본 | 1,500개 / 19개 기능군, 전체 출처 연결 |
| 검색용 특허 문서 | 11,796,076건 |
| 벡터 색인 | 11,796,076건, 대기 0건, Qdrant green / optimizer ok |
| 과학효과 조사용 특허 조회 | 13,160건 |
| 직접 읽은 저장 초록 | 10,851건 |
| 초록 없어 미분석 | 2,309건 |
| 조사 체크포인트 | 81페이지 완료, 다음 82페이지, `AT-512674-A1` 이후 |

검색용 수집은 `complete=false`로 계속 진행 중이다. 검색용 적재량은 내용을 직접 읽은 수가 아니며, 직접 검토 수 역시 청구항·전문 전체를 읽은 수가 아니다. 이번 작업에서 추가 문헌 조사나 특허 초록 검토를 수행하지 않았다.

## 사용자 도메인

09:17 KST 기준 `trizstudio.online`은 Hostinger 이메일 미인증 정지 화면과 `verification-hold.dns-suspended.com` 네임서버가 남아 있다. 사용자는 인증 완료를 알렸으며 Railway 서비스 자체는 정상이다.

현재 접속 가능한 주소: https://trizfront-production.up.railway.app

[Hostinger 공식 안내](https://www.hostinger.com/support/1583442-how-to-fix-a-domain-suspended-due-to-pending-icann-verification-at-hostinger/)에 따르면 인증 후 원래 네임서버로 복귀하고 DNS 전파에 최대 24시간이 걸릴 수 있다. registrar나 DNS 설정은 임의로 변경하지 않았다.

로컬 증빙은 `.deployment/all-updates-release-20260927.json`, `all-updates-20260927-backend-verified.json`, `all-updates-20260927-browser.json`, `all-updates-20260927-public.json`, `patent-inventory-live-20260927-final.json`에 저장했다.
