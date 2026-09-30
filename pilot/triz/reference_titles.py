"""Keep published paper/patent titles separate from translated product prose."""
import hashlib
import re
from collections.abc import Mapping

TITLE_FIELDS = frozenset(('title', 'original_title', 'source_title'))


def _get(record, key, default=None):
    return record.get(key, default) if isinstance(record, Mapping) else getattr(record, key, default)


def is_reference(record):
    return (_get(record, 'source_type') in ('PATENT', 'PAPER') or
            _get(record, 'kind') in ('PATENT', 'PAPER', '특허', '논문'))


def title(record):
    """Use a stored original when available; never infer or back-translate it."""
    return next((value for key in ('original_title', 'source_title', 'title')
                 if isinstance(value := _get(record, key), str) and value), '')


def protected_fields(record):
    return TITLE_FIELDS if is_reference(record) else frozenset()


def for_state(state):
    titles = set()
    def collect(value):
        if is_reference(value) and title(value):
            titles.add(title(value))
        if isinstance(value, Mapping):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)
    collect(state.evidence)
    for key in ('principle_patents', 'patent_additions', 'related_references'):
        collect(state.scratch.get(key, []))
    return titles


def transform_prose(text, titles, transform):
    """Mask exact source titles while the existing whole-document rules run."""
    if not titles:
        return transform(text)
    # Markdown tables escape pipes and flatten embedded line breaks. These are
    # rendering forms of the same stored title, not translated alternatives.
    titles = set(titles) | {re.sub(r'\s*\n\s*', ' ', value).replace('|', r'\|') for value in titles}
    pattern = re.compile('|'.join(re.escape(value) for value in sorted(titles, key=len, reverse=True)))
    replacements = {}
    def protect(match):
        value = match[0]
        marker = 'TRIZREFERENCETITLE' + hashlib.sha256(value.encode()).hexdigest() + 'END'
        while marker in text:
            marker += 'X'
        replacements[marker] = value
        return marker
    result = transform(pattern.sub(protect, text))
    for marker, value in replacements.items():
        result = result.replace(marker, value)
    return result
