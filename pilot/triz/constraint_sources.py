"""Direct user evidence for new constraints, separate from generated summaries.

Path/quote validation establishes provenance only. Independent semantic review
must still check scope, numbers, negation, hypothetical language and amendments.
"""
from collections.abc import Mapping

MAX_QUOTE_CHARS = 8192
MIN_CONTEXTUAL_QUOTE_CHARS = 8


def _get(value, key, default=None):
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def user_constraint_sources(state):
    """Return direct sources, original questions and the raw-query display alias.

    Attachment extracted_facts, model frames, constraints, chosen candidates and
    deep-dive confirmed_facts never authenticate a new USER constraint. Bare
    legacy deep-dive answers without preserved question context are excluded.
    """
    sources = {}

    def add(path, text, question=''):
        if _text(text) and isinstance(question, str):
            sources[path] = {'text': text, 'question': question}

    add('raw_query', _get(state, 'raw_query'))
    if 'raw_query' in sources:
        # facts_packet.observations.user_query is a presentation name for the
        # same original state.raw_query, never another independent source.
        sources['raw_query']['canonical_path'] = 'raw_query'
        sources['user_query'] = dict(sources['raw_query'])
    intake = _get(state, 'intake')
    turns = _get(intake, 'clarify_turns', [])
    if isinstance(turns, list):
        for index, turn in enumerate(turns):
            question = _get(turn, 'question', '')
            if _get(turn, 'answered') is True and _text(question):
                add(f'intake.clarify_turns[{index}].user_answer',
                    _get(turn, 'user_answer'), question)
    confirm = _get(state, 'confirm')
    amendments = _get(confirm, 'user_amendments', [])
    if isinstance(amendments, list):
        for index, amendment in enumerate(amendments):
            add(f'confirm.user_amendments[{index}]', amendment)
    scratch = _get(state, 'scratch', {})
    brief = _get(scratch, 'deep_dive', {})
    answer_turns = _get(brief, 'answer_turns', [])
    if isinstance(answer_turns, list) and _get(brief, 'skipped') is not True:
        for index, turn in enumerate(answer_turns):
            question = _get(turn, 'question', '')
            if isinstance(turn, Mapping) and _text(question):
                add(f'scratch.deep_dive.answer_turns[{index}].answer',
                    turn.get('answer'), question)
    return sources


def validate_user_constraint_source(row, sources):
    """Return provenance errors; an empty list is not a semantic PASS.

    Short complete answers such as '10%' are useful only together with their
    preserved question. A short fragment cut out of a longer answer is rejected.
    No Unicode, whitespace, number or punctuation normalization is performed.
    """
    if not isinstance(row, Mapping) or not isinstance(sources, Mapping):
        return ['FATAL-CONSTRAINT-SOURCE: 제약 행과 직접 사용자 근거 목록이 객체여야 한다.']
    path, quote = row.get('source_path'), row.get('source_quote')
    if not isinstance(path, str) or path not in sources:
        return ['FATAL-CONSTRAINT-SOURCE: source_path가 허용된 직접 사용자 원문 경로가 아니다.']
    item = sources[path]
    if (not isinstance(item, Mapping) or not _text(item.get('text'))
            or not isinstance(item.get('question', ''), str)):
        return ['FATAL-CONSTRAINT-SOURCE: 원문 또는 질문 맥락을 확인할 수 없다.']
    if not _text(quote) or len(quote) > MAX_QUOTE_CHARS:
        return ['FATAL-CONSTRAINT-SOURCE: source_quote에 길이 1~8192의 비어 있지 않은 원문 인용이 필요하다.']
    original = item['text']
    if quote not in original:
        return ['FATAL-CONSTRAINT-SOURCE: source_quote가 선택한 사용자 원문의 정확한 연속 인용과 일치하지 않는다.']
    compact = quote.strip()
    contextual_answer = (_text(item.get('question')) and compact == original.strip())
    has_words = any(character.isalpha() for character in compact)
    complete_short_statement = compact == original.strip() and len(compact) >= 4 and has_words
    if not contextual_answer and not complete_short_statement and (
            len(compact) < MIN_CONTEXTUAL_QUOTE_CHARS or not has_words):
        return ['FATAL-CONSTRAINT-SOURCE: 숫자·단어 조각만 인용하지 말고 조건과 범위가 드러나는 원문을 인용하라. 짧은 답변은 질문 맥락과 함께 답변 전체를 인용하라.']
    return []


def constraint_source_facts(data, sources):
    """Bounded exact provenance facts for semantic reviewers, not a PASS gate.

    A matching path and quote authenticate only the citation. They do not prove
    that the quote requires the claimed constraint or that its scope is valid.
    """
    groups = []
    if isinstance(data, Mapping):
        constraints = data.get('constraints')
        if isinstance(constraints, list):
            groups.append(('constraints', constraints))
        elif isinstance(constraints, Mapping):
            groups.extend((('constraints.items', constraints.get('items')),
                           ('constraints.baseline_facts', constraints.get('baseline_facts'))))
        groups.append(('user_constraints', data.get('user_constraints')))
        groups.append(('baseline_facts', data.get('baseline_facts')))
    rows = []
    count = 0
    for array, values in groups:
        if not isinstance(values, list):
            continue
        for index, row in enumerate(values):
            count += 1
            if len(rows) >= 40:
                continue
            row = row if isinstance(row, Mapping) else {}
            path, quote = row.get('source_path'), row.get('source_quote')
            item = sources.get(path) if isinstance(sources, Mapping) and isinstance(path, str) else None
            known = isinstance(item, Mapping) and _text(item.get('text'))
            exact = bool(known and _text(quote) and quote in item['text'])
            canonical = item.get('canonical_path', path) if known else None
            rows.append({'array': array, 'index': index,
                'id': row['id'][:160] if isinstance(row.get('id'), str) else None,
                'source_path': path[:240] if isinstance(path, str) else None,
                'canonical_path': canonical, 'path_exists': bool(known),
                'quote_exact_match': exact,
                'provenance_valid': not validate_user_constraint_source(row, sources)})
    return {'source': 'deterministic_primary_source_inspection',
        'source_aliases': {'user_query': 'raw_query'} if isinstance(sources, Mapping) and 'user_query' in sources else {},
        'canonical_path_preference': 'raw_query', 'semantic_claim_validated': False,
        'row_count': count, 'rows': rows, 'rows_truncated': count > len(rows)}
