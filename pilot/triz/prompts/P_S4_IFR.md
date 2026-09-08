당신은 TRIZ 마스터다. 이상해결책(IFR, Ideal Final Result)을 정의하라.

[주기능] {{basic_function}}
[핵심 단점] {{key_disadvantages}}
[근본 원인] {{root_causes}}
[가용 자원] {{resource_names}}
[작용 영역/시간] OZ={{operative_zone}} / OT={{operative_time}}

--- 작성 규칙 ---
1. statement 형식(엄수):
   "X-요소는, 시스템을 복잡하게 만들지 않고 유해한 영향을 일으키지 않으면서,
    [작용 시간] 동안 [작용 영역]에서, [유익 기능]을 유지하면서 [유해/부족 현상]을 스스로 제거한다."
2. x_element: 그 일을 해내는 미지의 요소를 '무엇인지 정하지 않은 채' 기능으로만 정의하라.
   실제 부품 이름을 넣지 마라("자성체를 넣는다" 같은 해결책 선점 금지).
3. without: 추가하면 안 되는 것 3~5개 (새 부품, 비용, 에너지, 복잡도, 인력 등 구체적으로)
4. ideality_note: 이상성 = (유익 기능의 합) / (비용 + 유해 작용의 합) 관점에서
   현재 시스템의 위치와 IFR이 지향하는 지점을 2~3문장으로.
5. intensified: 강화 IFR — "기존 자원만으로, 아무것도 추가하지 않고" 조건을 걸었을 때의 진술.
6. constraint_conflicts: 위 진술이 제약조건을 위반하거나 무시하고 있다면 모두 적어라.
   위반이 있으면 statement를 수정한 뒤 출력하라. 제약은 IFR보다 우선한다.

[출력 JSON]
{"statement":"","x_element":"","without":[],"ideality_note":"","intensified":"","constraint_conflicts":[]}
