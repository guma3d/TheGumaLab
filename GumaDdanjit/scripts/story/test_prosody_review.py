"""Guard against measuring silence or printed numerals as stretched vowels."""
import unittest
import tempfile
import json
from pathlib import Path
from prosody_review import evaluate, production_summary

CALIBRATION = dict(long_word_threshold=.32, minimum_word_active_seconds=.40,
    local_ratio_threshold=2, internal_pause_threshold_seconds=.70)


def word(text, count, activity, start=0, end=1):
    return dict(text=text, syllables=count, active_seconds=activity,
        active_seconds_per_syllable=activity/count, probability=.99, start=start, end=end)


def row(words, pauses=None):
    return dict(index=10, job_id='fixture', audio_sha256='fixture', words=words,
        pauses=pauses or [], active_syllables_per_second=5)


class ProsodyReviewTests(unittest.TestCase):
    def test_reported_cut_word_is_detected_without_sentence_average(self):
        # Measured original cut 010: the short word is buried in a normal-rate cut.
        r = evaluate(row([word('오늘은',3,.53),word('이',1,.59),word('차이를',3,.48),
            word('따라가',3,.40),word('보겠습니다',5,.62)]), CALIBRATION)
        self.assertTrue(any(f.get('text')=='이' for f in r['findings']))
        self.assertFalse(r['naturalness_passed'])

    def test_long_asr_span_with_silence_is_not_vowel_elongation(self):
        r = evaluate(row([word('오늘은',3,.48),word('이',1,.12,start=.6,end=1.4),
            word('차이를',3,.48)], [dict(start=.72,end=1.44,seconds=.72,internal=True)]), CALIBRATION)
        self.assertFalse(r['elongation_candidate'])
        self.assertTrue(any(f['type']=='long_pause_candidate' for f in r['findings']))

    def test_digits_are_not_counted_as_one_spoken_syllable(self):
        r = evaluate(row([word('조사는',3,.48),word('2026년',1,.97),word('결과를',3,.48)]), CALIBRATION)
        self.assertFalse(r['elongation_candidate'])

    def test_no_flag_is_not_a_listening_pass(self):
        r = evaluate(row([word('오늘은',3,.48),word('차이를',3,.48)]), CALIBRATION)
        self.assertEqual(r['status'],'no_timing_candidate')
        self.assertFalse(r['naturalness_passed'])
        self.assertFalse(r['human_listening_completed'])

    def test_missing_report_and_stale_audio_never_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertEqual(production_summary(root)['status'],'not_run')
            (root/'voice-manifest.json').write_text(json.dumps([dict(index=10,audio_sha256='new')]))
            (root/'prosody-review.json').write_text(json.dumps(dict(cuts=[dict(index=10,audio_sha256='old')])))
            with self.assertRaises(ValueError):
                production_summary(root)
            (root/'audio-release.json').write_text(json.dumps(dict(voice_manifest_sha256='stale')))
            with self.assertRaisesRegex(ValueError,'Audio release belongs'):
                production_summary(root)


if __name__=='__main__':
    unittest.main()
