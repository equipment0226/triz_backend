"""Review every consolidated idea in bounded, resumable model calls."""
import copy
import hashlib
import json
from pydantic import ValidationError

from .execution_config import ThreadPoolExecutor
from . import agent, digest, rag, verify
from .context import AbortRun
from .schema import ConceptSpec, Stage
from .settings import settings


PARAMETER_DIRECTION_INSTRUCTION = (
    "변수별로 물리량·변경 방향(증가/감소/유지/조건부/미확정)·기준 상태·단위·적용 조건을 구분한다. "
    "가속도와 가속 시간처럼 관련돼도 서로 다른 물리량을 같은 것으로 취급하지 않는다. "
    "시간·공간·운전 조건이 다르면 방향을 각각 명시하고, 근거 없이 시간은 감소·속도는 증가 같은 규칙을 적용하지 않는다. "
    "title, one_liner, description, working_principle, intervention_variable, changes_to_system, expected_effect, "
    "validation_plan 사이에서 변수와 증감 방향·수치·단위·부등호·조건이 일치하는지 확인한다. "
    "방향이 다른 변수들을 한 개의 상향/하향 동사로 묶지 않는다. 방향이 확정되지 않은 변수는 조정·탐색 대상으로 쓰고 임의로 정하지 않는다. "
    "문장들끼리 일치해도 조작의 직접 효과와 최종 성능의 인과 경로가 성립하는지 별도로 검토한다. "
    "목표·계산 예측·측정 결과를 구분하고 미검증 목표를 달성한 사실로 바꾸지 않는다."
)


def check_concept_batch(data, assigned_ids):
    """Keep each consolidated idea independent, with one explicit disposition."""
    prefix = "FATAL-S6-COVERAGE: "
    if not isinstance(data, dict) or not isinstance(data.get('concepts'), list):
        return [prefix + "concepts 배열을 반환해야 합니다."]
    if not isinstance(data.get('excluded', []), list):
        return [prefix + "excluded 배열을 반환해야 합니다."]
    issues, covered = [], set()
    for kind in ('concepts', 'excluded'):
        for row_index, row in enumerate(data.get(kind, [])):
            if not isinstance(row, dict):
                issues.append(prefix + f"{kind} 항목은 객체여야 합니다.")
                continue
            ids = row.get('source_idea_ids')
            if (not isinstance(ids, list) or not ids or
                    any(not isinstance(i, str) or not i for i in ids)):
                issues.append(prefix + f"{kind} 항목에 원본 source_idea_ids가 필요합니다.")
                continue
            if len(ids) != 1:
                issues.append(prefix + f"{kind} 항목은 통합 완료된 독립 아이디어 ID를 정확히 1개만 참조해야 합니다. "
                              "서로 다른 아이디어를 재결합하거나 한 사유로 묶어 제외하지 마세요.")
                continue
            if len(set(ids)) != len(ids) or covered.intersection(ids):
                issues.append(prefix + "하나의 배정 아이디어를 두 번 판정할 수 없습니다.")
            if set(ids) - assigned_ids:
                unexpected = json.dumps(sorted(set(ids) - assigned_ids), ensure_ascii=False)
                permitted = json.dumps(sorted(assigned_ids), ensure_ascii=False)
                issues.append(prefix + f"{kind}[{row_index}].source_idea_ids의 미배정 ID: {unexpected}. "
                              f"허용 대표 ID: {permitted}. 입력 ideas의 id만 독립 판정 대상이며, "
                              "source_idea_ids에 함께 기록된 통합 전 원안 ID는 별도 해결안으로 추가하지 마세요. "
                              "다른 후보의 ID나 과학효과를 복사해 연결하지 말고 배정 대표마다 정확히 한 번 "
                              "판정한 완전한 concepts/excluded JSON을 반환하세요.")
            covered.update(ids)
            if kind == 'concepts':
                try:
                    # Model-local IDs (often C1 in every batch) are not identities.
                    concept = ConceptSpec.model_validate({k: v for k, v in row.items() if k != 'id'})
                    if not concept.title.strip():
                        issues.append(prefix + f"아이디어 {ids[0]}: title에 비어 있지 않은 제목을 기록하세요.")
                except ValidationError as exc:
                    # Repair must see the precise field and accepted values. A
                    # generic error caused repeated, paid retries of invalid enums.
                    for error in exc.errors(include_url=False, include_input=False):
                        field = '.'.join(str(part) for part in error['loc'])
                        issues.append(prefix + f"아이디어 {ids[0]}: {field}: {error['msg']}. "
                                      "해당 필드를 수정하고 모든 배정 아이디어의 완전한 JSON을 반환하세요.")
                except (ValueError, TypeError) as exc:
                    issues.append(prefix + f"아이디어 {ids[0]}: 해결 개념 형식 오류 ({type(exc).__name__}).")
            elif not isinstance(row.get('reason'), str) or not row['reason'].strip():
                issues.append(prefix + "제외한 원본에는 구체적인 reason이 필요합니다.")
    missing = assigned_ids - covered
    if missing:
        issues.append(prefix + "판정 누락 아이디어: " + ', '.join(sorted(missing)))
    return issues


