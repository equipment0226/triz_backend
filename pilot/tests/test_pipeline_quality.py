import json
import threading
import time
from types import SimpleNamespace

import pytest

from triz import agent, digest, domain, evidence, knowledge, nodes, personas, quality, rag, verify
from triz.context import HumanInterrupt, RunContext
from triz.schema import (CauseEffectChain, CauseNode, ClarifyTurn, ConceptSpec, Constraint,
                         DomainContext, KeyProblem, RawIdea, SolutionFeedback, FeedbackArtifact,
                         SystemCandidate, TechnicalContradiction)
from triz.settings import settings


@pytest.mark.parametrize("prefix", ["", "반도체 회사의 ", "배터리 제조사의 "])
def test_industry_background_does_not_change_organizational_contract(state, prefix):
    state.raw_query = prefix + "조직에서 개인 성과급을 높이면 협업과 지식 공유가 줄어든다"
    profile = domain.sync_contract(state)
    assert profile["problem_type"] == "ORGANIZATIONAL_BUSINESS"
    assert profile["difficulty"] == "advanced"
    assert not state.domain.is_engineering
    text = domain.context(state, "s6_concept")
    assert "행위자" in text and "관련 물리·화학·공학 이론" not in text
    assert not {"C_STANDARDS", "H_EFFECTS"} & set(domain.select_tracks(state, settings.cfg("tracks.DEEP")))


def test_mixed_physics_requires_explicit_scope(state):
    state.domain.problem_type = "MIXED"
    assert not domain.physical_allowed(state)
    state.domain.physical_scope = "웨이퍼 표면 세정 과정"
    assert domain.physical_allowed(state)


def test_suffixed_gate_is_blind_to_hypotheses(state):
    domain.sync_contract(state)
    state.scratch["deep_dive"] = {"confirmed_facts": ["OBSERVATION"], "competing_hypotheses": ["HIDDEN"]}
    text = domain.context(state, "s7_gate_12")
    assert "OBSERVATION" in text and "HIDDEN" not in text


def test_confirmation_updates_every_boundary_consumer(state):
    first = SystemCandidate(name="기존 부서")
    second = SystemCandidate(name="부서 간 보상 관계", super_system="회사", operative_zone="공동 업무 승인", operative_time="성과 평가 시")
    state.confirm.candidates = [first, second]
    state.scratch["resume_payload"] = {"candidate_id": second.id}
    nodes.s2_confirm(RunContext(state))
    assert digest.target_system(state) == second.name == state.domain.target_system
    assert state.confirm.operative_zone == second.operative_zone
    assert digest.domain_brief(state)["target_system"] == second.name


def test_clarification_preserves_old_answers_and_maps_only_pending(state, monkeypatch):
    state.intake.clarify_turns = [ClarifyTurn(question="기존 질문", user_answer="기존 답", answered=True), ClarifyTurn(question="새 질문")]
    state.scratch["resume_payload"] = {"answers": ["새 답"]}
    captured = []
    def respond(ctx, **kw):
        if kw['node'] == 's1_extract':
            captured.extend(kw['vars']['clarify_history'])
            return {"domain": {"industry": "조직", "target_system": "보상 규칙", "problem_type": "ORGANIZATIONAL_BUSINESS"}, "frame": {"symptom": "협업 감소", "confidence": .9}}
        return {"questions": [{"question": "다음 질문"}]}
    monkeypatch.setattr(agent, "run_agent", respond)
    with pytest.raises(HumanInterrupt):
        nodes.s1_extract(RunContext(state))
    assert "기존 답" in captured[0] and "새 답" in captured[1]
    assert len(state.intake.clarify_turns) == 3


def test_cause_graph_rejects_cycles_disconnected_and_duplicate_nodes():
    nodes_ = [{'id': 'N1', 'node_type': 'TARGET_DISADVANTAGE', 'parents': ['N2']}, {'id': 'N2', 'node_type': 'ROOT_CAUSE', 'parents': ['N1']}]
    assert any('순환' in x for x in verify.check_ceca({'nodes': nodes_}))
    nodes_[0]['parents'] = []
    nodes_[1]['parents'] = []
    assert any('연결' in x for x in verify.check_ceca({'nodes': nodes_}))
    assert any('중복' in x for x in verify.check_ceca({'nodes': nodes_ + [nodes_[0]]}))


