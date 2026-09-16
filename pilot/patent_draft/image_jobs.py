"""One private sample per case. Durable dispatch independent of TRIZ and T3."""
import json
import os
from sqlalchemy import select, insert, update
from .repository import image_jobs, cases, now
from .domain import PatentError, ident, canonical
from .models import balance, settle
from .drawings import DiffusionAdapter, SAMPLE_IMAGE_NOTICE


def queue(service, c, case, material):
    previous = c.execute(select(image_jobs).where(image_jobs.c.case_id == case['case_id'])).mappings().first()
    if previous:
        return {'job_id': previous['job_id'], 'status': previous['status'], 'reused': True}
    drawing = material.get('drawings', {})
    if not drawing.get('sample_prompt_en'):
        raise PatentError('DRAWING_PROMPT_MISSING', '기술 구성에 연결된 도면 설명을 먼저 작성해야 합니다.', 422)
    if not case.get('provider_authorization'):
        raise PatentError('BUDGET_AUTHORIZATION', '특허 초안 예산을 먼저 승인해야 합니다.')
    if not os.getenv('PATENT_DRAWING_URL') or not os.getenv('PATENT_DRAWING_TOKEN'):
        raise PatentError('DRAWING_UNAVAILABLE', '특허 전용 이미지 서버를 설정해야 합니다.', 503)
    amount = int(os.getenv('PATENT_DRAWING_RESERVE_MICRO_USD', '0'))
    if not 1 <= amount <= 1_000_000:
        raise PatentError('DRAWING_COST_UNCONFIGURED', 'CPU 이미지의 최대 예약 비용을 먼저 설정해야 합니다.', 503)
    if balance(case['budget']) < amount:
        raise PatentError('BUDGET_EXHAUSTED', '필수 검토 예약을 제외한 이미지 예산이 부족합니다.')
    case['budget']['reserved_micro_usd'] += amount
    job_id = ident('pimg')
    body = {'case_id': case['case_id'], 'epoch': case['epoch'], 'drawing_version': case['artifacts']['drawings'],
            'prompt': drawing['sample_prompt_en'], 'reserved_micro_usd': amount, 'remote_job_id': None,
            'notice': SAMPLE_IMAGE_NOTICE, 'settled': False}
    c.execute(insert(image_jobs).values(job_id=job_id, case_id=case['case_id'], status='QUEUED',
        body=canonical(body), lease_until_ms=0, fence=0))
    service.repo.append(c, case['case_id'], 'event', {'type':'SAMPLE_IMAGE_QUEUED','job_id':job_id})
    return {'job_id': job_id, 'status':'QUEUED', 'max_images_per_case':1}


