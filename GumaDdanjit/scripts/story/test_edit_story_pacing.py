import array
import unittest
from edit_story_pacing import silence_plan,compressed_time,mapped_time,caption_alignment


class PacingEditTests(unittest.TestCase):
    def test_only_middle_of_confirmed_quiet_is_removed(self):
        rate=1000
        samples=array.array('h',[5000]*500+[0]*1500+[5000]*500)
        sentences=[dict(end=.5,start=0),dict(start=2,end=2.5)]
        edits=silence_plan(samples,rate,sentences)
        self.assertEqual(len(edits),1)
        self.assertAlmostEqual(edits[0]['removed_seconds'],1.05)
        self.assertTrue(all(v==0 for v in samples[round(edits[0]['start']*rate):round(edits[0]['end']*rate)]))

    def test_short_natural_pause_is_retained(self):
        samples=array.array('h',[5000]*500+[0]*300+[5000]*500)
        self.assertEqual(silence_plan(samples,1000,[dict(start=0,end=1.3)]),[])

    def test_edit_and_tempo_map_is_monotonic(self):
        edits=[dict(start=1,end=2)]
        pieces=[dict(input_start=0,input_end=2,output_start=0,output_end=2/1.12),
            dict(input_start=2,input_end=4,output_start=2/1.12,output_end=2/1.12+2)]
        times=[mapped_time(n/100,edits,pieces) for n in range(501)]
        self.assertEqual(times,sorted(times))
        self.assertAlmostEqual(mapped_time(1,edits,pieces),mapped_time(2,edits,pieces))
        self.assertAlmostEqual(compressed_time(5,edits),4)

    def test_captions_can_split_an_asr_word_without_overlap(self):
        cues=[dict(text='승진'),dict(text='의 조건')]
        words=[dict(text='승진의',start=0,end=.6),dict(text='조건',start=.6,end=1)]
        result=caption_alignment(cues,words)
        self.assertAlmostEqual(result[0]['end'],result[1]['start'])
        self.assertEqual(result[0]['coverage'],1)


if __name__=='__main__':unittest.main()
