import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.core import versions as store, shopping
from app.core.production_rules import snapshot


class NarrativeCategoryTests(unittest.TestCase):
    def test_category_pages_filter_archive_and_default_to_longform(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(store, 'ROOT', Path(temp)), \
                patch.object(main, 'visible_daily', return_value={'date': '2026-10-10', 'items': []}), \
                patch.object(main, 'list_all_projects', return_value=[]):
            long = store.create(dict(category='longform', subject='LONG STORY', hook='hook'), '2026-10-10')
            short = store.create(dict(category='story_shorts', subject='SHORT STORY', hook='hook'), '2026-10-10')
            client = TestClient(main.app)
            home = client.get('/')
            self.assertEqual(home.status_code, 200)
            self.assertIn('/ideas/' + long['id'], home.text)
            self.assertNotIn('/ideas/' + short['id'], home.text)
            self.assertIn('16:9', home.text)
            for category in ('longform', 'story_shorts', 'tech', 'food', 'household'):
                self.assertIn('category=' + category, home.text)
                self.assertEqual(client.get('/?category=' + category).status_code, 200)
            shorts = client.get('/?category=story_shorts').text
            self.assertIn('/ideas/' + short['id'], shorts)
            self.assertNotIn('/ideas/' + long['id'], shorts)
            self.assertIn('9:16', shorts)
            self.assertEqual(client.get('/?category=invalid').status_code, 404)

    def test_narratives_cannot_enter_shopping_renderer(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(store, 'ROOT', Path(temp)), \
                patch.object(shopping, 'verify_package') as verify:
            for category in ('longform', 'story_shorts'):
                idea = store.create(dict(category=category, subject='story'), '2026-10-10')
                with self.assertRaisesRegex(ValueError, '쇼핑쇼츠 제작기'):
                    shopping.enqueue(idea['id'], 1)
                self.assertEqual(store.history(idea['id'], 'Video'), [])
            verify.assert_not_called()

    def test_shopping_constraints_do_not_leak_into_narrative_prompts(self):
        for category in ('longform', 'story_shorts'):
            ids = {r['id'] for r in snapshot(category)['rules']}
            self.assertNotIn('coupang-purchase', ids)
            self.assertNotIn('approved-inserted-cut-preservation', ids)
            self.assertIn('web-version-review', ids)
            self.assertIn('required-bgm', ids)
            self.assertIn('longform-first-strategy', ids)
        self.assertIn('coupang-purchase', {r['id'] for r in snapshot('food')['rules']})
