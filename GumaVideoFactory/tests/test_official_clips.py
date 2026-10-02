import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.core import official_clips as clips, versions as store, studio_jobs as jobs


class OfficialClipTests(unittest.TestCase):
    def board(self):
        return clips.ClipBoard(title='테스트',summary='기술 설명',scenes=[dict(start_seconds=i*3,end_seconds=i*3+2,
            purpose='테스트 기능',visible_evidence='실제 시간표의 기능 시연 장면',narration_ko='자체 대본',covered_features=['main','second','third']) for i in range(6)])

    def test_time_bounds_overlap_and_missing_secondary_coverage(self):
        rec=dict(key_feature='main',supporting_features=['second','third'])
        board=self.board();clips.validate_board(board,20,rec)
        board.scenes[-1].end_seconds=21
        with self.assertRaises(ValueError):clips.validate_board(board,20,rec)
        board=self.board();board.scenes[1].start_seconds=1
        with self.assertRaises(ValueError):clips.validate_board(board,20,rec)
        board=self.board()
        for scene in board.scenes:scene.covered_features=['main']
        with self.assertRaises(ValueError):clips.validate_board(board,20,rec)

    def test_real_ffmpeg_preview_and_final_without_paid_api(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(store,'ROOT',root/'products'),patch.object(store,'STORAGE_DIR',root):
                idea=store.create(dict(category='tech',subject='Other product',sources=[],technical_video={},key_feature='main',supporting_features=['second','third']),'2026-10-02')
                iid=idea['id'];store.reserve(iid,'Preview');folder=store.version_dir(iid,'Preview',1)
                source=folder/'source.mp4'
                clips.run([clips.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=24','-t','20','-c:v','libx264',str(source)])
                meta=dict(url='https://www.youtube.com/watch?v=abcdefghijk',sha256='test',duration=20)
                store.write_json(folder/'source.json',meta)
                client=MagicMock();client.__enter__.return_value=client
                client.models.generate_content.side_effect=[SimpleNamespace(text=self.board().model_dump_json()),SimpleNamespace(text='{"passed":true,"issues":[]}')]
                with patch.object(clips,'download',return_value=(source,meta)),patch.object(clips.genai,'Client',return_value=client):
                    clips.create_preview(iid,1,lambda x:None)
                preview=store.get(iid,'Preview',1)
                self.assertEqual(preview['status'],'ready');self.assertFalse(preview['needs_3d'])
                self.assertEqual(len(list(folder.glob('scene_*.mp4'))),6)
                store.reserve(iid,'Video',preview_version=1,model_version=None,storyboard=preview['storyboard'],product_url='https://example.com/product')
                async def tts(text,path,**kwargs):
                    clips.run([clips.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','1','-c:a','libmp3lame',str(path)])
                with patch.object(jobs,'synthesize_speech',side_effect=tts),patch.object(jobs.blender,'video_size',return_value=(180,320)),patch.object(jobs,'generate_video_clip') as paid:
                    asyncio.run(jobs.video_job(iid,1));paid.assert_not_called()
                final=store.version_dir(iid,'Video',1)/'final.mp4'
                self.assertGreater(clips.duration(final),23)
                self.assertEqual(store.get(iid,'Video',1)['status'],'ready')
                provenance=json.loads((final.parent/'sources.json').read_text())
                self.assertEqual(len(provenance['clip_intervals']),6)
                # Exercise the hybrid compositor with a deterministic local 3D stand-in.
                preview['storyboard']['scenes'][0]['enhance_3d']=True
                store.reserve(iid,'3DModel',preview_version=1)
                store.update(iid,'3DModel',1,status='ready',approved_at='tested')
                store.reserve(iid,'Video',True,preview_version=1,model_version=1,storyboard=preview['storyboard'],product_url='https://example.com/product')
                def render(model,path,angle,seconds,**kwargs):
                    clips.run([clips.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','color=c=blue:size=180x320:rate=24','-t',str(seconds),'-c:v','libx264',str(path)])
                with patch.object(jobs,'synthesize_speech',side_effect=tts),patch.object(jobs.blender,'video_size',return_value=(180,320)),patch.object(jobs.blender,'clip',side_effect=render) as render3d:
                    asyncio.run(jobs.video_job(iid,2));render3d.assert_called_once()
                self.assertEqual(store.get(iid,'Video',2)['status'],'ready')
