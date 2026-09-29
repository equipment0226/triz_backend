"""Offline MCP contract checks: no model/provider or production services are used."""
import asyncio
import copy
import inspect
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from triz import agent, knowledge as K, pipeline, store
from triz import separation_contract as SC
from triz.ax import WORKFLOW
from triz.context import AbortRun
from triz.execution_config import profile
from triz.settings import settings


KINDS = {'SPACE', 'TIME', 'CONDITION', 'DIRECTION', 'SYSTEM_LEVEL', 'SATISFY', 'BYPASS'}
REQUIRED = {'element', 'parameter', 'state_a', 'reason_a', 'state_b', 'reason_b',
            'scale', 'target_system', 'resources', 'su_fields', 'separation_block'}
# Actual pre-patch prompt and rubric, kept inside this fixture so old AX pins do
# not accidentally combine today's seven-kind instructions with a four-kind pin.
LEGACY_PROMPT = '''당신은 물리적 모순을 분리 원리(Separation Principles)로 해소하는 TRIZ 마스터다.

[물리적 모순]
 요소: {{element}} / 파라미터: {{parameter}}
 상태 A: {{state_a}} (필요 이유: {{reason_a}})
 상태 B: {{state_b}} (필요 이유: {{reason_b}})
 규모: {{scale}}
[대상 시스템] {{target_system}}
[가용 자원] {{resources}}
[물질-장] {{su_fields}}

[4대 분리 원리 — 모두 검토하라. 건너뛰지 마라]
{{separation_block}}

각 분리 원리에 대해:
- kind: TIME | SPACE | CONDITION | SYSTEM_LEVEL
- applicable: true/false. false면 not_applicable_reason에 물리적·논리적 사유를 명시(귀찮아서 금지).
- how: 무엇을 기준으로 어떻게 분리하는지. 분리 축을 명확히 하라
  (시간축이면 어느 구간, 공간축이면 어느 부위, 조건축이면 어떤 임계값).
- title: 25자 이내 명칭
- idea: 대상 시스템에 적용한 구체안 2~4문장. 가용 자원을 활용할 것.
- supporting_principles: 실제로 사용한 발명원리 번호 목록

[추가 지시]
- 물질-장 모델이 실제 제공된 물리 문제에서만 S2/Field 변경을 검토한다. 조직 문제의 분리 축은 의사결정 시점·역할·상황·권한 범위로 정의한다.
  예) 기계적 접촉 지지 → 자기장/공기압 지지로 전환하면 공간·조건 분리가 동시에 성립
- 적용 가능한 원리가 2개 미만이면 물리적 모순의 정의가 잘못되었을 가능성을 redefine_hint에 적어라.

[출력 JSON]
{"applications":[{"kind":"TIME","applicable":true,"not_applicable_reason":"","how":"","title":"","idea":"","supporting_principles":[]}],
 "redefine_hint":""}

[후속 단계에 보존할 근거]
각 applications 또는 ideas 원소에 mechanism(인과 경로), mechanism_key(개입 변수+작동 방식), intervention_variable, conditions(필요 조건 배열), strongest_objection(가장 강한 반박), validation_test(반증할 관측), hypothesis_ids를 추가한다. 각 설명은 1문장 이내. 모르는 조건은 미확인이라고 표시한다. 원래 손실을 다른 사람·시점으로 전가한 것을 해결로 포장하지 않는다.
'''
LEGACY_RUBRIC = {
    'description': '분리 원리 적용의 완결성',
    'criteria': [
        {'id': 'C1', 'weight': .40, 'text': '시간/공간/조건/시스템수준 4가지를 모두 검토했는가(미적용은 물리적 사유가 있는가)'},
        {'id': 'C2', 'weight': .35, 'text': '분리 축(무엇을 기준으로 나누는가)이 명확한가'},
        {'id': 'C3', 'weight': .25, 'text': '아이디어가 물리적 모순을 실제로 해소하는가(절충이 아닌가)'},
    ],
}


def tool(name='triz_s5_track_b'):
    from triz import mcp_server
    registered = mcp_server.mcp._tool_manager.get_tool(name)
    assert registered is not None
    return registered


def invoke(state, variables=None):
    return tool().fn.__wrapped__(state.run_id, variables or inputs())


def audit(state, artifact, rubric='R5_B', facts='actual supplied facts'):
    return tool('triz_verify_artifact').fn.__wrapped__(state.run_id, rubric, artifact, facts)


def inputs():
    return dict(element='support', parameter='stiffness', state_a='rigid', reason_a='insertion',
        state_b='flexible', reason_b='operation', scale='component', target_system='electrode',
        resources=['existing body'], su_fields=[], separation_block='UNTRUSTED FOUR-ONLY BLOCK')


