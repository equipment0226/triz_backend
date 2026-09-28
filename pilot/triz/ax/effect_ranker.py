"""Small condition-applicability regressor, separate from execution-strategy Q."""
import math
from collections import Counter
from .contracts import digest, now

SCHEMA = 'effect-context-ranker-v1'
UTILITY_SCHEMA = 'effect-application-utility-v2'
DIMENSIONS = 256
EVALUATION_CONTRACT='utility-weighted-baselines-v1'
MIN_SUPPORTED_WEIGHT=.5
MIN_SUPPORTED_FAMILIES=2
IMPROVEMENT_MARGIN=1e-12
NUMERIC_TOLERANCE=1e-14


def observed(rows):
    valid=[]; excluded=Counter()
    for row in rows:
        weight=row.get('sample_weight',1.)  # Legacy absent weights mean one observation.
        if type(weight) not in (int,float) or not math.isfinite(weight) or weight<0:
            raise ValueError('Invalid sample weight')
        label=row.get('label')
        if label is None:
            excluded['unobserved_label']+=1;continue
        if type(label) not in (int,float) or not math.isfinite(label) or not -1<=label<=1:
            raise ValueError('Invalid observed utility')
        if weight==0:
            excluded['zero_weight']+=1;continue
        valid.append(row)
    if not math.isfinite(sum(r.get('sample_weight',1.) for r in valid)):
        raise ValueError('Nonfinite observed weighted mass')
    return valid,dict(excluded)


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
    if manifest.get('schema')==UTILITY_SCHEMA:
        try: rows,_=observed(rows)
        except ValueError: return dict(ready=False,reasons=['invalid_weight_or_label'],samples=len(rows))
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
    samples,excluded=observed(samples)
    if not samples: raise ValueError('Positive observed training weight required')
    weights = [0.0] * DIMENSIONS; initial = digest(weights); losses = []
    total_weight = sum(s.get('sample_weight',1.) for s in samples)
    for _ in range(epochs):
        gradients = [regularization * w for w in weights]; loss = 0
        for row in samples:
            x = row['features']
            if any(not 0<=int(i)<DIMENSIONS or not math.isfinite(v) for i,v in x.items()):
                raise ValueError('Invalid effect feature')
            if (schema==SCHEMA and row['label'] not in (-1, 1)) or not math.isfinite(row['label']) or not -1 <= row['label'] <= 1:
                raise ValueError('UNKNOWN and adoption labels cannot train applicability')
            error = sum(weights[int(i)] * v for i,v in x.items()) - row['label']
            weight = row.get('sample_weight',1.)
            loss += weight * error ** 2
            for i,v in x.items():
                gradients[int(i)] += weight * error * v / max(1e-9,total_weight)
        weights = [w - rate * g for w,g in zip(weights, gradients)]
        losses.append(loss / total_weight)
    return dict(feature_schema=schema, algorithm='regularized-linear-application-utility-v2' if schema==UTILITY_SCHEMA else 'regularized-linear-condition-proxy-v1', weights=weights,
                target_contract='candidate-utility-cost-v2' if schema==UTILITY_SCHEMA else 'condition-proxy-v1',
                evaluation_contract=EVALUATION_CONTRACT if schema==UTILITY_SCHEMA else None,
                train_weighted_mean=sum(r.get('sample_weight',1.)*r['label'] for r in samples)/total_weight,
                supported_effects=sorted({s['effect_id'] for s in samples}),
                supported_contexts=sorted({compatibility_key(s['context']) for s in samples}),
                training=dict(parameters_changed=initial != digest(weights), loss_first=losses[0], loss_last=losses[-1],weighted_mass=total_weight,excluded_count_by_reason=excluded))


def prediction(model,context,effect):
    weights=model.get('weights',[])
    if len(weights)!=DIMENSIONS or any(type(w) not in (int,float) or not math.isfinite(w) for w in weights):
        raise ValueError('Invalid effect model')
    if effect.get('id',effect.get('effect_id')) not in model.get('supported_effects',[]):
        return dict(prediction=0.,supported=False,fallback_reason='unsupported_effect')
    if compatibility_key(context) not in model.get('supported_contexts',[]):
        return dict(prediction=0.,supported=False,fallback_reason='unsupported_context')
    value=sum(weights[i]*v for i,v in features(context,effect).items())
    if not math.isfinite(value): raise ValueError('Nonfinite utility prediction')
    return dict(prediction=max(-1.,min(1.,value)),supported=True,fallback_reason=None)


def predict(model, context, effect):
    if (model.get('feature_schema') not in (SCHEMA,UTILITY_SCHEMA) or len(model.get('weights', [])) != DIMENSIONS
            or any(not math.isfinite(w) for w in model['weights'])):
        return 0.0
    if effect.get('id', effect.get('effect_id')) not in model['supported_effects'] or compatibility_key(context) not in model['supported_contexts']:
        return 0.0
    return max(-1, min(1, sum(model['weights'][i] * v for i,v in features(context, effect).items())))


