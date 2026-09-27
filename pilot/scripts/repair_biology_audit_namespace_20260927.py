"""Recover the installation audit after an agent reused its reserved filename."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / 'research/effects'


def main():
    journal = D / 'audit-namespace-repair-2026-09-27-biology.json'
    assert not journal.exists(), 'Repair already performed'
    moved = []
    for number in ('01', '02'):
        source = D / f'audit-additions-2026-09-27-biology-{number}.json'
        target = D / f'source-review-2026-09-27-biology-{number}.json'
        data = json.loads(source.read_text(encoding='utf-8'))
        assert 'evidence' in data and 'decisions' not in data
        assert not target.exists()
        source.rename(target)
        moved.append({'from': source.name, 'to': target.name})
    batch = D / 'additions-2026-09-27-biology-01.tsv'
    raw = batch.read_text(encoding='utf-8')
    digest = hashlib.sha256(raw.encode()).hexdigest()
    assert digest == '20960bee44c74a59cee94e5b6695a758dbee91ab8eb283dae71c7761a8eb168c'
    rows = [line.split('|') for line in raw.splitlines() if line and not line.startswith('#')]
    assert len(rows) == 20 and all(len(row) == 10 for row in rows)
    catalog = {line.split('|')[0]: line.split('|') for line in (D / 'catalog.tsv').read_text(encoding='utf-8').splitlines()
               if line and not line.startswith(('@', '#'))}
    references = json.loads((D / 'references.json').read_text(encoding='utf-8'))
    redirects = json.loads((D / 'mechanism_redirects.json').read_text(encoding='utf-8'))
    decisions = []
    for key, group, name, principle, conditions, title, url, scope, nearest, boundary in rows:
        ref = 'research-20260927-' + key
        assert catalog[key] == [key, name, principle, conditions, ref]
        assert references[ref] == [title, url]
        decisions.append(dict(key=key, group=int(group), related_keys=[redirects.get(k, k) for k in nearest.split(',')],
                              decision='KEEP_WITH_EXPLICIT_BOUNDARY', boundary=boundary, source_url=url,
                              retrieval_scope=scope))
    audit = dict(batch=batch.name, method='conversation_reasoning', external_llm_calls=0,
                 before=1539, added=20, after=1559, target=2000, source_sha256=digest, decisions=decisions)
    (D / ('audit-' + batch.stem + '.json')).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    journal.write_text(json.dumps(dict(moved=moved, restored_audit='audit-' + batch.stem + '.json',
        batch_sha256=digest, installed_rows_and_reference_labels_verified=20,
        reason='An evidence note overwrote the reserved installer audit filename. The unchanged first 20 authored rows and installed records reconstruct the audit; evidence notes are retained separately.',
        extra_ten_rows_installed=False), indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'restored_installation_audit_rows': 20, 'evidence_files_preserved': 2}))


if __name__ == '__main__':
    main()
