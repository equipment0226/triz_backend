"""Durable image dispatch is gated by account, input version and one-image limit."""
import copy,json
from sqlalchemy import select,update
from patent_draft.repository import image_jobs
from patent_draft.image_jobs import tick
from patent_draft.domain import canonical
from test_patent_draft import patent,opened,authorize,answered,change,DRAWINGS


class Images:
    def __init__(self):self.created=[]
    def create(self,case,version,prompt,key):
        self.created.append(key);return {'job_id':'a'*32}
    def status(self,job):return {'status':'COMPLETED','result':{'provider':'test-only'}}
    def image(self,job):return b'\x89PNG\r\n\x1a\nTEST-FIXTURE'


def queued(s,monkeypatch,key):
    monkeypatch.setenv('PATENT_DRAWING_URL','http://drawing.railway.internal:8000')
    monkeypatch.setenv('PATENT_DRAWING_TOKEN','test-only')
    monkeypatch.setenv('PATENT_DRAWING_RESERVE_MICRO_USD','10000')
    _,body=opened(s);case=s.open('owner',body,key)
    case=change(s,authorize(s,answered(s,case)),'start')
    drawing=copy.deepcopy(DRAWINGS);drawing['sample_prompt_en']='Black and white cooling plate'
    with s.repo.engine.begin() as c:
        current=s.repo.get('owner',case['case_id'],c,lock=True)
        s.repo.artifact(c,current,'drawings',drawing)
        s.repo.save(c,current,current['revision'])
    return change(s,s.repo.get('owner',case['case_id']),'sample-image')


def test_paused_image_does_not_starve_other_case_and_only_one_can_be_queued(patent,monkeypatch):
    s,_,_,_=patent;first=queued(s,monkeypatch,'image-first')
    first=change(s,first,'pause');second=queued(s,monkeypatch,'image-second')
    with s.repo.engine.begin() as c:
        c.execute(update(image_jobs).where(image_jobs.c.case_id==first['case_id']).values(lease_until_ms=-100))
    adapter=Images();assert tick(s,adapter)
    assert len(adapter.created)==1
    updated=s.repo.get('owner',second['case_id'])
    assert 'sample_image' in updated['artifacts']
    assert s.material('owner',updated)['sample_image']['notice']=='해당 이미지는 생성형 AI를 활용한 샘플 이미지입니다.'
    change(s,updated,'sample-image')
    assert not tick(s,adapter) and len(adapter.created)==1
    with s.repo.engine.connect() as c:
        jobs={r['case_id']:r['status'] for r in c.execute(select(image_jobs)).mappings()}
    assert jobs=={first['case_id']:'QUEUED',second['case_id']:'COMPLETED'}


def test_revoked_tester_cannot_dispatch_cpu_image(patent,monkeypatch):
    s,_,engine,_=patent;case=queued(s,monkeypatch,'image-revoked')
    from triz import store
    with engine.begin() as c:c.execute(update(store.accounts).where(store.accounts.c.user_id=='owner').values(email='other@example.com'))
    adapter=Images();assert not tick(s,adapter) and not adapter.created


def test_cancelled_undispatched_image_releases_reservation_without_provider_call(patent,monkeypatch):
    s,_,_,_=patent;case=queued(s,monkeypatch,'image-cancelled')
    case=change(s,case,'cancel');assert case['budget']['reserved_micro_usd']==10000
    adapter=Images();assert not tick(s,adapter)
    current=s.repo.get('owner',case['case_id'])
    assert not adapter.created and current['budget']['reserved_micro_usd']==0
    assert current['budget']['uncertain_micro_usd']==current['budget']['spent_micro_usd']==0
