# report_context · 저장 산출물

[산출물·스냅샷 목록](../ARTIFACTS.md)

| 항목 | 저장값 |
|---|---|
| version_id | av-fea07164dc5041d4a7c0a765829ae407 |
| epoch | 51 |
| content_hash | 2d1fd1a5797ec90423c2b4d5a2d7c86633acd510dd0377cd589342c442e0091c |
| created_at | 2026-09-29T22:42:56.093313+00:00 |
| available_at | 2026-09-29T22:42:56.093346+00:00 |
| supersedes | None |

## Payload

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `control` | {<br>  "current_stage": "S8_EVALUATE",<br>  "enabled_tracks": [<br>    "D_ARIZ",<br>    "A_MATRIX",<br>    "B_SEPARATION",<br>    "C_STANDARDS",<br>    "E_TRIMMING",<br>    "F_TRENDS",<br>    "G_FOS",<br>    "H_EFFECTS"<br>  ],<br>  "lang": "ko",<br>  "mode": "DEEP",<br>  "stage_index": 11<br>} | 표에 전체 값 표시 |
| `cost` | 객체 · budget_usd, by_stage, by_tier, over_budget, request_count, tokens_in, tokens_out … | [펼쳐 보기](#field-59452a02e5325756) |
| `created_at` | "2026-09-27T00:35:17.072889" | 표에 전체 값 표시 |
| `learning_summary` | {} | 표에 전체 값 표시 |
| `mode_coverage` | {} | 표에 전체 값 표시 |
| `narrative` | {} | 표에 전체 값 표시 |
| `scratch` | 객체 · ax_candidate_review, ax_coherence, ax_coordination, ax_idea_inventory, ax_recovery, ax_solve_start_seq, ax_track_execution … | [전체 값](../payloads/2105bd46f6e695ed7ff3dd5b.md) |
| `stored_step_projection` | 객체 · total_count, current_step_ids, body_omitted, reason | [펼쳐 보기](#field-7038aa4812b700f0) |

<a id="field-59452a02e5325756"></a>

<details>
<summary>cost · 전체 값</summary>

```json
{
  "budget_usd": 10.0,
  "by_stage": {
    "S0_BOOTSTRAP": 0.0018768,
    "S0_RESEARCH": 0.0181311,
    "S1_INTAKE": 0.0392679,
    "S2_CONFIRM": 0.017247,
    "S3_ANALYZE": 0.18118019999999996,
    "S4_DEFINE": 0.1280895,
    "S5_SOLVE": 2.1909308999999997,
    "S6_CONCEPT": 1.9178964000000003,
    "S7_CONSTRAINT": 0.3125954999999999,
    "S8_EVALUATE": 1.7938806,
    "S8_REFERENCES": 0.2506269
  },
  "by_tier": {
    "T1": 0.06275939999999999,
    "T2": 4.626543599999995,
    "T3": 2.162419800000001
  },
  "over_budget": false,
  "request_count": 730,
  "tokens_in": 13633192,
  "tokens_out": 2301471,
  "total_usd": 7.607363
}
```

</details>

<a id="field-7038aa4812b700f0"></a>

<details>
<summary>stored_step_projection · 전체 값</summary>

```json
{
  "total_count": 728,
  "current_step_ids": [
    "STP-2706d40f",
    "STP-80d197c1",
    "STP-2faef8a0",
    "STP-e0dbc382",
    "STP-59592074",
    "STP-87544e0b",
    "STP-e97e8b15",
    "STP-174c4be3",
    "STP-546553d2",
    "STP-c3b447c6",
    "STP-55291250",
    "STP-0c22f250",
    "STP-8edf7496",
    "STP-04084dd2",
    "STP-de5d769d",
    "STP-ecc9066d",
    "STP-5c0f3ac6",
    "STP-afe46119",
    "STP-b4a05607",
    "STP-aa6e2b89",
    "STP-f422fe90",
    "STP-6f538056",
    "STP-dc6a5452",
    "STP-f521d3b4",
    "STP-f149d0bd",
    "STP-b5dd6c1b",
    "STP-ff0af390",
    "STP-621540f9",
    "STP-09c6dec4",
    "STP-e6882719",
    "STP-234152f4",
    "STP-52c17d24",
    "STP-1333457e",
    "STP-3795488e",
    "STP-46504cca",
    "STP-9b08c9cd",
    "STP-5a211e0b",
    "STP-cd7aca37",
    "STP-9442b996",
    "STP-d2fcfb3d",
    "STP-dc783d31",
    "STP-134d3aa2",
    "STP-878ae922",
    "STP-7a178eea",
    "STP-db9ad5bd",
    "STP-83e658d4",
    "STP-e44b3edf",
    "STP-ebe5008d",
    "STP-c707d3fe",
    "STP-1a391d27",
    "STP-362ca555",
    "STP-08742341",
    "STP-7ff7e56e",
    "STP-a363be35",
    "STP-b0494faa",
    "STP-d056afa6",
    "STP-e1e32e0c",
    "STP-e1e29499",
    "STP-46d53f89",
    "STP-ddce579f",
    "STP-5e1a5e63",
    "STP-3e6bed03",
    "STP-030a8fb8",
    "STP-41b2ea79",
    "STP-accde3d1",
    "STP-583c4e9c",
    "STP-e0e257ce",
    "STP-94f8aba6",
    "STP-9762d548",
    "STP-56e22e2f",
    "STP-8902abc2",
    "STP-cea0e0f8",
    "STP-85ba7c8b",
    "STP-e0d306a2",
    "STP-2ff14bf1",
    "STP-3614dc2d",
    "STP-377bf78e",
    "STP-4b38652a",
    "STP-4b75fe30",
    "STP-d8ee8b50",
    "STP-7ed398b8",
    "STP-667b56ea",
    "STP-2618d71d",
    "STP-d9d7a870",
    "STP-6d983e86",
    "STP-bc1b417c",
    "STP-b3cf260e",
    "STP-96e56bc1",
    "STP-7ed87a9c",
    "STP-df1c8062",
    "STP-0d1d3ef5"
  ],
  "body_omitted": true,
  "reason": "과거 회차와 프롬프트 중복을 담은 전체 step projection 제외"
}
```

</details>

## 계보

| 필드 | 실제 저장값 / 규모 | 전체 값 |
|---|---|---|
| `parents` | [<br>  "av-4dfbe87665f3492fb5910b3834cf2c5f"<br>] | 표에 전체 값 표시 |
| `provenance` | 객체 · action_instance_ids, approval_status, bundle_id, decision_id, decision_ids, evidence_status, reason … | [펼쳐 보기](#field-169f4a2441d18d54) |

<a id="field-169f4a2441d18d54"></a>

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
  "reason": "report_context",
  "semantic_episode_id": null,
  "workflow": "triz-ax-v3.1"
}
```

</details>

보고서 본문 중복 또는 과거 Step 투영본은 제외했습니다. 따라서 위 DB `content_hash`는 게시한 축약 객체의 해시가 아닌 **DB 원본 버전의 해시**입니다. 제외 범위는 [수집 기준](../PROVENANCE.md)에 적었습니다.
