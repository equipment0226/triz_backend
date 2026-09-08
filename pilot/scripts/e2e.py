"""엔드투엔드 실행 테스트 (실제 LLM 호출).

    python scripts/e2e.py                # LITE 모드, 자동 응답으로 전 구간 실행
    python scripts/e2e.py --mode FULL
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

from triz import events, pipeline, store  # noqa: E402

QUERY = (
    "디스플레이용 인라인 열증착 시스템에서 유리기판 반송속도를 높이고 싶은데, "
    "컨베이어 구동부 걸림과 미세 진동 때문에 막두께 편차가 생겨 성막 불량이 발생합니다. "
    "반송속도는 최소 300mm/s 이상이어야 하고, 챔버 내부에 새로운 배관은 추가할 수 없습니다."
)


def auto_answer(pending) -> dict:
    kind = pending.kind
    if kind == "CLARIFY":
        return {"answers": ["잘 모르겠다"] * len(pending.payload.get("questions", [])), "skip": True}
    if kind == "CONFIRM":
        cands = pending.payload.get("candidates", [])
        return {"candidate_id": cands[0]["id"] if cands else "", "amendment": ""}
    if kind == "DECIDE":
        return {"decisions": {c["concept_id"]: "accept"
                              for c in pending.payload.get("conditional", [])}}
    if kind == "FEEDBACK":
        concepts = pending.payload.get("concepts", [])
        return {"overall_rating": 4,
                "solution_feedback": [{"concept_id": c["concept_id"], "rating": 5 if i == 0 else 3,
                                       "comment": "자동 테스트 피드백"}
                                      for i, c in enumerate(concepts[:3])]}
    return {}


def main() -> None:
    mode = "LITE"
    if "--mode" in sys.argv:
        mode = sys.argv[sys.argv.index("--mode") + 1].upper()

    state = pipeline.create_run(QUERY, mode=mode)
    run_id = state.run_id
    print(f"run_id = {run_id} (mode={mode})")
    pipeline.start(run_id)

    seen = 0
    t0 = time.time()
    while time.time() - t0 < 3600:
        time.sleep(2)
        hist = store.read_events(run_id, seen)
        for ev in hist:
            t = ev["type"]
            if t in ("stage_start",):
                print(f"\n=== {ev['label']} ===")
            elif t == "node_end":
                print(f"  [{ev.get('status')}] {ev.get('label')} — {ev.get('verdict')} "
                      f"{ev.get('score','')} (${ev.get('cost')})")
            elif t == "warning":
                print(f"  ! {ev['message']}")
            elif t == "error":
                print(f"  X {ev['message']}")
            elif t in ("artifact", "tracks", "personas", "track_escalation"):
                print(f"  · {t}: {str(ev)[:180]}")
        if hist:
            seen = hist[-1]["event_id"]

        st = store.load_state(run_id)
        if not st:
            continue
        if st.status == "WAITING_HUMAN" and st.pending:
            print(f"\n>>> 자동 응답: {st.pending.kind} — {st.pending.title}")
            pipeline.resume(run_id, auto_answer(st.pending))
        elif st.status in ("COMPLETED", "FAILED", "INTERRUPTED"):
            print(f"\n=== 종료: {st.status} / 비용 ${st.cost.total_usd:.4f} / "
                  f"스텝 {len(st.steps)} / 경고 {len(st.control.warnings)}")
            for w in st.control.warnings:
                print(f"  ⚠ {w}")
            if st.report:
                out = ROOT / "data" / f"e2e_{run_id}.md"
                out.write_text(st.report.markdown, encoding="utf-8")
                print(f"리포트: {out} ({len(st.report.markdown)}자)")
            print(f"해결책 {len(st.concepts)}개 / 아이디어 {len(st.solve.raw_ideas)}개 / "
                  f"모순 TC {len(st.definition.technical_contradictions)} "
                  f"PC {len(st.definition.physical_contradictions)}")
            return
    print("타임아웃")


if __name__ == "__main__":
    main()
