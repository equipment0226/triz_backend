"""Owner-scoped immutable review and lineage endpoints."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import FiniteFloat
from . import ledger
from .contracts import Review, Conflict, AccessDenied,Contract,ActionTicket

router=APIRouter(prefix='/api/runs/{run_id}/ax')


def actor(request):
    return getattr(request.state,'user_id','local')


def scoped(run_id,request):
    from .. import store
    from . import enabled
    state=store.load_state(run_id)
    if not state or not enabled(state):
        raise HTTPException(404,'실행 기록이 없습니다.')
    try:
        return ledger.head(run_id,actor(request))
    except (ValueError,AccessDenied):
        raise HTTPException(404,'실행 기록이 없습니다.')


@router.get('')
def overview(run_id: str,request: Request):
    h=scoped(run_id,request)
    return {'snapshot_id':h['snapshot_id'],'epoch':h['epoch'],
        'budget':ledger.budget(run_id,actor(request)),
        'decisions':ledger.decision_history(run_id,actor(request)),
        'reviews':ledger.active_reviews(run_id,actor(request))}


@router.get('/snapshots/{snapshot_id}')
def snapshot(run_id: str,snapshot_id: str,request: Request):
    scoped(run_id,request)
    try:
        return ledger.snapshot(run_id,snapshot_id,actor(request))
    except ValueError:
        raise HTTPException(404,'Snapshot not found')


@router.get('/artifacts/{version_id}')
def artifact(run_id: str,version_id: str,request: Request):
    scoped(run_id,request)
    try:
        return ledger.artifact(run_id,version_id,actor(request))
    except ValueError:
        raise HTTPException(404,'Artifact not found')


@router.post('/reviews')
def review(run_id: str,body: Review,request: Request):
    scoped(run_id,request)
    try:
        return ledger.submit_review(run_id,actor(request),body)
    except Conflict as exc:
        h=ledger.head(run_id,actor(request))
        current=ledger.snapshot(run_id,h['snapshot_id'],actor(request))
        try:
            previous=ledger.snapshot(run_id,body.snapshot_id,actor(request))['members']
        except ValueError:
            previous={}
        raise HTTPException(409,{'message':str(exc),'snapshot_id':h['snapshot_id'],'epoch':h['epoch'],
            'changed':[{'key':k,'previous':previous.get(k),'current':current['members'].get(k)}
                       for k in sorted(set(previous)|set(current['members']))
                       if previous.get(k)!=current['members'].get(k)]})


class Calculation(Contract):
    expected_epoch: int
    snapshot_id: str
    tool: str
    inputs: dict[str,FiniteFloat]


@router.post('/calculations')
def calculate(run_id: str,body: Calculation,request: Request):
    scoped(run_id,request)
    from .. import store
    from . import engineering,coordinator,runtime
    if body.tool not in engineering.TOOLS:
        raise HTTPException(422,'등록되지 않은 계산 도구입니다.')
    try:
        with store.run_lock(run_id):
            state=store.load_state(run_id)
            h=ledger.head(run_id,actor(request))
            if state.status in ('RUNNING','QUEUED') or h['epoch']!=body.expected_epoch or h['snapshot_id']!=body.snapshot_id:
                raise Conflict('분석이 진행 중이거나 입력 버전이 변경되었습니다.')
            ticket=ActionTicket(action_type='RUN_TEST',target_version_ids=[state.scratch['ax_members'].get('concepts',state.scratch['ax_members']['input'])],
                parameters={'tool':body.tool},expected_outputs=['CalculationResult'],allowed_tools=['deterministic_validation'],
                reason='입력 단위가 고정된 등록 계산을 실행한다. 실측 시험 통과로 승격하지 않는다.')
            _,did=coordinator.decide(state,[ticket],0,{'RUN_TEST'},'registered_calculation')
            result=engineering.run(body.tool,body.inputs)
            entry={'tool':body.tool,'inputs':body.inputs,'result':result,'decision_id':did}
            state.scratch.setdefault('ax_calculations',[]).append(entry)
            ledger.capture(state,{'calculations':state.scratch['ax_calculations']},
                {'calculations':('concepts','problem')},'registered_calculation')
            return {'snapshot_id':state.scratch['ax_snapshot_id'],**entry}
    except (Conflict,RuntimeError) as exc:
        raise HTTPException(409,str(exc))
