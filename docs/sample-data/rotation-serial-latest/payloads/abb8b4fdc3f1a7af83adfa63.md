# 저장 데이터 · abb8b4fdc3f1

정규 JSON SHA-256: `abb8b4fdc3f1a7af83adfa635e0314121c30ffba3488cc7d86a0ad5bcf89512d`

```json
[
  {
    "metric": "부하율 최대값 및 takt",
    "baseline": "부하율 60~70% 추정(정확 수치 미확인), takt 53초(soft)",
    "target": "부하율 허용 범위 이내 유지, takt 50초 이하",
    "experiment": "폐루프 제어 적용 시 부하율 최대값과 takt 변화를 동시 측정하고, 부하율 임계값을 단계적으로 변경하며 시험한다.",
    "success_criterion": "부하율이 허용 범위 이내로 유지되고 takt이 50초 이하로 단축된다.",
    "failure_criterion": "부하율이 허용 범위를 초과하거나 takt이 50초 이하로 단축되지 않으면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-da1055a5",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-da1055a5",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "강성·안정성 지표(진동 주파수·진폭, 베어링 온도)",
    "baseline": "강성·안정성 정량 기준값 미확인, 온도 측정값 미확인",
    "target": "강성·안정성 허용 범위 내 유지",
    "experiment": "폐루프 제어 적용 시 진동·온도를 측정하여 강성·안정성 위반 여부를 확인한다.",
    "success_criterion": "진동·온도가 허용 범위 이내로 유지된다.",
    "failure_criterion": "진동·온도가 허용 범위를 초과하면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-359be1cd",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-359be1cd",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "가속도 상향 폭 대비 부하율·진동·온도 변화율",
    "baseline": "가속도 상향 폭 0(기준선)",
    "target": "HARD 제약 도달 지점 판정",
    "experiment": "가속도를 단계적으로 상향(예: 10%씩)하며 부하율·진동·온도를 동시 측정하여 한계 도달 지점을 판정한다.",
    "success_criterion": "부하율·진동·온도 중 먼저 한계에 도달하는 지표와 그 시점의 가속도 상향 폭이 판정된다.",
    "failure_criterion": "한계 도달 지점이 판정되지 않거나 측정 노이즈로 구분 불가하면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-359be1cd",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-359be1cd",
        "side": "PROTECT"
      }
    ]
  }
]
```
