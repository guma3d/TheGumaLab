import unittest
from app.core import bgm, upload_metadata as meta


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.review = {'track':dict(license=bgm.MIXKIT_LICENSE,attribution_required=False,
            license_url='https://mixkit.co/license/#musicFree',
            attribution_policy_url='https://mixkit.co/free-stock-music/',license_checked_at='2026-10-09')}

    def test_no_credit_bullets_and_exact_last_line(self):
        text=meta.description(['고구마빵.','냉동 보관.'], 'https://example.com', self.review, '#쇼츠')
        self.assertTrue(text.startswith('- 고구마빵.\n- 냉동 보관.'))
        self.assertEqual(text.splitlines()[-1],meta.DISCLOSURE)
        self.assertNotIn('BGM:',text)
        self.assertTrue(bgm.has_required_credit(text,self.review))
        self.assertEqual(meta.title('[광고] 상품 이름'),'상품 이름')

    def test_unverified_license_cannot_omit_credit(self):
        self.review['track'].pop('attribution_policy_url')
        with self.assertRaises(ValueError):meta.description(['상품.'],'url',self.review)
        self.assertFalse(bgm.has_required_credit('',self.review))

    def test_description_always_has_ad_and_five_distinct_tags(self):
        text=meta.description(['새 제품의 사용법.'],'url',self.review)
        tags=next(line for line in text.splitlines() if line.startswith('#')).split()
        self.assertIn('#광고',tags)
        self.assertGreaterEqual(len(set(tags)-{'#광고'}),5)
        self.assertEqual(text.splitlines()[-1],meta.DISCLOSURE)

    def test_product_tags_preserve_author_tags_without_unrelated_defaults(self):
        text=meta.description(['니트 보풀 관리.'],'url',self.review,
            '#미지아 #미지아 #광고',context='미지아 보풀제거기 2')
        tags=next(line for line in text.splitlines() if line.startswith('#')).split()
        self.assertEqual(tags.count('#광고'),1)
        self.assertEqual(tags.count('#미지아'),1)
        self.assertIn('#가전',tags)
        self.assertIn('#니트',tags)
        self.assertNotIn('#간식',tags)
        self.assertNotIn('#가을',tags)

    def test_legacy_credit_before_disclosure(self):
        report={'track':dict(license='CC BY 4.0',attribution='Artist / CC BY 4.0')}
        text=meta.description(['상품.'],'url',report)
        self.assertIn('BGM: Artist / CC BY 4.0',text)
        self.assertEqual(text.splitlines()[-1],meta.DISCLOSURE)
        self.assertFalse(bgm.has_required_credit('No credit',report))

    def test_old_boilerplate_is_omitted_without_inventing_experience(self):
        text=meta.description('냉동 간식. 직접 시식 후기가 아닙니다. Zephyr 합성 여성 음성을 사용했습니다.', 'url', self.review)
        self.assertTrue(text.startswith('- 냉동 간식.'))
        self.assertNotIn('시식',text)
        self.assertNotIn('Zephyr',text)