def test_cause_depth_uses_all_parent_paths():
    graph = [{'id': 'N1', 'parents': []}, {'id': 'N2', 'parents': ['N1']},
             {'id': 'N3', 'parents': ['N2']}, {'id': 'N4', 'parents': ['N1', 'N3']}]
    assert verify._chain_depth(graph) == 4


def test_packets_keep_conditions_and_natural_language_requirements(state):
    state.definition.technical_contradictions = [TechnicalContradiction(then_good="개인 기여 식별", but_bad="공동 기여 감소", improving_param_id=1, worsening_param_id=2, coupling_mechanism="개인 실적만 보상")]
    packet = digest.contradictions_digest(state)[0]
    assert packet['then_good'] == "개인 기여 식별" and packet['worsening_definition']
    idea = RawIdea(idea="변경", detail={'adaptation_note': '보상 귀속을 확인', 'self_rebuttal': '상호 담합 가능'})
    assert digest.idea_packet(idea)['support']['adaptation_note'] == '보상 귀속을 확인'
    state.analysis.ceca = CauseEffectChain(nodes=[CauseNode(id='N1', node_type='TARGET_DISADVANTAGE'), CauseNode(id='N2', parents=['N1'], node_type='ROOT_CAUSE', is_contradiction_seed=True, hypothesis_ids=['H1'])])
    assert digest.ceca_seeds(state)[1]['hypothesis_ids'] == ['H1']


def test_idea_selection_does_not_starve_late_tracks():
    ideas = [RawIdea(track='A', idea=str(i)) for i in range(60)] + [RawIdea(track='H', idea='late')]
    assert any(i.idea == 'late' for i in digest.select_ideas(ideas, 8))


def test_merge_preserves_all_sources_and_rejects_fabricated_lineage(state, monkeypatch):
    tc = TechnicalContradiction()
    state.definition.technical_contradictions = [tc]
    state.definition.key_problems = [KeyProblem(title='핵심', contradiction_ids=[tc.id])]
    a = RawIdea(title='A', conditions=['condition A'], detail={'self_rebuttal': 'risk A'})
    b = RawIdea(title='B', conditions=['condition B'], detail={'adaptation_note': 'risk B'})
    state.solve.raw_ideas = [a, b]
    monkeypatch.setattr(agent, 'run_agent', lambda *args, **kwargs: {'ideas': [
        {'keep_ids': [a.id, b.id], 'title': '합침', 'addresses': [tc.id], 'resolution_status': 'RESOLVED', 'resolution_argument': '양쪽 조건을 분리하여 보존'},
        {'keep_ids': ['invented'], 'title': '허위'}]})
    assert not nodes._merge(RunContext(state))
    assert len(state.solve.raw_ideas) == 1
    result = state.solve.raw_ideas[0]
    assert set(result.source_idea_ids) == {a.id, b.id}
    assert set(result.conditions) == {'condition A', 'condition B'}
    assert len(result.detail['source_details']) == 2


def test_verifier_receives_observations_definitions_and_hypotheses(state, monkeypatch):
    state.intake.clarify_turns = [ClarifyTurn(question='Q', user_answer='MEASUREMENT', answered=True)]
    captured = {}
    def chat(ctx, **kw):
        captured.update(kw)
        return SimpleNamespace(data={'verdict': 'PASS', 'score': .9}, tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, 'tracked_chat', chat)
    agent.verify_artifact(RunContext(state), 'R4_CONTRA', {'technical_contradictions': [{'improving_param_id': 1, 'worsening_param_id': 2}]}, '')
    assert 'MEASUREMENT' in captured['user'] and 'parameter_definitions' in captured['user']
    assert state.raw_query in captured['user']


