from flask import Flask, request, jsonify, send_from_directory, Response
import subprocess
import json
import os
import re
import sys
import threading
import time
import logging
from datetime import datetime

app = Flask(__name__, static_folder='.')

# ===== LOGGING SETUP =====
# Logs 폴더 생성
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 로그 파일 이름: Server_YYYYMMDD_HHMMSS.log
log_filename = f"Server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(logs_dir, log_filename)

# 로거 설정
logger = logging.getLogger('YouTube_Extractor')
logger.setLevel(logging.DEBUG)

# 파일 핸들러 (모든 로그)
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 콘솔 핸들러 (INFO 이상만)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 로그 포맷
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("=" * 80)
logger.info("YouTube Script Extractor Server Started")
logger.info(f"Log file: {log_filepath}")
logger.info("=" * 80)

# 전역 진행 상태 추적
progress_data = {
    'video_id': None,
    'progress': 0,
    'status': '',
    'completed': False,  # 완료 여부
    'error': None,
    'result': None
}

@app.route('/')
def index():
    return send_from_directory('.', 'YoutubeAnalyzer.html')

@app.route('/extract', methods=['POST'])
def extract():
    global progress_data
    
    data = request.json
    url = data.get('url', '')
    
    logger.info(f"New extraction request: {url}")
    
    if not url:
        logger.warning("Empty URL provided")
        return jsonify({'success': False, 'message': 'URL is required'})
    
    # 비디오 ID 추출
    match = re.search(r'(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})', url)
    if not match:
        logger.warning(f"Invalid YouTube URL: {url}")
        return jsonify({'success': False, 'message': 'Invalid YouTube URL'})
    
    video_id = match.group(1)
    logger.info(f"Extracted video ID: {video_id}")
    
    # 진행 상태 초기화
    progress_data = {
        'video_id': video_id,
        'progress': 0,
        'status': 'Starting...',
        'completed': False,
        'error': None,
        'result': None
    }
    
    # 백그라운드 스레드에서 추출 시작
    thread = threading.Thread(target=extract_video, args=(video_id,))
    thread.start()
    logger.info(f"Background extraction thread started for video: {video_id}")
    
    return jsonify({'success': True, 'video_id': video_id})

@app.route('/status')
def status():
    """현재 진행 상태 반환"""
    return jsonify(progress_data)

@app.route('/progress/<video_id>')
def get_progress(video_id):
    """실시간 진행률을 위한 SSE (Server-Sent Events) 엔드포인트"""
    def generate():
        while True:
            if progress_data['video_id'] == video_id:
                data = json.dumps({
                    'progress': progress_data['progress'],
                    'status': progress_data['status'],
                    'completed': progress_data['completed'],
                    'error': progress_data['error'],
                    'result': progress_data['result']
                })
                yield f"data: {data}\n\n"
                
                if progress_data['completed'] or progress_data['error']:
                    break
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/scripts/list')
def list_scripts():
    """생성된 모든 스크립트 목록 반환"""
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Scripts')
    
    if not os.path.exists(scripts_dir):
        return jsonify({'success': True, 'scripts': []})
    
    scripts = []
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(scripts_dir, filename)
            
            # 파일명에서 비디오 ID 추출 (yt_VIDEOID.html)
            video_id = filename.replace('yt_', '').replace('.html', '')
            
            # HTML을 파싱하여 제목과 썸네일 추출
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # <title> 태그에서 제목 추출
                    title_match = re.search(r'<title>(.+?) - Script</title>', content)
                    title = title_match.group(1) if title_match else 'Unknown Title'
                    
                    # <img> 태그에서 썸네일 추출
                    thumbnail_match = re.search(r"<img src='([^']+)'", content)
                    thumbnail = thumbnail_match.group(1) if thumbnail_match else f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
                    
                    # 파일 수정 시간 가져오기
                    mtime = os.path.getmtime(filepath)
                    
                    scripts.append({
                        'filename': filename,
                        'video_id': video_id,
                        'title': title,
                        'thumbnail': thumbnail,
                        'youtube_url': f'https://www.youtube.com/watch?v={video_id}',
                        'script_url': f'Scripts/{filename}',
                        'created_at': mtime
                    })
            except Exception as e:
                logger.error(f"Error parsing {filename}: {e}")
                continue
    
    # 생성 시간 내림차순 정렬 (최신순)
    scripts.sort(key=lambda x: x['created_at'], reverse=True)
    
    logger.info(f"Listed {len(scripts)} scripts")
    return jsonify({'success': True, 'scripts': scripts})