def answer(catalog=None, *, applicable=False):
    catalog = K.separation() if catalog is None else catalog
    apps = [dict(kind=kind, applicable=False, not_applicable_reason='Unconfirmed operating conditions',
        how='', title='', idea='', supporting_principles=[]) for kind in catalog]
    if applicable:
        app = next(a for a in apps if a['kind'] == 'TIME')
        app.update(applicable=True, not_applicable_reason='', how='Change support after insertion',
                   title='Temporary support', idea='Remove temporary support after insertion',
                   supporting_principles=[34])
    return {'applications': apps, 'redefine_hint': 'Retain uncertainty; do not invent feasible options'}


@pytest.fixture
def ax_state():
    return pipeline.create_run('Rigid during insertion and flexible during operation',
                               mode='FULL', workflow_version=WORKFLOW)


@pytest.fixture
def legacy_state(ax_state):
    bundle = ax_state.scratch['ax_bundle']
    bundle.pop('separation_catalog')
    bundle['prompts']['P_S5_TRACK_B'] = LEGACY_PROMPT
    bundle['rubrics']['R5_B'] = copy.deepcopy(LEGACY_RUBRIC)
    store.save_state(ax_state)
    return ax_state


@pytest.fixture
def persistence_trace(monkeypatch):
    original_lock, original_save = store.run_lock, store.save_state
    trace, held = [], []

    @contextmanager
    def locked(run_id):
        with original_lock(run_id):
            held.append(run_id)
            trace.append('lock')
            try:
                yield
            finally:
                assert held.pop() == run_id
                trace.append('unlock')

    def save(state):
        assert state.run_id in held
        trace.append('save')
        return original_save(state)

    monkeypatch.setattr(store, 'run_lock', locked)
    monkeypatch.setattr(store, 'save_state', save)
    return trace


def test_direct_tool_schema_and_required_variables_are_unchanged():
    registered = tool()
    assert set(registered.parameters['properties']) == {'run_id', 'variables'}
    assert set(registered.parameters['required']) == {'run_id', 'variables'}
    assert list(inspect.signature(registered.fn).parameters) == ['run_id', 'variables']
    assert 'Required variables: ' + ', '.join(sorted(REQUIRED)) + '.' in registered.description


def test_missing_template_input_fails_before_agent_or_state_save(state, monkeypatch, persistence_trace):
    variables = inputs()
    variables.pop('state_a')
    provider = Mock(side_effect=AssertionError('Must reject missing input first'))
    monkeypatch.setattr(agent, 'run_agent', provider)
    with pytest.raises(ValueError, match='state_a'):
        invoke(state, variables)
    assert not provider.called and persistence_trace == []


def test_new_direct_tool_canonicalizes_without_mutating_inputs_or_workflow(state, monkeypatch, persistence_trace):
    variables = inputs()
    raw = answer(applicable=True)
    raw['applications'][0].update(source_pc_id='forged-pc', approach_name='forged catalog name')
    originals = copy.deepcopy((variables, raw))
    before = state.model_dump(mode='json')
    provider = Mock(return_value=raw)
    monkeypatch.setattr(agent, 'run_agent', provider)
    result = asyncio.run(tool().run(arguments={'run_id': state.run_id, 'variables': variables}))
    assert set(result) == {'artifact', 'run_id'} and result['run_id'] == state.run_id
    assert provider.call_count == 1
    kwargs = provider.call_args.kwargs
    assert kwargs['vars']['separation_block'] == K.separation_block()
    assert 'UNTRUSTED FOUR' not in kwargs['vars']['separation_block']
    assert kwargs['rubric_id'] == 'R5_B' and kwargs['agent_id'] == 'mcp::s5_track_b'
    assert callable(kwargs['checker']) and callable(kwargs['normalizer'])
    assert kwargs['checker'](kwargs['normalizer'](raw)) == []
    assert result['artifact'] == SC.normalize(raw)
    assert all('source_pc_id' not in row for row in result['artifact']['applications'])
    assert set(row['kind'] for row in result['artifact']['applications']) == KINDS
    assert (variables, raw) == originals
    saved = store.load_state(state.run_id).model_dump(mode='json')
    for field in ('analysis', 'definition', 'solve', 'control', 'status'):
        assert saved[field] == before[field]
    assert persistence_trace == ['lock', 'save', 'unlock']


