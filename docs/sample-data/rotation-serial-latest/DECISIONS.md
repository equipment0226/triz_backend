# 정책·보완 결정

[사례 개요](README.md)

각 행의 상세 링크에는 해당 저장 payload 전체가 있습니다. 별도 요청·응답 원문이 포함되는 필드는 본문 대신 해시를 남겼습니다.

| ID | KST | 종류 | 전체 payload |
|---|---|---|---|
| dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085 | 07:10:58 | decision | [보기](#row-dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085) |
| dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9 | 07:14:48 | decision | [보기](#row-dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9) |
| dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f | 07:15:47 | decision | [보기](#row-dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f) |
| dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde | 07:18:09 | decision | [보기](#row-dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde) |
| dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e | 07:22:17 | decision | [보기](#row-dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e) |
| dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287 | 07:23:02 | decision | [보기](#row-dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287) |
| dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943 | 07:23:48 | decision | [보기](#row-dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943) |
| dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586 | 07:24:38 | decision | [보기](#row-dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586) |
| dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307 | 07:33:03 | decision | [보기](#row-dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307) |
| dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca | 07:33:46 | decision | [보기](#row-dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca) |
| dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d | 07:34:29 | decision | [보기](#row-dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d) |
| dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359 | 07:35:17 | decision | [보기](#row-dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359) |
| dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6 | 07:36:06 | decision | [보기](#row-dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6) |
| dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12 | 07:43:10 | decision | [보기](#row-dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12) |

<a id="row-dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085"></a>

<details>
<summary>dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-4487c9a6151141879697ca76241925e4",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "GENERATE_BASELINE",
          "allowed_tools": [
            "legacy_tracks",
            "evidence_search"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "ApplicabilityCheck"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {
            "preserve_requirements": true,
            "tracks": [
              "D_ARIZ",
              "A_MATRIX",
              "B_SEPARATION"
            ]
          },
          "reason": "분석 모드의 필수 경로를 배치 크기 제한 안에서 순차 실행한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c"
          ]
        }
      },
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "DEFER",
          "allowed_tools": [],
          "expected_outputs": [
            "Blocker"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {},
          "reason": "예산 또는 적용조건 부족으로 탐색을 보류한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "s4.route",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      0.0,
      0.0,
      0.0,
      1.0,
      0.30672389999999994,
      1.0,
      0.0,
      0.0,
      0.0
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-4487c9a6151141879697ca76241925e4"
  },
  "created_at": "2026-09-29T22:10:58.186458+00:00"
}
```

</details>

<a id="row-dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9"></a>

<details>
<summary>dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-4487c9a6151141879697ca76241925e4",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "GENERATE_BASELINE",
          "allowed_tools": [
            "legacy_tracks"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "ApplicabilityCheck"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {
            "preserve_requirements": true,
            "tracks": [
              "C_STANDARDS",
              "E_TRIMMING",
              "F_TRENDS"
            ]
          },
          "reason": "아직 수행하지 않은 분석 모드의 필수 경로를 실행한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "solve:required_batch",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      0.5,
      0.0,
      0.0,
      1.0,
      0.29472699999999996,
      1.0,
      0.0,
      0.0,
      0.0
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-4487c9a6151141879697ca76241925e4"
  },
  "created_at": "2026-09-29T22:14:48.751243+00:00"
}
```

</details>

<a id="row-dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f"></a>

<details>
<summary>dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f · 전체 저장값</summary>

```json
{
  "decision_id": "dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-4487c9a6151141879697ca76241925e4",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "GENERATE_BASELINE",
          "allowed_tools": [
            "legacy_tracks"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "ApplicabilityCheck"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {
            "preserve_requirements": true,
            "tracks": [
              "G_FOS",
              "H_EFFECTS"
            ]
          },
          "reason": "아직 수행하지 않은 분석 모드의 필수 경로를 실행한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "solve:required_batch",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      0.5,
      0.0,
      0.0,
      1.0,
      0.2914175,
      1.0,
      0.0,
      0.0,
      0.0
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-4487c9a6151141879697ca76241925e4"
  },
  "created_at": "2026-09-29T22:15:47.118760+00:00"
}
```

</details>

<a id="row-dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde"></a>

<details>
<summary>dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde · 전체 저장값</summary>

```json
{
  "decision_id": "dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-74a823dc8b0c470bac6070c552f5277b",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "CHECK_APPLICABILITY",
          "allowed_tools": [
            "deterministic_validation"
          ],
          "expected_outputs": [
            "VersionedResult"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {},
          "reason": "과학효과의 필요 조건과 검증 의무를 점검한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-5787558b3bd746ab91a488cd619d84fe"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "stage:CHECK_APPLICABILITY",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      0.0,
      0.0,
      1.0,
      0.27809839999999997,
      1.0,
      0.0,
      0.0,
      0.0
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-74a823dc8b0c470bac6070c552f5277b"
  },
  "created_at": "2026-09-29T22:18:09.053275+00:00"
}
```

</details>

<a id="row-dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e"></a>

<details>
<summary>dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e · 전체 저장값</summary>

```json
{
  "decision_id": "dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 1,
            "candidate_id": "CPT-S6-32d46b742a89c1c2",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED"
            ],
            "obligation_ids": [
              "TC-ba15f1e6",
              "TC-c8cf7951"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-e7bdb345d9504a35bcb0ff4d88198e5d"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:before_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.26814899999999997,
      1.0,
      0.36666666666666664,
      0.6,
      0.0
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945"
  },
  "created_at": "2026-09-29T22:22:17.031435+00:00"
}
```

</details>

<a id="row-dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287"></a>

<details>
<summary>dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 2,
            "candidate_id": "CPT-S6-32d46b742a89c1c2",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED"
            ],
            "obligation_ids": [
              "TC-ba15f1e6",
              "TC-c8cf7951"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-e7bdb345d9504a35bcb0ff4d88198e5d"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:before_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.266552,
      1.0,
      0.36666666666666664,
      0.6,
      0.25
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945"
  },
  "created_at": "2026-09-29T22:23:02.584473+00:00"
}
```

</details>

<a id="row-dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943"></a>

<details>
<summary>dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 1,
            "candidate_id": "CPT-S6-099405e4edc0a658",
            "depth": 1,
            "gap_kinds": [
              "QUALITY_REVIEW"
            ],
            "obligation_ids": [
              "TC-c8cf7951"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-e7bdb345d9504a35bcb0ff4d88198e5d"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:before_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.264915,
      1.0,
      0.36666666666666664,
      0.6,
      0.5
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945"
  },
  "created_at": "2026-09-29T22:23:48.385336+00:00"
}
```

</details>

<a id="row-dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586"></a>

<details>
<summary>dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945",
  "epoch": 50,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 2,
            "candidate_id": "CPT-S6-099405e4edc0a658",
            "depth": 1,
            "gap_kinds": [
              "QUALITY_REVIEW"
            ],
            "obligation_ids": [
              "TC-c8cf7951"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-e7bdb345d9504a35bcb0ff4d88198e5d"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:before_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.2631542,
      1.0,
      0.36666666666666664,
      0.6,
      0.5
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945"
  },
  "created_at": "2026-09-29T22:24:38.250934+00:00"
}
```

</details>

<a id="row-dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307"></a>

<details>
<summary>dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 1,
            "candidate_id": "CPT-S6-d2c3056109ec002a",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED",
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED",
              "UNSUPPORTED_CAUSE"
            ],
            "obligation_ids": [
              "TC-ba15f1e6",
              "TC-c8cf7951",
              "TC-b5b764b0"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-b0e3902510de48e9b02e87891af05f3a",
            "av-a8bbcf6fe3eb491fa96001cff31d08b3"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:after_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.2589277,
      1.0,
      0.4583333333333333,
      0.75,
      0.5
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d"
  },
  "created_at": "2026-09-29T22:33:03.525185+00:00"
}
```

</details>

<a id="row-dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca"></a>

<details>
<summary>dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca · 전체 저장값</summary>

```json
{
  "decision_id": "dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 2,
            "candidate_id": "CPT-S6-d2c3056109ec002a",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED",
              "IMPROVEMENT_SIDE_OMITTED",
              "ADVERSE_SIDE_OMITTED",
              "UNSUPPORTED_CAUSE"
            ],
            "obligation_ids": [
              "TC-ba15f1e6",
              "TC-c8cf7951",
              "TC-b5b764b0"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-b0e3902510de48e9b02e87891af05f3a",
            "av-a8bbcf6fe3eb491fa96001cff31d08b3"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:after_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.2573890999999999,
      1.0,
      0.4583333333333333,
      0.75,
      0.75
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d"
  },
  "created_at": "2026-09-29T22:33:46.966967+00:00"
}
```

</details>

<a id="row-dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d"></a>

<details>
<summary>dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d · 전체 저장값</summary>

```json
{
  "decision_id": "dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 1,
            "candidate_id": "CPT-S6-ac128a6d03303a81",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED"
            ],
            "obligation_ids": [
              "TC-c8cf7951",
              "TC-097b79ff"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-b0e3902510de48e9b02e87891af05f3a",
            "av-a8bbcf6fe3eb491fa96001cff31d08b3"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:after_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.2558022,
      1.0,
      0.4583333333333333,
      0.75,
      1
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d"
  },
  "created_at": "2026-09-29T22:34:29.939881+00:00"
}
```

</details>

<a id="row-dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359"></a>

<details>
<summary>dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "REPAIR_CANDIDATE",
          "allowed_tools": [
            "candidate_repair"
          ],
          "expected_outputs": [
            "CandidateVersion",
            "CoherenceReview"
          ],
          "input_snapshot_id": "",
          "model_role": "FLASH",
          "parameters": {
            "ancestor_regression_checks": [
              "original_improvement",
              "original_protected_side",
              "hard_constraints"
            ],
            "attempt": 2,
            "candidate_id": "CPT-S6-ac128a6d03303a81",
            "depth": 1,
            "gap_kinds": [
              "IMPROVEMENT_SIDE_OMITTED"
            ],
            "obligation_ids": [
              "TC-c8cf7951",
              "TC-097b79ff"
            ],
            "optional": true
          },
          "reason": "?? ??? ??? ??? ?? ??? ????.",
          "reserved_microusd": 100000,
          "target_version_ids": [
            "av-1cb9c589494c44b0a4818055a455b84c",
            "av-b0e3902510de48e9b02e87891af05f3a",
            "av-a8bbcf6fe3eb491fa96001cff31d08b3"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "coherence:after_constraints",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.25417069999999997,
      1.0,
      0.4583333333333333,
      0.75,
      1
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d"
  },
  "created_at": "2026-09-29T22:35:17.095633+00:00"
}
```

</details>

<a id="row-dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6"></a>

<details>
<summary>dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-7231f58fa80a4136829ac2930ab655d6",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "FETCH_EVIDENCE",
          "allowed_tools": [
            "deterministic_validation"
          ],
          "expected_outputs": [
            "VersionedResult"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {},
          "reason": "후보별 적용 근거를 수집한다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-f87b49192c164f969e931e9e8660b7a4"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "stage:FETCH_EVIDENCE",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.2526155,
      1.0,
      0.4583333333333333,
      0.75,
      1
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-7231f58fa80a4136829ac2930ab655d6"
  },
  "created_at": "2026-09-29T22:36:06.715655+00:00"
}
```

</details>

<a id="row-dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12"></a>

<details>
<summary>dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12 · 전체 저장값</summary>

```json
{
  "decision_id": "dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "snapshot_id": "snap-3e7bf6228d8c493d9ced98991287bf98",
  "epoch": 51,
  "payload": {
    "actions": [
      {
        "allowed": true,
        "blocked_reason": null,
        "ticket": {
          "action_instance_id": "",
          "action_type": "DEFER",
          "allowed_tools": [
            "deterministic_validation"
          ],
          "expected_outputs": [
            "VersionedResult"
          ],
          "input_snapshot_id": "",
          "model_role": "CODE",
          "parameters": {},
          "reason": "미실행·미확인 검증을 조건부로 보고하고 추가 승인을 기다리지 않는다.",
          "reserved_microusd": 0,
          "target_version_ids": [
            "av-4dfbe87665f3492fb5910b3834cf2c5f"
          ]
        }
      }
    ],
    "behavior_probability": null,
    "bundle_id": "bundle-97dcff061e5d128c48d626fedfbefdb754c12b2d6fee03b9b97af35b6593da00",
    "context": "stage:DEFER",
    "executed_index": 0,
    "feature_schema": "ax-features-v2",
    "features": [
      1.0,
      1,
      1,
      1,
      1,
      0.0,
      1.0,
      0.23926369999999997,
      1.0,
      0.4583333333333333,
      0.75,
      1
    ],
    "governor_override": false,
    "override_reason": null,
    "policy_version": "rules-v1",
    "proposed_index": 0,
    "selection_mode": "RULE_BASED",
    "snapshot_id": "snap-3e7bf6228d8c493d9ced98991287bf98"
  },
  "created_at": "2026-09-29T22:43:10.322353+00:00"
}
```

</details>
