"""Small condition-applicability regressor, separate from execution-strategy Q."""
import math
from collections import Counter
from .contracts import digest, now

SCHEMA = 'effect-context-ranker-v1'
UTILITY_SCHEMA = 'effect-application-utility-v2'
DIMENSIONS = 256


def compatibility_key(context):
    return digest({k:context.get(k) for k in ('domain','resources','constraints')})


def features(context, effect):
    # Stable interactions retain context differences; IDs alone cannot imply success.
    effect_id = str(effect.get('id') or effect.get('effect_id'))
    mechanism = effect.get('mechanism_key', '')
    terms = ['effect=' + effect_id, 'mechanism=' + mechanism]
    for kind in ('domain', 'functions', 'contradictions', 'physical_contradictions', 'interactions', 'resources', 'constraints'):
        values = context.get(kind, [])
        if not isinstance(values, list):
            values = [values]
        for value in values:
            token = kind + ':' + digest(value)
            terms += [token + '*' + effect_id, token + '*' + mechanism]
    vector = {}
    for term in terms:
        key = int(digest(term)[:8], 16) % DIMENSIONS
        vector[key] = vector.get(key, 0) + 1
    length = math.sqrt(sum(v * v for v in vector.values()))
    return {k:v / length for k,v in vector.items()}


