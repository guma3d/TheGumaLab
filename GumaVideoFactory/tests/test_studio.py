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
from app.core import job_queue
from app.core.model_assets import fetch, Blueprint, PageAssets


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
    def ready_preview(self,needs=False):
        value,_=store.reserve(self.id,'Preview',regenerate=bool(store.history(self.id,'Preview')))
        n=value['number'];scenes=[]
        for i in range(1,7):
            for ext in ('png','mp4'):(store.version_dir(self.id,'Preview',n)/f'scene_{i:02d}.{ext}').write_bytes(b'asset')
            scenes.append(dict(scene_number=i,narration_ko='original',image_url='/test',visual_mode='official_clip'))
        store.update(self.id,'Preview',n,status='ready',package_ready=True,needs_3d=needs,storyboard=dict(scenes=scenes))
        from app.core.prepared_packages import digest
        f=store.version_dir(self.id,'Preview',n)
        store.write_json(f/'package.json',dict(files={p.relative_to(store.directory(self.id)).as_posix():digest(p) for p in f.glob('scene_*')},veo_transition='light'))
        return n

    def ready_model(self,preview):
        value,_=store.reserve(self.id,'3DModel',True,preview_version=preview);n=value['number']
        (store.version_dir(self.id,'3DModel',n)/'model.blend').write_bytes(b'test-model')
        store.update(self.id,'3DModel',n,status='ready')
        asyncio.run(studio.approve_model(self.id,n,studio.Approval(appearance_confirmed=True,usage_confirmed=True)))
        f=store.version_dir(self.id,'Preview',preview)/'package.json'
        package=json.loads(f.read_text());package['model_version']=n;store.write_json(f,package)
        return n

    def video(self,n,**kw):
        return self.start('Video',preview_version=n,approved=True,narrations=['edited']*6,product_url='https://example.com/product',**kw)

    def test_preview_first_and_optional_model_gate(self):
        with self.assertRaises(HTTPException):self.start('3DModel')
        n=self.ready_preview()
        with self.assertRaises(HTTPException):self.start('3DModel',preview_version=n,approved=True)
        result,_=self.video(n)
        self.assertIsNone(result['model_version'])
        self.assertEqual(result['storyboard']['scenes'][0]['narration_ko'],'edited')
        self.assertEqual(store.get(self.id,'Preview',n)['storyboard']['scenes'][0]['narration_ko'],'original')

    def test_needed_model_requires_preview_approval_and_matching_model(self):
        n=self.ready_preview(True)
        with self.assertRaises(HTTPException):self.start('3DModel',preview_version=n)
        with self.assertRaises(HTTPException):self.video(n)
        m=self.ready_model(n)
        result,_=self.video(n);self.assertEqual(result['model_version'],m)
        store.update(self.id,'Video',1,status='ready')
        new=self.ready_preview(True)
        with self.assertRaises(HTTPException):self.video(new,regenerate=True,model_version=m)

    def test_approved_geometry_cannot_change_silently(self):
        n=self.ready_preview(True);m=self.ready_model(n)
        (store.version_dir(self.id,'3DModel',m)/'model.blend').write_bytes(b'changed')
        with self.assertRaises(HTTPException):self.video(n)
        self.assertEqual(store.history(self.id,'Video'),[])

    def test_preparation_api_is_blocked_even_for_regeneration(self):
        for stage in ('Preview','3DModel'):
            for regenerate in (False,True):
                with self.assertRaises(HTTPException) as caught:self.start(stage,regenerate=regenerate)
                self.assertEqual(caught.exception.status_code,409)
            self.assertEqual(store.history(self.id,stage),[])

    def test_final_approval_and_all_assets_required(self):
        n=self.ready_preview()
        with self.assertRaises(HTTPException):self.start('Video',preview_version=n)
        (store.version_dir(self.id,'Preview',n)/'scene_06.mp4').unlink()
        with self.assertRaises(HTTPException):self.video(n)

    def test_http_dispatch(self):
        with patch.object(main,'Worker') as worker,TestClient(main.app) as client:
            worker.return_value.stop=AsyncMock()
            response=client.post(f'/api/ideas/{self.id}/Preview',json={})
            self.assertEqual(response.status_code,409)
            self.assertEqual(client.post(f'/api/ideas/{self.id}/3DModel',json={}).status_code,409)

    def test_restart_and_concurrent_reservation(self):
        def reserve():
            try:return store.reserve(self.id,'3DModel',True)[0]['number']
            except ValueError:return None
        with concurrent.futures.ThreadPoolExecutor(8) as pool:results=list(pool.map(lambda _:reserve(),range(8)))
        self.assertEqual([r for r in results if r], [1])
        store.recover_interrupted();self.assertEqual(store.get(self.id,'3DModel',1)['status'],'failed')

    def test_detail_and_listing_are_separate(self):
        with TestClient(main.app) as client:
            page=client.get('/?category=tech').text
            self.assertIn('/ideas/'+self.id,page)
            self.assertNotIn('id="versions"',page)
            detail=client.get('/ideas/'+self.id)
            self.assertEqual(detail.status_code,200)
            self.assertIn('id="versions"',detail.text)
            self.assertEqual(client.get('/api/ideas/invalid').status_code,404)

    def test_fetch_blocks_internal_dns_and_blueprint_invalid_geometry(self):
        with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]),patch('socket.create_connection') as network:
            with self.assertRaises(ValueError):fetch('https://example.com/model.glb')
            network.assert_not_called()
        with self.assertRaises(ValueError):Blueprint.model_validate(dict(reference_matches_product=True,product_identity='X',uncertainties=['draft'],parts=[dict(name='x',shape='box',position=[0,0,0],dimensions=[-1,1,1],color=[1,1,1])]))

    def test_product_page_exposes_relative_model_and_overview_links(self):
        parser=PageAssets('https://example.com/news/article/')
        parser.feed('<a href="/test-product/">Product</a><a href="/ar/product.usdz">AR</a><meta property="og:image" content="/photo.jpg">')
        self.assertIn('https://example.com/test-product/',parser.links)
        self.assertEqual(parser.models,['https://example.com/ar/product.usdz'])
        self.assertEqual(parser.images,['https://example.com/photo.jpg'])

    def test_job_failure_is_retained_as_a_failed_version(self):
        store.reserve(self.id,'Preview')
        with patch.object(jobs,'preview_job',side_effect=ValueError('No matching sources')):
            asyncio.run(jobs.execute(self.id,'Preview',1))
        self.assertEqual(store.get(self.id,'Preview',1)['status'],'failed')
        new,_=store.reserve(self.id,'Preview',regenerate=True);self.assertEqual(new['number'],2)


if __name__=='__main__':unittest.main()
