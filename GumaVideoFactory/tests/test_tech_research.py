import unittest

from app.core.tech_research import validate_tech_evidence


class TechSelectionTests(unittest.TestCase):
    def setUp(self):
        self.item = {
            'category': 'tech',
            'purchase_link': {'affiliate_url': 'https://link.coupang.com/a/test', 'affiliate_evidence': 'issued UI'},
            'tech_evidence': {
                'market_fit': {'basis': 'popularity', 'reason': 'observed purchase count',
                               'source_url': 'https://www.coupang.com/vp/products/1', 'checked_at': '2026-10-09'},
                'official_search_evidence': 'manufacturer page',
                'videos': [dict(source_type='manufacturer_official', source_url='https://example.com/video',
                                publisher_evidence='manufacturer linked', local_path='source.mp4', sha256='a' * 64,
                                technical_content='verified function', used_range='1-4s',
                                playback_review='reviewed range', reuse_permission_evidence='licensed')],
            },
        }

    def test_affiliate_is_first_required_condition(self):
        self.item['purchase_link'] = {}
        self.item['tech_evidence'] = {}
        with self.assertRaisesRegex(ValueError, '파트너스'):
            validate_tech_evidence(self.item)

    def test_popularity_or_context_is_required_before_media(self):
        self.item['tech_evidence']['market_fit'] = {}
        with self.assertRaisesRegex(ValueError, '계절'):
            validate_tech_evidence(self.item)

    def test_official_source_and_image_research_are_supported(self):
        validate_tech_evidence(self.item)
        asset = self.item['tech_evidence'].pop('videos')[0]
        asset['visual_review'] = 'exact technology diagram inspected'
        self.item['tech_evidence']['images'] = [asset]
        validate_tech_evidence(self.item)

    def test_third_party_country_and_permissions_remain_required(self):
        asset = self.item['tech_evidence']['videos'][0]
        asset.update(source_type='third_party', creator_country='US')
        with self.assertRaisesRegex(ValueError, '중국'):
            validate_tech_evidence(self.item)
        asset['creator_country'] = 'CN'
        self.item['tech_evidence']['official_unavailable_reason'] = 'no suitable official clip'
        validate_tech_evidence(self.item)
        del asset['reuse_permission_evidence']
        with self.assertRaisesRegex(ValueError, 'reuse_permission'):
            validate_tech_evidence(self.item)

    def test_non_tech_selection_is_unchanged(self):
        validate_tech_evidence({'category': 'food'})
        validate_tech_evidence({'category': 'household'})
