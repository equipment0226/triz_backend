import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from triz.effect_mining import extract_batch, prepare_documents
from triz import effect_source_pages,patent_corpus


path=Path(__file__).resolve().parents[1]/'scripts/sweep_patent_effects.py'
spec=importlib.util.spec_from_file_location('patent_effect_sweep',path)
sweep=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


def test_direct_pages_respect_bounds_and_omit_nonpublic_fields(monkeypatch):
    engine=create_engine('sqlite://')
    patent_corpus.metadata.create_all(engine)
    monkeypatch.setattr(patent_corpus,'engine',lambda:engine)
    with engine.begin() as connection:
        for number in ['AP-001-A','AP-002-A','US-001-A']:
            digest,blob=patent_corpus.encode(dict(title='Public title',abstract='Public abstract',private_note='never export this',claims='not harvested'))
            connection.execute(patent_corpus.patents.insert().values(publication_number=number,content_hash=digest,document=blob,pending=0))
    first=effect_source_pages.harvest_page(limit=1)
    assert first['inventory']['upper_bound']=='US-001-A'
    assert [d['identifier'] for d in first['documents']]==['AP-001-A']
    second=effect_source_pages.harvest_page(cursor='AP-001-A',upper_bound='AP-002-A',limit=10)
    assert [d['identifier'] for d in second['documents']]==['AP-002-A']
    assert second['inventory']['complete']
    assert second['documents'][0]['url']=='https://patents.google.com/patent/AP002A/en'
    assert 'private_note' not in json.dumps(second) and 'never export' not in json.dumps(second)
    assert 'claims' not in second['documents'][0]


def test_server_bootstrap_preserves_advanced_volume_and_rejects_zip_escape(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(path.parent))
    import effect_worker
    archive=tmp_path/'seed.zip';volume=tmp_path/'volume';volume.mkdir()
    with zipfile.ZipFile(archive,'w') as seed:
        seed.writestr('progress.json','{"cursor":"old"}')
        seed.writestr('ledger.sqlite3',b'fixture ledger')
        seed.writestr('sweep-001-page-000001/receipt.json','{}')
    effect_worker.bootstrap(volume,archive)
    assert (volume/'sweep-001-page-000001/receipt.json').exists()
    (volume/'progress.json').write_text('{"cursor":"new"}')
    effect_worker.bootstrap(volume,archive)
    assert json.loads((volume/'progress.json').read_text())['cursor']=='new'
    other=tmp_path/'other';other.mkdir()
    with zipfile.ZipFile(archive,'w') as seed:seed.writestr('../escape.txt','bad')
    with pytest.raises(ValueError,match='Unsafe seed path'):effect_worker.bootstrap(other,archive)
    assert not (tmp_path/'escape.txt').exists()


def test_committed_page_recovers_after_json_checkpoint_failure(tmp_path):
    ledger=sweep.open_ledger(tmp_path)
    old=dict(sweep=1,pages=0,cursor='',scanned=0)
    sweep.atomic_json(tmp_path/'progress.json',old)
    new=dict(sweep=1,pages=1,cursor='US-2-A',scanned=2)
    changes=[('US-1-A','h1','a1','ANALYZED','page1'),('US-2-A','h2','','INSUFFICIENT_TEXT','page1')]
    sweep.commit_page(ledger,changes,new,dict(records=2))
    ledger.close()
    # Simulate losing the process immediately after the database commit: the
    # public progress file is still stale, while cursor and records must agree.
    ledger=sweep.open_ledger(tmp_path)
    assert sweep.committed_progress(ledger,tmp_path)==new
    assert ledger.execute('SELECT count(*) FROM records').fetchone()[0]==2
    # A failed page transaction cannot leave a newer document ledger behind.
    with pytest.raises(Exception):
        sweep.commit_page(ledger,[('US-3-A','h3','a3','ANALYZED','page1')],new,{})
    assert ledger.execute('SELECT publication FROM records WHERE publication=?',('US-3-A',)).fetchone() is None
    assert sweep.committed_progress(ledger,tmp_path)==new
    ledger.close()


def test_worker_lock_prevents_double_processing_and_releases(tmp_path):
    with sweep.exclusive_run(tmp_path):
        with pytest.raises(RuntimeError,match='already owns'):
            with sweep.exclusive_run(tmp_path):pass
    with sweep.exclusive_run(tmp_path):pass


def test_empty_abstract_is_accounted_for_without_fabricating_or_calling_model():
    empty=prepare_documents([dict(identifier='empty',title='A very impressive invention',abstract='')])
    def forbidden(**kwargs):raise AssertionError('An empty abstract must not spend tokens')
    result=extract_batch(empty,forbidden)
    assert not result['effects'] and result['usage']['tokens_in']==0
    assert result['reviews'][0]['status']=='INSUFFICIENT_TEXT'
    mixed=prepare_documents([dict(identifier='readable',abstract='The text describes a mechanism.'),dict(identifier='empty',abstract='')])
    def model(**kwargs):
        packet=json.loads(kwargs['user'])
        assert [d['id'] for d in packet['documents']]==['D000001']
        return SimpleNamespace(data=dict(effects=[],reviews=[dict(id='D000001',status='NO_MECHANISM',reason='Insufficient causal detail')]),
            tokens_in=10,tokens_out=5,cost_usd=0,model='fixture')
    result=extract_batch(mixed,model)
    assert {r['id']:r['status'] for r in result['reviews']}=={'D000001':'NO_MECHANISM','D000002':'INSUFFICIENT_TEXT'}
