import unittest,tempfile,json
from pathlib import Path
from io import BytesIO
from PIL import Image
from unittest.mock import patch, MagicMock
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

 def test_youtube_requires_platform_cc_metadata_before_download(self):
  client=MagicMock();client.__enter__.return_value=client
  source=self.source(provider='youtube_cc',kind='video',source_url='https://www.youtube.com/watch?v=abcdefghijk')
  client.extract_info.return_value={'license':'Standard YouTube License','duration':60}
  with patch('yt_dlp.YoutubeDL',return_value=client):
   with self.assertRaises(ValueError):media.download_youtube_cc(source)
   client.process_info.assert_not_called()
  client.extract_info.return_value={'license':'Creative Commons Attribution license (reuse allowed)','duration':60}
  def save_clip(info):
   from pathlib import Path
   target=Path(client.options['outtmpl'].replace('%(ext)s','mp4'));target.write_bytes(b'video')
  def fake_downloader(options):
   client.options=options;client.process_info.side_effect=save_clip;return client
  with patch('yt_dlp.YoutubeDL',side_effect=fake_downloader),patch.object(media,'store_media',return_value='verified.mp4'):
   self.assertEqual(media.download_youtube_cc(source),'verified.mp4')
   self.assertEqual(source.start_seconds,0)
   self.assertIn('원본 발췌 위치',source.attribution)
