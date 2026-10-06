import unittest
from datetime import timedelta
from app.core.living_research import search_plan, validate_living_evidence
from app.core.recommendations import LivingEvidence, now_kst


class LivingResearchTests(unittest.TestCase):
    def record(self, **changes):
        data = dict(route='commerce', checked_at=now_kst(), sources=[dict(title='상품 원문', url='https://www.coupang.com/vp/products/123')],
                    review_count=800, rating=4.5, review_scope='상품 페이지 옵션 합산',
                    review_findings='최근 후기와 낮은 평점에서 확인한 한계를 기록한다.',
                    selection_reason='계절 불편을 해결하고 정확한 제품의 실제 시연을 확보할 수 있다.')
        data.update(changes)
        return LivingEvidence(**data)

    def test_commerce_without_fake_publication_date(self):
        validate_living_evidence(self.record(), now_kst().date())
        with self.assertRaises(ValueError):
            validate_living_evidence(self.record(review_scope=''), now_kst().date())
        with self.assertRaises(ValueError):
            validate_living_evidence(self.record(review_count=None), now_kst().date())

    def test_sales_requires_period_and_scope(self):
        with self.assertRaises(ValueError):
            validate_living_evidence(self.record(sales_statement='한 달간 100명 이상 구매'), now_kst().date())

    def test_news_can_have_few_reviews_but_must_be_recent(self):
        day = now_kst().date()
        item = self.record(route='news', review_count=2, event_date=day,
                           sources=[dict(title='뉴스 원문', url='https://example.com/news', published_date=str(day))])
        validate_living_evidence(item, day)
        item.event_date = day - timedelta(days=31)
        with self.assertRaises(ValueError): validate_living_evidence(item, day)

    def test_missing_evidence_and_stale_checks_fail(self):
        with self.assertRaises(ValueError): validate_living_evidence(None, now_kst().date())
        with self.assertRaises(ValueError): self.record(checked_at=now_kst()-timedelta(hours=25))
        self.assertFalse(search_plan()['review_preference']['hard_cutoff'])
