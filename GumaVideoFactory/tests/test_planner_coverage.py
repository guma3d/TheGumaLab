import json,unittest
from unittest.mock import patch,MagicMock
from app.core import planner
class PlannerCoverageTests(unittest.TestCase):
 def test_verified_secondary_features_cannot_be_omitted(self):
  scenes=[dict(scene_number=n,camera_movement='slow',visual_prompt='product',narration_ko='설명',covered_features=[]) for n in range(1,7)]
  board=dict(title='product',summary='intro',estimated_total_seconds=24,scenes=scenes)
  client=MagicMock();client.models.generate_content.return_value.text=json.dumps(board)
  evidence=json.dumps(dict(supporting_features=['Feature B','Feature C']))
  with patch.object(planner,'GEMINI_API_KEY','test'),patch.object(planner.genai,'Client',return_value=client):
   with self.assertRaisesRegex(ValueError,'누락'):planner.plan_video_storyboard('test',evidence=evidence)
   scenes[3]['covered_features']=['Feature B','Feature C'];client.models.generate_content.return_value.text=json.dumps(board)
   result=planner.plan_video_storyboard('test',evidence=evidence)
   self.assertEqual(result.scenes[3].purpose,'supporting_features')
   prompt=client.models.generate_content.call_args.kwargs['contents']
   self.assertIn('2-3 other important',prompt)
