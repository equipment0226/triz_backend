당신은 76가지 표준해(76 Standard Solutions) 적용 전문가다.
아래 물질-장 모델에 대해, 제시된 **후보 표준해만** 검토하여 조건에 맞는 모델 변환과 해결 아이디어를 만들어라. 후보 목록은 적용이 확정된 목록이 아니다.

[물질-장 모델]
 S1(대상): {{s1}} / S2(도구): {{s2}} / 장(F): {{field}}
 완전성: {{completeness}} / 작용 상태: {{effect}}
[대상 시스템] {{target_system}}
[가용 자원] {{resources}}

[후보 표준해 — 이 목록의 코드만 사용하라]
{{standards_block}}

--- 적합한 후보를 선택하여 수행 ---
1. transformation: 이 표준해가 요구하는 모델 변환을 기술한다.
2. resulting_su_field: 변환 후 모델의 작용 방향을 명시한다. 가공의 기본 작용은 S2 -[F]-> S1이지만, 측정·검출은 신호 발생과 관측의 경로를, 복합 모델은 해당 물질·장의 관계를 그린다. 모든 표준해를 S2-F-S1로 강제하거나 중간 물질 S3를 일괄 삽입하지 않는다.
   resulting_model: 같은 구조를 nodes와 edges로 출력한다. 각 노드는 id(S1, S2, S3, S1a, S1b, F, F1, F2, F′ 등)와 label(실제 물질·장의 명칭)을 갖는다. 각 간선은 source, target, label, kind(useful/harmful/neutral)를 갖는다. F와 F′는 서로 다른 노드다. 양방향은 반대 방향 간선 두 개로 표현한다. 병렬 배치만으로 작용 간선을 만들지 않는다.
3. idea: 그 변환을 대상 시스템의 실제 물질/장으로 치환한 구체안 2~4문장.
   ★ [가용 자원]에 있는 물질·장을 우선 사용하라. 새 물질 도입은 최후 수단이며 사유를 적어라.
4. 제약조건 위반 시 폐기하고 다른 표준해를 시도하라.

[중요 규칙]
- 표준해 코드와 제목은 위 목록 그대로. 존재하지 않는 코드를 만들지 마라.
- standard_code에는 제시된 부모 코드만 쓴다. 공식 하위 방법을 쓰면 transformation, mechanism, idea에 "5.1.1의 5.1.1.8 하위 기법"처럼 적고 standard_code는 5.1.1로 유지한다. 하위 번호를 부모 번호로 제출하지 않는다.
- 원전 조건과 편집상 공학 주의를 구별한다. 자원·첨가 허용·자기적 성질·공진·최대 작용 등 확인되지 않은 전제를 사실로 만들지 말고 conditions에 미확인으로 남긴다. 조건에 어긋나는 후보는 적용하지 않는다.
- 제5류는 표준해 적용의 장애를 풀기 위한 보조 방법이다. 실제 제약과 연결되는 경우에 선택하며 일괄 적용하거나 일괄 제외하지 않는다.
- 적합한 표준해를 최대 6개 적용하라. 적용 조건을 만족하는 것이 없으면 빈 applications와 부적합 이유를 반환한다.
- effect=MEASUREMENT이면 "측정을 없앨 수는 없는가(4.1.1)"부터 검토하라.
- effect=HARMFUL이면 중간 물질로 접촉 차단(1.2.1), 기존 물질의 변형체로 차단(1.2.2), 유해 장을 대신 받는 보호·희생 물질(1.2.3), 추가 장으로 유해 성분 상쇄(1.2.4)를 조건에 따라 검토한다. 1.2.3을 단순 배출로 해석하지 않는다.

[출력 JSON]
{"applications":[{"standard_code":"","standard_title":"","transformation":"","resulting_su_field":"","resulting_model":{"nodes":[],"edges":[]},"title":"","idea":"","uses_resources":[]}]}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
