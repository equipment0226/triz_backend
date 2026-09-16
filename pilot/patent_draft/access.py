"""Closed user test. Identity comes from the existing verified account record."""
from .domain import PatentError

TESTER_EMAIL = 'equipment0226@gmail.com'
PREPARING = '준비 중 입니다.'


def require_tester(legacy, owner):
    if not owner or not legacy.is_patent_tester(owner):
        raise PatentError('PATENT_TEST_RESTRICTED', PREPARING, 403)
    return owner
