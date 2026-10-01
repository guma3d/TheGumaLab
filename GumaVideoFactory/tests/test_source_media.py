import unittest,tempfile,json
from pathlib import Path
from io import BytesIO
from PIL import Image
from unittest.mock import patch
from pydantic import ValidationError
from app.core import source_media as media
class SourceMediaTests(unittest.TestCase):
 def source(self,**kwargs):
  data=dict(title='food',source_url='https://example.com/file',creator='creator',license='CC BY',license_url='https://creativecommons.org/licenses/by/4.0/',attribution='creator CC BY 4.0');data.update(kwargs);return media.MediaSource(**data)
 def test_unconfirmed_and_noncommercial_licenses_rejected(self):
  for license in ('unknown','standard_youtube','CC BY-NC'):
   with self.assertRaises(ValidationError):self.source(license=license)
  with self.assertRaises(ValidationError):self.source(source_url='javascript:alert(1)')
  with self.assertRaises(ValidationError):self.source(clip_seconds=5)
 def test_photo_cache_and_missing_source_guard(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(media,'SOURCE_MEDIA_DIR',Path(directory)):
   image=BytesIO();Image.new('RGB',(60,40),'orange').save(image,format='PNG')
   name=media.store_media(image.getvalue(),'image');source=self.source(local_file=name)
   self.assertEqual(source.file_path().name,name)
   preview=Path(directory)/'preview.png';media.media_preview(source,preview,'9:16')
   with Image.open(preview) as im:self.assertEqual(im.size,(720,1280))
   with self.assertRaises(ValueError):self.source(local_file='../outside.png').file_path()
 def test_private_network_download_is_rejected(self):
  with patch.object(media.socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
   with self.assertRaises(ValueError):media.download_media(self.source(download_url='https://example.com/file.png'))
