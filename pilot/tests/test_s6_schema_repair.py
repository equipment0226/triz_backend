"""Regressions for production S6 classification failures, without paid calls."""
import copy
from types import SimpleNamespace
import pytest
from triz import prompts_registry, quality
from triz.schema import ConceptSpec


@pytest.mark.parametrize('field,value,allowed', [
    ('novelty_class', 'ADAPTATION', ('SAME_DOMAIN', 'CROSS_DOMAIN', 'NEW')),
    ('novelty_class', 'DERIVATIVE', ('SAME_DOMAIN', 'CROSS_DOMAIN', 'NEW')),
    ('change_scale', 'SUBSYSTEM', ('PARAMETER', 'PARTIAL', 'REDESIGN')),
])
def test_production_errors_supply_exact_repair_instructions(field, value, allowed):
    data = {'concepts': [{'title': 'Keep the glass support during rotation',
        'source_idea_ids': ['I1'], field: value},
        {'title': 'Separate inspection', 'source_idea_ids': ['I2']}], 'excluded': []}
    original = copy.deepcopy(data)
    issues = quality.check_concept_batch(data, {'I1', 'I2'})
    assert len(issues) == 1
    assert all(token in issues[0] for token in ('FATAL-', 'I1', field, *allowed))
    assert data == original  # Never silently relabel or discard a candidate.
    data['concepts'][0][field] = allowed[0]
    assert quality.check_concept_batch(data, {'I1', 'I2'}) == []
    data['concepts'].pop()
    assert any('I2' in issue for issue in quality.check_concept_batch(data, {'I1', 'I2'}))


def test_nested_schema_error_identifies_candidate_and_field_without_echoing_input():
    data = {'concepts': [{'title': 'Candidate', 'source_idea_ids': ['I1'],
        'validation_plan': ['PRIVATE_INVALID_VALUE']} ]}
    issue = quality.check_concept_batch(data, {'I1'})[0]
    assert 'I1' in issue and 'validation_plan.0' in issue
    assert 'PRIVATE_INVALID_VALUE' not in issue


def test_empty_title_has_actionable_repair_instruction():
    issues = quality.check_concept_batch({'concepts': [{'title': ' ', 'source_idea_ids': ['I1']}]}, {'I1'})
    assert len(issues) == 1 and 'title' in issues[0] and 'I1' in issues[0]


def test_saved_prompt_pins_render_all_current_enum_choices():
    body = prompts_registry.compatible_body('P_S6_CONCEPT', 'old pinned prompt')
    schema = ConceptSpec.model_json_schema()['properties']
    for field in ('novelty_class', 'change_scale', 'maturity'):
        assert field in body
        assert all(value in body for value in schema[field]['enum'])


def test_agent_repair_receives_actionable_errors_and_preserves_coverage(state, monkeypatch):
    from triz import agent
    from triz.context import RunContext
    requests = []
    invalid = {'concepts': [{'title': 'First', 'source_idea_ids': ['I1'], 'novelty_class': 'DERIVATIVE'},
                            {'title': 'Second', 'source_idea_ids': ['I2'], 'change_scale': 'SUBSYSTEM'}]}
    def respond(ctx, **kwargs):
        requests.append(kwargs['user'])
        data = copy.deepcopy(invalid)
        if len(requests) == 2:
            repair = kwargs['user'].split('FATAL-S6-COVERAGE:', 1)[1]
            assert all(token in repair for token in ('I1', 'novelty_class', 'SAME_DOMAIN',
                'CROSS_DOMAIN', 'I2', 'change_scale', 'PARAMETER', 'PARTIAL', 'REDESIGN'))
            data['concepts'][0]['novelty_class'] = 'SAME_DOMAIN'
            data['concepts'][1]['change_scale'] = 'PARTIAL'
        return SimpleNamespace(data=data, model='offline', tokens_in=1, tokens_out=1, cost_usd=0)
    monkeypatch.setattr(agent, 'tracked_chat', respond)
    result = agent.run_agent(RunContext(state), node='s6_concept', label='S6 repair',
        stage='S6_CONCEPT', agent_id='concept_architect', prompt_id='P_S6_CONCEPT',
        repair_attempts=1, checker=lambda data: quality.check_concept_batch(data, {'I1', 'I2'}))
    assert len(requests) == 2
    assert quality.check_concept_batch(result, {'I1', 'I2'}) == []
    assert state.steps[-1].status == 'OK'
