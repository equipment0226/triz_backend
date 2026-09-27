"""Bounded, offline queue semantics; fakes make external reads impossible."""
from collections import Counter
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest

from triz import effect_balanced_review as q


def point(index, cpc=(), ipc=(), family=None, country='US', year=2020):
    number = f'{country}-{index}-A1'
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'triz:patent:' + number)),
                payload=dict(publication_number=number, cpc=list(cpc), ipc=list(ipc),
                             family_id=family, country=country, publication_date=year * 10000 + 101))


def pool(points, state=None, exhausted=False):
    state = state or q.empty_state()
    return dict(inventory=dict(version=q.VERSION, operation='pool', state_sha256=q.digest(state),
                collection='test-patents', offset=state['next_qdrant_offset'],
                next_offset=None if exhausted else str(uuid.uuid5(uuid.NAMESPACE_URL, 'next-' + str(state['batch_number']))),
                scanned_points=len(points), scroll_exhausted=exhausted), points=points)


def prior():
    return dict(identifiers=[], family_ids=[], section_counts={}, country_counts={}, year_counts={})


def hydration(selection, missing=(), blank=()):
    docs = []
    for c in selection['selected']:
        number = c['publication_number']
        if number in missing:
            continue
        docs.append(dict(identifier=number, publication_number=number, title='Public patent',
                         abstract='' if number in blank else 'A readable stored abstract.',
                         abstract_truncated=False, content_hash='a' * 64,
                         url='https://patents.google.com/patent/' + number + '/en',
                         retrieval_scope='stored_patent_abstract', cpc=c['cpc'], ipc=c['ipc'],
                         family_id=c['family_id'], country_code=c['country'],
                         publication_date=c['publication_date']))
    return dict(inventory=dict(version=q.VERSION, operation='hydrate',
                selection_sha256=q.digest(selection),
                requested_numbers=[c['publication_number'] for c in selection['selected']]), documents=docs)


