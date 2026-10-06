import hashlib
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from PIL import Image
from app.core.recommendation_readiness import RecommendationReadiness, validate_readiness


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=datetime.now(timezone.utc)
        (self.root/'proof.json').write_text('issued link verification')
        Image.new('RGB',(720,1080)).save(self.root/'product.png')
        def asset(name):return dict(path=name,sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest())
        self.item=SimpleNamespace(category='food',purchase_link=SimpleNamespace(url='https://www.coupang.com/vp/products/123',option='1개',affiliate_url='https://link.coupang.com/a/test',affiliate_evidence='실제 계정에서 발급된 링크와 옵션 확인'),readiness=None)
        self.item.readiness=RecommendationReadiness(checked_at=self.now,reviewer='Codex',product_url=self.item.purchase_link.url,option='1개',affiliate_url=self.item.purchase_link.affiliate_url,affiliate_proof=asset('proof.json'),resources=[dict(**asset('product.png'),kind='image',source_url='https://example.com/official',usage_basis='제조사의 사용 허가를 확인한 자료',product_match='실제 추천 상품의 옵션과 포장 일치',purpose='제품 외형과 식감 설명에 사용할 실물 참고 이미지',visually_reviewed=True)],coverage_review='실물 이미지의 해상도와 제품 일치 여부를 확인했으며 생성 보조 장면의 참고 자료로 사용한다.')

    def test_verified_resources_pass(self):
        validate_readiness(self.item,self.now,self.root)

    def test_missing_changed_and_escape_files_fail(self):
        original=self.item.readiness.resources[0].path
        for name in ('missing.png','../escape.png'):
            self.item.readiness.resources[0].path=name
            with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)
        self.item.readiness.resources[0].path=original
        (self.root/original).write_bytes(b'changed')
        with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)

    def test_mismatch_stale_and_missing_link_fail(self):
        self.item.readiness.option='다른 옵션'
        with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)
        self.item.readiness.option='1개';self.item.readiness.checked_at-=timedelta(days=2)
        with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)
        self.item.readiness.checked_at=self.now;self.item.purchase_link.affiliate_url=''
        with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)

    def test_thumbnail_is_not_production_resource(self):
        path=self.root/'product.png';Image.new('RGB',(212,212)).save(path)
        self.item.readiness.resources[0].sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):validate_readiness(self.item,self.now,self.root)
