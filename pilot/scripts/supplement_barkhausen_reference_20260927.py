"""Attach rejected duplicate research to its existing canonical effect."""
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / 'research/effects'


def main():
    audit = D / 'source-supplement-2026-09-27-barkhausen.json'
    assert not audit.exists(), 'Supplement already applied'
    ref = 'research-20260927-barkhausen-source-supplement'
    title = 'Dynamics of a ferromagnetic domain wall: Avalanches, depinning transition, and the Barkhausen effect'
    url = 'https://journals.aps.org/prb/abstract/10.1103/PhysRevB.58.6353'
    refs = json.loads((D / 'references.json').read_text(encoding='utf-8'))
    observations = json.loads((D / 'reference_observations.json').read_text(encoding='utf-8'))
    assert ref not in refs
    lines = (D / 'catalog.tsv').read_text(encoding='utf-8').splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith('barkhausen-noise|'))
    original = lines[index].split('|')
    row = original.copy()
    row[2] = '자화 중 고정되어 있던 자구벽이 불연속적으로 탈고정·이동하면 자속 변화 신호가 발생한다. 이 잡음에서 강자성체의 조직·응력 상태를 추정할 수 있다.'
    row[3] = '강자성 재료·자벽 구조·결함·자화 속도·반자기장·수신 조건을 확인한다. 조직·경도·응력·표면 상태의 중첩을 보정하며 잡음만으로 원인을 하나로 확정하지 않는다.'
    row[4] += ',' + ref
    lines[index] = '|'.join(row)
    refs[ref] = [title, url]
    observations[ref] = dict(retrieval_scope='stored_search_excerpt', accessed_at='2026-09-27',
        review_method='conversation_reasoning',
        supports='출판자 원저 초록 발췌의 자벽 탈고정·눈사태 이동과 구동률·반자기장 의존성을 확인. 전체 실험 데이터 재분석은 아님.')
    for path, data in ((D / 'references.json', refs), (D / 'reference_observations.json', observations),
                       (audit, dict(key=row[0], original_card=original, updated_card=row, reference=ref,
                         source_title=title, source_url=url, new_canonical_effects=0,
                         reason='The proposed new Barkhausen key described an existing mechanism; retain only its added evidence and condition detail.'))):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (D / 'catalog.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'existing_card_supplemented': row[0], 'new_effects': 0}))


if __name__ == '__main__':
    main()
