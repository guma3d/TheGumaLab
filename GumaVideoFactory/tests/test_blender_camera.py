import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from app.core import blender_runner as blender


class CameraExecutionTests(unittest.TestCase):
    def test_macro_target_and_orbit_reach_actual_blender_video(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(blender,'run_blender') as run,patch.object(blender.subprocess,'run',return_value=Mock(returncode=0)):
            blender.clip(Path(temp)/'model.blend',Path(temp)/'clip.mp4',25,4,
                camera_settings=dict(distance=1.8,elevation=.25,target=[-.15,0,.65],end_angle=70))
            args=run.call_args.args
            self.assertEqual(args[args.index('--end-angle')+1],70)
            self.assertEqual(args[args.index('--distance')+1],1.8)
            self.assertEqual(args[args.index('--target')+1:args.index('--target')+4],(-.15,0,.65))
            self.assertEqual(args[args.index('--width')+1],1080)
