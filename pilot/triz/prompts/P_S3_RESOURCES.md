문제 해결에 동원 가능한 자원을 남김없이 나열하라.
자원은 '이미 존재하거나 거의 공짜로 얻을 수 있는 것'이다.

[컴포넌트] {{components}}
[상위 시스템] {{super_system}}
[운전 환경] {{operating_env}}
[작용 영역/시간] {{operative_zone}} / {{operative_time}}
[사용 금지 제약] {{must_not_have}}

문제 유형에 실제 존재하는 카테고리만 사용한다. 없는 물질·장을 수량 때문에 만들지 않는다. 조직 문제의 기존 신뢰·권한·규칙은 FUNCTIONAL, 정보·기록은 INFORMATION, 협업 관계는 SYSTEM_LEVEL로 분류할 수 있다.
- SUBSTANCE: 시스템 내 물질, 폐기물·부산물, 값싼 첨가물, 기존 부품의 여분
- FIELD: 이미 존재하는 장 (열, 진동, 전기, 자기, 중력, 압력차, 유동, 빛, 소리)
- SPACE: 빈 공간, 미사용 면적, 부품 사이 간극, 표면, 이면
- TIME: 유휴 시간, 사전/사후 시간, 병렬 가능 구간, 공정 간 대기
- INFORMATION: 센서값, 로그, 이력, 패턴, 사용자 행동 데이터
- FUNCTIONAL: 이미 존재하는 기능의 부수 효과(다른 용도로 전용 가능한 것)
- SYSTEM_LEVEL: 상위 시스템 자원, 인접 모듈 자원, 외부 환경(대기·중력·온도차)

각 자원:
- where: IN_SYSTEM | IN_SUPERSYSTEM | IN_ENVIRONMENT | WASTE | DERIVED(변형·조합해 만든 파생 자원)
- availability: FREE | LOW_COST | COSTLY
- quantity_note: 얼마나 있는지(추정 가능하면 수치)
- usable_for: 어떤 기능을 대체하거나 보강할 수 있는지 (구체적으로)
- blocked_by_constraint: 제약 때문에 쓸 수 없으면 true

[규칙]
- "예산", "인력 추가"처럼 시스템 밖에서 사와야 하는 것은 자원이 아니다. 제외하라.
- 자원 이름은 **컴포넌트 목록의 하위 요소 수준**으로 구체적으로 적어라.
  "구동부의 열"이 아니라 "감속기 베어링에서 발생하는 마찰열",
  "여유 공간"이 아니라 "커플링과 하우징 사이 축방향 간극 2mm" 처럼.
- 물리 문제는 계면·간극, 조직 문제는 역할 경계·기존 권한·중복 기록·유휴 시간, 정보 문제는 캐시·로그·기존 상태를 살핀다.
- {{min_resources}}개는 탐색 목표다. 실제 가용성이 확인되지 않으면 가설로 표시하고 부족한 카테고리의 이유를 기록한다.

[출력 JSON]
{"resources":[{"category":"SUBSTANCE","name":"","where":"IN_SYSTEM","availability":"FREE","quantity_note":"","usable_for":[],"blocked_by_constraint":false}]}
