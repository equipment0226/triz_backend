"""Bounded industry routing and a pre-definition deep-dive interview."""
import json
import re
from . import agent, prompts_registry as P
from .context import HumanInterrupt
from .settings import settings

CATALOG = settings._load_yaml("industries.yaml")

def classify(query, attachments=()):
    blob = (query + " " + " ".join(a.extracted_text[:3000] for a in attachments)).lower()
    scores = {key: sum(bool(re.search(r"(?<![a-z])" + re.escape(k.lower()) + r"(?![a-z])", blob))
                       for k in profile["keywords"])
              for key, profile in CATALOG["industries"].items()}
    key = max(scores, key=scores.get)
    if not scores[key]:
        key = "general"
    profile = dict(CATALOG["industries"][key])
    difficulty = profile["default_difficulty"]
    if any(k in blob for k in ("양자", "분자", "나노", "quantum", "nanoscale", "tunneling")):
        difficulty = "frontier"
    return dict(profile, industry_id=key, difficulty=difficulty,
                policy=CATALOG["difficulties"][difficulty], source="keyword_catalog",
                confidence="tentative", alternatives=[k for k, v in scores.items() if v and k != key])

def context(state, node):
    profile = state.scratch.get("industry_profile", {})
    if not profile or node in ("s0_bootstrap", "s0_deep_dive"):
        return ""
    # Blind reviewers receive factual domain constraints, never TRIZ reasoning.
    brief = state.scratch.get("deep_dive", {})
    if node.startswith("s8_review") or node == "s7_gate":
        brief = {k: brief[k] for k in ("confirmed_facts", "unknowns", "answers") if k in brief}
    if node.startswith(("s5_merge", "s6_")):
        brief = dict(brief, retrieved_evidence=[{"title": r["title"], "identifier": r["identifier"],
            "snippet": r["snippet"], "scope": r.get("scope", "")}
            for r in state.scratch.get("evidence_candidates", [])[:8]])
    return "\n[산업별 분석 계약]\n" + json.dumps({
        "industry": profile.get("label"), "difficulty": profile.get("difficulty"),
        "disciplines": profile.get("disciplines"), "theories": profile.get("theories"),
        "depth": profile.get("policy", {}).get("depth"), "brief": brief,
    }, ensure_ascii=False, separators=(",", ":")) + (
        "\n관련 물리·화학·공학 이론의 적용 조건과 배제 이유를 구분하라. "
        "첨부·사용자 관측만 확인 사실로 취급한다. 미측정 수치와 인과관계는 가설이며 "
        "단위·경계조건·반증 실험을 명시한다. 단순히 양자/분자 용어를 덧붙이지 마라.")

def deep_dive(ctx):
    state = ctx.state
    ctx.set_stage("S0_RESEARCH")
    payload = ctx.resume_payload()
    if payload is not None:
        profile = state.scratch["industry_profile"]
        previous_route = (profile["industry_id"], profile["difficulty"])
        chosen = payload.get("industry_id")
        difficulty = payload.get("difficulty", profile["difficulty"])
        if chosen in CATALOG["industries"]:
            profile = dict(CATALOG["industries"][chosen], industry_id=chosen,
                           difficulty=difficulty, policy=CATALOG["difficulties"].get(difficulty,
                           CATALOG["difficulties"]["advanced"]), source="user", confidence="confirmed")
        state.scratch["industry_profile"] = profile
        if previous_route != (profile["industry_id"], profile["difficulty"]):
            old_brief = state.scratch.get("deep_dive", {})
            state.scratch.setdefault("deep_dive_history", []).append(old_brief)
            data = agent.run_agent(ctx, node="s0_deep_dive", label="수정한 산업·난이도 재검토",
                stage="S0_RESEARCH", agent_id="domain_researcher", prompt_id="P_S0_DEEP_DIVE", tier="T2",
                vars={"raw_query": state.raw_query, "profile": profile,
                      "attachments": [{"file": a.filename, "facts": a.extracted_facts} for a in state.intake.attachments]
                          + [{"original_questions": old_brief.get("questions", []), "answers": payload.get("answers", [])}]}, default={}) or {}
            state.scratch["deep_dive"] = data
        state.scratch["deep_dive"]["answers"] = payload.get("answers", [])
        state.scratch["deep_dive"]["skipped"] = bool(payload.get("skip"))
        return
    profile = classify(state.raw_query, state.intake.attachments)
    state.scratch["industry_profile"] = profile
    data = agent.run_agent(ctx, node="s0_deep_dive", label="산업·메커니즘 심층 검토",
        stage="S0_RESEARCH", agent_id="domain_researcher", prompt_id="P_S0_DEEP_DIVE", tier="T2",
        vars={"raw_query": state.raw_query, "profile": profile,
              "attachments": [{"file": a.filename, "facts": a.extracted_facts} for a in state.intake.attachments]},
        default={}) or {}
    state.scratch["deep_dive"] = data
    questions = [q for q in data.get("questions", []) if isinstance(q, dict) and q.get("question")]
    if not questions:
        questions = [{"question": f"{m}을 알려 주세요.", "why_needed": "분석의 경계 조건을 확정합니다."}
                     for m in profile["measurements"]]
    raise HumanInterrupt("CLARIFY", "산업과 분석 깊이를 먼저 확인할게요", {
        "questions": questions[:profile["policy"]["questions"]], "industry_profile": profile,
        "industries": [{"id": k, "label": v["label"]} for k, v in CATALOG["industries"].items()],
        "deep_dive": True}, "S0_RESEARCH")
