import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("API Key not found.")
else:
    from google import genai
    client = genai.Client(api_key=api_key)
    try:
        models = client.models.list()
        print("Available models:")
        for m in models:
            if 'flash' in m.name.lower() or 'pro' in m.name.lower():
                print(m.name)
    except Exception as e:
        print("Error listing models:", e)
