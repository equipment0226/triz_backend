"""Check canonical identity, authored decisions and source retention, not scientific equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
from publish_effects import build

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'research/effects'
K = ROOT / 'triz/knowledge'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', action='store_true', help='Check current authored data in memory without publishing')
    args = parser.parse_args()
    progress = read(D / 'resume-2026-09-27.json')
    baseline = D / progress['baseline_directory']
    groups, evidence, registry, counts, unresolved = build(D, K)
    # Historical topic placeholders coexist with real linked evidence. They are
    # recorded by the publisher, not mistaken for independently checked sources.
    assert all(item['has_other_source'] for item in unresolved), ('Unsupported topic-only card', unresolved)
    if not args.draft:
        assert groups == read(K / 'effects.json'), 'Published catalog differs from authored data'
        assert evidence == read(K / 'effects_sources.json'), 'Published evidence differs from authored data'
    entries = [e for group in groups for e in group['effects']]
    current = {e['id']: e for e in entries}
    by_key = {e['mechanism_key']: identifier for identifier, e in evidence.items()}
    legacy = {old: e['id'] for e in entries for old in e.get('legacy_ids', [])}
    assert len(groups) == 19
    assert len(entries) == len(current) == len(by_key)
    assert len({e['name'] for e in entries}) == len(entries)
    assert len({e['principle'] for e in entries}) == len(entries)
    assert len(legacy) == sum(len(e.get('legacy_ids', [])) for e in entries)
    assert set(legacy).isdisjoint(current)
    assert current.keys() == evidence.keys()
    assert all(e['sources'] for e in evidence.values())
    baseline_entries = [e for group in read(baseline / 'effects.json') for e in group['effects']]
    baseline_evidence = read(baseline / 'effects_sources.json')
    assert len(baseline_entries) == 1500 == progress['campaign_initial_effects']
    assert digest(baseline / 'catalog.tsv') == progress['baseline_sha256']
    for old in baseline_entries:
        identifier = old['id']
        target = legacy.get(identifier, identifier)
        assert target in current, ('Lost baseline ID', identifier)
        old_sources = baseline_evidence[identifier]['sources']
        new_sources = evidence[target]['sources']
        assert {s['url'] for s in old_sources} <= {s['url'] for s in new_sources}, ('Lost source URL', identifier)
        assert {(s.get('identifier'), s['url']) for s in old_sources} <= {
            (s.get('identifier'), s['url']) for s in new_sources}, ('Lost source identifier', identifier)
        for previous in old.get('legacy_ids', []):
            assert legacy.get(previous, previous) == target, ('Lost historical legacy ID', previous)
    redirects = read(D / 'mechanism_redirects.json')
    assert all(old not in by_key and target in by_key for old, target in redirects.items())
    merges = []
    for path in sorted(D.glob('merge-decisions-2026-09-27-*.json')):
        decisions = read(path)
        audit = read(D / ('audit-' + path.stem + '.json'))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == audit['decisions_sha256']
        assert len(decisions) == audit['merged'] == len(audit['decisions'])
        for decision in decisions:
            assert decision['reason'] and redirects[decision['source']] == redirects.get(decision['target'], decision['target'])
        merges.extend(decisions)
    assert len({d['source'] for d in merges}) == len(merges) == progress['merged_during_campaign']
    new_keys = set()
    audits = [read(p) for p in sorted(D.glob('audit-additions-2026-09-27-*.json'))]
    for audit in audits:
        batch = D / audit['batch']
        assert digest(batch) == audit['source_sha256'], ('Changed installed batch', batch.name)
        assert audit['added'] == len(audit['decisions']) and audit['target'] == 2000
        for decision in audit['decisions']:
            key = decision['key']
            target = redirects.get(key, key)
            assert key not in new_keys and target in by_key, ('Missing/repeated new key', key)
            assert all(item['key'] != target for item in unresolved), ('Unresolved new reference', key)
            new_keys.add(key)
            assert decision['boundary'] and decision['related_keys']
            assert all(redirects.get(k, k) in by_key for k in decision['related_keys']), key
            sources = evidence[by_key[target]]['sources']
            source = next(s for s in sources if s['url'] == decision['source_url']
                          and s.get('identifier') == 'REF-research-20260927-' + key)
            assert source['retrieval_scope'] == decision['retrieval_scope']
            assert source['review_method'] == 'conversation_reasoning'
    assert len(entries) == 1500 + len(new_keys) - len(merges)
    assert progress['effects'] == len(entries) <= progress['target'] == 2000
    assert progress['campaign_new_effects'] == progress['new_effects'] == len(entries) - 1500
    assert progress['completed_batches'] == len(audits)
    assert read(D / 'manual-progress.json') == read(baseline / 'manual-progress.json'), 'Manual patent cursor changed'
    result = dict(effects=len(entries), target=2000, remaining=2000-len(entries), groups=19,
        baseline_effects=1500, gross_additions=len(new_keys), merged=len(merges), net_additions=len(entries)-1500,
        batches=len(audits), with_sources=counts['with_sources'], baseline_ids_preserved=1500,
        baseline_source_urls_preserved=True, baseline_source_identifiers_preserved=True,
        legacy_ids_preserved=True, redirect_targets_valid=True, authored_batch_hashes_valid=True,
        source_observation_scopes_preserved=True, historical_topic_placeholders_with_other_sources=len(unresolved),
        manual_patent_cursor_advanced=False,
        external_llm_calls=0, catalog_sha256=digest(D / 'catalog.tsv'),
        catalog_hash_basis='UTF-8 text with LF newlines', draft=args.draft,
        caveat='Structural identity and evidence retention checks; not experimental validation or all-pairs semantic proof.')
    if not args.draft:
        assert result['remaining'] == 0, 'Requested target not reached'
        (D / 'verification-2026-09-27.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
