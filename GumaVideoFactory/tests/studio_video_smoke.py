"""Offline integration: real six-cut encoding/muxing, no generation APIs."""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app.core import versions as store, studio_jobs as jobs, source_media


async def run():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        with patch.object(store,'ROOT',root/'products'),patch.object(store,'STORAGE_DIR',root),patch.object(source_media,'SOURCE_MEDIA_DIR',root):
            photo=root/('a'*64+'.png');Image.new('RGB',(80,120),'teal').save(photo)
            rec=dict(category='food',subject='Offline test',product_keyword='Test',sources=[])
            idea=store.create(rec,'2026-10-02');iid=idea['id']
            model,_=store.reserve(iid,'3DModel');store.update(iid,'3DModel',1,status='ready',sources=[])
            preview,_=store.reserve(iid,'Preview',model_version=1)
            media=dict(title='Test',source_url='https://example.com',creator='Test',license='owned',license_url='https://example.com',attribution='Test',local_file=photo.name,kind='image')
            board=dict(scenes=[dict(scene_number=i,narration_ko=str(i),visual_mode='real_media',media_source=media) for i in range(1,7)])
            store.update(iid,'Preview',1,status='ready',storyboard=board)
            version,_=store.reserve(iid,'Video',model_version=1,preview_version=1,storyboard=board,product_url='https://example.com')
            async def speech(text,path,**kwargs):
                duration=5 if text=='1' else 2
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'sine=frequency=220:duration={duration}','-c:a','libmp3lame',str(path)],check=True)
            with patch.object(jobs,'synthesize_speech',side_effect=speech),patch.object(jobs,'generate_video_clip',side_effect=AssertionError('No paid API')),patch.object(jobs.blender,'clip',side_effect=AssertionError('No food 3D')):
                await jobs.video_job(iid,1)
            result=store.get(iid,'Video',1);assert result['status']=='ready'
            output=store.version_dir(iid,'Video',1)/'final.mp4'
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
            assert {s['codec_type'] for s in info['streams']}=={'video','audio'}
            assert float(info['format']['duration'])>=25.3,info['format']['duration']
            assert [s for s in info['streams'] if s['codec_type']=='video'][0]['width']==720
            print('PASS: six real clips, synchronized audio, long narration preserved, zero generation APIs')


asyncio.run(run())
