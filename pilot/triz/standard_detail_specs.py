"""Mechanism graphs for the source-reviewed SIS branches.

Keys after ``variant-`` are editorial positions, never official SIS numbers.
The catalog supplies the titles, premises and sources; these diagrams supply
only explanatory relationships, not observations about a user's design.
"""

# parent--detail | nodes (id~motif~label) | directed relationships
ROWS = '''
1.1.1--variant-1|F~field~새 장 F;S2~substance~새 도구 S2;S1~substance~기존 대상 S1|F>S2~장 도입~action;S2>S1~도구 도입으로 작용 완성~action
1.1.1--variant-2|F~field~새 장 F;S2~substance~기존 도구 S2;S1~substance~기존 대상 S1|F>S2~빠진 장 보충~action;S2>S1~요구 작용 형성~action
1.1.1--variant-3|F~field~기존 장 F;S2~substance~새 도구 S2;S1~substance~기존 대상 S1|F>S2~장과 도구 연결~action;S2>S1~빠진 물질로 작용 경로 완성~action
1.1.3--variant-1|F~field~작용 장;S3~layer~도구 밖 첨가 S3;S2~substance~변경하지 않는 도구 S2;S1~substance~대상 S1|F>S3~외부 첨가물에 작용~action;S3>S2~외부에서 결합~link;S2>S1~작용 개선~action
1.1.3--variant-2|F~field~작용 장;S2~substance~도구 S2;S3~layer~대상 밖 첨가 S3;S1~substance~변경하지 않는 대상 S1|F>S2~작용 제공~action;S2>S3~외부 첨가물을 경유~action;S3>S1~대상 밖에서 작용 개선~action
1.1.5--variant-1|E0~environment~기존 환경;E1~environment~필요 물질을 가진 환경;S~system~물질–장 시스템|E0>E1~환경 교체~action;E1>S~필요 성분으로 작용 개선~action
1.1.5--variant-2|E~environment~기존 환경;D~process~환경 성분 분해;S3~particles~필요 물질;S~system~물질–장 시스템|E>D~환경 자원 이용~action;D>S3~분해로 얻음~action;S3>S~작용 개선~action
1.1.5--variant-3|S3~substance~첨가 물질;E~environment~외부 환경;S~system~물질–장 시스템|S3>E~환경에 첨가~action;E>S~환경을 통한 작용 개선~action
1.1.6--variant-1|F~field~필요보다 큰 장;S1~substance~대상;S3~shield~초과분 흡수 물질|F>S1~필요한 작용 사용~action;F>S3~초과 장 흡수·제거~action
1.1.6--variant-2|S~substance~필요보다 많은 물질;F~field~제거용 장;R~substance~필요량의 물질|F>S~초과 물질 제거~action;S>R~초과분을 덜어 필요량 유지~action
1.1.8--sub-1.1.8.1|F~field~전체 최대 장;S1~substance~최대 작용 영역;S3~shield~차폐 물질;M~substance~최소 작용 영역|F>S1~최대 작용 유지~action;F>S3~국소 차폐~action;S3>M~장 작용 감소~action
1.1.8--sub-1.1.8.2|F~field~전체 최소 장;S3~substance~추가 장 생성 물질;H~substance~최대 작용 영역;M~substance~최소 작용 영역|F>M~최소 작용 유지~action;S3>H~국소 추가 장으로 강화~action;F>H~기본 장 작용~action
1.2.2--variant-1|S1~substance~기존 S1;S3~layer~미리 만든 변형체;S2~substance~기존 S2|S1>S3~기존 물질의 변형체 삽입~link;S3>S2~유해 상호작용 분리~link
1.2.2--variant-2|F~field~기존 또는 추가 장;S~substance~기존 물질;S3~foam~현장 생성 변형체;R~shield~유해 접촉 차단|F>S~기존 물질 변형~action;S>S3~공동·기포·거품 등 생성~action;S3>R~두 물질 사이에 변형체 배치~action
1.2.5--variant-1|I~pulse~기계적 충격;M~magnetic~자화된 물질;R~process~자기 결합 약화|I>M~탈자 유도~action;M>R~잔류 자화 감소 활용~action
1.2.5--variant-2|T~field~퀴리점 초과 가열;M~magnetic~강자성 물질;R~process~강자성 결합 해제|T>M~강자성 성질 상실~action;M>R~자기 작용 약화·제거~action
2.1.1--variant-1|S2~system~기존 요소 S2;S3~substance~내부 물질 S3;F2~field~내부 장 F2;S4~substance~내부 물질 S4|S2>S3~요소를 독립 모델로 확장~action;F2>S3~내부 작용~action;S3>S4~내부 물질–장 관계~action
2.1.1--variant-2|S1~substance~대상 S1;S3~substance~연결 물질 S3;S2~substance~도구 S2;F2~field~추가 제어 장|S1>S3~기존 연결을 분할~link;S3>S2~제어 가능한 연결~link;F2>S3~연결 상태 독립 제어~action
2.1.1--variant-3|M~substance~시스템 내부 질량;C~process~무게중심 이동;G~field~중력;R~system~시스템 회전|M>C~내부 질량 이동~action;C>R~중력에 대한 모멘트 변화~action;G>R~회전 작용~action
2.2.4--variant-1|A~flexible~단일 관절;B~flexible~다수 관절;C~flexible~유연한 도구|A>B~관절 수 증가~action;B>C~연속적인 유연성으로 전이~action
2.2.4--variant-2|F0~field~고정·연속 장;F1~pulse~시간에 따라 변하는 장;S~substance~작용 대상|F0>F1~장 동적화~action;F1>S~변화하는 작용~action
2.2.4--variant-3|P~phase~용융·응고 등 상변화;S~flexible~도구 구조·유연성;R~process~조건별 작용|P>S~물성·형태 변화~action;S>R~작용을 동적으로 조절~action
2.2.5--variant-1|F0~field~균일·무질서한 장;F1~pattern~공간 구조를 가진 장;S~substance~대상|F0>F1~고정 또는 가변 구조 부여~action;F1>S~위치별 다른 작용~action
2.2.5--variant-2|R~pattern~요구되는 물질 구조;F~pattern~대응하는 장 구조;S~pattern~형성되는 물질 구조|R>F~요구 구조에 맞춰 설정~action;F>S~장으로 물질 구조 형성~action
2.2.5--variant-3|W~wave~정상파;N~substance~마디 영역;A~substance~배 영역|W>N~에너지 작용 최소 영역~action;W>A~에너지 작용 최대 영역~action
2.2.5--variant-4|F~pattern~구조화된 장;M~magnetic~자성 결합 영역;N~substance~자성 해제 영역|F>M~필요 위치의 결합 유지~action;F>N~1.2.5로 선택적 결합 해제~action
2.2.6--variant-1|S0~substance~균일·무질서 물질;S1~pattern~공간·시간 구조 물질;R~process~위치·시점별 작용|S0>S1~물질 구조화~action;S1>R~요구 작용 분포 형성~action
2.2.6--variant-2|S~particles~국소 발열 물질;P~pattern~필요 지점·선에 사전 배치;T~gradient~국소 열장|S>P~발열 성분 배치~action;P>T~배치에 대응하는 열 발생~action
2.3.1--variant-1|F~wave~장 주파수 f;S~system~대상 고유 주파수 f;R~process~정합된 유효 작용|F>S~리듬 정합~action;S>R~공진 등 필요한 동조 활용~action
2.3.1--variant-2|F~wave~장 주파수 f1;S~system~대상 고유 주파수 f2;R~process~불필요한 동조 회피|F>S~f1과 f2를 의도적으로 비정합~action;S>R~요구되는 비정합 작용~action
2.3.2--variant-1|F1~wave~첫 장의 주파수;F2~wave~둘째 장의 주파수;S~system~상호작용 시스템|F1>F2~주파수 정합~both;F1>S~정합된 작용~action;F2>S~정합된 작용~action
2.3.2--variant-2|F1~wave~첫 장의 주파수;F2~wave~다른 장의 주파수;S~system~상호작용 시스템|F1>F2~의도적인 주파수 비정합~link;F1>S~비정합을 이용한 작용~action;F2>S~비정합을 이용한 작용~action
2.4.5--variant-1|F~magnet~자기장;S~composite~강자성 첨가물이 든 물질;R~process~제어할 작용|F>S~내부 강자성 성분에 작용~action;S>R~복합 물질 제어~action
2.4.5--variant-2|F~magnet~자기장;A~layer~외부 강자성 첨가물;S~substance~변경하지 않는 물질|F>A~외부 자성 성분에 작용~action;A>S~외부에서 물질 제어~action
2.4.6--variant-1|F~magnet~자기장;E~environment~강자성 입자를 둔 환경;S~substance~내부 변경 없는 대상|F>E~환경 상태 제어~action;E>S~환경을 경유한 작용~action
2.4.6--variant-2|F~field~자기장 또는 전류·전자기장;E~fluid~액체 환경;B~substance~부유체|F>E~겉보기 밀도 조절~action;E>B~부력·부유 상태 제어~action
2.4.6--variant-3|F~field~전기장;E~fluid~전기유변 환경;S~substance~대상|F>E~환경 점도 변화~action;E>S~유변 성질로 작용 제어~action
2.4.9--variant-1|F0~field~균일·무질서한 장;F1~pattern~구조화된 장;S~magnetic~Fe-Field 물질|F0>F1~공간 구조 부여~action;F1>S~위치별 제어 작용~action
2.4.9--variant-2|T~gradient~공간적으로 다른 열장;S~magnetic~자성 물질;R~pattern~위치별 자성 응답|T>S~온도에 따른 자성 변화~action;S>R~필요한 공간 분포 형성~action
2.4.9--variant-3|S0~pattern~요구 물질 구조;F~pattern~대응 장 구조;S1~pattern~형성된 물질 구조|S0>F~요구 구조에 맞춰 장 설정~action;F>S1~장으로 구조 형성~action
2.4.11--variant-1|F~field~외부 전자기장;I~current~접촉·유도 전류;R~process~필요한 작용|F>I~장과 전류의 상호작용~both;I>R~상호작용 활용~action
2.4.11--variant-2|I1~current~첫 전류;I2~current~둘째 전류;R~process~필요한 작용|I1>I2~전류 사이 상호작용~both;I2>R~상호작용 활용~action
3.1.1--variant-1|S1~substance~물질 요소 A;S2~substance~물질 요소 B;E~system~결합 집합·내부 환경|S1>E~물질 요소 결합~action;S2>E~새 특성·환경 형성~action
3.1.1--variant-2|A~system~장·물질–장 단위 A;B~system~장·물질–장 단위 B;P~system~복수 단위 시스템|A>P~단위 결합~action;B>P~바이·폴리 구조 형성~action
3.1.1--variant-3|A~system~첫 작용 단계;B~system~다음 작용 단계;R~process~다단 합성 작용|A>B~단계 사이 작용 전달~action;B>R~연쇄 작용 활용~action
3.1.2--variant-1|A~substance~연결 없는 요소 A;B~substance~연결 없는 요소 B;C~system~연결된 시스템|A>C~연결 도입·강화~action;B>C~새 상호작용 형성~action
3.1.2--variant-2|A~system~강체로 연결된 요소들;B~flexible~동적으로 연결된 요소들|A>B~기존 강체 연결의 동적화~action
3.2.1--variant-1|A~system~거시 수준의 기능;S~particles~미시 수준 물질;F~field~미시 수준 장;R~process~같은 필요 기능|A>S~기능을 미시 수준으로 전이~action;F>S~미시 상호작용~action;S>R~필요 기능 구현~action
3.2.1--variant-2|A~particles~현재 미시 수준;B~particles~더 낮은 미시 수준;R~process~필요 기능|A>B~더 낮은 구조 수준으로 전이~action;B>R~낮은 수준의 작용 활용~action
4.1.2--variant-1|S~substance~실제 대상;C~copy~복제물·사진;M~sensor~측정값|S>C~특성·상태를 대응시킴~action;C>M~대신 측정~action
4.1.2--variant-2|A~copy~대상 영상;B~copy~대비 기준 영상;C~pattern~광학 중첩 영상;R~sensor~차이 검출|A>C~영상 중첩~action;B>C~기준과 대조~action;C>R~차이로 검출·측정~action
4.2.1--variant-1|F~field~입력 장;S~substance~측정 대상;O~wave~변화한 같은 장;M~sensor~검출|F>S~대상과 상호작용~action;S>O~입력 장의 변화~action;O>M~변화량 검출~action
4.2.1--variant-2|F1~field~입력 장 F1;S~substance~측정 대상;F2~wave~다른 출력 장 F2;M~sensor~검출|F1>S~대상 자극~action;S>F2~다른 종류의 장 발생~action;F2>M~출력 장 검출~action
4.2.2--variant-1|S~composite~내부 표지가 든 대상;F~field~검출 가능한 장;M~sensor~측정|S>F~내부 첨가물의 신호~action;F>M~정보 획득~action
4.2.2--variant-2|S~substance~대상;A~layer~외부 표지;F~field~검출 가능한 장;M~sensor~측정|S>A~외부에서 상태 대응~link;A>F~외부 첨가물의 신호~action;F>M~정보 획득~action
4.2.4--variant-1|E~environment~기존 환경;D~process~환경 분해;A~particles~생성된 표지 물질;M~sensor~검출·측정|E>D~환경 자원 이용~action;D>A~검출 물질 생성~action;A>M~생성물의 신호 활용~action
4.2.4--variant-2|E~environment~기존 환경;P~phase~환경 상태 변화;B~foam~기체·증기 기포;M~sensor~검출·측정|E>P~환경의 상태 전이~action;P>B~검출 표지 형성~action;B>M~기포 등의 신호 활용~action
4.3.1--variant-1|A~substance~기존 물질 A;B~substance~기존 물질 B;V~current~열전 신호;M~sensor~상태 측정|A>B~접합·온도 조건~link;B>V~열전 효과~action;V>M~신호로 상태 파악~action
4.3.1--variant-2|S~system~기존 물질–장 시스템;I~current~유도 신호;M~sensor~상태 측정|S>I~유도 효과로 신호 생성~action;I>M~상태와 신호의 대응 이용~action
4.4.2--variant-1|S~substance~기존 물질;P~particles~강자성 미세입자;M~sensor~자기 측정|S>P~한 물질을 입자로 대체~action;P>M~입자의 자기 응답 검출~action
4.4.2--variant-2|P~particles~강자성 미세입자;S~composite~첨가된 기존 물질;M~sensor~자기 측정|P>S~기존 물질에 첨가~action;S>M~첨가 입자의 응답 검출~action
4.5.1--variant-1|A~substance~측정 대상 A;B~substance~측정 대상 B;E~environment~집합의 내부 환경;M~sensor~상태 측정|A>E~대상 집합 구성~action;B>E~집합 내 환경 형성~action;E>M~내부 환경으로 상태 파악~action
4.5.1--variant-2|A~sensor~첫 측정;B~sensor~다른 측정;R~process~측정 사이 관계;M~sensor~필요한 상태량|A>R~측정 결과 비교~action;B>R~신호 간 관계 이용~action;R>M~필요량 산출~action
5.1.1--sub-5.1.1.1|S~missing~도입이 제한된 물질;V~hollow~빈 공간·공동;R~process~필요 기능|S>V~물질 대신 빈 공간 이용~action;V>R~공동의 성질 활용~action
5.1.1--sub-5.1.1.2|S~missing~도입이 제한된 물질;F~field~대체 장;R~process~필요 기능|S>F~물질 역할을 장으로 대체~action;F>R~장 작용으로 수행~action
5.1.1--sub-5.1.1.3|I~missing~내부 첨가 제한;A~layer~외부 첨가물;S~substance~대상|I>A~첨가 위치를 밖으로 이동~action;A>S~외부에서 필요 작용~action
5.1.1--sub-5.1.1.4|A~particles~소량의 고활성 첨가물;S~substance~시스템 물질;R~process~필요 기능|A>S~높은 활성의 소량 물질 첨가~action;S>R~활성을 이용한 작용~action
5.1.1--sub-5.1.1.5|A~particles~소량의 일반 첨가물;L~pattern~필요 위치에 집중;R~process~국소 기능|A>L~공간적으로 국소화~action;L>R~필요 지점에만 작용~action
5.1.1--sub-5.1.1.6|A~substance~일시 도입 물질;T~pulse~필요한 시간 구간;R~process~해당 기간의 기능|A>T~필요 기간에만 투입~action;T>R~시간을 한정해 작용~action
5.1.1--sub-5.1.1.7|S~substance~첨가 금지 실제 대상;C~copy~복제물·모델;A~substance~모델에 넣는 첨가물;R~process~모델을 통한 필요 기능|S>C~실제를 대신할 모델 구성~action;A>C~모델에는 첨가 허용~action;C>R~대응 관계 이용~action
5.1.1--sub-5.1.1.8|C~composite~도입 가능한 화합물;D~process~도입 후 방출;A~substance~필요 첨가물;R~process~필요 기능|C>D~화합물 형태로 먼저 도입~action;D>A~필요 물질을 나중에 꺼냄~action;A>R~방출 후 작용~action
5.1.1--sub-5.1.1.9|S~environment~기존 대상·환경 물질;D~phase~분해·상변화;A~substance~필요 첨가물;R~process~필요 기능|S>D~기존 자원 변환~action;D>A~현장에서 물질 생성~action;A>R~생성 물질 활용~action
5.1.2--variant-1|A~particles~분할한 흐름 A의 전하;B~particles~분할한 흐름 B의 전하;R~process~입자 흐름 제어|A>B~같은 부호의 반발·다른 부호의 인력~both;B>R~부분 사이 상호작용 활용~action
5.1.2--variant-2|A~particles~같은 부호로 대전한 전체 흐름;B~substance~반대 전하를 가진 부분;R~process~입자 흐름 제어|A>B~반대 전하 사이 상호작용~both;B>R~흐름에 필요한 작용~action
5.1.3--variant-1|A~substance~일시 첨가물;F~process~필요 기능 수행;N~process~작용 후 소멸|A>F~첨가물을 사용~action;F>N~작용 종료 후 소멸~action
5.1.3--variant-2|A~substance~일시 첨가물;F~process~필요 기능 수행;S~substance~기존 물질과 구별되지 않는 상태|A>F~첨가물을 사용~action;F>S~작용 후 기존 물질로 동화~action
5.1.4--variant-1|S~missing~도입 제한된 대량 물질;V~hollow~팽창식 빈 공간 구조;R~process~물질을 대신하는 기능|S>V~거시 수준 팽창 구조로 대체~action;V>R~필요 부피·역할 확보~action
5.1.4--variant-2|S~missing~도입 제한된 대량 물질;V~foam~거품의 미세 빈 공간;R~process~물질을 대신하는 기능|S>V~미시 수준의 거품으로 대체~action;V>R~분산된 공동 활용~action
5.2.3--variant-1|S~substance~기존 시스템·환경 물질;F~field~겸용 물질이 운반·발생하는 장;R~process~필요 기능|S>F~장 운반체·발생원 역할 겸용~action;F>R~필요한 장 작용~action
5.2.3--variant-2|S~magnetic~기계적 역할의 기존 강자성 물질;F~field~추가 활용하는 자기 작용;R~process~새 작용·상태 정보|S>F~기존 물질의 자성 겸용~action;F>R~자기 상호작용·정보 활용~action
5.3.5--variant-1|A~phase~기존 두 상 중 A;B~phase~기존 두 상 중 B;R~process~향상된 유익 작용|A>B~부분·상 사이 물리적 상호작용~both;B>R~공존에 상호작용을 추가~action
5.3.5--variant-2|A~phase~기존 두 상 중 A;B~phase~기존 두 상 중 B;R~process~향상된 유익 작용|A>B~부분·상 사이 화학적 상호작용~both;B>R~공존에 상호작용을 추가~action
5.4.1--variant-1|A~substance~상 A;B~fluid~상 B|A>B~조건 변화에 따른 가역 상전이~both
5.4.1--variant-2|A~substance~중성 상태;B~particles~이온화 상태|A>B~이온화–재결합의 반복~both
5.4.1--variant-3|A~composite~회합 상태;B~particles~해리 상태|A>B~해리–회합의 반복~both
5.5.3--variant-1|H~composite~인접 상위의 완전·과잉 구조;D~process~분해;P~particles~필요 입자|H>D~5.5.1 경로: 구조 분해~action;D>P~필요한 구성 단위 확보~action
5.5.3--variant-2|L~particles~인접 하위의 미완결 구조;C~process~보완 구성·결합;P~composite~필요 입자|L>C~5.5.2 경로: 구성 보완~action;C>P~필요 입자 완성~action
'''


def detail_specifications():
    result = {}
    for row in ROWS.strip().splitlines():
        key, node_text, edge_text = row.split('|')
        assert key not in result, key
        nodes = [dict(zip(('id', 'kind', 'label'), part.split('~')))
                 for part in node_text.split(';')]
        edges = []
        for part in filter(None, edge_text.split(';')):
            pair, label, style = part.split('~')
            source, target = pair.split('>')
            edges.append(dict(source=source, target=target, label=label, style=style))
        result[key] = dict(nodes=nodes, edges=edges)
    return result
