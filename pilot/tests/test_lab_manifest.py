import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from triz.lab_manifest import build_manifest, source_fingerprint


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def manifest():
    return build_manifest()


def _copy_contract(manifest, destination_root):
    for name in manifest['file_sha256']:
        destination = destination_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)


def test_manifest_keeps_exact_native_stages_and_feedback_boundary(manifest):
    from triz.pipeline import stage_list
    assert [{key: stage[key] for key in ('key', 'label', 'index')} for stage in manifest['stages']] == stage_list()[:12]
    assert manifest['stages'][1]['function'] == 'triz.domain.deep_dive'
    assert manifest['stages'][-1]['key'] == 's9_report'
    assert manifest['excluded_stages'] == ['s10_feedback']
    assert all('P_S10_FEEDBACK_DISTILL' not in stage['literal_prompt_ids'] for stage in manifest['stages'])


def test_manifest_tracks_real_callbacks_dispatch_agents_and_knowledge(manifest):
    stages = {stage['key']: stage for stage in manifest['stages']}
    assert {'P_S3_NINE_WINDOWS', 'P_S3_FUNCTION_MODEL', 'P_S3_SUFIELD',
            'P_S3_RESOURCES', 'P_S3_CECA', 'P_S3_CONSTRAINTS'} <= set(stages['s3_analyze']['literal_prompt_ids'])
    assert {'P_S4_IFR', 'P_S4_CONTRADICTIONS', 'P_S4_TRIMMING', 'P_S4_KEY_PROBLEM'} <= set(stages['s4_define']['literal_prompt_ids'])
    solve = stages['s5_solve']
    assert {'P_S5_TRACK_' + letter for letter in 'ABCEFGH'} <= set(solve['literal_prompt_ids'])
    assert {'P_S5_ARIZ_PART' + str(part) for part in range(1, 8)} <= set(solve['literal_prompt_ids'])
    assert {'triz/knowledge/matrix_39x39.json', 'triz/knowledge/principles_40.json',
            'triz/knowledge/standards_76.json', 'triz/knowledge/effects.json',
            'triz/knowledge/effects_sources.json', 'triz/knowledge/ariz_85c.yaml'} <= set(solve['knowledge_files'])
    dispatch = next(item for item in manifest['functions']['triz.nodes._run_tracks.execute']['dispatches']
                    if item['registry'] == 'triz.nodes.TRACK_FUNCS')
    assert [item['key']['value'] for item in dispatch['entries']] == [
        'A_MATRIX', 'B_SEPARATION', 'C_STANDARDS', 'D_ARIZ', 'E_TRIMMING', 'F_TRENDS', 'G_FOS', 'H_EFFECTS']
    assert 'triz.quality.generate_concepts' in stages['s6_concept']['possible_source_functions']
    assert {'P_PERSONA_FACTORY', 'P_S8_REVIEW', 'P_S8_MEETING_INITIAL',
            'P_S8_MEETING_EXCHANGE', 'P_S8_MEETING_FINAL'} <= set(stages['s8_evaluate']['literal_prompt_ids'])
    calls = manifest['functions']['triz.nodes._track_b']['agent_calls']
    assert any(call['prompt_id'] == {'value': 'P_S5_TRACK_B'}
               and call['agent_id'] == {'value': 'inventor_b'} for call in calls)
    # Every exported literal model-call field must be the actual keyword at that line.
    parsed_calls = {}
    for record in manifest['functions'].values():
        if record['source'] not in parsed_calls:
            parsed_calls[record['source']] = {(node.lineno, node.col_offset): node for node in ast.walk(ast.parse(
                (ROOT / record['source']).read_text(encoding='utf-8-sig'))) if isinstance(node, ast.Call)}
        source_calls = parsed_calls[record['source']]
        for call in record['agent_calls']:
            keywords = {kw.arg: kw.value for kw in source_calls[(call['line'], call['column'])].keywords}
            for key in ('node', 'agent_id', 'prompt_id', 'tier', 'rubric_id'):
                if key in call and 'value' in call[key]:
                    assert ast.literal_eval(keywords[key]) == call[key]['value']


