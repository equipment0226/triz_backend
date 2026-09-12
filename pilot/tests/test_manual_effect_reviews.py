import copy
import json

import pytest

from triz.effect_manual_review import record_decisions, coverage, merge_explicit_links, read_pages
from triz.effect_mining import mine
from triz.effect_review import review_catalog


def pages():
    return [dict(inventory=dict(cursor='', next_cursor='A-2', upper_bound='Z-9',
        exported_records=2, complete=False, corpus_accounting={'documents':1000}),
        documents=[dict(identifier='A-1', title='Communication', abstract='Time slots share a channel.',
            url='https://example.org/patent', content_hash='abc', retrieval_scope='stored_patent_abstract'),
            dict(identifier='A-2', title='Title only', abstract='', content_hash='def')])]


def test_review_binding_is_immutable_and_changed_source_needs_new_read(tmp_path):
    decisions = tmp_path/'decisions.tsv'
    decisions.write_text('A-1|LINK|tdm|직접 읽은 슬롯 분할\n', encoding='utf-8')
    source = pages(); output = tmp_path/'review.json'
    snapshot = record_decisions(decisions, source, {'tdm'}, output)
    assert record_decisions(decisions, source, {'tdm'}, output) == snapshot
    decisions.write_bytes(decisions.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert record_decisions(decisions, source, {'tdm'}, output) == snapshot
    summary, records = coverage(source, [snapshot])
    assert summary['abstracts_directly_reviewed'] == 1
    assert summary['no_abstract'] == 1 and summary['cursor'] == 'A-2'
    assert records[1]['status'] == 'NO_ABSTRACT'
    changed = copy.deepcopy(source)
    changed[0]['documents'][0]['abstract'] += ' Changed text.'
    summary, _ = coverage(changed, [snapshot])
    assert summary['pending_review'] == 1 and summary['cursor'] == ''
    with pytest.raises(ValueError, match='Immutable'):
        record_decisions(decisions, changed, {'tdm'}, output)
    merge_explicit_links(changed, [snapshot], tmp_path)
    assert json.loads((tmp_path/'literature_links.json').read_text()) == {}


def test_only_explicit_valid_links_can_be_published(tmp_path):
    decisions = tmp_path/'decisions.tsv'; output = tmp_path/'review.json'
    decisions.write_text('A-1|LINK|unknown|manual\n', encoding='utf-8')
    with pytest.raises(ValueError, match='canonical'):
        record_decisions(decisions, pages(), {'tdm'}, output)
    decisions.write_text('A-2|DEFER||title alone\n', encoding='utf-8')
    with pytest.raises(ValueError, match='available abstract'):
        record_decisions(decisions, pages(), {'tdm'}, output)
    decisions.write_text('A-1|DEFER||not enough mechanism\n', encoding='utf-8')
    snapshot = record_decisions(decisions, pages(), {'tdm'}, output)
    merge_explicit_links(pages(), [snapshot], tmp_path)
    assert json.loads((tmp_path/'literature_links.json').read_text()) == {}


def test_missing_page_cannot_advance_checkpoint(tmp_path):
    page = pages()[0]; page['inventory']['cursor'] = 'A-0'
    path = tmp_path/'page.json'; path.write_text(json.dumps(page))
    with pytest.raises(ValueError, match='Noncontiguous'):
        read_pages([path])


def test_research_policy_blocks_default_model_calls_before_writing(tmp_path):
    with pytest.raises(RuntimeError, match='RESEARCH_LLM_API_DISABLED'):
        mine([], tmp_path/'mining')
    with pytest.raises(RuntimeError, match='RESEARCH_LLM_API_DISABLED'):
        review_catalog([], [], tmp_path/'review')
    assert not (tmp_path/'mining').exists()
    assert not (tmp_path/'review').exists()
