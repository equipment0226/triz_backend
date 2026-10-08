"""Current facts survive intake and S7 without becoming future obligations."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from triz import agent, analysis_semantic_gate, baseline_facts, digest, nodes, store, verify
from triz import verification_contract as contract
from triz.context import AbortRun, HumanInterrupt, RunContext
from triz.schema import Attachment, BaselineFact, ClarifyTurn, ConceptSpec, Constraint, ConstraintSet, GlobalState
from triz.settings import settings


QUERY = '현재 연간 에너지 사용은 6 GWh입니다. 보정 연간 총에너지는 45% 이상 절감해야 합니다.'


def baseline_row():
    return {'id': 'FACT-energy-before', 'statement': '현재 연간 에너지 사용은 6 GWh이다.',
        'source_path': 'raw_query', 'source_quote': '현재 연간 에너지 사용은 6 GWh입니다.',
        'context': '개선 전 기준선이며 개선 후 6 GWh를 유지해야 하는 요구가 아니다.'}


def requirement_row():
    return {'id': 'CON-saving-required', 'kind': 'NUMERIC', 'source': 'USER', 'hard': True,
        'statement': '보정 연간 총에너지를 45% 이상 절감해야 한다.',
        'parameter': '연간 에너지 절감률', 'operator': '>=', 'value': '45', 'unit': '%',
        'rationale': '직접 명시한 목표'}


def intake_output():
    return {'domain': {'industry': '건물 운영', 'job_family': '에너지 설계',
        'target_system': '건물 에너지 관리', 'problem_type': 'PHYSICAL_TECHNICAL', 'is_engineering': True},
        'frame': {'restated_problem': '보정 에너지 사용을 절감한다', 'symptom': '에너지 과다 사용',
                  'confidence': 1, 'success_criteria': ['45% 절감'], 'missing_info': []},
        'constraints': {'items': [requirement_row()], 'baseline_facts': [baseline_row()], 'open_questions': []},
        'candidate_characteristics': [], 'candidate_conflicts': []}


def install_energy(state):
    state.raw_query = QUERY
    state.constraints = ConstraintSet(items=[Constraint.model_validate(requirement_row())],
        baseline_facts=[BaselineFact.model_validate(baseline_row())])


def focused_pass():
    return {'checks': [{'id': key, 'status': 'PASS', 'reason': '원문 의무와 현재 사실의 역할이 일치한다.',
                        'findings': []} for key in analysis_semantic_gate.RULES['R1_CONSTRAINT_ROLES']]}


def misclassified_intake(case):
    data = intake_output()
    review = focused_pass()
    if case == 'requirement_excluded':
        data['constraints']['items'] = []
        statement = requirement_row()['statement']
        quote = '보정 연간 총에너지는 45% 이상 절감해야 합니다.'
        data['constraints']['baseline_facts'].append({'id': 'FACT-false-goal', 'statement': statement,
            'source_path': 'raw_query', 'source_quote': quote, 'context': '목표를 기준 사실로만 분류했다.'})
        path = '/constraints/baseline_facts/1/statement'
        key = 'INTAKE_REQUIREMENT_COVERAGE'
        issue = '직접 명시한 절감 목표가 active items에서 빠졌다.'
        correction = '45% 이상 절감 목표를 필수 제약 items로 보존하고 baseline에서 제거한다.'
    else:
        data['constraints']['baseline_facts'] = []
        statement, quote = baseline_row()['statement'], baseline_row()['source_quote']
        data['constraints']['items'].append({'id': 'CON-false-fixed-energy', 'statement': statement,
                                            'source': 'USER', 'hard': True})
        path = '/constraints/items/1/statement'
        key = 'INTAKE_ROLE_ASSIGNMENT'
        issue = '현재 사용량 보고를 개선 후에도 유지할 의무로 승격했다.'
        correction = '현재 6 GWh를 원문 근거와 함께 baseline에 옮기고 유지 의무 items에서 제외한다.'
    finding = {'artifact_path': path, 'artifact_quote': statement,
        'evidence_path': '/context/direct_user_sources/raw_query/text', 'evidence_quote': quote,
        'issue': issue, 'suggested_correction': correction}
    next(row for row in review['checks'] if row['id'] == key).update(
        status='REVISE', reason=issue, findings=[finding])
    return data, review


def test_only_role_rubric_is_mandatory_in_intake_and_pinned_missing_rubric_gets_current_rules(monkeypatch):
    assert contract.is_critical('R1_CONSTRAINT_ROLES', 's1_extract')
    assert not contract.is_critical('R1_INTAKE', 's1_extract')
    assert not contract.is_critical(None, 's1_clarify')
    monkeypatch.setattr(settings, 'rubric', lambda rubric_id: None)
    rubric = contract.effective_rubric(settings, 'R1_CONSTRAINT_ROLES')
    assert {row['id'] for row in rubric['criteria']} == {'C1', 'C2'}
    assert all(row['required'] and row['min_score'] == 1 for row in rubric['criteria'])
    supplement = contract.verifier_supplement(rubric)
    assert '역할 분류만 검증' in supplement and 'unknown/open_questions' in supplement
    assert 'PRODUCT가 object' not in supplement and 'BASIC 개수' not in supplement
    assert contract.SOURCE_ALIAS_CONTRACT in supplement


@pytest.mark.parametrize('case', ['requirement_excluded', 'baseline_promoted'])
@pytest.mark.parametrize('repair', [False, True])
def test_production_intake_gate_blocks_or_repairs_semantic_roles_despite_generic_pass(
        state, intake_runner, monkeypatch, case, repair):
    # The normal deployed whitelist need not know the new rubric. The always-on
    # contract must still run it, including when the old generic reviewer passes.
    assert 'R1_CONSTRAINT_ROLES' not in settings.cfg('verification.critical_rubrics', [])
    monkeypatch.setitem(settings.triz['verification'], 'analysis_semantic_repairs', int(repair))
    original = deepcopy(state.constraints.model_dump())
    bad, review = misclassified_intake(case)
    assert not baseline_facts.check_extraction(bad, state)  # Exact quotation alone is insufficient.
    calls = []
    # Production tier escalation permits one final attempt after the semantic
    # repair allowance. An unresolved defect must still stop after that attempt.
    generated = [bad, intake_output()] if repair else [bad, deepcopy(bad)]
    focused = [review, focused_pass()] if repair else [review, deepcopy(review)]
    def chat(ctx, **kwargs):
        assert state.constraints.model_dump() == original
        calls.append(kwargs)
        if kwargs.get('_node') == 's1_extract':
            data = generated.pop(0)
        elif 'focused semantic auditor' in kwargs.get('system', ''):
            data = focused.pop(0)
        else:
            data = {'verdict': 'PASS', 'per_criterion': [{'id': key, 'score': 1} for key in ['C1', 'C2']]}
        return SimpleNamespace(data=data, text='', model='offline', meta={}, tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    if repair:
        nodes.s1_extract(RunContext(state))
        assert state.constraints.baseline_facts[0].model_dump() == baseline_row()
        assert [row.id for row in state.constraints.items] == ['CON-saving-required']
        assert state.steps[-1].status == 'OK'
        assert [v['verdict'] for v in state.steps[-1].verdicts] == ['REVISE', 'PASS']
        assert review['checks'][0]['id'] in calls[2]['user']
    else:
        with pytest.raises(AbortRun):
            nodes.s1_extract(RunContext(state))
        assert state.constraints.model_dump() == original and state.steps[-1].status == 'FAILED'
        assert state.steps[-1].verdicts[-1]['generic_verdict'] == 'PASS'
    assert len(calls) == 6
    assert not generated and not focused


def test_incomplete_intake_passes_role_gate_then_requests_clarification(state, intake_runner):
    outputs, calls = intake_runner
    state.raw_query = '문제를 분석해 주세요.'
    state.scratch.pop('clarify_skipped', None)
    outputs.append({'domain': {}, 'frame': {'confidence': 0, 'missing_info': ['대상과 증상 미확인']},
        'constraints': {'items': [], 'baseline_facts': [], 'open_questions': ['문제와 제약은 무엇인가요?']}})
    with pytest.raises(HumanInterrupt) as stopped:
        nodes.s1_extract(RunContext(state))
    assert stopped.value.request.kind == 'CLARIFY'
    assert state.constraints.items == [] and state.constraints.baseline_facts == []
    assert state.intake.clarify_turns[-1].question == '어떤 시스템에서 어떤 문제가 발생합니까?'
    assert [step.status for step in state.steps] == ['OK', 'OK']
    assert len(calls) == 4 and any('focused semantic auditor' in call.get('system', '') for call in calls)


def test_legacy_state_load_defaults_to_empty_baseline_without_changing_requirements(state):
    legacy = state.model_dump(mode='json')
    legacy['constraints'] = {'items': [requirement_row()], 'open_questions': []}
    loaded = GlobalState.model_validate(legacy)
    assert loaded.constraints.baseline_facts == []
    assert loaded.constraints.items[0].id == 'CON-saving-required' and loaded.constraints.items[0].hard


def test_active_compliance_list_excludes_baseline_but_keeps_45_percent_requirement(state):
    install_energy(state)
    active = verify.constraints_full(state)
    assert len(active) == 1 and active[0]['constraint_id'] == 'CON-saving-required'
    assert active[0]['value'] == '45' and active[0]['hard'] is True
    assert all(row['constraint_id'] != 'FACT-energy-before' for row in active)
    assert state.constraints.hard_items() == state.constraints.items


def test_baseline_source_and_qualifier_survive_digest_focused_context_and_database_roundtrip(state):
    install_energy(state)
    RunContext(state).persist()
    loaded = store.load_state(state.run_id)
    assert loaded.constraints.baseline_facts[0].model_dump() == baseline_row()
    packet = digest.facts_packet(loaded)
    assert packet['baseline_facts'] == [baseline_row()]
    assert '유지해야 하는 의무가 아니다' in packet['baseline_policy']
    focused = analysis_semantic_gate.request_packet(loaded, 'R4_IFR', {})
    assert focused['context']['baseline_facts'] == [baseline_row()]
    block = verify.constraints_block(loaded)
    assert 'FACT-energy-before' in block and 'CON-saving-required' in block
    assert baseline_row()['source_quote'] in block


def test_answer_question_context_and_attachment_exact_quote_are_valid_primary_evidence(state):
    state.intake.clarify_turns = [ClarifyTurn(question='현재 공정의 PEB 온도는?', user_answer='현재 PEB 온도는 80°C입니다.', answered=True)]
    state.intake.attachments = [Attachment(filename='meter.txt', extracted_text='현재 계측 오차는 ±2℃이다.')]
    data = intake_output()
    data['constraints']['baseline_facts'] = [
        {'statement': '현재 PEB 온도 80°C', 'source_path': 'intake.clarify_turns[0].user_answer',
         'source_quote': '현재 PEB 온도는 80°C입니다.', 'context': '질문이 현재 운전 조건을 묻는다.'},
        {'statement': '현재 센서 오차 ±2℃', 'source_path': 'intake.attachments[0].extracted_text',
         'source_quote': '현재 계측 오차는 ±2℃이다.', 'context': '최악온도 계산에 반영한다.'}]
    assert not baseline_facts.check_extraction(data, state)
    sources = baseline_facts.sources(state)
    assert sources['intake.clarify_turns[0].user_answer']['question'] == '현재 공정의 PEB 온도는?'


@pytest.mark.parametrize('mutation', ['quote', 'generated_summary', 'unanswered', 'blank_statement', 'bad_shape', 'duplicate_id'])
def test_invalid_baseline_cannot_authenticate_a_new_current_fact(state, mutation):
    state.raw_query = QUERY
    data = intake_output()
    rows = data['constraints']['baseline_facts']
    if mutation == 'quote':
        rows[0]['source_quote'] = '현재 연간 에너지 사용은 3 GWh입니다.'
    elif mutation == 'generated_summary':
        rows[0]['source_path'] = 'intake.frame.restated_problem'
    elif mutation == 'unanswered':
        state.intake.clarify_turns = [ClarifyTurn(question='현재 사용량?', user_answer=QUERY, answered=False)]
        rows[0]['source_path'] = 'intake.clarify_turns[0].user_answer'
    elif mutation == 'blank_statement':
        rows[0]['statement'] = ' '
    elif mutation == 'bad_shape':
        data['constraints']['baseline_facts'] = {'statement': 'partial'}
    else:
        rows.append(deepcopy(rows[0]))
    assert baseline_facts.check_extraction(data, state)


def test_same_fact_cannot_be_both_an_active_requirement_and_a_baseline(state):
    state.raw_query = QUERY
    data = intake_output()
    data['constraints']['items'].append({'id': 'CON-false-fixed-energy',
        'statement': baseline_row()['statement'], 'source': 'USER', 'hard': True})
    assert baseline_facts.check_extraction(data, state)


@pytest.fixture
def intake_runner(state, monkeypatch):
    from triz import rag
    from triz.ax import runtime
    state.raw_query = QUERY
    state.scratch['clarify_skipped'] = True
    monkeypatch.setattr(rag, 'lessons_block', lambda state: '')
    # A frozen legacy template still tells the generator to freeze every number.
    monkeypatch.setattr(runtime, 'render_prompt', lambda state, prompt_id, **values:
        'OLD_PINNED_' + prompt_id + ': 모든 사용자 수치를 USER HARD items로 추출하라. ' + str(values))
    monkeypatch.setitem(settings.triz['verification'], 'enabled', True)
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 1)
    calls, outputs = [], []
    def chat(ctx, **kwargs):
        calls.append(kwargs)
        if kwargs.get('_node') == 's1_extract':
            data = outputs.pop(0)
        elif kwargs.get('_node') == 's1_clarify':
            data = {'questions': [{'question': '어떤 시스템에서 어떤 문제가 발생합니까?'}]}
        elif 'focused semantic auditor' in kwargs.get('system', ''):
            data = focused_pass()
        else:
            rubric = contract.effective_rubric(settings, 'R1_CONSTRAINT_ROLES')
            data = {'verdict': 'PASS', 'per_criterion': [{'id': c['id'], 'score': 1} for c in rubric['criteria']]}
        return SimpleNamespace(data=data, text='', model='offline', meta={}, tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    return outputs, calls


def test_s1_pinned_generation_receives_new_role_contract_and_persists_sourced_baseline(state, intake_runner):
    outputs, calls = intake_runner
    outputs.append(intake_output())
    nodes.s1_extract(RunContext(state))
    assert state.constraints.baseline_facts[0].model_dump() == baseline_row()
    assert [row.id for row in state.constraints.items] == ['CON-saving-required']
    assert 'OLD_PINNED_P_S1_EXTRACT' in calls[0]['user']
    assert baseline_facts.ROLE_CONTRACT in calls[0]['user']
    assert calls[0]['user'].index(baseline_facts.ROLE_CONTRACT) > calls[0]['user'].index('OLD_PINNED_P_S1_EXTRACT')
    assert 'raw_query' in calls[0]['user'] and QUERY in calls[0]['user']
    assert store.load_state(state.run_id).constraints.baseline_facts[0].source_quote == baseline_row()['source_quote']


def test_s1_repairs_duplicate_legacy_hard_fact_before_persisting(state, intake_runner):
    outputs, calls = intake_runner
    bad = intake_output()
    bad['constraints']['items'].append({'id': 'CON-false-fixed-energy',
        'statement': baseline_row()['statement'], 'source': 'USER', 'hard': True})
    outputs.extend([bad, intake_output()])
    nodes.s1_extract(RunContext(state))
    assert [row.id for row in state.constraints.items] == ['CON-saving-required']
    generated = [call for call in calls if call.get('_node') == 's1_extract']
    assert len(generated) == 2 and 'FATAL-INTAKE' in generated[1]['user']
    assert state.steps[-1].status == 'OK'


def test_s1_unrepaired_fabricated_source_stops_before_overwriting_prior_constraints(state, intake_runner, monkeypatch):
    outputs, calls = intake_runner
    original = deepcopy(state.constraints.model_dump())
    monkeypatch.setitem(settings.triz['verification'], 'analysis_structure_repairs', 0)
    bad = intake_output()
    bad['constraints']['baseline_facts'][0]['source_quote'] = '전혀 존재하지 않는 사용자 관측값'
    outputs.append(bad)
    with pytest.raises(AbortRun):
        nodes.s1_extract(RunContext(state))
    assert state.constraints.model_dump() == original
    assert len(calls) == 1 and state.steps[-1].status == 'FAILED'


@pytest.mark.parametrize('invalid_items', [None, {}, 'none', 0, False, [None], [{'statement': ''}]],
                         ids=['null', 'object', 'string', 'number', 'boolean', 'null_row', 'empty_statement'])
def test_s1_invalid_active_items_never_silently_clear_existing_requirements(
        state, intake_runner, monkeypatch, invalid_items):
    outputs, calls = intake_runner
    install_energy(state)
    original = deepcopy(state.constraints.model_dump())
    monkeypatch.setitem(settings.triz['verification'], 'analysis_structure_repairs', 0)
    bad = intake_output()
    bad['constraints']['items'] = invalid_items
    issues = baseline_facts.check_extraction(bad, state)
    assert issues and all(issue.startswith('FATAL-INTAKE:') for issue in issues)
    assert 'constraints.items' in issues[0]
    outputs.append(bad)
    with pytest.raises(AbortRun):
        nodes.s1_extract(RunContext(state))
    assert state.constraints.model_dump() == original
    assert state.steps[-1].status == 'FAILED' and len(calls) == 1
    assert store.load_state(state.run_id).constraints.model_dump() == original


def test_s1_null_active_items_can_be_repaired_without_losing_the_actual_requirement(state, intake_runner):
    outputs, calls = intake_runner
    install_energy(state)
    bad = intake_output()
    bad['constraints']['items'] = None
    outputs.extend([bad, intake_output()])
    nodes.s1_extract(RunContext(state))
    assert [item.id for item in state.constraints.items] == ['CON-saving-required']
    assert state.constraints.items[0].hard and state.constraints.items[0].value == '45'
    assert state.constraints.baseline_facts[0].model_dump() == baseline_row()
    generated = [call for call in calls if call.get('_node') == 's1_extract']
    assert len(generated) == 2 and 'constraints.items' in generated[-1]['user']
    assert state.steps[-1].status == 'OK'


def test_s7_receives_baseline_as_context_and_only_45_percent_as_obligation(state, monkeypatch):
    install_energy(state)
    concept = ConceptSpec(title='부분 부하 제어', description='현재 기준선과 비교해 에너지 사용을 줄인다.',
                          expected_effect='보정 연간 총에너지 45% 절감')
    state.concepts = [concept]
    captured = []
    def gate(ctx, **kwargs):
        captured.append(kwargs)
        rules = kwargs['vars']['constraints_full']
        assert [c['constraint_id'] for c in rules] == ['CON-saving-required']
        assert baseline_row()['source_quote'] in kwargs['system_override']
        return {'results': [{'concept_id': concept.id, 'verdict': 'PASS', 'per_constraint': [
            {'constraint_id': 'CON-saving-required', 'verdict': 'PASS', 'reason': '보정 연간 총에너지 45% 절감'}]}]}
    monkeypatch.setattr(agent, 'run_agent', gate)
    nodes.s7_gate(RunContext(state))
    assert len(captured) == 1 and len(state.concepts) == 1
    assert state.constraint_checks[0].verdict == 'PASS'
    assert state.constraints.baseline_facts[0].model_dump() == baseline_row()
