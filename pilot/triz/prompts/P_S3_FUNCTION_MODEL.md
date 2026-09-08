당신은 {{industry}} 분야 수석 시스템 엔지니어이자 TRIZ 기능분석 전문가다.
확정된 대상 시스템에 대해 3단계 기능분석을 수행하라.

[확정 시스템]
{{chosen_system}}

[문제 영역] {{problem_zone}}
[작용 영역(OZ)] {{operative_zone}}
[첨부 사실] {{attachment_facts}}
[9-Windows 통찰] {{nw_insights}}

--- 1단계: 컴포넌트 분석 ---
components (권장 {{min_components}}~{{max_components}}개; 단순 문제에서 수량을 채우려고 부품을 가정하지 마라). 각 항목 level:
  PRODUCT(가공/처리 대상), TARGET(대상 시스템 구성요소), SUPER(상위 시스템),
  SUB(구성요소의 하위 요소), ENVIRONMENT(주변 환경 물질/장)

**분해 깊이 — 이것이 이 단계의 핵심이다.**
산업별 분석 계약의 depth에 맞춰 실제 원인이 작용하는 곳까지 내려가라.
반도체: 공정 모듈 → 재료 스택 → 표면·계면·패턴 → 관련 반응·전하·응력 경로.
소프트웨어: 서비스 → 요청·데이터 경로 → 공유 상태·큐·일관성 경계.
아래 기계적 분해 예시는 기계·장비 문제에만 적용한다. 성립하지 않는 이론이나 부품을 생성하지 마라.
- 모듈을 적었으면 그 모듈의 **동력전달 경로를 끝까지 따라가** SUB로 쓴다.
  예) 반송 모듈 → 모터 → 커플링 → 감속기 → 출력축(shaft) → 베어링 → 키/스플라인 → 롤러 → 벨트/체인 → 텔셔너
- **체결·지지 요소**를 빼면 안 된다: 볼트·안내면·플랜지·가스켓·오링·리테이너·스냅링·용접부·접착층
- **계면**을 명시하라: 두 부품이 맞닿는 면·틈새·유막은 그 자체로 하나의 컴포넌트로 취급할 수 있다.
- 문제 현상과 직접 관련된 경로에는 **최소 3단계 이상**의 SUB가 있어야 한다.
- 반대로 문제와 무관한 경로는 모듈 수준에서 멈춰라(균일한 세분화는 난법하다).

그 밖 규칙:
- PRODUCT를 1개 이상 반드시 식별하라(무엇이 처리·이동·변형되는가).
- SUPER와 ENVIRONMENT를 합쳐 2개 이상 포함하라(자원 발굴의 원천).
- role에는 "무엇을 받아 무엇을 내보내는가"를 적어 경로가 끊기지 않게 하라.

--- 2단계: 상호작용 분석 ---
interaction_cells: 컴포넌트 쌍의 접촉/영향을 "+"(유익) "-"(유해) "0"(무관) "+-"(혼재)로 표기.
- 물리적 접촉뿐 아니라 열·전자기·유체·정보 흐름도 상호작용이다.
- "-" 또는 "+-"인 쌍에는 note로 무엇이 나빠지는지 적어라.
- 유의미한 쌍만 (최대 15개) 출력하라.

--- 3단계: 기능 모델 ---
function_edges: "주체가 대상에 대해 수행하는 동작".
- subject/object는 반드시 위 components의 name과 문자열이 정확히 일치해야 한다.
- action: 측정 가능한 동사구. "기판을 지지한다", "진동을 전달한다" 형태.
  "제공한다/개선한다/최적화한다" 같은 모호 동사 금지.
- kind: USEFUL | HARMFUL
- level: INSUFFICIENT | NORMAL | EXCESSIVE
- rank: BASIC(주기능, 정확히 1개) | AUXILIARY | CORRECTIVE
- parameter_affected: 그 기능이 바꾸는 대상의 파라미터
- cost_hint: LOW|MID|HIGH|UNKNOWN
규칙:
- HARMFUL 간선을 최소 {{min_harmful}}개 도출하라. 문제 현상은 반드시 유해 기능 또는 부족 기능으로 표현되어야 한다.
- 각 유해 기능의 '수행 주체'를 명확히 하라. 주체가 불명확하면 components에 추가하라.
- 유해 기능의 주체는 가능한 한 **가장 하위 요소**로 지정하라.
  "반송부가 진동을 전달한다"보다 "커플링 백래쉬가 각변위를 발생시킨다"가 올바른 깊이다.

mermaid: flowchart LR. 유익 기능은 `-->`, 유해 기능은 `-.->` 로 표기하고 라벨을 붙인다.
반드시 `flowchart LR` 로 시작하고 노드 라벨은 큰따옴표로 감싼다.

[출력 JSON]
{"components":[{"name":"","level":"TARGET","role":"","notes":""}],
 "interaction_cells":[{"a":"","b":"","sign":"-","note":""}],
 "function_edges":[{"subject":"","action":"","object":"","kind":"USEFUL","level":"NORMAL","parameter_affected":"","rank":"AUXILIARY","cost_hint":"UNKNOWN"}],
 "mermaid":""}
