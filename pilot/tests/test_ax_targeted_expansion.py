import json
import copy
import pytest
from test_ax_refactor import newrun
from triz import nodes, llm
from triz.context import RunContext
from triz.ax import coordinator
from triz.ax.action_runtime import executing
from triz.ax.contracts import ActionTicket, digest
from triz.ax.mode_contract import PROFILES
from triz.ax import exploration_context as exploration, ledger, routing_q
from triz.ax.action_runtime import active_action
from triz.schema import RawIdea, TechnicalContradiction


def prepare(state):
    state.scratch['ax_bundle']['effects'][0]['function_ko'] = '열 제거'
    coordinator.route(RunContext(state))
    state.scratch['ax_track_execution'] = {t: dict(status='COMPLETED', output_count=1) for t in PROFILES[state.control.mode.value]['tracks']}


def target_ticket(state, track='H_EFFECTS', ids=None):
    payload = exploration.build(state, ids or ['TC1'], ['UNCOVERED_OBLIGATION'])
    return ActionTicket(action_type='SOLVE_SUBPROBLEM', model_role='REASONING',
        target_version_ids=[state.scratch['ax_members']['definition']],
        parameters=dict(optional=True, tracks=[track], obligation_ids=ids or ['TC1'],
                        exploration_context=payload, semantic_context_hash=digest(payload)),
        allowed_tools=['legacy_tracks'], expected_outputs=['RawIdea'], reason='target')


def fake_provider(monkeypatch, states, *, application=False):
    calls = []
    def provider(**kw):
        step = next((s for state in states for s in reversed(state.steps)
                     if s.input_slice and s.input_slice.get('user') == kw['user']), None)
        prompt = step.input_slice['prompt_id'] if step else 'VERIFIER'
        calls.append(dict(kw, prompt=prompt))
        data = dict(applications=[], no_application_reason='새 적용 조건의 근거가 없어 보류한다.', principle_ids=[1], verdict='PASS', score=1.)
        if prompt == 'P_S5_MERGE':
            ids = step.input_slice['vars']['allowed_idea_ids']
            data.update(ideas=[dict(keep_ids=[i], title='대표안', idea='기구 유지', selection_reason='조건 검토 가능', resolution_status='UNSUPPORTED') for i in ids[:10]],
                        deferred=[dict(keep_ids=[i], reason='조건의 검증 근거가 부족하여 후속 실험까지 보류') for i in ids[10:]],
                        need_more=True, gaps=['미검증'], coverage_note='미해결')
        if application and prompt == 'P_S5_TRACK_H':
            data['applications'] = [dict(effect_id='E1', effect_name='First', idea='전도판 접촉면에 유연한 연결부를 설치하여 동일한 전도 효과를 다른 조건에서 이용한다.',
                mechanism='전도 경로 접촉면 수정', mechanism_key='modified-contact', intervention_variable='접촉면',
                conditions=['전도 경로 확보'], strongest_objection='접촉 저항 미검증', validation_test='열 저항 측정',
                required_function='열 제거', principle='전도', application='접촉면 변경')]
        return llm.LLMResult(data=data, text=json.dumps(data, ensure_ascii=False), cost_usd=.00001,
                             meta={'requests': [{'usage': {'input_tokens': 10, 'output_tokens': 10}}]})
    monkeypatch.setattr(llm, 'chat_json', provider)
    return calls


