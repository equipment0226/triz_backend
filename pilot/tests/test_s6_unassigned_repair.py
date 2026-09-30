"""A rejected merged-leaf concept gets a distinct repair, never silent credit."""
import copy
import json
import re

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from triz import llm, quality, rag, store
from triz.ax import concept_effects, ledger
from triz.context import ConceptReviewIncomplete, RunContext
from triz.schema import RawIdea
from triz.settings import settings


@pytest.mark.parametrize('kind', ['concepts', 'excluded'])
def test_unassigned_row_reports_exact_identity_and_allowed_representatives(kind):
    response = {'concepts': [{'title': 'First', 'source_idea_ids': ['R1']},
                             {'title': 'Second', 'source_idea_ids': ['R2']}], 'excluded': []}
    row = {'title': 'Merged source', 'source_idea_ids': ['LEAF'],
           'active_effect_ids': ['OTHER_EFFECT'], 'reason': 'Unconfirmed source condition'}
    index = len(response[kind])
    response[kind].append(row)
    original = copy.deepcopy(response)
    issues = quality.check_concept_batch(response, {'R2', 'R1'})
    assert len(issues) == 1
    assert all(token in issues[0] for token in (
        'FATAL-S6-COVERAGE:', f'{kind}[{index}].source_idea_ids', 'LEAF',
        '허용 대표 ID: ["R1", "R2"]', '통합 전 원안 ID', '과학효과'))
    assert response == original


def journals(state):
    with store.engine.connect() as conn:
        return {table.name: {row[key]: dict(row) for row in conn.execute(select(table)
            .where(table.c.run_id == state.run_id)).mappings()}
            for table, key in ((ledger.tasks, 'task_id'), (ledger.attempts, 'attempt_id'))}


def test_saved_failure_uses_one_new_repair_and_reuses_successful_batch(newrun, monkeypatch):
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'ax-run-v3')
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 1)
    monkeypatch.setitem(settings.triz['run'], 'parallel_workers', 1)
    monkeypatch.setattr(rag, 'prior_cases_block', lambda _: '')
    state = newrun()
    assert concept_effects.enabled(state)
    ideas = [RawIdea(id=f'R{i}', title=f'Representative {i}', idea=f'Mechanism {i}',
                     source_idea_ids=[f'R{i}'], detail={'source_effect_id': 'E1'}) for i in range(7)]
    ideas[-1].source_idea_ids = ['R6', 'LEAF']
    ideas[-1].detail = {'source_details': [
        {'source_idea_id': 'R6', 'source_effect_id': 'E1'},
        {'source_idea_id': 'LEAF', 'source_effect_id': 'E2'}]}
    state.solve.raw_ideas = ideas
    calls, audits = [], []

    def provider(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        ids = sorted(set(re.findall(r'"id":\s*"(R\d+)"', kwargs['user'])))
        assert ids in ([f'R{i}' for i in range(5)], ['R5', 'R6'])
        response = {'concepts': [{'title': f'Candidate {ident}', 'source_idea_ids': [ident],
                                 'active_effect_ids': ['E1']} for ident in ids], 'excluded': []}
        if ids == ['R5', 'R6']:
            instructions = kwargs['user'].replace('\\"', '"')
            corrected_instruction = ('concepts[2].source_idea_ids' in instructions and
                                     '허용 대표 ID: ["R5", "R6"]' in instructions)
            if not corrected_instruction:
                response['concepts'].append({'title': 'Unassigned merged source',
                    'source_idea_ids': ['LEAF'], 'active_effect_ids': ['E2']})
        return llm.LLMResult(data=response, text=json.dumps(response), model='offline-fixture',
                             cost_usd=.000123, tokens_in=10, tokens_out=20)

    def independent_review(ctx):
        assert all(c.quality_status == 'UNVERIFIED' for c in ctx.state.concepts)
        audits.append([c.model_dump(mode='json') for c in ctx.state.concepts])

    monkeypatch.setattr(llm, 'chat_json', provider)
    monkeypatch.setattr(quality, 'audit_concepts', independent_review)
    checker = quality.check_concept_batch

    def legacy_checker(data, assigned_ids):
        return ['FATAL-S6-COVERAGE: 배정되지 않은 아이디어 ID를 사용했습니다.'
                if '미배정 ID:' in issue else issue for issue in checker(data, assigned_ids)]

    # Save the former failure with the real gateway and an offline provider.
    # Its completed HTTP/JSON receipt remains valid evidence of the paid call.
    with monkeypatch.context() as old:
        old.setattr(quality, 'check_concept_batch', legacy_checker)
        with pytest.raises(ConceptReviewIncomplete):
            quality._generate_concepts(RunContext(state), ideas_override=ideas)
    assert len(calls) == 3 and audits == []
    successful, failed = [step for step in state.steps if step.node == 's6_concept'][-2:]
    assert successful.status == 'OK' and failed.status == 'FAILED'
    original_failure = copy.deepcopy(failed.model_dump(mode='json'))
    original_journals = journals(state)
    assert len(original_journals[ledger.tasks.name]) == 3
    assert all(row['status'] == 'COMPLETED' for row in original_journals[ledger.tasks.name].values())
    spent_before = ledger.budget(state.run_id)['spent_microusd']
    requests_before = state.cost.request_count

    state.scratch['execution_epoch'] += 1
    ledger.advance_epoch(state, 'offline fixture resume after precise identity repair')
    quality._generate_concepts(RunContext(state), ideas_override=ideas)
    reused, repaired = [step for step in state.steps if step.node == 's6_concept'][-2:]
    assert reused.status == 'SKIPPED' and repaired.status == 'OK'
    assert len(calls) == 4  # Only the more specific repair calls the provider.
    assert repaired.input_slice['user'] == failed.input_slice['user']
    assert calls[3]['user'] != calls[2]['user']
    assert calls[3]['user'].startswith(failed.input_slice['user'])
    assert repaired.input_slice['replay_source']['new_provider_calls'] == 0
    assert state.cost.request_count == requests_before + 1
    assert ledger.budget(state.run_id)['spent_microusd'] == spent_before + 123
    assert len(audits) == 1 and len(state.concepts) == 7
    assert {tuple(c.source_idea_ids) for c in state.concepts} == {(f'R{i}',) for i in range(7)}
    assert all(c.active_effect_ids == ['E1'] for c in state.concepts)
    assert failed.model_dump(mode='json') == original_failure
    after = journals(state)
    for table, records in original_journals.items():
        assert all(after[table][key] == value for key, value in records.items())
    assert len(after[ledger.tasks.name]) == 4
    original_receipts = [json.loads(row['result'])['data']
                         for row in original_journals[ledger.tasks.name].values()]
    assert sum(any(c['active_effect_ids'] == ['E2'] for c in data['concepts'])
               for data in original_receipts) == 2

    # Once accepted, both batches reuse their saved output without paying again.
    repaired_concepts = copy.deepcopy(state.concepts)
    spent_after = ledger.budget(state.run_id)['spent_microusd']
    monkeypatch.setattr(llm, 'chat_json', lambda **_: pytest.fail('Provider called for accepted S6 batch'))
    quality._generate_concepts(RunContext(state), ideas_override=ideas)
    assert [step.status for step in state.steps if step.node == 's6_concept'][-2:] == ['SKIPPED', 'SKIPPED']
    assert state.concepts == repaired_concepts and len(audits) == 2
    assert ledger.budget(state.run_id)['spent_microusd'] == spent_after
    assert journals(state) == after
