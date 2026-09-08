import httpx
import pytest
from triz import agent, evidence
from triz.context import RunContext
from triz.schema import ConceptSpec
from triz.settings import settings
from triz.tools import scholar, patent_search


@pytest.fixture(autouse=True)
def isolate_patent_provider(monkeypatch):
    patent_search._cooldown.clear(); patent_search._last_request.clear(); scholar.patent_page.cache_clear()
    monkeypatch.setattr(settings, 'triz', {**settings.triz, 'evidence': {'max_queries_per_run':1,'patent_request_interval_seconds':0}})
    monkeypatch.setattr(scholar, 'enabled_providers', lambda:['google_patents'])
    monkeypatch.setattr(settings, 'free_patent_search', True)
    monkeypatch.setattr(settings, 'patent_search_provider', 'legacy')
    yield
    patent_search._cooldown.clear(); patent_search._last_request.clear(); scholar.patent_page.cache_clear()


def response(url, status=200, **kwargs):
    return httpx.Response(status,request=httpx.Request('GET',url),**kwargs)


def plan(monkeypatch):
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:{'queries':[{'kind':'PATENT','query':'gasket preload','concept_ids':[]}]})


def test_outage_records_failure_without_zero_hit_cache_and_respects_cooldown(state,monkeypatch):
    calls=[]
    def get(url,**kw):
        calls.append(url)
        return response(url,503,text='<title>Sorry...</title>')
    monkeypatch.setattr(scholar.httpx,'get',get);plan(monkeypatch)
    evidence.discover(RunContext(state))
    assert 'PATENT:gasket preload' not in state.scratch['search_cache']
    info=state.scratch['search_diagnostics']['PATENT:gasket preload']
    assert info['status']=='UNAVAILABLE' and info['errors'][0]['http_status']==503
    assert state.steps[-1].status=='WARN'
    assert evidence.search_summary(state)['patent_status']=='UNAVAILABLE'
    detail={};assert scholar.search_kind('another query','PATENT',diagnostics=detail)==[]
    assert detail['errors'][0]['reason']=='COOLDOWN' and len(calls)==1


def test_true_empty_result_is_distinct_and_cached(state,monkeypatch):
    monkeypatch.setattr(scholar.httpx,'get',lambda url,**kw:response(url,json={'results':{'cluster':[]}}))
    plan(monkeypatch);evidence.discover(RunContext(state))
    assert state.scratch['search_cache']['PATENT:gasket preload']==[]
    assert evidence.search_summary(state)['patent_status']=='EMPTY'
    assert state.steps[-1].status=='OK'


def test_failed_query_retries_at_query_budget_limit_and_recovers(state,monkeypatch):
    key='PATENT:gasket preload'
    state.scratch.update(search_cache={},search_diagnostics={key:{'status':'UNAVAILABLE','errors':[]}},
        search_plans={key:{'kind':'PATENT','query':'gasket preload'}})
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:pytest.fail('Retry must reuse its original search plan'))
    def get(url,**kw):
        if '/xhr/' in url:return response(url,json={'results':{'cluster':[{'result':[{'patent':{'publication_number':'US7909155B2'}}]}]}})
        return response(url,text='<meta name="citation_patent_number" content="US:7909155"><meta name="DC.title" content="Verified patent"><div class="abstract">An actual patent abstract describing the functional mechanism and its operating conditions.</div>')
    monkeypatch.setattr(scholar.httpx,'get',get)
    evidence.discover(RunContext(state))
    assert evidence.search_summary(state)['patent_status']=='OK'
    assert state.scratch['search_cache'][key][0]['identifier']=='US7909155B2'
    assert state.scratch['evidence_candidates'][0]['title']=='Verified patent'


def test_legacy_zero_is_unknown_until_retried(state,monkeypatch):
    state.scratch['search_cache']={'PATENT:gasket preload':[]}
    assert evidence.search_summary(state)['patent_status']=='UNKNOWN'
    monkeypatch.setattr(agent,'run_agent',lambda *a,**kw:pytest.fail('Reuse legacy query'))
    monkeypatch.setattr(scholar.httpx,'get',lambda url,**kw:response(url,503))
    evidence.discover(RunContext(state))
    assert evidence.search_summary(state)['patent_status']=='UNAVAILABLE'
    assert 'PATENT:gasket preload' not in state.scratch['search_cache']


def test_invalid_response_is_not_a_successful_zero_result(monkeypatch):
    monkeypatch.setattr(scholar.httpx,'get',lambda url,**kw:response(url,json={}))
    detail={};assert scholar.search_kind('gasket','PATENT',diagnostics=detail)==[]
    assert detail['status']=='UNAVAILABLE'


def test_http_200_challenge_stops_further_requests(monkeypatch):
    calls=[]
    def get(url,**kw):
        calls.append(url)
        return response(url,text='<title>Sorry...</title>')
    monkeypatch.setattr(scholar.httpx,'get',get)
    detail={};scholar.search_kind('gasket','PATENT',diagnostics=detail)
    assert detail['errors'][0]['reason']=='ACCESS_CHALLENGE'
    scholar.search_kind('membrane','PATENT')
    assert len(calls)==1


def test_unassigned_patents_are_not_crowded_out_by_papers(state,monkeypatch):
    c=ConceptSpec(title='Seal');state.concepts=[c]
    state.scratch['evidence_candidates']=[{'identifier':str(i),'source_type':'PAPER','concept_ids':[]} for i in range(20)]+[
        {'identifier':'US1234567','source_type':'PATENT','concept_ids':[]}]
    monkeypatch.setattr(evidence,'discover',lambda ctx:None)
    def match(*a,**kw):
        kinds={r['source_type'] for r in kw['vars']['candidates']}
        assert kinds=={'PATENT','PAPER'}
        return {'matches':[],'additions':[]}
    monkeypatch.setattr(agent,'run_agent',match)
    evidence.attach(RunContext(state))


def test_existing_provider_selection_ignores_unrequested_alternative_key(monkeypatch):
    monkeypatch.setattr(settings,'tavily_key','registered-but-not-selected')
    monkeypatch.setattr(scholar.httpx,'post',lambda *a,**kw:pytest.fail('Do not switch providers'))
    monkeypatch.setattr(scholar.httpx,'get',lambda url,**kw:response(url,503))
    detail={};scholar.search_kind('gasket','PATENT',diagnostics=detail)
    assert detail['provider']=='google_patents'
