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
1.1.7|필요한 최대 작용을 직접 가할 수 없음|F~field~F 최대 작용;S1~substance~S1 대상|F>S1~직접 작용 불허~harmful|연결된 다른 물질로 작용을 돌림|F~field~F 최대 작용;S2~substance~S2 연결 물질;S1~substance~S1 대상|F>S2~최대 작용 유지~action;S2>S1~필요 결과 전달~action|최대 작용이 필요하다는 전제다. 단순한 과잉 작용 억제와 구별한다.
1.1.8|영역별 요구 강도가 다름|F~field~F 균일한 장;S1~pattern~S1 서로 다른 영역|F>S1~일률적 작용~harmful|국부 보호 또는 국부 증강|A~shield~강한 F + 보호층;B~pattern~선택 영역만 작용;C~field~약한 F + 국부 증강|A>B~보호 방식~action;C>B~증강 방식~action|두 경로는 대안이다. 모든 영역에 같은 강도를 가하지 않는다.
1.2.1|직접 접촉에 유해 작용|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~유해 접촉~harmful|제3의 물질로 접촉 분리|S2~substance~S2 도구;S3~layer~S3 중간 물질;S1~substance~S1 대상|S2>S3~접촉~link;S3>S1~유익 작용 유지~action|새 중간 물질이 유해한 직접 접촉을 차단한다.
1.2.2|외부 물질 도입이 제한됨|S2~substance~S2 기존 물질;S1~substance~S1 대상|S2>S1~유해 접촉~harmful|기존 물질에서 차단층 생성|S2~substance~S2 기존 물질;S3~layer~S3 = 변형된 S1·S2;S1~substance~S1 대상|S2>S3~기존 재료의 변형~action;S3>S1~유해 접촉 완화~action|S3의 기원이 기존 물질이라는 점이 1.2.1과 다르다.
1.2.3|유해한 장이 대상을 공격|F~field~F 유해 장;S1~substance~S1 대상|F>S1~유해 작용~harmful|보호 물질이 유해 장을 대신 받음|F~field~F 유해 장;S2~shield~S2 보호·희생 물질;S1~substance~S1 보호 대상|F>S2~흡수·완충~action|보호 물질 뒤에 유해 작용 화살표를 임의로 이어 그리지 않는다.
1.2.4|직접 접촉을 유지해야 함|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~유익 + 유해 작용~harmful|두 물질과 유익 작용 유지·제2장 추가|F1~field~F1 기존 장;S2~substance~S2 도구;S1~substance~S1 대상;F2~field~F2 추가 장|F1>S2~기존 작용 공급~action;S2>S1~직접 접촉·유익 작용 유지~action;F2>S1~유해 작용 중화·유익 전환~action|S1·S2의 직접 접촉을 유지한다. S3 분리층을 삽입하는 방식이 아니다.
1.2.5|강자성에 의한 유해 결합|F~magnet~자기장;S1~magnetic~강자성 물질|F>S1~유해한 결합~harmful|강자성 성질 변화로 결합 해제|P~process~가열·물리적 효과;S1~substance~자성 변화 물질;R~process~유해 결합 해제|P>S1~자기 특성 변화~action;S1>R~결합 약화~action|퀴리점 등 물성 변화를 이용하며 단순 역자장과 구별한다.
2.1.1|하나의 물질–장 작용|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~F1 작용~action|공유 물질을 통한 연쇄 작용|S3~substance~S3 새 도구;S2~substance~S2 공유 물질;S1~substance~S1 대상|S3>S2~F2 독립 제어~action;S2>S1~F1 작용~action|S2 자체를 별도의 물질–장 시스템으로 발전시킨 예다.
2.1.2|한 장의 작용이 부족함|F1~field~F1;S1~substance~기존 S1·S2|F1>S1~부족한 작용~harmful|같은 물질 쌍에 두 장 적용|F1~field~F1 기존 장;S1~substance~기존 S1·S2;F2~field~F2 추가 장|F1>S1~기존 작용~action;F2>S1~보강 작용~action|물질을 교체하지 않고 추가 장의 작용을 결합한다.
2.2.1|현재 장의 제어가 어려움|F~field~제어가 어려운 F;S1~substance~S1 대상|F>S1~불안정한 작용~harmful|제어성이 높은 장으로 교체|F~pulse~조절 가능한 F′;S1~substance~S1 대상|F>S1~정밀한 작용~action|보편적인 장의 우열이 아니라 해당 조건의 제어성을 비교한다.
2.2.2|일체형 도구 물질|S2~substance~S2 도구;S1~substance~S1 대상|S2>S1~도구의 작용~action|도구 물질의 분할도 증가|S2~particles~분할된 S2 도구;S1~substance~S1 대상|S2>S1~분산된 도구의 작용~action|도구 역할 물질 또는 대상과 직접 작용하는 도구 부분을 잘게 나눈다.
2.2.3|공동이 없는 고체|S~substance~일체 고체||기공 구조의 발전|A~hollow~공동;B~porous~다공질;C~capillary~구조화된 모세관|A>B~다수 기공~action;B>C~배열·크기 제어~action|기공 속 유체와 모세관 작용도 활용할 수 있다.
2.2.4|고정 구조와 일정한 작용|S~substance~고정된 S;F~field~일정한 F||운전 중 변화하는 시스템|S~flexible~관절·유연한 S;F~pulse~가변·맥동 F|F>S~조건에 맞춰 조절~action|물질 구조 또는 장을 동적화하는 두 방향을 표시한다.
2.2.5|균일한 작용장|F~field~균일 F||장의 분포를 구조화|F1~gradient~공간 구배 F;F2~pulse~시간 패턴 F||공간과 시간의 패턴은 선택하거나 결합할 수 있다.
2.2.6|균질한 물질|S~substance~균질 S||물질의 성질을 구조화|S1~pattern~위치별 물성 S;S2~phase~상태가 변하는 S||장 자체를 바꾸는 2.2.5와 달리 물질의 분포·상태를 바꾼다.
2.3.1|장과 물질의 주파수 관계를 조절해야 함|F~wave~F 작용 주파수;S~wave~대상·도구 고유 주파수|F>S~현재 주파수 관계~link|정합 또는 의도적 비정합|F~wave~조절한 F 주파수;S~wave~대상·도구 고유 주파수|F>S~목적에 맞게 정합·비정합 선택~both|불일치가 항상 유해한 것은 아니다. 동조가 필요한 경우와 반공진이 필요한 경우를 구별한다.
2.3.2|복수 장의 주파수 관계를 조절해야 함|F1~wave~F1 주파수;F2~pulse~F2 주파수|F1>F2~현재 장 사이 관계~link|장 사이 정합 또는 의도적 비정합|F1~wave~조절한 F1 주파수;F2~wave~조절한 F2 주파수|F1>F2~정합·의도적 비정합~both|장–물질의 고유 주파수 관계가 아니라 사용되는 여러 장 사이의 주파수 관계다.
2.3.3|동시 작용이 서로 방해함|A~process~작용 A;B~process~작용 B|A>B~동시 수행 충돌~harmful|휴지기에 다른 작용 배치|A1~pulse~A 수행;B~pulse~A 휴지기에 B;A2~pulse~A 재개|A1>B~시간 순서~action;B>A2~시간 순서~action|예: 가공이 멈춘 사이 측정. 화살표는 시간 진행이다.
2.4.1|일반적인 작용계|F~field~일반 F;S~substance~일반 물질|F>S~작용~action|덩어리 강자성체로 자기 제어|F~magnet~자기장;S~magnetic~덩어리 강자성체|F>S~자기력 제어~action|아직 입자화하지 않은 Proto-Fe-Field 단계다.
2.4.2|제어 효율을 높이려는 기존 시스템|F~field~기존 장;S~substance~기존 물질|F>S~기존 작용~action|강자성 입자의 교체·첨가와 자기 제어|F~magnet~자기·전자기장;S~particles~강자성 입자|F>S~입자 분포·운동 제어~action|기존 물질을 자성 입자로 바꾸거나 입자를 첨가한다. 출발 물질이 이미 강자성이어야 하는 것은 아니다.
2.4.3|자성 입자의 집합|S~particles~미세 자성 입자||유체 속 안정적인 콜로이드 분산|F~magnet~자기장;S~fluid~콜로이드 자성유체|F>S~유체 형상·이동 제어~action|액체 담체 속 안정 분산을 표현한다. MR 유체와 혼동하지 않는다.
2.4.4|모세관·기공을 가진 Fe-Field|F~magnet~자기장;S~porous~기공이 있는 자성계|F>S~기존 자기 작용~action|기존 기공 구조의 기능 활용|F~magnet~자기장;S~porous~자성계의 기공;L~fluid~기공 속 유체|F>S~자기 제어~action;S>L~모세관 보유·전달~link|많은 Fe-Field가 이미 가진 다공질 구조를 활용한다. 기공이 없어야 한다는 전제는 없다.
2.4.5|주재료를 자성 입자로 바꿀 수 없음|S~substance~유지해야 할 주재료||자성 첨가물을 가진 복합체|F~magnet~자기장;S~composite~주재료 + 자성 첨가물|F>S~복합체 제어~action|주재료를 유지한 내부·외부 복합 Fe-Field다.
2.4.6|대상에 자성 첨가를 할 수 없음|S~substance~변경 금지 대상||주변 자성 매질을 통해 제어|F~magnet~자기장;E~fluid~자성 입자 환경;S~substance~원래 대상|F>E~환경 제어~action;E>S~작용 전달~action|대상과 자성 입자 환경을 별개의 요소로 표시한다.
2.4.7|자기 특성이 고정됨|S~magnetic~고정 자기 특성||물리 상태를 바꾸어 자기 작용 제어|P~process~온도·응력 변화;S~magnetic~자기 특성 변화;R~process~작용 변화|P>S~물리효과~action;S>R~자기 제어~action|물리 상태 → 자기 물성 → 작용의 인과 경로다.
2.4.8|고정된 자기 시스템|F~magnet~일정 자기장;S~magnetic~고정 자성 구조|F>S~고정 작용~action|가변적인 자기 시스템|F~pulse~가변 자기장;S~flexible~유연·가변 자성 구조|F>S~운전 중 조정~action|자기 구동과 구성요소의 동적화를 표시한다.
2.4.9|균일하거나 무질서한 장의 Fe-Field|F~field~구조화되지 않은 장;S2~particles~강자성 입자계|F>S2~기존 작용~action|장을 구조화하여 위치별 작용 제어|F~gradient~공간 구조를 가진 장;S2~particles~강자성 입자계;S1~pattern~요구 구조의 대상|F>S2~위치별 장 작용~action;S2>S1~필요한 물질 구조 형성~action|일반형은 장의 구조화다. 구조화된 열장으로 자성을 달리하거나 장에 맞춰 물질 구조를 만드는 분기도 있다.
2.4.10|자기 구동과 응답 주기 불일치|F~magnet~자기 구동;S~wave~구성요소 응답|F>S~주기 불일치~harmful|자기계의 리듬 정합|F~wave~자기 구동 주기;S~wave~자성계 응답 주기|F>S~리듬 정합~both|자기장 또는 구성요소의 주기를 조정한다.
2.4.11|강자성체 도입·자화가 어려움|S~missing~사용하기 어려운 강자성체||전류 기반 작용의 두 대안|F~magnet~외부 전자기장;I~current~접촉 공급·유도 전류;J~current~다른 전류|F>I~대안 1: 외부 장과 전류~both;I>J~대안 2: 전류끼리 상호작용~both|두 경로는 대안이다. 전류×전류도 포함하며 단순 정전기장만을 뜻하지 않는다.
2.4.12|자성유체를 적용할 수 없음|S~missing~사용할 수 없는 자성유체||전기장으로 유동 특성 변화|F~field~인가 전기장;S~chains~입자 사슬 형성;R~process~항복·유동 특성 변화|F>S~입자 배열~action;S>R~유변 특성 제어~action|자성유체를 사용할 수 없을 때 전기유변 현탁액을 검토한다. 그림은 ER 현탁액의 전기장 반응을 설명한다.
3.1.1|단일 시스템|A~system~시스템 A||둘 또는 여럿을 결합|A~system~시스템 A;B~system~시스템 B;C~system~시스템 C|A>B~기능 결합~link;B>C~확장~link|개별 시스템의 결합으로 새로운 기능을 얻는다.
3.1.2|결합 시스템의 현재 연결 상태|A~system~연결 없는 집합;B~system~강체로 연결된 집합||현재 상태에 따라 선택하는 두 경로|A0~segmented~연결 없는 집합;A1~system~유효한 연결;B0~system~강체 연결;B1~flexible~동적인 연결|A0>A1~대안 1: 연결 도입·강화~action;B0>B1~대안 2: 기존 연결 동적화~action|무연결 집합은 연결을 강화한다. 이미 강체 연결이면 동적성을 높인다. 두 갈래를 하나의 필수 순서로 잇지 않는다.
3.1.3|같은 성질의 요소들|A~system~동일 요소 A;B~system~동일 요소 A|A>B~결합~link|성질 차이의 확대|A~system~특성이 다른 요소;B~pattern~이종 요소;C~system~상반 성질 요소|A>B~차이 확대~action;B>C~차이 확대~action|비슷한 요소의 집합에서 이종·반대 성질의 조합으로 발전한다.
3.1.4|바이·폴리 시스템의 보조 부분|A~system~시스템 A;B~system~시스템 B|A>B~결합된 시스템~link|보조 부분 우선 축약·공유|C~composite~공유된 보조 부분;R~system~축약된 단일 시스템|C>R~완전 축약 시 단일화~action|보조 부분을 우선 줄인다. 완전히 축약된 뒤 새 수준에서 결합·축약 주기를 반복할 수 있다.
3.1.5|전체와 부분에 다른 요구|P~substance~부분은 A;W~system~전체도 A|P>W~동일 성질~link|전체와 부분에 상반 성질 배치|P~segmented~부분은 A;W~flexible~전체는 반대 A|P>W~배치·연결로 구성~link|예: 단단한 개별 요소를 유연한 전체로 연결한다.
3.2.1|거시적 부품이 기능 수행|M~system~거시적 기구||미시 구조가 기능 수행|S~particles~분자·미시 구조;F~field~미시적 작용;R~process~필요 기능|S>F~구조·물성~link;F>R~기능 구현~action|단순 소형화가 아니라 기능을 수행하는 구조 수준을 바꾼다.
4.1.1|검출·측정이 필요한 시스템|S~system~기존 시스템;M~sensor~필요한 검출·측정|S>M~정보가 필요함~action|시스템 변경으로 측정 필요 제거|S~system~변경된 시스템;R~process~원래 필요한 기능|S>R~측정 없이 필요한 결과~action|검출·측정 문제에서 우선 검토하는 우회 경로다. 자기 조절만으로 한정하지 않는다.
4.1.2|4.1.1로 측정 필요를 없앨 수 없음|S~substance~실물 대상;M~sensor~필요한 검출·측정|S>M~정보가 필요함~action|복제물 또는 영상을 측정|S~substance~실물 대상;C~copy~대응 영상·복제물;M~sensor~측정기|S>C~대응 관계~link;C>M~간접 측정~action|4.1.1을 적용할 수 없을 때 검토한다. 복제물·영상과 실제 대상 사이의 대응 관계를 이용한다.
4.1.3|측정 제거·복제 측정을 적용할 수 없음|S~substance~측정 대상;M~sensor~요구 정밀도|S>M~측정 필요~action|두 상태의 순차 검출과 전이 계수|A~sensor~상태 A 검출;B~sensor~상태 B 검출;N~process~전이 횟수 계수;R~sensor~측정량 산출|A>B~정밀도 단위의 상태 전이~action;B>N~전이 검출~action;N>R~횟수로 측정~action|4.1.1과 4.1.2가 불가할 때의 대안이다. 단순한 연속 파형 관찰이나 4.5.2의 미분 측정과 구별한다.
4.2.1|관측 가능한 출력 장이 없음|S~substance~관측 대상||입력 작용을 검출 가능한 출력으로 변환|F~field~입력 작용;S~substance~측정 대상;O~sensor~검출 가능한 F출력|F>S~여기·작용~action;S>O~측정 신호~action|대상의 상태와 연결되는 출력 장을 형성한다.
4.2.2|시스템·부분의 검출이 어려움|S~substance~검출할 대상||내부·외부 검출 첨가물을 사용|S~composite~대상 + 내부·외부 표지;F~field~관측 가능한 출력 장;M~sensor~검출기|S>F~첨가물의 신호~action;F>M~검출·측정~action|내부 첨가와 외부 결합이 모두 가능하다. 외부 환경에 표지를 넣는 4.2.3과 구별한다.
4.2.3|대상에 표지를 넣을 수 없음|S~substance~변경 금지 대상||환경에 표지를 넣고 변화 관측|S~substance~원래 대상;E~environment~표지 S3가 있는 환경;M~sensor~검출기|S>E~대상·환경 상호작용~both;E>M~환경 신호~action|측정 신호가 환경의 표지에서 나온다.
4.2.4|환경에 새 표지도 넣을 수 없음|E~environment~기존 환경||환경 자원에서 표지를 생성|E~environment~환경 자원;S3~particles~현장에서 생성한 표지;M~sensor~검출기|E>S3~분해·상태 변화~action;S3>M~생성 표지 검출~action|표지의 공급원이 기존 환경이라는 점을 표시한다.
4.3.1|측정 신호가 약함|S~substance~측정할 상태;M~sensor~검출기|S>M~신호 부족~harmful|물리효과로 상태를 신호로 변환|S~substance~측정할 상태;P~process~선택한 물리효과;M~sensor~변환 신호 검출|S>P~상태 변화~action;P>M~신호 변화~action|효과의 작동 조건과 검출 가능한 변화량을 확인한다.
4.3.2|직접 측정·장 통과 방법을 모두 쓸 수 없음|S~substance~대상 상태||대상 자체의 공진 변화를 측정|F~wave~여기 주파수;S~wave~대상 자체의 공진;M~sensor~공진 변화 측정|F>S~진동 여기~action;S>M~공진 특성~action|보조 물체가 아니라 대상 또는 그 일부가 공진한다. 직접 측정과 장 통과 방법이 모두 불가하다는 전제를 유지한다.
4.3.3|대상 자체의 공진을 쓰기 어려움|S~substance~원래 대상||결합한 보조 물체의 공진 활용|S~substance~원래 대상;A~wave~결합된 보조 물체;M~sensor~공진 변화 측정|S>A~상태 전달~link;A>M~보조체 공진~action|보조체와 대상의 결합이 측정할 상태를 전달해야 한다.
4.4.1|비자기적 측정|S~substance~비자기적 물질;M~sensor~기존 측정기|S>M~기존 신호~action|자성체와 자기장으로 측정|F~magnet~자기장;S~magnetic~덩어리 자성 물질;M~sensor~자기 신호 검출|F>S~자기 작용~action;S>M~출력 변화~action|기계적 제어용 2.4.1과 달리 출력은 측정 신호다.
4.4.2|일반 물질 또는 덩어리 자성체|S~magnetic~측정 대상||자성 입자를 이용한 측정|S~particles~자성 입자;F~magnet~입자에 따른 자기 신호;M~sensor~검출기|S>F~분포·상태 반영~action;F>M~측정~action|입자화하거나 자성 입자를 도입해 검출성을 높인다.
4.4.3|주재료 교체가 제한됨|S~substance~유지해야 할 주재료||자성 첨가물의 신호 측정|S~composite~주재료 + 자성 첨가물;F~magnet~자기 출력;M~sensor~검출기|S>F~상태 반영~action;F>M~복합체 측정~action|주재료를 유지한 복합 자기 측정 모델이다.
4.4.4|대상에 자성 입자 첨가가 제한됨|S~substance~변경 금지 대상||자성 환경을 통해 상태 측정|S~substance~원래 대상;E~fluid~자성 입자 환경;M~sensor~자기 출력 검출|S>E~상태 전달~link;E>M~환경 자기 신호~action|대상이 아니라 환경의 자기 반응을 측정한다.
4.4.5|자기 신호 변화가 부족함|S~magnetic~자기 측정계||상태에 따른 자기 물성 변화를 검출|P~process~온도·응력 등 상태;S~magnetic~자기 물성 변화;M~sensor~변화 신호 검출|P>S~자기 물리효과~action;S>M~측정 신호~action|예: 퀴리점·자기탄성 등. 효과별 조건을 따로 검토한다.
4.5.1|측정 시스템의 결합을 검토|M~sensor~측정 시스템||측정 바이·폴리 시스템|M1~sensor~대상 집합·측정계 A;R~process~내부 환경·신호 관계;M2~sensor~대상 집합·측정계 B|M1>R~결합된 측정 정보~action;M2>R~관계 활용~action|어느 발전 단계에서도 검토한다. 대상 집합의 내부 환경 또는 복수 측정 신호의 관계를 활용할 수 있다.
4.5.2|함수값 자체를 측정|X~sensor~함수값 f(x)||1차·2차 도함수 측정으로 발전|X~sensor~함수값 f(x);V~wave~1차 도함수 f′(x);A~wave~2차 도함수 f″(x)|X>V~1차 도함수 측정~action;V>A~2차 도함수 측정~action|함수값 → 1차 → 2차 도함수의 발전 방향이다. 독립변수를 시간으로만 제한하지 않는다.
5.1.1|물질 도입이 필요하나 허용되지 않음|S3~missing~필요한 추가 물질;S~system~시스템|S3>S~문제·운전 조건의 제약~harmful|대표 대안 기전 · 아홉 공식 방법은 상세도 참조|V~hollow~빈 공간·공동;F~field~대체 장;E~environment~기존 물질·환경;R~process~필요 기능|V>R~5.1.1.1: 공동으로 대체~action;F>R~5.1.1.2: 장으로 대체~action;E>R~5.1.1.9: 현장 생성~action|이 개요는 세 대표 경로를 보인다. 공식 5.1.1.1~5.1.1.9의 모든 방법은 별도 상세 개념도로 제공하며 각 방법은 대안이다.
5.1.2|변경이 어렵고 도구 교체·첨가가 허용되지 않음|S1~substance~기존 대상 S1||대상의 일부가 다른 일부에 작용|A~segmented~S1a 대상의 일부;B~segmented~S1b 대상의 다른 일부|A>B~상호작용~both|S1을 나누어 물질–장 관계를 만든다. 기존 도구가 반드시 없어야 한다는 전제는 없다.
5.1.3|첨가물의 영구 잔류가 문제|S3~substance~남아 있는 S3||기능 수행 뒤 제거 또는 동화|S3~substance~일시적 S3;A~process~필요 기능 수행;R~process~제거·원래 물질과 동화|S3>A~사용~action;A>R~작용 종료 후~action|소멸을 가정하지 않고 실제 제거·변환 경로를 지정한다.
5.1.4|필요한 대량 물질 도입이 제한됨|S~missing~도입할 수 없는 대량 물질||거시·미시의 빈 공간 활용|A~hollow~거시: 팽창식 구조;B~foam~미시: 거품||두 크기 수준의 대안이다. 빈 공간으로 물질의 역할을 대신하며 물질량 자체가 증가하는 것은 아니다.
5.2.1|필요한 작용에 새 장을 고려|F~missing~추가하려는 F;S~system~시스템||시스템 내부의 장을 재활용|E~system~시스템의 기존 장;F~field~가용 F;S~substance~작용 대상|E>F~재배치~action;F>S~필요 기능~action|기존 기능과 에너지 사용이 충돌하는지 확인한다.
5.2.2|내부에서 사용할 장이 부족함|S~system~시스템 내부||환경에 존재하는 장을 사용|E~environment~환경;F~field~중력·압력·온도차;S~substance~작용 대상|E>F~환경의 가용 장~link;F>S~필요 기능~action|환경의 조건과 설치 위치에 따른 변동을 확인한다.
5.2.3|내부·환경의 기존 장을 직접 쓸 수 없음|F~missing~필요한 장 F||기존 물질이 장 운반·발생 역할 겸용|S~substance~시스템·환경의 기존 물질;F~field~운반·발생한 장;R~process~필요 기능|S>F~장 운반체·발생원 겸용~action;F>R~필요 작용~action|5.2.1과 5.2.2가 모두 불가할 때 검토한다. 기존 강자성 물질의 자성을 활용하는 분기도 있다.
5.3.1|현재 상의 성질이 부적합|A~substance~동일 물질의 상 A||상 상태를 바꾸어 기능 확보|A~substance~상 A;B~fluid~상 B|A>B~상태 변화~action|재료 종류를 추가하는 대신 기존 물질의 상을 바꾼다.
5.3.2|조건마다 필요한 상이 다름|A~substance~한 상으로 고정||조건에 따라 상 전환|A~substance~조건 A의 상 A;B~fluid~조건 B의 상 B|A>B~조건 전환~both|가역 운전에는 복귀 조건·히스테리시스 검토가 필요하다.
5.3.3|상 변화만 이용함|S~phase~상 A → 상 B||상전이의 동반 현상을 이용|P~phase~상전이;E~field~잠열·부피·물성 변화;R~process~필요 기능|P>E~동반 현상~action;E>R~기능으로 활용~action|상 자체의 성질과 상전이 과정에서 생기는 현상을 구별한다.
5.3.4|단일 상|A~substance~상 A||두 상을 함께 유지|S~phase~상 A + 상 B 공존||상 비율과 분포를 조절해 서로 다른 성질을 함께 활용한다.
5.3.5|5.3.4로 얻은 두 상 시스템|A~phase~상 A;B~phase~상 B|A>B~두 상 공존~link|상·부분 사이 물리적 또는 화학적 작용|A~phase~상 A·부분 A;B~phase~상 B·부분 B;R~process~향상된 유익 작용|A>B~물리적 또는 화학적 상호작용~both;B>R~상호작용 효과 활용~action|5.3.4 이후의 보강이다. 물리·화학 작용은 대안이며 단순 공존 자체와 구별한다.
5.4.1|서로 다른 상태가 반복 필요함|A~substance~상태 A;B~substance~상태 B||가역적인 물리 변환을 이용|A~phase~상태 A;B~phase~상태 B|A>B~정방향·복귀 조건~both|상전이·해리/결합 등 반복 가능한 변환 경로를 검토한다.
5.4.2|작은 제어 입력으로 큰 작용 필요|I~field~작은 입력;R~process~큰 출력 요구||임계 상태의 저장 에너지를 방출|E~energy~저장 에너지;C~critical~임계 상태;I~pulse~작은 제어 입력;R~process~큰 출력|E>C~에너지 공급~action;I>C~임계값 통과~action;C>R~저장 에너지 방출~action|출력 에너지원과 제어 신호를 별개의 노드로 표시한다.
5.5.1|필요 입자의 직접 도입이 어려움|P~missing~필요한 입자||상위 구조를 분해|H~composite~상위 구조의 물질;D~process~분해;P~particles~필요한 입자|H>D~구성 단위 분리~action;D>P~입자 확보~action|더 큰 구조에서 필요한 입자를 얻는다.
5.5.2|직접 획득·상위 구조 분해가 모두 불가|P~missing~필요한 입자||하위 구조에서 보완 구성·결합|L~particles~하위 수준 입자;C~process~보완 구성·결합;P~composite~필요한 입자|L>C~부족한 구성 보완·결합~action;C>P~필요 입자 획득~action|직접 획득과 5.5.1이 불가할 때의 대안이다. 단순 소형 부품 조립으로만 한정하지 않는다.
5.5.3|5.5.1 또는 5.5.2의 경로 선택|P~missing~필요 입자||인접한 온전한·과잉·미완결 구조 활용|H~composite~인접 상위 온전한·과잉 구조;P~particles~필요 입자;L~particles~인접 하위 미완결 구조|H>P~5.5.1: 분해~action;L>P~5.5.2: 보완 구성~action|분해와 구성은 대안이다. 인접 상위의 과잉 구조와 인접 하위의 미완결 구조를 빠뜨리지 않는다.
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
