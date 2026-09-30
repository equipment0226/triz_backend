# 저장 데이터 · 851b3ace480c

정규 JSON SHA-256: `851b3ace480caf00fdbce2d342fc231995131461f1cbc09dac8f16bd8ded2941`

```json
[
  {
    "concept_id": "CPT-S6-e20b4be099f5ce89",
    "title": "회전축 진동·온도 실시간 계측 장",
    "one_liner": "회전축-베어링 접촉면 주변 미사용 공간에 진동·온도 센서를 부착하고 운전 중 실시간 계측하여, 가속도 상향 시 공진 대역 통과 여부와 발열 한계 도달 지점을 정량 판정하는 진단 수단을 구성한다.",
    "description": "회전축-베어링 접촉면 주변 미사용 공간에 진동 센서와 온도 센서를 부착하고, 배선은 회전부를 통과하지 않는 고정 하우징 경로로 배치한다. 운전 중 진동 주파수·진폭과 접촉면 온도를 실시간 로깅하여, 가속도 상향 시 공진 대역 통과 여부와 발열 한계 도달 지점을 판정한다. 이 계측 장은 다른 상향 아이디어의 안전 판정 수단으로 기능하며, 단독으로는 takt을 단축하지 않는다.",
    "intervention_variable": "센서 부착 위치·계측 주기",
    "source_idea_ids": [
      "IDEA-87806e0b"
    ],
    "working_principle": "회전체의 진동 응답과 접촉면 온도는 가속도·각속도 상향에 따라 변하므로, 실시간 계측값이 허용 기준값에 도달하는 시점을 검출하면 안전한 상향 폭을 결정할 수 있다.",
    "source_proposals": [
      {
        "id": "IDEA-87806e0b",
        "idea": "회전축-베어링 접촉면 주변 미사용 공간에 진동·온도 센서를 부착하고, 운전 중 실시간 계측 장을 구성한다. 이 계측 장은 가속도 상향 시 공진 대역 통과 여부와 발열 한계를 판정하는 지표로 전용되어, HARD 제약 도달 지점을 정량적으로 판별하게 한다.",
        "mechanism": "진동·온도 실시간 계측 → 가속도 상향 시 제약 도달 지점 판정 → 안전한 상향 폭 결정.",
        "intervention_variable": "센서 부착 위치·계측 주기",
        "conditions": [
          "센서 부착 공간 확보(미사용 공간)",
          "고유진동수 미확인 상태에서 기준선 설정",
          "계측 데이터 로깅 체계",
          "회전축-베어링 접촉면 주변 미사용 공간 확보",
          "센서 배선이 회전부를 통과하지 않는 경로 확보",
          "회전축-베어링 접촉면 주변 미사용 공간(센서 부착) 확보 가능",
          "고유진동수 미확인",
          "온도 측정값 미확인",
          "측정 시스템의 효율을 높이려는 경우이며 어느 발전 단계에서나 검토할 수 있다.",
          "부하율·온도·진동 측정값 확보(일부 미확인)",
          "측정값 간 상관관계 확인(미확인)",
          "두 로그의 시간 동기화",
          "로그 정확도 확인(60~70% 추정)",
          "물질–장 모델의 효율 개선에 물질의 구조화가 필요하거나 특정 점·선에 강한 열 작용이 필요할 때.",
          "두 로그의 시간 동기화 필요",
          "로그 정확도 미확인(60~70% 추정)",
          "단계별 타임스탬프 실측 데이터 존재",
          "단계별 타임스탬프 실측 데이터 존재(첨부 answers[0])",
          "구간별 시간 비중 수치 미확인",
          "시스템 변화를 직접 검출·측정하는 방법과 시스템에 장을 통과시키는 방법을 모두 사용할 수 없을 때.",
          "회전축·베어링·클램프 계면 고유진동수 확인(미확인)",
          "가진이 시스템에 유해하지 않음(미확인)",
          "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
          "온도·부가 질량·감쇠·지지 조건 분리 필요",
          "한 주파수로 질량·강성 동시 결정 불가",
          "온도·부가 질량·감쇠·지지 조건을 분리해야 하며, 한 주파수로 질량과 강성을 동시에 결정할 수 없다. 액체 점성·점탄성 보정이 필요하고, 회전축·베어링·클램프 계면 고유진동수는 미확인이다."
        ],
        "strongest_objection": "계측은 takt 단축을 직접 달성하지 못하고 판정 수단에 그친다.",
        "validation_test": "센서 계측값과 실제 제약 위반 발생 시점의 상관관계 확인."
      }
    ],
    "changes_to_system": [
      "회전축-베어링 접촉면 주변 미사용 공간에 진동·온도 센서 부착",
      "센서 배선을 회전부를 통과하지 않는 고정 하우징 경로로 배치",
      "계측 데이터 로깅 체계 구성"
    ],
    "required_resources": [
      "회전축-베어링 접촉면 주변 미사용 공간",
      "구동계 운전 중 발생하는 진동(가진력)",
      "회전축-베어링 접촉면에서 발생하는 마찰열",
      "모터·인덱서 부하율 로그(현재 60~70% 추정)",
      "운전 중 베어링·접촉면 온도 이력"
    ],
    "addresses_contradictions": [
      "TC-eefef594",
      "PC-9ffb539d"
    ],
    "resolution_argument": "가속도 상향(IMPROVE)과 부하율·발열 억제(PROTECT)의 결합을 끊지 않고, 계측으로 제약 도달 지점을 판정하여 안전한 상향 폭을 결정한다. 계측 자체는 takt을 단축하지 않으므로 단독 해소가 아니라 상향 아이디어의 안전 판정 수단으로 기능한다.",
    "expected_effect": "목표로 한다: 가속도 상향 시 공진 대역 통과 여부와 발열 한계 도달 지점을 정량 판정. takt 단축 효과는 없으며, 다른 상향 아이디어의 안전 판정 수단으로 기능한다.",
    "assumptions": [
      "센서 부착 공간이 확보된다",
      "고유진동수 미확인 상태에서 기준선을 설정할 수 있다",
      "계측 데이터 로깅 체계가 구성된다",
      "센서 부착 공간 확보(미사용 공간)",
      "고유진동수 미확인 상태에서 기준선 설정",
      "계측 데이터 로깅 체계",
      "회전축-베어링 접촉면 주변 미사용 공간 확보",
      "센서 배선이 회전부를 통과하지 않는 경로 확보",
      "회전축-베어링 접촉면 주변 미사용 공간(센서 부착) 확보 가능",
      "고유진동수 미확인",
      "온도 측정값 미확인",
      "측정 시스템의 효율을 높이려는 경우이며 어느 발전 단계에서나 검토할 수 있다.",
      "부하율·온도·진동 측정값 확보(일부 미확인)",
      "측정값 간 상관관계 확인(미확인)",
      "두 로그의 시간 동기화",
      "로그 정확도 확인(60~70% 추정)",
      "물질–장 모델의 효율 개선에 물질의 구조화가 필요하거나 특정 점·선에 강한 열 작용이 필요할 때.",
      "두 로그의 시간 동기화 필요",
      "로그 정확도 미확인(60~70% 추정)",
      "단계별 타임스탬프 실측 데이터 존재",
      "단계별 타임스탬프 실측 데이터 존재(첨부 answers[0])",
      "구간별 시간 비중 수치 미확인",
      "시스템 변화를 직접 검출·측정하는 방법과 시스템에 장을 통과시키는 방법을 모두 사용할 수 없을 때.",
      "회전축·베어링·클램프 계면 고유진동수 확인(미확인)",
      "가진이 시스템에 유해하지 않음(미확인)",
      "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
      "온도·부가 질량·감쇠·지지 조건 분리 필요",
      "한 주파수로 질량·강성 동시 결정 불가",
      "온도·부가 질량·감쇠·지지 조건을 분리해야 하며, 한 주파수로 질량과 강성을 동시에 결정할 수 없다. 액체 점성·점탄성 보정이 필요하고, 회전축·베어링·클램프 계면 고유진동수는 미확인이다."
    ],
    "open_risks": [
      "고유진동수 미확인으로 공진 판정 기준선 설정 불가",
      "온도 측정값 미확인",
      "계측만으로는 takt이 단축되지 않음"
    ],
    "validation_plan": [
      {
        "metric": "가속도 상향 단계별 진동 주파수·진폭, 접촉면 온도, 부하율",
        "baseline": "현재 보수적 프로파일에서의 진동·온도·부하율(미측정)",
        "target": "허용 기준값 도달 지점을 판정할 수 있는 계측 분해능 확보",
        "experiment": "가속도를 단계적으로 상향하며 진동·온도·부하율을 동시 로깅하고, 제약 도달 시점과 계측값의 상관관계를 확인",
        "failure_criterion": "계측값과 실제 제약 위반 발생 시점의 상관관계가 확인되지 않음",
        "obligation_refs": [
          {
            "contradiction_id": "TC-eefef594",
            "side": "IMPROVE"
          },
          {
            "contradiction_id": "TC-eefef594",
            "side": "PROTECT"
          }
        ]
      }
    ],
    "transfer_conditions": [
      "회전축-베어링 접촉면 주변 미사용 공간 확보",
      "센서 배선이 회전부를 통과하지 않는 경로 확보"
    ],
    "coherence": {
      "candidate_id": "CPT-S6-e20b4be099f5ce89",
      "obligation_ids": [
        "TC-da1055a5",
        "TC-eefef594"
      ],
      "candidate_hash": "ccf6bcf6c5b59ce8c4ac01b00e903fc3699e6143d6760983002fcb3488f312d5",
      "source_effects": [
        {
          "source_effect_id": "12.56",
          "catalog_function": "상태·성분을 측정하거나 검출한다",
          "catalog_conditions": "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
          "catalog_limitations": "",
          "catalog_sources": [
            {
              "identifier": "REF-manual-final-mechanical-resonance-property-sensing",
              "title": "Identification of Corrosion on a Hollow Tube Using Vibration",
              "url": "https://www.scientific.net/AMM.564.176",
              "source_type": "REFERENCE",
              "retrieval_scope": "reference_section"
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
              "identifier": "REF-qcm",
              "title": "Stambaugh et al. · Linking mass measured by the quartz crystal microbalance to the SI",
              "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=927952",
              "source_type": "REFERENCE",
              "retrieval_scope": "reference_section",
              "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
            }
          ],
          "principle": "질량·강성·경계조건이 고유 진동수와 모드를 바꾸므로 기준 상태와 비교해 부착 질량·물성을 추정한다. 수정진동자 미량저울은 그 구현이다."
        },
        {
          "source_effect_id": "12.56",
          "catalog_function": "상태·성분을 측정하거나 검출한다",
          "catalog_conditions": "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
          "catalog_limitations": "",
          "catalog_sources": [
            {
              "identifier": "REF-manual-final-mechanical-resonance-property-sensing",
              "title": "Identification of Corrosion on a Hollow Tube Using Vibration",
              "url": "https://www.scientific.net/AMM.564.176",
              "source_type": "REFERENCE",
              "retrieval_scope": "reference_section"
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
              "identifier": "REF-qcm",
              "title": "Stambaugh et al. · Linking mass measured by the quartz crystal microbalance to the SI",
              "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=927952",
              "source_type": "REFERENCE",
              "retrieval_scope": "reference_section",
              "supports": "문헌에 등장하는 해당 원리의 응용 사례; 정본의 모든 조건이나 성능에 대한 실증 근거는 아님"
            }
          ],
          "principle": "질량·강성·경계조건이 고유 진동수와 모드를 바꾸므로 기준 상태와 비교해 부착 질량·물성을 추정한다. 수정진동자 미량저울은 그 구현이다."
        }
      ],
      "mechanism": {
        "intervention": "회전축-베어링 접촉면 주변 미사용 공간에 진동·온도 센서를 부착하고 실시간 계측",
        "target": "회전축-베어링 접촉면",
        "changed_variable": "계측 정보(진동 주파수·진폭, 접촉면 온도)",
        "mediating_functions": [
          "진동·온도 실시간 계측",
          "제약 도달 지점 판정",
          "안전한 상향 폭 결정"
        ],
        "outcome": "가속도 상향 시 공진 대역 통과 여부와 발열 한계 도달 지점을 정량 판정",
        "operating_scope": "로테이션 가속·감속·정지 구간(발생중)",
        "contribution": "MONITOR_ONLY",
        "control_mode": "DIAGNOSTIC",
        "control_chain": {
          "sensor": "진동 센서·온도 센서",
          "estimator": "계측값 로깅·상관 분석",
          "decision": "제약 도달 지점 판정",
          "actuator": "(없음, 판정 결과를 상향 아이디어에 제공)",
          "target": "회전축-베어링 접촉면"
        },
        "conditions": [
          {
            "source_idea_id": "IDEA-87806e0b",
            "condition": "센서 부착 공간 확보(미사용 공간)",
            "applicability": "회전축-베어링 접촉면 주변 미사용 공간의 실제 치수를 현장 측정하여 센서 부착 가능 여부 확인"
          },
          {
            "source_idea_id": "IDEA-87806e0b",
            "condition": "고유진동수 미확인 상태에서 기준선 설정",
            "applicability": "모달 시험으로 고유진동수를 측정한 후 기준선 설정. 미확인 상태에서는 기준선을 임시로 두고 시험 운전으로 보정"
          },
          {
            "source_idea_id": "IDEA-87806e0b",
            "condition": "계측 데이터 로깅 체계",
            "applicability": "계측 주기·저장 주기·동기화 방식을 현장에서 결정하고 로깅 체계 구성"
          },
          {
            "source_idea_id": "IDEA-74b7c01c",
            "condition": "회전축-베어링 접촉면 주변 미사용 공간 확보",
            "applicability": "공간 분리 접근의 전제 조건으로, 토크 전달 경로와 지지·계측 경로를 분할할 공간이 있는지 확인"
          },
          {
            "source_idea_id": "IDEA-74b7c01c",
            "condition": "센서 배선이 회전부를 통과하지 않는 경로 확보",
            "applicability": "배선 경로를 도면 검토로 확인하고, 회전부 통과 시 슬립링 등 대체 경로 검토"
          },
          {
            "source_idea_id": "IDEA-189b2329",
            "condition": "회전축-베어링 접촉면 주변 미사용 공간(센서 부착) 확보 가능",
            "applicability": "현장 실측으로 부착 공간 확인"
          },
          {
            "source_idea_id": "IDEA-189b2329",
            "condition": "고유진동수 미확인",
            "applicability": "모달 시험으로 측정 필요. 미확인 상태에서는 판정 기준선 설정 불가"
          },
          {
            "source_idea_id": "IDEA-189b2329",
            "condition": "온도 측정값 미확인",
            "applicability": "운전 중 접촉면 온도 측정값을 확보해야 발열 한계 판정 가능"
          },
          {
            "source_idea_id": "IDEA-afd39c61",
            "condition": "측정 시스템의 효율을 높이려는 경우이며 어느 발전 단계에서나 검토할 수 있다.",
            "applicability": "복수 측정계(부하율 로그, 온도 이력, 진동 신호)를 결합하는 바이·폴리 시스템 전환의 전제 조건"
          },
          {
            "source_idea_id": "IDEA-afd39c61",
            "condition": "부하율·온도·진동 측정값 확보(일부 미확인)",
            "applicability": "부하율 로그는 제공 가능, 온도·진동은 센서 부착 후 측정"
          },
          {
            "source_idea_id": "IDEA-afd39c61",
            "condition": "측정값 간 상관관계 확인(미확인)",
            "applicability": "시험 운전으로 상관관계 확인 필요"
          },
          {
            "source_idea_id": "IDEA-51c79765",
            "condition": "두 로그의 시간 동기화",
            "applicability": "부하율 로그와 단계별 타임스탬프의 시간 동기화 방식 현장 결정"
          },
          {
            "source_idea_id": "IDEA-51c79765",
            "condition": "로그 정확도 확인(60~70% 추정)",
            "applicability": "부하율 로그 정확도를 현장에서 확인. 60~70%는 추정치"
          },
          {
            "source_idea_id": "IDEA-82831c48",
            "condition": "물질–장 모델의 효율 개선에 물질의 구조화가 필요하거나 특정 점·선에 강한 열 작용이 필요할 때.",
            "applicability": "접촉면 국부 발열 지점에 센서를 집중 배치하는 구조화 접근의 전제 조건"
          },
          {
            "source_idea_id": "IDEA-82831c48",
            "condition": "두 로그의 시간 동기화 필요",
            "applicability": "현장에서 동기화 방식 결정"
          },
          {
            "source_idea_id": "IDEA-82831c48",
            "condition": "로그 정확도 미확인(60~70% 추정)",
            "applicability": "현장 확인 필요"
          },
          {
            "source_idea_id": "IDEA-82831c48",
            "condition": "단계별 타임스탬프 실측 데이터 존재",
            "applicability": "첨부 answers[0]에서 실측 데이터 존재 확인됨"
          },
          {
            "source_idea_id": "IDEA-30903f57",
            "condition": "단계별 타임스탬프 실측 데이터 존재(첨부 answers[0])",
            "applicability": "실측 데이터 존재 확인됨"
          },
          {
            "source_idea_id": "IDEA-30903f57",
            "condition": "구간별 시간 비중 수치 미확인",
            "applicability": "실측 데이터에서 구간별 시간 비중을 추출하여 확인"
          },
          {
            "source_idea_id": "IDEA-cc14fa86",
            "condition": "시스템 변화를 직접 검출·측정하는 방법과 시스템에 장을 통과시키는 방법을 모두 사용할 수 없을 때.",
            "applicability": "접촉면 상태 변화를 직접 측정할 수 없을 때 공진 가진으로 상태 변화를 판단하는 접근의 전제 조건"
          },
          {
            "source_idea_id": "IDEA-cc14fa86",
            "condition": "회전축·베어링·클램프 계면 고유진동수 확인(미확인)",
            "applicability": "모달 시험으로 측정 필요"
          },
          {
            "source_idea_id": "IDEA-cc14fa86",
            "condition": "가진이 시스템에 유해하지 않음(미확인)",
            "applicability": "가진 시험 시 유해 여부를 진동·온도로 확인"
          },
          {
            "source_idea_id": "IDEA-a2b5bc6e",
            "condition": "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
            "applicability": "공진 변화 계측 시 온도·부가 질량·감쇠·지지 조건을 분리해야 하며, 한 주파수로 질량·강성을 동시 결정할 수 없음을 전제"
          },
          {
            "source_idea_id": "IDEA-a2b5bc6e",
            "condition": "물질–장 모델의 효율 개선에 물질의 구조화가 필요하거나 특정 점·선에 강한 열 작용이 필요할 때.",
            "applicability": "접촉면 국부 발열 지점 구조화 접근의 전제 조건"
          },
          {
            "source_idea_id": "IDEA-a2b5bc6e",
            "condition": "온도·부가 질량·감쇠·지지 조건 분리 필요",
            "applicability": "계측 시 분리 조건을 현장에서 확인"
          },
          {
            "source_idea_id": "IDEA-a2b5bc6e",
            "condition": "한 주파수로 질량·강성 동시 결정 불가",
            "applicability": "복수 주파수 계측 또는 별도 강성 시험 필요"
          },
          {
            "source_idea_id": "IDEA-a2b5bc6e",
            "condition": "고유진동수 미확인",
            "applicability": "모달 시험으로 측정 필요"
          },
          {
            "source_idea_id": "IDEA-6931f367",
            "condition": "온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.",
            "applicability": "공진 변화 계측 시 분리 조건 전제"
          },
          {
            "source_idea_id": "IDEA-6931f367",
            "condition": "온도·부가 질량·감쇠·지지 조건을 분리해야 하며, 한 주파수로 질량과 강성을 동시에 결정할 수 없다. 액체 점성·점탄성 보정이 필요하고, 회전축·베어링·클램프 계면 고유진동수는 미확인이다.",
            "applicability": "계측 시 분리·보정 조건을 현장에서 확인하고, 고유진동수는 모달 시험으로 측정"
          }
        ],
        "claims": [
          {
            "text": "회전축-베어링 접촉면 주변 미사용 공간에 진동·온도 센서를 부착할 수 있다",
            "status": "HYPOTHESIS",
            "source_cause_id": "N11",
            "evidence_refs": [
              "CON-7cf7abd3"
            ]
          },
          {
            "text": "가속도 상향 시 공진 대역 통과 여부와 발열 한계 도달 지점을 계측값으로 판정할 수 있다",
            "status": "HYPOTHESIS",
            "source_cause_id": "N11",
            "evidence_refs": [
              "CON-cc073e11"
            ]
          },
          {
            "text": "계측만으로는 takt이 단축되지 않는다",
            "status": "DERIVED",
            "source_cause_id": "",
            "evidence_refs": []
          }
        ]
      },
      "gaps": [
        {
          "kind": "IMPROVEMENT_SIDE_OMITTED",
          "description": "TC1: 가속도 상향 → takt 단축 vs 부하율·발열 증가 — 개선측 검증계획 연결 누락",
          "obligation_ids": [
            "TC-da1055a5"
          ]
        },
        {
          "kind": "ADVERSE_SIDE_OMITTED",
          "description": "TC1: 가속도 상향 → takt 단축 vs 부하율·발열 증가 — 악화 방지측 검증계획 연결 누락",
          "obligation_ids": [
            "TC-da1055a5"
          ]
        }
      ],
      "structural_status": "INCOMPLETE",
      "concept_review": "UNVERIFIED",
      "test_preparation": "INCOMPLETE"
    }
  }
]
```
