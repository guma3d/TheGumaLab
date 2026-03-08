# YoutubeToDoc - 상세 기술 및 작동 방식 가이드 (Tech Spec & Workflow)

이 문서는 YoutubeToDoc이 어떤 시스템이며, 어떻게 작동하는지 개발자 시각에서 매우 상세하게 설명하는 기술 명세서입니다. 새로운 유지 보수 담당자나 프로그래머가 보았을 때 시스템 전체 아키텍처와 흐름을 단번에 이해할 수 있도록 설계되었습니다.

---

## 🚀 1. 시스템 개요 (Overview)
**YoutubeToDoc**은 사용자가 입력한 하나의 YouTube URL 링크를 입력값으로 받아, 해당 영상의 오디오를 텍스트로 추출(STT)해 번역하고, 중요한 프레임(화면)만 선별적으로 추출하여 **"자동 요약 문서(Summary) 및 상세 자막 프레임 리포트(Detail Document)"**를 자동으로 뱉어내는 AI 기반 올인원 서버 애플리케이션입니다.

### 핵심 기술 스택
- **Backend**: Python 3.9+ / Flask 
- **DB (State)**: 로컬 파일 시스템(`data/task_status.json`) - 큐에 들어온 영상의 작업 상태 기록.
- **DB (Vector)**: Qdrant (Docker 배포, `qdrant:6333` 포트 통신) - 영상 내 세부 스크립트를 임베딩하여 문맥 기반 의미(Semantic) 검색 지원.
- **Frontend**: Vanilla HTML / JS (`script.js`). 폴링(Polling) 방식을 통한 백엔드 태스크 모니터링 수행 가능.
- **AI Models**:
  - `faster-whisper`: 로컬 환경에서 구동되는 오디오-투-텍스트(Speech-to-Text) 추출 엔진. 시스템 자원 소모를 방지하기 최적화된 터보(`turbo`) 및 CPU `int8` 연산 모드를 씁니다.
  - `Gemini 3.1 Flash Lite`: 구글 제공 API로 입력받은 자막(Script) 뭉치를 한글로 번역(`translating`)하고, 전체 영상을 요약(`summarize`)하며 영어 4가지 핵심 태그(`tags`)를 생성하는 데 사용.

---

## ⚙️ 2. 작동 흐름 (Step-by-Step Workflow)

웹 UI상에서 YouTube 링크를 입력하여 `[처리 시작]` 버튼을 누르는 순간부터 생성되는 11개의 파이프라인 프로세스입니다.

### 2.1. 사용자 요청 트리거 (Frontend -> `/process`)
1. 사용자가 `<input>`에 유튜브 URL 입력 후 제출.
2. `script.js`가 fetch 비동기 통신으로 `POST /process` 라우트를 찌릅니다.
3. 백엔드는 고유한 `task_id`를 생성하고 상태 저장소(`task_status.json`)에 `"status": "queued"`로 넣은 후 **Task Queue(`queue.Queue`)**에 넣습니다. (동시 처리를 막기 위해 락 `task_lock` 적용).
4. 응답으로 `task_id`를 받은 프론트엔드는 주기적으로 `GET /task/<task_id>`를 호출하여(Polling) 현재 퍼센티지와 로깅 텍스트를 화면 프로그레스 바에 그립니다.

### 2.2. 백그라운드 Worker 스레드 
서버가 켜지면 `threading.Thread(target=task_worker, daemon=True)`에 의해 무한 루프를 도는 단일 워커가 돌아갑니다.
워커는 큐에 들어온 태스크 중 가장 오래된 것을 꺼내 `process_youtube_video()`라는 핵심 함수를 실행합니다.

---

## 🛠️ 3. `process_youtube_video(url, task_id)` 내부 상세 파이프라인

이 과정은 크게 총 11가지의 스텝으로 나뉘어져 로그가 출력됩니다. (진행도 `1/11 ~ 11/11`)

### Step 1: 비디오 다운로드 (`yt-dlp` 사용)
```python
# [1/11] 비디오 다운로드 중...
ydl_opts = {
    'format': 'best', # 1080p 해상도 이하 베스트
    'outtmpl': str(video_dir / f"{safe_title}.%(ext)s"),
    ...
}
```
`yt-dlp` 라이브러리를 통해 영상을 디스크에 다운로드합니다. 이 때 파일명 특수문자들로 인해 오류 발생 방지를 위해 정규식 기반 `safe_title` 변환 과정을 필수로 거칩니다.

### Step 2: 오디오 추출 (`ffmpeg` 사용)
```python
# [2/11] 오디오 추출 중... (ffmpeg)
# 다운받은 영상(mp4)에서 mp3 음성 데이터만을 외부 프로세스로 추출!
subprocess.run(['ffmpeg', '-i', downloaded_file, '-q:a', '0', '-map', 'a', output_audio, '-y'], check=True)
```
추출된 오디오를 이용해 다음 스텝에서 인간 언어를 인식하게 됩니다.

### Step 3: STT 시스템 기반 자막 스크립트화 (`faster-whisper`)
과거 Gemini API 등을 요청했으나 대용량 음원 오디오 파일 거부 문제로, 인하우스 자체 로컬인 **`faster-whisper`** 엔진을 내장했습니다.
```python
# [3/11] STT 자막 생성 중...
model = WhisperModel("turbo", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, beam_size=1) 
# -> 나온 결과물을 SRT(자막) 포맷에 맞게 변환 후 임시저장
```
결과는 `[00:00:10 -> 00:00:15] 안녕하세요` 형태로 저장됩니다.

