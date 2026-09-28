"""Offline journal-backed regressions for feedback case revisions and replay."""
import copy
import json
import uuid

import pytest
from sqlalchemy import select

from test_ax_refactor import newrun
from test_unified_feedback_adaptive import adaptive_run, candidate, events
from triz import llm, nodes, rag, store
from triz.ax import feedback_events, gateway, ledger
from triz.context import AbortRun, RunContext


@pytest.fixture
def source(adaptive_run):
    state = adaptive_run(user='rag-revision-' + uuid.uuid4().hex)
    state.scratch.pop('synthetic')
    concept = candidate(state)
    concept.title = '전도 경로 개선'
    concept.one_liner = '전도 경로 개선'
    state.intake.frame.restated_problem = '전도 경로 개선'
    store.save_state(state)
    return state


def submit(state, rating=5, **fields):
    payload = dict(submission_id=uuid.uuid4().hex, training_consent='PROJECT_ONLY',
                   solution_feedback=[dict(concept_id='C1', rating=rating, **fields)])
    nodes.record_feedback(state, payload)
    store.save_state(state)
    return payload


def hits(state, collection=rag.COLLECTION, **options):
    return rag.retrieve('전도 경로 개선', collection=collection, user_id=state.user_id,
                        project_id=state.scratch.get('ax_project_id', state.user_id), require_common=True, **options)


def doc(state, collection):
    return next(d for d in store.rag_all(collection) if d['id'] ==
                ('fb-' if collection == rag.COLLECTION else 'fx-') + state.run_id + '-C1')


def test_rating_transitions_replace_counterpart_and_preserve_immutable_history(source):
    for rating, expected in ((5, rag.COLLECTION), (2, rag.FAILURES), (5, rag.COLLECTION), (3, None), (2, rag.FAILURES)):
        submit(source, rating)
        positive, negative = hits(source), hits(source, rag.FAILURES)
        assert bool(positive) == (expected == rag.COLLECTION)
        assert bool(negative) == (expected == rag.FAILURES)
        active = positive or negative
        if active:
            assert active[0]['meta']['rating'] == rating
            assert len(active[0]['meta']['common_evaluation_ids']) == 1
        if rating == 3:
            assert doc(source, rag.COLLECTION)['meta']['retrieval_active'] is False
            assert doc(source, rag.FAILURES)['meta']['retrieval_active'] is False
    assert len([e for e in events(source) if e['evaluation_stage'] == 's10_feedback']) == 5
    with store.engine.connect() as c:
        assert len(c.execute(select(store.feedback).where(store.feedback.c.run_id == source.run_id)).all()) == 5


def test_legacy_stale_positive_is_filtered_without_rewriting_its_stored_document(source):
    submit(source, 5)
    old = copy.deepcopy(doc(source, rag.COLLECTION))
    submit(source, 2)
    old['meta'].pop('retrieval_active')
    old['meta'].pop('case_contract')
    store.rag_upsert(old['id'], old['collection'], old['doc'], old['meta'], old['weight'])
    before = doc(source, rag.COLLECTION)
    assert hits(source) == []
    assert hits(source, rag.FAILURES)[0]['meta']['rating'] == 2
    assert doc(source, rag.COLLECTION) == before


def test_legacy_negative_identity_comes_from_events_not_title(source):
    submit(source, 2)
    old = copy.deepcopy(doc(source, rag.FAILURES))
    for name in ('run_id', 'concept_id', 'retrieval_active', 'case_contract'):
        old['meta'].pop(name)
    store.rag_upsert(old['id'], old['collection'], old['doc'], old['meta'], old['weight'])
    assert hits(source, rag.FAILURES)
    submit(source, 5)
    store.rag_upsert(old['id'], old['collection'], old['doc'], old['meta'], old['weight'])
    assert hits(source, rag.FAILURES) == []


def test_old_or_repeated_writer_cannot_resurrect_prior_rating(source):
    old_payload = submit(source, 5)
    stale_state = source.model_copy(deep=True)
    submit(source, 2)
    assert rag.write_feedback(stale_state, {'accepted_patterns':['OLD PATTERN']}) == 0
    assert nodes.record_feedback(source, old_payload) == 0
    assert hits(source) == []
    assert hits(source, rag.FAILURES)[0]['meta']['rating'] == 2


