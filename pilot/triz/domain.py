"""Bounded industry routing and a pre-definition deep-dive interview."""
import json
import re
from . import agent, prompts_registry as P
from .context import HumanInterrupt
from .settings import settings

CATALOG = settings._load_yaml("industries.yaml")
TYPES = {"PHYSICAL_TECHNICAL", "INFORMATION_SOFTWARE", "ORGANIZATIONAL_BUSINESS", "MIXED"}


def problem_type(state):
    if state.domain.problem_type in TYPES:
        return state.domain.problem_type
    if not state.domain.is_engineering:
        return "ORGANIZATIONAL_BUSINESS"
    return classify(state.raw_query, state.intake.attachments)["problem_type"]


def physical_allowed(state):
    kind = problem_type(state)
    return kind == "PHYSICAL_TECHNICAL" or (kind == "MIXED" and bool(state.domain.physical_scope))


def normalize_brief(data, profile):
    hypotheses = [h for h in data.get("competing_hypotheses", []) if isinstance(h, dict)]
    for i, hypothesis in enumerate(hypotheses):
        hypothesis["id"] = f"H{i+1}"
    data["competing_hypotheses"] = hypotheses[:profile["policy"]["hypothesis_limit"]]
    return data


def select_tracks(state, tracks):
    selected = list(dict.fromkeys(tracks))
    if not physical_allowed(state):
        selected = [t for t in selected if t not in ("C_STANDARDS", "H_EFFECTS")]
        if state.control.mode.value != "LITE" and "G_FOS" not in selected:
            selected.append("G_FOS")
    return selected


def sync_contract(state, data=None):
    """One problem-type contract; industry remains contextual metadata."""
    data = data or {}
    profile = state.scratch.get("industry_profile") or classify(state.raw_query, state.intake.attachments)
    kind = data.get("problem_type")
    if kind not in TYPES:
        kind = state.domain.problem_type if state.domain.problem_type in TYPES else (
            profile.get("problem_type") or classify(state.raw_query, state.intake.attachments)["problem_type"])
        if data.get("is_engineering") is False and kind != "INFORMATION_SOFTWARE":
            kind = "ORGANIZATIONAL_BUSINESS"
    difficulty = data.get("difficulty")
    if profile.get("source") == "user":
        difficulty = profile.get("difficulty")
    if difficulty not in CATALOG["difficulties"]:
        difficulty = profile.get("difficulty", "advanced")
    state.domain.problem_type = kind
    state.domain.difficulty = difficulty
    state.domain.is_engineering = kind in ("PHYSICAL_TECHNICAL", "MIXED")
    state.domain.physical_scope = str(data.get("physical_scope", state.domain.physical_scope) or "")
    profile = dict(profile, problem_type=kind, difficulty=difficulty,
                   policy=CATALOG["difficulties"][difficulty])
    if kind in ("ORGANIZATIONAL_BUSINESS", "INFORMATION_SOFTWARE"):
        reference = CATALOG["industries"]["business" if kind == "ORGANIZATIONAL_BUSINESS" else "software"]
        for field in ("disciplines", "theories", "measurements", "transfer_domains", "roles"):
            profile[field] = reference[field]
    state.scratch["industry_profile"] = profile
    return profile

def classify(query, attachments=()):
    blob = (query + " " + " ".join(a.extracted_text[:3000] for a in attachments)).lower()
    scores = {key: sum(bool(re.search(r"(?<![a-z])" + re.escape(k.lower()) + r"(?![a-z])", blob))
                       for k in profile["keywords"])
              for key, profile in CATALOG["industries"].items()}
    key = max(scores, key=scores.get)
    if not scores[key]:
        key = "general"
    profile = dict(CATALOG["industries"][key])
    org = any(k in blob for k in ("성과급", "협업", "인사평가", "자율성", "인센티브", "보상", "조직", "마케팅", "유료 전환", "incentive", "employee", "cooperation"))
    software = key == "software"
    kind = "ORGANIZATIONAL_BUSINESS" if org or key == "business" else "INFORMATION_SOFTWARE" if software else "PHYSICAL_TECHNICAL"
    difficulty = "advanced"
    if key == "general" and not org and len(blob.strip()) < 30:
        difficulty = "routine"
    if not org and any(k in blob for k in ("양자", "분자", "나노", "미세", "식각", "quantum", "nanoscale", "tunneling")):
        difficulty = "frontier"
    if sum(k in blob for k in ("실패", "상충", "동시에", "불확실", "재현", "failed", "uncertain")) >= 3:
        difficulty = "frontier"
    if kind == "ORGANIZATIONAL_BUSINESS":
        for field in ("disciplines", "theories", "measurements", "transfer_domains", "roles"):
            profile[field] = CATALOG["industries"]["business"][field]
    return dict(profile, industry_id=key, problem_type=kind, difficulty=difficulty,
                policy=CATALOG["difficulties"][difficulty], source="keyword_catalog",
                confidence="tentative", alternatives=[k for k, v in scores.items() if v and k != key])