### Step 4 ~ Step 5: 화면(Frame) 이미지 추출 및 중복 제거(Deduplication)
OpenCV(`cv2`) 모듈을 이용합니다.
위에서 구해진 자막(Segment) 하나하나는 `(시작시간, 종료시간)`을 가집니다.
1. `cv2.VideoCapture`를 돌려 **자막의 중간(Mid) 시점의 1프레임(사진 1장)** 을 로컬 폴더에 이미지로 캡쳐(`cv2.imwrite`)해 저장합니다.
2. 캡쳐된 이미지들을 연속으로 비교하여 `Structural Similarity Index (SSIM)` 또는 `cv2.absdiff()` 차이값을 분석합니다. 
3. 이전에 캡쳐된 화면과 픽셀 차이 비율이 일정 스레시홀드(Threshold, 예: 화면의 3% 미만 변화) 이하라면 시각적으로 거의 동일한 화면을 계속 띄워두고 말만 이어가는 상황(예: 강연 PPT)이므로 **이미지를 버리고 텍스트만 하나로 이어 붙입니다(Merge)**. 결과적으로 불필요한 이미지 장수를 대폭 줄여 문서의 가독성을 높입니다.

### Step 6 ~ Step 8: Gemini API를 통한 번역 (Translation)
병합되고 간소화된 세그먼트 이미지+텍스트 조합들을 **Gemini 3.1 Flash API**에 전달합니다.
```python
# API Rate Limit (429에러)를 피하기 위한 지수 백오프 기반 재시도 코드 
@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=15, min=30, max=120),
    stop=stop_after_attempt(5)
)
def generate_content_with_retry(client, model, contents, system_instruction):
    time.sleep(4.1) # 15 RPM을 지키기위한 안전장치 (1분=60초 제한에 15번)
    return client.models.generate_content(...)
```
해당 부분에서 각 세그먼트의 원문을 한글로 변역한(`translated`) 기록을 Segment 객체에 주입합니다.

### Step 9: 상승하는 디테일 HTML 생성 (`Detail Document`)
모든 이미지가 들어간 세그먼트 루프를 돌며, 테이블 마크다운 테이블 기반의 긴 **상세 HTML(`[Title]-detail.html`)** 문서를 생성합니다. 여기에는 `<iframe>` 또는 비디오 JS 구문이 태깅되어 이미지를 누르면 특정 시간의 영상 프레임으로 바로 점프(Jump)하는 로직이 숨겨져 있습니다.

### Step 10: 영상 총 요약 (Summary) 및 Tag 생성
이번엔 번역된 모든 문자열을 한꺼번에 합쳐 단일 문자열로 만들고, 이를 다시 Gemini API에 던집니다.
목적: 
1. `system_instruction="...전체 맥락을 3단락으로 요약하라..."`를 통해 Summary 단락 생성
2. `system_instruction="Extract 4 key English tags..."`를 통해 영문 4가지 주요 해시태그(Tag)를 추출
생성된 요약문 데이터와 태그를 유튜브 썸네일(`maxresdefault.jpg`) 바로 하단에 에메랄드 그린 컬러로 삽입하여 **요약본 HTML(`[Title]-summary.html`)**을 만들어냅니다.

### Step 11: Qdrant 벡터 데이터베이스(VectorDB) 색인 저장
생성완료된 모든 내용 데이터에 대해 **Embedding (숫자형 벡터화 변환)**을 한 후 밀어넣습니다.
```python
# Qdrant에 저장
qdrant_client.upsert(
    collection_name="video_segments",
    points=[
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding_list, # Google 임베딩 768차원 배열
            payload={
                "task_id": task_id,
                "text": text,
                "type": "detail_segment"
            }
        )
    ]
)
```
이후 사용자가 화면에서 돋보기를 눌러 **Search(검색)** 를 할 경우 이 Qdrant DB를 뒤져 관련성이 높은 텍스트를 빠르게 가져옵니다.

### Final Step: 클린업 및 결과 반환
HTML과 최종 화면에 뿌려질 이미지 파일만 남기고, 수 기가바이트(GB)에 달하는 찌꺼기 `.mp4`, 오디오 파일 `.mp3`을 즉시 영구 삭제(Cleanup)합니다. 이후 폴링하던 프론트엔드에게 `Status = "Completed"` 신호가 떨어져 화면에 "Completed Documents" 갤러리뷰 카드 UI를 출력시킵니다.

---

## 🔒 4. 보안 및 유지보수 특징
- **API 키 은닉**: `.env` 파일에 보관되며 GitHub 저장소에는 절대로 올라가지 않습니다.
- **재시도의 신 (Retry Method)**: 구글 측에서 사용량 급증으로 일시 정지를 먹여도 서버 다운 현상을 막기 위해, 최소 30초 대기 후 자동으로 재시작을 타진합니다. (장시간 꺼둘 필요가 없음)
- **과거 문서 재생성 스크립트**: `regen.py` 를 통해 현재까지 쌓아놓은 로컬 데이터를 전부 스캔해서 최신기능(예: 태그 삽입 등) 기준으로 기존 사용 문서 HTML포맷 전체를 한 번에 덧씌워 파싱 재생성시킬 수 있습니다.