def _identity(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     default=str).encode()).hexdigest()


def normalize_concept_lineage(data, assigned, portfolio=None):
    """Keep a merged source's objection without treating it as another candidate.

    Only a unique leaf below an explicitly returned representative is eligible.
    Unknown IDs, other representatives and incomplete coverage remain errors.
    The paid response and input identities are untouched.
    """
    if not isinstance(data, dict) or not isinstance(data.get('concepts'), list) or not isinstance(data.get('excluded'), list):
        return data
    assigned_ids = {idea.id for idea in assigned}
    all_ideas = list(assigned if portfolio is None else portfolio)
    representative_ids = assigned_ids | {idea.id for idea in all_ideas}
    owners = {}
    for idea in all_ideas:
        for leaf in idea.source_idea_ids:
            owners.setdefault(leaf, set()).add(idea.id)
    counts, concepts = {}, {}
    for kind in ('concepts', 'excluded'):
        for row in data[kind]:
            ids = row.get('source_idea_ids') if isinstance(row, dict) else None
            if isinstance(ids, list) and len(ids) == 1 and isinstance(ids[0], str):
                counts[ids[0]] = counts.get(ids[0], 0) + 1
                if kind == 'concepts':
                    concepts[ids[0]] = row
    result = copy.deepcopy(data)
    moved, kept = [], []
    for row in result['excluded']:
        ids = row.get('source_idea_ids') if isinstance(row, dict) else None
        leaf = ids[0] if isinstance(ids, list) and len(ids) == 1 and isinstance(ids[0], str) else None
        parents = owners.get(leaf, set())
        parent = next(iter(parents)) if len(parents) == 1 else None
        reason = row.get('reason') if isinstance(row, dict) else None
        if (not leaf or leaf in representative_ids or counts.get(leaf) != 1 or
                parent not in assigned_ids or parent not in concepts or counts.get(parent) != 1 or
                not isinstance(reason, str) or not reason.strip()):
            kept.append(row)
            continue
        owner = next(c for c in result['concepts'] if isinstance(c, dict) and c.get('source_idea_ids') == [parent])
        risks = owner.get('open_risks', [])
        if not isinstance(risks, list) or any(not isinstance(r, str) for r in risks):
            return data
        risk = '통합 원안의 제외 의견: ' + reason
        owner['open_risks'] = list(dict.fromkeys([*risks, risk]))
        moved.append(dict(representative_id=parent, source_idea_id=leaf,
                          original_exclusion=row))
    if not moved:
        return data
    result['excluded'] = kept
    if check_concept_batch(result, assigned_ids):
        return data
    prior_notes = data.get('source_lineage_reviews') or []
    if not isinstance(prior_notes, list) or any(not isinstance(r, dict) for r in prior_notes):
        return data
    result['source_lineage_reviews'] = list({_identity(row): row for row in copy.deepcopy(prior_notes) + moved}.values())
    return result


def generate_concepts(ctx):
    from .ax.mode_contract import unified
    if unified(ctx.state):
        from .ax.incremental_review import generate
        return generate(ctx)
    return _generate_concepts(ctx)


