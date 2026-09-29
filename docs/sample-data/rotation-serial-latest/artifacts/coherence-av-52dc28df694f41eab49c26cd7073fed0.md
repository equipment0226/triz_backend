# coherence · 저장 산출물

[산출물·스냅샷 목록](../ARTIFACTS.md)

| 항목 | 저장값 |
|---|---|
| version_id | av-52dc28df694f41eab49c26cd7073fed0 |
| epoch | 50 |
| content_hash | 9c730f7fdbe3c33874c979f85af3419ac0055a7345b21ba3b061bb0bd82d462f |
| created_at | 2026-09-29T22:10:31.743768+00:00 |
| available_at | 2026-09-29T22:10:31.743788+00:00 |
| supersedes | None |

## Payload

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `candidates` | [] | 표에 전체 값 표시 |
| `contract` | "coherence-v1" | 표에 전체 값 표시 |
| `coverage_gaps` | 배열 6개 | [펼쳐 보기](#field-0aaa1f7d27669206) |
| `display_limit` | null | 표에 전체 값 표시 |
| `note` | "후보별 대응 범위의 합집합이며 결합 설계의 호환성이나 실제 실증을 의미하지 않는다." | 표에 전체 값 표시 |
| `obligations` | 배열 6개 | [펼쳐 보기](#field-c85038753d19e1a6) |
| `presentation_target` | 0 | 표에 전체 값 표시 |
| `retained_count` | 0 | 표에 전체 값 표시 |
| `scope_status` | "PARTIAL" | 표에 전체 값 표시 |
| `shortfall` | 0 | 표에 전체 값 표시 |

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

<a id="field-c85038753d19e1a6"></a>

<details>
<summary>obligations · 전체 값</summary>

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
    "protect": "로테이션 구간 시간이 늘어 takt time이 50초 이하 목표를 초과한다",
    "requirement_hash": "78dee04ccc0592811507ece3ac4ddeff52687045d0c0562e5ec2e91f11d7dbd7"
  }
]
```

</details>

## 계보

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `parents` | [<br>  "av-011963b3da4b406aa99f3c20e1c2b1ca",<br>  "av-1cb9c589494c44b0a4818055a455b84c"<br>] | 표에 전체 값 표시 |
| `provenance` | 객체 · action_instance_ids, approval_status, bundle_id, decision_id, decision_ids, evidence_status, reason … | [펼쳐 보기](#field-af1e261754808773) |

<a id="field-af1e261754808773"></a>

<details>
<summary>provenance · 전체 값</summary>

```json
{
  "action_instance_ids": [],
  "approval_status": "UNREVIEWED",
  "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
  "decision_id": "dec-e4d464594c69ae2a90b4c3534394bbc5c01b37f4a578251bfd9232baf64f",
  "decision_ids": [],
  "evidence_status": "ASSERTED",
  "reason": "s4_define",
  "semantic_episode_id": null,
  "workflow": "triz-ax-v3.1"
}
```

</details>
