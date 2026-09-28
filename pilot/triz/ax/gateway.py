"""Durable paid-call reservation, idempotent result reuse and unknown usage."""
import math
import time
from dataclasses import asdict
from .. import llm, store
from ..context import AbortRun, ProviderUnavailable
from ..settings import settings
from . import ledger
from .contracts import Conflict,BudgetBusy


def chat(ctx, **kwargs):
    node=kwargs.pop('_node','independent_verifier')
    state=ctx.state
    bundle=state.scratch['ax_bundle']
    from .action_runtime import active_action
    action_context = active_action.get()
    if action_context:
        role='INDEPENDENT_REVIEW' if node=='independent_verifier' else action_context['ticket']['model_role']
        expected=bundle.get('run_contract',{}).get('model_roles',{}).get(role)
        if expected and kwargs.get('tier','T2')!=expected:
            raise AbortRun('선택된 작업의 모델 역할과 실제 호출 설정이 일치하지 않습니다.')
        action_context=dict(action_context,call_model_role=role,actual_tier=kwargs.get('tier','T2'))
    config=bundle['models'][kwargs.get('tier','T2')]
    attempts=max(1,int(bundle['config'].get('ax',{}).get('max_provider_attempts',2)))
    request=dict(kwargs,model_config=config,retries=attempts)
    bound=len((kwargs['system']+kwargs['user']).encode('utf-8'))+16000
    reserve=math.ceil((bound*config['cost_in']+(kwargs.get('max_tokens') or config['max_tokens'])*config['cost_out'])*attempts)
    validation=node.startswith(('s7_','s8_','s9_')) or node=='independent_verifier'
    hold=0 if validation else bundle['limits']['validation_reserve_microusd']
    with ctx.call_slots:
        if time.time()>state.scratch.get('execution_deadline',float('inf')):
            raise AbortRun('실행 시간 예산을 초과했습니다.')
        if ctx.budget.get('provider_status'):
            raise ProviderUnavailable(ctx.budget['provider_status'])
        until=min(state.scratch.get('execution_deadline',float('inf')),
                  time.time()+max(390,settings.timeout*attempts+30))
        while True:
            try:
                optional_limit=bundle['limits']['optional_budget_microusd'] if action_context and action_context.get('optional') else None
                task=ledger.acquire(state.run_id,state.scratch.get('execution_epoch',0),
                                    {'node':node,'request':request,'bundle_id':bundle['bundle_id'],
                                     'decision_id':action_context.get('decision_id') if action_context else state.scratch.get('ax_last_decision'),
                                     **({'action_context':action_context} if action_context else {})},
                                    reserve,minimum_remaining=hold,optional_limit=optional_limit)
                break
            except BudgetBusy as exc:
                if time.time()>=until:
                    raise AbortRun('진행 중 호출의 비용 예약 정산을 기다리다 시간 예산에 도달했습니다.') from exc
                time.sleep(.2)
            except Conflict as exc:
                raise AbortRun(str(exc)) from exc
        if task.get('blocked'):
            if task['blocked']=='FAILED' and task.get('actual') is not None:
                stored=task.get('result') or {}
                result=llm.recover_failed_json(stored.get('usage') or {}, kwargs.get('expect','object'))
                if result is not None:
                    from .contracts import digest
                    from sqlalchemy import select
                    event_id='evt-'+digest([task['task_id'],'complete-json-v1'])[:60]
                    with ledger.transaction() as connection:
                        head=ledger._head(connection,state.run_id,lock=True)
                        if head['epoch']!=state.scratch.get('execution_epoch',0):
                            raise Conflict('Stale format recovery epoch')
                        if not connection.execute(select(ledger.events.c.event_id).where(ledger.events.c.event_id==event_id)).first():
                            ledger._event(connection,state.run_id,'ACTION_FORMAT_RECOVERED',
                                {'task_id':task['task_id'],'recovery_version':'complete-json-v1',
                                 'data_hash':digest(result.data),'additional_cost_microusd':0},event_id=event_id)
                    with ctx.lock:
                        state.cost.total_usd=ledger.budget(state.run_id)['spent_microusd']/1e6
                    return result
            raise AbortRun('이 호출의 실행 또는 과금 상태를 확인해야 합니다. 중복 호출을 보류했습니다.')
        if task.get('cached'):
            state.cost.total_usd=ledger.budget(state.run_id)['spent_microusd']/1e6
            result=llm.LLMResult(**task['result'])
            result.meta=dict(result.meta,durable_replay=True)
            return result
        try:
            result=llm.chat_json(**request)
        except BaseException as exc:
            usage=getattr(exc,'usage',None)
            requests=usage.meta.get('requests',[]) if usage else []
            known=bool(requests) and all(r.get('usage') or r.get('status_code') in (401,402,403) for r in requests)
            # A terminal account rejection with no accepted response has no output charge.
            rejected=isinstance(exc,llm.LLMError) and exc.terminal and not requests
            actual=math.ceil(usage.cost_usd*1e6) if known else (0 if rejected else None)
            ledger.settle(task,{'error':type(exc).__name__,'usage':asdict(usage) if usage else None},
                          actual,status='FAILED' if actual is not None else 'UNKNOWN')
            with ctx.lock:
                state.cost.total_usd=ledger.budget(state.run_id)['spent_microusd']/1e6
            if isinstance(exc,llm.LLMError) and exc.terminal:
                with ctx.lock:
                    ctx.budget['provider_status']=exc.status_code
                raise ProviderUnavailable(exc.status_code,usage=usage) from exc
            raise
        requests=result.meta.get('requests',[])
        if any(not r.get('usage') and r.get('status_code') not in (401,402,403) for r in requests):
            ledger.settle(task,asdict(result),None,status='UNKNOWN')
            raise AbortRun('일부 호출의 사용량이 미확인 상태입니다. 비용 예약을 유지합니다.')
        ledger.settle(task,asdict(result),math.ceil(result.cost_usd*1e6))
        with ctx.lock:
            state.cost.total_usd=ledger.budget(state.run_id)['spent_microusd']/1e6
            state.cost.request_count+=result.meta.get('attempt') or 1
            state.cost.tokens_in+=result.tokens_in
            state.cost.tokens_out+=result.tokens_out
            tier=kwargs.get('tier','T2')
            state.cost.by_tier[tier]=state.cost.by_tier.get(tier,0)+result.cost_usd
            stage=state.control.current_stage
            state.cost.by_stage[stage]=state.cost.by_stage.get(stage,0)+result.cost_usd
            state.cost.over_budget=state.cost.total_usd>state.cost.budget_usd
        store.save_call(state.run_id,{'node':node,'request':request,'response':result.text,
            'tokens_in':result.tokens_in,'tokens_out':result.tokens_out,'cost_usd':result.cost_usd,
            'model':result.model,'meta':result.meta,'task_id':task['task_id']})
        return result
