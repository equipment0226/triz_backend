"""A saved paid S6 response can recover its lineage without another call."""
import copy
import json

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from triz import llm, quality, rag, store
from triz.ax import ledger
from triz.context import AbortRun, RunContext
from triz.schema import RawIdea
from triz.settings import settings


def test_completed_s6_call_replays_across_resume_and_retains_objection(newrun, monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 0)
    monkeypatch.setattr(rag, 'prior_cases_block', lambda state: '')
    state = newrun()
    # This is a persisted pre-contract run, as in the BCI production replay.
    state.scratch['ax_bundle'].pop('concept_effect_contract', None)
    representative = RawIdea(id='R', title='Representative', idea='Fixture mechanism',
        source_idea_ids=['R', 'L'], mechanism_key='fixture-mechanism')
    state.solve.raw_ideas = [representative]
    original = {
        'concepts': [{'title': 'Representative solution', 'source_idea_ids': ['R'],
            'open_risks': ['Existing risk'], 'quality_status': 'PASS'}],
        'excluded': [{'source_idea_ids': ['L'], 'idea': 'Merged source',
            'reason': 'The environmental force has not been measured.'}],
    }
    requests = []

    def provider(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        return llm.LLMResult(data=copy.deepcopy(original), text=json.dumps(original),
            cost_usd=.000123, model='offline-fixture', tokens_in=10, tokens_out=20)

    monkeypatch.setattr(llm, 'chat_json', provider)
    audits = []

    def independent_review(ctx):
        candidate = ctx.state.concepts[0]
        # The generator's claimed PASS cannot skip the independent audit.
        assert candidate.quality_status == 'UNVERIFIED'
        assert candidate.source_idea_ids == ['R']
        assert original['excluded'][0]['reason'] in candidate.open_risks[-1]
        audits.append(candidate.model_dump(mode='json'))

    monkeypatch.setattr(quality, 'audit_concepts', independent_review)
    # Characterize the old failure while retaining the actual durable gateway.
    # The sole provider here is an offline fixture; the DB is the test fixture DB.
    with monkeypatch.context() as old:
        old.setattr(quality, 'normalize_concept_lineage', lambda data, *args: data)
        with pytest.raises(AbortRun):
            quality._generate_concepts(RunContext(state), ideas_override=[representative])
    failed = state.steps[-1]
    assert failed.status == 'FAILED' and failed.output_json == original
    assert audits == [] and len(requests) == 1
    with store.engine.connect() as connection:
        before = dict(connection.execute(select(ledger.tasks)
            .where(ledger.tasks.c.run_id == state.run_id)).mappings().one())
    assert before['status'] == 'COMPLETED'
    assert json.loads(before['result'])['data'] == original
    cost_before = ledger.budget(state.run_id)['spent_microusd']
    request_count_before = state.cost.request_count

    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline fixture resume')
    monkeypatch.setattr(llm, 'chat_json', lambda **kwargs: pytest.fail('Paid call on saved S6 replay'))
    quality._generate_concepts(RunContext(state), ideas_override=[representative])
    replay = state.steps[-1]
    assert replay.status == 'OK'
    assert replay.input_slice['user'] == failed.input_slice['user'] == requests[0]['user']
    assert replay.input_slice['system'] == failed.input_slice['system'] == requests[0]['system']
    assert replay.input_slice['vars'] == failed.input_slice['vars']
    assert quality.check_concept_batch(replay.output_json, {'R'}) == []
    assert replay.output_json['excluded'] == []
    assert replay.output_json['source_lineage_reviews'] == [{
        'representative_id': 'R', 'source_idea_id': 'L',
        'original_exclusion': original['excluded'][0],
    }]
    candidate = state.concepts[0]
    assert candidate.quality_status == 'UNVERIFIED' and len(audits) == 1
    assert state.scratch['s6_lineage_reviews'][candidate.id] == replay.output_json['source_lineage_reviews']
    assert state.scratch['ax_candidate_review']['completed_idea_ids'] == ['R']
    assert state.scratch['ax_candidate_review']['unreviewed_idea_ids'] == []
    assert state.scratch['excluded_concepts'] == []
    assert state.cost.request_count == request_count_before
    assert ledger.budget(state.run_id)['spent_microusd'] == cost_before
    with store.engine.connect() as connection:
        after = dict(connection.execute(select(ledger.tasks)
            .where(ledger.tasks.c.run_id == state.run_id)).mappings().one())
    assert after['task_id'] == before['task_id']
    assert after['actual'] == before['actual']
    assert json.loads(after['result'])['data'] == original

    # Successful agent-cache replay passes through the same normalizer again.
    quality._generate_concepts(RunContext(state), ideas_override=[representative])
    assert state.steps[-1].status == 'SKIPPED'
    assert state.concepts[0].open_risks == candidate.open_risks
    assert len(state.concepts[0].open_risks) == 2
    assert state.steps[-1].output_json['source_lineage_reviews'] == replay.output_json['source_lineage_reviews']
    assert len(audits) == 2 and len(requests) == 1
    assert ledger.budget(state.run_id)['spent_microusd'] == cost_before


def test_saved_failed_output_normalization_is_repeatable_and_non_mutating():
    representative = RawIdea(id='R', source_idea_ids=['R', 'L'])
    failed_output = {'concepts': [{'title': 'Saved concept', 'source_idea_ids': ['R']}],
        'excluded': [{'source_idea_ids': ['L'], 'reason': 'Source-specific concern'}]}
    snapshot = copy.deepcopy(failed_output)
    restored = quality.normalize_concept_lineage(failed_output, [representative])
    assert failed_output == snapshot
    assert quality.check_concept_batch(failed_output, {'R'})
    assert quality.check_concept_batch(restored, {'R'}) == []
    assert quality.normalize_concept_lineage(restored, [representative]) == restored
    assert restored['source_lineage_reviews'][0]['original_exclusion'] == snapshot['excluded'][0]
