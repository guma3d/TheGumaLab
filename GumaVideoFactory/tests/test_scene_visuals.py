import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import versions as store, studio_jobs as jobs
from app.core.scene_visuals import validate_tech_visuals


class SceneVisualTests(unittest.TestCase):
    def test_secondary_thermal_feature_cannot_use_unrelated_exterior(self):
        scenes=[dict(visual_mode='approved_model',visual_subject='제품',narration_ko='제품') for _ in range(6)]
        scenes[3].update(narration_ko='베이퍼 챔버가 칩의 열을 퍼뜨립니다.')
        with self.assertRaises(ValueError):validate_tech_visuals(scenes)
        scenes[3].update(visual_mode='mechanism_concept',visual_prompt='Vapor chamber evaporation and condensation cross-section')
        validate_tech_visuals(scenes)

    def test_legacy_tech_revision_cannot_call_paid_preview(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(store,'ROOT',Path(temp)),patch.object(store,'STORAGE_DIR',Path(temp)):
            idea=store.create(dict(category='tech',subject='Test cooler',hook='cool'),'2026-10-02');iid=idea['id']
            store.reserve(iid,'3DModel');store.update(iid,'3DModel',1,status='ready',approved_at='approved')
            store.reserve(iid,'Preview',model_version=1)
            parent=store.version_dir(iid,'Preview',1)
            scenes=[dict(scene_number=i,visual_mode='approved_model',visual_subject='제품',purpose='설명',narration_ko='제품',visual_prompt='product') for i in range(1,7)]
            for i in range(1,7):(parent/f'scene_{i:02d}.png').write_bytes(f'original-{i}'.encode())
            original=copy.deepcopy(scenes)
            store.update(iid,'Preview',1,status='ready',storyboard=dict(scenes=scenes))
            edits={'4':dict(visual_mode='mechanism_concept',visual_subject='베이퍼 챔버',narration_ko='베이퍼 챔버의 열 확산',visual_prompt='Vapor chamber evaporation and condensation')}
            store.reserve(iid,'Preview',True,model_version=1,parent_preview_version=1,scene_revisions=edits)
            def image(prompt,path,*args,**kwargs):path.write_bytes(b'new-concept')
            refs=[dict(file='reference.png',scope='exact_visible',page_url='https://example.com',limitation='')]
            with patch.object(jobs,'review_feature_image',return_value=dict(passed=True)),patch.object(jobs,'resolve_feature_references',return_value=refs),patch.object(jobs,'generate_preview_image',side_effect=image) as generate,patch.object(jobs.blender,'still') as render,patch.object(jobs,'plan_video_storyboard') as plan:
                with self.assertRaises(ValueError):jobs.preview_job(iid,2)
            generate.assert_not_called();render.assert_not_called();plan.assert_not_called()
            self.assertEqual(store.get(iid,'Preview',1)['storyboard']['scenes'],original)
