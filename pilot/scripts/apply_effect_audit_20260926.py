"""Apply explicit editorial merges; archive all cards and preserve source/ID history."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triz.effect_mining import atomic_json

D = ROOT / 'research/effects'
def read(name):
    return json.loads((D / name).read_text(encoding='utf-8'))

def main():
    archive = D / 'audit-2026-09-26-before'
    if archive.exists():
        raise SystemExit('One-shot migration already has an archive; inspect before retrying.')
    lines = (D / 'catalog.tsv').read_text(encoding='utf-8').splitlines()
    cards = {r[0]: r for l in lines if l and not l.startswith(('#', '@')) for r in [l.split('|')]}
    assert len(cards) == 959
    decisions = [l.split('|') for l in (D / 'merge-decisions-2026-09-26.tsv').read_text(encoding='utf-8').splitlines() if l and not l.startswith('#')]
    registry = read('identifiers.json'); metadata = read('editorial_metadata.json')
    links = read('literature_links.json'); literature = read('accepted_literature_sources.json')
    redirects = read('mechanism_redirects.json')
    evidence = json.loads((ROOT / 'triz/knowledge/effects_sources.json').read_text(encoding='utf-8'))
    originals = []
    for source, target, reason in decisions:
        assert source in cards and target in cards and target not in {x[0] for x in decisions}
        prior = metadata.pop(source, {})
        item = metadata.setdefault(target, {})
        item['legacy_ids'] = list(dict.fromkeys([*item.get('legacy_ids', []), registry[source], *prior.get('legacy_ids', [])]))
        item['aliases'] = list(dict.fromkeys([*item.get('aliases', []), cards[source][1], source.replace('-', ' '), *prior.get('aliases', [])]))
        sid = 'MERGED-20260926-' + source
        literature[sid] = {'sources': evidence[registry[source]]['sources']}
        links[target] = list(dict.fromkeys([*links.get(target, []), *links.pop(source, []), sid]))
        redirects[source] = target
        originals.append(dict(source=source, target=target, reason=reason, original_card=cards[source], original_metadata=prior, original_evidence=evidence[registry[source]]))
    for old, target in list(redirects.items()):
        seen = {old}
        while target in redirects:
            assert target not in seen, 'Redirect cycle'
            seen.add(target); target = redirects[target]
        redirects[old] = target
    edits = {
        'electrochemical-cell': ['전기화학 전지·연속 공급 연료전지', '분리된 산화·환원 반응의 전자를 외부 회로로 흘려 전력을 얻는다. 연료전지는 반응물을 계속 공급하는 운전 방식이다.', '전극·전해질과 이온·전자 경로가 필요하다. 과전압·부반응·고갈을 고려하며 연속 공급에서는 촉매 오염·수분·열 관리도 필요하다.'],
        'adsorption': ['흡착·탈착과 재생 분리', '성분이 고체 표면·기공과 선택적으로 상호작용해 농축된다. 압력변동 흡착은 분압을 순환하여 흡착·탈착시키는 재생 방식이다.', '흡착제·선택도·등온선·확산·접촉 시간을 확인한다. 포화·경쟁 흡착·이력을 고려하고 압력 재생에는 퍼지·압축 에너지가 필요하다.'],
        'chromatography': ['크로마토그래피와 이동층 모사', '이동상과 고정상에 대한 성분별 상호작용 차이로 이동 속도를 나눈다. 모사 이동층은 포트를 주기적으로 전환하여 연속 역류 접촉을 구현한다.', '고정상·용리 조건·과부하·확산·압력 손실을 확인한다. 모사 이동층에는 구간별 유량·포트 전환 주기·주기 정상상태 검증이 추가된다.'],
        'hydrostatic-pressure-compensation': ['액주 정수압에 의한 보상·액면 검출·봉수', '유효 중력장에서 액체 밀도와 높이차가 압력차를 정한다. 이를 보상 압력, 압력식 액면 판독 또는 봉수의 기체 통과 문턱으로 사용한다.', '밀도·가속도·높이·기준압을 확인한다. 자세·기포·유동·상부 압력·온도는 보정 대상이며 증발·사이펀은 봉수를 소실시킨다. 완전 기밀을 보장하지 않는다.'],
        'mechanical-resonance-property-sensing': ['기계 공진 변화에 의한 질량·강성 계측', '질량·강성·경계조건이 고유 진동수와 모드를 바꾸므로 기준 상태와 비교해 부착 질량·물성을 추정한다. 수정진동자 미량저울은 그 구현이다.', '온도·부가 질량·감쇠·지지 조건을 분리한다. 수정의 단순 질량 환산은 얇고 단단한 균일막에서 유효하며 액체 점성·점탄성은 보정한다. 한 주파수로 질량과 강성을 모두 정할 수 없다.'],
        'fluorescence-sensing': ['형광 세기·파장·수명 검출', '광여기 형광의 세기·파장·감쇠 시간으로 물질과 상태를 추정한다. 효소 절단에 의한 소광체 분리와 온도 의존 발광 변화도 검출 응용이다.', '여기·검출 대역, 기기 응답·다중 수명·광표백·배경·광자 수를 고려한다. 소광 해제에는 기질·표지 위치·검량이 필요하다. 모든 소광을 FRET로 단정하거나 수명의 농도 독립성을 보장하지 않는다.'],
        'absorption-spectroscopy': ['흡수 분광·소멸장 계면 분광', '특정 파장의 흡수량으로 성분·농도를 추정한다. 전반사 소멸장을 이용하면 경계면 가까운 시료의 흡수를 선택적으로 읽을 수 있다.', '흡수 대역·광경로·기준 보정·산란·고농도 비선형성을 확인한다. 소멸장 방식은 굴절률·입사각·침투 깊이·접촉에 의존하며 벌크 전체의 균일 측정이 아니다.'],
        'negative-feedback': ['음의 피드백과 변화율 제동', '목표와 측정값의 오차를 되돌려 입력을 보정한다. 측정량 변화율을 사용하는 제동도 피드백 구현이며 급격한 변화를 억제할 수 있다.', '관측·구동 가능성·안정성·지연·포화·잡음을 확인한다. 변화율 기반 구현은 표본 간격·미분 필터·문턱을 평가하며 문턱 제어를 완전한 PID와 동일시하지 않는다.'],
        'thermosiphon': ['중력 귀환 두상 열사이펀', '증발부에서 잠열을 흡수한 증기가 응축부에서 열을 내놓고, 응축액은 중력으로 되돌아온다. 심지 모세관 귀환 없이 두상 순환으로 열을 수송한다.', '응축부와 증발부의 높이·중력 방향·충전량·압력·건조·범람 한계를 확인한다. 단상 밀도차 순환은 자연대류에 포함하며 임의 자세에서 작동하지 않는다.'],
    }
    for key, fields in edits.items():
        cards[key][1:4] = fields
    removed = {x[0] for x in decisions}
    output = '\n'.join(l if l.startswith(('#', '@')) or not l else '|'.join(cards[l.split('|')[0]]) for l in lines if not l or l.startswith(('#', '@')) or l.split('|')[0] not in removed) + '\n'
    for row in cards.values():
        assert len(row[2]) <= 160 and len(row[3]) <= 180, row[0]
    archive.mkdir()
    for name in ['catalog.tsv', 'identifiers.json', 'editorial_metadata.json', 'literature_links.json', 'accepted_literature_sources.json', 'mechanism_redirects.json', 'publication.json']:
        shutil.copy2(D / name, archive / name)
    for name in ['effects.json', 'effects_sources.json']:
        shutil.copy2(ROOT / 'triz/knowledge' / name, archive / name)
    (D / 'catalog.tsv').write_text(output, encoding='utf-8')
    for name, value in [('editorial_metadata.json', metadata), ('literature_links.json', links), ('accepted_literature_sources.json', literature), ('mechanism_redirects.json', redirects), ('merged-evidence-2026-09-26.json', originals)]:
        atomic_json(D / name, value)
    print(json.dumps({'before': 959, 'merged': len(removed), 'after': 959-len(removed), 'legacy_ids_preserved': len(removed), 'external_llm_calls': 0}))

if __name__ == '__main__':
    main()
