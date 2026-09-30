"""Reprice recorded calls explicitly; keep source evidence and past cutoffs intact."""
import json
import threading
from dataclasses import asdict

import pytest
from sqlalchemy import select, update

from triz import llm, store
from triz.ax import cost_restatements as costs, ledger
from triz.ax.contracts import Conflict
from test_ax_refactor import newrun

FLASH = dict(model='deepseek-flash', base_url='https://api.deepseek.com/v1', cost_in=.3, cost_out=1.2)


def completed(newrun):
    state = newrun()
    tasks = []
    for i in range(2):
        task = ledger.acquire(state.run_id, state.scratch['execution_epoch'],
            {'node':'s5_track_h', 'request':{'tier':'T2', 'user':str(i), 'model_config':FLASH}}, 1000)
        result = llm.LLMResult(data={'ok':True}, text='{"ok":true}', model='deepseek-flash',
            tokens_in=100, tokens_out=20, cost_usd=.000054,
            meta={'requests':[{'usage':{'prompt_tokens':100, 'completion_tokens':20,
                'prompt_cache_hit_tokens':80, 'prompt_cache_miss_tokens':20}}]})
        ledger.settle(task, asdict(result), 54)
        tasks.append(task)
    state.status = 'COMPLETED'
    state.scratch['ax_report_snapshot_id'] = 'report-v1'
    state.cost.total_usd = .000108
    state.cost.by_tier = {'T2':.000108}
    state.cost.by_stage = {'S5_SOLVE':.000108}
    state.cost.tokens_in = 200
    state.cost.tokens_out = 40
    state.cost.request_count = 2
    store.save_state(state)
    return state, tasks


def originals(run_id):
    with store.engine.connect() as c:
        return [dict(r) for r in c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id==run_id)).mappings()], \
            [dict(r) for r in c.execute(select(ledger.attempts).where(ledger.attempts.c.run_id==run_id)).mappings()]


def test_apply_is_idempotent_preserves_receipts_and_past_prices(newrun):
    state, tasks = completed(newrun)
    before = originals(state.run_id)
    with store.engine.connect() as c:
        ended = c.execute(select(store.runs.c.ended_at).where(store.runs.c.run_id==state.run_id)).scalar_one()
    plan = costs.plan(state.run_id, state.user_id)
    assert plan['before_microusd'] == 108 and plan['after_microusd'] == 32
    assert plan['after_cost']['by_tier'] == {'T2':.000032}
    assert plan['after_cost']['by_stage'] == {'S5_SOLVE':.000032}
    applied = costs.apply(plan, state.user_id)
    assert costs.apply(plan, state.user_id) == applied
    assert originals(state.run_id) == before
    assert ledger.budget(state.run_id)['spent_microusd'] == 32
    saved = store.load_state(state.run_id)
    assert saved.cost.total_usd == .000032
    assert saved.cost.tokens_in == 200 and saved.cost.request_count == 2
    assert costs.report_cost(saved, 'report-v1', plan['before_cost']) == plan['after_cost']
    assert costs.report_cost(saved, 'other-report', plan['before_cost']) == plan['before_cost']
    with store.engine.connect() as c:
        assert costs.overrides(c,state.run_id,'2000-01-01T00:00:00+00:00') == {}
        assert costs.overrides(c,state.run_id) == {t['task_id']:16 for t in tasks}
        assert c.execute(select(store.runs.c.ended_at).where(store.runs.c.run_id==state.run_id)).scalar_one() == ended
        assert c.execute(select(store.runs.c.cost_usd).where(store.runs.c.run_id==state.run_id)).scalar_one() == .000032


@pytest.mark.parametrize('status', ['RUNNING','WAITING_HUMAN','INTERRUPTED'])
def test_requires_complete_not_just_an_idle_call_queue(newrun, status):
    state, _ = completed(newrun)
    state.status = status
    store.save_state(state)
    plan = costs.plan(state.run_id,state.user_id)
    with pytest.raises(Conflict,match='completed project'):
        costs.apply(plan,state.user_id)
    assert ledger.budget(state.run_id)['spent_microusd'] == 108


def test_changed_task_set_rejects_stale_plan(newrun):
    state, _ = completed(newrun)
    plan = costs.plan(state.run_id,state.user_id)
    ledger.acquire(state.run_id,state.scratch['execution_epoch'],{'node':'new','request':{'user':'new'}},100)
    with pytest.raises(Conflict,match='Unsettled'):
        costs.apply(plan,state.user_id)


def test_resume_lock_prevents_a_stale_state_writer_from_losing_the_correction(newrun):
    state, _ = completed(newrun)
    plan = costs.plan(state.run_id,state.user_id)
    entered, release = threading.Event(), threading.Event()
    def resume():
        with store.run_lock(state.run_id):
            entered.set()
            assert release.wait(5)
    worker = threading.Thread(target=resume)
    worker.start()
    try:
        assert entered.wait(5)
        with pytest.raises(RuntimeError,match='busy'):
            costs.apply(plan,state.user_id)
        assert ledger.budget(state.run_id)['spent_microusd'] == 108
    finally:
        release.set()
        worker.join(5)
    costs.apply(plan,state.user_id)
    assert ledger.budget(state.run_id)['spent_microusd'] == 32


def test_missing_usage_retains_original_charge_and_reports_exclusion(newrun):
    state, tasks = completed(newrun)
    with ledger.transaction() as c:
        receipt = json.loads(c.execute(select(ledger.tasks.c.result).where(
            ledger.tasks.c.task_id==tasks[0]['task_id'])).scalar_one())
        receipt['meta']['requests'][0]['usage'] = {'total_tokens':120}
        c.execute(update(ledger.tasks).where(ledger.tasks.c.task_id==tasks[0]['task_id']).values(result=json.dumps(receipt)))
    plan = costs.plan(state.run_id,state.user_id)
    assert plan['after_microusd'] == 70
    assert plan['excluded'] == {'invalid_usage':1}
    costs.apply(plan,state.user_id)
    assert ledger.budget(state.run_id)['spent_microusd'] == 70


def test_ambiguous_stage_is_explicit_and_no_unknown_charge_is_repriced():
    steps=[dict(node='a',stage='S3_ANALYZE',started_at='2026-01-01T00:00:00',ended_at='2026-01-01T00:02:00'),
           dict(node='b',stage='S4_DEFINE',started_at='2026-01-01T00:00:00',ended_at='2026-01-01T00:02:00')]
    assert costs._stage('independent_verifier','2026-01-01T00:01:00+00:00',steps) == ('UNATTRIBUTED','no_unique_recorded_stage')
    assert costs.effective(None,'t',{'t':0}) is None
