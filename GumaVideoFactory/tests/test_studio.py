import asyncio
import concurrent.futures
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi import BackgroundTasks, HTTPException
from fastapi.testclient import TestClient
from app import studio, main
from app.core import versions as store
from app.core import studio_jobs as jobs
from app.core.model_assets import fetch, Blueprint


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patcher=patch.object(store,'ROOT',self.root);self.patcher.start()
        self.rec=dict(id='test',category='tech',subject='Test product',product_keyword='Test product',hook='hook',sources=[],supporting_features=[])
        self.idea=store.create(self.rec,'2026-10-02');self.id=self.idea['id']
    def tearDown(self):
        self.patcher.stop();self.temp.cleanup()
    def start(self,stage,**kw):
        tasks=BackgroundTasks()
        result=asyncio.run(studio.start(self.id,stage,studio.StageRequest(**kw),tasks))
        return result,tasks
    def ready_model(self):
        value,_=self.start('3DModel');n=value['number']
        (store.version_dir(self.id,'3DModel',n)/'model.blend').write_bytes(b'test-model')
        store.update(self.id,'3DModel',n,status='ready')
        asyncio.run(studio.approve_model(self.id,n,studio.Approval(appearance_confirmed=True,usage_confirmed=True)))
        return n
    def ready_preview(self):
        model=self.ready_model();value,_=self.start('Preview',model_version=model)
        scenes=[]
        for i in range(1,7):
            path=store.version_dir(self.id,'Preview',value['number'])/f'scene_{i:02d}.png';path.write_bytes(b'image')
            scenes.append(dict(scene_number=i,narration_ko='original',image_url='/test',visual_mode='approved_model'))
        store.update(self.id,'Preview',value['number'],status='ready',storyboard=dict(scenes=scenes))
        return value['number']

    def test_idea_approval_is_idempotent_and_never_calls_generation(self):
        with patch.object(studio,'load_daily',return_value={'items':[self.rec]}),patch.object(studio,'execute') as paid:
            a=asyncio.run(studio.approve_idea(studio.IdeaRequest(recommendation_id='test',date='2026-10-02')))
            b=asyncio.run(studio.approve_idea(studio.IdeaRequest(recommendation_id='test',date='2026-10-02')))
            self.assertEqual(a['id'],b['id']);paid.assert_not_called()
        self.assertEqual(store.history(self.id,'3DModel'),[])

    def test_gate_prevents_preview_and_video_before_model_approval(self):
        value,tasks=self.start('3DModel');self.assertEqual(len(tasks.tasks),1)
        with self.assertRaises(HTTPException):self.start('Preview',model_version=1)
        store.update(self.id,'3DModel',1,status='ready')
        with self.assertRaises(HTTPException):self.start('Preview',model_version=1)
        with self.assertRaises(HTTPException):asyncio.run(studio.approve_model(self.id,1,studio.Approval(appearance_confirmed=True)))
        self.assertEqual(store.history(self.id,'Preview'),[])

    def test_duplicate_click_reuses_and_regeneration_preserves_old_files(self):
        first,_=self.start('3DModel');again,tasks=self.start('3DModel')
        self.assertEqual(first,again);self.assertEqual(len(tasks.tasks),0)
        with self.assertRaises(HTTPException):self.start('3DModel',regenerate=True)
        path=store.version_dir(self.id,'3DModel',1)/'model.blend';path.write_bytes(b'old')
        store.update(self.id,'3DModel',1,status='failed')
        second,tasks=self.start('3DModel',regenerate=True)
        self.assertEqual(second['number'],2);self.assertEqual(len(tasks.tasks),1);self.assertEqual(path.read_bytes(),b'old')

    def test_video_requires_approval_and_snapshots_edits_and_parent(self):
        n=self.ready_preview()
        with self.assertRaises(HTTPException):self.start('Video',preview_version=n)
        video,_=self.start('Video',preview_version=n,approved=True,narrations=['edited']*6,product_url='https://example.com/product')
        self.assertEqual(video['model_version'],1);self.assertEqual(video['preview_version'],n)
        self.assertTrue(video['approved_at']);self.assertEqual(video['storyboard']['scenes'][0]['narration_ko'],'edited')
        self.assertEqual(store.get(self.id,'Preview',n)['storyboard']['scenes'][0]['narration_ko'],'original')
        store.update(self.id,'Video',1,status='ready')
        (store.version_dir(self.id,'Video',1)/'final.mp4').write_bytes(b'original-video')
        second,_=self.start('Video',regenerate=True,preview_version=n,approved=True,narrations=['new']*6,product_url='https://example.com/product')
        self.assertEqual(second['number'],2)
        self.assertEqual((store.version_dir(self.id,'Video',1)/'final.mp4').read_bytes(),b'original-video')

    def test_model_change_does_not_rewrite_existing_preview_parent(self):
        n=self.ready_preview();second,_=self.start('3DModel',regenerate=True)
        store.update(self.id,'3DModel',2,status='ready')
        with self.assertRaises(HTTPException):self.start('Preview',regenerate=True,model_version=2)
        self.assertEqual(store.get(self.id,'Preview',n)['model_version'],1)

    def test_approved_geometry_cannot_change_silently(self):
        n=self.ready_model()
        (store.version_dir(self.id,'3DModel',n)/'model.blend').write_bytes(b'changed')
        with self.assertRaises(HTTPException):self.start('Preview',model_version=n)
        self.assertEqual(store.history(self.id,'Preview'),[])

    def test_http_stage_dispatch_and_rendered_script(self):
        with TestClient(main.app) as client,patch.object(studio,'execute',new_callable=AsyncMock) as work:
            response=client.post(f'/api/ideas/{self.id}/3DModel',json={})
            self.assertEqual(response.status_code,200)
            work.assert_awaited_once_with(self.id,'3DModel',1)
            self.assertEqual(client.post(f'/api/ideas/{self.id}/Preview',json={'model_version':1}).status_code,409)
            self.assertEqual(client.post(f'/api/ideas/{self.id}/3DModel',json={}).json()['number'],1)
            self.assertEqual(work.await_count,1)

    def test_restart_and_concurrent_reservation(self):
        def reserve():
            try:return store.reserve(self.id,'3DModel',True)[0]['number']
            except ValueError:return None
        with concurrent.futures.ThreadPoolExecutor(8) as pool:results=list(pool.map(lambda _:reserve(),range(8)))
        self.assertEqual([r for r in results if r], [1])
        store.recover_interrupted();self.assertEqual(store.get(self.id,'3DModel',1)['status'],'failed')

    def test_detail_and_listing_are_separate(self):
        with TestClient(main.app) as client:
            page=client.get('/').text
            self.assertIn('/ideas/'+self.id,page)
            self.assertNotIn('id="version-picker"',page)
            detail=client.get('/ideas/'+self.id)
            self.assertEqual(detail.status_code,200)
            self.assertIn('id="version-picker"',detail.text)
            self.assertEqual(client.get('/api/ideas/invalid').status_code,404)

    def test_fetch_blocks_internal_dns_and_blueprint_invalid_geometry(self):
        with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]),patch('socket.create_connection') as network:
            with self.assertRaises(ValueError):fetch('https://example.com/model.glb')
            network.assert_not_called()
        with self.assertRaises(ValueError):Blueprint.model_validate(dict(reference_matches_product=True,product_identity='X',uncertainties=['draft'],parts=[dict(name='x',shape='box',position=[0,0,0],dimensions=[-1,1,1],color=[1,1,1])]))

    def test_job_failure_is_retained_as_a_failed_version(self):
        self.start('3DModel')
        with patch.object(jobs,'model_job',side_effect=ValueError('No matching sources')):
            asyncio.run(jobs.execute(self.id,'3DModel',1))
        self.assertEqual(store.get(self.id,'3DModel',1)['status'],'failed')
        new,_=self.start('3DModel',regenerate=True);self.assertEqual(new['number'],2)


if __name__=='__main__':unittest.main()