def dataset(tenant, project, cutoff=None, *, schema=SCHEMA):
    if schema == UTILITY_SCHEMA:
        from .learning_outcomes import effect_dataset
        return effect_dataset(tenant,project,cutoff)
    from .effect_history import observations
    cutoff = cutoff or now()
    rows = observations(tenant, project, cutoff=cutoff)
    samples = {}; excluded = Counter(); states = {}
    for row in rows:
        app, review = row['application'], row['review']
        from . import ledger
        if app['run_id'] not in states:
            states[app['run_id']] = ledger.store.load_state(app['run_id'])
        state = states[app['run_id']]
        if not state or state.scratch.get('acceptance_fixture') or state.scratch.get('synthetic'):
            excluded['test_or_missing_run'] += 1
            continue
        if review.get('evidence_level') != 'USER_REPORTED':
            excluded['unsupported_evidence_level'] += 1
            continue
        key = (app['run_id'], app['effect_id'], review['condition_id'])
        value = dict(features=features(app['structured_context'], app), context=app['structured_context'],
            effect_id=app['effect_id'], label=row['label'], group=app['problem_family'],
            run_id=app['run_id'], available_at=review['label_available_at'],
            review_ids=[review['event_id']], maturity='CONCEPT_PROXY', application=app)
        if key not in samples or samples[key]['available_at'] < value['available_at']:
            samples[key] = value
    rows = list(samples.values())
    from .routing_q import bounded_families
    rows,limited=bounded_families(rows)
    excluded['cpu_batch_limit']+=limited
    groups = sorted({s['group'] for s in rows}, key=lambda g:max(s['available_at'] for s in rows if s['group'] == g))
    holdout = set(groups[-max(1, len(groups) // 4):])
    for row in rows:
        row['split'] = 'holdout' if row['group'] in holdout else 'train'
    return dict(schema=SCHEMA, task_kind='effect_ranker', samples=rows, excluded=dict(excluded),
                cutoff=cutoff, synthetic=False, tenant_id=tenant, project_id=project)


def readiness(manifest):
    rows = manifest['samples']; reasons = []
    train = [r for r in rows if r['split'] == 'train']
    holdout = [r for r in rows if r['split'] == 'holdout']
    if manifest.get('synthetic'):
        reasons.append('synthetic_dataset')
    if len(rows) < 16:
        reasons.append('fewer_than_16_common_evaluations' if manifest.get('schema')==UTILITY_SCHEMA else 'fewer_than_16_explicit_condition_reviews')
    if len({r['group'] for r in train}) < 4 or len({r['group'] for r in holdout}) < 2:
        reasons.append('insufficient_independent_time_holdout')
    if len({r['label'] for r in train}) < 2:
        reasons.append('missing_positive_or_negative_support')
    return dict(ready=not reasons, reasons=reasons, samples=len(rows))


def train(samples, epochs=200, rate=.1, regularization=.01):
    if not samples or len(samples)>2000 or not 1 <= epochs <= 2000:
        raise ValueError('Bounded nonempty effect dataset required')
    schema = samples[0].get('feature_schema', SCHEMA)
    if schema not in (SCHEMA,UTILITY_SCHEMA) or any(r.get('feature_schema',SCHEMA)!=schema or r.get('split','train')!='train' for r in samples):
        raise ValueError('Incompatible effect training partition/schema')
    if any(r.get('synthetic') for r in samples):
        raise ValueError('Synthetic event projections cannot establish effect support')
    weights = [0.0] * DIMENSIONS; initial = digest(weights); losses = []
    total_weight = sum(s.get('sample_weight',1.) for s in samples)
    for _ in range(epochs):
        gradients = [regularization * w for w in weights]; loss = 0
        for row in samples:
            x = row['features']
            if (schema==SCHEMA and row['label'] not in (-1, 1)) or not math.isfinite(row['label']) or not -1 <= row['label'] <= 1:
                raise ValueError('UNKNOWN and adoption labels cannot train applicability')
            error = sum(weights[int(i)] * v for i,v in x.items()) - row['label']
            weight = row.get('sample_weight',1.)
            loss += weight * error ** 2
            for i,v in x.items():
                gradients[int(i)] += weight * error * v / max(1e-9,total_weight)
        weights = [w - rate * g for w,g in zip(weights, gradients)]
        losses.append(loss / len(samples))
    return dict(feature_schema=schema, algorithm='regularized-linear-application-utility-v2' if schema==UTILITY_SCHEMA else 'regularized-linear-condition-proxy-v1', weights=weights,
                target_contract='candidate-utility-cost-v2' if schema==UTILITY_SCHEMA else 'condition-proxy-v1',
                supported_effects=sorted({s['effect_id'] for s in samples}),
                supported_contexts=sorted({compatibility_key(s['context']) for s in samples}),
                training=dict(parameters_changed=initial != digest(weights), loss_first=losses[0], loss_last=losses[-1]))


def predict(model, context, effect):
    if (model.get('feature_schema') not in (SCHEMA,UTILITY_SCHEMA) or len(model.get('weights', [])) != DIMENSIONS
            or any(not math.isfinite(w) for w in model['weights'])):
        return 0.0
    if effect.get('id', effect.get('effect_id')) not in model['supported_effects'] or compatibility_key(context) not in model['supported_contexts']:
        return 0.0
    return max(-1, min(1, sum(model['weights'][i] * v for i,v in features(context, effect).items())))


def evaluate(model, rows):
    errors = [(predict(model, s['context'], s['application']) - s['label']) ** 2 for s in rows]
    return dict(samples=len(rows), mse=sum(errors) / len(errors) if errors else None,
                ranking_metric=None, field_improvement_established=False)


def train_project(tenant, project, *, schema=SCHEMA):
    from . import registry
    manifest = dataset(tenant, project, schema=schema); ready = readiness(manifest)
    if not ready['ready']:
        return dict(ready, status='COLLECTING')
    dataset_id = registry.put('effect_dataset', tenant, project, manifest)
    model = train([s for s in manifest['samples'] if s['split'] == 'train'])
    evaluation = evaluate(model, [s for s in manifest['samples'] if s['split'] == 'holdout'])
    eligible = model['training']['parameters_changed'] and evaluation['mse'] is not None and evaluation['mse'] < 1
    payload = dict(model=model, dataset_id=dataset_id, readiness=ready, evaluation=evaluation,
        offline_eligible=eligible, synthetic=False,
        review_ids=sorted({rid for s in manifest['samples'] for rid in s['review_ids']}))
    vid = registry.put('effect_ranker', tenant, project, payload)
    if eligible:
        registry.set_task_shadow(tenant, project, 'effect_ranker', schema, vid)
    return dict(status='SHADOW' if eligible else 'EVALUATION_FAILED', version_id=vid, evaluation=evaluation)
