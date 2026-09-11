"""Individually authored concept diagrams for the 76 inventive standards.

These are explanatory redrawings, not scans of the source illustrations or
claims that a particular engineering implementation has been validated.
S1 = target, S2 = tool; F = field. Non-S/F nodes describe a process or state.
"""

# Every row specifies two graphs independently. A node is key~glyph~label.
# An edge is source>target~relationship~style (action, harmful, link, both).
# The renderer never infers an interaction from neighboring nodes.
ROWS = '''
1.1.1|누락된 작용 요소|S1~substance~S1 대상;S2~missing~S2 또는 F 누락||작용 관계 완성|F~field~F 작용장;S2~substance~S2 도구;S1~substance~S1 대상|F>S2~에너지 공급~action;S2>S1~필요 기능~action|없는 물질 또는 장을 보완한다.
1.1.2|장에 대한 반응 부족|F~field~F 기존 장;S1~substance~S1 원래 물질|F>S1~반응 부족~harmful|물질 내부에 첨가|F~field~F 기존 장;S1~composite~S1 내부의 S3|F>S1~내부 첨가로 반응 개선~action|S3는 S1 또는 S2 내부에 포함된다.
1.1.3|내부 변경이 어려움|S1~substance~S1 원래 물질||외부에 보조 물질 결합|F~field~F 기존 장;S3~layer~S3 외부 보조층;S1~substance~S1 대상|F>S3~작용~action;S3>S1~외부 결합~link|내부 첨가와 달리 S3를 표면·외부에 둔다.
1.1.4|필요 물질이 시스템 밖에 있음|E~environment~환경의 가용 물질;S1~substance~S1 대상||환경 물질을 작용에 편입|E~environment~환경 자원;S3~substance~S3 보조 물질;S1~substance~S1 대상|E>S3~확보~action;S3>S1~필요 작용~action|공기·물 등 실제로 있는 환경 자원을 활용한다.
1.1.5|환경 물질이 부적합|E~environment~기존 환경;S1~substance~S1 대상||환경을 변형해 자원 확보|E~environment~기존 환경;M~process~교체·분해·첨가;S3~substance~필요 성질의 S3|E>M~환경 변경~action;M>S3~물질 확보~action|이미 있는 물질을 가져오는 1.1.4와 구별한다.
1.1.6|미량 작용의 직접 제어가 어려움|F~field~투입 작용;S1~substance~정량이 필요한 S1|F>S1~양 조절 어려움~harmful|과잉 작용 후 잉여 제거|A~process~충분한 작용;B~process~초과분 제거;S1~substance~필요한 양만 잔류|A>B~잉여 발생~action;B>S1~정량 확보~action|물질의 잉여는 장으로, 장의 잉여는 물질로 제거할 수 있다.
1.1.7|대상이 최대 작용을 견디지 못함|F~field~F 최대 작용;S1~substance~S1 취약 대상|F>S1~직접 작용 금지~harmful|다른 물질이 강한 작용을 받음|F~field~F 최대 작용;S3~substance~S3 연결 물질;S1~substance~S1 대상|F>S3~최대 작용~action;S3>S1~필요 결과 전달~action|강한 작용의 수신 물질을 바꾸며 전달 경로를 검토한다.
1.1.8|영역별 요구 강도가 다름|F~field~F 균일한 장;S1~pattern~S1 서로 다른 영역|F>S1~일률적 작용~harmful|국부 보호 또는 국부 증강|A~shield~강한 F + 보호층;B~pattern~선택 영역만 작용;C~field~약한 F + 국부 증강|A>B~보호 방식~action;C>B~증강 방식~action|두 경로는 대안이다. 모든 영역에 같은 강도를 가하지 않는다.
1.2.1|직접 접촉에 유해 작용|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~유해 접촉~harmful|제3의 물질로 접촉 분리|S2~substance~S2 도구;S3~layer~S3 중간 물질;S1~substance~S1 대상|S2>S3~접촉~link;S3>S1~유익 작용 유지~action|새 중간 물질이 유해한 직접 접촉을 차단한다.
1.2.2|외부 물질 도입이 제한됨|S2~substance~S2 기존 물질;S1~substance~S1 대상|S2>S1~유해 접촉~harmful|기존 물질에서 차단층 생성|S2~substance~S2 기존 물질;S3~layer~S3 = 변형된 S1·S2;S1~substance~S1 대상|S2>S3~기존 재료의 변형~action;S3>S1~유해 접촉 완화~action|S3의 기원이 기존 물질이라는 점이 1.2.1과 다르다.
1.2.3|유해한 장이 대상을 공격|F~field~F 유해 장;S1~substance~S1 대상|F>S1~유해 작용~harmful|보호 물질이 유해 장을 대신 받음|F~field~F 유해 장;S2~shield~S2 보호·희생 물질;S1~substance~S1 보호 대상|F>S2~흡수·완충~action|보호 물질 뒤에 유해 작용 화살표를 임의로 이어 그리지 않는다.
1.2.4|접촉을 유지해야 하는 유해 작용|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~유익 + 유해~harmful|기존 작용과 상쇄 작용 병행|F1~field~F1 기존 장;S1~substance~S1 대상;F2~field~F2 추가 장|F1>S1~유익 작용 유지~action;F2>S1~유해 성분 상쇄~action|분리층 대신 제2의 장을 추가한다. 크기·위상 조건을 확인한다.
1.2.5|강자성에 의한 유해 결합|F~magnet~자기장;S1~magnetic~강자성 물질|F>S1~유해한 결합~harmful|강자성 성질 변화로 결합 해제|P~process~가열·물리적 효과;S1~substance~자성 변화 물질;R~process~유해 결합 해제|P>S1~자기 특성 변화~action;S1>R~결합 약화~action|퀴리점 등 물성 변화를 이용하며 단순 역자장과 구별한다.
2.1.1|하나의 물질–장 작용|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~F1 작용~action|공유 물질을 통한 연쇄 작용|S3~substance~S3 새 도구;S2~substance~S2 공유 물질;S1~substance~S1 대상|S3>S2~F2 독립 제어~action;S2>S1~F1 작용~action|S2 자체를 별도의 물질–장 시스템으로 발전시킨 예다.
2.1.2|한 장의 작용이 부족함|F1~field~F1;S1~substance~기존 S1·S2|F1>S1~부족한 작용~harmful|같은 물질 쌍에 두 장 적용|F1~field~F1 기존 장;S1~substance~기존 S1·S2;F2~field~F2 추가 장|F1>S1~기존 작용~action;F2>S1~보강 작용~action|물질을 교체하지 않고 추가 장의 작용을 결합한다.
2.2.1|현재 장의 제어가 어려움|F~field~제어가 어려운 F;S1~substance~S1 대상|F>S1~불안정한 작용~harmful|제어성이 높은 장으로 교체|F~pulse~조절 가능한 F′;S1~substance~S1 대상|F>S1~정밀한 작용~action|보편적인 장의 우열이 아니라 해당 조건의 제어성을 비교한다.
2.2.2|일체 물질|S~substance~일체형 S||분할도를 점차 높임|S~segmented~분할된 S;P~particles~미립자 S|S>P~더 작은 단위~action|S1 또는 S2의 분할로 접촉 면적·응답·분포를 바꾼다.
2.2.3|공동이 없는 고체|S~substance~일체 고체||기공 구조의 발전|A~hollow~공동;B~porous~다공질;C~capillary~구조화된 모세관|A>B~다수 기공~action;B>C~배열·크기 제어~action|기공 속 유체와 모세관 작용도 활용할 수 있다.
2.2.4|고정 구조와 일정한 작용|S~substance~고정된 S;F~field~일정한 F||운전 중 변화하는 시스템|S~flexible~관절·유연한 S;F~pulse~가변·맥동 F|F>S~조건에 맞춰 조절~action|물질 구조 또는 장을 동적화하는 두 방향을 표시한다.
2.2.5|균일한 작용장|F~field~균일 F||장의 분포를 구조화|F1~gradient~공간 구배 F;F2~pulse~시간 패턴 F||공간과 시간의 패턴은 선택하거나 결합할 수 있다.
2.2.6|균질한 물질|S~substance~균질 S||물질의 성질을 구조화|S1~pattern~위치별 물성 S;S2~phase~상태가 변하는 S||장 자체를 바꾸는 2.2.5와 달리 물질의 분포·상태를 바꾼다.
2.3.1|장과 물질의 주기가 어긋남|F~wave~F 구동 주기;S~substance~S 고유 응답|F>S~주기 불일치~harmful|구동과 고유 응답의 정합|F~wave~F 구동 주기;S~wave~S 고유 주기|F>S~주파수 정합~both|장–물질의 리듬을 맞춘다. 과대 공진은 별도로 검토한다.
2.3.2|여러 장이 독립적으로 작동|F1~wave~F1 주기;F2~pulse~F2 주기||장 사이의 리듬 정합|F1~wave~F1 조정된 주기;F2~wave~F2 조정된 주기|F1>F2~주기·위상 동기화~both|물질의 고유 진동이 아니라 여러 장 사이의 관계다.
2.3.3|동시 작용이 서로 방해함|A~process~작용 A;B~process~작용 B|A>B~동시 수행 충돌~harmful|휴지기에 다른 작용 배치|A1~pulse~A 수행;B~pulse~A 휴지기에 B;A2~pulse~A 재개|A1>B~시간 순서~action;B>A2~시간 순서~action|예: 가공이 멈춘 사이 측정. 화살표는 시간 진행이다.
2.4.1|일반적인 작용계|F~field~일반 F;S~substance~일반 물질|F>S~작용~action|덩어리 강자성체로 자기 제어|F~magnet~자기장;S~magnetic~덩어리 강자성체|F>S~자기력 제어~action|아직 입자화하지 않은 Proto-Fe-Field 단계다.
2.4.2|덩어리 자성 물질|F~magnet~자기장;S~magnetic~덩어리 자성체|F>S~자기 작용~action|강자성 입자의 분산 제어|F~magnet~자기장;S~particles~강자성 입자|F>S~입자 분포·운동 제어~action|자성 입자로 바꾸거나 입자를 첨가한다.
2.4.3|자성 입자의 집합|S~particles~미세 자성 입자||유체 속 안정적인 콜로이드 분산|F~magnet~자기장;S~fluid~콜로이드 자성유체|F>S~유체 형상·이동 제어~action|액체 담체 속 안정 분산을 표현한다. MR 유체와 혼동하지 않는다.
2.4.4|기공 기능이 없는 Fe-Field|F~magnet~자기장;S~magnetic~자성 물질|F>S~자기 작용~action|모세관·기공 기능의 결합|F~magnet~자기장;S~porous~기공을 가진 자성계;L~fluid~기공 속 유체|F>S~자기 제어~action;S>L~보유·이동~link|자기 작용과 기공의 저장·전달 기능을 함께 사용한다.
2.4.5|주재료를 자성 입자로 바꿀 수 없음|S~substance~유지해야 할 주재료||자성 첨가물을 가진 복합체|F~magnet~자기장;S~composite~주재료 + 자성 첨가물|F>S~복합체 제어~action|주재료를 유지한 내부·외부 복합 Fe-Field다.
2.4.6|대상에 자성 첨가를 할 수 없음|S~substance~변경 금지 대상||주변 자성 매질을 통해 제어|F~magnet~자기장;E~fluid~자성 입자 환경;S~substance~원래 대상|F>E~환경 제어~action;E>S~작용 전달~action|대상과 자성 입자 환경을 별개의 요소로 표시한다.
2.4.7|자기 특성이 고정됨|S~magnetic~고정 자기 특성||물리 상태를 바꾸어 자기 작용 제어|P~process~온도·응력 변화;S~magnetic~자기 특성 변화;R~process~작용 변화|P>S~물리효과~action;S>R~자기 제어~action|물리 상태 → 자기 물성 → 작용의 인과 경로다.
2.4.8|고정된 자기 시스템|F~magnet~일정 자기장;S~magnetic~고정 자성 구조|F>S~고정 작용~action|가변적인 자기 시스템|F~pulse~가변 자기장;S~flexible~유연·가변 자성 구조|F>S~운전 중 조정~action|자기 구동과 구성요소의 동적화를 표시한다.
2.4.9|균일한 자기 분포|F~magnet~균일 자기장;S~magnetic~균일 자성 분포||자기장·물질에 공간 패턴 부여|F~gradient~자기장 구배;S~pattern~자성 물질 패턴|F>S~위치별 작용~action|단순 시간 변동과 공간 분포의 구조화를 구별한다.
2.4.10|자기 구동과 응답 주기 불일치|F~magnet~자기 구동;S~wave~구성요소 응답|F>S~주기 불일치~harmful|자기계의 리듬 정합|F~wave~자기 구동 주기;S~wave~자성계 응답 주기|F>S~리듬 정합~both|자기장 또는 구성요소의 주기를 조정한다.
2.4.11|강자성 입자에 의존|F~magnet~자기장;S~particles~강자성 입자|F>S~자기 작용~action|전류와 장의 상호작용 활용|I~current~전류·유도전류;F~magnet~상호작용 장;S~substance~도전성 물질|I>F~전자기 결합~both;F>S~힘·변형~action|도전성 물질의 전류 작용을 쓰며 자성유체 도식과 구별한다.
2.4.12|전기장이 없는 현탁액|S~fluid~분산 입자 현탁액||전기장으로 유동 특성 변화|F~field~인가 전기장;S~chains~입자 사슬 형성;R~process~항복·유동 특성 변화|F>S~입자 배열~action;S>R~유변 특성 제어~action|ER 현탁액의 전기장 반응이며 자기장 반응이 아니다.
3.1.1|단일 시스템|A~system~시스템 A||둘 또는 여럿을 결합|A~system~시스템 A;B~system~시스템 B;C~system~시스템 C|A>B~기능 결합~link;B>C~확장~link|개별 시스템의 결합으로 새로운 기능을 얻는다.
3.1.2|느슨하거나 없는 연결|A~system~시스템 A;B~system~시스템 B||연결 방식의 발전|A~system~고정 결합;B~flexible~유연 결합;C~field~장에 의한 결합|A>B~발전 방향~action;B>C~발전 방향~action|화살표는 시스템 간 힘이 아니라 연결 방식의 발전이다.
3.1.3|같은 성질의 요소들|A~system~동일 요소 A;B~system~동일 요소 A|A>B~결합~link|성질 차이의 확대|A~system~특성이 다른 요소;B~pattern~이종 요소;C~system~상반 성질 요소|A>B~차이 확대~action;B>C~차이 확대~action|비슷한 요소의 집합에서 이종·반대 성질의 조합으로 발전한다.
3.1.4|기능과 부품이 중복됨|A~system~시스템 A;B~system~시스템 B|A>B~중복된 기능~link|공통 기능을 통합|C~composite~통합된 구성요소;R~process~중복 부품 제거|C>R~축약~action|기능을 보존하며 바이·폴리 시스템을 간소화한다.
3.1.5|전체와 부분에 다른 요구|P~substance~부분은 A;W~system~전체도 A|P>W~동일 성질~link|전체와 부분에 상반 성질 배치|P~segmented~부분은 A;W~flexible~전체는 반대 A|P>W~배치·연결로 구성~link|예: 단단한 개별 요소를 유연한 전체로 연결한다.
3.2.1|거시적 부품이 기능 수행|M~system~거시적 기구||미시 구조가 기능 수행|S~particles~분자·미시 구조;F~field~미시적 작용;R~process~필요 기능|S>F~구조·물성~link;F>R~기능 구현~action|단순 소형화가 아니라 기능을 수행하는 구조 수준을 바꾼다.
4.1.1|측정하고 나서 보정|M~sensor~측정;C~process~조절;R~substance~목표 상태|M>C~측정값~action;C>R~보정~action|측정 없이 목표 상태 확보|S~system~자기 조절 구조;R~substance~목표 상태|S>R~구조적으로 유지~action|필요한 결과를 보장하는 구조로 측정 자체의 필요를 줄인다.
4.1.2|실물을 직접 측정하기 어려움|S~substance~실물 대상;M~sensor~측정기|S>M~직접 접근 곤란~harmful|복제물 또는 영상을 측정|S~substance~실물 대상;C~copy~대응 영상·복제물;M~sensor~측정기|S>C~대응 관계~link;C>M~간접 측정~action|복제물과 실물 사이의 대응·보정 조건을 확인한다.
4.1.3|절대 상태의 측정이 어려움|S~substance~절대 상태;M~sensor~측정기|S>M~직접 판별 곤란~harmful|상태의 연속 변화 검출|S~wave~연속적인 상태 변화;M~sensor~변화·전환 검출|S>M~변화 신호~action|연속 변화를 감지하는 방식이다. 미분값 측정은 4.5.2다.
4.2.1|관측 가능한 출력 장이 없음|S~substance~관측 대상||입력 작용을 검출 가능한 출력으로 변환|F~field~입력 작용;S~substance~측정 대상;O~sensor~검출 가능한 F출력|F>S~여기·작용~action;S>O~측정 신호~action|대상의 상태와 연결되는 출력 장을 형성한다.
4.2.2|대상 자체가 잘 검출되지 않음|S~substance~약한 출력의 대상||대상에 검출 가능한 첨가물 도입|S~composite~대상 + 표지 S3;F~field~표지의 출력 장;M~sensor~검출기|S>F~표지 반응~action;F>M~신호 검출~action|표지는 대상에 첨가된다. 환경에 넣는 4.2.3과 구별한다.
4.2.3|대상에 표지를 넣을 수 없음|S~substance~변경 금지 대상||환경에 표지를 넣고 변화 관측|S~substance~원래 대상;E~environment~표지 S3가 있는 환경;M~sensor~검출기|S>E~대상·환경 상호작용~both;E>M~환경 신호~action|측정 신호가 환경의 표지에서 나온다.
4.2.4|환경에 새 표지도 넣을 수 없음|E~environment~기존 환경||환경 자원에서 표지를 생성|E~environment~환경 자원;S3~particles~현장에서 생성한 표지;M~sensor~검출기|E>S3~분해·상태 변화~action;S3>M~생성 표지 검출~action|표지의 공급원이 기존 환경이라는 점을 표시한다.
4.3.1|측정 신호가 약함|S~substance~측정할 상태;M~sensor~검출기|S>M~신호 부족~harmful|물리효과로 상태를 신호로 변환|S~substance~측정할 상태;P~process~선택한 물리효과;M~sensor~변환 신호 검출|S>P~상태 변화~action;P>M~신호 변화~action|효과의 작동 조건과 검출 가능한 변화량을 확인한다.
4.3.2|대상 상태를 직접 측정하기 어려움|S~substance~대상 상태||대상 자체의 공진 변화를 측정|F~wave~여기 주파수;S~wave~대상 자체의 공진;M~sensor~공진 변화 측정|F>S~진동 여기~action;S>M~공진 특성~action|보조 물체가 아니라 대상 또는 그 일부가 공진한다.
4.3.3|대상 자체의 공진을 쓰기 어려움|S~substance~원래 대상||결합한 보조 물체의 공진 활용|S~substance~원래 대상;A~wave~결합된 보조 물체;M~sensor~공진 변화 측정|S>A~상태 전달~link;A>M~보조체 공진~action|보조체와 대상의 결합이 측정할 상태를 전달해야 한다.
4.4.1|비자기적 측정|S~substance~비자기적 물질;M~sensor~기존 측정기|S>M~기존 신호~action|자성체와 자기장으로 측정|F~magnet~자기장;S~magnetic~덩어리 자성 물질;M~sensor~자기 신호 검출|F>S~자기 작용~action;S>M~출력 변화~action|기계적 제어용 2.4.1과 달리 출력은 측정 신호다.
4.4.2|일반 물질 또는 덩어리 자성체|S~magnetic~측정 대상||자성 입자를 이용한 측정|S~particles~자성 입자;F~magnet~입자에 따른 자기 신호;M~sensor~검출기|S>F~분포·상태 반영~action;F>M~측정~action|입자화하거나 자성 입자를 도입해 검출성을 높인다.
4.4.3|주재료 교체가 제한됨|S~substance~유지해야 할 주재료||자성 첨가물의 신호 측정|S~composite~주재료 + 자성 첨가물;F~magnet~자기 출력;M~sensor~검출기|S>F~상태 반영~action;F>M~복합체 측정~action|주재료를 유지한 복합 자기 측정 모델이다.
4.4.4|대상에 자성 입자 첨가가 제한됨|S~substance~변경 금지 대상||자성 환경을 통해 상태 측정|S~substance~원래 대상;E~fluid~자성 입자 환경;M~sensor~자기 출력 검출|S>E~상태 전달~link;E>M~환경 자기 신호~action|대상이 아니라 환경의 자기 반응을 측정한다.
4.4.5|자기 신호 변화가 부족함|S~magnetic~자기 측정계||상태에 따른 자기 물성 변화를 검출|P~process~온도·응력 등 상태;S~magnetic~자기 물성 변화;M~sensor~변화 신호 검출|P>S~자기 물리효과~action;S>M~측정 신호~action|예: 퀴리점·자기탄성 등. 효과별 조건을 따로 검토한다.
4.5.1|하나의 측정 채널|M~sensor~단일 측정||서로 보완하는 복수 측정|M1~sensor~측정 채널 A;R~process~통합된 판단;M2~sensor~측정 채널 B|M1>R~관측값 A~action;M2>R~관측값 B~action|채널의 결합으로 단일 측정의 한계를 보완한다.
4.5.2|값 자체를 측정|X~sensor~값 x(t)||변화율과 고차 변화량으로 발전|X~sensor~값 x(t);V~wave~변화율 dx/dt;A~wave~고차 변화 d²x/dt²|X>V~미분~action;V>A~추가 미분~action|상태값 → 1차 변화율 → 고차 변화율의 측정 방향이다.
5.1.1|새 물질의 직접 도입이 제한됨|S3~missing~새 물질 S3;S~system~기존 시스템|S3>S~도입 제약~harmful|제약에 맞는 물질 확보 경로|A~composite~기존 물질의 첨가물;B~hollow~공동·일시적 물질;C~environment~가용 자원 활용||상황에 맞는 우회 경로의 예다. 모든 대안을 동시에 적용하지 않는다.
5.1.2|도구가 없고 새 도구 도입이 어려움|S1~substance~대상 S1||대상의 일부가 다른 일부에 작용|A~segmented~S1a 대상의 일부;B~segmented~S1b 대상의 다른 일부|A>B~상호작용~both|S1을 나누어 물질–장 관계를 만들며 외부 S2를 가정하지 않는다.
5.1.3|첨가물의 영구 잔류가 문제|S3~substance~남아 있는 S3||기능 수행 뒤 제거 또는 동화|S3~substance~일시적 S3;A~process~필요 기능 수행;R~process~제거·원래 물질과 동화|S3>A~사용~action;A>R~작용 종료 후~action|소멸을 가정하지 않고 실제 제거·변환 경로를 지정한다.
5.1.4|큰 부피에 많은 재료가 필요함|S~substance~대량 고체||빈 공간을 포함해 부피 확보|S~foam~거품·팽창 구조;R~system~필요한 외형·부피|S>R~적은 물질로 확보~action|같은 물질량이 늘어나는 것이 아니라 공동을 포함하는 구조다.
5.2.1|필요한 작용에 새 장을 고려|F~missing~추가하려는 F;S~system~시스템||시스템 내부의 장을 재활용|E~system~시스템의 기존 장;F~field~가용 F;S~substance~작용 대상|E>F~재배치~action;F>S~필요 기능~action|기존 기능과 에너지 사용이 충돌하는지 확인한다.
5.2.2|내부에서 사용할 장이 부족함|S~system~시스템 내부||환경에 존재하는 장을 사용|E~environment~환경;F~field~중력·압력·온도차;S~substance~작용 대상|E>F~환경의 가용 장~link;F>S~필요 기능~action|환경의 조건과 설치 위치에 따른 변동을 확인한다.
5.2.3|사용 가능한 장이 없음|F~missing~필요한 장 F||기존 물질이 장을 발생하도록 변환|S~substance~기존 물질·저장 에너지;F~field~생성된 장;R~process~필요 기능|S>F~에너지 변환~action;F>R~작용~action|장 발생의 에너지원과 소모 경로를 명시한다.
5.3.1|현재 상의 성질이 부적합|A~substance~동일 물질의 상 A||상 상태를 바꾸어 기능 확보|A~substance~상 A;B~fluid~상 B|A>B~상태 변화~action|재료 종류를 추가하는 대신 기존 물질의 상을 바꾼다.
5.3.2|조건마다 필요한 상이 다름|A~substance~한 상으로 고정||조건에 따라 상 전환|A~substance~조건 A의 상 A;B~fluid~조건 B의 상 B|A>B~조건 전환~both|가역 운전에는 복귀 조건·히스테리시스 검토가 필요하다.
5.3.3|상 변화만 이용함|S~phase~상 A → 상 B||상전이의 동반 현상을 이용|P~phase~상전이;E~field~잠열·부피·물성 변화;R~process~필요 기능|P>E~동반 현상~action;E>R~기능으로 활용~action|상 자체의 성질과 상전이 과정에서 생기는 현상을 구별한다.
5.3.4|단일 상|A~substance~상 A||두 상을 함께 유지|S~phase~상 A + 상 B 공존||상 비율과 분포를 조절해 서로 다른 성질을 함께 활용한다.
5.3.5|두 상이 단순히 공존|A~phase~상 A + 상 B||상 사이 상호작용을 기능으로 사용|A~substance~상 A;B~fluid~상 B;R~process~계면·상간 기능|A>B~계면 상호작용~both;B>R~반응·전달~action|두 상 사이의 반응·확산·전달 경로에 주목한다.
5.4.1|서로 다른 상태가 반복 필요함|A~substance~상태 A;B~substance~상태 B||가역적인 물리 변환을 이용|A~phase~상태 A;B~phase~상태 B|A>B~정방향·복귀 조건~both|상전이·해리/결합 등 반복 가능한 변환 경로를 검토한다.
5.4.2|작은 제어 입력으로 큰 작용 필요|I~field~작은 입력;R~process~큰 출력 요구||임계 상태의 저장 에너지를 방출|E~energy~저장 에너지;C~critical~임계 상태;I~pulse~작은 제어 입력;R~process~큰 출력|E>C~에너지 공급~action;I>C~임계값 통과~action;C>R~저장 에너지 방출~action|출력 에너지원과 제어 신호를 별개의 노드로 표시한다.
5.5.1|필요 입자의 직접 도입이 어려움|P~missing~필요한 입자||상위 구조를 분해|H~composite~상위 구조의 물질;D~process~분해;P~particles~필요한 입자|H>D~구성 단위 분리~action;D>P~입자 확보~action|더 큰 구조에서 필요한 입자를 얻는다.
5.5.2|필요 입자를 바로 얻을 수 없음|P~missing~필요한 입자||하위 입자를 결합|L~particles~더 작은 구성 단위;C~process~결합·구성;P~composite~필요한 입자|L>C~조합~action;C>P~입자 형성~action|5.5.1의 분해와 반대로 작은 단위에서 구성한다.
5.5.3|목표 구조 수준에 자원이 없음|P~missing~목표 수준 입자||가장 가까운 구조 수준을 먼저 검토|H~composite~인접 상위 구조;P~particles~필요한 입자;L~particles~인접 하위 단위|H>P~분해 경로~action;L>P~결합 경로~action|멀리 떨어진 수준보다 인접 수준의 자원을 우선 검토한다.
'''


def specifications():
    result = {}
    for line in ROWS.strip().splitlines():
        code, before_title, before_nodes, before_edges, after_title, after_nodes, after_edges, note = line.split('|')
        assert code not in result, code
        def graph(title, nodes, edges):
            ns = [dict(zip(('id','kind','label'), item.split('~'))) for item in nodes.split(';')]
            es = []
            for item in filter(None,edges.split(';')):
                pair,label,style = item.split('~')
                source,target = pair.split('>')
                es.append(dict(source=source,target=target,label=label,style=style))
            return dict(title=title,nodes=ns,edges=es)
        result[code] = dict(code=code,before=graph(before_title,before_nodes,before_edges),after=graph(after_title,after_nodes,after_edges),note=note)
    return result
