import copy
import unittest
from app.core.quality import validate_living_actions


class LivingActionTests(unittest.TestCase):
    def fixture(self):
        board={'scenes':[{'mode':'acquired_clip','duration_seconds':4.5},{'mode':'official_image','duration_seconds':3}]}
        review={'living_actions':[
            dict(number=1,kind='action',notes='동일 모델의 실제 상부 급수 전 구간을 확인함',action_visible=True,model_match=True,playback_reviewed=True,continuous_motion=True,source_start_seconds=10,source_end_seconds=15,motion_seconds=4.5,original_short_edge=720,enlargement=1.5,original_sha256='a'*64,source_url='https://example.com/source',observed_action='피처에서 급수 공간으로 물을 붓는 실제 동작'),
            dict(number=2,kind='static_information',narrates_action=False,notes='고정 사진으로 제품의 외형과 색상만 설명함')]}
        return board,review

    def test_real_action_and_static_design_can_coexist(self):
        validate_living_actions(*self.fixture())

    def test_short_demo_cannot_be_filled_with_a_product_photo(self):
        board,review=self.fixture();review['living_actions'][0]['motion_seconds']=1.8
        with self.assertRaisesRegex(ValueError,'동작 길이'):validate_living_actions(board,review)

    def test_image_or_generated_illustration_cannot_prove_function(self):
        board,review=self.fixture()
        for mode in ['official_image','illustration_clip','veo']:
            board['scenes'][0]['mode']=mode
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'실제 동작'):validate_living_actions(board,review)

    def test_actual_speech_length_is_checked_after_tts(self):
        board,review=self.fixture()
        with self.assertRaisesRegex(ValueError,'동작 길이'):validate_living_actions(board,review,[6,3])

    def test_official_label_requires_original_publisher(self):
        board,review=self.fixture();board['scenes'][0]['mode']='official_clip'
        with self.assertRaisesRegex(ValueError,'발행자'):validate_living_actions(board,review)
        review['living_actions'][0]['official_publisher_verified']=True
        validate_living_actions(board,review)

    def test_missing_motion_review_or_all_stills_is_rejected(self):
        board,review=self.fixture()
        with self.assertRaises(ValueError):validate_living_actions(board,{'passed':True})
        review['living_actions'][0]=dict(number=1,kind='context',narrates_action=False,notes='영상 전체를 정지 이미지로만 구성한 경우')
        with self.assertRaisesRegex(ValueError,'실제 동작'):validate_living_actions(board,review)

    def test_invalid_original_dimensions_or_range_is_rejected(self):
        board,review=self.fixture()
        for changes in [dict(original_short_edge=480),dict(enlargement=2),dict(source_end_seconds=11),dict(motion_seconds=float('nan')),dict(continuous_motion=False)]:
            altered=copy.deepcopy(review);altered['living_actions'][0].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):validate_living_actions(board,altered)

    def test_still_classification_cannot_admit_narrated_action(self):
        board,review=self.fixture();review['living_actions'][1]['narrates_action']=True
        with self.assertRaisesRegex(ValueError,'정지 이미지'):validate_living_actions(board,review)
