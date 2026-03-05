import cv2
import numpy as np
import os
import yt_dlp

def process_video(video_url):
    """
    YouTube 비디오를 다운로드하고 10초마다 프레임을 분석합니다.
    """
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # 1. 비디오 다운로드
    # 혼잡을 피하기 위해 고정된 이름 사용, 또는 해시 기반. 단순성을 위해 'temp_video.mp4' 사용.
    # 이상적으로는 요청당 고유해야 하지만, 단일 사용자 모드에서는 적합함.
    video_filename = "temp_video.mp4"
    video_path = os.path.join(upload_dir, video_filename)
    
    # 기존 임시 파일 제거
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
        except:
            pass # 사용 중일 수 있음

    ydl_opts = {
        'outtmpl': video_path,
        'format': 'bestvideo*+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'overwrites': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"[ERROR] yt-dlp download failed: {str(e)}")
        return {"error": f"Download failed: {str(e)}"}

    # 2. 프레임 추출 및 분석
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Could not open video file"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    
    interval_frames = int(fps * 10) # 10초
    results = []
    frame_idx = 0
    step_count = 0 
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % interval_frames == 0:
            # 프레임 저장
            # 파일명에 타임스탬프 사용
            seconds = step_count * 10
            frame_filename = f"frame_{seconds}s.jpg"
            frame_path = os.path.join(upload_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            
            # 분석
            analysis = analyze_image(frame_path)
            
            # 시간 정보 추가
            analysis['time_seconds'] = seconds
            analysis['time_str'] = f"{seconds//60:02d}:{seconds%60:02d}"
            
            results.append(analysis)
            step_count += 1
            
        frame_idx += 1
        
    cap.release()
    return results

def analyze_image(image_path):
    """
    이미지를 분석하여 평균 밝기(Value)와 채도(Saturation)를 추출합니다.
    'brightness'와 'saturation' 메트릭이 포함된 딕셔너리를 반환합니다.
    """
    if not os.path.exists(image_path):
        return {"error": "File not found"}

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return {"error": "Could not decode image"}

    try:
        # BGR (OpenCV 기본)을 HSV로 변환
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 채널 분리: 색상(Hue), 채도(Saturation), 명도(Value)
        h, s, v = cv2.split(hsv_img)
        
        # 평균 계산 (0-255 범위) -> 0-1 정규화
        
        # 채도: Otsu 임계값 + 가중 평균
        # 1. Otsu 임계값법을 적용하여 전경/배경의 최적 임계값 찾기
        # Otsu를 위해 효과적으로 그레이스케일로 변환 (S 채널은 단일 채널)
        # THRESH_OTSU는 첫 번째 반환 값으로 최적 임계값을 반환
        otsu_val, _ = cv2.threshold(s, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 2. 전경 픽셀 추출 (Otsu 임계값보다 큰)
        foreground_mask = s > otsu_val
        foreground_pixels = s[foreground_mask]
        
        if len(foreground_pixels) > 0:
            # 3. 전경에 대한 가중 평균: Sum(p^2) / Sum(p)
            # 높은 채도 값에 더 많은 가중치 부여
            # 오버플로우 방지를 위해 float로 변환
            fg_float = foreground_pixels.astype(float)
            weighted_avg = np.sum(np.square(fg_float)) / np.sum(fg_float)
            avg_saturation = (weighted_avg / 255.0) * 100.0
        else:
            # 이미지가 완전히 균일하거나 흑백인 경우 대체
            avg_saturation = 0.0

        # 밝기: 전체 평균 (기존 로직 유지) -> 0-100 범위
        avg_brightness = (float(np.mean(v)) / 255.0) * 100.0

        # --- 새로운 지표 ---
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. 대비 (동적 범위): 99분위수와 1분위수의 차이
        # 범위: 0-100 (0에서 255의 차이를 스케일링)
        p99 = np.percentile(gray, 99)
        p1 = np.percentile(gray, 1)
        contrast = ((p99 - p1) / 255.0) * 100.0
        
        # 2. 색상 균형 (RGB 왜곡): R, G, B 채널 평균의 표준 편차
        # 범위: 0-100 (경험적 정규화)
        # 표준 편차가 크면 색상이 왜곡됨(불균형). 낮으면 균형 잡힘(회색/흰색).
        # "균형"을 균일함(낮은 표준 편차)으로 볼지 "생동감"(높음)으로 볼지. 
        # 사용자는 "RGB 왜곡"으로 정의했으므로, 점수가 높을수록 더 왜곡/다채로움, 낮으면 흑백에 가까움.
        # [0, 0, 255]에 대한 최대 이론적 표준 편차는 약 120. 분모로 128 사용.
        b_ch, g_ch, r_ch = cv2.split(img)
        mean_rgb = [np.mean(r_ch), np.mean(g_ch), np.mean(b_ch)]
        rgb_skew = np.std(mean_rgb)
        color_balance = min(100.0, (rgb_skew / 128.0) * 100.0)
        
        # 3. 선명도: 라플라시안 분산
        # 범위: 0-100 (경험적, 분산 > 500이면 보통 선명함)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(100.0, (laplacian_var / 500.0) * 100.0)
        
        # 4. 엔트로피: 히스토그램 엔트로피
        # 범위: 0-100 (8비트 이미지의 최대 엔트로피는 8비트)
        hist, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
        hist = hist[hist > 0] # 로그 계산을 위해 0 확률 제거
        entropy_val = -np.sum(hist * np.log2(hist))
        entropy_score = min(100.0, (entropy_val / 8.0) * 100.0)

        # 시각화 이미지 생성 (흑백 맵)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        upload_dir = os.path.dirname(image_path)
        
        # 1. 채도 맵 (S 채널)
        sat_map_filename = f"{base_name}_sat.jpg"
        cv2.imwrite(os.path.join(upload_dir, sat_map_filename), s)
        
        # 2. 밝기 맵 (V 채널)
        val_map_filename = f"{base_name}_val.jpg"
        cv2.imwrite(os.path.join(upload_dir, val_map_filename), v)

        # 3. 대비 맵 (그레이스케일)
        contrast_map_filename = f"{base_name}_contrast.jpg"
        cv2.imwrite(os.path.join(upload_dir, contrast_map_filename), gray)

        # 4. 색상 균형 맵 (크로마: Max(RGB) - Min(RGB))
        # 밝기에 상관없이 색상이 가장 강렬한(순수한) 부분을 보여줌
        # 3개 채널에 걸쳐 최대값과 최소값 계산
        b_float = b_ch.astype(float)
        g_float = g_ch.astype(float)
        r_float = r_ch.astype(float)
        chroma = np.maximum(np.maximum(r_float, g_float), b_float) - np.minimum(np.minimum(r_float, g_float), b_float)
        chroma_map = chroma.astype(np.uint8)
        color_map_filename = f"{base_name}_color.jpg"
        cv2.imwrite(os.path.join(upload_dir, color_map_filename), chroma_map)

        # 5. 선명도 맵 (라플라시안 엣지)
        # absdiff를 사용하여 검은 배경에 흰색으로 엣지 표시
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_abs = cv2.convertScaleAbs(laplacian)
        # 엣지 가시성 강화
        sharpness_map_filename = f"{base_name}_sharpness.jpg"
        cv2.imwrite(os.path.join(upload_dir, sharpness_map_filename), laplacian_abs)

        # 6. 엔트로피 맵 (대리자로 그라디언트 크기 사용)
        # 실제 지역 엔트로피는 느림. 복잡도의 시각적 대리자로 그라디언트 크기(Sobel)를 사용.
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = cv2.magnitude(sobelx, sobely)
        entropy_map = cv2.convertScaleAbs(gradient_magnitude)
        entropy_map_filename = f"{base_name}_entropy.jpg"
        cv2.imwrite(os.path.join(upload_dir, entropy_map_filename), entropy_map)
        
        return {
            "brightness": round(avg_brightness, 2),
            "saturation": round(avg_saturation, 2),
            "contrast": round(contrast, 2),
            "color_balance": round(color_balance, 2),
            "sharpness": round(sharpness, 2),
            "entropy": round(entropy_score, 2),
            "brightness_map": val_map_filename,
            "saturation_map": sat_map_filename,
            "contrast_map": contrast_map_filename,
            "color_map": color_map_filename,
            "sharpness_map": sharpness_map_filename,
            "entropy_map": entropy_map_filename,
            "original_image": os.path.basename(image_path)
        }
    except Exception as e:
        return {"error": str(e)}