def test_e01_real_h_provider_receives_target_before_cache(newrun, monkeypatch):
    state = newrun()
    state.scratch['ax_bundle']['effects'][0]['function_ko'] = '열 제거'
    coordinator.route(RunContext(state))
    state.scratch['ax_track_execution'] = {t: dict(status='COMPLETED', output_count=1) for t in PROFILES['FULL']['tracks']}
    calls = []
    data = {'applications': [], 'no_application_reason': '검증 가능한 새로운 적용 조건이 없습니다.'}
    def provider(**kw):
        calls.append(kw)
        return llm.LLMResult(data=data.copy(), text=json.dumps(data), cost_usd=.00001,
                             meta={'requests': [{'usage': {'input_tokens': 10, 'output_tokens': 10}}]})
    monkeypatch.setattr(llm, 'chat_json', provider)
    ctx = RunContext(state)
    nodes._track_h(ctx)
    payload = dict(schema='triz-targeted-expansion-v1',
        target_obligations=[dict(obligation_id='TC1', contradiction_ids=['TC1'], description='target', improve='열 제거', protect='전력 증가')],
        required_functions=['열 제거', '전력 증가'], function_mapping='UNAVAILABLE_TARGET_SIDES_AS_SEARCH_CLUES',
        gap_kinds=['UNCOVERED_OBLIGATION'], prior_mechanisms=[dict(source_idea_ids=['prior'], mechanism='기존 전도판',
        mechanism_key='plate', intervention='접촉면', conditions=['진공'], resolution_status='UNSUPPORTED', gap_reason='가설: 접촉저항 미검증')],
        required_new_direction='기존 기구의 조건을 보완하거나 다른 기구를 제안한다.', preserve_requirements=True)
    ticket = ActionTicket(action_type='SOLVE_SUBPROBLEM', model_role='REASONING',
        target_version_ids=[state.scratch['ax_members']['definition']],
        parameters=dict(optional=True, tracks=['H_EFFECTS'], obligation_ids=['TC1'],
                        exploration_context=payload, semantic_context_hash=digest(payload)),
        allowed_tools=['legacy_tracks'], expected_outputs=['RawIdea'], reason='target')
    with executing(ctx, ticket):
        nodes._track_h(ctx)
    assert len(calls) == 2
    user = calls[-1]['user']
    assert 'triz-targeted-expansion-v1' in user
    assert all(word in user for word in ('열 제거', '전력 증가', '기존 전도판', '접촉저항 미검증'))


@pytest.mark.parametrize('track,prompt', [('H_EFFECTS', 'P_S5_TRACK_H'), ('G_FOS', 'P_S5_TRACK_G'), ('A_MATRIX', 'P_S5_TRACK_A')])
def test_e02_e03_e10_e15_real_coordinator_thread_prompt_and_merge(newrun, monkeypatch, track, prompt):
    state = newrun(); prepare(state)
    state.solve.raw_ideas = [RawIdea(id='original', title='원안', idea='기존 전도판', mechanism='기존 전도판',
        conditions=['진공 접촉'], strongest_objection='접촉저항 미검증', addresses=['TC1'])]
    calls = fake_provider(monkeypatch, [state])
    monkeypatch.setattr(routing_q, 'choose', lambda p, f, tickets, mask, preferred:
        (next(i for i, t in enumerate(tickets) if t['parameters'].get('tracks') == [track]), {}, None))
    state.scratch['ax_bundle']['policy'] = {'offline_fixture': True}
    assert coordinator.expand(RunContext(state), True)
    generation = [c for c in calls if c['prompt'] == prompt]
    assert len(generation) == 1
    assert all(word in generation[0]['user'] for word in ('열 제거', '전력 증가', '기존 전도판', '진공 접촉', '접촉저항 미검증'))
    assert active_action.get() is None
    assert all('목표 기반 추가 탐색 계약' not in c['user'] for c in calls if c['prompt'] in ('P_S5_MERGE', 'VERIFIER'))
    decision = ledger.decision_history(state.run_id, state.user_id)[0]['payload']
    ticket = decision['actions'][decision['executed_index']]['ticket']
    step = next(s for s in state.steps if s.input_slice.get('prompt_id') == prompt)
    result = state.scratch['ax_action_results'][decision['executed_action_instance']]
    assert result['semantic_context_hash'] == ticket['parameters']['semantic_context_hash'] == step.input_slice['semantic_context_hash']
    assert step.input_slice['exploration_context'] == ticket['parameters']['exploration_context']
    assert result['contribution_status'] == 'NO_NEW_INFORMATION'
    assert result['ticket']['parameters']['tracks'] == [track]
    assert state.scratch['idea_consolidation']['coverage_complete']
    assert state.scratch['idea_consolidation']['source_ideas'][0]['conditions'] == ['진공 접촉']
    assert state.solve.raw_ideas[0].resolution_status == 'UNSUPPORTED'
    if track != 'A_MATRIX':
        assert step.input_slice['vars']['required_functions'] == ticket['parameters']['exploration_context']['required_functions']
    else:
        assert state.solve.matrix_lookups[0].source_tc_id == 'TC1'


def test_e04_e06_agent_and_durable_retry_ignore_attempt_and_epoch(newrun, monkeypatch):
    state = newrun(); prepare(state)
    calls = fake_provider(monkeypatch, [state])
    ctx = RunContext(state); ticket = target_ticket(state)
    with executing(ctx, ticket): nodes._track_h(ctx)
    spent = ledger.budget(state.run_id)['spent_microusd']
    with executing(ctx, ticket): nodes._track_h(ctx)
    assert len(calls) == 1  # agent cache
    state.scratch['agent_cache'] = {}
    ticket.parameters['attempt'] = 2
    ticket.action_instance_id = 'different-audit-identity'
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'resume')
    with executing(ctx, ticket, decision_id='another-decision'): nodes._track_h(ctx)
    assert len(calls) == 1  # durable cache
    assert ledger.budget(state.run_id)['spent_microusd'] == spent