def evaluate(model, rows):
    if model.get('feature_schema')==UTILITY_SCHEMA:
        valid,excluded=observed(rows)
        mean=model.get('train_weighted_mean')
        if type(mean) not in (int,float) or not math.isfinite(mean):
            raise ValueError('Frozen train weighted mean required')
        scored=[(r,prediction(model,r['context'],r['application'])) for r in valid]
        supported=[(r,p) for r,p in scored if p['supported']]
        mass=sum(r.get('sample_weight',1.) for r in valid)
        supported_mass=sum(r.get('sample_weight',1.) for r,p in supported)
        def wmse(items,kind):
            total=sum(r.get('sample_weight',1.) for r,p in items)
            if not total: return None
            return sum(r.get('sample_weight',1.)*((p['prediction'] if kind=='model' else mean if kind=='mean' else 0.)-r['label'])**2 for r,p in items)/total
        return dict(contract=EVALUATION_CONTRACT,observed_sample_count=len(valid),weighted_mass=mass,
            independent_problem_families=len({r.get('group') for r in valid if r.get('group') is not None}),
            supported_sample_count=len(supported),supported_weight_fraction=supported_mass/mass if mass else 0.,
            supported_problem_families=len({r.get('group') for r,p in supported if r.get('group') is not None}),
            wmse_supported_model=wmse(supported,'model'),wmse_supported_zero=wmse(supported,'zero'),wmse_supported_train_mean=wmse(supported,'mean'),
            wmse_full_fallback_policy=wmse(scored,'model'),wmse_full_zero=wmse(scored,'zero'),wmse_full_train_mean=wmse(scored,'mean'),
            predictions=[p for r,p in scored],excluded_count_by_reason=excluded,
            train_weighted_mean=mean,ranking_metric='not_evaluated',field_improvement_established=False)
    errors = [(predict(model, s['context'], s['application']) - s['label']) ** 2 for s in rows]
    return dict(samples=len(rows), mse=sum(errors) / len(errors) if errors else None,
                ranking_metric=None, field_improvement_established=False)


def eligibility(model,evaluation,ready):
    """Predeclared pure gate; an updated coefficient is not improvement evidence."""
    reasons=[]
    if not ready.get('ready'): reasons.append('data_not_ready')
    if model.get('evaluation_contract')!=EVALUATION_CONTRACT or evaluation.get('contract')!=EVALUATION_CONTRACT:
        reasons.append('evaluation_contract_mismatch')
    weights=model.get('weights',[])
    if not isinstance(weights,list) or len(weights)!=DIMENSIONS or any(type(w) not in (int,float) or not math.isfinite(w) for w in weights): reasons.append('invalid_model')
    if (model.get('feature_schema')!=UTILITY_SCHEMA or model.get('target_contract')!='candidate-utility-cost-v2'
        or not model.get('supported_effects') or not model.get('supported_contexts')
        or type(model.get('train_weighted_mean')) not in (int,float) or not math.isfinite(model['train_weighted_mean'])
        or model.get('train_weighted_mean')!=evaluation.get('train_weighted_mean')):
        reasons.append('invalid_model_baseline_or_support')
    support=evaluation.get('supported_sample_count',0);families=evaluation.get('supported_problem_families',0)
    fraction=evaluation.get('supported_weight_fraction',0);mass=evaluation.get('weighted_mass',0)
    if (type(support) is not int or support<2 or type(families) is not int or families<MIN_SUPPORTED_FAMILIES
        or type(fraction) not in (int,float) or not math.isfinite(fraction) or not MIN_SUPPORTED_WEIGHT<=fraction<=1
        or type(mass) not in (int,float) or not math.isfinite(mass) or mass<=0):
        reasons.append('insufficient_supported_holdout')
    keys=('wmse_supported_model','wmse_supported_zero','wmse_supported_train_mean','wmse_full_fallback_policy','wmse_full_zero','wmse_full_train_mean')
    if any(type(evaluation.get(k)) not in (int,float) or not math.isfinite(evaluation[k]) or evaluation[k]<0 for k in keys):
        reasons.append('invalid_or_empty_metrics')
    else:
        strongest=min(evaluation['wmse_supported_zero'],evaluation['wmse_supported_train_mean'])
        if strongest-evaluation['wmse_supported_model']<=IMPROVEMENT_MARGIN: reasons.append('no_supported_baseline_improvement')
        if evaluation['wmse_full_fallback_policy']>min(evaluation['wmse_full_zero'],evaluation['wmse_full_train_mean'])+NUMERIC_TOLERANCE:
            reasons.append('full_fallback_worse_than_baseline')
    return dict(eligible=not reasons,reasons=reasons,contract=EVALUATION_CONTRACT,
        minimum_supported_weight=MIN_SUPPORTED_WEIGHT,minimum_supported_families=MIN_SUPPORTED_FAMILIES,
        improvement_margin=IMPROVEMENT_MARGIN,numeric_tolerance=NUMERIC_TOLERANCE)


def train_project(tenant, project, *, schema=SCHEMA):
    from . import registry
    manifest = dataset(tenant, project, schema=schema); ready = readiness(manifest)
    if not ready['ready']:
        return dict(ready, status='COLLECTING')
    dataset_id = registry.put('effect_dataset', tenant, project, manifest)
    model = train([s for s in manifest['samples'] if s['split'] == 'train'])
    evaluation = evaluate(model, [s for s in manifest['samples'] if s['split'] == 'holdout'])
    gate=eligibility(model,evaluation,ready) if schema==UTILITY_SCHEMA else None
    eligible = gate['eligible'] if gate else model['training']['parameters_changed'] and evaluation['mse'] is not None and evaluation['mse'] < 1
    payload = dict(model=model, dataset_id=dataset_id, readiness=ready, evaluation=evaluation,
        offline_eligible=eligible, eligibility=gate, synthetic=False,
        review_ids=sorted({rid for s in manifest['samples'] for rid in s['review_ids']}))
    vid = registry.put('effect_ranker', tenant, project, payload)
    if eligible:
        registry.set_task_shadow(tenant, project, 'effect_ranker', schema, vid)
    return dict(status='SHADOW' if eligible else 'EVALUATION_FAILED', version_id=vid, evaluation=evaluation)
