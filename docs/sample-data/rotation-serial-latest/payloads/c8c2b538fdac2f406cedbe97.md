# 저장 데이터 · c8c2b538fdac

정규 JSON SHA-256: `c8c2b538fdac2f406cedbe9715ae043250b010f00b5153ccb5eb1f4be71a6886`

```json
[
  {
    "metric": "정지 후 클램프 체결 시간 및 전체 takt",
    "baseline": "정렬·클램프 4초 내외(soft, CON-b743bd0a), takt 53초(soft, CON-58b5c6a1)",
    "target": "정지 후 체결 시간 단축 및 takt 50초 이하(CON-1f3bada2)",
    "experiment": "클램프 헤드 사전 이동 위치별로 글라스 접촉 여부와 정지 후 체결 시간을 측정하고, 단계별 타임스탬프(투입/가속/정속/감속/정지/정렬·클램프/배출/복귀/대기)를 분해한다.",
    "success_criterion": "정지 후 체결 시간이 4초 내외 대비 유의하게 감소하고, 전체 takt가 50초 이하로 측정된다.",
    "failure_criterion": "감속 구간에서 클램프 헤드가 글라스에 접촉하거나, 정지 후 체결 시간이 4초보다 줄지 않거나, 정렬 정밀도가 허용 범위를 벗어나면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-0b4ac5ca",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-0b4ac5ca",
        "side": "PROTECT"
      },
      {
        "contradiction_id": "TC-f89321af",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-f89321af",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "정렬 정밀도 및 Slip 파손 발생 여부",
    "baseline": "정렬 정밀도 허용 범위 미확인",
    "target": "정렬 정밀도 허용 범위 내 유지, Slip 파손 0건",
    "experiment": "사전 스트로크 위치를 단계적으로 변경하며 정렬 정밀도와 Slip 발생을 측정한다.",
    "success_criterion": "전 스트로크 위치에서 Slip 파손 0건, 정렬 정밀도 허용 범위 내 유지.",
    "failure_criterion": "Slip 파손이 1건이라도 발생하거나 정렬 정밀도가 허용 범위를 벗어나면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-0b4ac5ca",
        "side": "PROTECT"
      },
      {
        "contradiction_id": "TC-f89321af",
        "side": "IMPROVE"
      }
    ]
  },
  {
    "metric": "시퀀스 고정 유지 여부 및 공정 리스크(Slip·오배출) 발생 건수",
    "baseline": "현행 시퀀스(투입>로테이션>배출>원위치 복귀) 유지, 공정 리스크 0건",
    "target": "시퀀스 재배치 없이 유닛 내부 동작 시간 분리만 적용, 공정 리스크 0건 유지",
    "experiment": "변경 전후의 장비 시퀀스 로그를 비교하여 시퀀스(투입>로테이션>배출>원위치 복귀)가 그대로 유지되는지 확인하고, 동시에 Slip·오배출 발생 건수를 카운트한다.",
    "success_criterion": "시퀀스 순서가 변경되지 않고, Slip·오배출 0건이 유지된다.",
    "failure_criterion": "시퀀스 순서가 변경되거나, Slip·오배출이 1건이라도 발생하면 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-703fae7f",
        "side": "IMPROVE"
      },
      {
        "contradiction_id": "TC-703fae7f",
        "side": "PROTECT"
      }
    ]
  },
  {
    "metric": "정지 후 체결 시간이 4초보다 짧은지 여부(핵심 전제 반증시험)",
    "baseline": "정렬·클램프 4초 내외(soft, CON-b743bd0a)",
    "target": "정지 후 체결 동작만의 시간이 4초보다 짧게 측정됨",
    "experiment": "정렬·클램프 4초를 준비 동작 시간과 체결 동작 시간으로 분해 계측한다. 준비 동작을 감속 구간으로 이동시킨 뒤 정지 후 남는 체결 시간을 측정하여 4초 대비 단축 폭을 산정한다.",
    "success_criterion": "정지 후 체결 시간이 4초보다 짧게 측정되어 단축 효과가 성립한다.",
    "failure_criterion": "정지 후 체결 시간이 4초 이상이면 이 후보의 단축 효과가 소멸하므로 실패로 판정한다.",
    "obligation_refs": [
      {
        "contradiction_id": "TC-703fae7f",
        "side": "PROTECT"
      },
      {
        "contradiction_id": "TC-f89321af",
        "side": "IMPROVE"
      }
    ]
  }
]
```
