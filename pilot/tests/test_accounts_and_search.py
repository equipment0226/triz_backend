import time
import pytest
from fastapi.testclient import TestClient
from triz import store, pipeline, render, visuals
from triz.settings import settings
from triz.schema import ReportArtifact, IFR, ResourceItem, TechnicalContradiction

def test_sessions_enforce_ownership_for_all_run_routes(monkeypatch):
    from api.main import app
    monkeypatch.setattr(settings, 'app_token', 'gateway-fixture')
    monkeypatch.setattr(settings, 'require_user_auth', True)
    a = store.create_session('subject-a', 'a@example.test', 'A')
    b = store.create_session('subject-b', 'b@example.test', 'B')
    state = pipeline.create_run('Private engineering problem', user_id=a['user']['id'])
    client = TestClient(app)
    def headers(token): return {'X-TRIZ-APP-TOKEN':'gateway-fixture', 'X-TRIZ-SESSION':token}
    assert client.get('/api/runs', headers=headers('forged')).status_code == 401
    assert client.get('/api/runs', headers=headers(b['token'])).json() == []
    assert client.get('/api/runs', headers=headers(a['token'])).json()[0]['run_id'] == state.run_id
    for suffix in ('', '/view', '/report?format=html', '/events', '/steps', '/report/context'):
        assert client.get('/api/runs/'+state.run_id+suffix, headers=headers(b['token'])).status_code == 404
    for suffix in ('/resume', '/rerun', '/continue', '/inject-agent', '/feedback'):
        assert client.post('/api/runs/'+state.run_id+suffix, json={}, headers=headers(b['token'])).status_code == 404
    assert client.delete('/api/runs/'+state.run_id, headers=headers(b['token'])).status_code == 404
    assert client.post('/internal/auth/sessions', json={'subject':'x','email':'x','name':'x'}).status_code == 401
    assert client.get('/api/rag', headers=headers(a['token'])).status_code == 403
    again = store.create_session('subject-a', 'renamed@example.test', 'Renamed')
    assert again['user']['id'] == a['user']['id']
    store.revoke_session(a['token'])
    assert store.session_user(a['token']) is None
    assert store.session_user(again['token'])['name'] == 'Renamed'

def test_expired_session_is_rejected():
    from sqlalchemy import update
    account = store.create_session('expired', 'expired@example.test', 'Expired')
    with store.engine.begin() as conn:
        conn.execute(update(store.sessions).where(store.sessions.c.user_id == account['user']['id']).values(expires_at=time.time()-1))
    assert store.session_user(account['token']) is None

def test_legacy_runs_are_claimed_only_by_configured_owner(state, monkeypatch):
    monkeypatch.setattr(settings, 'legacy_owner_email', 'owner@example.test')
    other = store.create_session('legacy-other', 'other@example.test', 'Other')
    assert store.run_owner(state.run_id) == 'local'
    owner = store.create_session('legacy-owner', 'owner@example.test', 'Owner')
    assert store.run_owner(state.run_id) == owner['user']['id']
    assert store.load_state(state.run_id).user_id == owner['user']['id']

def test_complete_report_uses_original_process_and_safe_html(state):
    from triz.presentation import view
    state.intake.frame.restated_problem = '성능 개선 시 손상 증가 <script>alert(1)</script>'
    state.analysis.resources = [ResourceItem(name='기존 냉각수', usable_for=['열 이동'])]
    state.definition.ifr = IFR(statement='추가 장치 없이 스스로 열을 제거한다')
    state.definition.technical_contradictions = [TechnicalContradiction(label='성능과 손상', if_action='유속 증가', then_good='냉각 향상', but_bad='표면 손상')]
    state.report = ReportArtifact(markdown='old summary', narrative={'executive_summary':'요약'})
    data = view(state)
    assert any('문제 정의' in s['title'] for s in data['report_sections'])
    html = render.render_html(state)
    assert '기존 냉각수' in html and '추가 장치 없이' in html and '성능과 손상' in html
    assert '<script>' not in html and '```mermaid' not in html
    assert all(f['svg'] in html for f in data['figures'])

def test_long_korean_labels_are_complete_and_boxes_expand():
    import xml.etree.ElementTree as ET
    label = '마이크로미터 단위의 표면 손상과 열팽창을 동시에 제어하는 기존 냉각수 순환 계통 ' * 8
    svg = visuals.svg('아주 긴 제목 ' * 30, [('a', label, ''), ('b', 'target', 'good')], [('a','b','긴 관계 설명 '*25, False)])
    root = ET.fromstring(svg); ns={'s':'http://www.w3.org/2000/svg'}
    group = root.find('.//s:g', ns)
    assert ''.join(group.find('s:text', ns).itertext()) == label
    assert float(group.find('s:rect', ns).attrib['height']) > 106
    assert len(group.findall('s:text/s:tspan', ns)) > 4

def test_free_search_verifies_actual_patent_page(monkeypatch):
    from triz.tools import scholar
    import httpx
    scholar.patent_page.cache_clear()
    def get(url, **kwargs):
        req = httpx.Request('GET', url)
        if '/xhr/' in url:
            return httpx.Response(200, request=req, json={'results':{'cluster':[{'result':[{'patent':{'publication_number':'US7909155B2'}}, {'patent':{'publication_number':'US9999999B2'}}]}]}})
        return httpx.Response(200, request=req, text='<meta name="citation_patent_number" content="US:7909155"><meta name="DC.title" content="Conveyor systems"><div class="abstract">Spacing control using independently driven zones.</div>')
    monkeypatch.setattr(scholar.httpx, 'get', get)
    results = scholar.google_patents('conveyor spacing control', 3)
    assert len(results) == 1 and results[0]['identifier'] == 'US7909155B2'
    assert 'independently driven zones' in results[0]['snippet']
    scholar.patent_page.cache_clear()
