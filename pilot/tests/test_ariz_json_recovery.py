"""Recover complete report tables without inventing or dropping analysis."""
import copy
import json
from dataclasses import asdict
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from triz import llm, pipeline, store
from triz.context import AbortRun, RunContext
from triz.ax import gateway, ledger, runtime
from triz.ax.action_runtime import executing
from triz.ax.contracts import ActionTicket
from test_ax_refactor import newrun

CHAT_JSON = llm.chat_json


def table_response(outer_close=True):
    data = {'steps': [{'step_code': f'4.{i}', 'output': 'Keep literal ] } and "quotes".',
                      'status': 'DONE', 'table_columns': ['idea', 'condition'],
                      'table_rows': [['first', 'unknown'], ['second', 'measure first']]}
                     for i in range(1, 8)], 'ideas': [{'title': 'Keep every idea'}],
            'solution_directions': ['Preserve the whole root']}
    raw = json.dumps(data, separators=(',', ':')).replace('"table_rows":[', '')
    if not outer_close:
        raw = raw.replace(']]}', ']}')
    return data, raw


@pytest.mark.parametrize('outer_close', [True, False])
@pytest.mark.parametrize('wrapper', ['{}', '```json\n{}\n```', 'Result:\n{}\nEnd.'])
def test_complete_table_label_repair_preserves_every_field(outer_close, wrapper):
    data, raw = table_response(outer_close)
    assert llm.extract_json(wrapper.format(raw)) == data


@pytest.mark.parametrize('raw', [
    '{"table_columns":["a","b"],["only one"]]}',
    '{"table_columns":["a"],[null]]}',
    '{"table_columns":["a"],[{"unknown":"object"}]]}',
    '{"columns":["a"],["value"]]}',
    '{"table_columns":["a"],"note":"intervening field",["value"]]}',
    '{"table_columns":["a"],["value"]],"table_rows":[["replacement"]]}',
    '{"table_columns":["a"],["value"]],"other":}',
])
def test_ambiguous_or_incomplete_tables_are_not_accepted(raw):
    with pytest.raises(ValueError):
        llm.extract_json(raw)


def usage(raw):
    return llm.LLMResult(data=None, text=raw, model='offline', tier='T2', cost_usd=.01,
        tokens_in=100, tokens_out=100,
        raw_error='ValueError: JSON root container is malformed',
        meta={'attempt': 2, 'requests': [{'response': raw, 'finish_reason': 'stop',
                                       'usage': {'prompt_tokens': 100, 'completion_tokens': 100}}]})


@pytest.mark.parametrize('defect', ['truncated', 'unknown_usage', 'other_error', 'partial_root', 'wrong_shape'])
def test_failed_call_recovery_requires_complete_accounted_response(defect):
    _, raw = table_response()
    saved = asdict(usage(raw))
    if defect == 'truncated':
        saved['meta']['requests'][-1]['finish_reason'] = 'length'
    elif defect == 'unknown_usage':
        saved['meta']['requests'][-1]['usage'] = {}
    elif defect == 'other_error':
        saved['raw_error'] = 'TimeoutError: request failed'
    elif defect == 'partial_root':
        saved['text'] = raw[:-1]
        saved['meta']['requests'][-1]['response'] = saved['text']
    elif defect == 'wrong_shape':
        saved['text'] = '[]'
        saved['meta']['requests'][-1]['response'] = '[]'
    assert llm.recover_failed_json(saved) is None