def prepare_concepts(state, monkeypatch, prior=False):
    tc = TechnicalContradiction()
    state.definition.technical_contradictions = [tc]
    state.solve.raw_ideas = [RawIdea(title=f'idea{i}', idea=f'mechanism{i}', mechanism_key=f'key{i}', addresses=[tc.id], resolution_status='RESOLVED') for i in range(12)]
    calls, audits = [], []
    monkeypatch.setattr(rag, 'prior_cases_block', lambda s: 'PRIOR' if prior else '')
    def generate(ctx, **kw):
        args = kw['vars']
        calls.append(args)
        return {'concepts': [{'title': i['title'], 'source_idea_ids': [i['id']], 'addresses_contradictions': [tc.id],
                 'working_principle': 'mechanism', 'resolution_argument': 'both goals',
                 'validation_plan': [{'experiment': 'controlled test', 'failure_criterion': 'goal lost'}]} for i in args['ideas']]}
    def audit(ctx, rubric, data, facts):
        audits.append(data)
        return {'verdict': 'PASS', 'per_concept': [{'concept_id': c['concept_id'], 'verdict': 'PASS'} for c in data['concepts']]}
    monkeypatch.setattr(agent, 'run_agent', generate)
    monkeypatch.setattr(agent, 'verify_artifact', audit)
    return calls, audits


def test_concept_allocation_generates_twelve_not_fifteen_and_audits_all(state, monkeypatch):
    calls, audits = prepare_concepts(state, monkeypatch)
    quality.generate_concepts(RunContext(state))
    assert sorted(c['batch_size'] for c in calls) == [2, 5, 5]
    assert len(state.concepts) == 12 and len(audits) == 1
    assert len(audits[0]['concepts']) == 12
    assert all(c.quality_status == 'PASS' for c in state.concepts)


def test_prior_cases_visible_to_only_bounded_assigned_candidates(state, monkeypatch):
    calls, audits = prepare_concepts(state, monkeypatch, prior=True)
    quality.generate_concepts(RunContext(state))
    influenced = sum(c['batch_size'] for c in calls if c['prior_cases_block'])
    assert influenced == 3 and len(calls) == 3


def test_quality_rejection_removes_only_affected_concept(state, monkeypatch):
    first, second = ConceptSpec(title='bad'), ConceptSpec(title='unknown')
    state.concepts = [first, second]
    monkeypatch.setattr(agent, 'verify_artifact', lambda *a: {'verdict': 'REJECT', 'per_concept': [
        {'concept_id': first.id, 'verdict': 'REJECT', 'fatal_flaws': ['invented evidence']} ]})
    quality.audit_concepts(RunContext(state))
    assert [c.id for c in state.concepts] == [second.id]
    assert second.quality_status != 'PASS'


def test_persona_cap_preserves_required_dimensions_and_business_roles(state, monkeypatch):
    state.domain = DomainContext(industry='반도체', problem_type='ORGANIZATIONAL_BUSINESS', is_engineering=False)
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **k: {'personas': [
        {'role_name': f'구성원{i}', 'dimensions': ['ADOPTION']} for i in range(6)]})
    reviewers = personas.build_personas(RunContext(state))
    covered = {d for p in reviewers for d in p.dimensions}
    assert {'GOAL', 'RESOLUTION', 'CAUSAL', 'FEASIBILITY', 'COST', 'RISK', 'TIME', 'ADOPTION'} <= covered
    assert len(reviewers) <= 6
    assert personas._seed_group('반도체', '인사', False) == 'business'


def test_equal_grounded_review_scores_are_valid():
    scores = [{'concept_id': k, 'score': 3, 'rationale': '동일한 근거 수준'} for k in ['A', 'B']]
    assert verify.check_review({'scores': scores}, {'A', 'B'}) == []
    assert verify.check_review({'scores': scores[:1]}, {'A', 'B'})


def test_business_search_does_not_force_patents(state, monkeypatch):
    state.domain.problem_type = 'ORGANIZATIONAL_BUSINESS'
    seen = []
    monkeypatch.setattr(agent, 'run_agent', lambda *a, **k: {'queries': [{'kind': 'PATENT', 'query': 'irrelevant hardware'}, {'kind': 'PAPER', 'query': 'incentive collaboration'}]})
    def search(query, kind, limit, diagnostics):
        seen.append(kind)
        diagnostics['status'] = 'EMPTY'
        return []
    monkeypatch.setattr(evidence.scholar, 'search_kind', search)
    evidence.discover(RunContext(state), before_concepts=True)
    assert seen == ['PAPER'] and evidence.required_kinds(state) == {'PAPER'}


