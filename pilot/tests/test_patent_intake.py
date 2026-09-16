"""Mandatory owner input, persistence and paid-work invalidation contracts."""
import copy
import json

import pytest
from sqlalchemy import select
from fastapi import FastAPI
from fastapi.testclient import TestClient

from patent_draft.domain import PatentError, digest
from patent_draft.models import ModelProfile
from patent_draft.repository import tasks
from patent_draft.service import Service
from test_patent_draft import (patent, opened, change, answered, authorize, drain, drafted,
                               APPLICATION_ANSWERS, INVENTION)


def queued(s, case):
    with s.repo.engine.connect() as c:
        return [json.loads(x)['ticket'] for x in c.execute(select(tasks.c.body).where(
            tasks.c.case_id == case['case_id'], tasks.c.status == 'QUEUED')).scalars()]


def test_selection_never_skips_owner_input_or_requires_paid_model(patent):
    s, gateway, *_ = patent
    s.profile = ModelProfile({})
    case, _ = opened(s)
    case = change(s, case, 'start')
    assert case['execution_status'] == 'WAITING_HUMAN'
    assert case['waiting_for'] == 'APPLICATION_CONTEXT'
    assert not queued(s, case) and not gateway.calls
    assert case['budget']['reserved_micro_usd'] == case['budget']['spent_micro_usd'] == 0
    material = s.material('owner', case)
    assert {q['id'] for q in material['application_questions']['questions']} == set(APPLICATION_ANSWERS)
    with pytest.raises(PatentError) as err:
        change(s, case, 'approvals', {'approval_type':'G1', 'content_hash':digest(INVENTION)})
    assert err.value.code == 'APPLICATION_CONTEXT_REQUIRED'


@pytest.mark.parametrize('missing', list(APPLICATION_ANSWERS))
def test_every_mandatory_answer_is_required(patent, missing):
    s, gateway, *_ = patent
    case, _ = opened(s)
    partial = {k:v for k,v in APPLICATION_ANSWERS.items() if k != missing}
    case = change(s, case, 'answers', {'answers':partial})
    case = change(s, case, 'start')
    assert case['waiting_for'] == 'APPLICATION_CONTEXT'
    assert not queued(s, case) and not gateway.calls


@pytest.mark.parametrize('bad', ['', '  ', True, [], 'x'*8001])
def test_blank_or_invalid_mandatory_input_cannot_be_saved(patent, bad):
    s, *_ = patent
    case, _ = opened(s)
    with pytest.raises(PatentError):
        change(s, case, 'answers', {'answers':{**APPLICATION_ANSWERS,'APPLICATION_RISKS':bad}})
    assert 'application_context' not in s.material('owner',s.repo.get('owner',case['case_id']))