def helper():
    path = Path(__file__).resolve().parents[2] / 'deploy/harvest_balanced_patent_page.py'
    spec = importlib.util.spec_from_file_location('balanced_remote_helper', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_classifications_ipc_fallback_and_y_cross_tag():
    multi = q.metadata(dict(cpc=[{'code': 'G06F 1/00'}, 'A01B1/00', 'Y02E10/00'], ipc=['H01L1/00', 'C01B1/00']))
    assert multi['sections'] == ['A', 'C', 'G', 'H']
    assert multi['y_tags'] == ['Y02E10/00']
    assert multi['classification_basis'] == 'CPC+IPC'
    assert q.metadata(dict(ipc=['D01F1/00']))['sections'] == ['D']
    assert q.metadata(dict(cpc=['Y02E10/00'], ipc=['E01B1/00']))['sections'] == ['E']
    assert q.metadata(dict(cpc=['Y02E10/00']))['sections'] == ['UNCLASSIFIED']
    assert q.metadata(dict(cpc=['invalid']))['sections'] == ['UNCLASSIFIED']


def test_prior_ledger_excludes_reviewed_no_abstract_and_their_families(tmp_path):
    ledger = dict(records=[dict(identifier='US-1-A1', status='LINK'),
                           dict(identifier='US-2-A1', status='NO_ABSTRACT'),
                           dict(identifier='US-3-A1', status='PENDING_REVIEW'),
                           dict(identifier='US-4-A1', status='DEFER')])
    q.atomic_json(tmp_path/'ledger.json', ledger)
    page = dict(documents=[dict(identifier='US-1-A1', cpc=['A01B1/00', 'C01B1/00'], family_id='f1'),
                           dict(identifier='US-2-A1', ipc=['H01B1/00'], family_id='f2'),
                           dict(identifier='US-3-A1', family_id='f3')])
    q.atomic_json(tmp_path/'page.json', page)
    before = (tmp_path/'ledger.json').read_bytes(), (tmp_path/'page.json').read_bytes()
    exclusions = q.prior_exclusions(tmp_path/'ledger.json', [tmp_path/'page.json'])
    assert exclusions['identifiers'] == ['US-1-A1', 'US-2-A1', 'US-4-A1']
    assert exclusions['family_ids'] == ['f1', 'f2']
    assert exclusions['section_counts'] == {'A': 1, 'C': 1}
    assert exclusions['missing_metadata_records'] == 1
    assert exclusions['directly_reviewed'] == 2
    assert before == ((tmp_path/'ledger.json').read_bytes(), (tmp_path/'page.json').read_bytes())


def test_sparse_sections_survive_multi_class_and_abundant_fields():
    points = [point(i, ['A01B1/00']) for i in range(1, 80)]
    points += [point(80, ['A01B1/00', 'D01F1/00']), point(81, ipc=['H01B1/00']), point(82)]
    selection = q.select_pool(pool(points), q.empty_state(), prior(), limit=9)
    counts = Counter(c['assigned_bucket'] for c in selection['selected'])
    assert counts == {'A': 6, 'D': 1, 'H': 1, 'UNCLASSIFIED': 1}
    assert 'D' not in selection['absent_buckets']
    assert selection['proposed_deficits']['B'] == 1
    assert next(c for c in selection['selected'] if c['assigned_bucket'] == 'D')['sections'] == ['A', 'D']


def test_equal_availability_allocates_all_nine_buckets_within_cap():
    points = []
    for i, bucket in enumerate(q.BUCKETS):
        for j in range(12):
            points.append(point(i * 100 + j + 1, [bucket + '01A1/00'] if bucket != 'UNCLASSIFIED' else []))
    selection = q.select_pool(pool(points), q.empty_state(), prior())
    assert len(selection['selected']) == 72
    assert Counter(c['assigned_bucket'] for c in selection['selected']) == {b: 8 for b in q.BUCKETS}
    assert sum(d['status'] == 'ELIGIBLE_NOT_SELECTED_UNREVIEWED' for d in selection['dispositions']) == 36
    assert not selection['analysis_performed']


def test_all_missing_classifications_still_queue_and_report_deficits():
    selection = q.select_pool(pool([point(i) for i in range(1, 101)]), q.empty_state(), prior())
    assert len(selection['selected']) == 72
    assert {c['assigned_bucket'] for c in selection['selected']} == {'UNCLASSIFIED'}
    assert selection['absent_buckets'] == list('ABCDEFGH')
    assert all(selection['proposed_deficits'][b] == 8 for b in 'ABCDEFGH')


def test_excludes_old_publications_old_families_and_same_pool_families():
    excluded = prior()
    excluded.update(identifiers=['US-1-A1'], family_ids=['old'])
    points = [point(1, ['A01B1/00']), point(2, ['B01B1/00'], family='old'),
              point(3, ['C01B1/00'], family='same'), point(4, ['D01B1/00'], family='same'),
              point(5, ['H01B1/00'], family='0'), point(6, ['E01B1/00'], family='0')]
    result = q.select_pool(pool(points), q.empty_state(), excluded)
    assert len(result['selected']) == 3
    statuses = {d['status'] for d in result['dispositions']}
    assert statuses >= {'PREVIOUS_REVIEW_NO_ABSTRACT_OR_QUEUE', 'PREVIOUS_FAMILY', 'DUPLICATE_SELECTED_FAMILY'}
    assert {'US-5-A1', 'US-6-A1'} <= {c['publication_number'] for c in result['selected']}


def test_previous_queue_deficits_and_prior_review_gaps_get_first_turn():
    state = q.empty_state()
    state['assigned_counts']['A'] = 20
    old = prior()
    old['section_counts'] = {'B': 900, 'D': 2}
    points = [point(1, ['A01B1/00']), point(2, ['B01B1/00']), point(3, ['D01B1/00'])]
    result = q.select_pool(pool(points, state), state, old, limit=1)
    assert result['selected'][0]['assigned_bucket'] == 'D'


@pytest.mark.parametrize('limit', [0, 73, 2000])
def test_selection_hard_cap(limit):
    with pytest.raises(ValueError):
        q.select_pool(pool([]), q.empty_state(), prior(), limit)


def test_pool_hard_cap_and_hash_identity():
    with pytest.raises(ValueError, match='pool size'):
        q.select_pool(pool([point(i) for i in range(1, 2002)]), q.empty_state(), prior())
    invalid = point(1)
    invalid['id'] = str(uuid.uuid4())
    result = q.select_pool(pool([invalid]), q.empty_state(), prior())
    assert not result['selected']
    assert result['dispositions'][0]['status'] == 'INVALID_PUBLICATION_OR_HASH_ID'


def test_only_readable_actual_abstracts_are_queued_and_sql_metadata_is_recorded():
    state = q.empty_state()
    source = pool([point(1, ['A01B1/00']), point(2, ['B01B1/00']), point(3, ['C01B1/00'])], exhausted=True)
    selection = q.select_pool(source, state, prior())
    response = hydration(selection, missing=['US-2-A1'], blank=['US-3-A1'])
    response['documents'][0]['country_code'] = 'KR'
    response['documents'][0]['publication_date'] = 20241231
    batch = q.finish_batch(source, selection, response, state, prior())
    assert [d['publication_number'] for d in batch['documents']] == ['US-1-A1']
    assert batch['inventory']['actual_country_counts'] == {'KR': 1}
    assert batch['inventory']['actual_year_counts'] == {'2024': 1}
    assert batch['state_after']['scroll_exhausted'] is True
    assert batch['state_after']['exhaustive_review_complete'] is False
    assert batch['state_after']['analysis_performed'] is False
    assert batch['inventory']['missing_abstracts'] == 1
    assert len(batch['state_after']['attempted_identifiers']) == 3
    from triz.effect_manual_review import source_fingerprint
    assert batch['documents'][0]['source_fingerprint'] == source_fingerprint(batch['documents'][0])
    with pytest.raises(ValueError, match='scroll ended'):
        q.pool_request(batch['state_after'])


def test_changed_classification_and_family_are_not_silently_counted():
    state = q.empty_state()
    source = pool([point(1, ['A01B1/00']), point(2, ['B01B1/00']), point(3, ['C01B1/00'])])
    old = prior()
    old['family_ids'] = ['reviewed']
    selection = q.select_pool(source, state, old)
    response = hydration(selection)
    docs = {d['publication_number']: d for d in response['documents']}
    docs['US-1-A1']['cpc'] = ['H01B1/00']
    docs['US-2-A1']['family_id'] = 'reviewed'
    batch = q.finish_batch(source, selection, response, state, old)
    assert len(batch['documents']) == 1
    assert {d['status'] for d in batch['dispositions']} >= {
        'CLASSIFICATION_CHANGED_SINCE_VECTOR_INDEX', 'DUPLICATE_HYDRATED_FAMILY'}


def test_hydration_unrequested_duplicate_or_stale_selection_rejected():
    state = q.empty_state()
    source = pool([point(1)])
    selection = q.select_pool(source, state, prior())
    response = hydration(selection)
    response['documents'].append({**response['documents'][0], 'publication_number': 'US-2-A1'})
    with pytest.raises(ValueError, match='unrequested'):
        q.finish_batch(source, selection, response, state, prior())
    response = hydration(selection)
    response['documents'].append(response['documents'][0])
    with pytest.raises(ValueError, match='duplicate'):
        q.finish_batch(source, selection, response, state, prior())
    excluded = prior()
    excluded['identifiers'] = ['US-1-A1']
    with pytest.raises(ValueError, match='exclusion ledger changed'):
        q.finish_batch(source, selection, hydration(selection), state, excluded)


def test_commit_is_immutable_idempotent_and_recovers_cursor_write_failure(tmp_path, monkeypatch):
    state = q.empty_state()
    source = pool([point(1)])
    selection = q.select_pool(source, state, prior())
    response = hydration(selection)
    real_atomic = q.atomic_json
    def fail_state(path, value):
        if Path(path).name == 'state.json':
            raise OSError('simulated interruption')
        real_atomic(path, value)
    monkeypatch.setattr(q, 'atomic_json', fail_state)
    with pytest.raises(OSError):
        q.commit_batch(tmp_path, source, selection, response, prior())
    assert (tmp_path/'batch-000001.json').exists()
    assert not (tmp_path/'state.json').exists()
    assert not (tmp_path/'.commit.lock').exists()
    monkeypatch.setattr(q, 'atomic_json', real_atomic)
    batch = q.commit_batch(tmp_path, source, selection, response, prior())
    before = (tmp_path/'batch-000001.json').read_bytes()
    assert q.load_state(tmp_path) == batch['state_after']
    assert q.commit_batch(tmp_path, source, selection, response, prior()) == batch
    assert (tmp_path/'batch-000001.json').read_bytes() == before
    response['documents'][0]['abstract'] = 'Changed source'
    with pytest.raises(ValueError, match='Immutable'):
        q.commit_batch(tmp_path, source, selection, response, prior())


def test_resume_does_not_reselect_prior_queue_or_family(tmp_path):
    state = q.empty_state()
    source = pool([point(1, ['A01B1/00'], family='f1')])
    selection = q.select_pool(source, state, prior())
    batch = q.commit_batch(tmp_path, source, selection, hydration(selection), prior())
    state = batch['state_after']
    following = pool([point(1, ['A01B1/00'], family='f1'), point(2, ['B01B1/00'], family='f1'), point(3)], state)
    selection = q.select_pool(following, state, prior())
    assert [c['publication_number'] for c in selection['selected']] == ['US-3-A1']
    assert q.pool_request(state)['offset'] == source['inventory']['next_offset']
    with pytest.raises(ValueError, match='current queue cursor'):
        q.select_pool(source, state, prior())


def test_remote_pool_scroll_is_bounded_metadata_only_and_no_filter():
    remote = helper()
    points = [point(i) for i in range(1, 2201)]
    calls = []
    class Client:
        def scroll(self, **kwargs):
            calls.append(kwargs)
            start = len(calls[:-1]) * 256
            batch = points[start:start + kwargs['limit']]
            return [SimpleNamespace(id=p['id'], payload={**p['payload'], 'secret_unrelated': 'omit'}) for p in batch], batch[-1]['id']
    response = remote.read_pool(q.pool_request(q.empty_state()), Client(), 'test-patents')
    assert len(response['points']) == 2000
    assert len(calls) == 8
    assert all(c['with_vectors'] is False and 'scroll_filter' not in c for c in calls)
    assert all(set(c['with_payload']) == set(remote.PAYLOAD_FIELDS) for c in calls)
    assert all('secret_unrelated' not in p['payload'] for p in response['points'])
    assert response['inventory']['sql_queries'] == 0
    assert not response['inventory']['scroll_exhausted']


def test_remote_pool_request_budget_does_not_claim_exhaustion():
    remote = helper()
    class Client:
        def __init__(self):
            self.calls = 0
        def scroll(self, **kwargs):
            self.calls += 1
            p = point(self.calls)
            return [SimpleNamespace(**p)], p['id']
    response = remote.read_pool(q.pool_request(q.empty_state()), Client(), 'test-patents')
    assert len(response['points']) == 16
    assert response['inventory']['request_budget_reached']
    assert response['inventory']['scroll_exhausted'] is False


def test_remote_hydrates_only_selected_numbers_and_never_calls_fetch_for_empty():
    remote = helper()
    calls = []
    def fetch(numbers):
        calls.append(numbers)
        return {n: dict(title='Title', abstract='Abstract', publication_date=20200101,
                        ipc=['H01B1/00'], country_code='US') for n in numbers}
    request = dict(version=q.VERSION, operation='hydrate', selection_sha256='a' * 64,
                   publication_numbers=['US-1-A1', 'US-2-A1'])
    response = remote.read_hydration(request, fetch, lambda d: (b'\x01' * 32, b''), lambda n: n.replace('-', ''))
    assert calls == [['US-1-A1', 'US-2-A1']]
    assert len(response['documents']) == 2
    assert response['documents'][0]['ipc'] == ['H01B1/00']
    assert response['inventory']['sql_scope'] == 'selected_publication_primary_keys_only'
    request['publication_numbers'] = []
    remote.read_hydration(request, fetch, lambda d: (b'', b''), lambda n: n)
    assert len(calls) == 1
    request['publication_numbers'] = [f'US-{i}-A1' for i in range(73)]
    with pytest.raises(ValueError):
        remote.read_hydration(request, fetch, lambda d: (b'', b''), lambda n: n)
    assert len(calls) == 1


def test_remote_main_uses_configured_existing_collection(monkeypatch):
    remote = helper()
    from triz.tools import vector_patents
    from triz.settings import settings
    monkeypatch.setattr(settings, 'patent_collection', 'configured-patents')
    monkeypatch.setattr(vector_patents, 'client', lambda: 'readonly-client')
    observed = []
    monkeypatch.setattr(remote, 'read_pool', lambda config, client, collection: observed.append((client, collection)))
    remote.main(q.pool_request(q.empty_state()))
    assert observed == [('readonly-client', 'configured-patents')]


def test_cli_local_workflow_preserves_prior_files(tmp_path, monkeypatch, capsys):
    import sys
    path = Path(__file__).resolve().parents[1] / 'scripts/prepare_balanced_patent_review.py'
    spec = importlib.util.spec_from_file_location('balanced_local_cli', path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    old = tmp_path/'old'
    output = tmp_path/'balanced'
    q.atomic_json(old/'review-ledger.json', dict(records=[]))
    q.atomic_json(old/'page-000001.json', dict(documents=[]))
    before = {p.name: p.read_bytes() for p in old.iterdir()}
    def run(action, *arguments):
        monkeypatch.setattr(sys, 'argv', ['prepare', action, '--queue', str(output), '--prior-pages', str(old), *map(str, arguments)])
        cli.main()
    run('request', '--output', tmp_path/'request.json')
    assert q.read_json(tmp_path/'request.json')['operation'] == 'pool'
    source = pool([point(1, ipc=['E01B1/00'])])
    q.atomic_json(tmp_path/'pool.json', source)
    run('select', '--pool', tmp_path/'pool.json', '--output', tmp_path/'selection.json',
        '--hydrate-request', tmp_path/'hydrate-request.json')
    selection = q.read_json(tmp_path/'selection.json')
    q.atomic_json(tmp_path/'hydration.json', hydration(selection))
    run('commit', '--pool', tmp_path/'pool.json', '--selection', tmp_path/'selection.json',
        '--hydration', tmp_path/'hydration.json')
    run('status')
    assert q.load_state(output)['queued_records'] == 1
    assert before == {p.name: p.read_bytes() for p in old.iterdir()}
    with pytest.raises(SystemExit):
        run('request', '--output', old/'forbidden.json')
    assert not (old/'forbidden.json').exists()
    capsys.readouterr()


def test_additive_sequential_harvest_metadata_retains_review_fingerprint(monkeypatch):
    from sqlalchemy import create_engine
    from triz import effect_source_pages, patent_corpus
    from triz.effect_manual_review import source_fingerprint
    engine = create_engine('sqlite://')
    patent_corpus.metadata.create_all(engine)
    monkeypatch.setattr(patent_corpus, 'engine', lambda: engine)
    document = dict(title='Title', abstract='Abstract', publication_date=20230515,
                    country_code='JP', cpc=[], ipc=['H01L1/00'], family_id='family')
    content_hash, blob = patent_corpus.encode(document)
    with engine.begin() as connection:
        connection.execute(patent_corpus.patents.insert().values(
            publication_number='JP-1-A1', content_hash=content_hash, document=blob, pending=0))
    new = effect_source_pages.harvest_page(limit=1)['documents'][0]
    assert new['ipc'] == ['H01L1/00']
    assert new['country_code'] == 'JP'
    assert new['publication_date'] == 20230515 and new['year'] == '2023'
    legacy = {k: v for k, v in new.items() if k not in {'ipc', 'country_code', 'publication_date'}}
    legacy['year'] = ''
    assert source_fingerprint(legacy) == source_fingerprint(new)
    engine.dispose()
