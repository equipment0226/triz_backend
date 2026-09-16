"""Exercise actual patent storage boundaries and immutable review conflicts."""
import copy
import pytest
from sqlalchemy import insert,select
from test_patent_draft import patent,opened,drafted,change,drain
from patent_draft.domain import PatentError,digest
from patent_draft.repository import TABLES
from patent_draft.sql_guard import verified


def test_reader_and_writer_reject_original_and_driver_writes(patent):
    from triz import store
    s,_,engine,original=patent
    assert verified(s.legacy.engine) and verified(s.repo.engine,TABLES)
    for port in (s.legacy.engine,s.repo.engine):
        with port.begin() as c:
            with pytest.raises(PatentError,match='SQL'):
                c.execute(insert(store.runs).values(run_id='forbidden',user_id='owner'))
            with pytest.raises(PatentError,match='SQL'):
                c.exec_driver_sql('DELETE FROM states')
    with engine.connect() as c:
        assert c.execute(select(store.runs.c.run_id)).scalars().all()==['source']


def test_opposing_same_version_reviews_are_preserved(patent):
    s,*_=patent
    case=drafted(s)
    initial=s.current_reviews('owner',case)
    original=next(r for r in initial if r['role']=='TECHNICAL_CONTENT')
    opposing=copy.deepcopy(original)
    opposing['findings'][0].update(outcome='FAIL',explanation='Conflicting technical finding on the same material')
    with s.repo.engine.begin() as c:
        s.repo.append(c,case['case_id'],'review',{k:v for k,v in opposing.items() if k not in ('id','kind')})
    current=s.current_reviews('owner',case)
    assert len(current)==len(initial)+1
    rule_id=opposing['findings'][0]['rule_id']
    checks={r['rule_id']:r for r in s.runtime_checks('owner',case,s.material('owner',case))}
    assert checks[rule_id]['outcome']=='FAIL'


def test_claim_patch_invalidates_dependent_documents_and_keeps_history(patent):
    s,*_=patent
    case=drafted(s);m=s.material('owner',case)
    previous=dict(case['artifacts'])
    replacement=copy.deepcopy(m['claims']);replacement['claims'][0]['text']+=' 추가 한정.'
    case=change(s,case,'patches',{'target_type':'claims','before_hash':digest(m['claims']),
        'replacement':replacement,'change_kind':'CLAIM_SCOPE','change_reason':'Owner scope correction','issue_ids':[]})
    patch=s.repo.records('owner',case['case_id'],'patch_proposal')[-1]
    case=change(s,case,'apply-patch',{'patch_id':patch['id']})
    assert case['artifacts']['claims']!=previous['claims']
    assert not {'specification','drawings','sample_image'} & case['artifacts'].keys()
    assert s.repo.record('owner',case['case_id'],previous['specification'])['payload']==m['specification']
    assert not s.current_reviews('owner',case)
    assert 'G2' not in s.approvals('owner',case)
    assert s.repo.records('owner',case['case_id'],'patch_applied')[-1]['after_version_id']==case['artifacts']['claims']