def test_feedback_retains_lessons_and_filters_type(state, monkeypatch):
    state.domain.problem_type = 'ORGANIZATIONAL_BUSINESS'
    c = ConceptSpec(title='보상 설계', working_principle='공동 기여 귀속', assumptions=['기여 기록 가능'])
    state.concepts = [c]
    state.feedback = FeedbackArtifact(solution_feedback=[SolutionFeedback(concept_id=c.id, rating=5)])
    saved = []
    monkeypatch.setattr(rag.store, 'rag_upsert', lambda **kw: saved.append(kw))
    rag.write_feedback(state, {'domain_lesson': '협업 비용', 'accepted_patterns': ['공동 귀속'], 'rejected_patterns': []})
    assert saved[0]['meta']['domain_lesson'] == '협업 비용'
    assert saved[0]['meta']['feedback_status'] == 'USER_PREFERENCE_NOT_VALIDATION'
    docs = [{'id': 'x', 'doc': '공동 귀속', 'meta': {'user_id': state.user_id, 'problem_type': 'PHYSICAL_TECHNICAL'}, 'weight': 1}]
    monkeypatch.setattr(rag.store, 'rag_all', lambda c: docs)
    assert rag.retrieve('공동 귀속', user_id=state.user_id, problem_type='ORGANIZATIONAL_BUSINESS') == []


def test_unconfirmed_practice_is_not_an_absolute_taboo(state):
    state.scratch['taboo'] = [{'item': '관행 유지', 'confirmed': True, 'constraint_id': 'invented'}]
    assert verify.confirmed_taboos(state) == []
    c = Constraint(statement='사용자 명시 금지', hard=True, source='USER')
    state.constraints.items = [c]
    state.scratch['taboo'][0]['constraint_id'] = c.id
    assert verify.confirmed_taboos(state)


def test_effects_retrieval_includes_conditions_and_coverage():
    block = knowledge.effects_block(limit=1, required_functions=['물체를 비접촉으로 지지하거나 이동시킨다'])
    assert '자기부상' in block and '조건:' in block and '51개' in block


def test_gate_batches_execute_concurrently_but_keep_order(state, monkeypatch):
    state.constraints.items = [Constraint(statement='성공 조건', hard=True)]
    state.concepts = [ConceptSpec(title=str(i)) for i in range(4)]
    barrier = threading.Barrier(2)
    def gate(ctx, **kw):
        barrier.wait(timeout=5)
        return {'results': [{'concept_id': c['concept_id'], 'verdict': 'PASS'} for c in kw['vars']['concepts_for_gate']]}
    monkeypatch.setattr(agent, 'run_agent', gate)
    nodes.s7_gate(RunContext(state))
    assert [r.concept_id for r in state.constraint_checks] == [c.id for c in state.concepts]


def test_s4_waits_for_parallel_definitions_before_selecting_problem(state, monkeypatch):
    barrier = threading.Barrier(3)
    finished = []
    def respond(ctx, **kw):
        if kw['node'] == 's4_key_problem':
            assert len(finished) == 3
            assert kw['vars']['technical_contradictions']
            return {'key_problems': []}
        barrier.wait(timeout=5)
        finished.append(kw['node'])
        if kw['node'] == 's4_contradictions':
            return {'technical_contradictions': [{'label': 'coupled goals'}]}
        return {}
    monkeypatch.setattr(agent, 'run_agent', respond)
    nodes.s4_define(RunContext(state))


