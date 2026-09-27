"""No paid calls: complete source coverage and resumable independent review."""
import copy
import json
from types import SimpleNamespace

import pytest

from triz import agent, idea_consolidation, quality, rag
from triz.context import AbortRun, RunContext
from triz.schema import ConceptSpec, RawIdea, TechnicalContradiction
from triz.settings import settings


def _concept(idea, tc):
    return {'title': idea['title'], 'source_idea_ids': [idea['id']],
            'addresses_contradictions': [tc.id], 'working_principle': 'change ' + idea['id'],
            'resolution_argument': 'both requirements remain conditional until measured',
            'validation_plan': [{'experiment': 'controlled test', 'failure_criterion': 'protected side worsens'}]}


def _pass(ctx, rubric, data, facts):
    return {'verdict': 'PASS', 'per_concept': [
        {'concept_id': c['concept_id'], 'verdict': 'PASS'} for c in data['concepts']]}


def _prepare(state, monkeypatch, count=15, ensure=False):
    tc = TechnicalContradiction()
    state.definition.technical_contradictions = [tc]
    state.solve.raw_ideas = [RawIdea(id=f'I{i}', title=f'idea {i}', idea=f'mechanism {i}',
        mechanism_key=f'm{i}', addresses=[tc.id], resolution_status='TRADEOFF' if i == 0 else 'UNSUPPORTED')
        for i in range(count)]
    monkeypatch.setattr(rag, 'prior_cases_block', lambda state: '')
    monkeypatch.setattr(agent, 'verify_artifact', _pass)
    if not ensure:
        monkeypatch.setattr(idea_consolidation, 'ensure_consolidated', lambda ctx: None)
    return tc


def test_46_sources_consolidate_to_10_and_all_10_are_reviewed(state, monkeypatch):
    tc = _prepare(state, monkeypatch, count=46, ensure=True)
    original_ids = {i.id for i in state.solve.raw_ideas}
    generated, audits, merges = [], [], []
    def respond(ctx, **kw):
        if kw['node'] == 's5_merge':
            rows = kw['vars']['all_ideas']
            merges.append(len(rows))
            groups = [rows[i:i+5] for i in range(0, 45, 5)] + [rows[45:]]
            return {'ideas': [{'keep_ids': [i['id'] for i in group],
                'merge_reason': 'same mechanism, intervention, conditions and protected requirement'}
                for group in groups]}
        rows = kw['vars']['ideas']
        generated.extend(rows)
        return {'concepts': [_concept(i, tc) for i in rows], 'excluded': []}
    def audit(ctx, rubric, data, facts):
        audits.extend(data['concepts'])
        return _pass(ctx, rubric, data, facts)
    monkeypatch.setattr(agent, 'run_agent', respond)
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    quality.generate_concepts(RunContext(state))
    assert merges == [46]
    assert len(state.solve.raw_ideas) == len(generated) == len(audits) == len(state.concepts) == 10
    assert all(len(c.source_idea_ids) == 1 for c in state.concepts)
    assert {c.source_idea_ids[0] for c in state.concepts} == {i.id for i in state.solve.raw_ideas}
    assert any(i['resolution_status'] == 'TRADEOFF' for i in generated)
    review = state.scratch['ax_candidate_review']
    assert review['review_limit'] is None
    assert review['available_ideas'] == review['assigned_ideas'] == review['completed_ideas'] == 10
    assert not review['unreviewed_idea_ids']
    assert {i for ids in review['source_lineage'].values() for i in ids} == original_ids
    assert len(review['audit_completed_concept_ids']) == 10
    assert not review['audit_unreviewed_concept_ids']
    # An S6 retry uses the completed partition without an extra consolidation call.
    quality.generate_concepts(RunContext(state))
    assert merges == [46]
    assert len(audits) == 10


@pytest.mark.parametrize('bad', ['missing', 'unknown', 'duplicate', 'excluded_no_ids', 'excluded_no_reason'])
def test_incomplete_disposition_stops_without_erasing_sources(state, monkeypatch, bad):
    tc = _prepare(state, monkeypatch, count=2)
    original = copy.deepcopy(state.solve.raw_ideas)
    def respond(ctx, **kw):
        rows = kw['vars']['ideas']
        data = {'concepts': [_concept(i, tc) for i in rows], 'excluded': []}
        if bad == 'missing':
            data['concepts'].pop()
        elif bad == 'unknown':
            data['concepts'][0]['source_idea_ids'] = ['invented']
        elif bad == 'duplicate':
            data['concepts'][1]['source_idea_ids'] = [rows[0]['id']]
        elif bad == 'excluded_no_ids':
            data['concepts'].pop()
            data['excluded'] = [{'idea': rows[1]['title'], 'reason': 'cannot work'}]
        else:
            data['concepts'].pop()
            data['excluded'] = [{'source_idea_ids': [rows[1]['id']], 'reason': ''}]
        return data
    monkeypatch.setattr(agent, 'run_agent', respond)
    with pytest.raises(AbortRun, match='판정이 완결'):
        quality.generate_concepts(RunContext(state))
    assert state.solve.raw_ideas == original
    assert state.scratch['ax_candidate_review']['completed_ideas'] == 0
    assert len(state.scratch['ax_candidate_review']['unreviewed_idea_ids']) == 2


