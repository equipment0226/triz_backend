"""Decimal-priced responses settle once without float rounding surcharges."""
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from triz import llm, store
from triz.ax import gateway, ledger
from triz.context import RunContext
from test_ax_refactor import newrun

CHAT_JSON = llm.chat_json


@pytest.mark.parametrize('finish,status', [('stop', 'COMPLETED'), ('length', 'FAILED')])
def test_exact_microusd_settlement_for_success_and_billed_failure(newrun, monkeypatch, finish, status):
    state = newrun()
    state.scratch['ax_bundle']['models']['T2'].update(
        model='deepseek-flash', base_url='https://api.deepseek.com/v1', cost_in=.3, cost_out=1.2)
    state.scratch['ax_bundle']['config']['ax']['max_provider_attempts'] = 1
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        # 20 * $0.15 + 200 * $0.60 per million = exactly 123 micro-USD.
        return SimpleNamespace(model='deepseek-flash', choices=[SimpleNamespace(
            finish_reason=finish, message=SimpleNamespace(content='{"ok":true}'))],
            usage=SimpleNamespace(prompt_tokens=20, completion_tokens=200,
                prompt_cache_hit_tokens=0, prompt_cache_miss_tokens=20))
    monkeypatch.setattr(llm, '_client', lambda *args: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setattr(llm, 'chat_json', CHAT_JSON)
    request = dict(_node='s5_track_h', system='JSON', user='offline price test', tier='T2')
    if finish == 'stop':
        result = gateway.chat(RunContext(state), **request)
    else:
        with pytest.raises(llm.LLMError) as caught:
            gateway.chat(RunContext(state), **request)
        result = caught.value.usage
    assert result.cost_usd == .000123
    with store.engine.connect() as conn:
        task = conn.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == state.run_id)).mappings().one()
    assert len(calls) == 1
    assert task['status'] == status and task['actual'] == 123
    assert ledger.budget(state.run_id)['spent_microusd'] == 123
