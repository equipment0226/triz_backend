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
    """Return exact state paths and the original question alongside each answer.

    Attachment extracted_facts, model frames, constraints, chosen candidates and
    deep-dive confirmed_facts never authenticate a new USER constraint. Bare
    legacy deep-dive answers without preserved question context are excluded.
    """
    sources = {}

    def add(path, text, question=''):
        if _text(text) and isinstance(question, str):
            sources[path] = {'text': text, 'question': question}

    add('raw_query', _get(state, 'raw_query'))
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
