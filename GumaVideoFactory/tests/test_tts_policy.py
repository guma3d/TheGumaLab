import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from app.core import tts_engine

class VoicePolicyTests(unittest.TestCase):
    def test_gateway_sends_approved_profiles_without_cloud(self):
        for project, voice in [('story','M5'),('longform','M5'),('story_shorts','F4'),('food','F4')]:
            synth=Mock()
            with patch.object(tts_engine.importlib.util,'module_from_spec',return_value=SimpleNamespace(synthesize=synth)), patch.object(tts_engine.importlib.util,'spec_from_file_location',return_value=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda m:None))):
                tts_engine._gateway('같은 원고',Path('voice.mp3'),voice,project=project)
            args=synth.call_args.kwargs
            self.assertEqual((args['model'],args['voice'],args['style'],args['allow_cloud']),('qwen-design-1.7b',voice,'',False))
    def test_gateway_rejects_cross_format_and_old_voice(self):
        for project,voice in [('story','F4'),('food','M5'),('video','Zephyr')]:
            with self.assertRaises(ValueError):tts_engine._gateway('원고',Path('voice.mp3'),voice,project=project)