def _concept_variables(st, assigned, facts, contradictions, prior):
    from .ax import coherence
    return {"industry": st.domain.industry, "target_system": digest.target_system(st),
        "super_system": st.domain.super_system, "operating_env": st.domain.operating_env,
        "components": digest.components_digest(st), "resources": digest.resources_digest(st),
        "facts": facts, "contradictions": contradictions,
        "ideas": [digest.idea_packet(i) for i in assigned],
        "evidence_digest": digest.relevant_evidence(st, assigned),
        "prior_cases_block": prior, "taboo_block": verify.taboo_block(st),
        "batch_size": len(assigned),
        "batch_note": "배정 항목은 이미 의미 통합한 독립 아이디어다. 모든 항목을 각각 검토하며 재결합하지 않는다. concepts와 excluded의 각 항목은 source_idea_ids에 배정 ID를 정확히 1개만 기록한다. 모든 배정 ID를 정확히 한 번 판정하고, 성립하지 않으면 해당 ID의 구체적인 reason을 기록한다. 다른 배치의 아이디어는 만들지 않는다. active_effect_ids에는 최종 작동 기구에 실제 남긴 source_details의 source_effect_id만 기록한다. 단순 노출되었거나 제거한 효과는 넣지 않는다.",
        "coherence_contract": coherence.contract_instruction(st)}


def _saved_prior_replay(st, ideas, facts, contradictions, prior_limit):
    """Reuse actual historical RAG bytes only for a usable, already-paid S6 call.

    Retrieval scores can change without any analysis input changing. Preserve
    that completed request's first batch; never pin stale cases for a new call.
    """
    from .ax import concept_effects, ledger
    from .ax.action_runtime import active_action
    from .ax.mode_contract import unified
    if not unified(st) or concept_effects.enabled(st) or active_action.get():
        return None
    from .domain import context, problem_type, physical_allowed
    from .ax.runtime import render_prompt
    from .ax.usage_recovery import stage_request_identity
    from sqlalchemy import select
    saved = [step for step in reversed(st.steps) if step.node == 's6_concept'
             and step.prompt_id == 'P_S6_CONCEPT' and step.label.startswith('해결 개념 구체화 (1/')]
    if not saved:
        return None
    with ledger.store.engine.connect() as connection:
        rows = connection.execute(select(ledger.tasks.c.result, ledger.attempts.c.details)
            .join(ledger.attempts, ledger.attempts.c.task_id == ledger.tasks.c.task_id)
            .where(ledger.tasks.c.run_id == st.run_id, ledger.tasks.c.status == 'COMPLETED',
                   ledger.tasks.c.actual.is_not(None))).all()
    completed = {}
    for result, detail in rows:
        request = json.loads(detail).get('request', {})
        if request.get('node') == 's6_concept':
            identity = stage_request_identity(request)
            if identity:
                completed[identity] = json.loads(result)
    bundle = st.scratch['ax_bundle']
    for step in saved:
        stored = step.input_slice.get('vars', {})
        prior = stored.get('prior_cases_block')
        if not isinstance(prior, str) or (prior and not prior_limit):
            continue
        size = min(len(ideas), min(5, prior_limit) if prior else 5)
        if not size or stored.get('batch_size') != size:
            continue
        assigned = ideas[:size]
        variables = _concept_variables(st, assigned, facts, contradictions, prior)
        if variables != stored:
            continue
        user = render_prompt(st, 'P_S6_CONCEPT', problem_type=problem_type(st),
            physical_scope=st.domain.physical_scope, physical_allowed=physical_allowed(st), **variables)
        user += context(st, 's6_concept')
        injected = list(st.control.injected_agents.get('s6_concept') or [])
        injected += list(st.control.injected_agents.get('stage:' + st.scratch.get('stage_key', '')) or [])
        if injected:
            user += "\n\n[추가 투입된 전문가의 관점 — 반드시 반영하라]\n" + "\n".join(
                f"- {a.get('role_name','전문가')}: {a.get('instruction','')}" for a in injected)
        system = render_prompt(st, 'P_COMMON_PREAMBLE', lang=st.control.lang,
            problem_type=problem_type(st), physical_scope=st.domain.physical_scope,
            constraints_block=verify.constraints_block(st))
        if user != step.input_slice.get('user') or system != step.input_slice.get('system'):
            continue
        request = dict(node='s6_concept', bundle_id=bundle['bundle_id'], request=dict(
            system=system, user=user, tier='T2', expect='object', temperature=None,
            max_tokens=max(4000, int(settings.cfg('solutions.concept_max_tokens', 8000))),
            model_config=bundle['models']['T2'],
            retries=max(1, int(bundle['config'].get('ax', {}).get('max_provider_attempts', 2))),
            semantic_episode_id=st.scratch['semantic_episode_id']))
        result = completed.get(stage_request_identity(request))
        if result is not None:
            data = normalize_concept_lineage(result.get('data'), assigned, st.solve.raw_ideas)
            if not check_concept_batch(data, {idea.id for idea in assigned}):
                return prior
    return None


