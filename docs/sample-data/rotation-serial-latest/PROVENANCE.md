# 수집 기준과 한계

[사례 개요](README.md)

추출 시각: `2026-09-30T05:19:12.818518+00:00`. 상태 갱신 시각: `2026-09-30T05:13:07.954796+00:00`. 완료된 실행을 읽기 전용 SELECT로 수집했습니다. 추출 중 상태 갱신 시각과 AX revision이 변하지 않았는지 확인했습니다.

## 실행 코드와 사후 비용정정 코드

| 구분 | 코드 / 근거 |
|---|---|
| 실제 분석 실행 당시 서버 | [전체 코드](https://github.com/equipment0226/triz_backend/tree/5ce8ec233b3d58d2005530a4e9b3113f5fc235f2/) · `5ce8ec233b3d58d2005530a4e9b3113f5fc235f2` |
| 완료 후 비용정정 계산 | [가격·캐시 계산 코드](https://github.com/equipment0226/triz_backend/blob/3fd16f06180d533f682956a010331063cd636cf9/pilot/triz/ax/cost_restatements.py) · `3fd16f06180d533f682956a010331063cd636cf9` |
| 저장된 비용정정 이벤트 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| 정정 적용 시각 UTC | 2026-09-30T05:13:07.954796+00:00 |

Stage 코드 링크는 실행 당시 서버 버전을 가리킵니다. task의 고정 모델 설정과 원본 usage는 호출 원장에 그대로 남겨 두었습니다. 이후 코드로 바뀐 것은 별도 정정 이벤트에 연결한 유효 비용이며, 과거 분석·피드백·검증 결과를 새 코드의 결과로 바꾸지 않았습니다.

## 기록 범위

이번 Stage 시작 이벤트에서 확인한 step_id와 epoch 범위를 사용했습니다. 이전 버전은 현재 task의 input_snapshot 또는 Stage 체크포인트가 실제로 참조한 자료만 포함했습니다. 계정·인증 정보는 전송 전에 제외했고, 중복된 프롬프트·provider 응답·보고서 전문은 해시로 식별했습니다.

Stage 귀속은 run_events의 stage_start 구간으로 정했습니다. Step의 DB stage는 별도로 보존합니다. task와 Step 사이에는 직접 외래키가 없으므로 병렬 task를 특정 Step에 시간만으로 연결하지 않습니다.

## 비용 기준

이번 task의 원본 actual 합계는 `0.971468 USD`, 정정 반영 합계는 `0.390118 USD`입니다. 이번 Step의 저장 비용 합계 `0.971418900 USD`는 실행 당시 원본이며 정정액으로 덮어쓰지 않았습니다. 프로젝트 누적액 `3.11851 USD`에는 이전 회차가 포함됩니다. 예약액은 실제 사용량이 아닙니다. 미확인 usage를 새로 만들어 비용을 계산하지 않았습니다.

Flash 비피크 기준은 100만 토큰당 캐시 미적중 입력 $0.15, 캐시 적중 입력 $0.003, 출력 $0.60입니다. 실제 저장된 토큰 카운터에 이 기준을 적용한 추정 비용이며, 피크 시간대 공급자 청구액과 일치함을 뜻하지 않습니다. [공식 가격표](https://api-docs.deepseek.com/quick_start/pricing/)

비용 = (미적중 입력 토큰 × 0.15 + 적중 입력 토큰 × 0.003 + 출력 토큰 × 0.60) / 1,000,000. 캐시 카운터가 없거나 불일치하면 할인량을 추정하지 않고 전체 입력에 미적중 단가를 적용합니다. 추론 토큰은 출력 토큰에 이미 포함되므로 중복 가산하지 않습니다. 비용정정과 원본 사용량은 연결된 원장으로 구분해서 읽습니다.

## 전체 context·범위

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `context` | 객체 · updated_at, raw_query, domain, confirm, cost, workflow_version … | [전체 값](payloads/ca963357d524d5ba4be345b8.md) |
| `head` | {"epoch": 58, "revision": 401, "snapshot_id": "snap-440b573371d94951b0a44e28c3db3abf", "budget": 10000000} | 전체 값 |
| `scope` | 객체 · run_id, start_event_id, last_event_id, start, epoch_range, source_code_commit … | [전체 값](payloads/55222aefaedb5567c7928b2e.md) |
| `inventory` | 객체 · steps, events, snapshots, artifacts, decisions, calls … | [전체 값](payloads/36e65b92daf9c3d6df0a32dd.md) |
