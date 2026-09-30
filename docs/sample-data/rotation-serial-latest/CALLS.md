# 모델 호출과 비용

[사례 개요](README.md)

이번 구간에 저장된 기록은 101개입니다.

task는 중복 없이 한 번씩 집계했습니다. reserve / actual 단위는 microUSD입니다. actual·provider usage·저장 pricing은 실행 당시 원문 값입니다. 정정액은 별도 COST_RESTATEMENT_APPLIED 이벤트에서 계산한 값이며 원본을 덮어쓰지 않았습니다.

[비용정정 근거·비교표](COSTS.md)

| task | KST 생성 | 실제 Stage | node | 원본 USD | 정정 반영 USD |
|---|---|---|---|---|---|
| [task-96d416cce2bffe30dd2ae2456a32e931d4ee959fe581a89f3d5b3d19053a](#row-0) | 2026-09-30 12:51:30 | s0_research | s0_deep_dive | 0.003818 | 0.001608 |
| [task-e5b5930949907f20ccf0c63c3c2cd1e47357438d0bcb2b429d12ace6dfd6](#row-1) | 2026-09-30 12:54:23 | s0_research | s0_deep_dive | 0.003798 | 0.001561 |
| [task-3d529c33e8f69919a81303d37dcf45669b54e6b3670770c4736b8e691615](#row-2) | 2026-09-30 12:55:31 | s1_intake | s1_extract | 0.007246 | 0.003322 |
| [task-837950718d92c18bc1a0cdc86c546849b36c92ea38865a897dd2d6a975cc](#row-3) | 2026-09-30 12:56:37 | s2_confirm | s2_candidates | 0.003654 | 0.001789 |
| [task-5d2586003cbcc1c9d5ba23cb9eba75c7c192f49ee41fe752517628b2c12a](#row-4) | 2026-09-30 12:59:28 | s3_analyze | s3_nine_windows | 0.003877 | 0.001675 |
| [task-b66ca81e3aa1e434fd8c3c97cd3e09dfc3a3d21dddab071aa68cc68afc7a](#row-5) | 2026-09-30 12:59:45 | s3_analyze | s3_function_model | 0.006641 | 0.003057 |
| [task-64040edcccc9df3c485881d5accf1cc3b1a36feb7c3471408c85398864dc](#row-6) | 2026-09-30 13:00:03 | s3_analyze | independent_verifier | 0.003646 | 0.001823 |
| [task-007809559d7bf02ec457b97d1b6835b037108bffbb7867afbfc6452c963d](#row-7) | 2026-09-30 13:00:13 | s3_analyze | s3_function_model | 0.008096 | 0.002787 |
| [task-3d0a1f1983f91870b39b33e2549fa3ecf368afe68707d397f61c09c07ada](#row-8) | 2026-09-30 13:00:29 | s3_analyze | independent_verifier | 0.003498 | 0.001731 |
| [task-e4f5d3452c59b97161d9444547d7c66b7d43e140c9b5a31893bc0c17856a](#row-9) | 2026-09-30 13:00:49 | s3_analyze | s3_ceca | 0.005902 | 0.002688 |
| [task-4679897664a9193bf4a856f94a689b37b53bab8f110e5a16a50ad38ca299](#row-10) | 2026-09-30 13:00:50 | s3_analyze | s3_sufield | 0.002776 | 0.001125 |
| [task-48616c5302936ba99c04ce4d80a02acba7d262aef13197ac54e93a566a4c](#row-11) | 2026-09-30 13:00:52 | s3_analyze | s3_resources | 0.005602 | 0.002538 |
| [task-c7956c4f0b8682c011ece4d05ff548c62a4d6c45bf8636c73352f5f66f57](#row-12) | 2026-09-30 13:01:05 | s3_analyze | independent_verifier | 0.003155 | 0.001578 |
| [task-60732446120732bd78ebfccdd187e0ca01420d387972cdaa98730d2fcf21](#row-13) | 2026-09-30 13:01:17 | s3_analyze | s3_constraints | 0.006565 | 0.003019 |
| [task-2d28fa3e44d4c66a701bd010487fe4dbed14722e1408452b0dd98f7c9f2b](#row-14) | 2026-09-30 13:02:29 | s4_define | s4_contradictions | 0.008569 | 0.004040 |
| [task-25f850857b7c56b7d97140f04149a619fa0b44c39b8b9704a96f09815829](#row-15) | 2026-09-30 13:02:31 | s4_define | s4_ifr | 0.003469 | 0.001434 |
| [task-2614b383ee7fce0563b15685bf0259266b4b425fc8424acf7dfc343d12ae](#row-16) | 2026-09-30 13:02:33 | s4_define | s4_trimming | 0.004748 | 0.002073 |
| [task-1f8d183469aef6c6461f5c86097068d29476ac31b51cb6dfee1767ed8b13](#row-17) | 2026-09-30 13:02:53 | s4_define | independent_verifier | 0.005246 | 0.002623 |
| [task-66ee14e6df1ac42207564e39fb8b6b1fda5a24365a159ad30a7c7e7cce46](#row-18) | 2026-09-30 13:03:07 | s4_define | s4_contradictions | 0.012012 | 0.004426 |
| [task-7061fd35a016b2872791214a81c12fea3f858ffad50fe1574f624540d5ef](#row-19) | 2026-09-30 13:03:33 | s4_define | independent_verifier | 0.006502 | 0.003082 |
| [task-188d821e2b857008361290675769dd9786af46b0c1dfa7733cc0258027f3](#row-20) | 2026-09-30 13:03:47 | s4_define | s4_key_problem | 0.004706 | 0.002052 |
| [task-eb6b9c8067a10f2842561bcde7f0bf98cb0472d89f873b055b79224f4b6a](#row-21) | 2026-09-30 13:04:57 | s5_solve | s5_track_a_select | 0.002485 | 0.000942 |
| [task-7b7cf6ede7f045163aa848d7eb3bd16ec39e6c1867103e114c35772f845e](#row-22) | 2026-09-30 13:05:00 | s5_solve | s5_track_b | 0.004978 | 0.002188 |
| [task-05512c0144bbc9b1916fe54968d53ae863cf4ec6e79f2e0733bfdc01b7b1](#row-23) | 2026-09-30 13:05:01 | s5_solve | s5_ariz_p1 | 0.007245 | 0.003322 |
| [task-1a7a16d5885f7914bc79649999678e7382da2e0f825c87ffb0bcf95679e2](#row-24) | 2026-09-30 13:05:07 | s5_solve | s5_track_a | 0.006277 | 0.002838 |
| [task-a997cdd1d2fd95918448e85cee6ead83eddae19ed9a81210d4feca7e19a0](#row-25) | 2026-09-30 13:05:16 | s5_solve | s5_track_b | 0.005264 | 0.002312 |
| [task-12b0482ccf629af17309947a1acff5f585d39bd9dca9d45c36b92395c3bb](#row-26) | 2026-09-30 13:05:26 | s5_solve | s5_ariz_p2 | 0.008591 | 0.003995 |
| [task-c1e1232a2f24602d6e0cd181f62f055c7698b725edf77ec3d6b8be08017d](#row-27) | 2026-09-30 13:05:31 | s5_solve | s5_track_a_select | 0.002520 | 0.000940 |
| [task-87688fa6d8a1dc869848107ead374e31973528858ff61cef69e190975da0](#row-28) | 2026-09-30 13:05:37 | s5_solve | s5_track_a | 0.006732 | 0.003046 |
| [task-67405b6f569f7bee8ab681331a8c18733492a5b2e4e1c84b2bf7f9013936](#row-29) | 2026-09-30 13:05:47 | s5_solve | s5_ariz_p3 | 0.009782 | 0.004590 |
| [task-70c570d46cb6cb76dd58cf4b4c2c3bfa9d1000b5d16d45f7e9d64beeb572](#row-30) | 2026-09-30 13:06:06 | s5_solve | s5_track_a_select | 0.002451 | 0.000906 |
| [task-61157672535aa6dffd1132e837f8c818058b006290239dfc4b8033324e30](#row-31) | 2026-09-30 13:06:12 | s5_solve | s5_ariz_p4 | 0.013161 | 0.006261 |
| [task-5a80415715466275630d60fcbfa3a220af9c6cf2f28aea0aa83eb5f3c1c1](#row-32) | 2026-09-30 13:06:14 | s5_solve | s5_track_a | 0.006888 | 0.003124 |
| [task-0c0e490f096add167ce06b7828fbd033502632c84149a9201d78f50765d7](#row-33) | 2026-09-30 13:06:57 | s5_solve | s5_ariz_p5 | 0.077195 | 0.034139 |
| [task-787d899c0b965da6ea0955ea819c25ca2df00d2c29687ebe428368aa531f](#row-34) | 2026-09-30 13:09:54 | s5_solve | s5_ariz_p6 | 0.015068 | 0.007233 |
| [task-0353c7e66812db34ecc64e9f4a3014a3affa4c07c97a15f7d9b244a5ba5b](#row-35) | 2026-09-30 13:10:05 | s5_solve | s5_ariz_p7 | 0.010365 | 0.004863 |
| [task-810b9f82fdb3aee459b69de39b895f8c85ce9624be89b6e7c8c6e761f2a4](#row-36) | 2026-09-30 13:10:52 | s5_solve | s5_track_e | 0.009996 | 0.004697 |
| [task-2b30875317368c949d772f5c0933284f0510f47ff0c2270c024246c08813](#row-37) | 2026-09-30 13:10:54 | s5_solve | s5_track_c | 0.008841 | 0.004120 |
| [task-c885f6a180b05d074507be66adc38dbb07eeb19d68352684721a415aec16](#row-38) | 2026-09-30 13:10:57 | s5_solve | s5_track_f | 0.010082 | 0.004740 |
| [task-9e8a1ac02eb2c53001446fc7a919f36b19d1bcbb0e206d2cdb4786ab7a20](#row-39) | 2026-09-30 13:11:18 | s5_solve | s5_track_c | 0.009253 | 0.004307 |
| [task-f158f08b4c70c9f43f7d0f463c0ce78e2a704884cdee415b88f3dbf60783](#row-40) | 2026-09-30 13:11:53 | s5_solve | s5_track_g | 0.008425 | 0.003912 |
| [task-908f316573a241ef496c58ae94dee079fab8d53d3744c8d14af90f7542db](#row-41) | 2026-09-30 13:11:57 | s5_solve | s5_track_h | 0.011583 | 0.005491 |
| [task-c412229a1afc16b2381cb4c8409337e15738cba131e62a14d6bec8e2774d](#row-42) | 2026-09-30 13:12:27 | s5_solve | s5_merge | 0.042628 | 0.021013 |
| [task-d79718f56e2bed82b63009c0f6297fc31ac3a8a89445bf1243e3e8fd661f](#row-43) | 2026-09-30 13:15:34 | s5_solve | s5_merge | 0.046774 | 0.006171 |
| [task-7516bec277efdf1fdd194622c670689a18c8ec9b5ac6f60b544b3cbe2e87](#row-44) | 2026-09-30 13:16:05 | s5_solve | s5_merge | 0.046794 | 0.006162 |
| [task-2d3e81d6cac68bc28226c369b7dbe00a1804a66b22bd5a0e38d0fbcd3291](#row-45) | 2026-09-30 13:18:12 | s6_concept | s6_concept | 0.026705 | 0.013052 |
| [task-255a5d8f1dd63462876a1a4fc12479bafeedc0aa796536cd475eb88c5dd5](#row-46) | 2026-09-30 13:18:14 | s6_concept | s6_concept | 0.013219 | 0.004728 |
| [task-3e888950030808b46c26bbe2dc600fc3412f3db61f5ed9206fea94ccf160](#row-47) | 2026-09-30 13:18:17 | s6_concept | s6_concept | 0.027340 | 0.011789 |
| [task-75d79981bca7fe8a0c9311e2dcf9e04ef1ba1f430e81175c38ba24e74115](#row-48) | 2026-09-30 13:19:18 | s6_concept | independent_verifier | 0.008160 | 0.004080 |
| [task-efcbbcc57d368e9530caea4c0f4210c7a1db3c43fdda0f3f9b5866de7b4d](#row-49) | 2026-09-30 13:19:37 | s6_concept | independent_verifier | 0.007773 | 0.003887 |
| [task-9fea385c0b523896b0426ffa6e2e3cd883cacbfaa5530bb7408b9502144c](#row-50) | 2026-09-30 13:19:58 | s6_concept | independent_verifier | 0.006377 | 0.003189 |
| [task-28eb94c8337dff3b995ab1f65ea8b2c239c98307b05c54470eaafd1f5b3f](#row-51) | 2026-09-30 13:20:15 | s6_concept | independent_verifier | 0.008065 | 0.004033 |
| [task-643597ff594e3331a4fcd79bdc6494cee6b654c7acd4b6099cac1a613587](#row-52) | 2026-09-30 13:20:39 | s6_concept | independent_verifier | 0.007026 | 0.003513 |
| [task-4c40bff126eb88b65b50046eb6ae3733a5352e5a6716616ae937b52e7db3](#row-53) | 2026-09-30 13:21:00 | s6_concept | independent_verifier | 0.009084 | 0.004542 |
| [task-7320ddeff65976f99a5632867e351282f7a739d133e3561a5d7105de7642](#row-54) | 2026-09-30 13:21:23 | s6_concept | independent_verifier | 0.007704 | 0.003852 |
| [task-2ac9e64017116bcf5fd851ba2a64aa4b42205c86818b0388ecd5babb7f0a](#row-55) | 2026-09-30 13:21:48 | s6_concept | independent_verifier | 0.006774 | 0.003387 |
| [task-c47c7889f7064bfa6d66de4232718d16131c0253fa20a3c03725f1f22f54](#row-56) | 2026-09-30 13:23:10 | s7_gate | ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_0 | 0.009865 | 0.004632 |
| [task-c238ad9996c60f8e8ca2282a7d322c5e9decbbb7d69d715881ecc2ffe4e8](#row-57) | 2026-09-30 13:23:34 | s7_gate | independent_verifier | 0.006502 | 0.003251 |
| [task-e815817f51c7da9045247ba6b248c505c58ff3cd05033247e475d15a6ec8](#row-58) | 2026-09-30 13:24:00 | s7_gate | ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_1 | 0.009174 | 0.001934 |
| [task-de01642c4a6ba1f049d589819211ba353bd46238c9dea70cff9e83df0876](#row-59) | 2026-09-30 13:24:22 | s7_gate | independent_verifier | 0.006554 | 0.003277 |
| [task-6cbd68f470f5381b8bd7f6b1983b511e5abdc13787e48d44b259c6832d1e](#row-60) | 2026-09-30 13:24:47 | s7_gate | ax_repair_gap-f705ac45d5656e38b0c6b5e9_0 | 0.011882 | 0.005490 |
| [task-6756d8a19b733b4fe4c1a8547c711e4df46adbc4c6b032f394a525b3b885](#row-61) | 2026-09-30 13:25:10 | s7_gate | independent_verifier | 0.008598 | 0.004299 |
| [task-a703932eb882a1b3d4e8cc61813719245814c186691a868671d26656a41c](#row-62) | 2026-09-30 13:25:35 | s7_gate | ax_repair_gap-f705ac45d5656e38b0c6b5e9_1 | 0.014311 | 0.004014 |
| [task-319944d610b87f6b2d33c4e9fcbbff76e16566c6f273f92f64d89f7c9089](#row-63) | 2026-09-30 13:26:04 | s7_gate | independent_verifier | 0.008557 | 0.004279 |
| [task-433083973487651917535eec5a4924b1f073b4b98314d9bcd76e20b91a3a](#row-64) | 2026-09-30 13:26:56 | s7_gate | s7_gate_4 | 0.002904 | 0.001433 |
| [task-a9169bd17aee35793963890002c83cdf33b0e2392785954655eb14cc722e](#row-65) | 2026-09-30 13:26:59 | s7_gate | s7_gate_3 | 0.002982 | 0.001152 |
| [task-b896788cdca0986380073eba09585d7f665c3e8152e1f80f94cfcfdc5ab3](#row-66) | 2026-09-30 13:27:01 | s7_gate | s7_gate_2 | 0.002888 | 0.001106 |
| [task-66149a335a59a37b21a2c6a1c115fef4e27d20625e35b2d11b01c7bd1e16](#row-67) | 2026-09-30 13:27:06 | s7_gate | s7_gate_1 | 0.003059 | 0.001191 |
| [task-2013132a6413a376d2015c3c511bfcee628c528c720dda62fc6c04b1bed5](#row-68) | 2026-09-30 13:27:25 | s7_gate | s7_gate_7 | 0.002723 | 0.001023 |
| [task-56c179cfc48b0ede2d3b8ddc821902f4b1511d9da1d539f118575c21f94a](#row-69) | 2026-09-30 13:27:28 | s7_gate | s7_gate_6 | 0.002740 | 0.001032 |
| [task-225d69a61036b2e52c4c1eaedd9b4eb4253d27f7df8d9b365900581fa156](#row-70) | 2026-09-30 13:27:32 | s7_gate | s7_gate_8 | 0.002755 | 0.001039 |
| [task-fba37ec4c9090e7a260ff78167ad327401eb831e5f1f9100b5bbcad06088](#row-71) | 2026-09-30 13:27:35 | s7_gate | s7_gate_5 | 0.002913 | 0.001118 |
| [task-1ddec92b7d7159732d76f182a2a5b343ca16c85b5f4b08de6696c7efb624](#row-72) | 2026-09-30 13:27:47 | s7_gate | s7_gate_9 | 0.002741 | 0.001032 |
| [task-2018a941b69de9ae2698444bd6776313a247c9eb715e470d109c911b3136](#row-73) | 2026-09-30 13:27:50 | s7_gate | s7_gate_10 | 0.002704 | 0.001014 |
| [task-8e775beffd34727b0289949205ccc06cc6967c6def86187bff92d7705636](#row-74) | 2026-09-30 13:31:52 | s8_references | ax_repair_gap-26e0db61185158a1836b4b6b_0 | 0.012018 | 0.005558 |
| [task-4d59e2d4177e5dce93098b51643cf44fc49668f8551984dbe35ae16b61fc](#row-75) | 2026-09-30 13:32:39 | s8_references | independent_verifier | 0.008564 | 0.004282 |
| [task-a9cc82dcf73639720d1f0b34dc3a7214b9fa1bc1e3ff12e86fc837ea0340](#row-76) | 2026-09-30 13:33:17 | s8_references | ax_repair_gap-26e0db61185158a1836b4b6b_1 | 0.009935 | 0.001901 |
| [task-cc15ffc14846556ca4a4121fd1894b432c56449ac34ff7285e1eab1cd2f4](#row-77) | 2026-09-30 13:33:48 | s8_references | independent_verifier | 0.007617 | 0.003809 |
| [task-9d5425e6cb7616eca9c456fea2f869d52595e44011f9e5d178bea5a537a7](#row-78) | 2026-09-30 13:35:10 | s8_references | ax_repair_gap-ab829f5d78d52e0eaeb7afea_0 | 0.010076 | 0.004587 |
| [task-2af69ca787931e1011e851e6606f298458f097821c8e910690c0e935f2c4](#row-79) | 2026-09-30 13:35:44 | s8_references | independent_verifier | 0.007293 | 0.003647 |
| [task-a3820767839185ee8333935d411ca988c7c2807ce71534f6551910e6c5aa](#row-80) | 2026-09-30 13:36:38 | s8_references | ax_repair_gap-ab829f5d78d52e0eaeb7afea_1 | 0.010246 | 0.002150 |
| [task-73551b14ceab30e8bf368088fcebf6bfc6991e8a9af663ceb12e8d060e3d](#row-81) | 2026-09-30 13:37:10 | s8_references | independent_verifier | 0.007347 | 0.003674 |
| [task-04b554ec43d937c9afb1c886b8a6bb4f9f0884338e283c864fbd687d2f71](#row-82) | 2026-09-30 13:41:12 | s8_references | s9_evidence_match_0 | 0.007818 | 0.003608 |
| [task-9f800905ce00e1dad9b2c86b3838716f3e4eb8ee8e64f7d321d3ccbb3aeb](#row-83) | 2026-09-30 13:41:41 | s8_references | s9_evidence_match_1 | 0.006669 | 0.003015 |
| [task-5d001a97f9e27c99e41d5da6af6e567baf2dfe52d85a68feab67f886fa3d](#row-84) | 2026-09-30 13:42:13 | s8_references | s9_evidence_match_2 | 0.006813 | 0.003087 |
| [task-52455f41692048d593c7f55ec1a6a885b9fb48d182c040864c5b8f1d7c70](#row-85) | 2026-09-30 13:42:57 | s8_references | s9_evidence_match_3 | 0.005712 | 0.002536 |
| [task-45a5bd564acc34f59cd610dc8974eb64c00e2415c26cd8dff5be3d0ba8bc](#row-86) | 2026-09-30 13:44:31 | s8_evaluate | s8_persona_factory | 0.003618 | 0.001508 |
| [task-b39fbcac51eff877b8ee13816441e3a908711ba182a009cb5c87e32527e7](#row-87) | 2026-09-30 13:45:14 | s8_evaluate | s8_review_independent | 0.012158 | 0.006079 |
| [task-d93dc77d3edc9d8f0a6dee6f8ebcf97bf6a6d1b86067f670197cacb83742](#row-88) | 2026-09-30 13:45:27 | s8_evaluate | s8_review_independent | 0.012043 | 0.006022 |
| [task-bc2c8e79ddac5aaca2be8b441fcc3e52e84d7a2af00b2539dd90ba201862](#row-89) | 2026-09-30 13:45:39 | s8_evaluate | s8_review_independent | 0.012331 | 0.006166 |
| [task-33c3aaef7999a292b8a35ba0eefea694135d3fc6ade6ca23d3e8bb613352](#row-90) | 2026-09-30 13:45:50 | s8_evaluate | s8_review_independent | 0.011659 | 0.005830 |
| [task-1a93d7c32a971d656641f70e08deeb5f90f36d183669cd9410e0db58e6cb](#row-91) | 2026-09-30 13:46:46 | s8_evaluate | s8_review_independent | 0.010818 | 0.002229 |
| [task-13c1df5928b052144ce0fb07129e254f9108c57841bccefb4c5de4dd8b32](#row-92) | 2026-09-30 13:46:59 | s8_evaluate | s8_review_independent | 0.010521 | 0.002081 |
| [task-e60304da2093962eb36a35ebf56eee40cde2f256b17dac984eaab375959b](#row-93) | 2026-09-30 13:47:10 | s8_evaluate | s8_review_independent | 0.010473 | 0.002057 |
| [task-623d8eeb04bc16ed3b2fa1366f9d38f80063781de8b5e2861cc0dd2c457e](#row-94) | 2026-09-30 13:47:19 | s8_evaluate | s8_review_independent | 0.010265 | 0.001953 |
| [task-1863fa93ae440c880e857aa113742d54c33d9d1aa6b41d167f201c8c0df4](#row-95) | 2026-09-30 13:48:32 | s8_evaluate | s8_review_independent | 0.010322 | 0.005161 |
| [task-418484586f7acc806666a3a6f166e3aedf5878fe6520e665272f28d2354c](#row-96) | 2026-09-30 13:48:52 | s8_evaluate | s8_review_independent | 0.011795 | 0.005898 |
| [task-f253d058d68bab2e0c7ed2970f86f934109c7f8e48723099267bdcc56c3f](#row-97) | 2026-09-30 13:52:50 | s8_evaluate | s8_review_independent | 0.010274 | 0.001957 |
| [task-fe2b47a69d2fbe25e7445b2e77a0b548a8ec09f46e03fed812f26fd56518](#row-98) | 2026-09-30 13:52:59 | s8_evaluate | s8_review_independent | 0.010708 | 0.002174 |
| [task-5e67663a09cdb6d9e1eff5544277c78f348baabf768f77dee36a15d45f6d](#row-99) | 2026-09-30 13:54:17 | s8_evaluate | s8_rank | 0.007354 | 0.003376 |
| [task-e27241035908f1fba291d125857029dfb77234e545786047230f4e90b9a6](#row-100) | 2026-09-30 13:55:12 | s8_evaluate | s8_rank | 0.008038 | 0.002062 |

<a id="row-0"></a>

<details>
<summary>기록 1 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-96d416cce2bffe30dd2ae2456a32e931d4ee959fe581a89f3d5b3d19053a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 53 | 전체 값 |
| `input_snapshot` | "snap-164fe0d9d21c44cfb95783c77d9de071" | 전체 값 |
| `input_hash` | "76fba12067e60a6e20fa6243aa60077711f10b9426f789efbaf79a333134317d" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742090.6170678 | 전체 값 |
| `reserve` | 92413 | 전체 값 |
| `actual` | 3818 | 전체 값 |
| `created_at` | "2026-09-30T03:51:30.617074+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:51:40.923210+00:00" | 전체 값 |
| `node` | "s0_deep_dive" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/05621b39db9c2462369445f5.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 3162, "tokens_out": 2391, "cost_usd": 0.0038177999999999997, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/96d97d6c2f336931cac64464.md) |

</details>

<a id="row-1"></a>

<details>
<summary>기록 2 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-e5b5930949907f20ccf0c63c3c2cd1e47357438d0bcb2b429d12ace6dfd6" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 54 | 전체 값 |
| `input_snapshot` | "snap-536b2744ed69438e8551fd125ae59aaa" | 전체 값 |
| `input_hash` | "c05f0f444fd15672c30d513953ddf1e0ef21e675fd0e3dac055ba8e901a37bb3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742263.270354 | 전체 값 |
| `reserve` | 93372 | 전체 값 |
| `actual` | 3798 | 전체 값 |
| `created_at` | "2026-09-30T03:54:23.270360+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:54:33.564683+00:00" | 전체 값 |
| `node` | "s0_deep_dive" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/b96aff64b846c40187851f82.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 3623, "tokens_out": 2259, "cost_usd": 0.0037977, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/f4fce0c2ad36427583f4e4c2.md) |

</details>

<a id="row-2"></a>

<details>
<summary>기록 3 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-3d529c33e8f69919a81303d37dcf45669b54e6b3670770c4736b8e691615" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 54 | 전체 값 |
| `input_snapshot` | "snap-b5b01fd0ffb54634ae3fcf23ae13447a" | 전체 값 |
| `input_hash` | "92f1c61256d2843456dea1b83db68bc7f1fa0a5d15047853e21d2a2710d3409c" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742331.0965345 | 전체 값 |
| `reserve` | 63591 | 전체 값 |
| `actual` | 7246 | 전체 값 |
| `created_at` | "2026-09-30T03:55:31.096539+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:55:44.536736+00:00" | 전체 값 |
| `node` | "s1_extract" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/86845153b173276802dad964.md) |
| `result_usage` | {"tier": "T1", "model": "deepseek-flash", "tokens_in": 8061, "tokens_out": 4023, "cost_usd": 0.0072458999999999996, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/357c3cb25c0e76c1336c1d0d.md) |

</details>

<a id="row-3"></a>

<details>
<summary>기록 4 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-837950718d92c18bc1a0cdc86c546849b36c92ea38865a897dd2d6a975cc" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 54 | 전체 값 |
| `input_snapshot` | "snap-7e313b9d637b445d90f429e7ecb6fd00" | 전체 값 |
| `input_hash` | "f1159a4f5591a8da48b2920778229a413847d4f808e8e111ed43c1ffbdf5eb4d" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742397.2552183 | 전체 값 |
| `reserve` | 97251 | 전체 값 |
| `actual` | 3654 | 전체 값 |
| `created_at` | "2026-09-30T03:56:37.255224+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:56:44.499395+00:00" | 전체 값 |
| `node` | "s2_candidates" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/a4a790d8e885ee3f83bde61c.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5741, "tokens_out": 1609, "cost_usd": 0.0036530999999999994, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/732bece817d675531832c8ba.md) |

</details>

<a id="row-4"></a>

<details>
<summary>기록 5 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-5d2586003cbcc1c9d5ba23cb9eba75c7c192f49ee41fe752517628b2c12a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "4aecd12acad42b6e215eca1713b82341bbf7720e2bd21b7c9435260971f4fd0c" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742568.8638911 | 전체 값 |
| `reserve` | 99231 | 전체 값 |
| `actual` | 3877 | 전체 값 |
| `created_at` | "2026-09-30T03:59:28.863896+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:59:37.088391+00:00" | 전체 값 |
| `node` | "s3_nine_windows" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/9d4c9775f3c27ecf6775c907.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 6754, "tokens_out": 1542, "cost_usd": 0.0038765999999999996, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/df270b0b3b3b3cec31cb36c0.md) |

</details>

<a id="row-5"></a>

<details>
<summary>기록 6 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-b66ca81e3aa1e434fd8c3c97cd3e09dfc3a3d21dddab071aa68cc68afc7a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "723fc9e42ec142bd8b8dac68fe3fd717876b85bf5717e6abccbe169689913e3a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742585.7401445 | 전체 값 |
| `reserve` | 102990 | 전체 값 |
| `actual` | 6641 | 전체 값 |
| `created_at` | "2026-09-30T03:59:45.740151+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T03:59:58.818328+00:00" | 전체 값 |
| `node` | "s3_function_model" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/6077b257b4b9ca5d3511b8cf.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8640, "tokens_out": 3374, "cost_usd": 0.0066408000000000005, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/26f58da920c844557f4addd8.md) |

</details>

<a id="row-6"></a>

<details>
<summary>기록 7 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-64040edcccc9df3c485881d5accf1cc3b1a36feb7c3471408c85398864dc" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "96f568e49f4f89d14e3e15466d9d76a1fc3f96e2b3a02d94d8b2fb61b180c393" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742603.3468137 | 전체 값 |
| `reserve` | 42700 | 전체 값 |
| `actual` | 3646 | 전체 값 |
| `created_at` | "2026-09-30T04:00:03.346819+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:00:09.324806+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/9ae048757bcf80272681e829.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 7475, "tokens_out": 1169, "cost_usd": 0.0036452999999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/197a3ef0235b0135da01f7d1.md) |

</details>

<a id="row-7"></a>

<details>
<summary>기록 8 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-007809559d7bf02ec457b97d1b6835b037108bffbb7867afbfc6452c963d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "4de4042d6abfbc29f69117cf803d4fd4270a0b988eac0e60b921b3ddf070347b" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742613.445578 | 전체 값 |
| `reserve` | 110445 | 전체 값 |
| `actual` | 8096 | 전체 값 |
| `created_at` | "2026-09-30T04:00:13.445586+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:00:24.850987+00:00" | 전체 값 |
| `node` | "s3_function_model" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ee23a315a24a255bb66a8708.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 12796, "tokens_out": 3547, "cost_usd": 0.0080952, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7bb17cf79213cdc74aacccf2.md) |

</details>

<a id="row-8"></a>

<details>
<summary>기록 9 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-3d0a1f1983f91870b39b33e2549fa3ecf368afe68707d397f61c09c07ada" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "26bf6a36f9988d7ec9e744bc6ef3b714b5aed3f9a0f95ad4b208d7a35188179b" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742629.2040455 | 전체 값 |
| `reserve` | 43059 | 전체 값 |
| `actual` | 3498 | 전체 값 |
| `created_at` | "2026-09-30T04:00:29.204050+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:00:34.623056+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/c3fc644a42da1c7197f40803.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 7648, "tokens_out": 1003, "cost_usd": 0.003498, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/e438904847ffe49f75825e85.md) |

</details>

<a id="row-9"></a>

<details>
<summary>기록 10 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-e4f5d3452c59b97161d9444547d7c66b7d43e140c9b5a31893bc0c17856a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "85e5e8ba36016c92456eb7b00cf66171f998e12b4be7ba418f96ab4a55da5377" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742649.3475711 | 전체 값 |
| `reserve` | 102039 | 전체 값 |
| `actual` | 5902 | 전체 값 |
| `created_at` | "2026-09-30T04:00:49.347577+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:01:00.983548+00:00" | 전체 값 |
| `node` | "s3_ceca" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/d594fa06461ed2cd19c7e63f.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8193, "tokens_out": 2870, "cost_usd": 0.0059019, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3b82ddc25f7c019005e545b6.md) |

</details>

<a id="row-10"></a>

<details>
<summary>기록 11 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-4679897664a9193bf4a856f94a689b37b53bab8f110e5a16a50ad38ca299" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "b945d73ccd4861c5083c1825de20a81c945b09243e5342f68f46f4d0e187d9aa" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742650.9963648 | 전체 값 |
| `reserve` | 101583 | 전체 값 |
| `actual` | 2776 | 전체 값 |
| `created_at` | "2026-09-30T04:00:50.996370+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:00:53.073526+00:00" | 전체 값 |
| `node` | "s3_sufield" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/8707cd69400e5d427ca5cc5b.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8016, "tokens_out": 309, "cost_usd": 0.0027756, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/0feaa0e473c738864f4f0e7d.md) |

</details>

<a id="row-11"></a>

<details>
<summary>기록 12 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-48616c5302936ba99c04ce4d80a02acba7d262aef13197ac54e93a566a4c" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "6e80764056287725e827fafae5dc1a0486af3c20212d8d2e29732e0f5191e820" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742652.670997 | 전체 값 |
| `reserve` | 101645 | 전체 값 |
| `actual` | 5602 | 전체 값 |
| `created_at` | "2026-09-30T04:00:52.671003+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:01:05.308885+00:00" | 전체 값 |
| `node` | "s3_resources" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/35d8934fa72e6301e30ed338.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7937, "tokens_out": 2684, "cost_usd": 0.0056019, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/30df1bd2ac85dc61e9b1186c.md) |

</details>

<a id="row-12"></a>

<details>
<summary>기록 13 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c7956c4f0b8682c011ece4d05ff548c62a4d6c45bf8636c73352f5f66f57" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "4304456d57f58d3b698064896b496ded4b00eb889b0ae0ee21a8157a940107e3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742665.2336376 | 전체 값 |
| `reserve` | 41327 | 전체 값 |
| `actual` | 3155 | 전체 값 |
| `created_at` | "2026-09-30T04:01:05.233642+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:01:09.730496+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/43ca08800eecd7cd6b598758.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 6954, "tokens_out": 890, "cost_usd": 0.0031542, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/cf29904808d3abac7332b53d.md) |

</details>

<a id="row-13"></a>

<details>
<summary>기록 14 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-60732446120732bd78ebfccdd187e0ca01420d387972cdaa98730d2fcf21" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-34e7956f50d143cabd2ac774fe607f25" | 전체 값 |
| `input_hash` | "caae079329d0530fabfbf45146c0c88c984088089e931cc6298d063ea521c1b6" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742677.2078831 | 전체 값 |
| `reserve` | 104742 | 전체 값 |
| `actual` | 6565 | 전체 값 |
| `created_at` | "2026-09-30T04:01:17.207888+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:01:28.206928+00:00" | 전체 값 |
| `node` | "s3_constraints" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/518c9d9d132367d94c1a9149.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 9570, "tokens_out": 3078, "cost_usd": 0.0065646, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7ea3c6b45f1d5b7115a9fcd9.md) |

</details>

<a id="row-14"></a>

<details>
<summary>기록 15 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2d28fa3e44d4c66a701bd010487fe4dbed14722e1408452b0dd98f7c9f2b" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "5111c6c6bf2cbdef693db2227af21ce43dad9235a5f63d6d0cfbf02821893cc3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742749.727662 | 전체 값 |
| `reserve` | 106981 | 전체 값 |
| `actual` | 8569 | 전체 값 |
| `created_at` | "2026-09-30T04:02:29.727668+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:02:49.335054+00:00" | 전체 값 |
| `node` | "s4_contradictions" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/2d10b3255e6ee3c110d510cc.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 10805, "tokens_out": 4439, "cost_usd": 0.008568300000000001, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d10518729f6aac2f3fc751a2.md) |

</details>

<a id="row-15"></a>

<details>
<summary>기록 16 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-25f850857b7c56b7d97140f04149a619fa0b44c39b8b9704a96f09815829" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "5f4c4e31f43848234db7b1f07bdcb0fd93fe2769f3f91f8db5d89f20ba885b63" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742751.3565524 | 전체 값 |
| `reserve` | 98605 | 전체 값 |
| `actual` | 3469 | 전체 값 |
| `created_at` | "2026-09-30T04:02:31.356558+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:02:38.286426+00:00" | 전체 값 |
| `node` | "s4_ifr" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ca7df8236f2c7ecef8f75cb2.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 6490, "tokens_out": 1268, "cost_usd": 0.0034685999999999996, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/aba624b012849e1fa0a948d6.md) |

</details>

<a id="row-16"></a>

<details>
<summary>기록 17 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2614b383ee7fce0563b15685bf0259266b4b425fc8424acf7dfc343d12ae" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "4ef4a3bb0a2ba29d9bfd42450ef28721f79114881e75f85658dbfe249564191e" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742753.0677054 | 전체 값 |
| `reserve` | 102708 | 전체 값 |
| `actual` | 4748 | 전체 값 |
| `created_at` | "2026-09-30T04:02:33.067711+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:02:42.243852+00:00" | 전체 값 |
| `node` | "s4_trimming" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/912a6ddb721579e779214f23.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8638, "tokens_out": 1797, "cost_usd": 0.0047478, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/02aff7c9b43f94a2dd90b3f8.md) |

</details>

<a id="row-17"></a>

<details>
<summary>기록 18 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-1f8d183469aef6c6461f5c86097068d29476ac31b51cb6dfee1767ed8b13" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "2ed665d39f961e5ba065349d55f110bca5de4321ae85cf985671c75c36308723" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742773.3995814 | 전체 값 |
| `reserve` | 50594 | 전체 값 |
| `actual` | 5246 | 전체 값 |
| `created_at` | "2026-09-30T04:02:53.399588+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:03:02.058806+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/db40d97a6cc3e95dc343aeb6.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 11520, "tokens_out": 1491, "cost_usd": 0.0052452, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7103032d8c4c9bcdeb8e2fb0.md) |

</details>

<a id="row-18"></a>

<details>
<summary>기록 19 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-66ee14e6df1ac42207564e39fb8b6b1fda5a24365a159ad30a7c7e7cce46" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "f3ef62c2909cef85610c929145c57b34fbf21e3dd2a1004317efd934583df321" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742787.701853 | 전체 값 |
| `reserve` | 116853 | 전체 값 |
| `actual` | 12012 | 전체 값 |
| `created_at` | "2026-09-30T04:03:07.701858+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:03:29.589649+00:00" | 전체 값 |
| `node` | "s4_contradictions" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/fe00e42e0699757d2e441420.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 15991, "tokens_out": 6012, "cost_usd": 0.012011699999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/6530390efab91b79cd225c1b.md) |

</details>

<a id="row-19"></a>

<details>
<summary>기록 20 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-7061fd35a016b2872791214a81c12fea3f858ffad50fe1574f624540d5ef" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "24f835b82ff53c68ca5bcd2c72936666b4858fa6993abe1a68e1ea267ab552e7" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742813.6311312 | 전체 값 |
| `reserve` | 53729 | 전체 값 |
| `actual` | 6502 | 전체 값 |
| `created_at` | "2026-09-30T04:03:33.631137+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:03:43.001944+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/da2caa5ba2314cd4381d1ed5.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 13155, "tokens_out": 2129, "cost_usd": 0.0065013, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d22a1fc51d825543242911e8.md) |

</details>

<a id="row-20"></a>

<details>
<summary>기록 21 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-188d821e2b857008361290675769dd9786af46b0c1dfa7733cc0258027f3" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-598fb131ae484180abf1e4ae394d3457" | 전체 값 |
| `input_hash` | "3c7ff5f9fe1206b369924d5d422cda1cbe63abd09853ffa6b322d0d056d1c016" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742827.2457387 | 전체 값 |
| `reserve` | 107436 | 전체 값 |
| `actual` | 4706 | 전체 값 |
| `created_at` | "2026-09-30T04:03:47.245744+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:03:53.402004+00:00" | 전체 값 |
| `node` | "s4_key_problem" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/a12309e2b7238b337ab8e22b.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 11041, "tokens_out": 1161, "cost_usd": 0.0047055, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d1ff2fef07a5b009f8a77314.md) |

</details>

<a id="row-21"></a>

<details>
<summary>기록 22 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-eb6b9c8067a10f2842561bcde7f0bf98cb0472d89f873b055b79224f4b6a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "6ce7fcb526cd02c50d1dc14229347837ec16f141fe2b44e705fa0ea92902ec14" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742897.0199292 | 전체 값 |
| `reserve` | 100025 | 전체 값 |
| `actual` | 2485 | 전체 값 |
| `created_at` | "2026-09-30T04:04:57.019936+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:01.949140+00:00" | 전체 값 |
| `node` | "s5_track_a_select" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/f6077e5f1c0f2bbd8cae0d55.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7185, "tokens_out": 274, "cost_usd": 0.0024843, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/914950a34681278a4461ce66.md) |

</details>

<a id="row-22"></a>

<details>
<summary>기록 23 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-7b7cf6ede7f045163aa848d7eb3bd16ec39e6c1867103e114c35772f845e" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "f8ac10b3edd5c127a5c9e71310439e789c04321b7f6156274f4d4ba3394f72f6" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742900.1576893 | 전체 값 |
| `reserve` | 101846 | 전체 값 |
| `actual` | 4978 | 전체 값 |
| `created_at` | "2026-09-30T04:05:00.157696+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:10.785696+00:00" | 전체 값 |
| `node` | "s5_track_b" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/2b2b690e01b7121c91ca395a.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8208, "tokens_out": 2096, "cost_usd": 0.0049776, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3ad6721aab3a7bb59df329cb.md) |

</details>

<a id="row-23"></a>

<details>
<summary>기록 24 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-05512c0144bbc9b1916fe54968d53ae863cf4ec6e79f2e0733bfdc01b7b1" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "c77c140f057807ef1ff8d585080c39f6339f1d3c693f008a3a3dc15499ed6ad0" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742901.8732808 | 전체 값 |
| `reserve` | 100021 | 전체 값 |
| `actual` | 7245 | 전체 값 |
| `created_at` | "2026-09-30T04:05:01.873286+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:20.086770+00:00" | 전체 값 |
| `node` | "s5_ariz_p1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/25d6fd1efbc5498b49dc4701.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7245, "tokens_out": 4226, "cost_usd": 0.0072447, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/5568383c621d595eb3e633f7.md) |

</details>

<a id="row-24"></a>

<details>
<summary>기록 25 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-1a7a16d5885f7914bc79649999678e7382da2e0f825c87ffb0bcf95679e2" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "439652c1ebfa48476ece7238f5bcaa5695713b18fa87cc781d6871e1810ccb34" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742907.7628014 | 전체 값 |
| `reserve` | 102031 | 전체 값 |
| `actual` | 6277 | 전체 값 |
| `created_at` | "2026-09-30T04:05:07.762806+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:22.839673+00:00" | 전체 값 |
| `node` | "s5_track_a" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/a3797e6da6a8bf8f44129da7.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8233, "tokens_out": 3172, "cost_usd": 0.0062763, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/460061c372f3a02f7c62fc1a.md) |

</details>

<a id="row-25"></a>

<details>
<summary>기록 26 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-a997cdd1d2fd95918448e85cee6ead83eddae19ed9a81210d4feca7e19a0" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "b68059cb2623e93281674c27d8bc385447c9f27376481bc263cb21cbde82a5e7" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742916.9170501 | 전체 값 |
| `reserve` | 101838 | 전체 값 |
| `actual` | 5264 | 전체 값 |
| `created_at` | "2026-09-30T04:05:16.917055+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:31.303281+00:00" | 전체 값 |
| `node` | "s5_track_b" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0239f8b4400f6ba31b3f2e40.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8193, "tokens_out": 2338, "cost_usd": 0.0052635, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/55aa0c632651fcc5dd85f2bc.md) |

</details>

<a id="row-26"></a>

<details>
<summary>기록 27 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-12b0482ccf629af17309947a1acff5f585d39bd9dca9d45c36b92395c3bb" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "ed27aaa217eb2d1566b9de8b0871152b392ec9b8f628cd3b9c1fa27eb04f1230" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742926.8589418 | 전체 값 |
| `reserve` | 109750 | 전체 값 |
| `actual` | 8591 | 전체 값 |
| `created_at` | "2026-09-30T04:05:26.858950+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:42.594412+00:00" | 전체 값 |
| `node` | "s5_ariz_p2" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/073e99448f51928ecaf3da07.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 12336, "tokens_out": 4075, "cost_usd": 0.008590799999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/00297e7f9311e2571a4aac6e.md) |

</details>

<a id="row-27"></a>

<details>
<summary>기록 28 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c1e1232a2f24602d6e0cd181f62f055c7698b725edf77ec3d6b8be08017d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "6989d39eb4a5e862e56fb05ec14f3cff08cad862db74e0efafabc9d4ee30d736" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742931.2386882 | 전체 값 |
| `reserve` | 100032 | 전체 값 |
| `actual` | 2520 | 전체 값 |
| `created_at` | "2026-09-30T04:05:31.238693+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:33.667705+00:00" | 전체 값 |
| `node` | "s5_track_a_select" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/16d3386901c8e250dd9bdfe2.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7191, "tokens_out": 302, "cost_usd": 0.0025197, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3d724c5e5407f23c71cf260d.md) |

</details>

<a id="row-28"></a>

<details>
<summary>기록 29 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-87688fa6d8a1dc869848107ead374e31973528858ff61cef69e190975da0" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "2639dc2b939d979905719f5945b6f71c8700d060e239b3215d4096da975a83aa" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742937.8450577 | 전체 값 |
| `reserve` | 102174 | 전체 값 |
| `actual` | 6732 | 전체 값 |
| `created_at` | "2026-09-30T04:05:37.845063+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:05:55.714682+00:00" | 전체 값 |
| `node` | "s5_track_a" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/e0ad7f8197897d21b4b3f780.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8313, "tokens_out": 3531, "cost_usd": 0.0067311, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/901402ed55f5cf820e81876b.md) |

</details>

<a id="row-29"></a>

<details>
<summary>기록 30 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-67405b6f569f7bee8ab681331a8c18733492a5b2e4e1c84b2bf7f9013936" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "217a5b27047cdb431a5465860b14c518e86268ca66195e22b966c451889874a5" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742947.02764 | 전체 값 |
| `reserve` | 112112 | 전체 값 |
| `actual` | 9782 | 전체 값 |
| `created_at` | "2026-09-30T04:05:47.027646+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:06:06.614993+00:00" | 전체 값 |
| `node` | "s5_ariz_p3" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/06f6e046c8fc097180b3d4a9.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13708, "tokens_out": 4724, "cost_usd": 0.0097812, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3745eb3888a75f1635136350.md) |

</details>

<a id="row-30"></a>

<details>
<summary>기록 31 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-70c570d46cb6cb76dd58cf4b4c2c3bfa9d1000b5d16d45f7e9d64beeb572" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "cd016a55b7340dfc87f735b7460fbe21055fc02a3f427b5b5d3cff9a7c2dde6d" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742966.170987 | 전체 값 |
| `reserve` | 99972 | 전체 값 |
| `actual` | 2451 | 전체 값 |
| `created_at` | "2026-09-30T04:06:06.170992+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:06:08.638126+00:00" | 전체 값 |
| `node` | "s5_track_a_select" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ce379f9c47d7083adae53a93.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7159, "tokens_out": 252, "cost_usd": 0.0024501, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d878cc811e3cc512f9ef8d36.md) |

</details>

<a id="row-31"></a>

<details>
<summary>기록 32 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-61157672535aa6dffd1132e837f8c818058b006290239dfc4b8033324e30" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "2447be6eb28e4d9546dd39dac56542ecfa8b9784370c0a4e3e00ce66f8f7f293" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742972.804993 | 전체 값 |
| `reserve` | 100767 | 전체 값 |
| `actual` | 13161 | 전체 값 |
| `created_at` | "2026-09-30T04:06:12.804998+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:06:52.887579+00:00" | 전체 값 |
| `node` | "s5_ariz_p4" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/1bd1ba7cbd016e55454b3773.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7608, "tokens_out": 9065, "cost_usd": 0.013160400000000001, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d0818c98383f893f835c8eb9.md) |

</details>

<a id="row-32"></a>

<details>
<summary>기록 33 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-5a80415715466275630d60fcbfa3a220af9c6cf2f28aea0aa83eb5f3c1c1" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "f12b94291644164037f38575278d0f92800b21f5a274f158cf1255790251e850" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790742974.503523 | 전체 값 |
| `reserve` | 102090 | 전체 값 |
| `actual` | 6888 | 전체 값 |
| `created_at` | "2026-09-30T04:06:14.503529+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:06:31.622233+00:00" | 전체 값 |
| `node` | "s5_track_a" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/cb5f04dc3cf1771349a0c0b7.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 8267, "tokens_out": 3673, "cost_usd": 0.0068877, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/8ca56096451fd4a37aace5a6.md) |

</details>

<a id="row-33"></a>

<details>
<summary>기록 34 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-0c0e490f096add167ce06b7828fbd033502632c84149a9201d78f50765d7" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "aa12674ee1fb2b98736c568c3e762db33a333d69330e01504b9eafde9e17a660" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743017.7630084 | 전체 값 |
| `reserve` | 141252 | 전체 값 |
| `actual` | 77195 | 전체 값 |
| `created_at` | "2026-09-30T04:06:57.763014+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:09:48.137733+00:00" | 전체 값 |
| `node` | "s5_ariz_p5" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ec7995ba529be64a2970a5e3.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 56676, "tokens_out": 50160, "cost_usd": 0.07719480000000001, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 2개 | [전체 값](payloads/95ca0f46981ed24d6e56d747.md) |

</details>

<a id="row-34"></a>

<details>
<summary>기록 35 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-787d899c0b965da6ea0955ea819c25ca2df00d2c29687ebe428368aa531f" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "a84de4066a71338c5afd972cd9da86cb2e4de5d0baefe0cd445a58ab00e3bdd3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743194.1240222 | 전체 값 |
| `reserve` | 118955 | 전체 값 |
| `actual` | 15068 | 전체 값 |
| `created_at` | "2026-09-30T04:09:54.124027+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:09:59.040695+00:00" | 전체 값 |
| `node` | "s5_ariz_p6" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/fc6c1906c582394a2435d53a.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 47081, "tokens_out": 786, "cost_usd": 0.0150675, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/fca629c56a050d70f9707e8c.md) |

</details>

<a id="row-35"></a>

<details>
<summary>기록 36 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-0353c7e66812db34ecc64e9f4a3014a3affa4c07c97a15f7d9b244a5ba5b" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "02501130324e3f0b435aa4c6fbe6a2200ece93bc70ff89f48e1cd2cf46314088" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743205.0257232 | 전체 값 |
| `reserve` | 101323 | 전체 값 |
| `actual` | 10365 | 전체 값 |
| `created_at` | "2026-09-30T04:10:05.025729+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:10:30.788271+00:00" | 전체 값 |
| `node` | "s5_ariz_p7" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/2d029b1037f76c5e293f9fda.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 7912, "tokens_out": 6659, "cost_usd": 0.0103644, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/728a832714b230d71e523ca0.md) |

</details>

<a id="row-36"></a>

<details>
<summary>기록 37 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-810b9f82fdb3aee459b69de39b895f8c85ce9624be89b6e7c8c6e761f2a4" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "99e16784a841c3ac42972d1bbe1ac34d327dbdb7eb7512ab1778f4f51827b21f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743252.9927144 | 전체 값 |
| `reserve` | 103512 | 전체 값 |
| `actual` | 9996 | 전체 값 |
| `created_at` | "2026-09-30T04:10:52.992719+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:11:18.258256+00:00" | 전체 값 |
| `node` | "s5_track_e" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/8f37ba1f3325aa7f23d4a154.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 9029, "tokens_out": 6072, "cost_usd": 0.0099951, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/5ebda2211870ca60693df9c0.md) |

</details>

<a id="row-37"></a>

<details>
<summary>기록 38 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2b30875317368c949d772f5c0933284f0510f47ff0c2270c024246c08813" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "1b6c56b936eec01755aee31168b8b088d4091e0463df571c8b69c46930b32558" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743254.7437077 | 전체 값 |
| `reserve` | 110469 | 전체 값 |
| `actual` | 8841 | 전체 값 |
| `created_at` | "2026-09-30T04:10:54.743713+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:11:11.593971+00:00" | 전체 값 |
| `node` | "s5_track_c" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/66adcdba8caad555ec769e44.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 12165, "tokens_out": 4326, "cost_usd": 0.0088407, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/8c76be6415bace73831848a4.md) |

</details>

<a id="row-38"></a>

<details>
<summary>기록 39 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c885f6a180b05d074507be66adc38dbb07eeb19d68352684721a415aec16" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "1b4dec628166383332343f51f1f5d15bed1a8973ed41279afb5f4e59fdb1dfab" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743257.8348927 | 전체 값 |
| `reserve` | 129357 | 전체 값 |
| `actual` | 10082 | 전체 값 |
| `created_at` | "2026-09-30T04:10:57.834899+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:11:12.665181+00:00" | 전체 값 |
| `node` | "s5_track_f" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/99d5241190aff2ae075d0dc7.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 21976, "tokens_out": 2907, "cost_usd": 0.010081199999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/47c7835f00aa8e3fd9c79c9c.md) |

</details>

<a id="row-39"></a>

<details>
<summary>기록 40 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-9e8a1ac02eb2c53001446fc7a919f36b19d1bcbb0e206d2cdb4786ab7a20" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "45b607e00b2e90571d8cee46d943874dea46c29c788df20bd33ec6383d5f94f3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743278.1906018 | 전체 값 |
| `reserve` | 110472 | 전체 값 |
| `actual` | 9253 | 전체 값 |
| `created_at` | "2026-09-30T04:11:18.190619+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:11:36.342212+00:00" | 전체 값 |
| `node` | "s5_track_c" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/a6a18e3dcb9e9c008c63adbe.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 12171, "tokens_out": 4668, "cost_usd": 0.0092529, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/2eedef69558268c8de1a6cb8.md) |

</details>

<a id="row-40"></a>

<details>
<summary>기록 41 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-f158f08b4c70c9f43f7d0f463c0ce78e2a704884cdee415b88f3dbf60783" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "fae7d73f248225654c321017b50e268928c8652118ef11cd473ec7ecd99e1244" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743313.7369637 | 전체 값 |
| `reserve` | 125031 | 전체 값 |
| `actual` | 8425 | 전체 값 |
| `created_at` | "2026-09-30T04:11:53.736970+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:12:05.115688+00:00" | 전체 값 |
| `node` | "s5_track_g" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/04a066a085bf580e36ae7e10.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 19689, "tokens_out": 2098, "cost_usd": 0.0084243, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/865889772682c747bd9737a7.md) |

</details>

<a id="row-41"></a>

<details>
<summary>기록 42 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-908f316573a241ef496c58ae94dee079fab8d53d3744c8d14af90f7542db" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "22d7b30ec5eef408f54de68bf8440d12175cbbdf7cd3998d158faec31cea8aad" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743317.4143498 | 전체 값 |
| `reserve` | 136925 | 전체 값 |
| `actual` | 11583 | 전체 값 |
| `created_at` | "2026-09-30T04:11:57.414367+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:12:12.719827+00:00" | 전체 값 |
| `node` | "s5_track_h" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/27f7eeceb34d07690ad76453.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 25752, "tokens_out": 3214, "cost_usd": 0.0115824, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/a3d9e75562336c6427954263.md) |

</details>

<a id="row-42"></a>

<details>
<summary>기록 43 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c412229a1afc16b2381cb4c8409337e15738cba131e62a14d6bec8e2774d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 55 | 전체 값 |
| `input_snapshot` | "snap-2a49a7b7a86e427093724c5ee4b0106a" | 전체 값 |
| `input_hash` | "63ebf1a376cd4d32f1d8e704361ac3e85853f3809e3f584e966d7a386aa4a35c" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743347.0705445 | 전체 값 |
| `reserve` | 322220 | 전체 값 |
| `actual` | 42628 | 전체 값 |
| `created_at` | "2026-09-30T04:12:27.070553+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:12:55.589462+00:00" | 전체 값 |
| `node` | "s5_merge" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/950e8de304ab1263f6995a11.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 117279, "tokens_out": 6203, "cost_usd": 0.0426273, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/4588ed011bc4d6104c1ce8ad.md) |

</details>

<a id="row-43"></a>

<details>
<summary>기록 44 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-d79718f56e2bed82b63009c0f6297fc31ac3a8a89445bf1243e3e8fd661f" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-5dba114002e041f6a5c116387a346dd5" | 전체 값 |
| `input_hash` | "90a56c03f9ba2cdc5f3efe60a06dc34e74b92d880d0e7bf28e7984da18814a87" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743534.1796427 | 전체 값 |
| `reserve` | 335525 | 전체 값 |
| `actual` | 46774 | 전체 값 |
| `created_at` | "2026-09-30T04:15:34.179648+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:15:58.949640+00:00" | 전체 값 |
| `node` | "s5_merge" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/d7b7f97e189a16fb917040a9.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 124575, "tokens_out": 7834, "cost_usd": 0.046773300000000004, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/b55c9c3c48856f953a8f56c5.md) |

</details>

<a id="row-44"></a>

<details>
<summary>기록 45 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-7516bec277efdf1fdd194622c670689a18c8ec9b5ac6f60b544b3cbe2e87" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-5dba114002e041f6a5c116387a346dd5" | 전체 값 |
| `input_hash` | "95b92acad077b63f124fb515094e12910f6019fb085290b9d91ae1af9eedfe4f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743565.6021705 | 전체 값 |
| `reserve` | 337168 | 전체 값 |
| `actual` | 46794 | 전체 값 |
| `created_at` | "2026-09-30T04:16:05.602175+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:16:28.572952+00:00" | 전체 값 |
| `node` | "s5_merge" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0ce40296528b849bfa73de64.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 125440, "tokens_out": 7635, "cost_usd": 0.046794, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/6a9279701033a3a7fb1655be.md) |

</details>

<a id="row-45"></a>

<details>
<summary>기록 46 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2d3e81d6cac68bc28226c369b7dbe00a1804a66b22bd5a0e38d0fbcd3291" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "880cfd92a05300f941a8f997f728764c24d990c97654de38fa5fd719071f8278" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743692.2821133 | 전체 값 |
| `reserve` | 164187 | 전체 값 |
| `actual` | 26705 | 전체 값 |
| `created_at` | "2026-09-30T04:18:12.282119+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:18:54.348363+00:00" | 전체 값 |
| `node` | "s6_concept" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/716382c56c8549f51d678382.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 39422, "tokens_out": 12398, "cost_usd": 0.026704199999999997, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/fcf0acb086e3edb61a66a5ef.md) |

</details>

<a id="row-46"></a>

<details>
<summary>기록 47 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-255a5d8f1dd63462876a1a4fc12479bafeedc0aa796536cd475eb88c5dd5" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "549898bcc69344adf5f3c7a68e62f4ec3314ad02bc1a5489e587aa80880d425e" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743694.2366452 | 전체 값 |
| `reserve` | 138633 | 전체 값 |
| `actual` | 13219 | 전체 값 |
| `created_at` | "2026-09-30T04:18:14.236653+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:18:33.900744+00:00" | 전체 값 |
| `node` | "s6_concept" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/cf749dceec913253e7ac958e.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 26415, "tokens_out": 4412, "cost_usd": 0.013218899999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/b1ea3be0ca02b175ac12fa12.md) |

</details>

<a id="row-47"></a>

<details>
<summary>기록 48 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-3e888950030808b46c26bbe2dc600fc3412f3db61f5ed9206fea94ccf160" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "d7238d4eb6c1eadac02619196369b7ad4b7f857c5e1cf227f21f1baa9ef01f11" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743697.9246118 | 전체 값 |
| `reserve` | 161437 | 전체 값 |
| `actual` | 27340 | 전체 값 |
| `created_at` | "2026-09-30T04:18:17.924617+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:19:02.272980+00:00" | 전체 값 |
| `node` | "s6_concept" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/cc98a1bb06e80133329e34df.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 38055, "tokens_out": 13269, "cost_usd": 0.027339299999999997, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3c7ba1f50336db8c56ae24f0.md) |

</details>

<a id="row-48"></a>

<details>
<summary>기록 49 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-75d79981bca7fe8a0c9311e2dcf9e04ef1ba1f430e81175c38ba24e74115" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "ec463c7b8969e50df250fc56f196171585d2c7b5f00837a53d3d42840291a8dd" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743758.5140946 | 전체 값 |
| `reserve` | 69264 | 전체 값 |
| `actual` | 8160 | 전체 값 |
| `created_at` | "2026-09-30T04:19:18.514101+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:19:27.445316+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/9fa4b4f7259a3b1c9c533d0e.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 20786, "tokens_out": 1603, "cost_usd": 0.008159399999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/245db05c2185f690d28e6ca6.md) |

</details>

<a id="row-49"></a>

<details>
<summary>기록 50 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-efcbbcc57d368e9530caea4c0f4210c7a1db3c43fdda0f3f9b5866de7b4d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "8857b8e64315154ade4cdb8ac09fcb46cc2a94b1928d87228592740a0fedab18" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743777.7142582 | 전체 값 |
| `reserve` | 66384 | 전체 값 |
| `actual` | 7773 | 전체 값 |
| `created_at` | "2026-09-30T04:19:37.714263+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:19:46.330731+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0c8d2ba277588d49c02787b4.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 19323, "tokens_out": 1646, "cost_usd": 0.0077721, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/6a137b756d9ac7b8fb8834b6.md) |

</details>

<a id="row-50"></a>

<details>
<summary>기록 51 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-9fea385c0b523896b0426ffa6e2e3cd883cacbfaa5530bb7408b9502144c" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "2063db0a9d5d90d2bb5002af8f7579c5c449887ee46ae85814cd0a8bf4f83ceb" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743798.5520627 | 전체 값 |
| `reserve` | 62175 | 전체 값 |
| `actual` | 6377 | 전체 값 |
| `created_at` | "2026-09-30T04:19:58.552067+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:20:03.928094+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/873c9b6f64cbce84338d09f7.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 17176, "tokens_out": 1020, "cost_usd": 0.0063768, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3cefbc2a4656295f4f7168e1.md) |

</details>

<a id="row-51"></a>

<details>
<summary>기록 52 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-28eb94c8337dff3b995ab1f65ea8b2c239c98307b05c54470eaafd1f5b3f" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "9b36a187a44ab0ace5218ee8fbc4e1e322f42f0fdeca57fdda37f1b9c54bf2f5" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743815.2671762 | 전체 값 |
| `reserve` | 67394 | 전체 값 |
| `actual` | 8065 | 전체 값 |
| `created_at` | "2026-09-30T04:20:15.267182+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:20:23.966094+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/40a12a14850c83cb76d866ee.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 19713, "tokens_out": 1792, "cost_usd": 0.0080643, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/c2ef66a9a0a53e786dda83e9.md) |

</details>

<a id="row-52"></a>

<details>
<summary>기록 53 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-643597ff594e3331a4fcd79bdc6494cee6b654c7acd4b6099cac1a613587" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "f24af5d980a3d3c407b610b6344d85237ea40ccdcfb681565739cbb944185ef3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743839.1041813 | 전체 값 |
| `reserve` | 63270 | 전체 값 |
| `actual` | 7026 | 전체 값 |
| `created_at` | "2026-09-30T04:20:39.104187+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:20:46.265794+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/9c7105706649a91423f8c493.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 17822, "tokens_out": 1399, "cost_usd": 0.0070254, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/8af98fd57d1566ee4f3d7020.md) |

</details>

<a id="row-53"></a>

<details>
<summary>기록 54 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-4c40bff126eb88b65b50046eb6ae3733a5352e5a6716616ae937b52e7db3" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "0b988842d5e9a07da3fcc44ba39f6e38e4b51eea0364955950f3c63536974602" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743860.5342157 | 전체 값 |
| `reserve` | 69513 | 전체 값 |
| `actual` | 9084 | 전체 값 |
| `created_at` | "2026-09-30T04:21:00.534220+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:21:11.964796+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/fe71ec788bbecbfd3561051e.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 21018, "tokens_out": 2315, "cost_usd": 0.009083399999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/397c6ad32c0f125867426717.md) |

</details>

<a id="row-54"></a>

<details>
<summary>기록 55 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-7320ddeff65976f99a5632867e351282f7a739d133e3561a5d7105de7642" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "53a6998f3da06ec2ebd8a366947c6cb9712f190102199b9e6287ecc0b06fe15f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743883.4136684 | 전체 값 |
| `reserve` | 65640 | 전체 값 |
| `actual` | 7704 | 전체 값 |
| `created_at` | "2026-09-30T04:21:23.413675+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:21:32.952546+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/175fc8c727b12bc273d7cb41.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 18988, "tokens_out": 1673, "cost_usd": 0.007704, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3e9831416fc1f738b4de6da8.md) |

</details>

<a id="row-55"></a>

<details>
<summary>기록 56 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2ac9e64017116bcf5fd851ba2a64aa4b42205c86818b0388ecd5babb7f0a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-6526e07589224012b018bd03a2638fdf" | 전체 값 |
| `input_hash` | "0dab009ddfd95b56e382cafee8a360bb3e648ba6057aad12f9dea7f3fd569db8" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743908.340006 | 전체 값 |
| `reserve` | 62218 | 전체 값 |
| `actual` | 6774 | 전체 값 |
| `created_at` | "2026-09-30T04:21:48.340011+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:21:55.556803+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0b7bb162e9a1b91a35751a4b.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 17093, "tokens_out": 1371, "cost_usd": 0.006773100000000001, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/63e70b78b17ab4f25d11e8d1.md) |

</details>

<a id="row-56"></a>

<details>
<summary>기록 57 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c47c7889f7064bfa6d66de4232718d16131c0253fa20a3c03725f1f22f54" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "e1add4db4cccf36e6951cbcef396630efc84ba6cb4f14be9d7ae1e8d3854264d" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790743990.1434898 | 전체 값 |
| `reserve` | 121460 | 전체 값 |
| `actual` | 9865 | 전체 값 |
| `created_at` | "2026-09-30T04:23:10.143494+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:23:27.599761+00:00" | 전체 값 |
| `node` | "ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_0" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/2108d90d05aa406d9b751d42.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 18222, "tokens_out": 3665, "cost_usd": 0.0098646, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/526560bdbd8f68c75ec34587.md) |

</details>

<a id="row-57"></a>

<details>
<summary>기록 58 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-c238ad9996c60f8e8ca2282a7d322c5e9decbbb7d69d715881ecc2ffe4e8" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "953facf15e7ed3724418bdfac6ef9928a86b8a1eb34c1cb19b55359d42b5cc52" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744014.2473032 | 전체 값 |
| `reserve` | 62106 | 전체 값 |
| `actual` | 6502 | 전체 값 |
| `created_at` | "2026-09-30T04:23:34.247308+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:23:39.668564+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ee4256a1d09544b0b389a418.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 17292, "tokens_out": 1095, "cost_usd": 0.0065016, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/197af6d5f58c37c66707caec.md) |

</details>

<a id="row-58"></a>

<details>
<summary>기록 59 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-e815817f51c7da9045247ba6b248c505c58ff3cd05033247e475d15a6ec8" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "478bd291bc380079c59c12041d048e4864a54fd35c49e35072e164ff9a9ad743" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744040.327019 | 전체 값 |
| `reserve` | 121460 | 전체 값 |
| `actual` | 9174 | 전체 값 |
| `created_at` | "2026-09-30T04:24:00.327024+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:24:15.909980+00:00" | 전체 값 |
| `node` | "ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/7e7f2c523a46eddd6f42ddb4.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 18222, "tokens_out": 3089, "cost_usd": 0.0091734, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/28ad1df64fc38547b650d3c9.md) |

</details>

<a id="row-59"></a>

<details>
<summary>기록 60 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-de01642c4a6ba1f049d589819211ba353bd46238c9dea70cff9e83df0876" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "3f7e7ce0b9ece8d98f02b6069519f6ddd67b2e842e5cf670ba2a989e3ac8ee18" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744062.5343068 | 전체 값 |
| `reserve` | 61168 | 전체 값 |
| `actual` | 6554 | 전체 값 |
| `created_at` | "2026-09-30T04:24:22.534312+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:24:28.957600+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/707849b133348a7113c6c60f.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 16745, "tokens_out": 1275, "cost_usd": 0.006553499999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d6ca99ed9b8b487b5bca805d.md) |

</details>

<a id="row-60"></a>

<details>
<summary>기록 61 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-6cbd68f470f5381b8bd7f6b1983b511e5abdc13787e48d44b259c6832d1e" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "f5264d03c8732d85307d6ee657ec3f4a419c7e9eb73ebbf772f2c0fbc67a1fa0" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744087.768069 | 전체 값 |
| `reserve` | 127872 | 전체 값 |
| `actual` | 11882 | 전체 값 |
| `created_at` | "2026-09-30T04:24:47.768075+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:25:04.727081+00:00" | 전체 값 |
| `node` | "ax_repair_gap-f705ac45d5656e38b0c6b5e9_0" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/56cea335ba3ea6bc3f2bc3c9.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 21514, "tokens_out": 4523, "cost_usd": 0.0118818, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/68005ef1001f606ad96563f6.md) |

</details>

<a id="row-61"></a>

<details>
<summary>기록 62 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-6756d8a19b733b4fe4c1a8547c711e4df46adbc4c6b032f394a525b3b885" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "e9dd29a555a5e0bb6990c08b047d895fea1747bf9a14046b028666f830437a8f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744110.5433526 | 전체 값 |
| `reserve` | 72329 | 전체 값 |
| `actual` | 8598 | 전체 값 |
| `created_at` | "2026-09-30T04:25:10.543358+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:25:19.053702+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/767c89bcaeb048da41519212.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 23028, "tokens_out": 1408, "cost_usd": 0.008598, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/0e361b1f3f5b9cd9dd7945f3.md) |

</details>

<a id="row-62"></a>

<details>
<summary>기록 63 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-a703932eb882a1b3d4e8cc61813719245814c186691a868671d26656a41c" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "5c064c7cad394a549d3c52c0c16a82d5fd76f54c9206c49ed73b6db4d57ba825" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744135.616398 | 전체 값 |
| `reserve` | 127872 | 전체 값 |
| `actual` | 14311 | 전체 값 |
| `created_at` | "2026-09-30T04:25:35.616403+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:25:58.266852+00:00" | 전체 값 |
| `node` | "ax_repair_gap-f705ac45d5656e38b0c6b5e9_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/7fd59bee10a768a50b0caa35.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 21514, "tokens_out": 6547, "cost_usd": 0.0143106, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/925361ffb4581163738cc915.md) |

</details>

<a id="row-63"></a>

<details>
<summary>기록 64 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-319944d610b87f6b2d33c4e9fcbbff76e16566c6f273f92f64d89f7c9089" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-083679b2e69f4895b5ca55dd287c6839" | 전체 값 |
| `input_hash` | "c3463947111ff8ca4af4751c4b23df14ee2518860654c7a1d89ec42103f965c3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744164.6736183 | 전체 값 |
| `reserve` | 71299 | 전체 값 |
| `actual` | 8557 | 전체 값 |
| `created_at` | "2026-09-30T04:26:04.673623+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:26:12.279070+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/10cf7f7f4e116709f56fa422.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 22199, "tokens_out": 1581, "cost_usd": 0.0085569, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/9d7ac34c3debcbe3ee084f79.md) |

</details>

<a id="row-64"></a>

<details>
<summary>기록 65 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-433083973487651917535eec5a4924b1f073b4b98314d9bcd76e20b91a3a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "53494db6e2f056cbfc6831e58a76e5275246290cf73fced6dc7495569ee28051" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744216.888886 | 전체 값 |
| `reserve` | 97982 | 전체 값 |
| `actual` | 2904 | 전체 값 |
| `created_at` | "2026-09-30T04:26:56.888891+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:06.585406+00:00" | 전체 값 |
| `node` | "s7_gate_4" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/97f113d9012148a5d8fc4a71.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5734, "tokens_out": 986, "cost_usd": 0.0029034, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/8898b44dd5ee6b32cd62684e.md) |

</details>

<a id="row-65"></a>

<details>
<summary>기록 66 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-a9169bd17aee35793963890002c83cdf33b0e2392785954655eb14cc722e" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "cc12042207cf0a42a52a5157ef65794fd658b599a83b6f4d84fba1b85807871f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744219.1224978 | 전체 값 |
| `reserve` | 97473 | 전체 값 |
| `actual` | 2982 | 전체 값 |
| `created_at` | "2026-09-30T04:26:59.122503+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:06.724227+00:00" | 전체 값 |
| `node` | "s7_gate_3" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/02914e0b09f07a76e5e0d2a4.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5485, "tokens_out": 1113, "cost_usd": 0.0029811, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3de28d80896df83880e9597d.md) |

</details>

<a id="row-66"></a>

<details>
<summary>기록 67 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-b896788cdca0986380073eba09585d7f665c3e8152e1f80f94cfcfdc5ab3" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "e69020f561cc6b04f983fd367fc54e57afebfbb80ff514416ddd8cfea5452eb1" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744221.0517917 | 전체 값 |
| `reserve` | 98349 | 전체 값 |
| `actual` | 2888 | 전체 값 |
| `created_at` | "2026-09-30T04:27:01.051799+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:06.931859+00:00" | 전체 값 |
| `node` | "s7_gate_2" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/10f1cc9f225771e9ad2caaf9.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5930, "tokens_out": 924, "cost_usd": 0.0028878000000000003, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/aa37cba9cfa49419cf9d77d5.md) |

</details>

<a id="row-67"></a>

<details>
<summary>기록 68 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-66149a335a59a37b21a2c6a1c115fef4e27d20625e35b2d11b01c7bd1e16" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "8d2bd921a0c3bdc3caae6feac14b76dea558e14038f7927510cd8862d21d53a3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744226.518081 | 전체 값 |
| `reserve` | 98789 | 전체 값 |
| `actual` | 3059 | 전체 값 |
| `created_at` | "2026-09-30T04:27:06.518087+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:10.678036+00:00" | 전체 값 |
| `node` | "s7_gate_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ff41da7b7ede5d9678b27209.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 6147, "tokens_out": 1012, "cost_usd": 0.0030584999999999996, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/dbac900f7361469c36574304.md) |

</details>

<a id="row-68"></a>

<details>
<summary>기록 69 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2013132a6413a376d2015c3c511bfcee628c528c720dda62fc6c04b1bed5" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "8226643d1e47f7d4be448eac41ee6c967059c9ab10dd7f5a2063b974d1069db8" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744245.201695 | 전체 값 |
| `reserve` | 96883 | 전체 값 |
| `actual` | 2723 | 전체 값 |
| `created_at` | "2026-09-30T04:27:25.201700+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:35.256261+00:00" | 전체 값 |
| `node` | "s7_gate_7" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/383acdfb05196ee6dc46d110.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5176, "tokens_out": 975, "cost_usd": 0.0027228, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/22c71d9a2762fdd21d28eee4.md) |

</details>

<a id="row-69"></a>

<details>
<summary>기록 70 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-56c179cfc48b0ede2d3b8ddc821902f4b1511d9da1d539f118575c21f94a" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "74dfd651c178443a86cce21d0a4d091fbe48c2243a99f24f57f99a2615482132" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744248.5564768 | 전체 값 |
| `reserve` | 97238 | 전체 값 |
| `actual` | 2740 | 전체 값 |
| `created_at` | "2026-09-30T04:27:28.556485+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:35.626776+00:00" | 전체 값 |
| `node` | "s7_gate_6" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/b77d5c0782efa74ebd840974.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5404, "tokens_out": 932, "cost_usd": 0.0027396, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/378e48d76504c62accf88328.md) |

</details>

<a id="row-70"></a>

<details>
<summary>기록 71 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-225d69a61036b2e52c4c1eaedd9b4eb4253d27f7df8d9b365900581fa156" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "08834cee8721fff4abe02bb5f9294f1a64ffa5e050ec8ba424f5010fb495e9fc" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744252.889148 | 전체 값 |
| `reserve` | 97280 | 전체 값 |
| `actual` | 2755 | 전체 값 |
| `created_at` | "2026-09-30T04:27:32.889152+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:37.055455+00:00" | 전체 값 |
| `node` | "s7_gate_8" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0cad6b828ddbf6a1d1dad8df.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5390, "tokens_out": 948, "cost_usd": 0.0027546, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/69e816ad89a6f4a1cd202698.md) |

</details>

<a id="row-71"></a>

<details>
<summary>기록 72 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-fba37ec4c9090e7a260ff78167ad327401eb831e5f1f9100b5bbcad06088" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "386b7946435f15727bdbbabe730d811bd688cd0edd71a8924ced2f12bd26583f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744255.145718 | 전체 값 |
| `reserve` | 97642 | 전체 값 |
| `actual` | 2913 | 전체 값 |
| `created_at` | "2026-09-30T04:27:35.145724+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:39.881406+00:00" | 전체 값 |
| `node` | "s7_gate_5" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/aa5ae8398c7b7af842770d2c.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5579, "tokens_out": 1032, "cost_usd": 0.0029121, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/9ea4f3edf32eb76d65735656.md) |

</details>

<a id="row-72"></a>

<details>
<summary>기록 73 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-1ddec92b7d7159732d76f182a2a5b343ca16c85b5f4b08de6696c7efb624" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "551c1b350ad84c62657b5dc0e04ab0c502c49eb680320d414293dd07c58e8d2b" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744267.3857317 | 전체 값 |
| `reserve` | 96962 | 전체 값 |
| `actual` | 2741 | 전체 값 |
| `created_at` | "2026-09-30T04:27:47.385737+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:52.190490+00:00" | 전체 값 |
| `node` | "s7_gate_9" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/12ac9ffcdc4c8ddc944b2a50.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5236, "tokens_out": 975, "cost_usd": 0.0027408, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7929dccaf77f3390dea4b26a.md) |

</details>

<a id="row-73"></a>

<details>
<summary>기록 74 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2018a941b69de9ae2698444bd6776313a247c9eb715e470d109c911b3136" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 56 | 전체 값 |
| `input_snapshot` | "snap-bd95c2b311eb491491880ba9bb20c269" | 전체 값 |
| `input_hash` | "1ba0cc0308debe322850d4f6466cbe96b2e58aa92e53c75461564cea7f0fc9ee" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744270.5684083 | 전체 값 |
| `reserve` | 97128 | 전체 값 |
| `actual` | 2704 | 전체 값 |
| `created_at` | "2026-09-30T04:27:50.568415+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:27:54.752583+00:00" | 전체 값 |
| `node` | "s7_gate_10" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/7e4143669281244a6468ddee.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 5300, "tokens_out": 928, "cost_usd": 0.0027036, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/91ea8b02128931db026ca3f9.md) |

</details>

<a id="row-74"></a>

<details>
<summary>기록 75 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-8e775beffd34727b0289949205ccc06cc6967c6def86187bff92d7705636" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "e4968ce4d0a47129ad46dec3dcdb3c9bbcf30de38820a866f00d65e26b29c9a1" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744512.4853246 | 전체 값 |
| `reserve` | 126890 | 전체 값 |
| `actual` | 12018 | 전체 값 |
| `created_at` | "2026-09-30T04:31:52.485331+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:32:12.152700+00:00" | 전체 값 |
| `node` | "ax_repair_gap-26e0db61185158a1836b4b6b_0" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/c89f2f4b327329bf7bd10234.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 20994, "tokens_out": 4766, "cost_usd": 0.0120174, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/3ba610b1b6b23f14b8777cc1.md) |

</details>

<a id="row-75"></a>

<details>
<summary>기록 76 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-4d59e2d4177e5dce93098b51643cf44fc49668f8551984dbe35ae16b61fc" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "e0ecffdeff8fefdee6f92a94af462efb7c10082e14ba19580137d4d016b89844" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744559.5979426 | 전체 값 |
| `reserve` | 70870 | 전체 값 |
| `actual` | 8564 | 전체 값 |
| `created_at` | "2026-09-30T04:32:39.597949+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:32:47.454412+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/60fa055b51034b718ca2fa9d.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 21889, "tokens_out": 1664, "cost_usd": 0.008563499999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/5c3335f18c79eaa06c7d35fc.md) |

</details>

<a id="row-76"></a>

<details>
<summary>기록 77 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-a9cc82dcf73639720d1f0b34dc3a7214b9fa1bc1e3ff12e86fc837ea0340" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "5d0ea8c516ce68a420d9ffa2a1122e0cecb310967b9ee00491f2dbf61864cb15" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744597.1213686 | 전체 값 |
| `reserve` | 126890 | 전체 값 |
| `actual` | 9935 | 전체 값 |
| `created_at` | "2026-09-30T04:33:17.121375+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:33:29.675531+00:00" | 전체 값 |
| `node` | "ax_repair_gap-26e0db61185158a1836b4b6b_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/aeb7bf82d3a638771b142b3d.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 20994, "tokens_out": 3030, "cost_usd": 0.009934199999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/34b01613c3eb627d5d4befed.md) |

</details>

<a id="row-77"></a>

<details>
<summary>기록 78 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-cc15ffc14846556ca4a4121fd1894b432c56449ac34ff7285e1eab1cd2f4" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "a97f84a0264752cc2c8dea6b15215dbac144021431ad17c6cea5e1db5af5aa9a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744628.281931 | 전체 값 |
| `reserve` | 67358 | 전체 값 |
| `actual` | 7617 | 전체 값 |
| `created_at` | "2026-09-30T04:33:48.281937+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:33:54.737054+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/1759123fa05f4b91d5be6a5a.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 20197, "tokens_out": 1298, "cost_usd": 0.0076167, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/c46adc8b4944b0cbf2632f2b.md) |

</details>

<a id="row-78"></a>

<details>
<summary>기록 79 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-9d5425e6cb7616eca9c456fea2f869d52595e44011f9e5d178bea5a537a7" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "827e3b33c4d42eb02cac7a5adadd94165e29f269ab9fc703dc3130ba44471bcb" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744710.0262408 | 전체 값 |
| `reserve` | 125790 | 전체 값 |
| `actual` | 10076 | 전체 값 |
| `created_at` | "2026-09-30T04:35:10.026248+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:35:24.780640+00:00" | 전체 값 |
| `node` | "ax_repair_gap-ab829f5d78d52e0eaeb7afea_0" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/74687a2fb49a001587080fb2.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 20440, "tokens_out": 3286, "cost_usd": 0.0100752, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/a330c81a95b4b4c4373ff215.md) |

</details>

<a id="row-79"></a>

<details>
<summary>기록 80 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-2af69ca787931e1011e851e6606f298458f097821c8e910690c0e935f2c4" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "5806c04c94249778557b266391d3a62f59bb555f4da48c0b3f50780f27513673" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744744.6783442 | 전체 값 |
| `reserve` | 65366 | 전체 값 |
| `actual` | 7293 | 전체 값 |
| `created_at` | "2026-09-30T04:35:44.678350+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:35:51.678864+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/28855474c2649a378d8bf930.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 18921, "tokens_out": 1347, "cost_usd": 0.007292699999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/c242e2c46324821406879946.md) |

</details>

<a id="row-80"></a>

<details>
<summary>기록 81 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-a3820767839185ee8333935d411ca988c7c2807ce71534f6551910e6c5aa" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "672a592cb521176c6cfcae31f144dd134ad5053dfb3fb1faa6b74e8b91cfd80a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744798.216926 | 전체 값 |
| `reserve` | 125790 | 전체 값 |
| `actual` | 10246 | 전체 값 |
| `created_at` | "2026-09-30T04:36:38.216932+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:36:53.039943+00:00" | 전체 값 |
| `node` | "ax_repair_gap-ab829f5d78d52e0eaeb7afea_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/d3b8dab2b318a75b73230820.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 20440, "tokens_out": 3428, "cost_usd": 0.0102456, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/351c99330697fc1ea8c20265.md) |

</details>

<a id="row-81"></a>

<details>
<summary>기록 82 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-73551b14ceab30e8bf368088fcebf6bfc6991e8a9af663ceb12e8d060e3d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-9be9f0ee5dba4e77aff67c21a391ffff" | 전체 값 |
| `input_hash` | "dd0f33a56a36305602797a2b0557bcf57cf35ba4c9e339847e2ef05084f2aa9a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790744830.0973332 | 전체 값 |
| `reserve` | 65736 | 전체 값 |
| `actual` | 7347 | 전체 값 |
| `created_at` | "2026-09-30T04:37:10.097340+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:37:17.250300+00:00" | 전체 값 |
| `node` | "independent_verifier" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/4a7af19f0e04ac4e597624c4.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 19118, "tokens_out": 1343, "cost_usd": 0.007346999999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/30ef6eb7cfe3a7a41ecdfa8a.md) |

</details>

<a id="row-82"></a>

<details>
<summary>기록 83 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-04b554ec43d937c9afb1c886b8a6bb4f9f0884338e283c864fbd687d2f71" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-379b943f2b7249068666ade186a93f7a" | 전체 값 |
| `input_hash` | "1cf815e7da43d282bbe34459996365289d1b614abb0a7413bdcc3d3ab72e89e0" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745072.161235 | 전체 값 |
| `reserve` | 115558 | 전체 값 |
| `actual` | 7818 | 전체 값 |
| `created_at` | "2026-09-30T04:41:12.161240+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:41:28.327143+00:00" | 전체 값 |
| `node` | "s9_evidence_match_0" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/ad8261e025a75c782e64425c.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13319, "tokens_out": 3185, "cost_usd": 0.0078177, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/da2b56467793c7e9a6df72f7.md) |

</details>

<a id="row-83"></a>

<details>
<summary>기록 84 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-9f800905ce00e1dad9b2c86b3838716f3e4eb8ee8e64f7d321d3ccbb3aeb" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-379b943f2b7249068666ade186a93f7a" | 전체 값 |
| `input_hash` | "ae5d198002c2b3312837949b3a529ab02243e7a70c258b34f8379e9b079916da" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745101.388883 | 전체 값 |
| `reserve` | 115393 | 전체 값 |
| `actual` | 6669 | 전체 값 |
| `created_at` | "2026-09-30T04:41:41.388887+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:41:53.678152+00:00" | 전체 값 |
| `node` | "s9_evidence_match_1" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/1c285fb2f39781b9ecc63da7.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13259, "tokens_out": 2242, "cost_usd": 0.0066681, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/f5c0b8ecb9dcf0c7ccd3363c.md) |

</details>

<a id="row-84"></a>

<details>
<summary>기록 85 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-5d001a97f9e27c99e41d5da6af6e567baf2dfe52d85a68feab67f886fa3d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-379b943f2b7249068666ade186a93f7a" | 전체 값 |
| `input_hash` | "fb826e3690311aff715aeaaeaec2e70afdb1689e7c4cc9c62efee886be0d7546" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745133.225736 | 전체 값 |
| `reserve` | 115384 | 전체 값 |
| `actual` | 6813 | 전체 값 |
| `created_at` | "2026-09-30T04:42:13.225743+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:42:28.409924+00:00" | 전체 값 |
| `node` | "s9_evidence_match_2" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/081b56bab0a2fc4d474e7fb1.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13255, "tokens_out": 2363, "cost_usd": 0.0068121, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7639d9bfb06fa74a79b76914.md) |

</details>

<a id="row-85"></a>

<details>
<summary>기록 86 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-52455f41692048d593c7f55ec1a6a885b9fb48d182c040864c5b8f1d7c70" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-379b943f2b7249068666ade186a93f7a" | 전체 값 |
| `input_hash` | "c10647cd2fb37d0e613c046b48daf6059b5b88c966760d283381161a5f238d87" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745177.2002642 | 전체 값 |
| `reserve` | 115066 | 전체 값 |
| `actual` | 5712 | 전체 값 |
| `created_at` | "2026-09-30T04:42:57.200271+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:43:05.371327+00:00" | 전체 값 |
| `node` | "s9_evidence_match_3" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/c3d38ba9a254233a6a320bd7.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13074, "tokens_out": 1491, "cost_usd": 0.0057114, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/b0d50ff7e212b83ad2af02c1.md) |

</details>

<a id="row-86"></a>

<details>
<summary>기록 87 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-45a5bd564acc34f59cd610dc8974eb64c00e2415c26cd8dff5be3d0ba8bc" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "fbce03cdd9398bf535e8dcdc674cb15ce35c56533de0347989eb696daffe8ab3" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745271.2008393 | 전체 값 |
| `reserve` | 62186 | 전체 값 |
| `actual` | 3618 | 전체 값 |
| `created_at` | "2026-09-30T04:44:31.200844+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:44:37.628017+00:00" | 전체 값 |
| `node` | "s8_persona_factory" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/1c9f432bbfceb5df9ed7e1de.md) |
| `result_usage` | {"tier": "T1", "model": "deepseek-flash", "tokens_in": 7494, "tokens_out": 1141, "cost_usd": 0.0036173999999999998, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/1b83751412fd969de5d7797a.md) |

</details>

<a id="row-87"></a>

<details>
<summary>기록 88 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-b39fbcac51eff877b8ee13816441e3a908711ba182a009cb5c87e32527e7" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "a13c6cefe00f119f6c910d0ac75b2e6c304609f418af8f4a67658eb3524221ce" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745314.7237232 | 전체 값 |
| `reserve` | 136384 | 전체 값 |
| `actual` | 12158 | 전체 값 |
| `created_at` | "2026-09-30T04:45:14.723729+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:45:51.110516+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/b828df71d85b3c6ff635d406.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25238, "tokens_out": 3822, "cost_usd": 0.0121578, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/ec105bb2696989b22cd4ce2d.md) |

</details>

<a id="row-88"></a>

<details>
<summary>기록 89 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-d93dc77d3edc9d8f0a6dee6f8ebcf97bf6a6d1b86067f670197cacb83742" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "565469503fdc4056535b49a49ae81b94bc8df8bf4348833a8cdf65add19b3d20" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745327.5257533 | 전체 값 |
| `reserve` | 136313 | 전체 값 |
| `actual` | 12043 | 전체 값 |
| `created_at` | "2026-09-30T04:45:27.525770+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:45:51.227119+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/e8254090a3f87e6785dd0ac3.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25202, "tokens_out": 3735, "cost_usd": 0.012042599999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/2af44809e40dcba5d43c77cf.md) |

</details>

<a id="row-89"></a>

<details>
<summary>기록 90 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-bc2c8e79ddac5aaca2be8b441fcc3e52e84d7a2af00b2539dd90ba201862" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "e1286b0bb5eeba76dfc652392ddf3cb71e78623ab7b7d78c1d829e10da87cbca" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745339.6987808 | 전체 값 |
| `reserve` | 136299 | 전체 값 |
| `actual` | 12331 | 전체 값 |
| `created_at` | "2026-09-30T04:45:39.698786+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:45:58.920408+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/b68f5cd2fcc69460dfb0083a.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25203, "tokens_out": 3975, "cost_usd": 0.012330899999999999, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/4e15319ba01f49c0b21d53dc.md) |

</details>

<a id="row-90"></a>

<details>
<summary>기록 91 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-33c3aaef7999a292b8a35ba0eefea694135d3fc6ade6ca23d3e8bb613352" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "4bb9f55531c2bb0888ba4c6f2493b74d482650e0ddb912aa37fb71b0b7afa157" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745350.5566766 | 전체 값 |
| `reserve` | 136296 | 전체 값 |
| `actual` | 11659 | 전체 값 |
| `created_at` | "2026-09-30T04:45:50.556682+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:46:09.240449+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/0b7301bec85ac4aa3be5c6cb.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25189, "tokens_out": 3418, "cost_usd": 0.0116583, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/2491661241158f125439087f.md) |

</details>

<a id="row-91"></a>

<details>
<summary>기록 92 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-1a93d7c32a971d656641f70e08deeb5f90f36d183669cd9410e0db58e6cb" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "08987745b79d4411e8edbf8415b5330fa6b3d129b0c1c8aed4d6c0e66c1af1ed" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745406.8463814 | 전체 값 |
| `reserve` | 136353 | 전체 값 |
| `actual` | 10818 | 전체 값 |
| `created_at` | "2026-09-30T04:46:46.846386+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:47:19.611608+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/7158fe03b9e67982ea3afe46.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25209, "tokens_out": 2712, "cost_usd": 0.0108171, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/ef74a52c68c9dbb7988fc8f8.md) |

</details>

<a id="row-92"></a>

<details>
<summary>기록 93 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-13c1df5928b052144ce0fb07129e254f9108c57841bccefb4c5de4dd8b32" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "68f752b0afb2796e63808c117bec5c31cd76653317490371cadb560204559596" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745419.323452 | 전체 값 |
| `reserve` | 136281 | 전체 값 |
| `actual` | 10521 | 전체 값 |
| `created_at` | "2026-09-30T04:46:59.323457+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:47:19.742157+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/108c02a73a20389d860e9d4b.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25173, "tokens_out": 2474, "cost_usd": 0.010520700000000001, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/ffa3b135335f03eed0b4b9ef.md) |

</details>

<a id="row-93"></a>

<details>
<summary>기록 94 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-e60304da2093962eb36a35ebf56eee40cde2f256b17dac984eaab375959b" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "ac0ef4811c22be63f719bdf6b544e415ba15259aa4944cfe413d9bf63ea3424a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745430.6004958 | 전체 값 |
| `reserve` | 136265 | 전체 값 |
| `actual` | 10473 | 전체 값 |
| `created_at` | "2026-09-30T04:47:10.600502+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:47:23.531068+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/65ebbd337488b9852f58d617.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25160, "tokens_out": 2437, "cost_usd": 0.0104724, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/538923d4cc587925fccaed4a.md) |

</details>

<a id="row-94"></a>

<details>
<summary>기록 95 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-623d8eeb04bc16ed3b2fa1366f9d38f80063781de8b5e2861cc0dd2c457e" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "5c061d8b24d5f224288e6107e17f023de63b72b0c79ddcc8493dddbe4f50ff67" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745439.4789174 | 전체 값 |
| `reserve` | 136268 | 전체 값 |
| `actual` | 10265 | 전체 값 |
| `created_at` | "2026-09-30T04:47:19.478923+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:47:30.807452+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/31377f21604cbcb37bf63f04.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25174, "tokens_out": 2260, "cost_usd": 0.0102642, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/7792efabeaf79cab7074c702.md) |

</details>

<a id="row-95"></a>

<details>
<summary>기록 96 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-1863fa93ae440c880e857aa113742d54c33d9d1aa6b41d167f201c8c0df4" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "8c4b71d9c4e76f5a1d47003c0fc189ea057354a22224059c1a4e431f52f1aa85" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745512.0431976 | 전체 값 |
| `reserve` | 136414 | 전체 값 |
| `actual` | 10322 | 전체 값 |
| `created_at` | "2026-09-30T04:48:32.043204+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:48:53.359566+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/47eb5dfd9c0525d8b162735c.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25253, "tokens_out": 2288, "cost_usd": 0.0103215, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/cd803c943628a9a56c7e8f9c.md) |

</details>

<a id="row-96"></a>

<details>
<summary>기록 97 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-418484586f7acc806666a3a6f166e3aedf5878fe6520e665272f28d2354c" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "0fadbe527f061c0e88650149ed1cf3e2a00345f53bd0162910e20f282f0e8a1a" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745532.8980494 | 전체 값 |
| `reserve` | 136424 | 전체 값 |
| `actual` | 11795 | 전체 값 |
| `created_at` | "2026-09-30T04:48:52.898055+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:49:08.354234+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/d75693c1a85f36f8430b4703.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25260, "tokens_out": 3514, "cost_usd": 0.0117948, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/72f05f59b91bd8417321daf0.md) |

</details>

<a id="row-97"></a>

<details>
<summary>기록 98 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-f253d058d68bab2e0c7ed2970f86f934109c7f8e48723099267bdcc56c3f" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "a1b433fdef2a2cde1dc15d022220c72581471d72e1649ac3bfff24a50f75d07f" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745770.9263434 | 전체 값 |
| `reserve` | 136383 | 전체 값 |
| `actual` | 10274 | 전체 값 |
| `created_at` | "2026-09-30T04:52:50.926350+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:53:03.143886+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/a6cc97cd5aa8352883a4cc23.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25224, "tokens_out": 2255, "cost_usd": 0.0102732, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/d9a76ac2c257aad4a592f5d6.md) |

</details>

<a id="row-98"></a>

<details>
<summary>기록 99 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-fe2b47a69d2fbe25e7445b2e77a0b548a8ec09f46e03fed812f26fd56518" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "551d8955adb2f04666f4d039a72193eb4f2b6f99338c033b8fa0cd2edf14c4c1" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745779.9153044 | 전체 값 |
| `reserve` | 136393 | 전체 값 |
| `actual` | 10708 | 전체 값 |
| `created_at` | "2026-09-30T04:52:59.915311+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:53:13.991305+00:00" | 전체 값 |
| `node` | "s8_review_independent" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/b70002f75c611422297799b8.md) |
| `result_usage` | {"tier": "T3", "model": "deepseek-flash", "tokens_in": 25231, "tokens_out": 2615, "cost_usd": 0.0107073, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/95b46312bd0e450825a541fd.md) |

</details>

<a id="row-99"></a>

<details>
<summary>기록 100 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-5e67663a09cdb6d9e1eff5544277c78f348baabf768f77dee36a15d45f6d" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "7fa1d8f5046db8082a93506e39b118ed1f6d84507ed9e0e884c94f0488c681bd" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745857.4986372 | 전체 값 |
| `reserve` | 111564 | 전체 값 |
| `actual` | 7354 | 전체 값 |
| `created_at` | "2026-09-30T04:54:17.498644+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:54:32.382641+00:00" | 전체 값 |
| `node` | "s8_rank" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/231abb0e8ae1564d2cb427a3.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 13361, "tokens_out": 2788, "cost_usd": 0.0073539, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/408ca1ca03096f2babbbb7f9.md) |

</details>

<a id="row-100"></a>

<details>
<summary>기록 101 · 전체 저장값</summary>

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `task_id` | "task-e27241035908f1fba291d125857029dfb77234e545786047230f4e90b9a6" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `epoch` | 57 | 전체 값 |
| `input_snapshot` | "snap-e37db405a2774f429721bf92198e2c89" | 전체 값 |
| `input_hash` | "6eb47d01ebf2e6eb02fe3f1d7533e3eb0fd010a43b86a3d73de8cad9e2709208" | 전체 값 |
| `status` | "COMPLETED" | 전체 값 |
| `fence` | 1 | 전체 값 |
| `lease_until` | 1790745912.273816 | 전체 값 |
| `reserve` | 113400 | 전체 값 |
| `actual` | 8038 | 전체 값 |
| `created_at` | "2026-09-30T04:55:12.273822+00:00" | 전체 값 |
| `settled_at` | "2026-09-30T04:55:24.981982+00:00" | 전체 값 |
| `node` | "s8_rank" | 전체 값 |
| `attempts` | 배열 1개 | [전체 값](payloads/c88c2210b58eabd1b47712c0.md) |
| `result_usage` | {"tier": "T2", "model": "deepseek-flash", "tokens_in": 14363, "tokens_out": 3107, "cost_usd": 0.0080373, "raw_error": ""} | 전체 값 |
| `pricing_metadata` | {"cost_basis": "configured_token_rates"} | 전체 값 |
| `provider_attempts` | 배열 1개 | [전체 값](payloads/2e731a61af18a41ecd131a77.md) |

</details>
