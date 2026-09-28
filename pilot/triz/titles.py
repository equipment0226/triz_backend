"""Validate project names and retry a small title extraction independently."""
import re

PENDING_TITLE = '입력 조건 확인 및 문제 정의'
_GREETING = re.compile(r'^(?:안녕하세요|안녕하십니까|반갑습니다|감사합니다|수고하십니다|'
                       r'(?:hello|hi|greetings)(?=\s|[,!.?·]|$))', re.I)


def _system_title(value):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    if len(text) > 28:
        # Remove explanatory parentheses before shortening at word boundaries.
        while re.search(r'\([^()]*\)', text):
            text = re.sub(r'\([^()]*\)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
    words = []
    for word in text.split():
        if len(' '.join(words + [word])) > 28:
            break
        words.append(word)
    while words and words[-1] in {'및', '또는', '과', '와', '의', '위한'}:
        words.pop()
    name = ' '.join(words)
    title = name + ' 개선 과제'
    return title if len(name) >= 2 and valid_title(title) else ''


def valid_title(title, query=''):
    if not isinstance(title, str):
        return False
    text = title.strip()
    return (4 <= len(text) <= 40 and '\n' not in text and not _GREETING.match(text) and
            text not in ('문제 분석', '제목 없음', '새 프로젝트', 'Untitled') and
            not re.search(r'[<>]|\.{3}|…|(?:싶은데|하는데|해서|하며|그리고|때문에)$', text) and
            not re.search(r'(?:합니다|됩니다|싶어요|있습니다)[.!?]?$',text) and
            not (len(query) > len(text) + 10 and query.strip().startswith(text)))


def fallback_title(state):
    # Before S1 there may be no identified system. Do not turn greetings,
    # introductions or arbitrary opening words into a technical project name.
    confirmed = getattr(state, 'confirm', None)
    if hasattr(confirmed, 'model_dump'):
        confirmed = confirmed.model_dump()
    if isinstance(confirmed, dict) and confirmed.get('user_confirmed') and confirmed.get('chosen_candidate_id'):
        for candidate in confirmed.get('candidates') or []:
            if isinstance(candidate, dict) and candidate.get('id') == confirmed['chosen_candidate_id']:
                title = _system_title(candidate.get('name'))
                if title:
                    return title
    for key in ('target_system', 'sub_domain', 'super_system'):
        title = _system_title(getattr(state.domain, key, ''))
        if title:
            return title
    return PENDING_TITLE


def fallback_shape(title):
    return isinstance(title, str) and (title == PENDING_TITLE or
        title.endswith(' 개선 과제'))


def _legacy_greeting_fallback(title, query):
    # Old report snapshots did not pin title_source. Recognize only the exact
    # broken formatter output, not an arbitrary title containing a greeting.
    if not fallback_shape(title) or not _GREETING.match(title):
        return False
    terms = []
    for word in re.findall(r'[가-힣A-Za-z][가-힣A-Za-z0-9-]*', query):
        word = re.sub(r'(에서는|에서|으로|을|를|은|는|이|가)$', '', word)
        if 2 <= len(word) <= 12 and not word.endswith(('는데', '싶다', '합니다', '하고')) and word not in terms:
            if len(' · '.join(terms + [word])) > 25:
                break
            terms.append(word)
        if len(terms) == 3:
            break
    return title == ' · '.join(terms) + ' 개선 과제'


def display_title(state):
    """Project a known automatic fallback from saved context without writes."""
    title = state.scratch.get('title') or state.raw_query[:60]
    source = state.scratch.get('title_source')
    if source == 'structured_fallback' or (not source and _legacy_greeting_fallback(title, state.raw_query)):
        replacement = fallback_title(state)
        return replacement if replacement != PENDING_TITLE else title
    return title


def refresh_fallback_title(state):
    """Once intake is available, refresh only provisional automatic titles."""
    if state.report or state.scratch.get('title_source') != 'structured_fallback':
        return
    title = fallback_title(state)
    previous = state.scratch.get('title')
    if title == PENDING_TITLE or title == previous:
        return
    state.scratch.setdefault('title_history', []).append(dict(
        previous_title=previous, reason='structured_intake_available'))
    state.scratch['title'] = title


def ensure_title(ctx, candidate=None):
    from . import agent, llm, prompts_registry
    from .context import AbortRun, ProviderUnavailable
    st = ctx.state
    supplied = candidate is not None
    candidate = candidate if candidate is not None else st.scratch.get('title')
    if valid_title(candidate, st.raw_query):
        if supplied:
            st.scratch['title_source'] = 'bootstrap'
        else:
            st.scratch.setdefault('title_source', 'bootstrap')
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
        except ProviderUnavailable:
            raise
        except (llm.LLMError, AbortRun):
            continue
    st.scratch['title_source'] = 'structured_fallback'
    return fallback_title(st)
