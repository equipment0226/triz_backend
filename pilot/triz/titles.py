"""Validate project names and retry a small title extraction independently."""
import re


def valid_title(title, query=''):
    if not isinstance(title, str):
        return False
    text = title.strip()
    return (4 <= len(text) <= 40 and '\n' not in text and
            text not in ('문제 분석', '제목 없음', '새 프로젝트', 'Untitled') and
            not re.search(r'[<>]|\.{3}|…|(?:싶은데|하는데|해서|하며|그리고|때문에)$', text) and
            not re.search(r'(?:합니다|됩니다|싶어요|있습니다)[.!?]?$',text) and
            not (len(query) > len(text) + 10 and query.strip().startswith(text)))


def fallback_title(state):
    # Use complete known terms, never a raw-query character slice.
    system = state.domain.target_system.strip()
    if system and len(system) <= 28:
        return system + ' 개선 과제'
    words = re.findall(r'[가-힣A-Za-z][가-힣A-Za-z0-9-]*', state.raw_query)
    terms = []
    for word in words:
        word = re.sub(r'(에서는|에서|으로|을|를|은|는|이|가)$', '', word)
        if 2 <= len(word) <= 12 and not word.endswith(('는데','싶다','합니다','하고')) and word not in terms:
            if len(' · '.join(terms + [word])) > 25:
                break
            terms.append(word)
        if len(terms) == 3:
            break
    return (' · '.join(terms) + ' 개선 과제') if terms else '입력 조건 확인 및 문제 정의'


def ensure_title(ctx, candidate=None):
    from . import agent, llm, prompts_registry
    from .context import AbortRun
    st = ctx.state
    candidate = candidate if candidate is not None else st.scratch.get('title')
    if valid_title(candidate, st.raw_query):
        return candidate.strip()
    for attempt in range(2):
        try:
            response = agent.tracked_chat(ctx, _node='s0_title_repair', tier='T1',
                system='Extract a concise, grounded project title. Return JSON only.',
                user=prompts_registry.render('P_PROJECT_TITLE', raw_query=st.raw_query,
                    problem=st.intake.frame.restated_problem, previous_title=candidate or ''),
                temperature=0.0, expect='object', max_tokens=512)
            candidate = response.data.get('title') if isinstance(response.data, dict) else None
            if valid_title(candidate, st.raw_query):
                st.scratch['title_source'] = 'title_extraction'
                return candidate.strip()
        except (llm.LLMError, AbortRun):
            continue
    st.scratch['title_source'] = 'structured_fallback'
    return fallback_title(st)