def test_independent_concepts_and_individual_exclusion_complete_every_id(state, monkeypatch):
    tc = _prepare(state, monkeypatch, count=3)
    def respond(ctx, **kw):
        rows = kw['vars']['ideas']
        return {'concepts': [_concept(i, tc) for i in rows[:2]], 'excluded': [{'source_idea_ids': [rows[2]['id']],
            'reason': 'cannot preserve the second requirement under its stated conditions'}]}
    monkeypatch.setattr(agent, 'run_agent', respond)
    quality.generate_concepts(RunContext(state))
    assert len(state.concepts) == 2
    assert [c.source_idea_ids for c in state.concepts] == [['I0'], ['I1']]
    assert state.scratch['excluded_concepts'][0]['source_idea_ids'] == ['I2']
    assert state.scratch['ax_candidate_review']['completed_ideas'] == 3
    assert not state.scratch['ax_candidate_review']['unreviewed_idea_ids']


@pytest.mark.parametrize('combine', ['concepts', 'excluded'])
def test_recombining_independent_ideas_or_grouping_exclusions_is_rejected(state, monkeypatch, combine):
    tc = _prepare(state, monkeypatch, count=3)
    originals = copy.deepcopy(state.solve.raw_ideas)
    prior = ConceptSpec(id='PRIOR', title='previous completed candidate')
    state.concepts = [prior]
    def respond(ctx, **kw):
        rows = kw['vars']['ideas']
        if combine == 'concepts':
            concept = _concept(rows[0], tc)
            concept['source_idea_ids'].append(rows[1]['id'])
            return {'concepts': [concept], 'excluded': [
                {'source_idea_ids': [rows[2]['id']], 'reason': 'specific failure of the third idea'}]}
        return {'concepts': [_concept(rows[0], tc)], 'excluded': [
            {'source_idea_ids': [rows[1]['id'], rows[2]['id']], 'reason': 'shared generic rejection'}]}
    monkeypatch.setattr(agent, 'run_agent', respond)
    with pytest.raises(AbortRun, match='독립 아이디어 ID를 정확히 1개'):
        quality.generate_concepts(RunContext(state))
    assert state.solve.raw_ideas == originals
    assert state.concepts == [prior]
    assert state.scratch['ax_candidate_review']['completed_ideas'] == 0
    assert state.scratch['ax_candidate_review']['unreviewed_idea_ids'] == ['I0', 'I1', 'I2']


def test_same_model_local_id_in_every_batch_gets_distinct_stable_server_ids(state, monkeypatch):
    tc = _prepare(state, monkeypatch, count=6)
    returned_id = ['C1']
    calls = []
    def respond(ctx, **kw):
        rows = kw['vars']['ideas']
        calls.append(len(rows))
        return {'concepts': [dict(_concept(row, tc), id=returned_id[0]) for row in rows], 'excluded': []}
    monkeypatch.setattr(agent, 'run_agent', respond)
    ctx = RunContext(state)
    quality.generate_concepts(ctx)
    first_ids = [c.id for c in state.concepts]
    assert sorted(calls) == [1, 5]
    assert len(first_ids) == len(set(first_ids)) == 6
    assert all(cid.startswith('CPT-S6-') for cid in first_ids)
    assert [c.source_idea_ids for c in state.concepts] == [[f'I{i}'] for i in range(6)]
    # Arbitrary labels from the model cannot change candidate identities on retry.
    returned_id[0] = 'different-label-on-retry'
    quality.generate_concepts(ctx)
    assert [c.id for c in state.concepts] == first_ids
    assert state.scratch['ax_candidate_review']['completed_ideas'] == 6


def _audit_candidates(state, count):
    state.concepts = [ConceptSpec(id=f'C{i}', title=f'candidate {i}', working_principle=f'm{i}',
        resolution_argument='both requirements', addresses_contradictions=['T1'],
        validation_plan=[{'experiment': 'test'}]) for i in range(count)]


def test_audit_cache_uses_actual_pinned_model_and_run_verification_policy(state, monkeypatch):
    from triz import prompts_registry
    from triz.ax import WORKFLOW
    from triz.ax.runtime import MODEL_FIELDS
    from triz.execution_config import profile
    _audit_candidates(state, 2)
    state.scratch['workflow_version'] = WORKFLOW
    pinned_model = {key: getattr(settings.tiers['T3'], key) for key in MODEL_FIELDS}
    state.scratch['ax_bundle'] = bundle = {
        'models': {'T3': dict(pinned_model, model='pinned-auditor-v1')},
        'config': copy.deepcopy(settings.triz), 'rubrics': copy.deepcopy(settings.rubrics),
        'prompts': {'P_VERIFIER_GENERIC': prompts_registry.raw('P_VERIFIER_GENERIC')}}
    calls = []
    def audit(ctx, rubric, data, facts):
        calls.append([c['concept_id'] for c in data['concepts']])
        return _pass(ctx, rubric, data, facts)
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    token = profile.set(bundle)
    try:
        ctx = RunContext(state)
        quality.audit_concepts(ctx)
        assert len(calls) == 1
        monkeypatch.setattr(settings.tiers['T3'], 'model', 'unrelated-future-default')
        monkeypatch.setitem(settings.triz['verification'], 'max_tokens', 99999)
        quality.audit_concepts(ctx)
        assert len(calls) == 1
        assert state.steps[-1].status == 'SKIPPED'
        bundle['models']['T3']['model'] = 'pinned-auditor-v2'
        quality.audit_concepts(ctx)
        assert len(calls) == 2
        bundle['config']['verification']['max_tokens'] += 1
        quality.audit_concepts(ctx)
        assert len(calls) == 3
        assert all(c.quality_status == 'PASS' for c in state.concepts)
    finally:
        profile.reset(token)


