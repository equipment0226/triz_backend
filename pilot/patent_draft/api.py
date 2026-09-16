"""Owner-only API. Every linked record/download shares the same case ACL."""
import hashlib
import json
import os
import secrets
from fastapi import APIRouter, Depends, Request, Header, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from .domain import Bootstrap, Mutation, PatentError, ident, canonical
from .repository import assets, tasks, cases
from .runtime import service
from .intake import complete as intake_complete, questions as intake_questions, unanswered
from .access import require_tester, PREPARING

router = APIRouter(prefix='/api/patent', tags=['Patent draft'])
internal = APIRouter(prefix='/internal/patent', tags=['Patent worker'])


def principal(request: Request):
    if os.getenv('PATENT_ENABLED', 'false').lower() != 'true':
        raise PatentError('FEATURE_DISABLED', PREPARING, 503)
    user = service().legacy.principal(request.headers.get('x-triz-session', ''))
    if not user:
        raise PatentError('AUTH_REQUIRED',PREPARING,401)
    return require_tester(service().legacy,user)


def operator(authorization: str = Header(default='')):
    token = os.getenv('PATENT_SERVICE_TOKEN', '')
    if not token or not secrets.compare_digest(authorization, 'Bearer '+token):
        raise PatentError('AUTH_REQUIRED', 'Unauthorized', 401)


async def error_handler(request, error):
    return JSONResponse({'code': error.code, 'detail': error.detail, 'retryable': error.retryable,
                         'request_id': ident('preq')}, status_code=error.status)


@router.get('/capabilities')
def capabilities(owner=Depends(principal)):
    return service().capabilities()


@router.get('/source-solutions')
def source_list(owner=Depends(principal), offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
    return service().legacy.list(owner, offset, limit)


@router.get('/source-runs/{run_id}/concepts/{concept_id}/preview')
def preview(run_id: str, concept_id: str, owner=Depends(principal)):
    return service().legacy.preview(owner, run_id, concept_id)


@router.post('/cases', status_code=201)
def create(body: Bootstrap, owner=Depends(principal), idempotency_key: str = Header(default='')):
    return service().open(owner, body.model_dump(), idempotency_key)


@router.get('/cases')
def case_list(owner=Depends(principal), offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=50)):
    return service().repo.list(owner, offset, limit)


@router.get('/cases/{case_id}')
def get_case(case_id: str, owner=Depends(principal)):
    s = service()
    case = s.repo.get(owner, case_id)
    material = s.material(owner, case)
    return {'case': case, 'material': material, 'approvals': s.approvals(owner, case),
            'intake': {'complete': intake_complete(material), 'pending_question_ids': [q['id'] for q in unanswered(material)]},
            'reviews': s.current_reviews(owner, case), 'attachment_requirements': __import__('patent_draft.forms', fromlist=['requirements']).requirements(material.get('facts', {}))}


@router.patch('/cases/{case_id}')
def metadata(case_id: str, body: Mutation, owner=Depends(principal), idempotency_key: str = Header(default='')):
    return service().mutate(owner, case_id, 'metadata', body.model_dump(), idempotency_key)


@router.post('/cases/{case_id}/patches/{patch_id}/apply')
def apply_patch(case_id: str, patch_id: str, body: Mutation, owner=Depends(principal), idempotency_key: str = Header(default='')):
    if body.payload:
        raise PatentError('PATCH_PAYLOAD', '수정안 ID 외에는 전달할 수 없습니다.', 422)
    body.payload = {'patch_id': patch_id}
    return service().mutate(owner, case_id, 'apply-patch', body.model_dump(), idempotency_key)


