"""Automatic authoring, pinned nodes and durable n8n/MCP boundaries."""
import asyncio
import copy
import json
import pytest
from sqlalchemy import select, update
from patent_draft.domain import digest, PatentError
from patent_draft.repository import tasks
from patent_draft import workflow, dispatch, runtime
from test_patent_draft import patent, opened, change, authorize, drain


def automatic(s):
    preview = s.legacy.preview('owner','source','C1')
    return s.open('owner', {'source_run_id':'source','concept_id':'C1',
        'expected_source_hash':preview['source_hash'],'purpose':'자동 초안'}, 'automatic')


def prepared(s):
    case = automatic(s)
    case = change(s,case,'answers',{'answers':{'APPLICATION_CHANGES':'변경사항 없음. 미검증 사항은 유지.'}})
    return authorize(s,case)


def test_one_delta_answer_runs_to_final_review_without_intermediate_approvals(patent):
    s, gateway, *_ = patent
    case = drain(s, prepared(s))
    material = s.material('owner',case)
    assert case['waiting_for'] == 'FINAL_REVIEW'
    assert {'claims','specification','drawings'} <= material.keys()
    assert len(s.current_reviews('owner',case)) == 3
    assert s.approvals('owner',case) == {}
    assert len(material['application_questions']['questions']) == 1
    assert gateway.calls[0][1]['application_context']['APPLICATION_CHANGES']
    assert gateway.calls[1][1]['synthesized_solution']['facts']
    assert 'source' not in gateway.calls[1][1]
    assert gateway.calls[0][1]['section_mapping']['sections']
    with pytest.raises(PatentError):
        change(s,case,'final-approval',{'content_hash':'wrong'})
    case = change(s,case,'final-approval',{'content_hash':digest({k:material[k] for k in ('invention','claims','specification','drawings')})})
    assert set(s.approvals('owner',case)) == {'G1','G2'}


def test_known_triz_context_is_pinned_and_not_read_again(patent):
    s, _, engine, state = patent
    from triz import store
    state['constraints'] = {'hard':['입구 35도 유지']}
    state['analysis'] = {'failure':'결로'}
    state['scratch'] = {'private_unrelated':'do not include'}
    with engine.begin() as conn:
        conn.execute(update(store.states).values(state_json=json.dumps(state)))
    case = automatic(s)
    material = s.material('owner',case)
    assert material['source']['triz_context']['constraints'] == state['constraints']
    assert 'scratch' not in material['source']['triz_context']
    assert any(i['source_path']=='triz_context.constraints' for section in material['section_mapping']['sections'] for i in section['inputs'])
    with engine.begin() as conn:
        conn.execute(update(store.states).values(state_json='{}'))
    assert s.material('owner',case) == material


def test_missing_delta_and_budget_do_not_dispatch(patent):
    s, gateway, *_ = patent
    case = authorize(s,automatic(s))
    case = change(s,case,'start')
    assert case['waiting_for'] == 'APPLICATION_CONTEXT'
    assert not gateway.calls
    with s.repo.engine.connect() as conn:
        assert not conn.execute(select(tasks)).first()


def test_answers_resume_and_source_changes_retire_pending_ticket(patent):
    s, gateway, *_ = patent
    case = prepared(s)
    with s.repo.engine.connect() as conn:
        old = json.loads(conn.execute(select(tasks.c.body)).scalar())['ticket']
    case = change(s,case,'answers',{'answers':{'APPLICATION_CHANGES':'구성을 냉각판 두 개로 변경'}})
    assert s.task('owner',case['case_id'],old['task_id'])['status'] == 'STALE'
    case = drain(s,case)
    assert case['waiting_for'] == 'FINAL_REVIEW'
    assert gateway.calls[0][1]['application_context']['APPLICATION_CHANGES'] == '구성을 냉각판 두 개로 변경'


