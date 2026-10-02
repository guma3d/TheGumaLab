import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import versions as store, job_queue as queue
from app.core.official_clips import ClipBoard
from google import genai
from google.genai import _transformers


class QueueTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patch=patch.object(store,'ROOT',Path(self.temp.name));self.patch.start()
        self.ids=[store.create(dict(category='tech',subject=name),'2026-10-02')['id'] for name in ('Insta360','Sennheiser')]
        for iid in self.ids:store.reserve(iid,'Preview',queued=True)

    def tearDown(self):
        self.patch.stop();self.temp.cleanup()

    async def test_fifo_single_execution_and_failure_does_not_cancel_next(self):
        started=asyncio.Event();release=asyncio.Event();calls=[]
        async def execute(iid,stage,n):
            calls.append(iid)
            if iid==self.ids[0]:
                started.set();await release.wait();raise ValueError('simulated provider failure')
            store.update(iid,stage,n,status='ready')
        with patch.object(queue,'execute',side_effect=execute):
            first=asyncio.create_task(queue.run_next());await started.wait()
            self.assertFalse(await queue.run_next())
            self.assertEqual(store.get(self.ids[1],'Preview',1)['status'],'queued')
            self.assertEqual(store.workflow(store.read(self.ids[1]))['message'],'제작 대기 · 1번째')
            with self.assertRaises(ValueError):store.reserve(self.ids[1],'Preview',True,queued=True)
            release.set();await first
            self.assertEqual(store.get(self.ids[0],'Preview',1)['status'],'failed')
            self.assertTrue(await queue.run_next());self.assertEqual(calls,self.ids)
            self.assertEqual(store.get(self.ids[1],'Preview',1)['status'],'ready')

    async def test_restart_keeps_waiting_jobs_and_does_not_repeat_active_paid_work(self):
        self.assertEqual(queue.claim()[0],self.ids[0])
        store.recover_interrupted()
        self.assertEqual(store.get(self.ids[0],'Preview',1)['status'],'failed')
        self.assertEqual(store.get(self.ids[1],'Preview',1)['status'],'queued')
        self.assertEqual(queue.claim()[0],self.ids[1])

    async def test_shutdown_finishes_active_job_and_preserves_waiting(self):
        started=asyncio.Event();release=asyncio.Event()
        async def execute(iid,stage,n):
            started.set();await release.wait();store.update(iid,stage,n,status='ready')
        with patch.object(queue,'execute',side_effect=execute):
            worker=queue.Worker();await started.wait()
            stopping=asyncio.create_task(worker.stop());await asyncio.sleep(0)
            self.assertFalse(stopping.done());release.set();await stopping
        self.assertEqual(store.get(self.ids[1],'Preview',1)['status'],'queued')


class ProviderSchemaTests(unittest.TestCase):
    def test_actual_sdk_accepts_full_clip_schema_without_network(self):
        with genai.Client(api_key='schema-test-no-network') as client:
            schema=_transformers.t_schema(client._api_client,ClipBoard)
            self.assertIsNotNone(schema.properties['scenes'].items)
