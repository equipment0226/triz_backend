"""Focused format repairs retain exact rubric coverage and independent verdicts."""
import json

import pytest

from triz import analysis_semantic_gate as gate


def packet():
    return {'rules': gate.RULES['R3_CONSTRAINT'], 'artifact': {}, 'context': {}}


def passed(rule_id):
    return {'id': rule_id, 'status': 'PASS', 'reason': 'No applicable violation.', 'findings': []}


def test_output_skeleton_has_every_actual_rule_once_without_prefilling_a_verdict():
    request = gate.render_request(packet())
    json_lines = [json.loads(line) for line in request.splitlines() if line.startswith('{')]
    skeleton = next(value for value in json_lines if 'checks' in value)
    assert [row['id'] for row in skeleton['checks']] == list(packet()['rules'])
    assert all(row['status'] not in ('PASS', 'REVISE') for row in skeleton['checks'])
    assert gate.normalize_review(skeleton, packet())['verdict'] == 'UNVERIFIED'


def test_exact_coverage_diagnostics_explain_the_repair_without_accepting_an_unknown_id():
    required = list(packet()['rules'])
    bad = {'checks': [passed(required[0]), passed(required[0]), passed('C1')]}
    result = gate.normalize_review(bad, packet())
    diagnostics = {'expected': required, 'received': [required[0], required[0], 'C1'],
        'missing': required[1:], 'duplicate': [required[0]], 'unknown': ['C1']}
    assert result['verdict'] == 'UNVERIFIED' and result['verification_unavailable']
    assert result['rule_id_diagnostics'] == diagnostics
    # agent.verify_artifact includes this error plus the original response in
    # its format-repair request, so the model receives the concrete discrepancy.
    assert json.dumps(diagnostics, ensure_ascii=False) in result['error']
    assert result['element_findings'] == [] and result['revision_instructions'] == []
    fixed = {'checks': [passed(rule_id) for rule_id in required]}
    assert gate.normalize_review(fixed, packet())['verdict'] == 'PASS'
    fixed['checks'].append(passed('INVENTED_VALIDATION_RULE'))
    assert gate.normalize_review(fixed, packet())['verdict'] == 'UNVERIFIED'


@pytest.mark.parametrize('raw', [None, {}, {'checks': None}, {'checks': []},
    {'checks': [None, {'id': ['DIRECT_SOURCE_SCOPE']}, {'id': 1}]}])
def test_missing_or_malformed_coverage_stays_unverified_with_actionable_ids(raw):
    result = gate.normalize_review(raw, packet())
    assert result['verdict'] == 'UNVERIFIED'
    assert result['rule_id_diagnostics']['expected'] == list(packet()['rules'])
    assert result['rule_id_diagnostics']['missing'] == list(packet()['rules'])


def test_valid_ids_do_not_bypass_finding_evidence_validation():
    checks = [passed(rule_id) for rule_id in packet()['rules']]
    checks[0].update(status='REVISE', findings=[{
        'artifact_path': '/invented', 'artifact_quote': 'not present',
        'evidence_path': '/context/invented', 'evidence_quote': 'not present',
        'issue': 'claim', 'suggested_correction': 'change the artifact'}])
    assert gate.normalize_review({'checks': checks}, packet())['verdict'] == 'UNVERIFIED'