def test_required_followup_pauses_then_auto_resumes(patent):
    s, gateway, *_ = patent
    gateway.questions=[{'id':'Q_PORT','question':'냉각판 연결 방식은?','reason':'구성 연결 근거 없음',
                        'affected_fields':['invention'],'blocking':True}]
    case=drain(s,prepared(s))
    assert case['waiting_for']=='QUESTIONS'
    case=change(s,case,'answers',{'answers':{'Q_PORT':'직렬 연결'}})
    case=drain(s,case)
    assert case['waiting_for']=='FINAL_REVIEW'
    assert s.material('owner',case)['answers']['Q_PORT']=='직렬 연결'


def followup_round_three(patent):
    s,gateway,*_=patent
    generate=gateway.generate
    def rounds(model,instruction,context,schema):
        result=generate(model,instruction,context,schema)
        if schema['title']=='SynthesizedSolution':
            answers=context.get('answers',{})
            pending=['Q-01','Q-02'] if 'Q-02' not in answers else ['Q-03'] if 'Q-03' not in answers else []
            result['value']['questions']=[{'id':qid,'question':qid+'의 조건은?',
                'reason':'추가 조건 확인','affected_fields':['invention'],'blocking':True} for qid in pending]
            result['value']['issues']=[{'id':'I-'+qid,'description':'조건 미확인','resolution':'','status':'OPEN',
                'blocking':True,'question_id':qid} for qid in pending]
        return result
    gateway.generate=rounds
    case=drain(s,prepared(s))
    case=drain(s,change(s,case,'answers',{'answers':{'Q-01':'조건 1','Q-02':'조건 2'}}))
    assert case['waiting_for']=='QUESTIONS'
    assert [q['id'] for q in s.material('owner',case)['synthesis_questions']['questions']]==['Q-03']
    return s,case


@pytest.mark.parametrize('send_history',[True,False])
def test_new_followup_accepts_answer_without_rejecting_unchanged_history(patent,send_history):
    s,case=followup_round_three(patent)
    before=s.material('owner',case)
    answers={**(before['answers'] if send_history else {}),'Q-03':'새 조건 3'}
    case=drain(s,change(s,case,'answers',{'answers':answers}))
    assert case['waiting_for']=='FINAL_REVIEW'
    material=s.material('owner',case)
    assert material['answers']['Q-01']=='조건 1' and material['answers']['Q-02']=='조건 2'
    assert material['answers']['Q-03']=='새 조건 3'
    assert 'specification' in material and 'report' in material


@pytest.mark.parametrize('invalid',[{'Q-01':'과거 답변 변경'},{'NOT_ASKED':'임의 답변'}])
def test_unknown_or_modified_retired_answer_is_not_silently_accepted(patent,invalid):
    s,case=followup_round_three(patent)
    with pytest.raises(PatentError) as error:
        change(s,case,'answers',{'answers':{**invalid,'Q-03':'새 조건 3'}})
    assert error.value.code=='ANSWER_INVALID'
    assert 'Q-03' not in s.material('owner',s.repo.get('owner',case['case_id']))['answers']


def test_node_contract_and_prompts_are_pinned(patent,monkeypatch):
    s, *_ = patent
    case=automatic(s)
    original=s.material('owner',case)['workflow_contract']
    monkeypatch.setattr(workflow,'load_contract',lambda: {'version':'future'})
    assert s.material('owner',case)['workflow_contract']==original
    diagram=workflow.describe(s,'owner',case,s.material('owner',case),[])
    assert len(diagram['stages'])==6
    assert {n['id'] for n in diagram['nodes'] if n['type']=='gate'}=={'G0','G1','G2','G3'}
    assert next(n for n in diagram['nodes'] if n['id']=='P3.2')['prompt_text']


def test_completed_retry_is_not_displayed_as_its_previous_failure(patent):
    s,*_=patent
    case=drain(s,prepared(s));material=s.material('owner',case)
    old_failure={'tool_name':'patent_synthesize_solution','review_role':None,'status':'FAILED'}
    diagram=workflow.progress(case,material,[],[old_failure])
    assert next(n for n in diagram['nodes'] if n['id']=='P1.0')['status']=='COMPLETED'
    del material['synthesized_solution']
    diagram=workflow.progress(case,material,[],[old_failure])
    assert next(n for n in diagram['nodes'] if n['id']=='P1.0')['status']=='FAILED'


