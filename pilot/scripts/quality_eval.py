"""Export offline, blinded comparisons from saved state.json files. Never calls a model."""
import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def metrics(state):
    concepts = state.get('concepts', [])
    steps = state.get('steps', [])
    timings = state.get('scratch', {}).get('stage_timings', [])
    return {
        'active_seconds': round(sum(t.get('seconds', 0) for t in timings), 3) if timings else None,
        'concepts': len(concepts),
        'mechanisms': len({c.get('mechanism_key') for c in concepts if c.get('mechanism_key')}),
        'resolution_arguments': sum(bool(c.get('resolution_argument')) for c in concepts),
        'validation_plans': sum(bool(c.get('validation_plan')) for c in concepts),
        'independently_passed': sum(c.get('quality_status') == 'PASS' for c in concepts),
        'repair_attempts': sum(max(0, s.get('verify_attempts', 0) - 1) for s in steps),
        'tokens_in': state.get('cost', {}).get('tokens_in', 0),
        'tokens_out': state.get('cost', {}).get('tokens_out', 0),
        'cost_usd': state.get('cost', {}).get('total_usd', 0),
        'requests': state.get('cost', {}).get('request_count'),
    }


def load_runs(directory):
    result = {}
    for path in sorted(Path(directory).rglob('state.json')):
        state = json.loads(path.read_text(encoding='utf-8'))
        if not state.get('raw_query'):
            continue
        # Match user inputs, answers and selected candidate index; reviewers still
        # check that the generated candidate boundaries have equivalent meanings.
        confirm = state.get('confirm', {})
        selected = next((i for i, c in enumerate(confirm.get('candidates', []))
                         if c.get('id') == confirm.get('chosen_candidate_id')), None)
        identity = [state['raw_query'], state.get('intake', {}).get('clarify_turns', []),
                    state.get('scratch', {}).get('deep_dive', {}).get('answers', []),
                    selected, confirm.get('user_amendments', [])]
        key = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        result.setdefault(key, []).append(state)
    return result


def export(baseline, candidate, output, seed=42):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    groups = [load_runs(baseline), load_runs(candidate)]
    rows, mapping, review = [], [], ['# 블라인드 품질 비교', '',
        '각 답변을 도메인 충실성·모순 해소·인과 근거·실행 가능성·반증 가능성으로 1~5점 평가한다.',
        '자동 집계는 구조적 신호이며 품질 점수가 아니다. 같은 수치가 없다는 이유로 낮게 평가하지 않는다.', '']
    rng = random.Random(seed)
    for key in sorted(groups[0].keys() & groups[1].keys()):
        for repetition, pair in enumerate(zip(groups[0][key], groups[1][key])):
            order = [0, 1]
            rng.shuffle(order)
            review += [f'## 문제 {key} / 반복 {repetition+1}', pair[0]['raw_query'], '']
            for index, variant in enumerate(order):
                label = chr(65 + index)
                state = pair[variant]
                mapping.append({'case': key, 'repetition': repetition+1, 'label': label,
                                'variant': ['baseline', 'candidate'][variant], 'run_id': state.get('run_id')})
                rows.append(dict(mapping[-1], **metrics(state)))
                review += [f'### 답변 {label}', '']
                for c in state.get('concepts', []):
                    review += [f"**{c.get('title','')}**", c.get('description', ''),
                               c.get('working_principle', ''), c.get('resolution_argument', ''),
                               json.dumps(c.get('validation_plan', []), ensure_ascii=False), '']
    (output / 'blind_review.md').write_text('\n'.join(review), encoding='utf-8')
    (output / 'mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    with (output / 'metrics.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        if rows:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {}
    for variant in ('baseline', 'candidate'):
        values = sorted(r['active_seconds'] for r in rows if r['variant'] == variant and r['active_seconds'] is not None)
        def percentile(p):
            if not values:
                return None
            pos = (len(values)-1) * p
            lo = int(pos)
            hi = min(lo+1, len(values)-1)
            return round(values[lo] + (values[hi]-values[lo]) * (pos-lo), 3)
        summary[variant] = {'timed_runs': len(values), 'p50_seconds': percentile(.5),
                            'p95_seconds': percentile(.95), 'at_least_20_runs': len(values) >= 20}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return len(mapping) // 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    print(f"Exported {export(args.baseline, args.candidate, args.output, args.seed)} matched pairs")
