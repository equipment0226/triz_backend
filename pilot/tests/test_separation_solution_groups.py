"""A solution diagram may use recorded ID lineage, never a similar title or PC."""
from copy import deepcopy

import pytest

from triz.idea_consolidation import _merged_idea
from triz.report_groups import separation_solution_groups
from triz.schema import ConceptSpec, GlobalState, PhysicalContradiction, RawIdea


def fixture():
    state = GlobalState(run_id='separation-lineage-offline')
    state.definition.physical_contradictions = [PhysicalContradiction(
        id='PC-1', label='삽입 강직성과 장기 유연성', element='전극', parameter='강성',
        state_a='단단함', state_b='유연함')]
    return state


def idea(ident='B-1', *, pc='PC-1', kind='TIME', track='B_SEPARATION', applicable=True):
    return RawIdea(id=ident, track=track, title='저장한 원안', idea='삽입 후 임시 지지층을 제거한다.',
        addresses=[pc] if pc else [], detail=dict(kind=kind, applicable=applicable,
        source_pc_id=pc, title='임시 지지 원안', how='삽입 시와 사용 시를 나눈다.',
        supporting_principles=[34], catalog_version='saved-version'))


def concept(*source_ids, ident='C-1'):
    return ConceptSpec(id=ident, title='최종 전극 해결안', source_idea_ids=list(source_ids),
        working_principle='최종 검토에서 저장한 작동 기구', changes_to_system=['저장된 실제 변경'])


def test_direct_explicit_id_keeps_final_mechanism_separate_from_origin_and_never_mutates():
    state = fixture()
    state.solve.raw_ideas = [idea()]
    state.concepts = [concept('B-1')]
    before = state.model_dump_json()
    groups = separation_solution_groups(state)
    assert len(groups) == 1
    row = groups[0]
    assert row['key'] == 'concept-separation-0-0'
    assert row['application']['how'] == '삽입 시와 사용 시를 나눈다.'
    assert row['application']['source_idea_id'] == 'B-1'
    assert row['contradiction']['id'] == 'PC-1'
    assert row['solution']['id'] == 'C-1'
    assert row['solution']['working_principle'] == '최종 검토에서 저장한 작동 기구'
    assert row['solution']['provenance_label'] == '도출 원안의 분리 적용 기록'
    assert state.model_dump_json() == before
    row['application']['supporting_principles'].append(99)
    row['solution']['changes_to_system'].append('must not reach source')
    row['contradiction']['label'] = 'must not reach source'
    assert state.model_dump_json() == before


def test_actual_merge_keeps_first_id_and_two_same_kind_leaves_distinct():
    state = fixture()
    first, second, unrelated = idea('B-1'), idea('B-2'), idea('A-1', track='A_MATRIX')
    second.detail['how'] = '수술 직후와 장기 사용 시를 나눈다.'
    merged = _merged_idea({'title':'대표 아이디어'}, [unrelated, first, second])
    assert merged.id == 'A-1' and merged.track == 'A_MATRIX'
    state.solve.raw_ideas = [merged]
    state.concepts = [concept(merged.id)]
    groups = separation_solution_groups(state)
    assert [row['application']['source_idea_id'] for row in groups] == ['B-1','B-2']
    assert [row['application']['kind'] for row in groups] == ['TIME','TIME']
    assert [row['key'] for row in groups] == ['concept-separation-0-0','concept-separation-0-1']
    restored = GlobalState.model_validate_json(state.model_dump_json())
    assert separation_solution_groups(restored) == groups


def test_same_id_saved_packet_wins_over_representative_current_fields():
    state = fixture()
    source = idea()
    merged = _merged_idea({'title':'changed representative'}, [source, idea('B-2',kind='SPACE')])
    merged.detail['how'] = 'representative base must not replace saved leaf'
    state.solve.raw_ideas = [merged]
    state.concepts = [concept(merged.id)]
    rows = separation_solution_groups(state)
    assert rows[0]['application']['how'] == source.detail['how']
    assert 'representative base' not in str(rows)


