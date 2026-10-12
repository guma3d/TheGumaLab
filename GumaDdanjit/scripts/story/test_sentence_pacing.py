import unittest
import json
import tempfile
from pathlib import Path
from prosody_review import sentence_screen_summary
from sentence_pacing import sentence_units, evaluate_sentence, calibrate_sentences, matched_word_indices

CAL=dict(minimum_syllables=8,active_median=.15,active_threshold=.195,
    elapsed_median=.17,elapsed_threshold=.23,pause_fraction_threshold=.25,
    minimum_quiet_seconds=.60,long_pause_seconds=.70)


class SentencePacingTests(unittest.TestCase):
    def test_asr_hallucination_is_not_a_fast_pace_reference(self):
        words=[dict(text='고객이',start=0,end=.5),dict(text='원하지',start=.5,end=1),
            dict(text='않습니다.',start=1,end=1.5),dict(text='감사합니다.',start=1.5,end=1.7)]
        units=sentence_units('고객이 원하지 않습니다.',words,[True]*170)
        self.assertEqual(matched_word_indices(units),[0,1,2])
    def test_numeric_asr_uses_spoken_syllables(self):
        words=[dict(text='2026년',start=0,end=1),dict(text='조사입니다.',start=1,end=2)]
        unit=sentence_units('이천이십육년 조사입니다.',words,[True]*200)[0]
        self.assertEqual(unit['status'],'aligned')
        self.assertEqual(unit['syllables'],11) # 이천이십육년(6) + 조사입니다(5)

    def test_sentence_lead_in_does_not_become_a_long_vowel(self):
        words=[dict(text='오늘은',start=0,end=.6),dict(text='살펴봅니다.',start=.6,end=1.4),
            dict(text='이제',start=2.8,end=3.2),dict(text='이유를',start=3.2,end=3.8),
            dict(text='알아봅니다.',start=3.8,end=4.8)]
        activity=[True]*140+[False]*140+[True]*200
        units=sentence_units('오늘은 살펴봅니다. 이제 이유를 알아봅니다.',words,activity)
        self.assertAlmostEqual(units[1]['preceding_pause_seconds'],1.4)
        self.assertAlmostEqual(units[1]['active_seconds'],2)
        self.assertAlmostEqual(units[1]['elapsed_seconds'],2)
        result=evaluate_sentence(units[1],CAL)
        self.assertTrue(any(f['type']=='long_preceding_sentence_pause' for f in result['findings']))

    def test_uniformly_slow_sentence_cannot_hide_in_local_word_median(self):
        unit=dict(status='aligned',syllables=15,active_seconds_per_syllable=.21,
            elapsed_seconds_per_syllable=.21,pause_fraction=0,quiet_seconds=0,preceding_pause_seconds=0)
        result=evaluate_sentence(unit,CAL)
        self.assertTrue(any(f['type']=='slow_sentence_active' for f in result['findings']))
        self.assertFalse(result['naturalness_passed'])

    def test_subthreshold_pause_can_be_detected_as_sentence_density(self):
        unit=dict(status='aligned',syllables=15,active_seconds_per_syllable=.19,
            elapsed_seconds_per_syllable=.27,pause_fraction=.296,quiet_seconds=1.2,preceding_pause_seconds=0)
        result=evaluate_sentence(unit,CAL)
        self.assertTrue(any(f['type']=='high_sentence_pause_fraction' for f in result['findings']))

    def test_misaligned_and_literal_digits_are_not_timing_passes(self):
        unit=sentence_units('2026년 조사입니다.',[dict(text='2026년',start=0,end=1)], [True]*100)[0]
        self.assertEqual(unit['status'],'alignment_review_required')
        self.assertFalse(evaluate_sentence(unit,CAL)['naturalness_passed'])

    def test_reported_cuts_are_excluded_from_calibration(self):
        rows=[dict(index=i,sentences=[dict(status='aligned',syllables=10,
            active_seconds_per_syllable=.15 if i not in (6,10) else 3,
            elapsed_seconds_per_syllable=.18 if i not in (6,10) else 4)]) for i in range(1,21)]
        result=calibrate_sentences(rows)
        self.assertEqual(result['baseline_sentences'],18)
        self.assertEqual(result['active_median'],.15)

    def test_stale_final_video_cannot_reuse_sentence_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertEqual(sentence_screen_summary(root)['status'],'not_run')
            (root/'final.mp4').write_bytes(b'changed video')
            (root/'sentence-prosody-review.json').write_text(json.dumps(dict(source=dict(video_sha256='stale'))))
            with self.assertRaisesRegex(ValueError,'another final video'):
                sentence_screen_summary(root)


if __name__=='__main__':unittest.main()