def test_all_seven_inapplicable_is_valid_without_forcing_ideas(state, monkeypatch):
    provider = Mock(return_value=answer())
    monkeypatch.setattr(agent, 'run_agent', provider)
    result = invoke(state)['artifact']
    assert all(row['applicable'] is False for row in result['applications'])
    assert result['redefine_hint'] == answer()['redefine_hint']
    assert len(result['applications']) == 7 and provider.call_count == 1


@pytest.mark.parametrize('bad', ['empty', 'missing', 'string_bool', 'duplicate_alias', 'invalid_principle', 'wrong_axis'])
def test_invalid_result_is_rejected_even_if_mock_agent_skips_checker(state, monkeypatch, persistence_trace, bad):
    raw = answer(applicable=True)
    if bad == 'empty':
        raw = {}
    elif bad == 'missing':
        raw['applications'].pop()
    elif bad == 'string_bool':
        raw['applications'][0]['applicable'] = 'false'
    elif bad == 'duplicate_alias':
        raw['applications'].append(dict(next(a for a in raw['applications'] if a['kind'] == 'CONDITION'), kind='RELATION'))
    elif bad == 'invalid_principle':
        raw['applications'][0]['supporting_principles'] = [True]
    elif bad == 'wrong_axis':
        raw['applications'][0]['kind'] = 'PRESSURE'
    provider = Mock(return_value=raw)
    monkeypatch.setattr(agent, 'run_agent', provider)
    with pytest.raises(AbortRun, match='FATAL-SEPARATION'):
        invoke(state)
    assert provider.call_count == 1
    assert store.load_state(state.run_id).solve == state.solve
    assert persistence_trace == ['lock', 'save', 'unlock']


@pytest.mark.parametrize('legacy', [False, True])
def test_ax_direct_call_uses_pinned_catalog_prompt_and_rubric_then_resets_profile(request, monkeypatch, legacy):
    state = request.getfixturevalue('legacy_state' if legacy else 'ax_state')
    before_bundle = copy.deepcopy(state.scratch['ax_bundle'])
    catalog = SC.catalog_for(state)
    observed = []

    def run(ctx, **kwargs):
        from triz.ax.runtime import render_prompt
        observed.append(copy.deepcopy(profile.get()))
        assert kwargs['vars']['separation_block'] == K.separation_block(catalog=catalog)
        rendered = render_prompt(ctx.state, 'P_S5_TRACK_B', **kwargs['vars'])
        if legacy:
            assert '4대 분리 원리' in rendered
            assert settings.rubric('R5_B')['description'] == LEGACY_RUBRIC['description']
        else:
            assert 'SATISFY' in rendered and 'BYPASS' in rendered
        return answer(catalog)

    monkeypatch.setattr(agent, 'run_agent', run)
    ambient = {'foreign-profile': True}
    token = profile.set(ambient)
    try:
        result = invoke(state)['artifact']
        assert profile.get() is ambient
    finally:
        profile.reset(token)
    assert observed == [before_bundle]
    assert store.load_state(state.run_id).scratch['ax_bundle'] == before_bundle
    assert len(result['applications']) == (4 if legacy else 7)
    assert all(a['catalog_version'] == SC.LEGACY_VERSION for a in result['applications']) == legacy
    assert all('source_pc_id' not in a for a in result['applications'])


def test_non_ax_clears_ambient_and_stale_bundle_only_for_this_call(state, monkeypatch):
    state.scratch['ax_bundle'] = {'prompts': {'P_S5_TRACK_B': LEGACY_PROMPT}}
    store.save_state(state)
    observed = []

    def run(*args, **kwargs):
        observed.append(profile.get())
        return answer()

    monkeypatch.setattr(agent, 'run_agent', run)
    ambient = {'foreign-profile': True}
    token = profile.set(ambient)
    try:
        assert len(invoke(state)['artifact']['applications']) == 7
        assert observed == [None] and profile.get() is ambient
    finally:
        profile.reset(token)


@pytest.mark.parametrize('failure', ['model', 'postcheck', 'save'])
def test_profile_is_restored_on_every_direct_exit(ax_state, monkeypatch, failure):
    provider = Mock(side_effect=RuntimeError('synthetic model failure')) if failure == 'model' else Mock(return_value={} if failure == 'postcheck' else answer())
    monkeypatch.setattr(agent, 'run_agent', provider)
    if failure == 'save':
        monkeypatch.setattr(store, 'save_state', Mock(side_effect=RuntimeError('synthetic save failure')))
    ambient = {'foreign-profile': True}
    token = profile.set(ambient)
    try:
        with pytest.raises(AbortRun if failure == 'postcheck' else RuntimeError):
            invoke(ax_state)
        assert profile.get() is ambient
    finally:
        profile.reset(token)


