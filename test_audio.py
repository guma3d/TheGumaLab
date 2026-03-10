
import os
import sys
from google import genai
from google.genai import types

def test_audio():
    # Make dummy audio file
    with open('dummy.mp3', 'wb') as f:
        f.write(b'\x00' * 1024)

    try:
        from dotenv import load_dotenv; load_dotenv('YoutubeToDoc/.env')
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        print('Uploading file...')
        uploaded_file = client.files.upload(file='dummy.mp3')
        
        m = 'gemini-3.1-flash-lite-preview'
        print(f'Testing {m} for audio...')
        response = client.models.generate_content(
            model=m,
            contents=[uploaded_file, 'What is this?']
        )
        print('SUCCESS:', getattr(response, 'text', 'unknown'))
    except Exception as e:
        print('FAILED:', str(e))

if __name__ == '__main__':
    test_audio()

