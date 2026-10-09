import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import public_catalog as catalog


class PublicCatalogTests(unittest.TestCase):
    def test_only_approved_public_exact_versions_are_exposed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = dict(idea_id='a'*16,version=11,number=1,approved=True,name='<상품>',category='푸드',summary='요약',details=['특징'],purchase_url='https://link.coupang.com/a/test',private_note='SECRET')
            (root/'public_catalog.json').write_text(json.dumps({'items':[item]}))
            def write_upload(state):
                (root/'upload.json').write_text(json.dumps(dict(state=state,privacy=state,url='https://www.youtube.com/watch?v=T0eKHI5ieXA',secret='SECRET')))
            with patch.object(catalog,'STORAGE_DIR',root), patch.object(catalog.versions,'version_dir',return_value=root), patch.object(catalog.versions,'read',return_value={}):
                for state in ['private','web_review','publish_requested']:
                    write_upload(state)
                    self.assertEqual(catalog.public_products(),[])
                write_upload('public')
                result=catalog.public_products()
                self.assertEqual(len(result),1)
                self.assertNotIn('SECRET',json.dumps(result))
                item['approved']=False
                (root/'public_catalog.json').write_text(json.dumps({'items':[item]}))
                self.assertEqual(catalog.public_products(),[])

    def test_absent_registry_is_empty(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(catalog,'STORAGE_DIR',Path(temp)):
            self.assertEqual(catalog.public_products(),[])
