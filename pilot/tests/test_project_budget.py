"""Project budgets are independent and resume never replenishes the allowance."""
import pytest

from triz import pipeline, store
from triz.settings import Settings, settings
from triz.execution_config import profile


def test_environment_sets_both_budget_defaults(monkeypatch):
    monkeypatch.setenv('TRIZ_PROJECT_BUDGET_USD', '2')
    configured = Settings.__new__(Settings)
    configured.triz = {'run': {'budget_usd': 3}, 'ax': {'hard_budget_usd': .6}}
    configured._apply_env_overrides()
    assert configured.triz['run']['budget_usd'] == 2
    assert configured.triz['ax']['hard_budget_usd'] == 2


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf'])
def test_invalid_budget_is_rejected(monkeypatch, value):
    monkeypatch.setenv('TRIZ_PROJECT_BUDGET_USD', value)
    configured = Settings.__new__(Settings)
    configured.triz = {}
    with pytest.raises(ValueError):
        configured._apply_env_overrides()


def test_legacy_creation_ignores_old_context_and_resume_keeps_cap(monkeypatch):
    monkeypatch.setitem(settings.triz['run'], 'budget_usd', 2.0)
    token = profile.set({'config': {'run': {'budget_usd': 3}}})
    try:
        first = pipeline.create_run('Legacy budget isolation', workflow_version='legacy')
    finally:
        profile.reset(token)
    assert first.cost.budget_usd == 2
    first.cost.total_usd = .8
    first.status = 'INTERRUPTED'
    store.save_state(first)
    second = pipeline.create_run('Independent legacy project', workflow_version='legacy')
    assert second.cost.total_usd == 0 and second.cost.budget_usd == 2
    monkeypatch.setitem(settings.triz['run'], 'budget_usd', 10.0)
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    assert pipeline.continue_run(first.run_id)
    resumed = store.load_state(first.run_id)
    assert resumed.cost.budget_usd == 2 and resumed.cost.total_usd == .8


@pytest.mark.parametrize('workflow', ['legacy', 'triz-ax-v3.1'])
def test_authorized_existing_cap_increase_preserves_content_and_usage(monkeypatch, workflow):
    import copy
    import json
    from sqlalchemy import select, update
    from triz import budget_limits
    from triz.ax import ledger
    monkeypatch.setitem(settings.triz['run'], 'budget_usd', 1)
    monkeypatch.setitem(settings.triz['ax'], 'hard_budget_usd', 1)
    current = pipeline.create_run('Existing budget migration', workflow_version=workflow)
    current.status = 'INTERRUPTED'
    current.cost.total_usd = .9
    current.cost.over_budget = True
    store.save_state(current)
    if workflow != 'legacy':
        task = ledger.acquire(current.run_id, 0, {'migration_probe': True}, 900000)
        ledger.settle(task, {}, 900000)
        reservation = ledger.acquire(current.run_id, 0, {'pending_probe': True}, 10000)
    with store.engine.begin() as c:
        before = json.loads(c.execute(select(store.states.c.state_json)
            .where(store.states.c.run_id == current.run_id)).scalar_one())
        before['unknown_historical_field'] = {'preserve': True}
        c.execute(update(store.states).where(store.states.c.run_id == current.run_id)
            .values(state_json=json.dumps(before)))
        run_before = dict(c.execute(select(store.runs).where(store.runs.c.run_id == current.run_id)).mappings().one())
    result = budget_limits.increase(current.run_id, 2, reason='Explicit test authorization')
    assert result['changed'] and result['spent_usd'] == .9 and result['limit_usd'] == 2
    with store.engine.connect() as c:
        after = json.loads(c.execute(select(store.states.c.state_json)
            .where(store.states.c.run_id == current.run_id)).scalar_one())
        assert dict(c.execute(select(store.runs).where(store.runs.c.run_id == current.run_id)).mappings().one()) == run_before
    expected = copy.deepcopy(before)
    expected['cost'].update(budget_usd=2, over_budget=False)
    assert after == expected
    if workflow != 'legacy':
        assert ledger.budget(current.run_id)['spent_microusd'] == 900000
        assert ledger.budget(current.run_id)['reserved_microusd'] == 10000
        assert ledger.budget(current.run_id)['limit_microusd'] == 2000000
    assert not budget_limits.increase(current.run_id, 2, reason='Repeat request')['changed']
    assert not budget_limits.increase(current.run_id, 1, reason='Never lower')['changed']