def context(state, node):
    from .digest import target_system
    profile = state.scratch.get("industry_profile", {})
    if not profile or node in ("s0_bootstrap", "s0_deep_dive"):
        return ""
    # Blind reviewers receive factual domain constraints, never TRIZ reasoning.
    brief = state.scratch.get("deep_dive", {})
    if node.startswith(("s8_review", "s7_gate")):
        brief = {k: brief[k] for k in ("confirmed_facts", "unknowns", "answers", "answer_turns") if k in brief}
    elif state.scratch.get("domain_assumptions"):
        brief = dict(brief, unconfirmed_practices=state.scratch["domain_assumptions"])
    kind = problem_type(state)
    instruction = {
        "ORGANIZATIONAL_BUSINESS": "행위자·정보·권한·유인·제도·행동의 인과관계로 분석한다. 산업 배경 때문에 장치·재료·물리적 힘을 가정하지 마라. 심리와 행동도 관측 없이는 가설이다.",
        "INFORMATION_SOFTWARE": "요청·데이터·상태·큐·일관성·정보 흐름의 작동 조건을 분석한다. 물리 장치나 입자 비유를 강요하지 마라.",
        "PHYSICAL_TECHNICAL": "관련 물리·화학·공학 이론의 적용 조건과 배제 이유를 구분한다. 지배 메커니즘이 확인되지 않으면 미시·양자 효과를 원인으로 단정하지 마라.",
        "MIXED": "사람·제도·정보·물리 계층을 구분한다. 물질·장·Effects는 명시된 physical_scope 안에만 적용한다.",
    }[kind]
    return "\n[산업별 분석 계약]\n" + json.dumps({
        "industry": profile.get("label"), "problem_type": kind,
        "physical_scope": state.domain.physical_scope, "difficulty": profile.get("difficulty"),
        "confirmed_boundary": target_system(state), "user_amendments": state.confirm.user_amendments,
        "operative_zone": state.confirm.operative_zone, "operative_time": state.confirm.operative_time,
        "disciplines": profile.get("disciplines"), "theories": profile.get("theories"),
        "depth": profile.get("policy", {}).get("depth"), "brief": brief,
    }, ensure_ascii=False, separators=(",", ":")) + (
        "\n" + instruction + " "
        "첨부·사용자 관측만 확인 사실로 취급한다. 미측정 수치와 인과관계는 가설이며 "
        "단위·경계조건·반증 실험을 명시한다. 단순히 양자/분자 용어를 덧붙이지 마라.")

def deep_dive(ctx):
    state = ctx.state
    ctx.set_stage("S0_RESEARCH")
    payload = ctx.resume_payload()
    if payload is not None:
        original_questions = state.scratch.get("deep_dive", {}).get("questions", [])
        profile = state.scratch["industry_profile"]
        previous_route = (profile["industry_id"], profile["difficulty"])
        chosen = payload.get("industry_id")
        difficulty = payload.get("difficulty", profile["difficulty"])
        if chosen in CATALOG["industries"]:
            profile = dict(CATALOG["industries"][chosen], industry_id=chosen,
                           difficulty=difficulty, policy=CATALOG["difficulties"].get(difficulty,
                           CATALOG["difficulties"]["advanced"]), source="user", confidence="confirmed")
        state.scratch["industry_profile"] = profile
        profile = sync_contract(state, {"problem_type": state.domain.problem_type, "difficulty": difficulty})
        if previous_route != (profile["industry_id"], profile["difficulty"]):
            old_brief = state.scratch.get("deep_dive", {})
            state.scratch.setdefault("deep_dive_history", []).append(old_brief)
            data = agent.run_agent(ctx, node="s0_deep_dive", label="수정한 산업·난이도 재검토",
                stage="S0_RESEARCH", agent_id="domain_researcher", prompt_id="P_S0_DEEP_DIVE", tier="T2",
                vars={"raw_query": state.raw_query, "profile": profile,
                      "attachments": [{"file": a.filename, "facts": a.extracted_facts} for a in state.intake.attachments]
                          + [{"original_questions": old_brief.get("questions", []), "answers": payload.get("answers", [])}]}, default={}) or {}
            state.scratch["deep_dive"] = normalize_brief(data, profile)
        state.scratch.setdefault("deep_dive", {})["answers"] = payload.get("answers", [])
        state.scratch["deep_dive"]["answer_turns"] = [
            {"question": q.get("question", ""), "answer": a}
            for q, a in zip(original_questions, payload.get("answers", [])) if isinstance(q, dict)]
        state.scratch["deep_dive"]["skipped"] = bool(payload.get("skip"))
        return
    profile = sync_contract(state)
    data = agent.run_agent(ctx, node="s0_deep_dive", label="산업·메커니즘 심층 검토",
        stage="S0_RESEARCH", agent_id="domain_researcher", prompt_id="P_S0_DEEP_DIVE", tier="T2",
        vars={"raw_query": state.raw_query, "profile": profile,
              "attachments": [{"file": a.filename, "facts": a.extracted_facts} for a in state.intake.attachments]},
        default={}) or {}
    state.scratch["deep_dive"] = normalize_brief(data, profile)
    questions = [q for q in data.get("questions", []) if isinstance(q, dict) and q.get("question")]
    if not questions:
        questions = [{"question": f"{m}을 알려 주세요.", "why_needed": "분석의 경계 조건을 확정합니다."}
                     for m in profile["measurements"]]
    state.scratch["deep_dive"]["questions"] = questions[:profile["policy"]["questions"]]
    raise HumanInterrupt("CLARIFY", "산업과 분석 깊이를 먼저 확인할게요", {
        "questions": questions[:profile["policy"]["questions"]], "industry_profile": profile,
        "industries": [{"id": k, "label": v["label"]} for k, v in CATALOG["industries"].items()],
        "deep_dive": True}, "S0_RESEARCH")
