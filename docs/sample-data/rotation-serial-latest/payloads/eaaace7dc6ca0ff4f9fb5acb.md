# 저장 데이터 · eaaace7dc6ca

원본 값의 정규 JSON SHA-256: `eaaace7dc6ca0ff4f9fb5acbd7e982c449850c58d91b08873c3165b63286da2f`

```json
[
  {
    "title": "전자석 간극 능동 유지",
    "idea": "계면 간극을 전자석 인력·간극 센서 피드백으로 능동 유지하여 T2 미세 간극·T1 압착을 구현한다.",
    "source_step": "5.4",
    "standard_code": null,
    "source_effect_id": "1.1",
    "effect_name": "전자석 흡인형 자기부상",
    "mechanism": "전자석 인력으로 하중을 지지하고 피드백으로 공극을 유지한다.",
    "mechanism_key": "전자석 전류·간극 피드백 → 계면 간극",
    "intervention_variable": "전자석 전류와 간극 피드백 이득",
    "conditions": [
      "자성 경로, 간극 센서, 제어 전원 필요. 전원 상실 시 지지 대책 필요.",
      "자성 경로·간극 센서·제어 전원 필요",
      "전원 상실 시 지지 대책 필요"
    ],
    "strongest_objection": "전원 상실 시 계면이 이완되어 안정성 HARD 제약을 위반한다.",
    "validation_test": "전원 상실 시 계면 거동과 안전 정지 동작을 측정",
    "hypothesis_ids": [
      "H3"
    ],
    "catalog_sources": [
      {
        "identifier": "REF-maglev",
        "title": "US DOE · How Maglev Works",
        "url": "https://www.energy.gov/articles/how-maglev-works",
        "source_type": "REFERENCE",
        "retrieval_scope": "reference_section",
        "accessed_at": "2026-09-11",
        "supports": "기초 메커니즘과 조건을 확인하기 위한 참고 자료; 산업별 성능 보증 아님"
      },
      {
        "identifier": "AR-071666-A1",
        "title": "Cojinete de empuje con magnetico con componentes electronicos integrados",
        "url": "https://patents.google.com/patent/AR071666A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "5c2a1eb329ad9bee2c62f54126ef2a5b56ca7b437068c1598790f0cddff1a57a",
        "review_note": "rotor 추력 디스크를 stator의 자기력으로 지지한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-505479-B1",
        "title": "Magnetlagereinrichtung",
        "url": "https://patents.google.com/patent/AT505479B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "c86a836c5e65b4d00f84f1b7c9985d7ef2d04a9dddcf5d959f1b12f4cf646128",
        "review_note": "문헌·중복 검토 후 연결: reluctance-dependent-inductive-position-sensing; 자성체와 코일 사이 간극이 변하면 자기회로 저항과 쇄교 자속이 달라져 코일의 인덕턴스·전류 응답이 바뀐다. 전압·전류 응답을 보정하여 대상의 상대 위치를 추정한다. 자기 포화·누설 자속·히스테리시스·권선 저항·구동 파형·온도 보정이 필요하다. 도체 내 와전류에 의한 응답과 구분하며 구동 코일을 센서로 겸용해도 위치 모델 검증이 필요하다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-505598-B1",
        "title": "Magnetlagereinrichtung",
        "url": "https://patents.google.com/patent/AT505598B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "9f83079c6a7c3608ed90dc36d950d3b4129223c617d94a45b06d0735af4b4295",
        "review_note": "위치 이탈에 따른 전자석 전류로 축을 비접촉 지지한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      }
    ],
    "catalog_evidence_level": "참고 문헌과 편집 지식",
    "effect_domain": "PHYSICAL",
    "principle": "전자석의 인력으로 하중을 지지하고 피드백으로 공극을 유지한다.",
    "catalog_conditions": "자성 경로, 간극 센서, 제어 전원 필요. 전원 상실 시 지지 대책 필요.",
    "catalog_limitations": "",
    "catalog_function": "물체를 지지·고정하거나 이동시킨다",
    "catalog_mechanism_key": "electromagnetic-suspension"
  },
  {
    "title": "인덕턴스 간극 감지",
    "idea": "계면 간극을 인덕턴스 변화로 실시간 감지하여 T1 강결합 도달을 판정한다.",
    "source_step": "5.4",
    "standard_code": null,
    "source_effect_id": "12.83",
    "effect_name": "간극 자기저항의 인덕턴스 변화에 의한 위치 감지",
    "mechanism": "자성체-코일 간극 변화가 자기회로 저항·쇄교 자속을 바꿔 인덕턴스·전류 응답을 변화시킨다.",
    "mechanism_key": "계면 간극 → 코일 인덕턴스",
    "intervention_variable": "코일 구동 파형과 보정 계수",
    "conditions": [
      "자기 포화·누설 자속·히스테리시스·권선 저항·구동 파형·온도 보정이 필요하다. 도체 내 와전류에 의한 응답과 구분하며 구동 코일을 센서로 겸용해도 위치 모델 검증이 필요하다.",
      "자기 포화·누설 자속·히스테리시스·온도 보정 필요"
    ],
    "strongest_objection": "자기 포화·온도 드리프트가 감지 정밀도를 떨어뜨린다.",
    "validation_test": "온도 변화·포화 조건에서 인덕턴스-간극 관계의 반복성을 측정",
    "hypothesis_ids": [
      "H3"
    ],
    "catalog_sources": [
      {
        "identifier": "REF-manual-final-reluctance-dependent-inductive-position-sensing",
        "title": "A Self-Sensing Active Magnetic Bearing Based on a Direct Current Measurement Approach",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3821321/",
        "source_type": "REFERENCE",
        "retrieval_scope": "reference_section"
      },
      {
        "identifier": "AT-505479-B1",
        "title": "Magnetlagereinrichtung",
        "url": "https://patents.google.com/patent/AT505479B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "c86a836c5e65b4d00f84f1b7c9985d7ef2d04a9dddcf5d959f1b12f4cf646128",
        "review_note": "문헌·중복 검토 후 연결: reluctance-dependent-inductive-position-sensing; 자성체와 코일 사이 간극이 변하면 자기회로 저항과 쇄교 자속이 달라져 코일의 인덕턴스·전류 응답이 바뀐다. 전압·전류 응답을 보정하여 대상의 상대 위치를 추정한다. 자기 포화·누설 자속·히스테리시스·권선 저항·구동 파형·온도 보정이 필요하다. 도체 내 와전류에 의한 응답과 구분하며 구동 코일을 센서로 겸용해도 위치 모델 검증이 필요하다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      }
    ],
    "catalog_evidence_level": "참고 문헌과 편집 지식",
    "effect_domain": "PHYSICAL",
    "principle": "자성체와 코일 사이 간극이 변하면 자기회로 저항과 쇄교 자속이 달라져 코일의 인덕턴스·전류 응답이 바뀐다. 전압·전류 응답을 보정하여 대상의 상대 위치를 추정한다.",
    "catalog_conditions": "자기 포화·누설 자속·히스테리시스·권선 저항·구동 파형·온도 보정이 필요하다. 도체 내 와전류에 의한 응답과 구분하며 구동 코일을 센서로 겸용해도 위치 모델 검증이 필요하다.",
    "catalog_limitations": "",
    "catalog_function": "상태·성분을 측정하거나 검출한다",
    "catalog_mechanism_key": "reluctance-dependent-inductive-position-sensing"
  },
  {
    "title": "ToF 정착 판정",
    "idea": "로테이션 각도·정지 위치를 ToF로 측정하여 정착 시간 단축 판정에 사용한다.",
    "source_step": "5.4",
    "standard_code": null,
    "source_effect_id": "12.12",
    "effect_name": "비행·통과시간 측정(ToF)",
    "mechanism": "전파 시간이나 통과 시간으로 거리·속도를 구한다.",
    "mechanism_key": "전파 시간 → 각도·정지 위치",
    "intervention_variable": "ToF 측정 기준과 표본화율",
    "conditions": [
      "알려진 전파 속도 또는 검출점 간격과 시간 기준 필요. 지연·다중 경로·매질 변화·특징 대응 오류 고려.",
      "알려진 전파 속도·시간 기준 필요",
      "지연·다중 경로·매질 변화 고려"
    ],
    "strongest_objection": "다중 경로·매질 변화가 측정 오차를 키워 정착 판정을 흐린다.",
    "validation_test": "ToF 측정값과 인코더 기준값을 비교하여 오차 범위 확인",
    "hypothesis_ids": [
      "H1"
    ],
    "catalog_sources": [
      {
        "identifier": "AR-011379-A1",
        "title": "Dispositivo medidor de velocidad para vehiculos y otros usos",
        "url": "https://patents.google.com/patent/AR011379A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "0e2d6d423bd4a165e7e53d271ca9d66f95fdc146178651577ab9cb75b1003098",
        "review_note": "같은 표면 특징이 두 검출 위치를 통과하는 시간차로 속도를 구함. 광자의 비행시간과 대상의 이동시간을 구분해야 한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-015898-A1",
        "title": "Dispositivo en maquinas agricolas y procedimiento para la exploracion sin contacto fisico de contornos que se extienden por arriba del terreno",
        "url": "https://patents.google.com/patent/AR015898A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "327f187f8b9fc55e25f844ce2690508ee7f9609e1b5ce0c4de80b04ae15a0319",
        "review_note": "농업 기계가 레이저 왕복 시간과 주사각으로 작물 윤곽을 측정한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-022531-A1",
        "title": "Un aparato y metodo para calcular la demora de senal de carga util que viaja a traves de un canal de comunicacion",
        "url": "https://patents.google.com/patent/AR022531A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "47a45dd6b2a2346c68b14b216f35261896865e72e8f8ea938cbdbd89c9d3764e",
        "review_note": "알려진 비트열의 전송 지연으로 위성까지 경로 길이를 계산한다. 속도 측정이 있다는 이유로 도플러를 추정하지 않는다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-070674-A1",
        "title": "Equipo de cirugia que contiene laser y ecografo",
        "url": "https://patents.google.com/patent/AR070674A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "1720cb4cfda9287403d3e07101d42563ace1395f9b87cfd3ea49ec65ba85fae3",
        "review_note": "적외선 laser 처리와 초음파 echo 영상으로 위치를 확인한다. 특정 시술 에너지 권장은 추출하지 않는다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-078332-A1",
        "title": "Sistema de control de integridad incorporado a bolsas para almacenamiento de granos y/o forrajes",
        "url": "https://patents.google.com/patent/AR078332A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "24b08080fe16100e6d3eb16c81967b96fbba0f568c433f82f1cb42e07d652fad",
        "review_note": "기존 초록 검토: 도전 띠의 단선과 시간영역 반사로 손상 위치를 찾고 태양전지로 전원 공급한다. 임피던스 불연속 반사 계측 후보로 기록한다. 문헌 대조 후 연결한 일반 원리(특허 세부 구현의 추가 입증은 아님): 시간 영역 반사에 의한 전송선 결함 위치 추정: 전송선에 보낸 신호가 임피던스 불연속에서 반사되어 돌아오는 시간을 측정하면 전파 속도를 이용해 불연속 위치를 추정할 수 있다. 전파 속도·분산·다중 반사·대역폭 보정이 필요하다. 비행시간 측정의 전송선 응용이며 반사 크기·극성은 결함 성질의 보조 정보다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-094645-A1",
        "title": "Sistema de monitoreo personal",
        "url": "https://patents.google.com/patent/AR094645A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "eb63bf12764cd18e3689ac97482d2bce4658cddecef5e4f19701d6a1f5cc4193",
        "review_note": "문헌·중복 검토 후 연결: range-based-multilateration; 위치를 아는 여러 기준점까지의 거리 또는 의사거리를 함께 만족하는 좌표를 구해 대상 위치를 추정한다. 위성 항법에서는 수신기 시계 오차도 함께 추정한다. 기준점 배치·시간 기준·전파 지연·다중 경로·측정 오차를 고려한다. 일반적인 3차원 위치와 공통 시계 오차에는 최소 네 개의 독립 제약이 필요하며 단일 ToF 측정과 구분한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-112719-A1",
        "title": "Análisis interactivo de datos y herramienta de visualización para el monitoreo ultrasónico de la corrosión",
        "url": "https://patents.google.com/patent/AR112719A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "6e9fe58640e29ce50f6fbd5a794b6ff489b1ac8fac179bcf0a761ad05432a94d",
        "review_note": "초음파 펄스 반사로 관벽 두께를 측정하고 왜곡된 파형을 보정한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-113356-A1",
        "title": "Métodos para determinación de referencia en tdoa inter-rat",
        "url": "https://patents.google.com/patent/AR113356A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "92afb6af0895d9e5c2bdab027a6925913222dbae09cc814a894c2df1136cd2ee",
        "review_note": "서로 다른 무선망의 기준 신호로 도착시간차 측위를 한다. 거리 기반 다변측량 후보의 추가 사례이다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-113366-A1",
        "title": "Fase aleatoria y códigos de radares de amplitud para rastreo de objetos espaciales",
        "url": "https://patents.google.com/patent/AR113366A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "7b44823e89966ea72726209ade6327abdb593c550ea04e034e63c693cfe3f3ce",
        "review_note": "무작위 진폭·위상의 레이더 펄스 반사로 물체를 추적한다. 특정 상관 처리 사용은 별도 확인한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-114800-A1",
        "title": "Imagenología depositacional de la línea de conducción",
        "url": "https://patents.google.com/patent/AR114800A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "303262e730d7b8096cbb632813dd5560153efbf918772a4e654f1668f93d7c07",
        "review_note": "관 양단의 압력 펄스와 반사를 이용해 내부 퇴적 상태를 추정한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-125700-A2",
        "title": "Sistemas, métodos y aparatos para detectar la profundidad de surcos agrícolas",
        "url": "https://patents.google.com/patent/AR125700A2/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "ce2e59363e6d2f42ee8373dc731111ba83aca6a0cda04bdee478a92019506b33",
        "review_note": "초음파 거리 검출로 파종 홈 깊이를 측정한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-413453-B",
        "title": "Einrichtung zur aufnahme eines objektraumes",
        "url": "https://patents.google.com/patent/AT413453B/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "1172f5f235f1f382a5ed801e64ee2caab1c7dd70e4af5a578233db99f75b6aa0",
        "review_note": "광 펄스 전파 시간·위상으로 거리와 위치를 구한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-508562-B1",
        "title": "3-d vermessungseinrichtung",
        "url": "https://patents.google.com/patent/AT508562B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "e853a32bf1e16692656381d7e792abcc3c26f2580864821cc8feb5bd1ac0e581",
        "review_note": "비행 시간 거리와 회전 거울 방향을 결합한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-509180-B1",
        "title": "Optoelektronisches messsystem",
        "url": "https://patents.google.com/patent/AT509180B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "260c247d617acf5414e6e1f45426624958b8cb9479acb8cc6c09de9c1a9742d7",
        "review_note": "회전 거울과 비행 시간 거리로 공간을 훑는다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-511750-B1",
        "title": "Verfahren und system zur ortung von objekten",
        "url": "https://patents.google.com/patent/AT511750B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "6bb6239465f73ef8ee1a44cf4001e3cc53aa0a4f586da15f65808e6a720e1ad2",
        "review_note": "전파 왕복·지연을 사용한 거리 판독이며 수동 응답 세부는 별도 초안에서 다룬다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      }
    ],
    "catalog_evidence_level": "참고 문헌과 편집 지식",
    "effect_domain": "PHYSICAL",
    "principle": "빛·소리의 전파 시간이나 대상의 두 위치 사이 통과 시간을 이용해 거리·속도를 구한다.",
    "catalog_conditions": "알려진 전파 속도 또는 검출점 간격과 시간 기준 필요. 지연·다중 경로·매질 변화·특징 대응 오류 고려.",
    "catalog_limitations": "",
    "catalog_function": "상태·성분을 측정하거나 검출한다",
    "catalog_mechanism_key": "time-of-flight"
  },
  {
    "title": "동적 시스템 식별 최적화",
    "idea": "가감속 프로파일 입력과 부하율·진동·온도 출력으로 구동계 동적 모델을 식별해 최적 프로파일을 도출한다.",
    "source_step": "5.4",
    "standard_code": null,
    "source_effect_id": "19.18",
    "effect_name": "동적 시스템 식별",
    "mechanism": "입력-출력의 시간·주파수 관계에서 동적 모델 구조·매개변수를 추정한다.",
    "mechanism_key": "가진 입력·출력 로그 → 동적 모델 매개변수",
    "intervention_variable": "가진 입력 패턴과 모델 구조",
    "conditions": [
      "충분히 다양한 가진·적절한 표본화·모델 구조와 독립 검증 자료 필요. 잡음·식별 가능성·비선형성·운전 범위 변화를 고려.",
      "다양한 가진·적절한 표본화·모델 구조·독립 검증 자료 필요"
    ],
    "strongest_objection": "모델이 운전 범위 밖에서 외삽 오차를 보이면 최적화 결과가 무효가 된다.",
    "validation_test": "식별 모델 예측과 독립 검증 실험 결과를 비교하여 외삽 오차 확인",
    "hypothesis_ids": [
      "H1",
      "H2"
    ],
    "catalog_sources": [
      {
        "identifier": "REF-manual300-system-identification",
        "title": "MathWorks · System Identification Overview",
        "url": "https://www.mathworks.com/help/ident/gs/about-system-identification.html",
        "source_type": "REFERENCE",
        "retrieval_scope": "reference_section"
      },
      {
        "identifier": "AR-029860-A1",
        "title": "Metodo para calibrar una senal de excitacion a ser aplicada a un excitador de un aparato de medicion de caudal",
        "url": "https://patents.google.com/patent/AR029860A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "40f6b5831b281550114b7a1bbd4ad23a689a55777700e701ccf7a4afd77e26cc",
        "review_note": "유량계 관을 가진하고 진동을 측정해 물리 매개변수를 식별한 동적 모델로 전압을 구한다. 입력·출력에 따른 모델 식별만 연결하며 이를 별도 근거 없이 코리올리 유량 원리로 분류하지 않는다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-075020-A1",
        "title": "Aparato, metodo y programa de computadora para obtener un parametro que describe una variacion de una caracteristica de senal de una senal",
        "url": "https://patents.google.com/patent/AR075020A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "bc03b815e7a57e7224200af214680f3fe12f013bb956384b9b4c93e45a78f7ab",
        "review_note": "변환 영역의 시간 변화를 모델로 맞추고 오차를 줄여 매개변수를 구한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-093594-A1",
        "title": "Deteccion mejorada de un cambio en el area transversal de un tubo de fluido en un medidor vibrante",
        "url": "https://patents.google.com/patent/AR093594A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "1dc953fe65a23703a4259938c6d0b88f8980c5b66be856c22308e89d8b803ab6",
        "review_note": "문헌·중복 검토 후 연결: mechanical-resonance-property-sensing; 구조물의 고유 진동수와 모드 응답은 질량·강성·경계조건에 의존한다. 기준 상태와의 변화를 비교해 물성이나 구조 손상을 추정할 수 있다. 온도·유체 부가 질량·감쇠·지지 조건을 분리해야 한다. 주파수 하나만으로 질량과 강성을 모두 식별할 수 없다. 수정 미량저울을 포함하는 상위 계측 원리이며 추정 알고리즘과 구분한다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AR-120747-A1",
        "title": "Análisis térmico de datos de temperatura recolectados de un sistema de sensor de temperatura distribuida para estimar las propiedades térmicas de un pozo",
        "url": "https://patents.google.com/patent/AR120747A1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "4e28722a2dd21f97a7390570b4311330ebec1afdfb77ef5c3ca29bae7be781de",
        "review_note": "시간별 온도에서 열전달 계수·지열 물성을 역산한다. 분포 온도 센서 자체의 광학 원리는 미특정이다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      },
      {
        "identifier": "AT-511807-B1",
        "title": "Verfahren und vorrichtung zur online-erkennung einer zustandsverschlechterung einer isolierung in einer elektrischen maschine",
        "url": "https://patents.google.com/patent/AT511807B1/en",
        "source_type": "PATENT",
        "retrieval_scope": "stored_patent_abstract",
        "review_method": "conversation_reasoning",
        "source_fingerprint": "752c11bf0ed6115005d8327eeec8ff86fd37f62a7750b9613962dd48b4647993",
        "review_note": "전압 계단 뒤 전류의 고유 주파수·감쇠·오버슈트를 관찰한다. 절연 결함 판정은 다른 기생 성분과의 구분이 필요하다.",
        "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
      }
    ],
    "catalog_evidence_level": "참고 문헌과 편집 지식",
    "effect_domain": "INFORMATIONAL",
    "principle": "시스템에 가한 입력과 측정한 출력의 시간·주파수 관계에서 동적 모델의 구조나 매개변수를 추정한다.",
    "catalog_conditions": "충분히 다양한 가진·적절한 표본화·모델 구조와 독립 검증 자료 필요. 잡음·식별 가능성·비선형성·운전 범위 변화를 고려.",
    "catalog_limitations": "",
    "catalog_function": "정보를 전달·추정하거나 시스템을 제어한다",
    "catalog_mechanism_key": "dynamic-system-identification"
  },
  {
    "title": "변형 시효 마찰 강화",
    "idea": "계면 접촉면 재질의 변형 시효 특성으로 T1 정지 시 마찰 고정력을 시간 의존적으로 강화한다.",
    "source_step": "5.4",
    "standard_code": null,
    "source_effect_id": "17.39",
    "effect_name": "용질 확산과 전위 고정의 변형 시효",
    "mechanism": "이동 가능한 용질이 전위 부근에 모여 전위 운동을 지연시켜 유동응력을 변화시킨다.",
    "mechanism_key": "용질 확산 시간·온도 → 마찰 고정력",
    "intervention_variable": "접촉면 재질의 용질 농도와 온도",
    "conditions": [
      "용질 확산 시간과 전위 대기·이동 시간을 비교한다. 정적·동적 시효를 구분하고 톱니형 유동·연성 저하를 단순한 유익한 강화로 해석하지 않는다.",
      "용질 확산 시간과 전위 대기·이동 시간 비교 필요",
      "연성 저하 고려"
    ],
    "strongest_objection": "시효가 진행되면 연성이 저하되어 계면이 취성 파괴될 수 있다.",
    "validation_test": "반복 운전 후 접촉면 경도·연성 변화와 마찰 계수를 측정",
    "hypothesis_ids": [
      "H4"
    ],
    "catalog_sources": [
      {
        "identifier": "REF-research-20260926-solute-dislocation-strain-aging",
        "title": "Curtin et al. · A predictive mechanism for dynamic strain ageing in aluminium–magnesium alloys",
        "url": "https://www.nature.com/articles/nmat1765",
        "source_type": "REFERENCE",
        "retrieval_scope": "publisher_abstract",
        "accessed_at": "2026-09-26",
        "review_method": "conversation_reasoning",
        "supports": "공개 문헌의 원리·조건을 대화에서 검토한 참고 근거. 초록·검색 발췌 범위는 원문 전체 검증과 구분하며 개별 응용의 성능을 보장하지 않는다."
      }
    ],
    "catalog_evidence_level": "참고 문헌과 편집 지식",
    "effect_domain": "PHYSICAL",
    "principle": "이동 가능한 용질이 전위 부근에 모여 전위 운동을 지연시키면 시간·온도·변형률 속도에 따라 유동응력이 달라지고 불안정 변형이 나타날 수 있다.",
    "catalog_conditions": "용질 확산 시간과 전위 대기·이동 시간을 비교한다. 정적·동적 시효를 구분하고 톱니형 유동·연성 저하를 단순한 유익한 강화로 해석하지 않는다.",
    "catalog_limitations": "",
    "catalog_function": "손상을 억제하거나 재료를 강화한다",
    "catalog_mechanism_key": "solute-dislocation-strain-aging"
  }
]
```
