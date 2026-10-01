import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image
from app.core import image_client


class ImageClientTests(unittest.TestCase):
    def test_request_keeps_client_open_and_saves_decodable_image(self):
        payload = BytesIO()
        Image.new('RGB', (12, 20), 'blue').save(payload, format='PNG')
        response = SimpleNamespace(parts=[SimpleNamespace(inline_data=SimpleNamespace(
            mime_type='image/png', data=payload.getvalue()))])
        manager = MagicMock()
        active_client = manager.__enter__.return_value

        def generate(**kwargs):
            manager.__enter__.assert_called_once()
            manager.__exit__.assert_not_called()
            self.assertEqual(kwargs['config'].image_config.aspect_ratio, '9:16')
            self.assertEqual(len(kwargs['contents']), 2)
            return response

        active_client.models.generate_content.side_effect = generate
        with tempfile.TemporaryDirectory() as tmp, patch.object(image_client, 'GEMINI_API_KEY', 'test'), patch.object(image_client.genai, 'Client', return_value=manager):
            reference = Path(tmp) / 'reference.png'
            reference.write_bytes(payload.getvalue())
            target = Path(tmp) / 'nested' / 'preview.png'
            result = image_client.generate_preview_image('scene', target, '9:16', '3D', reference)
            self.assertEqual(result, target)
            with Image.open(target) as saved:
                self.assertEqual(saved.size, (12, 20))
        manager.__exit__.assert_called_once()

    def test_failed_request_closes_client_without_creating_image(self):
        manager = MagicMock()
        manager.__enter__.return_value.models.generate_content.side_effect = RuntimeError('request failed')
        with tempfile.TemporaryDirectory() as tmp, patch.object(image_client, 'GEMINI_API_KEY', 'test'), patch.object(image_client.genai, 'Client', return_value=manager):
            target = Path(tmp) / 'preview.png'
            with self.assertRaisesRegex(RuntimeError, 'request failed'):
                image_client.generate_preview_image('scene', target, '9:16', '3D')
            self.assertFalse(target.exists())
        manager.__exit__.assert_called_once()