@pytest.mark.parametrize('corruption', ['missing_bundle', 'empty_catalog', 'incomplete_catalog'])
def test_corrupt_ax_pin_never_downgrades_to_new_or_legacy_default(ax_state, monkeypatch, corruption):
    if corruption == 'missing_bundle':
        ax_state.scratch.pop('ax_bundle')
    elif corruption == 'empty_catalog':
        ax_state.scratch['ax_bundle']['separation_catalog'] = {}
    else:
        ax_state.scratch['ax_bundle']['separation_catalog'].pop('DIRECTION')
    store.save_state(ax_state)
    provider = Mock(side_effect=AssertionError('Bad execution pin must fail before agent'))
    monkeypatch.setattr(agent, 'run_agent', provider)
    with pytest.raises(ValueError, match='separation'):
        invoke(ax_state)
    assert not provider.called


def test_current_pin_rejects_old_four_kind_response(ax_state, monkeypatch):
    monkeypatch.setattr(agent, 'run_agent', Mock(return_value=answer(SC.legacy_catalog())))
    with pytest.raises(AbortRun, match='DIRECTION'):
        invoke(ax_state)


@pytest.mark.parametrize('needs_repair', [False, True])
def test_real_agent_path_checks_repairs_and_archives_without_optional_auditor_call(state, monkeypatch, needs_repair):
    monkeypatch.setitem(settings.triz['verification'], 'critical_rubrics', ['R3_CECA'])
    monkeypatch.setitem(settings.triz['verification'], 'max_repair_attempts', 1)
    def response(data):
        return SimpleNamespace(data=data, text='', tokens_in=10, tokens_out=5,
                               cost_usd=.001, model='offline-synthetic', meta={})
    outputs = ([response({})] if needs_repair else []) + [response(answer(applicable=True))]
    provider = Mock(side_effect=outputs)
    monkeypatch.setattr(agent, 'tracked_chat', provider)
    result = invoke(state)['artifact']
    assert result == SC.normalize(answer(applicable=True))
    assert provider.call_count == (2 if needs_repair else 1)
    assert all(call.kwargs.get('_node') == 's5_track_b' for call in provider.call_args_list)
    steps = store.list_steps(state.run_id)
    assert len(steps) == 1 and steps[0]['node'] == 's5_track_b'
    step = store.get_step(state.run_id, steps[0]['step_id'])
    assert step['output_json'] == result and step['status'] == 'WARN'
    assert step['verdicts'][-1]['source'] == 'policy'
    assert step['verify_attempts'] == (2 if needs_repair else 1)
    assert store.load_state(state.run_id).solve == state.solve
    if needs_repair:
        assert step['verdicts'][0]['source'] == 'deterministic'
        assert 'FATAL-SEPARATION' in provider.call_args_list[1].kwargs['user']


@pytest.mark.parametrize('failure', ['model', 'save'])
def test_r5_b_audit_restores_profile_even_if_verifier_or_persistence_raises(ax_state, monkeypatch, failure):
    verifier = Mock(side_effect=RuntimeError('synthetic verifier failure')) if failure == 'model' else Mock(return_value={'verdict': 'PASS'})
    monkeypatch.setattr(agent, 'verify_artifact', verifier)
    if failure == 'save':
        monkeypatch.setattr(store, 'save_state', Mock(side_effect=RuntimeError('synthetic save failure')))
    ambient = {'foreign-profile': True}
    token = profile.set(ambient)
    try:
        with pytest.raises(RuntimeError):
            audit(ax_state, answer())
        assert profile.get() is ambient
    finally:
        profile.reset(token)


@pytest.mark.parametrize('artifact', [{}, {'applications': []}, {'applications': 'invalid'}, None])
def test_r5_b_malformed_audit_is_rejected_before_model(state, monkeypatch, persistence_trace, artifact):
    raw = copy.deepcopy(artifact)
    verifier = Mock(side_effect=AssertionError('Malformed artifact cannot receive an LLM PASS'))
    monkeypatch.setattr(agent, 'verify_artifact', verifier)
    result = audit(state, artifact)
    assert result['verdict'] == 'REJECT' and result['score'] == 0.0
    assert result['source'] == 'deterministic' and result['fatal_flaws']
    assert result['revision_instructions'] == result['fatal_flaws']
    assert artifact == raw and not verifier.called
    assert persistence_trace == ['lock', 'save', 'unlock']


