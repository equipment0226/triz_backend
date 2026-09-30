# 저장 데이터 · ef60c6cecfcc

정규 JSON SHA-256: `ef60c6cecfcc49ce685c2f24a0e730508b4abb0654e1bd9ce94dcbb256ef51d8`

```json
{
  "intervention": "서보 제어기 가감속 프로파일을 저크 제한 S자형으로 변경하여 가진 스펙트럼의 고주파 성분을 억제한다. 고유진동수 회피 대역을 금지 구간으로 설정하지 않는다.",
  "target": "서보 모터 출력축 → 인덱서 → 회전축 → 베어링 접촉면의 토크·각가속도 전달 계면의 가진 스펙트럼",
  "changed_variable": "가속도 변화율(저크) 프로파일 형상 파라미터",
  "mediating_functions": [
    "저크 제한으로 가진 에너지가 저주파 대역에 집중되어 계면 고유진동수 부근 가진 진폭이 감소한다",
    "가진 진폭 감소로 공진 응답(진동·변형)이 억제되어 강성·안정성 HARD 제약 확보에 기여한다",
    "최고 각속도·가속도를 변경하지 않으므로 금지 대역 설정 없이 프로파일 자유도가 보존된다"
  ],
  "outcome": "공진 회피 대역 금지 없이 진동·변형이 억제되어 강성·하드웨어 안정성 HARD 제약 확보에 기여하고, 가속도·최고 각속도 선택 자유도가 보존된다.",
  "operating_scope": "로테이션 가속·감속 구간(글라스 부하 상태). 원위치 복귀(무부하) 구간은 별도 프로파일 적용 가능.",
  "contribution": "DIRECT",
  "control_mode": "PASSIVE",
  "control_chain": {},
  "conditions": [
    {
      "source_idea_id": "TC-1517ceea",
      "condition": "고유진동수 회피 대역 설정 → 안정성 확보 vs 가감속 프로파일 자유도 제한",
      "applicability": "이 후보는 회피 대역 설정을 전제로 하지 않으므로, 고유진동수 미확인 상태에서도 적용 가능하다. 다만 저크 제한의 공진 억제 효과는 고유진동수 대역이 가진 스펙트럼과 겹칠 때만 유효하므로, 모달 시험 또는 운전 중 진동 스펙트럼 측정으로 고유진동수와 가진 대역의 겹침을 확인해야 한다. 확인 완료를 주장하지 않는다."
    }
  ],
  "claims": [
    {
      "text": "저크 제한 S자형 프로파일은 가진 스펙트럼의 고주파 성분을 억제하여 계면 고유진동수 부근 가진 진폭을 낮춘다",
      "status": "HYPOTHESIS",
      "source_cause_id": "N11",
      "evidence_refs": [
        "CON-7cf7abd3",
        "CON-cc073e11"
      ]
    },
    {
      "text": "회전축·베어링·클램프 계면 고유진동수가 미확인이라 공진 회피 대역을 설정할 수 없다",
      "status": "OBSERVED",
      "source_cause_id": "N11",
      "evidence_refs": [
        "CON-7cf7abd3",
        "CON-cc073e11"
      ]
    },
    {
      "text": "저크 제한은 최고 각속도·가속도를 변경하지 않으므로 부하율 증가가 없다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": [
        "CON-215562ab"
      ]
    },
    {
      "text": "저크 제한으로 정착 시간이 감소하여 총 가감속 구간 시간이 상쇄될 수 있다",
      "status": "HYPOTHESIS",
      "source_cause_id": "",
      "evidence_refs": [
        "CON-6a1787d3"
      ]
    }
  ]
}
```
