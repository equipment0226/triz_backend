# AX / QLearn 검증 기록

2026-09-28, Windows / Python 3.11.3 / pytest 9.1.1. 실행기는 작업공간 `.venv/Scripts/python.exe`를 사용했다. 테스트 conftest는 임시 SQLite·임시 storage·local orchestrator·가짜 키를 설정한다. 실제 LLM은 stub이며 예상 밖 네트워크 연결은 실패시킨다. Windows asyncio의 내부 loopback socketpair만 허용한다. MySQL과 외부 유료 API는 호출하지 않았다.

## 기준선

수정 전 핵심 12개 모듈(AX learning/phase1/coherence/recovery/portfolio/full report, gate resume, execution lifecycle, project budget, provider interruptions, pipeline quality, summary labels)을 실행했다.

```powershell
.venv/Scripts/python.exe -m pytest pilot/tests/test_ax_learning.py pilot/tests/test_ax_phase1.py pilot/tests/test_ax_coherence.py pilot/tests/test_ax_coherence_recovery.py pilot/tests/test_ax_portfolio_completion.py pilot/tests/test_gate_resume.py pilot/tests/test_execution_lifecycle.py pilot/tests/test_project_budget.py pilot/tests/test_provider_interruptions.py pilot/tests/test_pipeline_quality.py pilot/tests/test_ax_full_report.py pilot/tests/test_summary_labels.py -vv -o faulthandler_timeout=40 --tb=short
```

결과: **165 passed, 253.35초**. 로그: `.tmp/ax-baseline-focused.txt`.

처음 시도한 전체 기준선 실행은 진행 지연으로 중단했다. 전체 기준선이 통과했다고 주장하지 않는다. 요청 문서의 Git HEAD는 루트가 Git checkout이 아니어서 검증할 수 없었다.

## 구현 후 회귀

| 실행 | 결과 | 로그 |
|---|---|---|
| 전체 `pytest pilot/tests -q --tb=short` | **1,101 passed**, 591.30초 | `.tmp/ax-full-after-final.txt` |
| 이후 AX·재개·예산 영향 범위 | **79 passed**, 111.91초 | `.tmp/ax-final-focused.txt` |
| 이후 신규 계약·보고서·보류 영향 범위 | **74 passed**, 38.47초 | `.tmp/ax-final-acceptance.txt` |
| 최종 코드의 신규 계약 29개 + AX gateway/계약·프로젝트 예산 | **59 passed**, 70.50초 | `.tmp/ax-last-check.txt` |
| offline smoke | **7 passed**, 13.19초 | `.tmp/ax-smoke-7.txt` |
| frontend `npm.cmd run build` | 성공, Vite 7.3.6 | 빌드 산출물 `frontend/dist/` |
| `python -m compileall -q pilot/triz pilot/scripts/ax_offline_smoke.py` | 성공 | 컴파일 오류 없음 |

서로 겹치는 테스트이므로 위 숫자를 합산하지 않는다. 전체 회귀 이후 추가된 인수 테스트와 최종 모델 역할/정산/stale 산출물 점검은 마지막 59개 영향 범위 실행에 포함됐다. 최종 이 실행에는 실패·skip이 없다.

전체 회귀의 경고 1개는 기존 Qdrant local mode에서 `search_params`가 검색 방식에 영향을 주지 않는다는 알림이다. frontend에는 기존 큰 MaterialLibrary chunk 경고가 있었다. 둘 다 검증 실패는 아니다.

구현 중 발견·수정한 실패:

- 네트워크 guard가 Windows asyncio의 내부 socketpair를 막음 → loopback 내부 연결만 허용.
- 과거 pin을 검증하는 fixture가 신규 모드 계약을 사용함 → 기존 회귀 fixture의 legacy 계약을 명시하고 신규 v2는 별도 fixture로 검증.
- 조건 재검토 child가 pending 사용자 응답을 다시 소비하며 재귀함 → child에서 응답 제어 상태를 제거하고 사용자 응답은 부모에서 보존.
- 예산 부족 때 비용 없는 DEFER까지 검토 예약으로 차단됨 → 정상 optional 종료를 예약 비용 검사에서 제외.
- 한 번의 추가 검증 명령은 존재하지 않는 `test_report_redesign.py`를 지정해 수집되지 않음 → 실제 `test_report_layout.py` 등으로 수정한 명령이 74개 통과.

위 중간 실패/중단 로그를 최종 통과로 세지 않았다.

## 신규 인수 검증

`pilot/tests/test_ax_refactor.py`는 다음을 실제 코드 경로와 provider stub으로 확인한다.

- LITE 4개/FULL 7개/DEEP 8개 트랙 실행과 완료 트랙 재개 재사용.
- 초기/직접 executor/Q 제안의 LITE/FULL ARIZ 차단, DEEP optional/Q 호출 0.
- genuine NOT_APPLICABLE과 입력 부족·미완료의 구분.
- 서로 다른 추가 트랙/복구 대상 중 실제 선택, 선택 대상 handler와 독립 감사만 실행, 기준 후보 보존.
- 같은 action type의 서로 다른 track과 상태에 따라 바뀌는 Q 선택, 실제 weight 변경·mask·지원 부족 fallback.
- 80개 원안/10개 대표 선정에서 leaf 재고·보류 사유·TRADEOFF 보존.
- H/ARIZ 동일 effect application 계약, 타 소유자/잘못된 ID 차단, 중복 event 방지, drop 후 immutable 참조.
- 같은 조건의 이력 재정렬과 다른 제약/소유자 fallback, UNKNOWN·채택·경제성의 라벨 분리.
- 조건 확인 후 변경 후보만 S7 재검토하고 CONDITIONAL 유지. 재검토 중 transport 중단 후 답변·관측 보존.
- consent cutoff·철회와 미래 모델 적격성 차단.
- semantic replan archive와 budget 보존, transport epoch 변경 후 완료 호출 및 UNKNOWN 예약 재사용.
- gateway 단계의 optional cap과 비용 없는 종료, stale snapshot 차단.
- review → outbox → worker → dataset → routing/effect CPU train → 서로 다른 shadow pointer → 다음 run 고정 bundle의 end-to-end 연결.
- DEEP track → 실제 merge → 검토 → frozen report와 API 해결안 목록의 불변성.

## 재현

```powershell
.venv/Scripts/python.exe pilot/scripts/ax_offline_smoke.py
.venv/Scripts/python.exe -m pytest pilot/tests/test_ax_refactor.py -q
.venv/Scripts/python.exe -m pytest pilot/tests -q --tb=short
```

frontend는 `frontend` 폴더에서 `npm.cmd run build`를 실행한다.

합성 데이터는 임시 SQLite에만 기록했고 운영 active pointer로 승격하지 않았다. smoke의 학습 선택 변화는 연결/구조 검증이다. 현업 quality·비용·물리적 성능 개선, 실제 공급자 오류율/latency, MySQL 동시성, 배포된 n8n/MCP, 실제 브라우저 조작은 미검증이다. 실제 relevance 라벨이 없으므로 ranking metric·반사실적 정책 가치도 보고하지 않는다.
