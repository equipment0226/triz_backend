"""Owner-scoped, resumable patent backfill. Default is a read-only inventory.

Run from pilot/: python scripts/refresh_project_patents.py --owner-email EMAIL
  --exclude-run-id FIRST_TEST --ticket UNIQUE_ID [--execute]
Each query batch is saved before matching so retries cannot repeat its scan.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from triz import evidence, render, store
from triz.context import RunContext
from triz.settings import settings


def emit(**data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def fingerprint(state):
    data = [state.raw_query, [c.model_dump(mode='json') for c in state.concepts],
            state.constraints.model_dump(mode='json')]
    # Evidence links/transfer conditions are produced by this maintenance run.
    for concept in data[1]:
        concept.pop('evidence_ids', None)
        concept.pop('transfer_conditions', None)
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def plans_for(state):
    plans = {}
    def add(q):
        if not isinstance(q, dict) or q.get('kind') != 'PATENT' or not isinstance(q.get('query'), str):
            return
        query = q['query'].strip()
        if not query:
            return
        key = 'PATENT:' + query.lower()
        previous = plans.get(key, {})
        ids = sorted(set(previous.get('concept_ids', []) + q.get('concept_ids', [])))
        plans[key] = {**q, 'query':query, 'concept_ids':[i for i in ids if state.concept(i)]}
    for step in state.steps:
        if step.node in ('s5_patent_plan', 's9_evidence_plan') and isinstance(step.output_json, dict):
            for q in step.output_json.get('queries', []):
                add(q)
    for q in state.scratch.get('search_plans', {}).values():
        add(q)
    for key in set(state.scratch.get('search_cache', {})) | set(state.scratch.get('search_diagnostics', {})):
        if key.startswith('PATENT:') and key not in plans:
            add({'kind':'PATENT', 'query':key.split(':', 1)[1]})
    return plans


def batches(keys):
    count = (len(keys) + 63) // 64
    return [keys[i::count] for i in range(count)] if count else []


def inventory(owner_email, excluded):
    store.init()
    with store.engine.connect() as connection:
        owners = list(connection.execute(select(store.accounts.c.user_id).where(
            store.accounts.c.email == owner_email.lower())).scalars())
        if not owners:
            raise ValueError('Owner not found')
        first = connection.execute(select(store.runs).where(
            store.runs.c.run_id == excluded, store.runs.c.user_id.in_(owners))).mappings().first()
        if not first or not first['title'].startswith('[배포 검증·가상]'):
            raise ValueError('Excluded run must be the owner verified initial test')
        rows = list(connection.execute(select(store.runs).where(
            store.runs.c.user_id.in_(owners), store.runs.c.started_at > first['started_at'],
            store.runs.c.run_id != excluded).order_by(store.runs.c.started_at)).mappings())
    targets = []
    for row in rows:
        state = store.load_state(row['run_id'])
        if state.status != 'COMPLETED' or not state.report or not state.concepts:
            raise ValueError('Target is not a completed report: ' + state.run_id)
        plans = plans_for(state)
        if not plans:
            raise ValueError('No historical patent search plan: ' + state.run_id)
        targets.append(dict(run_id=state.run_id, title=row['title'], user_id=state.user_id,
                            signature=fingerprint(state), plans=plans))
    return targets


def apply_target(target, query_results, ticket, folder):
    rid = target['run_id']
    with store.run_lock(rid):
        state = store.load_state(rid)
        if state.user_id != target['user_id'] or state.status != 'COMPLETED' or fingerprint(state) != target['signature']:
            raise ValueError('Run changed since inventory: ' + rid)
        mark = state.scratch.get('patent_refresh', {})
        if mark.get('ticket') == ticket and mark.get('status') == 'COMPLETED':
            return mark['result']
        backup_name = 'before-' + ticket + '.json'
        backup = settings.storage_dir / 'runs' / rid / backup_name
        if not backup.exists():
            store.archive(rid, backup_name, state.model_dump_json())
        before_cost = state.cost.total_usd
        before_patents = sum(e.source_type == 'PATENT' for e in state.evidence)
        ctx = RunContext(state)
        state.scratch['patent_refresh'] = dict(ticket=ticket, status='MATCHING')
        step = ctx.start_step(node='s9_patent_backfill', label='특허 검색 저장소 재검색',
            stage=state.control.current_stage, agent_id='patent_researcher', prompt_id='', tier='')
        step.input_slice = {'ticket':ticket, 'queries':list(target['plans'].values())}
        cache = state.scratch.setdefault('search_cache', {})
        diagnostics = state.scratch.setdefault('search_diagnostics', {})
        saved = state.scratch.setdefault('search_plans', {})
        for key, plan in target['plans'].items():
            records, detail = query_results[key]
            if detail['status'] not in ('OK', 'EMPTY'):
                raise ValueError('Incomplete search: ' + key)
            previous = {r['identifier']:r for r in cache.get(key, [])}
            previous.update({r['identifier']:{**r, 'concept_ids':plan.get('concept_ids', []),
                'scope':plan.get('scope', 'direct'), 'function_mapping':plan.get('function_mapping', '')} for r in records})
            cache[key] = list(previous.values())
            diagnostics[key] = {**detail, 'checked_at':time.time(), 'refresh_ticket':ticket}
            saved[key] = plan
        candidates = {}
        for hits in cache.values():
            for hit in hits:
                key = hit['identifier'].lower()
                if key not in candidates:
                    candidates[key] = dict(hit)
                else:
                    candidates[key]['concept_ids'] = sorted(set(candidates[key].get('concept_ids', []) + hit.get('concept_ids', [])))
        state.scratch['evidence_candidates'] = list(candidates.values())
        state.scratch['search_status'] = evidence.search_summary(state)
        step.output_json = {'queries':{k:diagnostics[k] for k in target['plans']}}
        ctx.finish_step(step, 'OK')
        ctx.persist()
        emit(run_id=rid, phase='MATCHING', patent_candidates=sum(r['source_type']=='PATENT' for r in candidates.values()))
        start = len(state.steps)
        # All historical searches have already been refreshed across projects.
        evidence.attach(ctx, discover_sources=False)
        if any(s.status == 'FAILED' for s in state.steps[start:]):
            raise RuntimeError('Applicability matching failed: ' + rid)
        state.report.markdown = render.render_report(state, state.report.narrative)
        state.report.word_count = len(state.report.markdown)
        render.save(state, state.report.markdown)
        patents = [e for e in state.evidence if e.source_type == 'PATENT']
        linked_ids = {e.id for e in patents}
        result = dict(run_id=rid, title=target['title'], status='COMPLETED',
            patent_queries=len(target['plans']), patent_candidates=state.scratch['search_status']['patent_records'],
            patents_before=before_patents, patents_after=len(patents),
            solutions=len(state.concepts), solutions_with_patents=sum(bool(linked_ids.intersection(c.evidence_ids)) for c in state.concepts),
            related_patents=sum(r['reference']['source_type']=='PATENT' for r in state.scratch.get('related_references', [])),
            added_llm_cost_usd=round(state.cost.total_usd-before_cost, 6))
        state.scratch['patent_refresh'] = dict(ticket=ticket, status='COMPLETED', result=result)
        ctx.persist()
        write(folder / (rid + '.json'), result)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner-email', required=True)
    parser.add_argument('--exclude-run-id', required=True)
    parser.add_argument('--ticket', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', args.ticket):
        raise ValueError('Invalid ticket')
    with store.run_lock('maintenance-' + args.ticket):
        targets = inventory(args.owner_email, args.exclude_run_id)
        plans = {k:q for t in targets for k,q in t['plans'].items()}
        groups = batches(sorted(plans))
        emit(phase='INVENTORY', excluded=args.exclude_run_id, targets=[
            {'run_id':t['run_id'], 'title':t['title'], 'queries':len(t['plans'])} for t in targets],
            unique_queries=len(plans), batch_sizes=[len(g) for g in groups])
        if not args.execute:
            return
        if settings.patent_search_provider not in ('vector', 'bigquery'):
            raise ValueError('A batch patent provider must be selected')
        folder = settings.storage_dir / 'maintenance' / args.ticket
        folder.mkdir(parents=True, exist_ok=True)
        manifest_path = folder / 'manifest.json'
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if manifest['targets'] != targets or manifest['groups'] != groups:
                raise ValueError('Inventory changed; inspect the existing maintenance manifest')
        else:
            write(manifest_path, dict(targets=targets, groups=groups))
        # This maintenance process batches up to 64 queries; normal app timeout is unchanged.
        if settings.patent_search_provider == 'bigquery':
            settings.bigquery_timeout = max(settings.bigquery_timeout, 300)
        all_results = {}
        for index, group in enumerate(groups):
            output = folder / f'batch-{index}.json'
            if output.exists():
                results = json.loads(output.read_text(encoding='utf-8'))
            else:
                emit(phase='QUERY_BATCH', batch=index, queries=len(group))
                from triz.tools.scholar import patent_search_batch
                results = patent_search_batch([plans[k]['query'] for k in group], 6)
                if any(d['status'] not in ('OK', 'EMPTY') for _,d in results):
                    emit(phase='QUERY_FAILED', batch=index, diagnostics=[d for _,d in results[:1]])
                    raise RuntimeError('Query batch incomplete; report changes not started')
                write(output, results)
            if len(results) != len(group):
                raise ValueError('Saved batch length mismatch')
            all_results.update(zip(group, results))
            emit(phase='QUERY_COMPLETE', batch=index, candidates=sum(len(h) for h,_ in results),
                 job_id=results[0][1].get('job_id'), billed_bytes=results[0][1].get('billed_bytes'))
        failures = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(apply_target, t, all_results, args.ticket, folder):t['run_id'] for t in targets}
            for future in as_completed(futures):
                try:
                    emit(phase='REPORT_UPDATED', **future.result())
                except Exception as exc:
                    failures.append(futures[future])
                    emit(phase='REPORT_FAILED', run_id=futures[future], error_type=type(exc).__name__)
        if failures:
            raise RuntimeError('Report refresh incomplete: ' + ','.join(failures))
        emit(phase='COMPLETE', reports=len(targets))


if __name__ == '__main__':
    main()