def test_adoption_change_updates_weight_and_missing_rating_clears_positive(source):
    submit(source, 5, adopted=True)
    original_weight = doc(source, rag.COLLECTION)['weight']
    submit(source, 5, adopted=False)
    assert doc(source, rag.COLLECTION)['weight'] < original_weight
    assert hits(source)[0]['meta']['adopted'] is False
    nodes.record_feedback(source, dict(submission_id=uuid.uuid4().hex,
        solution_feedback=[dict(concept_id='C1', adopted=False, adopted_explicit=True)]))
    store.save_state(source)
    assert hits(source) == []
    assert hits(source, rag.FAILURES) == []


@pytest.mark.parametrize('withdrawal', ['new_feedback', 'revision', 'persisted_state', 'empty_submission'])
def test_withdrawal_cannot_fall_back_to_old_positive(source, withdrawal):
    submit(source, 5)
    positive = doc(source, rag.COLLECTION)
    if withdrawal == 'new_feedback':
        nodes.record_feedback(source, dict(submission_id=uuid.uuid4().hex, training_consent='NO_TRAINING',
            solution_feedback=[dict(concept_id='C1', rating=2)]))
    elif withdrawal == 'revision':
        feedback_events.revise(source.run_id, source.user_id, positive['meta']['source_evaluation_id'],
            consent_scope='NO_TRAINING', reason='Withdraw permission')
    elif withdrawal == 'persisted_state':
        source.scratch['training_consent'] = 'NO_TRAINING'
        store.save_state(source)
    else:
        feedback_events.final_feedback(source, dict(submission_id=uuid.uuid4().hex,
            training_consent='NO_TRAINING', solution_feedback=[]))
    # For event-based withdrawals the state may not have been persisted yet.
    assert hits(source) == []
    source.scratch['prior_case_ids'] = [positive['id']]
    assert not rag.case_permissions_current(source)


def test_current_event_reference_with_mismatched_rating_is_rejected(source):
    submit(source, 2)
    latest = doc(source, rag.FAILURES)
    forged = dict(latest['meta'], rating=5)
    store.rag_upsert('fb-' + source.run_id + '-C1', rag.COLLECTION, latest['doc'], forged, 1.10)
    assert hits(source) == []


def test_cases_are_scoped_by_owner_project_and_exact_candidate_identity(source):
    submit(source, 5)
    candidate(source, 'C2').title = source.concepts[0].title
    nodes.record_feedback(source, dict(submission_id=uuid.uuid4().hex,
        solution_feedback=[dict(concept_id='C2', rating=2)]))
    assert hits(source)[0]['meta']['concept_id'] == 'C1'
    assert rag.retrieve('전도 경로 개선', user_id='another-owner', require_common=True) == []
    assert rag.retrieve('전도 경로 개선', user_id=source.user_id,
                        project_id='another-project', require_common=True) == []


