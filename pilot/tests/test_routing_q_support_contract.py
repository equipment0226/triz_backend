import pytest
import copy
from triz.ax import routing_q as q
from test_ax_refactor import newrun


def fixture_q(monkeypatch):
    tickets = [dict(action_type=name, parameters={}, model_role='CODE') for name in ('A', 'B', 'C')]
    features = dict(schema=q.SCHEMA, mode='FULL', domain='PHYSICAL', phase='next')
    monkeypatch.setattr(q, 'phi', lambda f, a: {ord(a['action_type']) - ord('A'): 1.0})
    policy = dict(feature_schema=q.SCHEMA, weights=[.1, .2, 10.] + [0.] * 509, discount=.8,
                  support={q.support_key(a): 4 for a in tickets},
                  state_support={q.support_region(features, a): 4 for a in tickets[:2]})
    if hasattr(q, 'contracts'):
        policy.update(q.contracts())
    row = dict(features=features, actions=tickets, permitted=[0, 1, 2], executed_index=0,
               reward=0., terminal=False, next_features=features, next_actions=tickets,
               next_permitted=[0, 1, 2], next_rule_preferred=0)
    return policy, features, tickets, row


def test_q01_nonterminal_regional_support_matches_online(monkeypatch):
    policy, features, tickets, row = fixture_q(monkeypatch)
    assert q.choose(policy, features, tickets, [0, 1, 2], 0)[0] == 1
    assert q.evaluate(policy, [row])['bellman_mse'] == pytest.approx((.1 - .16) ** 2)
    policy['weights'][2] = 1000
    assert q.evaluate(policy, [row])['bellman_mse'] == pytest.approx((.1 - .16) ** 2)


def backup(policy, row):
    return q.next_state_backup(support_model=policy, value_model=policy, transition=row)


@pytest.mark.parametrize('field,value', [('mode', 'LITE'), ('domain', 'OTHER'), ('phase', 'repair')])
def test_q02_uses_next_state_region(monkeypatch, field, value):
    policy, features, tickets, row = fixture_q(monkeypatch)
    row['features'] = dict(features, **{field: value})
    assert backup(policy, row)['value'] == .2
    row['next_features'] = row['features']
    assert backup(policy, row)['value'] is None


def test_q03_independent_support_reasons(monkeypatch):
    policy, features, tickets, row = fixture_q(monkeypatch)
    policy['support'][q.support_key(tickets[0])] = 0
    result = q.supported_action_indices(policy, features, tickets, [0, 1, 2])
    assert result['rejected'] == {0: 'action_support_missing', 2: 'state_support_missing'}
    assert result['supported'] == [1]


@pytest.mark.parametrize('mode', ['LITE', 'FULL', 'DEEP'])
def test_q04_mode_forbidden_even_with_support(monkeypatch, mode):
    policy, features, tickets, row = fixture_q(monkeypatch)
    features['mode'] = mode
    tickets[2]['parameters']['tracks'] = ['D_ARIZ']
    policy['support'] = {q.support_key(a): 100 for a in tickets}
    policy['state_support'] = {q.support_region(features, a): 100 for a in tickets}
    result = backup(policy, row)
    assert 2 not in result['mask']
    assert q.choose(policy, features, tickets, [0, 1, 2], 0)[0] != 2
    if mode == 'DEEP':
        assert result['value'] is None


def test_q05_train_evaluate_share_support_backup(monkeypatch):
    policy, features, tickets, row = fixture_q(monkeypatch)
    rows = [dict(row, executed_index=i, terminal=True, reward=float(i)) for i in (0, 1) for _ in range(4)]
    rows.append(row)
    calls = []
    original = q.next_state_backup
    def capture(**kwargs):
        result = original(**kwargs)
        if not kwargs['transition']['terminal']:
            calls.append(result['mask'])
        return result
    monkeypatch.setattr(q, 'next_state_backup', capture)
    trained = q.train(rows, epochs=2)
    q.evaluate(trained, [row])
    assert calls and all(mask == [0, 1] for mask in calls)
    assert set(q.choose(trained, features, tickets, [0, 1, 2], 0)[1]) == {0, 1}