@router.post('/cases/{case_id}/attachments', status_code=201)
async def attachment(case_id: str, file: UploadFile = File(...), expected_revision: int = Form(...),
                     expected_epoch: int = Form(...), input_snapshot_id: str = Form(...),
                     owner=Depends(principal), idempotency_key: str = Header(default='')):
    data = await file.read(20_000_001)
    # Non-executing evidence files only. No ZIP/XML/SVG/HTML uploads or path input.
    types = {'application/pdf': b'%PDF-', 'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}
    mime = file.content_type or ''
    if len(data) > 20_000_000 or mime not in types or not data.startswith(types[mime]):
        raise PatentError('ATTACHMENT_INVALID', '20MB 이하의 PDF·PNG·JPEG 자료만 첨부할 수 있습니다.', 422)
    name = (file.filename or 'attachment').replace('\\','/').split('/')[-1][:200]
    body = {'expected_revision': expected_revision, 'expected_epoch': expected_epoch, 'input_snapshot_id': input_snapshot_id,
            'payload': {'sha256': hashlib.sha256(data).hexdigest(), 'mime': mime, 'name': name}}
    s = service()
    import asyncio
    from .attachments import extract
    extracted=await asyncio.to_thread(extract,data,mime)
    def save(c, case, payload):
        if case['execution_status']=='CANCELLED':
            raise PatentError('TERMINAL_CASE','종료된 사건에 자료를 추가할 수 없습니다.')
        material=s.material(owner,case,c)
        asset_id = ident('passet')
        s.put_asset(c, case, asset_id, name, mime, data)
        evidence={**payload,'asset_id':asset_id,'origin':'OWNER_PRIVATE_UPLOAD',**extracted}
        s.repo.append(c,case_id,'attachment',evidence)
        s.invalidate(c,case,{'invention','questions','review_questions'},'ATTACHMENT_ADDED')
        previous=case['artifacts'].get('attachments')
        s.repo.artifact(c,case,'attachments',{'documents':[*material.get('attachments',{}).get('documents',[]),evidence]},
                       [previous] if previous else [],producer='OWNER_UPLOAD')
        s.retire_stale_queued(c,case)
        return {'asset_id': asset_id, 'parse_status': extracted['parse_status']}
    return s.repo.mutate(owner, case_id, 'attachments', body, idempotency_key, save)


@router.get('/cases/{case_id}/assets/{asset_id}')
@router.get('/cases/{case_id}/exports/{asset_id}/download')
def download(case_id: str, asset_id: str, owner=Depends(principal)):
    s = service()
    s.repo.get(owner, case_id)
    with s.repo.engine.connect() as c:
        row = c.execute(select(assets).where(assets.c.case_id == case_id, assets.c.asset_id == asset_id)).mappings().first()
    if not row:
        raise PatentError('NOT_FOUND', '파일을 찾을 수 없습니다.', 404)
    return Response(row['content'], media_type=row['mime'], headers={'Cache-Control':'private, no-store',
        'X-Content-Type-Options':'nosniff', 'Content-Disposition':'attachment; filename="patent-draft'+('.zip' if row['mime']=='application/zip' else '.bin')+'"'})


@router.get('/cases/{case_id}/artifacts/{version_id}')
@router.get('/cases/{case_id}/exports/{version_id}')
def record(case_id: str, version_id: str, owner=Depends(principal)):
    return service().repo.record(owner, case_id, version_id)


@router.get('/cases/{case_id}/artifacts/{version_id}/lineage')
def lineage(case_id: str, version_id: str, owner=Depends(principal)):
    current = service().repo.record(owner, case_id, version_id)
    return {'artifact': current, 'parents': [service().repo.record(owner, case_id, v) for v in current.get('parent_version_ids', [])]}


@router.get('/cases/{case_id}/tasks/{task_id}')
def task(case_id: str, task_id: str, owner=Depends(principal)):
    return service().task(owner, case_id, task_id)


@router.get('/cases/{case_id}/{collection}')
def collection(case_id: str, collection: str, owner=Depends(principal)):
    s = service()
    case = s.repo.get(owner, case_id)
    if collection == 'budget':
        return case['budget']
    if collection == 'questions':
        m = s.material(owner, case)
        return {'questions': intake_questions(m), 'answers': m.get('answers', {})}
    if collection == 'checks':
        return s.runtime_checks(owner, case, s.material(owner, case))
    if collection == 'sources':
        m = s.material(owner, case)
        return {k: m[k] for k in ('sources','source_detail') if k in m}
    if collection == 'sample-image':
        from .repository import image_jobs
        with s.repo.engine.connect() as c:
            row=c.execute(select(image_jobs).where(image_jobs.c.case_id==case_id)).mappings().first()
        if not row:return {'status':'NOT_RUN'}
        body=json.loads(row['body'])
        return {'job_id':row['job_id'],'status':row['status'],'error_code':body.get('error_code'),
                'artifact_status':body.get('artifact_status'),'max_images_per_case':1}
    if collection == 'issues':
        return [f for r in s.current_reviews(owner, case) for f in r['findings'] if f['outcome'] in ('FAIL','UNKNOWN')]
    kinds = {'reviews':'review','patches':'patch_proposal','events':'event','attachments':'attachment','exports':'export'}
    if collection not in kinds:
        raise PatentError('NOT_FOUND', '자료를 찾을 수 없습니다.', 404)
    data = s.repo.records(owner, case_id, kinds[collection])
    if collection == 'events':
        # Browser reconnects with server state; bounded response avoids holding DB leases.
        return Response(''.join('id: '+x['id']+'\nevent: patent\ndata: '+canonical(x)+'\n\n' for x in data[-100:]),
                        media_type='text/event-stream', headers={'Cache-Control':'no-store'})
    return data


@router.post('/cases/{case_id}/{operation}')
def mutate(case_id: str, operation: str, body: Mutation, owner=Depends(principal), idempotency_key: str = Header(default='')):
    allowed = {'budget-authorizations','start','pause','resume','cancel','answers','patches','approvals','enrichment-requests','sample-image','exports','feedback','withdraw-attachment'}
    if operation not in allowed:
        raise PatentError('NOT_FOUND', '작업을 찾을 수 없습니다.', 404)
    return service().mutate(owner, case_id, operation, body.model_dump(), idempotency_key)


@internal.post('/dispatch', dependencies=[Depends(operator)])
def dispatch():
    from .runtime import tick
    return {'executed': tick()}


@internal.post('/tasks/{task_id}/execute', dependencies=[Depends(operator)])
def execute(task_id: str):
    s = service()
    with s.repo.engine.connect() as c:
        row = c.execute(select(tasks.c.body, cases.c.owner_id).join(cases, tasks.c.case_id == cases.c.case_id).where(tasks.c.task_id == task_id)).first()
    if not row:
        raise PatentError('NOT_FOUND', '작업을 찾을 수 없습니다.', 404)
    return s.execute(row.owner_id, json.loads(row.body)['ticket'])