def _generate_concepts(ctx, ideas_override=None):
    st = ctx.state
    from .idea_consolidation import ensure_consolidated
    ctx.set_stage(Stage.S6.value)
    if ideas_override is None:
        ensure_consolidated(ctx)
    from .ax import coherence
    ideas = list(st.solve.raw_ideas if ideas_override is None else ideas_override)
    assigned_ids = {idea.id for idea in ideas}
    if len(assigned_ids) != len(ideas):
        raise AbortRun("S6 원본 아이디어 ID가 중복되어 전체 검토를 시작할 수 없습니다.")
    st.scratch['ax_candidate_review'] = {
        'contract': 'idea-retention-v2', 'policy': 'full-idea-review-v1',
        'available_ideas': len(ideas), 'assigned_ideas': len(ideas), 'review_limit': None,
        'completed_ideas': 0, 'completed_idea_ids': [], 'unassigned_idea_ids': [],
        'unreviewed_idea_ids': [i.id for i in ideas],
        'source_lineage': {i.id: list(i.source_idea_ids or [i.id]) for i in ideas}}
    prior_limit = max(0, int(settings.cfg("feedback_rag.max_influenced_concepts", 3)))
    facts = digest.facts_packet(st)
    contradictions = digest.contradictions_digest(st)
    saved_prior = _saved_prior_replay(st, ideas, facts, contradictions, prior_limit)
    prior = saved_prior if saved_prior is not None else rag.prior_cases_block(st) if prior_limit else ""
    groups = []
    cursor = 0
    while cursor < len(ideas):
        size = min(5, prior_limit) if not groups and prior else 5
        groups.append(ideas[cursor:cursor + size])
        cursor += size

    def generate(item):
        number, assigned = item
        batch_prior = prior if number == 0 else ""
        ids = {i.id for i in assigned}
        result = agent.run_agent(ctx, node="s6_concept", label=f"해결 개념 구체화 ({number+1}/{len(groups)})",
            stage=Stage.S6.value, agent_id="concept_architect", prompt_id="P_S6_CONCEPT", tier="T2",
            max_tokens=max(4000,int(settings.cfg('solutions.concept_max_tokens',8000))),
            vars=_concept_variables(st, assigned, facts, contradictions, batch_prior),
            checker=lambda data: check_concept_batch(data, ids),
            normalizer=lambda data: normalize_concept_lineage(data, assigned, st.solve.raw_ideas),
            default={}) or {}
        issues = check_concept_batch(result, ids)
        from .ax import concept_effects
        if concept_effects.enabled(st):
            issues += concept_effects.check_batch(st, result)
        if issues:
            raise AbortRun("상세 검토에서 원본별 판정이 완결되지 않았습니다. " + '; '.join(issues))
        with ctx.lock:
            progress = st.scratch['ax_candidate_review']
            completed = set(progress['completed_idea_ids']) | ids
            progress['completed_idea_ids'] = [i.id for i in ideas if i.id in completed]
            progress['completed_ideas'] = len(completed)
            progress['unreviewed_idea_ids'] = [i.id for i in ideas if i.id not in completed]
        # Persist completed calls and their agent-cache keys even if a sibling fails.
        ctx.persist()
        return assigned, result, bool(batch_prior)

    made, excluded = [], []
    valid_contra = {c['id'] for c in contradictions}
    with ThreadPoolExecutor(max_workers=max(1, int(settings.cfg("run.parallel_workers", 4)))) as pool:
        results = list(pool.map(generate, enumerate(groups)))
    for assigned, data, prior_allowed in results:
        allowed = {i.id: i for i in assigned}
        lineage_records = data.get('source_lineage_reviews')
        lineage_records = lineage_records if isinstance(lineage_records, list) else []
        for raw in data['concepts']:
            # Stable IDs allow independent audit checkpoints to survive a resumed
            # generation stage that reuses its completed model calls.
            payload = {key: value for key, value in raw.items() if key != 'id'}
            c = ConceptSpec.model_validate(dict(payload, id='CPT-S6-' + _identity([
                st.run_id, sorted(payload['source_idea_ids']), payload])[:16]))
            source_ids = set(c.source_idea_ids)
            sources = [allowed[i] for i in sorted(source_ids)]
            def effect_ids(value):
                if isinstance(value,dict):
                    return ({value['source_effect_id']} if value.get('source_effect_id') else set()).union(*(effect_ids(v) for v in value.values()))
                return set().union(*(effect_ids(v) for v in value)) if isinstance(value,list) else set()
            source_effects = set().union(*(effect_ids(i.detail) for i in sources))
            from .ax import concept_effects
            if concept_effects.enabled(st):
                # Strict validation above rejects invalid attribution rather
                # than silently changing the model's explicit adoption claim.
                c.active_effect_ids = sorted(c.active_effect_ids)
            else:
                c.active_effect_ids = sorted(set(c.active_effect_ids) & source_effects)
            key = tuple(sorted(i.mechanism_key or i.id for i in sources))
            c.mechanism_key = " + ".join(key)
            if coherence.enabled(st):
                st.scratch.setdefault('ax_mechanisms', {})[c.id] = raw.get('coherence')
            c.quality_status = "UNVERIFIED"  # generator cannot approve itself
            c.assumptions = list(dict.fromkeys(c.assumptions + [condition for i in sources for condition in i.conditions]))
            c.hypothesis_ids = list(dict.fromkeys(c.hypothesis_ids + [h for i in sources for h in i.hypothesis_ids]))
            c.addresses_contradictions = [i for i in c.addresses_contradictions if i in valid_contra]
            c.evidence_ids = [i for i in c.evidence_ids if any(e.id == i for e in st.evidence)]
            # Search metadata supplied during generation does not establish maturity.
            if not c.evidence_ids:
                c.maturity = "CONCEPT"
            if not prior_allowed:
                c.prior_case_ids = []
            elif not c.prior_case_ids:
                c.prior_case_ids = list(st.scratch.get("prior_case_ids", []))
            else:
                c.prior_case_ids = [i for i in c.prior_case_ids if i in st.scratch.get("prior_case_ids", [])]
            made.append(c)
            lineage_notes = [r for r in lineage_records
                             if isinstance(r, dict) and r.get('representative_id') in c.source_idea_ids]
            if lineage_notes:
                st.scratch.setdefault('s6_lineage_reviews', {})[c.id] = copy.deepcopy(lineage_notes)
            review_inputs=st.scratch.get('review_inputs',{})
            refs=[review_inputs[i] for i in c.source_idea_ids if i in review_inputs]
            if refs:
                st.scratch.setdefault('candidate_review_revisions',{})[c.id]=dict(refs[0])
        excluded.extend(dict(row, idea=row.get('idea') or ' / '.join(
            allowed[i].title for i in row['source_idea_ids'])) for row in data.get('excluded', []))
    if len({c.id for c in made}) != len(made):
        raise AbortRun("상세 검토 결과의 해결 개념 ID가 중복되었습니다.")
    st.concepts = made
    st.scratch["excluded_concepts"] = excluded
    generated_count=len(st.concepts)
    audit_concepts(ctx)
    st.scratch.setdefault('ax_portfolio_trace',[]).append({'stage':'concepts',
        'policy': 'full-idea-review-v1',
        'available_ideas':len(st.solve.raw_ideas),'assigned_ideas':len(ideas),
        'generated_count':generated_count,'retained_after_audit':len(st.concepts),
        'excluded_count':len(st.scratch.get('excluded_concepts',[]))})
    ctx.emit("artifact", kind="CONCEPTS", data={"count": len(st.concepts), "titles": [c.title for c in st.concepts]})
    ctx.persist()


