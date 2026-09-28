"""Project titles stay grounded when model title extraction falls back."""
from copy import deepcopy

import pytest

from triz import agent, nodes, store, titles
from triz.context import RunContext
from triz.schema import ReportArtifact


NEUTRAL_TITLE = '입력 조건 확인 및 문제 정의'
BAD_TITLE = '안녕하세요 · 초전도 · 방식의 개선 과제'
LONG_SYSTEM = '상온-극저온 신호 전달 경로(동축 케이블 및 그 계면)'
SYSTEM_TITLE = '상온-극저온 신호 전달 경로 개선 과제'


@pytest.mark.parametrize('candidate', [
    BAD_TITLE,
    '안녕하세요, 초전도 배선 개선',
    'Hello, quantum wiring improvement',
])
def test_greetings_are_not_valid_generated_project_titles(candidate):
    assert not titles.valid_title(candidate)


@pytest.mark.parametrize('candidate', [
    '인사말 생성 시스템 개선',
    '공기 냉각 장비 개선',
    'Hi-Fi 오디오 잡음 개선',
])
def test_technical_titles_are_not_rejected_as_conversational(candidate):
    assert titles.valid_title(candidate)


@pytest.mark.parametrize(('system', 'expected'), [
    ('공기 냉각 장비', '공기 냉각 장비 개선 과제'),
    ('진동 데이터 수집 시스템', '진동 데이터 수집 시스템 개선 과제'),
    (LONG_SYSTEM, SYSTEM_TITLE),
])
def test_fallback_uses_complete_structured_system_terms(state, system, expected):
    state.raw_query = '안녕하세요, 초전도 방식의 배선 문제를 해결하고 싶습니다.'
    state.domain.target_system = system
    original = state.raw_query
    assert titles.fallback_title(state) == expected
    assert state.raw_query == original


def test_long_system_fallback_ends_at_whole_word_boundary(state):
    state.domain.target_system = '상온 신호 전달 배선의 극저온 영역 열유입 억제를 위한 초전도 연결 장치'
    title = titles.fallback_title(state)
    assert len(title) <= 40
    assert title.endswith(' 개선 과제')
    system_phrase = title.removesuffix(' 개선 과제')
    assert state.domain.target_system.startswith(system_phrase + ' ')
    assert not any(mark in title for mark in ('…', '...'))


@pytest.mark.parametrize('query', [
    '안녕하세요, 초전도 방식의 배선 문제를 해결하고 싶습니다.',
    'Hello, please help improve quantum wiring.',
    '파티클 제거 성능과 장비 부품 수명 사이의 문제',
])
def test_fallback_without_structured_system_does_not_guess_from_query(state, query):
    state.raw_query = query
    state.domain.target_system = ''
    assert titles.fallback_title(state) == NEUTRAL_TITLE
    assert state.raw_query == query


def test_refresh_records_fallback_correction_once_without_changing_input(state):
    original = state.raw_query
    state.scratch.update(title=BAD_TITLE, title_source='structured_fallback')
    state.domain.target_system = LONG_SYSTEM

    titles.refresh_fallback_title(state)

    assert state.scratch['title'] == SYSTEM_TITLE
    assert state.scratch['title_source'] == 'structured_fallback'
    assert state.raw_query == original
    history = deepcopy(state.scratch['title_history'])
    assert len(history) == 1
    assert history[0]['previous_title'] == BAD_TITLE
    assert history[0]['reason']

    titles.refresh_fallback_title(state)
    assert state.scratch['title_history'] == history


@pytest.mark.parametrize('source', ['custom', 'title_extraction', None])
def test_refresh_preserves_existing_titles_without_explicit_fallback_source(state, source):
    state.scratch['title'] = '사용자가 정한 초전도 배선 개선 목표'
    if source is not None:
        state.scratch['title_source'] = source
    state.domain.target_system = LONG_SYSTEM
    original = deepcopy(state.scratch)

    titles.refresh_fallback_title(state)

    assert state.scratch == original


def test_valid_bootstrap_replaces_fallback_source_and_survives_intake_refresh(state, monkeypatch):
    state.scratch.update(title=BAD_TITLE, title_source='structured_fallback')
    state.domain.target_system = LONG_SYSTEM
    model_title = '초전도 배선 신호 전달과 열유입 상충 해결'

    def unexpected_call(*args, **kwargs):
        raise AssertionError('A valid bootstrap title must not trigger title repair')

    monkeypatch.setattr(agent, 'tracked_chat', unexpected_call)
    state.scratch['title'] = titles.ensure_title(RunContext(state), model_title)
    assert state.scratch['title_source'] == 'bootstrap'

    titles.refresh_fallback_title(state)

    assert state.scratch['title'] == model_title
    assert not state.scratch.get('title_history')


def test_refresh_waits_for_meaningful_structured_system(state):
    state.scratch.update(title=BAD_TITLE, title_source='structured_fallback')
    state.domain.target_system = ''
    original = deepcopy(state.scratch)

    titles.refresh_fallback_title(state)

    assert state.scratch == original


def test_refresh_preserves_completed_report_title(state):
    state.scratch.update(title=BAD_TITLE, title_source='structured_fallback')
    state.domain.target_system = LONG_SYSTEM
    state.report = ReportArtifact()
    original = state.model_dump()

    titles.refresh_fallback_title(state)

    assert state.model_dump() == original


def test_intake_refreshes_and_persists_fallback_without_extra_model_calls(state, monkeypatch):
    state.scratch.update(title=BAD_TITLE, title_source='structured_fallback')
    original = state.raw_query
    calls = []

    def extract(ctx, **kwargs):
        calls.append(kwargs['node'])
        assert kwargs['node'] == 's1_extract'
        return {
            'domain': {'industry': '초전도', 'target_system': LONG_SYSTEM},
            'frame': {'restated_problem': '배선 열유입을 줄이며 신호를 전달한다.',
                      'symptom': '상온 배선에서 극저온 영역으로 열이 유입된다.',
                      'confidence': 0.9},
            'constraints': {'items': [{'statement': '신호 전달 성능을 유지한다.'}]},
        }

    monkeypatch.setattr(agent, 'run_agent', extract)
    nodes.s1_extract(RunContext(state))

    saved = store.load_state(state.run_id)
    assert saved.scratch['title'] == SYSTEM_TITLE
    assert saved.scratch['title_source'] == 'structured_fallback'
    assert saved.raw_query == original
    assert len(saved.scratch['title_history']) == 1
    assert calls == ['s1_extract']