def test_manifest_is_secret_free_and_never_imports_runtime_or_connects(tmp_path):
    script = '''
import importlib.abc, json, os, socket, sqlite3, sys
class BlockRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ('triz.settings', 'triz.store', 'triz.pipeline', 'triz.llm'):
            raise AssertionError('Manifest imported runtime: ' + fullname)
sys.meta_path.insert(0, BlockRuntime())
def forbidden(*args, **kwargs):
    raise AssertionError('Manifest tried to connect')
socket.create_connection = forbidden
socket.socket.connect = forbidden
sqlite3.connect = forbidden
secret = 'manifest-test-secret-must-not-appear'
for key in ('TRIZ_SERVICE_TOKEN', 'QDRANT_API_KEY', 'PATENT_DATABASE_URL', 'DATABASE_URL'):
    os.environ[key] = secret
from triz.lab_manifest import build_manifest
manifest = build_manifest()
assert secret not in json.dumps(manifest)
assert not any(name in sys.modules for name in ('triz.settings', 'triz.store', 'triz.pipeline', 'triz.llm'))
print(json.dumps({'fingerprint': manifest['fingerprint'], 'stages': len(manifest['stages'])}))
'''
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT,
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['stages'] == 12


def test_fingerprint_covers_source_prompts_knowledge_config_lab_and_report(manifest, tmp_path):
    _copy_contract(manifest, tmp_path)
    original = build_manifest(tmp_path)
    assert source_fingerprint(tmp_path) == original['fingerprint']
    assert all((tmp_path / name).is_file() for name in original['file_sha256'])
    targets = ['triz/nodes.py', 'triz/prompts/P_S5_TRACK_B.md',
               'triz/knowledge/separation.json', 'config/triz.yaml', 'triz/lab_manifest.py',
               next(name for name in original['file_sha256'] if name.startswith('templates/'))]
    previous = original
    for name in targets:
        path = tmp_path / name
        path.write_bytes(path.read_bytes() + b'\n')
        changed = build_manifest(tmp_path)
        assert changed['file_sha256'][name] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert changed['file_sha256'][name] != previous['file_sha256'][name]
        assert changed['fingerprint'] != previous['fingerprint']
        assert source_fingerprint(tmp_path) == changed['fingerprint']
        previous = changed


def test_source_fingerprint_rehashes_fresh_and_retries_a_concurrent_edit(manifest, tmp_path, monkeypatch):
    _copy_contract(manifest, tmp_path)
    original = source_fingerprint(tmp_path)
    target = tmp_path / 'triz/nodes.py'
    read_bytes = Path.read_bytes
    reads = []

    def change_once(path):
        raw = read_bytes(path)
        if path == target:
            reads.append(True)
            if len(reads) == 1:
                path.write_bytes(raw + b'\n')
        return raw

    monkeypatch.setattr(Path, 'read_bytes', change_once)
    updated = source_fingerprint(tmp_path)
    assert len(reads) >= 2
    assert updated != original
    assert updated == build_manifest(tmp_path)['fingerprint']
    # New source files are part of the contract immediately, without a restart.
    (tmp_path / 'triz/new_contract.py').write_text('VALUE = 1\n', encoding='utf-8')
    assert source_fingerprint(tmp_path) != updated


def test_source_fingerprint_rejects_a_continuously_changing_contract(manifest, tmp_path, monkeypatch):
    _copy_contract(manifest, tmp_path)
    target = tmp_path / 'triz/nodes.py'
    read_bytes = Path.read_bytes

    def change_during_read(path):
        raw = read_bytes(path)
        if path == target:
            path.write_bytes(raw + b'\n')
        return raw

    monkeypatch.setattr(Path, 'read_bytes', change_during_read)
    with pytest.raises(RuntimeError, match='source changed'):
        source_fingerprint(tmp_path)


def test_retrieval_contract_keeps_native_embedding_and_separate_read_only_sql(manifest):
    retrieval = manifest['read_only_retrieval']
    patents = retrieval['patents']
    assert patents['default_collection'] == 'patents_e5_small_v1'
    assert patents['embedding_model'] == 'intfloat/multilingual-e5-small'
    assert patents['dimensions'] == 384
    assert patents['query_prefix'] == 'query: ' and patents['document_prefix'] == 'passage: '
    assert patents['sql_is_separate_from_analysis_db']
    assert not patents['automatically_falls_back_to_paid_bigquery']
    assert 'triz.tools.vector_patents.ensure_collection' in patents['blocked_functions']
    assert 'triz.patent_corpus.init' in patents['blocked_functions']
    assert 'triz_execute_stage' not in retrieval['mcp']['allowed_tools']
    assert not retrieval['exclusions']['feedback_rag_enabled']
