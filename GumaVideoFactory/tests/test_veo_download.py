import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from app.core import veo_client as v


class VeoCompatibilityTest(unittest.TestCase):
    def test_uri_response_is_downloaded_without_unsupported_option(self):
        video=Mock(video_bytes=None)
        client=Mock()
        client.models.generate_videos.return_value=SimpleNamespace(done=True,error=None,response=SimpleNamespace(generated_videos=[SimpleNamespace(video=video)]))
        with tempfile.TemporaryDirectory() as temp, patch.object(v,'GEMINI_API_KEY','test'), patch.object(v.genai,'Client',return_value=client):
            output=Path(temp)/'cut.mp4'
            v.generate_video_clip('A contextual test shot',output)
            config=client.models.generate_videos.call_args.kwargs['config']
            self.assertNotIn('enhance_prompt',config.model_dump(exclude_none=True))
            client.files.download.assert_called_once_with(file=video)
            video.save.assert_called_once_with(str(output))


if __name__=='__main__':unittest.main()
