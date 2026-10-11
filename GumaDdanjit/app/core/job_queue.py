"""Single-worker FIFO backed by immutable version records, not browser requests."""
import asyncio
import logging
from app.core import versions as store
from app.core.studio_jobs import execute
from app.core.recommendations import now_kst

logger=logging.getLogger(__name__)


def claim():
    with store.LOCK:
        jobs=store.pending_jobs()
        if any(v['status']=='running' for _,_,v in jobs):return None
        if not jobs:return None
        idea,stage,value=jobs[0]
        store.update(idea,stage,value['number'],status='running',started_at=now_kst().isoformat(),message='제작을 시작합니다.')
        return idea,stage,value['number']


async def run_next():
    job=claim()
    if job is None:return False
    try:
        await execute(*job)
    except Exception:
        logger.exception('Queued production failed')
        store.update(*job,status='failed',message='제작 중 오류가 발생했습니다. 재생성해주세요.')
    return True


class Worker:
    def __init__(self):
        self.stopping=False
        self.wake=asyncio.Event()
        self.task=asyncio.create_task(self.run())

    async def run(self):
        while not self.stopping:
            if await run_next():continue
            try:await asyncio.wait_for(self.wake.wait(),timeout=1)
            except asyncio.TimeoutError:pass
            self.wake.clear()

    async def stop(self):
        # Finish the active job; unstarted versions stay queued for the next startup.
        self.stopping=True
        self.wake.set()
        await self.task
