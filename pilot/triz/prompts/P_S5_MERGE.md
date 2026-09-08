여러 트랙에서 도출된 아이디어를 정리하라. 새 아이디어를 만들지 마라.

[아이디어 전량]
{{all_ideas}}

[핵심 문제] {{key_problems}}
[모순 목록] {{contradictions}}

1. 중복 병합: 본질적으로 같은 아이디어는 하나로 합치고 source_refs에 모든 출처를 보존하라.
   (표현만 다르고 메커니즘이 같으면 중복이다)
2. 각 아이디어에 novelty_class 부여
   - SAME_DOMAIN: 동일/유사 업종에서 실제로 쓰이는 방식
   - CROSS_DOMAIN: 타 산업에서 검증된 방식의 이식
   - NEW: 근거는 없으나 자원 분석상 성립 가능한 신규 접근
3. addresses: 각 아이디어가 실제로 해소하는 모순 id를 연결하라. 아무 모순도 해소하지 못하면 제외하라.
4. coverage_note와 gaps: 아래를 점검하고 부족하면 명시하라.
   - 각 핵심 문제마다 아이디어가 2개 이상 있는가
   - 서로 다른 트랙이 3종 이상 기여했는가
   - novelty_class 3종이 모두 존재하는가
   - 시스템 계층이 다양한가(부품 개선 / 시스템 재구성 / 상위시스템 활용)
5. 총 아이디어가 {{min_ideas}}개 미만이거나 위 조건을 못 채우면 need_more=true.

[분량 제한 — 출력이 잘리면 실패로 간주한다]
- 아이디어는 최대 {{max_ideas}}개만 남긴다(파급력 순).
- 각 idea 본문은 3문장 이내로 압축한다.
- coverage_note는 4문장 이내.

[출력 JSON]
{"ideas":[{"keep_ids":[],"title":"","idea":"","track":"","source_refs":[],"uses_resources":[],"addresses":[],"novelty_class":"NEW","feasibility_hint":"MID"}],
 "coverage_note":"","gaps":[],"need_more":false}