@app.route('/Scripts/<filename>')
def serve_script(filename):
    """생성된 스크립트 HTML 파일 제공"""
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Scripts')
    return send_from_directory(scripts_dir, filename)


def update_progress(progress, status):
    global progress_data
    progress_data['progress'] = progress
    progress_data['status'] = status
    logger.info(f"[{progress}%] {status}")
    print(f"[{progress}%] {status}", flush=True)  # flush=True for real-time display
    sys.stdout.flush()  # Force output to terminal

def extract_video(video_id):
    global progress_data
    
    try:
        logger.info(f"Starting extraction for video: {video_id}")
        update_progress(5, '비디오 정보 추출 중...')
        
        # 제목 먼저 가져오기
        logger.debug(f"Getting video title for: {video_id}")
        title_result = subprocess.run(
            [sys.executable, '-m', 'yt_dlp', '--skip-download', '--print', 'title', f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        title = title_result.stdout.strip() or 'Unknown Title'
        logger.info(f"Video title: {title}")
        
        update_progress(10, f'오디오 다운로드: {title}...')
        
        # 진행 상태 모니터링과 함께 추출 스크립트 실행
        logger.debug(f"Starting extract_transcript.py subprocess for: {video_id}")
        process = subprocess.Popen(
            [sys.executable, '-u', 'extract_transcript.py', video_id],  # -u: unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # 버퍼링 없음 (1에서 변경됨)
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # stderr를 통해 진행 상태(extract_transcript.py 출력) 모니터링
        line_count = 0
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            line = line.strip()
            
            # 디버그 라인을 서버 콘솔과 로그 파일에 출력
            if line:
                line_count += 1
                print(f"[DEBUG] {line}", flush=True)
                logger.debug(f"extract_transcript.py: {line}")
            
            # 새로운 상세 디버그 포맷 파싱
            if 'YT-DLP 오디오 다운로드 시작' in line or '[YT-DLP INFO]' in line:
                update_progress(15, 'YouTube에서 오디오 다운로드 중...')
            elif '[YT-DLP DOWNLOAD]' in line and '진행률:' in line:
                # 퍼센트 추출: [YT-DLP DOWNLOAD] 진행률: 45.8% | ...
                try:
                    percent_str = line.split('진행률:')[1].split('%')[0].strip()
                    percent = float(percent_str)
                    update_progress(15 + int(percent * 0.2), f'다운로드 중: {percent:.1f}%...')
                except:
                    pass
            elif 'YT-DLP 다운로드 완료' in line:
                update_progress(35, '오디오 다운로드 완료!')
            elif '[WHISPER] 모델 로딩 중' in line:
                update_progress(38, 'Whisper AI 초기화 중...')
            elif '[WHISPER] Whisper 모델 초기화 중' in line:
                update_progress(40, '모델 파라미터 설정 중...')
            elif '[WHISPER] 메모리에 모델 적재 중' in line:
                update_progress(42, '메모리에 모델 로딩 중 (대용량 I/O)...')
            elif '[WHISPER] ⏳ 모델 로딩 진행 중' in line:
                try:
                    time_str = line.split('(')[1].split(')')[0]
                    update_progress(43, f'모델 로딩 중... {time_str}')
                except:
                    pass
            elif '[WHISPER] 모델 로딩 완료' in line:
                update_progress(45, 'Whisper 모델 로드 성공!')
            elif '[WHISPER] 오디오 파일 분석 중' in line:
                update_progress(48, '오디오 파형 분석 중...')
            elif '[WHISPER] 딥러닝 추론 시작' in line:
                update_progress(50, '딥러닝 추론 시작...')
            elif '[WHISPER] ⏳ 추론 진행 중' in line:
                try:
                    time_str = line.split('(')[1].split(')')[0]
                    update_progress(52, f'딥러닝 추론 중... {time_str}')
                except:
                    pass
            elif '[WHISPER] 감지된 언어:' in line:
                try:
                    lang = line.split('감지된 언어:')[1].split('(')[0].strip()
                    update_progress(55, f'감지된 언어: {lang}')
                except:
                    update_progress(55, '언어 감지됨')
            elif '[WHISPER] 세그먼트 처리 시작' in line:
                update_progress(60, '세그먼트 변환 중...')
            elif '[WHISPER] Segment #' in line:
                # 세그먼트 번호 추출
                try:
                    seg_num = int(line.split('#')[1].split()[0])
                    # 최대 100 세그먼트 가정, 60~85% 범위로 진행률 매핑
                    progress = 60 + min(25, int(seg_num * 0.25))
                    update_progress(progress, f'세그먼트 #{seg_num} 처리 중...')
                except:
                    pass
            elif 'WHISPER 처리 완료' in line:
                update_progress(90, 'Whisper 받아쓰기 완료!')
        
        logger.info(f"extract_transcript.py completed. Total debug lines: {line_count}")
        
        # 결과 가져오기
        stdout, stderr = process.communicate()
        
        logger.debug(f"Process return code: {process.returncode}")
        
        if process.returncode != 0:
            logger.error(f"Extraction process failed with return code {process.returncode}")
            logger.error(f"stderr: {stderr}")
            logger.error(f"stdout: {stdout}")
            raise Exception(f"Extraction failed: {stderr}")
        
        update_progress(90, '스크립트 처리 중...')
        
        # 파이프 교착 상태를 피하기 위해 stdout 대신 파일에서 결과 읽기
        result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Temp_Audio', f"{video_id}_result.json")
        logger.debug(f"Reading result from file: {result_file}")
        
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                transcript_result = json.load(f)
            logger.debug(f"Result file loaded successfully")
            
            # Clean up result file
            os.remove(result_file)
            logger.debug(f"Result file removed")
        except FileNotFoundError:
            logger.error(f"Result file not found: {result_file}")
            logger.error(f"stdout: {stdout}")
            raise Exception(f"Result file not found. Process may have failed silently.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from file: {e}")
            raise Exception(f"Failed to parse transcript result: {e}")
        
        if not transcript_result.get('success'):
            error_msg = transcript_result.get('message', 'Unknown error')
            logger.error(f"Transcript extraction failed: {error_msg}")
            raise Exception(error_msg)
        
        logger.info("Transcript extraction successful")
        update_progress(95, 'HTML 파일 생성 중...')
        
        # HTML 파일 저장
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
        file_name = f"yt_{video_id}.html"
        
        scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Scripts')
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
            logger.debug(f"Created Scripts directory: {scripts_dir}")
        
        file_path = os.path.join(scripts_dir, file_name)
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        full_html = f"""<!DOCTYPE html><html><head><title>{title} - Script</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;line-height:1.8;padding:40px 20px;background:#000;color:#fff;}}h1{{font-size:28px;margin-bottom:25px;padding-bottom:15px;border-bottom:2px solid #333;color:#fff;font-weight:700;}}img{{width:100%;border-radius:8px;margin-bottom:30px;border:1px solid #333;}}div{{margin-bottom:20px;padding:15px;background:#1a1a1a;border-left:3px solid #444;border-radius:4px;transition:all 0.3s;}}div:hover{{background:#222;border-left-color:#666;}}small{{color:#999;font-size:12px;font-weight:600;margin-right:15px;display:inline-block;min-width:60px;letter-spacing:0.5px;}}@media(max-width:768px){{body{{padding:20px 10px;}}h1{{font-size:22px;}}small{{display:block;margin-bottom:8px;}}}}</style>
</head><body><div style="max-width:900px;margin:0 auto;background:#111;border:1px solid #333;border-radius:8px;padding:40px;box-shadow:0 4px 20px rgba(0,0,0,0.5);"><h1>{title}</h1><img src='{thumbnail}'>{transcript_result['html']}<div style="margin-top:40px;padding-top:20px;border-top:1px solid #333;text-align:center;color:#666;font-size:13px;">Generated by YouTube Transcript Lab</div></div></body></html>"""
        
        logger.debug(f"Saving HTML to: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        logger.info(f"HTML file saved: {file_path}")
        update_progress(100, 'Completed!')
        
        progress_data['completed'] = True
        progress_data['result'] = {
            'success': True,
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'scriptPath': f'Scripts/{file_name}'
        }
        
        logger.info(f"✓ Extraction completed successfully for: {title} ({video_id})")
        
    except Exception as e:
        logger.error(f"✗ Extraction failed for video {video_id}: {str(e)}", exc_info=True)
        progress_data['error'] = str(e)
        progress_data['completed'] = True
        progress_data['status'] = f'Error: {str(e)}'

if __name__ == '__main__':
    print("\nYouTube Script Extractor (Local)")
    print("=" * 50)
    print("Server running at: http://localhost:5000")
    print("=" * 50)
    print("\nPress Ctrl+C to stop the server\n")
    app.run(host='0.0.0.0', debug=True, port=5000, threaded=True)
