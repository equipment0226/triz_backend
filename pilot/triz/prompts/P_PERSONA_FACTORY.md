아래 문제 상황의 해결안을 각자의 직무 관점에서 독립 검토할 책임자는 누구인가?
검토자 페르소나를 설계하라.

[업종/직군] {{industry}} / {{job_family}}
[대상 시스템] {{target_system}}
[제약 요약] {{constraints_digest}}
[해결안 성격 요약] {{concepts_digest}}
[기본 시드] {{seed_roles}}

--- 생성 규칙 ---
- 총 {{min_reviewers}}~{{max_reviewers}}명. 시드를 우선 사용하고, 이 문제 특유의 역할을 추가하라.
- 서로 관심사가 겹치지 않아야 한다.
- 반드시 포함: 구현 담당 / 비용 담당 / 리스크·품질 담당 / 운영·일정 담당
- 안전·규제·환경 이슈가 보이면 veto_power=true 역할을 추가하라.
- 비엔지니어링 문제라면 해당 도메인 실무 역할로 대체하라.

각 페르소나:
- role_name: 구체적 직함 (예: "진공 반송 설비 기술 리더")
- seniority: 경력과 배경
- mandate: 이 역할이 책임지는 KPI(성과 지표·목표 방향)와 조직에서 반드시 지켜야 하는 것을 1문장으로 명시. 제공되지 않은 수치 목표를 만들지 않는다.
- dimensions: 평가 차원 1~2개
  (FEASIBILITY|COST|RISK|TIME|QUALITY|ADOPTION|SAFETY|SCALABILITY)
- bias_note: 성향 (보수적/실험적, 무엇에 민감한지)
- veto_power: true/false

[출력 JSON]
{"personas":[{"role_name":"","seniority":"","mandate":"","dimensions":[],"bias_note":"","veto_power":false}]}
