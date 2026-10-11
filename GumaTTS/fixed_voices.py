"""Immutable synthetic references; no user-supplied path or remote audio."""
import hashlib
import json
from pathlib import Path

CLONE_MODEL = 'qwen-clone-1.7b'
CLONE_REPO = 'Qwen/Qwen3-TTS-12Hz-1.7B-Base'
STORY_VOICE = 'M5-fixed-v1'
FOOD_VOICE = 'F1-bright-v2'
REGISTERED_VOICES = frozenset({'F1-fixed-v1', 'F4-dates-v1', FOOD_VOICE, STORY_VOICE})


def reference(root, voice):
    if voice not in REGISTERED_VOICES:
        raise ValueError('등록되지 않은 고정 화자입니다.')
    folder = Path(root) / 'fixed-voices' / voice
    manifest = json.loads((folder/'reference.json').read_text(encoding='utf-8'))
    wav = folder/'reference.wav'
    digest = hashlib.sha256(wav.read_bytes()).hexdigest()
    if digest != manifest['sha256'] or not manifest['text'].strip():
        raise ValueError('고정 화자 기준음성 해시/대본 검증 실패')
    return wav, manifest
