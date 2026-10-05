import tempfile
import unittest
from pathlib import Path
from PIL import Image
from app.core import quality


class QualityTests(unittest.TestCase):
    def test_audio_cannot_outlast_final_video(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'truncated.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=white:s=1080x1920:r=30:d=0.5','-f','lavfi','-i','sine=frequency=440:duration=1.0','-c:v','libx264','-preset','ultrafast','-c:a','aac',str(path)],check=True)
            with self.assertRaisesRegex(ValueError,'스트림 길이'):quality.inspect_output(path)

    def test_thumbnail_is_not_a_high_resolution_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.jpg'
            Image.new('RGB',(405,350),'white').save(path)
            with self.assertRaises(ValueError):quality.inspect_source(path)
            Image.new('RGB',(1000,1000),'white').save(path)
            self.assertEqual(quality.inspect_source(path)['width'],1000)

    def test_editorial_requires_listening_and_all_axes(self):
        review=dict(scores={k:9 for k in quality.REVIEW_AXES},listened_to_audio=False)
        with self.assertRaises(ValueError):quality.validate_editorial(review)
        review['listened_to_audio']=True
        quality.validate_editorial(review)
        review['scores']['sharpness']=7
        with self.assertRaises(ValueError):quality.validate_editorial(review)
        review['scores']['sharpness']=9
        review['unresolved_issues']=['실물과 다른 제품']
        with self.assertRaises(ValueError):quality.validate_editorial(review)

    def test_preflight_is_not_a_single_passed_flag(self):
        with self.assertRaises(ValueError):quality.validate_preflight({'passed':True})
        quality.validate_preflight({'preflight':{k:True for k in quality.PREFLIGHT_AXES}})

    def test_black_letterbox_is_rejected_even_in_1080_output(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=white:s=1080x608:r=30','-f','lavfi','-i','sine=frequency=440','-t','0.5','-vf','pad=1080:1920:0:656:black','-c:v','libx264','-preset','ultrafast','-c:a','aac',str(path)],check=True)
            with self.assertRaisesRegex(ValueError,'검은 여백'):quality.inspect_output(path)
