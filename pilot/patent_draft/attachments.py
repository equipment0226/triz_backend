"""Bounded local PDF extraction; original bytes remain a private immutable asset."""
import json,subprocess,sys
from pathlib import Path


def extract(content,mime):
    if mime!='application/pdf':
        return {'parse_status':'VISUAL_REVIEW_REQUIRED','pages':[],
                'limitation':'이미지 내용은 아직 읽지 않았습니다. 기술내용과 부호를 별도로 확인해야 합니다.'}
    try:
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('pdf_extract.py'))],input=content,
                              capture_output=True,timeout=15,check=True)
        value=json.loads(result.stdout)
        if value.get('parse_status') not in ('TEXT_EXTRACTED','PARTIAL','TEXT_UNAVAILABLE'):
            raise ValueError('invalid parser result')
        return value
    except (subprocess.SubprocessError,ValueError):
        return {'parse_status':'TEXT_UNAVAILABLE','pages':[],
                'limitation':'원문 텍스트를 읽지 못했습니다. 검색 결과 없음이나 검토 완료로 처리하지 않습니다.'}
