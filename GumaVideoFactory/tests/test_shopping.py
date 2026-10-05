import asyncio
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app.core import shopping as s, versions as store
from app.core.recommendations import DailyBatch, now_kst
from app.studio import request_publish, StageRequest


class ShoppingTests(unittest.TestCase):
    def test_private_review_does_not_invent_audio_verification(self):
        evidence=dict(voice='Zephyr',user_selected_voice=True,visual_passed=True,
            director_checks={k:True for k in s.quality.DIRECTOR_AXES},
            audio_review='user_review_on_private_youtube',listened_to_audio=False)
        s.quality.validate_private_review(evidence)
        with self.assertRaises(ValueError):
            s.quality.validate_private_review(dict(evidence,listened_to_audio=True))
        evidence['director_checks']['narration_visual_match']=False
        with self.assertRaises(ValueError):s.quality.validate_private_review(evidence)

    def test_food_private_review_uses_version_voice(self):
        evidence=dict(voice='Zephyr',user_selected_voice=True,visual_passed=True,
            director_checks={k:True for k in s.quality.DIRECTOR_AXES},
            audio_review='user_review_on_private_youtube',listened_to_audio=False)
        s.quality.validate_private_review(evidence,expected_voice='Zephyr')
        with self.assertRaises(ValueError):
            s.quality.validate_private_review(dict(evidence,voice='Achird'),expected_voice='Zephyr')

    def test_repeated_sources_are_rejected(self):
        scene=lambda identity:dict(mode='official_image',source_sha256=identity)
        with self.assertRaises(ValueError):s.quality.validate_variety([scene('a'),scene('a')])
        with self.assertRaises(ValueError):s.quality.validate_variety([scene(x) for x in 'abaca'])
        s.quality.validate_variety([scene(x) for x in 'abac'])

    def test_korean_topic_keys_remain_distinct(self):
        import unicodedata
        from app.core.recommendations import product_key
        self.assertEqual(product_key('프라이팬 예열'), '프라이팬예열')
        self.assertNotEqual(product_key('프라이팬 예열'), product_key('딸기 크림떡'))
        self.assertEqual(product_key(unicodedata.normalize('NFD','프라이팬')), product_key('프라이팬'))

    def fixture(self,root):
        image=root/'image.png';Image.new('RGB',(1080,1920),'teal').save(image)
        today=now_kst().date().isoformat()
        rec=dict(category='tech',title='Test',subject='Test',product_identity='Test',hook='문제 해결',why_now='새 공식 자료',key_feature='main',supporting_features=['a','b'],facts=['main'],visual_concept='실제 자료',product_keyword='Test',sources=[dict(title='source',url='https://example.org',published_date=today)],official_images=[dict(title='image',url='https://example.org/image',published_date=today)],purchase_link=dict(url='https://www.coupang.com/vp/products/123',seller='fixture',price_krw=99000,price_evidence='Synthetic verified option price',official_evidence='synthetic official evidence',rocket_evidence='synthetic rocket evidence',option='fixture',checked_at=now_kst().isoformat(),affiliate_url='https://link.coupang.com/a/fixture',affiliate_evidence='synthetic issued link evidence'))
        board=dict(author_model='gpt-6-astra',title='fixture',summary='test',popularity_basis='관심을 끄는 기능을 근거로 설명',scenes=[dict(role=role,mode='official_image',source_file=str(image),source_url='https://example.org/image',evidence='synthetic test image only',narration_ko='테스트입니다.',hook='문제가 있나요?' if i==0 else '',covered_features=['main','a','b'],duration_seconds=2) for i,role in enumerate(['need','solution','reason','product','product','cta'])])
        for i,scene in enumerate(board['scenes']):
            unique=root/f'fixture_{i}.png';Image.new('RGB',(1080,1920),(20+i*20,100,120)).save(unique);scene['source_file']=str(unique)
        rec.update(topic_key='fixture-topic',problem_key='fixture-problem',novelty_review=dict(checked_at=now_kst().isoformat(),channel='https://www.youtube.com/@GumaShop86',studio_checked=True,notes='Synthetic empty Studio fixture',comparisons=[]))
        board['bgm_track']='Carefree'
        return rec,board

    def test_funnel_and_model(self):
        with tempfile.TemporaryDirectory() as temp:
            rec,b=self.fixture(Path(temp));s.Board(**b)
            for change in ('model','order','popularity','veo','cta'):
                bad=copy.deepcopy(b)
                if change=='model':bad['author_model']='gemini-3.8-flash'
                if change=='order':bad['scenes'][0]['role']='product'
                if change=='popularity':bad['scenes'][2]['narration_ko']='인기 제품입니다.'
                if change=='veo':bad['scenes'][0].update(mode='veo',preserve_actual=True)
                if change=='cta':bad['scenes'][-1]['narration_ko']='하단 링크를 클릭하세요.'
                with self.assertRaises(ValueError,msg=change):s.Board(**bad)

    def test_expensive_tech_is_rejected_before_reserving(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rec,b=self.fixture(root)
            rec['purchase_link']['price_krw']=500001
            store.write_json(root/'rec.json',rec);store.write_json(root/'board.json',b)
            with patch.object(store,'reserve',side_effect=AssertionError('must not reserve')):
                with self.assertRaisesRegex(ValueError,'50만원'):s.build(root/'rec.json',root/'board.json')

    def test_weekly_similarity_and_category_slot(self):
        from app.core import recommendations as r
        with tempfile.TemporaryDirectory() as temp:
            rec,_=self.fixture(Path(temp));item=r.Recommendation(**rec)
            old=dict(idea_id='other',url='https://www.youtube.com/watch?v=12345678901',topic_key='other-topic',problem_key='other-problem')
            with patch.object(r,'recent_uploads',return_value=[old]):
                with self.assertRaises(ValueError):r.validate_novelty(item)
                item.novelty_review['comparisons']=[dict(url=old['url'],similar=False,reason='다른 문제와 사용 맥락을 다루는 테스트')]
                r.validate_novelty(item)
                old['problem_key']=item.problem_key
                with self.assertRaises(ValueError):r.validate_novelty(item)
            with patch.object(r,'recent_uploads',return_value=[]):
                with self.assertRaises(ValueError):r.DailyBatch(date=r.now_kst().date().isoformat(),researched_at=r.now_kst(),slot='15:00',items=[item])

    def test_slot_accumulation_and_affiliate(self):
        from app.core import recommendations as recs
        with tempfile.TemporaryDirectory() as temp,patch.object(recs,'RECOMMENDATIONS_DIR',Path(temp)/'recommendations'),patch.object(recs,'recent_uploads',return_value=[]):
            root=Path(temp);rec,_=self.fixture(root)
            for i,hour in enumerate((9,15,21)):
                stamp=now_kst().replace(hour=hour,minute=0,second=0,microsecond=0)
                item=copy.deepcopy(rec);item['subject']='fixture'+str(i);item['product_identity']=item['subject'];item['purchase_link']['checked_at']=stamp.isoformat();item['category']=['tech','food','household'][i];item['novelty_review']['checked_at']=stamp.isoformat()
                with patch.object(recs,'now_kst',return_value=stamp):
                    data=dict(date=stamp.date().isoformat(),researched_at=stamp,slot=f'{hour:02d}:00',items=[item])
                    batch=DailyBatch(**data);result=recs.save_batch(batch)
                    self.assertEqual(len(result['items']),i+1)
                    self.assertEqual(result['research_count'],i+1)
                    with self.assertRaises(ValueError):recs.save_batch(batch)
                    with self.assertRaises(ValueError):DailyBatch(**dict(data,items=[item,item]))
                    item['purchase_link']['affiliate_url']=''
                    with self.assertRaises(ValueError):DailyBatch(**dict(data,items=[item]))
            self.assertEqual(len(list((Path(temp)/'recommendations/history').glob('*.json'))),3)

    def test_images_render_private_and_explicit_public_approval(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(store,'ROOT',Path(temp)/'products'),patch.object(store,'STORAGE_DIR',Path(temp)):
            root=Path(temp);rec,b=self.fixture(root)
            store.write_json(root/'rec.json',rec);store.write_json(root/'board.json',b)
            result=s.build(root/'rec.json',root/'board.json');id=result['idea_id'];n=result['number']
            folder=store.version_dir(id,'Preview',n)
            review=dict(preflight={k:True for k in s.quality.PREFLIGHT_AXES},reviewed_by='gpt-6-astra',passed=True,board_sha256=s.digest(folder/'storyboard.json'),scenes=[dict(number=i,passed=True,notes='Synthetic fixture verification') for i in range(1,7)])
            store.write_json(root/'review.json',review);s.seal(id,n,root/'review.json')
            v=s.enqueue(id,n);self.assertEqual(v['voice'],'Zephyr')
            self.assertEqual([x['stage'] for x in store.workflow(store.read(id))['buttons']],['Preview','Video'])
            async def speech(text,path,voice,rate):
                self.assertEqual(voice,'Zephyr')
                s.media.run([s.media.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','sine=frequency=440','-t','0.3',str(path)])
            with patch.object(s,'synthesize_speech',side_effect=speech),patch.object(s,'generate_video_clip',side_effect=AssertionError('No Veo for official images')):
                asyncio.run(s.render(id,v['number']))
            vf=store.version_dir(id,'Video',v['number']);self.assertTrue((vf/'final.mp4').is_file())
            completed=store.get(id,'Video',v['number']);self.assertEqual(len(completed['cuts']),6)
            self.assertEqual(s.enqueue(id,n)['storyboard']['bgm_track'],v['storyboard']['bgm_track'])
            music=s.read(vf/'bgm_review.json')
            self.assertTrue(music['video_stream_unchanged'])
            self.assertLess(music['peak_dbfs'],0)
            self.assertIn(music['track']['attribution'],s.read(vf/'upload.json')['description'])
            from app.studio import cut_feedback,CutFeedback
            request=asyncio.run(cut_feedback(id,1,2,CutFeedback(narration='수정 대사',feedback='두 번째 컷 교체')))
            self.assertEqual(request['cut_number'],2)
            self.assertEqual(request['state'],'pending')
            self.assertEqual(completed['cuts'][1]['narration_ko'],'테스트입니다.')
            duplicate=asyncio.run(cut_feedback(id,1,2,CutFeedback(narration='수정 대사',feedback='두 번째 컷 교체')))
            self.assertEqual(request['id'],duplicate['id'])
            evidence=dict(notes='Synthetic test evidence only')
            with self.assertRaises(ValueError):s.publication(id,1,'public',dict(evidence,visibility='public',url='https://www.youtube.com/watch?v=12345678901'))
            s.publication(id,1,'review',dict(evidence,audio_visual_passed=True,listened_to_audio=True,scores={k:8 for k in s.quality.REVIEW_AXES},file_sha256=s.digest(vf/'final.mp4')))
            self.assertEqual(s.read(vf/'upload.json')['state'],'web_review')
            with self.assertRaisesRegex(ValueError,'별도 YouTube'):s.publication(id,1,'claim',evidence)
            with self.assertRaises(ValueError):s.publication(id,1,'authorize_upload',dict(evidence,user_approved=False,file_sha256=s.digest(vf/'final.mp4')))
            s.publication(id,1,'authorize_upload',dict(evidence,user_approved=True,file_sha256=s.digest(vf/'final.mp4')))
            s.publication(id,1,'claim',evidence)
            with self.assertRaises(ValueError):s.publication(id,1,'claim',evidence)
            s.publication(id,1,'private',dict(evidence,visibility='private',channel='https://www.youtube.com/@GumaShop86',url='https://www.youtube.com/watch?v=12345678901'))
            with self.assertRaises(Exception):asyncio.run(request_publish(id,1,StageRequest(approved=False)))
            asyncio.run(request_publish(id,1,StageRequest(approved=True)))
            s.publication(id,1,'public',dict(evidence,visibility='public',url='https://www.youtube.com/watch?v=12345678901'))
            self.assertEqual(s.read(vf/'upload.json')['state'],'public')
            (vf/'final.mp4').write_bytes(b'tampered')
            with self.assertRaises(ValueError):s.publication(id,1,'public',evidence)


if __name__=='__main__':unittest.main()
