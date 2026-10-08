"""Focused review coverage, exact evidence, bounded retry and usage accounting."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_semantic_gate as gate, llm
from triz.context import AbortRun, RunContext
from triz.schema import Attachment, ClarifyTurn, Constraint


def passed(rubric_id):
    return {'checks': [{'id': key, 'status': 'PASS', 'reason': '현재 산출물과 근거 정합', 'findings': []}
                       for key in gate.RULES[rubric_id]]}


def generic(status='PASS'):
    return {'verdict': status, 'per_criterion': [{'id': 'C1', 'score': 1},
        {'id': 'C2', 'score': 1}, {'id': 'C3', 'score': 1}],
        'revision_instructions': [] if status == 'PASS' else ['기존 필수 의미 결함 수리']}


def model_result(data, cost=.01):
    return SimpleNamespace(data=data, text='', model='offline', tokens_in=3, tokens_out=5, cost_usd=cost, meta={})


def ifr_packet(state):
    state.intake.clarify_turns = [ClarifyTurn(question='대면재가 견뎌야 하는 허용 최고 온도는?',
        user_answer='2000 K 이상', answered=True)]
    return gate.request_packet(state, 'R4_IFR', {
        'statement': '필요한 차폐와 열 배출을 보존한다',
        'intensified': '표면(>=2000 K 조건)과 자석 측(<=4 K 조건) 사이에 이미 형성된 온도 구배',
        'ideality_note': '이상성 비율은 1 미만',
    })


def ifr_revise():
    review = passed('R4_IFR')
    review['checks'][0].update(status='REVISE', reason='허용 온도를 현재 온도로 승격', findings=[{
        'artifact_path': '/intensified', 'artifact_quote': '이미 형성된 온도 구배',
        'evidence_path': '/context/direct_user_sources/intake.clarify_turns[0].user_answer/question',
        'evidence_quote': '견뎌야 하는 허용 최고 온도',
        'issue': '허용 요구만으로 현재 측정 온도와 가용 구배를 확정했다.',
        'suggested_correction': '허용 경계와 실제 온도 미확인을 구별해 조건부 가설로 표현한다.'}])
    return review


@pytest.mark.parametrize('rubric_id', list(gate.RULES))
def test_every_focused_rule_must_explicitly_pass(state, rubric_id):
    packet = gate.request_packet(state, rubric_id, {})
    assert gate.normalize_review(passed(rubric_id), packet)['verdict'] == 'PASS'
    missing = passed(rubric_id)
    missing['checks'].pop()
    assert gate.normalize_review(missing, packet)['verdict'] == 'UNVERIFIED'


def test_exact_requirement_quotation_supports_actionable_current_artifact_repair(state):
    out = gate.normalize_review(ifr_revise(), ifr_packet(state))
    assert out['verdict'] == 'REVISE'
    assert out['element_findings'][0]['path'] == '/intensified'
    assert out['element_findings'][0]['artifact_quote'] == '이미 형성된 온도 구배'
    assert out['revision_instructions']


@pytest.mark.parametrize('mutation', ['bad_path', 'invented_quote', 'invented_evidence', 'no_correction',
                                      'pass_with_findings', 'empty_findings', 'duplicate', 'inconsistent'])
def test_unverifiable_focused_review_neither_passes_nor_orders_artifact_repair(state, mutation):
    packet, review = ifr_packet(state), ifr_revise()
    row, finding = review['checks'][0], review['checks'][0]['findings'][0]
    if mutation == 'bad_path':
        finding['artifact_path'] = '/missing'
    elif mutation == 'invented_quote':
        finding['artifact_quote'] = '실측 2400 K'
    elif mutation == 'invented_evidence':
        finding['evidence_quote'] = '실제 온도 2000 K'
    elif mutation == 'no_correction':
        finding['suggested_correction'] = ''
    elif mutation == 'pass_with_findings':
        row['status'] = 'PASS'
    elif mutation == 'empty_findings':
        row['findings'] = []
    elif mutation == 'duplicate':
        review['checks'][1] = deepcopy(row)
    else:
        review['verdict'] = 'PASS'
    out = gate.normalize_review(review, packet)
    assert out['verdict'] == 'UNVERIFIED' and out['verification_unavailable']
    assert not out['revision_instructions']


def test_pc_independent_properties_and_constraint_or_alternative_have_specific_rules(state):
    pc = gate.request_packet(state, 'R4_CONTRA', {'physical_contradictions': [{
        'parameter': '검증 충실도(실데이터 사용 범위와 맞춤 튜닝 정도)',
        'state_a': '실제 생산 데이터로 맞춤 검증 결과 제시', 'state_b': '최적화 모델 상세 설정 비공개'}]})
    assert '공개 깊이 낮음은 독립 속성' in pc['rules']['SAME_PROPERTY_OPPOSITES']
    state.constraints.items = [Constraint(id='CON-2a822873', statement='비식별화 또는 사용 범위 제한 필요')]
    packet = gate.request_packet(state, 'R3_CONSTRAINT', {'taboo': [{'item': '비식별화 없이 처리 금지'}]})
    assert packet['context']['existing_constraints'][0]['statement'] == '비식별화 또는 사용 범위 제한 필요'
    assert '둘 중 하나의 대안' in packet['rules']['ALTERNATIVES_AND_TABOO']


def test_legacy_self_contained_reports_remain_evidence_without_user_hard_authentication(state):
    from triz.constraint_sources import user_constraint_sources, validate_user_constraint_source
    state.scratch['deep_dive'] = {'answers': ['Measured coolant flow is 10 kg/s.', '10%']}
    packet = gate.request_packet(state, 'R4_IFR', {})
    report = packet['context']['legacy_user_reports'][0]
    assert report['text'] == 'Measured coolant flow is 10 kg/s.'
    assert report['question_context'] == 'MISSING'
    assert '신규 USER/HARD 인증 경로가 아니다' in report['source_policy']
    assert validate_user_constraint_source({'source_path': report['source_path'], 'source_quote': report['text']},
                                           user_constraint_sources(state))
    assert packet['context']['legacy_user_reports'][1]['text'] == '10%'


@pytest.fixture
def verify_runner(state, monkeypatch):
    calls, responses = [], []
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return model_result(item)
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    return calls, responses


def test_generic_revise_does_not_spend_on_focused_gate(state, verify_runner):
    calls, responses = verify_runner
    responses.append(generic('REVISE'))
    out = agent.verify_artifact(RunContext(state), 'R4_IFR', {}, '')
    assert out['verdict'] == 'REVISE' and len(calls) == 1


def test_generic_pass_can_be_revised_by_evidence_grounded_focused_gate(state, verify_runner):
    calls, responses = verify_runner
    packet = ifr_packet(state)
    responses.extend([generic(), ifr_revise()])
    out = agent.verify_artifact(RunContext(state), 'R4_IFR', packet['artifact'], '')
    assert out['generic_verdict'] == 'PASS' and out['verdict'] == 'REVISE'
    assert out['focused_semantic_gate']['checks'][0]['status'] == 'REVISE'
    assert out['_tokens'] == (6, 10, .02)
    assert len(calls) == 2 and calls[1]['_analysis_reasoning'] is True
    from triz import verification_contract as contract
    from triz.settings import settings
    assert contract.normalize_verdict(out, contract.effective_rubric(settings, 'R4_IFR'))['verdict'] == 'REVISE'


@pytest.mark.parametrize('repair_ok', [True, False])
def test_one_malformed_review_retry_keeps_artifact_unchanged_and_counts_usage(state, verify_runner, repair_ok):
    calls, responses = verify_runner
    data = ifr_packet(state)['artifact']
    before = deepcopy(data)
    responses.extend([generic(), {'checks': []}, passed('R4_IFR') if repair_ok else {'checks': []}])
    out = agent.verify_artifact(RunContext(state), 'R4_IFR', data, '')
    assert out['verdict'] == ('PASS' if repair_ok else 'UNVERIFIED')
    assert len(calls) == 3 and data == before and out['_tokens'] == (9, 15, .03)
    assert len(out['focused_semantic_gate']['review_attempts']) == 2
    assert 'previous_review' in calls[-1]['user']
    if not repair_ok:
        assert out['verification_unavailable']


def test_focused_provider_failure_is_unverified_without_artifact_retry(state, verify_runner):
    calls, responses = verify_runner
    responses.extend([generic(), llm.LLMError('offline provider failure')])
    out = agent.verify_artifact(RunContext(state), 'R4_IFR', {}, '')
    assert out['verdict'] == 'UNVERIFIED' and out['verification_unavailable']
    assert len(calls) == 2 and out['_tokens'] == (3, 5, .01)


def test_exhausted_reviewer_format_repair_aborts_step_without_regenerating_artifact(state, verify_runner, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values: prompt_id + str(values))
    calls, responses = verify_runner
    responses.extend([{'statement': 'unmodified fixture'}, generic(), {'checks': []}, {'checks': []}])
    with pytest.raises(AbortRun):
        agent.run_agent(RunContext(state), node='s4_ifr', stage='S4', label='IFR', agent_id='problem_definer',
                        prompt_id='P_S4_IFR', rubric_id='R4_IFR', checker=lambda data: [], tier='T2')
    assert len(calls) == 4
    step = state.steps[-1]
    assert step.status == 'FAILED' and step.verdicts[-1]['verification_unavailable']
    assert step.output_json == {'statement': 'unmodified fixture'}
    assert step.tokens_in == 12 and step.tokens_out == 20 and step.cost_usd == .04


def test_attachment_text_correction_invalidates_focused_cached_pass(state, verify_runner, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values: prompt_id + str(values))
    state.intake.attachments = [Attachment(filename='flow.txt', extracted_text='Measured coolant flow is 10 kg/s.')]
    calls, responses = verify_runner
    value = {'statement': 'fixture'}
    responses.extend([value, generic(), passed('R4_IFR')])
    def run():
        return agent.run_agent(RunContext(state), node='s4_ifr', stage='S4', label='IFR', agent_id='problem_definer',
                               prompt_id='P_S4_IFR', rubric_id='R4_IFR', checker=lambda data: [], tier='T2')
    assert run() == value
    assert run() == value and len(calls) == 3 and state.steps[-1].status == 'SKIPPED'
    state.intake.attachments[0].extracted_text = 'Measured coolant flow is 20 kg/s.'
    responses.extend([value, generic(), passed('R4_IFR')])
    assert run() == value and len(calls) == 6 and state.steps[-1].status == 'OK'
    assert '20 kg/s' in calls[-1]['user']