def test_q06_q07_unsupported_rule_is_not_single_supported_backup(monkeypatch):
    policy, features, tickets, row = fixture_q(monkeypatch)
    policy['state_support'].pop(q.support_region(features, tickets[0]))
    assert q.choose(policy, features, tickets, [0, 1, 2], 0)[0] == 0
    result = backup(policy, row)
    assert result['status'] == 'SKIP_UNSUPPORTED_FALLBACK' and result['value'] is None
    assert row['terminal'] is False
    evaluation = q.evaluate(policy, [row])
    assert evaluation['td_used'] == 0 and evaluation['bellman_mse'] is None
    assert evaluation['zero_prediction_same_target_mse'] is None


def test_q08_supported_rule_and_forced(monkeypatch):
    policy, features, tickets, row = fixture_q(monkeypatch)
    policy['state_support'].pop(q.support_region(features, tickets[0]))
    row['next_rule_preferred'] = 1
    assert backup(policy, row)['status'] == 'SUPPORTED_RULE'
    assert backup(policy, row)['value'] == .2
    row['next_permitted'] = [1]
    row.pop('next_rule_preferred')
    assert backup(policy, row)['status'] == 'SUPPORTED_FORCED'


def test_q09_explicit_terminal_needs_no_next_data(monkeypatch):
    policy, _, _, row = fixture_q(monkeypatch)
    terminal = {k: v for k, v in row.items() if not k.startswith('next_')}
    terminal['terminal'] = True
    terminal['reward'] = 1
    assert backup(policy, terminal)['value'] == 0
    assert q.evaluate(policy, [terminal])['bellman_mse'] == pytest.approx(.81)
    terminal['terminal'] = False
    assert backup(policy, terminal)['status'] == 'SKIP_INVALID_TRANSITION'


@pytest.mark.parametrize('mask', [[0, 0], [-1], [3], [True], []])
def test_q11_bad_masks(monkeypatch, mask):
    policy, _, _, row = fixture_q(monkeypatch)
    row['next_permitted'] = mask
    assert backup(policy, row)['status'] == 'SKIP_INVALID_TRANSITION'


@pytest.mark.parametrize('mutation', ['count', 'schema', 'contract', 'score'])
def test_q11_nonfinite_and_incompatible(monkeypatch, mutation):
    policy, features, tickets, row = fixture_q(monkeypatch)
    if mutation == 'count': policy['support'][q.support_key(tickets[0])] = float('nan')
    if mutation == 'schema': features.pop('schema')
    if mutation == 'contract': policy['backup_contract'] = 'old'
    if mutation == 'score': policy['weights'][0] = float('nan')
    assert backup(policy, row)['value'] is None
    assert q.choose(policy, features, tickets, [0, 1, 2], 0)[2]


def test_q12_holdout_cannot_build_support_or_cross_episode(monkeypatch):
    policy, _, _, row = fixture_q(monkeypatch)
    with pytest.raises(ValueError, match='Holdout'):
        q.train([dict(row, split='holdout')])
    row.update(semantic_episode_id='one', next_semantic_episode_id='two')
    assert backup(policy, row)['reason'] == 'cross_episode'


def test_q13_cql_penalty_keeps_legal_unsupported_action(monkeypatch):
    _, _, _, row = fixture_q(monkeypatch)
    rows = [dict(row, terminal=True, reward=1) for _ in range(4)]
    model = q.train(rows, epochs=2)
    assert model['support'].get(q.support_key(row['actions'][2]), 0) == 0
    assert model['weights'][2] < 0  # CQL suppresses legal C even without a logged C.
    restricted = q.train([dict(r, permitted=[0, 1]) for r in rows], epochs=2)
    assert restricted['weights'][2] == 0


def test_q14_collecting_preserves_observation_support(monkeypatch):
    _, _, _, row = fixture_q(monkeypatch)
    rows = [dict(row, next_rule_preferred=1) for _ in range(4)]
    model = q.train(rows, epochs=2)
    assert model['training']['status'] == 'COLLECTING'
    assert not model['training']['parameters_changed']
    assert model['training']['td_used'] == 0
    assert model['support'][q.support_key(row['actions'][0])] == 4


def test_q15_old_checkpoint_readable_but_not_promotable(monkeypatch):
    from triz.ax import registry
    policy, features, tickets, _ = fixture_q(monkeypatch)
    old = {k: v for k, v in policy.items() if k not in q.contracts()}
    q.validate(old)  # Shape remains readable.
    assert not registry.compatible_model(old)
    assert registry.compatible_model(policy)
    assert q.choose_legacy(old, features, tickets, [0, 1, 2], 0)[0] == 1
    assert q.choose(old, features, tickets, [0, 1, 2], 0)[2]


