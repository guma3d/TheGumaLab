"""실사 자료와 사용 조건을 보존하고 검증된 파일만 편집에 전달."""
import hashlib
import ipaddress
import socket
import ssl
import http.client
import subprocess
import tempfile
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from PIL import Image, ImageOps
from app.config import SOURCE_MEDIA_DIR
from app.core.ffmpeg_mixer import get_ffmpeg_bin

class MediaSource(BaseModel):
    title: str = Field(min_length=1,max_length=300)
    source_url: str = Field(min_length=1,max_length=2000)
    creator: str = Field(min_length=1,max_length=300)
    license: Literal['CC0','CC BY','CC BY-SA','permission','owned']
    license_url: str = Field(min_length=1,max_length=2000)
    attribution: str = Field(min_length=1,max_length=2000)
    provider: Literal['official','youtube_cc','commons','licensed_search','owned'] = 'official'
    kind: Literal['image','video'] = 'image'
    download_url: str = ''
    local_file: str = ''
    start_seconds: float = Field(default=0,ge=0,le=36000)
    clip_seconds: float = Field(default=3,gt=0,le=4)
    illustrative: bool = False

    @field_validator('source_url','license_url','download_url')
    @classmethod
    def valid_url(cls,value):
        if not value: return value
        p=urlparse(value)
        if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:
            raise ValueError('출처·사용 조건은 HTTP(S) 주소로 기록해주세요.')
        return value

    def file_path(self):
        name=self.local_file
        if not name or Path(name).name!=name or any(c not in '0123456789abcdef.'+'pngmp4' for c in name):
            raise ValueError('자료 파일이 준비되지 않았습니다.')
        path=SOURCE_MEDIA_DIR/name
        if not path.is_file(): raise ValueError('자료 파일이 없습니다.')
        return path

def store_media(content,kind):
    if len(content)>40*1024*1024: raise ValueError('자료는 40MB 이하로 등록해주세요.')
    SOURCE_MEDIA_DIR.mkdir(parents=True,exist_ok=True)
    if kind=='image':
        with Image.open(BytesIO(content)) as im:
            if im.format not in ('PNG','JPEG','WEBP') or im.width*im.height>25000000:
                raise ValueError('PNG/JPEG/WebP 사진만 등록해주세요.')
            buf=BytesIO();ImageOps.exif_transpose(im).convert('RGB').save(buf,format='PNG');content=buf.getvalue()
        suffix='.png'
    else:
        if len(content)<12 or content[4:8]!=b'ftyp': raise ValueError('정상 MP4 영상을 등록해주세요.')
        suffix='.mp4'
    name=hashlib.sha256(content).hexdigest()+suffix
    path=SOURCE_MEDIA_DIR/name
    path.write_bytes(content)
    if kind=='video':
        result=subprocess.run([get_ffmpeg_bin(),'-v','error','-protocol_whitelist','file,pipe','-i',str(path),'-frames:v','1','-f','null','-'],capture_output=True,timeout=30)
        if result.returncode: raise ValueError('영상을 디코딩할 수 없습니다.')
    return name

def download_media(source):
    """조사 도구에서만 실행. 내부 주소·리다이렉트·과대 파일 제외."""
    parsed=urlparse(source.download_url)
    if parsed.scheme!='https' or parsed.port not in (None,443): raise ValueError('직접 HTTPS 파일 주소가 필요합니다.')
    addresses=socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('공개 자료 서버만 사용할 수 있습니다.')
    # 검증했던 공개 IP로 연결하고 원래 호스트명으로 TLS 인증서를 검사합니다.
    class PinnedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            raw=socket.create_connection((addresses[0][4][0],443),timeout=30)
            self.sock=ssl.create_default_context().wrap_socket(raw,server_hostname=parsed.hostname)
    connection=PinnedHTTPS(parsed.hostname,timeout=30)
    try:
        target=parsed.path or '/'
        if parsed.query: target+='?'+parsed.query
        connection.request('GET',target,headers={'User-Agent':'GumaVideoFactory/1.0'})
        response=connection.getresponse()
        if response.status!=200: raise ValueError('직접 공개 파일 주소가 필요합니다.')
        content=response.read(40*1024*1024+1)
    finally:
        connection.close()
    return store_media(content,source.kind)