@pytest.mark.parametrize('applicable', [False, 'true', 1, None])
def test_only_boolean_true_is_an_application(applicable):
    state = fixture()
    state.solve.raw_ideas = [idea(applicable=applicable)]
    state.concepts = [concept('B-1')]
    assert separation_solution_groups(state) == []


@pytest.mark.parametrize('source_ids', [[], ['unknown']])
def test_similar_titles_triz_origin_and_one_pc_never_attach_a_solution(source_ids):
    state = fixture()
    source = idea()
    state.solve.raw_ideas = [source]
    state.solve.separation_apps = [deepcopy(source.detail)]
    candidate = concept(*source_ids)
    candidate.title = source.title
    candidate.addresses_contradictions = ['PC-1']
    candidate.triz_origin = [{'track':'B_SEPARATION','ref':'시간 분리'}]
    state.concepts = [candidate]
    assert separation_solution_groups(state) == []


@pytest.mark.parametrize('case', ['missing_packet_id','unlisted_packet_id','lost_packets','wrong_track','unknown_kind','invalid_kind','duplicate_root_id'])
def test_unknown_or_lost_lineage_is_not_guessed(case):
    state = fixture()
    source = idea()
    merged = _merged_idea({}, [source, idea('B-2',track='A_MATRIX')])
    if case == 'missing_packet_id':
        merged.detail['source_details'][0].pop('source_idea_id')
    elif case == 'unlisted_packet_id':
        merged.detail['source_details'][0]['source_idea_id'] = 'invented'
    elif case == 'lost_packets':
        merged.detail.pop('source_details')
    elif case == 'wrong_track':
        merged.detail['source_details'][0]['source_track'] = 'D_ARIZ'
    elif case == 'unknown_kind':
        merged.detail['source_details'][0]['kind'] = 'UNRECORDED_APPROACH'
    elif case == 'invalid_kind':
        merged.detail['source_details'][0]['kind'] = ['TIME', 'SPACE']
    state.solve.raw_ideas = [merged]
    if case == 'duplicate_root_id':
        state.solve.raw_ideas.append(deepcopy(merged))
    state.concepts = [concept(merged.id)]
    assert separation_solution_groups(state) == []


def test_exact_same_leaf_deduplicates_and_conflicting_same_id_is_skipped():
    state = fixture()
    source = idea()
    merged = _merged_idea({}, [source])
    merged.detail['source_details'].append(deepcopy(merged.detail['source_details'][0]))
    state.solve.raw_ideas = [merged]
    state.concepts = [concept(merged.id,merged.id)]
    assert len(separation_solution_groups(state)) == 1
    merged.detail['source_details'][1]['how'] = 'different record for same source ID'
    assert separation_solution_groups(state) == []


def test_pc_context_uses_saved_source_id_or_one_explicit_raw_address_only():
    state = fixture()
    state.definition.physical_contradictions.append(PhysicalContradiction(id='PC-2',label='다른 모순'))
    source = idea(pc='')
    source.addresses = ['TC-else','PC-2']
    source.detail['addresses'] = ['PC-1']  # The raw record's addresses are authoritative.
    state.solve.raw_ideas = [source]
    state.concepts = [concept(source.id)]
    assert separation_solution_groups(state)[0]['contradiction']['id'] == 'PC-2'
    source.addresses = ['PC-1','PC-2']
    assert separation_solution_groups(state)[0]['contradiction'] is None
    source.addresses = ['PC-2']
    source.detail['source_pc_id'] = 'unknown'
    assert separation_solution_groups(state)[0]['contradiction'] is None
    source.detail['source_pc_id'] = 'PC-1'
    assert separation_solution_groups(state)[0]['contradiction']['id'] == 'PC-1'


def test_same_origin_can_explain_two_explicitly_linked_solutions_without_rank_renumbering():
    state = fixture()
    state.solve.raw_ideas = [idea()]
    state.concepts = [concept('unknown',ident='C-unlinked'),concept('B-1'),concept('B-1',ident='C-2')]
    assert [row['key'] for row in separation_solution_groups(state)] == [
        'concept-separation-1-0','concept-separation-2-0']