def tick(service, adapter=None):
    adapter = adapter or DiffusionAdapter()
    with service.repo.engine.begin() as c:
        candidates=c.execute(select(image_jobs.c.job_id,image_jobs.c.case_id,cases.c.owner_id)
            .join(cases,image_jobs.c.case_id==cases.c.case_id)
            .where(image_jobs.c.status.in_(['QUEUED','SUBMITTED','SUBMITTING']),image_jobs.c.lease_until_ms<now())
            .order_by(image_jobs.c.lease_until_ms,image_jobs.c.job_id)).all()
        row=None
        for candidate in candidates:
            if not service.legacy.is_patent_tester(candidate.owner_id):continue
            owner=candidate.owner_id
            case=service.repo.get(owner,candidate.case_id,c,lock=True)
            selected=c.execute(select(image_jobs).where(image_jobs.c.job_id==candidate.job_id).with_for_update()).mappings().one()
            if selected['status'] not in ('QUEUED','SUBMITTED','SUBMITTING') or selected['lease_until_ms']>=now():continue
            body=json.loads(selected['body'])
            if not body['remote_job_id'] and selected['status']=='QUEUED':
                stale=case['execution_status']=='CANCELLED' or case['epoch']!=body['epoch'] or case['artifacts'].get('drawings')!=body['drawing_version']
                if stale:
                    settle(case['budget'],body['reserved_micro_usd'],0)
                    body['settled']=True
                    c.execute(update(image_jobs).where(image_jobs.c.job_id==candidate.job_id).values(status='STALE',body=canonical(body)))
                    service.repo.append(c,case['case_id'],'cost',{'category':'image','job_id':candidate.job_id,'status':'RELEASED_NOT_DISPATCHED','reserved_micro_usd':body['reserved_micro_usd'],'actual_micro_usd':0})
                    service.repo.save(c,case,case['revision'])
                    continue
                if case['execution_status'] in ('PAUSED_USER','PAUSED_BUDGET','PAUSED_DEPENDENCY'):continue
            row=selected
            break
        if row is None:return False
        fence = row['fence'] + 1
        changed = c.execute(update(image_jobs).where(image_jobs.c.job_id == row['job_id'],image_jobs.c.fence == row['fence'])
            .values(status='SUBMITTING' if not body['remote_job_id'] else 'SUBMITTED', fence=fence, lease_until_ms=now()+240_000))
        if changed.rowcount != 1:
            return False
    status, image, error = 'SUBMITTED', None, None
    try:
        if not body['remote_job_id']:
            value = adapter.create(row['case_id'], body['drawing_version'], body['prompt'], row['job_id'])
            body['remote_job_id'] = value['job_id']
        value = adapter.status(body['remote_job_id'])
        if value['status'] == 'COMPLETED':
            image = adapter.image(body['remote_job_id'])
            status = 'COMPLETED'
            body['generation'] = value['result']
        elif value['status'] in ('FAILED','INTERRUPTED'):
            status, error = 'FAILED', value.get('result', {}).get('code','DRAWING_FAILED')
    except PatentError as exc:
        # Same opaque idempotency key is safe to retry at the durable image server.
        body['retry_count'] = body.get('retry_count', 0) + 1
        error = exc.code
        if body['retry_count'] >= 3:
            status = 'UNCERTAIN'
    with service.repo.engine.begin() as c:
        case = service.repo.get(owner, row['case_id'], c, lock=True)
        current = c.execute(select(image_jobs).where(image_jobs.c.job_id == row['job_id']).with_for_update()).mappings().one()
        if current['fence'] != fence:
            return False
        if status in ('COMPLETED','FAILED','UNCERTAIN') and not body['settled']:
            # Railway compute is not an itemized model invoice. Keep its maximum
            # charge in uncertain until an operator reconciles measured billing.
            settle(case['budget'], body['reserved_micro_usd'], None)
            body['settled'] = True
            service.repo.append(c, case['case_id'], 'cost', {'category':'image','job_id':row['job_id'],
                'status':'UNKNOWN','reserved_micro_usd':body['reserved_micro_usd'],'actual_micro_usd':None})
        if image is not None:
            asset_id = ident('passet')
            service.put_asset(c, case, asset_id, 'sample-1.png', 'image/png', image)
            artifact = {'asset_id':asset_id,'notice':SAMPLE_IMAGE_NOTICE,'kind':'CONCEPT_IMAGE',
                'technical_review':'NOT_RUN','official_editor_validation':'NOT_RUN',
                'drawing_version':body['drawing_version'],'generation':body['generation']}
            # Sample image is a supporting artifact, never a verified filing diagram.
            stale = case['epoch'] != body['epoch'] or case['artifacts'].get('drawings') != body['drawing_version'] or case['execution_status'] in ('CANCELLED','PAUSED_USER')
            service.repo.artifact(c, case, 'sample_image', artifact, [body['drawing_version']], producer='STABLE_DIFFUSION', update_head=not stale)
            body['artifact_status'] = 'STALE' if stale else 'CURRENT'
            if not stale and case['execution_status']=='COMPLETED':
                case['execution_status'],case['waiting_for']='WAITING_HUMAN','INPUT_UPDATED'
        body['error_code'] = error
        c.execute(update(image_jobs).where(image_jobs.c.job_id == row['job_id']).values(status=status,
            body=canonical(body), lease_until_ms=now()+15_000 if status=='SUBMITTED' else 0))
        service.repo.save(c, case, case['revision'])
    return True