def test_settled_failed_response_replays_without_new_charge(newrun, monkeypatch):
    state = newrun('DEEP')
    ctx = RunContext(state)
    expected, raw = table_response()
    paid = []
    def fail(**kwargs):
        paid.append(kwargs)
        error = llm.LLMError('Malformed JSON')
        error.usage = usage(raw)
        raise error
    monkeypatch.setattr(llm, 'chat_json', fail)
    ticket = ActionTicket(action_type='GENERATE_BASELINE', parameters={'tracks': ['D_ARIZ']},
        target_version_ids=[state.scratch['ax_members']['definition']], model_role='REASONING',
        expected_outputs=['TrackResult'], allowed_tools=['legacy_tracks'], reason='Required ARIZ')
    request = dict(_node='s5_ariz_p4', system='Return JSON', user='ARIZ Part4', tier='T2')
    with pytest.raises(llm.LLMError):
        with executing(ctx, ticket, context='track:D_ARIZ', optional=False):
            gateway.chat(ctx, **request)
    before = ledger.budget(state.run_id)
    runtime.checkpoint(state, 's5_solve', interrupted=True)
    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'user_resume')
    ledger.capture(state, {}, runtime.DEPENDENCIES, 'stage_read_set')
    with executing(ctx, ticket, context='track:D_ARIZ', optional=False):
        recovered = gateway.chat(ctx, **request)
        assert recovered.data == expected
        assert recovered.meta['durable_replay'] is True
        assert (recovered.tokens_in, recovered.tokens_out, recovered.cost_usd) == (0, 0, 0)
        assert recovered.meta['replay_source_usage'] == {
            'tokens_in': 100, 'tokens_out': 100, 'cost_usd': .01, 'settled_microusd': 10000}
        again = gateway.chat(ctx, **request)
        assert again.data == expected
        assert (again.tokens_in, again.tokens_out, again.cost_usd) == (0, 0, 0)
        assert again.meta['replay_source_usage'] == recovered.meta['replay_source_usage']
    assert len(paid) == 1
    assert ledger.budget(state.run_id) == before
    with store.engine.connect() as connection:
        tasks = connection.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == state.run_id)).mappings().all()
        audit = connection.execute(select(ledger.events).where(ledger.events.c.run_id == state.run_id,
            ledger.events.c.event_type == 'ACTION_FORMAT_RECOVERED')).mappings().all()
    assert len(tasks) == 1 and tasks[0]['status'] == 'FAILED' and tasks[0]['actual'] == 10000
    assert recovered.meta['source_task_id'] == tasks[0]['task_id']
    original = json.loads(tasks[0]['result'])['usage']
    assert (original['tokens_in'], original['tokens_out'], original['cost_usd']) == (100, 100, .01)
    assert len(audit) == 1


def test_changed_analysis_does_not_reuse_old_track_read_set(newrun):
    from triz.ax.action_runtime import active_action
    state = newrun('DEEP')
    ctx = RunContext(state)
    ticket = ActionTicket(action_type='GENERATE_BASELINE', parameters={'tracks': ['D_ARIZ']},
        target_version_ids=[state.scratch['ax_members']['definition']], model_role='REASONING',
        expected_outputs=['TrackResult'], allowed_tools=['legacy_tracks'], reason='Required ARIZ')
    with executing(ctx, ticket, context='track:D_ARIZ', optional=False):
        original = dict(active_action.get()['exact_input_versions'])
    ledger.capture(state, {'analysis': {'changed': True}}, {}, 'changed_analysis')
    with executing(ctx, ticket, context='track:D_ARIZ', optional=False):
        assert active_action.get()['exact_input_versions']['analysis'] != original['analysis']


def test_retry_feedback_includes_late_json_error(monkeypatch):
    broken = '{"long":"' + 'x' * 5000 + '","missing":}'
    requests = []
    def create(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        text = broken if len(requests) == 1 else '{"long":"preserved","missing":null}'
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason='stop')],
                               usage=None, model='offline')
    monkeypatch.setattr(llm, '_client', lambda *a: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm.time, 'sleep', lambda *a: None)
    result = CHAT_JSON(system='JSON', user='Keep all fields', retries=2)
    assert result.data['long'] == 'preserved'
    excerpt = requests[1]['messages'][-2]['content']
    assert '"missing":}' in excerpt and len(excerpt) <= 4000
    assert '파서 오류:' in requests[1]['messages'][-1]['content']


def test_ariz_stop_exposes_specific_part_in_retry_notification(state, monkeypatch):
    reason = 'ARIZ Part4 검토가 완전하지 않아 후속 분석을 중단합니다. FATAL-ARIZ: steps 누락'
    def stop(ctx):
        raise AbortRun(reason)
    monkeypatch.setattr(pipeline, 'PIPELINE', [('s5_solve', 'Solve', stop)])
    assert pipeline.execute_stage(state.run_id, 0)['status'] == 'INTERRUPTED'
    assert store.load_state(state.run_id).scratch['interruption_reason'] == reason
