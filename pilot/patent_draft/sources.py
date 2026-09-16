"""Reference → raw cache → local ANN/SQL → targeted KR detail; never reindex."""
import base64
import hashlib
import json
import os
import re
import logging
from xml.etree import ElementTree as ET
import httpx
from sqlalchemy import select, insert
from .domain import PatentError, canonical
from .repository import cache, now


class SecretQueryFilter(logging.Filter):
    def filter(self,record):
        message=record.getMessage()
        if re.search(r'(?i)servicekey(?:=|%3d)',message):
            record.msg=re.sub(r'(?i)(servicekey(?:=|%3d))[^&\s\"\']+',r'\1[REDACTED]',message)
            record.args=()
        return True


for _logger in ('httpx','httpcore','httpcore.http11','httpcore.http2'):
    logging.getLogger(_logger).addFilter(SecretQueryFilter())


PUBLIC_FIELDS=frozenset({'provider','application_number','status','raw_xml_base64','raw_sha256',
    'parsed_fields','parser_version','fulltext_coverage','translation','fetched_ms','origin'})


def public_document(value):
    if set(value)!=PUBLIC_FIELDS or value.get('origin')!='EXTERNAL_PATENT' or value.get('provider')!='KIPRIS':
        raise PatentError('PUBLIC_CACHE_SCOPE','공개 원문 이외의 자료는 공유 캐시에 저장할 수 없습니다.',422)
    try:
        raw=base64.b64decode(value['raw_xml_base64'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=value['raw_sha256'] or not value['parsed_fields']:
            raise ValueError()
    except (ValueError,TypeError,KeyError):
        raise PatentError('PUBLIC_CACHE_INTEGRITY','공개 원문의 무결성을 확인할 수 없습니다.',503) from None
    return value


def publication_number(ref):
    value=ref.get('publication_number') or ref.get('identifier') or ''
    match=re.fullmatch(r'([A-Z]{2})-?(\d+)-?([A-Z]\d?)',value)
    return '-'.join(match.groups()) if match else None


class Kipris:
    # Official KIPRIS operation spelling includes Sevice (not Service).
    endpoint = 'https://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getBibliographyDetailInfoSearch'

    def __init__(self, transport=None):
        self.transport = transport

    def detail(self, application_number):
        if not re.fullmatch(r'(10|20)\d{11}', application_number):
            raise PatentError('SOURCE_IDENTIFIER', 'KR 출원번호 13자리가 필요합니다.', 422)
        key = os.getenv('KIPRIS_API_KEY', '')
        if not key:
            raise PatentError('KIPRIS_UNAVAILABLE', 'KIPRIS_API_KEY가 설정되지 않았습니다.', 503)
        try:
            with httpx.Client(transport=self.transport, timeout=30, follow_redirects=False) as c:
                with c.stream('GET', self.endpoint, params=[('applicationNumber', application_number), ('ServiceKey', key)]) as r:
                    if r.status_code != 200:
                        raise ValueError('HTTP')
                    data = bytearray()
                    for chunk in r.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 4_000_000:
                            raise ValueError('size')
            raw = bytes(data)
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ValueError('unsafe XML')
            root = ET.fromstring(raw)
            codes = [x.text for x in root.iter() if x.tag.split('}')[-1] in ('resultCode', 'returnReasonCode')]
            if codes and any(x not in ('00', '0', '000') for x in codes):
                raise PatentError('KIPRIS_SERVICE_ERROR', 'KIPRIS 이용 권한 또는 서비스 응답을 확인해야 합니다.', 503)
            values = {}
            for node in root.iter():
                if len(node) == 0 and node.text and node.text.strip():
                    values.setdefault(node.tag.split('}')[-1], []).append(node.text.strip())
            if not any(k in values for k in ('inventionTitle', 'applicationNumber', 'inventionTitleEng', 'inventionTitleKor')):
                raise PatentError('KIPRIS_EMPTY', '해당 출원번호의 상세 문헌을 찾지 못했습니다.', 404)
            return {'provider': 'KIPRIS', 'application_number': application_number, 'status': 'OK',
                    'raw_xml_base64': base64.b64encode(raw).decode(), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                    'parsed_fields': values, 'parser_version': 'kipris-bibliography-v1',
                    'fulltext_coverage': 'DETAIL_FIELDS_ONLY', 'translation': None,
                    'fetched_ms': now(), 'origin': 'EXTERNAL_PATENT'}
        except PatentError:
            raise
        except Exception:
            # Exception URLs may contain ServiceKey; never propagate raw errors.
            raise PatentError('KIPRIS_UNAVAILABLE', 'KIPRIS 상세 조회에 실패했습니다. 검색 결과 없음과 구분합니다.', 503, True) from None


class SourceService:
    def __init__(self, repository, kipris=None):
        self.repo = repository
        self.kipris = kipris or Kipris()

    def cache_read(self, application_number):
        with self.repo.engine.connect() as c:
            body = c.execute(select(cache.c.body).where(cache.c.cache_key == 'kr-detail:'+application_number)).scalar()
        return public_document(json.loads(body)) if body else None

    def enrich(self, application_number, issue_id, missing_fields):
        if not issue_id or not missing_fields or len(missing_fields) > 10:
            raise PatentError('ENRICHMENT_SCOPE', '보강할 쟁점과 누락 필드를 지정해야 합니다.', 422)
        existing = self.cache_read(application_number)
        if existing:
            return {**existing, 'reused_cache': True}
        value = public_document(self.kipris.detail(application_number))
        # Public provider response only; no query, case IDs or private analysis.
        with self.repo.engine.begin() as c:
            key = 'kr-detail:'+application_number
            if c.execute(select(cache.c.cache_key).where(cache.c.cache_key == key)).first() is None:
                c.execute(insert(cache).values(cache_key=key, body=canonical(value), fetched_ms=now()))
        return value

    def local(self, queries, source_refs):
        from triz.tools import vector_patents as vector
        from triz import patent_corpus as corpus
        if not queries or len(queries) > 4 or any(not isinstance(q, str) or len(q) > 1000 for q in queries):
            raise PatentError('SEARCH_SCOPE', '최대 4개의 구체적인 검색식이 필요합니다.', 422)
        reused = [dict(ref, reused=True) for ref in source_refs]
        cached=[]
        for ref in reused:
            number=ref.get('application_number')
            if isinstance(number,str) and re.fullmatch(r'(10|20)\d{11}',number):
                value=self.cache_read(number)
                if value:cached.append(value)
        numbers=list(dict.fromkeys(n for ref in reused if (n:=publication_number(ref))))[:50]
        # Exact IDs only; restore the stored full abstract and bibliographic fields.
        try:
            documents=corpus.fetch(numbers) if numbers else {}
        except Exception:
            documents={}
        reused=[self.hydrate(ref,documents.get(publication_number(ref))) for ref in reused]
        # Complete linked detailed documents satisfy this retrieval pass. The
        # remaining search limits stay explicit; this is never a novelty verdict.
        if reused and all(ref.get('application_number') in {v['application_number'] for v in cached} for ref in reused):
            return {'references':reused,'hits':[],'cached_details':cached,'queries':queries,
                'diagnostics':[{'status':'PARTIAL','reason':'LINKED_DETAILS_REUSED','additional_search':'NOT_SEARCHED'}],
                'status':'PARTIAL','scope':'SOURCE_REFERENCES_AND_PUBLIC_CACHE',
                'fulltext_coverage':'DETAIL_FIELDS_ONLY','legal_opinion':None,'fto_performed':False}
        results = vector.search_batch(queries, k=6)
        hits, diagnostics = [], []
        for records, info in results:
            diagnostics.append(info)
            hits.extend(records)
        numbers=list(dict.fromkeys(n for ref in hits if (n:=publication_number(ref))))[:24]
        try:
            documents=corpus.fetch(numbers) if numbers else {}
        except Exception:
            documents={}
            diagnostics.append({'status':'UNAVAILABLE','reason':'BIBLIOGRAPHY_UNAVAILABLE'})
        hits=[self.hydrate(ref,documents.get(publication_number(ref))) for ref in hits]
        return {'references': reused, 'hits': hits, 'cached_details':cached,'queries': queries, 'diagnostics': diagnostics,
                'status': 'UNAVAILABLE' if all(d['status'] == 'UNAVAILABLE' for d in diagnostics) else
                          'PARTIAL' if any(d['status'] in ('PARTIAL', 'UNAVAILABLE') for d in diagnostics) else
                          'OK' if hits or reused else 'EMPTY',
                'scope': 'GLOBAL_ALL_INDUSTRIES_ANN', 'fulltext_coverage': 'TITLE_ABSTRACT_ONLY',
                'legal_opinion': None, 'fto_performed': False}

    @staticmethod
    def hydrate(ref,document):
        if not document:return {**ref,'bibliography_status':'UNVERIFIED'}
        allowed=('publication_number','publication_date','filing_date','priority_date','application_number',
                 'country_code','kind_code','family_id','title','abstract','cpc','ipc')
        value={k:document[k] for k in allowed if k in document}
        number=value.get('publication_number','')
        if not value.get('kind_code') and re.fullmatch(r'[A-Z]{2}-\d+-[A-Z]\d?',number):
            value['kind_code']=number.rsplit('-',1)[-1]
        return {**ref,**value,'bibliography_status':'LOCAL_SOURCE','fulltext_coverage':'TITLE_ABSTRACT_ONLY'}
