# AX V3 구현 및 운영 계약

2026-09-16. 신규 실행의 workflow는 `triz-ax-v3.1`이다. 기존 `pipeline_version=3`과 별개이며 기존 13개 단계 인덱스와 저장된 legacy 실행은 유지한다.

상태: 2026-09-16 사용자의 배포 승인 후 Railway production 백엔드·프런트엔드 배포와 운영 검증을 완료했다. 신규 실행에 AX가 활성화되어 있다. [배포 기록](TRIZ_AX_V3_DEPLOYMENT_20260916.md)에 모델 설정, MySQL 보정 및 검증 범위를 기록했다.

## 구현된 흐름

- 4개 게이트 상태를 UI에 표시한다. G2/S5 경계의 `s4.route`는 모순에 맞춰 최대 3개 경로를 선택한다. 최초 아이디어 6개, 상세 후보 3개로 제한한다.
- 조율기에서 `ASK_HUMAN`을 항상 차단한다. 복구도 사람 질문 없이 진행한다. 부족한 조건·근거는 자동 보완 또는 조건부·보류로 남긴다.
- 효과별 정본 ID, 기구·조건·출처 및 적용성 미확인 상태를 저장한다. 정본 선택·문헌 확보만으로 실제 적용성 PASS를 부여하지 않는다.
- 기구 검토 실패 후보를 최대 2개 대상으로, 각 2회·깊이 2 이내 복구한다. 기준안과 제외 후보를 보존한다. 상호 보완 기능과 외부 시작 자원이 있는 경우에만 공동 설계를 제안하며 순환 의존만으로 성립하지 않는다. 생성안은 다시 독립 품질 검토와 제약 게이트를 거친다.
- 임의 Python을 실행하지 않는 등록 계산 도구를 제공한다. `dlc_steady_state_v1`은 C, W, K/W 단위의 입수 온도·열부하·총 열저항·GPU 상한으로 정상 상태를 계산한다. 펌프·압력·과도 응답·결로 검증과 실제 장비 시험을 대체하지 않는다.
- 필수 제약별 판정·기구 검토·모순 연결·시험 결과가 없으면 최종 추천하지 않는다. 화면과 다운로드 보고서는 동일 선택 snapshot을 사용한다. 요약 보고서에 새로운 LLM 주장을 추가하지 않는다.

## 저장·재개·예산

`pilot/triz/ax/ledger.py`의 `ax_*` 테이블은 MySQL/SQLite 공용의 additive 저장 구조다. 섹션 산출물 버전, 부모 관계, snapshot, epoch, 결정, 검토, 호출 lease/fence, 정수 마이크로달러, domain event와 outbox를 저장한다. 산출물+snapshot+event+기존 상태 projection은 같은 트랜잭션이다. 외부 호출 동안 DB 행 잠금을 유지하지 않는다.

새 실행은 모델 설정·가격, 프롬프트, 효과 정본·출처, 구성·루브릭, 정책·규칙을 pin한다. 스레드 풀에도 실행별 구성을 전파한다. 전체 실행 바이너리·외부 검색 인덱스의 과거 버전을 재현하는 기능은 아니다.

모델 API의 설정 단가 기준 원장 한도는 $0.60이고 검증용 $0.06을 보존한다. 병렬 호출의 예약이 일시적으로 예산을 점유하면 정산까지 기다린다. 사용량이 불명확하면 예약을 해제하지 않는다. `ax_ops.py reconcile`은 공급자 사용량 증거와 운영자·사유를 기록해야 한다. 이 한도는 기존 서버·DB·벡터 저장소의 고정비를 포함하지 않는다. V3에서 단가 미등록 BigQuery/Tavily 특허 검색은 차단한다. 운영 배포 시 모델을 `deepseek-flash`로 명시하고 최신 피크·캐시 미적중 요율로 갱신했다. 기존 두 DLC 시험의 실제 청구액 상한은 소급 확인되지 않았다. 상세는 [비용 기록의 한계](TRIZ_AX_V3_DLC_TEST.md)와 [배포 기록](TRIZ_AX_V3_DEPLOYMENT_20260916.md)을 따른다.

## 검토 API

기존 로그인과 run 소유권을 유지하며, 소유자의 개인 프로젝트 안에서만 원장·학습 자료를 읽는다. 팀 공유/RBAC 관리 화면은 아직 없다.

- `GET /api/runs/{id}/ax`: snapshot, epoch, 결정·검토, 비용.
- `GET .../ax/snapshots/{snapshot_id}`, `GET .../ax/artifacts/{version_id}`: 정확한 버전과 연결.
- `POST .../ax/reviews`: `event_id`, `expected_epoch`, `snapshot_id`, `target_version_id`, 판단 종류·이유. 오래된 검토는 409와 버전 diff.
- 실제 결과는 candidate·obligation ID, 조건, 측정값, 근거를 함께 제출한다. 탐색 승인/선호는 시험 통과를 주장할 수 없다. 수정 의견은 제안으로 기록하고 `applied_to_artifact=false`를 반환한다.
- `POST .../ax/calculations`: 위 snapshot/epoch와 `tool`, 고정 단위의 `inputs`. 실행 중 변경은 409. 계산 PASS를 실제 시험 결과로 자동 전환하지 않는다.

