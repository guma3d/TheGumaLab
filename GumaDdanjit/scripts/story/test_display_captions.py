import unittest
from display_captions import display_text, assert_display_numbers

class DisplayCaptionTests(unittest.TestCase):
    def test_overlapping_numbers_and_units(self):
        self.assertEqual(display_text('육 퍼센트, 칠십육 퍼센트, 사십삼 점 육 퍼센트. 사백사십만 원, 이만 오천 원.'),'6%, 76%, 43.6%. 440만 원, 25,000원.')
    def test_dates_sample_and_no_unintended_word_replacement(self):
        self.assertEqual(display_text('이천이십삼년 천백십사 명, 충분한 시간과 한 시간.'),'2023년 1,114명, 충분한 시간과 1시간.')
        assert_display_numbers('충분한 시간과 몇 퍼센트인지 모릅니다.')
    def test_spoken_source_does_not_mutate(self):
        text='사백만 원과 백육십 시간'
        self.assertEqual(display_text(text),'400만 원과 160시간')
        self.assertEqual(text,'사백만 원과 백육십 시간')
        with self.assertRaises(ValueError):assert_display_numbers(text)

if __name__=='__main__':unittest.main()