@pytest.mark.parametrize('field', ['condition', 'mechanism', 'gap', 'target'])
def test_e05_semantic_changes_invalidate_cache(newrun, monkeypatch, field):
    state = newrun(); prepare(state)
    state.solve.raw_ideas = [RawIdea(id='prior', idea='prior', mechanism='plate', conditions=['vacuum'])]
    calls = fake_provider(monkeypatch, [state]); ctx = RunContext(state)
    first = target_ticket(state)
    with executing(ctx, first): nodes._track_h(ctx)
    if field == 'condition': state.solve.raw_ideas[0].conditions = ['fluid']
    if field == 'mechanism': state.solve.raw_ideas[0].mechanism = 'heat pipe'
    if field == 'gap': state.solve.raw_ideas[0].strongest_objection = '새로운 미검증 가설'
    second = target_ticket(state, ids=['PC1'] if field == 'target' else ['TC1'])
    assert first.parameters['semantic_context_hash'] != second.parameters['semantic_context_hash']
    with executing(ctx, second): nodes._track_h(ctx)
    assert len(calls) == 2


def test_e07_parallel_run_context_and_cost_isolation(newrun, monkeypatch):
    from triz.execution_config import ThreadPoolExecutor
    states = [newrun(user='parallel-one'), newrun(user='parallel-two')]
    for s in states: prepare(s)
    states[1].definition.technical_contradictions[0].then_good = '별도 사용자 목표'
    calls = fake_provider(monkeypatch, states)
    def run(state):
        with executing(RunContext(state), target_ticket(state)):
            nodes._run_tracks(RunContext(state), ['H_EFFECTS'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, states))
    assert len(calls) == 2 and active_action.get() is None
    assert sum('별도 사용자 목표' in c['user'] for c in calls) == 1
    assert all(ledger.budget(s.run_id)['spent_microusd'] == 10 for s in states)
    assert states[0].scratch['agent_cache'] is not states[1].scratch['agent_cache']


def test_e08_exception_reset_and_invalid_target_rejected(newrun):
    state = newrun(); prepare(state)
    with pytest.raises(RuntimeError):
        with executing(RunContext(state), target_ticket(state)):
            raise RuntimeError('handler interruption')
    assert active_action.get() is None
    from triz.ax.contracts import Conflict
    with pytest.raises(Conflict): exploration.build(state, ['FOREIGN'], ['GAP'])
    ticket = target_ticket(state)
    state.definition.technical_contradictions[0].then_good = 'changed'
    with pytest.raises(Conflict):
        with executing(RunContext(state), ticket): pass
    assert active_action.get() is None


def test_e09_unknown_reservation_survives_audit_changes(newrun, monkeypatch):
    from triz.context import AbortRun, UsageUncertain
    state = newrun(); prepare(state); calls = []
    def unknown(**kw):
        calls.append(kw)
        return llm.LLMResult(data={}, meta={'requests': [{'usage': None}]})
    monkeypatch.setattr(llm, 'chat_json', unknown)
    ticket = target_ticket(state); ctx = RunContext(state)
    with pytest.raises(AbortRun):
        with executing(ctx, ticket): nodes._track_h(ctx)
    held = ledger.budget(state.run_id)['reserved_microusd']
    assert held > 0
    ticket.parameters['attempt'] = 2; ticket.action_instance_id = 'retry-audit'
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'resume')
    with pytest.raises(UsageUncertain):
        with executing(ctx, ticket): nodes._track_h(ctx)
    assert len(calls) == 1 and ledger.budget(state.run_id)['reserved_microusd'] == held


def test_e13_same_effect_allowed_new_application_and_retry_no_duplicate(newrun, monkeypatch):
    state = newrun(); prepare(state)
    state.solve.raw_ideas = [RawIdea(id='prior', idea='prior', mechanism='전도판', detail={'source_effect_id': 'E1'})]
    calls = fake_provider(monkeypatch, [state], application=True)
    ctx = RunContext(state); ticket = target_ticket(state)
    with executing(ctx, ticket): nodes._track_h(ctx)
    ids = [i.id for i in state.solve.raw_ideas]
    assert len(ids) == 2
    with executing(ctx, ticket): nodes._track_h(ctx)
    assert [i.id for i in state.solve.raw_ideas] == ids and len(calls) == 1


