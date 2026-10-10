import unittest

from app.core.tech_research import validate_tech_evidence, validate_tech_visual_plan


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


class TechFixedCameraTests(unittest.TestCase):
    def setUp(self):
        self.scene = dict(mode='illustration_clip', tech_visual=dict(
            generator='imagegen', camera='fixed', reference_evidence='official diagram',
            base_image='base.png + hash', edit_lineage='base -> separated -> assembled',
            consistency_review='parts, lighting and camera compared across all frames'))

    def test_imagegen_still_and_composite_are_allowed(self):
        for mode in ('illustration_clip', 'explanatory_image'):
            self.scene['mode'] = mode
            validate_tech_visual_plan('tech', {'scenes': [self.scene]})

    def test_paid_generation_legacy_bypass_and_orbit_are_rejected(self):
        self.scene['mode'] = 'veo'
        with self.assertRaises(ValueError):
            validate_tech_visual_plan('tech', {'paid_generation_user_request': 'old permission', 'scenes': [self.scene]})
        self.scene['mode'] = 'illustration_clip'
        self.scene['tech_visual']['camera'] = 'orbit'
        with self.assertRaises(ValueError):
            validate_tech_visual_plan('tech', {'scenes': [self.scene]})
        self.scene['tech_visual']['camera'] = 'fixed'
        with self.assertRaises(ValueError):
            validate_tech_visual_plan('tech', {'needs_3d': True, 'scenes': [self.scene]})

    def test_missing_lineage_is_not_accepted(self):
        del self.scene['tech_visual']['edit_lineage']
        with self.assertRaisesRegex(ValueError, 'edit_lineage'):
            validate_tech_visual_plan('tech', {'scenes': [self.scene]})

    def test_other_categories_keep_their_existing_paths(self):
        from app.core.production_rules import snapshot
        for category in ('food', 'household', 'longform', 'story_shorts'):
            validate_tech_visual_plan(category, {'scenes': [{'mode': 'veo'}]})
            self.assertNotIn('tech-imagegen-fixed-camera', [r['id'] for r in snapshot(category)['rules']])
        self.assertIn('tech-imagegen-fixed-camera', [r['id'] for r in snapshot('tech')['rules']])
