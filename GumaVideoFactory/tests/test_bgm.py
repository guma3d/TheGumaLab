import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import bgm


class MusicTests(unittest.TestCase):
    def test_missing_selection_and_tampered_source_block(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(bgm,'STORAGE_DIR',Path(temp)):
            folder=Path(temp)/'audio/bgm';folder.mkdir(parents=True)
            (folder/'manifest.json').write_text(json.dumps([dict(title='Test',filename='test.mp3',
                sha256='wrong',license='CC BY 4.0',attribution='test credit')]),encoding='utf-8-sig')
            with self.assertRaisesRegex(ValueError,'bgm_track'):bgm.select({})
            with self.assertRaisesRegex(ValueError,'없는 곡'):bgm.select({'bgm_track':'Other'})
            (folder/'test.mp3').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'해시'):bgm.select({'bgm_track':'Test'})

    def test_credit_is_added_once(self):
        report=dict(track=dict(attribution='fixture CC BY 4.0 credit'))
        text=bgm.credit('Description',report)
        self.assertEqual(bgm.credit(text,report),text)
        self.assertIn(report['track']['attribution'],text)