def test_r5_b_valid_audit_normalizes_and_delegates_existing_verdict(ax_state, monkeypatch, persistence_trace):
    raw = answer(applicable=True)
    raw['applications'][0]['source_pc_id'] = 'forged-pc'
    before = copy.deepcopy(raw)
    verdict = {'verdict': 'REVISE', 'score': .6, 'revision_instructions': ['Confirm timing']}
    seen = []

    def verify(ctx, rubric, data, facts):
        seen.append(copy.deepcopy(profile.get()))
        assert rubric == 'R5_B' and facts == 'actual supplied facts'
        assert data == SC.normalize(raw, catalog=SC.catalog_for(ctx.state))
        return verdict

    monkeypatch.setattr(agent, 'verify_artifact', verify)
    result = audit(ax_state, raw)
    assert result is verdict and raw == before
    assert seen == [ax_state.scratch['ax_bundle']] and profile.get() is None
    assert persistence_trace == ['lock', 'save', 'unlock']


def test_r5_b_valid_legacy_audit_uses_old_rubric_without_fabricated_extra_reviews(legacy_state, monkeypatch):
    raw = answer(SC.legacy_catalog())

    def verify(ctx, rubric, data, facts):
        assert profile.get()['prompts']['P_S5_TRACK_B'] == LEGACY_PROMPT
        assert settings.rubric(rubric)['description'] == LEGACY_RUBRIC['description']
        assert len(data['applications']) == 4
        assert {a['catalog_version'] for a in data['applications']} == {SC.LEGACY_VERSION}
        return {'verdict': 'UNVERIFIED', 'score': 0.0, 'source': 'policy'}

    monkeypatch.setattr(agent, 'verify_artifact', verify)
    assert audit(legacy_state, raw)['source'] == 'policy'


@pytest.mark.parametrize('enabled, critical', [(False, ['R5_B']), (True, ['R3_CECA'])])
def test_r5_b_valid_audit_preserves_existing_no_extra_llm_policy(ax_state, monkeypatch, enabled, critical):
    ax_state.scratch['ax_bundle']['config']['verification'].update(enabled=enabled, critical_rubrics=critical)
    store.save_state(ax_state)
    provider = Mock(side_effect=AssertionError('Optional rubric must not add model calls'))
    monkeypatch.setattr(agent, 'tracked_chat', provider)
    result = audit(ax_state, answer())
    assert result['verdict'] == 'UNVERIFIED' and result['skipped'] is True
    assert not provider.called


def test_r5_b_explicitly_enabled_audit_uses_pinned_rubric_and_one_existing_t3_call(ax_state, monkeypatch):
    config = ax_state.scratch['ax_bundle']['config']['verification']
    config.update(enabled=True, critical_rubrics=['R5_B'])
    ax_state.scratch['ax_bundle']['rubrics']['R5_B']['description'] = 'PINNED SEVEN APPROACH RUBRIC'
    store.save_state(ax_state)
    provider = Mock(return_value=SimpleNamespace(data={'verdict': 'PASS', 'score': .91},
        tokens_in=10, tokens_out=5, cost_usd=.001, meta={}))
    monkeypatch.setattr(agent, 'tracked_chat', provider)
    result = audit(ax_state, answer())
    assert result['verdict'] == 'PASS' and result['rubric'] == 'R5_B'
    assert provider.call_count == 1
    assert provider.call_args.kwargs['tier'] == 'T3'
    assert 'PINNED SEVEN APPROACH RUBRIC' in provider.call_args.kwargs['user']


def test_non_b_rubric_retains_existing_path_and_unmodified_artifact(state, monkeypatch):
    raw = {'arbitrary_existing_artifact': ['no separation rows']}
    verdict = {'verdict': 'REVISE', 'score': .5}
    verifier = Mock(return_value=verdict)
    monkeypatch.setattr(agent, 'verify_artifact', verifier)
    monkeypatch.setattr(SC, 'catalog_for', Mock(side_effect=AssertionError('Unrelated rubric must be unchanged')))
    assert audit(state, raw, rubric='R3_CECA') is verdict
    assert verifier.call_count == 1 and verifier.call_args.args[2] is raw


def test_execute_stage_delegates_exactly_as_before(monkeypatch):
    result = {'status': 'WAITING', 'stage': 's5_solve'}
    execute = Mock(return_value=result)
    monkeypatch.setattr(pipeline, 'execute_stage', execute)
    monkeypatch.setattr(SC, 'catalog_for', Mock(side_effect=AssertionError('Stage endpoint must remain unchanged')))
    assert tool('triz_execute_stage').fn.__wrapped__('stored-run', 7, 42) is result
    execute.assert_called_once_with('stored-run', 7, 42)
