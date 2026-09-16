"""Pinned official source bytes; source integrity is not editor validation."""
from pathlib import Path
import hashlib,json
from .domain import PatentError,digest

ROOT=Path(__file__).parent


def load():
    registry=json.loads((ROOT/'config/form_registry.json').read_text(encoding='utf-8'))
    if {f['id'] for f in registry['forms']}!={'form14','form15','form16','form17'}:
        raise PatentError('FORM_REGISTRY_INVALID','필수 공식 서식 등록 정보를 확인해야 합니다.',503)
    files={}
    for item in registry['forms']:
        filename=item['file']
        if filename!=f"form-{item['id'][4:]}.pdf":
            raise PatentError('FORM_REGISTRY_INVALID','공식 서식 파일 경로가 잘못됐습니다.',503)
        value=(ROOT/'assets/official'/filename).read_bytes()
        if not value.startswith(b'%PDF-') or hashlib.sha256(value).hexdigest()!=item['sha256']:
            raise PatentError('FORM_SOURCE_CHANGED','고정된 공식 서식 원문의 무결성을 확인할 수 없습니다.',503)
        files['official-reference/'+filename]=value
    return registry,files


def fingerprint():
    registry,_=load()
    return digest(registry)