def media_preview(source,output_path,aspect_ratio):
    path=source.file_path()
    if source.kind=='image':
        size=(720,1280) if aspect_ratio=='9:16' else (1280,720)
        with Image.open(path) as image:
            ImageOps.pad(image.convert('RGB'),size,color='black').save(output_path)
    else:
        output_path.unlink(missing_ok=True)
        result=subprocess.run([get_ffmpeg_bin(),'-y','-v','error','-protocol_whitelist','file,pipe','-ss',str(source.start_seconds),'-i',str(path),'-frames:v','1',str(output_path)],capture_output=True,timeout=30)
        if result.returncode or not output_path.is_file(): raise ValueError('선택한 영상 구간에서 프리뷰를 만들 수 없습니다.')
    return output_path

def render_source_clip(source,output_path,aspect_ratio,duration=4):
    from app.core.ffmpeg_mixer import render_product_still
    path=source.file_path()
    if source.kind=='image': return render_product_still(path,output_path,aspect_ratio,duration)
    width,height=(720,1280) if aspect_ratio=='9:16' else (1280,720)
    cmd=[get_ffmpeg_bin(),'-y','-v','error','-protocol_whitelist','file,pipe','-ss',str(source.start_seconds),'-i',str(path),'-t',str(duration),'-vf',f'trim=duration={min(source.clip_seconds,duration)},setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=24,tpad=stop_mode=clone:stop={duration*24}', '-r','24','-an','-c:v','libx264','-pix_fmt','yuv420p',str(output_path)]
    result=subprocess.run(cmd,capture_output=True,timeout=120)
    if result.returncode: raise ValueError('실사 영상 편집에 실패했습니다.')
    return output_path

def download_youtube_cc(source):
    """CC BY 메타데이터가 확인되는 공개 YouTube 영상의 짧은 구간만 확보."""
    import yt_dlp
    from yt_dlp.utils import download_range_func
    p=urlparse(source.source_url)
    if source.license!='CC BY' or source.kind!='video' or p.scheme!='https' or p.hostname not in ('youtube.com','www.youtube.com','youtu.be') or p.username or p.password or p.port:
        raise ValueError('공개 YouTube CC BY 영상만 자동 확보할 수 있습니다.')
    from urllib.parse import parse_qs
    video_id=p.path.strip('/') if p.hostname=='youtu.be' else parse_qs(p.query).get('v',[''])[0] if p.path=='/watch' else ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id): raise ValueError('단일 YouTube 영상 주소가 필요합니다.')
    url='https://www.youtube.com/watch?v='+video_id
    with tempfile.TemporaryDirectory(prefix='gumavideo_cc_') as directory:
        options=dict(quiet=True,no_warnings=True,noplaylist=True,socket_timeout=20,retries=1,extractor_retries=1,
                     format='bestvideo[ext=mp4][height<=720]/best[ext=mp4][height<=720]',
                     outtmpl=str(Path(directory)/'source.%(ext)s'),max_filesize=40*1024*1024,
                     download_ranges=download_range_func(None,[(source.start_seconds,source.start_seconds+source.clip_seconds)]),
                     force_keyframes_at_cuts=True,ffmpeg_location=get_ffmpeg_bin())
        with yt_dlp.YoutubeDL(options) as downloader:
            info=downloader.extract_info(url,download=False)
            license_text=str(info.get('license') or '').lower()
            if 'creative commons' not in license_text or 'attribution' not in license_text or info.get('is_live') or info.get('_type','video')!='video':
                raise ValueError('YouTube에서 CC BY 사용 조건을 확인할 수 없습니다.')
            if float(info.get('duration') or 0)<=source.start_seconds:
                raise ValueError('발췌 시작 위치가 영상 길이를 벗어났습니다.')
            downloader.process_info(info)
        path=Path(directory)/'source.mp4'
        if not path.is_file() or path.stat().st_size>40*1024*1024: raise ValueError('짧은 MP4 구간을 확보하지 못했습니다.')
        name=store_media(path.read_bytes(),'video')
        source.attribution+=f"\n원본 발췌 위치: {source.start_seconds}초부터 {source.clip_seconds}초"
        source.start_seconds=0
        return name
