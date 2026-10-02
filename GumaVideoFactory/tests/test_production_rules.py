import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core.production_rules import snapshot, prompt_context
from app.core import versions as store
from app.core.product_selection import selection_policy


class SharedRulesTests(unittest.TestCase):
    def test_tech_context_is_general_and_food_keeps_real_media(self):
        tech = snapshot('tech')
        food = snapshot('food')
        self.assertIn('surface-fidelity', [r['id'] for r in tech['rules']])
        self.assertNotIn('surface-fidelity', [r['id'] for r in food['rules']])
        self.assertIn('real-food', [r['id'] for r in food['rules']])
        self.assertNotIn('iPhone 18', prompt_context('tech'))
        self.assertEqual(len(tech['sha256']), 64)

    def test_other_products_use_same_approval_flow_without_phone_dimensions(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(store, 'ROOT', Path(temp)):
            for product in ('DJI Osmo 360 II', 'Steam Robot Cleaner', 'Wireless Headphones'):
                self.assertIsNone(selection_policy(product))
                idea = store.create(dict(category='tech', subject=product), '2026-10-02')
                store.reserve(idea['id'], '3DModel')
                store.update(idea['id'], '3DModel', 1, status='ready', approved_at='approved')
                flow = store.workflow(idea)
                self.assertEqual(flow['message'], '예약 준비 · 매일 09·21시')
                self.assertTrue(flow['buttons'][0]['primary'])
