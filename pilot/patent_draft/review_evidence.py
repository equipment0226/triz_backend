"""Resolve exact cited passages in the immutable material supplied to a reviewer."""
from .domain import PatentError


def validate(finding,material,version_to_kind,readset,semantic):
    available=set(readset)
    if not set(finding['affected_artifacts'])<=available or not set(finding['evidence_ids'])<=available:
        raise PatentError('REVIEW_EVIDENCE_INVALID','검토가 입력에 없는 산출물을 인용했습니다.',503)
    if semantic and finding['outcome'] in ('PASS','FAIL','NOT_APPLICABLE') and not finding['source_spans']:
        raise PatentError('REVIEW_EVIDENCE_MISSING','의미 판정에는 실제 검토 원문의 인용 위치가 필요합니다.',503)
    for span in finding['source_spans']:
        try:
            if span['artifact_id'] not in available or not span['pointer'].startswith('/'):
                raise ValueError()
            value=material[version_to_kind[span['artifact_id']]]
            for part in span['pointer'][1:].split('/'):
                key=part.replace('~1','/').replace('~0','~')
                if isinstance(value,list):
                    if not key.isdecimal():raise ValueError()
                    value=value[int(key)]
                elif isinstance(value,dict):
                    value=value[key]
                else:
                    raise ValueError()
            if not isinstance(value,str) or span['excerpt'] not in value:
                raise ValueError()
        except (KeyError,IndexError,ValueError,TypeError):
            raise PatentError('REVIEW_EVIDENCE_INVALID','검토 인용문이 고정된 원문과 일치하지 않습니다.',503) from None
