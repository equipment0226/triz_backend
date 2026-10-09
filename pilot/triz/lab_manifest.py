"""Read-only source manifest for the isolated, no-feedback analysis lab.

No analysis module is imported: inspecting this manifest must not initialize a
database, launch a worker, read credentials, or make a provider request. The AST
map describes possible source dependencies, not runtime branch/call order.
"""
import ast
import hashlib
import json
from pathlib import Path


VERSION = 'triz-analysis-lab-manifest-v1'
_BOUNDARIES = {
    'triz.agent', 'triz.store', 'triz.events', 'triz.llm', 'triz.pipeline',
    'triz.mcp_server', 'triz.mcp_client', 'triz.prompts_registry', 'triz.ax.ledger',
}
_AGENT_FIELDS = ('node', 'agent_id', 'prompt_id', 'tier', 'rubric_id')


def _contract_paths(root):
    paths = {path for folder in ('triz', 'api') for path in (root / folder).rglob('*.py')
             if '__pycache__' not in path.parts}
    for folder, suffixes in [('triz/prompts', {'.md'}),
                             ('triz/knowledge', {'.json', '.yaml', '.yml'}),
                             ('config', {'.yaml', '.yml', '.json'})]:
        paths.update(path for path in (root / folder).iterdir()
                     if path.is_file() and path.suffix in suffixes)
    paths.update(path for path in (root / 'templates').rglob('*') if path.is_file())
    return {path.relative_to(root).as_posix(): path for path in sorted(paths)}