def test_audit_reuses_complete_batches_after_interruption_and_state_roundtrip(state, monkeypatch):
    from triz.schema import GlobalState
    _audit_candidates(state, 12)
    calls, failed = [], False
    def audit(ctx, rubric, data, facts):
        nonlocal failed
        ids = [c['concept_id'] for c in data['concepts']]
        calls.append(ids)
        if ids[0] == 'C5' and not failed:
            failed = True
            raise AbortRun('interrupted')
        return _pass(ctx, rubric, data, facts)
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    with pytest.raises(AbortRun, match='interrupted'):
        quality.audit_concepts(RunContext(state))
    restored = GlobalState.model_validate_json(state.model_dump_json())
    quality.audit_concepts(RunContext(restored))
    assert calls == [[f'C{i}' for i in range(5)], [f'C{i}' for i in range(5, 10)],
                     [f'C{i}' for i in range(5, 10)], ['C10', 'C11']]
    assert len(restored.concepts) == 12
    assert all(c.quality_status == 'PASS' for c in restored.concepts)


def test_generation_resumes_with_completed_model_calls_from_persisted_cache(state, monkeypatch):
    from triz.schema import GlobalState
    tc = _prepare(state, monkeypatch, count=12)
    monkeypatch.setitem(settings.triz['run'], 'parallel_workers', 1)
    calls, failed = [], False
    def chat(ctx, **kw):
        nonlocal failed
        rows = json.loads(kw['user'].split('[배정 아이디어와 반박·조건] ', 1)[1].split('\n', 1)[0])
        first = rows[0]['id']
        calls.append(first)
        if first == 'I5' and not failed:
            failed = True
            raise AbortRun('interrupted')
        return SimpleNamespace(data={'concepts': [_concept(i, tc) for i in rows], 'excluded': []},
                               tokens_in=1, tokens_out=1, cost_usd=0, model='offline')
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    with pytest.raises(AbortRun, match='interrupted'):
        quality.generate_concepts(RunContext(state))
    restored = GlobalState.model_validate_json(state.model_dump_json())
    quality.generate_concepts(RunContext(restored))
    assert calls.count('I0') == calls.count('I10') == 1
    assert calls.count('I5') == 2
    assert len(restored.concepts) == 12
    assert restored.scratch['ax_candidate_review']['completed_ideas'] == 12
    assert not restored.scratch['ax_candidate_review']['unreviewed_idea_ids']


def test_missing_audit_rows_remain_unverified_with_explicit_reason(state, monkeypatch):
    _audit_candidates(state, 12)
    def audit(ctx, rubric, data, facts):
        output = _pass(ctx, rubric, data, facts)
        output['per_concept'].pop()
        return output
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    quality.audit_concepts(RunContext(state))
    missing = [c for c in state.concepts if c.quality_status == 'UNVERIFIED']
    assert [c.id for c in missing] == ['C4', 'C9', 'C11']
    assert all(any('후보별 판정' in issue for issue in c.quality_issues) for c in missing)
    assert state.scratch['s6_quality_batches'] == {}


def test_unlocated_audit_flaw_cannot_silently_reject_all_candidates(state, monkeypatch):
    _audit_candidates(state, 2)
    monkeypatch.setattr(agent, 'verify_artifact', lambda *args: {
        'verdict': 'REJECT', 'fatal_flaws': ['an unspecified candidate has a design flaw'], 'per_concept': []})
    quality.audit_concepts(RunContext(state))
    assert len(state.concepts) == 2
    assert all(c.quality_status == 'UNVERIFIED' for c in state.concepts)
    assert not state.scratch.get('excluded_concepts')
    assert not state.scratch['s6_quality_batches']


def test_long_audit_payloads_are_batched_without_truncation(state, monkeypatch):
    _audit_candidates(state, 7)
    for c in state.concepts:
        c.working_principle = c.id + ('long mechanism ' * 800)
    seen, sizes = [], []
    def audit(ctx, rubric, data, facts):
        seen.extend(data['concepts'])
        sizes.append(len(data['concepts']))
        return _pass(ctx, rubric, data, facts)
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    quality.audit_concepts(RunContext(state))
    assert sizes == [1] * 7
    assert [p['working_principle'] for p in seen] == [c.working_principle for c in state.concepts]
