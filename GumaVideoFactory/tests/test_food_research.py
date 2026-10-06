import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from app.core.food_research import search_plan, validate_food_trend
from app.core.recommendations import FoodTrend, now_kst


class FoodResearchTests(unittest.TestCase):
    def record(self):
        day=now_kst().date()
        return FoodTrend(route='overseas', topic='검증용 음식', country='일본', event_date=day,
            evidence=[dict(title='현지 원문',url='https://example.com/news',published_date=day.isoformat())],
            connection='related_product',connection_evidence='현지 음식과 관련된 제품이며 동일 제품이나 같은 맛을 보장하지 않는다.')

    def test_search_window(self):
        plan=search_plan(date(2026,10,6))
        self.assertEqual({q['route'] for q in plan['queries']}, {'broadcast','overseas','retail','recipe'})
        self.assertTrue(all('after:2026-09-29' in q['query'] for q in plan['queries']))

    def test_stale_or_missing_evidence(self):
        day=now_kst().date()
        with self.assertRaises(ValueError): validate_food_trend(None,day)
        trend=self.record();validate_food_trend(trend,day)
        trend.event_date=day-timedelta(days=31)
        with self.assertRaises(ValueError): validate_food_trend(trend,day)

    def test_broadcast_stock_and_recipe_claims(self):
        day=now_kst().date();trend=self.record();trend.route='broadcast'
        with self.assertRaises(ValueError): validate_food_trend(trend,day)
        trend.program='방송명 1회';validate_food_trend(trend,day)
        trend.stock_claim='판매처의 정확한 옵션이 확인 시각에 품절'
        with self.assertRaises(ValueError): validate_food_trend(trend,day)
        trend.stock_claim='';trend.route='recipe'
        with self.assertRaises(ValueError): validate_food_trend(trend,day)
        trend.connection='recipe_ingredient';validate_food_trend(trend,day)
