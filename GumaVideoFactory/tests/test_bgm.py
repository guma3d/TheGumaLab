import json
import hashlib
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import bgm


class MusicTests(unittest.TestCase):
    def test_missing_selection_and_tampered_source_block(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(bgm,'STORAGE_DIR',Path(temp)):
            folder=Path(temp)/'audio/bgm';folder.mkdir(parents=True)
            (folder/'manifest.json').write_text(json.dumps([dict(title='Life of Riley',filename='test.mp3',
                sha256='wrong',license='CC BY 4.0',attribution='test credit')]),encoding='utf-8-sig')
            with self.assertRaisesRegex(ValueError,'원본'):bgm.select({'bgm_track':'Life of Riley'})
            with self.assertRaisesRegex(ValueError,'없는 곡'):bgm.select({'bgm_track':'Other'})
            (folder/'test.mp3').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'해시'):bgm.select({'bgm_track':'Life of Riley'})

    def test_random_selection_is_persisted_and_retries_keep_it(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(bgm,'STORAGE_DIR',Path(temp)), patch.object(bgm.secrets,'choice',return_value='Carefree') as choice:
            folder=Path(temp)/'audio/bgm';folder.mkdir(parents=True)
            source=folder/'fixture.wav';source.write_bytes(b'fixture')
            manifest=[dict(title=title,filename=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),license='CC BY 4.0',attribution='fixture credit') for title in bgm.TRACK_TITLES]
            (folder/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            board={};bgm.select(board);bgm.select(board)
            self.assertEqual(board['bgm_track'],'Carefree')
            choice.assert_called_once_with(bgm.TRACK_TITLES)

    def test_actual_music_level_is_constant_during_speech_and_silence(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);music=p/'music.wav';source=p/'source.mp4';out=p/'out.mp4'
            ff=bgm.media.get_ffmpeg_bin()
            bgm.media.run([ff,'-v','error','-f','lavfi','-i','sine=frequency=440:duration=6','-ar','48000','-ac','2',str(music)])
            bgm.media.run([ff,'-v','error','-f','lavfi','-i','color=s=64x96:r=30:d=6','-f','lavfi','-i','sine=frequency=997:duration=6',
                '-af',"volume=if(between(t\\,2\\,4)\\,0\\,1):eval=frame",'-c:v','libx264','-c:a','aac','-ar','48000','-ac','2',str(source)])
            with patch.object(bgm,'select',return_value=(music,dict(title='fixture'))):
                report=bgm.mix(source,out,{'bgm_track':'fixture'})
            def band_rms(start):
                r=subprocess.run([ff,'-hide_banner','-ss',str(start),'-i',str(out),'-t','1','-vn','-af',
                    'bandpass=f=440:w=10,astats=metadata=0:reset=0','-f','null','-'],capture_output=True,text=True,check=True)
                return float(re.findall(r'RMS level dB: ([-\d.]+)',r.stderr)[-1])
            self.assertAlmostEqual(band_rms(.7),band_rms(2.7),delta=.25)
            self.assertAlmostEqual(report['music_measurement']['integrated_lufs'],-25,delta=.3)
            self.assertFalse(report['ducking'])
            self.assertTrue(report['video_stream_unchanged'])
            self.assertLess(report['final_measurement']['true_peak_dbfs'],0)

    def test_credit_is_added_once(self):
        report=dict(track=dict(license='CC BY 4.0',attribution='fixture CC BY 4.0 credit'))
        text=bgm.credit('Description',report)
        self.assertEqual(bgm.credit(text,report),text)
        self.assertIn(report['track']['attribution'],text)