def audit_concepts(ctx):
    st = ctx.state
    if not st.concepts:
        return
    sources = {idea.id: idea for idea in st.solve.raw_ideas}
    packets = [{"concept_id": c.id, "title": c.title, "one_liner": c.one_liner,
        "description": c.description, "intervention_variable": c.intervention_variable,
        "source_idea_ids": c.source_idea_ids, "working_principle": c.working_principle,
        "source_proposals": [{field: getattr(sources[sid], field) for field in (
            'id', 'idea', 'mechanism', 'intervention_variable', 'conditions', 'strongest_objection', 'validation_test')}
            for sid in c.source_idea_ids if sid in sources],
        "changes_to_system": c.changes_to_system, "required_resources": c.required_resources,
        "addresses_contradictions": c.addresses_contradictions, "resolution_argument": c.resolution_argument,
        "expected_effect": c.expected_effect, "assumptions": c.assumptions, "open_risks": c.open_risks,
        "validation_plan": c.validation_plan, "transfer_conditions": c.transfer_conditions} for c in st.concepts]
    from .ax import coherence
    coherence_checks = {}
    if coherence.enabled(st):
        coherence_checks = {c.id: coherence.candidate_check(st,c) for c in st.concepts}
        for packet in packets:
            packet['coherence'] = coherence_checks[packet['concept_id']]
    instruction = (
        "후보별 판단을 per_concept에 반드시 기록한다. 개입→매개 기능→결과의 물리적 타당성, 원래 모순 양측, "
        "조건의 적용 범위와 원인 가설을 독립 검토한다. 경로 문자열의 존재는 타당성 증명이 아니다. "
        "미실험은 설계 불성립과 구분한다. 능동 구동 누락은 수동/진단안에 적용하지 않는다." if coherence.enabled(st)
        else "후보별 판단을 per_concept에 반드시 기록한다.")
    instruction += ("\n" + PARAMETER_DIRECTION_INSTRUCTION +
        " source_proposals는 원안의 주장이지 관측 사실이나 정답이 아니다. 원안과 개념의 방향 차이도 조건·인과 근거로 검토한다. "
        " 명시적인 방향 충돌이나 근거 없는 달성 단정은 해당 후보의 issues에 필드명·변수·문제 표현과 필요한 수정을 기록하고 "
        "전역 점수와 관계없이 해당 후보를 최소 REVISE로 판정한다. 성립 불가능 또는 필수 제약 위반이 명확할 때만 fatal_flaws로 구분한다. "
        "서로 다른 조건에서 상반 방향이 필요한 설계는 조건이 명시되어 있으면 그 자체로 결함이 아니다. "
        "근거가 부족하면 미확정으로 남기고 올바른 방향이나 수치를 지어내지 않는다.")
    from . import domain, prompts_registry
    prompt = st.scratch.get('ax_bundle', {}).get('prompts', {}).get(
        'P_VERIFIER_GENERIC', prompts_registry.raw('P_VERIFIER_GENERIC'))
    from .ax import enabled as ax_enabled
    if ax_enabled(st):
        model = copy.deepcopy(st.scratch['ax_bundle']['models']['T3'])
    else:
        model = {key: getattr(settings.tiers['T3'], key) for key in (
            'model', 'base_url', 'temperature', 'max_tokens', 'json_mode',
            'supports_temperature', 'token_parameter', 'thinking_mode')}
    identity = {'contract': 's6-audit-batches-v3-directions', 'facts': digest.facts_packet(st),
                'causal': digest.causal_packet(st), 'contradictions': digest.contradictions_digest(st),
                'constraints': verify.constraints_block(st), 'problem_type': domain.problem_type(st),
                'rubric': settings.rubric('R6_CONCEPT'), 'policy': settings.cfg('verification', {}),
                'model': model,
                'prompt': prompt, 'instruction': instruction}
    if st.scratch.get('review_inputs'):
        identity.update(review_contract='current-review-projection-v2',
            evidence=[e.model_dump(mode='json') for e in st.evidence])
    groups, group, length = [], [], 0
    for packet in packets:
        size = len(json.dumps(packet, ensure_ascii=False, default=str))
        if group and (len(group) >= 5 or length + size > 18000):
            groups.append(group)
            group, length = [], 0
        group.append(packet)
        length += size
    if group:
        groups.append(group)
    cache = st.scratch.setdefault('s6_quality_batches', {})
    all_verdicts, audited, review_steps = {}, [], {}
    progress = st.scratch.get('ax_candidate_review')
    if progress and progress.get('contract') == 'idea-retention-v2':
        progress.update(audit_completed_concept_ids=[], audit_unreviewed_concept_ids=[c.id for c in st.concepts])
    for number, batch in enumerate(groups, 1):
        key = _identity([identity, batch])
        step = ctx.start_step(node='s6_quality', label=f'독립 품질 검토 ({number}/{len(groups)})',
            stage=Stage.S6.value, agent_id='independent_auditor', prompt_id='P_VERIFIER_GENERIC', tier='T3')
        step.input_slice = {'concepts': batch, 'facts': identity['facts'], 'input_hash': key,
                            'audit_contract': identity['contract'], 'review_instruction': instruction}
        reused = key in cache
        try:
            verdict = copy.deepcopy(cache[key]) if reused else agent.verify_artifact(
                ctx, 'R6_CONCEPT', {'concepts': batch}, instruction)
        except Exception as exc:
            step.error = str(exc)
            ctx.finish_step(step, 'FAILED')
            ctx.persist()
            raise
        if not isinstance(verdict, dict):
            verdict = {'verdict': 'UNVERIFIED', 'per_concept': []}
        if verdict.get('verdict') not in ('PASS', 'REVISE', 'REJECT', 'UNVERIFIED'):
            verdict = dict(verdict, verdict='UNVERIFIED')
        usage = verdict.pop('_tokens', None)
        if usage:
            step.tokens_in, step.tokens_out, step.cost_usd = usage
        rows = verdict.get('per_concept')
        rows = rows if isinstance(rows, list) else []
        ids = {p['concept_id'] for p in batch}
        row_ids = [r.get('concept_id') for r in rows if isinstance(r, dict)]
        malformed = (len(row_ids) != len(rows) or any(not isinstance(i, str) for i in row_ids) or
                     len(set(row_ids)) != len(row_ids) or bool(set(row_ids) - ids))
        if malformed:
            verdict = dict(verdict, verdict='UNVERIFIED', per_concept=[],
                           coverage_issue='독립 검토의 후보 ID가 중복되거나 배정과 일치하지 않습니다.')
            rows, row_ids = [], []
        localized_fatal = any(r.get('fatal_flaws') or r.get('verdict') == 'REJECT' for r in rows)
        unlocated_fatal = bool(verdict.get('fatal_flaws')) and not localized_fatal
        complete = (not unlocated_fatal and set(row_ids) == ids and verdict.get('verdict') in ('PASS', 'REVISE', 'REJECT') and
                    all(r.get('verdict') in ('PASS', 'REVISE', 'REJECT') for r in rows))
        if complete:
            cache[key] = copy.deepcopy(verdict)
        else:
            cache.pop(key, None)
        by_id = {r['concept_id']: r for r in rows}
        for cid in ids:
            all_verdicts[cid] = (verdict, by_id.get(cid, {}), localized_fatal)
            review_steps[cid] = step.step_id
        if not unlocated_fatal and verdict.get('verdict') in ('PASS', 'REVISE', 'REJECT'):
            audited.extend(cid for cid in row_ids if by_id[cid].get('verdict') in ('PASS', 'REVISE', 'REJECT'))
        if progress and progress.get('contract') == 'idea-retention-v2':
            progress['audit_completed_concept_ids'] = list(audited)
            progress['audit_unreviewed_concept_ids'] = [c.id for c in st.concepts if c.id not in audited]
        step.output_json = verdict
        step.verdicts = [verdict]
        from .ax.feedback_events import model_review
        for row in rows:
            candidate = st.concept(row.get('concept_id'))
            if candidate:
                model_review(st, candidate, row, stage='s6_quality', step_id=step.step_id,
                             rubric=identity['rubric'], model=identity['model'])
        ctx.finish_step(step, 'SKIPPED' if reused and complete else
                        'OK' if complete and verdict.get('verdict') == 'PASS' else 'WARN')
        ctx.persist()
    retained = []
    for c in st.concepts:
        verdict, row, localized_fatal = all_verdicts[c.id]
        status = row.get("verdict", "UNVERIFIED")
        if status not in ("PASS", "REVISE", "REJECT"):
            status = "UNVERIFIED"
        if verdict.get("verdict") == "UNVERIFIED":
            status = "UNVERIFIED"
        issues = row.get("issues") or []
        if not isinstance(issues, list):
            issues = [issues]
        if not row or status == 'UNVERIFIED':
            issues.append(verdict.get('coverage_issue') or '독립 품질 검토의 후보별 판정이 없어 미검증 상태입니다.')
        if row.get("fatal_flaws"):
            status = "REJECT"
            flaws = row["fatal_flaws"]
            issues += flaws if isinstance(flaws, list) else [flaws]
        # An unlocated portfolio-level flaw cannot approve or reject an individual
        # candidate. Preserve it as unverified until the auditor identifies it.
        if verdict.get("fatal_flaws") and not localized_fatal:
            flaws = verdict["fatal_flaws"]
            status = 'UNVERIFIED'
            issues += (flaws if isinstance(flaws, list) else [flaws]) + ['전체 지적의 해당 후보가 명시되지 않아 후보별 검토가 필요합니다.']
        c.quality_status, c.quality_issues = status, [str(i) for i in issues]
        structural = coherence_checks.get(c.id, {}).get('gaps', [])
        if structural:
            if c.quality_status not in ('REJECT', 'UNVERIFIED'):
                c.quality_status = 'REVISE'
            c.quality_issues.extend(g['description'] for g in structural)
        if not c.resolution_argument or not c.validation_plan or not c.addresses_contradictions:
            if c.quality_status not in ('REJECT', 'UNVERIFIED'):
                c.quality_status = "REVISE"
            c.quality_issues.append("모순 해소 근거·대상 모순·검증 계획을 모두 명시해야 한다.")
        known = {verify._norm_resource(r.name) for r in st.analysis.resources if r.name}
        for name in c.required_resources:
            normalized = verify._norm_resource(name)
            if name and not name.startswith("신규:") and normalized not in known:
                if c.quality_status not in ('REJECT', 'UNVERIFIED'):
                    c.quality_status = "REVISE"
                c.quality_issues.append(f"기존 자원 확인 또는 신규 도입 표시 필요: {name}")
        from .ax.feedback_events import coverage_review
        coverage_review(st,c,review_steps[c.id],coherence_checks.get(c.id,{}))
        if c.quality_status == "REJECT":
            from .ax.mode_contract import unified
            if unified(st):
                from .ax.candidate_disposition import record
                record(st,c,'QUALITY_REJECT',list(c.quality_issues),review_steps[c.id])
            from .ax import enabled as ax_enabled
            if ax_enabled(st):
                st.scratch.setdefault('ax_excluded', []).append(c.model_dump(mode='json'))
            st.scratch.setdefault("excluded_concepts", []).append({"idea": c.title,
                "source_idea_ids": list(c.source_idea_ids),
                "reason": "; ".join(c.quality_issues) or "독립 품질 검토 REJECT"})
        else:
            retained.append(c)
    st.concepts = retained
    ctx.persist()
