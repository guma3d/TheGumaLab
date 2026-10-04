"""Measured media gates; editorial approval is separate from technical success."""
import json
import subprocess
import io
from fractions import Fraction
from PIL import Image, ImageOps

REVIEW_AXES = ('source_fidelity', 'sharpness', 'vertical_composition', 'pacing', 'voice', 'audience_fit', 'hook')
PREFLIGHT_AXES = ('source_fidelity','source_resolution','vertical_composition','script_pacing','audience_fit','hook')

def validate_preflight(review):
    checks=review.get('preflight',{})
    if any(checks.get(k) is not True for k in PREFLIGHT_AXES) or review.get('unresolved_issues'):
        raise ValueError('제작 전 원본·해상도·세로구도·대본 템포·타깃·후킹 검수를 완료하세요.')

def inspect_output(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    audios=[s for s in data['streams'] if s['codec_type']=='audio']
    fps=float(Fraction(video['avg_frame_rate']))
    if (video['width'],video['height'])!=(1080,1920) or abs(fps-30)>.05 or not audios:
        raise ValueError('최종 영상은 음성이 포함된 1080×1920·30fps여야 합니다.')
    duration=float(video.get('duration',0))
    samples=[]
    for fraction in (.1,.3,.5,.7,.9):
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(duration*fraction),'-i',str(path),'-frames:v','1','-vf','scale=108:192','-f','image2pipe','-vcodec','png','-'])
        with Image.open(io.BytesIO(raw)) as frame:
            gray=frame.convert('L')
            edges=[list(gray.crop(box).tobytes()) for box in ((0,0,108,12),(0,180,108,192))]
            bars=all(sum(p<12 for p in edge)/len(edge)>.98 for edge in edges)
            samples.append(dict(at=round(duration*fraction,2),black_borders=bars))
    if any(s['black_borders'] for s in samples):
        raise ValueError('최종 영상 위아래 검은 여백이 감지됐습니다. 구도를 수정하세요.')
    return dict(width=1080,height=1920,fps=30,audio_present=True,border_samples=samples,passed=True)

def dimensions(path):
    if path.suffix.lower() != '.mp4':
        with Image.open(path) as im:
            return ImageOps.exif_transpose(im).size
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','json',str(path)]))
    stream=data['streams'][0]
    return stream['width'],stream['height']

def inspect_source(path):
    w,h=dimensions(path)
    # 720px originals may occupy a bounded region; never enlarge thumbnails into full-screen detail.
    minimum=1080 if path.suffix.lower()=='.mp4' else 720
    if min(w,h)<minimum:
        raise ValueError(f'원본 해상도 부족: {w}×{h}; 최소 짧은 변 {minimum}px. 고해상도 원본을 다시 확보하세요.')
    scale=min(1080/w,1920/h)
    if scale>1.5:
        raise ValueError('원본을 1.5배 이상 확대할 수 없습니다. 더 큰 자료가 필요합니다.')
    return dict(width=w,height=h,enlargement=round(scale,3),max_enlargement=1.5,passed=True)

def validate_editorial(review):
    scores=review.get('scores',{})
    if any(type(scores.get(k)) not in (int,float) or not 8<=scores[k]<=10 for k in REVIEW_AXES):
        raise ValueError('실물·선명도·세로구도·템포·음성·타깃·후킹 각 8/10 이상 검수가 필요합니다.')
    if not review.get('listened_to_audio') or review.get('unresolved_issues'):
        raise ValueError('실제 음성 청취 검수와 미해결 문제 수정 후 진행하세요.')

def portrait_filter(background='f4eee8'):
    # Preserve the entire official product, fill the remaining canvas without black letterboxing.
    return f'scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x{background},setsar=1'


def generated_portrait_filter(path):
    """Remove only consistent baked-in top/bottom matte before reframing generated context."""
    w,h=dimensions(path)
    margins=[]
    for at in (.2,1,2):
        raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1','-vf','scale=108:192','-f','image2pipe','-vcodec','png','-'])
        with Image.open(io.BytesIO(raw)) as frame:
            gray=frame.convert('L');rows=[]
            for y in range(192):
                rows.append(sum(gray.getpixel((x,y))<12 for x in range(108))/108>.95)
            top=next((i for i,b in enumerate(rows) if not b),0)
            bottom=next((i for i,b in enumerate(reversed(rows)) if not b),0)
            margins.append((top,bottom))
    top=min(x[0] for x in margins)*h//192//2*2
    bottom=min(x[1] for x in margins)*h//192//2*2
    if top+bottom>h*.3:raise ValueError('생성 영상의 여백이 지나치게 큽니다. 장면을 다시 검토하세요.')
    prefix=f'crop={w}:{h-top-bottom}:0:{top},' if top or bottom else ''
    return prefix+'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1'
