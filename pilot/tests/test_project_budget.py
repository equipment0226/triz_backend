"""Project budgets are independent and resume never replenishes the allowance."""
import pytest

from triz import pipeline, store
from triz.settings import Settings, settings
from triz.execution_config import profile


def test_environment_sets_both_budget_defaults(monkeypatch):
    monkeypatch.setenv('TRIZ_PROJECT_BUDGET_USD', '1')
    configured = Settings.__new__(Settings)
    configured.triz = {'run': {'budget_usd': 3}, 'ax': {'hard_budget_usd': .6}}
    configured._apply_env_overrides()
    assert configured.triz['run']['budget_usd'] == 1
    assert configured.triz['ax']['hard_budget_usd'] == 1


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf'])
def test_invalid_budget_is_rejected(monkeypatch, value):
    monkeypatch.setenv('TRIZ_PROJECT_BUDGET_USD', value)
    configured = Settings.__new__(Settings)
    configured.triz = {}
    with pytest.raises(ValueError):
        configured._apply_env_overrides()


def test_legacy_creation_ignores_old_context_and_resume_keeps_cap(monkeypatch):
    monkeypatch.setitem(settings.triz['run'], 'budget_usd', 1.0)
    token = profile.set({'config': {'run': {'budget_usd': 3}}})
    try:
        first = pipeline.create_run('Legacy budget isolation', workflow_version='legacy')
    finally:
        profile.reset(token)
    assert first.cost.budget_usd == 1
    first.cost.total_usd = .8
    first.status = 'INTERRUPTED'
    store.save_state(first)
    second = pipeline.create_run('Independent legacy project', workflow_version='legacy')
    assert second.cost.total_usd == 0 and second.cost.budget_usd == 1
    monkeypatch.setitem(settings.triz['run'], 'budget_usd', 10.0)
    monkeypatch.setattr(pipeline, 'start', lambda _: None)
    assert pipeline.continue_run(first.run_id)
    resumed = store.load_state(first.run_id)
    assert resumed.cost.budget_usd == 1 and resumed.cost.total_usd == .8
