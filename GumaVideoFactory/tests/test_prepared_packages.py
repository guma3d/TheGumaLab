import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import prepared_packages as p, versions as s, official_clips as c, studio_jobs as jobs


class PreparedPackageTests(unittest.TestCase):
    def test_local_preparation_seal_tamper_and_final_veo(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(s,'ROOT',Path(temp)/'products'),patch.object(s,'STORAGE_DIR',Path(temp)),patch.object(c.genai,'Client',side_effect=AssertionError('paid API forbidden')):
            rec=dict(category='tech',subject='Local fixture',sources=[],technical_video={},key_feature='main',supporting_features=['second','third'])
            def download(source,folder):
                path=folder/'source.mp4'
                c.run([c.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=24','-t','20','-c:v','libx264',str(path)])
                meta=dict(duration=20,sha256=p.digest(path),url='https://example.com/official')
                s.write_json(folder/'source.json',meta);return path,meta
            with patch.object(c,'download',side_effect=download):result=p.prepare(rec,'2026-10-02')
            id=result['id'];n=result['version'];folder=s.version_dir(id,'Preview',n)
            self.assertIsNone(s.read(id)['idea_approved_at'])
            self.assertEqual(p.prepare(rec,'2026-10-02')['version'],n)
            board=c.ClipBoard(title='검증',summary='로컬 테스트',scenes=[dict(start_seconds=i*3,end_seconds=i*3+2,purpose='테스트',visible_evidence='테스트 패턴에 대한 검증 자료',narration_ko='대본',covered_features=['main','second','third']) for i in range(6)])
            draft=Path(temp)/'board.json';s.write_json(draft,board.model_dump());p.draft(id,n,draft)
            report=dict(reviewed_by='codex',passed=True,source_sha256=p.digest(folder/'source.mp4'),board_sha256=p.digest(folder/'storyboard.json'),veo_transition='light',scenes=[dict(number=i,feature_match=True,correct_product=True,clean_boundaries=True,notes='synthetic test fixture') for i in range(1,7)])
            review=Path(temp)/'review.json';s.write_json(review,report)
            broken=dict(report,board_sha256='wrong');s.write_json(review,broken)
            with self.assertRaises(ValueError):p.seal(id,n,review)
            s.write_json(review,report);p.seal(id,n,review);p.verify_package(id,n)
            with self.assertRaises(ValueError):p.draft(id,n,draft)
            with self.assertRaises(ValueError):p.seal(id,n,review)
            asset=folder/'scene_01.png';old=asset.read_bytes();asset.write_bytes(b'tampered')
            with self.assertRaises(ValueError):p.verify_package(id,n)
            asset.write_bytes(old)
            preview=s.get(id,'Preview',n)
            s.reserve(id,'Video',preview_version=n,storyboard=preview['storyboard'],model_version=None,product_url='https://example.com',veo_transition='light')
            async def tts(text,path,**kw):c.run([c.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','1','-c:a','libmp3lame',str(path)])
            def veo(**kw):c.run([c.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','color=c=teal:size=180x320:rate=24','-t','4','-c:v','libx264',str(kw['output_path'])])
            with patch.object(jobs,'generate_video_clip',side_effect=veo) as paid,patch.object(jobs,'synthesize_speech',side_effect=tts),patch.object(jobs.blender,'video_size',return_value=(180,320)):
                asyncio.run(jobs.video_job(id,1));paid.assert_called_once()
                self.assertNotIn('image_path',paid.call_args.kwargs)
            self.assertEqual(s.get(id,'Video',1)['status'],'ready')
            self.assertGreater(c.duration(s.version_dir(id,'Video',1)/'final.mp4'),27)

    def test_stale_queue_cannot_use_paid_planner_or_model(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(s,'ROOT',Path(temp)),patch.object(c.genai,'Client',side_effect=AssertionError('paid API forbidden')):
            idea=s.create(dict(category='tech',subject='stale'),'2026-10-02')
            for fn in (jobs.preview_job,jobs.model_job):
                with self.assertRaises(ValueError):fn(idea['id'],1)