def test_old_pinned_run_keeps_original_generation_semantics(newrun, monkeypatch):
    state = newrun(); prepare(state)
    state.scratch['ax_bundle'].pop('exploration_contract')
    calls = fake_provider(monkeypatch, [state])
    with executing(RunContext(state), target_ticket(state)):
        nodes._track_h(RunContext(state))
    assert '목표 기반 추가 탐색 계약' not in calls[0]['user']


def test_e10_real_addition_all_sources_and_max_ten(newrun, monkeypatch):
    state = newrun(); prepare(state)
    state.solve.raw_ideas = [RawIdea(id=f'original-{i}', title=f'원안 {i}', idea='원안 기구',
        mechanism=f'기구 {i}', conditions=[f'조건 {i}'], addresses=['TC1']) for i in range(11)]
    calls = fake_provider(monkeypatch, [state], application=True)
    monkeypatch.setattr(routing_q, 'choose', lambda p, f, tickets, mask, preferred:
        (next(i for i, t in enumerate(tickets) if t['parameters'].get('tracks') == ['H_EFFECTS']), {}, None))
    state.scratch['ax_bundle']['policy'] = {'offline_fixture': True}
    assert coordinator.expand(RunContext(state), True)
    record = state.scratch['idea_consolidation']
    assert record['input_count'] == 12 and len(state.solve.raw_ideas) == 10
    assert len(record['deferred']) == 2 and record['coverage_complete']
    assert len(record['source_ideas']) == 12
    assert {f'original-{i}' for i in range(11)} <= {r['source_idea_id'] for r in record['source_ideas']}
    assert all(r['conditions'] for r in record['source_ideas'])
    assert all(i.resolution_status == 'UNSUPPORTED' for i in state.solve.raw_ideas)
    assert any(c['prompt'] == 'P_S5_MERGE' for c in calls)


def test_e03_a_only_recorded_pc_parent_and_user_selection(newrun, monkeypatch):
    from triz.schema import KeyProblem
    state = newrun(); prepare(state)
    state.definition.technical_contradictions.append(TechnicalContradiction(id='TC2', if_action='다른 개입', then_good='별도 개선측', but_bad='별도 보호측'))
    state.definition.physical_contradictions[0].derived_from_tc_id = 'TC2'
    ticket = target_ticket(state, track='A_MATRIX', ids=['PC1'])
    calls = fake_provider(monkeypatch, [state])
    with executing(RunContext(state), ticket):
        nodes._run_tracks(RunContext(state), ['A_MATRIX'])
    assert [x.source_tc_id for x in state.solve.matrix_lookups] == ['TC2']
    generation = [c for c in calls if c['prompt'] == 'P_S5_TRACK_A']
    assert len(generation) == 1 and '별도 개선측' in generation[0]['user']
    state.definition.physical_contradictions[0].derived_from_tc_id = ''
    context = exploration.build(state, ['PC1'], ['GAP'])
    assert exploration.target_tcs(state, context) == []
    state.definition.key_problems = [KeyProblem(contradiction_ids=['TC1'])]
    context = exploration.build(state, ['TC2'], ['GAP'])
    assert exploration.target_tcs(state, context) == []


def test_e09_optional_budget_still_defers_without_call(newrun, monkeypatch):
    state = newrun(); prepare(state)
    state.scratch['ax_bundle']['limits']['optional_budget_microusd'] = 1
    calls = fake_provider(monkeypatch, [state])
    with executing(RunContext(state), target_ticket(state)):
        nodes._track_h(RunContext(state))
    assert calls == [] and state.scratch['ax_optional_deferred_budget']
    assert ledger.budget(state.run_id)['spent_microusd'] == 0


def test_context_digest_bounded_but_constraints_and_sides_preserved(newrun):
    state = newrun(); prepare(state)
    state.definition.technical_contradictions[0].then_good = '개선측' * 2000
    state.solve.raw_ideas = [RawIdea(id=f'prior-{i}', idea='prior', mechanism='mechanism' * 200,
        conditions=['조건' * 1000], addresses=['TC1']) for i in range(30)]
    context = exploration.build(state, ['TC1'], ['GAP'])
    assert len(json.dumps(context['prior_mechanisms'], ensure_ascii=False).encode()) <= exploration.MAX_PRIOR_BYTES + 100
    assert context['target_obligations'][0]['improve'] == state.definition.technical_contradictions[0].then_good
    assert context['constraints'] == state.constraints.model_dump(mode='json')
    assert context['prior_digest_omitted'] > 0 and len(state.solve.raw_ideas) == 30
