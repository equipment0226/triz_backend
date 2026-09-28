"""Validate project names and retry a small title extraction independently."""
import re

PENDING_TITLE = '입력 조건 확인 및 문제 정의'
_GREETING = re.compile(r'^(?:안녕하세요|안녕하십니까|반갑습니다|감사합니다|수고하십니다|'
                       r'(?:hello|hi|greetings)(?=\s|[,!.?·]|$))', re.I)
_AUTOMATIC_SOURCES = {'bootstrap', 'title_extraction', 'structured_fallback'}
_BEAM_NAMES = {
    'EBEAM': re.compile(r'(?<![A-Za-z0-9])e[\s-]?beam(?![A-Za-z0-9])|전자\s*빔', re.I),
    'EUV': re.compile(r'(?<![A-Za-z0-9])euv(?![A-Za-z0-9])|극자외선', re.I),
}
_NEGATED_TECHNOLOGY = re.compile(
    r'^\s*(?:은|는|이|가|을|를)?\s*(?:아니(?:라|고|며|다|라고|에요)|아닌|아닙니다|말고)')


def _beam_technologies(text):
    """Recognize explicit names; never treat a process node as a beam type."""
    text = str(text or '')
    present = set()
    for name, pattern in _BEAM_NAMES.items():
        for match in pattern.finditer(text):
            if (_NEGATED_TECHNOLOGY.match(text[match.end():]) or
                    re.search(r'\bnot\s*$', text[:match.start()], re.I)):
                continue
            present.add(name)
    return present


def _confirmed(state):
    value = getattr(state, 'confirm', None)
    return value.model_dump() if hasattr(value, 'model_dump') else value or {}


def _beam_identity(state):
    confirmed = _confirmed(state)
    # An explicit amendment wins an earlier candidate and original wording.
    for amendment in reversed(confirmed.get('user_amendments') or []):
        names = _beam_technologies(amendment)
        mentioned = {name for name, pattern in _BEAM_NAMES.items() if pattern.search(str(amendment))}
        # Merely mentioning the wafer's EUV process in an amendment must not
        # override a confirmed E-beam inspection system. Require an explicit
        # contrast/negation, or an answer consisting of the technology name.
        bare_name = any(pattern.fullmatch(str(amendment).strip(' .!')) for pattern in _BEAM_NAMES.values())
        if len(names) == 1 and (len(mentioned) > 1 or bare_name):
            return next(iter(names))
    if confirmed.get('user_confirmed') and confirmed.get('chosen_candidate_id'):
        for candidate in confirmed.get('candidates') or []:
            if isinstance(candidate, dict) and candidate.get('id') == confirmed['chosen_candidate_id']:
                names = _beam_technologies(candidate.get('name'))
                if len(names) == 1:
                    return next(iter(names))
    source_names = _beam_technologies(state.raw_query)
    if len(source_names) == 1:
        return next(iter(source_names))
    # In mixed input, S1 may identify the actual inspection system while EUV
    # describes the wafer's fabrication process. Only use a source-backed name.
    target_names = _beam_technologies(getattr(state.domain, 'target_system', ''))
    if len(target_names) == 1 and target_names <= source_names:
        return next(iter(target_names))
    return None


def identity_title(state, title):
    """Ground a generated label without rewriting any scientific artifacts."""
    if not isinstance(title, str):
        return title
    expected = _beam_identity(state)
    if not expected or expected in _beam_technologies(title):
        return title
    other = 'EUV' if expected == 'EBEAM' else 'EBEAM'
    # A title which names both the process and inspection beam is already
    # unambiguous. Correct only a conflicting, sole beam label.
    return _BEAM_NAMES[other].sub(expected, title, count=1)


def needs_identity_projection(title):
    return isinstance(title, str) and any(p.search(title) for p in _BEAM_NAMES.values())


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
    names = _beam_technologies(query)
    title_names = _beam_technologies(text)
    return (not (len(names) == 1 and title_names - names) and
            4 <= len(text) <= 40 and '\n' not in text and not _GREETING.match(text) and
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
                    return identity_title(state, title)
    for key in ('target_system', 'sub_domain', 'super_system'):
        title = _system_title(getattr(state.domain, key, ''))
        if title:
            return identity_title(state, title)
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
    if source in _AUTOMATIC_SOURCES:
        title = identity_title(state, title)
    if source == 'structured_fallback' or (not source and _legacy_greeting_fallback(title, state.raw_query)):
        replacement = fallback_title(state)
        return replacement if replacement != PENDING_TITLE else title
    return title


def refresh_fallback_title(state):
    """Refresh generated names when intake or user confirmation grounds them."""
    if state.report or state.scratch.get('title_source') not in _AUTOMATIC_SOURCES:
        return
    previous = state.scratch.get('title')
    corrected = identity_title(state, previous)
    if corrected != previous:
        state.scratch.setdefault('title_history', []).append(dict(
            previous_title=previous, title=corrected, reason='confirmed_problem_identity'))
        state.scratch['title'] = corrected
    if state.scratch.get('title_source') != 'structured_fallback':
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
    if st.scratch.get('title_source') == 'custom' and valid_title(st.scratch.get('title')):
        return st.scratch['title'].strip()
    supplied = candidate is not None
    candidate = candidate if candidate is not None else st.scratch.get('title')
    candidate = identity_title(st, candidate)
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
            candidate = identity_title(st, candidate)
            if valid_title(candidate, st.raw_query):
                st.scratch['title_source'] = 'title_extraction'
                return candidate.strip()
        except ProviderUnavailable:
            raise
        except (llm.LLMError, AbortRun):
            continue
    st.scratch['title_source'] = 'structured_fallback'
    return fallback_title(st)
