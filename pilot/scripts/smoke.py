"""오프라인 스모크 테스트: LLM 호출 없이 배선이 맞는지 확인한다.

    python scripts/smoke.py            # 구조 검사만
    python scripts/smoke.py --llm      # LLM 연결까지 확인
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):  # Windows cp949 콘솔에서 이모지 출력 보호
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from triz import knowledge as K, prompts_registry as P, render  # noqa: E402
from triz.pipeline import PIPELINE, create_run  # noqa: E402
from triz.schema import (  # noqa: E402
    AnalysisBundle, CauseEffectChain, CauseNode, Component, ConceptEvaluation, ConceptSpec,
    Constraint, ConstraintSet, DefinitionBundle, EvaluationBundle, FunctionEdge, IFR,
    InteractionCell, InteractionMatrix, NineWindows, PhysicalContradiction, ProblemFrame,
    ResourceItem, ReviewerScore, SolveBundle, SuFieldModel, SystemCandidate,
    TechnicalContradiction, GlobalState,
)
from triz.settings import settings  # noqa: E402

ok, fail = [], []


def check(name: str, fn):
    try:
        fn()
        ok.append(name)
        print(f"  ✅ {name}")
    except Exception as exc:  # noqa: BLE001
        fail.append((name, exc))
        print(f"  ❌ {name}: {type(exc).__name__}: {exc}")


def t_settings():
    assert settings.cfg("solutions.min_solutions"), "triz.yaml 로드 실패"
    assert settings.rubric("R4_CONTRA"), "rubrics.yaml 로드 실패"
    assert settings.personas.get("seeds"), "personas.yaml 로드 실패"


def t_knowledge():
    assert len(K.params()) == 39, f"39 파라미터 아님: {len(K.params())}"
    assert len(K.principles()) == 40, f"40 원리 아님: {len(K.principles())}"
    assert len(K.params('BIZ_31')) == 31
    assert K.param_name(9) and K.principle_name(15)
    assert K.separation_block() and K.trends_block() and K.effects_block()
    assert K.candidate_standards("COMPLETE", "HARMFUL"), "표준해 후보 선별 실패"
    assert K.ariz_part(1).get("steps"), "ARIZ 스크립트 로드 실패"
    ids, src = K.lookup_matrix(9, 27)
    assert src in ("MATRIX", "LLM_FALLBACK")


def t_prompts():
    required = [
        "P_COMMON_PREAMBLE", "P_VERIFIER_GENERIC", "P_REPAIR", "P_S0_BOOTSTRAP", "P_S1_EXTRACT",
        "P_S1_CLARIFY", "P_S2_CANDIDATES", "P_S3_NINE_WINDOWS", "P_S3_FUNCTION_MODEL",
        "P_S3_SUFIELD", "P_S3_RESOURCES", "P_S3_CECA", "P_S4_IFR", "P_S4_CONTRADICTIONS",
        "P_S4_TRIMMING", "P_S4_KEY_PROBLEM", "P_S5_TRACK_A", "P_S5_TRACK_B", "P_S5_TRACK_C",
        "P_S5_TRACK_E", "P_S5_TRACK_F", "P_S5_TRACK_G", "P_S5_TRACK_H", "P_S5_MATRIX_FALLBACK",
        "P_S5_ARIZ_PART1", "P_S5_ARIZ_PART2", "P_S5_ARIZ_PART3", "P_S5_ARIZ_PART4",
        "P_S5_ARIZ_PART5", "P_S5_ARIZ_PART7", "P_S5_MERGE", "P_S5_EVIDENCE", "P_S6_CONCEPT",
        "P_S7_GATEKEEPER", "P_PERSONA_FACTORY", "P_S8_REVIEW", "P_S8_RANK", "P_S9_NARRATIVE",
        "P_S10_FEEDBACK_DISTILL", "P_S3_CONSTRAINTS", "P_S9_REF_QUERIES", "P_S9_REF_SELECT",
    ]
    have = set(P.list_prompts())
    missing = [r for r in required if r not in have]
    assert not missing, f"프롬프트 누락: {missing}"
    body = P.render("P_S5_TRACK_A", industry="테스트", principles_block=K.principles_block([1, 15]))
    assert "{{" not in body, "치환되지 않은 변수가 남아 있음"


def t_verify():
    from triz import verify

    issues = verify.check_contradictions({
        "technical_contradictions": [{"improving_param_id": 9, "worsening_param_id": 9}],
        "physical_contradictions": [],
    })
    assert any("DET-01b" in i for i in issues), "동일 파라미터 검사 실패"
    assert verify.check_standards({"applications": [{"standard_code": "9.9.9"}]}), "표준해 코드 검사 실패"
    assert verify.check_separation({"applications": [{"kind": "TIME"}]}), "분리원리 커버리지 검사 실패"


def t_pipeline():
    assert len(PIPELINE) == 13, f"스테이지 수 이상: {len(PIPELINE)}"
    keys = [k for k, _, _ in PIPELINE]
    assert keys[0] == "s0_bootstrap" and keys[-1] == "s10_feedback"
    assert "s8_references" in keys


def _fake_state() -> GlobalState:
    st = GlobalState(run_id="run-smoke", raw_query="테스트 문제")
    st.domain.industry = "디스플레이 장비"
    st.domain.target_system = "인라인 증착기 기판 반송 모듈"
    st.domain.super_system = "인라인 열증착 시스템"
    st.constraints = ConstraintSet(items=[
        Constraint(statement="반송속도 300mm/s 이상", kind="NUMERIC", parameter="반송속도",
                   operator=">=", value="300", unit="mm/s")])
    st.intake.frame = ProblemFrame(restated_problem="반송속도를 높이면 성막 불량이 발생한다",
                                   symptom="막두께 편차", success_criteria=["속도 +20%"])
    st.confirm.candidates = [SystemCandidate(name="반송 구동부", description="롤러 구동 반송",
                                             diagram_mermaid="flowchart TB\n A-->B")]
    st.confirm.chosen_candidate_id = st.confirm.candidates[0].id
    st.confirm.operative_zone = "롤러-기판 접촉면"
    st.confirm.operative_time = "가속 구간"
    st.analysis = AnalysisBundle(
        nine_windows=NineWindows(cells={"SYS_PRESENT": "현재"}, insights=["상위시스템 활용"]),
        components=[Component(name="롤러", level="TARGET"), Component(name="기판", level="PRODUCT")],
        function_edges=[FunctionEdge(subject="롤러", action="기판을 이송한다", object="기판",
                                     kind="USEFUL", rank="BASIC"),
                        FunctionEdge(subject="롤러", action="진동을 전달한다", object="기판",
                                     kind="HARMFUL", level="EXCESSIVE")],
        interaction_matrix=InteractionMatrix(components=["롤러", "기판"],
                                             cells=[InteractionCell(a="롤러", b="기판", sign="+-",
                                                                    note="진동 전달")]),
        su_fields=[SuFieldModel(label="접촉 마찰", s1="기판", s2="롤러", field="Me(마찰력)",
                                effect="HARMFUL")],
        resources=[ResourceItem(name="챔버 진공", category="FIELD", where="IN_SYSTEM",
                                usable_for=["비접촉 지지"])],
        ceca=CauseEffectChain(nodes=[CauseNode(id="N1", text="수율 저하",
                                               node_type="TARGET_DISADVANTAGE"),
                                     CauseNode(id="N2", text="접촉식 지지", node_type="ROOT_CAUSE",
                                               parents=["N1"], is_contradiction_seed=True)],
                              mermaid="flowchart TD\n N1-->N2"))
    tc = TechnicalContradiction(label="속도-신뢰성", if_action="속도를 높이면",
                                then_good="생산성 향상", but_bad="신뢰성 저하",
                                improving_param_id=39, worsening_param_id=27)
    pc = PhysicalContradiction(label="접촉 유무", element="롤러", parameter="접촉",
                               state_a="있어야 한다", reason_a="지지", state_b="없어야 한다",
                               reason_b="진동 차단")
    st.definition = DefinitionBundle(ifr=IFR(statement="X-요소가 스스로 진동을 제거한다"),
                                     technical_contradictions=[tc], physical_contradictions=[pc])
    st.solve = SolveBundle(coverage_note="테스트")
    c = ConceptSpec(title="비접촉 지지 하이브리드 반송", one_liner="성막 구간만 비접촉 지지",
                    description="설명", expected_effect="속도 +25% (가정: 강성 2배)",
                    novelty_class="CROSS_DOMAIN", change_scale="PARTIAL")
    st.concepts = [c]
    st.evaluation = EvaluationBundle(evaluations=[ConceptEvaluation(
        concept_id=c.id, rank=1, total_score=4.1, quadrant="QUICK_WIN",
        scores=[ReviewerScore(concept_id=c.id, reviewer_role="설비 리더", dimension="FEASIBILITY",
                              score=4, rationale="구현 가능")])])
    return st


def t_render():
    md = render.render_report(_fake_state(), {"executive_summary": "요약", "limitation_note": "한계"})
    assert "TRIZ 문제해결 리포트" in md, "리포트 렌더 실패"
    assert "{{" not in md, "템플릿 미치환 변수 존재"
    assert "비접촉 지지 하이브리드 반송" in md, "해결책 섹션 누락"
    out = ROOT / "data" / "smoke_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"     └ 샘플 리포트: {out}")


def t_store():
    from triz import store

    st = create_run("스모크 테스트 질의입니다. 충분히 길게 작성합니다.", mode="LITE")
    loaded = store.load_state(st.run_id)
    assert loaded and loaded.run_id == st.run_id, "상태 저장/로드 실패"
    store.delete_run(st.run_id)


def t_rag():
    from triz import rag

    assert isinstance(rag.retrieve("테스트 쿼리"), list)


def main() -> None:
    print("\n[TRIZ Pilot 스모크 테스트]\n")
    check("설정 로드", t_settings)
    check("TRIZ 지식자산", t_knowledge)
    check("프롬프트 카탈로그", t_prompts)
    check("검증 로직", t_verify)
    check("파이프라인 구성", t_pipeline)
    check("리포트 렌더링", t_render)
    check("SQLite 저장소", t_store)
    check("피드백 RAG", t_rag)

    if "--llm" in sys.argv:
        from triz import llm

        def t_llm():
            res = llm.healthcheck()
            assert res.get("ok"), res
            print(f"     └ 응답: {res}")

        check("LLM 연결", t_llm)

    print(f"\n결과: 통과 {len(ok)} / 실패 {len(fail)}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
