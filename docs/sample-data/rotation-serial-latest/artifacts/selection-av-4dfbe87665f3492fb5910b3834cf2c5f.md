# selection · 저장 산출물

[산출물·스냅샷 목록](../ARTIFACTS.md)

| 항목 | 저장값 |
|---|---|
| version_id | av-4dfbe87665f3492fb5910b3834cf2c5f |
| epoch | 51 |
| content_hash | 4b39f8e3e7b4a6d05eb838032f1d9a0bb563223acfbb541c53a1a87d10483425 |
| created_at | 2026-09-29T22:42:14.494656+00:00 |
| available_at | 2026-09-29T22:42:14.494674+00:00 |
| supersedes | None |

## Payload

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `candidates` | 배열 8개 | [전체 값](../payloads/a82b37277e1b69008f7c85b6.md) |
| `conditional` | [<br>  "CPT-S6-32d46b742a89c1c2",<br>  "CPT-S6-099405e4edc0a658",<br>  "CPT-S6-d2c3056109ec002a",<br>  "CPT-S6-ac128a6d03303a81",<br>  "CPT-S6-33d3b8f2d4fa57e5",<br>  "CPT-S6-de9b1cabaf6dacce",<br>  "CPT-S6-b6dfcbd4dd9d8841",<br>  "CPT-S6-783786b342651a96"<br>] | 표에 전체 값 표시 |
| `coverage_gaps` | 배열 6개 | [펼쳐 보기](#field-0aaa1f7d27669206) |
| `display_limit` | null | 표에 전체 값 표시 |
| `presentation_target` | 0 | 표에 전체 값 표시 |
| `recommended` | [] | 표에 전체 값 표시 |
| `retained_count` | 8 | 표에 전체 값 표시 |
| `scope` | "개념 검토와 실제 시험 결과를 구분한 판정" | 표에 전체 값 표시 |
| `scope_status` | "PARTIAL" | 표에 전체 값 표시 |
| `shortfall` | 0 | 표에 전체 값 표시 |
| `status` | "PARTIAL" | 표에 전체 값 표시 |

<a id="field-0aaa1f7d27669206"></a>

<details>
<summary>coverage_gaps · 전체 값</summary>

```json
[
  {
    "contradiction_ids": [
      "TC-ba15f1e6",
      "PC-8efb2898",
      "PC-5a3521d4"
    ],
    "description": "TC1: 가속도 상향으로 takt 단축 → 부하율·강성 악화",
    "id": "TC-ba15f1e6",
    "improve": "가속·감속 구간 시간이 줄어 takt time이 단축된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-ba15f1e6",
    "protect": "모터·인덱서 부하율이 상승하고 가진력 증가로 구동계 강성·안정성이 저하될 수 있다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  },
  {
    "contradiction_ids": [
      "TC-c8cf7951"
    ],
    "description": "TC2: 부하율·강성 보호를 위해 가속도를 하향 → takt 초과",
    "id": "TC-c8cf7951",
    "improve": "모터·인덱서 부하율과 구동계 강성·하드웨어 안정성이 유지된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-c8cf7951",
    "protect": "가속·감속 구간 시간이 늘어 takt time이 50초 이하 목표를 초과한다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  },
  {
    "contradiction_ids": [
      "TC-b5b764b0",
      "PC-82950bf3"
    ],
    "description": "TC3: 정렬·클램프 중첩으로 takt 단축 → Slip 파손 위험",
    "id": "TC-b5b764b0",
    "improve": "직렬 누적 시간이 줄어 takt time이 단축된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-b5b764b0",
    "protect": "감속 중 글라스 미끄럼(Slip)으로 파손·정렬 오차가 발생할 수 있다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  },
  {
    "contradiction_ids": [
      "TC-097b79ff"
    ],
    "description": "TC4: 정렬·클램프 직렬 유지로 Slip 방지 → takt 초과",
    "id": "TC-097b79ff",
    "improve": "글라스 미끄럼·파손이 방지되고 정렬 정밀도가 확보된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-097b79ff",
    "protect": "직렬 소요 시간이 누적되어 takt time이 50초 이하 목표를 초과한다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  },
  {
    "contradiction_ids": [
      "TC-4f7ba034",
      "PC-fa63e298"
    ],
    "description": "TC5: 고속화로 takt 단축 → 베어링 발열·열변형 악화",
    "id": "TC-4f7ba034",
    "improve": "로테이션 구간 시간이 줄어 takt time이 단축된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-4f7ba034",
    "protect": "마찰 발열이 증가하여 열변형으로 정착 시간·정렬 정밀도가 저하될 수 있다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  },
  {
    "contradiction_ids": [
      "TC-9a13d136"
    ],
    "description": "TC6: 발열 억제를 위해 속도 하향 → takt 초과",
    "id": "TC-9a13d136",
    "improve": "베어링·접촉면 온도가 억제되어 정착 시간·정렬 정밀도가 유지된다",
    "kind": "COVERAGE_GAP",
    "obligation_id": "TC-9a13d136",
    "protect": "로테이션 구간 시간이 늘어 takt time이 50초 이하 목표를 초과한다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  }
]
```

</details>

## 계보

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `parents` | [<br>  "av-2993e53e0aad4bd0911034d2d78d4d5a",<br>  "av-04ff51006a3e4b639cb85bfdc57346e6",<br>  "av-cd107f5e5c8941d7b4e6f9e15cf4e3d2",<br>  "av-03c8ece38f8543f989d9c637ee499fbe"<br>] | 표에 전체 값 표시 |
| `provenance` | 객체 · action_instance_ids, approval_status, bundle_id, decision_id, decision_ids, evidence_status, reason … | [펼쳐 보기](#field-12ccf365b95a5650) |

<a id="field-12ccf365b95a5650"></a>

<details>
<summary>provenance · 전체 값</summary>

```json
{
  "action_instance_ids": [],
  "approval_status": "UNREVIEWED",
  "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
  "decision_id": "dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6",
  "decision_ids": [],
  "evidence_status": "ASSERTED",
  "reason": "s8_evaluate",
  "semantic_episode_id": null,
  "workflow": "triz-ax-v3.1"
}
```

</details>
