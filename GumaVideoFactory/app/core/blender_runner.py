import os
import shutil
import subprocess
import threading
from pathlib import Path
from app.core.ffmpeg_mixer import get_ffmpeg_bin

RENDER_LOCK = threading.Lock()
SCRIPT = Path(__file__).with_name('blender_scene.py')


def video_size():
    width=int(os.getenv('BLENDER_VIDEO_WIDTH','720'))
    if width not in (720,1080):raise ValueError('BLENDER_VIDEO_WIDTH는 720 또는 1080으로 설정해주세요.')
    return width,width*16//9


def run_blender(folder, *args, timeout=3600):
    binary=shutil.which('blender')
    if not binary: raise ValueError('Blender 실행기가 없습니다. 서비스 이미지를 다시 빌드해주세요.')
    # No API keys/environment credentials enter the renderer.
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TEMP','TMP','SystemRoot','LD_LIBRARY_PATH')}
    env['OMP_NUM_THREADS']='4'
    with RENDER_LOCK:
        with (folder/'render.log').open('ab') as log:
            result=subprocess.run([binary,'--background','--factory-startup','--disable-autoexec',
                '--threads','4','--python-exit-code','1','--python',str(SCRIPT),'--',*map(str,args)],
                stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env,cwd=folder)
        if result.returncode:
            raise ValueError('3D 렌더링에 실패했습니다. 해당 버전의 render.log를 확인해주세요.')


def build(folder, source=None, product_name=''):
    if (folder/'model.blend').exists():
        raise ValueError('기존 Blender 파일은 덮어쓸 수 없습니다. 새 버전으로 생성해주세요.')
    params=['--source',source] if source else ['--build',folder/'blueprint.json']
    run_blender(folder,*params,'--output',folder,'--product-name',product_name)
    if not (folder/'model.blend').is_file() or not all((folder/f'view_{i}.png').is_file() for i in range(1,5)):
        raise ValueError('모델 프리뷰가 완성되지 않았습니다.')


def still(model, output, angle=25):
    run_blender(output.parent,'--scene',model,'--output',output,'--angle',angle,'--width',540,'--height',960)


def clip(model, output, angle=25, duration=4):
    frames=output.parent/(output.stem+'_frames'); frames.mkdir(exist_ok=False)
    width,height=video_size()
    run_blender(output.parent,'--scene',model,'--output',frames,'--angle',angle,
                '--width',width,'--height',height,'--samples',64,'--frames',max(2,round(duration*24)),timeout=7200)
    result=subprocess.run([get_ffmpeg_bin(),'-v','error','-framerate','24','-i',str(frames/'frame_%04d.png'),
            '-c:v','libx264','-pix_fmt','yuv420p',str(output)],capture_output=True,timeout=180)
    if result.returncode: raise ValueError('3D 영상 인코딩에 실패했습니다.')
