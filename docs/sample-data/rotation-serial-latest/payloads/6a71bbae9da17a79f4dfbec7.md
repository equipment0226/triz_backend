# 저장 데이터 · 6a71bbae9da1

정규 JSON SHA-256: `6a71bbae9da17a79f4dfbec7b4757c9fced55ab7e740921425685b0ce093655f`

```json
{
  "id": "SYS-fdc2e61f",
  "name": "로테이션 구동계(서보 모터·인덱서·회전축·베어링)",
  "scope": "TARGET",
  "description": "180도 로테이션을 담당하는 서보 모터·인덱서·회전축·베어링 조립체를 문제 경계로 본다. 가감속 프로파일과 부하율·강성·발열이 takt 병목과 HARD 제약의 상충이 직접 발생하는 지점이다. 정렬·클램프는 경계 밖 고정 지연으로 취급한다.",
  "diagram_mermaid": "flowchart TB\n  SS[\"대형 OLED 배면 증착 인라인 반송 라인\"] --> TS[\"로테이션 구동계(서보 모터·인덱서·회전축·베어링)\"]\n  TS --> A[\"서보 제어 가감속 프로파일\"]\n  TS --> B[\"인덱서·모터 부하율\"]\n  TS --> C[\"회전축·베어링 강성·발열\"]\n  A --> P[\"가속·감속·정지 구간 시간 과다\"]:::problem\n  B --> P\n  C --> P\n  classDef problem fill:#ffd6d6,stroke:#d33,stroke-width:2px;",
  "similarity_reason": "사용자 진술에서 로테이션 가속·감속·정지 구간이 takt의 지배적 병목이며, 부하율 60~70% 여유와 보수적 가감속 설정 추정이 제시됨. H1(제어 파라미터 병목)과 H3(구조 동역학 한계)이 모두 이 경계 안에서 발생한다.",
  "super_system": "대형 OLED 배면 증착 인라인 반송 라인",
  "operative_zone": "서보 모터 출력축 → 인덱서 → 회전축 → 베어링 접촉면의 토크·각가속도 전달 계면",
  "operative_time": "로테이션 가속·감속·정지 구간(발생중)"
}
```
