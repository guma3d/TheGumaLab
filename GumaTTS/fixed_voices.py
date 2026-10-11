"""Immutable synthetic references; no user-supplied path or remote audio."""
import hashlib
import json
from pathlib import Path

CLONE_MODEL = 'qwen-clone-1.7b'
CLONE_REPO = 'Qwen/Qwen3-TTS-12Hz-1.7B-Base'
FOOD_VOICE = 'F1-fixed-v1'


def reference(root, voice):
    if voice != FOOD_VOICE:
        raise ValueError('등록되지 않은 고정 화자입니다.')
    folder = Path(root) / 'fixed-voices' / voice
    manifest = json.loads((folder/'reference.json').read_text(encoding='utf-8'))
    wav = folder/'reference.wav'
    digest = hashlib.sha256(wav.read_bytes()).hexdigest()
    if digest != manifest['sha256'] or not manifest['text'].strip():
        raise ValueError('고정 화자 기준음성 해시/대본 검증 실패')
    return wav, manifest
