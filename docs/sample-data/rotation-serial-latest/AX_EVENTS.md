# AX 실행 이벤트

[사례 개요](README.md)

각 행의 상세 링크에는 해당 저장 payload 전체가 있습니다. 별도 요청·응답 원문이 포함되는 필드는 본문 대신 해시를 남겼습니다.

| ID | KST | 종류 | 전체 payload |
|---|---|---|---|
| event-0e988893c44a456d869846f410eaaaa3 | 06:46:26 | EPOCH_CHANGED | [보기](#row-event-0e988893c44a456d869846f410eaaaa3) |
| event-1126c4ec51764fca8c8b75d0b6a6a915 | 06:46:55 | SNAPSHOT_COMMITTED | [보기](#row-event-1126c4ec51764fca8c8b75d0b6a6a915) |
| event-60135bf499f04333a21301b2267dc539 | 06:47:22 | ACTION_RESERVED | [보기](#row-event-60135bf499f04333a21301b2267dc539) |
| event-12550159e785428eb582dac492bc7bc9 | 06:47:32 | ACTION_COMPLETED | [보기](#row-event-12550159e785428eb582dac492bc7bc9) |
| event-f2502343d932403c8d1c433ee87fcbd4 | 06:47:32 | SNAPSHOT_COMMITTED | [보기](#row-event-f2502343d932403c8d1c433ee87fcbd4) |
| event-3f47739fecff4a359a37565d83aeca61 | 06:49:07 | EPOCH_CHANGED | [보기](#row-event-3f47739fecff4a359a37565d83aeca61) |
| event-b5ef7fcf0b2343d1b9f5f9f397774f86 | 06:49:31 | SNAPSHOT_COMMITTED | [보기](#row-event-b5ef7fcf0b2343d1b9f5f9f397774f86) |
| event-2ec47bd9bdae4068afd92f1cc3b922fd | 06:49:49 | ACTION_RESERVED | [보기](#row-event-2ec47bd9bdae4068afd92f1cc3b922fd) |
| event-5778788995a34b5f8d9cf86626b5d87e | 06:49:58 | ACTION_COMPLETED | [보기](#row-event-5778788995a34b5f8d9cf86626b5d87e) |
| event-9be5cf3c0fab452395c637015bf22a5a | 06:49:59 | SNAPSHOT_COMMITTED | [보기](#row-event-9be5cf3c0fab452395c637015bf22a5a) |
| event-23fc4a7d3c484c1881a0fcbf327aa1ad | 06:50:47 | ACTION_RESERVED | [보기](#row-event-23fc4a7d3c484c1881a0fcbf327aa1ad) |
| event-a8c4f7d1f706492c9524c1a81f090a4a | 06:50:58 | ACTION_COMPLETED | [보기](#row-event-a8c4f7d1f706492c9524c1a81f090a4a) |
| event-eedaa927823041dd8949e5458ec9a1d9 | 06:51:11 | ACTION_RESERVED | [보기](#row-event-eedaa927823041dd8949e5458ec9a1d9) |
| event-ff632ebddb564c30adaaa34e533f25e7 | 06:51:13 | ACTION_COMPLETED | [보기](#row-event-ff632ebddb564c30adaaa34e533f25e7) |
| event-a228557e3dda44e4b87c31aa72cfd3c4 | 06:51:19 | SNAPSHOT_COMMITTED | [보기](#row-event-a228557e3dda44e4b87c31aa72cfd3c4) |
| event-5aeccff6ab36490ab6922bf6395e4747 | 06:52:06 | EPOCH_CHANGED | [보기](#row-event-5aeccff6ab36490ab6922bf6395e4747) |
| event-04ebda3cc27a461187fac4757c3c3918 | 06:52:32 | SNAPSHOT_COMMITTED | [보기](#row-event-04ebda3cc27a461187fac4757c3c3918) |
| event-50587501e57748aaa864a03d2b6fa49f | 06:52:58 | ACTION_RESERVED | [보기](#row-event-50587501e57748aaa864a03d2b6fa49f) |
| event-fc18e66c2c4d4b49a7a7a06bd7cb33ee | 06:53:09 | ACTION_COMPLETED | [보기](#row-event-fc18e66c2c4d4b49a7a7a06bd7cb33ee) |
| event-623e4b49a45c455a99745109a440cf7f | 06:53:17 | SNAPSHOT_COMMITTED | [보기](#row-event-623e4b49a45c455a99745109a440cf7f) |
| event-a5af1e19a18e4a9a83cbd9ef0e88df7a | 06:53:58 | ACTION_RESERVED | [보기](#row-event-a5af1e19a18e4a9a83cbd9ef0e88df7a) |
| event-f68589db610b46c8a2793e56dc2f7c51 | 06:54:04 | ACTION_COMPLETED | [보기](#row-event-f68589db610b46c8a2793e56dc2f7c51) |
| event-c72b1c1cf4644e86ab1ca0844be34219 | 06:54:10 | SNAPSHOT_COMMITTED | [보기](#row-event-c72b1c1cf4644e86ab1ca0844be34219) |
| event-055891ab577e478ebbccdb0a230bba6c | 07:06:02 | EPOCH_CHANGED | [보기](#row-event-055891ab577e478ebbccdb0a230bba6c) |
| event-34cb350f5b2a4bccaf18647a3c09ea54 | 07:06:31 | SNAPSHOT_COMMITTED | [보기](#row-event-34cb350f5b2a4bccaf18647a3c09ea54) |
| event-e4959864d59d4b7aacd1fb4a1c4bb9b0 | 07:06:48 | SNAPSHOT_COMMITTED | [보기](#row-event-e4959864d59d4b7aacd1fb4a1c4bb9b0) |
| event-a7cf32c6f29947a9b7c6ccec41e17c77 | 07:07:35 | ACTION_RESERVED | [보기](#row-event-a7cf32c6f29947a9b7c6ccec41e17c77) |
| event-4eddf5da69da4de1a9a7152ad7b1993d | 07:07:44 | ACTION_COMPLETED | [보기](#row-event-4eddf5da69da4de1a9a7152ad7b1993d) |
| event-c91b251ff0fb4bb2ad8d1cd1434b30cf | 07:07:50 | ACTION_RESERVED | [보기](#row-event-c91b251ff0fb4bb2ad8d1cd1434b30cf) |
| event-fbaf9499429c4efe9ed7601a5758b2fe | 07:08:02 | ACTION_COMPLETED | [보기](#row-event-fbaf9499429c4efe9ed7601a5758b2fe) |
| event-6479b7682fb940629ffefcf4a2708b5b | 07:08:06 | ACTION_RESERVED | [보기](#row-event-6479b7682fb940629ffefcf4a2708b5b) |
| event-7258ad7160904c6ab2d1ec67ddbc7d3a | 07:08:10 | ACTION_COMPLETED | [보기](#row-event-7258ad7160904c6ab2d1ec67ddbc7d3a) |
| event-8648cd3dc21c458ebd23935f7c5c0fea | 07:08:21 | ACTION_RESERVED | [보기](#row-event-8648cd3dc21c458ebd23935f7c5c0fea) |
| event-2034880183fa4c3486a2b12b7edacb73 | 07:08:23 | ACTION_RESERVED | [보기](#row-event-2034880183fa4c3486a2b12b7edacb73) |
| event-056e7c0941844960885b1bb6675efe14 | 07:08:24 | ACTION_RESERVED | [보기](#row-event-056e7c0941844960885b1bb6675efe14) |
| event-200f0a4774594f9f9231b7f7bc9a8d0e | 07:08:26 | ACTION_COMPLETED | [보기](#row-event-200f0a4774594f9f9231b7f7bc9a8d0e) |
| event-c0cbb0004600420db135f411e9ca4630 | 07:08:35 | ACTION_COMPLETED | [보기](#row-event-c0cbb0004600420db135f411e9ca4630) |
| event-3c9dff22015f45578b8e631c55bc6dfc | 07:08:35 | ACTION_COMPLETED | [보기](#row-event-3c9dff22015f45578b8e631c55bc6dfc) |
| event-feb9302f315e487697b01aae6a6a3917 | 07:08:38 | ACTION_RESERVED | [보기](#row-event-feb9302f315e487697b01aae6a6a3917) |
| event-b98757ce95e84d6083475b4dd5063e02 | 07:08:42 | ACTION_COMPLETED | [보기](#row-event-b98757ce95e84d6083475b4dd5063e02) |
| event-7503ca69215c499da17fe2a41661431b | 07:08:48 | ACTION_RESERVED | [보기](#row-event-7503ca69215c499da17fe2a41661431b) |
| event-1c9e768ff6cb429989b50b033db7182e | 07:08:58 | ACTION_COMPLETED | [보기](#row-event-1c9e768ff6cb429989b50b033db7182e) |
| event-c5d943be20464f8898470298ecdcf5b6 | 07:09:05 | SNAPSHOT_COMMITTED | [보기](#row-event-c5d943be20464f8898470298ecdcf5b6) |
| event-0ababd31e20e45ee95e150022dcdabcf | 07:09:49 | ACTION_RESERVED | [보기](#row-event-0ababd31e20e45ee95e150022dcdabcf) |
| event-2cfaa4803bd94947a553949749a62206 | 07:09:51 | ACTION_RESERVED | [보기](#row-event-2cfaa4803bd94947a553949749a62206) |
| event-ba1e65c0cbfb47ac8f45000ed0aa5c9e | 07:09:52 | ACTION_RESERVED | [보기](#row-event-ba1e65c0cbfb47ac8f45000ed0aa5c9e) |
| event-58ef89a4e13c4950a044f695e0f535ed | 07:09:54 | ACTION_COMPLETED | [보기](#row-event-58ef89a4e13c4950a044f695e0f535ed) |
| event-eeefc117534940cf9bed7b7cda2cd4c2 | 07:09:59 | ACTION_COMPLETED | [보기](#row-event-eeefc117534940cf9bed7b7cda2cd4c2) |
| event-729dfe8a5e70470dbb9859d8b0d34869 | 07:10:03 | ACTION_COMPLETED | [보기](#row-event-729dfe8a5e70470dbb9859d8b0d34869) |
| event-80fc320b72854697a848ec6c1b47cdec | 07:10:08 | ACTION_RESERVED | [보기](#row-event-80fc320b72854697a848ec6c1b47cdec) |
| event-42bacd272b5848e186000cd6f8dfc24e | 07:10:16 | ACTION_COMPLETED | [보기](#row-event-42bacd272b5848e186000cd6f8dfc24e) |
| event-4463bce6274348fbbd84864af80f2acb | 07:10:21 | ACTION_RESERVED | [보기](#row-event-4463bce6274348fbbd84864af80f2acb) |
| event-c76629e49c954710843a2fa0e30d37b6 | 07:10:26 | ACTION_COMPLETED | [보기](#row-event-c76629e49c954710843a2fa0e30d37b6) |
| event-1b66ac32a163425bb3be32e0b959f7da | 07:10:31 | SNAPSHOT_COMMITTED | [보기](#row-event-1b66ac32a163425bb3be32e0b959f7da) |
| event-a03e5772dddf464e9e0b02f59b30bac4 | 07:10:58 | DECISION_RECORDED | [보기](#row-event-a03e5772dddf464e9e0b02f59b30bac4) |
| event-1afdf23913364d8392ef49c1747e898b | 07:11:16 | ACTION_RESERVED | [보기](#row-event-1afdf23913364d8392ef49c1747e898b) |
| event-b4e339307ffb4ecd8c5b4f50f98f95c1 | 07:11:17 | ACTION_RESERVED | [보기](#row-event-b4e339307ffb4ecd8c5b4f50f98f95c1) |
| event-9714e9aa07d5494c9ca8f3b89d03e3f2 | 07:11:19 | ACTION_RESERVED | [보기](#row-event-9714e9aa07d5494c9ca8f3b89d03e3f2) |
| event-e5a07b125284427f835d539c6be1a43f | 07:11:20 | ACTION_COMPLETED | [보기](#row-event-e5a07b125284427f835d539c6be1a43f) |
| event-04983c53935c45f3a94876ded364697a | 07:11:27 | ACTION_RESERVED | [보기](#row-event-04983c53935c45f3a94876ded364697a) |
| event-058067fc7d5147b8a7c143127e601784 | 07:11:28 | ACTION_COMPLETED | [보기](#row-event-058067fc7d5147b8a7c143127e601784) |
| event-dc700fafecea4aa4ae64516f4ef2adfb | 07:11:31 | ACTION_COMPLETED | [보기](#row-event-dc700fafecea4aa4ae64516f4ef2adfb) |
| event-86db933698de466c842a79c2a0e397ea | 07:11:37 | ACTION_RESERVED | [보기](#row-event-86db933698de466c842a79c2a0e397ea) |
| event-bc1c6d0228534c5da8c8ba2a38ec76bd | 07:11:38 | ACTION_RESERVED | [보기](#row-event-bc1c6d0228534c5da8c8ba2a38ec76bd) |
| event-86fc94ffd11a40a3aab8289f1de2e8e9 | 07:11:43 | ACTION_COMPLETED | [보기](#row-event-86fc94ffd11a40a3aab8289f1de2e8e9) |
| event-f74867bb282843dfb8bf4273d8c8f518 | 07:11:46 | ACTION_COMPLETED | [보기](#row-event-f74867bb282843dfb8bf4273d8c8f518) |
| event-57b5ae6ffc47448791cdf5e03ed6c4bc | 07:11:48 | ACTION_RESERVED | [보기](#row-event-57b5ae6ffc47448791cdf5e03ed6c4bc) |
| event-a6e3b09b730a48bfa3407b8915bc1afb | 07:11:50 | ACTION_COMPLETED | [보기](#row-event-a6e3b09b730a48bfa3407b8915bc1afb) |
| event-b8b8f7967cd24d34adae94aa0810dc24 | 07:11:55 | ACTION_RESERVED | [보기](#row-event-b8b8f7967cd24d34adae94aa0810dc24) |
| event-88e2c4dc6e574938a8372a42fb181557 | 07:11:55 | ACTION_COMPLETED | [보기](#row-event-88e2c4dc6e574938a8372a42fb181557) |
| event-2944ec2b087847f68c96c93282ef719a | 07:12:00 | ACTION_RESERVED | [보기](#row-event-2944ec2b087847f68c96c93282ef719a) |
| event-9f29311b72aa4c6fa698cb68462b4b90 | 07:12:09 | ACTION_COMPLETED | [보기](#row-event-9f29311b72aa4c6fa698cb68462b4b90) |
| event-1e6cd610b27848a08be4490359217533 | 07:12:13 | ACTION_RESERVED | [보기](#row-event-1e6cd610b27848a08be4490359217533) |
| event-4031a56a4b99426596f09118fb13c2f7 | 07:12:15 | ACTION_COMPLETED | [보기](#row-event-4031a56a4b99426596f09118fb13c2f7) |
| event-fd56b197d1c74e7981bc6e78c4f84188 | 07:12:19 | ACTION_RESERVED | [보기](#row-event-fd56b197d1c74e7981bc6e78c4f84188) |
| event-a364013b26c3493683f3e645ac0b7374 | 07:12:19 | ACTION_COMPLETED | [보기](#row-event-a364013b26c3493683f3e645ac0b7374) |
| event-558517318c4e46b8a37ecab95ef0c307 | 07:12:22 | ACTION_RESERVED | [보기](#row-event-558517318c4e46b8a37ecab95ef0c307) |
| event-d164a735de314d86a13ed6e34329cbe5 | 07:12:34 | ACTION_COMPLETED | [보기](#row-event-d164a735de314d86a13ed6e34329cbe5) |
| event-12995c59777f4ded80a7b7e22d86b92b | 07:12:46 | ACTION_COMPLETED | [보기](#row-event-12995c59777f4ded80a7b7e22d86b92b) |
| event-a4041346592f460f84b2a9db835339f0 | 07:12:50 | ACTION_RESERVED | [보기](#row-event-a4041346592f460f84b2a9db835339f0) |
| event-4b7e68c901004f56824d0bd766e38158 | 07:13:42 | ACTION_COMPLETED | [보기](#row-event-4b7e68c901004f56824d0bd766e38158) |
| event-9b5cae89dc4549acb947945e1c5fc6c4 | 07:13:46 | ACTION_RESERVED | [보기](#row-event-9b5cae89dc4549acb947945e1c5fc6c4) |
| event-955c600a2d96454b8aceced93206b230 | 07:13:51 | ACTION_COMPLETED | [보기](#row-event-955c600a2d96454b8aceced93206b230) |
| event-422f7374075c448eaf802c6717447963 | 07:13:55 | ACTION_RESERVED | [보기](#row-event-422f7374075c448eaf802c6717447963) |
| event-9b5b4b43965c4d0ca65da1dfa96d82db | 07:14:39 | ACTION_COMPLETED | [보기](#row-event-9b5b4b43965c4d0ca65da1dfa96d82db) |
| event-4da5eb543307464fb7999dd2c6e7891a | 07:14:48 | DECISION_RECORDED | [보기](#row-event-4da5eb543307464fb7999dd2c6e7891a) |
| event-3346344519c9499b988722506862caba | 07:14:56 | ACTION_RESERVED | [보기](#row-event-3346344519c9499b988722506862caba) |
| event-0fedc8c2df4a486199fa7878da7f4bb4 | 07:14:58 | ACTION_RESERVED | [보기](#row-event-0fedc8c2df4a486199fa7878da7f4bb4) |
| event-99be9e8a26bc46f1bf1aea30e12c3cbb | 07:14:59 | ACTION_RESERVED | [보기](#row-event-99be9e8a26bc46f1bf1aea30e12c3cbb) |
| event-daea572d8f6549da8d6281cd52e39e7a | 07:15:08 | ACTION_COMPLETED | [보기](#row-event-daea572d8f6549da8d6281cd52e39e7a) |
| event-da62e611fffc4dc59fcc571e1ac6953b | 07:15:13 | ACTION_COMPLETED | [보기](#row-event-da62e611fffc4dc59fcc571e1ac6953b) |
| event-743984a14b834df396bf220a22adf3b4 | 07:15:16 | ACTION_COMPLETED | [보기](#row-event-743984a14b834df396bf220a22adf3b4) |
| event-0a388b5edce64997b8a0fbd0f8f91dbe | 07:15:19 | ACTION_RESERVED | [보기](#row-event-0a388b5edce64997b8a0fbd0f8f91dbe) |
| event-f48b469d1cd14a42986bc4d4d795def4 | 07:15:41 | ACTION_COMPLETED | [보기](#row-event-f48b469d1cd14a42986bc4d4d795def4) |
| event-7eff2d349e1d4a82bf227cd3a1ce7c63 | 07:15:47 | DECISION_RECORDED | [보기](#row-event-7eff2d349e1d4a82bf227cd3a1ce7c63) |
| event-699485d92a3245e693e5a6573fb5022f | 07:15:53 | ACTION_RESERVED | [보기](#row-event-699485d92a3245e693e5a6573fb5022f) |
| event-ea90e8d1e51e4d199b73e2c01c04f0f5 | 07:15:55 | ACTION_RESERVED | [보기](#row-event-ea90e8d1e51e4d199b73e2c01c04f0f5) |
| event-170ebb07783e411589126acf37c6bbd3 | 07:16:07 | ACTION_COMPLETED | [보기](#row-event-170ebb07783e411589126acf37c6bbd3) |
| event-ef9b3688d79d45a38ef72d4e75cd65c1 | 07:16:09 | ACTION_COMPLETED | [보기](#row-event-ef9b3688d79d45a38ef72d4e75cd65c1) |
| event-b5d831bea559474fa40c3c4502feab10 | 07:16:18 | ACTION_RESERVED | [보기](#row-event-b5d831bea559474fa40c3c4502feab10) |
| event-cfa1f162458b490bb2154cbe3689d934 | 07:16:55 | ACTION_COMPLETED | [보기](#row-event-cfa1f162458b490bb2154cbe3689d934) |
| event-ca6a2ff253204ea18f8a3c51ca60d467 | 07:17:00 | ACTION_RESERVED | [보기](#row-event-ca6a2ff253204ea18f8a3c51ca60d467) |
| event-e0f827808c9a4c4abc3fe8c4e043ce67 | 07:17:28 | ACTION_COMPLETED | [보기](#row-event-e0f827808c9a4c4abc3fe8c4e043ce67) |
| event-042fafe97b614df0a0e911cf230b17a0 | 07:17:34 | SNAPSHOT_COMMITTED | [보기](#row-event-042fafe97b614df0a0e911cf230b17a0) |
| event-599e4440c18149a8989b80704eb60050 | 07:18:09 | DECISION_RECORDED | [보기](#row-event-599e4440c18149a8989b80704eb60050) |
| event-4b65924ac1e849b8bd6a71c469dacba6 | 07:18:11 | SNAPSHOT_COMMITTED | [보기](#row-event-4b65924ac1e849b8bd6a71c469dacba6) |
| event-2542a5593cb94eb3aa619320fc3cdd59 | 07:19:02 | ACTION_RESERVED | [보기](#row-event-2542a5593cb94eb3aa619320fc3cdd59) |
| event-bf6913f631f94d2da721df62dd0668b6 | 07:19:04 | ACTION_RESERVED | [보기](#row-event-bf6913f631f94d2da721df62dd0668b6) |
| event-e30f798011214e8085f7278546136d3f | 07:19:09 | ACTION_RESERVED | [보기](#row-event-e30f798011214e8085f7278546136d3f) |
| event-836a58dac23c4f2aa763ea24dbb9d98d | 07:19:24 | ACTION_COMPLETED | [보기](#row-event-836a58dac23c4f2aa763ea24dbb9d98d) |
| event-09f940ea3652416f8ca8e85781389b0a | 07:19:33 | ACTION_COMPLETED | [보기](#row-event-09f940ea3652416f8ca8e85781389b0a) |
| event-28fe38b24a9942dcb38b0412b649189f | 07:19:35 | ACTION_COMPLETED | [보기](#row-event-28fe38b24a9942dcb38b0412b649189f) |
| event-0afe5b54ea5f4a029696920b6135d180 | 07:19:53 | ACTION_RESERVED | [보기](#row-event-0afe5b54ea5f4a029696920b6135d180) |
| event-198afeb848824b0099fbb19d1a1d02d0 | 07:20:02 | ACTION_COMPLETED | [보기](#row-event-198afeb848824b0099fbb19d1a1d02d0) |
| event-15129f51a77747cf95ed4003de93e3b1 | 07:20:11 | ACTION_RESERVED | [보기](#row-event-15129f51a77747cf95ed4003de93e3b1) |
| event-0f98422a728f44629d798a246600db75 | 07:20:21 | ACTION_COMPLETED | [보기](#row-event-0f98422a728f44629d798a246600db75) |
| event-51f3e9fc07b3426ea2347088ce71159e | 07:20:32 | ACTION_RESERVED | [보기](#row-event-51f3e9fc07b3426ea2347088ce71159e) |
| event-1a6e72b5b6c54e20b4a62211c197bb7d | 07:20:37 | ACTION_COMPLETED | [보기](#row-event-1a6e72b5b6c54e20b4a62211c197bb7d) |
| event-659ff07d24ee4f4a82ec491fa04ce703 | 07:20:47 | ACTION_RESERVED | [보기](#row-event-659ff07d24ee4f4a82ec491fa04ce703) |
| event-94b4a9146c814285a86bb75b533b75a4 | 07:20:55 | ACTION_COMPLETED | [보기](#row-event-94b4a9146c814285a86bb75b533b75a4) |
| event-6933b4fb67224cb3a42e185b0e59ed9e | 07:21:06 | ACTION_RESERVED | [보기](#row-event-6933b4fb67224cb3a42e185b0e59ed9e) |
| event-448ee272b002463e984541b242a387f4 | 07:21:13 | ACTION_COMPLETED | [보기](#row-event-448ee272b002463e984541b242a387f4) |
| event-c62c240741bd4aa8a2014657bc62aef5 | 07:21:36 | SNAPSHOT_COMMITTED | [보기](#row-event-c62c240741bd4aa8a2014657bc62aef5) |
| event-6581d07c7a444e2eab96fa0ca4e60722 | 07:22:17 | DECISION_RECORDED | [보기](#row-event-6581d07c7a444e2eab96fa0ca4e60722) |
| event-56d8e294f6274bd782545212d0921b45 | 07:22:21 | ACTION_RESERVED | [보기](#row-event-56d8e294f6274bd782545212d0921b45) |
| event-9cb7615c456d44f28601176bd5349697 | 07:22:37 | ACTION_COMPLETED | [보기](#row-event-9cb7615c456d44f28601176bd5349697) |
| event-a92b88fe90644dda88f045aa24c7000d | 07:22:41 | ACTION_RESERVED | [보기](#row-event-a92b88fe90644dda88f045aa24c7000d) |
| event-b7fa110a0980482e90369bc4330530d4 | 07:22:49 | ACTION_COMPLETED | [보기](#row-event-b7fa110a0980482e90369bc4330530d4) |
| event-16f96a4db4124deb856e7a9eb759bf70 | 07:23:02 | DECISION_RECORDED | [보기](#row-event-16f96a4db4124deb856e7a9eb759bf70) |
| event-8a16975c25784a0d968b868454e1eb29 | 07:23:05 | ACTION_RESERVED | [보기](#row-event-8a16975c25784a0d968b868454e1eb29) |
| event-a15f0c26ba35401c8c6924d9606fce88 | 07:23:21 | ACTION_COMPLETED | [보기](#row-event-a15f0c26ba35401c8c6924d9606fce88) |
| event-e7ed177e88f64b6b97b2ab12d54e76c3 | 07:23:26 | ACTION_RESERVED | [보기](#row-event-e7ed177e88f64b6b97b2ab12d54e76c3) |
| event-0ef1cff83b814459b988203404c05f76 | 07:23:34 | ACTION_COMPLETED | [보기](#row-event-0ef1cff83b814459b988203404c05f76) |
| event-77f8301c3d0f43609c2f023494d5d590 | 07:23:48 | DECISION_RECORDED | [보기](#row-event-77f8301c3d0f43609c2f023494d5d590) |
| event-e408c636650945e7a4ba324b2268fe59 | 07:23:50 | ACTION_RESERVED | [보기](#row-event-e408c636650945e7a4ba324b2268fe59) |
| event-e7eecdef19004f4bb9147d7f05ecdc6e | 07:24:14 | ACTION_COMPLETED | [보기](#row-event-e7eecdef19004f4bb9147d7f05ecdc6e) |
| event-148f76e783814d0a85cfe860e1711f66 | 07:24:17 | ACTION_RESERVED | [보기](#row-event-148f76e783814d0a85cfe860e1711f66) |
| event-c2159b1affa84a528b5916e5af70b17c | 07:24:23 | ACTION_COMPLETED | [보기](#row-event-c2159b1affa84a528b5916e5af70b17c) |
| event-167ea3032a6c46d8bb2c8f9d41e0b8a1 | 07:24:38 | DECISION_RECORDED | [보기](#row-event-167ea3032a6c46d8bb2c8f9d41e0b8a1) |
| event-8d43948a3f5c4f48b5fe13269610f1dc | 07:24:42 | ACTION_RESERVED | [보기](#row-event-8d43948a3f5c4f48b5fe13269610f1dc) |
| event-0b6826c4878a4ca4a9b03adf99ac88f9 | 07:25:02 | ACTION_COMPLETED | [보기](#row-event-0b6826c4878a4ca4a9b03adf99ac88f9) |
| event-5f7ababdfce443f580f69d5199299364 | 07:25:08 | ACTION_RESERVED | [보기](#row-event-5f7ababdfce443f580f69d5199299364) |
| event-fe975dff0eec474894a0ef3dc43e76e8 | 07:25:14 | ACTION_COMPLETED | [보기](#row-event-fe975dff0eec474894a0ef3dc43e76e8) |
| event-d79b680b525c4d188b6bbdd26989f666 | 07:25:27 | SNAPSHOT_COMMITTED | [보기](#row-event-d79b680b525c4d188b6bbdd26989f666) |
| event-4bc812632c744be3a48e592a997ad0a2 | 07:25:51 | ACTION_RESERVED | [보기](#row-event-4bc812632c744be3a48e592a997ad0a2) |
| event-af31e64087814d18b174e2c1544a26b5 | 07:25:53 | ACTION_RESERVED | [보기](#row-event-af31e64087814d18b174e2c1544a26b5) |
| event-071e6c27282b4af180acaf09fa46918a | 07:25:55 | ACTION_RESERVED | [보기](#row-event-071e6c27282b4af180acaf09fa46918a) |
| event-74efb61f57b84fad9f687224e21a11d2 | 07:25:59 | ACTION_RESERVED | [보기](#row-event-74efb61f57b84fad9f687224e21a11d2) |
| event-c391f880c5ff4aafb5059b9944db9037 | 07:25:59 | ACTION_COMPLETED | [보기](#row-event-c391f880c5ff4aafb5059b9944db9037) |
| event-a0f56561506843a38101e062a5e7a45d | 07:25:59 | ACTION_COMPLETED | [보기](#row-event-a0f56561506843a38101e062a5e7a45d) |
| event-b2118e5f873b4180b51ada02a20fa036 | 07:25:59 | ACTION_COMPLETED | [보기](#row-event-b2118e5f873b4180b51ada02a20fa036) |
| event-965a2e51a9b341518d78313e3156b5ef | 07:26:05 | ACTION_RESERVED | [보기](#row-event-965a2e51a9b341518d78313e3156b5ef) |
| event-5f6d178a49894d82b6102655513d3044 | 07:26:07 | ACTION_RESERVED | [보기](#row-event-5f6d178a49894d82b6102655513d3044) |
| event-309be95ffff4434099e6804115c1ff69 | 07:26:09 | ACTION_RESERVED | [보기](#row-event-309be95ffff4434099e6804115c1ff69) |
| event-223fa9e0c33840e586a309ca678ae940 | 07:26:09 | ACTION_COMPLETED | [보기](#row-event-223fa9e0c33840e586a309ca678ae940) |
| event-41e9c19b8f6a45eab1cb38d785f2784c | 07:26:10 | ACTION_COMPLETED | [보기](#row-event-41e9c19b8f6a45eab1cb38d785f2784c) |
| event-bfcc93a5385a45678edf567f0560a818 | 07:26:14 | ACTION_RESERVED | [보기](#row-event-bfcc93a5385a45678edf567f0560a818) |
| event-99cc61a3ef6b4b30bda5e792517de769 | 07:26:14 | ACTION_COMPLETED | [보기](#row-event-99cc61a3ef6b4b30bda5e792517de769) |
| event-3fd60dee2bf34670abb69788185f7491 | 07:26:15 | ACTION_COMPLETED | [보기](#row-event-3fd60dee2bf34670abb69788185f7491) |
| event-46fc56f597804924acd5894c769acdef | 07:26:19 | ACTION_RESERVED | [보기](#row-event-46fc56f597804924acd5894c769acdef) |
| event-43a930a76f144ea38525795e0390aac2 | 07:26:21 | ACTION_RESERVED | [보기](#row-event-43a930a76f144ea38525795e0390aac2) |
| event-c6ba43e8e602413896ff1f1c740d473a | 07:26:21 | ACTION_COMPLETED | [보기](#row-event-c6ba43e8e602413896ff1f1c740d473a) |
| event-07a4cfa30f424b049e1027cc652e2bf0 | 07:26:24 | ACTION_COMPLETED | [보기](#row-event-07a4cfa30f424b049e1027cc652e2bf0) |
| event-163b8b1b528f4b6f9e435afad8c85db4 | 07:26:25 | ACTION_COMPLETED | [보기](#row-event-163b8b1b528f4b6f9e435afad8c85db4) |
| event-6c72e80ae350489586977b64851e910e | 07:26:33 | SNAPSHOT_COMMITTED | [보기](#row-event-6c72e80ae350489586977b64851e910e) |
| event-0495e68f3ef1419a94fde16bd9a2ec09 | 07:31:28 | EPOCH_CHANGED | [보기](#row-event-0495e68f3ef1419a94fde16bd9a2ec09) |
| event-2ea76ea9de3842fcade2840b896b1b9e | 07:32:07 | SNAPSHOT_COMMITTED | [보기](#row-event-2ea76ea9de3842fcade2840b896b1b9e) |
| event-77290f5ad22b47e09aa4bc3f3c83d327 | 07:32:27 | SNAPSHOT_COMMITTED | [보기](#row-event-77290f5ad22b47e09aa4bc3f3c83d327) |
| event-3d51ae987ebd4817a7b04373d25f3c3c | 07:33:03 | DECISION_RECORDED | [보기](#row-event-3d51ae987ebd4817a7b04373d25f3c3c) |
| event-6cfe0d1846ec42a28d8c1b3f2592ef6e | 07:33:06 | ACTION_RESERVED | [보기](#row-event-6cfe0d1846ec42a28d8c1b3f2592ef6e) |
| event-e325f6e4a89c48449978b4464d5c9e07 | 07:33:21 | ACTION_COMPLETED | [보기](#row-event-e325f6e4a89c48449978b4464d5c9e07) |
| event-3473b9bdae2c4631b742ab041880409b | 07:33:28 | ACTION_RESERVED | [보기](#row-event-3473b9bdae2c4631b742ab041880409b) |
| event-babc1e536d694b6eb7c9591d8fb9eaba | 07:33:34 | ACTION_COMPLETED | [보기](#row-event-babc1e536d694b6eb7c9591d8fb9eaba) |
| event-0e6e87a94a3241ec837631fa0e115cf6 | 07:33:46 | DECISION_RECORDED | [보기](#row-event-0e6e87a94a3241ec837631fa0e115cf6) |
| event-ce1e1c268e4040e5b88c6df64c6cea95 | 07:33:51 | ACTION_RESERVED | [보기](#row-event-ce1e1c268e4040e5b88c6df64c6cea95) |
| event-22dca37741674fb3999011487380c9f3 | 07:34:09 | ACTION_COMPLETED | [보기](#row-event-22dca37741674fb3999011487380c9f3) |
| event-54750e0d516d42088d8a6388e6098431 | 07:34:12 | ACTION_RESERVED | [보기](#row-event-54750e0d516d42088d8a6388e6098431) |
| event-1b514cd7c5cb41caa2908110c6f745c5 | 07:34:18 | ACTION_COMPLETED | [보기](#row-event-1b514cd7c5cb41caa2908110c6f745c5) |
| event-e81a008d5bb140a8ad0c67d9a7040aed | 07:34:29 | DECISION_RECORDED | [보기](#row-event-e81a008d5bb140a8ad0c67d9a7040aed) |
| event-9fb047b2b70b4b5c83af1deb6b45eaef | 07:34:32 | ACTION_RESERVED | [보기](#row-event-9fb047b2b70b4b5c83af1deb6b45eaef) |
| event-790ae30ac24f451bae022de2dc8c9c90 | 07:34:50 | ACTION_COMPLETED | [보기](#row-event-790ae30ac24f451bae022de2dc8c9c90) |
| event-d116aa8311ca44cf936bbf088bcd641c | 07:34:56 | ACTION_RESERVED | [보기](#row-event-d116aa8311ca44cf936bbf088bcd641c) |
| event-279e143ca74c449bb51d531b43c9dc53 | 07:35:04 | ACTION_COMPLETED | [보기](#row-event-279e143ca74c449bb51d531b43c9dc53) |
| event-f3c81d8867c142ce8e7b898fe7b2e7c9 | 07:35:17 | DECISION_RECORDED | [보기](#row-event-f3c81d8867c142ce8e7b898fe7b2e7c9) |
| event-94df086ddb454b3d9087469bd9751d12 | 07:35:19 | ACTION_RESERVED | [보기](#row-event-94df086ddb454b3d9087469bd9751d12) |
| event-d0e54aaf509a42a3aa308abfbd69eb01 | 07:35:36 | ACTION_COMPLETED | [보기](#row-event-d0e54aaf509a42a3aa308abfbd69eb01) |
| event-2bf92af7da3c4f5cb381e40b780729d4 | 07:35:40 | ACTION_RESERVED | [보기](#row-event-2bf92af7da3c4f5cb381e40b780729d4) |
| event-94ba82653230418aaf6bdde6c6823ccd | 07:35:47 | ACTION_COMPLETED | [보기](#row-event-94ba82653230418aaf6bdde6c6823ccd) |
| event-7773753aa5784ab48f76154d53cac1ad | 07:35:57 | SNAPSHOT_COMMITTED | [보기](#row-event-7773753aa5784ab48f76154d53cac1ad) |
| event-fd511c29276442c494548db0b29f88f5 | 07:36:06 | DECISION_RECORDED | [보기](#row-event-fd511c29276442c494548db0b29f88f5) |
| event-b3d4bc09078e49db856d42e53fa21c24 | 07:36:44 | ACTION_RESERVED | [보기](#row-event-b3d4bc09078e49db856d42e53fa21c24) |
| event-4060e510cc534997aaec41893e3b7a70 | 07:36:59 | ACTION_COMPLETED | [보기](#row-event-4060e510cc534997aaec41893e3b7a70) |
| event-37261ac9a54940679e36ffa80686308d | 07:37:02 | ACTION_RESERVED | [보기](#row-event-37261ac9a54940679e36ffa80686308d) |
| event-364ab6c8e30845718040e32aebe8a66b | 07:37:22 | ACTION_COMPLETED | [보기](#row-event-364ab6c8e30845718040e32aebe8a66b) |
| event-d9314c6f6b69400791ec5a853366085a | 07:37:25 | ACTION_RESERVED | [보기](#row-event-d9314c6f6b69400791ec5a853366085a) |
| event-692c4c09ae334f548f0d97264c96f11e | 07:37:36 | ACTION_COMPLETED | [보기](#row-event-692c4c09ae334f548f0d97264c96f11e) |
| event-324e2bd6dea147388f13704ad4d0e1fc | 07:37:44 | SNAPSHOT_COMMITTED | [보기](#row-event-324e2bd6dea147388f13704ad4d0e1fc) |
| event-b488967dd386402eaa3a4dd2398a2a7d | 07:38:30 | ACTION_RESERVED | [보기](#row-event-b488967dd386402eaa3a4dd2398a2a7d) |
| event-e7d03c280ffd45838613415c5e46c30c | 07:38:36 | ACTION_COMPLETED | [보기](#row-event-e7d03c280ffd45838613415c5e46c30c) |
| event-0dc706bc2e8e475bb7f290fef7647ea4 | 07:38:48 | ACTION_RESERVED | [보기](#row-event-0dc706bc2e8e475bb7f290fef7647ea4) |
| event-5f60cd06e91c47928a3d0af35c21cded | 07:38:50 | ACTION_RESERVED | [보기](#row-event-5f60cd06e91c47928a3d0af35c21cded) |
| event-bf3ff13f87d4496f9e6fcccbf4118a75 | 07:38:51 | ACTION_RESERVED | [보기](#row-event-bf3ff13f87d4496f9e6fcccbf4118a75) |
| event-38e11dd3a3974fb988c29738c867fbfd | 07:38:53 | ACTION_RESERVED | [보기](#row-event-38e11dd3a3974fb988c29738c867fbfd) |
| event-801e9ddfad1f4c49b6e8b9d61ae086e2 | 07:39:00 | ACTION_COMPLETED | [보기](#row-event-801e9ddfad1f4c49b6e8b9d61ae086e2) |
| event-b459e485fb99451d8e37e83b2d0facd1 | 07:39:03 | ACTION_RESERVED | [보기](#row-event-b459e485fb99451d8e37e83b2d0facd1) |
| event-20d5684b630c4170bff3413c03230bd6 | 07:39:04 | ACTION_COMPLETED | [보기](#row-event-20d5684b630c4170bff3413c03230bd6) |
| event-9e1c250c5ad346e7b3b2cc9bae58d673 | 07:39:07 | ACTION_COMPLETED | [보기](#row-event-9e1c250c5ad346e7b3b2cc9bae58d673) |
| event-ced785796ca349f799edb71a8e0bb397 | 07:39:07 | ACTION_COMPLETED | [보기](#row-event-ced785796ca349f799edb71a8e0bb397) |
| event-a331363b127a4e1c97fdccc694ede1bb | 07:39:20 | ACTION_RESERVED | [보기](#row-event-a331363b127a4e1c97fdccc694ede1bb) |
| event-b62f60de923a419e9d4fa1f0930343d6 | 07:39:20 | ACTION_COMPLETED | [보기](#row-event-b62f60de923a419e9d4fa1f0930343d6) |
| event-f72dd730ab5b46daabca3c82de0d73da | 07:39:28 | ACTION_COMPLETED | [보기](#row-event-f72dd730ab5b46daabca3c82de0d73da) |
| event-812a35e85fb44e71b4fc95e723c4aee8 | 07:39:37 | ACTION_RESERVED | [보기](#row-event-812a35e85fb44e71b4fc95e723c4aee8) |
| event-b378e7ffaf974e62b831ce3973d60dd8 | 07:39:43 | ACTION_RESERVED | [보기](#row-event-b378e7ffaf974e62b831ce3973d60dd8) |
| event-04187a23c7474b2eab133c256a41ec8b | 07:39:45 | ACTION_RESERVED | [보기](#row-event-04187a23c7474b2eab133c256a41ec8b) |
| event-be87c2259de046c3b1715ef7afe57985 | 07:39:45 | ACTION_COMPLETED | [보기](#row-event-be87c2259de046c3b1715ef7afe57985) |
| event-6f0406421cbc4aeb8d1c1d5ab095196a | 07:39:53 | ACTION_COMPLETED | [보기](#row-event-6f0406421cbc4aeb8d1c1d5ab095196a) |
| event-5d02cb989ddc4947a878744c52425c8b | 07:39:53 | ACTION_COMPLETED | [보기](#row-event-5d02cb989ddc4947a878744c52425c8b) |
| event-03b49469487f41958eed90f47dd26e77 | 07:40:02 | ACTION_RESERVED | [보기](#row-event-03b49469487f41958eed90f47dd26e77) |
| event-a2144bede2754cb28840ea6a1c8302a9 | 07:40:14 | ACTION_RESERVED | [보기](#row-event-a2144bede2754cb28840ea6a1c8302a9) |
| event-4a97d95f572f4d10b04d0930e615a124 | 07:40:14 | ACTION_COMPLETED | [보기](#row-event-4a97d95f572f4d10b04d0930e615a124) |
| event-e6c179c1ea2c41ebabe209c4a1d831da | 07:40:33 | ACTION_COMPLETED | [보기](#row-event-e6c179c1ea2c41ebabe209c4a1d831da) |
| event-8598ea15771141e58ac498573237c9a8 | 07:41:01 | ACTION_RESERVED | [보기](#row-event-8598ea15771141e58ac498573237c9a8) |
| event-97890cc3059849e48dc43de52905e567 | 07:41:05 | ACTION_RESERVED | [보기](#row-event-97890cc3059849e48dc43de52905e567) |
| event-b289a08c94d34431ac6803eb4f4ed09b | 07:41:10 | ACTION_COMPLETED | [보기](#row-event-b289a08c94d34431ac6803eb4f4ed09b) |
| event-848f487dc31944aba0729562cea683b2 | 07:41:13 | ACTION_COMPLETED | [보기](#row-event-848f487dc31944aba0729562cea683b2) |
| event-c0c4e02ab96747ba87e36508df6fda2e | 07:41:57 | ACTION_RESERVED | [보기](#row-event-c0c4e02ab96747ba87e36508df6fda2e) |
| event-9aa9e3eb1707466aa163e0ab5b156ff3 | 07:42:07 | ACTION_COMPLETED | [보기](#row-event-9aa9e3eb1707466aa163e0ab5b156ff3) |
| event-70bd128ee8dc489ba9f64acd7ec18e63 | 07:42:14 | SNAPSHOT_COMMITTED | [보기](#row-event-70bd128ee8dc489ba9f64acd7ec18e63) |
| event-3d7b63e3d368413489cdadd30336985a | 07:42:59 | SNAPSHOT_COMMITTED | [보기](#row-event-3d7b63e3d368413489cdadd30336985a) |
| event-1e39d8967f1d4a1a94c42a7ea3701877 | 07:43:10 | DECISION_RECORDED | [보기](#row-event-1e39d8967f1d4a1a94c42a7ea3701877) |
| event-93b93b5530844750979aff68704d0288 | 07:43:38 | SNAPSHOT_COMMITTED | [보기](#row-event-93b93b5530844750979aff68704d0288) |
| event-df21e948b27145568051ca6b64cd8d70 | 07:44:19 | SNAPSHOT_COMMITTED | [보기](#row-event-df21e948b27145568051ca6b64cd8d70) |
| event-9e38aa05bfbd4c18adbe4ee4d6e3617c | 07:57:01 | EPOCH_CHANGED | [보기](#row-event-9e38aa05bfbd4c18adbe4ee4d6e3617c) |
| event-3708c748d0f84f53a4303e6e7c231e1e | 07:57:39 | SNAPSHOT_COMMITTED | [보기](#row-event-3708c748d0f84f53a4303e6e7c231e1e) |
| event-d3fce5ae797740209fc2d52a11a837cb | 07:58:08 | ACTION_RESERVED | [보기](#row-event-d3fce5ae797740209fc2d52a11a837cb) |
| event-caf5963a6a02421cbf6ffc5daac943bc | 07:58:13 | ACTION_COMPLETED | [보기](#row-event-caf5963a6a02421cbf6ffc5daac943bc) |
| event-6c2e88d6298741d596ddc8b00c21f1f9 | 07:58:22 | SNAPSHOT_COMMITTED | [보기](#row-event-6c2e88d6298741d596ddc8b00c21f1f9) |

<a id="row-event-0e988893c44a456d869846f410eaaaa3"></a>

<details>
<summary>event-0e988893c44a456d869846f410eaaaa3 · 전체 저장값</summary>

```json
{
  "event_id": "event-0e988893c44a456d869846f410eaaaa3",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 47,
    "previous": 46,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T21:46:26.233412+00:00"
}
```

</details>

<a id="row-event-1126c4ec51764fca8c8b75d0b6a6a915"></a>

<details>
<summary>event-1126c4ec51764fca8c8b75d0b6a6a915 · 전체 저장값</summary>

```json
{
  "event_id": "event-1126c4ec51764fca8c8b75d0b6a6a915",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-e6e662cc4e1a4696b2e92a1ecd6ecab0",
    "versions": []
  },
  "created_at": "2026-09-29T21:46:55.550302+00:00"
}
```

</details>

<a id="row-event-60135bf499f04333a21301b2267dc539"></a>

<details>
<summary>event-60135bf499f04333a21301b2267dc539 · 전체 저장값</summary>

```json
{
  "event_id": "event-60135bf499f04333a21301b2267dc539",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 92949,
    "task_id": "task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2"
  },
  "created_at": "2026-09-29T21:47:22.913104+00:00"
}
```

</details>

<a id="row-event-12550159e785428eb582dac492bc7bc9"></a>

<details>
<summary>event-12550159e785428eb582dac492bc7bc9 · 전체 저장값</summary>

```json
{
  "event_id": "event-12550159e785428eb582dac492bc7bc9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3326,
    "task_id": "task-4140d22333b0e1515d19ec22bfaef06ac66c89c905e33119c664cbdaeeb2"
  },
  "created_at": "2026-09-29T21:47:32.320317+00:00"
}
```

</details>

<a id="row-event-f2502343d932403c8d1c433ee87fcbd4"></a>

<details>
<summary>event-f2502343d932403c8d1c433ee87fcbd4 · 전체 저장값</summary>

```json
{
  "event_id": "event-f2502343d932403c8d1c433ee87fcbd4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "problem",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-69f32964ae364eeab69e07d5b5375a6f",
    "versions": [
      "av-5ce999f9d9444777986ba30b67e5e79e"
    ]
  },
  "created_at": "2026-09-29T21:47:32.606651+00:00"
}
```

</details>

<a id="row-event-3f47739fecff4a359a37565d83aeca61"></a>

<details>
<summary>event-3f47739fecff4a359a37565d83aeca61 · 전체 저장값</summary>

```json
{
  "event_id": "event-3f47739fecff4a359a37565d83aeca61",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 48,
    "previous": 47,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T21:49:07.253886+00:00"
}
```

</details>

<a id="row-event-b5ef7fcf0b2343d1b9f5f9f397774f86"></a>

<details>
<summary>event-b5ef7fcf0b2343d1b9f5f9f397774f86 · 전체 저장값</summary>

```json
{
  "event_id": "event-b5ef7fcf0b2343d1b9f5f9f397774f86",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-77d1bbb8d3374e44aab6472310bb4c65",
    "versions": []
  },
  "created_at": "2026-09-29T21:49:31.676056+00:00"
}
```

</details>

<a id="row-event-2ec47bd9bdae4068afd92f1cc3b922fd"></a>

<details>
<summary>event-2ec47bd9bdae4068afd92f1cc3b922fd · 전체 저장값</summary>

```json
{
  "event_id": "event-2ec47bd9bdae4068afd92f1cc3b922fd",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 93759,
    "task_id": "task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8"
  },
  "created_at": "2026-09-29T21:49:49.902956+00:00"
}
```

</details>

<a id="row-event-5778788995a34b5f8d9cf86626b5d87e"></a>

<details>
<summary>event-5778788995a34b5f8d9cf86626b5d87e · 전체 저장값</summary>

```json
{
  "event_id": "event-5778788995a34b5f8d9cf86626b5d87e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3407,
    "task_id": "task-31309ea4a9bfa0c8e76281afab271b67a35ba8e2e89d7220c8f54a5531e8"
  },
  "created_at": "2026-09-29T21:49:58.762897+00:00"
}
```

</details>

<a id="row-event-9be5cf3c0fab452395c637015bf22a5a"></a>

<details>
<summary>event-9be5cf3c0fab452395c637015bf22a5a · 전체 저장값</summary>

```json
{
  "event_id": "event-9be5cf3c0fab452395c637015bf22a5a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "problem",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-637dd636b5614fdb9b0958244b6bb1ae",
    "versions": [
      "av-da1805ee57974f8597fc5971a001282f"
    ]
  },
  "created_at": "2026-09-29T21:49:59.028124+00:00"
}
```

</details>

<a id="row-event-23fc4a7d3c484c1881a0fcbf327aa1ad"></a>

<details>
<summary>event-23fc4a7d3c484c1881a0fcbf327aa1ad · 전체 저장값</summary>

```json
{
  "event_id": "event-23fc4a7d3c484c1881a0fcbf327aa1ad",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 62249,
    "task_id": "task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a"
  },
  "created_at": "2026-09-29T21:50:47.605067+00:00"
}
```

</details>

<a id="row-event-a8c4f7d1f706492c9524c1a81f090a4a"></a>

<details>
<summary>event-a8c4f7d1f706492c9524c1a81f090a4a · 전체 저장값</summary>

```json
{
  "event_id": "event-a8c4f7d1f706492c9524c1a81f090a4a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6371,
    "task_id": "task-454b48aac14d282a3bce3fc190441fb56eea1366db554daf7c2eaec11a7a"
  },
  "created_at": "2026-09-29T21:50:58.540627+00:00"
}
```

</details>

<a id="row-event-eedaa927823041dd8949e5458ec9a1d9"></a>

<details>
<summary>event-eedaa927823041dd8949e5458ec9a1d9 · 전체 저장값</summary>

```json
{
  "event_id": "event-eedaa927823041dd8949e5458ec9a1d9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 59526,
    "task_id": "task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067"
  },
  "created_at": "2026-09-29T21:51:11.542249+00:00"
}
```

</details>

<a id="row-event-ff632ebddb564c30adaaa34e533f25e7"></a>

<details>
<summary>event-ff632ebddb564c30adaaa34e533f25e7 · 전체 저장값</summary>

```json
{
  "event_id": "event-ff632ebddb564c30adaaa34e533f25e7",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2294,
    "task_id": "task-83a37ccdeb1c5e04bef657c80f426364dba6e3f3e3a6531d7d2f53705067"
  },
  "created_at": "2026-09-29T21:51:13.864370+00:00"
}
```

</details>

<a id="row-event-a228557e3dda44e4b87c31aa72cfd3c4"></a>

<details>
<summary>event-a228557e3dda44e4b87c31aa72cfd3c4 · 전체 저장값</summary>

```json
{
  "event_id": "event-a228557e3dda44e4b87c31aa72cfd3c4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "problem",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-9c28f1071f1a493fa73df97f966ec5c0",
    "versions": [
      "av-04f9e092ef9d43c49ab2f224bd4be2ff"
    ]
  },
  "created_at": "2026-09-29T21:51:19.318625+00:00"
}
```

</details>

<a id="row-event-5aeccff6ab36490ab6922bf6395e4747"></a>

<details>
<summary>event-5aeccff6ab36490ab6922bf6395e4747 · 전체 저장값</summary>

```json
{
  "event_id": "event-5aeccff6ab36490ab6922bf6395e4747",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 49,
    "previous": 48,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T21:52:06.711433+00:00"
}
```

</details>

<a id="row-event-04ebda3cc27a461187fac4757c3c3918"></a>

<details>
<summary>event-04ebda3cc27a461187fac4757c3c3918 · 전체 저장값</summary>

```json
{
  "event_id": "event-04ebda3cc27a461187fac4757c3c3918",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-057b74df690c4957b6613656b36fcf38",
    "versions": []
  },
  "created_at": "2026-09-29T21:52:32.580085+00:00"
}
```

</details>

<a id="row-event-50587501e57748aaa864a03d2b6fa49f"></a>

<details>
<summary>event-50587501e57748aaa864a03d2b6fa49f · 전체 저장값</summary>

```json
{
  "event_id": "event-50587501e57748aaa864a03d2b6fa49f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 61270,
    "task_id": "task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7"
  },
  "created_at": "2026-09-29T21:52:58.228900+00:00"
}
```

</details>

<a id="row-event-fc18e66c2c4d4b49a7a7a06bd7cb33ee"></a>

<details>
<summary>event-fc18e66c2c4d4b49a7a7a06bd7cb33ee · 전체 저장값</summary>

```json
{
  "event_id": "event-fc18e66c2c4d4b49a7a7a06bd7cb33ee",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6206,
    "task_id": "task-227da7c56e3c5aa2abb5e3824a23bc662fdca5c66998f55afd8f24ce11c7"
  },
  "created_at": "2026-09-29T21:53:09.130972+00:00"
}
```

</details>

<a id="row-event-623e4b49a45c455a99745109a440cf7f"></a>

<details>
<summary>event-623e4b49a45c455a99745109a440cf7f · 전체 저장값</summary>

```json
{
  "event_id": "event-623e4b49a45c455a99745109a440cf7f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "problem",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-530bf632a2824745af2db86e237c95df",
    "versions": [
      "av-4415f0c5e3d74db09648dde3edfa65ba"
    ]
  },
  "created_at": "2026-09-29T21:53:17.524313+00:00"
}
```

</details>

<a id="row-event-a5af1e19a18e4a9a83cbd9ef0e88df7a"></a>

<details>
<summary>event-a5af1e19a18e4a9a83cbd9ef0e88df7a · 전체 저장값</summary>

```json
{
  "event_id": "event-a5af1e19a18e4a9a83cbd9ef0e88df7a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 96150,
    "task_id": "task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1"
  },
  "created_at": "2026-09-29T21:53:58.054264+00:00"
}
```

</details>

<a id="row-event-f68589db610b46c8a2793e56dc2f7c51"></a>

<details>
<summary>event-f68589db610b46c8a2793e56dc2f7c51 · 전체 저장값</summary>

```json
{
  "event_id": "event-f68589db610b46c8a2793e56dc2f7c51",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3377,
    "task_id": "task-55eb7897cf866e0418ecd9216e18ba3ba5256827bc1d057a66356a0940d1"
  },
  "created_at": "2026-09-29T21:54:04.543393+00:00"
}
```

</details>

<a id="row-event-c72b1c1cf4644e86ab1ca0844be34219"></a>

<details>
<summary>event-c72b1c1cf4644e86ab1ca0844be34219 · 전체 저장값</summary>

```json
{
  "event_id": "event-c72b1c1cf4644e86ab1ca0844be34219",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-2498749a17b64716a92df6e26df510fd",
    "versions": [
      "av-95b8f1e196294604bc4a71db72e4305c"
    ]
  },
  "created_at": "2026-09-29T21:54:10.683396+00:00"
}
```

</details>

<a id="row-event-055891ab577e478ebbccdb0a230bba6c"></a>

<details>
<summary>event-055891ab577e478ebbccdb0a230bba6c · 전체 저장값</summary>

```json
{
  "event_id": "event-055891ab577e478ebbccdb0a230bba6c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 50,
    "previous": 49,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T22:06:02.417894+00:00"
}
```

</details>

<a id="row-event-34cb350f5b2a4bccaf18647a3c09ea54"></a>

<details>
<summary>event-34cb350f5b2a4bccaf18647a3c09ea54 · 전체 저장값</summary>

```json
{
  "event_id": "event-34cb350f5b2a4bccaf18647a3c09ea54",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-1869b2a3c96f4bffadf87d11c3086237",
    "versions": []
  },
  "created_at": "2026-09-29T22:06:31.412631+00:00"
}
```

</details>

<a id="row-event-e4959864d59d4b7aacd1fb4a1c4bb9b0"></a>

<details>
<summary>event-e4959864d59d4b7aacd1fb4a1c4bb9b0 · 전체 저장값</summary>

```json
{
  "event_id": "event-e4959864d59d4b7aacd1fb4a1c4bb9b0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "analysis",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-48dde9a56a904700ba6518af3610184a",
    "versions": [
      "av-011963b3da4b406aa99f3c20e1c2b1ca"
    ]
  },
  "created_at": "2026-09-29T22:06:48.627093+00:00"
}
```

</details>

<a id="row-event-a7cf32c6f29947a9b7c6ccec41e17c77"></a>

<details>
<summary>event-a7cf32c6f29947a9b7c6ccec41e17c77 · 전체 저장값</summary>

```json
{
  "event_id": "event-a7cf32c6f29947a9b7c6ccec41e17c77",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 97397,
    "task_id": "task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761"
  },
  "created_at": "2026-09-29T22:07:35.641277+00:00"
}
```

</details>

<a id="row-event-4eddf5da69da4de1a9a7152ad7b1993d"></a>

<details>
<summary>event-4eddf5da69da4de1a9a7152ad7b1993d · 전체 저장값</summary>

```json
{
  "event_id": "event-4eddf5da69da4de1a9a7152ad7b1993d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3713,
    "task_id": "task-07087684b93d7e4dc4fed09b9a9790427b9b9a4f31ebbff06c61d6a06761"
  },
  "created_at": "2026-09-29T22:07:44.671395+00:00"
}
```

</details>

<a id="row-event-c91b251ff0fb4bb2ad8d1cd1434b30cf"></a>

<details>
<summary>event-c91b251ff0fb4bb2ad8d1cd1434b30cf · 전체 저장값</summary>

```json
{
  "event_id": "event-c91b251ff0fb4bb2ad8d1cd1434b30cf",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100721,
    "task_id": "task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f"
  },
  "created_at": "2026-09-29T22:07:50.545760+00:00"
}
```

</details>

<a id="row-event-fbaf9499429c4efe9ed7601a5758b2fe"></a>

<details>
<summary>event-fbaf9499429c4efe9ed7601a5758b2fe · 전체 저장값</summary>

```json
{
  "event_id": "event-fbaf9499429c4efe9ed7601a5758b2fe",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5999,
    "task_id": "task-1ca99fc15ecb6941c30d06eb7a776c61b1fed4719b22e1a0690bef73da6f"
  },
  "created_at": "2026-09-29T22:08:02.909361+00:00"
}
```

</details>

<a id="row-event-6479b7682fb940629ffefcf4a2708b5b"></a>

<details>
<summary>event-6479b7682fb940629ffefcf4a2708b5b · 전체 저장값</summary>

```json
{
  "event_id": "event-6479b7682fb940629ffefcf4a2708b5b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 41435,
    "task_id": "task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a"
  },
  "created_at": "2026-09-29T22:08:06.283777+00:00"
}
```

</details>

<a id="row-event-7258ad7160904c6ab2d1ec67ddbc7d3a"></a>

<details>
<summary>event-7258ad7160904c6ab2d1ec67ddbc7d3a · 전체 저장값</summary>

```json
{
  "event_id": "event-7258ad7160904c6ab2d1ec67ddbc7d3a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3168,
    "task_id": "task-3e3a156f2cda8792e1bc173cd3d7d211dd2cf0dc92cd8a786cd1873bcc5a"
  },
  "created_at": "2026-09-29T22:08:10.766705+00:00"
}
```

</details>

<a id="row-event-8648cd3dc21c458ebd23935f7c5c0fea"></a>

<details>
<summary>event-8648cd3dc21c458ebd23935f7c5c0fea · 전체 저장값</summary>

```json
{
  "event_id": "event-8648cd3dc21c458ebd23935f7c5c0fea",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 99469,
    "task_id": "task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc"
  },
  "created_at": "2026-09-29T22:08:21.897671+00:00"
}
```

</details>

<a id="row-event-2034880183fa4c3486a2b12b7edacb73"></a>

<details>
<summary>event-2034880183fa4c3486a2b12b7edacb73 · 전체 저장값</summary>

```json
{
  "event_id": "event-2034880183fa4c3486a2b12b7edacb73",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100055,
    "task_id": "task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d"
  },
  "created_at": "2026-09-29T22:08:23.450401+00:00"
}
```

</details>

<a id="row-event-056e7c0941844960885b1bb6675efe14"></a>

<details>
<summary>event-056e7c0941844960885b1bb6675efe14 · 전체 저장값</summary>

```json
{
  "event_id": "event-056e7c0941844960885b1bb6675efe14",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 99589,
    "task_id": "task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799"
  },
  "created_at": "2026-09-29T22:08:24.987994+00:00"
}
```

</details>

<a id="row-event-200f0a4774594f9f9231b7f7bc9a8d0e"></a>

<details>
<summary>event-200f0a4774594f9f9231b7f7bc9a8d0e · 전체 저장값</summary>

```json
{
  "event_id": "event-200f0a4774594f9f9231b7f7bc9a8d0e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2450,
    "task_id": "task-1b76d517e1bec52e218a3a83a505618c2e2cf9ddaeea1cf355225acef799"
  },
  "created_at": "2026-09-29T22:08:26.593686+00:00"
}
```

</details>

<a id="row-event-c0cbb0004600420db135f411e9ca4630"></a>

<details>
<summary>event-c0cbb0004600420db135f411e9ca4630 · 전체 저장값</summary>

```json
{
  "event_id": "event-c0cbb0004600420db135f411e9ca4630",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5607,
    "task_id": "task-642c473a09db9b1b08fc9f65f36dff000b92664ec1b632f2cfdcf0f061fc"
  },
  "created_at": "2026-09-29T22:08:35.203179+00:00"
}
```

</details>

<a id="row-event-3c9dff22015f45578b8e631c55bc6dfc"></a>

<details>
<summary>event-3c9dff22015f45578b8e631c55bc6dfc · 전체 저장값</summary>

```json
{
  "event_id": "event-3c9dff22015f45578b8e631c55bc6dfc",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5799,
    "task_id": "task-5f74fe7f1b9e5910240fd1cae9baba4db2712518532e1640b96a9f5ac61d"
  },
  "created_at": "2026-09-29T22:08:35.585194+00:00"
}
```

</details>

<a id="row-event-feb9302f315e487697b01aae6a6a3917"></a>

<details>
<summary>event-feb9302f315e487697b01aae6a6a3917 · 전체 저장값</summary>

```json
{
  "event_id": "event-feb9302f315e487697b01aae6a6a3917",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 40550,
    "task_id": "task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af"
  },
  "created_at": "2026-09-29T22:08:38.763467+00:00"
}
```

</details>

<a id="row-event-b98757ce95e84d6083475b4dd5063e02"></a>

<details>
<summary>event-b98757ce95e84d6083475b4dd5063e02 · 전체 저장값</summary>

```json
{
  "event_id": "event-b98757ce95e84d6083475b4dd5063e02",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2880,
    "task_id": "task-e0fb50dd1d5d9adf01b1c245776047f193063366a1aeedc7894da26365af"
  },
  "created_at": "2026-09-29T22:08:42.896859+00:00"
}
```

</details>

<a id="row-event-7503ca69215c499da17fe2a41661431b"></a>

<details>
<summary>event-7503ca69215c499da17fe2a41661431b · 전체 저장값</summary>

```json
{
  "event_id": "event-7503ca69215c499da17fe2a41661431b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 102827,
    "task_id": "task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da"
  },
  "created_at": "2026-09-29T22:08:48.150480+00:00"
}
```

</details>

<a id="row-event-1c9e768ff6cb429989b50b033db7182e"></a>

<details>
<summary>event-1c9e768ff6cb429989b50b033db7182e · 전체 저장값</summary>

```json
{
  "event_id": "event-1c9e768ff6cb429989b50b033db7182e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5961,
    "task_id": "task-2a14edfec37abdf8af0637571bb6c651219733f5bfb28db7e0617e8042da"
  },
  "created_at": "2026-09-29T22:08:58.065072+00:00"
}
```

</details>

<a id="row-event-c5d943be20464f8898470298ecdcf5b6"></a>

<details>
<summary>event-c5d943be20464f8898470298ecdcf5b6 · 전체 저장값</summary>

```json
{
  "event_id": "event-c5d943be20464f8898470298ecdcf5b6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "definition",
      "evidence",
      "report",
      "concepts",
      "selection",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-e0ba08dd32b4463c80e07f67ef45bec7",
    "versions": [
      "av-2bc340c2ccb84491beb6b27d284b2ef0"
    ]
  },
  "created_at": "2026-09-29T22:09:05.616891+00:00"
}
```

</details>

<a id="row-event-0ababd31e20e45ee95e150022dcdabcf"></a>

<details>
<summary>event-0ababd31e20e45ee95e150022dcdabcf · 전체 저장값</summary>

```json
{
  "event_id": "event-0ababd31e20e45ee95e150022dcdabcf",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 98122,
    "task_id": "task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6"
  },
  "created_at": "2026-09-29T22:09:49.697301+00:00"
}
```

</details>

<a id="row-event-2cfaa4803bd94947a553949749a62206"></a>

<details>
<summary>event-2cfaa4803bd94947a553949749a62206 · 전체 저장값</summary>

```json
{
  "event_id": "event-2cfaa4803bd94947a553949749a62206",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 105888,
    "task_id": "task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a"
  },
  "created_at": "2026-09-29T22:09:51.288161+00:00"
}
```

</details>

<a id="row-event-ba1e65c0cbfb47ac8f45000ed0aa5c9e"></a>

<details>
<summary>event-ba1e65c0cbfb47ac8f45000ed0aa5c9e · 전체 저장값</summary>

```json
{
  "event_id": "event-ba1e65c0cbfb47ac8f45000ed0aa5c9e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 101398,
    "task_id": "task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc"
  },
  "created_at": "2026-09-29T22:09:52.728367+00:00"
}
```

</details>

<a id="row-event-58ef89a4e13c4950a044f695e0f535ed"></a>

<details>
<summary>event-58ef89a4e13c4950a044f695e0f535ed · 전체 저장값</summary>

```json
{
  "event_id": "event-58ef89a4e13c4950a044f695e0f535ed",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2899,
    "task_id": "task-4d1ac8442fa88186b887fe20c5e96706d023a37c13a911a8898c161bdbe6"
  },
  "created_at": "2026-09-29T22:09:54.917322+00:00"
}
```

</details>

<a id="row-event-eeefc117534940cf9bed7b7cda2cd4c2"></a>

<details>
<summary>event-eeefc117534940cf9bed7b7cda2cd4c2 · 전체 저장값</summary>

```json
{
  "event_id": "event-eeefc117534940cf9bed7b7cda2cd4c2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3967,
    "task_id": "task-7975fed2633982643412789abe142fb93f8871392f2a615ff59a2fe26dbc"
  },
  "created_at": "2026-09-29T22:09:59.444475+00:00"
}
```

</details>

<a id="row-event-729dfe8a5e70470dbb9859d8b0d34869"></a>

<details>
<summary>event-729dfe8a5e70470dbb9859d8b0d34869 · 전체 저장값</summary>

```json
{
  "event_id": "event-729dfe8a5e70470dbb9859d8b0d34869",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6366,
    "task_id": "task-6056abfac54f7354815838064327a60280048ffc0bd709858fe2f5050a7a"
  },
  "created_at": "2026-09-29T22:10:03.279472+00:00"
}
```

</details>

<a id="row-event-80fc320b72854697a848ec6c1b47cdec"></a>

<details>
<summary>event-80fc320b72854697a848ec6c1b47cdec · 전체 저장값</summary>

```json
{
  "event_id": "event-80fc320b72854697a848ec6c1b47cdec",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 46826,
    "task_id": "task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d"
  },
  "created_at": "2026-09-29T22:10:08.687864+00:00"
}
```

</details>

<a id="row-event-42bacd272b5848e186000cd6f8dfc24e"></a>

<details>
<summary>event-42bacd272b5848e186000cd6f8dfc24e · 전체 저장값</summary>

```json
{
  "event_id": "event-42bacd272b5848e186000cd6f8dfc24e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 4642,
    "task_id": "task-5b545aa0bfee7f2701eda8dd6b383b5f92a17d807e87260ae6c6f69af75d"
  },
  "created_at": "2026-09-29T22:10:16.037458+00:00"
}
```

</details>

<a id="row-event-4463bce6274348fbbd84864af80f2acb"></a>

<details>
<summary>event-4463bce6274348fbbd84864af80f2acb · 전체 저장값</summary>

```json
{
  "event_id": "event-4463bce6274348fbbd84864af80f2acb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100828,
    "task_id": "task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce"
  },
  "created_at": "2026-09-29T22:10:21.124078+00:00"
}
```

</details>

<a id="row-event-c76629e49c954710843a2fa0e30d37b6"></a>

<details>
<summary>event-c76629e49c954710843a2fa0e30d37b6 · 전체 저장값</summary>

```json
{
  "event_id": "event-c76629e49c954710843a2fa0e30d37b6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3386,
    "task_id": "task-c4fa39e362d672f440a677a22488b2fff9952e961d2064bd60a8153507ce"
  },
  "created_at": "2026-09-29T22:10:26.189477+00:00"
}
```

</details>

<a id="row-event-1b66ac32a163425bb3be32e0b959f7da"></a>

<details>
<summary>event-1b66ac32a163425bb3be32e0b959f7da · 전체 저장값</summary>

```json
{
  "event_id": "event-1b66ac32a163425bb3be32e0b959f7da",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "concepts",
      "evidence",
      "report",
      "selection",
      "coherence",
      "feedback",
      "report_context",
      "solve"
    ],
    "snapshot_id": "snap-4487c9a6151141879697ca76241925e4",
    "versions": [
      "av-1cb9c589494c44b0a4818055a455b84c",
      "av-52dc28df694f41eab49c26cd7073fed0"
    ]
  },
  "created_at": "2026-09-29T22:10:31.908876+00:00"
}
```

</details>

<a id="row-event-a03e5772dddf464e9e0b02f59b30bac4"></a>

<details>
<summary>event-a03e5772dddf464e9e0b02f59b30bac4 · 전체 저장값</summary>

```json
{
  "event_id": "event-a03e5772dddf464e9e0b02f59b30bac4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-d820d7cad35789e857b53f1f387ee9ad76801e719694d6adf83471d93085"
  },
  "created_at": "2026-09-29T22:10:58.189369+00:00"
}
```

</details>

<a id="row-event-1afdf23913364d8392ef49c1747e898b"></a>

<details>
<summary>event-1afdf23913364d8392ef49c1747e898b · 전체 저장값</summary>

```json
{
  "event_id": "event-1afdf23913364d8392ef49c1747e898b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 98868,
    "task_id": "task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265"
  },
  "created_at": "2026-09-29T22:11:16.287215+00:00"
}
```

</details>

<a id="row-event-b4e339307ffb4ecd8c5b4f50f98f95c1"></a>

<details>
<summary>event-b4e339307ffb4ecd8c5b4f50f98f95c1 · 전체 저장값</summary>

```json
{
  "event_id": "event-b4e339307ffb4ecd8c5b4f50f98f95c1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 98825,
    "task_id": "task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9"
  },
  "created_at": "2026-09-29T22:11:17.909903+00:00"
}
```

</details>

<a id="row-event-9714e9aa07d5494c9ca8f3b89d03e3f2"></a>

<details>
<summary>event-9714e9aa07d5494c9ca8f3b89d03e3f2 · 전체 저장값</summary>

```json
{
  "event_id": "event-9714e9aa07d5494c9ca8f3b89d03e3f2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100764,
    "task_id": "task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e"
  },
  "created_at": "2026-09-29T22:11:19.460190+00:00"
}
```

</details>

<a id="row-event-e5a07b125284427f835d539c6be1a43f"></a>

<details>
<summary>event-e5a07b125284427f835d539c6be1a43f · 전체 저장값</summary>

```json
{
  "event_id": "event-e5a07b125284427f835d539c6be1a43f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2308,
    "task_id": "task-66bf3a8cd3eb997b863358a2af7de5045644f3e9a994646f96661f64f8d9"
  },
  "created_at": "2026-09-29T22:11:20.336432+00:00"
}
```

</details>

<a id="row-event-04983c53935c45f3a94876ded364697a"></a>

<details>
<summary>event-04983c53935c45f3a94876ded364697a · 전체 저장값</summary>

```json
{
  "event_id": "event-04983c53935c45f3a94876ded364697a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 101066,
    "task_id": "task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c"
  },
  "created_at": "2026-09-29T22:11:27.794631+00:00"
}
```

</details>

<a id="row-event-058067fc7d5147b8a7c143127e601784"></a>

<details>
<summary>event-058067fc7d5147b8a7c143127e601784 · 전체 저장값</summary>

```json
{
  "event_id": "event-058067fc7d5147b8a7c143127e601784",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 4593,
    "task_id": "task-3db597ee10bd97559977e992f5115063374692ab4a6d2eeacc28bea1399e"
  },
  "created_at": "2026-09-29T22:11:28.864017+00:00"
}
```

</details>

<a id="row-event-dc700fafecea4aa4ae64516f4ef2adfb"></a>

<details>
<summary>event-dc700fafecea4aa4ae64516f4ef2adfb · 전체 저장값</summary>

```json
{
  "event_id": "event-dc700fafecea4aa4ae64516f4ef2adfb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6753,
    "task_id": "task-e933a9eb570490fbf9ca36e6e9adec45b00ec0f392c02449b4ecf7b30265"
  },
  "created_at": "2026-09-29T22:11:31.779122+00:00"
}
```

</details>

<a id="row-event-86db933698de466c842a79c2a0e397ea"></a>

<details>
<summary>event-86db933698de466c842a79c2a0e397ea · 전체 저장값</summary>

```json
{
  "event_id": "event-86db933698de466c842a79c2a0e397ea",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100811,
    "task_id": "task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008"
  },
  "created_at": "2026-09-29T22:11:37.215187+00:00"
}
```

</details>

<a id="row-event-bc1c6d0228534c5da8c8ba2a38ec76bd"></a>

<details>
<summary>event-bc1c6d0228534c5da8c8ba2a38ec76bd · 전체 저장값</summary>

```json
{
  "event_id": "event-bc1c6d0228534c5da8c8ba2a38ec76bd",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 108275,
    "task_id": "task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043"
  },
  "created_at": "2026-09-29T22:11:38.773248+00:00"
}
```

</details>

<a id="row-event-86fc94ffd11a40a3aab8289f1de2e8e9"></a>

<details>
<summary>event-86fc94ffd11a40a3aab8289f1de2e8e9 · 전체 저장값</summary>

```json
{
  "event_id": "event-86fc94ffd11a40a3aab8289f1de2e8e9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6283,
    "task_id": "task-4c134d293a392b94a7b115fead22c921143aa7dcaf458b6cd4ce0633694c"
  },
  "created_at": "2026-09-29T22:11:43.688440+00:00"
}
```

</details>

<a id="row-event-f74867bb282843dfb8bf4273d8c8f518"></a>

<details>
<summary>event-f74867bb282843dfb8bf4273d8c8f518 · 전체 저장값</summary>

```json
{
  "event_id": "event-f74867bb282843dfb8bf4273d8c8f518",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 4547,
    "task_id": "task-dea0ca3df3616ac722f9f7da8e5fbbb4c2b4d0366fb6e6e811514226e008"
  },
  "created_at": "2026-09-29T22:11:46.694387+00:00"
}
```

</details>

<a id="row-event-57b5ae6ffc47448791cdf5e03ed6c4bc"></a>

<details>
<summary>event-57b5ae6ffc47448791cdf5e03ed6c4bc · 전체 저장값</summary>

```json
{
  "event_id": "event-57b5ae6ffc47448791cdf5e03ed6c4bc",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 98849,
    "task_id": "task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1"
  },
  "created_at": "2026-09-29T22:11:48.507663+00:00"
}
```

</details>

<a id="row-event-a6e3b09b730a48bfa3407b8915bc1afb"></a>

<details>
<summary>event-a6e3b09b730a48bfa3407b8915bc1afb · 전체 저장값</summary>

```json
{
  "event_id": "event-a6e3b09b730a48bfa3407b8915bc1afb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2259,
    "task_id": "task-128ac5fa11cc7b7100bdb4fca0ccbbb5b9ae058acbef057a0e63307fedd1"
  },
  "created_at": "2026-09-29T22:11:50.465350+00:00"
}
```

</details>

<a id="row-event-b8b8f7967cd24d34adae94aa0810dc24"></a>

<details>
<summary>event-b8b8f7967cd24d34adae94aa0810dc24 · 전체 저장값</summary>

```json
{
  "event_id": "event-b8b8f7967cd24d34adae94aa0810dc24",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100973,
    "task_id": "task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3"
  },
  "created_at": "2026-09-29T22:11:55.449772+00:00"
}
```

</details>

<a id="row-event-88e2c4dc6e574938a8372a42fb181557"></a>

<details>
<summary>event-88e2c4dc6e574938a8372a42fb181557 · 전체 저장값</summary>

```json
{
  "event_id": "event-88e2c4dc6e574938a8372a42fb181557",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 8450,
    "task_id": "task-552ec5c50d4bff94587a877c396ea63ff49794854937527413923215b043"
  },
  "created_at": "2026-09-29T22:11:55.565092+00:00"
}
```

</details>

<a id="row-event-2944ec2b087847f68c96c93282ef719a"></a>

<details>
<summary>event-2944ec2b087847f68c96c93282ef719a · 전체 저장값</summary>

```json
{
  "event_id": "event-2944ec2b087847f68c96c93282ef719a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 110394,
    "task_id": "task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808"
  },
  "created_at": "2026-09-29T22:12:00.659595+00:00"
}
```

</details>

<a id="row-event-9f29311b72aa4c6fa698cb68462b4b90"></a>

<details>
<summary>event-9f29311b72aa4c6fa698cb68462b4b90 · 전체 저장값</summary>

```json
{
  "event_id": "event-9f29311b72aa4c6fa698cb68462b4b90",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6104,
    "task_id": "task-0589e934d2a63a3c2d53936630cbbfbb33447f4ec9e7f63dcae4cb234ae3"
  },
  "created_at": "2026-09-29T22:12:09.995050+00:00"
}
```

</details>

<a id="row-event-1e6cd610b27848a08be4490359217533"></a>

<details>
<summary>event-1e6cd610b27848a08be4490359217533 · 전체 저장값</summary>

```json
{
  "event_id": "event-1e6cd610b27848a08be4490359217533",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 98843,
    "task_id": "task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08"
  },
  "created_at": "2026-09-29T22:12:13.379096+00:00"
}
```

</details>

<a id="row-event-4031a56a4b99426596f09118fb13c2f7"></a>

<details>
<summary>event-4031a56a4b99426596f09118fb13c2f7 · 전체 저장값</summary>

```json
{
  "event_id": "event-4031a56a4b99426596f09118fb13c2f7",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2282,
    "task_id": "task-472957fa9690997a5bacd07bcab4c5475b6a601c07389eb4bb4bbc1edc08"
  },
  "created_at": "2026-09-29T22:12:15.555856+00:00"
}
```

</details>

<a id="row-event-fd56b197d1c74e7981bc6e78c4f84188"></a>

<details>
<summary>event-fd56b197d1c74e7981bc6e78c4f84188 · 전체 저장값</summary>

```json
{
  "event_id": "event-fd56b197d1c74e7981bc6e78c4f84188",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100944,
    "task_id": "task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b"
  },
  "created_at": "2026-09-29T22:12:19.167676+00:00"
}
```

</details>

<a id="row-event-a364013b26c3493683f3e645ac0b7374"></a>

<details>
<summary>event-a364013b26c3493683f3e645ac0b7374 · 전체 저장값</summary>

```json
{
  "event_id": "event-a364013b26c3493683f3e645ac0b7374",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9143,
    "task_id": "task-dd7f3f5d9b630f1b0d80f6b7c328ec1c08e8782fb65c5d4fb10bf052e808"
  },
  "created_at": "2026-09-29T22:12:19.252258+00:00"
}
```

</details>

<a id="row-event-558517318c4e46b8a37ecab95ef0c307"></a>

<details>
<summary>event-558517318c4e46b8a37ecab95ef0c307 · 전체 저장값</summary>

```json
{
  "event_id": "event-558517318c4e46b8a37ecab95ef0c307",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 100029,
    "task_id": "task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f"
  },
  "created_at": "2026-09-29T22:12:22.411596+00:00"
}
```

</details>

<a id="row-event-d164a735de314d86a13ed6e34329cbe5"></a>

<details>
<summary>event-d164a735de314d86a13ed6e34329cbe5 · 전체 저장값</summary>

```json
{
  "event_id": "event-d164a735de314d86a13ed6e34329cbe5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6026,
    "task_id": "task-5b8e3940bc5949ad5095673406f4fa43ec16e402d9f662b1d1383b70c14b"
  },
  "created_at": "2026-09-29T22:12:34.576473+00:00"
}
```

</details>

<a id="row-event-12995c59777f4ded80a7b7e22d86b92b"></a>

<details>
<summary>event-12995c59777f4ded80a7b7e22d86b92b · 전체 저장값</summary>

```json
{
  "event_id": "event-12995c59777f4ded80a7b7e22d86b92b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 8759,
    "task_id": "task-6642720b84a12d6276d735777dd12f7f18f1260942af96a92ba54832292f"
  },
  "created_at": "2026-09-29T22:12:46.038352+00:00"
}
```

</details>

<a id="row-event-a4041346592f460f84b2a9db835339f0"></a>

<details>
<summary>event-a4041346592f460f84b2a9db835339f0 · 전체 저장값</summary>

```json
{
  "event_id": "event-a4041346592f460f84b2a9db835339f0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 134891,
    "task_id": "task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5"
  },
  "created_at": "2026-09-29T22:12:50.352626+00:00"
}
```

</details>

<a id="row-event-4b7e68c901004f56824d0bd766e38158"></a>

<details>
<summary>event-4b7e68c901004f56824d0bd766e38158 · 전체 저장값</summary>

```json
{
  "event_id": "event-4b7e68c901004f56824d0bd766e38158",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 23206,
    "task_id": "task-76f575dbd21e58f2cf411666433e8d2160bef717c3ffde03c1c58a2d8da5"
  },
  "created_at": "2026-09-29T22:13:42.726597+00:00"
}
```

</details>

<a id="row-event-9b5cae89dc4549acb947945e1c5fc6c4"></a>

<details>
<summary>event-9b5cae89dc4549acb947945e1c5fc6c4 · 전체 저장값</summary>

```json
{
  "event_id": "event-9b5cae89dc4549acb947945e1c5fc6c4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 91429,
    "task_id": "task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97"
  },
  "created_at": "2026-09-29T22:13:46.147612+00:00"
}
```

</details>

<a id="row-event-955c600a2d96454b8aceced93206b230"></a>

<details>
<summary>event-955c600a2d96454b8aceced93206b230 · 전체 저장값</summary>

```json
{
  "event_id": "event-955c600a2d96454b8aceced93206b230",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10834,
    "task_id": "task-5a4542ddfa3c99f434e4fc4e4cbe12fb37a628210249e7eda4987499eb97"
  },
  "created_at": "2026-09-29T22:13:51.664809+00:00"
}
```

</details>

<a id="row-event-422f7374075c448eaf802c6717447963"></a>

<details>
<summary>event-422f7374075c448eaf802c6717447963 · 전체 저장값</summary>

```json
{
  "event_id": "event-422f7374075c448eaf802c6717447963",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 101429,
    "task_id": "task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f"
  },
  "created_at": "2026-09-29T22:13:55.301493+00:00"
}
```

</details>

<a id="row-event-9b5b4b43965c4d0ca65da1dfa96d82db"></a>

<details>
<summary>event-9b5b4b43965c4d0ca65da1dfa96d82db · 전체 저장값</summary>

```json
{
  "event_id": "event-9b5b4b43965c4d0ca65da1dfa96d82db",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 18422,
    "task_id": "task-d41b968ad2122b99d7e4ec29a85a2be72875a5f8a6fb78de92343963a97f"
  },
  "created_at": "2026-09-29T22:14:39.391672+00:00"
}
```

</details>

<a id="row-event-4da5eb543307464fb7999dd2c6e7891a"></a>

<details>
<summary>event-4da5eb543307464fb7999dd2c6e7891a · 전체 저장값</summary>

```json
{
  "event_id": "event-4da5eb543307464fb7999dd2c6e7891a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-b6587f90d386926a60eca98c50d78286336e25d4de8e932d431c90cf8ca9"
  },
  "created_at": "2026-09-29T22:14:48.752796+00:00"
}
```

</details>

<a id="row-event-3346344519c9499b988722506862caba"></a>

<details>
<summary>event-3346344519c9499b988722506862caba · 전체 저장값</summary>

```json
{
  "event_id": "event-3346344519c9499b988722506862caba",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 114477,
    "task_id": "task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a"
  },
  "created_at": "2026-09-29T22:14:56.671623+00:00"
}
```

</details>

<a id="row-event-0fedc8c2df4a486199fa7878da7f4bb4"></a>

<details>
<summary>event-0fedc8c2df4a486199fa7878da7f4bb4 · 전체 저장값</summary>

```json
{
  "event_id": "event-0fedc8c2df4a486199fa7878da7f4bb4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 101685,
    "task_id": "task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7"
  },
  "created_at": "2026-09-29T22:14:58.236430+00:00"
}
```

</details>

<a id="row-event-99be9e8a26bc46f1bf1aea30e12c3cbb"></a>

<details>
<summary>event-99be9e8a26bc46f1bf1aea30e12c3cbb · 전체 저장값</summary>

```json
{
  "event_id": "event-99be9e8a26bc46f1bf1aea30e12c3cbb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 109677,
    "task_id": "task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4"
  },
  "created_at": "2026-09-29T22:14:59.791664+00:00"
}
```

</details>

<a id="row-event-daea572d8f6549da8d6281cd52e39e7a"></a>

<details>
<summary>event-daea572d8f6549da8d6281cd52e39e7a · 전체 저장값</summary>

```json
{
  "event_id": "event-daea572d8f6549da8d6281cd52e39e7a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 7113,
    "task_id": "task-cc7a74def5932b00e6a32472841762a86d290400682cd4c8bdb4f4ce815a"
  },
  "created_at": "2026-09-29T22:15:08.068567+00:00"
}
```

</details>

<a id="row-event-da62e611fffc4dc59fcc571e1ac6953b"></a>

<details>
<summary>event-da62e611fffc4dc59fcc571e1ac6953b · 전체 저장값</summary>

```json
{
  "event_id": "event-da62e611fffc4dc59fcc571e1ac6953b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6908,
    "task_id": "task-ce6c19a0a5af121ff0c764a69a871ccea75552e85a42be719fe3ccc68ad7"
  },
  "created_at": "2026-09-29T22:15:13.428296+00:00"
}
```

</details>

<a id="row-event-743984a14b834df396bf220a22adf3b4"></a>

<details>
<summary>event-743984a14b834df396bf220a22adf3b4 · 전체 저장값</summary>

```json
{
  "event_id": "event-743984a14b834df396bf220a22adf3b4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9089,
    "task_id": "task-a9795068db3766c716a3f7895fc1598426912edf3c0c8a968d419c8801b4"
  },
  "created_at": "2026-09-29T22:15:16.434694+00:00"
}
```

</details>

<a id="row-event-0a388b5edce64997b8a0fbd0f8f91dbe"></a>

<details>
<summary>event-0a388b5edce64997b8a0fbd0f8f91dbe · 전체 저장값</summary>

```json
{
  "event_id": "event-0a388b5edce64997b8a0fbd0f8f91dbe",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 109731,
    "task_id": "task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a"
  },
  "created_at": "2026-09-29T22:15:19.886954+00:00"
}
```

</details>

<a id="row-event-f48b469d1cd14a42986bc4d4d795def4"></a>

<details>
<summary>event-f48b469d1cd14a42986bc4d4d795def4 · 전체 저장값</summary>

```json
{
  "event_id": "event-f48b469d1cd14a42986bc4d4d795def4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9985,
    "task_id": "task-88d966e551c05c00a46cdc3315ee9a731a95ea40440ebc436e675c36bc5a"
  },
  "created_at": "2026-09-29T22:15:41.138701+00:00"
}
```

</details>

<a id="row-event-7eff2d349e1d4a82bf227cd3a1ce7c63"></a>

<details>
<summary>event-7eff2d349e1d4a82bf227cd3a1ce7c63 · 전체 저장값</summary>

```json
{
  "event_id": "event-7eff2d349e1d4a82bf227cd3a1ce7c63",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-f9ed2c539fd33fbe90fe97d65e3aa3f5719ac436c3070e617ab7898cf85f"
  },
  "created_at": "2026-09-29T22:15:47.120363+00:00"
}
```

</details>

<a id="row-event-699485d92a3245e693e5a6573fb5022f"></a>

<details>
<summary>event-699485d92a3245e693e5a6573fb5022f · 전체 저장값</summary>

```json
{
  "event_id": "event-699485d92a3245e693e5a6573fb5022f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 110205,
    "task_id": "task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf"
  },
  "created_at": "2026-09-29T22:15:53.999324+00:00"
}
```

</details>

<a id="row-event-ea90e8d1e51e4d199b73e2c01c04f0f5"></a>

<details>
<summary>event-ea90e8d1e51e4d199b73e2c01c04f0f5 · 전체 저장값</summary>

```json
{
  "event_id": "event-ea90e8d1e51e4d199b73e2c01c04f0f5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 123333,
    "task_id": "task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b"
  },
  "created_at": "2026-09-29T22:15:55.489351+00:00"
}
```

</details>

<a id="row-event-170ebb07783e411589126acf37c6bbd3"></a>

<details>
<summary>event-170ebb07783e411589126acf37c6bbd3 · 전체 저장값</summary>

```json
{
  "event_id": "event-170ebb07783e411589126acf37c6bbd3",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6812,
    "task_id": "task-253658de40cc089f0897bab8e8fbe5dfbdaaa2baea96bc0e59c6dbe12ecf"
  },
  "created_at": "2026-09-29T22:16:07.171433+00:00"
}
```

</details>

<a id="row-event-ef9b3688d79d45a38ef72d4e75cd65c1"></a>

<details>
<summary>event-ef9b3688d79d45a38ef72d4e75cd65c1 · 전체 저장값</summary>

```json
{
  "event_id": "event-ef9b3688d79d45a38ef72d4e75cd65c1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9272,
    "task_id": "task-3efae683570aefce12e9028eee5273c3b16f676780e8fbc6adb6ce80b73b"
  },
  "created_at": "2026-09-29T22:16:09.484823+00:00"
}
```

</details>

<a id="row-event-b5d831bea559474fa40c3c4502feab10"></a>

<details>
<summary>event-b5d831bea559474fa40c3c4502feab10 · 전체 저장값</summary>

```json
{
  "event_id": "event-b5d831bea559474fa40c3c4502feab10",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 388822,
    "task_id": "task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813"
  },
  "created_at": "2026-09-29T22:16:18.254921+00:00"
}
```

</details>

<a id="row-event-cfa1f162458b490bb2154cbe3689d934"></a>

<details>
<summary>event-cfa1f162458b490bb2154cbe3689d934 · 전체 저장값</summary>

```json
{
  "event_id": "event-cfa1f162458b490bb2154cbe3689d934",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 56918,
    "task_id": "task-57c014744c45243421ba2326ede3594bbaa304b6baa20659bd1eca1b5813"
  },
  "created_at": "2026-09-29T22:16:55.703359+00:00"
}
```

</details>

<a id="row-event-ca6a2ff253204ea18f8a3c51ca60d467"></a>

<details>
<summary>event-ca6a2ff253204ea18f8a3c51ca60d467 · 전체 저장값</summary>

```json
{
  "event_id": "event-ca6a2ff253204ea18f8a3c51ca60d467",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 406255,
    "task_id": "task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2"
  },
  "created_at": "2026-09-29T22:17:00.179691+00:00"
}
```

</details>

<a id="row-event-e0f827808c9a4c4abc3fe8c4e043ce67"></a>

<details>
<summary>event-e0f827808c9a4c4abc3fe8c4e043ce67 · 전체 저장값</summary>

```json
{
  "event_id": "event-e0f827808c9a4c4abc3fe8c4e043ce67",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 60189,
    "task_id": "task-3eb8754bc521e328a8c6913d0a1c38595a7c6044821a1c7c37f50aad61b2"
  },
  "created_at": "2026-09-29T22:17:28.650526+00:00"
}
```

</details>

<a id="row-event-042fafe97b614df0a0e911cf230b17a0"></a>

<details>
<summary>event-042fafe97b614df0a0e911cf230b17a0 · 전체 저장값</summary>

```json
{
  "event_id": "event-042fafe97b614df0a0e911cf230b17a0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "concepts",
      "evidence",
      "report",
      "selection",
      "coherence",
      "feedback",
      "report_context"
    ],
    "snapshot_id": "snap-74a823dc8b0c470bac6070c552f5277b",
    "versions": [
      "av-5787558b3bd746ab91a488cd619d84fe"
    ]
  },
  "created_at": "2026-09-29T22:17:34.973255+00:00"
}
```

</details>

<a id="row-event-599e4440c18149a8989b80704eb60050"></a>

<details>
<summary>event-599e4440c18149a8989b80704eb60050 · 전체 저장값</summary>

```json
{
  "event_id": "event-599e4440c18149a8989b80704eb60050",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-2fc4b03d18d357f283c71ae677d28380cd9395a54d6810e49e5d38891fde"
  },
  "created_at": "2026-09-29T22:18:09.056575+00:00"
}
```

</details>

<a id="row-event-4b65924ac1e849b8bd6a71c469dacba6"></a>

<details>
<summary>event-4b65924ac1e849b8bd6a71c469dacba6 · 전체 저장값</summary>

```json
{
  "event_id": "event-4b65924ac1e849b8bd6a71c469dacba6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-79aadae8281243288bb60a7919a19408",
    "versions": [
      "av-8a5a069aae7740e9951e27625b697aae"
    ]
  },
  "created_at": "2026-09-29T22:18:11.105081+00:00"
}
```

</details>

<a id="row-event-2542a5593cb94eb3aa619320fc3cdd59"></a>

<details>
<summary>event-2542a5593cb94eb3aa619320fc3cdd59 · 전체 저장값</summary>

```json
{
  "event_id": "event-2542a5593cb94eb3aa619320fc3cdd59",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 142478,
    "task_id": "task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9"
  },
  "created_at": "2026-09-29T22:19:02.886949+00:00"
}
```

</details>

<a id="row-event-bf6913f631f94d2da721df62dd0668b6"></a>

<details>
<summary>event-bf6913f631f94d2da721df62dd0668b6 · 전체 저장값</summary>

```json
{
  "event_id": "event-bf6913f631f94d2da721df62dd0668b6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 193272,
    "task_id": "task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5"
  },
  "created_at": "2026-09-29T22:19:04.531962+00:00"
}
```

</details>

<a id="row-event-e30f798011214e8085f7278546136d3f"></a>

<details>
<summary>event-e30f798011214e8085f7278546136d3f · 전체 저장값</summary>

```json
{
  "event_id": "event-e30f798011214e8085f7278546136d3f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 136714,
    "task_id": "task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287"
  },
  "created_at": "2026-09-29T22:19:09.278201+00:00"
}
```

</details>

<a id="row-event-836a58dac23c4f2aa763ea24dbb9d98d"></a>

<details>
<summary>event-836a58dac23c4f2aa763ea24dbb9d98d · 전체 저장값</summary>

```json
{
  "event_id": "event-836a58dac23c4f2aa763ea24dbb9d98d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 22386,
    "task_id": "task-6d08ad3e1053353d3b5068e0dcf408f4868ec7d885d036aeec9afc0529f5"
  },
  "created_at": "2026-09-29T22:19:24.990270+00:00"
}
```

</details>

<a id="row-event-09f940ea3652416f8ca8e85781389b0a"></a>

<details>
<summary>event-09f940ea3652416f8ca8e85781389b0a · 전체 저장값</summary>

```json
{
  "event_id": "event-09f940ea3652416f8ca8e85781389b0a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 15683,
    "task_id": "task-f8311a43cb6ee1e82c20d50ea74c242f555fd83798ece9ce9392b3220287"
  },
  "created_at": "2026-09-29T22:19:33.069964+00:00"
}
```

</details>

<a id="row-event-28fe38b24a9942dcb38b0412b649189f"></a>

<details>
<summary>event-28fe38b24a9942dcb38b0412b649189f · 전체 저장값</summary>

```json
{
  "event_id": "event-28fe38b24a9942dcb38b0412b649189f",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 20201,
    "task_id": "task-d41aa15a4e66825e47cfe54390cc964d26789c3b4d208de94f374b0d30a9"
  },
  "created_at": "2026-09-29T22:19:35.980760+00:00"
}
```

</details>

<a id="row-event-0afe5b54ea5f4a029696920b6135d180"></a>

<details>
<summary>event-0afe5b54ea5f4a029696920b6135d180 · 전체 저장값</summary>

```json
{
  "event_id": "event-0afe5b54ea5f4a029696920b6135d180",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 60549,
    "task_id": "task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80"
  },
  "created_at": "2026-09-29T22:19:53.026455+00:00"
}
```

</details>

<a id="row-event-198afeb848824b0099fbb19d1a1d02d0"></a>

<details>
<summary>event-198afeb848824b0099fbb19d1a1d02d0 · 전체 저장값</summary>

```json
{
  "event_id": "event-198afeb848824b0099fbb19d1a1d02d0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 7365,
    "task_id": "task-8a2532d98950f9638484d73cef2bf5dab9c05c53f2163731634b6e2dee80"
  },
  "created_at": "2026-09-29T22:20:02.344048+00:00"
}
```

</details>

<a id="row-event-15129f51a77747cf95ed4003de93e3b1"></a>

<details>
<summary>event-15129f51a77747cf95ed4003de93e3b1 · 전체 저장값</summary>

```json
{
  "event_id": "event-15129f51a77747cf95ed4003de93e3b1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 61113,
    "task_id": "task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269"
  },
  "created_at": "2026-09-29T22:20:11.884397+00:00"
}
```

</details>

<a id="row-event-0f98422a728f44629d798a246600db75"></a>

<details>
<summary>event-0f98422a728f44629d798a246600db75 · 전체 저장값</summary>

```json
{
  "event_id": "event-0f98422a728f44629d798a246600db75",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 7610,
    "task_id": "task-3c950090e87d8cb0d7de0005aff3b511c5aacdcdc963e8f5c45ab5be5269"
  },
  "created_at": "2026-09-29T22:20:21.361897+00:00"
}
```

</details>

<a id="row-event-51f3e9fc07b3426ea2347088ce71159e"></a>

<details>
<summary>event-51f3e9fc07b3426ea2347088ce71159e · 전체 저장값</summary>

```json
{
  "event_id": "event-51f3e9fc07b3426ea2347088ce71159e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 57094,
    "task_id": "task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9"
  },
  "created_at": "2026-09-29T22:20:32.002454+00:00"
}
```

</details>

<a id="row-event-1a6e72b5b6c54e20b4a62211c197bb7d"></a>

<details>
<summary>event-1a6e72b5b6c54e20b4a62211c197bb7d · 전체 저장값</summary>

```json
{
  "event_id": "event-1a6e72b5b6c54e20b4a62211c197bb7d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5809,
    "task_id": "task-ecf38ecb9336d759930fe036aa3b4e5b2f377f2228b43b72b133e527d9b9"
  },
  "created_at": "2026-09-29T22:20:37.372646+00:00"
}
```

</details>

<a id="row-event-659ff07d24ee4f4a82ec491fa04ce703"></a>

<details>
<summary>event-659ff07d24ee4f4a82ec491fa04ce703 · 전체 저장값</summary>

```json
{
  "event_id": "event-659ff07d24ee4f4a82ec491fa04ce703",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 117767,
    "task_id": "task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc"
  },
  "created_at": "2026-09-29T22:20:47.578196+00:00"
}
```

</details>

<a id="row-event-94b4a9146c814285a86bb75b533b75a4"></a>

<details>
<summary>event-94b4a9146c814285a86bb75b533b75a4 · 전체 저장값</summary>

```json
{
  "event_id": "event-94b4a9146c814285a86bb75b533b75a4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 15462,
    "task_id": "task-63370b1f5ef969c90c03309a474b0204a0ac30179f37a0257a79ebe2a7fc"
  },
  "created_at": "2026-09-29T22:20:55.898698+00:00"
}
```

</details>

<a id="row-event-6933b4fb67224cb3a42e185b0e59ed9e"></a>

<details>
<summary>event-6933b4fb67224cb3a42e185b0e59ed9e · 전체 저장값</summary>

```json
{
  "event_id": "event-6933b4fb67224cb3a42e185b0e59ed9e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 50567,
    "task_id": "task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809"
  },
  "created_at": "2026-09-29T22:21:06.885069+00:00"
}
```

</details>

<a id="row-event-448ee272b002463e984541b242a387f4"></a>

<details>
<summary>event-448ee272b002463e984541b242a387f4 · 전체 저장값</summary>

```json
{
  "event_id": "event-448ee272b002463e984541b242a387f4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 4978,
    "task_id": "task-2f364a5baa91439f0ec5bbd04b3492d01f8ad98ed27684eab863575ac809"
  },
  "created_at": "2026-09-29T22:21:13.391532+00:00"
}
```

</details>

<a id="row-event-c62c240741bd4aa8a2014657bc62aef5"></a>

<details>
<summary>event-c62c240741bd4aa8a2014657bc62aef5 · 전체 저장값</summary>

```json
{
  "event_id": "event-c62c240741bd4aa8a2014657bc62aef5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "constraints",
      "report",
      "evidence",
      "selection",
      "coherence",
      "feedback",
      "report_context"
    ],
    "snapshot_id": "snap-5cf9be1da04042098bf9bd21706c7945",
    "versions": [
      "av-e7bdb345d9504a35bcb0ff4d88198e5d",
      "av-2b1d1289efda45a58b8e762312c0ff90"
    ]
  },
  "created_at": "2026-09-29T22:21:36.501795+00:00"
}
```

</details>

<a id="row-event-6581d07c7a444e2eab96fa0ca4e60722"></a>

<details>
<summary>event-6581d07c7a444e2eab96fa0ca4e60722 · 전체 저장값</summary>

```json
{
  "event_id": "event-6581d07c7a444e2eab96fa0ca4e60722",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-0d68d3b0ad22db4b89171e8538f90d1fb53773677be806a20b7457e1182e"
  },
  "created_at": "2026-09-29T22:22:17.038171+00:00"
}
```

</details>

<a id="row-event-56d8e294f6274bd782545212d0921b45"></a>

<details>
<summary>event-56d8e294f6274bd782545212d0921b45 · 전체 저장값</summary>

```json
{
  "event_id": "event-56d8e294f6274bd782545212d0921b45",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120643,
    "task_id": "task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0"
  },
  "created_at": "2026-09-29T22:22:21.667298+00:00"
}
```

</details>

<a id="row-event-9cb7615c456d44f28601176bd5349697"></a>

<details>
<summary>event-9cb7615c456d44f28601176bd5349697 · 전체 저장값</summary>

```json
{
  "event_id": "event-9cb7615c456d44f28601176bd5349697",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10012,
    "task_id": "task-70a11732d91b3bc0e0b9c3e0bac6b835379d6e2408daaa583902c4a028d0"
  },
  "created_at": "2026-09-29T22:22:37.599167+00:00"
}
```

</details>

<a id="row-event-a92b88fe90644dda88f045aa24c7000d"></a>

<details>
<summary>event-a92b88fe90644dda88f045aa24c7000d · 전체 저장값</summary>

```json
{
  "event_id": "event-a92b88fe90644dda88f045aa24c7000d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 56011,
    "task_id": "task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4"
  },
  "created_at": "2026-09-29T22:22:41.500630+00:00"
}
```

</details>

<a id="row-event-b7fa110a0980482e90369bc4330530d4"></a>

<details>
<summary>event-b7fa110a0980482e90369bc4330530d4 · 전체 저장값</summary>

```json
{
  "event_id": "event-b7fa110a0980482e90369bc4330530d4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5958,
    "task_id": "task-a2cf5bbb1371956b017fbc718774d4ef68991c4a5d6260a10a2baa217ed4"
  },
  "created_at": "2026-09-29T22:22:49.609520+00:00"
}
```

</details>

<a id="row-event-16f96a4db4124deb856e7a9eb759bf70"></a>

<details>
<summary>event-16f96a4db4124deb856e7a9eb759bf70 · 전체 저장값</summary>

```json
{
  "event_id": "event-16f96a4db4124deb856e7a9eb759bf70",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-459c07076938c350733c27d3e8578e6475e00d4282b9ea9e5ae66614b287"
  },
  "created_at": "2026-09-29T22:23:02.585869+00:00"
}
```

</details>

<a id="row-event-8a16975c25784a0d968b868454e1eb29"></a>

<details>
<summary>event-8a16975c25784a0d968b868454e1eb29 · 전체 저장값</summary>

```json
{
  "event_id": "event-8a16975c25784a0d968b868454e1eb29",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120643,
    "task_id": "task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029"
  },
  "created_at": "2026-09-29T22:23:05.297880+00:00"
}
```

</details>

<a id="row-event-a15f0c26ba35401c8c6924d9606fce88"></a>

<details>
<summary>event-a15f0c26ba35401c8c6924d9606fce88 · 전체 저장값</summary>

```json
{
  "event_id": "event-a15f0c26ba35401c8c6924d9606fce88",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10507,
    "task_id": "task-3b8023ac8a4d20f7b40bcbfd8e3064c81c2293bb7a7f5b9bd7c70218d029"
  },
  "created_at": "2026-09-29T22:23:21.897163+00:00"
}
```

</details>

<a id="row-event-e7ed177e88f64b6b97b2ab12d54e76c3"></a>

<details>
<summary>event-e7ed177e88f64b6b97b2ab12d54e76c3 · 전체 저장값</summary>

```json
{
  "event_id": "event-e7ed177e88f64b6b97b2ab12d54e76c3",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 55551,
    "task_id": "task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b"
  },
  "created_at": "2026-09-29T22:23:26.231452+00:00"
}
```

</details>

<a id="row-event-0ef1cff83b814459b988203404c05f76"></a>

<details>
<summary>event-0ef1cff83b814459b988203404c05f76 · 전체 저장값</summary>

```json
{
  "event_id": "event-0ef1cff83b814459b988203404c05f76",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5863,
    "task_id": "task-e63502bd28fa109c20599a250cd881261ab4a51e03a24cba183be33dab4b"
  },
  "created_at": "2026-09-29T22:23:34.542756+00:00"
}
```

</details>

<a id="row-event-77f8301c3d0f43609c2f023494d5d590"></a>

<details>
<summary>event-77f8301c3d0f43609c2f023494d5d590 · 전체 저장값</summary>

```json
{
  "event_id": "event-77f8301c3d0f43609c2f023494d5d590",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-858f9f941e098496173ac4c15c45c9c753e689eeb18e3af343e3d7e5e943"
  },
  "created_at": "2026-09-29T22:23:48.387281+00:00"
}
```

</details>

<a id="row-event-e408c636650945e7a4ba324b2268fe59"></a>

<details>
<summary>event-e408c636650945e7a4ba324b2268fe59 · 전체 저장값</summary>

```json
{
  "event_id": "event-e408c636650945e7a4ba324b2268fe59",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120461,
    "task_id": "task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f"
  },
  "created_at": "2026-09-29T22:23:50.965310+00:00"
}
```

</details>

<a id="row-event-e7eecdef19004f4bb9147d7f05ecdc6e"></a>

<details>
<summary>event-e7eecdef19004f4bb9147d7f05ecdc6e · 전체 저장값</summary>

```json
{
  "event_id": "event-e7eecdef19004f4bb9147d7f05ecdc6e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 11715,
    "task_id": "task-ee76d0372c5d74a3e5af6b14a4e338129ec4a8139d3c1c3118059f7ec04f"
  },
  "created_at": "2026-09-29T22:24:14.043241+00:00"
}
```

</details>

<a id="row-event-148f76e783814d0a85cfe860e1711f66"></a>

<details>
<summary>event-148f76e783814d0a85cfe860e1711f66 · 전체 저장값</summary>

```json
{
  "event_id": "event-148f76e783814d0a85cfe860e1711f66",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 57102,
    "task_id": "task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728"
  },
  "created_at": "2026-09-29T22:24:17.663074+00:00"
}
```

</details>

<a id="row-event-c2159b1affa84a528b5916e5af70b17c"></a>

<details>
<summary>event-c2159b1affa84a528b5916e5af70b17c · 전체 저장값</summary>

```json
{
  "event_id": "event-c2159b1affa84a528b5916e5af70b17c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5893,
    "task_id": "task-4fc989e1ce4ad8d0e6e0276cf99d6b54eab65b46a1137ab066fe30d70728"
  },
  "created_at": "2026-09-29T22:24:23.828686+00:00"
}
```

</details>

<a id="row-event-167ea3032a6c46d8bb2c8f9d41e0b8a1"></a>

<details>
<summary>event-167ea3032a6c46d8bb2c8f9d41e0b8a1 · 전체 저장값</summary>

```json
{
  "event_id": "event-167ea3032a6c46d8bb2c8f9d41e0b8a1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-c9019a502ec0f4e71a9a2722c7588724ce244982a827662d142a39063586"
  },
  "created_at": "2026-09-29T22:24:38.255927+00:00"
}
```

</details>

<a id="row-event-8d43948a3f5c4f48b5fe13269610f1dc"></a>

<details>
<summary>event-8d43948a3f5c4f48b5fe13269610f1dc · 전체 저장값</summary>

```json
{
  "event_id": "event-8d43948a3f5c4f48b5fe13269610f1dc",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120461,
    "task_id": "task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24"
  },
  "created_at": "2026-09-29T22:24:42.709297+00:00"
}
```

</details>

<a id="row-event-0b6826c4878a4ca4a9b03adf99ac88f9"></a>

<details>
<summary>event-0b6826c4878a4ca4a9b03adf99ac88f9 · 전체 저장값</summary>

```json
{
  "event_id": "event-0b6826c4878a4ca4a9b03adf99ac88f9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 11122,
    "task_id": "task-b4aa671f8e608ee1def07050f9fc0bcb37e8565cf1bd7d2887ede01c9c24"
  },
  "created_at": "2026-09-29T22:25:02.234557+00:00"
}
```

</details>

<a id="row-event-5f7ababdfce443f580f69d5199299364"></a>

<details>
<summary>event-5f7ababdfce443f580f69d5199299364 · 전체 저장값</summary>

```json
{
  "event_id": "event-5f7ababdfce443f580f69d5199299364",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 56229,
    "task_id": "task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce"
  },
  "created_at": "2026-09-29T22:25:08.129875+00:00"
}
```

</details>

<a id="row-event-fe975dff0eec474894a0ef3dc43e76e8"></a>

<details>
<summary>event-fe975dff0eec474894a0ef3dc43e76e8 · 전체 저장값</summary>

```json
{
  "event_id": "event-fe975dff0eec474894a0ef3dc43e76e8",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6064,
    "task_id": "task-c7e54d3c09f7bb8e9e24c1a73fdc4d4b6d6404992fb450593d9bbb3038ce"
  },
  "created_at": "2026-09-29T22:25:14.763781+00:00"
}
```

</details>

<a id="row-event-d79b680b525c4d188b6bbdd26989f666"></a>

<details>
<summary>event-d79b680b525c4d188b6bbdd26989f666 · 전체 저장값</summary>

```json
{
  "event_id": "event-d79b680b525c4d188b6bbdd26989f666",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-449e8133744e4505b9e5affe26a8b9d4",
    "versions": [
      "av-84af471e3f39499f9f418f1b542f1024",
      "av-32ca21fd8ff84d06ba5aaf5f449f8e4a"
    ]
  },
  "created_at": "2026-09-29T22:25:27.743625+00:00"
}
```

</details>

<a id="row-event-4bc812632c744be3a48e592a997ad0a2"></a>

<details>
<summary>event-4bc812632c744be3a48e592a997ad0a2 · 전체 저장값</summary>

```json
{
  "event_id": "event-4bc812632c744be3a48e592a997ad0a2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95934,
    "task_id": "task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1"
  },
  "created_at": "2026-09-29T22:25:51.988234+00:00"
}
```

</details>

<a id="row-event-af31e64087814d18b174e2c1544a26b5"></a>

<details>
<summary>event-af31e64087814d18b174e2c1544a26b5 · 전체 저장값</summary>

```json
{
  "event_id": "event-af31e64087814d18b174e2c1544a26b5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95983,
    "task_id": "task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b"
  },
  "created_at": "2026-09-29T22:25:53.672154+00:00"
}
```

</details>

<a id="row-event-071e6c27282b4af180acaf09fa46918a"></a>

<details>
<summary>event-071e6c27282b4af180acaf09fa46918a · 전체 저장값</summary>

```json
{
  "event_id": "event-071e6c27282b4af180acaf09fa46918a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 96177,
    "task_id": "task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8"
  },
  "created_at": "2026-09-29T22:25:55.397349+00:00"
}
```

</details>

<a id="row-event-74efb61f57b84fad9f687224e21a11d2"></a>

<details>
<summary>event-74efb61f57b84fad9f687224e21a11d2 · 전체 저장값</summary>

```json
{
  "event_id": "event-74efb61f57b84fad9f687224e21a11d2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95966,
    "task_id": "task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848"
  },
  "created_at": "2026-09-29T22:25:59.015651+00:00"
}
```

</details>

<a id="row-event-c391f880c5ff4aafb5059b9944db9037"></a>

<details>
<summary>event-c391f880c5ff4aafb5059b9944db9037 · 전체 저장값</summary>

```json
{
  "event_id": "event-c391f880c5ff4aafb5059b9944db9037",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2549,
    "task_id": "task-d0c9f4e8a3b02a95e0cd324719d47c53647280e61f5986ec42f713cc83a1"
  },
  "created_at": "2026-09-29T22:25:59.084179+00:00"
}
```

</details>

<a id="row-event-a0f56561506843a38101e062a5e7a45d"></a>

<details>
<summary>event-a0f56561506843a38101e062a5e7a45d · 전체 저장값</summary>

```json
{
  "event_id": "event-a0f56561506843a38101e062a5e7a45d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2536,
    "task_id": "task-3fec767e46665e187b75cba93fed628cd07a7849f5adaf7578f9361f082b"
  },
  "created_at": "2026-09-29T22:25:59.220238+00:00"
}
```

</details>

<a id="row-event-b2118e5f873b4180b51ada02a20fa036"></a>

<details>
<summary>event-b2118e5f873b4180b51ada02a20fa036 · 전체 저장값</summary>

```json
{
  "event_id": "event-b2118e5f873b4180b51ada02a20fa036",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2569,
    "task_id": "task-477d1ca6fe0dd50b967d7cbe9669a6237087bc262dd7eede39905fb874d8"
  },
  "created_at": "2026-09-29T22:25:59.586109+00:00"
}
```

</details>

<a id="row-event-965a2e51a9b341518d78313e3156b5ef"></a>

<details>
<summary>event-965a2e51a9b341518d78313e3156b5ef · 전체 저장값</summary>

```json
{
  "event_id": "event-965a2e51a9b341518d78313e3156b5ef",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95708,
    "task_id": "task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8"
  },
  "created_at": "2026-09-29T22:26:05.846479+00:00"
}
```

</details>

<a id="row-event-5f6d178a49894d82b6102655513d3044"></a>

<details>
<summary>event-5f6d178a49894d82b6102655513d3044 · 전체 저장값</summary>

```json
{
  "event_id": "event-5f6d178a49894d82b6102655513d3044",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95577,
    "task_id": "task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131"
  },
  "created_at": "2026-09-29T22:26:07.418859+00:00"
}
```

</details>

<a id="row-event-309be95ffff4434099e6804115c1ff69"></a>

<details>
<summary>event-309be95ffff4434099e6804115c1ff69 · 전체 저장값</summary>

```json
{
  "event_id": "event-309be95ffff4434099e6804115c1ff69",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95801,
    "task_id": "task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e"
  },
  "created_at": "2026-09-29T22:26:09.030894+00:00"
}
```

</details>

<a id="row-event-223fa9e0c33840e586a309ca678ae940"></a>

<details>
<summary>event-223fa9e0c33840e586a309ca678ae940 · 전체 저장값</summary>

```json
{
  "event_id": "event-223fa9e0c33840e586a309ca678ae940",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2574,
    "task_id": "task-7f4e975641627d17c1ce061d2e999f1c89b29be87d8524096f89503fc848"
  },
  "created_at": "2026-09-29T22:26:09.140863+00:00"
}
```

</details>

<a id="row-event-41e9c19b8f6a45eab1cb38d785f2784c"></a>

<details>
<summary>event-41e9c19b8f6a45eab1cb38d785f2784c · 전체 저장값</summary>

```json
{
  "event_id": "event-41e9c19b8f6a45eab1cb38d785f2784c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2417,
    "task_id": "task-3d9a7d1d22607343d4b5665d344161df4441f37de4e619bac7ef33525ca8"
  },
  "created_at": "2026-09-29T22:26:10.586237+00:00"
}
```

</details>

<a id="row-event-bfcc93a5385a45678edf567f0560a818"></a>

<details>
<summary>event-bfcc93a5385a45678edf567f0560a818 · 전체 저장값</summary>

```json
{
  "event_id": "event-bfcc93a5385a45678edf567f0560a818",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95936,
    "task_id": "task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f"
  },
  "created_at": "2026-09-29T22:26:14.926569+00:00"
}
```

</details>

<a id="row-event-99cc61a3ef6b4b30bda5e792517de769"></a>

<details>
<summary>event-99cc61a3ef6b4b30bda5e792517de769 · 전체 저장값</summary>

```json
{
  "event_id": "event-99cc61a3ef6b4b30bda5e792517de769",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2320,
    "task_id": "task-530f6a73b36be73f59ac91489ba3addc1bee4b10c9ec1dc7a51c4f182131"
  },
  "created_at": "2026-09-29T22:26:14.997250+00:00"
}
```

</details>

<a id="row-event-3fd60dee2bf34670abb69788185f7491"></a>

<details>
<summary>event-3fd60dee2bf34670abb69788185f7491 · 전체 저장값</summary>

```json
{
  "event_id": "event-3fd60dee2bf34670abb69788185f7491",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2539,
    "task_id": "task-f3f92213dab12ac080a2966ae7282644283e5a61b238bf495531cc3a9c7e"
  },
  "created_at": "2026-09-29T22:26:15.140242+00:00"
}
```

</details>

<a id="row-event-46fc56f597804924acd5894c769acdef"></a>

<details>
<summary>event-46fc56f597804924acd5894c769acdef · 전체 저장값</summary>

```json
{
  "event_id": "event-46fc56f597804924acd5894c769acdef",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 96328,
    "task_id": "task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa"
  },
  "created_at": "2026-09-29T22:26:19.753449+00:00"
}
```

</details>

<a id="row-event-43a930a76f144ea38525795e0390aac2"></a>

<details>
<summary>event-43a930a76f144ea38525795e0390aac2 · 전체 저장값</summary>

```json
{
  "event_id": "event-43a930a76f144ea38525795e0390aac2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 95808,
    "task_id": "task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273"
  },
  "created_at": "2026-09-29T22:26:21.311991+00:00"
}
```

</details>

<a id="row-event-c6ba43e8e602413896ff1f1c740d473a"></a>

<details>
<summary>event-c6ba43e8e602413896ff1f1c740d473a · 전체 저장값</summary>

```json
{
  "event_id": "event-c6ba43e8e602413896ff1f1c740d473a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2446,
    "task_id": "task-c10cdda7afba6ebe8ba56a4b3a8f3b2f64e0fab93123588b59925431732f"
  },
  "created_at": "2026-09-29T22:26:21.396190+00:00"
}
```

</details>

<a id="row-event-07a4cfa30f424b049e1027cc652e2bf0"></a>

<details>
<summary>event-07a4cfa30f424b049e1027cc652e2bf0 · 전체 저장값</summary>

```json
{
  "event_id": "event-07a4cfa30f424b049e1027cc652e2bf0",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2623,
    "task_id": "task-3769af4f88fa2a2ebb6f0e0d057421612b6a58b2ff8a433e81db1574e2fa"
  },
  "created_at": "2026-09-29T22:26:24.607866+00:00"
}
```

</details>

<a id="row-event-163b8b1b528f4b6f9e435afad8c85db4"></a>

<details>
<summary>event-163b8b1b528f4b6f9e435afad8c85db4 · 전체 저장값</summary>

```json
{
  "event_id": "event-163b8b1b528f4b6f9e435afad8c85db4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 2506,
    "task_id": "task-9993c2eab5b616d4af7d3d4d9edb66f64dc6b1fea5bbaf5653e9a6d96273"
  },
  "created_at": "2026-09-29T22:26:25.079441+00:00"
}
```

</details>

<a id="row-event-6c72e80ae350489586977b64851e910e"></a>

<details>
<summary>event-6c72e80ae350489586977b64851e910e · 전체 저장값</summary>

```json
{
  "event_id": "event-6c72e80ae350489586977b64851e910e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "report",
      "evidence",
      "selection",
      "coherence",
      "feedback",
      "report_context"
    ],
    "snapshot_id": "snap-0b378bb6c49242848ff2e058532cd65a",
    "versions": [
      "av-0ea83fd7fefc4278afc6325ad95cb099",
      "av-934e670867bc4eb8a37265b886a62657",
      "av-a0984695bff14608a062f8772d5c75ca"
    ]
  },
  "created_at": "2026-09-29T22:26:33.487612+00:00"
}
```

</details>

<a id="row-event-0495e68f3ef1419a94fde16bd9a2ec09"></a>

<details>
<summary>event-0495e68f3ef1419a94fde16bd9a2ec09 · 전체 저장값</summary>

```json
{
  "event_id": "event-0495e68f3ef1419a94fde16bd9a2ec09",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 51,
    "previous": 50,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T22:31:28.318949+00:00"
}
```

</details>

<a id="row-event-2ea76ea9de3842fcade2840b896b1b9e"></a>

<details>
<summary>event-2ea76ea9de3842fcade2840b896b1b9e · 전체 저장값</summary>

```json
{
  "event_id": "event-2ea76ea9de3842fcade2840b896b1b9e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-ac5f5868c8a44072a32c15e8856e4e73",
    "versions": []
  },
  "created_at": "2026-09-29T22:32:07.086727+00:00"
}
```

</details>

<a id="row-event-77290f5ad22b47e09aa4bc3f3c83d327"></a>

<details>
<summary>event-77290f5ad22b47e09aa4bc3f3c83d327 · 전체 저장값</summary>

```json
{
  "event_id": "event-77290f5ad22b47e09aa4bc3f3c83d327",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "report",
      "evidence",
      "selection",
      "coherence",
      "feedback",
      "report_context"
    ],
    "snapshot_id": "snap-fedc4ff3f684478b856a0388b9e5ba4d",
    "versions": [
      "av-b0e3902510de48e9b02e87891af05f3a",
      "av-a8bbcf6fe3eb491fa96001cff31d08b3",
      "av-3d07d4953595484d8b569892c6cb2050"
    ]
  },
  "created_at": "2026-09-29T22:32:27.509069+00:00"
}
```

</details>

<a id="row-event-3d51ae987ebd4817a7b04373d25f3c3c"></a>

<details>
<summary>event-3d51ae987ebd4817a7b04373d25f3c3c · 전체 저장값</summary>

```json
{
  "event_id": "event-3d51ae987ebd4817a7b04373d25f3c3c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-b52c0ee7bbfbf3c1dc45556c9f8f7059551de5fc6cd495c8b9f70abb4307"
  },
  "created_at": "2026-09-29T22:33:03.529123+00:00"
}
```

</details>

<a id="row-event-6cfe0d1846ec42a28d8c1b3f2592ef6e"></a>

<details>
<summary>event-6cfe0d1846ec42a28d8c1b3f2592ef6e · 전체 저장값</summary>

```json
{
  "event_id": "event-6cfe0d1846ec42a28d8c1b3f2592ef6e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120562,
    "task_id": "task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72"
  },
  "created_at": "2026-09-29T22:33:06.432990+00:00"
}
```

</details>

<a id="row-event-e325f6e4a89c48449978b4464d5c9e07"></a>

<details>
<summary>event-e325f6e4a89c48449978b4464d5c9e07 · 전체 저장값</summary>

```json
{
  "event_id": "event-e325f6e4a89c48449978b4464d5c9e07",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9660,
    "task_id": "task-114324c26650cc9b52f6f2c20d25b68c2521a45215892e253675c4449c72"
  },
  "created_at": "2026-09-29T22:33:21.954969+00:00"
}
```

</details>

<a id="row-event-3473b9bdae2c4631b742ab041880409b"></a>

<details>
<summary>event-3473b9bdae2c4631b742ab041880409b · 전체 저장값</summary>

```json
{
  "event_id": "event-3473b9bdae2c4631b742ab041880409b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 55659,
    "task_id": "task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b"
  },
  "created_at": "2026-09-29T22:33:28.092094+00:00"
}
```

</details>

<a id="row-event-babc1e536d694b6eb7c9591d8fb9eaba"></a>

<details>
<summary>event-babc1e536d694b6eb7c9591d8fb9eaba · 전체 저장값</summary>

```json
{
  "event_id": "event-babc1e536d694b6eb7c9591d8fb9eaba",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5726,
    "task_id": "task-3069b26b62950edee3df9cde3f392bb4d253f58c31baac8e9b7ccaa1a12b"
  },
  "created_at": "2026-09-29T22:33:34.174553+00:00"
}
```

</details>

<a id="row-event-0e6e87a94a3241ec837631fa0e115cf6"></a>

<details>
<summary>event-0e6e87a94a3241ec837631fa0e115cf6 · 전체 저장값</summary>

```json
{
  "event_id": "event-0e6e87a94a3241ec837631fa0e115cf6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-6289f2223d47d36098eca1f558d3269074a0abad00c4799b73cb4a162aca"
  },
  "created_at": "2026-09-29T22:33:46.969043+00:00"
}
```

</details>

<a id="row-event-ce1e1c268e4040e5b88c6df64c6cea95"></a>

<details>
<summary>event-ce1e1c268e4040e5b88c6df64c6cea95 · 전체 저장값</summary>

```json
{
  "event_id": "event-ce1e1c268e4040e5b88c6df64c6cea95",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120562,
    "task_id": "task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599"
  },
  "created_at": "2026-09-29T22:33:51.625954+00:00"
}
```

</details>

<a id="row-event-22dca37741674fb3999011487380c9f3"></a>

<details>
<summary>event-22dca37741674fb3999011487380c9f3 · 전체 저장값</summary>

```json
{
  "event_id": "event-22dca37741674fb3999011487380c9f3",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10291,
    "task_id": "task-68b62b4ad66c385c1bb2e4a209ad1bf9278c748363ea12b0e004adc7b599"
  },
  "created_at": "2026-09-29T22:34:09.123005+00:00"
}
```

</details>

<a id="row-event-54750e0d516d42088d8a6388e6098431"></a>

<details>
<summary>event-54750e0d516d42088d8a6388e6098431 · 전체 저장값</summary>

```json
{
  "event_id": "event-54750e0d516d42088d8a6388e6098431",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 56562,
    "task_id": "task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025"
  },
  "created_at": "2026-09-29T22:34:12.823277+00:00"
}
```

</details>

<a id="row-event-1b514cd7c5cb41caa2908110c6f745c5"></a>

<details>
<summary>event-1b514cd7c5cb41caa2908110c6f745c5 · 전체 저장값</summary>

```json
{
  "event_id": "event-1b514cd7c5cb41caa2908110c6f745c5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5578,
    "task_id": "task-8035a77dba796710c70dc826ef206962aa9f89404a0dccbd813fcd4bd025"
  },
  "created_at": "2026-09-29T22:34:18.125674+00:00"
}
```

</details>

<a id="row-event-e81a008d5bb140a8ad0c67d9a7040aed"></a>

<details>
<summary>event-e81a008d5bb140a8ad0c67d9a7040aed · 전체 저장값</summary>

```json
{
  "event_id": "event-e81a008d5bb140a8ad0c67d9a7040aed",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-5ab82cea6b1e9391424aa162117bd999a1f8e709f0df754aa1ec20f1bf2d"
  },
  "created_at": "2026-09-29T22:34:29.942204+00:00"
}
```

</details>

<a id="row-event-9fb047b2b70b4b5c83af1deb6b45eaef"></a>

<details>
<summary>event-9fb047b2b70b4b5c83af1deb6b45eaef · 전체 저장값</summary>

```json
{
  "event_id": "event-9fb047b2b70b4b5c83af1deb6b45eaef",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119866,
    "task_id": "task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64"
  },
  "created_at": "2026-09-29T22:34:32.697796+00:00"
}
```

</details>

<a id="row-event-790ae30ac24f451bae022de2dc8c9c90"></a>

<details>
<summary>event-790ae30ac24f451bae022de2dc8c9c90 · 전체 저장값</summary>

```json
{
  "event_id": "event-790ae30ac24f451bae022de2dc8c9c90",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10274,
    "task_id": "task-ef02375de8a814b72f3e968fc03afda4041bd5aca605a0c87c4e93c7ed64"
  },
  "created_at": "2026-09-29T22:34:50.534874+00:00"
}
```

</details>

<a id="row-event-d116aa8311ca44cf936bbf088bcd641c"></a>

<details>
<summary>event-d116aa8311ca44cf936bbf088bcd641c · 전체 저장값</summary>

```json
{
  "event_id": "event-d116aa8311ca44cf936bbf088bcd641c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 55020,
    "task_id": "task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56"
  },
  "created_at": "2026-09-29T22:34:56.476859+00:00"
}
```

</details>

<a id="row-event-279e143ca74c449bb51d531b43c9dc53"></a>

<details>
<summary>event-279e143ca74c449bb51d531b43c9dc53 · 전체 저장값</summary>

```json
{
  "event_id": "event-279e143ca74c449bb51d531b43c9dc53",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6041,
    "task_id": "task-ee690678e6f481d67c54da3d09ba28907b22ad79ad9b1bc2b2ae7049fd56"
  },
  "created_at": "2026-09-29T22:35:04.022502+00:00"
}
```

</details>

<a id="row-event-f3c81d8867c142ce8e7b898fe7b2e7c9"></a>

<details>
<summary>event-f3c81d8867c142ce8e7b898fe7b2e7c9 · 전체 저장값</summary>

```json
{
  "event_id": "event-f3c81d8867c142ce8e7b898fe7b2e7c9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-770fa026b2374672cba017d759c75e8fc5cb6bb293c5e5db0c5831b8b359"
  },
  "created_at": "2026-09-29T22:35:17.097640+00:00"
}
```

</details>

<a id="row-event-94df086ddb454b3d9087469bd9751d12"></a>

<details>
<summary>event-94df086ddb454b3d9087469bd9751d12 · 전체 저장값</summary>

```json
{
  "event_id": "event-94df086ddb454b3d9087469bd9751d12",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119866,
    "task_id": "task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7"
  },
  "created_at": "2026-09-29T22:35:19.906085+00:00"
}
```

</details>

<a id="row-event-d0e54aaf509a42a3aa308abfbd69eb01"></a>

<details>
<summary>event-d0e54aaf509a42a3aa308abfbd69eb01 · 전체 저장값</summary>

```json
{
  "event_id": "event-d0e54aaf509a42a3aa308abfbd69eb01",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9956,
    "task_id": "task-170199d152ea86431bce5a808900d1466c7aadd1a4270d00e9a44d5514a7"
  },
  "created_at": "2026-09-29T22:35:36.507779+00:00"
}
```

</details>

<a id="row-event-2bf92af7da3c4f5cb381e40b780729d4"></a>

<details>
<summary>event-2bf92af7da3c4f5cb381e40b780729d4 · 전체 저장값</summary>

```json
{
  "event_id": "event-2bf92af7da3c4f5cb381e40b780729d4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 54489,
    "task_id": "task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3"
  },
  "created_at": "2026-09-29T22:35:40.755498+00:00"
}
```

</details>

<a id="row-event-94ba82653230418aaf6bdde6c6823ccd"></a>

<details>
<summary>event-94ba82653230418aaf6bdde6c6823ccd · 전체 저장값</summary>

```json
{
  "event_id": "event-94ba82653230418aaf6bdde6c6823ccd",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5596,
    "task_id": "task-babe01a3a7bf779560aa99c50593ddbf7822e2104037004564cb5f7bfbf3"
  },
  "created_at": "2026-09-29T22:35:47.345926+00:00"
}
```

</details>

<a id="row-event-7773753aa5784ab48f76154d53cac1ad"></a>

<details>
<summary>event-7773753aa5784ab48f76154d53cac1ad · 전체 저장값</summary>

```json
{
  "event_id": "event-7773753aa5784ab48f76154d53cac1ad",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-7231f58fa80a4136829ac2930ab655d6",
    "versions": [
      "av-f87b49192c164f969e931e9e8660b7a4",
      "av-aa47c29d0ad14ae3bd1d61e736f951a2"
    ]
  },
  "created_at": "2026-09-29T22:35:57.882509+00:00"
}
```

</details>

<a id="row-event-fd511c29276442c494548db0b29f88f5"></a>

<details>
<summary>event-fd511c29276442c494548db0b29f88f5 · 전체 저장값</summary>

```json
{
  "event_id": "event-fd511c29276442c494548db0b29f88f5",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-20e77609c2235f2cba1aa65bbadf480574b3900c47c82e3723546dae5ae6"
  },
  "created_at": "2026-09-29T22:36:06.717196+00:00"
}
```

</details>

<a id="row-event-b3d4bc09078e49db856d42e53fa21c24"></a>

<details>
<summary>event-b3d4bc09078e49db856d42e53fa21c24 · 전체 저장값</summary>

```json
{
  "event_id": "event-b3d4bc09078e49db856d42e53fa21c24",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 113541,
    "task_id": "task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1"
  },
  "created_at": "2026-09-29T22:36:44.895664+00:00"
}
```

</details>

<a id="row-event-4060e510cc534997aaec41893e3b7a70"></a>

<details>
<summary>event-4060e510cc534997aaec41893e3b7a70 · 전체 저장값</summary>

```json
{
  "event_id": "event-4060e510cc534997aaec41893e3b7a70",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6628,
    "task_id": "task-9588b53beb283878569d1b41c9b58103c3fea71cc7a9ff74e36d95753eb1"
  },
  "created_at": "2026-09-29T22:36:59.405308+00:00"
}
```

</details>

<a id="row-event-37261ac9a54940679e36ffa80686308d"></a>

<details>
<summary>event-37261ac9a54940679e36ffa80686308d · 전체 저장값</summary>

```json
{
  "event_id": "event-37261ac9a54940679e36ffa80686308d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 113528,
    "task_id": "task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd"
  },
  "created_at": "2026-09-29T22:37:02.414491+00:00"
}
```

</details>

<a id="row-event-364ab6c8e30845718040e32aebe8a66b"></a>

<details>
<summary>event-364ab6c8e30845718040e32aebe8a66b · 전체 저장값</summary>

```json
{
  "event_id": "event-364ab6c8e30845718040e32aebe8a66b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 8446,
    "task_id": "task-8d4b6a1414780bbc099250152d5fe47744965a0e8c68690161827d6197bd"
  },
  "created_at": "2026-09-29T22:37:22.851391+00:00"
}
```

</details>

<a id="row-event-d9314c6f6b69400791ec5a853366085a"></a>

<details>
<summary>event-d9314c6f6b69400791ec5a853366085a · 전체 저장값</summary>

```json
{
  "event_id": "event-d9314c6f6b69400791ec5a853366085a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 113345,
    "task_id": "task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0"
  },
  "created_at": "2026-09-29T22:37:25.974918+00:00"
}
```

</details>

<a id="row-event-692c4c09ae334f548f0d97264c96f11e"></a>

<details>
<summary>event-692c4c09ae334f548f0d97264c96f11e · 전체 저장값</summary>

```json
{
  "event_id": "event-692c4c09ae334f548f0d97264c96f11e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5675,
    "task_id": "task-3ddb3323d4eed7834b36cb9000a4b295d59770f7dc3ab45a52fdbf8d71b0"
  },
  "created_at": "2026-09-29T22:37:36.059862+00:00"
}
```

</details>

<a id="row-event-324e2bd6dea147388f13704ad4d0e1fc"></a>

<details>
<summary>event-324e2bd6dea147388f13704ad4d0e1fc · 전체 저장값</summary>

```json
{
  "event_id": "event-324e2bd6dea147388f13704ad4d0e1fc",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "evaluation",
      "report",
      "selection",
      "coherence",
      "feedback",
      "report_context"
    ],
    "snapshot_id": "snap-a3e819359d8144efae7fd943812a96ac",
    "versions": [
      "av-04ff51006a3e4b639cb85bfdc57346e6",
      "av-cd107f5e5c8941d7b4e6f9e15cf4e3d2",
      "av-03c8ece38f8543f989d9c637ee499fbe"
    ]
  },
  "created_at": "2026-09-29T22:37:44.713285+00:00"
}
```

</details>

<a id="row-event-b488967dd386402eaa3a4dd2398a2a7d"></a>

<details>
<summary>event-b488967dd386402eaa3a4dd2398a2a7d · 전체 저장값</summary>

```json
{
  "event_id": "event-b488967dd386402eaa3a4dd2398a2a7d",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 60359,
    "task_id": "task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02"
  },
  "created_at": "2026-09-29T22:38:30.751122+00:00"
}
```

</details>

<a id="row-event-e7d03c280ffd45838613415c5e46c30c"></a>

<details>
<summary>event-e7d03c280ffd45838613415c5e46c30c · 전체 저장값</summary>

```json
{
  "event_id": "event-e7d03c280ffd45838613415c5e46c30c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 3135,
    "task_id": "task-60b076cda4fb165527d2ca6ecc3719151175cf51e0d1316b8b55bb7abc02"
  },
  "created_at": "2026-09-29T22:38:36.689214+00:00"
}
```

</details>

<a id="row-event-0dc706bc2e8e475bb7f290fef7647ea4"></a>

<details>
<summary>event-0dc706bc2e8e475bb7f290fef7647ea4 · 전체 저장값</summary>

```json
{
  "event_id": "event-0dc706bc2e8e475bb7f290fef7647ea4",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120010,
    "task_id": "task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77"
  },
  "created_at": "2026-09-29T22:38:48.622286+00:00"
}
```

</details>

<a id="row-event-5f60cd06e91c47928a3d0af35c21cded"></a>

<details>
<summary>event-5f60cd06e91c47928a3d0af35c21cded · 전체 저장값</summary>

```json
{
  "event_id": "event-5f60cd06e91c47928a3d0af35c21cded",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119999,
    "task_id": "task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029"
  },
  "created_at": "2026-09-29T22:38:50.342331+00:00"
}
```

</details>

<a id="row-event-bf3ff13f87d4496f9e6fcccbf4118a75"></a>

<details>
<summary>event-bf3ff13f87d4496f9e6fcccbf4118a75 · 전체 저장값</summary>

```json
{
  "event_id": "event-bf3ff13f87d4496f9e6fcccbf4118a75",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120078,
    "task_id": "task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73"
  },
  "created_at": "2026-09-29T22:38:51.935590+00:00"
}
```

</details>

<a id="row-event-38e11dd3a3974fb988c29738c867fbfd"></a>

<details>
<summary>event-38e11dd3a3974fb988c29738c867fbfd · 전체 저장값</summary>

```json
{
  "event_id": "event-38e11dd3a3974fb988c29738c867fbfd",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120039,
    "task_id": "task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d"
  },
  "created_at": "2026-09-29T22:38:53.620504+00:00"
}
```

</details>

<a id="row-event-801e9ddfad1f4c49b6e8b9d61ae086e2"></a>

<details>
<summary>event-801e9ddfad1f4c49b6e8b9d61ae086e2 · 전체 저장값</summary>

```json
{
  "event_id": "event-801e9ddfad1f4c49b6e8b9d61ae086e2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 7672,
    "task_id": "task-6be2ff6c8c012d06244e96fa00dbb24b3ed175859f601ba755d190606029"
  },
  "created_at": "2026-09-29T22:39:00.788525+00:00"
}
```

</details>

<a id="row-event-b459e485fb99451d8e37e83b2d0facd1"></a>

<details>
<summary>event-b459e485fb99451d8e37e83b2d0facd1 · 전체 저장값</summary>

```json
{
  "event_id": "event-b459e485fb99451d8e37e83b2d0facd1",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 124583,
    "task_id": "task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11"
  },
  "created_at": "2026-09-29T22:39:03.785829+00:00"
}
```

</details>

<a id="row-event-20d5684b630c4170bff3413c03230bd6"></a>

<details>
<summary>event-20d5684b630c4170bff3413c03230bd6 · 전체 저장값</summary>

```json
{
  "event_id": "event-20d5684b630c4170bff3413c03230bd6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9213,
    "task_id": "task-90ec03aeab083318be188ef6c4dbe4da525e316b3305a073246aa4a3aa77"
  },
  "created_at": "2026-09-29T22:39:04.253551+00:00"
}
```

</details>

<a id="row-event-9e1c250c5ad346e7b3b2cc9bae58d673"></a>

<details>
<summary>event-9e1c250c5ad346e7b3b2cc9bae58d673 · 전체 저장값</summary>

```json
{
  "event_id": "event-9e1c250c5ad346e7b3b2cc9bae58d673",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9519,
    "task_id": "task-0360d9d8627211ae448947210d06b960afcc916080fab30defc27bc3cd73"
  },
  "created_at": "2026-09-29T22:39:07.380384+00:00"
}
```

</details>

<a id="row-event-ced785796ca349f799edb71a8e0bb397"></a>

<details>
<summary>event-ced785796ca349f799edb71a8e0bb397 · 전체 저장값</summary>

```json
{
  "event_id": "event-ced785796ca349f799edb71a8e0bb397",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 8968,
    "task_id": "task-0cac8021a30fbb4e2ffcb7a06a56c7d5c5b8fc6984fe2da78dfdb8513e9d"
  },
  "created_at": "2026-09-29T22:39:07.465866+00:00"
}
```

</details>

<a id="row-event-a331363b127a4e1c97fdccc694ede1bb"></a>

<details>
<summary>event-a331363b127a4e1c97fdccc694ede1bb · 전체 저장값</summary>

```json
{
  "event_id": "event-a331363b127a4e1c97fdccc694ede1bb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119948,
    "task_id": "task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4"
  },
  "created_at": "2026-09-29T22:39:20.139910+00:00"
}
```

</details>

<a id="row-event-b62f60de923a419e9d4fa1f0930343d6"></a>

<details>
<summary>event-b62f60de923a419e9d4fa1f0930343d6 · 전체 저장값</summary>

```json
{
  "event_id": "event-b62f60de923a419e9d4fa1f0930343d6",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 10404,
    "task_id": "task-2f2b41f7004ff791b699fa3657a9f6b3d2e4a5c6221a554c177977d2cc11"
  },
  "created_at": "2026-09-29T22:39:20.536994+00:00"
}
```

</details>

<a id="row-event-f72dd730ab5b46daabca3c82de0d73da"></a>

<details>
<summary>event-f72dd730ab5b46daabca3c82de0d73da · 전체 저장값</summary>

```json
{
  "event_id": "event-f72dd730ab5b46daabca3c82de0d73da",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6918,
    "task_id": "task-e478273cebae3b9df5cd11f8ba9758859fa712d47925c2b0c09b1f12dfe4"
  },
  "created_at": "2026-09-29T22:39:28.761271+00:00"
}
```

</details>

<a id="row-event-812a35e85fb44e71b4fc95e723c4aee8"></a>

<details>
<summary>event-812a35e85fb44e71b4fc95e723c4aee8 · 전체 저장값</summary>

```json
{
  "event_id": "event-812a35e85fb44e71b4fc95e723c4aee8",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119977,
    "task_id": "task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685"
  },
  "created_at": "2026-09-29T22:39:37.651570+00:00"
}
```

</details>

<a id="row-event-b378e7ffaf974e62b831ce3973d60dd8"></a>

<details>
<summary>event-b378e7ffaf974e62b831ce3973d60dd8 · 전체 저장값</summary>

```json
{
  "event_id": "event-b378e7ffaf974e62b831ce3973d60dd8",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120015,
    "task_id": "task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa"
  },
  "created_at": "2026-09-29T22:39:43.133772+00:00"
}
```

</details>

<a id="row-event-04187a23c7474b2eab133c256a41ec8b"></a>

<details>
<summary>event-04187a23c7474b2eab133c256a41ec8b · 전체 저장값</summary>

```json
{
  "event_id": "event-04187a23c7474b2eab133c256a41ec8b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119937,
    "task_id": "task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9"
  },
  "created_at": "2026-09-29T22:39:45.448062+00:00"
}
```

</details>

<a id="row-event-be87c2259de046c3b1715ef7afe57985"></a>

<details>
<summary>event-be87c2259de046c3b1715ef7afe57985 · 전체 저장값</summary>

```json
{
  "event_id": "event-be87c2259de046c3b1715ef7afe57985",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6716,
    "task_id": "task-7b44bb5c3dc140574491623249c5e9e408fd5dcccaa0c859a037608b0685"
  },
  "created_at": "2026-09-29T22:39:45.749293+00:00"
}
```

</details>

<a id="row-event-6f0406421cbc4aeb8d1c1d5ab095196a"></a>

<details>
<summary>event-6f0406421cbc4aeb8d1c1d5ab095196a · 전체 저장값</summary>

```json
{
  "event_id": "event-6f0406421cbc4aeb8d1c1d5ab095196a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6915,
    "task_id": "task-b358b5f85fe57f1bf8a64783575fb3cd2797705c7e6090d565f5e72029fa"
  },
  "created_at": "2026-09-29T22:39:53.888909+00:00"
}
```

</details>

<a id="row-event-5d02cb989ddc4947a878744c52425c8b"></a>

<details>
<summary>event-5d02cb989ddc4947a878744c52425c8b · 전체 저장값</summary>

```json
{
  "event_id": "event-5d02cb989ddc4947a878744c52425c8b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6693,
    "task_id": "task-6f1ff00d9f8425546c7672ef6cea68d7af4f6e87515afd3932830125c2e9"
  },
  "created_at": "2026-09-29T22:39:53.993072+00:00"
}
```

</details>

<a id="row-event-03b49469487f41958eed90f47dd26e77"></a>

<details>
<summary>event-03b49469487f41958eed90f47dd26e77 · 전체 저장값</summary>

```json
{
  "event_id": "event-03b49469487f41958eed90f47dd26e77",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120095,
    "task_id": "task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233"
  },
  "created_at": "2026-09-29T22:40:02.354939+00:00"
}
```

</details>

<a id="row-event-a2144bede2754cb28840ea6a1c8302a9"></a>

<details>
<summary>event-a2144bede2754cb28840ea6a1c8302a9 · 전체 저장값</summary>

```json
{
  "event_id": "event-a2144bede2754cb28840ea6a1c8302a9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120011,
    "task_id": "task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3"
  },
  "created_at": "2026-09-29T22:40:14.223732+00:00"
}
```

</details>

<a id="row-event-4a97d95f572f4d10b04d0930e615a124"></a>

<details>
<summary>event-4a97d95f572f4d10b04d0930e615a124 · 전체 저장값</summary>

```json
{
  "event_id": "event-4a97d95f572f4d10b04d0930e615a124",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 7895,
    "task_id": "task-22edd920ad0f0b85efac83e141b8ef08be0df630c3ddf2bf56d1ca0de233"
  },
  "created_at": "2026-09-29T22:40:14.434601+00:00"
}
```

</details>

<a id="row-event-e6c179c1ea2c41ebabe209c4a1d831da"></a>

<details>
<summary>event-e6c179c1ea2c41ebabe209c4a1d831da · 전체 저장값</summary>

```json
{
  "event_id": "event-e6c179c1ea2c41ebabe209c4a1d831da",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 9220,
    "task_id": "task-7b3fc1500d8ae73a9c97ab1f2e99a22fd55d4dbdff0a3d8d0501b678bee3"
  },
  "created_at": "2026-09-29T22:40:33.720096+00:00"
}
```

</details>

<a id="row-event-8598ea15771141e58ac498573237c9a8"></a>

<details>
<summary>event-8598ea15771141e58ac498573237c9a8 · 전체 저장값</summary>

```json
{
  "event_id": "event-8598ea15771141e58ac498573237c9a8",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 120033,
    "task_id": "task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06"
  },
  "created_at": "2026-09-29T22:41:01.528317+00:00"
}
```

</details>

<a id="row-event-97890cc3059849e48dc43de52905e567"></a>

<details>
<summary>event-97890cc3059849e48dc43de52905e567 · 전체 저장값</summary>

```json
{
  "event_id": "event-97890cc3059849e48dc43de52905e567",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 119949,
    "task_id": "task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a"
  },
  "created_at": "2026-09-29T22:41:05.459903+00:00"
}
```

</details>

<a id="row-event-b289a08c94d34431ac6803eb4f4ed09b"></a>

<details>
<summary>event-b289a08c94d34431ac6803eb4f4ed09b · 전체 저장값</summary>

```json
{
  "event_id": "event-b289a08c94d34431ac6803eb4f4ed09b",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6792,
    "task_id": "task-54da606d114c321a6ffe9b50fc3816fa10e95a60fcfeb24eb43cafe13a06"
  },
  "created_at": "2026-09-29T22:41:10.030665+00:00"
}
```

</details>

<a id="row-event-848f487dc31944aba0729562cea683b2"></a>

<details>
<summary>event-848f487dc31944aba0729562cea683b2 · 전체 저장값</summary>

```json
{
  "event_id": "event-848f487dc31944aba0729562cea683b2",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 6929,
    "task_id": "task-2fc5bdc35bdfa896c389263cee2c4e33563f24a34225ccb0249a8f85ad7a"
  },
  "created_at": "2026-09-29T22:41:13.778688+00:00"
}
```

</details>

<a id="row-event-c0c4e02ab96747ba87e36508df6fda2e"></a>

<details>
<summary>event-c0c4e02ab96747ba87e36508df6fda2e · 전체 저장값</summary>

```json
{
  "event_id": "event-c0c4e02ab96747ba87e36508df6fda2e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 107481,
    "task_id": "task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7"
  },
  "created_at": "2026-09-29T22:41:57.165838+00:00"
}
```

</details>

<a id="row-event-9aa9e3eb1707466aa163e0ab5b156ff3"></a>

<details>
<summary>event-9aa9e3eb1707466aa163e0ab5b156ff3 · 전체 저장값</summary>

```json
{
  "event_id": "event-9aa9e3eb1707466aa163e0ab5b156ff3",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 5780,
    "task_id": "task-d1e1ed932b3564524450d1f414bb1284d42cbcaa2e5b3c2c5d71520faee7"
  },
  "created_at": "2026-09-29T22:42:07.218854+00:00"
}
```

</details>

<a id="row-event-70bd128ee8dc489ba9f64acd7ec18e63"></a>

<details>
<summary>event-70bd128ee8dc489ba9f64acd7ec18e63 · 전체 저장값</summary>

```json
{
  "event_id": "event-70bd128ee8dc489ba9f64acd7ec18e63",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [
      "feedback",
      "report_context",
      "report"
    ],
    "snapshot_id": "snap-9e56415fa138459e8d7fd4f2b0224aab",
    "versions": [
      "av-2993e53e0aad4bd0911034d2d78d4d5a",
      "av-4dfbe87665f3492fb5910b3834cf2c5f"
    ]
  },
  "created_at": "2026-09-29T22:42:14.532475+00:00"
}
```

</details>

<a id="row-event-3d7b63e3d368413489cdadd30336985a"></a>

<details>
<summary>event-3d7b63e3d368413489cdadd30336985a · 전체 저장값</summary>

```json
{
  "event_id": "event-3d7b63e3d368413489cdadd30336985a",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-3e7bf6228d8c493d9ced98991287bf98",
    "versions": [
      "av-fea07164dc5041d4a7c0a765829ae407"
    ]
  },
  "created_at": "2026-09-29T22:42:59.962813+00:00"
}
```

</details>

<a id="row-event-1e39d8967f1d4a1a94c42a7ea3701877"></a>

<details>
<summary>event-1e39d8967f1d4a1a94c42a7ea3701877 · 전체 저장값</summary>

```json
{
  "event_id": "event-1e39d8967f1d4a1a94c42a7ea3701877",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "DECISION_RECORDED",
  "payload": {
    "decision_id": "dec-6451d50e7b39b502decc397db7d4d3fe780ea0c395c3b632cd65789e3e12"
  },
  "created_at": "2026-09-29T22:43:10.326254+00:00"
}
```

</details>

<a id="row-event-93b93b5530844750979aff68704d0288"></a>

<details>
<summary>event-93b93b5530844750979aff68704d0288 · 전체 저장값</summary>

```json
{
  "event_id": "event-93b93b5530844750979aff68704d0288",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-41ca8f7ce9484568b130ff09276d4620",
    "versions": [
      "av-930bb2bc8cf245be82ec07c0e2678202"
    ]
  },
  "created_at": "2026-09-29T22:43:38.271311+00:00"
}
```

</details>

<a id="row-event-df21e948b27145568051ca6b64cd8d70"></a>

<details>
<summary>event-df21e948b27145568051ca6b64cd8d70 · 전체 저장값</summary>

```json
{
  "event_id": "event-df21e948b27145568051ca6b64cd8d70",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-12ef7dca76e6425f87bc37a58d0ad316",
    "versions": [
      "av-0702df0f5b4f4b0b86557e81397e9e88"
    ]
  },
  "created_at": "2026-09-29T22:44:19.556648+00:00"
}
```

</details>

<a id="row-event-9e38aa05bfbd4c18adbe4ee4d6e3617c"></a>

<details>
<summary>event-9e38aa05bfbd4c18adbe4ee4d6e3617c · 전체 저장값</summary>

```json
{
  "event_id": "event-9e38aa05bfbd4c18adbe4ee4d6e3617c",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "EPOCH_CHANGED",
  "payload": {
    "epoch": 52,
    "previous": 51,
    "reason": "user_resume_or_replan"
  },
  "created_at": "2026-09-29T22:57:01.829324+00:00"
}
```

</details>

<a id="row-event-3708c748d0f84f53a4303e6e7c231e1e"></a>

<details>
<summary>event-3708c748d0f84f53a4303e6e7c231e1e · 전체 저장값</summary>

```json
{
  "event_id": "event-3708c748d0f84f53a4303e6e7c231e1e",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-ab9f74e25b044c86a2e227b43c6157ff",
    "versions": []
  },
  "created_at": "2026-09-29T22:57:39.195332+00:00"
}
```

</details>

<a id="row-event-d3fce5ae797740209fc2d52a11a837cb"></a>

<details>
<summary>event-d3fce5ae797740209fc2d52a11a837cb · 전체 저장값</summary>

```json
{
  "event_id": "event-d3fce5ae797740209fc2d52a11a837cb",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_RESERVED",
  "payload": {
    "reserve": 68573,
    "task_id": "task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e"
  },
  "created_at": "2026-09-29T22:58:08.777677+00:00"
}
```

</details>

<a id="row-event-caf5963a6a02421cbf6ffc5daac943bc"></a>

<details>
<summary>event-caf5963a6a02421cbf6ffc5daac943bc · 전체 저장값</summary>

```json
{
  "event_id": "event-caf5963a6a02421cbf6ffc5daac943bc",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "ACTION_COMPLETED",
  "payload": {
    "actual_microusd": 4032,
    "task_id": "task-acfd96c9fdfe81af87a0bf528edb501ce874067a2e1532ac50935046125e"
  },
  "created_at": "2026-09-29T22:58:13.159168+00:00"
}
```

</details>

<a id="row-event-6c2e88d6298741d596ddc8b00c21f1f9"></a>

<details>
<summary>event-6c2e88d6298741d596ddc8b00c21f1f9 · 전체 저장값</summary>

```json
{
  "event_id": "event-6c2e88d6298741d596ddc8b00c21f1f9",
  "run_id": "run-baa72a38ef40c8c63155ffc7a1dd25ee",
  "event_type": "SNAPSHOT_COMMITTED",
  "payload": {
    "invalidated": [],
    "snapshot_id": "snap-f6d53363d6714c2c8f15d3d5a4c70178",
    "versions": [
      "av-0d55982984a84cf581a386c864043cd4"
    ]
  },
  "created_at": "2026-09-29T22:58:22.471342+00:00"
}
```

</details>
