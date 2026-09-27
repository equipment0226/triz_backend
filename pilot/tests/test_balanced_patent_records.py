import copy
import importlib.util
from pathlib import Path

import pytest

from triz.effect_manual_review import source_fingerprint, merge_review_records


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/record_balanced_patent_reviews.py'
    spec = importlib.util.spec_from_file_location('balanced_records', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture():
    doc = dict(identifier='US-1-A1', title='Public abstract', abstract='Heat transfer through a solid.',
        content_hash='a' * 64, abstract_truncated=False, url='https://example.org/patent',
        retrieval_scope='stored_patent_abstract', assigned_bucket='F',
        balanced_metadata=dict(sections=['F', 'H'], country='US', year='2020'))
    doc['source_fingerprint'] = source_fingerprint(doc)
    batch = dict(documents=[doc], candidate_pool=dict(points=[{}, {}, {}]),
        inventory=dict(selected_for_hydration=2, missing_abstracts=1))
    snapshot = dict(reviews=[dict(identifier=doc['identifier'], source_fingerprint=doc['source_fingerprint'],
        content_hash=doc['content_hash'], decision='LINK', keys=['fourier-conduction'], reason='Explicit conduction path')])
    return batch, snapshot


def test_metadata_and_missing_abstracts_never_count_as_review():
    batch, snapshot = fixture()
    result, _ = module().summarize([batch], [])
    assert result['metadata_points_scanned'] == 3
    assert result['selected_for_hydration'] == 2
    assert result['abstract_fields_directly_reviewed'] == 0
    assert result['pending_review'] == result['no_abstract'] == 1
    result, _ = module().summarize([batch], [snapshot])
    assert result['abstract_fields_directly_reviewed'] == 1 and result['pending_review'] == 0
    assert result['reviewed_assigned_sections']['F'] == 1
    assert result['reviewed_assigned_sections']['H'] == 0
    assert result['reviewed_section_memberships'] == {'F': 1, 'H': 1}
    assert not result['old_sequential_cursor_advanced'] and not result['exhaustive_review_complete']


def test_changed_source_cannot_reuse_old_decisions_or_write_links(tmp_path):
    batch, snapshot = fixture()
    result, documents = module().summarize([batch], [snapshot])
    documents['US-1-A1']['abstract'] = 'Different content'
    with pytest.raises(ValueError, match='Source changed'):
        merge_review_records(result['records'], documents, tmp_path)
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError, match='Changed immutable'):
        module().summarize([batch], [snapshot])
    batch['documents'][0]['source_fingerprint'] = source_fingerprint(batch['documents'][0])
    result, _ = module().summarize([batch], [snapshot])
    assert result['abstract_fields_directly_reviewed'] == 0


def test_conflicts_and_duplicate_batches_are_rejected():
    batch, snapshot = fixture()
    changed = copy.deepcopy(snapshot)
    changed['reviews'][0]['decision'] = 'DEFER'
    with pytest.raises(ValueError, match='Conflicting'):
        module().summarize([batch], [snapshot, changed])
    with pytest.raises(ValueError, match='Repeated queued'):
        module().summarize([batch, batch], [snapshot])
