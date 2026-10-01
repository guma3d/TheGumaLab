import unittest
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from pydantic import ValidationError
from app.core import recommendations as rec

class RecommendationTests(unittest.TestCase):
    def batch(self):
        now=rec.now_kst()
        return dict(date=now.strftime('%Y-%m-%d'), researched_at=now, items=[dict(category=c,title=f'{c}{i}',subject=f'{c}{i}',hook='hook',why_now='recent',key_feature='feature',visual_concept='3D',product_keyword='product',supporting_features=['feature two','feature three'] if c=='tech' else [],facts=['verified'],sources=[dict(title='source',url='https://example.com/news',published_date=now.strftime('%Y-%m-%d'))]) for c in ('tech','food') for i in range(5)])
    def test_exact_daily_counts_duplicates_and_freshness(self):
        data=self.batch(); self.assertEqual(len(rec.DailyBatch(**data).items),10)
        data['items'][0]['category']='food'
        with self.assertRaises(ValidationError): rec.DailyBatch(**data)
        data=self.batch(); data['items'][1]['subject']=data['items'][0]['subject']
        with self.assertRaises(ValidationError): rec.DailyBatch(**data)
        data=self.batch(); data['items'][0]['sources'][0]['published_date']=(rec.now_kst()-timedelta(days=31)).strftime('%Y-%m-%d')
        with self.assertRaises(ValidationError): rec.DailyBatch(**data)
    def test_archives_and_rejects_stale_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(rec,'RECOMMENDATIONS_DIR',Path(tmp)):
            batch=rec.DailyBatch(**self.batch()); saved=rec.save_batch(batch)
            self.assertEqual(saved['research_count'],1)
            self.assertEqual(len(list((Path(tmp)/'history').glob('*.json'))),1)
            self.assertEqual(rec.load_daily()['items'][0]['id'],saved['items'][0]['id'])
            with self.assertRaises(ValueError): rec.save_batch(batch)

    def test_category_only_update_preserves_other_category(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(rec,'RECOMMENDATIONS_DIR',Path(tmp)):
            original=rec.save_batch(rec.DailyBatch(**self.batch()))
            data=self.batch()
            data['researched_at']=data['researched_at']+timedelta(seconds=1)
            data['items']=[item for item in data['items'] if item['category']=='tech']
            data['items'][0]['title']='Updated tech'
            saved=rec.save_batch(rec.DailyBatch(**data))
            self.assertEqual(len(saved['items']),10)
            self.assertEqual(saved['items'][0]['title'],'Updated tech')
            self.assertEqual([i for i in saved['items'] if i['category']=='food'],[i for i in original['items'] if i['category']=='food'])

    def test_first_category_only_batch_and_incomplete_category(self):
        data=self.batch()
        data['items']=data['items'][:5]
        with tempfile.TemporaryDirectory() as tmp, patch.object(rec,'RECOMMENDATIONS_DIR',Path(tmp)):
            saved=rec.save_batch(rec.DailyBatch(**data))
            self.assertEqual(len(saved['items']),5)
        data['items'].pop()
        with self.assertRaises(ValidationError): rec.DailyBatch(**data)
