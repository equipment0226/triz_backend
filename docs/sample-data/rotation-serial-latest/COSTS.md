# 원본 비용과 정정 비용

[사례 개요](README.md)

원본 task.actual, Step 비용, token usage와 기존 산출물은 실행 당시 기록으로 보존했습니다. 정정액은 별도로 저장된 COST_RESTATEMENT_APPLIED 이벤트의 task_adjustments.after_microusd를 반영합니다. 아래 합계는 이번 재실행 task만 포함하며 프로젝트 누적액과 구분됩니다.

분석 실행 코드: `5ce8ec233b3d58d2005530a4e9b3113f5fc235f2`. 완료 후 정정 계산 코드: `3fd16f06180d533f682956a010331063cd636cf9`. 정정 시각: `2026-09-30T05:13:07.954796+00:00`.

| 범위 | USD |
|---|---|
| 이번 재실행 · 실행 당시 task.actual | 0.971468 |
| 이번 재실행 · 정정 반영 | 0.390118 |
| 프로젝트 전체 · 조회 시 누적 | 3.11851 |

## task별 비교

| task | Stage | node | 원본 USD | 정정 반영 USD | 근거 이벤트 |
|---|---|---|---|---|---|
| task-96d416cce2bffe30dd2ae2456a32e931d4ee959fe581a89f3d5b3d19053a | s0_research | s0_deep_dive | 0.003818 | 0.001608 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-e5b5930949907f20ccf0c63c3c2cd1e47357438d0bcb2b429d12ace6dfd6 | s0_research | s0_deep_dive | 0.003798 | 0.001561 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-3d529c33e8f69919a81303d37dcf45669b54e6b3670770c4736b8e691615 | s1_intake | s1_extract | 0.007246 | 0.003322 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-837950718d92c18bc1a0cdc86c546849b36c92ea38865a897dd2d6a975cc | s2_confirm | s2_candidates | 0.003654 | 0.001789 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-5d2586003cbcc1c9d5ba23cb9eba75c7c192f49ee41fe752517628b2c12a | s3_analyze | s3_nine_windows | 0.003877 | 0.001675 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-b66ca81e3aa1e434fd8c3c97cd3e09dfc3a3d21dddab071aa68cc68afc7a | s3_analyze | s3_function_model | 0.006641 | 0.003057 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-64040edcccc9df3c485881d5accf1cc3b1a36feb7c3471408c85398864dc | s3_analyze | independent_verifier | 0.003646 | 0.001823 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-007809559d7bf02ec457b97d1b6835b037108bffbb7867afbfc6452c963d | s3_analyze | s3_function_model | 0.008096 | 0.002787 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-3d0a1f1983f91870b39b33e2549fa3ecf368afe68707d397f61c09c07ada | s3_analyze | independent_verifier | 0.003498 | 0.001731 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-e4f5d3452c59b97161d9444547d7c66b7d43e140c9b5a31893bc0c17856a | s3_analyze | s3_ceca | 0.005902 | 0.002688 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-4679897664a9193bf4a856f94a689b37b53bab8f110e5a16a50ad38ca299 | s3_analyze | s3_sufield | 0.002776 | 0.001125 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-48616c5302936ba99c04ce4d80a02acba7d262aef13197ac54e93a566a4c | s3_analyze | s3_resources | 0.005602 | 0.002538 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c7956c4f0b8682c011ece4d05ff548c62a4d6c45bf8636c73352f5f66f57 | s3_analyze | independent_verifier | 0.003155 | 0.001578 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-60732446120732bd78ebfccdd187e0ca01420d387972cdaa98730d2fcf21 | s3_analyze | s3_constraints | 0.006565 | 0.003019 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2d28fa3e44d4c66a701bd010487fe4dbed14722e1408452b0dd98f7c9f2b | s4_define | s4_contradictions | 0.008569 | 0.004040 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-25f850857b7c56b7d97140f04149a619fa0b44c39b8b9704a96f09815829 | s4_define | s4_ifr | 0.003469 | 0.001434 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2614b383ee7fce0563b15685bf0259266b4b425fc8424acf7dfc343d12ae | s4_define | s4_trimming | 0.004748 | 0.002073 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-1f8d183469aef6c6461f5c86097068d29476ac31b51cb6dfee1767ed8b13 | s4_define | independent_verifier | 0.005246 | 0.002623 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-66ee14e6df1ac42207564e39fb8b6b1fda5a24365a159ad30a7c7e7cce46 | s4_define | s4_contradictions | 0.012012 | 0.004426 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-7061fd35a016b2872791214a81c12fea3f858ffad50fe1574f624540d5ef | s4_define | independent_verifier | 0.006502 | 0.003082 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-188d821e2b857008361290675769dd9786af46b0c1dfa7733cc0258027f3 | s4_define | s4_key_problem | 0.004706 | 0.002052 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-eb6b9c8067a10f2842561bcde7f0bf98cb0472d89f873b055b79224f4b6a | s5_solve | s5_track_a_select | 0.002485 | 0.000942 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-7b7cf6ede7f045163aa848d7eb3bd16ec39e6c1867103e114c35772f845e | s5_solve | s5_track_b | 0.004978 | 0.002188 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-05512c0144bbc9b1916fe54968d53ae863cf4ec6e79f2e0733bfdc01b7b1 | s5_solve | s5_ariz_p1 | 0.007245 | 0.003322 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-1a7a16d5885f7914bc79649999678e7382da2e0f825c87ffb0bcf95679e2 | s5_solve | s5_track_a | 0.006277 | 0.002838 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-a997cdd1d2fd95918448e85cee6ead83eddae19ed9a81210d4feca7e19a0 | s5_solve | s5_track_b | 0.005264 | 0.002312 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-12b0482ccf629af17309947a1acff5f585d39bd9dca9d45c36b92395c3bb | s5_solve | s5_ariz_p2 | 0.008591 | 0.003995 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c1e1232a2f24602d6e0cd181f62f055c7698b725edf77ec3d6b8be08017d | s5_solve | s5_track_a_select | 0.002520 | 0.000940 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-87688fa6d8a1dc869848107ead374e31973528858ff61cef69e190975da0 | s5_solve | s5_track_a | 0.006732 | 0.003046 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-67405b6f569f7bee8ab681331a8c18733492a5b2e4e1c84b2bf7f9013936 | s5_solve | s5_ariz_p3 | 0.009782 | 0.004590 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-70c570d46cb6cb76dd58cf4b4c2c3bfa9d1000b5d16d45f7e9d64beeb572 | s5_solve | s5_track_a_select | 0.002451 | 0.000906 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-61157672535aa6dffd1132e837f8c818058b006290239dfc4b8033324e30 | s5_solve | s5_ariz_p4 | 0.013161 | 0.006261 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-5a80415715466275630d60fcbfa3a220af9c6cf2f28aea0aa83eb5f3c1c1 | s5_solve | s5_track_a | 0.006888 | 0.003124 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-0c0e490f096add167ce06b7828fbd033502632c84149a9201d78f50765d7 | s5_solve | s5_ariz_p5 | 0.077195 | 0.034139 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-787d899c0b965da6ea0955ea819c25ca2df00d2c29687ebe428368aa531f | s5_solve | s5_ariz_p6 | 0.015068 | 0.007233 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-0353c7e66812db34ecc64e9f4a3014a3affa4c07c97a15f7d9b244a5ba5b | s5_solve | s5_ariz_p7 | 0.010365 | 0.004863 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-810b9f82fdb3aee459b69de39b895f8c85ce9624be89b6e7c8c6e761f2a4 | s5_solve | s5_track_e | 0.009996 | 0.004697 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2b30875317368c949d772f5c0933284f0510f47ff0c2270c024246c08813 | s5_solve | s5_track_c | 0.008841 | 0.004120 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c885f6a180b05d074507be66adc38dbb07eeb19d68352684721a415aec16 | s5_solve | s5_track_f | 0.010082 | 0.004740 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-9e8a1ac02eb2c53001446fc7a919f36b19d1bcbb0e206d2cdb4786ab7a20 | s5_solve | s5_track_c | 0.009253 | 0.004307 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-f158f08b4c70c9f43f7d0f463c0ce78e2a704884cdee415b88f3dbf60783 | s5_solve | s5_track_g | 0.008425 | 0.003912 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-908f316573a241ef496c58ae94dee079fab8d53d3744c8d14af90f7542db | s5_solve | s5_track_h | 0.011583 | 0.005491 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c412229a1afc16b2381cb4c8409337e15738cba131e62a14d6bec8e2774d | s5_solve | s5_merge | 0.042628 | 0.021013 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-d79718f56e2bed82b63009c0f6297fc31ac3a8a89445bf1243e3e8fd661f | s5_solve | s5_merge | 0.046774 | 0.006171 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-7516bec277efdf1fdd194622c670689a18c8ec9b5ac6f60b544b3cbe2e87 | s5_solve | s5_merge | 0.046794 | 0.006162 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2d3e81d6cac68bc28226c369b7dbe00a1804a66b22bd5a0e38d0fbcd3291 | s6_concept | s6_concept | 0.026705 | 0.013052 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-255a5d8f1dd63462876a1a4fc12479bafeedc0aa796536cd475eb88c5dd5 | s6_concept | s6_concept | 0.013219 | 0.004728 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-3e888950030808b46c26bbe2dc600fc3412f3db61f5ed9206fea94ccf160 | s6_concept | s6_concept | 0.027340 | 0.011789 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-75d79981bca7fe8a0c9311e2dcf9e04ef1ba1f430e81175c38ba24e74115 | s6_concept | independent_verifier | 0.008160 | 0.004080 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-efcbbcc57d368e9530caea4c0f4210c7a1db3c43fdda0f3f9b5866de7b4d | s6_concept | independent_verifier | 0.007773 | 0.003887 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-9fea385c0b523896b0426ffa6e2e3cd883cacbfaa5530bb7408b9502144c | s6_concept | independent_verifier | 0.006377 | 0.003189 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-28eb94c8337dff3b995ab1f65ea8b2c239c98307b05c54470eaafd1f5b3f | s6_concept | independent_verifier | 0.008065 | 0.004033 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-643597ff594e3331a4fcd79bdc6494cee6b654c7acd4b6099cac1a613587 | s6_concept | independent_verifier | 0.007026 | 0.003513 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-4c40bff126eb88b65b50046eb6ae3733a5352e5a6716616ae937b52e7db3 | s6_concept | independent_verifier | 0.009084 | 0.004542 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-7320ddeff65976f99a5632867e351282f7a739d133e3561a5d7105de7642 | s6_concept | independent_verifier | 0.007704 | 0.003852 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2ac9e64017116bcf5fd851ba2a64aa4b42205c86818b0388ecd5babb7f0a | s6_concept | independent_verifier | 0.006774 | 0.003387 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c47c7889f7064bfa6d66de4232718d16131c0253fa20a3c03725f1f22f54 | s7_gate | ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_0 | 0.009865 | 0.004632 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-c238ad9996c60f8e8ca2282a7d322c5e9decbbb7d69d715881ecc2ffe4e8 | s7_gate | independent_verifier | 0.006502 | 0.003251 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-e815817f51c7da9045247ba6b248c505c58ff3cd05033247e475d15a6ec8 | s7_gate | ax_repair_gap-bd9a38e4e0b0f6aea7fe0620_1 | 0.009174 | 0.001934 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-de01642c4a6ba1f049d589819211ba353bd46238c9dea70cff9e83df0876 | s7_gate | independent_verifier | 0.006554 | 0.003277 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-6cbd68f470f5381b8bd7f6b1983b511e5abdc13787e48d44b259c6832d1e | s7_gate | ax_repair_gap-f705ac45d5656e38b0c6b5e9_0 | 0.011882 | 0.005490 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-6756d8a19b733b4fe4c1a8547c711e4df46adbc4c6b032f394a525b3b885 | s7_gate | independent_verifier | 0.008598 | 0.004299 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-a703932eb882a1b3d4e8cc61813719245814c186691a868671d26656a41c | s7_gate | ax_repair_gap-f705ac45d5656e38b0c6b5e9_1 | 0.014311 | 0.004014 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-319944d610b87f6b2d33c4e9fcbbff76e16566c6f273f92f64d89f7c9089 | s7_gate | independent_verifier | 0.008557 | 0.004279 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-433083973487651917535eec5a4924b1f073b4b98314d9bcd76e20b91a3a | s7_gate | s7_gate_4 | 0.002904 | 0.001433 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-a9169bd17aee35793963890002c83cdf33b0e2392785954655eb14cc722e | s7_gate | s7_gate_3 | 0.002982 | 0.001152 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-b896788cdca0986380073eba09585d7f665c3e8152e1f80f94cfcfdc5ab3 | s7_gate | s7_gate_2 | 0.002888 | 0.001106 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-66149a335a59a37b21a2c6a1c115fef4e27d20625e35b2d11b01c7bd1e16 | s7_gate | s7_gate_1 | 0.003059 | 0.001191 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2013132a6413a376d2015c3c511bfcee628c528c720dda62fc6c04b1bed5 | s7_gate | s7_gate_7 | 0.002723 | 0.001023 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-56c179cfc48b0ede2d3b8ddc821902f4b1511d9da1d539f118575c21f94a | s7_gate | s7_gate_6 | 0.002740 | 0.001032 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-225d69a61036b2e52c4c1eaedd9b4eb4253d27f7df8d9b365900581fa156 | s7_gate | s7_gate_8 | 0.002755 | 0.001039 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-fba37ec4c9090e7a260ff78167ad327401eb831e5f1f9100b5bbcad06088 | s7_gate | s7_gate_5 | 0.002913 | 0.001118 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-1ddec92b7d7159732d76f182a2a5b343ca16c85b5f4b08de6696c7efb624 | s7_gate | s7_gate_9 | 0.002741 | 0.001032 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2018a941b69de9ae2698444bd6776313a247c9eb715e470d109c911b3136 | s7_gate | s7_gate_10 | 0.002704 | 0.001014 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-8e775beffd34727b0289949205ccc06cc6967c6def86187bff92d7705636 | s8_references | ax_repair_gap-26e0db61185158a1836b4b6b_0 | 0.012018 | 0.005558 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-4d59e2d4177e5dce93098b51643cf44fc49668f8551984dbe35ae16b61fc | s8_references | independent_verifier | 0.008564 | 0.004282 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-a9cc82dcf73639720d1f0b34dc3a7214b9fa1bc1e3ff12e86fc837ea0340 | s8_references | ax_repair_gap-26e0db61185158a1836b4b6b_1 | 0.009935 | 0.001901 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-cc15ffc14846556ca4a4121fd1894b432c56449ac34ff7285e1eab1cd2f4 | s8_references | independent_verifier | 0.007617 | 0.003809 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-9d5425e6cb7616eca9c456fea2f869d52595e44011f9e5d178bea5a537a7 | s8_references | ax_repair_gap-ab829f5d78d52e0eaeb7afea_0 | 0.010076 | 0.004587 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-2af69ca787931e1011e851e6606f298458f097821c8e910690c0e935f2c4 | s8_references | independent_verifier | 0.007293 | 0.003647 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-a3820767839185ee8333935d411ca988c7c2807ce71534f6551910e6c5aa | s8_references | ax_repair_gap-ab829f5d78d52e0eaeb7afea_1 | 0.010246 | 0.002150 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-73551b14ceab30e8bf368088fcebf6bfc6991e8a9af663ceb12e8d060e3d | s8_references | independent_verifier | 0.007347 | 0.003674 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-04b554ec43d937c9afb1c886b8a6bb4f9f0884338e283c864fbd687d2f71 | s8_references | s9_evidence_match_0 | 0.007818 | 0.003608 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-9f800905ce00e1dad9b2c86b3838716f3e4eb8ee8e64f7d321d3ccbb3aeb | s8_references | s9_evidence_match_1 | 0.006669 | 0.003015 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-5d001a97f9e27c99e41d5da6af6e567baf2dfe52d85a68feab67f886fa3d | s8_references | s9_evidence_match_2 | 0.006813 | 0.003087 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-52455f41692048d593c7f55ec1a6a885b9fb48d182c040864c5b8f1d7c70 | s8_references | s9_evidence_match_3 | 0.005712 | 0.002536 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-45a5bd564acc34f59cd610dc8974eb64c00e2415c26cd8dff5be3d0ba8bc | s8_evaluate | s8_persona_factory | 0.003618 | 0.001508 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-b39fbcac51eff877b8ee13816441e3a908711ba182a009cb5c87e32527e7 | s8_evaluate | s8_review_independent | 0.012158 | 0.006079 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-d93dc77d3edc9d8f0a6dee6f8ebcf97bf6a6d1b86067f670197cacb83742 | s8_evaluate | s8_review_independent | 0.012043 | 0.006022 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-bc2c8e79ddac5aaca2be8b441fcc3e52e84d7a2af00b2539dd90ba201862 | s8_evaluate | s8_review_independent | 0.012331 | 0.006166 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-33c3aaef7999a292b8a35ba0eefea694135d3fc6ade6ca23d3e8bb613352 | s8_evaluate | s8_review_independent | 0.011659 | 0.005830 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-1a93d7c32a971d656641f70e08deeb5f90f36d183669cd9410e0db58e6cb | s8_evaluate | s8_review_independent | 0.010818 | 0.002229 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-13c1df5928b052144ce0fb07129e254f9108c57841bccefb4c5de4dd8b32 | s8_evaluate | s8_review_independent | 0.010521 | 0.002081 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-e60304da2093962eb36a35ebf56eee40cde2f256b17dac984eaab375959b | s8_evaluate | s8_review_independent | 0.010473 | 0.002057 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-623d8eeb04bc16ed3b2fa1366f9d38f80063781de8b5e2861cc0dd2c457e | s8_evaluate | s8_review_independent | 0.010265 | 0.001953 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-1863fa93ae440c880e857aa113742d54c33d9d1aa6b41d167f201c8c0df4 | s8_evaluate | s8_review_independent | 0.010322 | 0.005161 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-418484586f7acc806666a3a6f166e3aedf5878fe6520e665272f28d2354c | s8_evaluate | s8_review_independent | 0.011795 | 0.005898 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-f253d058d68bab2e0c7ed2970f86f934109c7f8e48723099267bdcc56c3f | s8_evaluate | s8_review_independent | 0.010274 | 0.001957 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-fe2b47a69d2fbe25e7445b2e77a0b548a8ec09f46e03fed812f26fd56518 | s8_evaluate | s8_review_independent | 0.010708 | 0.002174 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-5e67663a09cdb6d9e1eff5544277c78f348baabf768f77dee36a15d45f6d | s8_evaluate | s8_rank | 0.007354 | 0.003376 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |
| task-e27241035908f1fba291d125857029dfb77234e545786047230f4e90b9a6 | s8_evaluate | s8_rank | 0.008038 | 0.002062 | cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991 |

## 저장된 정정 근거

### cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991

| 필드 | 저장값 / 미리보기 | 상세 |
|---|---|---|
| `event_id` | "cost-restatement-5de95ce3a3ac35352432fca643444c15f7d199f165614991" | 전체 값 |
| `run_id` | "run-baa72a38ef40c8c63155ffc7a1dd25ee" | 전체 값 |
| `event_type` | "COST_RESTATEMENT_APPLIED" | 전체 값 |
| `payload` | 객체 · after_cost, after_microusd, applied_at, basis, before_cost, before_microusd … | [전체 값](payloads/3088d7a11aac19ee8d195496.md) |
| `created_at` | "2026-09-30T05:13:07.962460+00:00" | 전체 값 |


가격 기준과 계산식은 [수집·비용 기준](PROVENANCE.md), 원본 usage는 [모델 호출 원장](CALLS.md)을 확인합니다.