현재 lineage 단위는 typed 섹션과 섹션 내 candidate/obligation 식별자다. 문장별 claim/source span 그래프 및 범용 그래프 편집기는 마스터의 후속 범위로 남는다.

## 실제 RL과 규칙 진화

`learning.py`는 8개 특징·12개 행동 head의 선형 Q 네트워크를 Bellman 손실과 보수적 log-sum-exp 항으로 실제 갱신한다. 기본 LLM 가중치는 변경하지 않는다. 선택은 실행 가능한 행동과 관측된 지원 범위로 제한한다.

동의한 검토를 결정·산출물 lineage에 연결한다. 미관측 보상은 표본에 넣지 않으며 선호와 TEST/FIELD 판단을 구분한다. 수정·철회는 supersedes revision으로 이전 보상을 대체한다. 같은 문제군을 같은 split에 두고 최신 문제군을 holdout으로 사용한다. 문제군 ID가 없으면 정규화한 질문의 hash를 사용하므로 의미가 비슷한 다른 표현까지 자동 판별하지는 못한다. CPU 배치는 전체 문제군을 유지하며 최대 2,000개 결정이다.

32개 확정 결정, 8개 독립 문제군, 2개 holdout 문제군, 두 행동 각각 4개 이상 지원, 8개 기술 관측을 모두 요구한다. 이는 서비스 성능 향상 보장이 아니다. holdout 계산 손실과 지원 범위를 확인한 뒤 shadow로만 올린다. 실제 행동 변경은 최소 20개 shadow 결정·5개 실행과 깨끗한 Governor 기록 및 운영자 승격 명령을 추가로 요구한다. canary는 최대 25% 신규 실행이며 rollback도 다음 실행부터 적용된다. 확률을 모르는 로그에 IPS/OPE 수치를 만들지 않는다.

규칙 lab은 실제 후보에 연결된 효과와 동의한 PASS 관측으로 검증 의무 규칙을 제안한다. 현재 자동 승격 범위는 `ADD_VERIFICATION`뿐이다. 두 독립 문제군과 긍정·부정 적용 범위 검사를 거쳐 다음 실행에 추가 검증을 부과한다. 효과 정본 수정, 요구조건 완화, 시험 PASS 생성, 임의 코드 실행은 하지 않는다. 효과·복구 제안 DSL은 판독 가능하지만 자동 운영 승격 대상은 아니다. 완전한 범용 기능 그래프 규칙 발굴·교차 도메인 성능 입증은 후속 범위다.

## 워커와 운영

`scripts/ax_worker.py`는 API와 별도 CPU 프로세스이며 외부 LLM 호출이 0이다. 기존 backend 컨테이너에서 한 프로세스를 감독하므로 새 Railway 서비스의 고정비를 추가하지 않는다. 별도 컨테이너급 CPU/메모리 격리는 아직 하지 않는다. `TRIZ_AX_WORKER_ENABLED=false`로 중지할 수 있다. outbox lease·receipt로 중복 전달을 처리하고 프로젝트별 학습과 규칙 연구는 온라인 응답을 막지 않는다.

```powershell
.venv/Scripts/python.exe pilot/scripts/ax_worker.py --once
.venv/Scripts/python.exe pilot/scripts/ax_ops.py train --tenant OWNER_ID --project OWNER_ID
.venv/Scripts/python.exe pilot/scripts/ax_ops.py rollback --tenant OWNER_ID --project OWNER_ID --actor OPERATOR --reason "관측 품질 저하"
```

신규 workflow rollback은 `TRIZ_AX_ENABLED=false`다. 기존 V3 run의 snapshot·정책을 중간에 교체하지 않는다. 운영 모델 데이터는 현재 승격 조건 미충족이며 규칙 기반 정책을 유지한다. 합성 시험 데이터를 운영 학습으로 넣지 않는다.

테스트 수치와 실제 DLC 산출물은 [DLC 검증 기록](TRIZ_AX_V3_DLC_TEST.md), 직접검토 상태는 [과학효과 조사 기록](EFFECTS_RESEARCH.md)에 별도로 기록한다.

과학효과의 전체 검색 범위, 상위 후보 축소, 산업 전이의 현재 한계 및 제안은 [과학효과 검색 흐름 점검](TRIZ_AX_V3_EFFECT_SEARCH_REVIEW.md)을 따른다. 검색 순위와 탐색 폭을 조절하는 RL은 현재 작업 선택 RL의 후속 범위다.
