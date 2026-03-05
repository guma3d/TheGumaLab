import os
import sys
import json
import yt_dlp
import logging
import threading
import time

def extract_transcript_whisper(video_id):
    """yt-dlp 및 Faster Whisper (로컬 버전)를 사용하여 스크립트 추출"""
    # 동적 임포트: 필요할 때만 faster_whisper 로드
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise Exception("faster-whisper is not installed. Install with: pip install faster-whisper")
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_dir = "Temp_Audio"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    audio_path = os.path.join(temp_dir, f"{video_id}.m4a")
    
    # ===== YT-DLP FULL DEBUGGING - PROGRESS HOOK =====
    def yt_dlp_progress_hook(d):
        """yt-dlp 다운로드 진행상황 상세 출력"""
        status = d.get('status', 'unknown')
        
        if status == 'downloading':
            # 다운로드 진행 중
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            fragment_index = d.get('fragment_index')
            fragment_count = d.get('fragment_count')
            
            info_parts = []
            
            if total > 0:
                percent = (downloaded / total) * 100
                info_parts.append(f"진행률: {percent:.1f}%")
                info_parts.append(f"다운로드: {downloaded:,}/{total:,} bytes")
            else:
                info_parts.append(f"다운로드: {downloaded:,} bytes")
            
            if speed and speed > 0:
                info_parts.append(f"속도: {speed/1024:.1f} KB/s")
            
            if eta:
                info_parts.append(f"남은시간: {eta}초")
            
            if fragment_index and fragment_count:
                info_parts.append(f"Fragment: {fragment_index}/{fragment_count}")
            
            print(f"[YT-DLP DOWNLOAD] {' | '.join(info_parts)}", file=sys.stderr, flush=True)
                      
        elif status == 'finished':
            total = d.get('total_bytes', 0)
            elapsed = d.get('elapsed', 0)
            filename = d.get('filename', 'unknown')
            print(f"[YT-DLP DOWNLOAD] ✓ 다운로드 완료!", file=sys.stderr, flush=True)
            print(f"[YT-DLP DOWNLOAD]    - 파일: {filename}", file=sys.stderr, flush=True)
            print(f"[YT-DLP DOWNLOAD]    - 크기: {total:,} bytes", file=sys.stderr, flush=True)
            print(f"[YT-DLP DOWNLOAD]    - 소요시간: {elapsed:.2f}초", file=sys.stderr, flush=True)
            if elapsed > 0 and total > 0:
                avg_speed = total / elapsed / 1024
                print(f"[YT-DLP DOWNLOAD]    - 평균 속도: {avg_speed:.1f} KB/s", file=sys.stderr, flush=True)
                  
        elif status == 'error':
            print(f"[YT-DLP DOWNLOAD] ✗ 다운로드 오류 발생!", file=sys.stderr, flush=True)
    
    # ===== YT-DLP FULL DEBUGGING - DETAILED LOGGER =====
    class YtDlpDetailedLogger:
        """yt-dlp의 모든 내부 동작을 상세히 출력하는 로거"""
        def debug(self, msg):
            if msg.startswith('[debug]'):
                return  # 중복 방지
            print(f"[YT-DLP DEBUG] {msg}", file=sys.stderr, flush=True)
            
        def info(self, msg):
            print(f"[YT-DLP INFO] {msg}", file=sys.stderr, flush=True)
            
        def warning(self, msg):
            print(f"[YT-DLP WARNING] ⚠️  {msg}", file=sys.stderr, flush=True)
            
        def error(self, msg):
            print(f"[YT-DLP ERROR] ❌ {msg}", file=sys.stderr, flush=True)
    
    # yt-dlp 옵션 - 전체 디버깅 모드 (로컬)
    # Bot 차단 우회를 위한 설정 포함
    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': audio_path,
        'quiet': False,              # 로그 출력 활성화
        'verbose': True,             # 상세 로그
        'no_warnings': False,        # 경고 표시
        'progress_hooks': [yt_dlp_progress_hook],  # 진행상황 Hook
        'logger': YtDlpDetailedLogger(),           # 상세 로거
        # Bot 차단 우회 설정
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # 안드로이드 클라이언트 우선 사용
                'skip': ['hls', 'dash']  # m3u8 관련 이슈 회피
            }
        }
    }
    
    try:
        # ===== YT-DLP 다운로드 (상세 디버깅) =====
        print("\n" + "="*80, file=sys.stderr)
        print("📹 YT-DLP 오디오 다운로드 시작", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(f"[YT-DLP] URL: {video_url}", file=sys.stderr, flush=True)
        
        # 1. Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        print("\n" + "="*80, file=sys.stderr)
        print("✅ YT-DLP 다운로드 완료", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr, flush=True)
        
        # ===== WHISPER 상세 디버깅 시작 =====
        print("=" * 80, file=sys.stderr)
        print("🎤 WHISPER AI 음성 인식 상세 로그", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        import time
        start_time = time.time()
        
        # 2. Transcribe with Faster Whisper
        model_size = "turbo"
        
        print(f"\n[WHISPER] 📥 모델 로딩 중...", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 모델: {model_size}", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 디바이스: CUDA (GPU)", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 연산 타입: float16", file=sys.stderr, flush=True)
        
        print(f"[WHISPER] ⚙️  Whisper 모델 초기화 중...", file=sys.stderr, flush=True)
        
        # ===== 장시간 작업을 위한 하트비트 로거 =====
        class LoadingIndicator(threading.Thread):
            def __init__(self, msg_prefix):
                super().__init__()
                self.msg_prefix = msg_prefix
                self.running = True
                self.start_time = time.time()
                
            def run(self):
                while self.running:
                    time.sleep(2)
                    if not self.running: break
                    elapsed = int(time.time() - self.start_time)
                    print(f"{self.msg_prefix} ({elapsed}s...)", file=sys.stderr, flush=True)

            def stop(self):
                self.running = False
                self.join()

        model_load_start = time.time()
        print(f"[WHISPER] 💾 메모리에 모델 적재 중...", file=sys.stderr, flush=True)
        
        loader_params = LoadingIndicator("[WHISPER] ⏳ 모델 로딩 진행 중")
        loader_params.start()
        
        try:
            model = WhisperModel(model_size, device="cuda", compute_type="float16")
        finally:
            loader_params.stop()
            
        model_load_time = time.time() - model_load_start
        
        print(f"[WHISPER] ✓ 모델 로딩 완료 (소요시간: {model_load_time:.2f}초)\n", file=sys.stderr, flush=True)
        
        print(f"[WHISPER] 🔍 오디오 파일 분석 중...", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 파일: {audio_path}", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - Beam size: 5", file=sys.stderr, flush=True)
        
        # 임포트 확인

        print(f"[WHISPER] 🧠 딥러닝 추론 시작...", file=sys.stderr, flush=True)
        transcribe_start = time.time()
        
        loader_infer = LoadingIndicator("[WHISPER] ⏳ 추론 진행 중")
        loader_infer.start()
        
        try:
            segments, info = model.transcribe(audio_path, beam_size=5)
        finally:
            loader_infer.stop()
        
        print(f"\n[WHISPER] ✓ 오디오 분석 완료", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 감지된 언어: {info.language}", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 언어 확률: {info.language_probability:.4f} ({info.language_probability*100:.2f}%)", file=sys.stderr, flush=True)
        print(f"[WHISPER]    - 예상 총 길이: {info.duration:.2f}초", file=sys.stderr, flush=True)
        
        print(f"\n[WHISPER] 📝 세그먼트 처리 시작...\n", file=sys.stderr, flush=True)
        print("-" * 80, file=sys.stderr)
        
        html_snippet = ""
        segment_count = 0
        total_chars = 0
        
        for segment in segments:
            segment_count += 1
            start = round(segment.start, 2)
            end = round(segment.end, 2)
            duration = end - start
            text = segment.text.strip()
            
            if text:
                # 상세 로그 출력
                text_preview = text[:60] + "..." if len(text) > 60 else text
                print(f"[WHISPER] Segment #{segment_count:03d}", file=sys.stderr, flush=True)
                print(f"          ⏱️  시간: {start:.2f}s ~ {end:.2f}s (길이: {duration:.2f}s)", file=sys.stderr, flush=True)
                print(f"          📄 텍스트: {text_preview}", file=sys.stderr, flush=True)
                print(f"          📊 문자수: {len(text)} chars", file=sys.stderr, flush=True)
                
                # 평균 단어 확률 표시 (있는 경우)
                if hasattr(segment, 'avg_logprob'):
                    print(f"          🎯 평균 확률: {segment.avg_logprob:.4f}", file=sys.stderr, flush=True)
                
                # No speech 확률 표시 (있는 경우)
                if hasattr(segment, 'no_speech_prob'):
                    print(f"          🔇 No-speech 확률: {segment.no_speech_prob:.4f}", file=sys.stderr, flush=True)
                
                print("-" * 80, file=sys.stderr, flush=True)
                
                html_snippet += f"<div><small>[{start}s]</small> {text}</div>"
                total_chars += len(text)
        
        transcribe_time = time.time() - transcribe_start
        total_time = time.time() - start_time
        
        print(f"\n{'=' * 80}", file=sys.stderr)
        print(f"✅ WHISPER 처리 완료!", file=sys.stderr)
        print(f"{'=' * 80}", file=sys.stderr)
        print(f"📊 처리 통계:", file=sys.stderr)
        print(f"   - 총 세그먼트 수: {segment_count}", file=sys.stderr)
        print(f"   - 총 문자 수: {total_chars:,} chars", file=sys.stderr)
        print(f"   - 모델 로딩 시간: {model_load_time:.2f}초", file=sys.stderr)
        print(f"   - 음성 인식 시간: {transcribe_time:.2f}초", file=sys.stderr)
        print(f"   - 전체 처리 시간: {total_time:.2f}초", file=sys.stderr)
        print(f"   - 처리 속도: {info.duration/transcribe_time:.2f}x 실시간", file=sys.stderr)
        print(f"{'=' * 80}\n", file=sys.stderr, flush=True)
        
        # 오디오 파일 정리
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        return html_snippet
        
    except Exception as e:
        # 실패 시 정리
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        raise e

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "No video ID provided"}), flush=True)
        sys.stdout.flush()
        sys.exit(1)
        
    video_id = sys.argv[1]
    
    # 파이프 교착 상태를 피하기 위해 stdout 대신 파일에 결과 기록
    result_file = os.path.join("Temp_Audio", f"{video_id}_result.json")
    
    try:
        print(f"[MAIN] Calling extract_transcript_whisper for video: {video_id}", file=sys.stderr, flush=True)
        transcript_html = extract_transcript_whisper(video_id)
        print(f"[MAIN] extract_transcript_whisper returned. HTML length: {len(transcript_html) if transcript_html else 0}", file=sys.stderr, flush=True)
        
        if transcript_html:
            print(f"[MAIN] Creating JSON result...", file=sys.stderr, flush=True)
            result = {
                "success": True, 
                "html": transcript_html, 
                "method": "whisper"
            }
            
            # stdout 대신 파일에 결과 기록
            print(f"[MAIN] Writing result to file: {result_file}", file=sys.stderr, flush=True)
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f)
            
            print(f"[MAIN] Result file written successfully", file=sys.stderr, flush=True)
            print("SUCCESS", flush=True)  # Simple success indicator on stdout
            sys.stdout.flush()
            print(f"[MAIN] Calling sys.exit(0)...", file=sys.stderr, flush=True)
            sys.exit(0)
        else:
            print(f"[MAIN] No transcript generated (transcript_html is empty)", file=sys.stderr, flush=True)
            result = {
                "success": False, 
                "message": "No transcript generated"
            }
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f)
            print("FAILURE", flush=True)
            sys.stdout.flush()
            sys.exit(1)
            
    except Exception as e:
        print(f"[MAIN] Exception caught: {str(e)}", file=sys.stderr, flush=True)
        print(f"Error: {str(e)}", file=sys.stderr, flush=True)
        result = {
            "success": False, 
            "message": f"Failed to extract transcript: {str(e)}"
        }
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f)
        except:
            pass
        print("ERROR", flush=True)
        sys.stdout.flush()
        sys.exit(1)