def test_cloned_jobs_are_not_independent_but_different_targets_are(monkeypatch):
    policy, features, tickets, _ = fixture_q(monkeypatch)
    clone = copy.deepcopy(tickets[0]); clone['action_instance_id'] = 'new-audit-id'
    clone['parameters']['attempt'] = 2
    assert q.choose(policy, features, [tickets[0], clone], [0, 1], 0)[2] == 'insufficient_action_support'
    clone['parameters']['obligation_ids'] = ['different-target']
    assert q.choose(policy, features, [tickets[0], clone], [0, 1], 0)[2] is None


def test_q10_dataset_retains_full_next_indices_and_rule(newrun):
    from test_ax_refactor import action, review
    from triz import store
    from triz.context import RunContext
    from triz.schema import RawIdea, ConceptSpec
    from triz.ax import coordinator, effect_history
    from triz.ax.contracts import ActionTicket
    from triz.ax.action_runtime import executing
    state = newrun(user='mapping-owner')
    def proposal(track):
        return ActionTicket(**action(track), expected_outputs=['RawIdea'], allowed_tools=['legacy_tracks'], reason='fixture')
    tickets = [proposal(t) for t in ('A_MATRIX', 'H_EFFECTS')]
    chosen, did = coordinator.decide(state, tickets, 0, {'SOLVE_SUBPROBLEM'}, 'solve:fixture')
    with executing(RunContext(state), chosen, did):
        state.solve.raw_ideas = [RawIdea(id='raw1', track='A_MATRIX', idea='path', detail={'source_effect_id':'E1','conditions':['전도 경로 확보']})]
    state.concepts = [ConceptSpec(id='C1', working_principle='path', source_idea_ids=['raw1'])]
    app = effect_history.collect(state)[0]
    effect_history.user_reviews(state, [review(app)], {'C1':'accept'}, 'mapping-answer')
    _, next_did = coordinator.decide(state, [proposal(t) for t in ('A_MATRIX', 'D_ARIZ', 'H_EFFECTS')],
        2, {'SOLVE_SUBPROBLEM'}, 'solve:next')
    store.save_state(state)
    manifest = q.dataset(state.user_id, state.user_id)
    row = manifest['samples'][0]
    assert len(row['next_actions']) == 3 and row['next_permitted'] == [0, 2]
    assert row['next_rule_preferred'] == 2
    assert row['next_actions'][2]['parameters']['tracks'] == ['H_EFFECTS']
    assert row['next_action_instance_ids'][2] == row['next_actions'][2]['action_instance_id']
    assert not row['terminal'] and row['next_contracts'] == q.contracts()
    # The immutable next decision disappears at an earlier cutoff; it is not
    # replaced by today's state or by a fabricated terminal value.
    from triz.ax import ledger
    first = next(d for d in ledger.decision_history(state.run_id, state.user_id) if d['decision_id'] == did)
    early = q.dataset(state.user_id, state.user_id, cutoff=first['created_at'])
    assert not early['samples']  # The reward label was not yet available either.


def test_q15_registry_rejects_old_semantics_at_shadow_promotion_and_load(newrun, monkeypatch):
    from triz.ax import registry, ledger
    from triz.ax.contracts import Conflict
    from sqlalchemy import update
    policy, _, _, _ = fixture_q(monkeypatch)
    old = {k: v for k, v in policy.items() if k not in q.contracts()}
    state = newrun(user='old-checkpoint-owner')
    owner = state.user_id
    vid = registry.put('policy', owner, owner, dict(model=old, offline_eligible=True, review_ids=['isolated-review']))
    monkeypatch.setattr(registry, 'reviews_current', lambda *a, **kw: True)
    assert registry.get(vid, owner, owner)['payload']['model'] == old
    with pytest.raises(Conflict): registry.set_task_shadow(owner, owner, 'routing_q', q.SCHEMA, vid)
    with pytest.raises(Conflict): registry.promote_task(owner, owner, 'routing_q', q.SCHEMA, vid, 'operator', 'fixture')
    with ledger.transaction() as connection:
        connection.execute(update(registry.pointers).where(registry.pointers.c.scope == registry.scope(owner, owner)).values(
            policy_id=vid, shadow_policy_id=vid, canary_percent=100))
    loaded = registry.for_run(state, feature_schema=q.SCHEMA)
    assert not loaded.get('policy') and not loaded.get('shadow_policy')
    assert loaded['policy_fallback_reason'] == 'incompatible_support_backup_or_handler_contract'
