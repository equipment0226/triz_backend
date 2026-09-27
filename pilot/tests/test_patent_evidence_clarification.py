"""Invalid citations become a bound owner decision, not a paid regeneration loop."""
import copy
import pytest
from sqlalchemy import select
from patent_draft.domain import PatentError,digest
from patent_draft.repository import tasks
from patent_draft import workflow,dispatch
from test_patent_draft import patent,change,drain,mutation
from test_patent_workflow import prepared


def rejected(patent,kind='SynthesizedSolution'):
    s,gateway,*_=patent
    generate=gateway.generate
    def invalid(model,instruction,context,schema):
        response=generate(model,instruction,context,schema)
        if schema['title']==kind:
            group='facts' if kind=='SynthesizedSolution' else 'checks'
            response['value'][group][0]['basis'][0]['excerpt']='원문에 없는 인용'
        return response
    gateway.generate=invalid
    case=drain(s,prepared(s))
    assert case['waiting_for']=='EVIDENCE_CLARIFICATION' and case['last_error'] is None
    return s,gateway,case


def response(s,case,action='CORRECT',text='사용자가 확인한 냉각판 구성'):
    pending=s.material('owner',case)['evidence_clarification']
    return {'clarification_version_id':case['artifacts']['evidence_clarification'],
        'resolutions':[{'issue_id':issue['id'],'action':action,'text':text} for issue in pending['issues']]}


@pytest.mark.parametrize('action',['CORRECT','UNVERIFIED'])
def test_owner_resolution_advances_to_keywords_without_repeating_synthesis(patent,action):
    s,gateway,case=rejected(patent)
    before=s.material('owner',case);source=digest(before['source'])
    issue=before['evidence_clarification']['issues'][0]
    assert issue['references'][0]['source_text']=='Two cooling loops'
    assert issue['references'][0]['excerpt']=='원문에 없는 인용'
    case=change(s,case,'evidence-resolutions',response(s,case,action))
    current=s.material('owner',case)
    assert 'evidence_clarification' not in current and len(gateway.calls)==1
    assert current['synthesized_solution']['facts'][0]['status']==('USER_REPORTED' if action=='CORRECT' else 'UNKNOWN')
    assert current['synthesized_solution']['facts'][0]['basis'][0]['artifact']=='answers'
    with s.repo.engine.connect() as c:
        import json
        tickets=[json.loads(raw)['ticket'] for raw in c.execute(select(tasks.c.body).where(tasks.c.status=='QUEUED')).scalars()]
    assert [t['tool_name'] for t in tickets]==['patent_extract_keywords']
    case=drain(s,case)
    assert case['waiting_for']=='FINAL_REVIEW'
    assert sum('source' in context and 'section_mapping' in context for _,context in gateway.calls)==1
    assert digest(s.material('owner',case)['source'])==source
    assert len(s.repo.records('owner',case['case_id'],'evidence_resolution'))==1


def test_continue_and_duplicate_ticket_cannot_repeat_paid_invalid_analysis(patent,monkeypatch):
    s,gateway,case=rejected(patent)
    spent=case['budget']['spent_micro_usd']
    for i in range(3):case=change(s,case,'resume')
    assert len(gateway.calls)==1 and case['budget']['spent_micro_usd']==spent
    assert case['waiting_for']=='EVIDENCE_CLARIFICATION'
    pending=s.material('owner',case)['evidence_clarification']
    async def execute(ticket):return s.execute('owner',ticket)
    monkeypatch.setattr(dispatch,'execute_mcp',execute)
    import asyncio
    result=asyncio.run(dispatch.execute_stage(s,pending['task_id']))
    assert result['gate_id']=='G1' and not result['continue_execution']
    graph=workflow.describe(s,'owner',case,s.material('owner',case),[])
    assert {n['id'] for n in graph['nodes'] if n['status']=='WAITING'}>={'P1.0','G1'}


def test_exclusion_cannot_leave_removed_claim_in_summary(patent):
    s,gateway,*_=patent;generate=gateway.generate
    def invalid(*args):
        value=generate(*args)
        if args[-1]['title']=='SynthesizedSolution':
            fact=copy.deepcopy(value['value']['facts'][0]);fact.update(id='BAD',statement='제외할 잘못된 기술 주장')
            fact['basis'][0]['excerpt']='없는 인용';value['value']['facts'].append(fact)
            value['value']['revised_solution']='제외할 잘못된 기술 주장'
        return value
    gateway.generate=invalid;case=drain(s,prepared(s))
    case=change(s,case,'evidence-resolutions',response(s,case,'EXCLUDE','확인되지 않아 제외'))
    synthesis=s.material('owner',case)['synthesized_solution']
    assert [f['id'] for f in synthesis['facts']]==['SF1']
    assert '제외할 잘못된 기술 주장' not in synthesis['revised_solution']


def test_resolution_is_version_bound_and_all_issues_require_choices(patent):
    s,_,case=rejected(patent)
    for payload in ({'clarification_version_id':'wrong','resolutions':[]},
                    {'clarification_version_id':case['artifacts']['evidence_clarification'],'resolutions':[]}):
        with pytest.raises(PatentError):change(s,case,'evidence-resolutions',payload)
    old=response(s,case)
    case=change(s,case,'answers',{'answers':{'APPLICATION_CHANGES':'원래 해결안을 새 조건으로 변경'}})
    with pytest.raises(PatentError):change(s,case,'evidence-resolutions',old)


def test_user_cannot_convert_invalid_coherence_review_into_pass(patent):
    s,_,case=rejected(patent,'DocumentCoherence')
    case=change(s,case,'evidence-resolutions',response(s,case))
    assert s.material('owner',case)['document_coherence']['checks'][0]['outcome']=='UNKNOWN'
    case=drain(s,case)
    assert case['waiting_for']=='PATCH_REVIEW'
    assert {r['role'] for r in s.current_reviews('owner',case)}=={'TECHNICAL_CONTENT','PATENT_CONTENT'}
    assert not s.approvals('owner',case)
