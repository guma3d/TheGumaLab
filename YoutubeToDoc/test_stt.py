from youtube_transcript_api import YouTubeTranscriptApi
import sys
try:
    r = YouTubeTranscriptApi.get_transcript(sys.argv[1], languages=["ko", "en"])
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
