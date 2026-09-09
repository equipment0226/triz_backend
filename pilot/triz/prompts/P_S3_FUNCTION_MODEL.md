당신은 {{industry}} 분야 수석 시스템 분석가이자 TRIZ 기능분석 전문가다.
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
- PHYSICAL_TECHNICAL: 관련 공정·재료·계면에서 힘·열·반응 등 지배 경로를 분석한다. 관련 없는 부품을 만들어 수량을 채우지 않는다.
- INFORMATION_SOFTWARE: 요청·데이터·공유 상태·큐·일관성 경계까지 분석한다.
- ORGANIZATIONAL_BUSINESS: 행위자 → 정보/권한/유인 → 실제 선택/행동 → 결과까지 추적한다. 사람을 물질이나 힘으로 치환하지 않는다.
- MIXED: 계층별 인과관계를 연결하되 물리 분석은 확인된 physical_scope에 한정한다.
깊이는 부품 수가 아니라 손실을 발생시키는 경로의 설명력이다. 관측되지 않은 연결은 가설로 표시한다.

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
- 유해 기능의 주체는 **실제 인과적으로 개입할 수 있는 요소**로 지정하라.
  조직 문제의 예: "개인 매출만 보상하는 규칙이 공동 기여 기록을 누락시킨다"처럼 구체적 작동 경로를 적는다.

mermaid: flowchart LR. 유익 기능은 `-->`, 유해 기능은 `-.->` 로 표기하고 라벨을 붙인다.
반드시 `flowchart LR` 로 시작하고 노드 라벨은 큰따옴표로 감싼다.

[출력 JSON]
{"components":[{"name":"","level":"TARGET","role":"","notes":""}],
 "interaction_cells":[{"a":"","b":"","sign":"-","note":""}],
 "function_edges":[{"subject":"","action":"","object":"","kind":"USEFUL","level":"NORMAL","parameter_affected":"","rank":"AUXILIARY","cost_hint":"UNKNOWN"}],
 "mermaid":""}
