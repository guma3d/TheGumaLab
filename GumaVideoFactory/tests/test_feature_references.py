import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core.feature_references import resolve_feature_references, motion_prompt, review_feature_image, apply_reference_policy


class FeatureReferenceTests(unittest.TestCase):
    def test_unknown_geometry_uses_principles_for_other_products_too(self):
        for subject in ('로봇청소기 스팀 유로','헤드폰 소음 제거','카메라 안정화'):
            scene=dict(visual_subject=subject,narration_ko='검증한 작동 원리',visual_prompt='feature',reference_presentation='display')
            apply_reference_policy(scene,[dict(scope='related_context')])
            self.assertEqual(scene['reference_fidelity'],'principle_only')
            self.assertIsNone(scene['reference_presentation'])
            self.assertIn('실제 형상 미확보',scene['reference_limitation'])
            self.assertIn('No invented exact component',scene['visual_prompt'])

    def test_documented_surface_is_not_replaced_by_context_photo(self):
        scene=dict(visual_prompt='documented lens',reference_presentation='display')
        apply_reference_policy(scene,[dict(scope='related_context'),dict(scope='exact_visible')])
        self.assertEqual(scene['reference_fidelity'],'documented_surface')
        self.assertEqual(scene['visual_prompt'],'documented lens')

    def test_missing_reference_stops_unfounded_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'임의 형상'):
                resolve_feature_references('other product',dict(visual_subject='냉각 구조'),Path(temp),[])

    def test_invented_image_url_is_rejected_before_download(self):
        with tempfile.TemporaryDirectory() as temp,patch('app.core.feature_references.fetch',return_value=b'<html>no asset</html>') as fetch:
            with self.assertRaisesRegex(ValueError,'원문'):
                resolve_feature_references('test',dict(scene_number=1),Path(temp),[
                    dict(page_url='https://maker.example/product',url='https://maker.example/fake.png',scope='exact_visible')])
            fetch.assert_called_once()

    def test_video_receives_camera_orbit_and_fidelity_constraints(self):
        prompt=motion_prompt(dict(visual_prompt='Lens',camera_movement='Orbit 30 to 100 degrees'))
        self.assertIn('Orbit 30 to 100 degrees',prompt)
        self.assertIn('parallax',prompt)
        self.assertIn('undocumented',prompt)

    def test_generic_pass_cannot_bypass_exterior_fidelity_check(self):
        with tempfile.TemporaryDirectory() as temp,patch('app.core.feature_references.genai.Client') as client:
            folder=Path(temp);path=folder/'scene.png';path.write_bytes(b'fake')
            client.return_value.__enter__.return_value.models.generate_content.return_value.text='{"passed":true,"reason":"ok"}'
            with self.assertRaisesRegex(ValueError,'검토 실패'):
                review_feature_image(dict(scene_number=1),path,[],folder)
