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
    def fixture(self,root):
        image=root/'image.png';Image.new('RGB',(160,240),'teal').save(image)
        today=now_kst().date().isoformat()
        rec=dict(category='tech',title='Test',subject='Test',product_identity='Test',hook='문제 해결',why_now='새 공식 자료',key_feature='main',supporting_features=['a','b'],facts=['main'],visual_concept='실제 자료',product_keyword='Test',sources=[dict(title='source',url='https://example.org',published_date=today)],official_images=[dict(title='image',url='https://example.org/image',published_date=today)],purchase_link=dict(url='https://www.coupang.com/vp/products/123',seller='fixture',official_evidence='synthetic official evidence',rocket_evidence='synthetic rocket evidence',option='fixture',checked_at=now_kst().isoformat(),affiliate_url='https://link.coupang.com/a/fixture',affiliate_evidence='synthetic issued link evidence'))
        board=dict(author_model='gpt-6-astra',title='fixture',summary='test',popularity_basis='관심을 끄는 기능을 근거로 설명',scenes=[dict(role=role,mode='official_image',source_file=str(image),source_url='https://example.org/image',evidence='synthetic test image only',narration_ko='테스트입니다.',hook='문제가 있나요?' if i==0 else '',covered_features=['main','a','b'],duration_seconds=2) for i,role in enumerate(['need','solution','reason','product','product','cta'])])
        rec.update(topic_key='fixture-topic',problem_key='fixture-problem',novelty_review=dict(checked_at=now_kst().isoformat(),channel='https://www.youtube.com/@GumaShop86',studio_checked=True,notes='Synthetic empty Studio fixture',comparisons=[]))
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
        with tempfile.TemporaryDirectory() as temp,patch.object(recs,'RECOMMENDATIONS_DIR',Path(temp)/'recommendations'):
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
            review=dict(reviewed_by='gpt-6-astra',passed=True,board_sha256=s.digest(folder/'storyboard.json'),scenes=[dict(number=i,passed=True,notes='Synthetic fixture verification') for i in range(1,7)])
            store.write_json(root/'review.json',review);s.seal(id,n,root/'review.json')
            v=s.enqueue(id,n);self.assertEqual(v['voice'],'ko-KR-SunHiNeural')
            self.assertEqual([x['stage'] for x in store.workflow(store.read(id))['buttons']],['Preview','Video'])
            async def speech(text,path,voice):
                self.assertEqual(voice,'ko-KR-SunHiNeural')
                s.media.run([s.media.get_ffmpeg_bin(),'-v','error','-f','lavfi','-i','sine=frequency=440','-t','0.3',str(path)])
            with patch.object(s,'synthesize_speech',side_effect=speech),patch.object(s,'generate_video_clip',side_effect=AssertionError('No Veo for official images')):
                asyncio.run(s.render(id,v['number']))
            vf=store.version_dir(id,'Video',v['number']);self.assertTrue((vf/'final.mp4').is_file())
            completed=store.get(id,'Video',v['number']);self.assertEqual(len(completed['cuts']),6)
            from app.studio import cut_feedback,CutFeedback
            request=asyncio.run(cut_feedback(id,1,2,CutFeedback(narration='수정 대사',feedback='두 번째 컷 교체')))
            self.assertEqual(request['cut_number'],2)
            self.assertEqual(request['state'],'pending')
            self.assertEqual(completed['cuts'][1]['narration_ko'],'테스트입니다.')
            duplicate=asyncio.run(cut_feedback(id,1,2,CutFeedback(narration='수정 대사',feedback='두 번째 컷 교체')))
            self.assertEqual(request['id'],duplicate['id'])
            evidence=dict(notes='Synthetic test evidence only')
            with self.assertRaises(ValueError):s.publication(id,1,'public',dict(evidence,visibility='public',url='https://www.youtube.com/watch?v=12345678901'))
            s.publication(id,1,'review',dict(evidence,audio_visual_passed=True));s.publication(id,1,'claim',evidence)
            with self.assertRaises(ValueError):s.publication(id,1,'claim',evidence)
            s.publication(id,1,'private',dict(evidence,visibility='private',channel='https://www.youtube.com/@GumaShop86',url='https://www.youtube.com/watch?v=12345678901'))
            with self.assertRaises(Exception):asyncio.run(request_publish(id,1,StageRequest(approved=False)))
            asyncio.run(request_publish(id,1,StageRequest(approved=True)))
            s.publication(id,1,'public',dict(evidence,visibility='public',url='https://www.youtube.com/watch?v=12345678901'))
            self.assertEqual(s.read(vf/'upload.json')['state'],'public')
            (vf/'final.mp4').write_bytes(b'tampered')
            with self.assertRaises(ValueError):s.publication(id,1,'public',evidence)


if __name__=='__main__':unittest.main()