def test_server_restores_answers_and_same_save_preserves_versions_and_reservations(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    before = copy.deepcopy(case)
    ticket = queued(s, case)[0]
    case = change(s,case,'answers',{'answers':APPLICATION_ANSWERS})
    assert case['snapshot_id'] == before['snapshot_id']
    assert case['artifacts'] == before['artifacts']
    assert case['budget'] == before['budget']
    assert queued(s,case) == [ticket]
    restored = Service(s.repo,s.legacy,s.profile,s.gateway,s.sources)
    assert restored.material('owner',restored.repo.get('owner',case['case_id']))['answers'] == APPLICATION_ANSWERS
    assert len(s.repo.records('owner',case['case_id'],'artifact')) == 4
    assert not gateway.calls


def test_changed_conditions_retire_unstarted_task_without_spend(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    ticket = queued(s,case)[0]
    review_reserve = case['budget']['review_plan_micro_usd']
    case = change(s,case,'answers',{'answers':{'APPLICATION_CONSTRAINTS':'시설수 입구 40°C'}})
    assert s.task('owner',case['case_id'],ticket['task_id'])['status'] == 'STALE'
    assert case['budget']['reserved_micro_usd'] == 0
    assert case['budget']['review_plan_micro_usd'] == review_reserve
    assert case['budget']['spent_micro_usd'] == 0 and not gateway.calls
    assert s.execute('owner',ticket)['status'] == 'STALE'
    case = change(s,case,'resume')
    new_ticket = queued(s,case)[0]
    assert new_ticket['task_id'] != ticket['task_id']
    s.execute('owner',new_ticket)
    assert gateway.calls[0][1]['application_context']['APPLICATION_CONSTRAINTS'] == '시설수 입구 40°C'


def test_application_change_invalidates_completed_reviews_and_equal_text_approval(patent):
    s, *_ = patent
    case = drafted(s)
    old = copy.deepcopy(case)
    assert len(s.current_reviews('owner',case)) == 3
    assert set(s.approvals('owner',case)) == {'G1','G2'}
    case = change(s,case,'answers',{'answers':{'APPLICATION_RISKS':'실험 결과 유량 불균형 위험을 추가로 발견함'}})
    assert 'invention' not in case['artifacts'] and 'claims' not in case['artifacts']
    assert s.current_reviews('owner',case) == [] and s.approvals('owner',case) == {}
    assert case['budget']['spent_micro_usd'] == old['budget']['spent_micro_usd']
    assert s.repo.record('owner',case['case_id'],old['artifacts']['claims'])['kind'] == 'artifact'
    case = drain(s,change(s,case,'resume'))
    assert case['waiting_for'] == 'G1'
    # Fake generator returns the exact same text, but its conditions/version changed.
    assert digest(s.material('owner',case)['invention']) == digest(INVENTION)
    assert s.approvals('owner',case) == {}


def test_running_old_result_is_charged_but_cannot_restore_old_draft(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    ticket = queued(s,case)[0]
    generate = gateway.generate
    def change_during_call(*args):
        current = s.repo.get('owner',case['case_id'])
        change(s,current,'answers',{'answers':{'APPLICATION_CHANGES':'냉각판 재질을 변경할 계획이다.'}})
        return generate(*args)
    gateway.generate = change_during_call
    assert s.execute('owner',ticket)['status'] == 'STALE'
    current = s.repo.get('owner',case['case_id'])
    assert 'invention' not in current['artifacts']
    assert current['budget']['spent_micro_usd'] == 300
    assert current['budget']['reserved_micro_usd'] == 0


def test_resume_while_previous_input_is_running_schedules_changed_input(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    ticket = queued(s,case)[0]
    generate = gateway.generate
    def resume_during_call(*args):
        current = s.repo.get('owner',case['case_id'])
        current = change(s,current,'answers',{'answers':{'APPLICATION_CHANGES':'루프 분리와 냉각판 재질 변경'}})
        change(s,current,'resume')
        assert not queued(s,current)
        return generate(*args)
    gateway.generate = resume_during_call
    assert s.execute('owner',ticket)['status'] == 'STALE'
    current = s.repo.get('owner',case['case_id'])
    assert len(queued(s,current)) == 1
    assert queued(s,current)[0]['task_id'] != ticket['task_id']
    assert current['budget']['spent_micro_usd'] == 300


def test_followup_question_blocks_drafting_until_owner_answer(patent):
    s, gateway, *_ = patent
    gateway.questions = [{'id':'Q_CONDENSATION','question':'결로 방지 방식은 무엇인가요?',
        'reason':'예상 위험에 대한 구조 변경 필요', 'affected_fields':['invention'], 'blocking':True}]
    case, _ = opened(s)
    case = drain(s,change(s,authorize(s,answered(s,case)),'start'))
    assert case['waiting_for'] == 'QUESTIONS'
    assert len(gateway.calls) == 2 and 'claims' not in case['artifacts']
    with pytest.raises(PatentError) as err:
        change(s,case,'approvals',{'approval_type':'G1','content_hash':digest(INVENTION)})
    assert err.value.code == 'QUESTIONS_REQUIRED'
    case = change(s,case,'answers',{'answers':{'Q_CONDENSATION':'아직 결정하지 못함. 검증 필요.'}})
    assert 'invention' not in case['artifacts']
    case = drain(s,change(s,case,'resume'))
    assert case['waiting_for'] == 'G1'
    assert gateway.calls[2][1]['answers']['Q_CONDENSATION'].startswith('아직 결정하지 못함')
    assert all(e['evidence_status'] == 'HYPOTHESIS' for e in s.material('owner',case)['invention']['effects'])


def test_api_restores_mandatory_questions_and_answers_with_owner_acl(patent, monkeypatch):
    s, *_ = patent
    import patent_draft.api as api
    monkeypatch.setattr(api,'service',lambda:s)
    monkeypatch.setattr(s.legacy,'principal',lambda token: {'owner-token':'owner','other-token':'other'}.get(token))
    case, _ = opened(s)
    case = answered(s,case)
    app = FastAPI()
    app.include_router(api.router)
    app.add_exception_handler(PatentError,api.error_handler)
    with TestClient(app) as client:
        url = '/api/patent/cases/'+case['case_id']
        data = client.get(url,headers={'x-triz-session':'owner-token'}).json()
        assert data['intake'] == {'complete':True,'pending_question_ids':[]}
        assert data['material']['application_context']['evidence_status'] == 'USER_REPORTED_NOT_MEASUREMENT'
        restored = client.get(url+'/questions',headers={'x-triz-session':'owner-token'}).json()
        assert len(restored['questions']) == 3 and restored['answers'] == APPLICATION_ANSWERS
        assert client.get(url+'/questions',headers={'x-triz-session':'other-token'}).status_code == 403


def test_paused_task_is_held_and_changed_input_releases_only_unused_reservation(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    ticket = queued(s,case)[0]
    reserved = case['budget']['reserved_micro_usd']
    case = change(s,case,'pause')
    assert not queued(s,case)
    assert s.task('owner',case['case_id'],ticket['task_id'])['status'] == 'HELD'
    assert case['budget']['reserved_micro_usd'] == reserved
    case = change(s,case,'answers',{'answers':{'APPLICATION_RISKS':'追加: leak risk'}})
    assert case['execution_status'] == 'PAUSED_USER'
    assert case['budget']['reserved_micro_usd'] == 0
    case = change(s,case,'resume')
    assert len(queued(s,case)) == 1 and not gateway.calls
    assert queued(s,case)[0]['task_id'] != ticket['task_id']


def test_cancel_releases_unstarted_work_and_cannot_be_reopened_by_answers(patent):
    s, gateway, *_ = patent
    case, _ = opened(s)
    case = change(s,authorize(s,answered(s,case)),'start')
    ticket = queued(s,case)[0]
    case = change(s,case,'cancel')
    assert case['budget']['reserved_micro_usd'] == case['budget']['review_plan_micro_usd'] == 0
    assert case['budget']['spent_micro_usd'] == 0 and not gateway.calls
    assert s.execute('owner',ticket)['status'] == 'CANCELLED'
    with pytest.raises(PatentError) as err:
        answered(s,case)
    assert err.value.code == 'TERMINAL_CASE'