def test_cached_paid_reply_survives_rating_edit_but_new_request_is_blocked(source, adaptive_run, monkeypatch):
    submit(source, 5)
    target = adaptive_run(user=source.user_id)
    target.scratch.pop('synthetic')
    selected = hits(source)
    target.scratch['prior_case_ids'] = [h['id'] for h in selected]
    rag._remember_sources(target, selected)
    calls = []
    monkeypatch.setattr(llm, 'chat_json', lambda **kw:(calls.append(kw) or llm.LLMResult(data={'ok':True}, cost_usd=.00001)))
    reference = selected[0]['id']
    block = '[참고: 과거 유사 문제에서 사용자가 높게 평가한 접근]\n- [' + reference + '] 전도 경로 개선'
    historical = 'historical input\n' + block
    fresh_request = 'new request\n' + block
    original = gateway.chat(RunContext(target), system='s', user=historical, tier='T1')
    assert original.data == {'ok':True}
    submit(source, 2)
    assert rag.case_permissions_current(target)  # Rating edit is not a consent withdrawal.
    assert not rag.case_sources_current(target)
    replay = gateway.chat(RunContext(target), system='s', user=historical, tier='T1')
    assert replay.data == {'ok':True} and replay.meta['durable_replay']
    before = ledger.budget(target.run_id)
    with pytest.raises(AbortRun, match='최신 피드백'):
        gateway.chat(RunContext(target), system='s', user=fresh_request, tier='T1')
    after = ledger.budget(target.run_id)
    assert len(calls) == 1
    assert after['spent_microusd'] == before['spent_microusd']
    assert after['reserved_microusd'] == before['reserved_microusd']
    with store.engine.connect() as c:
        tasks = c.execute(select(ledger.tasks).where(ledger.tasks.c.run_id == target.run_id)).mappings().all()
    assert len(tasks) == 1  # A preflight rejection never occupies a paid-call key.
    with store.engine.connect() as c:
        blocked = c.execute(select(ledger.events.c.payload).where(ledger.events.c.run_id == target.run_id,
            ledger.events.c.event_type == 'ACTION_PREFLIGHT_BLOCKED')).scalars().all()
    assert len(blocked) == 1
    assert json.loads(blocked[0])['provider_called'] is False
    assert json.loads(blocked[0])['reserved_microusd'] == 0
    # An earlier S1 case must not trap unrelated S7/S8/S9 requests.
    downstream = json.dumps({'candidate':{'prior_case_ids':[reference], 'mechanism':'stored candidate'}})
    assert gateway.chat(RunContext(target), system='s', user=downstream, tier='T1').data['ok']
    submit(source, 5)
    rag._remember_sources(target, hits(source))
    assert gateway.chat(RunContext(target), system='s', user=fresh_request, tier='T1').data['ok']
    assert len(calls) == 3  # Exactly one original, unrelated, and refreshed call.


def test_legacy_cases_without_common_events_follow_latest_raw_feedback(state):
    concept = candidate(state)
    state.intake.frame.restated_problem = '전도 경로 개선'
    nodes.record_feedback(state, dict(solution_feedback=[dict(concept_id=concept.id, rating=5)]))
    old = copy.deepcopy(doc(state, rag.COLLECTION))
    assert 'common_evaluation_ids' not in old['meta']
    nodes.record_feedback(state, dict(solution_feedback=[dict(concept_id=concept.id, rating=2)]))
    old['meta'].pop('retrieval_active')
    store.rag_upsert(old['id'], old['collection'], old['doc'], old['meta'], old['weight'])
    assert old['id'] not in {r['id'] for r in rag.retrieve('전도 경로 개선', user_id=state.user_id)}
    assert any(r['id'] == 'fx-' + state.run_id + '-C1' for r in rag.retrieve('전도 경로 개선',
        user_id=state.user_id, collection=rag.FAILURES))


def test_lessons_preserve_legacy_text_and_pin_ids_only_for_new_contract(source):
    submit(source, 2, comment='전도 경로 개선')
    source.raw_query = '전도 경로 개선'
    source.scratch['ax_bundle'].pop('rag_case_contract', None)
    old_block = rag.lessons_block(source)
    assert '과거 사용자 피드백' in old_block
    assert 'fx-' + source.run_id not in old_block
    source.scratch['ax_bundle']['rag_case_contract'] = rag.FEEDBACK_CASE_CONTRACT
    assert '[fx-' + source.run_id + '-C1]' in rag.lessons_block(source)


def test_failed_projection_rolls_back_counterpart_deactivation(source, monkeypatch):
    submit(source, 5)
    payload = dict(submission_id=uuid.uuid4().hex, solution_feedback=[dict(concept_id='C1', rating=2)])
    with monkeypatch.context() as patch:
        patch.setattr(store, '_upsert', lambda *a, **kw:(_ for _ in ()).throw(RuntimeError('storage failure')))
        with pytest.raises(RuntimeError, match='storage failure'):
            nodes.record_feedback(source, payload)
    assert doc(source, rag.COLLECTION)['meta']['retrieval_active'] is True
    assert hits(source) == []  # Journal revision already makes the old rating ineligible.
    assert rag.write_feedback(source, source.feedback.distilled) == 1
    assert doc(source, rag.COLLECTION)['meta']['retrieval_active'] is False
    assert hits(source, rag.FAILURES)