def test_n8n_bridge_uses_persisted_ticket_and_continues_same_case(patent,monkeypatch):
    s, gateway, *_ = patent
    case=prepared(s)
    task_id=dispatch.next_task(s,'owner',case['case_id'])
    received=[]
    async def execute(ticket):
        received.append(ticket)
        return s.execute('owner',ticket)
    monkeypatch.setattr(dispatch,'execute_mcp',execute)
    result=asyncio.run(dispatch.execute_stage(s,task_id))
    assert received[0]['task_id']==task_id
    assert received[0]['tool_name']=='patent_synthesize_solution'
    assert result['continue_execution'] and result['task_id']!=task_id
    asyncio.run(dispatch.execute_stage(s,task_id))
    assert len(gateway.calls)==1
    with pytest.raises(PatentError):
        asyncio.run(dispatch.execute_stage(s,'arbitrary'))


def test_n8n_queue_dispatch_is_leased_and_does_not_execute_locally(patent,monkeypatch):
    s, gateway, *_ = patent
    prepared(s)
    monkeypatch.setenv('PATENT_ORCHESTRATOR','n8n')
    monkeypatch.setattr(runtime,'service',lambda:s)
    from patent_draft import image_jobs
    monkeypatch.setattr(image_jobs,'tick',lambda _:None)
    sent=[]
    monkeypatch.setattr(dispatch,'dispatch_task',lambda task_id,node_id:sent.append((task_id,node_id)))
    assert runtime.tick()
    assert not runtime.tick()
    assert len(sent)==1 and not gateway.calls


def test_final_edit_restarts_affected_nodes_and_preserves_unaffected_draft(patent):
    s, *_ = patent
    case=drain(s,prepared(s))
    material=s.material('owner',case)
    replacement=copy.deepcopy(material['specification'])
    replacement['abstract']='냉각판과 루프를 분리하는 장치의 수정된 요약.'
    case=change(s,case,'patches',{'target_type':'specification','before_hash':digest(material['specification']),
        'replacement':replacement,'change_kind':'TECHNICAL','change_reason':'요약 표현 수정','issue_ids':[]})
    proposal=s.repo.records('owner',case['case_id'],'patch_proposal')[-1]
    claims_version=case['artifacts']['claims']
    case=change(s,case,'apply-patch',{'patch_id':proposal['id']})
    assert case['artifacts']['claims']==claims_version
    assert dispatch.next_task(s,'owner',case['case_id'])
    assert not s.current_reviews('owner',case)
    case=drain(s,case)
    assert case['waiting_for']=='FINAL_REVIEW'
    assert s.material('owner',case)['specification']['abstract']==replacement['abstract']


def test_generated_n8n_graph_matches_process_registry():
    from scripts.export_patent_workflow import build
    from pathlib import Path
    graph=build()
    target=Path(__file__).resolve().parents[2]/'deploy/n8n/patent-workflow.json'
    assert json.loads(target.read_text(encoding='utf-8'))==graph
    ids={n['id'] for n in graph['nodes']}
    contract=workflow.load_contract()
    assert {n['id'] for n in contract['nodes'] if n['tool'] or n['type']=='gate'} <= ids
    names={n['name'] for n in graph['nodes']}
    assert all(c['node'] in names for group in graph['connections'].values() for output in group['main'] for c in output)


def test_resaving_same_answers_does_not_restart_a_review_checkpoint(patent):
    s,gateway,*_=patent
    case=drain(s,prepared(s))
    before=len(gateway.calls)
    answers=s.material('owner',case)['answers']
    case=change(s,case,'answers',{'answers':answers})
    assert case['waiting_for']=='FINAL_REVIEW'
    assert not dispatch.next_task(s,'owner',case['case_id'])
    assert len(gateway.calls)==before
