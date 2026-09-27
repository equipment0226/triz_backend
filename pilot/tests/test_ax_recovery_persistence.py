"""Interrupted isolated audits must checkpoint the owning portfolio, not one branch."""
import copy

import pytest

from test_ax_phase1 import dlc, candidate
from test_ax_coherence_recovery import proposal
from triz import agent, store
from triz.ax import coherence, coherence_recovery, coordinator, ledger, recovery
from triz.context import AbortRun, RunContext


@pytest.mark.parametrize('path', ['coherence', 'legacy', 'codesign'])
def test_recovery_audit_failure_keeps_saved_portfolio_progress_and_cache(dlc, monkeypatch, path):
    candidate(dlc)
    first = dlc.concepts[0]
    first.quality_status = 'REVISE'
    first.quality_issues = ['기구 보완 필요']
    second = first.model_copy(deep=True, update={'id': 'DLC-2', 'title': '별도 기준 후보', 'quality_status': 'PASS'})
    dlc.concepts.append(second)
    baseline = [item.model_dump(mode='json') for item in dlc.concepts]
    progress = {'contract': 'idea-retention-v2', 'completed_ideas': 2,
        'audit_completed_concept_ids': [first.id, second.id], 'audit_unreviewed_concept_ids': []}
    dlc.scratch['ax_candidate_review'] = copy.deepcopy(progress)
    dlc.scratch['ax_recovery'] = []
    store.save_state(dlc)

    raw = proposal(dlc)
    if path != 'coherence':
        raw = {key: value for key, value in raw.items() if key in recovery.Proposal.model_fields}
        monkeypatch.setattr(coherence, 'enabled', lambda state: False)
    else:
        monkeypatch.setattr(coherence_recovery, 'targets', lambda state, phase: [{
            'candidate_id': first.id, 'baseline': first, 'obligation_ids': ['TC-DLC'],
            'gaps': [{'kind': 'QUALITY_REVIEW', 'description': '기구 보완'}], 'action': 'REPAIR_CANDIDATE'}])
    monkeypatch.setattr(ledger, 'budget', lambda run_id: {'remaining_microusd': 10000000})
    monkeypatch.setattr(coordinator, 'decide', lambda state, tickets, *args: (tickets[0], 'test-recovery-decision'))
    monkeypatch.setattr(agent, 'run_agent', lambda *args, **kwargs: raw)

    def interrupted_auditor(ctx, *args):
        assert len(ctx.state.concepts) == 1
        assert ctx.state is not dlc
        # Represent an earlier completed review checkpoint, shared for resumption.
        ctx.state.scratch['s6_quality_batches']['previous-completed-review'] = {'verdict': 'PASS'}
        # The real audit resets this only on its isolated branch.
        assert ctx.state.scratch['ax_candidate_review']['audit_unreviewed_concept_ids'] != []
        ctx.persist()
        mid_audit = store.load_state(dlc.run_id)
        assert [item.model_dump(mode='json') for item in mid_audit.concepts] == baseline
        assert mid_audit.scratch['ax_candidate_review'] == progress
        raise AbortRun('Simulated audit interruption')

    monkeypatch.setattr(agent, 'verify_artifact', interrupted_auditor)
    with pytest.raises(AbortRun, match='Simulated audit interruption'):
        if path == 'codesign':
            recovery.codesign(RunContext(dlc),
                {'candidate_id': first.id, 'blocker_id': 'left', 'proposal': {}},
                {'candidate_id': second.id, 'blocker_id': 'right', 'proposal': {}},
                {item.id: item for item in dlc.concepts})
        else:
            recovery.run(RunContext(dlc))
    saved = store.load_state(dlc.run_id)
    assert [item.model_dump(mode='json') for item in saved.concepts] == baseline
    assert saved.scratch['ax_candidate_review'] == progress
    assert saved.scratch['s6_quality_batches']['previous-completed-review']['verdict'] == 'PASS'
    assert saved.steps[-1].status == 'FAILED'
