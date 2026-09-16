"""Nonblocking port to the existing trainer; never relabel telemetry as learning."""
from .domain import PatentError, digest

ALLOWED_ACTIONS = frozenset({'FETCH_EVIDENCE', 'ASK_HUMAN', 'REPAIR_CANDIDATE', 'RUN_TEST', 'DEFER'})
REQUIRED_OBLIGATIONS = frozenset({'TECHNICAL_CONTENT', 'PATENT_CONTENT', 'GLOBAL_FINAL', 'G1', 'G2'})


class LegacyLearningAdapter:
    def capabilities(self):
        from triz.ax import learning
        # The actual existing trainer binds features/actions/labels to TRIZ runs.
        port = getattr(learning, 'patent_training_port', None)
        compatible = callable(port) and getattr(port, 'contract_version', None) == 'patent-draft-v1'
        return {'state': 'ADAPTER_READY' if compatible else 'TELEMETRY_ONLY',
                'trainer': 'triz.ax.learning', 'namespace': 'patent_draft',
                'reason': None if compatible else 'Existing trainer has no patent namespace contract',
                'training_completed': False}

    def train(self, dataset):
        if self.capabilities()['state'] != 'ADAPTER_READY':
            raise PatentError('TRAINER_NOT_AVAILABLE', '특허 데이터 계약을 지원하는 trainer adapter가 없습니다.', 503)
        from triz.ax.learning import patent_training_port
        return patent_training_port(dataset)


def masked_action(proposal):
    if proposal.get('action') not in ALLOWED_ACTIONS or proposal.get('remove_obligations'):
        return {'action': 'DEFER', 'governor_override': True}
    return {'action': proposal['action'], 'governor_override': False}


def govern_operation(tool, proposed=None):
    """Learning is advisory; the validated scheduler retains mandatory work."""
    if tool in ('patent_search_local','patent_enrich_sources','patent_plan_search'):
        required='FETCH_EVIDENCE'
    elif tool=='patent_plan_questions':required='ASK_HUMAN'
    elif tool in ('patent_review_content','patent_final_review','patent_check_rules'):
        required='RUN_TEST'
    else:required='REPAIR_CANDIDATE'
    proposed=proposed or {'action':required}
    masked=masked_action(proposed)
    return {'source':'DETERMINISTIC_GOVERNOR','proposed':proposed,'executed_action':required,
            'governor_override':masked['governor_override'] or masked['action']!=required,
            'feasible_actions':[required], 'required_obligations':sorted(REQUIRED_OBLIGATIONS)}


def feedback_event(case, payload):
    allowed = {'STRUCTURAL_CHECK', 'T3_REVIEW_PROVISIONAL', 'HUMAN_CONFIRMED_CORRECTION', 'MEASURED_COST', 'OUTCOME_WHEN_AVAILABLE'}
    if payload.get('signal') not in allowed:
        raise PatentError('FEEDBACK_SIGNAL', '허용되지 않은 학습 신호입니다.', 422)
    if payload.get('origin') == 'TRIZ_STUDIO_BETA' and payload.get('negative_label'):
        raise PatentError('SCOPE_EXCLUDED', '베타 공개는 부정 학습 라벨에서 제외합니다.', 422)
    if payload.get('reward') is not None or payload.get('behavior_probability') is not None:
        raise PatentError('FEEDBACK_UNVERIFIED_REWARD','사용자가 학습 보상이나 행동 확률을 직접 지정할 수 없습니다.',422)
    from .repository import now
    event = {'namespace': 'patent_draft', 'case_id': case['case_id'], 'epoch': case['epoch'],
             'policy_version': case['policy_version'], 'snapshot_id': case['snapshot_id'],
             'signal': payload['signal'], 'origin': payload.get('origin'), 'reward': None,
             'behavior_probability': None, 'consent': bool(payload.get('training_consent', False)),
             'state': 'TELEMETRY_ONLY', 'payload': payload,'available_at_ms':now(),
             'source_group':source_group(case),'owner_id':case['owner_id'],
             'maturity':'USER_SUBMITTED_UNVERIFIED','training_eligible':False}
    event['dedupe_key'] = digest([case['case_id'], case['epoch'], case['snapshot_id'], payload])
    return event


def source_group(case):
    # All revisions and concepts derived from the same original problem stay in
    # one partition. A revision's changed content hash must not move its split.
    return digest([case['owner_id'],case['source_run_id']])


def export_dataset(repository,owner,case_id,cutoff_ms):
    """Explicit trainer port: consent, maturity and same-invention split boundary."""
    case=repository.get(owner,case_id)
    rows=repository.records(owner,case_id,'feedback')
    eligible=[r for r in rows if r.get('consent') and r.get('training_eligible') is True
        and r.get('owner_id')==owner and r.get('available_at_ms',cutoff_ms+1)<=cutoff_ms
        and r.get('maturity')=='HUMAN_CONFIRMED' and r.get('origin')!='TRIZ_STUDIO_BETA']
    unique={r['dedupe_key']:r for r in eligible}
    group=source_group(case)
    return {'namespace':'patent_draft','policy_version':case['policy_version'],'cutoff_ms':cutoff_ms,
        'group_id':group,'split':'train' if int(group[:8],16)%5 else 'evaluation',
        'events':list(unique.values()),'training_completed':False}
