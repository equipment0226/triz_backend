"""Run-local config propagation into bounded worker pools; no global mutation."""
from concurrent.futures import ThreadPoolExecutor as BasePool
from contextvars import ContextVar,copy_context

profile=ContextVar('triz_execution_profile',default=None)


class ThreadPoolExecutor(BasePool):
    def submit(self,fn,/,*args,**kwargs):
        context=copy_context()
        return super().submit(context.run,fn,*args,**kwargs)