def _metadata(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _contract_hashes(root):
    """Rehash every file; retry if a file or file-set changes during the read."""
    for _ in range(3):
        try:
            paths = _contract_paths(root)
            before = {name: _metadata(path) for name, path in paths.items()}
            hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
            after_paths = _contract_paths(root)
            if paths.keys() == after_paths.keys() and before == {
                    name: _metadata(path) for name, path in after_paths.items()}:
                return hashes
        except FileNotFoundError:
            # An atomic source replacement can briefly remove an old filename.
            continue
    raise RuntimeError('TRIZ source changed while reading the lab contract')


def _fingerprint(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def source_fingerprint(pilot_root=None):
    """Fresh contract hash without the AST map, runtime imports, or env reads."""
    root = Path(pilot_root) if pilot_root is not None else Path(__file__).resolve().parents[1]
    return _fingerprint(_contract_hashes(root))


def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _name(node.value)
        return parent + '.' + node.attr if parent else ''
    return ''


def _own_nodes(node):
    """A nested function has its own record and is reached via calls/callbacks."""
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield child
            yield from _own_nodes(child)


def _imports(nodes, module, package):
    aliases = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ''
            if node.level:
                parts = package.split('.')
                base = '.'.join(parts[:len(parts) - node.level + 1] + ([base] if base else []))
            for item in node.names:
                if item.name != '*':
                    aliases[item.asname or item.name] = base + '.' + item.name
    return aliases


def _resolve(node, module, aliases, function, functions):
    value = _name(node)
    if not value:
        return ''
    first, *rest = value.split('.')
    if first in aliases:
        return '.'.join([aliases[first], *rest])
    # Try the innermost local function, then enclosing functions, then globals.
    scope = function
    while scope.startswith(module + '.'):
        candidate = scope + '.' + value
        if candidate in functions:
            return candidate
        scope = scope.rsplit('.', 1)[0]
    return module + '.' + value


def _value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
        return {'value': node.value}
    return {'expression': ast.unparse(node)}


def _source_index(root):
    modules, functions = {}, {}
    for path in sorted((root / 'triz').rglob('*.py')):
        if path.name.startswith('lab_') or '__pycache__' in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        parts = list(path.relative_to(root).with_suffix('').parts)
        is_package = parts[-1] == '__init__'
        if is_package:
            parts.pop()
        module = '.'.join(parts)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=relative)
        package = module if is_package else module.rsplit('.', 1)[0]
        modules[module] = dict(tree=tree, path=relative, package=package,
            aliases=_imports(_own_nodes(tree), module, package))

        def collect(parent, prefix):
            for child in ast.iter_child_nodes(parent):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = prefix + '.' + child.name
                    functions[qualified] = (module, child)
                    collect(child, qualified)
                elif not isinstance(child, ast.ClassDef):
                    collect(child, prefix)
        collect(tree, module)
    return modules, functions


def _relationships(root, modules, functions):
    catalog = {p.name for p in (root / 'triz' / 'knowledge').iterdir() if p.is_file()}
    prompt_ids = {p.stem for p in (root / 'triz' / 'prompts').glob('*.md')}
    records = {}
    for qualified, (module, function) in sorted(functions.items()):
        info = modules[module]
        own = list(_own_nodes(function))
        aliases = dict(info['aliases'], **_imports(own, module, info['package']))
        calls, agents, knowledge_files, dispatches, prompt_references = set(), [], set(), [], set()
        for item in own:
            if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value in catalog:
                knowledge_files.add('triz/knowledge/' + item.value)
            if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value in prompt_ids:
                prompt_references.add(item.value)
            if not isinstance(item, ast.Call):
                continue
            callee = _resolve(item.func, module, aliases, qualified, functions)
            if callee.startswith('triz.'):
                calls.add(callee)
            if callee in ('triz.agent.run_agent', 'triz.agent.verify_artifact', 'triz.agent.tracked_chat'):
                keywords = {kw.arg: kw.value for kw in item.keywords if kw.arg}
                agents.append(dict(line=item.lineno, column=item.col_offset, callee=callee,
                    **{key: _value(keywords[key]) for key in _AGENT_FIELDS if key in keywords}))
            # ThreadPoolExecutor submit/map carry callable references as inputs.
            if isinstance(item.func, ast.Attribute) and item.func.attr in ('submit', 'map') and item.args:
                callback = _resolve(item.args[0], module, aliases, qualified, functions)
                if callback in functions:
                    calls.add(callback)
        # Resolve a source dispatch registry such as nodes.TRACK_FUNCS.get(t).
        referenced = {_resolve(n, module, aliases, qualified, functions) for n in own
                      if isinstance(n, (ast.Name, ast.Attribute))}
        # Local workers can be placed in lists/tuples before pool.submit(fn).
        # Passing a function object is a possible edge, even without a direct call.
        calls.update(referenced.intersection(functions))
        for registry_module, registry_info in modules.items():
            if not any(name.startswith(registry_module + '.') for name in referenced):
                continue
            for binding in registry_info['tree'].body:
                if not isinstance(binding, ast.Assign) or not isinstance(binding.value, ast.Dict):
                    continue
                names = [registry_module + '.' + n.id for n in binding.targets if isinstance(n, ast.Name)]
                if not set(names).intersection(referenced):
                    continue
                entries = []
                for key, target in zip(binding.value.keys, binding.value.values):
                    ref = _resolve(target, registry_module, registry_info['aliases'], registry_module, functions)
                    if ref in functions:
                        calls.add(ref)
                        entries.append(dict(key=_value(key), function=ref))
                if entries:
                    dispatches.append(dict(registry=names[0], entries=entries))
        # File-backed guidance may name its catalog in a module-level Path.
        local_names = {n.id for n in own if isinstance(n, ast.Name)}
        for binding in info['tree'].body:
            if isinstance(binding, ast.Assign) and any(isinstance(t, ast.Name) and t.id in local_names for t in binding.targets):
                for item in ast.walk(binding.value):
                    if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value in catalog:
                        knowledge_files.add('triz/knowledge/' + item.value)
                    if isinstance(item, ast.Constant) and isinstance(item.value, str) and item.value in prompt_ids:
                        prompt_references.add(item.value)
        records[qualified] = dict(source=info['path'], line=function.lineno,
            calls=sorted(calls), agent_calls=agents, prompt_references=sorted(prompt_references),
            knowledge_files=sorted(knowledge_files), dispatches=dispatches)
    return records


def _build_manifest(root, hashes):
    modules, functions = _source_index(root)
    pipeline = modules['triz.pipeline']
    assignment = next(node for node in pipeline['tree'].body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'PIPELINE' for t in node.targets))
    entries = assignment.value.elts
    if len(entries) != 13 or ast.literal_eval(entries[-1].elts[0]) != 's10_feedback':
        raise ValueError('Review the lab stage boundary after a production pipeline change')
    relationships = _relationships(root, modules, functions)
    stages, used = [], set()
    for index, entry in enumerate(entries[:12]):
        key, label = (ast.literal_eval(value) for value in entry.elts[:2])
        function = _resolve(entry.elts[2], 'triz.pipeline', pipeline['aliases'], 'triz.pipeline', functions)
        pending, reached = [function], set()
        while pending:
            ref = pending.pop()
            if ref in reached or ref not in relationships:
                continue
            reached.add(ref)
            if ref.rsplit('.', 1)[0] not in _BOUNDARIES:
                pending.extend(relationships[ref]['calls'])
        used.update(reached)
        direct_prompts = sorted({call['prompt_id']['value'] for ref in reached
            for call in relationships[ref]['agent_calls']
            if 'prompt_id' in call and 'value' in call['prompt_id'] and call['prompt_id']['value']})
        prompts = sorted({prompt for ref in reached for prompt in relationships[ref]['prompt_references']})
        stages.append(dict(index=index, key=key, label=label, function=function,
            possible_source_functions=sorted(reached), literal_prompt_ids=prompts,
            direct_literal_agent_prompt_ids=direct_prompts,
            knowledge_files=sorted({path for ref in reached for path in relationships[ref]['knowledge_files']})))
    fingerprint = _fingerprint(hashes)
    return dict(version=VERSION, fingerprint=fingerprint,
        stage_boundary='PIPELINE[:12]', excluded_stages=['s10_feedback'],
        mapping_semantics='Static possible calls/callbacks/dispatches; runtime conditions and order are not inferred.',
        stages=stages, functions={ref: relationships[ref] for ref in sorted(used)}, file_sha256=hashes,
        read_only_retrieval=dict(
            mcp=dict(path='/agent/mcp', standalone_path='/mcp', auth='Bearer TRIZ_SERVICE_TOKEN',
                allowed_tools=['triz_query_matrix', 'triz_get_engineering_parameters',
                    'triz_get_inventive_principles', 'triz_search_evidence'], allowed_resources=['triz://workflow'],
                production_prompt_tools_persist_analysis=True, production_token_has_no_tool_scope=True),
            patents=dict(provider='vector', function='triz.tools.vector_patents.search_batch',
                environment_keys=['PATENT_DATABASE_URL', 'QDRANT_URL', 'QDRANT_API_KEY', 'PATENT_VECTOR_COLLECTION'],
                default_collection='patents_e5_small_v1', embedding_model='intfloat/multilingual-e5-small',
                model_commit='614241f622f53c4eeff9890bdc4f31cfecc418b3', dimensions=384,
                model_file='onnx/model_qint8_avx512_vnni.onnx', query_prefix='query: ', document_prefix='passage: ',
                distance='COSINE', qdrant_operation='POST /collections/{collection}/points/query/batch',
                qdrant_auth_header='api-key', sql_read_tables=['patent_documents', 'patent_checkpoints'],
                sql_hydration_key='publication_number', sql_is_separate_from_analysis_db=True,
                automatically_falls_back_to_paid_bigquery=False, exposes_retrieval_diagnostics=True,
                blocked_functions=['triz.patent_corpus.init', 'triz.patent_corpus.ingest',
                    'triz.patent_corpus.acknowledge', 'triz.patent_corpus.save_checkpoint',
                    'triz.tools.vector_patents.ensure_collection', 'triz.tools.vector_patents.index_pending']),
            knowledge=dict(directory='triz/knowledge', storage='versioned source files',
                feedback_rag_is_separate=True),
            exclusions=dict(feedback_rag_enabled=False, learned_and_shadow_policies=False,
                learned_and_shadow_effect_rankers=False, feedback_event_writes=False,
                learning_workers=False, production_analysis_db_writes=False)))


def build_manifest(pilot_root=None):
    """Return a consistent source map and hash without consulting env/DB."""
    root = Path(pilot_root) if pilot_root is not None else Path(__file__).resolve().parents[1]
    for _ in range(3):
        hashes = _contract_hashes(root)
        result = _build_manifest(root, hashes)
        if hashes == _contract_hashes(root):
            return result
    raise RuntimeError('TRIZ source changed while building the lab manifest')
