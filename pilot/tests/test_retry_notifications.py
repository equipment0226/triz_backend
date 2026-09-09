from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from triz import agent, domain, llm, nodes, pipeline, store
from triz.context import HumanInterrupt, RunContext
from triz.schema import ClarifyTurn, Constraint, HumanRequest, RawIdea, StepRecord, TechnicalContradiction

CHAT_JSON = llm.chat_json


def test_retry_notifications_are_owner_scoped_stable_and_clear_on_resume(monkeypatch):
    own = pipeline.create_run('owner problem', user_id='retry-owner')
    other = pipeline.create_run('private problem', user_id='retry-other')
    for state in (own, other):
        state.status = 'FAILED'
        state.control.errors = ['private raw traceback that must not appear']
        store.save_state(state)
    notice = store.pending_notifications('retry-owner')
    assert len(notice) == 1 and notice[0]['run_id'] == own.run_id
    assert notice[0]['kind'] == 'RETRY_REQUIRED'
    assert 'traceback' not in str(notice)
    assert store.pending_notifications('retry-owner')[0]['id'] == notice[0]['id']
    monkeypatch.setattr(pipeline, 'start', lambda rid: None)
    assert pipeline.continue_run(own.run_id)
    assert store.pending_notifications('retry-owner') == []
    own = store.load_state(own.run_id)
    own.status = 'INTERRUPTED'
    store.save_state(own)
    assert store.pending_notifications('retry-owner')[0]['id'] != notice[0]['id']


def test_pending_human_request_takes_precedence_over_retry_notice(state):
    state.pending = HumanRequest(kind='CLARIFY', title='조건 확인', payload={})
    state.status = 'INTERRUPTED'
    store.save_state(state)
    notices = [n for n in store.pending_notifications(state.user_id) if n['run_id'] == state.run_id]
    assert len(notices) == 1 and notices[0]['id'] == state.pending.interrupt_id
    assert notices[0]['kind'] == 'CLARIFY'


def test_failed_intake_keeps_answers_and_previous_frame_without_new_questions(state, monkeypatch):
    state.control.stage_index = 2
    state.status = 'RUNNING'
    state.intake.frame.symptom = 'previous observed symptom'
    state.constraints.items = [Constraint(statement='confirmed limit')]
    state.intake.clarify_turns = [ClarifyTurn(question='what is the limit?')]
    state.scratch['resume_payload'] = {'answers': ['retain 95%']}
    store.save_state(state)
    calls = []
    def failed(ctx, **kw):
        calls.append(kw)
        step = ctx.start_step(node=kw['node'], label=kw['label'], stage=kw['stage'],
            agent_id=kw['agent_id'], prompt_id=kw['prompt_id'], tier=kw['tier'])
        ctx.finish_step(step, 'FAILED')
        return kw['default']
    monkeypatch.setattr(agent, 'run_agent', failed)
    result = pipeline.execute_stage(state.run_id, 2)
    saved = store.load_state(state.run_id)
    assert result['status'] == 'INTERRUPTED' and saved.pending is None
    assert saved.intake.frame.symptom == 'previous observed symptom'
    assert saved.constraints.items[0].statement == 'confirmed limit'
    assert saved.intake.clarify_turns[0].user_answer == 'retain 95%'
    assert saved.intake.clarify_turns[0].answered
    assert [c['node'] for c in calls] == ['s1_extract']
    assert calls[0]['max_tokens'] == 4800


def test_confirmed_catalog_fallback_resolves_failed_research_without_claiming_success(state, monkeypatch):
    def failed(ctx, **kw):
        step = ctx.start_step(node=kw['node'], label=kw['label'], stage=kw['stage'],
            agent_id=kw['agent_id'], prompt_id=kw['prompt_id'], tier=kw['tier'])
        ctx.finish_step(step, 'FAILED')
        return {}
    monkeypatch.setattr(agent, 'run_agent', failed)
    with pytest.raises(HumanInterrupt):
        domain.deep_dive(RunContext(state))
    original = state.steps[-1]
    state.scratch['resume_payload'] = {'answers': ['observed boundary']}
    domain.deep_dive(RunContext(state))
    assert original.status == 'FAILED'
    assert original.step_id in state.scratch['resolved_step_failures']
    assert state.scratch['deep_dive']['answer_turns'][0]['answer'] == 'observed boundary'
    assert len(state.steps) == 1


def test_compact_merge_restores_all_original_resources_conditions_and_provenance(state, monkeypatch):
    tc = TechnicalContradiction(label='two goals')
    state.definition.technical_contradictions = [tc]
    first = RawIdea(title='first', idea='existing mechanism', mechanism='preserved mechanism',
        addresses=[tc.id], uses_resources=['sensor'], conditions=['condition one'], source_ref='source one')
    second = RawIdea(title='second', uses_resources=['operator'], conditions=['condition two'],
        hypothesis_ids=['H2'], source_ref='source two')
    state.solve.raw_ideas = [first, second]
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **kw: {'ideas': [{
        'keep_ids': [first.id, second.id], 'addresses': [tc.id],
        'resolution_status': 'RESOLVED', 'resolution_argument': 'both hold when condition one and two hold'}]})
    nodes._merge(RunContext(state))
    merged = state.solve.raw_ideas[0]
    assert merged.title == first.title and merged.mechanism == first.mechanism
    assert merged.uses_resources == ['sensor', 'operator']
    assert merged.conditions == ['condition one', 'condition two']
    assert merged.source_idea_ids == [first.id, second.id]
    assert merged.hypothesis_ids == ['H2'] and len(merged.detail['source_details']) == 2
    assert 'source one' in merged.source_ref and 'source two' in merged.source_ref


def response(finish, text):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20))


def test_truncation_retry_keeps_required_ids_and_counts_all_attempts(monkeypatch):
    create = Mock(side_effect=[response('length', '{"items":[{"id":"A"}'),
                               response('stop', '{"items":[{"id":"A"},{"id":"B"}]}')])
    monkeypatch.setattr(llm, '_client', lambda tier: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm.time, 'sleep', lambda _: None)
    result = CHAT_JSON(system='JSON', user='Evaluate A and B', max_tokens=2000, retries=2)
    assert [i['id'] for i in result.data['items']] == ['A', 'B']
    correction = create.call_args_list[1].kwargs['messages'][-1]['content']
    assert '모든 대상 ID' in correction and '60%' not in correction
    assert result.meta['attempt'] == 2 and result.tokens_out == 40


def test_truncated_partial_json_never_becomes_success(monkeypatch):
    create = Mock(return_value=response('length', '{"items":[{"id":"A"}]}'))
    monkeypatch.setattr(llm, '_client', lambda tier: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    with pytest.raises(llm.LLMError) as error:
        CHAT_JSON(system='JSON', user='Evaluate A and B', retries=1)
    assert error.value.usage.tokens_out == 20