def test_s5_overlaps_search_without_sharing_solve_mutations(state, monkeypatch):
    state.control.enabled_tracks = ['A_MATRIX']
    barrier = threading.Barrier(2)
    def tracks(ctx, selected):
        assert ctx.state is not state
        ctx.state.solve.raw_ideas = [RawIdea(title='track result')]
        barrier.wait(timeout=5)
    def search(ctx):
        assert not ctx.state.solve.raw_ideas
        ctx.state.scratch['evidence_candidates'] = [{'title': 'retrieved'}]
        barrier.wait(timeout=5)
    def merge(ctx):
        assert ctx.state.solve.raw_ideas[0].title == 'track result'
        assert ctx.state.scratch['evidence_candidates'][0]['title'] == 'retrieved'
        return False
    monkeypatch.setattr(nodes, '_run_tracks', tracks)
    monkeypatch.setattr(nodes, '_evidence', search)
    monkeypatch.setattr(nodes, '_merge', merge)
    nodes.s5_solve(RunContext(state))


def test_saved_v2_reference_stage_migrates_before_evaluation(state):
    from triz import pipeline
    state.scratch['pipeline_version'] = 2
    state.control.stage_index = 10
    pipeline._upgrade(state)
    assert state.control.stage_index == 9
    assert pipeline.PIPELINE[9][0] == 's8_references'
    assert pipeline.PIPELINE[10][0] == 's8_evaluate'
    assert state.scratch['pipeline_version'] == 3


def test_completed_saved_report_is_not_rewound(state):
    from triz import pipeline
    state.scratch['pipeline_version'] = 2
    state.control.stage_index = 13
    state.status = 'COMPLETED'
    pipeline._upgrade(state)
    assert state.control.stage_index == 13 and state.status == 'COMPLETED'


def test_timeout_prevents_new_model_call(state, monkeypatch):
    from triz import llm
    from triz.context import AbortRun
    state.scratch['execution_deadline'] = time.time() - 1
    with pytest.raises(AbortRun):
        agent.tracked_chat(RunContext(state), system='rules', user='query', tier='T2')


def test_new_provenance_fields_survive_state_serialization(state):
    from triz.schema import GlobalState
    state.concepts = [ConceptSpec(source_idea_ids=['I1'], mechanism_key='K', quality_status='REVISE',
        quality_issues=['verify condition'], hypothesis_ids=['H1'], prior_case_ids=['F1'])]
    restored = GlobalState.model_validate_json(state.model_dump_json())
    assert restored.concepts[0].source_idea_ids == ['I1']
    assert restored.concepts[0].quality_status == 'REVISE'


def test_offline_eval_exports_blinded_pairs_and_missing_timings(tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('quality_eval', Path(__file__).resolve().parents[1] / 'scripts' / 'quality_eval.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for variant in ['before', 'after']:
        folder = tmp_path / variant
        folder.mkdir()
        (folder / 'state.json').write_text(json.dumps({'raw_query': 'same case', 'concepts': [], 'run_id': variant}), encoding='utf-8')
    assert module.export(tmp_path/'before', tmp_path/'after', tmp_path/'out') == 1
    summary = json.loads((tmp_path/'out'/'summary.json').read_text())
    assert summary['baseline']['p95_seconds'] is None
    assert 'baseline' not in (tmp_path/'out'/'blind_review.md').read_text(encoding='utf-8')


def test_legacy_profile_without_type_can_be_upgraded(state):
    state.raw_query = '반도체 회사의 조직에서 성과급과 협업이 상충한다'
    state.scratch['industry_profile'] = {'industry_id': 'semiconductor', 'difficulty': 'advanced', 'source': 'keyword_catalog'}
    profile = domain.sync_contract(state)
    assert profile['problem_type'] == 'ORGANIZATIONAL_BUSINESS'
    assert not state.domain.is_engineering


def test_post_run_feedback_preserves_mechanism_without_model_call(state, monkeypatch):
    concept = ConceptSpec(title='공동 귀속', working_principle='공동 기여에 보상 권리를 분리 배정한다')
    state.concepts = [concept]
    captured = []
    monkeypatch.setattr(rag, 'write_feedback', lambda state, distill: captured.append(distill) or 1)
    nodes.record_feedback(state, {'missing_perspective': '기여 기록 비용', 'solution_feedback': [{'concept_id': concept.id, 'rating': 5}]})
    assert captured[0]['domain_lesson'] == '기여 기록 비용'
    assert captured[0]['accepted_patterns'] == [concept.working_principle]
