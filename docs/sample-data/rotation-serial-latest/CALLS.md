# 모델 호출과 실제 비용

[사례 개요](README.md)

`ax_tasks`와 `ax_task_attempts`에서 확인한 최신 회차 task 95건입니다. Step과 task 사이에 직접 외래키가 없으므로 병렬 호출을 시간만으로 특정 Step에 귀속시키지 않았습니다. Stage는 실행 이벤트 구간으로 연결했습니다. `reserve`는 예약, `actual`은 정산이며 단위는 microUSD입니다.

| KST 생성 | 실제 Stage | node | epoch | 정산 USD | task 상세 |
|---|---|---|---|---|---|
| 06:47:22 | s0_research | s0_deep_dive | 47 | 0.003326 | [task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2](#task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2) |
| 06:49:49 | s0_research | s0_deep_dive | 48 | 0.003407 | [task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8](#task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8) |
| 06:50:47 | s1_intake | s1_extract | 48 | 0.006371 | [task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a](#task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a) |
| 06:51:11 | s1_intake | s1_clarify | 48 | 0.002294 | [task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067](#task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067) |
| 06:52:58 | s1_intake | s1_extract | 49 | 0.006206 | [task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7](#task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7) |
| 06:53:58 | s2_confirm | s2_candidates | 49 | 0.003377 | [task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1](#task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1) |
| 07:07:35 | s3_analyze | s3_nine_windows | 50 | 0.003713 | [task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761](#task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761) |
| 07:07:50 | s3_analyze | s3_function_model | 50 | 0.005999 | [task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f](#task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f) |
| 07:08:06 | s3_analyze | independent_verifier | 50 | 0.003168 | [task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a](#task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a) |
| 07:08:21 | s3_analyze | s3_resources | 50 | 0.005607 | [task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc](#task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc) |
| 07:08:23 | s3_analyze | s3_ceca | 50 | 0.005799 | [task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d](#task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d) |
| 07:08:24 | s3_analyze | s3_sufield | 50 | 0.002450 | [task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799](#task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799) |
| 07:08:38 | s3_analyze | independent_verifier | 50 | 0.002880 | [task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af](#task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af) |
| 07:08:48 | s3_analyze | s3_constraints | 50 | 0.005961 | [task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da](#task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da) |
| 07:09:49 | s4_define | s4_ifr | 50 | 0.002899 | [task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6](#task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6) |
| 07:09:51 | s4_define | s4_contradictions | 50 | 0.006366 | [task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a](#task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a) |
| 07:09:52 | s4_define | s4_trimming | 50 | 0.003967 | [task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc](#task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc) |
| 07:10:08 | s4_define | independent_verifier | 50 | 0.004642 | [task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d](#task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d) |
| 07:10:21 | s4_define | s4_key_problem | 50 | 0.003386 | [task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce](#task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce) |
| 07:11:16 | s5_solve | s5_ariz_p1 | 50 | 0.006753 | [task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265](#task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265) |
| 07:11:17 | s5_solve | s5_track_a_select | 50 | 0.002308 | [task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9](#task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9) |
| 07:11:19 | s5_solve | s5_track_b | 50 | 0.004593 | [task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e](#task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e) |
| 07:11:27 | s5_solve | s5_track_a | 50 | 0.006283 | [task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c](#task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c) |
| 07:11:37 | s5_solve | s5_track_b | 50 | 0.004547 | [task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008](#task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008) |
| 07:11:38 | s5_solve | s5_ariz_p2 | 50 | 0.008450 | [task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043](#task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043) |
| 07:11:48 | s5_solve | s5_track_a_select | 50 | 0.002259 | [task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1](#task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1) |
| 07:11:55 | s5_solve | s5_track_a | 50 | 0.006104 | [task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3](#task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3) |
| 07:12:00 | s5_solve | s5_ariz_p3 | 50 | 0.009143 | [task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808](#task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808) |
| 07:12:13 | s5_solve | s5_track_a_select | 50 | 0.002282 | [task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08](#task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08) |
| 07:12:19 | s5_solve | s5_track_a | 50 | 0.006026 | [task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b](#task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b) |
| 07:12:22 | s5_solve | s5_ariz_p4 | 50 | 0.008759 | [task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f](#task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f) |
| 07:12:50 | s5_solve | s5_ariz_p5 | 50 | 0.023206 | [task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5](#task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5) |
| 07:13:46 | s5_solve | s5_ariz_p6 | 50 | 0.010834 | [task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97](#task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97) |
| 07:13:55 | s5_solve | s5_ariz_p7 | 50 | 0.018422 | [task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f](#task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f) |
| 07:14:56 | s5_solve | s5_track_f | 50 | 0.007113 | [task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a](#task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a) |
| 07:14:58 | s5_solve | s5_track_e | 50 | 0.006908 | [task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7](#task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7) |
| 07:14:59 | s5_solve | s5_track_c | 50 | 0.009089 | [task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4](#task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4) |
| 07:15:19 | s5_solve | s5_track_c | 50 | 0.009985 | [task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a](#task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a) |
| 07:15:53 | s5_solve | s5_track_g | 50 | 0.006812 | [task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf](#task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf) |
| 07:15:55 | s5_solve | s5_track_h | 50 | 0.009272 | [task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b](#task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b) |
| 07:16:17 | s5_solve | s5_merge | 50 | 0.056918 | [task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813](#task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813) |
| 07:17:00 | s5_solve | s5_merge | 50 | 0.060189 | [task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2](#task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2) |
| 07:19:02 | s6_concept | s6_concept | 50 | 0.020201 | [task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9](#task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9) |
| 07:19:04 | s6_concept | s6_concept | 50 | 0.022386 | [task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5](#task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5) |
| 07:19:09 | s6_concept | s6_concept | 50 | 0.015683 | [task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287](#task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287) |
| 07:19:53 | s6_concept | independent_verifier | 50 | 0.007365 | [task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80](#task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80) |
| 07:20:11 | s6_concept | independent_verifier | 50 | 0.007610 | [task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269](#task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269) |
| 07:20:31 | s6_concept | independent_verifier | 50 | 0.005809 | [task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9](#task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9) |
| 07:20:47 | s6_concept | independent_verifier | 50 | 0.015462 | [task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc](#task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc) |
| 07:21:06 | s6_concept | independent_verifier | 50 | 0.004978 | [task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809](#task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809) |
| 07:22:21 | s7_gate | ax_repair_gap-99452800a5dc788ae3d52b55_0 | 50 | 0.010012 | [task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0](#task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0) |
| 07:22:41 | s7_gate | independent_verifier | 50 | 0.005958 | [task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4](#task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4) |
| 07:23:05 | s7_gate | ax_repair_gap-99452800a5dc788ae3d52b55_1 | 50 | 0.010507 | [task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029](#task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029) |
| 07:23:26 | s7_gate | independent_verifier | 50 | 0.005863 | [task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b](#task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b) |
| 07:23:50 | s7_gate | ax_repair_gap-ee8407b02217eddd77e4bfbd_0 | 50 | 0.011715 | [task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f](#task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f) |
| 07:24:17 | s7_gate | independent_verifier | 50 | 0.005893 | [task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728](#task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728) |
| 07:24:42 | s7_gate | ax_repair_gap-ee8407b02217eddd77e4bfbd_1 | 50 | 0.011122 | [task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24](#task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24) |
| 07:25:08 | s7_gate | independent_verifier | 50 | 0.006064 | [task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce](#task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce) |
| 07:25:51 | s7_gate | s7_gate_2 | 50 | 0.002549 | [task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1](#task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1) |
| 07:25:53 | s7_gate | s7_gate_3 | 50 | 0.002536 | [task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b](#task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b) |
| 07:25:55 | s7_gate | s7_gate_1 | 50 | 0.002569 | [task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8](#task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8) |
| 07:25:59 | s7_gate | s7_gate_4 | 50 | 0.002574 | [task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848](#task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848) |
| 07:26:05 | s7_gate | s7_gate_6 | 50 | 0.002417 | [task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8](#task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8) |
| 07:26:07 | s7_gate | s7_gate_5 | 50 | 0.002320 | [task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131](#task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131) |
| 07:26:09 | s7_gate | s7_gate_7 | 50 | 0.002539 | [task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e](#task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e) |
| 07:26:14 | s7_gate | s7_gate_8 | 50 | 0.002446 | [task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f](#task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f) |
| 07:26:19 | s7_gate | s7_gate_9 | 50 | 0.002623 | [task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa](#task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa) |
| 07:26:21 | s7_gate | s7_gate_10 | 50 | 0.002506 | [task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273](#task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273) |
| 07:33:06 | s8_references | ax_repair_gap-80693d8f5a5d25a6d2dfa098_0 | 51 | 0.009660 | [task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72](#task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72) |
| 07:33:28 | s8_references | independent_verifier | 51 | 0.005726 | [task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b](#task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b) |
| 07:33:51 | s8_references | ax_repair_gap-80693d8f5a5d25a6d2dfa098_1 | 51 | 0.010291 | [task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599](#task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599) |
| 07:34:12 | s8_references | independent_verifier | 51 | 0.005578 | [task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025](#task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025) |
| 07:34:32 | s8_references | ax_repair_gap-23e4763bd7081652230dfb23_0 | 51 | 0.010274 | [task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64](#task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64) |
| 07:34:56 | s8_references | independent_verifier | 51 | 0.006041 | [task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56](#task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56) |
| 07:35:19 | s8_references | ax_repair_gap-23e4763bd7081652230dfb23_1 | 51 | 0.009956 | [task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7](#task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7) |
| 07:35:40 | s8_references | independent_verifier | 51 | 0.005596 | [task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3](#task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3) |
| 07:36:44 | s8_references | s9_evidence_match_0 | 51 | 0.006628 | [task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1](#task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1) |
| 07:37:02 | s8_references | s9_evidence_match_1 | 51 | 0.008446 | [task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd](#task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd) |
| 07:37:25 | s8_references | s9_evidence_match_2 | 51 | 0.005675 | [task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0](#task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0) |
| 07:38:30 | s8_evaluate | s8_persona_factory | 51 | 0.003135 | [task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02](#task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02) |
| 07:38:48 | s8_evaluate | s8_review_independent | 51 | 0.009213 | [task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77](#task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77) |
| 07:38:50 | s8_evaluate | s8_review_independent | 51 | 0.007672 | [task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029](#task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029) |
| 07:38:51 | s8_evaluate | s8_review_independent | 51 | 0.009519 | [task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73](#task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73) |
| 07:38:53 | s8_evaluate | s8_review_independent | 51 | 0.008968 | [task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d](#task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d) |
| 07:39:03 | s8_evaluate | s8_review_independent | 51 | 0.010404 | [task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11](#task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11) |
| 07:39:18 | s8_evaluate | s8_review_independent | 51 | 0.006918 | [task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4](#task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4) |
| 07:39:35 | s8_evaluate | s8_review_independent | 51 | 0.006716 | [task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685](#task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685) |
| 07:39:43 | s8_evaluate | s8_review_independent | 51 | 0.006915 | [task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa](#task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa) |
| 07:39:44 | s8_evaluate | s8_review_independent | 51 | 0.006693 | [task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9](#task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9) |
| 07:40:02 | s8_evaluate | s8_review_independent | 51 | 0.007895 | [task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233](#task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233) |
| 07:40:11 | s8_evaluate | s8_review_independent | 51 | 0.009220 | [task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3](#task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3) |
| 07:41:00 | s8_evaluate | s8_review_independent | 51 | 0.006792 | [task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06](#task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06) |
| 07:41:05 | s8_evaluate | s8_review_independent | 51 | 0.006929 | [task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a](#task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a) |
| 07:41:57 | s8_evaluate | s8_rank | 51 | 0.005780 | [task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7](#task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7) |
| 07:58:08 | s10_feedback | s10_distill | 52 | 0.004032 | [task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e](#task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e) |

<a id="task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2"></a>

<details>
<summary>s0_deep_dive · task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2</summary>

```json
{
  "task_id": "task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2",
  "epoch": 47,
  "input_snapshot": "snap-e6e662cc4e1a4696b2e92a1ecd6ecab0",
  "input_hash": "116c5015fd9552da61bbb7ed92c9b6132b77d3ee01db1638304efe1a0258aa66",
  "status": "COMPLETED",
  "reserve": 92949,
  "actual": 3326,
  "created_at": "2026-09-29T21:47:22.907249+00:00",
  "settled_at": "2026-09-29T21:47:32.299658+00:00",
  "node": "s0_deep_dive",
  "request_fingerprint": {
    "sha256": "83e0ae3560e646b8d40890eaa595644970a45641bb4d7d92490591960d61cfd5",
    "utf8_bytes": 11771
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 3424,
    "tokens_out": 1915,
    "cost_usd": 0.0033252000000000004,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d9f68d0ede88338bc7ea68fb100749d34f728c0bee3fe6c001858b5a2f908305",
        "utf8_bytes": 11419
      },
      "response_fingerprint": {
        "sha256": "5f602631f8783a1f23782a44a1eeb60276efe27b88d5d02e0ac834778e58c00f",
        "utf8_bytes": 6354
      },
      "usage": {
        "completion_tokens": 1915,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2304,
        "prompt_cache_miss_tokens": 1120,
        "prompt_tokens": 3424,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2304,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5339
      },
      "finish_reason": "stop",
      "elapsed": 9.050902843475342
    }
  ]
}
```

</details>

<a id="task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8"></a>

<details>
<summary>s0_deep_dive · task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8</summary>

```json
{
  "task_id": "task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8",
  "epoch": 48,
  "input_snapshot": "snap-77d1bbb8d3374e44aab6472310bb4c65",
  "input_hash": "b1180dbe227fa6a2f760494e150f1eb3d57c3ba2a845766030a89cd02c21c699",
  "status": "COMPLETED",
  "reserve": 93759,
  "actual": 3407,
  "created_at": "2026-09-29T21:49:49.899868+00:00",
  "settled_at": "2026-09-29T21:49:58.755810+00:00",
  "node": "s0_deep_dive",
  "request_fingerprint": {
    "sha256": "ad93a99c66211f57ee4915c08c1e5eb9161a177deeaabd0c753a96e916384d36",
    "utf8_bytes": 13180
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 3827,
    "tokens_out": 1882,
    "cost_usd": 0.0034065,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "fcbb71f30d5bdb52671fab4261784ec7f95fe4199e3eafadcfd9f8b775dc26eb",
        "utf8_bytes": 12828
      },
      "response_fingerprint": {
        "sha256": "d9494f37f32cd7238b727725bc733e5e0ff57de38021550bd9184f6f091b1948",
        "utf8_bytes": 6126
      },
      "usage": {
        "completion_tokens": 1882,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2560,
        "prompt_cache_miss_tokens": 1267,
        "prompt_tokens": 3827,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2560,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5709
      },
      "finish_reason": "stop",
      "elapsed": 8.779016971588135
    }
  ]
}
```

</details>

<a id="task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a"></a>

<details>
<summary>s1_extract · task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a</summary>

```json
{
  "task_id": "task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a",
  "epoch": 48,
  "input_snapshot": "snap-637dd636b5614fdb9b0958244b6bb1ae",
  "input_hash": "6e0a3017998cf1abaa11cb9be4c8170af55b4f847a1114d63fb4a584ddbedf1f",
  "status": "COMPLETED",
  "reserve": 62249,
  "actual": 6371,
  "created_at": "2026-09-29T21:50:47.599660+00:00",
  "settled_at": "2026-09-29T21:50:58.529738+00:00",
  "node": "s1_extract",
  "request_fingerprint": {
    "sha256": "dadfba25a08821925d61e0ea1add1cae09d52ed8009d2945fba68692f01322c5",
    "utf8_bytes": 25027
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T1",
    "model": "deepseek-flash",
    "tokens_in": 7328,
    "tokens_out": 3477,
    "cost_usd": 0.006370799999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3efc6b93196552a763620447ba7827161509aa226742f9e8a12dccef076c9d44",
        "utf8_bytes": 24676
      },
      "response_fingerprint": {
        "sha256": "e5ec34431e68b4ea996902c1738ac56f52146d72e78d28330eed8a6a90d00633",
        "utf8_bytes": 11799
      },
      "usage": {
        "completion_tokens": 3477,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2304,
        "prompt_cache_miss_tokens": 5024,
        "prompt_tokens": 7328,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2304,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10805
      },
      "finish_reason": "stop",
      "elapsed": 10.820557832717896
    }
  ]
}
```

</details>

<a id="task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067"></a>

<details>
<summary>s1_clarify · task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067</summary>

```json
{
  "task_id": "task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067",
  "epoch": 48,
  "input_snapshot": "snap-637dd636b5614fdb9b0958244b6bb1ae",
  "input_hash": "012088a526ce21aa39a98adbf02e647dc21b57d123b268359d287b41eb623700",
  "status": "COMPLETED",
  "reserve": 59526,
  "actual": 2294,
  "created_at": "2026-09-29T21:51:11.537903+00:00",
  "settled_at": "2026-09-29T21:51:13.857874+00:00",
  "node": "s1_clarify",
  "request_fingerprint": {
    "sha256": "41150d3f58ce82bb2ddf50c949246ed2f968317dda9a2468fa914bfcecc30084",
    "utf8_bytes": 20354
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T1",
    "model": "deepseek-flash",
    "tokens_in": 6006,
    "tokens_out": 410,
    "cost_usd": 0.0022938,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "9c24624cd2719221df039ae053c1556d66c5a26e8ef12215cdd32f0ba2fdd61e",
        "utf8_bytes": 20004
      },
      "response_fingerprint": {
        "sha256": "6ef95dad377c7758fda5994582ee3355c7cd8ed5b88d0887e6aa5335514a78c4",
        "utf8_bytes": 1427
      },
      "usage": {
        "completion_tokens": 410,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 256,
        "prompt_cache_miss_tokens": 5750,
        "prompt_tokens": 6006,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 256,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6416
      },
      "finish_reason": "stop",
      "elapsed": 2.246677875518799
    }
  ]
}
```

</details>

<a id="task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7"></a>

<details>
<summary>s1_extract · task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7</summary>

```json
{
  "task_id": "task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7",
  "epoch": 49,
  "input_snapshot": "snap-057b74df690c4957b6613656b36fcf38",
  "input_hash": "9cd7b1d2817bc28a468bc9235d28cd4b5e18f9f27d36be547232f13e10f35e91",
  "status": "COMPLETED",
  "reserve": 61270,
  "actual": 6206,
  "created_at": "2026-09-29T21:52:58.221945+00:00",
  "settled_at": "2026-09-29T21:53:09.110461+00:00",
  "node": "s1_extract",
  "request_fingerprint": {
    "sha256": "3623e7b3c20df997bc49327aa50e97dacf496435015d98d3e8badf2625a9c3db",
    "utf8_bytes": 23394
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T1",
    "model": "deepseek-flash",
    "tokens_in": 6850,
    "tokens_out": 3459,
    "cost_usd": 0.006205799999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b59d06f43ade1ee08fa7d941f5074a86f329eb29f37e12c45481273aa6b64291",
        "utf8_bytes": 23043
      },
      "response_fingerprint": {
        "sha256": "6edf77c03248d7f1612fa681333c1477861a5dc98ceab45629391d8cc9c8d6aa",
        "utf8_bytes": 11750
      },
      "usage": {
        "completion_tokens": 3459,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 5186,
        "prompt_tokens": 6850,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10309
      },
      "finish_reason": "stop",
      "elapsed": 10.759281635284424
    }
  ]
}
```

</details>

<a id="task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1"></a>

<details>
<summary>s2_candidates · task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1</summary>

```json
{
  "task_id": "task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1",
  "epoch": 49,
  "input_snapshot": "snap-530bf632a2824745af2db86e237c95df",
  "input_hash": "e4f553d6ba7f36038a65efdb99b4fe1b5879a768a1e93c3fe23e7be6fb2540d7",
  "status": "COMPLETED",
  "reserve": 96150,
  "actual": 3377,
  "created_at": "2026-09-29T21:53:58.050586+00:00",
  "settled_at": "2026-09-29T21:54:04.535734+00:00",
  "node": "s2_candidates",
  "request_fingerprint": {
    "sha256": "67485fb2aa748af51e1309a91fb595bce55cf6e6621472f2bc17049102c20614",
    "utf8_bytes": 17428
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 5112,
    "tokens_out": 1536,
    "cost_usd": 0.0033768,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "daa62593cc067a58ac1218d19ae499fd6318d786fd9aa1162b43f2be8ea09db8",
        "utf8_bytes": 17075
      },
      "response_fingerprint": {
        "sha256": "92f3e67808061dd55e5688226c01fd848985c172571e88865a4bf63ea152ca49",
        "utf8_bytes": 4749
      },
      "usage": {
        "completion_tokens": 1536,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 256,
        "prompt_cache_miss_tokens": 4856,
        "prompt_tokens": 5112,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 256,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6648
      },
      "finish_reason": "stop",
      "elapsed": 6.415265083312988
    }
  ]
}
```

</details>

<a id="task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761"></a>

<details>
<summary>s3_nine_windows · task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761</summary>

```json
{
  "task_id": "task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "5769b7445fd12122ad356e93b0df190ff6e171791ddf1d5243d7fcfaf01c107a",
  "status": "COMPLETED",
  "reserve": 97397,
  "actual": 3713,
  "created_at": "2026-09-29T22:07:35.634910+00:00",
  "settled_at": "2026-09-29T22:07:44.621892+00:00",
  "node": "s3_nine_windows",
  "request_fingerprint": {
    "sha256": "890240367375f427f6a8996aee31df67d4128144c17ae49414c3ea632cb12ad4",
    "utf8_bytes": 19460
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 5740,
    "tokens_out": 1659,
    "cost_usd": 0.0037128,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c441eef10955a7fc8a2bb53ec3f16ee5d9daa5ab0d315120e1f6f9a6bd4633e3",
        "utf8_bytes": 19105
      },
      "response_fingerprint": {
        "sha256": "6df34a229ab0a900240bbd09bc0a5d2cfc4672b2566065eecbb05886b5f555e9",
        "utf8_bytes": 5506
      },
      "usage": {
        "completion_tokens": 1659,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 4076,
        "prompt_tokens": 5740,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 7399
      },
      "finish_reason": "stop",
      "elapsed": 8.909832000732422
    }
  ]
}
```

</details>

<a id="task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f"></a>

<details>
<summary>s3_function_model · task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f</summary>

```json
{
  "task_id": "task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "48b34801bc1761fd51b1cb8121a4faf8e0f27eb5060bc2b24c8e749bd3a66ac2",
  "status": "COMPLETED",
  "reserve": 100721,
  "actual": 5999,
  "created_at": "2026-09-29T22:07:50.540357+00:00",
  "settled_at": "2026-09-29T22:08:02.896118+00:00",
  "node": "s3_function_model",
  "request_fingerprint": {
    "sha256": "5aaeaaf49500ece9cd58a6fb2e47e309b069b0dfd5a26625ce8df5d88f8a1d4d",
    "utf8_bytes": 25178
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7414,
    "tokens_out": 3145,
    "cost_usd": 0.0059981999999999995,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ca7936c1d5fbc236af705b1c403b08184c10c37d071aa9ce4f6bd390466455de",
        "utf8_bytes": 24821
      },
      "response_fingerprint": {
        "sha256": "029873e2d2d488d05bfb36586ccb18a1957ceaec119104b111592f605f9e331d",
        "utf8_bytes": 9855
      },
      "usage": {
        "completion_tokens": 3145,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 5750,
        "prompt_tokens": 7414,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10559
      },
      "finish_reason": "stop",
      "elapsed": 12.267897129058838
    }
  ]
}
```

</details>

<a id="task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a"></a>

<details>
<summary>independent_verifier · task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a</summary>

```json
{
  "task_id": "task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "0ebe706992d6efe7c729c90ac8d80729e846376f47df52a4157432d209acea13",
  "status": "COMPLETED",
  "reserve": 41435,
  "actual": 3168,
  "created_at": "2026-09-29T22:08:06.274210+00:00",
  "settled_at": "2026-09-29T22:08:10.759750+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "0495e98f239c68fd89e828a616d75d0f4a75e680c51417bac60a3d62a1823ab9",
    "utf8_bytes": 23027
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 6835,
    "tokens_out": 931,
    "cost_usd": 0.0031677,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b11b92707aff6d39174769ae28208eeb367e1907575dc501f37c7e7203a7cd0e",
        "utf8_bytes": 22667
      },
      "response_fingerprint": {
        "sha256": "b75a6d08480fbea462c1eb76744490bf7f7fb926da4bdd73c1a8753e9d43cfca",
        "utf8_bytes": 2959
      },
      "usage": {
        "completion_tokens": 931,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 6835,
        "prompt_tokens": 6835,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 7766
      },
      "finish_reason": "stop",
      "elapsed": 4.404851675033569
    }
  ]
}
```

</details>

<a id="task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc"></a>

<details>
<summary>s3_resources · task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc</summary>

```json
{
  "task_id": "task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "57b2150a043af770c8156cfafb45c7320ac384401ae91e72e68e9c6f524112bd",
  "status": "COMPLETED",
  "reserve": 99469,
  "actual": 5607,
  "created_at": "2026-09-29T22:08:21.894349+00:00",
  "settled_at": "2026-09-29T22:08:35.192844+00:00",
  "node": "s3_resources",
  "request_fingerprint": {
    "sha256": "bbb66e1290d8ceb9f1f4ae9721263783c492366f762fa7480742813d0f997d12",
    "utf8_bytes": 22959
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6771,
    "tokens_out": 2979,
    "cost_usd": 0.005606099999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b2b660c074f05fe36816d1ba593898b21971a15fc755279d93ae72577ac3b147",
        "utf8_bytes": 22607
      },
      "response_fingerprint": {
        "sha256": "69a35cdec68bac0437f0329e39fda658225d9d1968f8176963c61e82cddaaeef",
        "utf8_bytes": 10227
      },
      "usage": {
        "completion_tokens": 2979,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 5107,
        "prompt_tokens": 6771,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 9750
      },
      "finish_reason": "stop",
      "elapsed": 13.215503454208374
    }
  ]
}
```

</details>

<a id="task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d"></a>

<details>
<summary>s3_ceca · task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d</summary>

```json
{
  "task_id": "task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "ab6b467912145e570ae85bb76c87774a0e7d80b9fd4c0e8b3ea51dc0d006722e",
  "status": "COMPLETED",
  "reserve": 100055,
  "actual": 5799,
  "created_at": "2026-09-29T22:08:23.446660+00:00",
  "settled_at": "2026-09-29T22:08:35.575513+00:00",
  "node": "s3_ceca",
  "request_fingerprint": {
    "sha256": "731cc018e8a8c86d47327a5956aae9340655f6d4c1cbeecc70e468f9352a4534",
    "utf8_bytes": 23972
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7131,
    "tokens_out": 3049,
    "cost_usd": 0.0057981,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "06239f1d78f24b5b962f4934db61cd5da59c113990d3b322a14d7ae3056b648c",
        "utf8_bytes": 23624
      },
      "response_fingerprint": {
        "sha256": "e28ccbce14aed7cb7451a6cccf0768074b0c69f7a4f7c89de148808e726d6237",
        "utf8_bytes": 9258
      },
      "usage": {
        "completion_tokens": 3049,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 5467,
        "prompt_tokens": 7131,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10180
      },
      "finish_reason": "stop",
      "elapsed": 12.042414665222168
    }
  ]
}
```

</details>

<a id="task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799"></a>

<details>
<summary>s3_sufield · task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799</summary>

```json
{
  "task_id": "task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "cfc6d0e82fe50be15b30de52f62ce763a55a78f7d5edafe31d37f9f6a5752a29",
  "status": "COMPLETED",
  "reserve": 99589,
  "actual": 2450,
  "created_at": "2026-09-29T22:08:24.979974+00:00",
  "settled_at": "2026-09-29T22:08:26.583459+00:00",
  "node": "s3_sufield",
  "request_fingerprint": {
    "sha256": "da44c61d1455de4ac0b3f257968387416f98b228bba602e93eeced6c161d7ccf",
    "utf8_bytes": 23157
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6940,
    "tokens_out": 306,
    "cost_usd": 0.0024492,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "160e513a5831bea96c06f768a5edde519e403ad35d6e38a73b755da83a6c6c1c",
        "utf8_bytes": 22807
      },
      "response_fingerprint": {
        "sha256": "a419f727b2dcb33e26e9347a401d6cad617294e98da7e18415ea54419d4d2453",
        "utf8_bytes": 924
      },
      "usage": {
        "completion_tokens": 306,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 5276,
        "prompt_tokens": 6940,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 7246
      },
      "finish_reason": "stop",
      "elapsed": 1.5153698921203613
    }
  ]
}
```

</details>

<a id="task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af"></a>

<details>
<summary>independent_verifier · task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af</summary>

```json
{
  "task_id": "task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "5b79dff4f690abd4b73e5a08aab8988df39ddde73dd850ca578972d71bd629e5",
  "status": "COMPLETED",
  "reserve": 40550,
  "actual": 2880,
  "created_at": "2026-09-29T22:08:38.757985+00:00",
  "settled_at": "2026-09-29T22:08:42.889252+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "0be816e5efd872fb4b481181c08ba33d577b1a9b035a747227261f63412feda4",
    "utf8_bytes": 20921
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 6489,
    "tokens_out": 777,
    "cost_usd": 0.0028791,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "2d071a993a5552446cec5b091d0d22c31e5e87467daef4ba9f7141d33a092a78",
        "utf8_bytes": 20561
      },
      "response_fingerprint": {
        "sha256": "ff98fbd118e780dfecf113bfb82d2f6ba3069371b2640b0ed05a87711410b901",
        "utf8_bytes": 2261
      },
      "usage": {
        "completion_tokens": 777,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 6489,
        "prompt_tokens": 6489,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 7266
      },
      "finish_reason": "stop",
      "elapsed": 4.005887269973755
    }
  ]
}
```

</details>

<a id="task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da"></a>

<details>
<summary>s3_constraints · task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da</summary>

```json
{
  "task_id": "task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da",
  "epoch": 50,
  "input_snapshot": "snap-48dde9a56a904700ba6518af3610184a",
  "input_hash": "b3acfad09586112b5dba3c16f0bf24cb17b1838433067d4123e867077b711a30",
  "status": "COMPLETED",
  "reserve": 102827,
  "actual": 5961,
  "created_at": "2026-09-29T22:08:48.143884+00:00",
  "settled_at": "2026-09-29T22:08:58.053478+00:00",
  "node": "s3_constraints",
  "request_fingerprint": {
    "sha256": "06f10549a65497637499a8b4f89dc4d0abdb0a7ca2ef0eb6f823839ffde6a745",
    "utf8_bytes": 28649
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 8517,
    "tokens_out": 2838,
    "cost_usd": 0.005960699999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c496dedf5a1de5cb8b50b214480c5674205a00e380ccb7027547991b985f3fc6",
        "utf8_bytes": 28295
      },
      "response_fingerprint": {
        "sha256": "1095fbce430ca1f9429af8b73f4a382f675d6610d626d48d13ad712dd75067b1",
        "utf8_bytes": 9542
      },
      "usage": {
        "completion_tokens": 2838,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1664,
        "prompt_cache_miss_tokens": 6853,
        "prompt_tokens": 8517,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1664,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 11355
      },
      "finish_reason": "stop",
      "elapsed": 9.833827257156372
    }
  ]
}
```

</details>

<a id="task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6"></a>

<details>
<summary>s4_ifr · task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6</summary>

```json
{
  "task_id": "task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6",
  "epoch": 50,
  "input_snapshot": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
  "input_hash": "214ebb3fb5ee56d5a1219aeb5051e8547aab60993f0d8a6c7d72060086e25fc3",
  "status": "COMPLETED",
  "reserve": 98122,
  "actual": 2899,
  "created_at": "2026-09-29T22:09:49.691637+00:00",
  "settled_at": "2026-09-29T22:09:54.910596+00:00",
  "node": "s4_ifr",
  "request_fingerprint": {
    "sha256": "409a4314a8afe4ff1d1f0320f1165153ef9a5543e5af90d940b3c3683ccea1ec",
    "utf8_bytes": 20722
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6103,
    "tokens_out": 890,
    "cost_usd": 0.0028989,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "5c355cca36326cbe2c903a272938a3103a7d61562d51194c012f92c77bfc24a7",
        "utf8_bytes": 20376
      },
      "response_fingerprint": {
        "sha256": "a25d11da5f8776b5681621f71e00eadfe720974907d23a7927e79464dd79ac2d",
        "utf8_bytes": 3001
      },
      "usage": {
        "completion_tokens": 890,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 1536,
        "prompt_cache_miss_tokens": 4567,
        "prompt_tokens": 6103,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 1536,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6993
      },
      "finish_reason": "stop",
      "elapsed": 4.951110124588013
    }
  ]
}
```

</details>

<a id="task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a"></a>

<details>
<summary>s4_contradictions · task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a</summary>

```json
{
  "task_id": "task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a",
  "epoch": 50,
  "input_snapshot": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
  "input_hash": "95b936a21cda0cacade7ee6803feb7c5ba8fccbc3caaf5eb30d6d86e8a64fe45",
  "status": "COMPLETED",
  "reserve": 105888,
  "actual": 6366,
  "created_at": "2026-09-29T22:09:51.284363+00:00",
  "settled_at": "2026-09-29T22:10:03.269185+00:00",
  "node": "s4_contradictions",
  "request_fingerprint": {
    "sha256": "6e12eb93d6d18c8ad9c67a9d11f48acbbffb7b0ed6ee764cb40935c1b1e2f95f",
    "utf8_bytes": 34079
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 10141,
    "tokens_out": 2769,
    "cost_usd": 0.0063651,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c02d2171b9def05a8b68b570e13f027a215d7ef70368277c369d136db1e47010",
        "utf8_bytes": 33722
      },
      "response_fingerprint": {
        "sha256": "b68d658d90f79652c5d5b65287072a09d152863ee49fd0e997474313cffcbff3",
        "utf8_bytes": 8898
      },
      "usage": {
        "completion_tokens": 2769,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 8093,
        "prompt_tokens": 10141,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 12910
      },
      "finish_reason": "stop",
      "elapsed": 11.829448461532593
    }
  ]
}
```

</details>

<a id="task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc"></a>

<details>
<summary>s4_trimming · task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc</summary>

```json
{
  "task_id": "task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc",
  "epoch": 50,
  "input_snapshot": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
  "input_hash": "6616b3210a6a0dc666b5501baf20a9218e8dbe9fd26d9d66f3c61c24a8939698",
  "status": "COMPLETED",
  "reserve": 101398,
  "actual": 3967,
  "created_at": "2026-09-29T22:09:52.724388+00:00",
  "settled_at": "2026-09-29T22:09:59.434735+00:00",
  "node": "s4_trimming",
  "request_fingerprint": {
    "sha256": "6dfd31a16a99d3003dc51e77e5c6ca2f51e09c53eb2dec36d9beb077b2ea8bcb",
    "utf8_bytes": 26219
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7850,
    "tokens_out": 1343,
    "cost_usd": 0.0039666,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b21a6527d820f2161a36ee02411cb6af4dc7302d86185e4d4cfa0fa467eb5453",
        "utf8_bytes": 25868
      },
      "response_fingerprint": {
        "sha256": "f3541312eb9acc40b3a60e803adfbbd2cf06d6648707304cc7df0ab048d4b8da",
        "utf8_bytes": 4426
      },
      "usage": {
        "completion_tokens": 1343,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5802,
        "prompt_tokens": 7850,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 9193
      },
      "finish_reason": "stop",
      "elapsed": 6.63434624671936
    }
  ]
}
```

</details>

<a id="task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d"></a>

<details>
<summary>independent_verifier · task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d</summary>

```json
{
  "task_id": "task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d",
  "epoch": 50,
  "input_snapshot": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
  "input_hash": "0131acd2a2240b5d844c3598459c43d6457f505987a167007c6e2d4e85b2bc91",
  "status": "COMPLETED",
  "reserve": 46826,
  "actual": 4642,
  "created_at": "2026-09-29T22:10:08.683210+00:00",
  "settled_at": "2026-09-29T22:10:16.020499+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "054688831e9959ca6fd36d3c8b5330a2c5432a30d7a7cc15a943723caf8db63f",
    "utf8_bytes": 31813
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 9664,
    "tokens_out": 1452,
    "cost_usd": 0.0046416,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "8e95ef090e68565c0224a51491c107c9b7093e4ce5f6f72692af55315c843512",
        "utf8_bytes": 31453
      },
      "response_fingerprint": {
        "sha256": "1f11d3ffd37ce2d02b8a4b8caefad58c75fe9fb03f23484135c0150a8179616b",
        "utf8_bytes": 4450
      },
      "usage": {
        "completion_tokens": 1452,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 9664,
        "prompt_tokens": 9664,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 11116
      },
      "finish_reason": "stop",
      "elapsed": 7.260721445083618
    }
  ]
}
```

</details>

<a id="task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce"></a>

<details>
<summary>s4_key_problem · task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce</summary>

```json
{
  "task_id": "task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce",
  "epoch": 50,
  "input_snapshot": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
  "input_hash": "0ea3c22aac733c3248880f857a1c2f35277e1035f1a05840cd9b32886fd8bf45",
  "status": "COMPLETED",
  "reserve": 100828,
  "actual": 3386,
  "created_at": "2026-09-29T22:10:21.120443+00:00",
  "settled_at": "2026-09-29T22:10:26.182738+00:00",
  "node": "s4_key_problem",
  "request_fingerprint": {
    "sha256": "906d6fd17ed0396f5d53db237b565d6451873da425c05cfb1af4af412bda6892",
    "utf8_bytes": 25673
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7577,
    "tokens_out": 927,
    "cost_usd": 0.0033855,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "53b30e2db6c16dba6e9f27df69cc8156b16fd88f95a3498f7b70409aff283e5b",
        "utf8_bytes": 25319
      },
      "response_fingerprint": {
        "sha256": "feb8dfbc91c364fc87513320c4681faed78722aa93721832b56a061cd103dbef",
        "utf8_bytes": 2923
      },
      "usage": {
        "completion_tokens": 927,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5529,
        "prompt_tokens": 7577,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 8504
      },
      "finish_reason": "stop",
      "elapsed": 4.993568658828735
    }
  ]
}
```

</details>

<a id="task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265"></a>

<details>
<summary>s5_ariz_p1 · task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265</summary>

```json
{
  "task_id": "task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "689d561e686a63ccc05f320b763dd61cb0ef4a3edfe5987599b19ab1d963075a",
  "status": "COMPLETED",
  "reserve": 98868,
  "actual": 6753,
  "created_at": "2026-09-29T22:11:16.283189+00:00",
  "settled_at": "2026-09-29T22:11:31.766804+00:00",
  "node": "s5_ariz_p1",
  "request_fingerprint": {
    "sha256": "593ba7bfb5a4259eaf12e597fe64ce449e0433be6f6c7cd50a9dc3fe291e12c0",
    "utf8_bytes": 21996
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6548,
    "tokens_out": 3990,
    "cost_usd": 0.0067523999999999995,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "98c1741fa24a5466a99c1a0aac73ab6015fd87353056a93ef88b5d48c8bbce6b",
        "utf8_bytes": 21645
      },
      "response_fingerprint": {
        "sha256": "1826e0d43fd9ef49e3ce36cf7adfacc7a59f53662bef1f59e82873afe38e24f2",
        "utf8_bytes": 13001
      },
      "usage": {
        "completion_tokens": 3990,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 4500,
        "prompt_tokens": 6548,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10538
      },
      "finish_reason": "stop",
      "elapsed": 15.39468240737915
    }
  ]
}
```

</details>

<a id="task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9"></a>

<details>
<summary>s5_track_a_select · task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9</summary>

```json
{
  "task_id": "task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "c49cea8ae0f3993113d45e77e56f8b4e0db821677da26ec691be48ba7e418559",
  "status": "COMPLETED",
  "reserve": 98825,
  "actual": 2308,
  "created_at": "2026-09-29T22:11:17.905228+00:00",
  "settled_at": "2026-09-29T22:11:20.325444+00:00",
  "node": "s5_track_a_select",
  "request_fingerprint": {
    "sha256": "1383d643bc76ed4ef6229eb7c8af7f93adff79b8bf5c02efa8c05903d91972fe",
    "utf8_bytes": 21858
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6452,
    "tokens_out": 310,
    "cost_usd": 0.0023076,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d49269ba218059cae0db5e15998efdf04106f3884a2e58ce325b3804d190dfc3",
        "utf8_bytes": 21500
      },
      "response_fingerprint": {
        "sha256": "7bde23b314ca76703b48e84e99125d5eed5fef3a796477c66f1f37a06cfbb5b9",
        "utf8_bytes": 1026
      },
      "usage": {
        "completion_tokens": 310,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 4404,
        "prompt_tokens": 6452,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6762
      },
      "finish_reason": "stop",
      "elapsed": 2.3349475860595703
    }
  ]
}
```

</details>

<a id="task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e"></a>

<details>
<summary>s5_track_b · task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e</summary>

```json
{
  "task_id": "task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "6768f5e6858ff644024b1e41b88f714e861658184d8cd507f80dab4287e90bd8",
  "status": "COMPLETED",
  "reserve": 100764,
  "actual": 4593,
  "created_at": "2026-09-29T22:11:19.456146+00:00",
  "settled_at": "2026-09-29T22:11:28.839521+00:00",
  "node": "s5_track_b",
  "request_fingerprint": {
    "sha256": "10a2af39609807977f576f56dd5600514b2bbe40391636372e52e5dbaa237db4",
    "utf8_bytes": 25141
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7526,
    "tokens_out": 1946,
    "cost_usd": 0.004593,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "5c1946ec534145ce4f0f8b8fba33d550a220cd84cb2f8910bd31a8f1f500c5a0",
        "utf8_bytes": 24790
      },
      "response_fingerprint": {
        "sha256": "ffb580b5d0c11fc454da41883c652be1eb98597d906d0ffa865ee59aa1c5f51f",
        "utf8_bytes": 6523
      },
      "usage": {
        "completion_tokens": 1946,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5478,
        "prompt_tokens": 7526,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 9472
      },
      "finish_reason": "stop",
      "elapsed": 9.280645608901978
    }
  ]
}
```

</details>

<a id="task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c"></a>

<details>
<summary>s5_track_a · task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c</summary>

```json
{
  "task_id": "task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "6caa4e4aa0aa4824249711fa65d57f76c8dfaa35f0104e36cdc7d9528f97a361",
  "status": "COMPLETED",
  "reserve": 101066,
  "actual": 6283,
  "created_at": "2026-09-29T22:11:27.788636+00:00",
  "settled_at": "2026-09-29T22:11:43.676417+00:00",
  "node": "s5_track_a",
  "request_fingerprint": {
    "sha256": "ad90b34dbd6cf03dff1889caa72d6f5a5eda98a51caad5f7f461bbcb0c1faa89",
    "utf8_bytes": 25655
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7627,
    "tokens_out": 3329,
    "cost_usd": 0.006282899999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "cc348f18283f76d08a8f6ad3a448a89fa18aeaaede7889472dc903fdd9e757fe",
        "utf8_bytes": 25304
      },
      "response_fingerprint": {
        "sha256": "3ca3130fedb99915afbea9287a5104c31591be02a2a8bbbaf9a4715300f21075",
        "utf8_bytes": 11324
      },
      "usage": {
        "completion_tokens": 3329,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5579,
        "prompt_tokens": 7627,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10956
      },
      "finish_reason": "stop",
      "elapsed": 15.778409719467163
    }
  ]
}
```

</details>

<a id="task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008"></a>

<details>
<summary>s5_track_b · task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008</summary>

```json
{
  "task_id": "task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "68cc01cff97cbb8a4c94543164996c6c44be3505438f6003295e6b0c8e9e0afa",
  "status": "COMPLETED",
  "reserve": 100811,
  "actual": 4547,
  "created_at": "2026-09-29T22:11:37.211163+00:00",
  "settled_at": "2026-09-29T22:11:46.682274+00:00",
  "node": "s5_track_b",
  "request_fingerprint": {
    "sha256": "225b95c66a67b977daa2597bdfdf84360da0ff00986da3f739520c69b44176c1",
    "utf8_bytes": 25219
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7546,
    "tokens_out": 1902,
    "cost_usd": 0.0045462,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "10bd34d0e207f7a3437d24779478dd1015ba33faffb24116e1f12b6335acbbe7",
        "utf8_bytes": 24868
      },
      "response_fingerprint": {
        "sha256": "c44690ae950bc8a46ba147bceb75d09e318c85016d248a38f2448f9134c9f7a3",
        "utf8_bytes": 6407
      },
      "usage": {
        "completion_tokens": 1902,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5498,
        "prompt_tokens": 7546,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 9448
      },
      "finish_reason": "stop",
      "elapsed": 9.352190256118774
    }
  ]
}
```

</details>

<a id="task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043"></a>

<details>
<summary>s5_ariz_p2 · task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043</summary>

```json
{
  "task_id": "task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "78bc999aabeace311ef1d79fb996b26e623ad47f04178f9a318df1f154e69d4d",
  "status": "COMPLETED",
  "reserve": 108275,
  "actual": 8450,
  "created_at": "2026-09-29T22:11:38.768668+00:00",
  "settled_at": "2026-09-29T22:11:55.535600+00:00",
  "node": "s5_ariz_p2",
  "request_fingerprint": {
    "sha256": "11a7b9af60de2536df5f82e7d3d3e554d59bffde7a98fc5bfcfcab4ad5f06773",
    "utf8_bytes": 37951
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 11369,
    "tokens_out": 4199,
    "cost_usd": 0.008449499999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "5b64707d9b1ebda0187d9f114f7e172f8c903f4720d52a68241a2b64d6f2fd1c",
        "utf8_bytes": 37600
      },
      "response_fingerprint": {
        "sha256": "1433d45ce7172f7a4c77e7829f1c477726eb5b90bf8b9db2c60b460884f08867",
        "utf8_bytes": 12696
      },
      "usage": {
        "completion_tokens": 4199,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 9321,
        "prompt_tokens": 11369,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15568
      },
      "finish_reason": "stop",
      "elapsed": 15.299573183059692
    }
  ]
}
```

</details>

<a id="task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1"></a>

<details>
<summary>s5_track_a_select · task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1</summary>

```json
{
  "task_id": "task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "a173383622cee0994164b1e96f2c8628f07fc914b61bfaae89a15c6261547d0f",
  "status": "COMPLETED",
  "reserve": 98849,
  "actual": 2259,
  "created_at": "2026-09-29T22:11:48.503476+00:00",
  "settled_at": "2026-09-29T22:11:50.421143+00:00",
  "node": "s5_track_a_select",
  "request_fingerprint": {
    "sha256": "ed19bf6fa3ef07ceba9b9dfe7c83253b220a94da38d21d4ca1b2d87bf3b73999",
    "utf8_bytes": 21898
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6467,
    "tokens_out": 265,
    "cost_usd": 0.0022581,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "9b9a4e3ca87636536dfbe6cfd5e341f8d87b50ace96f10a5cbb5dc80d5c8f4a7",
        "utf8_bytes": 21540
      },
      "response_fingerprint": {
        "sha256": "bdad3abec0f0416fe0540f468a1800f4a73b42e374a741f625ebc161d6b75174",
        "utf8_bytes": 888
      },
      "usage": {
        "completion_tokens": 265,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 4419,
        "prompt_tokens": 6467,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6732
      },
      "finish_reason": "stop",
      "elapsed": 1.8280811309814453
    }
  ]
}
```

</details>

<a id="task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3"></a>

<details>
<summary>s5_track_a · task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3</summary>

```json
{
  "task_id": "task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "29cc8972fb4981c8288d2bada7b10de1e6f517e0655bc976ad05ae2643564438",
  "status": "COMPLETED",
  "reserve": 100973,
  "actual": 6104,
  "created_at": "2026-09-29T22:11:55.445692+00:00",
  "settled_at": "2026-09-29T22:12:09.974221+00:00",
  "node": "s5_track_a",
  "request_fingerprint": {
    "sha256": "363118872305902f79e6058d88f20a9544aa649d6aeb57b2dfa5c95d4f22b3f2",
    "utf8_bytes": 25497
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7572,
    "tokens_out": 3193,
    "cost_usd": 0.0061032,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "25ecb58ba391469eec39799cb2f2b9fcbdc0d09fe73d2720b444f46c51cb1d69",
        "utf8_bytes": 25146
      },
      "response_fingerprint": {
        "sha256": "4f53a17a9ba106640a5498242971cf0c4ab39968ff997b4dfd693c64f5984df0",
        "utf8_bytes": 10939
      },
      "usage": {
        "completion_tokens": 3193,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 5396,
        "prompt_tokens": 7572,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2176,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10765
      },
      "finish_reason": "stop",
      "elapsed": 14.444567680358887
    }
  ]
}
```

</details>

<a id="task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808"></a>

<details>
<summary>s5_ariz_p3 · task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808</summary>

```json
{
  "task_id": "task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "50c6ed0f4aa5c125298049a8eefe2ec76560f56a88d3cc0a74886c8e3aae03de",
  "status": "COMPLETED",
  "reserve": 110394,
  "actual": 9143,
  "created_at": "2026-09-29T22:12:00.655782+00:00",
  "settled_at": "2026-09-29T22:12:19.236694+00:00",
  "node": "s5_ariz_p3",
  "request_fingerprint": {
    "sha256": "e26081eb20b2d2dfda2830720221e73e59b642f216dd49073cc96957d77a7a29",
    "utf8_bytes": 41779
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 12566,
    "tokens_out": 4477,
    "cost_usd": 0.0091422,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3fae05dcc0bbd7c483480f01751ff281662ef1ffd38af3d7c416cb91119878b1",
        "utf8_bytes": 41428
      },
      "response_fingerprint": {
        "sha256": "c260dd3cc78f40351f93f2ec845a850c9f75ef1441fc8c4792a372cadf50f307",
        "utf8_bytes": 14508
      },
      "usage": {
        "completion_tokens": 4477,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 10518,
        "prompt_tokens": 12566,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 17043
      },
      "finish_reason": "stop",
      "elapsed": 17.207205295562744
    }
  ]
}
```

</details>

<a id="task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08"></a>

<details>
<summary>s5_track_a_select · task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08</summary>

```json
{
  "task_id": "task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "88fd644ea4838b0436c7fc0af2dfe112be02ac4cd550d856c04d1bc8c3abfbc8",
  "status": "COMPLETED",
  "reserve": 98843,
  "actual": 2282,
  "created_at": "2026-09-29T22:12:13.375374+00:00",
  "settled_at": "2026-09-29T22:12:15.549979+00:00",
  "node": "s5_track_a_select",
  "request_fingerprint": {
    "sha256": "e646f97672aa70743f68b8a29cfeb8c891e04cb21990f651d220a4f076f4cebe",
    "utf8_bytes": 21887
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 6465,
    "tokens_out": 285,
    "cost_usd": 0.0022815,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "990ba8f96b561e482eea9e9255cd08a3480ae2fd380f37293f3123ac362a6063",
        "utf8_bytes": 21529
      },
      "response_fingerprint": {
        "sha256": "4eefec53d9e47bd2b983cf295ccb3ed6801bcdbf6e3b31f8ca7a8c0938d8a7bd",
        "utf8_bytes": 961
      },
      "usage": {
        "completion_tokens": 285,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 4417,
        "prompt_tokens": 6465,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 6750
      },
      "finish_reason": "stop",
      "elapsed": 2.104461431503296
    }
  ]
}
```

</details>

<a id="task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b"></a>

<details>
<summary>s5_track_a · task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b</summary>

```json
{
  "task_id": "task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "60f44259b33bf6eb40b6fddb108d8fd7d56c3c4091dcda8c213759ff6d969b6b",
  "status": "COMPLETED",
  "reserve": 100944,
  "actual": 6026,
  "created_at": "2026-09-29T22:12:19.157375+00:00",
  "settled_at": "2026-09-29T22:12:34.564326+00:00",
  "node": "s5_track_a",
  "request_fingerprint": {
    "sha256": "faa2737b42014fd645d3417f88449c67e1ba8706552041cf37767e9889ffb921",
    "utf8_bytes": 25449
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7570,
    "tokens_out": 3129,
    "cost_usd": 0.0060257999999999996,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b3de834d80ac069da14a15400d8773d30645a9e844b925c6c47562992c2c8659",
        "utf8_bytes": 25098
      },
      "response_fingerprint": {
        "sha256": "447b9b2f3eaefcfeb0704c1dd71c173abc1eb3a3113dbd1ea15aa41693555e83",
        "utf8_bytes": 10451
      },
      "usage": {
        "completion_tokens": 3129,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 5394,
        "prompt_tokens": 7570,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2176,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 10699
      },
      "finish_reason": "stop",
      "elapsed": 15.330825805664062
    }
  ]
}
```

</details>

<a id="task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f"></a>

<details>
<summary>s5_ariz_p4 · task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f</summary>

```json
{
  "task_id": "task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "284cf67396bdcd10e9bcb3ff68b37bd9abaf91e767cd6da818f5a16470df8b26",
  "status": "COMPLETED",
  "reserve": 100029,
  "actual": 8759,
  "created_at": "2026-09-29T22:12:22.407514+00:00",
  "settled_at": "2026-09-29T22:12:46.028493+00:00",
  "node": "s5_ariz_p4",
  "request_fingerprint": {
    "sha256": "87e14a9f5033a9a8b00bd042b302357d60d962ddf8e3b9ad58401940861a3b1d",
    "utf8_bytes": 23918
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7147,
    "tokens_out": 5512,
    "cost_usd": 0.0087585,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "f1735a63964077ac9cacda91712b3f9dee44631e86d1eaa0c0a02d3c3b995a9d",
        "utf8_bytes": 23567
      },
      "response_fingerprint": {
        "sha256": "b44ea33d90a52b2e729fe4802957558793b4f11ffa16d0334fe5700bdff9a07e",
        "utf8_bytes": 18368
      },
      "usage": {
        "completion_tokens": 5512,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 4971,
        "prompt_tokens": 7147,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2176,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 12659
      },
      "finish_reason": "stop",
      "elapsed": 23.544513702392578
    }
  ]
}
```

</details>

<a id="task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5"></a>

<details>
<summary>s5_ariz_p5 · task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5</summary>

```json
{
  "task_id": "task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "30dca9d71b8161abcbb9e53cceb4668542853e215e536d26411067fd64c1d3a2",
  "status": "COMPLETED",
  "reserve": 134891,
  "actual": 23206,
  "created_at": "2026-09-29T22:12:50.346532+00:00",
  "settled_at": "2026-09-29T22:13:42.700588+00:00",
  "node": "s5_ariz_p5",
  "request_fingerprint": {
    "sha256": "fd049a968686d8928328309f9082a719acc19123fa9900a73cb2cf9f4e841c1c",
    "utf8_bytes": 82831
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 24609,
    "tokens_out": 13186,
    "cost_usd": 0.023205899999999998,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c632ca75f31e2755d0cdce73755945cd5872c3abf075bea48b0e867ca2164063",
        "utf8_bytes": 82480
      },
      "response_fingerprint": {
        "sha256": "16a1e2b763f289669d18a9e7bbb684d09523bb60b8404eacef62046971f36982",
        "utf8_bytes": 43444
      },
      "usage": {
        "completion_tokens": 13186,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 22433,
        "prompt_tokens": 24609,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2176,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 37795
      },
      "finish_reason": "stop",
      "elapsed": 52.263617277145386
    }
  ]
}
```

</details>

<a id="task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97"></a>

<details>
<summary>s5_ariz_p6 · task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97</summary>

```json
{
  "task_id": "task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "eadfd7f2083fb415df266d24cfc739a0cf6ee4c7bcc5dba244e8681586df5968",
  "status": "COMPLETED",
  "reserve": 91429,
  "actual": 10834,
  "created_at": "2026-09-29T22:13:46.139519+00:00",
  "settled_at": "2026-09-29T22:13:51.642281+00:00",
  "node": "s5_ariz_p6",
  "request_fingerprint": {
    "sha256": "2b8ca19c81ff57bd7af793814d62ab377a5772dc3b361a3953e9c7f52b251995",
    "utf8_bytes": 108700
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 32273,
    "tokens_out": 960,
    "cost_usd": 0.0108339,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "f46af67f36d0dd14199affa2cd2e890486c6de6adfce405e2c8fbb7006b5e830",
        "utf8_bytes": 108349
      },
      "response_fingerprint": {
        "sha256": "439c0a060cdcf28ff188eeab465f596113e8e5923c8cb5962a50349709d67970",
        "utf8_bytes": 2944
      },
      "usage": {
        "completion_tokens": 960,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 30225,
        "prompt_tokens": 32273,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 33233
      },
      "finish_reason": "stop",
      "elapsed": 5.422782897949219
    }
  ]
}
```

</details>

<a id="task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f"></a>

<details>
<summary>s5_ariz_p7 · task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f</summary>

```json
{
  "task_id": "task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "0fcaa7a0dd844495c6f27261f798d89a8594cad96940ea70d39e494c27d5fe06",
  "status": "COMPLETED",
  "reserve": 101429,
  "actual": 18422,
  "created_at": "2026-09-29T22:13:55.297684+00:00",
  "settled_at": "2026-09-29T22:14:39.374891+00:00",
  "node": "s5_ariz_p7",
  "request_fingerprint": {
    "sha256": "5b4a1b6a89694957d9a7ee5acd0c8660bedd395d7e42471fb87d73b1f838996b",
    "utf8_bytes": 26245
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7925,
    "tokens_out": 13370,
    "cost_usd": 0.0184215,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "aebbbf8451c6034fb4de3206da0dfd3638ce0cdaef22bffe76308f9fdef4fae7",
        "utf8_bytes": 25894
      },
      "response_fingerprint": {
        "sha256": "f9ab398c0268c3e3159426a2bf4a7605b9fcc38a4f2e2d249d4ff0e13b3ba217",
        "utf8_bytes": 39943
      },
      "usage": {
        "completion_tokens": 13370,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2176,
        "prompt_cache_miss_tokens": 5749,
        "prompt_tokens": 7925,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2176,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21295
      },
      "finish_reason": "stop",
      "elapsed": 44.00018239021301
    }
  ]
}
```

</details>

<a id="task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a"></a>

<details>
<summary>s5_track_f · task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a</summary>

```json
{
  "task_id": "task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "3374be6903114b54e7f202561e4840f4c5c1eec1085a32d215f0dcd9df74317e",
  "status": "COMPLETED",
  "reserve": 114477,
  "actual": 7113,
  "created_at": "2026-09-29T22:14:56.666520+00:00",
  "settled_at": "2026-09-29T22:15:08.054081+00:00",
  "node": "s5_track_f",
  "request_fingerprint": {
    "sha256": "1af87bce441b41ae3574dd26f2fc0a4aa742e4b4a0e5829a8892acdd7768b17e",
    "utf8_bytes": 49401
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 14487,
    "tokens_out": 2305,
    "cost_usd": 0.0071121,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "fdd40fed31e5560357a7f2fdc7d09f7f326836ee9508d5a09ed05ff7419addf3",
        "utf8_bytes": 49050
      },
      "response_fingerprint": {
        "sha256": "eb6e7b7750b208480f1783cc3d49cfbf76890d1a586fb012bbf123a15252ab2f",
        "utf8_bytes": 8014
      },
      "usage": {
        "completion_tokens": 2305,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 12439,
        "prompt_tokens": 14487,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 16792
      },
      "finish_reason": "stop",
      "elapsed": 11.116084814071655
    }
  ]
}
```

</details>

<a id="task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7"></a>

<details>
<summary>s5_track_e · task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7</summary>

```json
{
  "task_id": "task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "78e9f0d53a148f8490a444b2d08a8abb4fc3db6b40be5d1aef9a821c1d124232",
  "status": "COMPLETED",
  "reserve": 101685,
  "actual": 6908,
  "created_at": "2026-09-29T22:14:58.232638+00:00",
  "settled_at": "2026-09-29T22:15:13.417490+00:00",
  "node": "s5_track_e",
  "request_fingerprint": {
    "sha256": "82874307466ac9cc45294dbc01f029da658465e232350765344def626ce98d0f",
    "utf8_bytes": 26816
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 7938,
    "tokens_out": 3772,
    "cost_usd": 0.0069078,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "43e8b3de05dbfdd6d79b053d9dfcfa9d9d6d053fc35c4d1e05f13a98c10ada5a",
        "utf8_bytes": 26465
      },
      "response_fingerprint": {
        "sha256": "ecb81e83224dc7f0eda6bca0b60218d348b83add41582b9ecba7633d68c2aad0",
        "utf8_bytes": 12652
      },
      "usage": {
        "completion_tokens": 3772,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 5890,
        "prompt_tokens": 7938,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 11710
      },
      "finish_reason": "stop",
      "elapsed": 15.099320650100708
    }
  ]
}
```

</details>

<a id="task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4"></a>

<details>
<summary>s5_track_c · task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4</summary>

```json
{
  "task_id": "task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "313bd5897d511d19844a4c908027c03fc5390fc354f44a220db39552e50976ce",
  "status": "COMPLETED",
  "reserve": 109677,
  "actual": 9089,
  "created_at": "2026-09-29T22:14:59.786161+00:00",
  "settled_at": "2026-09-29T22:15:16.421542+00:00",
  "node": "s5_track_c",
  "request_fingerprint": {
    "sha256": "8671c3549334d15c9b2423346cf6ecc917ba16aa317126aa50813690d1bab086",
    "utf8_bytes": 40074
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 11698,
    "tokens_out": 4649,
    "cost_usd": 0.0090882,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d501e38fd27f1a3e9f42172ae8f4cc20592761eb5d9e7baee3fad051e6a26fbf",
        "utf8_bytes": 39723
      },
      "response_fingerprint": {
        "sha256": "66741574eb3fa25ea058e982745929f3f03bd7b91345b224ae619f184f97533c",
        "utf8_bytes": 15506
      },
      "usage": {
        "completion_tokens": 4649,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 9650,
        "prompt_tokens": 11698,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 16347
      },
      "finish_reason": "stop",
      "elapsed": 16.558908939361572
    }
  ]
}
```

</details>

<a id="task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a"></a>

<details>
<summary>s5_track_c · task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a</summary>

```json
{
  "task_id": "task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "f85d0d67f5da9db2a8567422af506c20ec46e5832f695a3244026e1a5f2dd59c",
  "status": "COMPLETED",
  "reserve": 109731,
  "actual": 9985,
  "created_at": "2026-09-29T22:15:19.881398+00:00",
  "settled_at": "2026-09-29T22:15:41.125080+00:00",
  "node": "s5_track_c",
  "request_fingerprint": {
    "sha256": "726256ac40fe8138f7e847f1160eda59944552f8637a42e2e09a6b31bef0da0d",
    "utf8_bytes": 40164
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 11742,
    "tokens_out": 5385,
    "cost_usd": 0.0099846,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3e3819cd6e2be2f8ed8f7a36d53b44c84721e96913a6c7a5d22866dc744115b9",
        "utf8_bytes": 39813
      },
      "response_fingerprint": {
        "sha256": "f79975613809eeedb07e5ef967a43530e1e48cdc91e5e15697166cae6de85339",
        "utf8_bytes": 17782
      },
      "usage": {
        "completion_tokens": 5385,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 9694,
        "prompt_tokens": 11742,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 17127
      },
      "finish_reason": "stop",
      "elapsed": 21.168311595916748
    }
  ]
}
```

</details>

<a id="task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf"></a>

<details>
<summary>s5_track_g · task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf</summary>

```json
{
  "task_id": "task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "26f251ec00a48e111271abd83b8614c2f38a62c548ba2938804c7f1863bcdbea",
  "status": "COMPLETED",
  "reserve": 110205,
  "actual": 6812,
  "created_at": "2026-09-29T22:15:53.993224+00:00",
  "settled_at": "2026-09-29T22:16:07.160062+00:00",
  "node": "s5_track_g",
  "request_fingerprint": {
    "sha256": "b13e9cab2e6d2749746cba52002606d3632c1cb0b2b8712a7fef30084185c55e",
    "utf8_bytes": 42195
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 12210,
    "tokens_out": 2624,
    "cost_usd": 0.0068118,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "6479aa424732ad130ddf5a79ecd30b8eb90a749923382dfd220efb3f1f679836",
        "utf8_bytes": 41844
      },
      "response_fingerprint": {
        "sha256": "8ffb71d79807b87c5c867683585e6df24253a2a8d048b6dad403a24859cc2d21",
        "utf8_bytes": 8799
      },
      "usage": {
        "completion_tokens": 2624,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 10162,
        "prompt_tokens": 12210,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 14834
      },
      "finish_reason": "stop",
      "elapsed": 13.094518661499023
    }
  ]
}
```

</details>

<a id="task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b"></a>

<details>
<summary>s5_track_h · task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b</summary>

```json
{
  "task_id": "task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "15c64e3cc9b806086322bdf8b797cf861dc3f17c3d9450a72ef1bf14e574623a",
  "status": "COMPLETED",
  "reserve": 123333,
  "actual": 9272,
  "created_at": "2026-09-29T22:15:55.484759+00:00",
  "settled_at": "2026-09-29T22:16:09.469798+00:00",
  "node": "s5_track_h",
  "request_fingerprint": {
    "sha256": "bbfba677280ae9b61e941cfb8797e69a85faa5c8951acca4e5762a2322248825",
    "utf8_bytes": 64296
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 18926,
    "tokens_out": 2995,
    "cost_usd": 0.009271799999999998,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "759f1857cfd1ac0e11ffd7f5914b24cfe009d7ac06ca6a61c9f56b4e408aafea",
        "utf8_bytes": 63945
      },
      "response_fingerprint": {
        "sha256": "5eb40ca313a9cdad1954b4a3469df1b9810815f34212f342c5ae2eb00f92cc53",
        "utf8_bytes": 10189
      },
      "usage": {
        "completion_tokens": 2995,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 16878,
        "prompt_tokens": 18926,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21921
      },
      "finish_reason": "stop",
      "elapsed": 13.916183948516846
    }
  ]
}
```

</details>

<a id="task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813"></a>

<details>
<summary>s5_merge · task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813</summary>

```json
{
  "task_id": "task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "fc1bc7f7fee5a935432cf3dfc1e9746174efe50596a9eb8d4218223af69bd412",
  "status": "COMPLETED",
  "reserve": 388822,
  "actual": 56918,
  "created_at": "2026-09-29T22:16:17.972695+00:00",
  "settled_at": "2026-09-29T22:16:55.636258+00:00",
  "node": "s5_merge",
  "request_fingerprint": {
    "sha256": "51506b2c56f495f21cbd67638f47b3c72d959a41c559f12eb0c36d60087cba03",
    "utf8_bytes": 529906
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 152433,
    "tokens_out": 9323,
    "cost_usd": 0.0569175,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d6a5d9d1b3b9f9a9514ca013c456c4a8d8d1fa78207baa6635b3c8a8b2f00bd6",
        "utf8_bytes": 529557
      },
      "response_fingerprint": {
        "sha256": "016e39155c4b0d5451dff6c5b0ecd636ee0b9ccf9003732e09e3889db2ad9b1d",
        "utf8_bytes": 28330
      },
      "usage": {
        "completion_tokens": 9323,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 150385,
        "prompt_tokens": 152433,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 161756
      },
      "finish_reason": "stop",
      "elapsed": 37.22539281845093
    }
  ]
}
```

</details>

<a id="task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2"></a>

<details>
<summary>s5_merge · task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2</summary>

```json
{
  "task_id": "task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2",
  "epoch": 50,
  "input_snapshot": "snap-4487c9a6151141879697ca76241925e4",
  "input_hash": "077ca5dd1163c14d0344e3fde518659aef55a51b86a6c33607f8c66d1661a952",
  "status": "COMPLETED",
  "reserve": 406255,
  "actual": 60189,
  "created_at": "2026-09-29T22:17:00.155540+00:00",
  "settled_at": "2026-09-29T22:17:28.511956+00:00",
  "node": "s5_merge",
  "request_fingerprint": {
    "sha256": "d2ca6c15b08318ea00d1fffd037a19cb892d03d94095f065c30cb68cb9af2df7",
    "utf8_bytes": 559547
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 162051,
    "tokens_out": 9644,
    "cost_usd": 0.0601881,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b78f625d5f00f2bb5bd6671258c32ca736b772902166b1f701df03a8fd3408a0",
        "utf8_bytes": 559198
      },
      "response_fingerprint": {
        "sha256": "7141c1743eb87ba02007e87d3372ba732526c463c83e29ca8fd0bf6e1b30160d",
        "utf8_bytes": 29366
      },
      "usage": {
        "completion_tokens": 9644,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 152320,
        "prompt_cache_miss_tokens": 9731,
        "prompt_tokens": 162051,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 152320,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 171695
      },
      "finish_reason": "stop",
      "elapsed": 28.227619171142578
    }
  ]
}
```

</details>

<a id="task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9"></a>

<details>
<summary>s6_concept · task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9</summary>

```json
{
  "task_id": "task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "bcf9e9b831860fb77bdc5ebe1f3eac79e4170243dbe8d77acf4289b694ecca4e",
  "status": "COMPLETED",
  "reserve": 142478,
  "actual": 20201,
  "created_at": "2026-09-29T22:19:02.877410+00:00",
  "settled_at": "2026-09-29T22:19:35.912938+00:00",
  "node": "s6_concept",
  "request_fingerprint": {
    "sha256": "6f6fa3c2786b856228302108f4e5a79135ca24d2e40184b6309112704a3274ce",
    "utf8_bytes": 98084
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 28408,
    "tokens_out": 9732,
    "cost_usd": 0.020200799999999998,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d8e52e2d316e9433802591089b111ca43311e3a3eb212b712e1babd9a6c9a55e",
        "utf8_bytes": 97733
      },
      "response_fingerprint": {
        "sha256": "0860f7f84f52c16e60e31cd6a88bc95810f9e1494b5687e03ba9a8afe527c4ec",
        "utf8_bytes": 32325
      },
      "usage": {
        "completion_tokens": 9732,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 26360,
        "prompt_tokens": 28408,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 38140
      },
      "finish_reason": "stop",
      "elapsed": 32.91397738456726
    }
  ]
}
```

</details>

<a id="task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5"></a>

<details>
<summary>s6_concept · task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5</summary>

```json
{
  "task_id": "task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "985f223e645001c13afc4580a1f644a454bcde945cff6636011c5e4e7ad4e4ed",
  "status": "COMPLETED",
  "reserve": 193272,
  "actual": 22386,
  "created_at": "2026-09-29T22:19:04.520043+00:00",
  "settled_at": "2026-09-29T22:19:24.958801+00:00",
  "node": "s6_concept",
  "request_fingerprint": {
    "sha256": "dce9848c72cfd36a3b72f73f241425161cee2fecab7a04ec7168733808f93a9e",
    "utf8_bytes": 188063
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 55393,
    "tokens_out": 4806,
    "cost_usd": 0.022385099999999998,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "be71a8f5813fd9c6a4436fc5f5894331f53f7923e1d277527b0fedf08c8f9dcf",
        "utf8_bytes": 187712
      },
      "response_fingerprint": {
        "sha256": "4928852d02dffdc103594d036896c770b8145a058c563aea718681607e4a2966",
        "utf8_bytes": 16043
      },
      "usage": {
        "completion_tokens": 4806,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 8960,
        "prompt_cache_miss_tokens": 46433,
        "prompt_tokens": 55393,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 8960,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 60199
      },
      "finish_reason": "stop",
      "elapsed": 19.844725131988525
    }
  ]
}
```

</details>

<a id="task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287"></a>

<details>
<summary>s6_concept · task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287</summary>

```json
{
  "task_id": "task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "15e8f48890026c78dd2cf7f68792aea4f16f58c69c90b0d515318c667a8ac3a8",
  "status": "COMPLETED",
  "reserve": 136714,
  "actual": 15683,
  "created_at": "2026-09-29T22:19:09.268301+00:00",
  "settled_at": "2026-09-29T22:19:33.051749+00:00",
  "node": "s6_concept",
  "request_fingerprint": {
    "sha256": "685cf5ece11037b9398207248f92851849a69d691116ac9f7de9a3dd9ee4f6e9",
    "utf8_bytes": 87547
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 25672,
    "tokens_out": 6651,
    "cost_usd": 0.015682799999999997,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "837992b520b49e35ae07d865d5639dfe1c6023b439c628af55c973cf37292418",
        "utf8_bytes": 87196
      },
      "response_fingerprint": {
        "sha256": "7d56f94468d81922b707bcb83aafff0ebae9dff9cbbbb2fa2b470fd90c2fdb6e",
        "utf8_bytes": 22088
      },
      "usage": {
        "completion_tokens": 6651,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 8960,
        "prompt_cache_miss_tokens": 16712,
        "prompt_tokens": 25672,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 8960,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 32323
      },
      "finish_reason": "stop",
      "elapsed": 23.691229581832886
    }
  ]
}
```

</details>

<a id="task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80"></a>

<details>
<summary>independent_verifier · task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80</summary>

```json
{
  "task_id": "task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "026b83d1f02a042333d0ecb4854159acca1494e55b9c72954000ae4f5d86b42e",
  "status": "COMPLETED",
  "reserve": 60549,
  "actual": 7365,
  "created_at": "2026-09-29T22:19:53.018104+00:00",
  "settled_at": "2026-09-29T22:20:02.331965+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "fe72f874f74018d29320a182b3001f8d71b38b928e95844879ef1fb9d0cd22dd",
    "utf8_bytes": 56180
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 16669,
    "tokens_out": 1970,
    "cost_usd": 0.007364699999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "4e642ca712716c913bb2162712d0f06b0a008f685852f1370dd605d3d37121e9",
        "utf8_bytes": 55820
      },
      "response_fingerprint": {
        "sha256": "e6959db6ec1dd76a0483fb4f9ff87b22c06464d1298556ce1b4479aea83da4c6",
        "utf8_bytes": 6062
      },
      "usage": {
        "completion_tokens": 1970,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 16669,
        "prompt_tokens": 16669,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18639
      },
      "finish_reason": "stop",
      "elapsed": 9.159316778182983
    }
  ]
}
```

</details>

<a id="task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269"></a>

<details>
<summary>independent_verifier · task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269</summary>

```json
{
  "task_id": "task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "2f57809c6fa75fed0bd30d9072cc607bb4a99a5137c08c99cb349b4e44fe0aaa",
  "status": "COMPLETED",
  "reserve": 61113,
  "actual": 7610,
  "created_at": "2026-09-29T22:20:11.874888+00:00",
  "settled_at": "2026-09-29T22:20:21.349457+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "35e89c67a4a4dca7a68e3009198978b5b45b47d6e7f3be5f52e40411dd7853f9",
    "utf8_bytes": 57189
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 16916,
    "tokens_out": 2112,
    "cost_usd": 0.0076092,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "974897aad48c575df49050e3ff7d8cb77b7347b462564782308beb906d58ce93",
        "utf8_bytes": 56829
      },
      "response_fingerprint": {
        "sha256": "258880db53f5be6721352be8ec2036bfb350e8dbe457db9af45257531c62193b",
        "utf8_bytes": 6500
      },
      "usage": {
        "completion_tokens": 2112,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 16916,
        "prompt_tokens": 16916,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 19028
      },
      "finish_reason": "stop",
      "elapsed": 9.305439233779907
    }
  ]
}
```

</details>

<a id="task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9"></a>

<details>
<summary>independent_verifier · task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9</summary>

```json
{
  "task_id": "task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "61a4a7dbf9b73ecd686d0f78fe720d7d5199d894d0fa0ce95764b019a6bdd235",
  "status": "COMPLETED",
  "reserve": 57094,
  "actual": 5809,
  "created_at": "2026-09-29T22:20:31.993809+00:00",
  "settled_at": "2026-09-29T22:20:37.360997+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "def2a37fd73711ef2d09c609f087ee15edac76efadb543ba24c3ba3c6f64ef85",
    "utf8_bytes": 50015
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14833,
    "tokens_out": 1132,
    "cost_usd": 0.0058083,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b3cdaa508e17285dbea6dc9a9d75f4428a38f2458fb95684c0cd3cb15b2b813b",
        "utf8_bytes": 49655
      },
      "response_fingerprint": {
        "sha256": "d5fc494d9dd00d848533919c22451376f32b361337ae61c354730434fde4a954",
        "utf8_bytes": 3670
      },
      "usage": {
        "completion_tokens": 1132,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14833,
        "prompt_tokens": 14833,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15965
      },
      "finish_reason": "stop",
      "elapsed": 5.191119909286499
    }
  ]
}
```

</details>

<a id="task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc"></a>

<details>
<summary>independent_verifier · task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc</summary>

```json
{
  "task_id": "task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "9b52780155dd6266070d109aa7961f8465f0a2931586dc9cfb61992013dcc69d",
  "status": "COMPLETED",
  "reserve": 117767,
  "actual": 15462,
  "created_at": "2026-09-29T22:20:47.569735+00:00",
  "settled_at": "2026-09-29T22:20:55.868819+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "9aa6df46828d6e8a0751515d7b4afc71cb4c704099fbf0c1a74498ee4b53ca02",
    "utf8_bytes": 157260
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 46992,
    "tokens_out": 1137,
    "cost_usd": 0.015461999999999998,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "4ef580b0c5e60953bb099df258d0a10e5756564b488b98f94a42394be39d90dd",
        "utf8_bytes": 156900
      },
      "response_fingerprint": {
        "sha256": "4569d176a63b4dd4b9b9ed72e19c48e8ba9728d5e3dbc8106bebacc84f39575f",
        "utf8_bytes": 3680
      },
      "usage": {
        "completion_tokens": 1137,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 46992,
        "prompt_tokens": 46992,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 48129
      },
      "finish_reason": "stop",
      "elapsed": 7.405031204223633
    }
  ]
}
```

</details>

<a id="task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809"></a>

<details>
<summary>independent_verifier · task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809</summary>

```json
{
  "task_id": "task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809",
  "epoch": 50,
  "input_snapshot": "snap-79aadae8281243288bb60a7919a19408",
  "input_hash": "25b4177497e1d819c96259d38ae0da8a2d4d2b9f4cd3074b107a6b0dd2d3ad86",
  "status": "COMPLETED",
  "reserve": 50567,
  "actual": 4978,
  "created_at": "2026-09-29T22:21:06.879859+00:00",
  "settled_at": "2026-09-29T22:21:13.380391+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "a7e2379d8274dc1e0f062363ca19b98c414f3ab246d679880eb643fb920d7dca",
    "utf8_bytes": 38540
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 11464,
    "tokens_out": 1282,
    "cost_usd": 0.0049775999999999996,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "51ac75169d6e8a18ad1de681f25b69ed162407f635f3ae5ceca05455f8592c2e",
        "utf8_bytes": 38180
      },
      "response_fingerprint": {
        "sha256": "9fce8639ba35b189ae1d6227cb38155406f1ca78762f294dde7f8350486a04ee",
        "utf8_bytes": 4189
      },
      "usage": {
        "completion_tokens": 1282,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 11464,
        "prompt_tokens": 11464,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 12746
      },
      "finish_reason": "stop",
      "elapsed": 6.399843692779541
    }
  ]
}
```

</details>

<a id="task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0"></a>

<details>
<summary>ax_repair_gap-99452800a5dc788ae3d52b55_0 · task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0</summary>

```json
{
  "task_id": "task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "63c3fc993ee92dce8c1252183b1a73232719438f0676b5080290291c88a34cb1",
  "status": "COMPLETED",
  "reserve": 120643,
  "actual": 10012,
  "created_at": "2026-09-29T22:22:21.660939+00:00",
  "settled_at": "2026-09-29T22:22:37.548021+00:00",
  "node": "ax_repair_gap-99452800a5dc788ae3d52b55_0",
  "request_fingerprint": {
    "sha256": "315d262e705ee554ad9e666617522817c18eeb28e2679acd3f70294aab9782ff",
    "utf8_bytes": 62295
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17525,
    "tokens_out": 3962,
    "cost_usd": 0.010011899999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c1cc72ad92e811a99bf01e43d498f9689ae97e9f5689917fbae1ab9934411507",
        "utf8_bytes": 61915
      },
      "response_fingerprint": {
        "sha256": "429fb83950703fffbc9c50681914b258685bfa89869f03a172073e10d5c686a2",
        "utf8_bytes": 12901
      },
      "usage": {
        "completion_tokens": 3962,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 15477,
        "prompt_tokens": 17525,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21487
      },
      "finish_reason": "stop",
      "elapsed": 15.510929346084595
    }
  ]
}
```

</details>

<a id="task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4"></a>

<details>
<summary>independent_verifier · task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4</summary>

```json
{
  "task_id": "task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "f53f0826e46ce068fd91056931082b108091a9db20be99ce7b57028e1a26c20b",
  "status": "COMPLETED",
  "reserve": 56011,
  "actual": 5958,
  "created_at": "2026-09-29T22:22:41.491564+00:00",
  "settled_at": "2026-09-29T22:22:49.583007+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "316ea39e16caf55b5cde6a7714408ba989480531a6d2b4e948587c9bc86bc7ee",
    "utf8_bytes": 47980
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14408,
    "tokens_out": 1363,
    "cost_usd": 0.005958,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "fb25a0b57c01345e0f1c6359e1e32cb19dd2986e787646a4108bafaccc90ab10",
        "utf8_bytes": 47620
      },
      "response_fingerprint": {
        "sha256": "8c689aef6a55c59e23362f77ee83c6897b39ef8b48fa100e5088f3d9f930bad3",
        "utf8_bytes": 4333
      },
      "usage": {
        "completion_tokens": 1363,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14408,
        "prompt_tokens": 14408,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15771
      },
      "finish_reason": "stop",
      "elapsed": 7.372077703475952
    }
  ]
}
```

</details>

<a id="task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029"></a>

<details>
<summary>ax_repair_gap-99452800a5dc788ae3d52b55_1 · task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029</summary>

```json
{
  "task_id": "task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "a5292dd08311f3744b38995fac23540bbe52c64a6f7b601dde28130467232666",
  "status": "COMPLETED",
  "reserve": 120643,
  "actual": 10507,
  "created_at": "2026-09-29T22:23:05.291441+00:00",
  "settled_at": "2026-09-29T22:23:21.864218+00:00",
  "node": "ax_repair_gap-99452800a5dc788ae3d52b55_1",
  "request_fingerprint": {
    "sha256": "48eec67c1f521a098545fb947e6f9789462a073231dbc081b803eb571d8bc7d8",
    "utf8_bytes": 62295
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17525,
    "tokens_out": 4374,
    "cost_usd": 0.0105063,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c1cc72ad92e811a99bf01e43d498f9689ae97e9f5689917fbae1ab9934411507",
        "utf8_bytes": 61915
      },
      "response_fingerprint": {
        "sha256": "3a9557e8b6841467454be1031db16becdc8b16588695568c8f05a8c8407eae7b",
        "utf8_bytes": 14543
      },
      "usage": {
        "completion_tokens": 4374,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 17280,
        "prompt_cache_miss_tokens": 245,
        "prompt_tokens": 17525,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 17280,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21899
      },
      "finish_reason": "stop",
      "elapsed": 15.759472131729126
    }
  ]
}
```

</details>

<a id="task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b"></a>

<details>
<summary>independent_verifier · task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b</summary>

```json
{
  "task_id": "task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "a9fa1223dc130d2231a7436c46f0a7a0afc2e1c4b04de5bde6ac00a110280fbe",
  "status": "COMPLETED",
  "reserve": 55551,
  "actual": 5863,
  "created_at": "2026-09-29T22:23:26.219074+00:00",
  "settled_at": "2026-09-29T22:23:34.532636+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "014a13e72c80282045693f523900f186277ecda4e45e52d49a80c455cb5ea634",
    "utf8_bytes": 47161
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14053,
    "tokens_out": 1372,
    "cost_usd": 0.0058623,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "1d9cac43d88b9ccedadde836d308589f41c97542fea3268a6cffd20afa723608",
        "utf8_bytes": 46801
      },
      "response_fingerprint": {
        "sha256": "df2f2d250520e6617427ba09aa8692ffb0c813168d3ce1e394c94dd1bbe2ad7a",
        "utf8_bytes": 4463
      },
      "usage": {
        "completion_tokens": 1372,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14053,
        "prompt_tokens": 14053,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15425
      },
      "finish_reason": "stop",
      "elapsed": 6.630642414093018
    }
  ]
}
```

</details>

<a id="task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f"></a>

<details>
<summary>ax_repair_gap-ee8407b02217eddd77e4bfbd_0 · task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f</summary>

```json
{
  "task_id": "task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "61127a3818cc415e89f144ee5f946a701a29a8840b3ec0da8410d03c546887f3",
  "status": "COMPLETED",
  "reserve": 120461,
  "actual": 11715,
  "created_at": "2026-09-29T22:23:50.953291+00:00",
  "settled_at": "2026-09-29T22:24:14.024210+00:00",
  "node": "ax_repair_gap-ee8407b02217eddd77e4bfbd_0",
  "request_fingerprint": {
    "sha256": "42a286e13b77a0632ee85c8e70752d2a401eb7083b76ea27eb7a5dbbeba6a7ab",
    "utf8_bytes": 61961
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17399,
    "tokens_out": 5412,
    "cost_usd": 0.0117141,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "dcc876c42fb818f358ecdab99233bfd8bae28037d93fc34e9e7559102161b3e9",
        "utf8_bytes": 61581
      },
      "response_fingerprint": {
        "sha256": "5edaf39450d4dec77d90cd6137f979f47a8359c84779b967eb0e80f94c36a53c",
        "utf8_bytes": 17841
      },
      "usage": {
        "completion_tokens": 5412,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2944,
        "prompt_cache_miss_tokens": 14455,
        "prompt_tokens": 17399,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2944,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 22811
      },
      "finish_reason": "stop",
      "elapsed": 22.97486639022827
    }
  ]
}
```

</details>

<a id="task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728"></a>

<details>
<summary>independent_verifier · task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728</summary>

```json
{
  "task_id": "task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "a25a9e3ea9f709a73ab3a87ac7491d25a6285051bf41409b156563ea08d33008",
  "status": "COMPLETED",
  "reserve": 57102,
  "actual": 5893,
  "created_at": "2026-09-29T22:24:17.654424+00:00",
  "settled_at": "2026-09-29T22:24:23.802690+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "4df4355fa41d2040d3225bf7b5a7550328d11bca5af17d61b2eedda51ceeea20",
    "utf8_bytes": 49767
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14858,
    "tokens_out": 1196,
    "cost_usd": 0.0058926,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3302fdb69e0b3bb77f7c829dc382e567b8520118f57a071deafc0782ef58dd54",
        "utf8_bytes": 49407
      },
      "response_fingerprint": {
        "sha256": "3eb4fa88dcc84c9c982e937ea9dd9b2e3509e628135b9df153b89758668257a1",
        "utf8_bytes": 3707
      },
      "usage": {
        "completion_tokens": 1196,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14858,
        "prompt_tokens": 14858,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 16054
      },
      "finish_reason": "stop",
      "elapsed": 6.005134582519531
    }
  ]
}
```

</details>

<a id="task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24"></a>

<details>
<summary>ax_repair_gap-ee8407b02217eddd77e4bfbd_1 · task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24</summary>

```json
{
  "task_id": "task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "7c717feea5799aa554962767ba472efcee0c0267269a2f6364e5bf855b7c22d6",
  "status": "COMPLETED",
  "reserve": 120461,
  "actual": 11122,
  "created_at": "2026-09-29T22:24:42.703407+00:00",
  "settled_at": "2026-09-29T22:25:02.207908+00:00",
  "node": "ax_repair_gap-ee8407b02217eddd77e4bfbd_1",
  "request_fingerprint": {
    "sha256": "64eb3866c14ffbbfb81d1ac93c11d06449627696604096620dd163b528e6e51e",
    "utf8_bytes": 61961
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17399,
    "tokens_out": 4918,
    "cost_usd": 0.011121299999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "dcc876c42fb818f358ecdab99233bfd8bae28037d93fc34e9e7559102161b3e9",
        "utf8_bytes": 61581
      },
      "response_fingerprint": {
        "sha256": "9d07f12fe4fcb58bc26b3b8d7110820ffd0a9ec37a07dbb1bf9dd528a7b5856a",
        "utf8_bytes": 16176
      },
      "usage": {
        "completion_tokens": 4918,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 17152,
        "prompt_cache_miss_tokens": 247,
        "prompt_tokens": 17399,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 17152,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 22317
      },
      "finish_reason": "stop",
      "elapsed": 19.404163599014282
    }
  ]
}
```

</details>

<a id="task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce"></a>

<details>
<summary>independent_verifier · task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce</summary>

```json
{
  "task_id": "task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce",
  "epoch": 50,
  "input_snapshot": "snap-5cf9be1da04042098bf9bd21706c7945",
  "input_hash": "bc05e6653a2b7163133e59fdb2569fa6bfc1a9185d5c77e839b87a04a8055124",
  "status": "COMPLETED",
  "reserve": 56229,
  "actual": 6064,
  "created_at": "2026-09-29T22:25:08.125127+00:00",
  "settled_at": "2026-09-29T22:25:14.751199+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "b523d5c06eb1fbc200d60ba420a17cb2d4aff99bc2ea3c87098382878494832b",
    "utf8_bytes": 48316
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14423,
    "tokens_out": 1447,
    "cost_usd": 0.0060633,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "f8d07218dce383851c1cccd983f857c5cebdc2d7f33e005ca844c6fe992ef4ba",
        "utf8_bytes": 47956
      },
      "response_fingerprint": {
        "sha256": "28c92ca225eb920ca746603672cf722eff43aa2cfe59a56ea13b7ef5fe6e4127",
        "utf8_bytes": 4549
      },
      "usage": {
        "completion_tokens": 1447,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14423,
        "prompt_tokens": 14423,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15870
      },
      "finish_reason": "stop",
      "elapsed": 6.532864093780518
    }
  ]
}
```

</details>

<a id="task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1"></a>

<details>
<summary>s7_gate_2 · task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1</summary>

```json
{
  "task_id": "task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "95fe374c8973826ed49df88dc9ade9ff5ff5b1276e8be0b2a39fe6579dfafd71",
  "status": "COMPLETED",
  "reserve": 95934,
  "actual": 2549,
  "created_at": "2026-09-29T22:25:51.982521+00:00",
  "settled_at": "2026-09-29T22:25:59.077370+00:00",
  "node": "s7_gate_2",
  "request_fingerprint": {
    "sha256": "8f4a5f87740cc52b185d68fc13a58554bb69d4ac105f513baec08485e3056290",
    "utf8_bytes": 17779
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4710,
    "tokens_out": 946,
    "cost_usd": 0.0025482,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "56481c7ec4195a41f629cf4e532f36c7d13f68edcd1825f70867ca02c1fef7ff",
        "utf8_bytes": 17430
      },
      "response_fingerprint": {
        "sha256": "8298bf5279363b03eb93707e3af9091e954a61a587aa5ffd4552577fb2824209",
        "utf8_bytes": 2949
      },
      "usage": {
        "completion_tokens": 946,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 128,
        "prompt_cache_miss_tokens": 4582,
        "prompt_tokens": 4710,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 128,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5656
      },
      "finish_reason": "stop",
      "elapsed": 3.921764373779297
    }
  ]
}
```

</details>

<a id="task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b"></a>

<details>
<summary>s7_gate_3 · task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b</summary>

```json
{
  "task_id": "task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "5740e6e5ead6044807891bfecdd1fef9092a0d2a96b35a7b53ae1cb947981ba1",
  "status": "COMPLETED",
  "reserve": 95983,
  "actual": 2536,
  "created_at": "2026-09-29T22:25:53.668584+00:00",
  "settled_at": "2026-09-29T22:25:59.206898+00:00",
  "node": "s7_gate_3",
  "request_fingerprint": {
    "sha256": "b46ba681e5516e2a043c61ba27fad460992e61cc2c8edd0e1fda3cb1355719e9",
    "utf8_bytes": 17862
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4751,
    "tokens_out": 925,
    "cost_usd": 0.0025353,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "7e4065310e8c1451594b7be60371d1d236802b1d621c03be8388fc682e01c2d7",
        "utf8_bytes": 17513
      },
      "response_fingerprint": {
        "sha256": "f50415958d765ef8dd953a39a165a2bec3c2cfd3cc97f4676e04ea0dd315f574",
        "utf8_bytes": 2900
      },
      "usage": {
        "completion_tokens": 925,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2703,
        "prompt_tokens": 4751,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5676
      },
      "finish_reason": "stop",
      "elapsed": 4.292987108230591
    }
  ]
}
```

</details>

<a id="task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8"></a>

<details>
<summary>s7_gate_1 · task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8</summary>

```json
{
  "task_id": "task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "b7a8dd5f90f26bfa44181629d6b8956e2c7a713d124995317709e67392372384",
  "status": "COMPLETED",
  "reserve": 96177,
  "actual": 2569,
  "created_at": "2026-09-29T22:25:55.391692+00:00",
  "settled_at": "2026-09-29T22:25:59.576041+00:00",
  "node": "s7_gate_1",
  "request_fingerprint": {
    "sha256": "c60a9c385290f5c050bf1e05615621b6f7eeeafbcdc13592b99367c00225ed42",
    "utf8_bytes": 18188
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4850,
    "tokens_out": 928,
    "cost_usd": 0.0025686,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d1442bbca2f16d84f5f5caadf9dc0660ac0179459e4a67f3805db55dd3f70856",
        "utf8_bytes": 17839
      },
      "response_fingerprint": {
        "sha256": "3e1df1ec1bac7cbfd2040910c5a33178cb1b423019b7774e0d967dc25e13dd4b",
        "utf8_bytes": 2841
      },
      "usage": {
        "completion_tokens": 928,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2802,
        "prompt_tokens": 4850,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5778
      },
      "finish_reason": "stop",
      "elapsed": 4.047523260116577
    }
  ]
}
```

</details>

<a id="task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848"></a>

<details>
<summary>s7_gate_4 · task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848</summary>

```json
{
  "task_id": "task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "041116dc0011ab7d2df7f990404fc4d057e7bb41e8671d3e4758c97b99a40012",
  "status": "COMPLETED",
  "reserve": 95966,
  "actual": 2574,
  "created_at": "2026-09-29T22:25:59.011691+00:00",
  "settled_at": "2026-09-29T22:26:09.101529+00:00",
  "node": "s7_gate_4",
  "request_fingerprint": {
    "sha256": "f84eacfb767787ee19ee14faea40903423ab8cac98b84fece2b36d807e03617f",
    "utf8_bytes": 17824
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4748,
    "tokens_out": 958,
    "cost_usd": 0.002574,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "f24eb413a94bc3ace3ff510bf390336294b43c028668ca6d4673c5d85d2f89f8",
        "utf8_bytes": 17475
      },
      "response_fingerprint": {
        "sha256": "56a1ef23cf5aba8e916fe762283b3a474d2d6128d8844d5cb81b2e1d4116795d",
        "utf8_bytes": 3001
      },
      "usage": {
        "completion_tokens": 958,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2700,
        "prompt_tokens": 4748,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5706
      },
      "finish_reason": "stop",
      "elapsed": 4.7850518226623535
    }
  ]
}
```

</details>

<a id="task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8"></a>

<details>
<summary>s7_gate_6 · task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8</summary>

```json
{
  "task_id": "task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "e4f2adb2aea334e04e736c248a364d138af142c031736f5bb7f6bae7a5c551a4",
  "status": "COMPLETED",
  "reserve": 95708,
  "actual": 2417,
  "created_at": "2026-09-29T22:26:05.842722+00:00",
  "settled_at": "2026-09-29T22:26:10.576663+00:00",
  "node": "s7_gate_6",
  "request_fingerprint": {
    "sha256": "f0dbfde5c4d3eea6d6bf5fa19dbb289b4897054db1abd572d280644b4bc04ad4",
    "utf8_bytes": 17393
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4596,
    "tokens_out": 865,
    "cost_usd": 0.0024168,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "df3ec633cdb1c553e6f91669b2b147b1fc1e059a4c76dc2171fcf6252a3e9ce2",
        "utf8_bytes": 17044
      },
      "response_fingerprint": {
        "sha256": "f53761ffaaaf94a10e6492fa133ce8d9520a4568f35e211015bdbd369ee8292f",
        "utf8_bytes": 2715
      },
      "usage": {
        "completion_tokens": 865,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2548,
        "prompt_tokens": 4596,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5461
      },
      "finish_reason": "stop",
      "elapsed": 3.6529619693756104
    }
  ]
}
```

</details>

<a id="task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131"></a>

<details>
<summary>s7_gate_5 · task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131</summary>

```json
{
  "task_id": "task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "838acdb6b09b7d723a73e495dd1bfa37c63c81a160d974a7aa3c5dfdbf62bcc7",
  "status": "COMPLETED",
  "reserve": 95577,
  "actual": 2320,
  "created_at": "2026-09-29T22:26:07.415288+00:00",
  "settled_at": "2026-09-29T22:26:14.990931+00:00",
  "node": "s7_gate_5",
  "request_fingerprint": {
    "sha256": "75229269b03585c5019d187edbea51621646cfe9b6b2d09a1bc2dd5960a117c8",
    "utf8_bytes": 17164
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4532,
    "tokens_out": 800,
    "cost_usd": 0.0023196,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ee3baf6559c698a2ee405df58149b6a3f6559d505d390471cf920ac9502d6a39",
        "utf8_bytes": 16815
      },
      "response_fingerprint": {
        "sha256": "e92895b4dbce6de1f3befc1786a48104bc2c08e821db5bfa59954bcdeb72ab7e",
        "utf8_bytes": 2484
      },
      "usage": {
        "completion_tokens": 800,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2484,
        "prompt_tokens": 4532,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5332
      },
      "finish_reason": "stop",
      "elapsed": 3.3458080291748047
    }
  ]
}
```

</details>

<a id="task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e"></a>

<details>
<summary>s7_gate_7 · task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e</summary>

```json
{
  "task_id": "task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "70bbe7148a5637044b22fcdacc458c684d34d42804b69fccc56fbe81a7ed3539",
  "status": "COMPLETED",
  "reserve": 95801,
  "actual": 2539,
  "created_at": "2026-09-29T22:26:09.026127+00:00",
  "settled_at": "2026-09-29T22:26:15.096816+00:00",
  "node": "s7_gate_7",
  "request_fingerprint": {
    "sha256": "a79576e06ccf6168a432b3f796056de8ed720a0311c450c1011c103080763ef0",
    "utf8_bytes": 17546
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4609,
    "tokens_out": 963,
    "cost_usd": 0.0025383,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "1e466785e5f43a697b52c23e6056c8a6234b1503f978096a5edd5e0cc28a484d",
        "utf8_bytes": 17197
      },
      "response_fingerprint": {
        "sha256": "c96cf0c55b4e517b9b35557a1bea47af62676ef942c22032f4597bf120365a5b",
        "utf8_bytes": 3002
      },
      "usage": {
        "completion_tokens": 963,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2561,
        "prompt_tokens": 4609,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5572
      },
      "finish_reason": "stop",
      "elapsed": 4.237914323806763
    }
  ]
}
```

</details>

<a id="task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f"></a>

<details>
<summary>s7_gate_8 · task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f</summary>

```json
{
  "task_id": "task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "b408ceeb7d7993c5742ab3525e110204d2371f77539cdcb95f23bfd9dda58d38",
  "status": "COMPLETED",
  "reserve": 95936,
  "actual": 2446,
  "created_at": "2026-09-29T22:26:14.922056+00:00",
  "settled_at": "2026-09-29T22:26:21.387695+00:00",
  "node": "s7_gate_8",
  "request_fingerprint": {
    "sha256": "5e0d3975add66ea3a717c0c9cbefbf2daa494e5d210734e559d4c45fe76b1568",
    "utf8_bytes": 17775
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4721,
    "tokens_out": 858,
    "cost_usd": 0.0024459,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "dda268baba69bffb0e817fd31a1714ec87ada10e974e5f45adc0f90be44d802a",
        "utf8_bytes": 17426
      },
      "response_fingerprint": {
        "sha256": "6cf00b565fc6edb0f4eb09024e0fe57412589d5c9398ac70306bb069edc0c239",
        "utf8_bytes": 2632
      },
      "usage": {
        "completion_tokens": 858,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2673,
        "prompt_tokens": 4721,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5579
      },
      "finish_reason": "stop",
      "elapsed": 3.9855196475982666
    }
  ]
}
```

</details>

<a id="task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa"></a>

<details>
<summary>s7_gate_9 · task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa</summary>

```json
{
  "task_id": "task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "13092178caa09f5b2a4b885fe162779fef7e7ff40210e62516fec21dd83e19bd",
  "status": "COMPLETED",
  "reserve": 96328,
  "actual": 2623,
  "created_at": "2026-09-29T22:26:19.750212+00:00",
  "settled_at": "2026-09-29T22:26:24.600445+00:00",
  "node": "s7_gate_9",
  "request_fingerprint": {
    "sha256": "acb737dff022156a3416048f75bd875bd4ac497b7b460bf1a0b152f374fde8f6",
    "utf8_bytes": 18425
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4897,
    "tokens_out": 961,
    "cost_usd": 0.0026223,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "841159bdf6163f868a52513f8cda32ade87e934f9eee51ca5342a8866ae46a48",
        "utf8_bytes": 18076
      },
      "response_fingerprint": {
        "sha256": "f1c5bd32073a0039eff809a8c77f7dc4921570b1b97aaeefac8664ba912bacd3",
        "utf8_bytes": 2986
      },
      "usage": {
        "completion_tokens": 961,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2849,
        "prompt_tokens": 4897,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5858
      },
      "finish_reason": "stop",
      "elapsed": 4.314497709274292
    }
  ]
}
```

</details>

<a id="task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273"></a>

<details>
<summary>s7_gate_10 · task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273</summary>

```json
{
  "task_id": "task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273",
  "epoch": 50,
  "input_snapshot": "snap-449e8133744e4505b9e5affe26a8b9d4",
  "input_hash": "91f8ac208cec62fa8988722d37385fc720f9c20d32092101bc5cd0ced72f4b58",
  "status": "COMPLETED",
  "reserve": 95808,
  "actual": 2506,
  "created_at": "2026-09-29T22:26:21.308864+00:00",
  "settled_at": "2026-09-29T22:26:25.073469+00:00",
  "node": "s7_gate_10",
  "request_fingerprint": {
    "sha256": "b7674fe0cc8f8e685856fca02f8e2924b6e41be21f94bf5e4a7f6d96dba58b16",
    "utf8_bytes": 17563
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 4647,
    "tokens_out": 926,
    "cost_usd": 0.0025053,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "fd710cf0deaca5b81f981e2c97599f0f5414610c02dc4885d5472ab1d7136f9d",
        "utf8_bytes": 17213
      },
      "response_fingerprint": {
        "sha256": "58c14d9799329958464927acac7b5af800096da4d7136d3d5b12ed5b76c35360",
        "utf8_bytes": 3031
      },
      "usage": {
        "completion_tokens": 926,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 2599,
        "prompt_tokens": 4647,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 5573
      },
      "finish_reason": "stop",
      "elapsed": 3.6865599155426025
    }
  ]
}
```

</details>

<a id="task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72"></a>

<details>
<summary>ax_repair_gap-80693d8f5a5d25a6d2dfa098_0 · task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72</summary>

```json
{
  "task_id": "task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "793965d8eff9c7edf8f037933d4e411d049cbe9c6e2435fa1fa7e2686cd4d0ae",
  "status": "COMPLETED",
  "reserve": 120562,
  "actual": 9660,
  "created_at": "2026-09-29T22:33:06.427463+00:00",
  "settled_at": "2026-09-29T22:33:21.928778+00:00",
  "node": "ax_repair_gap-80693d8f5a5d25a6d2dfa098_0",
  "request_fingerprint": {
    "sha256": "39087fdf6c3e11383babbf69b8df29e695893f41a54571e137d6e1064f7caa17",
    "utf8_bytes": 62204
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17534,
    "tokens_out": 3666,
    "cost_usd": 0.0096594,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3136125f87337795506518b47a31339d703efdd7928bc9f2e9bf55947c438a89",
        "utf8_bytes": 61824
      },
      "response_fingerprint": {
        "sha256": "cad9754e1c96f3d281df31883226743f24515b321f1148fc667cde1797231833",
        "utf8_bytes": 12035
      },
      "usage": {
        "completion_tokens": 3666,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2944,
        "prompt_cache_miss_tokens": 14590,
        "prompt_tokens": 17534,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2944,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21200
      },
      "finish_reason": "stop",
      "elapsed": 15.385301351547241
    }
  ]
}
```

</details>

<a id="task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b"></a>

<details>
<summary>independent_verifier · task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b</summary>

```json
{
  "task_id": "task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "40072ad616fe09f0091b07b012ac495011ac30b52e1cb1424cecb72484f1fb45",
  "status": "COMPLETED",
  "reserve": 55659,
  "actual": 5726,
  "created_at": "2026-09-29T22:33:28.087311+00:00",
  "settled_at": "2026-09-29T22:33:34.160585+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "e3b080a3417e66d9baa2e22b5b3d0eae1439de2d2b873bcf2a7d7243ec02ddb1",
    "utf8_bytes": 47468
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14260,
    "tokens_out": 1206,
    "cost_usd": 0.0057252,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "84e8ca6239c686169011cf5334e771aa84402a0e6607e49c5a9e78c480048443",
        "utf8_bytes": 47108
      },
      "response_fingerprint": {
        "sha256": "5d8d8af0fbaed38b2b23d6cef962eb7258a71ff431f5499b152c6272d2409d39",
        "utf8_bytes": 3798
      },
      "usage": {
        "completion_tokens": 1206,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14260,
        "prompt_tokens": 14260,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15466
      },
      "finish_reason": "stop",
      "elapsed": 5.957428216934204
    }
  ]
}
```

</details>

<a id="task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599"></a>

<details>
<summary>ax_repair_gap-80693d8f5a5d25a6d2dfa098_1 · task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599</summary>

```json
{
  "task_id": "task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "2b6017a6b1caa303dae140a43b219f341a9e82758f1feafbc222284f5ef0a70f",
  "status": "COMPLETED",
  "reserve": 120562,
  "actual": 10291,
  "created_at": "2026-09-29T22:33:51.620465+00:00",
  "settled_at": "2026-09-29T22:34:09.105507+00:00",
  "node": "ax_repair_gap-80693d8f5a5d25a6d2dfa098_1",
  "request_fingerprint": {
    "sha256": "774a1561d92d2ce9b4b1fa9967440da3568fbeccd5eb0c19d8dc015c7221cfe7",
    "utf8_bytes": 62204
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17534,
    "tokens_out": 4192,
    "cost_usd": 0.0102906,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "3136125f87337795506518b47a31339d703efdd7928bc9f2e9bf55947c438a89",
        "utf8_bytes": 61824
      },
      "response_fingerprint": {
        "sha256": "55c1be4cb6c4da3e8a5811ed905ef74c5a8f219d70fbde3d84c9d8d188e9f93b",
        "utf8_bytes": 13585
      },
      "usage": {
        "completion_tokens": 4192,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 17280,
        "prompt_cache_miss_tokens": 254,
        "prompt_tokens": 17534,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 17280,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21726
      },
      "finish_reason": "stop",
      "elapsed": 17.403745412826538
    }
  ]
}
```

</details>

<a id="task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025"></a>

<details>
<summary>independent_verifier · task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025</summary>

```json
{
  "task_id": "task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "a947e74c0fac6a8b07295b3e861c11bc06dea1ae1f11e17fe496f1d9bee7327d",
  "status": "COMPLETED",
  "reserve": 56562,
  "actual": 5578,
  "created_at": "2026-09-29T22:34:12.817876+00:00",
  "settled_at": "2026-09-29T22:34:18.115855+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "e2a092d45bd77e602348b25608f354f2a1c9b82f0941e0410c1629afba8ed8bf",
    "utf8_bytes": 49018
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 14772,
    "tokens_out": 955,
    "cost_usd": 0.0055776,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "7f0f2a50d2a8f693e26a1e246a702d0e92c6fc5f61ec03df26fe9ad5604e1397",
        "utf8_bytes": 48658
      },
      "response_fingerprint": {
        "sha256": "b0e92c7094c112f875d6e78532115ce176dcc84ab9ef669156b86f49830b64ba",
        "utf8_bytes": 3033
      },
      "usage": {
        "completion_tokens": 955,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 14772,
        "prompt_tokens": 14772,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15727
      },
      "finish_reason": "stop",
      "elapsed": 5.220940589904785
    }
  ]
}
```

</details>

<a id="task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64"></a>

<details>
<summary>ax_repair_gap-23e4763bd7081652230dfb23_0 · task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64</summary>

```json
{
  "task_id": "task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "9cfd3d0ded4cd69be337aa6c5bb1ab4d0e94f3e7746ae37fd02e6c76e498ee5b",
  "status": "COMPLETED",
  "reserve": 119866,
  "actual": 10274,
  "created_at": "2026-09-29T22:34:32.677053+00:00",
  "settled_at": "2026-09-29T22:34:50.520730+00:00",
  "node": "ax_repair_gap-23e4763bd7081652230dfb23_0",
  "request_fingerprint": {
    "sha256": "199820c6a9591aa79acf8e5734f926a1f0dec04f61375868d5014409b70f8cea",
    "utf8_bytes": 60964
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17094,
    "tokens_out": 4288,
    "cost_usd": 0.0102738,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "e25312926a4f63a639f74a8a80d2c028f708dfba0b8f3cb0f87e9c6caa1f6079",
        "utf8_bytes": 60584
      },
      "response_fingerprint": {
        "sha256": "b97aef94c729f1ee2a3098dde9555ea5aa9fd898257922cea3cc3d2e0d3826c3",
        "utf8_bytes": 13984
      },
      "usage": {
        "completion_tokens": 4288,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2944,
        "prompt_cache_miss_tokens": 14150,
        "prompt_tokens": 17094,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2944,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21382
      },
      "finish_reason": "stop",
      "elapsed": 17.71977925300598
    }
  ]
}
```

</details>

<a id="task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56"></a>

<details>
<summary>independent_verifier · task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56</summary>

```json
{
  "task_id": "task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "69ba794b058255f3b81fcd7f3c2d2992abb46a419e318392ba1de5ad15caf643",
  "status": "COMPLETED",
  "reserve": 55020,
  "actual": 6041,
  "created_at": "2026-09-29T22:34:56.471433+00:00",
  "settled_at": "2026-09-29T22:35:04.010080+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "bad713cffe1af4d98c9cda84a02766f0653386d383c6cfc1bc294cacffd21a32",
    "utf8_bytes": 46132
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 13831,
    "tokens_out": 1576,
    "cost_usd": 0.0060405,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "90c866d014cbbcefbecc84a851dc566f3497ccca0f7ea2856951eb8c9c40aa54",
        "utf8_bytes": 45772
      },
      "response_fingerprint": {
        "sha256": "9c4f19bd8682b5652e8b53e6487b377e6cf61e410df7cf610cd99db176ca6e65",
        "utf8_bytes": 5018
      },
      "usage": {
        "completion_tokens": 1576,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 13831,
        "prompt_tokens": 13831,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 15407
      },
      "finish_reason": "stop",
      "elapsed": 7.449976205825806
    }
  ]
}
```

</details>

<a id="task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7"></a>

<details>
<summary>ax_repair_gap-23e4763bd7081652230dfb23_1 · task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7</summary>

```json
{
  "task_id": "task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "634826f8db3ef7694cdd411bb7bce4b2edcb33df129ef9f938f102105b2269b7",
  "status": "COMPLETED",
  "reserve": 119866,
  "actual": 9956,
  "created_at": "2026-09-29T22:35:19.900763+00:00",
  "settled_at": "2026-09-29T22:35:36.492845+00:00",
  "node": "ax_repair_gap-23e4763bd7081652230dfb23_1",
  "request_fingerprint": {
    "sha256": "2203c6674b4eb3126dd52e0b54997ad90219ca71de2738546e37e7bb77d9165b",
    "utf8_bytes": 60964
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 17094,
    "tokens_out": 4023,
    "cost_usd": 0.0099558,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "e25312926a4f63a639f74a8a80d2c028f708dfba0b8f3cb0f87e9c6caa1f6079",
        "utf8_bytes": 60584
      },
      "response_fingerprint": {
        "sha256": "ac23079c09f2eec88b924bf540deaeecd1eaced8563e5e2561173fae7b6f78d7",
        "utf8_bytes": 13139
      },
      "usage": {
        "completion_tokens": 4023,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 16896,
        "prompt_cache_miss_tokens": 198,
        "prompt_tokens": 17094,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 16896,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 21117
      },
      "finish_reason": "stop",
      "elapsed": 16.51467728614807
    }
  ]
}
```

</details>

<a id="task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3"></a>

<details>
<summary>independent_verifier · task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3</summary>

```json
{
  "task_id": "task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3",
  "epoch": 51,
  "input_snapshot": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
  "input_hash": "44a1764d889f5072137899e6eebecac57029655301dabe47f5b54e9926ba074c",
  "status": "COMPLETED",
  "reserve": 54489,
  "actual": 5596,
  "created_at": "2026-09-29T22:35:40.748860+00:00",
  "settled_at": "2026-09-29T22:35:47.334803+00:00",
  "node": "independent_verifier",
  "request_fingerprint": {
    "sha256": "98b69679b6d3d8d0de271c60df7249fd527a2f8829268f409286b9da5cfe601f",
    "utf8_bytes": 45244
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 13565,
    "tokens_out": 1272,
    "cost_usd": 0.0055959,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ceb7548d50a8d0ee549af5a88ca7ac832042fde46664593939acfdb37c1cdcba",
        "utf8_bytes": 44884
      },
      "response_fingerprint": {
        "sha256": "ff0d8463468b5b9523b24b56b36c7eda177828082c9e299b655875dc3f028618",
        "utf8_bytes": 4100
      },
      "usage": {
        "completion_tokens": 1272,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 13565,
        "prompt_tokens": 13565,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 14837
      },
      "finish_reason": "stop",
      "elapsed": 6.494372606277466
    }
  ]
}
```

</details>

<a id="task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1"></a>

<details>
<summary>s9_evidence_match_0 · task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1</summary>

```json
{
  "task_id": "task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1",
  "epoch": 51,
  "input_snapshot": "snap-7231f58fa80a4136829ac2930ab655d6",
  "input_hash": "6913f94f683ae4f44301ca461f2b0e5f738f8c70ff5a04f78edc919fbb901d64",
  "status": "COMPLETED",
  "reserve": 113541,
  "actual": 6628,
  "created_at": "2026-09-29T22:36:44.888205+00:00",
  "settled_at": "2026-09-29T22:36:59.394340+00:00",
  "node": "s9_evidence_match_0",
  "request_fingerprint": {
    "sha256": "8d7762c0fbaa46c1fbdb95b4f347f1ed9ebe06354f677146462d53ee74b43a2a",
    "utf8_bytes": 48385
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 12319,
    "tokens_out": 2443,
    "cost_usd": 0.006627299999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "19a70b68b4708cf5ae11ed2aa5574f178d14d9a3accb4ea4636ec8f947702bf8",
        "utf8_bytes": 48025
      },
      "response_fingerprint": {
        "sha256": "d12abed2e3410566e40eef43d202c8b29b9a3c80ea843460f5aa53343fbf635f",
        "utf8_bytes": 8068
      },
      "usage": {
        "completion_tokens": 2443,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 10271,
        "prompt_tokens": 12319,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 14762
      },
      "finish_reason": "stop",
      "elapsed": 14.42685079574585
    }
  ]
}
```

</details>

<a id="task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd"></a>

<details>
<summary>s9_evidence_match_1 · task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd</summary>

```json
{
  "task_id": "task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd",
  "epoch": 51,
  "input_snapshot": "snap-7231f58fa80a4136829ac2930ab655d6",
  "input_hash": "2c09adc207a100b1508610c30997e14613cd6a2a179afd47f4edaea669720cfa",
  "status": "COMPLETED",
  "reserve": 113528,
  "actual": 8446,
  "created_at": "2026-09-29T22:37:02.409189+00:00",
  "settled_at": "2026-09-29T22:37:22.839122+00:00",
  "node": "s9_evidence_match_1",
  "request_fingerprint": {
    "sha256": "a3ca07a22eb9a390b74a82459d3a9163e95149c44910cf8db7f117c4e49e72c1",
    "utf8_bytes": 48364
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 12312,
    "tokens_out": 3960,
    "cost_usd": 0.008445600000000001,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "b1689a9e285088893f6da5e429530754ee71c016bdacc45a8172dd2c5305ba32",
        "utf8_bytes": 48004
      },
      "response_fingerprint": {
        "sha256": "895b442aa3a3f9d9f9c1c1133ea4cdf05de99466da7244c8861f0052ad93d5f7",
        "utf8_bytes": 13514
      },
      "usage": {
        "completion_tokens": 3960,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 10264,
        "prompt_tokens": 12312,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 16272
      },
      "finish_reason": "stop",
      "elapsed": 20.35373592376709
    }
  ]
}
```

</details>

<a id="task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0"></a>

<details>
<summary>s9_evidence_match_2 · task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0</summary>

```json
{
  "task_id": "task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0",
  "epoch": 51,
  "input_snapshot": "snap-7231f58fa80a4136829ac2930ab655d6",
  "input_hash": "9e2ae471f5cacffa9b0287ce631376ab2a0ef70b83826d42a56730c8878958ec",
  "status": "COMPLETED",
  "reserve": 113345,
  "actual": 5675,
  "created_at": "2026-09-29T22:37:25.967363+00:00",
  "settled_at": "2026-09-29T22:37:36.049314+00:00",
  "node": "s9_evidence_match_2",
  "request_fingerprint": {
    "sha256": "102ed03556bf9ba58362029361513217ff2359eb79c89e33694d0fe1e46559b9",
    "utf8_bytes": 48047
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 12220,
    "tokens_out": 1674,
    "cost_usd": 0.0056748,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ee2b3d32f499d36f2ccdb82cbb3fac63b63ba4947ed6c5da3c430bc675a39a66",
        "utf8_bytes": 47687
      },
      "response_fingerprint": {
        "sha256": "d2a91fa71bad7f32c9bb2a73743993720306762cca1a45dda96b76ec0c84d8ca",
        "utf8_bytes": 5678
      },
      "usage": {
        "completion_tokens": 1674,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 10172,
        "prompt_tokens": 12220,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 13894
      },
      "finish_reason": "stop",
      "elapsed": 9.98752498626709
    }
  ]
}
```

</details>

<a id="task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02"></a>

<details>
<summary>s8_persona_factory · task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02</summary>

```json
{
  "task_id": "task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "4e3a8ea4f6fa923ee150b5c4000040dc73ca405b6f23630cc879bed9014a7bba",
  "status": "COMPLETED",
  "reserve": 60359,
  "actual": 3135,
  "created_at": "2026-09-29T22:38:30.747113+00:00",
  "settled_at": "2026-09-29T22:38:36.680910+00:00",
  "node": "s8_persona_factory",
  "request_fingerprint": {
    "sha256": "758f1c7bc739b9176814d9acb8da4bef7f37259abfeec6c2b7ae498398284fa0",
    "utf8_bytes": 21882
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T1",
    "model": "deepseek-flash",
    "tokens_in": 6468,
    "tokens_out": 995,
    "cost_usd": 0.0031344,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ed20fbd9807ac02e9ee1de7ff96fff7626d5d4d9dd9afdb259833a66076019b0",
        "utf8_bytes": 21524
      },
      "response_fingerprint": {
        "sha256": "6eed93970d9686b90edcba1775a5e3056746cdce3ba1ba7b5db6fb3f3229a66b",
        "utf8_bytes": 3169
      },
      "usage": {
        "completion_tokens": 995,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 4420,
        "prompt_tokens": 6468,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 7463
      },
      "finish_reason": "stop",
      "elapsed": 5.854734659194946
    }
  ]
}
```

</details>

<a id="task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77"></a>

<details>
<summary>s8_review_independent · task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77</summary>

```json
{
  "task_id": "task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "2bee33926568a39c4cee4805bf2024188e6f666bce34ccb16aa1e98f18d35334",
  "status": "COMPLETED",
  "reserve": 120010,
  "actual": 9213,
  "created_at": "2026-09-29T22:38:48.614148+00:00",
  "settled_at": "2026-09-29T22:39:04.234685+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "2f4ef77de482a38fc3dab14527bda549c696b0287b0536c77dc8d0fc23f27798",
    "utf8_bytes": 58564
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17150,
    "tokens_out": 3390,
    "cost_usd": 0.009212999999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "da4a010a6aa9aedf7f36e4712478fc76d34f569c6cb44dcc991615454d92804e",
        "utf8_bytes": 58203
      },
      "response_fingerprint": {
        "sha256": "806e23dc565f5d26212503ce80b23e3fee6619280dab25a88264d6ac98bb261e",
        "utf8_bytes": 10802
      },
      "usage": {
        "completion_tokens": 3390,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17150,
        "prompt_tokens": 17150,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 20540
      },
      "finish_reason": "stop",
      "elapsed": 15.53134799003601
    }
  ]
}
```

</details>

<a id="task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029"></a>

<details>
<summary>s8_review_independent · task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029</summary>

```json
{
  "task_id": "task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "dcb3daaccdfeec4776308b8e43db494bf59fe2329311bc78cde3f86bc078abbd",
  "status": "COMPLETED",
  "reserve": 119999,
  "actual": 7672,
  "created_at": "2026-09-29T22:38:50.336595+00:00",
  "settled_at": "2026-09-29T22:39:00.778015+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "433901ba1beef6640393b0d39bd2d42d102d20f48fc33d5136ece4386a85917b",
    "utf8_bytes": 58546
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17123,
    "tokens_out": 2112,
    "cost_usd": 0.0076713,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "ddd6695a5a8f0bb225d9f7a6b62d7fa591047ad91d1d39f0192bf1ac08ce3b56",
        "utf8_bytes": 58185
      },
      "response_fingerprint": {
        "sha256": "ce79ef1051549454808b071368b0144dd335e7831b5525b629350e568d73f8be",
        "utf8_bytes": 6871
      },
      "usage": {
        "completion_tokens": 2112,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17123,
        "prompt_tokens": 17123,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 19235
      },
      "finish_reason": "stop",
      "elapsed": 10.365732192993164
    }
  ]
}
```

</details>

<a id="task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73"></a>

<details>
<summary>s8_review_independent · task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73</summary>

```json
{
  "task_id": "task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "1b7b7acb1a58cdbfa437b8b482298e09550bdf35ba7c70d74d6a4eb4af38f885",
  "status": "COMPLETED",
  "reserve": 120078,
  "actual": 9519,
  "created_at": "2026-09-29T22:38:51.931035+00:00",
  "settled_at": "2026-09-29T22:39:07.364005+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "deaf99b95376646994f98acfadfbcadd3dbcabb77c795b032ceec06a4474e29e",
    "utf8_bytes": 58677
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17177,
    "tokens_out": 3638,
    "cost_usd": 0.0095187,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "58c2dc93be8950341a3d260714d29c9dce19dbced390f4bdd8a1522be413b517",
        "utf8_bytes": 58316
      },
      "response_fingerprint": {
        "sha256": "bc1cc05d08e802e941d19ed133c591944a2a896b53d21b95f1c3754ffa0b50cb",
        "utf8_bytes": 11666
      },
      "usage": {
        "completion_tokens": 3638,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17177,
        "prompt_tokens": 17177,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 20815
      },
      "finish_reason": "stop",
      "elapsed": 15.306226253509521
    }
  ]
}
```

</details>

<a id="task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d"></a>

<details>
<summary>s8_review_independent · task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d</summary>

```json
{
  "task_id": "task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "49bf6bd0fca4a45901e6d93ba403ce2ecc2791003f70af8534b9d50ca355baf7",
  "status": "COMPLETED",
  "reserve": 120039,
  "actual": 8968,
  "created_at": "2026-09-29T22:38:53.615970+00:00",
  "settled_at": "2026-09-29T22:39:07.451474+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "80b7e83ec62606e866b2a12372fdcf08f1a83fd7dc29bf0f456eb76343301236",
    "utf8_bytes": 58613
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17159,
    "tokens_out": 3183,
    "cost_usd": 0.0089673,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "08b55d5ff4fc03d422768804ea8f3978cdae3d24e0d8ce0a34843ee637a877e0",
        "utf8_bytes": 58252
      },
      "response_fingerprint": {
        "sha256": "fc151c82c9d2e0f6ec1b94571f8a51bd188d2d8d74af82c71d038931e170c973",
        "utf8_bytes": 10298
      },
      "usage": {
        "completion_tokens": 3183,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17159,
        "prompt_tokens": 17159,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 20342
      },
      "finish_reason": "stop",
      "elapsed": 13.62120509147644
    }
  ]
}
```

</details>

<a id="task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11"></a>

<details>
<summary>s8_review_independent · task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11</summary>

```json
{
  "task_id": "task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "a4e8036f0d96416b4e9dd8df9c1e1677bfdafeeb01afff10e7504abbac01483b",
  "status": "COMPLETED",
  "reserve": 124583,
  "actual": 10404,
  "created_at": "2026-09-29T22:39:03.779710+00:00",
  "settled_at": "2026-09-29T22:39:20.206142+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "be54d3241576eea8e3aad5c027deb2de0c1c21faa1f4fcdb4a7d65f16e185b2c",
    "utf8_bytes": 66386
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 19576,
    "tokens_out": 3776,
    "cost_usd": 0.010404,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "2cb2e47c7e8975454db8e2dd105f2a282a81c15753582c6662c1f9346fc8dd67",
        "utf8_bytes": 66025
      },
      "response_fingerprint": {
        "sha256": "76457d8e0a7f4b2f17cda92392e233835e283ef64843e1750505d6924f578b66",
        "utf8_bytes": 12303
      },
      "usage": {
        "completion_tokens": 3776,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 17024,
        "prompt_cache_miss_tokens": 2552,
        "prompt_tokens": 19576,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 17024,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 23352
      },
      "finish_reason": "stop",
      "elapsed": 14.06418514251709
    }
  ]
}
```

</details>

<a id="task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4"></a>

<details>
<summary>s8_review_independent · task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4</summary>

```json
{
  "task_id": "task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "a902269ebb34c0920964e3074a5784c79840bbb36c08e8550c34456b60259379",
  "status": "COMPLETED",
  "reserve": 119948,
  "actual": 6918,
  "created_at": "2026-09-29T22:39:18.002535+00:00",
  "settled_at": "2026-09-29T22:39:28.388466+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "bd76ceb61da7866df4aaef855af34c0e49b627e390340e6509851c92e5085ccf",
    "utf8_bytes": 58452
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17085,
    "tokens_out": 1493,
    "cost_usd": 0.0069171,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c9e2795e9d77a50b27c6427630f787597c54a72801ec23562b1ae0dc8167f409",
        "utf8_bytes": 58091
      },
      "response_fingerprint": {
        "sha256": "cdff9929e14dcc264ed4fc6d4738f50ff8340ea74b7c924e337b86f7e462c0c1",
        "utf8_bytes": 4871
      },
      "usage": {
        "completion_tokens": 1493,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2749,
        "prompt_tokens": 17085,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18578
      },
      "finish_reason": "stop",
      "elapsed": 8.132366418838501
    }
  ]
}
```

</details>

<a id="task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685"></a>

<details>
<summary>s8_review_independent · task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685</summary>

```json
{
  "task_id": "task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "86c667ad166dc8684b180ff9b48e19825ae5b30f5f07133ed9879e0406f28e88",
  "status": "COMPLETED",
  "reserve": 119977,
  "actual": 6716,
  "created_at": "2026-09-29T22:39:35.907582+00:00",
  "settled_at": "2026-09-29T22:39:45.507435+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "d4a7de05726ba7154ba32453bf15f44a34e86e631973d0d50ff1cb5a87f28e48",
    "utf8_bytes": 58501
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17094,
    "tokens_out": 1323,
    "cost_usd": 0.0067158,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "2858a8ca2719e59ea39b760481985c68a7494956b58cd205a75797f4a637c5c9",
        "utf8_bytes": 58140
      },
      "response_fingerprint": {
        "sha256": "f1e01ad49acb7b7d1df6a509ac371832b57035eeec3d3152ffc6541ad55575c1",
        "utf8_bytes": 4164
      },
      "usage": {
        "completion_tokens": 1323,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2758,
        "prompt_tokens": 17094,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18417
      },
      "finish_reason": "stop",
      "elapsed": 7.166075229644775
    }
  ]
}
```

</details>

<a id="task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa"></a>

<details>
<summary>s8_review_independent · task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa</summary>

```json
{
  "task_id": "task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "091d42cd49c332c8642e62b9b804a1752053802a12c2103d603134cb5f39f3f1",
  "status": "COMPLETED",
  "reserve": 120015,
  "actual": 6915,
  "created_at": "2026-09-29T22:39:43.125784+00:00",
  "settled_at": "2026-09-29T22:39:53.062452+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "f8ee1761533fcc5b6ac8348b27fbbed30259a6fd1d8d9fe5c1599a018e3b38e1",
    "utf8_bytes": 58565
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17112,
    "tokens_out": 1484,
    "cost_usd": 0.006914399999999999,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "e45afd4efd9dea4c58298977991ef1df9535c404b937e0ee893129cac2de4d88",
        "utf8_bytes": 58204
      },
      "response_fingerprint": {
        "sha256": "1f7d2a53f604dc60463d476ce649d0cec853ecdec754720a43af95be78b128ef",
        "utf8_bytes": 4874
      },
      "usage": {
        "completion_tokens": 1484,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2776,
        "prompt_tokens": 17112,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18596
      },
      "finish_reason": "stop",
      "elapsed": 7.93290901184082
    }
  ]
}
```

</details>

<a id="task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9"></a>

<details>
<summary>s8_review_independent · task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9</summary>

```json
{
  "task_id": "task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "acb219ed1f9bffaad0155f9a5d9360fa9db64fe802d9ff0b462287392a889985",
  "status": "COMPLETED",
  "reserve": 119937,
  "actual": 6693,
  "created_at": "2026-09-29T22:39:44.829121+00:00",
  "settled_at": "2026-09-29T22:39:53.978811+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "ec43ea99ac553ee9d0fbdddfed3f29d1c971c7b727ab3cfb10f06bde1cd13114",
    "utf8_bytes": 58434
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17058,
    "tokens_out": 1313,
    "cost_usd": 0.006693,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "c00d1d5c7f822f0af2d46b722c19cde5311863cde3820b2c4090f6a2d09684d6",
        "utf8_bytes": 58073
      },
      "response_fingerprint": {
        "sha256": "c54428d53ea9c2d34b7d0a923ebce12a4824c67abd6db4f1b14fead1b62bf78d",
        "utf8_bytes": 4364
      },
      "usage": {
        "completion_tokens": 1313,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2722,
        "prompt_tokens": 17058,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18371
      },
      "finish_reason": "stop",
      "elapsed": 7.470337867736816
    }
  ]
}
```

</details>

<a id="task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233"></a>

<details>
<summary>s8_review_independent · task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233</summary>

```json
{
  "task_id": "task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "9f5d402e6dfde9c9298c114c7517d265aa182db856978af53acdff83c91bd668",
  "status": "COMPLETED",
  "reserve": 120095,
  "actual": 7895,
  "created_at": "2026-09-29T22:40:02.349826+00:00",
  "settled_at": "2026-09-29T22:40:14.423275+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "06fbfccc6f4b1f890a972de1f937942f49cd3548773db20fd55adb6fa66ae5f4",
    "utf8_bytes": 58706
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17184,
    "tokens_out": 2283,
    "cost_usd": 0.0078948,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "f4cf0bed0def4267c9adef8718467192a64d4e9a7089524f74eb06bd85849c78",
        "utf8_bytes": 58345
      },
      "response_fingerprint": {
        "sha256": "c3ad73034f8d1438c15707f921ec73c6958257615b03d7c4c575b2a4110d244d",
        "utf8_bytes": 7222
      },
      "usage": {
        "completion_tokens": 2283,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17184,
        "prompt_tokens": 17184,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 19467
      },
      "finish_reason": "stop",
      "elapsed": 10.785257577896118
    }
  ]
}
```

</details>

<a id="task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3"></a>

<details>
<summary>s8_review_independent · task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3</summary>

```json
{
  "task_id": "task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "ebeef226bf3d10b96704cf3f9f3c1b353774b64564679202396ae784fa055b4e",
  "status": "COMPLETED",
  "reserve": 120011,
  "actual": 9220,
  "created_at": "2026-09-29T22:40:11.992215+00:00",
  "settled_at": "2026-09-29T22:40:33.699410+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "c467b26a8dab507734563db92aca6d8690226e77d52c978b20e8672a8a148f43",
    "utf8_bytes": 58566
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17148,
    "tokens_out": 3396,
    "cost_usd": 0.0092196,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "1028fba6ac848fc2bc38e19f7dc2dcfd6e31d253f2f58c4495e669d6f30ba9d7",
        "utf8_bytes": 58205
      },
      "response_fingerprint": {
        "sha256": "f2a58171cc6b003e7a5c4c28c92397871329fc2e797a041e9ba9843bfdc8daea",
        "utf8_bytes": 10902
      },
      "usage": {
        "completion_tokens": 3396,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 0,
        "prompt_cache_miss_tokens": 17148,
        "prompt_tokens": 17148,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 0,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 20544
      },
      "finish_reason": "stop",
      "elapsed": 16.282034158706665
    }
  ]
}
```

</details>

<a id="task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06"></a>

<details>
<summary>s8_review_independent · task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06</summary>

```json
{
  "task_id": "task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "9bd00c0d463b4292fb96d23a67ae647dfb0ce7cad52ae10e2dad8378751b41b6",
  "status": "COMPLETED",
  "reserve": 120033,
  "actual": 6792,
  "created_at": "2026-09-29T22:41:00.497532+00:00",
  "settled_at": "2026-09-29T22:41:10.018927+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "0b1a200c75682bf0e382cf62f7d38a9d8f9cc83974771c381d33665d8354d435",
    "utf8_bytes": 58594
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17119,
    "tokens_out": 1380,
    "cost_usd": 0.0067916999999999995,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "eb68632407c7ee73b9e38bf5692baa6e6ea36c752767e41343b5baded284195d",
        "utf8_bytes": 58233
      },
      "response_fingerprint": {
        "sha256": "d149c89984ee7e974eac3c126a324e10ce83a22b4963c90494d78fb29f3ce200",
        "utf8_bytes": 4535
      },
      "usage": {
        "completion_tokens": 1380,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2783,
        "prompt_tokens": 17119,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18499
      },
      "finish_reason": "stop",
      "elapsed": 7.574033498764038
    }
  ]
}
```

</details>

<a id="task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a"></a>

<details>
<summary>s8_review_independent · task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a</summary>

```json
{
  "task_id": "task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "106626cfee4ebf7dcb4c8b26b4fe3836f0b62f2a082f552d3ae565e780dd6d06",
  "status": "COMPLETED",
  "reserve": 119949,
  "actual": 6929,
  "created_at": "2026-09-29T22:41:05.454474+00:00",
  "settled_at": "2026-09-29T22:41:13.768849+00:00",
  "node": "s8_review_independent",
  "request_fingerprint": {
    "sha256": "5d8a4a1bb20b81482f5a7cc82ceebd2e59d9defb759601c6541b5af589e279cd",
    "utf8_bytes": 58454
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T3",
    "model": "deepseek-flash",
    "tokens_in": 17083,
    "tokens_out": 1503,
    "cost_usd": 0.0069285,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "5903b812918366026097d44cf49c65470730cbbe0e6096a1d5166ea17afd8ab9",
        "utf8_bytes": 58093
      },
      "response_fingerprint": {
        "sha256": "17d3170039447891f40d5e09f758441b855b3c882ef2be487036c0bfd54581f8",
        "utf8_bytes": 5022
      },
      "usage": {
        "completion_tokens": 1503,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 14336,
        "prompt_cache_miss_tokens": 2747,
        "prompt_tokens": 17083,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 14336,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 18586
      },
      "finish_reason": "stop",
      "elapsed": 8.230074644088745
    }
  ]
}
```

</details>

<a id="task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7"></a>

<details>
<summary>s8_rank · task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7</summary>

```json
{
  "task_id": "task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7",
  "epoch": 51,
  "input_snapshot": "snap-a3e819359d8144efae7fd943812a96ac",
  "input_hash": "c8f09d4362fc9f457f735f9887c2c4c08976ead259ed929a102bc5ce16bb768a",
  "status": "COMPLETED",
  "reserve": 107481,
  "actual": 5780,
  "created_at": "2026-09-29T22:41:57.161984+00:00",
  "settled_at": "2026-09-29T22:42:07.208430+00:00",
  "node": "s8_rank",
  "request_fingerprint": {
    "sha256": "19edcb327043570450e2264b370f0374adf3070fe5cd2a33cb404b9fa7b1eb44",
    "utf8_bytes": 37027
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T2",
    "model": "deepseek-flash",
    "tokens_in": 11138,
    "tokens_out": 2032,
    "cost_usd": 0.0057798,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "a0c005449d9775e75f6b631056c6f4eff566e9e977ca66a1728a23b7b5001064",
        "utf8_bytes": 36679
      },
      "response_fingerprint": {
        "sha256": "d6f83f69153a1b7bd134baeb8396ccebd001f0ffffa7a2d234a8b8a9acea6cf3",
        "utf8_bytes": 6555
      },
      "usage": {
        "completion_tokens": 2032,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 9090,
        "prompt_tokens": 11138,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 13170
      },
      "finish_reason": "stop",
      "elapsed": 9.906436920166016
    }
  ]
}
```

</details>

<a id="task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e"></a>

<details>
<summary>s10_distill · task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e</summary>

```json
{
  "task_id": "task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e",
  "epoch": 52,
  "input_snapshot": "snap-ab9f74e25b044c86a2e227b43c6157ff",
  "input_hash": "e5476b34c8d0d0d9207a516dc3b77f81555f273fe17ca6c964ade8e3b97d6369",
  "status": "COMPLETED",
  "reserve": 68573,
  "actual": 4032,
  "created_at": "2026-09-29T22:58:08.769274+00:00",
  "settled_at": "2026-09-29T22:58:13.139294+00:00",
  "node": "s10_distill",
  "request_fingerprint": {
    "sha256": "586d4c12d29f6f80c2fb6c1cd3c76779a2fd1b22b6448869452f635874c36d17",
    "utf8_bytes": 36393
  },
  "request_settings": {},
  "result_usage": {
    "tier": "T1",
    "model": "deepseek-flash",
    "tokens_in": 10616,
    "tokens_out": 706,
    "cost_usd": 0.004032,
    "raw_error": ""
  },
  "provider_attempts": [
    {
      "request_fingerprint": {
        "sha256": "d429dbb83d9f8e14022d37c59a0e370a6a3c56996a809fab81d450186e730df4",
        "utf8_bytes": 36042
      },
      "response_fingerprint": {
        "sha256": "ed5e9d43f8e4d216e19ace78ceb94cb170df63a1c674c644f86c088d25857459",
        "utf8_bytes": 2439
      },
      "usage": {
        "completion_tokens": 706,
        "completion_tokens_details": null,
        "prompt_cache_hit_tokens": 2048,
        "prompt_cache_miss_tokens": 8568,
        "prompt_tokens": 10616,
        "prompt_tokens_details": {
          "audio_tokens": null,
          "cache_write_tokens": null,
          "cached_tokens": 2048,
          "image_tokens": null,
          "text_tokens": null
        },
        "total_tokens": 11322
      },
      "finish_reason": "stop",
      "elapsed": 4.268137693405151
    }
  ]
}
```

</details>
