# Story 발화 속도 검수

2026-10-12: Sohee 시험 v1의 10번 컷에 대한 사용자 피드백을 회귀 사례로 사용한다. 음량·대사 일치 검수와 발화 리듬 검수는 별개다. 실제 청취를 수행하지 않은 결과를 자연스러움 통과로 표시하지 않는다.

## 실행

`scripts/story/prosody_review.py`를 로컬 GumaTTS 컨테이너의 storage/diagnostics 작업 폴더로 복사해 실행한다. faster-whisper turbo의 로컬 캐시가 필요하며 CPU int8로 실행한다. 음성 생성 모델은 변경하지 않는다.

```text
python prosody_review.py manifest.json words
python prosody_review.py manifest.json words --analyze --exclude 10
```

manifest는 선택된 컷별 index, text, tts_job_id, audio_sha256을 포함한다. MP3 해시를 대조하고 ASR 어절 시작/끝을 기록한다. 원본 WAV의 10ms RMS 활동으로 어절 구간에 포함된 무음을 분리한다. 절대 -48dBFS와 최대 RMS 대비 -35dB 중 높은 문턱을 사용한다. 순수 모음 길이나 음소 강제 정렬을 의미하지 않으며, 활동 시간은 후보 탐지용 근사치다.

기준은 문제 컷을 제외한 다른 컷의 신뢰도 높은 한글 어절에서 계산한다. 이 컷들도 사람이 승인한 정상 샘플은 아니므로 검출 정확도·오탐률을 입증한 평가 세트라고 주장하지 않는다. 숫자/영문/%를 포함한 어절은 한글 문자 수로 발화 속도를 계산하지 않는다. 숫자가 포함된 컷의 전체 음절 속도는 미계산으로 표시한다.

검토 후보:

- 긴 어절: 활동 시간/음절이 `max(0.32초, peer median + 3 × 1.4826 × MAD)`를 넘고, 해당 컷 중앙값의 2배 초과이며 어절 활동 0.40초 이상.
- 컷 내부 속도 변화: 최소 8음절인 다어절 구간끼리 활동 시간/음절의 최대/최소 비율이 2배 초과.
- 긴 쉼: 컷 내부 파형 무음이 0.70초 초과. 문장 경계·강조에 따른 정상 쉼일 수 있어 오류나 자동 삭제 대상으로 간주하지 않는다.

결과는 `needs_review` 또는 `no_timing_candidate`다. 모두 `naturalness_passed=false`, `human_listening_completed=false`를 유지한다. 무검출은 자연스러움을 보증하지 않는다. 정렬 실패·해시 불일치는 통과시키지 않는다.

## 제작 연결과 수정

`review_longform.py`와 `review_promotion_v3.py`는 `production_summary()`를 통해 prosody-review.json을 검수 기록에 포함한다. 보고서가 없으면 not_run이고, 컷 누락이나 음성 해시 불일치는 실패한다. 이전 파일을 덮어쓰지 않으며 새 버전에서 실패 컷만 재생성한다. 새 테이크는 기준을 다시 학습하지 않고 동결된 원본 기준으로 비교한다.

`retake_sohee_cut.py`는 원본 대본을 보존한 10번 컷의 비교 테이크를 GumaTTS project=test로 생성한다. 속도/피치를 후처리로 바꾸지 않는다. 모든 테이크의 원본·정렬·해시·작업 ID·선택 사유를 남긴다. 재생성 결과가 자동 후보를 해소했어도 실제 청취 완료나 기본 Sohee 채택으로 기록하지 않는다.
