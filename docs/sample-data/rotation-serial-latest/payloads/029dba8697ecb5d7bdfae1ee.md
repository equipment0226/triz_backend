# 저장 데이터 · 029dba8697ec

정규 JSON SHA-256: `029dba8697ecb5d7bdfae1eeb4b0382e45daac00303277be8ecad1d0ff194e61`

```json
[
  {
    "conditions": [
      "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
      "온도·부가 질량·감쇠·지지 조건을 분리해야 하며, 한 주파수로 질량과 강성을 동시에 결정할 수 없다. 액체 점성·점탄성 보정이 필요하고, 회전축·베어링·클램프 계면 고유진동수는 미확인이다."
    ],
    "id": "app-2a36c685ffca28978ff08dde",
    "mechanism": "질량·강성·경계조건이 고유 진동수와 모드를 바꾸므로 기준 상태와 비교해 부착 질량·물성을 추정한다. 수정진동자 미량저울은 그 구현이다.",
    "reason": "정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음",
    "required_function": "상태·성분을 측정하거나 검출한다",
    "source_effect_id": "12.56",
    "sources": [
      {
        "identifier": "REF-manual-final-mechanical-resonance-property-sensing",
        "retrieval_scope": "reference_section",
        "source_type": "REFERENCE",
        "title": "Identification of Corrosion on a Hollow Tube Using Vibration",
        "url": "https://www.scientific.net/AMM.564.176"
      },
      {
        "identifier": "AR-093594-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "문헌·중복 검토 후 연결: mechanical-resonance-property-sensing; 구조물의 고유 진동수와 모드 응답은 질량·강성·경계조건에 의존한다. 기준 상태와의 변화를 비교해 물성이나 구조 손상을 추정할 수 있다. 온도·유체 부가 질량·감쇠·지지 조건을 분리해야 한다. 주파수 하나만으로 질량과 강성을 모두 식별할 수 없다. 수정 미량저울을 포함하는 상위 계측 원리이며 추정 알고리즘과 구분한다.",
        "source_fingerprint": "1dc953fe65a23703a4259938c6d0b88f8980c5b66be856c22308e89d8b803ab6",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Deteccion mejorada de un cambio en el area transversal de un tubo de fluido en un medidor vibrante",
        "url": "https://patents.google.com/patent/AR093594A1/en"
      },
      {
        "identifier": "REF-qcm",
        "retrieval_scope": "reference_section",
        "source_type": "REFERENCE",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Stambaugh et al. · Linking mass measured by the quartz crystal microbalance to the SI",
        "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=927952"
      }
    ],
    "status": "UNKNOWN",
    "validation_obligations": [
      "운전 범위와 자원 충족 확인",
      "효과와 후보 기구 연결 확인"
    ]
  },
  {
    "conditions": [
      "지연 추정·모형 불일치·교란·불안정 플랜트·필터 영향을 확인한다.",
      "지연 추정·모형 불일치·교란·불안정 플랜트·필터 영향을 확인해야 한다. 가감속 프로파일 파라미터(가속 시간, 최고 각속도, 정착 시간)는 미확인이다."
    ],
    "id": "app-df929af67e300a245deb9d61",
    "mechanism": "지연을 분리한 내부 모형의 응답으로 제어하고 실제 지연 출력과 모형 출력의 차이로 예측을 보정한다.",
    "reason": "정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음",
    "required_function": "정보를 전달·추정하거나 시스템을 제어한다",
    "source_effect_id": "19.160",
    "sources": [
      {
        "accessed_at": "2026-09-26",
        "identifier": "REF-research-20260926-smith-delay-free-model-prediction-feedback",
        "retrieval_scope": "stored_search_excerpt",
        "review_method": "conversation_reasoning",
        "source_type": "REFERENCE",
        "supports": "공개 문헌의 원리·조건을 대화에서 검토한 참고 근거. 초록·검색 발췌 범위는 원문 전체 검증과 구분하며 개별 응용의 성능을 보장하지 않는다.",
        "title": "MathWorks · Control of Processes with Long Dead Time: The Smith Predictor",
        "url": "https://www.mathworks.com/help/control/ug/control-of-processes-with-long-dead-time-the-smith-predictor.html"
      }
    ],
    "status": "UNKNOWN",
    "validation_obligations": [
      "운전 범위와 자원 충족 확인",
      "효과와 후보 기구 연결 확인"
    ]
  },
  {
    "conditions": [
      "캠·롤러 등의 형상과 마찰·회전 방향을 맞춘다. 전달 토크·윤활·과속·마모를 확인하며 기어비 변환과 구별한다.",
      "캠·롤러 형상과 마찰·회전 방향을 맞추고 전달 토크·윤활·과속·마모를 확인해야 한다. 정렬·클램프 중첩은 soft 제약(CON-b76ecf8e)으로 금지되어 있어 적용 전 재검토가 필요하다."
    ],
    "id": "app-68a4a6fb6597002bd6732b4e",
    "mechanism": "상대 회전 방향에 따라 접촉 요소가 끼이거나 풀려 한 방향에서는 토크를 전달하고 반대 방향에서는 공회전을 허용한다.",
    "reason": "정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음",
    "required_function": "물체를 지지·고정하거나 이동시킨다",
    "source_effect_id": "1.30",
    "sources": [
      {
        "identifier": "REF-manual500-one-way-clutch",
        "retrieval_scope": "reference_section",
        "source_type": "REFERENCE",
        "title": "Stieber: Function principle of freewheels",
        "url": "https://www.stieberclutch.com/technical/function-principle"
      },
      {
        "identifier": "AR-068202-A4",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "기존 검토: 한 방향으로만 잠기는 freewheel bearing으로 역회전 여유각을 줄인다. 일방향 클러치 후보. 문헌 대조 후 원리 연결: 일방향 클러치의 선택적 토크 전달: 상대 회전 방향에 따라 접촉 요소가 끼이거나 풀려 한 방향에서는 토크를 전달하고 반대 방향에서는 공회전을 허용한다. 캠·롤러 등의 형상과 마찰·회전 방향을 맞춘다. 전달 토크·윤활·과속·마모를 확인하며 기어비 변환과 구별한다.",
        "source_fingerprint": "c71be0ba95fb3f145ce1a19b09f577ba34dd4de35458dfd3a81e0fac8240ddbe",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Llave manual tipo crique de ajuste y desajuste",
        "url": "https://patents.google.com/patent/AR068202A4/en"
      },
      {
        "identifier": "AR-078028-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "공기 주머니로 가압하고 한 방향 롤러로 커프 조임을 유지한다.",
        "source_fingerprint": "acd3e9779f2c76cd98a7d2b1c2687ee750c1c650e4391e254bf5de6abe540a55",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Manguito de equipo para medir la presion sanguinea y equipo para medir la presion sanguinea que lo contiene",
        "url": "https://patents.google.com/patent/AR078028A1/en"
      },
      {
        "identifier": "AR-085785-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "왕복 입력을 한 방향 칼날 회전으로 바꾸어 연필을 절삭한다.",
        "source_fingerprint": "c88632ee27e56f7e88dca451469a8544cf6193b610e9eef1649546c1ae78cb2a",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Sacapuntas con rotacion alternativa",
        "url": "https://patents.google.com/patent/AR085785A1/en"
      },
      {
        "identifier": "AR-095189-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "래칫의 일방향 맞물림으로 확장 위치의 역행을 막는다. 회전 클러치와 공통 정류 원리 범위로 연결한다.",
        "source_fingerprint": "c938f0e58bcc08aeeb7706c6ffa893be07ec26476b1171cfc4305f5ac61f9f70",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Caja intervertebral expandible en forma escalonada",
        "url": "https://patents.google.com/patent/AR095189A1/en"
      },
      {
        "identifier": "AR-114589-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "일방향 클러치와 스위블 잠금으로 튜빙의 회전 방향과 위치를 제어한다.",
        "source_fingerprint": "3500eb747869bc2f9699648525809bc15ec2cf74ca8e6400fb49fe0df7e797f8",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Rotador de tubería con liberación de torsión, colgador de tubería, y sistema",
        "url": "https://patents.google.com/patent/AR114589A1/en"
      },
      {
        "identifier": "AT-16579-U1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "한 회전 방향에서만 속도 조절부와 연결한다.",
        "source_fingerprint": "fe0b582d5725fbb63262505c10a3e97a860fc5051885b5e8519a3b0bde5c6efa",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Baustrukturabdeckung mit einer geschwindigkeitsregulierenden Baugruppe",
        "url": "https://patents.google.com/patent/AT16579U1/en"
      },
      {
        "identifier": "AT-16769-U1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "스프링 에너지 방출과 일방향 결합으로 삽을 가속한다.",
        "source_fingerprint": "afd2a8450c44afbf72488176f8fa02f85c284b5d763322d38460d3f1ec2d1408",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Vorrichtung zum Werfen von festen stückigen Materialien",
        "url": "https://patents.google.com/patent/AT16769U1/en"
      },
      {
        "identifier": "AT-502671-B1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "걸림 고리로 체인 휠의 역회전을 막는다.",
        "source_fingerprint": "413d98041797fffcfd05b36c3007088e630b0af4a0dc7369d7dbd44f0ad4fca2",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Deflecting device e.g. deflection roller, for anti-skid chain of truck tire, has geared rim provided in side of chainwheel, where geared rim blocks movement of chainwheel in opposite direction, where chainwheel is supported in housing",
        "url": "https://patents.google.com/patent/AT502671B1/en"
      },
      {
        "identifier": "AT-504671-B1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "감쇠 방향에는 결합하고 복귀 방향에는 해제한다.",
        "source_fingerprint": "daffb38f1a003adf46e9cd095ab250ff52a0775451bd29fa5984dfe75692ce03",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Dämpfer",
        "url": "https://patents.google.com/patent/AT504671B1/en"
      },
      {
        "identifier": "AT-512020-A1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "로프 제동 마찰과 방향 선택 작동을 이용한다.",
        "source_fingerprint": "64d7dc630f3aa6330d4ca58d3780ebf6a68adc5ccf2f8c1b22ce41b283f8dc77",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Klettersicherung",
        "url": "https://patents.google.com/patent/AT512020A1/en"
      }
    ],
    "status": "UNKNOWN",
    "validation_obligations": [
      "운전 범위와 자원 충족 확인",
      "효과와 후보 기구 연결 확인"
    ]
  },
  {
    "conditions": [
      "전체 모드·운전 주파수·감쇠·강성 변경 속도와 안정성을 확인한다. 다른 모드의 공진이나 전달률이 커질 수 있다. 추가 질량으로 진동을 흡수하거나 반대 힘을 가하는 제어와 구별한다.",
      "전체 모드·운전 주파수·감쇠·강성 변경 속도와 안정성을 확인해야 한다. 다른 모드의 공진이나 전달률이 커질 수 있고, 고유진동수·강성 허용 기준값은 미확인이다."
    ],
    "id": "app-24aa535e3d14f08e35a7dcef",
    "mechanism": "지지 강성이나 하중 방향을 바꾸면 진동계의 고유 주파수가 이동한다. 가진 주파수와 고유 주파수를 떨어뜨리면 해당 공진 응답을 줄일 수 있다.",
    "reason": "정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음",
    "required_function": "진동을 억제하거나 격리한다",
    "source_effect_id": "2.10",
    "sources": [
      {
        "identifier": "REF-manual-final-stiffness-detuning-resonance-avoidance",
        "retrieval_scope": "reference_section",
        "source_type": "REFERENCE",
        "title": "Theoretical and experimental investigation of a stiffness-controllable suspension for railway vehicles to avoid resonance",
        "url": "https://doi.org/10.1016/j.ijmecsci.2020.105901"
      },
      {
        "identifier": "AT-507002-B1",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "review_note": "문헌·중복 검토 후 연결: stiffness-detuning-resonance-avoidance; 지지 강성이나 하중 방향을 바꾸면 진동계의 고유 주파수가 이동한다. 가진 주파수와 고유 주파수를 떨어뜨리면 해당 공진 응답을 줄일 수 있다. 전체 모드·운전 주파수·감쇠·강성 변경 속도와 안정성을 확인한다. 다른 모드의 공진이나 전달률이 커질 수 있다. 추가 질량으로 진동을 흡수하거나 반대 힘을 가하는 제어와 구별한다.",
        "source_fingerprint": "f1c1ab5f92a3902afdb448b4e9e4796b6c8a07e920e01eb7ca1f0ca01a167ead",
        "source_type": "PATENT",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님",
        "title": "Verfahren und anordnung zum kontrollieren der vibrationen",
        "url": "https://patents.google.com/patent/AT507002B1/en"
      }
    ],
    "status": "UNKNOWN",
    "validation_obligations": [
      "운전 범위와 자원 충족 확인",
      "효과와 후보 기구 연결 확인"
    ]
  },
  {
    "conditions": [
      "속도·상태 의존 마찰·유효 수직하중·구동 강성·특성 미끄럼 거리를 확인한다.",
      "속도·상태 의존 마찰·유효 수직하중·구동 강성·특성 미끄럼 거리를 확인해야 한다. 마찰 계수와 접촉 상태는 미확인이다."
    ],
    "id": "app-084effadec04bc104c9259f7",
    "mechanism": "미끄럼이 빨라질수록 마찰 저항이 낮아지는 접촉에서 구동계 강성이 충분하지 않으면 탄성 에너지 축적과 급격한 미끄럼이 반복된다.",
    "reason": "정본의 적용 조건과 현장 측정값 대조 전; 검색·생성만으로 통과하지 않음",
    "required_function": "진동을 억제하거나 격리한다",
    "source_effect_id": "2.15",
    "sources": [
      {
        "accessed_at": "2026-09-26",
        "identifier": "REF-research-20260926-velocity-weakening-stick-slip-instability",
        "retrieval_scope": "stored_search_excerpt",
        "review_method": "conversation_reasoning",
        "source_type": "REFERENCE",
        "supports": "공개 문헌의 원리·조건을 대화에서 검토한 참고 근거. 초록·검색 발췌 범위는 원문 전체 검증과 구분하며 개별 응용의 성능을 보장하지 않는다.",
        "title": "Nature Communications · Laboratory observations of slow earthquakes and the spectrum of tectonic fault slip modes",
        "url": "https://www.nature.com/articles/ncomms11104"
      }
    ],
    "status": "UNKNOWN",
    "validation_obligations": [
      "운전 범위와 자원 충족 확인",
      "효과와 후보 기구 연결 확인"
    ]
  }
]
```
